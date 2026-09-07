"""Local-only bundle discovery and source commitment helpers."""
from __future__ import annotations

import os
import stat
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


def _lexical_absolute(path: Path) -> Path:
    """Normalize dots without resolving symlinks or junctions."""

    return Path(os.path.abspath(os.fspath(path)))


def _is_link_like(path: Path) -> bool:
    """Reject POSIX symlinks and Windows directory junctions."""

    try:
        if stat.S_ISLNK(path.lstat().st_mode):
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction and is_junction())
    except OSError:
        return True


def source_owned(repo_root: Path, path: Path) -> bool:
    """Prove that ``path`` is a direct, existing entry below ``repo_root``.

    Containment is checked twice: first lexically, before link resolution, and
    then against strict resolved paths. Every component from the repository
    root to the candidate is inspected with ``lstat`` and link-like entries are
    rejected, including aliases whose target remains inside the repository.
    """

    lexical_root = _lexical_absolute(repo_root)
    lexical_candidate = _lexical_absolute(path)
    try:
        relative = lexical_candidate.relative_to(lexical_root)
    except ValueError:
        return False

    try:
        if _is_link_like(lexical_root):
            return False
        resolved_root = lexical_root.resolve(strict=True)
        current = lexical_root
        for part in relative.parts:
            current /= part
            if _is_link_like(current):
                return False
        resolved_candidate = current.resolve(strict=True)
        resolved_candidate.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def safe_child(root: Path, path: Path) -> bool:
    """Backward-compatible name for the direct-source ownership predicate."""

    return source_owned(root, path)


def discover_bundles(repo_root: Path) -> list[dict[str, Any]]:
    discovered: dict[str, dict[str, Any]] = {}
    for relative_root in DISCOVERY_ROOTS:
        root = repo_root / relative_root
        if not source_owned(repo_root, root) or not root.is_dir():
            continue
        directories = sorted(
            path
            for path in root.iterdir()
            if (
                not path.name.startswith(".")
                and source_owned(repo_root, path)
                and path.is_dir()
            )
        )
        for directory in directories:
            if not SLUG_RE.fullmatch(directory.name):
                continue
            manifests: list[dict[str, Any]] = []
            for name in MANIFEST_NAMES:
                path = directory / name
                if not source_owned(repo_root, path) or not path.is_file():
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
    hashes: dict[str, str | None] = {}
    for name in CONTROLLED_FILES:
        path = repo_root / name
        hashes[name] = (
            sha256_file(path)
            if source_owned(repo_root, path) and path.is_file()
            else None
        )
    return hashes


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
