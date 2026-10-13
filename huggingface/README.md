# Hugging Face dataset cards sourced from this repository

This repository is the canonical GitHub source for three Hugging Face datasets
(HF upgrade plan, P18). Each `datasets/<id>/README.md` began as a **verbatim import**
of the dated Hub revision below. Subsequent source edits are listed separately;
the import hashes preserve lineage and do not describe the current edited cards.
The original import was a read-only fetch; nothing was written to the Hub.

| Hub dataset | Card imported from Hub revision | sha256 of the imported card |
|---|---|---|
| [`SZLHOLDINGS/uds-bundles-v1`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1) | `28c14086211944cfc2ceb6ece0f729153b545575` | `3c38e90b132bca761b32b0858fae0433e4f72d81d4abca22d070e62cf1256f7e` |
| [`SZLHOLDINGS/uds-spans-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-spans-receipts) | `6573c9e3c9cf990e5975a3f19685a083bb962dd3` | `5ed3604d0e0472c8c7e05b9e0ae448722a481fda59ec3889bacb2276f702979d` |
| [`SZLHOLDINGS/uds-governance-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-governance-receipts) | `b0f2631e8f3ade758acfcd70797096bdc0c5e922` | `a3123b5b6f0e05d90c69dd24b3b5ec6bf99e604f252a61fec767eb52aa1f66e1` |

All three cards declare `license: apache-2.0`, which matches this repository's
[`LICENSE`](../LICENSE).

## Hub copies behind this source

The `uds-bundles-v1` and `uds-spans-receipts` cards have been edited here since the
imports above; `uds-governance-receipts` retains its imported bytes. These source
changes require a verified publication before Hub alignment can be claimed.

- `uds-bundles-v1`: the Hub copy is **behind** at revision `28c14086211944cfc2ceb6ece0f729153b545575`.
  The source card now states the airgap status from the dataset's own evidence
  (`AIRGAP_TEST_REPORT.md`, `GAP_CHECK.md`, `STATUS.md`): image-free proof packages only, no
  air-gapped deploy demonstrated. `tests/test_hf_dataset_cards.py` checks this.
- `uds-spans-receipts`: the Hub copy is **behind** at revision `6573c9e3c9cf990e5975a3f19685a083bb962dd3`.
  The source card now labels the `spans` and `receipts` rows as synthetic (every Hub row carries
  `synthetic: true`), adds the `synthetic` tag, and lists the fields the rows actually have.
  `tests/test_hf_dataset_cards.py` checks the card text; the JSONL payload lives only on the Hub.

## Lineage (from Hub commit history, read 2026-09-29)

- `uds-bundles-v1`: created 2026-06-01. Its payload was uploaded by a local run with a
  founder token, not by a workflow; see [`uds-bundles/HF_PUSH_LOG.md`](../uds-bundles/HF_PUSH_LOG.md).
- `uds-spans-receipts`: its history includes `sync: mirror szl-holdings/uds-mesh@08b77e4`
  (2026-05-29). `szl-holdings/uds-mesh` no longer exists.
- `uds-governance-receipts`: the HF inventory's only recorded reference to it is
  `szl-holdings/szl-uds-deployment` (`scripts/verify_signed_assets.sh`), which is archived.
- The three cards were last edited on the Hub on 2026-09-28 ("estate audit" Hub PRs); that
  content is what is imported here.

## Publishing status

The cards (only `README.md`, never the payloads) are published by
[`hf-dataset-cards-publish.yml`](../.github/workflows/hf-dataset-cards-publish.yml):

- it runs on a push to `main` that changes a card, publisher, publisher test, or workflow, and on
  `workflow_dispatch` (one dataset or all, with an optional dry run);
- it first runs `tests/test_hf_dataset_cards.py` and refuses to publish if the card claim
  checks fail or are missing;
- it uploads a card only when its bytes differ from the Hub copy, with the Hub's current head
  as the parent commit and the GitHub commit SHA in the Hub commit message;
- it verifies the checkout SHA, tracked card bytes, and current canonical `main` before
  publishing and again around each upload; a stale rerun fails instead of republishing old cards;
- it reads the card back at the new Hub revision and fails unless its sha256 equals the
  sha256 of the card in this repository and the Hub head still matches that revision;
- unchanged-card checks also re-read the Hub head; a concurrent Hub edit fails verification;
- only publication jobs share the write queue, so PR validation cannot replace a pending publish;
- it authenticates with the org-level `HF_TOKEN` secret (not `HF_ORG_TOKEN`).

The payloads are not published from here; they still come only from the uploads recorded in
the lineage above. Edit cards here, not on the Hub. If a publish run fails, note in this file
that the Hub copy is behind until a run succeeds.

The GitHub-main check and Hub compare-and-swap operate on separate services. A main
advance after the last pre-upload check can still race an upload; the post-upload check
reports failure, and the newer main run reconciles the card. A successful result is a
dated observation of the checked heads, not a permanent synchronization guarantee.
