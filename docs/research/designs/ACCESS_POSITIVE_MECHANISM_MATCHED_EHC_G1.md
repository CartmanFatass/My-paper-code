# Access-positive mechanism-matched EHC G1

```text
assignment_id=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION
source_family=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1
scientific_source=external_pro
executable_author=project_manager
backend=cpu
torch_threads=1
formal_evidence_contract=PM_FROZEN
G0_reuse=forbidden
backward_compatibility=not_required
```

## Question and scope

This independent G1 source asks whether a learned event-held per-lifecycle
commitment produces useful persistent behavior beyond matched DUM and ordinary
recurrence when a two-step cue disappears. G0 remains permanently closed as
`NO_ACCESS_THIS_BENCHMARK`; no G0 task, reward, seed, checkpoint, analyzer,
threshold, result, or artifact schema is imported.

The formal arms are `OR`, `DUM`, and `EHC`. They receive identical actor
information and the same recurrent base architecture. DUM and EHC additionally
receive identical event/mark capacity and optimizer exposure. Only EHC applies

```text
primitive_logits = base_logits + W_z(m*z)
```

Primary gain is `G_DUM = U_EHC - U_DUM`. The matched simpler-explanation gain
is `G_OR = U_EHC - U_OR`. Neither a source access pass nor a local mechanism
pass integrates EHC into the full algorithm.

## Source and lifecycle

An episode has horizon 80, maximum capacity four, and an initial anonymous
roster of two or three lifecycles, balanced within every evaluation cell. Each
lifecycle owns hidden physical state
`(g, age, remaining, correct_count, terminal_streak)`. At a genuine JOIN and at
every completed segment, `g` is sampled uniformly from `{-1,+1}` and duration
uniformly from `{6,10,14,18}`. A sign mate shares every exogenous realization
and negates every duty target.

Actor fields are exactly, in order:

```text
(cue_value, cue_present, new_segment, join_flag, rejoin_flag,
 normalized_active_count)
```

The cue exposes `g` for exactly two active transitions. No target, duration,
remaining time, progress, reward, success, identity, lifecycle key, future duty,
or future membership is actor-visible.

For each active action, `correct = 1[action == g]`. A segment succeeds only if
both `4 * correct_count >= 3 * duration` and the final two active actions are
correct. This corrects the nonformal prototype's deliberately smaller
last-two-only completion rule; the prototype remains measurement evidence, not
formal source evidence.

Temporary LEAVE freezes physical state, recurrent state, commitment state,
segment clock, and opportunity clock. REJOIN restores the same lifecycle.
Terminal LEAVE censors the open segment and removes the lifecycle. A segment
unfinished at horizon is censored. Every started segment remains in the eligible
denominator; censored segments receive no completion credit.

Utility is

```text
U = 0.75 * correct_active_actions / registered_active_opportunities
  + 0.25 * successful_segments / registered_started_segments
```

The dense team reward is the exact per-transition increment of this utility, so
the episode reward sum equals `U`. No intrinsic reward or task shaping exists.

## Train and held-out ledgers

All exogenous ledgers are precomputed from owned counter-based streams before
policy execution. Actions and policy events never change future task,
membership, duty, or opportunity draws.

Training and IID evaluation use this membership pattern:

- one temporary LEAVE at a uniformly selected step 10--18;
- REJOIN after 3--7 physical steps;
- one JOIN at step 28--38 after the REJOIN;
- one terminal LEAVE of a distinct initial lifecycle at step 58--70.

Held-out evaluation changes the pattern rather than the scientific object:

- JOIN occurs first at step 8--14;
- temporary LEAVE occurs at step 30--38;
- REJOIN follows after 8--12 physical steps;
- terminal LEAVE occurs at step 62--74;
- anonymous physical packing is reversed and rotated; and
- duration realizations use a balanced cyclic permutation of the same declared
  support instead of the training IID order.

Targets, durations, membership choices, and opportunity schedules remain
independent. Initial roster sizes stay `{2,3}`; held-out evidence does not add a
new task support value after results.

