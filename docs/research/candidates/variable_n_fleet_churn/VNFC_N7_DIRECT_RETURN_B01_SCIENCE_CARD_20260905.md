Claim: This B tests whether real shared-policy training at post-loss N7 improves native recovery and how MAPR-4 compares with DIRECT-SET-AR and fixed BCRH-PERSIST on fresh same-distribution episodes.
Binding MARL structure: (a) roster change; one unannounced executor loss changes available entities and multi-agent recovery coordination.

# VNFC N7 direct-return B01 science card

Object: `VNFC-N7-DIRECT-RETURN-B01`. Evidence class: `B/EXPLORE`.
Selected by the complete 2026-09-05 direction Convergence decision; application is in
`VNFC_N7_DIRECT_RETURN_CONVERGENCE_INTAKE_20260905.md`. This card fixes the new scientific
comparison and budget. Source integration, trainer configuration and measured cost are not yet
certified. There is no result, live process or automatic E01 follow-up implied by the card.

## Question, population and preserved task

Train and evaluate after loss at N=7 on the existing R02 two-zone native host with one
unannounced executor loss. Training and evaluation draw disjoint fresh episodes from this same
distribution. Preserve public actor observations, entity and role ownership, legal masks, the
four-token physical action grammar and complete native terminal. Use the current corrected
canonical presentation/action path; do not reuse the unrepaired R01 presentation probe or
interpret an old checkpoint under changed action semantics.

N=7 names the post-loss roster. CM must map this to the host's actual pre-loss and survivor
construction rather than assume N is a pre-loss count. One episode includes its prehistory,
six post-loss joint decisions and the full 120s post-loss native process: 240 native ticks in
the selected transferred host. Retain existing lost-entity, survivor-state and identity mapping.
No join, rejoin, replacement, repeated churn or change to temporal abstraction is selected.
Administrative episode, world and seed identifiers remain bookkeeping and do not enter actors.

Learn the original unshaped objective `J_ext = 0.5 R_fail_60 + 0.5 U_total`. The primary outcome
is `R_fail_60`. Report `U_total`, `J_ext`, `U_intact` and the existing native recovery/non-harm
context without substituting one for the primary outcome. Preserve the native service/demand
definitions and complete terminal; collecting a 60s primary outcome does not truncate the
120s training reward. No oracle supervision, BCRH-action imitation or new reward shaping.

This changes the old N={3,5}-training/N7-evaluation question to same-distribution N7 learning.
The sixteen old worlds and privileged search are not new training data or an independent test
set. The question does not claim to diagnose the unique cause of historical cross-N failure.

## Treatments and comparison

- MAPR-4 and DIRECT-SET-AR each start a fresh actual model and optimizer and train. Match the
  allowed actor information, episode distribution, rewards, interaction count and optimization
  schedule. Preserve the established topology and DIRECT's containing residual construction;
  report actual DIRECT updates, parameter motion and residual behavior, not competence by
  architectural declaration alone. Parameter counts and inference work need not be equal.
- BCRH-PERSIST stays fixed and is neither trained nor tuned. Execute it once on the same 64
  evaluation episodes and reuse those results for paired comparisons. Its complete internal
  controller/checker work is included. MAPR–DIRECT is the same-information learner comparison;
  BCRH input equivalence has not been established field-by-field, so its comparison is a native
  return reference without an extra strictly matched-information causal attribution.

The terminal checkpoint is the primary readout. Preserve and report each arm's initial,
midpoint and final values; do not choose the best checkpoint, metric, arm or evaluation seed.
Report aggregate and each failed zone for:

1. Each learned arm's final-minus-initial `R_fail_60` on the same evaluation episodes.
2. Final MAPR-minus-final DIRECT `R_fail_60`.
3. Each final learned arm minus fixed BCRH `R_fail_60`.

A learned policy may be worse than BCRH without an engineering failure. The exact-class maximum's
nonnegativity property does not apply to a finite-trained policy.

## Seeds, schedule and prospective exposure

Use one new paired training instance per learned arm. Namespace
`VNFC-N7-DIRECT-RETURN-B01-20260905`; training master seed `2026090501`, evaluation master seed
`2026090502`. Pair exogenous world randomness across arms, with separate, declared initialization
and action-draw streams. Do not require heterogeneous parameter arrays to be identical. Reuse
the established addressed RNG mechanism with the new namespace; no old master or checkpoint.

