#!/usr/bin/env bash
# The one ACVC_M_DEPLOYMENT_TRANSFER_B01 original: fresh admission joined by && to the exact runner under GNU time.
# Ordinary wall plans are not runtime caps. Launch only through hmasd-experiment-operator after the Portfolio grant.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd -- "$root"
launch_sha=${1:?launch SHA required}
output=${2:?original absolute output required}
upstream=${3:?isolated on-policy source path required}
[ "$#" -eq 3 ] || { echo "usage: launch.sh <launch_sha> <output> <on_policy_root>" >&2; exit 2; }
HMASD_PYTHON=${HMASD_PYTHON:-python3}
export PYTHONDONTWRITEBYTECODE=1
mkdir -- "$output"
"$HMASD_PYTHON" scripts/hmasd_resource_preflight.py admit-memory --out "$output/admission.json" &&
exec /usr/bin/time -f 'native_wall_s=%e\npeak_rss_kib=%M\nuser_s=%U\nsystem_s=%S\nexit_code=%x' -o "$output/native_time.txt" \
    "$HMASD_PYTHON" scripts/run_acvc_m_deployment_transfer_b01.py \
    --seed 28531 --launch-sha "$launch_sha" --output "$output" \
    --on-policy-root "$upstream" >"$output/stdout.log" 2>"$output/stderr.log"
