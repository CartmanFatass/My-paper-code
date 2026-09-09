# VSP03 B05 / P76 technical acceptance and exact batch

Source **32ce8a7355b86bee64956e3d24b76d01c31a8d77**, committed/pushed under the
[full CM assignment](VSP03_B05_P76_CM_ASSIGNMENT_20260909.md) and
[card sections2/3/5/6](VSP03_B05_P76_SCIENCE_CARD_20260909.md). No intermediate
approval handoff is required. This record freezes the execution before submission.

Changes are36 new lines: the28-line run_vsp03_b05.py uses default/only seed7 and
scientific object VSP03_B05; the8-line launch_p76.sh binds the new P76 paths and
handle. Shared B01/B02/B03 science, canonical admission helper/platform dependency,
old seed6 runner and P67 single-clock adapter are byte-unchanged against828da0034.
Thus Torch40000+seed becomes40007 and G arm1 remains fixed. CPUfloat32/one thread,
all training/evaluation/RNG/primary/count semantics retain their accepted implementation.

[Focused checks](VSP03_B05_P76_SOURCE_CHECK_20260909.json) cover the11 committed
execution/import files, Git blobs/SHA256, LF, AST/bash syntax and exact argument
capture. Actual new/old entrypoints called an in-memory scientific-function stub
with7/B05 and6/B04 respectively; no Torch/model/world import or output construction.
The harmless argv capture retained literal start-variable quoting and passed numeric
start plus seed7. Reuse canonical helper import/parser and all P67 lifecycle and
scientific output/readback coverage. No repeated smoke, timing or scientific check.
[Independent review](VSP03_B05_P76_SOURCE_REVIEW_20260909.md) covers only the new
seed/object/command binding. No new scope-spec section4 machinery is added; the
existing cardsection6 task-local deadline adapter is reused. Cumulative source and
runner budgets remain; no new test budget was created.

**Legacy envelope mapping:** DM explicitly clarified that unchanged control/deadline
receipts retain object=VSP03_B04 as inherited technical metadata. The scientific
summary is VSP03_B05/seed7, while the exact P76 handle, command and roots bind every
receipt to this allocation. Keep the original receipt bytes; no relabeling, second
object/submission or adapter propagation change follows. B04-named internal command/
clock environment variables also remain unchanged.

Node wsl_4070 (ssh hmasd-wsl-node), Python /home/wu/.venvs/hmasd/bin/python.
Exact new detached cwd:
`/home/wu/hmasd-worktrees/vsp03-b05-p76-32ce8a7355b86bee64956e3d24b76d01c31a8d77`.
Execute these committed LF bytes after staged source/cwd/LF verification:

```bash
bash /home/wu/hmasd-worktrees/vsp03-b05-p76-32ce8a7355b86bee64956e3d24b76d01c31a8d77/experiments/candidates/vsp_03/vsp03_b04/launch_p76.sh /home/wu/hmasd-worktrees/vsp03-b05-p76-32ce8a7355b86bee64956e3d24b76d01c31a8d77
```

Handle/unit base vsp03-b05-p76-20260909. Output base
`/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b05_seed7_p76_20260909`;
admission _admission.json, whole-task _terminal.json, payload _terminal.payload.json.
Supervisor /home/wu/.agent-tasks/vsp03-b05-p76-20260909/ retains actual status/exit/log.
Use env -u TMUX with TMUX_TMPDIR equal to outputbase+_terminal.tmux for live agent-task
status. Read journalctl --user -u vsp03-b05-p76-20260909.service for manager facts.
CM /root/dm_vsp03_p54_reentry/cm_b03_single_g is sole executor/observer/collector;
notify Root and DM of actual acceptance, without duplicate observation or shell relay.

Fresh physical/effective4GiB admission is joined by&& immediately before the runner.
The manager's original clock covers all task work;110s work cutoff,118s cleanup,
119s hard cgroup kill inside120s. Prior P67 complete3.253184s/CPU3.278770s are the
per-arm planning observations under the unchanged one-G cost law, not upper bounds.
Post-learner path coverage reuses the accepted normal readback and lifecycle evidence.
Actual P76 wall/CPU and output remain to be observed. At most one accepted submission;
collect any refusal/exit/timeout/failure without retry, fallback, replacement, extra
seed/evaluation, resume or cap change. Preserve all old evidence and scratch.