Each learner has 64 collect/update rounds, each with 32 complete training episodes balanced
across the two failed zones (16 each). Evaluate at rounds 0, 32 and 64 on the same 64 fresh
evaluation episodes (32 each zone), separated from training. Fixed BCRH is evaluated on these
64 episodes once. Repeated evaluation is not an independent training seed.

| Planned quantity | MAPR-4 | DIRECT-SET-AR | BCRH-PERSIST |
| --- | ---: | ---: | ---: |
| Training instances | 1 | 1 | 0 |
| Training rounds | 64 | 64 | 0 |
| Training episodes | 2,048 | 2,048 | 0 |
| Training post-loss joint transitions | 12,288 | 12,288 | 0 |
| PPO epochs per round / minibatch size | 4 / 24 | 4 / 24 | 0 |
| Optimizer steps per round / total | 32 / 2,048 | 32 / 2,048 | 0 |
| Evaluation episodes, counting all checkpoints | 192 | 192 | 64 |
| Total post-loss policy decisions | 13,440 | 13,440 | 384 |
| Total native ticks including prehistory | 537,600 | 537,600 | 15,360 |

These are selected plan counts, not completed exposure. A joint decision is not seven
independent samples, and four-token internal decisions are not four environment transitions.
CM's source mapping found the existing trainer uses four PPO epochs and 24-transition
minibatches. Retain those values: 192 transitions per new round produce eight minibatches
per epoch and 32 `optimizer.step` calls per round, or 2,048 per arm / 4,096 in the pair.
This is a prospective adaptation of the actual algorithm, not a claim that the old hard-coded
96-transition trainer already supports it. Sixty-four rounds is not sixty-four optimizer steps.
Keep the two arms' optimizer exposure matched and report both parameter counts,
initialization norms/scales, per-round actual gradient/update counts and parameter displacement
relative to each arm's own initialization. Unknown costs and as-yet-unmeasured norms are unknown,
not zero. The new runner produces the machine-generated exposure line from these actual values.

## Complete cost and stop boundary

The selected first round's cumulative complete invocation wall is at most 2,700 seconds across
both learning arms, BCRH evaluation, required initialization/build and publication. This is this
object's explicit total investment, not the runtime spec's project-wide investigation threshold,
an extra budget per arm or leftover E01 budget. No forced division into slices changes the total.

Use each arm's real unit work:

`T_a = setup_a + 2048 * collect_episode_a + 64 * update_round_a + 192 * eval_episode_a + publication_a`.

`T_B = setup_B + 64 * complete_BCRH_episode + publication_B`.

Count genuinely shared preparation once; require
`T_shared + T_MAPR + T_DIRECT + T_B <= 2700s` for the complete planned work. Report actual
cumulative wall and per-arm work rather than assume concurrent time or unused remote capacity
is a saving. Each learned episode includes reset, observations/masks, policy, native stepping
and terminal; the update-round term includes every epoch/minibatch/gradient step. BCRH includes
384 complete calls and environment execution. Do not derive a training second estimate from
the old census call count or divide E01 timing by a thread count.

Dominant request factors are two learners × one training seed × 64 rounds × 32 episodes × six
joint decisions, plus two learners × three evaluation checkpoints × 64 episodes × six decisions
and 384 BCRH reference calls. Four-token policy work and BCRH's intrinsic candidate scoring remain
algorithm work. There is no outer all-action, all-history, all-policy or counterfactual-trajectory
enumeration. Added verification is a focused check of the changed N7/training/output path, not
the old 94,128-continuation census, 52/304-row law ladder or all-intermediate publication.

Current complete new-arm seconds are unmeasured. Prefer reusable existing timing records;
a necessary focused real training/evaluation/output check may supply missing unit costs in
the same engineering task. No separate exact cost-proof experiment is selected. If actual
trainer constraints, primary correctness or the selected total cannot be met, return that
specific gap before performance-dependent redesign. Do not silently shorten one arm, omit
an unfavorable seed, choose a checkpoint, or call partial output the planned complete result.
Keep independently trustworthy partial facts at their proper ceiling.

