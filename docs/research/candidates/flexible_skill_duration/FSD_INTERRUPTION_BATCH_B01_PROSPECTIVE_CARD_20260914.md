Claim under test: at the accepted early-training Scenario1 exposure, enabling individual policy-gap renewal can change native return beyond the effect of the coordinator's larger joint-row batch.
Binding MARL structure: (b) temporal abstraction or termination; asynchronous skill boundaries change the joint rows and valid credit heads used to train the shared coordinator.

# FSD interruption × batch B01 — allocated finite experiment

**B/EXPLORE: F is allocated by complete Portfolio decision; no fit has launched
at application.** Two independent four-arm blocks (eight fresh original fits)
and necessary implementation/acceptance/intake work are selected in the
[applied investment](../../portfolio/decisions/2026-09-14-fsd-interruption-batch-investment.md).
The fixed submitted version at `cbdac09d5` remains the prospective design evidence.
The owner restart separately restored preparation and the working direction.

## 1. Decision and source of the new question

The completed U decision retains the whole I1280 recipe as a limited optional
scheme, with authentic D0 default. Its five I1280/D0-128 comparisons changed
renewal and batch together. This card asks whether I still improves return over
a freshly trained D0 at the same batch, and whether low-batch controls reveal a
batch effect or interaction. It does not repeat U, buy a sixth unchanged pair,
revive the corridor ladder or use the old unfunded LONG offer.

Adopt the [restart recommendations](FSD_RESTART_RECOMMENDATIONS_20260914.md)
§§1–9 and evidence-spec §§11.7–11.11. The four historical positive package
observations, one adverse package pair, adverse worlds, earlier I128 losses and
greater I wall remain visible through [the U intake](pro_packets/20260912_post_five_pair_use_convergence/INTAKE.md).
They informed this design; they are not new factorial cells or confirmation data.

## 2. Arms and actual implemented factors

| Arm | Individual gap | Coordinator joint-row batch | Common configuration |
| --- | ---: | ---: | --- |
| D128 | +infinity | 128 | D2 route; k=individual cap=team cap=10; team gap infinity; opportunity spacing1; age off |
| D1280 | +infinity | 1280 | same |
| I128 | .25 | 128 | same |
| I1280 | .25 | 1280 | same |

Nominal PPO epochs, learning rates, architecture, reward and all other training
configuration remain the accepted early-exposure recipe. D0 is the D2 infinite-gap
control, not `policy_interruption_mode=off`. All actors retain current primitive
observations, their private GRU and fresh primitive movement actions while skills
are held. No arm receives privileged state, a withheld observation or a held-velocity
control. Six UAV identities and fifty users are fixed; there is no churn/transfer.

The renewal intervention changes decisions, trajectories, segment credit and
valid joint rows. Batch changes optimizer boundaries and masked advantage
normalization groups. The sampler still traverses each valid row for every PPO
epoch. These are mediators of the two implemented switches, not nuisance variables
to equalize after observing results. This study does not isolate a pure online
termination effect at fixed weights or each separate data/normalization mediator.

Source path: host motion/partial observation → per-UAV held-prefix gap decision
and common team clock → selected skill plus current observation into reactive
actor → native reward and primitive-discount segment storage → valid joint rows
and batch grouping → arm-owned learner update → subsequent native trajectory.
Team renewal ends individual segments; one partner's individual renewal does not
reset another's skill/GRU. Episode reset clears that lane's state. Existing terminal
storage/fresh reset and continuing-rollout bootstrap semantics remain intact.

## 3. Endpoint, pairing and independent units

Host is `envs.pettingzoo.scenario1.UAVBaseStationEnv`, six UAVs/fifty users/H500.
Each fit has five 16-lane training rollouts (40,000 team-environment steps), then
one separately constructed, synchronized deterministic 32-world H500 final panel.
Preserve native adapter reward U and report `J = 6*U/500`; learner reward is never
rescaled by that reporting factor. No interim evaluation, checkpoint selection,
extra tuning, model reuse, optimizer continuation or additional evaluation panel.
Training-row returns and existing optimizer/renewal metrics remain descriptive.

