#!/usr/bin/env bash
# One whole newly allocated arm, with its own adjacent memory admission.
set -eu
source_sha="$1"
arm="$2"
case "$arm" in C|F) ;; *) exit 2;; esac
output="temp/directions/acvc/exp/training_use_b02_20260912/arm_${arm}"
test ! -e "$output"
"${HMASD_PYTHON}" scripts/hmasd_resource_preflight.py admit-memory \
    --out "temp/directions/acvc/training_use_b02_${arm}_admission.json" &&
exec "${HMASD_PYTHON}" scripts/run_acvc_training_use_b02.py \
    --arm "$arm" --output "$output" --launch-sha "$source_sha" --execution-seconds 260
