#!/usr/bin/env python3
"""Deterministic Helm file SBOM and unsigned integrity bindings (stdlib only).

SPDX-License-Identifier: Apache-2.0
This is deliberately not a signature, provenance, or runtime package scanner.
"""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import zlib


REPOSITORY = "https://github.com/szl-holdings/uds-bundles"
SCOPE = "Helm archive files only; excludes container contents, models, agents, and tools"
MAX_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 10000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def require_digest(value, length):
    if not re.fullmatch(r"[0-9a-f]{%d}" % length, value) or set(value) == {"0"}:
        raise ValueError("missing, placeholder, or invalid expected digest")


def read_limited(path):
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("evidence input exceeds size limit")
    return data


def bounded_members(compressed):
    """Bound the entire TAR, including metadata/padding, before parsing headers.

    Parse individual headers only: TarFile would consume PAX/GNU extensions
    internally before yielding members. This deliberately narrow chart profile
    rejects those extensions, sparse entries and every non-file/directory type.
    """
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        expanded = stream.read(MAX_BYTES + 1)
    if len(expanded) > MAX_BYTES:
        raise ValueError("total decompressed TAR exceeds size limit")
    if len(expanded) % 512:
        raise ValueError("TAR stream is not block-aligned")
    offset = 0
    count = 0
    while offset + 512 <= len(expanded):
        header = expanded[offset:offset + 512]
        if header == bytes(512):
            if len(expanded) - offset < 1024 or any(expanded[offset:]):
                raise ValueError("invalid TAR end markers or trailing data")
            return
        member = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
        count += 1
        if count > MAX_MEMBERS:
            raise ValueError("too many archive members")
        if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
            raise ValueError("unsupported TAR type (including PAX/GNU metadata)")
        if member.size < 0 or (member.isdir() and member.size != 0):
            raise ValueError("invalid archive member size")
        start = offset + 512
        offset = start + ((member.size + 511) // 512) * 512
        if offset > len(expanded):
            raise ValueError("truncated archive member")
        yield member, expanded[start:start + member.size]
    raise ValueError("missing TAR end markers")


def documents(artifact, source_sha, license_file):
    """Reproduce evidence for these exact archive bytes, without extracting files."""
    require_digest(source_sha, 40)
    artifact_bytes = read_limited(artifact)
    artifact_hash = digest(artifact_bytes)
    license_bytes = read_limited(license_file)
    if b"Apache License" not in license_bytes or b"Version 2.0" not in license_bytes:
        raise ValueError("expected repository Apache-2.0 LICENSE")
    components = []
    seen = set()
    files = set()
    directories = set()
    roots = set()
    for member, contents in bounded_members(artifact_bytes):
        path = PurePosixPath(member.name)
        if (not path.parts or path.is_absolute() or ".." in path.parts or "\\" in member.name
                or ":" in member.name or str(path) != member.name
                or member.name in seen):
            raise ValueError("unsafe or duplicate archive path")
        seen.add(member.name)
        roots.add(path.parts[0])
        parents = {str(parent) for parent in path.parents if parent != PurePosixPath(".")}
        if parents & files or (member.isfile() and member.name in directories):
            raise ValueError("file/directory hierarchy collision")
        directories.update(parents)
        if member.isdir():
            directories.add(member.name)
            continue
        if not member.isfile() or len(path.parts) < 2:
            raise ValueError("only regular chart files are supported")
        files.add(member.name)
        components.append({
            "type": "file", "bom-ref": member.name, "name": member.name,
            "hashes": [{"alg": "SHA-256", "content": digest(contents)}],
        })
    if len(roots) != 1 or next(iter(roots)) + "/Chart.yaml" not in files:
        raise ValueError("expected one nonempty Helm chart")
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
        "metadata": {
            "component": {
                "type": "application", "name": artifact.name,
                "bom-ref": "sha256:" + artifact_hash,
                "hashes": [{"alg": "SHA-256", "content": artifact_hash}],
                "licenses": [{"license": {"id": "Apache-2.0"}}],
            },
            "properties": [
                {"name": "szl:evidence:scope", "value": SCOPE},
                {"name": "szl:source:repository", "value": REPOSITORY},
                {"name": "szl:source:gitCommit", "value": source_sha},
                {"name": "szl:evidence:authentication", "value": "unsigned"},
            ],
        },
        "components": sorted(components, key=lambda item: item["name"]),
    }
    sbom_bytes = canonical(sbom)
    manifest = {
        "schema": "szl-helm-evidence/v1", "authentication": "unsigned",
        "scope": SCOPE,
        "source": {"repository": REPOSITORY, "gitCommit": source_sha},
        "artifact": {"name": artifact.name, "sha256": artifact_hash},
        "sbom": {"name": artifact.name + ".cdx.json", "sha256": digest(sbom_bytes)},
        "license": {"name": "LICENSE", "sha256": digest(license_bytes),
                    "declared": "Apache-2.0", "scope": "repository-owned chart; no runtime license inference"},
    }
    return sbom_bytes, canonical(manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["generate", "verify"])
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--source-sha", required=True, help="expected full source commit from an independent trusted channel")
    parser.add_argument("--artifact-sha256", help="required for verify; obtain independently of this unsigned evidence")
    parser.add_argument("--license", type=Path, default=Path("LICENSE"))
    args = parser.parse_args()
    try:
        if args.mode == "verify":
            require_digest(args.artifact_sha256 or "", 64)
            if digest(read_limited(args.artifact)) != args.artifact_sha256:
                raise ValueError("artifact digest mismatch")
        sbom, manifest = documents(args.artifact, args.source_sha, args.license)
        for suffix, expected in [(".cdx.json", sbom), (".evidence.json", manifest)]:
            path = args.artifact.with_name(args.artifact.name + suffix)
            if args.mode == "generate":
                path.write_bytes(expected)
            elif read_limited(path) != expected:
                raise ValueError("missing, noncanonical, placeholder, or mismatched evidence: " + path.name)
    except (OSError, EOFError, ValueError, tarfile.TarError, zlib.error) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
    print("PASS: unsigned chart-file integrity; source binding is an assertion, not authenticated provenance")


if __name__ == "__main__":
    main()
