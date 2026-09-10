#!/usr/bin/env bash
cd /home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020 || exit
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VSP03_B02_COMMAND='VSP03_B02_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b02.py --seed 4 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907 --started-monotonic "$VSP03_B02_STARTED" --node wsl_4070'
exec /usr/bin/time -f 'whole_wall_seconds=%e peak_rss_kib=%M' /usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B02_COMMAND"
