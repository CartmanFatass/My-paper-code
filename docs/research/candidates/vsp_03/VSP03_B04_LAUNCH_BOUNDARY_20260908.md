# VSP03 B04 P65 complete task boundary

Current binding: [card](VSP03_B04_SCIENCE_CARD_20260908.md) section8 and the P65
assignment. This replaces the rejected payload-only deadline proposal at1289f0514;
its evidence and open-review history remain. No B04 scientific invocation has started.
After source acceptance and Root integration, SOURCE_SHA is the exact pushed revision
staged in the configured wsl_4070 detached worktree. No local fallback or second run.

```bash
VSP03_B04_PAYLOAD=$(cat <<'VSP03_B04_LITERAL'
(
cd /home/wu/hmasd-worktrees/vsp03-b04-p64-SOURCE_SHA || exit
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python
export VSP03_B04_COMMAND='/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b04.py --seed 6 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'
bash experiments/candidates/vsp_03/vsp03_b04/deadline.sh /home/wu/.agent-tasks/vsp03-b04-p64-20260908/start_time 120 10 /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_terminal.json -- bash -c "$VSP03_B04_COMMAND"
)
VSP03_B04_LITERAL
)
/usr/local/bin/agent-task run vsp03-b04-p64-20260908 "$VSP03_B04_PAYLOAD"
```

## Clock and containment

The unmodified supervisor records start_time before detached startup. That existing
Unix-second timestamp is the one task origin. The B04 shell adapter derives remaining
seconds as start+120-EPOCHSECONDS-1, rounding elapsed up rather than extending the cap.
It launches GNU timeout with that remaining duration, not a fresh120s. The timeout
process group contains /usr/bin/time, the Python adapter, admission, scientific runner,
ordinary descendants, descendant cleanup, authoritative terminal write/readback and
the final process timing line. No child creates a new session in the accepted path.
All required task publications occur inside this enclosing timeout.

Python maps the original wall start once into its monotonic clock (wall sampled after
monotonic for conservative conversion). The scientific work cutoff is that same
origin+110s. Ten seconds inside the cap are reserved for shutdown/publication; cleanup
ends by origin+118s, leaving publication space before the conservatively rounded outer
limit. No stage resets or additional grace. The runner receives this same mapped start.
Fresh physical/effective admission each>=4GiB is directly joined to it by &&.

The Linux subreaper adopts orphaned descendants. On normal nonzero exit or work timeout,
the adapter captures the real root return code, kills and reaps remaining descendants,
then publishes terminal.json and reads it back. A timeout is task exit124; internal
cleanup/setup failure is125; ordinary child exits/signals remain attributable separately.
If descendants remain, the adapter retains the outer containment until its hard kill
rather than returning and abandoning them. GNU timeout is the final whole-group kill.
There is no restart, process pool, supervisor edit or manual supervisor-receipt writing.

## Authoritative evidence and limits

The sibling b04_seed6_p64_20260908_terminal.json and its readback log line are the
adapter's authoritative task exit/termination evidence, with original/mapped start,
cap/reserve, real root return, timeout state, reaped/remaining descendants and elapsed.
The contained_process_wall_s line is published by /usr/bin/time inside containment
and is narrower than the origin-to-terminal interval because startup precedes it.
The outer timeout's actual return is forwarded normally to the unmodified supervisor.
A hard kill before terminal publication means the terminal evidence is missing; retain
that failure, not a fabricated complete/exit0 claim. It spends the sole invocation.

Supervisor exit_code/status/footer after payload return remain actual separate
bookkeeping, outside the authoritative task boundary; they are neither overwritten
nor required to be inside the new containment. This is the explicit P65 distinction.
Collect those raw files alongside the task evidence. Missing task evidence, surviving
descendants or an over-cap observation limits acceptance; no retry follows.

## Cost, coverage and handoff

One G cost law and counts are unchanged. B03's3.50s remains a planning observation,
not a bound. New adapter overhead is not assigned a scientific timing pilot. The sole
complete120s budget includes it; aggregate CPU is unmeasured. The existing primary/
count/weight readback is unchanged and occurs only in the selected normal invocation.
Reuse passing seed/object/status checks. Independent shortened normal-nonzero and
forced-timeout fixtures cover the new lifecycle using no scientific model/world/step.
Card section8 authorizes exactly one task-local deadline/termination adapter for
complete invocation wall<=120s; no standing framework or unrelated telemetry follows.

After actual handle acceptance, send node/name/SHA/cwd/log/result/admission/terminal
paths to Root /root and copy DM /root/dm_vsp03_p54_reentry. CM retains observation
until adoption, then collection/technical acceptance. DM owns all-outcome intake.
