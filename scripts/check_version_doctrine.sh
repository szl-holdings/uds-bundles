#!/usr/bin/env bash
# check_version_doctrine.sh — UDS version-string doctrine check ("make doctrine"-style).
#
# Asserts that NEW / aggregation UDS ecosystem version strings agree on ONE canonical
# version (the contents of ./VERSION, e.g. uds-v0.4.0).
#
# SCOPE: this check polices ONLY the ecosystem version token form `uds-vX.Y.Z`.
# It deliberately ignores bare semver tokens (e.g. tool/chart/dependency versions
# like v0.51.0, v26.1.5, 0.2.0 Helm chart versions) — those are NOT the ecosystem
# version string and have their own upstream lifecycles.
#
# FORWARD-ONLY HONESTY (HARD RULE): already-SIGNED artifacts are NEVER renamed.
#   * uds-v0.2.0  — the cosign-signed, Rekor-anchored flagship organ images
#                   (a11oy/sentra/amaru/rosie/killinchu). Renaming = broken signatures.
#   * uds-v0.1.0  — the signed v0.1.0 Zarf package release (releases/v0.1.0/).
#   * uds-v1.0.0  — the signed szl-warhacker release (releases/szl-warhacker-uds-v1.0.0/).
#   * uds-v0.3.0  — the signed capstone tag documented in BFT_SINGLE_SIGNER_CAVEAT.md
#                   ("uds-v0.3.0 tag signed") and the DEPRECATED.md honest-named roadmap.
# Additionally, uds-v0.3.1 survives ONLY as the DEFERRED szl-receipts-server image tag
# (ghcr.io/szl-holdings/szl-receipts-server:uds-v0.3.1) — a specific not-yet-published
# component reference, NOT the ecosystem aggregation version. Lines that pair the token
# with `szl-receipts` are therefore permitted.
# These are historical signed bytes, ALLOWLISTED below. We cut NEW versioned releases
# forward; we do not re-tag signed bytes.
#
# SUPERSEDED (documented in DEPRECATED.md): the uds-v0.3.0 / uds-v0.3.1 PER_BUNDLE
# plan structure and the UDS_v0.3.1_RELEASE_PLAN.md are SUPERSEDED by uds-v0.4.0.
# They are retained as historical record but carry a SUPERSEDED banner; their paths
# are listed in the SUPERSEDED_PATHS allowlist so the check passes while the record
# is preserved (forward-only — we never silently rewrite history).
#
# Usage: bash scripts/check_version_doctrine.sh
# Exit:  0 = no unexpected drift,  1 = drift found.

set -euo pipefail
cd "$(dirname "$0")/.."

CANONICAL="$(tr -d '[:space:]' < VERSION)"
echo "=== UDS version doctrine check (uds-v* ecosystem tokens) ==="
echo "Canonical (VERSION): $CANONICAL"

# Signed / historical byte-stable ecosystem tags that MUST NOT be renamed.
ALLOWLIST_REGEX='^(uds-v0\.2\.0|uds-v0\.1\.0|uds-v1\.0\.0|uds-v0\.3\.0)$'

# Superseded legacy plan paths (retained with a SUPERSEDED banner; see DEPRECATED.md).
SUPERSEDED_PATHS_REGEX='uds-bundles/PER_BUNDLE/|uds-bundles/INVENTORY\.md|uds-bundles/FOUNDER_DEPLOY_QUICKSTART\.md|uds-bundles/AIRGAP_TEST_REPORT\.md|mesh/docs/UDS_v0\.3\.1_RELEASE_PLAN\.md'

DRIFT=0
while IFS= read -r -d '' f; do
  # Skip signed-artifact trees entirely.
  case "$f" in
    *./releases/*|*/attestations/*|*./bundles/v0.1.0/*|*./uds-bundles/artifacts/*|*/.git/*) continue ;;
  esac
  hits=$(grep -oE 'uds-v[0-9]+\.[0-9]+\.[0-9]+' "$f" 2>/dev/null | sort -u || true)
  [ -z "$hits" ] && continue
  while IFS= read -r tok; do
    [ -z "$tok" ] && continue
    [ "$tok" = "$CANONICAL" ] && continue
    echo "$tok" | grep -qE "$ALLOWLIST_REGEX" && continue
    # Superseded legacy plan files are allowed to retain historical version strings.
    echo "$f" | grep -qE "$SUPERSEDED_PATHS_REGEX" && continue
    # The DEFERRED szl-receipts-server:uds-v0.3.1 image tag is a specific component
    # reference, not ecosystem drift — permit lines that mention szl-receipts.
    if [ "$tok" = "uds-v0.3.1" ] && grep -q 'szl-receipts' "$f"; then continue; fi
    # BFT caveat doc references uds-v0.3.1 as the planned caveat-doc PR target — permit.
    case "$f" in *BFT_SINGLE_SIGNER_CAVEAT.md) [ "$tok" = "uds-v0.3.1" ] && continue ;; esac
    echo "  DRIFT: $f -> $tok (expected $CANONICAL or an allowlisted signed/superseded tag)"
    DRIFT=$((DRIFT+1))
  done <<< "$hits"
done < <(find . \( -name '*.md' -o -name '*.yaml' -o -name '*.yml' -o -name '*.cff' \) -type f -print0)

echo ""
if [ "$DRIFT" -eq 0 ]; then
  echo "=== RESULT: PASS — no unexpected uds-v* drift (canonical=$CANONICAL) ==="
  echo "Signed tags allowlisted: uds-v0.2.0, uds-v0.1.0, uds-v1.0.0 (forward-only, never renamed)."
  exit 0
else
  echo "=== RESULT: FAIL — $DRIFT unexpected uds-v* version disagreement(s) ==="
  echo "Fix: bump stale strings to $CANONICAL (forward-only). NEVER rename signed artifacts."
  exit 1
fi
