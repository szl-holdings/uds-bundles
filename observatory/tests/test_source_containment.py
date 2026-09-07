# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from observatory.app import create_app
from observatory.catalog import controlled_hashes, discover_bundles, source_owned


def _manifest(path: Path, name: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "kind: ZarfPackageConfig\n"
        "metadata:\n"
        f"  name: {name}\n"
        "components: []\n",
        encoding="utf-8",
    )
    return path


def _symlink(
    link: Path,
    target: Path | str,
    *,
    target_is_directory: bool = False,
) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks unavailable on this test host: {exc}")


def test_direct_repository_manifest_is_admitted(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    manifest = _manifest(
        repository / "bundles" / "direct" / "zarf.yaml",
        "direct",
    )

    assert source_owned(repository, manifest) is True
    items = discover_bundles(repository)
    assert [item["slug"] for item in items] == ["direct"]
    assert items[0]["manifests"][0]["path"] == "bundles/direct/zarf.yaml"


def test_external_symlink_escape_is_excluded_from_list_and_detail(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    bundle = repository / "bundles" / "escape"
    bundle.mkdir(parents=True)
    outside = _manifest(tmp_path / "outside-zarf.yaml", "outside")
    link = bundle / "zarf.yaml"
    _symlink(link, outside)

    assert source_owned(repository, link) is False
    assert discover_bundles(repository) == []
    response = TestClient(create_app(repository)).get("/api/bundles/escape")
    assert response.status_code == 404


def test_internal_symlink_alias_is_rejected_but_direct_file_remains(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    bundle = repository / "bundles" / "internal"
    target = _manifest(bundle / "uds-bundle.yaml", "internal")
    alias = bundle / "zarf.yaml"
    _symlink(alias, target.name)

    assert source_owned(repository, target) is True
    assert source_owned(repository, alias) is False
    items = discover_bundles(repository)
    assert [item["slug"] for item in items] == ["internal"]
    assert [row["name"] for row in items[0]["manifests"]] == [
        "uds-bundle.yaml"
    ]


def test_symlinked_parent_directory_is_not_traversed(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    bundles = repository / "bundles"
    bundles.mkdir(parents=True)
    outside_bundle = tmp_path / "outside" / "linked"
    _manifest(outside_bundle / "zarf.yaml", "outside-linked")
    linked = bundles / "linked"
    _symlink(linked, outside_bundle, target_is_directory=True)

    assert source_owned(repository, linked / "zarf.yaml") is False
    assert discover_bundles(repository) == []


def test_controlled_hashes_do_not_follow_symlinked_files(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    controlled = repository / "observatory" / "app.py"
    controlled.parent.mkdir(parents=True)
    outside = tmp_path / "outside.py"
    outside.write_text("SECRET = 'not repository owned'\n", encoding="utf-8")
    _symlink(controlled, outside)

    assert source_owned(repository, controlled) is False
    assert controlled_hashes(repository)["observatory/app.py"] is None


def test_lexical_parent_escape_is_rejected(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = _manifest(tmp_path / "outside.yaml", "outside")
    candidate = repository / "bundles" / ".." / ".." / outside.name

    assert source_owned(repository, candidate) is False
