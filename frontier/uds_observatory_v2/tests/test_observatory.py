# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as service  # noqa: E402
import parser as manifest_parser  # noqa: E402

client = TestClient(service.app)


def valid_manifest(image: str = "registry.example.test/szl/api@sha256:" + "a" * 64) -> str:
    return "\n".join(
        [
            "kind: ZarfPackageConfig",
            "metadata:",
            "  name: bounded-example",
            "  version: 0.1.0",
            "components:",
            "  - name: api",
            "    images:",
            f"      - {image}",
        ]
    )


def test_health_readiness_and_source_are_side_effect_free(monkeypatch) -> None:
    monkeypatch.setenv("SOURCE_REVISION", "b" * 40)
    monkeypatch.setenv("GH_TOKEN", "ghp_" + "x" * 40)
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/readyz").status_code == 200
    response = client.get("/api/source")
    assert response.status_code == 200
    assert "ghp_" not in response.text
    payload = response.json()
    assert payload["source"] == {"state": "MEASURED", "revision": "b" * 40}
    for key in ("mutation_authority", "cluster_authority", "registry_authority", "shell_authority", "secrets_recorded"):
        assert payload[key] is False


def test_strict_duplicate_key_rejection() -> None:
    with pytest.raises(manifest_parser.ManifestError, match="duplicate JSON key"):
        manifest_parser.parse_manifest('{"name":"one","name":"two"}', "json")
    with pytest.raises(manifest_parser.ManifestError, match="duplicate YAML key"):
        manifest_parser.parse_manifest("name: one\nname: two\n", "yaml")


def test_root_depth_alias_and_byte_bounds() -> None:
    with pytest.raises(manifest_parser.ManifestError, match="root must be"):
        manifest_parser.parse_manifest("- one\n- two\n", "yaml")

    deep = "value: 1"
    for index in range(manifest_parser.MAX_DEPTH + 2):
        deep = f"level{index}:\n" + "  " + deep.replace("\n", "\n  ")
    with pytest.raises(manifest_parser.ManifestError, match="depth"):
        manifest_parser.parse_manifest(deep, "yaml")

    aliases = ["base: &base {name: test}"] + [f"copy{i}: *base" for i in range(manifest_parser.MAX_ALIASES + 1)]
    with pytest.raises(manifest_parser.ManifestError, match="alias limit"):
        manifest_parser.parse_manifest("\n".join(aliases), "yaml")

    with pytest.raises(manifest_parser.ManifestError, match="exceeds"):
        manifest_parser.parse_manifest("name: " + "x" * manifest_parser.MAX_INPUT_BYTES, "yaml")


def test_inspection_distinguishes_declared_and_digest_pinned() -> None:
    parsed = manifest_parser.parse_manifest(valid_manifest(), "yaml")
    inspected = manifest_parser.inspect_manifest(parsed)
    assert inspected["state"] == "DECLARED"
    assert inspected["references"][0]["digest_pinned"] is True
    assert inspected["signature_verification"] == "UNAVAILABLE_NOT_VERIFIED"
    assert inspected["checksum_verification"] == "DECLARED_ONLY"
    assert inspected["deployment"] == "NOT_ATTEMPTED"

    parsed_unpinned = manifest_parser.parse_manifest(valid_manifest("registry.example.test/szl/api:latest"), "yaml")
    unpinned = manifest_parser.inspect_manifest(parsed_unpinned)
    assert unpinned["references"][0]["digest_pinned"] is False
    assert any(item["code"] == "REFERENCE_NOT_DIGEST_PINNED" for item in unpinned["findings"])


def test_validate_api_never_executes_or_publishes() -> None:
    response = client.post("/api/validate", json={"text": valid_manifest(), "format": "yaml"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["side_effects"] is False
    assert payload["deployment"] == "NOT_ATTEMPTED"
    assert payload["publication"] == "NOT_ATTEMPTED"
    assert len(payload["manifest_sha256"]) == 64
    assert len(payload["receipt_sha256"]) == 64


def test_validate_api_rejects_extra_fields_and_malformed_input() -> None:
    assert client.post("/api/validate", json={"text": "name: one\nname: two", "format": "yaml"}).status_code == 422
    assert client.post("/api/validate", json={"text": "name: one", "format": "yaml", "execute": True}).status_code == 422
    assert client.post("/api/validate", json={"text": "", "format": "auto"}).status_code == 422


def test_repository_inventory_is_local_bounded_and_deterministic(tmp_path, monkeypatch) -> None:
    (tmp_path / "zarf.yaml").write_text(valid_manifest(), encoding="utf-8")
    (tmp_path / "not-a-manifest.txt").write_text("secret", encoding="utf-8")
    monkeypatch.setattr(service, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(service, "_cache", None)
    first = client.get("/api/bundles")
    monkeypatch.setattr(service, "_cache", None)
    second = client.get("/api/bundles")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    payload = first.json()
    assert payload["count"] == 1
    assert payload["items"][0]["path"] == "zarf.yaml"
    assert "not-a-manifest" not in first.text
    artifact_id = payload["items"][0]["id"]
    assert client.get(f"/api/bundles/{artifact_id}").status_code == 200
    assert client.get("/api/bundles/../../etc/passwd").status_code == 404


def test_security_headers_and_local_assets() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "connect-src 'self'" in response.headers["content-security-policy"]
    html = response.text
    assert "http://" not in html
    assert "https://" not in html
    assert "<iframe" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    javascript = client.get("/app.js")
    assert javascript.status_code == 200
    assert "innerHTML" not in javascript.text
    assert "insertAdjacentHTML" not in javascript.text
    assert client.get("/styles.css").status_code == 200


def test_manifest_receipt_is_stable() -> None:
    one = manifest_parser.inspect_manifest(manifest_parser.parse_manifest(valid_manifest(), "yaml"))
    two = manifest_parser.inspect_manifest(manifest_parser.parse_manifest(valid_manifest(), "yaml"))
    assert json.dumps(one, sort_keys=True) == json.dumps(two, sort_keys=True)
    assert one["receipt_sha256"] == two["receipt_sha256"]
