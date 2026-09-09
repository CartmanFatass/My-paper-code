# MGTAP B01 source acceptance and restart evidence - 2026-09-09

This record corrects the readiness and review claims preserved at `55e3adce5`.
The final source is technically accepted for the frozen REL/DENSE implementation;
no native run, pilot, profiler, new scientific exposure or successor is selected.
The owner's soft stop applies after this source/review/publication closure.

CM: `/root/cm_mgtap_p72_repair`. Independent native Reviewer:
`/root/cm_mgtap_p72_repair/review_mgtap_b01` (hmasd-reviewer).
Checkout: `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`, branch `codex/mgtap`.
Root is the assigning parent and integration owner; the original DM owns closure
intake. The prior app writer `01a084ec-b10f-7c63-b44f-439ec6a77f3d` finished and
pushed `5ce038e4aa6130be48b9cd17095470c6bde65d39` before this CM took sole editing
ownership. Its implementation and credible checks were reused, not discarded.

## Preserved source and scientific boundaries

All five shared `experiments/candidates/ucope/uav_motion_prefix_b01/` files match
main `6485fe0080abafe7521ed89f3425516407303d78`. Only `study.py` needed the prior
writer's reconciliation, retaining renewal-B02 registration. Environment, policy,
learner and initializer already matched both main and the frozen source pin
`d726acf63f8db47bd2e93e43cac8bbd27529d8ad`. No current shared learner, renewal or
VSPC1 API is downgraded, and no legacy framework is vendored.

The unchanged actor equations implement bias-free U(20x3), V(21x4), P(64x41),
fixed denominators 20/10, and the full 108-to-64 raw affine path. DENSE retains
D(16x108), zero d(16), Q(64x16), and its full raw path. Correct REL arithmetic is
`20*3 + 21*4 + 41*64 = 2768`; the earlier `10*4` term was a reporting typo.
Both complete learners have 69079 parameters. Common initialization at b+11,
private branch initialization at b+12, zero P/Q, primitive G, no duration or
renewal, raw actor/global critic inputs, native summed rewards, CPU FP32,
B02 agent_compound PPO, entropy .01, no ValueNorm, all action/reset RNG domains,
masters 8201/8202 and the frozen exposure are preserved.

The CLI sets BLAS/OpenMP environment controls before Torch import, then one
Torch intra/inter-op thread and CPU/FP32 defaults. Merely importing the package
no longer mutates another consumer's Torch defaults. Numerical movement is
reported separately for encoder, recurrent, critic, inner branch and projection;
zero-norm projection movement is absolute with no relative-to-zero ratio.

## Primary, runtime and publication repairs

The offline aggregate retains both masters and their paired episode differences,
REL/DENSE/H values, means and limits. It applies the card's mean of the two pair
means and +/- .01 branches. Training-pair sample SD is distinct from conditional
evaluation SE; the latter is `sqrt(SE_8201^2 + SE_8202^2) / 2`.
Missing/duplicate/corrupt primary values, wrong master or shortened learned
endpoints cannot yield aggregate polarity or a COMPLETE pair. Short or missing H
marks the H diagnostic incomplete without erasing trustworthy learned primary
measurements. Partial step, episode, rollout and optimizer counters survive
failures; no retry or resume path exists.

The existing shared Deadline supplies cooperative 1800-second complete-arm and
3600-second pair bounds. REL includes imports and shared construction; DENSE
includes H and pair publication. Checks reach reset, steps, PPO, arm transition
and publication. Exceptions and observed overruns retain partial facts and
report INCOMPLETE, PUBLICATION_FAILED or CAP_BREACH, as appropriate.
The no-op callback is named fixture-only; native execution uses Deadline.check.

Cooperative checks do not interrupt an opaque call precisely at the cap.
Persisted runner timing precedes the last write; a final observation detects a
new breach, but shutdown is outside that clock. The literal wrapper uses the
installed GNU time to record full interpreter wall through exit. A future
collector must reconcile supervisor exit, summary status and external wall;
check pair wall <=3600 and external pair wall minus completed REL wall <=1800
for DENSE/H/publication/exit. GNU time output is rounded to hundredths, so a
boundary case cannot establish strict conformance. A zero process exit alone
is not a resource-conformance claim. No native timing exists here.

Required offline aggregation is a separate process: its imports, readback and
final publication must be included in complete-study accounting. Report study
critical path, sum of pair process walls plus aggregation, and aggregate CPU
work separately. CPU work remains unmeasured; do not infer it from wall or a
thread limit. The aggregate's wall does not disappear into an already-ended pair.

