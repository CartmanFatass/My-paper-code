# VSP03 B04 independent source review

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
