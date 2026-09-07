# Service-allocation B01 — implementation technical acceptance, 2026-09-07

**Implementation accepted; selected experiments remain undispatched.** P07-VSPC1-IMPLEMENT-01
authorizes this return under the [five-item handoff](VSPC1_K4_SERVICE_ALLOCATION_B01_CM_HANDOFF_20260907.md)
at `a66351805` and [card §§2–7](VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md).
The historical preparation-only dispatch wording in those documents is superseded by that
implementation assignment; the implementation-only stop remains intact.

Source/test commit **`63b8a6888e780f06d783bd900e052f9f08cf2d9f`** is pushed on
`cm/vspc1-service-allocation-b01-20260907`, based on planning snapshot
`3e415347f7268c048b2015a9594d47be8fa876ba`. Worktree:
`C:/Projects/HMASD-worktrees/cm-vspc1-service-allocation-b01-20260907`.
Root integrates this technical return; the original DM performs source/card conformance intake
and returns it to Portfolio. This record adds no experiment, scientific choice or Pro send.

## Delivered source and preserved boundaries

| New owned path | Lines | Responsibility |
| --- | ---: | --- |
| `experiments/candidates/vsp_c1/k4_service_allocation_b01/experiment.py` | 309 | Three-queue host, rule, RNG/features/models, actual segment learning, counts and evaluation |
| `experiments/candidates/vsp_c1/k4_service_allocation_b01/reporting.py` | 109 | Paired endpoint/SE, five-point AUC, initial changes, overlapping descriptive branches and JSON readback |
| `scripts/run_vspc1_k4_service_allocation_b01.py` | 84 | One selected arm; GENERIC includes the rule and paired publication |
| `tests/experiments/candidates/vsp_c1/k4_service_allocation_b01/test_contract.py` | 281 | Focused synthetic fixtures and selected-count comparison |

Scope-spec §4 additions, listed before writing: **none**, as card §7 requests.
502 non-test research source lines and 84 runner lines are within the ordinary budgets.
No scheduler, registry, guard, recovery route, instrumentation framework, compatibility layer
or new dependency was added. The completed diff changes only new assigned paths and this record;
the diff against the old reactive implementation/runner is empty. Old cards/results and unrelated
user/agent work remain unchanged. Governing scope/evidence/runtime specifications are unchanged
from the previously read versions; relevant evidence §§11.7–11.8.5 were additionally read here.

The code uses the accepted reactive implementation as a read-only starting point, with ordinary
in-process NumPy/Torch batching. Each `collect` call allocates fresh `(q0,q1,q2)` and copies the
initial `h`; the shared tape holds only exogenous arrivals and assigned exploration draws.
The partner resolves longest-queue ties in `[(h+1)%3,(h+2)%3,h]` from old `h`. Service uses
distinct selected queues once, then arrivals/clipping/overflow, then `h=held_action`.
The focal scores all three actions only at renewal; it holds the chosen action for all d ticks.
LQ-EXCLUDE recomputes its immediate partner action only at renewal, excludes that queue for
its own rule choice, uses smallest-index remaining ties and holds the choice. That exclusion
never affects a learner's legal actions, targets or data. All controllers own their endogenous
state and partner responses; no controller's trajectory is replayed into another.

Stored state is `[q0,q1,q2,h,t]`. Common features are normalized queues/time followed by
three-way h/action one-hots; GENERIC appends the two duration indicators. Network construction
preserves the prior order: hidden Linear, output Linear, FACTOR empty embedding allocation;
then hidden/output Xavier weights and zero biases, then Normal(0,0.5) embedding. Only the
declared input dimensions change. Online parameters are 372/393; target is a non-optimized
deep copy. The real learner uses detached actual-segment Double-Q, no terminal action scoring,
served/96 without division by d, per-episode mean loss followed by equal-period mean, one Adam
step per unchanged-parameter collection batch and target copying after each multiple of 16.

