"""Read-only FastAPI surface for inspecting local UDS/Zarf bundle manifests."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .catalog import catalog_payload, controlled_hashes, discover_bundles
from .config import MAX_MANIFEST_BYTES, SLUG_RE
from .parsing import validate_manifest


class ValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    manifest: str = Field(min_length=1, max_length=MAX_MANIFEST_BYTES)
    filename: str = Field(default="manifest.yaml", min_length=1, max_length=128)


def create_app(repo_root: Path | None = None) -> FastAPI:
    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    static_root = Path(__file__).resolve().parent / "static"
    application = FastAPI(
        title="UDS Bundle Observatory",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if (
            content_length
            and content_length.isdigit()
            and int(content_length) > MAX_MANIFEST_BYTES + 4096
        ):
            response = JSONResponse(
                status_code=413,
                content={"detail": "REQUEST_TOO_LARGE"},
            )
        else:
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'none'; connect-src 'self'; "
            "font-src 'self'; frame-ancestors 'self' https://huggingface.co "
            "https://*.huggingface.co; img-src 'self' data:; "
            "object-src 'none'; script-src 'self'; style-src 'self'"
        )
        response.headers["Cache-Control"] = (
            "no-store"
            if request.url.path.startswith("/api/")
            or request.url.path in {"/healthz", "/readyz"}
            else "public, max-age=300"
        )
        response.headers["X-SZL-Authority"] = "read-only-observatory"
        return response

    @application.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "uds-bundle-observatory",
            "mutation_authority": False,
        }

    @application.get("/readyz")
    def readyz():
        required = [
            static_root / "index.html",
            static_root / "app.js",
            static_root / "styles.css",
            static_root / "responsive.css",
        ]
        missing = [path.name for path in required if not path.is_file()]
        return JSONResponse(
            status_code=200 if not missing else 503,
            content={
                "status": "ready" if not missing else "not_ready",
                "missing": missing,
                "bundle_count": len(discover_bundles(root)),
            },
        )

    @application.get("/api/source")
    def source() -> dict[str, Any]:
        revision = (
            os.getenv("SOURCE_REVISION")
            or os.getenv("GITHUB_SHA")
            or os.getenv("SPACE_COMMIT_SHA")
        )
        return {
            "schema": "szl.source-identity/v1",
            "repository": "szl-holdings/uds-bundles",
            "revision": revision,
            "revision_state": "MEASURED_ENVIRONMENT" if revision else "UNAVAILABLE",
            "controlled_files_sha256": controlled_hashes(root),
            "provider_head": "UNAVAILABLE_REQUIRES_EXTERNAL_READBACK",
            "hub_publication": "UNAVAILABLE_REQUIRES_EXTERNAL_READBACK",
            "runtime_source_match": "UNAVAILABLE_REQUIRES_EXTERNAL_READBACK",
        }

    @application.get("/api/bundles")
    def bundles() -> dict[str, Any]:
        return catalog_payload(root)

    @application.get("/api/bundles/{slug}")
    def bundle(slug: str) -> dict[str, Any]:
        if not SLUG_RE.fullmatch(slug):
            raise HTTPException(status_code=404, detail="BUNDLE_NOT_FOUND")
        item = next(
            (row for row in discover_bundles(root) if row["slug"] == slug),
            None,
        )
        if item is None:
            raise HTTPException(status_code=404, detail="BUNDLE_NOT_FOUND")
        return item

    @application.post("/api/validate")
    def validate(request: ValidationRequest = Body(...)) -> dict[str, Any]:
        try:
            return validate_manifest(request.manifest, request.filename)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)[:400]) from exc

    @application.get("/")
    def index():
        return FileResponse(static_root / "index.html")

    @application.get("/{asset_name}", include_in_schema=False)
    def asset(asset_name: str):
        allowed = {
            "app.js": "application/javascript",
            "styles.css": "text/css",
            "responsive.css": "text/css",
        }
        media_type = allowed.get(asset_name)
        if media_type is None:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return FileResponse(static_root / asset_name, media_type=media_type)

    return application


app = create_app()
