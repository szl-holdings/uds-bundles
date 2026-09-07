# UDS Bundle Observatory

## Purpose

The observatory is the read-only inspection surface for repository-owned UDS and Zarf manifests. It exposes source identity, local bundle inventory, bounded validation, structural findings, and deterministic receipts without acquiring deployment authority.

It is a capability surfaced through SZL Atelier and SZL Constellation. It is not a peer commercial flagship, an OCI publisher, a cluster operator, or a replacement for the source repository.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-observatory.txt
SOURCE_REVISION="$(git rev-parse HEAD)" uvicorn observatory.app:app --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860` and inspect the API contract at `/api/docs`.

## API

| Route | Authority | Result |
|---|---|---|
| `GET /healthz` | local read | process liveness |
| `GET /readyz` | local read | repository/static readiness |
| `GET /api/source` | local read | exact controlled-file hashes and source revision |
| `GET /api/bundles` | local read | bounded repository manifest catalog |
| `GET /api/bundles/{slug}` | local read | parsed source-owned manifest and findings |
| `POST /api/validate` | bounded computation | deterministic validation receipt for supplied text |
| `GET /deployment.json` | local read | runtime identity without a Hub-success claim |

## Security and truth boundary

The service deliberately contains no code path for:

- Kubernetes or cluster writes;
- Zarf package deployment;
- OCI or container-registry publication;
- shell or subprocess execution;
- arbitrary URL retrieval;
- credential handling;
- signature-success inference from a declared field;
- repository or Hugging Face mutation.

A manifest checksum or signature field is **DECLARED** evidence unless a separate trusted verifier produces a measured receipt. This service reports signature verification as `UNAVAILABLE_NOT_ATTEMPTED`.

## Input limits

- request body: 131,072 UTF-8 bytes;
- repository manifest: 524,288 bytes;
- repository inventory: at most 300 manifests;
- nested object depth: 32;
- YAML alias events: 32;
- duplicate JSON/YAML keys: rejected;
- non-finite JSON numbers: rejected.

## Publication

GitHub is canonical. Any Hugging Face presentation must be generated from an exact protected-main revision by one canonical publisher and must independently read back:

1. Hub commit;
2. controlled file bytes;
3. Space readiness;
4. `/deployment.json` source revision.

A GitHub merge is not a Hub publication, and a Hub commit is not runtime readiness.
