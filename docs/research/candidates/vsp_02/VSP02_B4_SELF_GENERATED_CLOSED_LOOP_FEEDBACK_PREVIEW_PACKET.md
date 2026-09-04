# VSP02-B4 Self-Generated Closed-Loop Feedback — External Pro Pre-Freeze Preview

## Review identity and status

- `direction_id`: `CAND-VSP-02`
- `candidate_id`: `CAND-VSP-02@adversarial-revision-v8`
- `revision_id`: `adversarial-revision-v8`
- `provisional_treatment_id`: `VSP02-B4-SELF-GENERATED-CLOSED-LOOP-FEEDBACK`
- `review_kind`: `INSPIRATIONAL_PRE_FREEZE_PREVIEW`
- `conversation_intent`: `NEW_CONVERSATION`
- `later_convergence_intent`: `EXACT_CONTINUATION_OF_THIS_CONVERSATION_AFTER_ACCEPTED_B4_RESULT`
- `review_access`: `GITHUB_CONNECTOR_ONLY_AFTER_ROOT_PUBLICATION`
- `review_scope`: `SCIENTIFIC_IDENTIFIABILITY_NOT_CODE_REVIEW`
- `scientific_status`: `PROVISIONAL_CANDIDATE_NOT_FROZEN`
- `authority_boundary`: External Pro may criticize the proposed single-axis identifiability. Explorer retains direction-local advisory freeze authority; Code Manager retains implementation, runtime, and technical-acceptance authority; Root retains publication, relay, and Git authority.

This packet requests one bounded pre-freeze criticism. It does not authorize implementation, execution, treatment freeze, B3 reuse, a conclusion-bearing claim, promotion, or retirement.

## Accepted predecessor boundary

B2 found that the direct correct-label and inverse-label paths acquired their corresponding cue-conditioned mappings in `5/5` paired units, while `RL_ORIGINAL` acquired the correct mapping in `0/5`. This supports only a local learner-path contrast under B2's direct-supervision bundle.

B3 then changed only lifecycle actor-credit sign to the oracle-correct sign while retaining each bridge arm's realized original-form absolute advantage magnitude. `CREDIT_SIGN_BRIDGE` and `RL_ORIGINAL` were both exact-correct in `0/5` paired units, with all B3 validity, activity, exposure, noninterference, and artifact gates passing. B3 therefore falsified sign-only sufficiency at the realized B3 magnitude on that frozen shadow route. B3 is exhausted and is not available for rerun, rescue, tuning, extension, reinterpretation, or post-result intervention.

## Proposed single-axis causal discriminator

The sole manipulated cause is the edge from the oracle-sign learner's current parameters to the source of its future training batches:

```text
SELF_FEEDBACK: oracle-sign parameters_t -> own batch_t -> oracle-sign update -> parameters_t+1
SHADOW:       RL-original parameters_t -> batch_t -> oracle-sign shadow update
```

The proposed treatment has three fresh arms within every fresh paired root unit:

1. `RL_ORIGINAL_GENERATOR`: the non-claim-bearing nuisance generator, using the unchanged original actor-critic objective and the unchanged behavior-mixture law. It generates the immutable batch consumed by the shadow arm.
2. `CREDIT_SIGN_SHADOW`: the matched feedback-cut comparator. It retains B3-form lifecycle actor credit `c_i * detach(abs(G_i - b_shadow(h_i)))` and consumes the frozen `RL_ORIGINAL_GENERATOR` batch.
3. `CREDIT_SIGN_SELF_FEEDBACK`: the candidate. It uses the identical oracle-sign coefficient, loss assembly, and behavior-mixture law, but collects and consumes its own batch.

All three arms start from byte-identical actor, critic, recurrent, optimizer, and initial-state bytes. The only treatment-level switch is which learner's parameters source the next collected batch. Subsequent differences in action coverage, history or state occupancy, returns, critic targets, advantage magnitude or variance, clipping, Adam state, and recurrent representation are intended descendants of that feedback edge. They are logged as mediators and are neither separately controlled nor interpreted as independently identified causes.

The treatment must be called `SELF_GENERATED_CLOSED_LOOP_FEEDBACK`, not an `on-policy` correction. The unchanged behavior mixture may differ from the policy appearing in the sampled-action log-probability, and the custom oracle coefficient is not established to be a standard policy-gradient advantage.

## Immutable collection and update order

For every unit and update:

