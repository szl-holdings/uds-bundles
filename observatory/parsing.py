"""Bounded, deterministic parsing for repository-owned UDS/Zarf manifests."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from .config import (
    MAX_ALIAS_REFERENCES,
    MAX_COLLECTION_ITEMS,
    MAX_MANIFEST_BYTES,
    MAX_NESTING_DEPTH,
    MAX_REFERENCE_LENGTH,
    canonical_bytes,
    sha256_bytes,
)


class DuplicateKeyError(ValueError):
    """Raised when a JSON or YAML mapping repeats a key."""


class StrictLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(
    loader: StrictLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, (str, int, float, bool, type(None))):
            raise DuplicateKeyError("mapping key must be scalar")
        if key in mapping:
            raise DuplicateKeyError(f"duplicate mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate mapping key: {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite value: {value}")


def _walk_shape(value: Any, *, depth: int = 0) -> tuple[int, int]:
    if depth > MAX_NESTING_DEPTH:
        raise ValueError("manifest nesting exceeds limit")
    if isinstance(value, Mapping):
        total = len(value)
        deepest = depth
        for key, item in value.items():
            key_total, key_depth = _walk_shape(key, depth=depth + 1)
            item_total, item_depth = _walk_shape(item, depth=depth + 1)
            total += key_total + item_total
            deepest = max(deepest, key_depth, item_depth)
    elif isinstance(value, list):
        total = len(value)
        deepest = depth
        for item in value:
            item_total, item_depth = _walk_shape(item, depth=depth + 1)
            total += item_total
            deepest = max(deepest, item_depth)
    else:
        total = 1
        deepest = depth
    if total > MAX_COLLECTION_ITEMS:
        raise ValueError("manifest collection count exceeds limit")
    return total, deepest


def _alias_reference_count(text: str) -> int:
    # Conservative pre-parse guard, not a claim of complete YAML lexing.
    return len(re.findall(r"(?<![A-Za-z0-9_.-])\*[A-Za-z0-9_.-]+", text))


def parse_manifest(text: str, filename: str) -> tuple[Mapping[str, Any], str]:
    raw = text.encode("utf-8")
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("manifest exceeds byte limit")
    if "\x00" in text:
        raise ValueError("NUL bytes are forbidden")
    if _alias_reference_count(text) > MAX_ALIAS_REFERENCES:
        raise ValueError("YAML alias reference count exceeds limit")

    try:
        if Path(filename).suffix.lower() == ".json":
            value = json.loads(
                text,
                object_pairs_hook=_json_object,
                parse_constant=_reject_constant,
            )
            parser = "json-strict"
        else:
            value = yaml.load(text, Loader=StrictLoader)
            parser = "yaml-safe-strict"
    except (
        DuplicateKeyError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        raise ValueError(f"invalid manifest: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValueError("manifest root must be a mapping")
    _walk_shape(value)
    return value, parser


def _collect_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _collect_strings(key)
            yield from _collect_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _collect_strings(item)


def classify_manifest(value: Mapping[str, Any], filename: str) -> str:
    lower = filename.lower()
    kind = str(value.get("kind", "")).lower()
    if lower == "zarf.yaml" or "components" in value:
        return "zarf-package"
    if lower == "uds-bundle.yaml" or kind == "bundle":
        return "uds-bundle"
    if lower == "uds-package.yaml" or kind == "package":
        return "uds-package"
    return "generic-manifest"


def extract_references(value: Mapping[str, Any]) -> dict[str, list[str]]:
    images: set[str] = set()
    urls: set[str] = set()
    local_paths: set[str] = set()
    digest_claims: set[str] = set()

    for text in _collect_strings(value):
        candidate = text.strip()
        if not candidate or len(candidate) > MAX_REFERENCE_LENGTH:
            continue
        if re.fullmatch(r"sha256:[0-9a-fA-F]{64}", candidate):
            digest_claims.add(candidate.lower())
        elif candidate.startswith(("http://", "https://", "oci://")):
            urls.add(candidate)
        elif (
            re.fullmatch(
                r"[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+|@sha256:[0-9a-fA-F]{64})",
                candidate,
            )
            and "/" in candidate
        ):
            images.add(candidate)
        elif candidate.startswith(("./", "../")) or candidate.endswith(
            (".yaml", ".yml", ".json", ".tgz")
        ):
            local_paths.add(candidate)

    return {
        "images": sorted(images),
        "urls": sorted(urls),
        "local_paths": sorted(local_paths),
        "declared_digests": sorted(digest_claims),
    }


def validate_manifest(text: str, filename: str) -> dict[str, Any]:
    raw = text.encode("utf-8")
    value, parser = parse_manifest(text, filename)
    item_count, max_depth = _walk_shape(value)
    references = extract_references(value)
    manifest_type = classify_manifest(value, filename)

    findings: list[dict[str, str]] = []
    metadata = value.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    if not metadata.get("name"):
        findings.append({"level": "warning", "code": "METADATA_NAME_UNAVAILABLE"})
    if manifest_type == "zarf-package" and not isinstance(value.get("components"), list):
        findings.append({"level": "warning", "code": "ZARF_COMPONENTS_UNAVAILABLE"})
    if any(path.startswith("../") for path in references["local_paths"]):
        findings.append({"level": "error", "code": "PARENT_PATH_REFERENCE"})

    canonical = canonical_bytes(value)
    return {
        "schema": "szl.uds-observatory.validation/v1",
        "status": (
            "INVALID"
            if any(row["level"] == "error" for row in findings)
            else "VALID"
        ),
        "parser": parser,
        "filename": filename,
        "manifest_type": manifest_type,
        "raw_sha256": sha256_bytes(raw),
        "canonical_sha256": sha256_bytes(canonical),
        "raw_bytes": len(raw),
        "canonical_bytes": len(canonical),
        "item_count": item_count,
        "max_depth": max_depth,
        "references": references,
        "findings": findings,
        "signature_state": "UNAVAILABLE_NOT_VERIFIED",
        "deployment_state": "NOT_ATTEMPTED",
        "mutation_performed": False,
    }
