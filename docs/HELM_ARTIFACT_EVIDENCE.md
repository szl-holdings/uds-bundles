# Helm artifact evidence

The Helm packaging workflow produces a **file-level CycloneDX 1.6 SBOM** for
the exact `.tgz` it uploads. This inventory covers packaged chart files and
their SHA-256 hashes. It does not scan container layers or establish the
dependencies of the applications referenced by the chart. Model weights,
model licenses, agent definitions, tool permissions, and runtime configuration
need a separate model/agent/tool inventory and their own digest bindings.

## Release outputs

- `<chart>.tgz`: the deployment artifact built with Helm.
- `<chart>.tgz.cdx.json`: deterministic chart-file SBOM, with the archive hash,
  repository URL, full source commit, explicit scope, and declared Apache-2.0
  repository license. This declaration does not infer runtime licenses.
- `<chart>.tgz.evidence.json`: **unsigned** manifest binding archive, SBOM,
  source commit, and the distributed LICENSE digest.
- `LICENSE` and `helm_evidence.py`: license text and standalone offline verifier.

The existing `helm-lint.yml` release package job generates and verifies all of
these before upload using its existing `contents: write` permission. It refuses
to overwrite existing assets. No signing permission, credential, registry grant,
or security setting is added. This source change does not repair past releases.

Evidence generation is byte-reproducible for identical archive bytes, source
commit, license, and artifact filename. Helm archives may contain build-time
metadata; this is not a claim of reproducible Helm archive builds. The source
commit is a build assertion, not a cryptographically authenticated derivation
of the chart. CI obtains it from the actual checkout using `git rev-parse HEAD`.

## Clean consumer, offline integrity check

Transfer the five outputs above to an empty directory with Python 3.12 available.
Obtain the expected full source commit and archive SHA-256 independently from
an approved channel; do not take trust anchors from the unsigned manifest itself.
Run from that directory (replace the example variables with those expected values):

```sh
python3 helm_evidence.py verify szl-0.1.0.tgz \
  --source-sha "$EXPECTED_SOURCE_COMMIT" \
  --artifact-sha256 "$EXPECTED_ARCHIVE_SHA256"
```

No network, checkout, third-party Python dependency, registry, or credentials
are needed. Verification recomputes the archive and every chart-file digest,
regenerates canonical evidence, and compares both sidecars byte-for-byte. It
rejects missing evidence, placeholders (including `PENDING-cosign-attest-at-build`),
digest/source/license/scope mismatches, duplicate/unsafe archive paths and links.
It never extracts archive members. Noncanonical edits fail even if JSON-equivalent.

The archive profile permits only regular files and directories under one chart
root, with a regular-file `Chart.yaml`. File/descendant collisions are rejected
in either entry order. Compressed inputs and the **entire decompressed TAR** each
have a 32 MiB limit; the latter includes metadata, headers and padding and is
checked before any TAR header parsing. At most 10,000 members are accepted.
PAX/GNU extension records (including long-name and sparse metadata), links,
devices and other entry types are unsupported and rejected, even below the size
limit. Truncated records, missing end markers and nonzero trailing data fail
closed. Charts needing unsupported extensions require a reviewed profile change.

Success means **unsigned integrity against the supplied expected values**.
Someone able to replace both artifacts and the trusted expected values can
forge this evidence. This verifier does not authenticate a publisher, validate
an attestation, validate a certificate chain, check Rekor, or award a SLSA level.

To regenerate evidence in a checkout:

```sh
mkdir -p dist
helm package charts/szl -d dist
python3 scripts/helm_evidence.py generate dist/szl-0.1.0.tgz \
  --source-sha "$(git rev-parse HEAD)"
python3 -m unittest discover -s tests -p test_helm_evidence.py -v
```

The tests create only synthetic archives, copy the standalone verifier and
license into a clean consumer directory, test repeatable output, and exercise
tampered artifacts, sidecars, expected digests, and unsafe archives.

## Signed evidence remains a separate release requirement

The historical checked-in `bundles/*/sbom` inventories and
`bundles/*/attestations` files are not inputs to this verifier. In particular,
provenance with a placeholder subject digest is not accepted release evidence.
The existing `release.yml` scans repository contents and attests the SBOM file
itself; those outputs do not authenticate this Helm archive. Likewise, a package
SBOM and a separate source-tarball attestation in an upstream a11oy release do
not establish a signed SBOM for this deployment artifact.

Before claiming signed Helm evidence for a future approved release:

1. Build and preserve the exact archive from the reviewed source commit. Capture
   the archive digest and verify the downloaded release outputs in a clean consumer.
2. Bind an actual signed SBOM attestation and build provenance to that archive
   digest, not to the SBOM file or a separately rebuilt archive. The existing
   `release.yml` job already declares `id-token: write` and `attestations: write`;
   review a follow-up that hands the exact packaged artifact to that job and
   uses established GitHub/Sigstore tooling. The package job has neither grant;
   adding them would require separately authorized permission changes. No such
   changes are needed for this unsigned implementation or performed here.
3. Preserve the actual verification bundles. Use established `gh attestation`
   or Sigstore verification tooling with the intended repository/workflow
   identity, issuer and trusted roots; require certificate-chain and Rekor
   verification where applicable. For offline verification, provision the trust
   roots and transparency-log evidence in advance. Do not bypass tlog checks or
   manufacture placeholder signatures. Verify artifact, SBOM predicate, source
   commit and builder identity, and retain a tampered-artifact rejection transcript.
4. Separately inventory and verify the pinned runtime images and model/agent/tool
   artifacts. A chart-file SBOM cannot substantiate their readiness or licenses.

References: [CycloneDX JSON specification](https://cyclonedx.org/docs/1.6/json/),
[GitHub attestation tooling](https://github.com/actions/attest), and
[GitHub CLI attestation verification](https://cli.github.com/manual/gh_attestation_verify).
