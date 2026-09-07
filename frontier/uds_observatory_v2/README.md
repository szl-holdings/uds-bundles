# UDS Bundle Observatory v2

A source-owned, read-only inspection service for UDS and Zarf bundle definitions in `szl-holdings/uds-bundles`.

The observatory validates and describes local source. It does not deploy a package, contact a cluster, push an image, publish an OCI artifact, invoke a shell, or claim that a declared checksum or signature has been independently verified.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r frontier/uds_observatory_v2/requirements.txt
SOURCE_REVISION="$(git rev-parse HEAD)" \
BUNDLE_ROOT="$PWD" \
  python -m uvicorn app:app --app-dir frontier/uds_observatory_v2 --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860`.

## API

| Route | Purpose |
|---|---|
| `GET /healthz` | Process liveness only |
| `GET /readyz` | Controlled-file and local bundle-root readiness |
| `GET /api/source` | Source revision, controlled-file commitments, and authority flags |
| `GET /api/bundles` | Bounded inventory of recognized local manifest files |
| `GET /api/bundles/{id}` | One exact inventory item by derived 16-character ID |
| `POST /api/validate` | Parse and inspect bounded YAML or JSON text without side effects |

## Parser bounds

- maximum submitted manifest: 128 KiB;
- maximum repository manifest: 256 KiB;
- maximum nesting depth: 32;
- maximum YAML aliases: 24;
- maximum repository manifest files: 200;
- maximum sequence or mapping size: 1,000;
- duplicate YAML and JSON keys rejected;
- non-finite JSON values rejected;
- root must be a mapping/object;
- only recognized local filename shapes are inventoried.

## Evidence semantics

- `DECLARED`: present in the source manifest and structurally recognized.
- `INVALID`: outside a parser or reference-shape boundary.
- `UNAVAILABLE_NOT_VERIFIED`: no independent signature proof was performed.
- `DECLARED_ONLY`: a checksum declaration was observed; bytes were not independently pulled and measured.
- `NOT_ATTEMPTED`: deployment or publication was not performed.

## Container

```bash
docker build -f frontier/uds_observatory_v2/Dockerfile -t uds-observatory-v2 .
docker run --rm -p 7860:7860 -e SOURCE_REVISION="$(git rev-parse HEAD)" uds-observatory-v2
```

The image runs as UID/GID `10002:10002`. The repository is copied into `/workspace` for read-only application behavior; the service exposes no filesystem mutation API.

## Test

```bash
python -m pytest -q frontier/uds_observatory_v2/tests
```

## State boundary

```text
DECLARED != MEASURED != VERIFIED != DEPLOYED
SOURCE_PR != MERGED != HUB_PUBLISHED != RUNTIME_READY != EXACT_READBACK_VERIFIED
```