At genuine JOIN the first active transition creates a mark. Thereafter an
independent opportunity clock samples active-step gaps uniformly from `{1,2}`.
Only a non-CREATE opportunity permits a learned natural `KEEP` or `RENEW`.
Inactive time consumes no opportunity draw. A completed segment resets the
base recurrent state before the next cue but does not reset the lifecycle-held
mark or opportunity clock. This makes a natural RENEW across segment boundaries
both possible and behaviorally load-bearing; only terminal LEAVE destroys the
commitment.

## Policy, information, and gradients

The actor is a shared per-lifecycle network: a 6-to-32 encoder, a 32-unit
`GRUCell`, and a three-action head for action order `(-1,0,+1)`. Actions
factorize across active anonymous lifecycles conditional on their actor fields,
recurrent state, and commitment treatment. There is no physical-slot or
lifecycle-ID embedding.

The critic has a separate encoder and receives a padded active set with ten
per-lifecycle fields: the six actor fields plus `age/18`, `remaining/18`,
`correct_count/max(age,1)`, and `terminal_streak/2`, together with the active
mask. It receives neither `g` nor future state. Critic tensors never enter the
actor or event heads.

DUM and EHC have identical two-way event (`KEEP`,`RENEW`) and two-way mark
(`-1`,`+1`) heads. CREATE and RENEW sample a mark; KEEP preserves it. OR carries
the same base model but executes no event or mark. All three instantiated arm
objects retain the same parameter structure; DUM hard-masks the treatment and
OR hard-masks the event path. EHC alone adds the learned three-vector
`W_z(m*z)` to primitive logits.

The base PPO loss uses primitive-action log probability, value loss, and
primitive entropy. It updates the actor encoder, recurrent cell, primitive head,
critic, and `W_z`; sampled event and mark values are detached. A separate event
PPO loss uses event/mark log probability and the same team advantage with actor
features detached; it updates only event and mark heads. DUM and EHC take one
event optimizer step for every base optimizer step. No event loss reaches the
base representation, and no critic value reaches actor inputs.

Hyperparameters are fixed before data:

```text
hidden_dim=32
gamma=0.99
gae_lambda=0.95
ppo_clip=0.20
value_clip=0.20
value_coefficient=0.50
primitive_entropy_coefficient=0.01
event_entropy_coefficient=0.01
gradient_clip=0.50
learning_rate=0.0003
ppo_passes=4
minibatch=one full 16x80 rollout
```

## Exposure, seeds, RNG, and checkpoints

There are five paired replicates. Per replicate and arm: 16 environments,
horizon 80, 250 updates, 4,000 episodes, 320,000 environment transitions, and
1,000 base optimizer steps. DUM/EHC each take 1,000 event optimizer steps; OR
takes zero. Base parameters start identically across arms within a replicate;
DUM/EHC event and mark parameters also start identically. Arms never share
mutable parameters, optimizers, hidden state, or RNG objects after creation.

Training update `u` contains base IDs `8u..8u+7`, each with sign mates `-1,+1`,
in base-ID then sign order. Every arm receives that same 16-ledger batch.
Evaluation likewise uses base IDs `0..127` with both sign mates in every cell.
This is the exact paired-episode inventory; it does not share mutable state
between arms.

The G1 seed registry is:

```text
model=158058
train_task=168058
train_membership=169058
train_duty=170058
train_opportunity=171058
train_event=172058
train_mark=173058
train_primitive=174058
evaluation_task=198058
evaluation_membership=199058
evaluation_duty=200058
evaluation_opportunity=201058
evaluation_event=202058
evaluation_mark=203058
evaluation_primitive=204058
audit=206058
bootstrap=208058
replicate_offset=1000
```

Every namespace owns one draw type. Paired arms instantiate separate generators
from the same exogenous/CRN coordinates; there is no shared mutable generator.
Training and evaluation namespaces never overlap. Replay consumes stored draws,
not fresh RNG.

