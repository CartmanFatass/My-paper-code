# CBSC-OMRC-B01 CM implementation contract

Status: `PRO_BOUND / IMPLEMENTATION_READY_WITH_NULL_DERIVED_FIELDS`

This is the meaning boundary for implementing the Innovator-selected
`CBSC-OMRC-B01` B/EXPLORE object on `CBSC-DYNAMIC-CACHE-2R-1C-v1`. It is not an experiment
authorization or result. `DIRECTION.md` owns the accepted mechanism and claim ceiling; `.01` selects
the object, `.02` binds literal implementation identity, and `.03` binds lossless raw publication
while reserving derived interpretation for Convergence. `CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md` and
`CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md` are the implementation authorities. CM owns
implementation and direct runtime observation.

## Objective and evidence class

Implement one real online recurrent-PPO comparison that can answer only whether a typed
OWNER/epoch currentness adapter produces a preliminary native-action and native-return signal,
null, instability, control explanation, or adverse counterexample on the declared host beyond:

1. competent same-information `RAW-GRU`;
2. ordinary `PI-GRU`; and
3. equal-work `DERANGED-CURRENTNESS-GRU`.

The implementation must exercise the real environment, policy, recurrent learner, PPO trainer, and
adaptation-free held-out evaluator with nonzero transitions, optimizer updates, and evaluations.
Representation response, tests, generated tapes, Q-loss reduction, or process exit cannot establish
mechanism value.

## Protected scientific meaning

CM must implement the following without substitution:

- one controller, two receiver entities, two persistent body slots, and two execution carriers;
- eight public initialization tokens and 24 opportunities per episode;
- four randomly ordered pre-action event positions plus decision and settlement, giving 152
  primitive transitions per episode;
- OWNER/semantic/capability/body event probabilities `0.20/0.20/0.25/0.50`, body role probabilities
  `0.50/0.25/0.25`, equal OPEN/GATED probability, active request probability `0.85`, and the target
  selection law in the Pro decision;
- the exact evaluator-only validity conjunction over request, neutral flag, addressed/payload
  receiver, content, OWNER, epoch, and OPEN-or-permitted capability;
- the exact native ledger: SERVE `+1.00/-0.30/-0.10`, REFRESH `-0.40` then delayed `+1.00` only for
  active requests, and SAFE_FALLBACK `+0.20/0` for active/inactive requests;
- pathwise arm-independent exogenous tapes and identical 136-bit primitive histories;
- one deterministic 32-bit adapter per arm with no privileged or future input;
- the common `168 -> Linear(128) -> ReLU -> GRU(128) -> actor(4), value(1)` FP32 network with
  exactly `121,349` active parameters and zero-initialized adapter input columns;