1. Address-indexed, immutable common exogenous tapes provide the cue schedule, environment randomness, behavior-mixture coins, and sampling uniforms to both collectors. They are not a shared mutable RNG.
2. From the complete pre-update states, collect the entire `RL_ORIGINAL_GENERATOR` batch and the entire `CREDIT_SIGN_SELF_FEEDBACK` batch before any arm is updated.
3. Freeze both batches, including rows, row order, masks, actions, rewards, returns, metadata, and digests. No row may be retroactively changed or regenerated.
4. In a fixed manifest order after both freezes, update `RL_ORIGINAL_GENERATOR` on its own batch, `CREDIT_SIGN_SHADOW` on the exact frozen generator batch, and `CREDIT_SIGN_SELF_FEEDBACK` on its exact frozen self-generated batch. No arm may mutate another arm, collector, tape, batch, optimizer, RNG, or successor state.
5. The two collector batches at the first update must be byte-identical. Only after the original-objective and oracle-sign updates have diverged their parameter states may later collector rows diverge. Later divergence is the intended treatment exposure, not an immutable-batch violation.

Within every arm, preserve the B3 actor, critic, recurrent, observation/history, masks, return, loss reduction, entropy coefficient, Adam settings, global clipping threshold and order, and evaluation semantics. The cue/action oracle may enter only through scalar `c_i`; it may not enter observations, hidden state, critic targets or loss, entropy, sampling, rewards, returns, batch composition, masks, branch selection, or evaluation.

## Proposed fixed `B_TOY_LIGHT` budget

- Registered run identity: `VSP02-B4-REGISTERED-FULL-01`.
- Five fresh paired root units: `VSP02-B4-U01` through `VSP02-B4-U05`, proposed decimal roots `22040001` through `22040005`. CM must prove collision freedom before the run; collision permits no silent reseed.
- Per unit: 128 updates per learned arm.
- Per collector and update: eight real training episodes with exact cue balance `4/4`.
- Real training episodes: `2 collectors * 5 units * 128 updates * 8 episodes = 10,240`.
- Optimizer updates: `3 arms * 5 units * 128 updates = 1,920`.
- Final held-out evaluation: 128 common-panel episodes per arm and unit with cue balance `64/64`, totaling `1,920` evaluation episodes.
- Final checkpoints: one per arm and unit, totaling 15.
- Hard caps: one result-bearing full, 30 CPU minutes, 2 GiB peak memory, and at most 145,348 real environment transitions.
- Prohibited: retry, rescue, sweep, additional arm, additional seed, extra checkpoint, cap extension, early checkpoint selection, or any post-result intervention.

## Required gates and observables

The treatment is interpretable only if all applicable gates pass:

- fresh treatment, unit, seed, tape, batch, checkpoint, evaluation, and run identities;
- byte-identical three-arm initial parameter, Adam, recurrent, and initial-state hashes;
- byte-identical first collector batches and their ordered row digests;
- complete pre-update collection and post-collection immutability for both batches on every update;
- exact shadow-to-generator batch and row-order identity;
- collector, optimizer, RNG, tape, batch, and successor-state noninterference;
- unchanged behavior-mixture law and exact actor, critic, recurrent, entropy, clipping, Adam, mask, return, and reduction routes;
- oracle firewall and exact `c_i * detach(abs(G_i - b(h_i)))` coefficient in both oracle-sign arms;
- finite nonzero actor gradients, finite losses, and exact activity and cap counts;
- common independently recreated held-out evaluation panels, finite logits, and no stochastic evaluation draw;
- per-unit `exact_correct_unit`, `J_eval`, `Kappa`, ties, and final hashes.

Feedback exposure must be realized in every unit: after the first update, the original and oracle-sign collector parameter hashes must differ, and at least one later action or environment-transition row must differ under the indexed common tape. Failure of this gate is inconclusive; no post-result minimum effect-size threshold may be invented.

Record action and history occupancy, correctness-class exposure, credit density, absolute-advantage magnitude and variance, critic targets, route-separated gradient norms, pre-clip norm, clip flag or factor, and Adam transitions only as possible mediators. The primary result branch must not condition on their direction.

## Prospectively separating branches