## Implementation and proportionate verification assignment

CM maps the current corrected R02 policy/trainer/native host into one minimal fresh runner and
records all material configuration, numerical, RNG or checkpoint differences. Preserve framework
autograd, native rewards and physical actions; no reconstruction of the old scalar exact-adjoint
proof is required. Preserve the existing optimizer hyperparameters unless CM exposes a concrete
incompatibility, which returns to the DM before alteration. The old N3/N5 schedule, DEBUG seal,
heldout-freeze protocol and publication systems are not the new scientific assignment.

Use `wsl_4070` under `.codex/hmasd-compute.toml`, CPU execution for the existing binary64/native
policy path unless its actual source requires a concrete prospective clarification. The empirical
claim is conditional on the declared host/device; no cross-platform bit equivalence is claimed.
Ordinary in-process batching may be used with task-local episodes and matched arm semantics.
Do not inherit E01's four-participant/batch8 exact-assessment exception as new CPU authority.
Commit and push exact source before a detached remote invocation. Fresh memory admission must
run immediately before every actual invocation on the execution node and meet both 4 GiB floors.

The engineering check reaches actual changed behavior and primary output:

- Trace native service/demand counts into `R_fail_60`, `U_total`, `U_intact` and `J_ext`; keep the
  full terminal and enough per-episode values to check the reported contrasts.
- Check the N7 event/entity/role/input/mask/physical-command chain for both arms. Use the repaired
  presentation path and check its actual action consequence; do not impose universal bit equality
  or all-history replay. World/seed metadata must not enter either actor.
- Exercise both actual learner update paths and readable evaluation/output; record nonzero
  transitions, updates and evaluation and the machine-generated exposure line. Report DIRECT
  training and residual activity as observations, without making a favorable competence result
  a prerequisite for running or reporting the learner comparison.
- Read the main summary, episode-level primary outcomes and declared checkpoints. Retain all
  observed outcomes; missing optional resource telemetry limits the resource account only.

Engineering Scope Spec §4 additions: none. Reuse the project supervisor and learner checkpoints;
no new worker service, provenance/refusal framework, retry machinery, full intermediate-record
publication or recurrent smoke is needed. The ordinary 2,000 new-source-line and 600-runner-line
budgets apply to this distinct B implementation. Existing checks can be reused; one launch
boundary does not require an extra smoke. Code acceptance does not establish scientific value.

## Expected reading, strongest alternatives and non-goals

The headroom record is incomplete: old privileged K lower/physical upper bounds are not a tuned
same-information generic learner headroom pair. Its absence does not hold this B. The selected
absolute MEI is `0.10 R_fail_60`, retaining the existing host's interpretation of an acquisition
interval rather than lowering it after seeing outcomes. It is a descriptive investment scale,
not a requirement that every contrast, zone or seed cross it.

DM prediction on record: a positive final-minus-initial signal in at least one real learning arm
is more plausible than MAPR exceeding the competent fixed BCRH by 0.10; this is a qualitative
prediction, not an observed probability or a success gate. Owner prediction: not taken
(unattended). Competing explanations are a useful MAPR recovery bias, a generic DIRECT advantage,
or inadequate useful learning/headroom at this budget. No new seed result exists at card time.

If MAPR learns and is better on the native scale, this supports one N7 B signal and a same-comparison
follow-up with one or two independent training seeds. If DIRECT learns or outperforms MAPR, retain
that as evidence for the generic shared learner, not MAPR-specific value. If learners improve but
remain below BCRH, or recovery trades away other service, report the learning and losses separately.
Inside the MEI, report actual effect size and uncertainty without turning it into a pass/fail gate.
If both fail to improve or effects reverse, retain the negative and do not fill more seeds at the
same configuration automatically; a justified new B may be proposed from actual curves/behavior.
No requirement that all zones or subsequent seeds be positive.

The 64 paired evaluation episodes describe these trained policies conditionally. One training
seed cannot estimate training-seed population uncertainty. No stable-superiority, invariance,
exact maximum, complete causal explanation, cross-N transfer, repeated-churn, real-UAV, safety,
flight or deployment claim follows. E01/R03 and all historical quarantines and bounded negative
comparisons retain their original meaning.
