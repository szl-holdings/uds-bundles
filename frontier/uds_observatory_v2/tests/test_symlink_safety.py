# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import parser as manifest_parser  # noqa: E402


def test_symlinked_manifest_is_reported_invalid_without_reading_target(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks unavailable")
    outside = tmp_path.parent / f"outside-{tmp_path.name}.yaml"
    outside.write_text("token: should-not-be-read\n", encoding="utf-8")
    link = tmp_path / "zarf.yaml"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    rows = manifest_parser.discover_manifests(tmp_path)
    assert rows == [
        {
            "path": "zarf.yaml",
            "bytes": None,
            "sha256": None,
            "state": "INVALID",
            "error": "symlinked manifests are not read",
        }
    ]
    assert "should-not-be-read" not in repr(rows)


def test_missing_repository_root_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises((manifest_parser.ManifestError, FileNotFoundError)):
        manifest_parser.discover_manifests(missing)
