# SPDX-License-Identifier: Apache-2.0
"""UDS Bundle Observatory v2: bounded, read-only evidence service."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Final, Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from parser import ManifestError, discover_manifests, inspect_manifest, parse_manifest, receipt

HERE: Final = Path(__file__).resolve().parent
STATIC: Final = HERE / "static"
DEFAULT_REPOSITORY_ROOT: Final = HERE.parents[1]
SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[0-9a-f]{16}$")
CACHE_SECONDS: Final = 30.0
CONTROLLED: Final = (
    HERE / "app.py",
    HERE / "parser.py",
    STATIC / "index.html",
    STATIC / "app.js",
    STATIC / "styles.css",
)


class ValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    text: str = Field(min_length=1, max_length=131_072)
    format: Literal["auto", "yaml", "json"] = "auto"


_cache_lock = threading.Lock()
_cache: tuple[float, list[dict[str, Any]]] | None = None


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def source_revision() -> dict[str, str]:
    raw = os.getenv("SOURCE_REVISION", "").strip().lower()
    if SOURCE_RE.fullmatch(raw):
        return {"state": "MEASURED", "revision": raw}
    return {"state": "UNAVAILABLE", "revision": "UNAVAILABLE"}


def repository_root() -> Path:
    configured = os.getenv("BUNDLE_ROOT", "").strip()
    root = Path(configured) if configured else DEFAULT_REPOSITORY_ROOT
    return root.resolve()


def controlled_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in CONTROLLED:
        result[path.relative_to(HERE).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "UNAVAILABLE"
    return result


def bundle_id(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]


def inventory(*, force: bool = False) -> list[dict[str, Any]]:
    global _cache
    now = time.monotonic()
    with _cache_lock:
        if not force and _cache and now - _cache[0] < CACHE_SECONDS:
            return _cache[1]
    rows = discover_manifests(repository_root())
    normalized: list[dict[str, Any]] = []
    for row in rows:
        value = dict(row)
        value["id"] = bundle_id(str(value["path"]))
        normalized.append(value)
    normalized.sort(key=lambda item: str(item["path"]))
    with _cache_lock:
        _cache = (now, normalized)
    return normalized


app = FastAPI(
    title="UDS Bundle Observatory",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):  # noqa: ANN001
    response: Response = await call_next(request)
    response.headers.update(
        {
            "Cache-Control": "no-store" if request.url.path.startswith("/api/") else "public, max-age=300",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=()",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
    )
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "uds-bundle-observatory-v2"}


@app.get("/readyz")
def readyz(response: Response) -> dict[str, Any]:
    missing = [path.relative_to(HERE).as_posix() for path in CONTROLLED if not path.is_file()]
    root = repository_root()
    if not root.is_dir():
        missing.append("BUNDLE_ROOT")
    state = "READY" if not missing else "NOT_READY"
    if missing:
        response.status_code = 503
    return {"status": state, "missing": missing, "source": source_revision()}


@app.get("/api/source")
def source() -> dict[str, Any]:
    value = {
        "schema": "szl.uds-source/v1",
        "repository": "szl-holdings/uds-bundles",
        "source": source_revision(),
        "controlled_files": controlled_hashes(),
        "bundle_root_state": "MEASURED_LOCAL_DIRECTORY" if repository_root().is_dir() else "UNAVAILABLE",
        "mutation_authority": False,
        "cluster_authority": False,
        "registry_authority": False,
        "shell_authority": False,
        "secrets_recorded": False,
    }
    value["receipt_sha256"] = receipt(value)
    return value


@app.get("/api/bundles")
def bundles() -> dict[str, Any]:
    try:
        rows = inventory()
    except ManifestError as exc:
        raise HTTPException(status_code=503, detail=str(exc)[:240]) from exc
    value = {
        "schema": "szl.uds-bundle-index/v1",
        "count": len(rows),
        "items": rows,
        "deployment": "NOT_ATTEMPTED",
        "publication": "NOT_ATTEMPTED",
    }
    value["receipt_sha256"] = receipt(value)
    return value


@app.get("/api/bundles/{artifact_id}")
def bundle(artifact_id: str) -> dict[str, Any]:
    if not ID_RE.fullmatch(artifact_id):
        raise HTTPException(status_code=404, detail="unknown bundle")
    try:
        matches = [item for item in inventory() if item["id"] == artifact_id]
    except ManifestError as exc:
        raise HTTPException(status_code=503, detail=str(exc)[:240]) from exc
    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="unknown bundle")
    value = {"schema": "szl.uds-bundle/v1", "bundle": matches[0]}
    value["receipt_sha256"] = receipt(value)
    return value


@app.post("/api/validate")
def validate(request: ValidationRequest) -> dict[str, Any]:
    try:
        parsed = parse_manifest(request.text, request.format)
        inspection = inspect_manifest(parsed)
    except ManifestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)[:240]) from exc
    value = {
        "schema": "szl.uds-validation/v1",
        "format": request.format,
        "manifest_sha256": hashlib.sha256(request.text.encode("utf-8")).hexdigest(),
        "inspection": inspection,
        "side_effects": False,
        "deployment": "NOT_ATTEMPTED",
        "publication": "NOT_ATTEMPTED",
    }
    value["receipt_sha256"] = receipt(value)
    return value


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", media_type="text/html")


@app.get("/app.js")
def javascript() -> FileResponse:
    return FileResponse(STATIC / "app.js", media_type="text/javascript")


@app.get("/styles.css")
def stylesheet() -> FileResponse:
    return FileResponse(STATIC / "styles.css", media_type="text/css")


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"status": "ERROR", "detail": exc.detail})
