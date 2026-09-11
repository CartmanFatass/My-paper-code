#!/usr/bin/env bash
# One fresh DENSE fit and three final panels; called inside the whole-task timer.
set -eu
source_sha="$1"
output="temp/directions/acvc/exp/fresh_dense_reuse_b01_8931_20260910"
"${HMASD_PYTHON}" scripts/hmasd_resource_preflight.py admit-memory \
    --out temp/directions/acvc/fresh_dense_reuse_b01_8931_admission.json &&
exec "${HMASD_PYTHON}" scripts/run_acvc_fresh_dense_reuse_b01.py \
    --seed 8931 --output "$output" --launch-sha "$source_sha" --execution-seconds 260