- recurrent PPO, not Q-learning: `gamma=1`, GAE `0.95`, clip `0.20`, value coefficient `0.50`,
  entropy coefficient `0.01`, Adam `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay,
  global gradient cap `0.5`, full-episode BPTT, no reward normalization, no auxiliary loss, no replay,
  no target network, and no arm-specific tuning;
- `WAIT` forced on nondecision transitions and masked at decisions; scientific actions masked
  elsewhere; actor loss excludes forced WAIT while critic targets retain event and settlement rows;
- identical interactions, update/minibatch order, optimizer exposure, checkpoints, held-out tapes,
  action-uniform draws, evaluation state resets, and zero model-selection exposure within a seed;
  and
- every individual seed curve, support count, material outlier, counter, and invalidity fact.

No implementation may add reduced validity/currentness/correctness/permission Booleans, oracle
action/value/regret, reward/success, future events, scientific-cell/motif/arm labels, or hidden
environment state to the actor, critic, adapter, recurrent state, or loss.

## Required implementation surfaces

CM may choose file/module boundaries, but the delivered implementation must make these objects
independently testable and auditable:

1. **Dynamic host and typed tape generator.** It must generate initialization, four event slots,
   NOOPs, decisions, settlements, potential outcomes, evaluator truth, causal-twin/motif labels for
   evaluator use only, and arm-independent counter-addressed draws. Host settlement and public
   observation must remain separate from evaluator-only truth.
2. **Four deterministic adapters.** STRUCT, RAW, PI, and DERANGED state updates and emissions must be
   literal, total for every token kind, fixed-work where required, and independently replayable from
   primitive tokens. Adapter state and output must never enter exogenous addresses.
3. **Common recurrent actor-critic.** One implementation and parameter layout must serve all arms.
   Check exact active parameter count, FP32 parameters/activations/optimizer state, zero adapter
   columns, identical update-zero bytes outside adapter semantics, masks, and no privileged critic.
4. **Recurrent PPO trainer.** Preserve complete episode sequences for GAE and BPTT, common sampled
   action uniforms, full checkpointable RNG/optimizer/trainer state, exact exposure counters, and
   adaptation-free evaluation at updates `0,12,24,48`.
5. **Evaluator.** Recompute exact potential ledger, unique oracle action/value, every truth component,
   and the mechanical RAW-competence components. Publish all raw held-out decisions, per-tape returns,
   motifs/twins, supports, and individual curves without AUC, diagnostic rates/effects, arm contrasts,
   thresholds, checkpoint/seed selection, B2 trigger, branch, or polarity.
6. **Artifact and telemetry.** Publish complete-only, create-only manifests with code/config digests,
   literal host/adapter laws, seeds, train/evaluation tape identities, counts, full curves,
   checkpoints or checkpoint digests, raw diagnostic ingredients, validity audits, process-tree peak RSS,
   wall/CPU time, worker/thread occupancy, scratch and durable-output high-water, and failure facts.

## Existing `online/` substrate boundary

The current `PotentialOutcomeTape`, vectorized gather, FP32 validation, checkpoint-complete state,
adaptation-free evaluation, and performance telemetry patterns may be reused after conformance
review. The current `RecurrentQLearner`, epsilon-greedy action path, `BoundedReplay`, Bellman target,
and `OnlineQTrainer` do **not** implement the selected object. They are `PILOT_ONLY` engineering
fixtures and must not be renamed, wrapped, or reported as recurrent PPO or as `CBSC-OMRC-B01`.

## Named runs and maximum exposure

- `B0-INSTRUMENT`, seed `21001`, uses TRAIN episodes `0..7`, one rollout, four PPO epochs, four
  two-episode minibatches per epoch, and 16 Adam steps per arm. After its update-zero checks and
  single rollout, it evaluates stochastic roots `0..3` and motif tapes `0,12,20,28`, for exactly 16
  episode executions per arm. It checks event-order causality, exact ledger/oracle arithmetic,
  masks, literal adapter replay, primitive-history parity, held-out separation, RNG/address
  independence, counters, checkpoint round-trip, publication, and complete telemetry. It has no
  scientific interpretation or model-selection authority.
- `B1-THREE-SEED-SCOUT` uses only `21101,21121,21143`. Per arm/seed: 384 train episodes, 58,368
  train transitions, 9,216 decisions, 48 eight-episode rollouts, four PPO epochs with four
  two-episode minibatches per rollout, 768 Adam steps, and four checkpoints. Each checkpoint has 64
  held-out episodes and 38,912 evaluation transitions.
- `B2-TWO-SEED-STABILITY` uses only `21161,21179`, unchanged, and only after the mandatory interim
  Convergence decision returns `RUN_FIXED_B2_STABILITY`. It cannot replace an earlier seed.
- B0+B1+B2 is capped at two million primitive transitions. There is no sixth seed, selected
  checkpoint, silent budget increase, or adapter/host/reward redesign inside B01.

Immediately before every B0 arm or B1/B2 arm-seed invocation or slice, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require at least 4 GiB
physical and effective available memory. Per invocation, peak RSS is capped at 4 GiB and scratch at
2 GiB; B0 wall time is capped at 30 minutes and B1/B2 at 120 minutes. The complete create-only
durable-output cap is 512 MiB. A pass does not override implementation conformance.

## Raw evidence and interpretation boundary

The result reporter implements `CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md`: canonical raw tape,
truth, policy, curve, motif/twin, support, training, optimizer, resource, and audit records. It must
set every derived AUC/mean/regret, diagnostic, separation/concentration/instability, adverse-seed,
promotion, B2-trigger, branch, and polarity field to literal null. It may compute only mechanical
readability/conformance and the exact nonpolar per-seed RAW-competence Boolean.

Implementation/instrumentation failure, leakage, support failure, unequal exposure, evaluator
overlap, recurrent-reset defect, or RAW incompetence is a blocking mechanical fact, not an
implementation-assigned `INVALID_OR_NONIDENTIFYING` branch and not mechanism polarity. Preserve the
incident. An outcome-blind repair may produce a new create-only attempt under the unchanged object.
After three valid B1 seeds, set `convergence_required=true`; B2 is forbidden until the persistent
Convergence node authorizes it.

## Literal binding and implementation boundary

The recovered `.02` clarification is a complete formed decision bound to the existing B01 object.
It fixes event codes/masks/NOOPs, preamble and initial distributions, all four adapters, PI age,
counter-addressed randomness and common action uniforms, parameter initialization and GRU equations,
full-episode PPO/minibatch order, the 32 motif tapes, B0, checkpoints, artifact transaction, and
resource caps. It reports `REMAINING_MATERIAL_AMBIGUITY=NONE` and `IMPLEMENTATION_READY=YES`.

The complete `.03` clarification resolves the later classifier and aggregation tension with
`METRICS_ONLY_CONVERGENCE_CLASSIFIES`. It does not modify `.02`; it requires lossless raw records,
literal-null derived fields, exact mechanical conformance/RAW competence, absolute B0 nonpolarity,
and mandatory interim/final Convergence decisions. It reports no remaining implementation or raw-
publication ambiguity and intentionally leaves scientific reductions to Convergence.

CM must implement both bound specifications exactly. Only module/class organization,
scalar versus vectorized execution, same-seed device choice under FP32 parity, worker scheduling,
logging, compression/container format, filenames below the run root, progress/plotting, and
episode-local cache layout remain delegated prospective engineering choices. They must be fixed
before an attempt, symmetric across arms, recorded, and meaning-preserving.

Implementation readiness does not authorize result execution. Before B1, CM must first establish
literal-law conformance, full recurrent-PPO rather than Q/replay realization, B0 completeness,
resource admission/telemetry, create-only publication, and every parity audit. B0 itself has no
scientific branch, classifier eligibility, threshold-tuning eligibility, or B2-trigger eligibility.

## Evidence and non-goals

- `DIRECTION.md`
- `CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md`
- `CBSC_LR01_RESULT_INTAKE_20260831.md`
- `CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md`
- `CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/capability_bound_semantic_currentness/cbsc-online-b-innovator-20260901-01/RESPONSE.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/capability_bound_semantic_currentness/cbsc-online-b-innovator-20260901-02/RESPONSE.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/capability_bound_semantic_currentness/cbsc-online-b-innovator-20260901-03/RESPONSE.md`

Technical success cannot establish stable superiority, representation necessity, general MARL,
natural prevalence, paid acquisition, authentication/security, receiver credit, variable population
or lifetime, UAV transfer, safety, deployment, convergence, closure, or any reinterpretation of the
completed exact factorial or LR01.

## Addendum — 2026-09-02 (section-11 recast)

The frozen body above is unchanged. This addendum records, per evidence spec §11.6, which of its
conditions stopped being launch or publication gates on 2026-09-02 under owner decisions 3 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`. The full record,
with `file:line` for every condition, is `CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md`.

