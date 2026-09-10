#!/usr/bin/env bash
# One P79 invocation in its detached exact-source checkout.
set -u
sha="$1"
checkpoint="$2"
check_wall="$3"
process_cap="$4"
output="temp/directions/acvc/exp/native_link_loss_b02_8902_p79_20260909"
"${HMASD_PYTHON}" scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/acvc/p79_admission.json &&
mkdir -p "$output" &&
/usr/bin/time -f 'process_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x' -o "$output/process_time.txt" \
    timeout --signal=TERM --kill-after=5 "$process_cap" "${HMASD_PYTHON}" scripts/run_acvc_native_link_loss_b01.py \
    --seed 8902 --checkpoint "$checkpoint" --output "$output" --launch-sha "$sha" \
    --focused-check-wall-s "$check_wall"
