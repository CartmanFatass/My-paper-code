# FSD B01 P34 implementation and readiness intake

Date: 2026-09-08. Decision tier: object, under the existing P25 PRO_FINAL question
and P34 implementation/readiness assignment. **Implementation accepted; no
scientific result or runtime allocation.**

## 1. Assignment, return and source reconciliation

[P34](../../portfolio/handoffs/2026-09-08-p34-fsd-learning-implementation.md),
published at `f8355ca8f5a477eb209d7fcf85472db992ceb189`, allocated the complete P30
implementation, synthetic checks and independent source review. It explicitly
superseded P30's no-coding boundary and retained zero real model/host/learner/
evaluation/Pro invocation and no fourth CM comparison. Root subsequently returned
the main integration for this same DM's card/intake/brief/audit and exact next
allocation request; scientific runtime remains unallocated.

The reused CM `fsd_cm_baseline_a01` returned source
**b3f86bb28879db239b07291c39d93a1c494abe50**, pushed on `codex/fsd`. Root integrated
its three owned paths at main **0e731dbbd30ee6ec68f70f0d54e40a0dd3fc2c3f**:

- `scripts/run_fsd_native_renewal_learning_b01.py`: 445 lines.
- `tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py`:
  533 lines, synthetic production-boundary tests.
- [Technical acceptance](FSD_NATIVE_RENEWAL_LEARNING_B01_TECHNICAL_ACCEPTANCE_20260908.md):
  source/check/review facts and future CLI syntax.

The designated checkout remains `C:/Projects/HMASD-worktrees/codex-fsd`, branch
`codex/fsd`. Before CM work, merge `e1549c8bee6777720e083255dca5777853c08feb`
reconciled P34 and preserved the full starting source
`ebce42e23e8a86b4e8d44f840441d166828fbe54`; the only audit conflict retained all
three FSD rows and the other main rows. After CM return, clean merge
`46770dc1cded0b5cd55fb9728008d3fca54fd56a` reconciled Root's main integration.
Both merges were immediately pushed. The new runner/test and relevant
E0/E2/E3, config, learner and host source surfaces match the reviewed code across
the source/main integration; no doc-only commit changes its scientific meaning.
Accepted historical A01 source remains in this checkout. The new runner directly
uses E0/E2/E3/host helpers and does not import the A01 runner.

## 2. What I checked and the acceptance rule

Checked the technical return against [card §§2–7](FSD_NATIVE_RENEWAL_LEARNING_B01_SCIENCE_CARD_20260908.md)
and [CM specification §§3–6](FSD_NATIVE_RENEWAL_LEARNING_B01_CM_SPEC_20260908.md),
the actual changed functions, focused regression assertions, final raw test output,
the independent review/recheck and the source integration diff. I did not rerun
the CM's tests or construct a model/host during intake.

Controlling CM specification acceptance rule, verbatim:

> Acceptance is runnable changed code, trustworthy focused check/review evidence,
> readable true future exposure and correct claim/stop semantics. Test success is
> engineering conformance; it is not a learning result or a scientific launch.

Controlling evidence §5.2 rule, verbatim:

> A B run MUST exercise the real environment, policy, learner, trainer, and evaluator and report
> nonzero transition, update, and evaluation counts when it is called an algorithm experiment.

This return meets engineering acceptance. The second rule is **not yet exercised
by a real run**. Synthetic counts and fake optimizer calls are not learner
exposure, native-return evidence or a B result branch. Evidence §11.8 controls
the proportionate checks and dependency-based handling of failures; the four
§11.4 launch conditions are retained without an added smoke, profile or review gate.

| Boundary checked | Direct source/check evidence and bounded finding |
| --- | --- |
| Fresh setup | Existing large/D2 config builder, seed770203, CPU/four threads before `HMASDAgent`; arm-local constructors and ValueNorm. The synthetic constructor check uses the real config builder with a fake model/adapter. |
| Action→reward→storage | `applied_mask` copies the public H flag only after t0. `collect_training` passes original actions/step_data and the adapter's actual float64 shared reward and next inputs into storage. The paired fake rewards change with applied masks while sampled metadata stays intact and non-aliased. |
| Episode/credit boundary | The real terminal transition is stored first; both next policy values come from reset. Tests use distinct terminal/reset sentinels, no public-renew internal reset, five consumed episode blocks and updated fake policy state on later rollouts. Internal D2 sampling/segment credit source is unchanged. |
| Update/exposure | Real `agent.update` precedes metric capture and clear. Existing counters count actual optimizer calls; raw segment lengths and D2 rows are captured before clearing. Tests cover unequal calls, a legitimate zero and first/final parameter displacement. |
| Independent evaluator | E2 construction, active-module/ValueNorm synchronization, lane reset and deterministic scoring sit inside E0 RNG preservation. Tests show separate mutable state and zero evaluator optimizer calls. |
| Primary/failure output | Float64 full/post returns, paired ddof1 SE and own-opportunity loss are measured independently of reward-classification diagnostics. Missing G affects reference claims; missing/damaged learned endpoints prevent the complete learning pair. |
| Complete cap | The clock precedes heavy imports; cooperative checks cover ordinary boundaries and publication. An external complete-command timeout remains required for indivisible updates. No actual 900/900/60s invocation has been observed. |

