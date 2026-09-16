#!/usr/bin/env bash
# The ACVC_MATCHED_PACKAGE_COMPARISON_B01 M original: fresh admission joined by && to the exact runner under GNU time.
# Ordinary wall plans are not runtime caps. Launch only through hmasd-experiment-operator under Portfolio grant G3.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd -- "$root"
launch_sha=${1:?launch SHA required}
output=${2:?original absolute output required}
upstream=${3:?isolated on-policy source path required}
[ "$#" -eq 3 ] || { echo "usage: launch_m.sh <launch_sha> <output> <on_policy_root>" >&2; exit 2; }
HMASD_PYTHON=${HMASD_PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
mkdir -- "$output"
"$HMASD_PYTHON" scripts/hmasd_resource_preflight.py admit-memory --out "$output/admission.json" &&
exec /usr/bin/time -f 'native_wall_s=%e\npeak_rss_kib=%M\nuser_s=%U\nsystem_s=%S\nexit_code=%x' -o "$output/native_time.txt" \
    "$HMASD_PYTHON" scripts/run_acvc_matched_package_comparison_b01.py \
    --arm M --seed 28731 --launch-sha "$launch_sha" --output "$output" \
    --on-policy-root "$upstream" >"$output/stdout.log" 2>"$output/stderr.log"
