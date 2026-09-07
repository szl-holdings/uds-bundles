# UDS Bundle Observatory

A bounded, read-only FastAPI and local-static inspection surface for the repository-owned UDS and Zarf bundle manifests.

## Run

```bash
python -m pip install -r observatory/requirements.txt -r observatory/requirements-dev.txt
uvicorn observatory.app:app --host 127.0.0.1 --port 7860
pytest -q observatory/tests
```

## Authority boundary

The service discovers and parses local manifests. It cannot deploy packages, contact a Kubernetes cluster, push OCI artifacts, sign bundles, execute shell commands, or mutate repository content. `DECLARED` digests and signature references are never represented as independently measured verification.
