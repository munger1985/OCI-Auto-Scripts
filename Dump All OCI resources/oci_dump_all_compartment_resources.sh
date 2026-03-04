#!/usr/bin/env bash
set -euo pipefail

# NOTE:
# If you see errors like "syntax error: unexpected end of file", it's often because the file
# was edited/saved with Windows CRLF or a wrong encoding on some systems.
# To normalize on Linux:
#   sed -i 's/\r$//' oci_dump_all_compartment_resources.sh

# Dump all resources across ALL compartments in a tenancy (or a specified root compartment)
# by using OCI Search structured-search and paginating results.
#
# Prereqs:
#   - oci cli configured (profile/region)
#   - jq installed
#   - policy allows: inspect compartments, read/inspect resources via search

export OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING=True

# ==================== [Edit here if needed] ====================
# Root compartment to start from.
# - If you want the whole tenancy, keep it as the tenancy OCID.
# - If you want only a subtree, set it to that compartment OCID (will include all descendants).
# ROOT_COMPARTMENT_OCID="ocid1.tenancy.oc1..aaaaaaaaaxpdh4jwbujm65yzxdblsi4la"
ROOT_COMPARTMENT_OCID="ocid1.compartment.oc1..aaaaaaaa67aj6v3kzx4x7vo6xtfdipk7fp4g2sp7rf4a7q"
# Optional: OCI CLI profile
OCI_PROFILE="${OCI_PROFILE:-DEFAULT}"

# Output
OUTPUT_FILE="full_subtree_resources.json"

# ==============================================================

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: missing command: $1" >&2
    exit 1
  }
}

need_cmd oci
need_cmd jq

echo "[]" > "${OUTPUT_FILE}"

echo "🔎 Collecting compartments under: ${ROOT_COMPARTMENT_OCID}"

# If ROOT is tenancy OCID, search the full subtree. If ROOT is a compartment OCID, use only direct children.
if [[ "${ROOT_COMPARTMENT_OCID}" == ocid1.tenancy.* ]]; then
  COMPARTMENT_ID_IN_SUBTREE=true
else
  COMPARTMENT_ID_IN_SUBTREE=false
fi
echo "ℹ️  --compartment-id-in-subtree: ${COMPARTMENT_ID_IN_SUBTREE}"

# Get ALL descendant compartments (multi-level) using compartment list with --compartment-id-in-subtree true.
# Include ROOT itself in the final list.
ALL_COMPARTMENTS_JSON=$(oci iam compartment list \
  --profile "${OCI_PROFILE}" \
  --compartment-id "${ROOT_COMPARTMENT_OCID}" \
  --compartment-id-in-subtree "${COMPARTMENT_ID_IN_SUBTREE}" \
  --access-level ANY \
  --all \
  --output json)

# Build a newline-separated list of compartment OCIDs (including ROOT itself)
COMPARTMENT_IDS=$(jq -r --arg root "${ROOT_COMPARTMENT_OCID}" '
  ([ $root ] + (.data | map(.id)))
  | unique
  | .[]
' <<<"${ALL_COMPARTMENTS_JSON}" | tr -d '\r')

COMP_COUNT=$(wc -l <<<"${COMPARTMENT_IDS}" | tr -d ' ')
echo "✅ Total compartments in scope (including root): ${COMP_COUNT}"

# NOTE: We do NOT use "IN (...)" because it may fail to parse for large lists.
# We will query one compartment at a time and merge results.

TEMP_FILE="temp_page.json"
PAGE=""
TOTAL=0

echo "🚀 Start paging structured-search..."

idx=0
while IFS= read -r CID; do
  idx=$((idx + 1))
  echo "\n=== [${idx}/${COMP_COUNT}] Searching compartment: ${CID} ==="
  QUERY_TEXT="query all resources where compartmentId = '${CID}' && lifecycleState != 'TERMINATED'"
  PAGE=""

  while true; do
    # We keep full JSON output because next-page token is in response headers-like field "opc-next-page".
    oci search resource structured-search \
      --profile "${OCI_PROFILE}" \
      --query-text "${QUERY_TEXT}" \
      --limit 1000 \
      ${PAGE:+--page "${PAGE}"} \
      --output json > "${TEMP_FILE}"
    PAGE_ITEMS=$(jq '.data.items | length' "${TEMP_FILE}")
    TOTAL=$((TOTAL + PAGE_ITEMS))
    echo "✅ Page items: ${PAGE_ITEMS}, running total: ${TOTAL}"

    # Append items into OUTPUT_FILE array
    # Avoid process substitution <( ) because some environments (/proc restrictions) may break it.
    PAGE_ITEMS_FILE="${TEMP_FILE}.items"
    jq '.data.items' "${TEMP_FILE}" > "${PAGE_ITEMS_FILE}"
    jq -s '.[0] + .[1]' "${OUTPUT_FILE}" "${PAGE_ITEMS_FILE}" > "${OUTPUT_FILE}.tmp"
    mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}"
    rm -f "${PAGE_ITEMS_FILE}"

    PAGE=$(jq -r '."opc-next-page" // empty' "${TEMP_FILE}")
    if [[ -z "${PAGE}" || "${PAGE}" == "null" ]]; then
      break
    fi
  done
done <<<"${COMPARTMENT_IDS}"

rm -f "${TEMP_FILE}"

echo "🎉 Done. Total resources: ${TOTAL}" 
echo "📄 Saved to: ${OUTPUT_FILE}" 
ls -lh "${OUTPUT_FILE}"

exit 0