The source trace follows regional lease invalidation → current public/arm-owned
inputs → authentic internal skills and actor action → selected applied mask →
actual reward/next inputs → internal segment storage/update → subsequent learned
policy. This establishes implementation correspondence, not an empirical mechanism
effect. No shared/core/historical semantics were changed. The required finite-value
check sees numeric D2 sampled metadata; raw gap diagnostics are not substituted for
sampled actions or fed back as public renewal labels.

## 3. Counts, receipts, review repairs and engineering scope

Final focused suite: **18 passed**, pytest **3.33 s**, complete process
**4.4069052 s**. The raw output read at intake is
`temp/directions/flexible_skill_duration/test/b01-learning-final-check.txt`;
the exact command and earlier check outcomes are in the technical acceptance.
The initial run was 13 passed/1 failed (pytest8.28s), from an inconsistent fake
horizon/cap; its fixture used the existing horizon-aware helper in the correction.
The repair run passed18 in4.2460821s; the final run strengthened own-reward and
non-alias assertions. No production constant changed and the total focused-check
work stayed below300s. Warnings were the existing cache/Pyparsing warnings.

The same independent `fsd_integration_review` reviewer found two material
publication defects, both returned to the same CM and repaired before acceptance:

1. Initial norms or D2 metrics containing NaN/Inf could poison JSON before failure
   publication. They are validated locally before summary assignment. Main-path
   synthetic failures now retain valid JSON, failure status and true completed
   construction/transition/update/optimizer counts.
2. Truncating the only summary could destroy the previous boundary on interruption.
   The writer now closes an ordinary same-directory temporary file before
   replacement. Interrupted and nonfinite writes preserve the prior readable JSON.

The reviewer rechecked the repairs and additional evaluator/comparison fields:
**no material findings remain**. Its inspected regression run was18 passed in
4.246s; it did not duplicate execution. The final strengthened test run is also
18 passed. I read the actual repair code and regression assertions during intake.
No additional check was warranted by the unchanged source integration.

No ENGINEERING_SCOPE_SPEC §4 machinery was added. New non-test source is445 lines,
below both the600-line runner and2,000-line attempt limits. Ordinary replacement
of one summary preserves required output; it is not a registry, retry loop,
tamper-evidence system or new supervisor. No budget breach was observed. The
record makes no real-run resource or throughput claim.

Current scientific exposure for P34 and this intake is **0** real model or
HMASDAgent constructions, checkpoint loads, training starts/transitions/updates,
scientific host/evaluation episodes and Pro Sends. No run root, process handle
or admission for the prospective invocation was created. Test artifacts remain
under the direction's `test/` root and are not relabelled scientific output.

## 4. Scientific reading, prediction and owner flags

There is no new native-return observation and no B sign to score. The prior
low-confidence prediction (H−C >.01, G−H >0) remains on record; owner prediction
is `not taken (unattended)`. The [Chinese owner brief](../../portfolio/owner/briefs/flexible_skill_duration/2026-09-08_B01-P34-readiness.md)
explicitly describes implementation readiness, not learning evidence.

Claim ceiling remains one paired training seed's early total-control-package
comparison after five rollouts. The supplied public rule is not learned;
episode SE is conditional on the one trained pair. No unique actor/credit/team
attribution, D0 advantage, convergence, stable superiority or UAV transfer follows.
The strongest existing support is selected-artifact A01 H−C +.26935. Its G−H
.16403, H's higher wrong-role losses on altered opportunities, all six competent
E3 learning losses and E4's public-null explanation remain contradictions.
Tuned generic headroom remains absent. The new complete runtime and segment-
dependent optimizer work remain unknown, with no extra cost experiment selected.

No material critic dissent was overridden; the technical findings were fixed.
No new card, direction decision, recast, Portfolio disposition or owner-console
item is required for this ordinary acceptance/request. Existing new-card item
`20260908-fsd-001` and its evidence remain. Its original `audit...#L5` points to
the P30 publication at8ddd85d7a; main's merged current audit places that row atL8.
That unqualified line-pointer drift was reported to Root; no inbox file was edited
by hand and it does not change authorization or the card. This intake and its own
audit rows identify the current decision directly. Owner-review queries returned
no unapplied instructions; relevant FSD ledger owner cells are empty.

## 5. Decisions this intake produces

1. **Object technical acceptance.** Options: (a) accept the reviewed implementation
   and integrated source at its engineering ceiling; (b) return a concrete remaining
   source/check defect; (c) claim a scientific result from tests. Recommend/select
   (a): changed boundaries and both publication repairs have direct source/test
   support, with no remaining material finding.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **Object next-rung request.** Options: (a) return one exact runtime-allocation
   request for the already selected C/H/G B; (b) add a model/cost probe, checkpoint
   panel, seed, arm or longer budget; (c) stop preparation without a new concrete
   defect. Recommend/select (a). This prepares the task Portfolio must allocate;
   it does not allocate capacity or execute a command locally.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

