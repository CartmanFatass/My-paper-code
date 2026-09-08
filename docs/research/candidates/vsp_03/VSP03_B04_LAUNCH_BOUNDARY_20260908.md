# VSP03 B04 P65 complete task boundary

Accepted revised binding: card sections8–9. Science remains seed6/G1/Torch40006;
no B04 scientific invocation has started. The earlier c436e7bab payload boundary
is rejected because detached startup preceded timeout arming. This revision places
that startup inside a task-specific transient systemd unit on the configured node.
The command fixes accepted source b5d605bf4f39b5ab18f01c98e04dc07e53764354.
Root integration precedes its sole execution; later record-only commits do not
change this source surface.
Root's latest explicit continuation assigns Root this one launch. The existing CM
retains collection/technical acceptance and must not launch another copy.

```bash
bash experiments/candidates/vsp_03/vsp03_b04/launch.sh \
  vsp03-b04-p64-20260908 \
  /home/wu/hmasd-worktrees/vsp03-b04-p64-b5d605bf4f39b5ab18f01c98e04dc07e53764354 \
  vsp03-b04-p64-20260908 \
  /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_terminal.json \
  120 10 -- bash -c '/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b04.py --seed 6 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'
```

## Clock and containment

The existing user systemd manager arms the oneshot startup timer before ExecStart.
Its InactiveExitTimestampMonotonic is the single origin passed through controller,
payload, admission and runner. No payload clock resets. TimeoutStartSec=119s with
TimeoutStartFailureMode=kill and KillMode=control-group sends immediate SIGKILL to
the whole unit on timeout, leaving a conservative one-second margin inside120s.
The actual kernel/manager termination observation remains evidence, not a promise
about arbitrary scheduler starvation. The 120s card budget is unchanged.

The one-shot controller launches the installed unmodified /usr/local/bin/agent-task.
It unsets TMUX and sets TMUX_TMPDIR to the terminal sibling ending .tmux, ensuring
that this invocation's tmux server/pane are created inside the unit cgroup. No
default server, global supervisor/configuration, standing service or retry is added.
A startup stall even before the controller's first Python instruction is contained.
The systemd-run --wait client may be disconnected without killing the unit or
creating another invocation. Its output reports the unit's actual terminal result.

The payload subreaper stops work at original origin+110s. The controller and payload
reserve cleanup/publication inside the same cap, with cleanup cutoff origin+118s.
The controller captures the actual supervisor exit_code if published, kills/reaps
its private tmux/control descendants, and writes/reads the final terminal JSON.
A payload timeout returns124; a controller/collection failure returns125. A hard
manager kill can leave terminal JSON absent: preserve that failed publication and
actual manager failure, never synthesize exit0 or retry. Old deadline.sh remains
only as the earlier downstream fixture surface; launch.sh is the production entry.

## Authoritative evidence and Root access

The *_terminal.json controller receipt and its readback journal line are the
whole-task authoritative publication. The sibling *_terminal.payload.json records
the child return/timeout and scientific descendants. The receipt includes the
original manager timestamp, actual supervisor exit, child receipt and controller
termination facts. Final unit exit/timeout is separate OS evidence. Read journal:

```bash
journalctl --user -u vsp03-b04-p64-20260908.service --no-pager
systemctl --user show vsp03-b04-p64-20260908.service
```

While live, use the actual private-server environment for supervisor access:

```bash
env -u TMUX TMUX_TMPDIR=/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_terminal.tmux /usr/local/bin/agent-task status vsp03-b04-p64-20260908
```

The original supervisor files remain /home/wu/.agent-tasks/vsp03-b04-p64-20260908/
(task.log, start_time, exit_code, status, runner.sh). Collect them unchanged.
Unqualified default-server status is not evidence of inactivity for this task.
Manager properties may be unloaded after successful exit; retain the --wait output,
journal and controller receipt rather than treating absent unit state as failure.
The controller never writes supervisor bookkeeping. A missing final receipt or
remaining descendant limits acceptance and spends the sole scientific invocation.

## Cost, coverage and handoff

One G and the B03 cost law/counts are unchanged. The prior3.50s is planning evidence,
not a bound; complete120s includes task startup, admission, learning/output,
cleanup/publication. Aggregate CPU is unmeasured. No scientific timing pilot.
Reuse seed/object/status checks and existing downstream harmless checks. Independently
check this startup boundary and unchanged-supervisor/private-tmux path with shortened
nonzero and forced timeout fixtures. All check scratch remains invocation-owned temp.

Return accepted source, review and exact command to DM then Root before one launch.
After handle acceptance send unit/name/SHA/cwd/log/result/admission/terminal and the
private TMUX_TMPDIR access command to Root /root, copying DM. CM observes until
Root adoption, then retains collection. DM owns scientific intake for every outcome.

## Observed manager/client status distinction

The independent shortened checks establish that systemd-run --wait may return1 for
failed units whose actual ExecMainStatus is7,124 or9. Do not equate the client numeric
return to the task exit. Retain ExecMainCode, ExecMainStatus and Result from the manager,
the --wait output, journal and the authoritative task receipt. Evidence and independent
review bind the accepted source b5d605bf4f39b5ab18f01c98e04dc07e53764354; later record-only
commits do not change that source surface. Root integration precedes launch.