## Actual focused evidence and budget

The original 55e3 record's seven checks and toy publication are historical
engineering evidence, not an independent review. Its 4.72/5.12-second test
reports are inconsistent and no complete-process wall was retained; neither is
silently promoted to a full-process measurement or a proof of the smoke bound.

The prior app writer's actual command records were inspected and retained:

| Check | Outcome | pytest time | Command wall |
| --- | --- | ---: | ---: |
| First setup attempt | 20 pass, 6 setup errors (missing scratch parent) | 5.22 s | 6.395 s |
| Repaired directory suite | 26 pass | 7.51 s | 9.094 s |
| Changed endpoint subset | 16 pass, 4 deselected | 4.21 s | 6.405 s (also includes edit/diff commands) |
| CM changed-path checks | 12 pass, 20 deselected | 12.34 s | 13.829 s including cleanup |
| Final endpoint/control correction | 3 pass, 21 deselected | 3.97 s | 4.937 s including cleanup |

Known charged command wall is 40.660 seconds. The original total focused-check
cap remains 300 seconds: known remaining ceiling is 259.340 seconds minus the
unmeasured older check/process cost. Exact all-history consumed/remaining wall
cannot be certified. No additional check budget was allocated, and no further
checks are planned at this soft-stop boundary. The first proposed CM PowerShell
check/cleanup command was rejected before process creation (policy rejection;
no more specific reason returned); the same bounded check ran with a Python
controller and verified scratch cleanup, without escalation or permission.

CM checks used `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q
-p no:cacheprovider --basetemp <invocation scratch>` on the candidate test directory.
First selection: `branch_is or relation_padding or native_binding or training_sd
or controls_precede or package_import or missing_primary or runner_fixture or
partial_step or publication_is`; final selection on test_reporting_deadline.py:
`short_hover or short_episode or controls_precede`. Parent process timeouts were
60 and 30 seconds respectively. Each invocation's resolved scratch was under
this checkout's temp/directions/metric_ground_transport_allocation/test/ and
was removed in finally after retaining these results. The cache_dir warning is
pytest configuration noise; the tests passed. No native environment was called.

Tests establish both branch velocity-density gradient paths after projection
movement, zero initial inner gradients, both fixed padding denominators,
separate uncertainty units, default compatibility, pre-import controls,
partial/deadline/publication behavior and no COMPLETE on missing primary.
Literal wrapper tests use shlex against agent-task's actual argument flattening
and local Git Bash `-n`, without submitting the scientific command. Read-only
remote inspection confirmed agent-task's `run <name> <cmd...>` implementation
and availability of GNU time. Shared-source diff and git diff --check pass.

## Independent review and scope

The named native Reviewer independently inspected actor/credit/source boundaries,
final runtime/aggregate/exposure/control changes and focused test code. It found
no remaining material source defect after the velocity-loss, movement reporting,
uncertainty and H-only endpoint corrections. It accepted the CM's actual check
evidence without duplicating tests; it executed no scientific import or test.
This is independent technical review, not the original implementer's self-review
and not scientific or runtime validation.

No new Engineering Scope Spec section 4 machinery was added. The implementation
uses existing collection/learner/deadline/publication APIs, a small numerical
aggregate and a literal command list. Actor equations and production credit are
unchanged. Exact final line counts and committed bindings are recorded below.

## Cost and restart boundary

Per learned fit: 512x256=131072 training steps, 1024 Adam calls and 32x256=8192
sampled evaluation steps. Four fits plus two H references total 573440 steps,
4096 Adam calls and 192 evaluation episodes. Per-arm cost law remains
`C_init + 131072*c_env_actor + 1024*c_update + 8192*c_eval + C_publication`, with
8192 extra H steps charged once per master to DENSE. REL/DENSE branch arithmetic
is 4664/2752 matrix-weight products and 610/16 inner tanh outputs per actor row;
3,317,760 logical actor-row evaluations per fit. These are computed counts,
not measured time or affordability. Native coefficients, activation memory,
RSS, CPU work and complete-process times remain unknown.

The final restart HANDOFF in this directory supplies exact source/evidence
revisions and next owner. Root may integrate accepted source and route closure
intake to the original DM. No staging, admission, native run, retry, new Pro round
or successor work proceeds under the current soft stop.

Final source size: runner 492 lines, geometry 168, package initializer 21 and entry script 29. Relative to the card commit 7e880cb33, 1628 non-test source lines are added including the five reconciled shared UCOPE files; this is below 2000 and the runner is below 600. The independent review found no prohibited machinery; reporting/deadline code is the explicitly assigned repair surface.
