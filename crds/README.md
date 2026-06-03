# SZL K8s-Native Governance CRDs (`szl.dev/v1alpha1`)

**Doctrine v11 LOCKED 749/14/163 · Λ Conjecture 1 (NOT a theorem) · SLSA L1 honest · NO HALLUCINATION**

This directory expresses the three things SZL governance actually does — **gate, prove, lock** — as
first-class Kubernetes objects, the same way sigstore expresses image policy as `ClusterImagePolicy`.
Source design: `SZL_K8S_NATIVE_PATTERNS.md`.

| CRD | Scope | What it does | Compiles / verifies via |
|---|---|---|---|
| **LambdaGate** (`lambdagate-crd.yaml`) | Cluster | Fail-CLOSED Λ-axis gate at admission | Renders a `ValidatingAdmissionPolicy` + Binding (K8s VAP GA v1.30, in-API-server) |
| **KhipuReceipt** (`khipureceipt-crd.yaml`) | Namespaced | DSSE-signed decision receipt as cluster state | cosign v3 + in-toto v1.2.0 DSSE; SHA-256 receipt chain |
| **DoctrineLock** (`doctrinelock-crd.yaml`) | Cluster | Tamper-resistant `749/14/163` constant, parameterizes every gate | Founder-DSSE-signed change control (HNC enforced-label pattern) |

## Composition

```
DoctrineLock (749/14/163, founder-signed)
        │  paramRef
        ▼
   LambdaGate (Λ-axis, failClosed) ──compiles──▶ ValidatingAdmissionPolicy + Binding (fail-CLOSED)
        │  requires label dsse-receipt=required
        ▼
   Pod admitted ONLY IF it will emit a ──▶ KhipuReceipt (DSSE-signed, cosign-verified, chained)
                                              └─ kubectl get khipureceipts  (auditor-queryable)
```

These ride **beside** UDS Core's `uds.dev/Package` (kept for compatibility) and sigstore's
`ClusterImagePolicy` (image-layer). Our CRDs govern the **decision layer** the package/image layers
don't touch: *Fleet signs the package; we sign the decision.*

## Samples

`samples/lambdagate-sample.yaml`, `samples/khipureceipt-sample.yaml`, `samples/doctrinelock-sample.yaml`.

## Honest status

These CRDs are a **design** grounded in GA upstream primitives (VAP, CRD machinery, cosign v3,
in-toto DSSE). They are **not yet implemented** — do not claim them "live" until the operator image
builds, deploys, and `kubectl get` returns the objects with verifying status. Λ stays **Conjecture 1**;
SLSA stays **L1 honest**; Doctrine **v11 LOCKED 749/14/163**. Built on Apache-2.0/MIT upstreams only —
the `uds.dev` interop is an API *shape*, not copied code. **No GPL/AGPL source.**

## Upstream references

- ValidatingAdmissionPolicy: https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/
- sigstore policy-controller: https://docs.sigstore.dev/policy-controller/overview/
- in-toto attestation: https://github.com/in-toto/attestation/releases
- HNC enforced-label pattern: https://blog.sighup.io/an-introduction-to-hierarchical-namespace-controller-hnc/
