#!/usr/bin/env bash
# One original indexed C01 unit; called detached by agent-task with simple argv.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd -- "$root"
launch_sha=${1:?launch SHA required}
unit=${2:?unit index required}
case "$unit" in
    1|2|3|4|5|6) ;;
    *) echo "Unit index must be 1..6" >&2; exit 64 ;;
esac
printf -v suffix 'unit_%02d' "$unit"
output="temp/directions/acvc/exp/cluster_fixed_recipe_c01_20260914/$suffix"
HMASD_PYTHON=${HMASD_PYTHON:-python3}
if [[ -e "$output" ]]; then
    echo "Refusing to reuse original fixed-recipe C01 output: $output" >&2
    exit 73
fi
mkdir -p -- "$output"
"$HMASD_PYTHON" scripts/hmasd_resource_preflight.py admit-memory --out "$output/admission.json" &&
exec /usr/bin/time -f 'native_wall_s=%e\nuser_cpu_s=%U\nsystem_cpu_s=%S\npeak_rss_kib=%M\nexit_code=%x' -o "$output/native_time.txt" \
    timeout --signal=TERM --kill-after=10s 1860s \
    timeout --signal=TERM --kill-after=10s 1800s \
    "$HMASD_PYTHON" scripts/run_acvc_cluster_fixed_recipe_c01.py \
    --unit "$unit" --launch-sha "$launch_sha" --output "$output" \
    --execution-seconds 1800 >"$output/stdout.log" 2>"$output/stderr.log"