Preferred plan: two independent blocks, training bases 772003 and 772103 and
evaluation bases 782003 and 782103. These are prospective identities to be checked
against the registry/artifacts before publication of executable inputs. Within a
block, all arms use the same declared initialization seed and disjoint arm-owned
models/optimizers/RNG state, the same 16 training lane seeds (base through base+15)
and the same ordered 32 evaluator lane seeds (base through base+31). Each evaluator
has isolated RNG, evaluation-mode normalizers and zero optimizer calls. Branching
trajectories may consume different endogenous random draws; identical trajectories
or full stochastic replay are neither required nor claimed. Across blocks all
initialization/world seeds differ and no learned state, buffer or selected checkpoint
is shared. This supports designed block contrasts, not pairing inferred from labels.

Training-level sample size is two blocks, not eight exchangeable arm fits or
64/128/256 independent endpoint episodes. Two blocks provide early replication
and an initial description of training variation, not stable superiority or
adequate power for a small interaction. The old package SD is not the variance
of the new contrasts. No power pilot or universal seed quota is added.

## 4. Primary and supporting contrasts

For each block b, each J below is its arm's mean over its single final panel.

**Primary:** `SI1280_b = J(I1280,b) − J(D1280,b)`, then the equal-weight mean
over the two planned blocks. This directly tests the outstanding high-batch
renewal contribution; it is the same primary for the smaller two-arm option.
Predeclared auxiliaries in the full design are:

```text
SI128_b = J(I128,b) − J(D128,b)
MI_b    = (SI128_b + SI1280_b) / 2
MB_b    = [(J(D1280,b)−J(D128,b)) + (J(I1280,b)−J(I128,b))] / 2
INT_b   = SI1280_b − SI128_b
PKG_b   = J(I1280,b) − J(D128,b)
```

Report every block/arm and both simple effects. The auxiliaries explain the
factorial pattern and cannot replace a disappointing primary. The `/2` fixes
the standard marginal-effect scale; interaction retains the difference-of-effects
scale. Conditional episode variability remains explicitly conditional on the
trained policies. No pooling with historical fits or retrospective subgroup choice.

MEI for the primary is **.01 absolute J**, selected here as a small but potentially
useful service-return increment worth examining against the extra renewal work.
If other reward terms were held fixed, it corresponds to about 1.43 coverage
percentage points at weight .7; it is not a coverage-only endpoint. An absolute
MEI remains interpretable when attainable baseline levels vary; neither old seed
SD nor a uniform repository value defines it. This is a fresh justified choice,
not a retroactive change to any old .01 branch. No formal equivalence claim is
targeted by this two-block exploratory allocation.

Report block contrasts, mean, sample SD and SE, and a descriptive 95% Student-t interval
under an explicitly declared iid-normal working model
for block contrasts (df=1 for two completed blocks), with the uncheckable small-n
model assumption and likely broad precision made prominent. This choice is tied
to this mean contrast, not an automatic rule for n<10. One available block has no
training SD/SE or interval; retain only its bounded observation and conditional
evaluation uncertainty. Do not substitute episode precision for training uncertainty
or present the working-model interval as verified coverage. Bootstrap is not required.

How the result will be interpreted: a primary mean above +.01 is a bounded local
high-batch renewal signal; within [−.01,+.01] is an unresolved/small observed contrast,
not equivalence; below −.01 is adverse for this specific intervention/budget.
Opposite simple-effect signs or a large interaction motivate a narrower dependence
question. Even a precise two-arm zero says nothing by itself about MB. Supported
MB plus the other factorial contrasts is needed for a batch explanation. No branch
automatically parks the direction, switches D0 default, promotes C, adds a seed or
changes the selected endpoint. Record uncertainty and the next useful question.
DM prediction: primary inside the .01 region, low confidence; batch/renewal
interaction may explain part of the old package gains. Owner prediction: not taken.

