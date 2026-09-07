# SPDX-License-Identifier: Apache-2.0
"""Bounded parsing and read-only inspection for repository-owned UDS/Zarf files."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal

import yaml

MAX_INPUT_BYTES: Final = 131_072
MAX_FILE_BYTES: Final = 262_144
MAX_DEPTH: Final = 32
MAX_ALIASES: Final = 24
MAX_FILES: Final = 200
MAX_SEQUENCE: Final = 1_000
MANIFEST_NAMES: Final = re.compile(
    r"^(?:zarf(?:-package)?|uds(?:-bundle)?|bundle|package)(?:[._-][A-Za-z0-9._-]+)?\.(?:ya?ml|json)$",
    re.IGNORECASE,
)
IMAGE_REF: Final = re.compile(
    r"^(?:(?P<registry>[a-z0-9.-]+(?::[0-9]{1,5})?)/)?"
    r"(?P<path>[a-z0-9._-]+(?:/[a-z0-9._-]+)*)"
    r"(?:(?::(?P<tag>[A-Za-z0-9._-]{1,128}))|(?:@sha256:(?P<digest>[0-9a-f]{64})))?$"
)
SKIP_DIRS: Final = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}


class ManifestError(ValueError):
    """Input is malformed, ambiguous, or outside the parser bounds."""


class BoundedSafeLoader(yaml.SafeLoader):
    alias_count = 0

    def compose_node(self, parent, index):  # noqa: ANN001
        if self.check_event(yaml.AliasEvent):
            self.alias_count += 1
            if self.alias_count > MAX_ALIASES:
                raise ManifestError(f"YAML alias limit exceeded ({MAX_ALIASES})")
        return super().compose_node(parent, index)


def _construct_unique_mapping(loader: BoundedSafeLoader, node: yaml.MappingNode, deep: bool = False):
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ManifestError("mapping key must be scalar and hashable") from exc
        if duplicate:
            raise ManifestError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


BoundedSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _json_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ManifestError(f"non-finite JSON value is forbidden: {value}")


def _measure(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise ManifestError(f"nesting depth exceeded ({MAX_DEPTH})")
    if isinstance(value, dict):
        if len(value) > MAX_SEQUENCE:
            raise ManifestError("mapping entry limit exceeded")
        for key, item in value.items():
            if not isinstance(key, (str, int, float, bool, type(None))):
                raise ManifestError("mapping keys must be JSON-compatible scalars")
            _measure(item, depth=depth + 1)
    elif isinstance(value, list):
        if len(value) > MAX_SEQUENCE:
            raise ManifestError("sequence item limit exceeded")
        for item in value:
            _measure(item, depth=depth + 1)
    elif not isinstance(value, (str, int, float, bool, type(None))):
        raise ManifestError(f"unsupported YAML value type: {type(value).__name__}")


def parse_manifest(text: str, format_hint: Literal["auto", "yaml", "json"] = "auto") -> dict[str, Any]:
    raw = text.encode("utf-8", errors="strict")
    if not raw:
        raise ManifestError("manifest is empty")
    if len(raw) > MAX_INPUT_BYTES:
        raise ManifestError(f"manifest exceeds {MAX_INPUT_BYTES} bytes")
    hint = format_hint
    if hint == "auto":
        hint = "json" if text.lstrip().startswith(("{", "[")) else "yaml"
    try:
        if hint == "json":
            value = json.loads(text, object_pairs_hook=_json_unique, parse_constant=_reject_constant)
        elif hint == "yaml":
            loader = BoundedSafeLoader(text)
            try:
                value = loader.get_single_data()
            finally:
                loader.dispose()
        else:
            raise ManifestError("format_hint must be auto, yaml, or json")
    except (json.JSONDecodeError, yaml.YAMLError, UnicodeError) as exc:
        raise ManifestError(f"invalid {hint}: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise ManifestError("manifest root must be a mapping/object")
    _measure(value)
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def receipt(value: Any) -> str:
    return sha256(canonical_bytes(value))


def _walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, path + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, path + (str(index),))
    else:
        yield path, value


@dataclass(frozen=True, slots=True)
class Reference:
    path: str
    value: str
    shape: str
    digest_pinned: bool
    state: Literal["DECLARED", "INVALID"]


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    path: str | None = None


def inspect_manifest(value: dict[str, Any]) -> dict[str, Any]:
    references: list[Reference] = []
    findings: list[Finding] = []
    component_count = 0
    package_name = None
    package_version = None

    metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
    package_name = metadata.get("name") or value.get("name")
    package_version = metadata.get("version") or value.get("version")

    for path, scalar in _walk(value):
        key = path[-1].casefold() if path else ""
        joined = ".".join(path)
        if key in {"components", "packages"} and isinstance(scalar, list):
            component_count += len(scalar)
        if isinstance(scalar, str) and key in {"image", "images", "repository", "ref", "reference"}:
            candidates = [scalar]
        elif isinstance(scalar, str) and ("image" in key or key.endswith("ref")):
            candidates = [scalar]
        else:
            candidates = []
        for candidate in candidates:
            if len(candidate) > 512:
                references.append(Reference(joined, candidate[:80] + "…", "oversized", False, "INVALID"))
                findings.append(Finding("error", "REFERENCE_TOO_LONG", "Declared reference exceeded 512 characters", joined))
                continue
            match = IMAGE_REF.fullmatch(candidate)
            if not match:
                references.append(Reference(joined, candidate, "unrecognized", False, "INVALID"))
                findings.append(Finding("warning", "REFERENCE_SHAPE", "Reference does not match the bounded OCI/image shape", joined))
                continue
            digest_pinned = bool(match.group("digest"))
            references.append(Reference(joined, candidate, "oci-image", digest_pinned, "DECLARED"))
            if not digest_pinned:
                findings.append(Finding("warning", "REFERENCE_NOT_DIGEST_PINNED", "Reference is declared but not pinned by sha256 digest", joined))

    if not isinstance(package_name, str) or not package_name.strip():
        findings.append(Finding("warning", "PACKAGE_NAME_UNAVAILABLE", "No package name was found in the recognized metadata fields"))
    if not isinstance(package_version, (str, int, float)):
        findings.append(Finding("warning", "PACKAGE_VERSION_UNAVAILABLE", "No package version was found in the recognized metadata fields"))
    if not references:
        findings.append(Finding("info", "REFERENCES_UNAVAILABLE", "No recognized image/reference fields were found"))

    errors = sum(1 for finding in findings if finding.severity == "error")
    result = {
        "schema": "szl.uds-manifest-inspection/v1",
        "state": "INVALID" if errors else "DECLARED",
        "package": {
            "name": str(package_name) if package_name is not None else None,
            "version": str(package_version) if package_version is not None else None,
        },
        "component_count": component_count,
        "references": [asdict(item) for item in references[:MAX_SEQUENCE]],
        "findings": [asdict(item) for item in findings[:MAX_SEQUENCE]],
        "signature_verification": "UNAVAILABLE_NOT_VERIFIED",
        "checksum_verification": "DECLARED_ONLY",
        "deployment": "NOT_ATTEMPTED",
    }
    result["receipt_sha256"] = receipt(result)
    return result


def discover_manifests(root: Path) -> list[dict[str, Any]]:
    resolved = root.resolve()
    results: list[dict[str, Any]] = []
    seen = 0
    for path in sorted(resolved.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(resolved).parts):
            continue
        if not path.is_file() or not MANIFEST_NAMES.fullmatch(path.name):
            continue
        seen += 1
        if seen > MAX_FILES:
            raise ManifestError(f"repository manifest count exceeded {MAX_FILES}")
        relative = path.relative_to(resolved).as_posix()
        size = path.stat().st_size
        row: dict[str, Any] = {"path": relative, "bytes": size, "sha256": sha256(path.read_bytes()) if size <= MAX_FILE_BYTES else None}
        if size > MAX_FILE_BYTES:
            row.update({"state": "INVALID", "error": f"file exceeds {MAX_FILE_BYTES} bytes"})
        else:
            try:
                parsed = parse_manifest(path.read_text(encoding="utf-8"), "json" if path.suffix.lower() == ".json" else "yaml")
                inspected = inspect_manifest(parsed)
                row.update({"state": inspected["state"], "inspection": inspected})
            except (ManifestError, UnicodeError) as exc:
                row.update({"state": "INVALID", "error": str(exc)[:240]})
        results.append(row)
    return results
