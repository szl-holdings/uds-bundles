"""Constants and deterministic digest helpers for the UDS observatory."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

MAX_MANIFEST_BYTES = 128 * 1024
MAX_ALIAS_REFERENCES = 32
MAX_NESTING_DEPTH = 32
MAX_COLLECTION_ITEMS = 5000
MAX_REFERENCE_LENGTH = 2048
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,78}[a-z0-9])?$")
MANIFEST_NAMES = ("zarf.yaml", "uds-bundle.yaml", "uds-package.yaml")
DISCOVERY_ROOTS = (Path("bundles"), Path("uds-bundles") / "PER_BUNDLE")
CONTROLLED_FILES = (
    "observatory/app.py",
    "observatory/catalog.py",
    "observatory/config.py",
    "observatory/parsing.py",
    "observatory/static/index.html",
    "observatory/static/app.js",
    "observatory/static/styles.css",
    "observatory/static/responsive.css",
    "observatory/requirements.txt",
    "observatory/Dockerfile",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
