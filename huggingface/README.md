# Hugging Face dataset cards sourced from this repository

This repository is the canonical GitHub source for three Hugging Face datasets
(HF upgrade plan, P18). Each `datasets/<id>/README.md` below started as a **verbatim
import** of that dataset's Hub card, so GitHub holds the card before any mirror
publishes it. The import was a read-only fetch; nothing was written to the Hub.

The table records the imported bytes, not the current source. The
`uds-governance-receipts` card is still byte-identical to its import. The `uds-bundles-v1`
and `uds-spans-receipts` cards have been edited here since; see the next section.

| Hub dataset | Card imported from Hub revision | sha256 of the imported card |
|---|---|---|
| [`SZLHOLDINGS/uds-bundles-v1`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1) | `28c14086211944cfc2ceb6ece0f729153b545575` | `3c38e90b132bca761b32b0858fae0433e4f72d81d4abca22d070e62cf1256f7e` |
| [`SZLHOLDINGS/uds-spans-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-spans-receipts) | `6573c9e3c9cf990e5975a3f19685a083bb962dd3` | `5ed3604d0e0472c8c7e05b9e0ae448722a481fda59ec3889bacb2276f702979d` |
| [`SZLHOLDINGS/uds-governance-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-governance-receipts) | `b0f2631e8f3ade758acfcd70797096bdc0c5e922` | `a3123b5b6f0e05d90c69dd24b3b5ec6bf99e604f252a61fec767eb52aa1f66e1` |

All three cards declare `license: apache-2.0`, which matches this repository's
[`LICENSE`](../LICENSE).

## Hub copies behind this source

Two cards have been edited here since the import above, so for these two the table
describes the imported bytes, not the current source. Each Hub copy stays behind until a
publish lane runs. `uds-governance-receipts` has not been edited and still matches the table.

- `uds-bundles-v1`: the Hub copy is **behind** at revision `28c14086211944cfc2ceb6ece0f729153b545575`.
  The source card now states the airgap status from the dataset's own evidence
  (`AIRGAP_TEST_REPORT.md`, `GAP_CHECK.md`, `STATUS.md`): image-free proof packages only, no
  air-gapped deploy demonstrated. It lists the five proof packages with the sha256 values in
  `uds-bundles/artifacts/SHA256SUMS_PROOF.txt`, names their signer as the uds-bundles key
  (`daa4aeca…7cb40b`, `bundles/v0.1.0/cosign_signing_key.pub`) rather than the org receipts
  key, limits the deploy preview to the one recorded run (`a11oy-runtime-proof` 0.3.1,
  cancelled before deployment), and admits a future air-gap claim only with a proof receipt
  whose package name, version and sha256 match each claimed package.
  `tests/test_hf_dataset_cards.py` checks all of this against the repository's evidence.
- `uds-spans-receipts`: the Hub copy is **behind** at revision `6573c9e3c9cf990e5975a3f19685a083bb962dd3`.
  The source card now labels the `spans` and `receipts` rows as synthetic (every Hub row carries
  `synthetic: true`), adds the `synthetic` tag, and lists the fields the rows actually have.
  `tests/test_hf_dataset_cards.py` checks the card text; the JSONL payload lives only on the Hub.

## Lineage (from Hub commit history, read 2026-09-29)

- `uds-bundles-v1`: created 2026-06-01. Its first payload upload was a local run with a
  founder token, not a workflow; see [`uds-bundles/HF_PUSH_LOG.md`](../uds-bundles/HF_PUSH_LOG.md).
  That log records only the first upload (Hub commit `bcfd121a0e56969c48a09045c282508d46fd0d81`,
  09:13 UTC), which excluded `artifacts/*`. Hub commit `ab5cc3ff7977b06083bc8114de0b79f419112d7c`
  (09:24 UTC the same day) added `uds_productionization/artifacts/`, including the five proof
  `.tar.zst` packages; no file in this repository records how that upload was made. A read-only
  listing on 2026-10-13 of Hub revision `28c14086211944cfc2ceb6ece0f729153b545575` showed the five
  packages with LFS sha256 object ids equal to `uds-bundles/artifacts/SHA256SUMS_PROOF.txt`.
- `uds-spans-receipts`: its history includes `sync: mirror szl-holdings/uds-mesh@08b77e4`
  (2026-05-29). `szl-holdings/uds-mesh` no longer exists.
- `uds-governance-receipts`: the HF inventory's only recorded reference to it is
  `szl-holdings/szl-uds-deployment` (`scripts/verify_signed_assets.sh`), which is archived.
- The three cards were last edited on the Hub on 2026-09-28 ("estate audit" Hub PRs); that
  content is what is imported here.

## Publishing status

No workflow publishes these cards or payloads yet. Two things are missing:

1. the org-level `reusable-hf-mirror.yml` in `szl-holdings/.github` (not yet present), and
2. a Hugging Face credential in this repository: an `HF_TOKEN` scoped to these three
   datasets, or a Hugging Face Trusted Publisher bound to this repository.

Until then, edit a card here and in the same change note that the Hub copy is behind. Do not
edit the cards on the Hub.
