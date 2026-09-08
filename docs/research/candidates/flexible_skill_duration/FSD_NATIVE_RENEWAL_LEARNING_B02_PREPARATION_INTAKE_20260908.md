# FSD native-renewal learning B02 — P40 preparation intake

2026-09-08. **Object-tier preparation complete:** one prospective independent-pair
B/EXPLORE card with training770303/evaluation770304 and a complete bounded CM
seed/input specification. No implementation, model/host/learner, diagnostic fixture,
training/evaluation, scientific runtime, Pro Send or CM dispatch occurred.
No new empirical prediction is scored. B01 retains its original one-pair result.

## 1. Assignment, source and focused inspection

Root's published [P40 handoff](../../portfolio/handoffs/2026-09-08-p40-fsd-independent-pair-preparation.md)
at main6717784f9 supplies the authority. It supersedes the prior successor-
preparation stop only and explicitly allocates no code or runtime. Current Portfolio
pointer selects this independent-pair preparation; the direction's ACTIVE/HIGH
lifecycle/priority is unchanged. No Portfolio file is edited here.

The designated checkout remains `C:/Projects/HMASD-worktrees/codex-fsd`, branch
`codex/fsd`, clean at entry27980200fb229b5bb1fccac456939eb821268f00. P40 main inputs
merged without conflict at **ab6426ef6ca0267d7b5ca7c833401d6348ab07fb**, immediately
pushed. The B01 runner/test bytes match accepted scientific source
**b3f86bb28879db239b07291c39d93a1c494abe50**. Existing evidence, P38 command bytes,
source and unrelated work are preserved. This is the complete starting code for
the proposed CM task, with the new card/spec commit to be reconciled before dispatch.

