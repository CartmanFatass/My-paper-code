#!/usr/bin/env bash
# One whole K invocation, with fresh adjacent actual-node memory admission.
set -eu
source_sha="$1"
output="temp/directions/acvc/exp/cluster_deployment_b01_20260912"
test ! -e "$output"
"${HMASD_PYTHON}" scripts/hmasd_resource_preflight.py admit-memory \
    --out "temp/directions/acvc/cluster_deployment_b01_admission.json" &&
exec "${HMASD_PYTHON}" scripts/run_acvc_cluster_deployment_b01.py \
    --seed 21457 --output "$output" --launch-sha "$source_sha" --execution-seconds 580
