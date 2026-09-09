# VSP03 B03 launch boundary

Binding: card sections3–7 and CM assignment. No launch has occurred.
SOURCE_SHA below is the exact source commit after review and DM source intake.
Stage only committed/pushed source to the configured node repository and create
its exact-SHA detached execution worktree. Node wsl_4070, SSH hmasd-wsl-node.
No new authoring branch or alternative host is selected.

```bash
VSP03_B03_PAYLOAD=$(cat <<'VSP03_B03_LITERAL'
cd /home/wu/hmasd-worktrees/vsp03-b03-p54-SOURCE_SHA || exit
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VSP03_B03_COMMAND='VSP03_B03_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b03_seed5_p54_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b03.py --seed 5 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b03_seed5_p54_20260908 --started-monotonic "$VSP03_B03_STARTED" --node wsl_4070'
exec /usr/bin/time -f 'whole_wall_seconds=%e peak_rss_kib=%M' /usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B03_COMMAND"
VSP03_B03_LITERAL
)
/usr/local/bin/agent-task run vsp03-b03-p54-20260908 "$VSP03_B03_PAYLOAD"
```

The outer120s covers timestamp helper, adjacent memory admission, imports, G init,
128 training updates, four shared-world final executions, publication/readback and exit.
Both physical/effective available memory must measure >=4GiB. No stage clock reset,
grace period, extra fixture, profile, calibration, retry or local fallback.
Internal elapsed starts before admission and is narrower than complete process wall.
Whole aggregate CPU remains unmeasured; existing OS tools record wall and peak RSS.

Per-arm cost projection: admission/import + G init +128 batches of128 complete40-tick
2-target episodes +4 final executions of1024 worlds +weights/publication/readback/exit.
Historical complete T/G5.05s is only a planning anchor for smaller work count, not a
new bound or proportionally scaled timing. Sole G receives the complete120s cap.
No extra timing measurement is authorized.

Post-learner coverage: static connection checks and literal difference/JSON readback
reuse unchanged B01 publication and B02 difference helpers before launch. Normal run
reads final weights, endpoints, primary, interaction counts and learner records back.
Zero extra scientific models/episodes/updates for validation. Tests cannot establish
normal output existence, actual runtime counts or scientific value.

Send accepted handle/SHA/cwd/log/root/admission/bound to Root /root and DM
/root/dm_vsp03_p54_reentry. CM observes until Root adoption ACK, then keeps collection
and technical acceptance. Stop at sole publication/exit,120s, or a dependent defect.
Preserve partial records and return a gap without another invocation.
