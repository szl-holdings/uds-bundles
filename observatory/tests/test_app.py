from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from observatory.app import create_app
from observatory.config import MAX_ALIAS_REFERENCES
from observatory.parsing import validate_manifest


def write_bundle(root: Path, slug: str = "szl-test") -> None:
    bundle = root / "bundles" / slug
    bundle.mkdir(parents=True)
    (bundle / "zarf.yaml").write_text(
        "kind: ZarfPackageConfig\nmetadata:\n  name: szl-test\n  version: 0.1.0\ncomponents: []\n",
        encoding="utf-8",
    )
    (bundle / "uds-bundle.yaml").write_text(
        "kind: Bundle\nmetadata:\n  name: szl-test\npackages: []\n",
        encoding="utf-8",
    )


def client(tmp_path: Path) -> TestClient:
    write_bundle(tmp_path)
    return TestClient(create_app(tmp_path))


def test_health_and_readiness_are_read_only(tmp_path: Path) -> None:
    api = client(tmp_path)
    health = api.get("/healthz")
    assert health.status_code == 200
    assert health.json()["mutation_authority"] is False
    assert health.headers["x-szl-authority"] == "read-only-observatory"
    assert api.get("/readyz").status_code == 200


def test_catalog_is_deterministic_and_receipted(tmp_path: Path) -> None:
    api = client(tmp_path)
    first = api.get("/api/bundles").json()
    second = api.get("/api/bundles").json()
    assert first == second
    assert first["bundle_count"] == 1
    assert first["manifest_count"] == 2
    assert first["manifest_states"] == {"VALID": 2}
    assert len(first["receipt_sha256"]) == 64
    assert first["mutation_performed"] is False


def test_slug_traversal_is_rejected(tmp_path: Path) -> None:
    api = client(tmp_path)
    assert api.get("/api/bundles/%2e%2e").status_code in {404, 422}
    assert api.get("/api/bundles/szl-test").status_code == 200


def test_duplicate_yaml_keys_fail_closed() -> None:
    try:
        validate_manifest("kind: A\nkind: B\nmetadata:\n  name: x\n", "zarf.yaml")
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate keys were accepted")


def test_alias_bomb_guard_fails_before_parse() -> None:
    manifest = "metadata:\n  name: x\na: &a [1]\nb: [" + ",".join("*a" for _ in range(MAX_ALIAS_REFERENCES + 1)) + "]\n"
    try:
        validate_manifest(manifest, "manifest.yaml")
    except ValueError as exc:
        assert "alias" in str(exc).lower()
    else:
        raise AssertionError("excess aliases were accepted")


def test_validate_endpoint_returns_stable_canonical_receipt(tmp_path: Path) -> None:
    api = client(tmp_path)
    payload = {
        "filename": "zarf.yaml",
        "manifest": "metadata:\n  version: 0.1.0\n  name: example\ncomponents: []\nkind: ZarfPackageConfig\n",
    }
    response = api.post("/api/validate", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "VALID"
    assert report["signature_state"] == "UNAVAILABLE_NOT_VERIFIED"
    assert report["deployment_state"] == "NOT_ATTEMPTED"
    expected = hashlib.sha256(
        b'{"components":[],"kind":"ZarfPackageConfig","metadata":{"name":"example","version":"0.1.0"}}'
    ).hexdigest()
    assert report["canonical_sha256"] == expected


def test_parent_reference_is_invalid(tmp_path: Path) -> None:
    api = client(tmp_path)
    response = api.post(
        "/api/validate",
        json={"filename": "zarf.yaml", "manifest": "metadata:\n  name: x\ncomponents:\n  - files:\n      - source: ../secret\n"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "INVALID"


def test_frontend_uses_local_assets_only(tmp_path: Path) -> None:
    api = client(tmp_path)
    page = api.get("/")
    assert page.status_code == 200
    html = page.text
    assert 'src="/app.js"' in html
    assert 'href="/styles.css"' in html
    assert 'href="/responsive.css"' in html
    assert "https://" not in html
    assert "http://" not in html
    assert "localStorage" not in api.get("/app.js").text
