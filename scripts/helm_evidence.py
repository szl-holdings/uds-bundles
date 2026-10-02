#!/usr/bin/env python3
"""Deterministic Helm file SBOM and unsigned integrity bindings (stdlib only).

SPDX-License-Identifier: Apache-2.0
This is deliberately not a signature, provenance, or runtime package scanner.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile


REPOSITORY = "https://github.com/szl-holdings/uds-bundles"
SCOPE = "Helm archive files only; excludes container contents, models, agents, and tools"
MAX_BYTES = 32 * 1024 * 1024


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


def documents(artifact, source_sha, license_file):
    """Reproduce evidence for these exact archive bytes, without extracting files."""
    require_digest(source_sha, 40)
    artifact_hash = digest(read_limited(artifact))
    license_bytes = read_limited(license_file)
    if b"Apache License" not in license_bytes or b"Version 2.0" not in license_bytes:
        raise ValueError("expected repository Apache-2.0 LICENSE")
    components = []
    seen = set()
    total = 0
    with tarfile.open(artifact, "r:gz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name
                    or ":" in member.name or str(path) != member.name
                    or member.name in seen):
                raise ValueError("unsafe or duplicate archive path")
            seen.add(member.name)
            if len(seen) > 10000:
                raise ValueError("too many archive members")
            if member.isdir():
                continue
            if not member.isfile() or len(path.parts) < 2:
                raise ValueError("only regular chart files are supported")
            total += member.size
            if total > MAX_BYTES:
                raise ValueError("expanded chart exceeds size limit")
            with archive.extractfile(member) as stream:
                contents = stream.read()
            components.append({
                "type": "file", "bom-ref": member.name, "name": member.name,
                "hashes": [{"alg": "SHA-256", "content": digest(contents)}],
            })
    roots = {PurePosixPath(item["name"]).parts[0] for item in components}
    if len(roots) != 1 or next(iter(roots)) + "/Chart.yaml" not in seen:
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
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
    print("PASS: unsigned chart-file integrity; source binding is an assertion, not authenticated provenance")


if __name__ == "__main__":
    main()
