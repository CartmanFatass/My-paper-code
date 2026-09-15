#!/usr/bin/env bash
# One original longer-C B01 invocation; called by agent-task with simple argv.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd -- "$root"
launch_sha=${1:?launch SHA required}
output=${2:?absolute output path required}
HMASD_PYTHON=${HMASD_PYTHON:-python3}
if [[ -e "$output" ]]; then
    echo "Refusing to reuse original longer-C B01 output: $output" >&2
    exit 73
fi
mkdir -p -- "$output"
"$HMASD_PYTHON" scripts/hmasd_resource_preflight.py admit-memory --out "$output/admission.json" &&
exec /usr/bin/time -f 'native_wall_s=%e\npeak_rss_kib=%M\nexit_code=%x' -o "$output/native_time.txt" \
    timeout --signal=TERM --kill-after=10s 1860s \
    "$HMASD_PYTHON" scripts/run_acvc_cluster_longer_c_b01.py \
    --seed 22319 --launch-sha "$launch_sha" --output "$output" \
    --execution-seconds 1800 >"$output/stdout.log" 2>"$output/stderr.log"