Focused inputs were B01 [intake§6](FSD_NATIVE_RENEWAL_LEARNING_B01_INTAKE_20260908.md#6-decisions-this-intake-produces)
and [result](FSD_NATIVE_RENEWAL_LEARNING_B01_RESULT_EVIDENCE_20260908.md), integrated
mainbdf9d024b2e626874445dcd1e912efddf6bc2af4; its card§§2–7 and CM spec; actual
runner seed/constants/base_summary/build_learner/final_evaluation/main call sites;
the existing synthetic builder, E2 evaluator/RNG, main-panel and metadata test
entry points; applicable root/docs/scripts/tests AGENTS and CM independent-review
wording for RNG/result identity. The shared collector, learner/core and full
historical review were not re-explored or executed.

Evidence-spec§4,5.2,11.4,11.7–11.9 govern this B preparation. In particular§11.8.3:

> When the question is learning performance, prefer a small follow-up with one or two new independent training seeds using the same comparison and evaluation.

The question remains whether the native package signal depends on one training
seed. A new real pair has direct decision value; additional episodes of the old
learners do not create an independent training observation. An exact diagnosis,
policy-class maximum or new baseline census would ask a different question and
is not preserved as an upstream prerequisite. No such work is commissioned.

## 2. Fixed card, keys, reporting and interpretation

The new [B02 science card](FSD_NATIVE_RENEWAL_LEARNING_B02_SCIENCE_CARD_20260908.md)
first states its claim and binding temporal-abstraction structure. Training770303
seeds Python/NumPy/Torch, config and own training hosts separately for C and H;
evaluation770304 supplies the new common C/H/G endpoints. `git grep -l -w -E '770303|770304' 6717784f9 -- .` returned exit1 with no matching files/error before
selection. This is a whole-identifier search of the tracked starting snapshot,
not an outcome-dependent seed search. It creates no scientific exposure.

The [machine record](FSD_NATIVE_RENEWAL_LEARNING_B02_EXPOSURE_AND_COST_20260908.json)
retains the exact query/keys, training blocks0–15 through64–79 and evaluation
IDs0–31. Both masters are distinct from B01's770203/770204. Paired initialization
and exogenous keys do not share subsequent learner state, trajectories or updates.
No checkpoint, old result array or B01 summary is a runtime input for the fresh pair.

The original G/C/H semantics, large N6/K2 host, own real learning, five16×400
rollouts, deterministic final32 per policy, CPU4/FP32 learner/FP64 host and reward,
MEI.01 and actual exposure/role-loss reporting remain. All four outcome branches
are fixed before new output: above-MEI recurrence, small/resolution-limited,
opposite sign, or incomplete/damaged required pair. A smaller above-.01 result is
still shown with its actual magnitude. No all-positive, matching-magnitude or
retention-fraction rule is added.

B02's32-episode SE is conditional on **one new trained pair**. Reporting is selected
now: B01 and B02 have separate per-pair rows; there is no pooled64-episode SE,
best-pair selection, combined mean or chosen-after-output uncertainty estimator.
This preserves B01's full+.49738281249999894/SE.00864640484198601 and its branch
regardless of the new result. Neither two positive pairs nor one pair's adverse
result would justify stable superiority or whole-family closure.

MEI stays.01 absolute reward for its existing service/reset scale reason. Tuned
generic baseline/upper-reference headroom remains absent; B01's full/post G gaps
.021184895833334313/.0187317251461998 remain conditional reference facts. They
inform the interpretation but impose no baseline-tuning gate.

## 3. Chosen minimal implementation design and acceptance

The [complete CM spec](FSD_NATIVE_RENEWAL_LEARNING_B02_CM_SPEC_20260908.md) freezes
one thin B02 entry point and explicit keyword bindings through the shared runner's
summary, learner setup, evaluator setup and main. B01 keeps its current defaults.
The wrapper does not mutate shared globals or duplicate the445-line learning path.
This directly handles the actual input limitation when reusing the unmodified CLI for another
pair: it fixes770203/770204 in both consumer calls and metadata, so changing only
an output path/label would not generate the intended independent observation.

The specified propagation covers all Python/NumPy/Torch seeds, training adapter,
learner config, G host, evaluator config/master and object/card/seed metadata.
Existing comparison checks retain their own missing/mismatched C/G behavior;
no new validator, registry, provenance guard, general CLI configuration layer,
checkpoint/retry service or cross-pair aggregation is added. Card scope§4: none.

Future checks reuse all18 synthetic B01 cases and add only new binding consumers,
evaluator/RNG preservation, actual thin-wrapper dispatch, no leftover B02 state
in a later B01 call, and cross-pair metadata rejection with independently preserved
endpoints. They retain the existing fake-only model/host guard and <=300s total
focused suite. Independent source review is limited to changed RNG/result identity,
using the same available reviewer through the existing CM. No test or diagnostic
fixture is executed during P40 preparation. Real runtime remains unallocated even
when the later code task passes these checks.

The five-item implementation handoff in CM spec§7 includes deliverable, exact owned
paths/call sites, preserved semantics, complete acceptance and budget/stops. The
proposed executor is the same `/root/fsd_cm_baseline_a01`; it was not dispatched
here. P40 explicitly requests no fourth CM comparison after the completed three
batches. This is not a reused historical comparison task or silent bypass.

## 4. Counts, cost and zero present exposure

Known prospective algorithm work is2 arms×1 new paired training seed×5×16×400 =
64000 stored transitions/160 training episodes/10 stages, plus3×32×400 =38400
scoring steps/96 endpoints. Combined exposure is102400 host steps,614400 agent
observations, four agent constructions (two learners/two evaluators),4800 learned
controller batches and400 G batches. No nested candidate/trajectory search or
extra endpoint is present. Actual optimizer/segment/coordinator counts remain
unknown until real execution; stages/rows/buffers are not optimizer counts or M.

Proposed complete caps are G60s,C900s,H900s, sum1860s, including admission through
closed-file publication. B01 actual2.47/371.89/333.89s and708.25s sum are explicit
anchors, not feasibility guarantees for the fresh seed. The historical cost law
retains unmeasured new M; no profile, calibration or additional cost experiment
precedes the learning question. Any future changed-boundary validation is separate
synthetic engineering work, not another scientific sample or production-model probe.

P40 present exposure is **all zero**: code changes, CM dispatches, models, checkpoints,
hosts/diagnostic fixtures, learners, training/evaluation/optimizer calls, scientific
invocations and Pro Sends. Python calculated known counts and read committed
seed/source facts only; it imported no learner or host. No runtime root, handle,
admission or command script is created. There is no engineering budget breach.

## 5. Scientific interpretation, source reuse and prediction

Strongest support is B01's complete+.49738 native gap after actual fresh learning
within708.25s. Strongest contrary evidence is its one-pair scope, G's remaining
advantage, weak component control C, and the older competent E3 losses/E4 public-
null account. This new B does not replace a D0 comparator or rescue earlier results.
It asks about recurrence of the supplied package, not whether the rule was learned.

The question/comparator is unchanged from accepted B01. Reuse the verified local
ACAC/UTE temporal-action distinctions already recorded in B01 intake§4 and P25's
PREPARATION_INTAKE literature section: supplied applied renewal, intra-skill actor
behavior and high-level termination are different variables. No fresh literature
search, additional baseline/architecture or novelty claim is needed for this seed
follow-up. The existing evidence keeps the card's package wording and prevents
relabelling a future positive as learned termination or a unique credit effect.

Prospective DM prediction is modest-confidence H−C>.01 with G−H still positive,
without a magnitude forecast. There is no new result to score. Owner prediction:
not taken (unattended). Primary and direction owner reviews were empty at this
clean boundary, with no populated FSD audit override. The standing delegation
continues; no owner reply is invented or awaited.

## 6. Decisions this preparation produces

1. **Fresh card/keys/reporting — object tier.** Options: (a) accept B02 at770303/
   770304 with the four prospective branches and separate per-pair reporting;
   (b) reuse old keys or add old-pair evaluation; (c) defer for exact diagnosis or
   a stronger class. Recommend/select(a): it targets training-seed dependence at
   bounded cost without changing the accepted comparison. **Owner-delegated
   decision (unattended, 2026-09-03 instruction): (a).** Create the P2 new-card item
   with this evidence/decision packet and actual auto-applied choice; do not wait
   for an owner reply. The new card fixes no new scientific result.
2. **Prepared coding need — object tier.** Options: (a) return the complete bounded
   seed/input implementation handoff to Root; (b) implement/dispatch/launch during
   preparation; (c) duplicate the full runner or broaden the algorithm. Recommend/
   select(a): explicit parameter threading and one thin entry point suffice, with
   focused consumer/RNG/identity checks and existing independent review. **Owner-
   delegated decision (unattended, 2026-09-03 instruction): (a).** No CM or scientific
   invocation is started. Portfolio supplies the next named implementation task;
   Root integrates this preparation and dispatches only that task.

建议接受这张前瞻性B02卡：用新的训练和评价种子检验同一控制方案的差距是否再次出现；本次只交付卡和最小实现规格，不修改代码、不运行学习。

Both choices appear in the existing audit. A P2 item is due for the new card;
ordinary preparation/prediction facts need no separate items. No valid new result
exists, so a new Chinese valid-result brief is not due. B01's brief remains linked
from its unchanged intake. No family/recast/lifecycle/priority/UAV decision occurs.

## 7. Exact return and remaining task

Return this card/spec/preparation/machine record plus its new-card owner item and
audit to Root for integration. The exact next need is CM spec§7's one implementation
assignment to the same CM in this checkout. New accepted source must contain the
B02 entry point and explicit seed propagation before any future runtime binding.
No launch SHA/handle, production fixture or runtime allocation is fabricated now.
The same DM handles focused corrections; no other scientific task is selected.

The owner-console CLI created P2 new-card item
[20260908-fsd-002](../../portfolio/owner/inbox/2026-09-08/20260908-fsd-002.json),
auto-applied accept for the prospective card/preparation only, with its Chinese
packet and audit row30. No owner reply or implementation/runtime allocation is
represented by that choice.

Publication checks passed: machine arithmetic/seed selection, all four actual
seed/identity consumer mappings,19 local links, owner packet quotes/context and
ledger reference agree. B01 evidence, scientific source/tests and governance are
unchanged; the proposed B02 script and scientific root do not exist. No production
object or test fixture was constructed. Final reviews in both checkouts and FSD
audit owner cells were empty. Git whitespace checks passed.