## 5. Fixed work and ordinary runtime planning

Counts were computed without importing or constructing the learner from AST-literal
runner constants (16 training lanes,32 evaluation lanes,H500,five rollouts).

| Plan | Fits | Train steps | Eval steps | Train episodes | Eval episodes | Models | Batched control calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Preferred four arms × two blocks | 8 | 320000 | 128000 | 640 | 256 | 16 | 24000 |
| Smaller high-batch pair × two blocks | 4 | 160000 | 64000 | 320 | 128 | 8 | 12000 |

The preferred plan has 2,688,000 agent-step observations; these are exposure, not
independent samples. Per arm, five real update stages occur. With M_r valid joint
rows in rollout r, coordinator minibatches are `15*sum_r ceil(M_r/batch)`.
The D0 clock gives 800 rows/rollout: D128 schedules525 calls and D1280 schedules75.
I has at most8000 rows/rollout: I128 schedules at most4725 and I1280 at most525.
Record actual finite calls/rows; fewer optimizer steps do not remove full-row tensor
work or the held-gap/actor/critic/discriminator work. There is no combinatorial
search, nested simulator, exact upper or added validation evaluation.

Recent complete CPU/FP32/four-thread arm observations: 771303 D128=458.80s,
I1280=987.99s; 771203 D128=475.03s,I1280=1042.92s; earlier P72 I128=1297.28s.
These are historical invocation walls, not new four-arm measurements. D1280 wall,
current contention, support and complete study cost remain unknown. Working per-fit
plans are D128=900s, D1280=900s, I128=1800s and I1280=1800s: preferred summed
native plan 10800s and smaller plan 5400s. These are adjustable engineering forecasts, not
scientific hard caps or reasons to stop at a modest overrun. Support is ordinary
source/check/review/launch/collection work with unknown wall; no separate mandatory
profiling or short support timer is imposed. Preserve any actual platform limit.

Remote-first execution uses the configured WSL node, CPU FP32/four threads, exact
committed source and detached supervisor, fresh destination memory admission per
fit and one DM-owned native Monitor. Do not change to GPU/mixed precision for
convenience. The proposed scientific boundary is the selected fit count and
five-rollout/sole-final endpoint; a failed/missing primary is retained, with zero
automatic replacement fits/retries. All original selected arms/blocks run regardless
of preceding score, subject to real resource/integrity failure. Complete every
available contrast only from its intact required operands; distinguish partial
own-arm/high-batch-pair evidence from a complete four-arm/two-block result.

## 6. Minimal prospective L0 and baseline relation

Deliverable: one explicit independent renewal/batch binding and block-aware primary
publication on the existing UAV collector/evaluator. Owned checkout is
`C:/Projects/HMASD-worktrees/codex-fsd`; prospective owned paths are
`scripts/run_fsd_uav_individual_renewal_b01.py`, one new factorial entry/reducer,
`tests/experiments/candidates/flexible_skill_duration/interruption_batch_b01/`,
and this direction's records. Default old bindings and their exact historical
source remain available. Decouple only the arm/batch configuration required by
this card; do not duplicate the full runner or rewrite shared HMASD core.

Protected semantics: §§2–4, per-arm model/RNG/buffer/evaluator ownership, terminal
storage/reset, primitive-time reward/credit, single final endpoint and object/seed
identity. Focused acceptance covers all four configuration mappings in learner and
evaluator, actual batch consumer, primary/contrast scaling, complete/missing operand
handling and no episode-as-training-replicate path. Required independent high-risk
review covers changed scientific/configuration/RNG/primary semantics; DM accepts
and repairs directly. No model-bearing smoke, extra performance panel, profiler,
all-history replay or blanket suite is a preparation/launch prerequisite.
Engineering Scope §4: none needed. The applied F investment includes the necessary
bounded implementation/check/review/collection and preservation work. No additional
model-bearing test or empirical invocation is implied.

