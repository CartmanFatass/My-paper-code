# VSP03 B04 independent source review

Current reviewed candidate: `b5d605bf4f39b5ab18f01c98e04dc07e53764354`.
No material finding remains in its revised unit/startup/lifecycle path. Five
independent shortened checks pass; the current review is at the end of this file.
Earlier P64/P65 findings and narrower checks are preserved as historical evidence.

Reviewed the working-tree change against `aaf36703f` under the
[assignment](VSP03_B04_CM_ASSIGNMENT_20260908.md) and
[card](VSP03_B04_SCIENCE_CARD_20260908.md) sections2,3,5,6. Reused the accepted
[B03 affected-path review](VSP03_B03_SOURCE_REVIEW_20260908.md). Owned only this file;
no source/index edits and no scientific execution or check reruns.

## Material finding

**P2 — the complete120s stop boundary is measured but not enforced.** The
[launch boundary](VSP03_B04_LAUNCH_BOUNDARY_20260908.md#L16) starts a fresh120s
timeout around the child shell after the supervisor has started. Its own lines30–41
correctly state that exit/status/footer publication occurs after that timeout and
that the complete interval starts at the earlier supervisor start_time. The raw
[wrapper evidence](VSP03_B04_EXIT_CHECK_20260908.json) directly confirms the ordering:
eval finishes, then EXIT_CODE is captured, then the exit/status files and footer are
written. There is no encompassing deadline in the supplied boundary.

On the existing timeout path, the child can therefore consume120s in addition to
supervisor startup and subsequent required publication. That exceeds card section5's
single120s complete cap and its instruction to stop at that cap. Reporting the
overrun afterward avoids a false conformance claim but does not implement that stop
boundary. This is confined to cap enforcement; the new subshell correctly preserves
the command status and does not misreport the primary.

Repair: bind the complete selected interval, including required exit publication,
to an existing enclosing deadline mechanism and derive any inner timeout from its
remaining budget. If the unmodified supervisor cannot support that boundary, return
the concrete execution-contract gap to CM/DM before the sole invocation rather than
representing the child timeout as the complete cap. No extra scientific check or
new supervisor framework is requested. Actual completion comfortably within120s
would establish that invocation's observed compliance, but is still unobserved.

CM confirmed that the inspected existing agent-task has no omitted supervisor-level
deadline and returned this enforcement/accounting conflict to DM. The finding remains
open pending that disposition; no new machinery or additional execution was performed.

## Conforming connections and scope

- The shared driver's only diff is a defaulted `object_name="VSP03_B03"` argument
  and use of that value in summary.object. B01/B02 and the seed5 B03 runner have no
  diff against the assigned base. No model, objective, rollout, output or RNG path
  changes; the prior scientific review remains applicable.
- `scripts/run_vsp03_b04.py` restricts seed to6, passes args.seed to the shared
  driver, passes object_name VSP03_B04, and records VSP03_B04_COMMAND. Existing arm1
  and initialization40000+seed give G1/Torch40006. The preserved B03 default and
  seed5 CLI remain distinct. No weights, optimizer or streams load from an old run.
- Inherited counts, primary, five contrasts, float64 worlds/float32 CPU learning,
  one-thread settings, shared immutable evaluation tapes and private rollout state
  are unchanged. This review does not repeat scientific execution to verify them.
- The new outer subshell confines cwd failure and allows eval to return its real
  status. The inner exec replaces only the timed child. Raw harmless check evidence
  records numeric_exit7, status failed and footer code7, while the wrapper process
  returns0 after its idle sleep. Thus a wrapper exit or inactive tmux cannot substitute
  for the actual command receipt. The retained fixture's old B03 task label is
  disclosed and is not scientific B03 execution.
- The maximum required publication mtime minus rounded-down start_time is a
  conservative receipt span on the declared unchanged clock. The lower payload
  timer is correctly labelled separately. Missing numeric receipts are not inferred
  from summaries. The evidence contains start1788906217 and publication
  1788906217353791744ns, consistent with its reported0.353791744s harmless-check
  span; it provides no scientific runtime measurement.

Applied runtime-spec General requirements before scope-spec sections4–5; no B04
object-specific appendix applies. Prohibited optional machinery added without a
card line: **none found**. The shared-driver diff adds2/deletes2 lines and the new
runner adds28, within ordinary source/runner budgets; tests33 lines. Minimal seed/
object wiring and specified exit receipts have a concrete purpose; no orchestration
ratio gate, profiler, pool, retry, registry or validator is introduced.

Inspected both static binding tests and consumed CM's2-pass/0.11s record and remote
bash-n exit0 record without repeating them. Consumed the raw harmless postamble
check; it reports zero scientific models/episodes/updates and scratch_removed=true.
This review's work was read-only source/evidence inspection and line counting.

No other material finding was found. Residual risk is actual result completion,
normal-run readback/counts and full receipt-span/resource observation. These remain
CM's technical collection responsibility; DM owns the all-outcome scientific intake.
This review is independent evidence, not approval or a terminal disposition.

## P65 candidate review and independent checks

Reviewed committed candidate `c436e7babe31a981a0f9ee4062fe6b4405f5b20d` under card
section8 and the P65 correction handoff at `aa2e409f8`. These explicitly authorize
one B04 task-local deadline/termination adapter. The revised binding makes its
terminal.json authoritative inside containment; subsequent unchanged supervisor
bookkeeping is a separate actual observation. This prospective scope/boundary change
addresses the prior prohibition on the missing adapter without rewriting P64 evidence.

**P2 remaining finding — required startup precedes armed containment.** At this
candidate, launch-boundary lines12–16 perform detached startup, cwd/export work and
invoke deadline.sh before its line20 arms GNU timeout. deadline.sh line10 reads the
supervisor start_file before that timer exists. Charging those intervals against the
later remaining-time calculation cannot terminate a stall in detached startup or
that pre-timer read. The card section8 claims a complete deadline before required
startup/admission, so this path remains outside actual enforcement. DM independently
raised the same boundary; CM confirmed it is revising within the P65 allocation.
Repair is to arm the task's containment before the included startup path, preserving
the single origin and complete budget. No scientific check or framework is requested.

The downstream adapter has no additional material finding from this inspection.
Source comparison against `1289f0514` shows only the new deadline.sh(23 lines) and
deadline.py(120 lines) in the scientific/runner surfaces: scientific code and both
seed bindings are unchanged. The optional machinery is now expressly named by card
section8; cumulative B04 source additions are173 lines (30 earlier plus143 adapter),
with no source/runner budget breach. Linux subreaper setup precedes the direct child;
no new session separates it from timeout's group. Root return and task exit are
recorded distinctly, adopted descendants are killed/reaped before normal publication,
and any remaining descendants keep the adapter inside hard containment. Work cutoff
and cleanup/publication reserves derive from the one mapped origin. Hard containment
does not fabricate terminal evidence when it kills publication itself.

Independently authored
`tests/experiments/candidates/vsp_03/vsp03_b04/test_deadline.py` and ran it with the
configured Linux interpreter against files obtained by git show of exactly the
candidate SHA, under a unique remote temp directory. No scientific module was
imported. Each fixture used cap7s/reserve3s and a harmless root/child/grandchild tree.
Raw source-bound evidence, commands, receipts, PIDs, logs and times are in
[VSP03_B04_DEADLINE_CHECK_20260908.json](VSP03_B04_DEADLINE_CHECK_20260908.json).

| Fixture | Observed outcome | Origin through shell return |
| --- | --- | --- |
| Normal nonzero root with orphan tree | root7/task7; child and grandchild adopted and reaped; terminal readback; all four recorded PIDs absent | 0.674978s |
| Forced work timeout with live tree | root−9/task124, timed_out true; both descendants reaped; terminal readback; all recorded PIDs absent | 4.023334s |
| Adapter stopped with SIGSTOP | outer group kill137; terminal absent, no false completed record; all recorded PIDs absent | 6.029248s |

All three checks passed; harness wall9.485425s. Check code records process states
before its emergency cleanup, so test cleanup cannot conceal surviving descendants.
The hard case permits a separately recorded zombie state as terminated, but all
observed states here were absent. Both normal/task-timeout records report no error
and no surviving descendants. These facts cover the downstream lifecycle component,
not the unresolved pre-timer startup boundary or scientific performance.

Initial staging encountered a lazy Git blob fetch without the required zsh-lic
network environment; no fixture executed. Cancelled only its staging Git process
chain, retained that setup failure, and removed its scratch in finally. Corrected
git-show staging to zsh-lic and ran the checks once. Both owned scratch directories
were resolved against the exact remote test parent and removed; the record confirms
scratch_removed=true. Old B03 scratch and scientific roots were untouched.

No new seed/source-binding checks were repeated. Scientific model/episode/update
exposure remains0/0/0. The existing downstream evidence is reusable if that code
remains unchanged in the startup repair. CM retains correction and integration;
this is independent technical evidence, not final source acceptance.

## Revised unit boundary — b5d605bf4

**No material finding remains** in the assigned revised execution path at
`b5d605bf4f39b5ab18f01c98e04dc07e53764354`. Reviewed new control.py/launch.sh,
the deadline.py delta and revised launch binding under the unchanged card section8.
Reused scientific/seed/object review and the earlier downstream cleanup evidence.
This is independent technical evidence, not approval or scientific disposition.

The previous startup finding is resolved by arming the existing user systemd
manager's oneshot startup timer before ExecStart. launch.sh emits cap−1 seconds,
TimeoutStartFailureMode=kill, KillMode=control-group and FinalKillSignal=SIGKILL.
The controller passes the manager's InactiveExitTimestampMonotonic through the
payload adapter to the command; startup, private tmux creation, admission, learner,
descendant cleanup and final controller publication are inside that unit. Private
TMUX_TMPDIR ensures the task does not attach to the unrelated default tmux server.
Actual final manager state remains separate evidence, including failed publication.

During review, candidate28164ecb4 omitted VSP03_B04_COMMAND although the unchanged
runner indexes it. CM repaired this in2e02bce40 by exporting the actual shlex-joined
command before private tmux startup. A further DM-found publication/exit precedence
gap was repaired inb5d605bf4: a later actual nonzero supervisor exit takes precedence
over an earlier differing payload receipt; an actual0 mismatch becomes125. Both
observations are retained rather than rewriting the payload receipt. The focused
checks below confirm the repaired connections without scientific imports.

The independently authored harness executed the committed launch.sh bytes on
wsl_4070, with cap10s/reserve4s. A test-only PATH interceptor captured its exact
systemd-run argv, inserted only the existing controller's --supervisor/--task-dir
fixture overrides, and placed an ExecStart fault gate before exec of the exact
controller. Thus manager properties came from production launch.sh and were checked
against observed manager properties. Normal/task-timeout/stopped-controller paths
used a copy of the installed supervisor with only TASK_DIR replaced by owned temp;
production supervisor metadata and default tmux were untouched. The fifth case is
explicitly a literal receipt/real-shell-exit interface stub, not a tmux-path claim.

| Independent fixture | Direct outcome | Manager origin through client return |
| --- | --- | --- |
| Normal nonzero root plus orphan tree, actual copied supervisor/private tmux | controller/payload/supervisor7; terminal readback; no remaining descendants | 0.395306s |
| Forced work timeout, actual copied supervisor/private tmux | controller/payload/supervisor124; terminal readback; no remaining descendants | 6.043307s |
| ExecStart stall before controller code/clock lookup, with child | manager Result=timeout, ExecMainCode=2, ExecMainStatus=9; final terminal absent | 9.024161s |
| SIGSTOP controller with live task tree/private tmux | manager timeout/SIGKILL; final terminal absent | 9.125985s |
| Literal earlier payload0 plus real later shell exit7 | controller terminal retains payload0, supervisor7 and authoritative task7 | 0.305349s |

All five passed in25.511261s harness wall. Observed Type=oneshot,
TimeoutStartUSec=9s, TimeoutStartFailureMode=kill and KillMode=control-group matched
the exact launch argv. Every recorded fixture PID and sampled unit-cgroup PID was
absent after return, and each unit cgroup was empty/absent before test cleanup.
Normal paths asserted VSP03_B04_COMMAND, VSP03_B04_STARTED and private TMUX_TMPDIR
through actual tmux; controller and payload origin values matched the manager's
original timestamp. Required final terminal/readback and real manager exit facts
are preserved in the raw check JSON and journals. The startup/hard-failure cases
correctly have no invented final terminal receipt.

The systemd-run wait client returned1 for all these non-success cases, while actual
ExecMainStatus was7,124 or9. Consequently its client return must not be interpreted
as the numeric task exit; retain controller receipts and the manager's actual
code/status/result/journal. The revised binding already distinguishes those facts.

Current raw evidence is the top-level record in
[VSP03_B04_DEADLINE_CHECK_20260908.json](VSP03_B04_DEADLINE_CHECK_20260908.json);
earlier downstream checks and the initial staging failure remain under prior_checks.
The installed supervisor source, sole fixture-line replacement, emitted launch argv,
receipt/environment checks, manager properties, raw journal, PID states and stub
source are retained there. Exact committed candidate files were staged with git show
under zsh-lic into the short owned remote temp path. All five test units were stopped/
reset after evidence capture and the exact owned scratch directory was removed in
finally; scratch_removed=true. Old scratch and scientific evidence were untouched.

Scope-spec section4 additions are the single task-local deadline/termination adapter
explicitly requested by card section8; **no uncarded prohibited item was found**.
No supervisor/global configuration edit, standing service, retry, recovery or worker
pool was added. From1289f0514, adapter files total270 added source lines
(control101, deadline.py124, historical deadline.sh23, launch22); including earlier
B04 seed/object plumbing gives300 additions, below2000. The scientific runner remains
28 lines, below600. Execution-control code has a high orchestration share, but its
purpose is the explicitly selected complete-boundary correction; no independent
semantic or budget breach was found and no ratio-only gate was imposed.

Residual risk is actual scientific invocation completion and its primary/count/weight
readback, real full-span termination/resource evidence, and ordinary OS scheduling.
The shortened failure fixtures establish the selected node's boundary behavior,
not a scientific speedup or a guarantee against arbitrary kernel starvation. No
scientific source audit or seed checks were repeated; new scientific exposure is
models/episodes/updates0/0/0. CM retains actual collection/integration and DM the
all-outcome scientific intake. No source repair is requested by this final review.
