#!/bin/bash
# Each external timeout includes its immediately adjacent admission and process exit.
set -euo pipefail
sha="$1"
root="$2"
python="$HMASD_PYTHON"
mkdir -p "$root"
export sha root python
/usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/learned-time.txt" timeout 150 bash -c '"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/learned-admission.json" && "$python" scripts/run_rcle_b04_nearest_prior.py --arm learned --seed 24 --wall-cap 148 --out "$root/learned" --launch-sha "$sha" --admission-receipt "$root/learned-admission.json"'
/usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/reference-time.txt" timeout 10 bash -c '"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/reference-admission.json" && "$python" scripts/run_rcle_b04_nearest_prior.py --arm reference --seed 24 --wall-cap 8 --out "$root/reference" --launch-sha "$sha" --admission-receipt "$root/reference-admission.json" --learned-summary "$root/learned/summary.json"'
