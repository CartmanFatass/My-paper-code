#!/bin/bash
# Fresh seed21 pair at the fixed1000 endpoint. Stop on failure; no retry.
set -euo pipefail
sha="$1"
root="$2"
python="$HMASD_PYTHON"
mkdir -p "$root"
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/W1-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/W1-time.txt" timeout 600 "$python" scripts/run_rcle_tbcfv_b03.py --arm W1 --seed 21 --updates 1000 --reporting-object RCLE-TBCFV-B03-ACTOR100-FRESH1000-S21 --out "$root/W1" --launch-sha "$sha" --admission-receipt "$root/W1-admission.json" || exit $?
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/W100-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/W100-time.txt" timeout 600 "$python" scripts/run_rcle_tbcfv_b03.py --arm W100 --seed 21 --updates 1000 --reporting-object RCLE-TBCFV-B03-ACTOR100-FRESH1000-S21 --out "$root/W100" --launch-sha "$sha" --admission-receipt "$root/W100-admission.json" --control-summary "$root/W1/summary.json" || exit $?
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/reference-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/reference-time.txt" timeout 30 "$python" scripts/run_rcle_tbcfv_b03.py --arm reference --wall-cap 30 --seed 21 --updates 1000 --reporting-object RCLE-TBCFV-B03-ACTOR100-FRESH1000-S21 --out "$root/reference" --launch-sha "$sha" --admission-receipt "$root/reference-admission.json" || exit $?
