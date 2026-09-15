#!/usr/bin/env bash
# One block-2 original through the identity-binding wrapper; same elements as launch.sh (block 1).
# Ordinary wall plans are not runtime caps.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd -- "$root"
launch_sha=${1:?launch SHA required}
output=${2:?original absolute output required}
arm=${3:?C or M required}
upstream=${4:?isolated on-policy source path required}
HMASD_PYTHON=${HMASD_PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
mkdir -- "$output"
"$HMASD_PYTHON" scripts/hmasd_resource_preflight.py admit-memory --out "$output/admission.json" &&
exec /usr/bin/time -f 'native_wall_s=%e\npeak_rss_kib=%M\nuser_s=%U\nsystem_s=%S\nexit_code=%x' -o "$output/native_time.txt" \
    "$HMASD_PYTHON" scripts/run_acvc_cluster_mappo_comparison_b02.py \
    --seed 28431 --arm "$arm" --launch-sha "$launch_sha" --output "$output" \
    --on-policy-root "$upstream" >"$output/stdout.log" 2>"$output/stderr.log"
