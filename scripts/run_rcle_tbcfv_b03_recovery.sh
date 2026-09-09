#!/bin/bash
# One newly allocated W100 from update0, then the missing reference; no retry.
set -euo pipefail
sha="$1"
root="$2"
control="$3"
python="$HMASD_PYTHON"
mkdir -p "$root"
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/W100-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/W100-time.txt" timeout 600 "$python" scripts/run_rcle_tbcfv_b03.py --arm W100 --seed 19 --wall-cap 600 --out "$root/W100" --launch-sha "$sha" --admission-receipt "$root/W100-admission.json" --control-summary "$control" || exit $?
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/reference-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/reference-time.txt" timeout 30 "$python" scripts/run_rcle_tbcfv_b03.py --arm reference --seed 19 --wall-cap 30 --out "$root/reference" --launch-sha "$sha" --admission-receipt "$root/reference-admission.json" || exit $?