Same-host baseline preparation proceeds with this design. The existing baseline
record is exposure/integrity-only and gives no tuned headroom. `hmasd/baselines.py`
offers a flat MAPPO-style switch, but its existence is not an accepted Scenario1
integration/result. Direct HMASD fixed-k (`off`), that flat baseline, and D2-D0 must
be mapped separately for actor/critic information, reward/normalizers, training
rights, endpoint and tuning exposure. This grant proposal includes zero flat-MAPPO
or direct-HMASD fits and zero baseline tuning; their missing comparison limits
claims about overall method value. A bounded baseline card is a parallel preparation
deliverable under the restart, not a reason to suspend funded direction work.

## 7. Investment options and current continuation

F (recommended): fund the complete four-arm/two-block B above, eight original fits
and the necessary implementation/acceptance/collection; useful because it estimates
the primary, both simple effects, MB and interaction from new concurrent design.
S: fund only I1280/D1280 for two blocks, four original fits with the same primary;
lower cost, but no batch attribution, low-batch or interaction conclusion.
N: decline this empirical allocation while the DM completes the separately bounded
same-host baseline design preparation; no lifecycle/default change, no fresh fits.

Portfolio has selected F for this finite new investment. Renewal/batch
controls are object-tier choices inside the accepted native individual-renewal
mechanism. I128 is a predeclared comparator in a new factorial question, not another
unchanged early-pair extension under P74. No new family, recast or specification
exception is proposed. The DM executes the complete conforming F decision directly.
Root integration/ACK is not an execution gate.

At the original preparation: new fits/models/environment steps/optimizer calls/
evaluations=0; tests/profiling=0; Pro Sends=0. The subsequent single accepted request
is completely archived and intaken; all empirical counts remain zero at application.
Current source/document reads and prospective configuration arithmetic create no
empirical result. No numerical reanalysis of historical primaries was performed.
Next: implement the minimal selected bindings/reducer, complete focused acceptance
and independent high-risk review, then execute the selected originals directly.

## 8. Execution implementation and acceptance record

The selected L0 in §6 is implemented in `scripts/run_fsd_interruption_batch_b01.py`
plus the existing shared collector. Its `fit --arm D128|D1280|I128|I1280 --seed
772003|772103` binds one original; evaluation seed is respectively782003/782103.
`factorial_arm` records the full arm while shared `arm` retains I/D0 renewal-path
identity. The explicit batch keyword reaches both learner and separately built
evaluator. The shared legacy defaults/caps remain unchanged; this new object passes
`caps=None` and records ordinary wall plans separately. It calls the existing
training, terminal storage, update and final-evaluation code without replacing it.

The same entry's `reduce` reads original summaries, preserves every block/arm and
forms only contrasts with intact operands and matching non-factor settings.
SD/SE/interval are over the two block contrasts, not endpoint episodes. With one
operand-complete block it publishes its bounded mean but no training interval;
missing low-batch arms do not erase an intact high-batch primary. No provenance
guard, framework, core code change or additional empirical invocation is added.

Focused acceptance uses synthetic-only config/RNG/collector/evaluator seams and
complete/missing-operand publication in
`tests/experiments/candidates/flexible_skill_duration/interruption_batch_b01/test_factorial.py`,
plus directly relevant existing default/final/deadline checks. Tests replace real
model and host constructors. The actual batch consumer remains
`hmasd/agent.py`'s D2 coordinator update and `hmasd/utils.py`'s valid-row sampler;
the published previous synthetic1281-row sampler traversal is reused as unchanged
coverage. No real model-bearing smoke is selected. Independent high-risk review
will inspect the reachable scientific/configuration/RNG/reducer change before launch.
Engineering Scope §4: none. Actual check/review results and exact execution bindings
are appended here when completed, rather than inferred from implementation.