Demoted to recorded fields:

- lines 125-127, "It must set every derived AUC/mean/regret, diagnostic,
  separation/concentration/instability, adverse-seed, promotion, B2-trigger, branch, and polarity
  field to literal null" — superseded for **descriptive** quantities only. The runner now publishes
  per-checkpoint held-out returns, held-out action counts and serve rate, training action counts,
  the RAW-competence flags and one exposure line. The interpretive fields (`scientific_branch`,
  `scientific_polarity`, `promotion_eligible`, `b2_extension_trigger`) and every named AUC and
  diagnostic definition stay literal null.
- lines 117-119, the per-invocation 4 GiB RSS, 2 GiB scratch and 512 MiB durable caps — recorded
  budgets. A measured exceedance is published, not refused. Only the 120-minute B1/B2 wall cap stops
  a run.
- lines 129-132, "Implementation/instrumentation failure ... is a blocking mechanical fact" — split
  by decision 7. Missing, unreadable or invalid **resource** telemetry downgrades to
  `resources_unmeasured` with reasons and keeps the attempt valid. **Learner-side** instrumentation
  failure — absent or unreadable worker result, recurrent-reset defect, checkpoint round-trip
  failure, learner leakage, unequal exposure, illegal action, incomplete twins, RAW incompetence —
  still refuses and still quarantines under §6.2.
- lines 110-111, chaining `B2-TWO-SEED-STABILITY` behind an interim Convergence decision — no longer
  a launch condition. B2 keeps seeds `21161, 21179` unchanged, with no replacement, and is sequenced
  by the direction itself.
- lines 156-159, "Before B1, CM must first establish ... create-only publication, and every parity
  audit" — the parity audits, literal-law conformance and real recurrent-PPO realization remain and
  still run; "create-only publication" remains a property of publication but is no longer a
  pre-launch condition.

Unchanged and still gating: lines 23-25 (real environment, policy, recurrent learner, PPO trainer
and adaptation-free evaluator with nonzero transitions, updates and evaluations), lines 115-117 (the
4 GiB admission immediately before every invocation or slice), the protected scientific meaning of
lines 30-60 in full, the leakage and equal-exposure audits, and the §6.2 quarantine of an incomplete
attempt.
