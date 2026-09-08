#!/usr/bin/env bash
# One transient unit; its startup timer precedes every task process.
set -eu
unit=$1
cwd=$2
name=$3
record=$4
cap=$5
reserve=$6
shift 6
if [ "${1-}" = "--" ]; then shift; fi
exec systemd-run --user --unit="$unit" --service-type=oneshot --wait \
    --working-directory="$cwd" \
    --property="TimeoutStartSec=$((cap - 1))s" \
    --property=TimeoutStartFailureMode=kill --property=KillMode=control-group \
    --property=FinalKillSignal=SIGKILL --property=TimeoutStopSec=1s \
    --setenv=OMP_NUM_THREADS=1 --setenv=MKL_NUM_THREADS=1 \
    --setenv=OPENBLAS_NUM_THREADS=1 --setenv=NUMEXPR_NUM_THREADS=1 \
    /home/wu/.venvs/hmasd/bin/python \
    "$cwd/experiments/candidates/vsp_03/vsp03_b04/control.py" \
    --unit="$unit.service" --name="$name" --record="$record" \
    --cap="$cap" --reserve="$reserve" -- "$@"