1. `B4_FEEDBACK_LOCAL_SUFFICIENCY`: `CREDIT_SIGN_SELF_FEEDBACK` is exact-correct in `5/5` units; `CREDIT_SIGN_SHADOW` and `RL_ORIGINAL_GENERATOR` are exact-correct in `0/5`; self-feedback mean `J_eval - 1 > 0.05`; self-feedback mean `Kappa >= 0.70`; feedback exposure and every validity/activity gate pass.
2. `B4_FEEDBACK_LOCAL_INSUFFICIENT`: all three arms are exact-correct in `0/5`; feedback exposure is realized in every unit; every validity/activity gate passes.
3. `B4_INCONCLUSIVE_OR_INVALID`: every other mapping pattern, any inactive-feedback unit, any unexpected nuisance or shadow recovery, any partial self-feedback pattern, or any identity, firewall, batch, activity, cap, finite-value, or evaluation failure.

A positive branch supports only that closing the learner-to-future-data feedback edge is locally sufficient under this exact finite toy and budget. It does not identify which downstream distribution or optimization mediator carried the effect. A negative branch falsifies only this exact self-generated-feedback intervention's local sufficiency. It does not establish general feedback irrelevance.

## Literature boundary

The local literature makes the feedback edge scientifically coherent but does not validate this exact treatment:

- `MARL-0014`, pp.2-3, restates policy-gradient expectations under policy-induced state and action distributions.
- `MARL-0544`, pp.3-5, develops action and stationary-distribution correction for its own offline MARL setting.
- `MARL-0670`, p.7, uses trajectory likelihood ratios for its own off-policy surrogate.
- `MARL-0018`, pp.1-2, motivates behavior/learned-policy mismatch as a source of effective transition and value-estimation error.

These sources do not prove that `c_i * abs(A_i)` is a valid advantage estimator, do not analyze this recurrent oracle-sign shadow construction, and do not support general actor-critic, recurrence, optimizer, or MARL claims.

The hypothesis-only SCIC, ACE, and VSP pointers do not provide an admissible downstream-response density replacement here. SCIC inserts an intrinsic influence reward without signing receiver benefit; ACE changes the TD target and temporal-credit semantics; VSP preserves asynchronous action identity through proxy updates without establishing receiver-benefit sign. Under frozen B3 semantics, a nontrivial response-conditioned density change would also change reward, target, eligibility locus, coefficient mass, or row-wise information; a mass-normalized duplication is algebraically unchanged.

## Exact External Pro question

> With byte-identical three-way initialization, address-indexed common exogenous tapes, byte-identical first collector batches, and both complete batches frozen before any update, does switching only the fixed-mixture collector's parameter source from the `RL_ORIGINAL_GENERATOR` nuisance process to the oracle-sign learner define an identifiable single-edge total-effect intervention, despite all ensuing batch, target, gradient, clipping, Adam, and representation differences being descendants of that edge? If not, identify exactly one missing invariant or one repair that remains strictly within the feedback axis. Also state the strongest prospective falsifier.

Return exactly one verdict:

- `SOUND_AS_WRITTEN`
- `REPAIR_WITHIN_FEEDBACK_AXIS`
- `REJECT_SINGLE_AXIS`

Do not propose or authorize a direct-label or cross-entropy intervention, a second simultaneous scientific axis, importance weighting, reward or target changes, optimizer tuning, a B3 rerun or rescue, an extra arm or seed, a sweep, a cap extension, a result reinterpretation, C-level inference, promotion, retirement, sibling-direction transfer, implementation, or runtime execution.

## Nonclaims and return boundary

This preview does not claim:

- that the proposed treatment is frozen, admitted, implemented, executable, technically accepted, or scientifically accepted;
- that the self-generated arm is strictly on-policy or optimizes a standard return objective;
- that B3 failed because of feedback, magnitude, variance, density, critic learning, clipping, Adam, recurrence, or shared gradients;
- that any observed B4 difference would identify a particular downstream mediator;
- that the actor-critic, recurrent architecture, optimizer, temporal credit, or baseline is generally capable or incapable;
- natural-distribution, transfer, sample-efficiency, general MARL, C-level, formal, promotion, retirement, or portfolio claims;
- any new meaning for B3 or authorization to reopen it.

Root must first publish this exact packet through an ordinary non-force configured-upstream push. The registered Explorer transport must then start a new External Pro conversation using explicit transport state rather than invented or defaulted parameters. If transport blocks, return the exact blocker; do not use another browser route. After an accepted B4 result and publication, any convergence review must be an exact continuation of the conversation created for this preview.