Training consumes owned generators in canonical `(environment, physical_slot)`
order only at applicable primitive, event, or mark decisions. Evaluation and
causal audit derive each policy draw from its registered namespace plus the
coordinate `(replicate, profile, base_id, sign_mate, time, physical_slot)`.
Thus paired arms and continuation branches request the same future coordinate
without a treatment-dependent stream shift. A forced RENEW at a natural KEEP
row obtains its candidate mark only from the `audit` namespace; it never
advances or replaces the natural mark schedule. Unused coordinates are not
reported as policy draws.

The independent G1 checkpoint schema stores arm, replicate, update, model,
both optimizer states when applicable, seed registry, every owned RNG state,
and Python/NumPy/Torch runtime RNG. Checkpoints are written only at completed
rollout/update boundaries. A rolling latest checkpoint supports recovery and
`update_250.pt` is the only evaluation checkpoint. CPU checkpoints cannot load
under another backend or thread contract.

## Evaluation and source identification

Evaluate only `update_250.pt`. For every replicate and arm, run four cells:
IID deterministic, IID stochastic, held-out deterministic, and held-out
stochastic, 256 episodes each. Each cell contains 128 base ledgers and both sign
mates. Primary estimands and the behavioral battery use held-out stochastic
episodes; other cells are registered transport diagnostics.

Before access, all of these must pass:

- exact reward-sum/utility identity and finite schema;
- exact actor-field/no-leakage, lifecycle freeze/restore, RNG, replay, and
  checkpoint invariants;
- all four durations, both roster sizes, both sign mates, temporary
  LEAVE-to-REJOIN spans, completed and censored segments are present;
- a persistent oracle has `LCB95(U) >= 0.80` in every evaluation profile;
- a registered history-free controller has `UCB95(U) < 0.80` in every profile;
- across five held-out stochastic EHC replicates there are at least 1,000
  non-CREATE opportunities and 250 lifecycles with at least two; and
- natural support has at least 128 eligible KEEP and 128 eligible RENEW rows in
  total and at least 16 of each per replicate.

Any failure is `SOURCE_NON_IDENTIFIABLE_G1`, not a mechanism result. The oracle
always acts on hidden `g`. The history-free controller uses the visible cue and
an independent fair sign after cue expiry; it owns no recurrent or commitment
state.

## Statistical contract and battery

Use 10,000 percentile hierarchical bootstrap repetitions. Resample five paired
replicate triples, then 128 base-ledger IDs within each selected replicate;
retain both sign mates, all arms, all profiles, lifecycle rows, opportunity
rows, and CRN audit branches. Do not independently resample lower-level rows.

The access floor is `0.80`; equality passes. Primary `G_DUM` passes only when
`LCB95(G_DUM) > 0.10` and confidently fails when `UCB95(G_DUM) <= 0.10`.
Resistance to ordinary recurrence uses the same local scale:
`LCB95(G_OR) > 0.10` excludes the matched recurrent explanation, while
`UCB95(G_OR) <= 0.10` supports it.

The unchanged held-out stochastic battery is:

- at least two complete-spell opportunity bins `K=1`, `K=2`, `K>=3` have
  `LCB95(proportion) > 0.10`;
- same-state mark derangement has `LCB95(I_TV) > 0.10`;
- both `LCB95(C_total_KEEP) > 0` and `LCB95(C_total_RENEW) > 0`; and
- both corresponding means are at least `0.02`.

A commitment spell opens at CREATE or RENEW. `K` counts every subsequent
non-CREATE opportunity, including the RENEW that closes the spell. Only spells
closed by a natural RENEW are complete; spells still open at terminal LEAVE or
horizon are censored from the K-bin denominator.

For a natural KEEP row,
`C_total_KEEP=U(KEEP_HELD_MARK)-U(RENEW_CANDIDATE_MARK)`. For a natural RENEW
row, `C_total_RENEW=U(RENEW_CANDIDATE_MARK)-U(KEEP_HELD_MARK)`. Outcome-blind
selection takes the first 16 eligible rows per action and replicate in
`(base_id, sign_mate, time, lifecycle)` order. Branches clone the exact state and
future CRN schedule and never copy future outcomes. `C_timing`, `C_mark`,
sequence hamming/correctness, natural mediation, and held-out robustness are
descriptive decompositions with no branch threshold.

