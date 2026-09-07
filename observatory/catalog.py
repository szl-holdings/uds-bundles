"""Local-only bundle discovery and source commitment helpers."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .config import (
    CONTROLLED_FILES,
    DISCOVERY_ROOTS,
    MANIFEST_NAMES,
    SLUG_RE,
    canonical_bytes,
    sha256_bytes,
    sha256_file,
)
from .parsing import validate_manifest


def safe_child(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def discover_bundles(repo_root: Path) -> list[dict[str, Any]]:
    discovered: dict[str, dict[str, Any]] = {}
    for relative_root in DISCOVERY_ROOTS:
        root = (repo_root / relative_root).resolve()
        if not root.is_dir() or not safe_child(repo_root, root):
            continue
        directories = sorted(
            path
            for path in root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        )
        for directory in directories:
            if not SLUG_RE.fullmatch(directory.name):
                continue
            manifests: list[dict[str, Any]] = []
            for name in MANIFEST_NAMES:
                path = directory / name
                if not path.is_file() or not safe_child(repo_root, path):
                    continue
                raw = path.read_bytes()
                row: dict[str, Any] = {
                    "name": name,
                    "path": path.relative_to(repo_root).as_posix(),
                    "bytes": len(raw),
                    "sha256": sha256_bytes(raw),
                }
                try:
                    report = validate_manifest(raw.decode("utf-8"), name)
                    row.update(
                        {
                            "status": report["status"],
                            "manifest_type": report["manifest_type"],
                            "canonical_sha256": report["canonical_sha256"],
                            "finding_count": len(report["findings"]),
                            "references": report["references"],
                        }
                    )
                except (UnicodeDecodeError, ValueError) as exc:
                    row.update({"status": "INVALID", "error": str(exc)[:300]})
                manifests.append(row)
            if not manifests:
                continue
            candidate = {
                "slug": directory.name,
                "source_root": relative_root.as_posix(),
                "manifest_count": len(manifests),
                "manifests": manifests,
            }
            prior = discovered.get(directory.name)
            # Prefer the canonical top-level bundles/ tree for duplicate names.
            if prior is None or candidate["source_root"] == "bundles":
                discovered[directory.name] = candidate
    return [discovered[key] for key in sorted(discovered)]


def controlled_hashes(repo_root: Path) -> dict[str, str | None]:
    return {
        name: sha256_file(repo_root / name) if (repo_root / name).is_file() else None
        for name in CONTROLLED_FILES
    }


def catalog_payload(repo_root: Path) -> dict[str, Any]:
    items = discover_bundles(repo_root)
    states = Counter(
        manifest.get("status", "UNAVAILABLE")
        for item in items
        for manifest in item["manifests"]
    )
    payload: dict[str, Any] = {
        "schema": "szl.uds-observatory.catalog/v1",
        "bundle_count": len(items),
        "manifest_count": sum(item["manifest_count"] for item in items),
        "manifest_states": dict(sorted(states.items())),
        "items": items,
        "signature_state": "UNAVAILABLE_NOT_VERIFIED",
        "deployment_state": "NOT_ATTEMPTED",
        "mutation_performed": False,
    }
    payload["receipt_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload
