# N3 DISH B01 C04 — technical intake and first seed selection

Date: 2026-09-04. DM `/root/dm_amx_n3_continue`.
Scientific class and ceiling: unchanged **B / EXPLORE**, preliminary first-trigger source selection
on this host, three seeds and 64-update budget. No scientific result exists at this boundary.

## What I checked

Read CM's complete `N3_DISH_B01_C04_CM_RETURN_20260904.md` at pushed report commit
`fc60efb58b17235f82c0a0a0cac3d667a5c36548`, and compared its counts, source surface, command,
precision/RNG/checkpoint/side-effect statements and remaining coverage to B01 and the C04 objective.
Source is `e0541d0cb3e9e63731c72f4dacb10b44d268fd39`; transplant commit is `e15c1794ee2be2907d3b692f8ab7c347c5bc688e`.
CM and implementer branches are pushed; CM's worktree is clean.

All nine non-test source files are the exact previously reviewed candidate bytes. The only
candidate departure is a +13/-1 test oracle correction independently reviewed without a material
finding. The full eleven-file delta is +1,578/-157; new non-test lines 1,198, runner 118,
conservative orchestration 274/1,198 (22.9 percent), no section-4 machinery or section-5 breach.

Eight requested tests have passing evidence: seven unchanged passes at the first source plus
the changed-node pass at final source. The native compile/load regression passed in 2.06 seconds;
the single prepared-branch smoke passed in 1.23 seconds. After the targeted pass, direct runner
`project-cost` emitted all three seed and all three arm rows at 1474.544745605439 seconds each,
below the 1800-second arm cap. These are projections, not measured learner costs.

## Reproduced failure and rule application

The C03 zero-collection failure is a reproduced launch-cwd quoting defect, as recorded in the
resumption intake. C04's first exact-SHA task then ran 7 passing tests and failed one strict
action equality assertion. The failing step was reproduced over the recorded bytes before
classification: hidden state, preparation/commit outputs, old log probabilities and ratio were
exact; grouping FP32 motion-head GEMM across ticks caused maximum head difference
2.9802322387695312e-8 and action difference 1.1920928955078125e-7. Per-tick expected actions
matched live actions exactly. The initially proposed float64 projection cause was explicitly
rejected by reproduction.

The repaired test uses that exact per-tick action oracle and separately bounds batched motion
rounding by `eps(float32) * max(1, abs(step_motion))` for its unit-scale sentinel. It retains exact
hidden/input/discrete/action/logprob/ratio checks and does not alter any production numerical
kernel. This implements the original within-inherited-precision contract; it is not an exact GEMM
theorem and not a scientific threshold change. Evidence-spec section 11.2 adds no B bit-identity
obligation. The final focused check passed and the previously passing unchanged smoke was reused.

Verification tasks `dish_b01_c04_final_e15c1794_01` and `dish_b01_c04_repair_e0541d0c_01` are
terminal, and tracker notices were acknowledged. Their exit codes and tests establish technical
facts only. No `FTS-*` rule was entered: scientific seeds, admissions, training transitions,
optimizer updates, panel outcomes, checkpoints and result summaries are all zero at this intake.

## Decisions this intake produces

### 1. Accept the scoped technical return — object tier, technical

Options: (a) accept conformance for a real B01 invocation with the remaining publication coverage
explicit; (b) demand full bit identity from the batched sentinel or rebuild unchanged source;
(c) infer source value from tests. Recommend/select **(a)**. The reproduced test issue is resolved
without changing the protected algorithm, the exact native fork is exercised, and original counts,
cost/output instrumentation and source definitions match. Tests cannot select a scientific branch.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Provenance `OWNER_DELEGATED`; reversible; owner flag `none`.

### 2. Stage the unchanged first real seed — object tier, selection

Options: (a) invoke seed 11, collect its technical completeness, then continue unchanged seeds 29
and 47; (b) invoke all three immediately in parallel. Recommend/select **(a)** because B01 has
never completed its actual learner-to-publication path. This reduces duplicated exposure to a
possible common implementation failure. It changes no seed, budget, arm, comparator or estimator.
Every complete seed, including no-trigger or adverse output, is retained. Continuation is based
only on technical integrity, not sign, effect size or trigger support. All three complete seed
summaries remain necessary for the card's aggregate rule; there is no efficacy-based early stop.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
Provenance `OWNER_DELEGATED`; reversible; owner flag `none`.

## Prospective exact invocation and recovery

Node `wsl_4070`, `hmasd-wsl-node`; CPU, one Torch thread, carded FP32 learner/float64 native
semantics. Use the already prepared exact source worktree and the existing detached supervisor.
One complete command string, with correctly scoped `cd`, is:

```sh
cd /home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_first_trigger_source_scout_b01.py run --seed 11 --admission temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1_admission.json --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1
```

Intended fresh supervisor name: `dish_b01_c04_seed11_e0541d0c_a1`. CM must reconcile that name
before dispatch and record actual acceptance; this line is prospective, not a claim of launch.
Physical and effective available memory must each be at least 4 GiB immediately before the runner.
The receipt is outside the absent output child. The cap is 1,800 seconds, checked at update
boundaries, with no efficacy stop and no resume. Expected cost is 1,474.544745605439 seconds,
fully charged to each of the three source arms. Remaining seeds are queued, not launched here.

The machine-generated nominal exposure is recorded in the C04 resumption intake: 2,048 steps,
lr path 0.6144, minimum Xavier RMS 0.07216878364870322, nominal ratio 8.513376129362545.
Actual exposure and all learner/evaluation measurements remain obligations of the real invocation.
The DM prediction remains insufficient trigger support, conditionally generic-remap-only; the
owner prediction is not taken (unattended). No pending owner review instruction was returned at
this boundary. The five-tick MEI remains descriptive; the original ordered `FTS-*` rule controls.

CM hands the accepted handle, launch SHA/cwd, receipt and output/log paths and expected bound
directly to `/root/tracker_tl_experiments`. Tracker alone observes/reminds; CM collects and
technically checks; DM reads every result. The owner resumption remains active, with no N3 or
constituent lifecycle, priority, recast or family change.

## Limitation and next discriminator

**Open engineering item:** the smoke does not exercise the real learner, full sixteen-row panel,
actual displacement or final checkpoint/summary writes through `_run`. There has been no B01
post-learner failure. Carry this limitation on every result until actual collection closes it;
it adds no fifth B launch gate. Missing resource telemetry alone is `resources_unmeasured`.
Incomplete learner instrumentation still quarantines the attempt without scientific polarity.

The next discriminator is the real first-trigger source contrast. COPY may absorb apparent
SHADOW value; a later same-information replay or different training convention may also absorb it.
No-trigger rows cannot establish source equality. B04's small typed-mask effect supplies no
source-transfer polarity, and no result here can close N3 as a route.

## Append-ready shared audit rows

Root owns the ledger; append under `n3-dish-b01-c04-launch`.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T17:10:37-07:00 | degraded_incumbent_shadow_handover | object | technical | (a) accept scoped conformance; (b) extra bit identity or rebuild; (c) infer value from tests | (a) conformance accepted, real learner/publication coverage open | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | docs/research/portfolio/owner/inbox/2026-09-04/20260904-dish-011.json | none | |
| 2026-09-04T17:10:39-07:00 | degraded_incumbent_shadow_handover | object | selection | (a) seed11 then technical collection then29/47; (b) all three parallel | (a) unchanged sequential technical staging, no efficacy screening | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | docs/research/portfolio/owner/inbox/2026-09-04/20260904-dish-012.json | none | |
