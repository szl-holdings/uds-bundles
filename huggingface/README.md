# Hugging Face dataset cards sourced from this repository

This repository is the canonical GitHub source for three Hugging Face datasets
(HF upgrade plan, P18). Each `datasets/<id>/README.md` below is a **verbatim import**
of that dataset's current Hub card, so GitHub holds the card before any mirror
publishes it. The import was a read-only fetch; nothing was written to the Hub.

| Hub dataset | Card imported from Hub revision | sha256 of the imported card |
|---|---|---|
| [`SZLHOLDINGS/uds-bundles-v1`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1) | `28c14086211944cfc2ceb6ece0f729153b545575` | `3c38e90b132bca761b32b0858fae0433e4f72d81d4abca22d070e62cf1256f7e` |
| [`SZLHOLDINGS/uds-spans-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-spans-receipts) | `6573c9e3c9cf990e5975a3f19685a083bb962dd3` | `5ed3604d0e0472c8c7e05b9e0ae448722a481fda59ec3889bacb2276f702979d` |
| [`SZLHOLDINGS/uds-governance-receipts`](https://huggingface.co/datasets/SZLHOLDINGS/uds-governance-receipts) | `b0f2631e8f3ade758acfcd70797096bdc0c5e922` | `a3123b5b6f0e05d90c69dd24b3b5ec6bf99e604f252a61fec767eb52aa1f66e1` |

All three cards declare `license: apache-2.0`, which matches this repository's
[`LICENSE`](../LICENSE).

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

No workflow publishes these cards or payloads yet. Two things are missing:

1. the org-level `reusable-hf-mirror.yml` in `szl-holdings/.github` (not yet present), and
2. a Hugging Face credential in this repository: an `HF_TOKEN` scoped to these three
   datasets, or a Hugging Face Trusted Publisher bound to this repository.

Until then, edit a card here and in the same change note that the Hub copy is behind. Do not
edit the cards on the Hub.
