#!/usr/bin/env bash
# One B02 invocation with fresh adjacent admission on the actual execution node.
set -eu
source_sha="$1"
output="temp/directions/acvc/exp/cluster_deployment_b02_20260913"
test ! -e "$output"
"${HMASD_PYTHON}" scripts/hmasd_resource_preflight.py admit-memory \
    --out "temp/directions/acvc/cluster_deployment_b02_admission.json" &&
exec "${HMASD_PYTHON}" scripts/run_acvc_cluster_deployment_b02.py \
    --seed 21493 --output "$output" --launch-sha "$source_sha" --execution-seconds 580