RNG retains the declared PCG64/SeedSequence namespace IDs11/12,21–24,31/32, with
`[root_seed,namespace_id,d,u]`, evaluation u0 and training u1–256. Initialization takes the
first uint64 word with d/u0 as the arm Torch seed in a forked CPU RNG scope. The selected
seed remains402. Training arrays are `(8,48,3)` arrivals `<0.5`, `(8,)` initial h in0..2,
and `(8,48)` coins/actions; evaluation arrays are `(128,48,3)` and `(128,)`. No outcome-bearing
seed402 RNG/model/host invocation occurred in this implementation assignment.

## Focused acceptance evidence

One local focused synthetic suite was executed, with the configured scientific interpreter:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/service_allocation_synthetic_20260907 tests/experiments/candidates/vsp_c1/k4_service_allocation_b01
```

**9 passed in6.06s**, within the five-minute budget. The single pytest warning is the existing
`cache_dir` option with cacheprovider disabled. No complete runner smoke, historical rerun,
performance probe, remote task, memory admission, form of `run()`/runner `main()`, or selected
call was executed. `git diff --cached --check` passed before the source commit.

The suite establishes these bounded facts:

- Cyclic old-h partner decisions, collisions, empty service, overflow and queue conservation
  match hand-built transition examples. LQ-EXCLUDE ties/exclusion are correct.
- All three Q actions are scored with the specified features. Synthetic model construction
  preserves the surrounding Torch RNG state and exposes the expected parameter counts.
- Assigned tape values match independently constructed namespace streams at fixture seed9402;
  training/update/period/evaluation separation is checked. Exploration reads primitive slots
  only at renewals, including action2; successor state and actual segment reward are checked.
- A rule evaluation on hand-built tapes calls each period once and owns its queues/h. Its d6
  state/action sequence matches an independent scalar fixture oracle. A fixed alternative
  controller on the same tapes has a different endogenous sequence; tapes remain unchanged.
- Synthetic Double-Q selects action2 where appropriate and never scores terminal successors;
  targets are detached. The loss gradient is equal episode/period weighted, not row weighted.
  A single synthetic real-network Adam update exercises the common differentiable path while
  the target remains unchanged. This is not a selected-model displacement experiment.
- Synthetic primary values are written/read for FACTOR, GENERIC and LQ-EXCLUDE. Each paired
  difference/conditional SE is checked independently with standard-library statistics;
  five-point AUC, initial changes, rule-relative initial advantage and overlapping MEI/period
  branches are checked. `E_FACTOR-E_GENERIC=Delta` is preserved. Adding rule data leaves the
  learner contrast unchanged; absent rule data retains that contrast with unresolved rule value.

Saved synthetic artifacts, relative to the worktree:

- `temp/directions/vsp_c1/test/service_allocation_synthetic_20260907/test_features_models_and_sourc0/configuration_exposure.json`
- `temp/directions/vsp_c1/test/service_allocation_synthetic_20260907/test_primary_publication_three0/`
  contains `FACTOR.json`, `GENERIC.json`, `LQ-EXCLUDE.json`, `pair_without_rule.json`, `pair.json`.

The synthetic values are fixture inputs, not service performance measurements. Actual fixture
exposure: three QNetwork initializations at seed9402 and one target deep copy; one real Adam
step over64 synthetic terminal TD rows and one scalar zero-lr SGD step over64 synthetic rows;
four synthetic host episodes totaling192 primitive ticks (two rule, two fixed-policy), plus
six standalone batched transition examples. Thus implementation host exposure is198 primitive
episode-ticks; an independent scalar rule oracle adds48 checker ticks. RNG-array fixtures
generate only fixture seed9402 tapes, without additional host calls. No optimized policy was
evaluated in the environment. Selected B exposure is zero: no seed402 learning/evaluation,
reference run, parameter selection or scientific result.

## Source-to-selected-counts comparison

The synthetic suite directly compared delivered `counts`, `rule_counts`, model parameter
counts and default budget to the [selected machine record](VSPC1_K4_SERVICE_ALLOCATION_B01_COUNTS_20260907.json).
These matched; that record's historical dispatch fields were not rewritten.

| Selected quantity | Each learner | Once-only rule |
| --- | ---: | ---: |
| Online parameters | FACTOR372 / GENERIC393 | 0 |
| Training episodes / ticks | 4096 /196608 | 0 /0 |
| Actual renewal / nonterminal rows | 65536 /61440 | 0 /0 |
| Optimizer steps | 256 | 0 |
| Evaluation episodes / ticks | 1280 /61440 | 256 /12288 |
| Evaluation decisions | 20480 | 4096 |
| Scalar Q predictions | 569344 | 0 |
| Target copies including initialization | 17 | 0 |

Each learner's Q predictions split into behavior196608, online bootstrap184320, target
selected-action61440, loss65536 and evaluation61440. Five checkpoints are exactly
`[0,64,128,192,256]`; pair totals528384 joint ticks,512 Adam steps and1138688 Q predictions
include the rule's once-only evaluation. Counts are source/configuration facts, not observed
scientific exposure. The can-move statement describes the nonzero-lr real Adam/TD path;
actual seed402 initial norms and final displacement remain unknown until selected execution.

## Primary publication and call boundary

The runner has one FACTOR/GENERIC arm interface at fixed seed402 and no technical-fixture,
standalone rule, compare-only or arbitrary-budget option. GENERIC requires the accepted
FACTOR summary path. Both learners publish `summary.json` with actual counts, all selected
curves/period losses, indexed endpoint/native values, initial norm/final movement and launch
facts. GENERIC then writes its trustworthy learner contrast before evaluating the rule once,
adds the rule's endpoint/counts to its own summary and publishes the full three-contrast report
at `GENERIC/paired_summary.json`. A rule dependency failure therefore need not erase Delta;
it does not authorize a third call. No rule observation informs training/checkpoint selection.

All rule/paired work occurs inside the same GENERIC process and future complete-call clock.
The existing external launch facility supplies fresh adjacent node-local admission and the
2700s timeout; this assignment created neither a launch command nor a supervisor handle.
Future interface (paths/launch SHA are bound by the later execution assignment): FACTOR uses
`--arm FACTOR --seed 402 --out <run>/FACTOR`; GENERIC uses
`--arm GENERIC --seed 402 --factor-summary <run>/FACTOR/summary.json --out <run>/GENERIC`.
Runtime roots remain under `temp/directions/vsp_c1/exp/k4_service_allocation_b01_<run>/`.

**Post-learner publication coverage:** the new primary write/read and three-contrast calculation
were exercised with synthetic data, including missing-rule degradation. Source inspection and
independent review cover their GENERIC call ordering; no complete-runner smoke was commissioned.
This establishes the affected publication functions, not complete selected-call execution.

**Per-arm cost projection status:** delivered cost law retains initialization, host ticks,
three-action behavior/backup/loss work, optimizer, five evaluations and publication/exit.
FACTOR has258048 joint ticks; GENERIC's complete call has270336 including the rule. Unit
times for this host are unknown; no seconds projection or resource-conformance claim is
manufactured from the old two-queue4.84/5.48s measurements. No cost/profiling experiment was
selected. The later execution record retains the original2700s cap independently per call;
summed caps5400s are neither forecast study elapsed nor measured aggregate CPU.

## Independent review, disposition and next owner

Independent `hmasd-reviewer` task `review_ah_reactive_queues` read the new complete source,
card/handoff, tests and saved synthetic artifacts. It found **no material issue** in cyclic
old-h timing, three-action/RNG/init order, actual Double-Q/equal-period loss, own-state held
rule, five-point AUC or three-contrast publication. It checked that the rule is called exactly
once only after GENERIC learning, and that learner contrast publication precedes it. No scope
§4 addition or line-budget breach was found. The reviewer ran no models, host steps, tests
or experiments and made no edits. CM accepts that disposition; no source finding remains.

This return satisfies the bounded implementation assignment. Whole selected-call execution,
observed full counts, resource peaks/wall, seed402 movement and performance remain unmeasured.
These are future call facts, not implementation blockers or an extra feasibility gate.
Root integrates the clean source/record; the original DM performs card/source intake and
reports to Portfolio for its next bounded command. Both2700s scientific calls remain
undispatched. No further implementation, experiment or Pro action is selected here.