## First-match result

Apply exactly in this order:

1. `INVALID_OPERATIONAL_G1`: any protected runtime, probability, gradient,
   replay, lifecycle, mask, RNG, checkpoint, backend, reference, schema, or
   finite-value invariant fails.
2. `SOURCE_NON_IDENTIFIABLE_G1`: any source-identification or natural-support
   predicate above fails.
3. `NO_ACCESS_THIS_G1_SOURCE`: maximum arm utility UCB is strictly below 0.80.
4. `UNDERPOWERED_ACCESS_G1`: maximum arm LCB is below 0.80 while its UCB reaches
   0.80.
5. `COMMITMENT_SUPPORTED_G1`: `LCB(G_DUM)>0.10`, `LCB(G_OR)>0.10`, and every
   interval and point condition of the battery passes.
6. `REPRESENTATION_ONLY_G1`: both gain LCBs exceed 0.10 and at least one required
   interval confidently fails. A C-total point-floor shortfall alone is not a
   confident failure.
7. `ORDINARY_EXPLANATION_G1`: either `UCB(G_DUM)<=0.10` or
   `UCB(G_OR)<=0.10`.
8. `MIXED_UNDERPOWERED_G1`: every other valid numerical pattern.

For step 6, a required interval confidently fails exactly when fewer than two
K bins have `UCB95(proportion)>0.10`, `UCB95(I_TV)<=0.10`, or either
`UCB95(C_total_KEEP)<=0` or `UCB95(C_total_RENEW)<=0`. A low LCB whose UCB still
crosses the gate is underpowered and falls through to step 8. A C-total mean
below `0.02` without interval failure also falls through to step 8.

No branch rescues or relabels G0. A valid negative is never rerun with changed
seed, budget, model, reward, observation, threshold, or name.

## Formal artifact contract

The independent runner exposes `train`, `evaluate`, `analyze`, and `exercise`.
Formal training writes one rolling recovery checkpoint per active arm and only
the 15 registered `update_250.pt` checkpoints as retained conclusions. Formal
evaluation writes the exact 60 arm/replicate/profile cells plus source-control
and selected causal-audit rows. The analyzer closes those references by exact
path, schema, identity and row inventory; per-file hashes are not an authority
or acceptance gate.

Source-control evidence retains the canonical replicate/base/sign utility
clusters needed to recompute its observed means and bootstrap intervals. Formal
validation rederives every metric, source-identification predicate and result
predicate from the referenced evaluation, source-control and audit evidence.
Observed rows define point estimates; bootstrap replicates define confidence
bounds only. Formal `analyze` succeeds only after that binding validates.

`analysis_result.json` is conclusion-bearing only when `formal=true`, all five
replicates, budgets, final checkpoints, 60 cells, 10,000 bootstrap repetitions,
source predicates, natural quotas and operational invariants close exactly.
Any mismatch selects `INVALID_OPERATIONAL_G1` before numerical interpretation.
`exercise` always writes `formal=false`, uses reduced inventories only to cover
the end-to-end path, and is rejected by the formal-result validator.

## Active-line replacement and completion

Formal G1 owns new source, model, checkpoint, runner, analyzer, and tests. Once
accepted, delete the synthetic-controller prototype executable and its tests;
retain only its design and evidence note as unique scientific evidence. No
compatibility reader or migration is created.

Prelaunch completion requires focused source/model/replay/checkpoint/selector
tests, one bounded `formal=false` CPU exercise, exact inspection for leakage,
RNG drift, repeated packing, scalar transfers, synchronization and serial
evaluation, and Project Manager acceptance. Only then may Project Manager assign
the already user-authorized formal CPU run to the registered experiment
operator.
