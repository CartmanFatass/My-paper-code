#!/usr/bin/env bash
# One complete C01 unit inside its existing whole-command timer.
set -eu
source_sha="$1"
master="$2"
output="temp/directions/acvc/exp/fresh_dense_package_c01_20260911/unit_${master}"
"${HMASD_PYTHON}" scripts/hmasd_resource_preflight.py admit-memory \
    --out "temp/directions/acvc/fresh_dense_package_c01_${master}_admission.json" &&
exec "${HMASD_PYTHON}" scripts/run_acvc_fresh_dense_package_c01.py \
    --seed "$master" --output "$output" --launch-sha "$source_sha" --execution-seconds 260
