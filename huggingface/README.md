# Hugging Face dataset cards sourced from this repository

This repository is the canonical GitHub source for three Hugging Face datasets
(HF upgrade plan, P18). Each `datasets/<id>/README.md` began as a **verbatim import** of a
Hub card (see Lineage). The table below records, for each dataset, the Hub revision whose
`README.md` was last confirmed and the sha256 of that Hub card. It was read on 2026-10-13
with read-only Hub API calls, after card-lane publish run
[38432684574](https://github.com/szl-holdings/uds-bundles/actions/runs/38432684574): each
listed revision's `README.md` blob id equals the source card at `main`
`3a61e65fc5456ba46561f73614de914744614d8e`.

| Hub dataset | Hub card revision (read 2026-10-13) | sha256 of the Hub card at that revision |
|---|---|---|
| [`SZLHOLDINGS/uds-bundles-v1`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1) | `004670e9e87b8958cb81544a01b2bf1c9058a7b8` | `fd7adc3f6279ce4c883a000e725e399ea369cf78b11458d55384b4137325614f` |
| [`SZLHOLDINGS/uds-spans-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-spans-receipts) | `310d53fd9781a6f50f19d13c77c2736944ce3022` | `8a36efbb2b3037378203356d869b1979223eee5765d2708b3203c5877749bb5f` |
| [`SZLHOLDINGS/uds-governance-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-governance-receipts) | `b0f2631e8f3ade758acfcd70797096bdc0c5e922` | `a3123b5b6f0e05d90c69dd24b3b5ec6bf99e604f252a61fec767eb52aa1f66e1` |

All three cards declare `license: apache-2.0`, which matches this repository's
[`LICENSE`](../LICENSE).

## Hub copies behind this source

`uds-spans-receipts` and `uds-governance-receipts` match the table. A card listed below has
been edited here since its table revision; its Hub copy stays behind until the card lane
publishes it. After that run, set the row to the new Hub revision and card sha256 and remove
the note in the same change. `tests/test_hf_dataset_cards.py` checks that these notes agree
with the card bytes.

- `uds-bundles-v1`: the Hub copy is **behind** at revision `004670e9e87b8958cb81544a01b2bf1c9058a7b8`.
  The source card adds the five proof packages with their sha256 values and cites the Hub
  commit that added them (see Lineage). `tests/test_hf_dataset_cards.py` checks the package
  table against `uds-bundles/artifacts/SHA256SUMS_PROOF.txt` and the committed files.

## Lineage (from Hub commit history, read 2026-09-29)

- `uds-bundles-v1`: created 2026-06-01. Its first payload upload was a local run with a
  founder token, not a workflow; see [`uds-bundles/HF_PUSH_LOG.md`](../uds-bundles/HF_PUSH_LOG.md).
  That log records only that upload (Hub commit `bcfd121a0e56969c48a09045c282508d46fd0d81`,
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
  content is what was originally imported here: revisions `28c14086211944cfc2ceb6ece0f729153b545575`
  (`uds-bundles-v1`, card sha256 `3c38e90b132bca761b32b0858fae0433e4f72d81d4abca22d070e62cf1256f7e`),
  `6573c9e3c9cf990e5975a3f19685a083bb962dd3` (`uds-spans-receipts`,
  `5ed3604d0e0472c8c7e05b9e0ae448722a481fda59ec3889bacb2276f702979d`) and
  `b0f2631e8f3ade758acfcd70797096bdc0c5e922` (`uds-governance-receipts`,
  `a3123b5b6f0e05d90c69dd24b3b5ec6bf99e604f252a61fec767eb52aa1f66e1`).
- 2026-10-13: card-lane run 38432684574 (source `3a61e65fc5456ba46561f73614de914744614d8e`)
  uploaded the edited `uds-bundles-v1` and `uds-spans-receipts` cards as Hub revisions
  `004670e9e87b8958cb81544a01b2bf1c9058a7b8` and `310d53fd9781a6f50f19d13c77c2736944ce3022`
  (`README.md` only; payloads unchanged). `uds-governance-receipts` was unchanged.

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