Rows are appended to [the September8 audit](../../portfolio/audit/2026-09-08.md).
No P1/P2 proposal is created for this ordinary within-card next-rung request.
P25 already selected the direction question; no new Pro round is a launch gate.

Intake publication checks passed without importing the runner: static AST values
and all three future argument lists match the accepted source; count/cap arithmetic
matches the existing machine record; fourteen local links and both verbatim rules
resolve; the Chinese brief has330 characters and the six required headings. The
reviewed source is unchanged in the intake checkout and main integration. The
prospective local scientific root does not exist, and relevant owner cells are empty.

## 6. Exact next allocation need — requested, not allocated

**Requested task:** allocate exactly one C_train/H_train/G B01 panel using the
reviewed implementation, its collection/technical acceptance and DM intake. Reuse
the same CM/DM and FSD checkout; Root observes accepted detached handles through
the existing EXPERIMENT_MONITOR/ROOT_OPERATIONS route. No new agent role or branch
is needed. This is the next observation that can decide whether the supplied
renewal package has a useful early-learning native difference; another fixed-
weight panel or exact diagnostic would not answer that learning question.

Fixed requested source: `b3f86bb28879db239b07291c39d93a1c494abe50`, with main
integration `0e731dbbd30ee6ec68f70f0d54e40a0dd3fc2c3f` confirmed equivalent on the
runner and its relevant dependencies. Use the configured remote-first
`wsl_4070` CPU route (`hmasd-wsl-node`, interpreter
`/home/wu/.venvs/hmasd/bin/python`), an exact-source detached worktree and existing
`agent-task`. CPU/four Torch threads, float32 learner and float64 host/reward
remain fixed; host portability/fallback stays exactly card §6. This intake
performs no remote probe, admission, launch or migration.

Prospective output root, not created:
`temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203`.
The exact runner arguments below use that root and fixed source. Within the
future detached command, use the configured interpreter in place of `python`:

```text
python scripts/run_fsd_native_renewal_learning_b01.py --policy G --seed 770203 --launch-sha b3f86bb28879db239b07291c39d93a1c494abe50 --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/G
python scripts/run_fsd_native_renewal_learning_b01.py --policy C --seed 770203 --launch-sha b3f86bb28879db239b07291c39d93a1c494abe50 --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/C
python scripts/run_fsd_native_renewal_learning_b01.py --policy H --seed 770203 --launch-sha b3f86bb28879db239b07291c39d93a1c494abe50 --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/H --c-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/C/summary.json --g-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b01_770203/G/summary.json
```

Execute G/C/H once each, in that order. Each requires fresh physical and effective
memory >=4 GiB on its executing node, with the existing `admit-memory --out ...`
immediately joined by `&&` to its invocation. Record the exact admitted command,
node, receipt and detached handle at future launch. A complete-command OS timeout
must bound interpreter/import, setup, training, evaluator, required paired
arithmetic and closed-file publication: **G60s, C900s, H900s; summed1,860s**.
The runner's cooperative timer cannot alone interrupt a long optimizer call.
Nothing needed to complete a result is charged to a follow-on invocation.

The [existing machine count/cost record](FSD_NATIVE_RENEWAL_LEARNING_B01_EXPOSURE_AND_COST_20260908.json)
remains the projection source: one paired training seed, two real training starts,
2×5×16×400=64,000 training transitions/160 episodes; C32/H32/G32 final evaluation
totals96 episodes/38,400 steps; combined102,400 steps/614,400 agent observations.
Two learner and two evaluator agent constructions are charged. Actual network
optimizer calls, coordinator/segment counts and first/final displacement must be
read from the run. No nested search is present. Ordinary summary writes are
included in the caps; they add no scientific samples.

Per C/H planning law remains `1.15*[5*(64.6+.769*M_arm)+.46*32]`, with new effective
M unmeasured. Historical scale anchor505.86596735480975s per learned arm and prior
G.27s are only anchors. The selected caps express this question's budget, not
proved feasibility. No new calibration, profile or old-panel replay is requested.

Stop each invocation at completion, its cap, nonfinite learning/primary values or
a concrete reward/information/storage/update/primary defect. Preserve every
outcome and actual counts. A failed G does not prevent the independent C/H calls;
a failed learned arm prevents complete H−C polarity but does not erase an
independently trustworthy companion/G result. No automatic retry, stitched
completion, shorter declared five-rollout result, alternate seed, extra endpoint,
second seed or cap increase is allocated by this request. A full valid adverse
result follows the card's reading and is retained. Optional resource missingness
is labelled; damaged primary claims follow their actual dependency.

Return the actual C/H/G summaries and complete-wall/receipt facts for CM technical
acceptance and DM E0 scientific intake, with H−C mean/32 paired values/conditional
SE, full/post G gaps, own-opportunity wrong-role losses and true learner exposure.
This request selects no result sign, next object, lifecycle, priority or UAV entry.
