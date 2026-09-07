# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from observatory import app as module

client = TestClient(module.app)


def test_health_and_readiness_are_bounded() -> None:
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert set(ready.json()["checks"]) == {"repository_root", "static_index"}


def test_source_receipt_has_no_mutation_authority() -> None:
    response = client.get("/api/source")
    assert response.status_code == 200
    payload = response.json()
    assert payload["repository"] == "szl-holdings/uds-bundles"
    assert payload["mutation_authority"] is False
    assert payload["network_authority"] is False
    assert payload["cluster_authority"] is False
    assert payload["registry_authority"] is False
    assert len(payload["receipt"]["digest"]) == 64


def test_duplicate_json_key_fails_closed() -> None:
    response = client.post(
        "/api/validate",
        json={"format": "json", "text": '{"kind":"a","kind":"b"}'},
    )
    assert response.status_code == 422
    assert "duplicate JSON key" in response.json()["detail"]


def test_duplicate_yaml_key_fails_closed() -> None:
    response = client.post(
        "/api/validate",
        json={"format": "yaml", "text": "kind: one\nkind: two\n"},
    )
    assert response.status_code == 422
    assert "duplicate YAML key" in response.json()["detail"]


def test_nonfinite_json_fails_closed() -> None:
    response = client.post(
        "/api/validate",
        json={"format": "json", "text": '{"value":NaN}'},
    )
    assert response.status_code == 422
    assert "non-finite" in response.json()["detail"]


def test_inline_secret_and_mutable_tag_are_reported() -> None:
    response = client.post(
        "/api/validate",
        json={
            "format": "yaml",
            "text": (
                "kind: ZarfPackageConfig\n"
                "metadata:\n  name: sample\n"
                "password: not-a-variable\n"
                "components:\n"
                "  - name: app\n"
                "    images:\n"
                "      - registry.example/app:latest\n"
            ),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "INVALID"
    codes = {row["code"] for row in payload["findings"]}
    assert "POSSIBLE_INLINE_SECRET" in codes
    assert "MUTABLE_IMAGE_TAG" in codes
    assert payload["evidence"]["deployment"] == "NOT_ATTEMPTED"


def test_receipt_is_deterministic_for_equivalent_json() -> None:
    first = client.post(
        "/api/validate",
        json={"format": "json", "text": '{"kind":"x","components":[]}'},
    ).json()
    second = client.post(
        "/api/validate",
        json={"format": "json", "text": '{ "components": [], "kind": "x" }'},
    ).json()
    assert first["receipt"]["digest"] == second["receipt"]["digest"]


def test_catalog_reads_only_injected_local_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "zarf-package.yaml"
    manifest.write_text(
        "kind: ZarfPackageConfig\nmetadata:\n  name: sample\ncomponents: []\n",
        encoding="utf-8",
    )
    with patch.object(module, "_candidate_files", return_value=[manifest]), patch.object(
        module, "ROOT", tmp_path
    ):
        response = client.get("/api/bundles")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["slug"] == "zarf-package.yaml"
    assert payload["items"][0]["parse_state"] == "VALID"


def test_bundle_path_traversal_is_rejected() -> None:
    response = client.get("/api/bundles/%2E%2E%2FREADME.md")
    assert response.status_code in {400, 404}


def test_manifest_input_rejects_extra_fields() -> None:
    response = client.post(
        "/api/validate",
        json={"format": "yaml", "text": "kind: x\n", "execute": True},
    )
    assert response.status_code == 422


def test_frontend_is_local_only_and_accessible() -> None:
    html = (module.STATIC / "index.html").read_text(encoding="utf-8")
    script = (module.STATIC / "app.js").read_text(encoding="utf-8")
    style = (module.STATIC / "styles.css").read_text(encoding="utf-8")
    assert 'href="#main"' in html
    assert 'aria-live="polite"' in html
    assert "https://" not in html and "http://" not in html
    assert "localStorage" not in script and "sessionStorage" not in script
    assert "prefers-reduced-motion" in style
    assert "forced-colors" in style
    assert "@media print" in style


def test_deployment_contract_does_not_claim_hub_success() -> None:
    response = client.get("/deployment.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_state"] == "MEASURED_BY_THIS_RESPONSE"
    assert payload["hub_publication"].startswith("UNAVAILABLE")
