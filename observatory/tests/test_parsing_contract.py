"""Untrusted manifests cannot construct Python objects or escape HTTP rejection."""
import hashlib
from unittest import mock

import pytest
import yaml
from fastapi.testclient import TestClient

from observatory.app import create_app
from observatory.config import MAX_NESTING_DEPTH
from observatory.parsing import StrictLoader, parse_manifest, validate_manifest


@pytest.mark.parametrize("manifest", [
    "value: !!python/object/apply:builtins.eval ['1']",
    "value: !!python/object/new:builtins.list [[1]]",
    "value: !!python/name:builtins.eval",
    "value: !!python/object:builtins.object {}",
])
def test_python_tags_are_rejected_without_invoking_a_constructor(manifest):
    with mock.patch("builtins.eval") as evaluate:
        with pytest.raises(ValueError, match="invalid manifest"):
            parse_manifest(manifest, "manifest.yaml")
        evaluate.assert_not_called()


@pytest.mark.parametrize("manifest", [
    "date: 2026-10-01",
    "binary: !!binary aGVsbG8=",
    "set: !!set {a: null}",
    "1: integer-key\n'1': string-key",
    "value: .nan",
    "value: .inf",
])
def test_non_json_yaml_is_rejected_at_parser_boundary(manifest):
    with pytest.raises(ValueError):
        parse_manifest(manifest, "manifest.yaml")


def test_loader_is_safe_and_disposed_on_success_and_failure():
    assert issubclass(StrictLoader, yaml.SafeLoader)
    original = StrictLoader.dispose
    calls = []

    def dispose(loader):
        calls.append(loader)
        original(loader)

    with mock.patch.object(StrictLoader, "dispose", dispose):
        assert parse_manifest("name: example", "manifest.yaml")[0] == {"name": "example"}
        with pytest.raises(ValueError):
            parse_manifest("name: !!python/name:builtins.eval", "manifest.yaml")
    assert len(calls) == 2


@pytest.mark.parametrize("filename,manifest", [
    ("manifest.json", '{"value":' + '[' * 1500 + '0' + ']' * 1500 + '}'),
    ("manifest.yaml", "value: " + '[' * 1500 + '0' + ']' * 1500),
    ("manifest.yaml", "value: " + '[' * (MAX_NESTING_DEPTH + 1) + '0' + ']' * (MAX_NESTING_DEPTH + 1)),
])
def test_deep_inputs_are_normalized_to_validation_errors(filename, manifest):
    with pytest.raises(ValueError):
        parse_manifest(manifest, filename)


def test_recursive_alias_is_rejected():
    with pytest.raises(ValueError):
        parse_manifest("value: &cycle [*cycle]", "manifest.yaml")


def test_date_input_returns_422_and_service_remains_ready(tmp_path):
    api = TestClient(create_app(tmp_path))
    response = api.post("/api/validate", json={"manifest": "date: 2026-10-01"})
    assert response.status_code == 422
    assert "JSON-compatible" in response.json()["detail"]
    assert api.get("/readyz").status_code == 200


def test_valid_manifest_retains_canonical_digest():
    report = validate_manifest("metadata:\n  name: example\ncomponents: []", "zarf.yaml")
    assert report["canonical_sha256"] == hashlib.sha256(
        b'{"components":[],"metadata":{"name":"example"}}'
    ).hexdigest()
