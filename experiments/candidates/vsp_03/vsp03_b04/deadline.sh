#!/usr/bin/env bash
# One B04 envelope from the existing supervisor start clock. No postamble edits.
set -u
start_file=$1
cap=$2
reserve=$3
record=$4
shift 4
if [ "${1-}" = "--" ]; then shift; fi
read -r started < "$start_file" || exit 125
if (( cap <= 0 || cap > 120 || reserve <= 2 || reserve >= cap )); then
    exit 125
fi
# EPOCHSECONDS rounds down; subtract one second to round elapsed up. Bootstrap,
# interpreter startup and authoritative terminal publication share this budget.
remaining=$((started + cap - EPOCHSECONDS - 1))
if (( remaining <= 0 )); then
    exit 124
fi
/usr/bin/timeout --signal=KILL "${remaining}s" /usr/bin/time \
    -f 'contained_process_wall_s=%e peak_rss_kib=%M' \
    "${HMASD_PYTHON:-python}" "${BASH_SOURCE[0]%/*}/deadline.py" \
    --start-wall "$started" --cap "$cap" --reserve "$reserve" --record "$record" -- "$@"
