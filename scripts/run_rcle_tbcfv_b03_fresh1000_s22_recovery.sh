#!/bin/bash
# One fresh-initialization seed22 W100 fit, then reference; retained W1, no retry.
set -euo pipefail
sha="$1"
root="$2"
control="$3"
python="$HMASD_PYTHON"
mkdir -p "$root"
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/W100-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/W100-time.txt" timeout 600 "$python" scripts/run_rcle_tbcfv_b03.py --arm W100 --seed 22 --updates 1000 --reporting-object RCLE-TBCFV-B03-ACTOR100-FRESH1000-S22-RECOVERY --out "$root/W100" --launch-sha "$sha" --admission-receipt "$root/W100-admission.json" --control-summary "$control" || exit $?
"$python" scripts/hmasd_resource_preflight.py admit-memory --out "$root/reference-admission.json" && /usr/bin/time -f 'wall_s=%e peak_rss_kib=%M exit=%x' -o "$root/reference-time.txt" timeout 30 "$python" scripts/run_rcle_tbcfv_b03.py --arm reference --wall-cap 30 --seed 22 --updates 1000 --reporting-object RCLE-TBCFV-B03-ACTOR100-FRESH1000-S22-RECOVERY --out "$root/reference" --launch-sha "$sha" --admission-receipt "$root/reference-admission.json" || exit $?
