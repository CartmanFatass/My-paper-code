#!/bin/bash
# Outer committed launch enforces 900s for this entire native comparison.
set -euo pipefail
sha="$1"
root="$2"
python="$HMASD_PYTHON"
mkdir -p "$root"
export sha root python
/usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/learned-time.txt" timeout 880 bash -c '"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/learned-admission.json" && "$python" scripts/run_rcle_b07_equal_unit.py --arm learned --seed 27 --wall-cap 878 --out "$root/learned" --launch-sha "$sha" --admission-receipt "$root/learned-admission.json"'
/usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/reference-time.txt" timeout 15 bash -c '"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/reference-admission.json" && "$python" scripts/run_rcle_b07_equal_unit.py --arm reference --seed 27 --wall-cap 13 --out "$root/reference" --launch-sha "$sha" --admission-receipt "$root/reference-admission.json" --learned-summary "$root/learned/summary.json"'
