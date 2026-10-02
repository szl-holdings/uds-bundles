"""Existing references and static assets keep the same bounded public contract."""
import itertools
import re

import pytest
from fastapi.testclient import TestClient

from observatory.app import create_app
from observatory.config import MAX_REFERENCE_LENGTH
from observatory.parsing import _is_image_reference, extract_references


def test_image_recognizer_preserves_existing_grammar():
    previous = re.compile(r"[A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+|@sha256:[0-9a-fA-F]{64})")
    names = ("ghcr.io/szl/a", "a/b", "-/-", "a", "a:b/c", "a@b/c", "é/a", "")
    suffixes = ("latest", "v1.2-3", "-" * 2048, "a/b", "a:b", "", "é", "A" * 64)
    for name, separator, suffix in itertools.product(names, (":", "@sha256:"), suffixes):
        candidate = name + separator + suffix
        expected = bool(previous.fullmatch(candidate)) and "/" in candidate
        assert _is_image_reference(candidate) == expected, candidate


def test_reference_length_limit_and_hyphen_runs_are_retained():
    valid = "a/b:" + "-" * (MAX_REFERENCE_LENGTH - 4)
    refs = extract_references({"image": valid, "oversize": valid + "-", "bad": "a/b:" + "-" * 100 + "!"})
    assert refs["images"] == [valid]


def test_digest_and_other_reference_categories_are_unchanged():
    digest = "a" * 64
    image = "ghcr.io/szl/test@sha256:" + digest
    assert extract_references({"refs": [image, "sha256:" + digest, "https://example.test/a", "../x.yaml"]}) == {
        "images": [image],
        "urls": ["https://example.test/a"],
        "local_paths": ["../x.yaml"],
        "declared_digests": ["sha256:" + digest],
    }


@pytest.mark.parametrize("asset,media_type", [
    ("app.js", "application/javascript"),
    ("styles.css", "text/css"),
    ("responsive.css", "text/css"),
])
def test_named_assets_remain_available(tmp_path, asset, media_type):
    api = TestClient(create_app(tmp_path))
    response = api.get("/" + asset)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(media_type)


@pytest.mark.parametrize("path", [
    "/config.py", "/app.py", "/missing.js", "/styles.css.bak", "/%2e%2e%2fconfig.py", "/app.js%00",
])
def test_unnamed_and_traversal_assets_are_rejected(tmp_path, path):
    api = TestClient(create_app(tmp_path))
    assert api.get(path).status_code == 404
