# CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2

Status: permanently closed as `TEAM_REC_SUFFICIENT_HANDOFF_G2` after one valid
formal CPU run.

## Provenance and correction

The exact `ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1` source is closed as
`ORDINARY_EXPLANATION_G1` at source commit
`de9a315b4969ee6920be08a3d911d559fe362f03`. Its evidence is recorded in
`docs/research/cdc/EVIDENCE_NOTES/20260723_ACCESS_POSITIVE_EHC_G1_FORMAL_RESULT.md`.
G1 is not imported, renamed, retuned or rerun here.

G1 retained a cue and acted on it within one member lifecycle. A per-member GRU
therefore supplied the whole useful memory. G2 asks a smaller structural
question: can a task-relevant bit remain available after the observing member
has terminally left and the acting successor begins with fresh member state?

## Claim boundary

G2 does not claim that event-held state is more expressive than every recurrent
network. A team-level recurrent state can emulate any finite event-held object.
The bounded gate must expose that simpler explanation rather than hiding it.

The gate distinguishes three facts:

1. fresh per-member recurrence cannot carry creator-only information across a
   terminal lifecycle handoff;
2. both a persistent team recurrence and an event-held team commitment can carry
   it constructively; and
3. changing the held commitment after the creator leaves changes the successor
   sequence and external utility.

Only a later trainable comparison may ask whether event-conditioned holding has
a learning or held-out robustness advantage over matched team recurrence. The
future strongest comparator is team recurrence, not the already-refuted
per-member G1 comparator.

## Minimal anonymous handoff source

Each exhaustive case contains a creator, a neutral survivor and a successor.
Physical slots are packing coordinates only and are never actor identity.

- A fair bit `b in {-1,+1}` is visible only to the creator at CREATE.
- The creator and survivor begin active.
- The creator terminally leaves after one or two active steps.
- For one gap step only the survivor remains active.
- An anonymous successor then joins with exact zero member-recurrent state and
  acts for two or four steps.
- The successor observation trace, membership history, physical packing and
  lifetime are independent of `b`; the survivor never observes `b` and has no
  communication action.
- Creator slot, successor slot, survivor slot, same-slot reuse, cross-slot
  transfer, creator lifetime and successor lifetime are exhaustively balanced.
- External utility is successor action accuracy for `b`. There is no intrinsic
  reward, shaping, learning or optimizer.

The commitment object is team/event scoped, not agent or physical-slot scoped.
CREATE stores the mark; terminal creator departure does not delete it; JOIN
exposes the same held object to the successor mechanism. This is the one new
algorithmic state-ownership proposal. It is generic to lifecycle events and does
not read task reward, named roles or persistent identities.

## Bounded policies and reduction

- `PER_MEMBER_REC`: the creator may store `b`, but terminal LEAVE destroys that
  state and successor JOIN starts at zero. Its best balanced successor utility
  is exactly `0.5`.
- `DUM`: receives the same CREATE/mark/handoff records but the held mark has no
  primitive-logit path. Its balanced utility is exactly `0.5`.
- `TEAM_REC`: a team recurrent state observes CREATE and survives membership
  churn. A constructive oracle attains utility `1.0`.
- `EHC`: the event-held mark survives the handoff and enters the primitive path
  through `base_logits + W_z(m*z)`. A constructive oracle attains utility `1.0`.
- `RANDOM_MARK`: an outcome-independent held mark attains utility `0.5`.

For every successor-visible trace `x`, the exhaustive case set contains one
`b=-1` and one `b=+1` case. Hence
`P(b=-1|x)=P(b=+1|x)=1/2`, and any policy whose only state is freshly initialized
successor recurrence has maximum expected accuracy `1/2`. This is the gate's
information proof; it is not an empirical threshold.

## Intervention

Snapshot immediately after terminal creator departure. Under common future
membership and action timing, replace only the held mark `z=b` with `z=-b`.
The EHC oracle must change every successor action, moving natural utility from
`1.0` to `0.0`. Team recurrence is retained as a simpler natural-capability
explanation and is not modified by this mark-only intervention.

## Exact bounded result

The nonformal runner always writes `formal=false` and one of:

1. `INVALID_HANDOFF_INFORMATION_GATE_G2` if schema, case balance, anonymity,
   lifecycle reset, state ownership or finite/exact metric invariants fail;
2. `PASS_HANDOFF_INFORMATION_GATE_G2` only when the per-member Bayes bound,
   PER_MEMBER_REC, DUM and RANDOM_MARK utilities equal `0.5`; TEAM_REC and EHC
   equal `1.0`; and the EHC mark-flip action-change and utility-drop equal `1.0`;
3. `FAIL_HANDOFF_INFORMATION_GATE_G2` for any other valid measurement.

This gate is deterministic, zero-training, nonformal and consumes zero
conclusion-bearing iterations. A pass establishes only an executable handoff
and comparator boundary. It does not support EHC adoption or authorize formal
iteration 3.

## Successor boundary

After a pass, freeze a separate trainable G2 evidence contract with:

- TEAM_REC as the strongest primary comparator;
- DUM as the link-null control and EHC as the treatment;
- primary `G_team = U_EHC - U_TEAM_REC` and secondary
  `G_link = U_EHC - U_DUM`;
- access before mechanism interpretation;
- event-held intervention, natural mediation and held-out churn/gap robustness;
- exact budgets, seeds, thresholds and first-match branches chosen before any
  conclusion-bearing run.

## Frozen trainable G2 contract

This section freezes formal iteration 3. It is an independent source and does
not rescue G0 or G1.

### Scientific question

Under anonymous creator-to-successor turnover, does event-conditioned held state
learn and transport the creator bit better than both a link-null control and a
persistent team recurrent state, especially across longer unseen handoff gaps?

The claim is an inductive-bias and robustness claim, not an expressivity claim.
TEAM_REC is constructively sufficient and is the strongest primary comparator.

### Source distribution

Every episode has one fair sign-mated bit, one creator, one neutral survivor and
one anonymous successor. Physical packing uses the 12 mappings from the passed
information gate and is never actor-visible.

- Creator lifetime support is `{1,2}` active steps. The bit is visible only to
  the creator at its first step, which is the single CREATE opportunity.
- The creator terminally leaves; the survivor remains during a gap; the
  successor then JOINs with zero member state.
- Training and IID gap support is `{1,2,3}` and successor duty support is `{4,6}`.
- Held-out gap support is `{8,12}` and successor duty support is `{8,10}`.
- A fair nuisance sign changes during the gap independently of the target bit,
  packing and lifetimes. It is actor-visible with `cue_present=0` and prevents a
  degenerate constant team-memory input without carrying target information.
- External reward is one for each correct successor duty action and zero
  otherwise. Episode utility is successor accuracy. Creator/survivor actions
  receive zero reward. There is no intrinsic reward or shaping.

Actor input has exactly six anonymous fields: cue value, cue-present flag,
JOIN flag, normalized lifecycle age, normalized active count and nuisance sign.
It excludes physical/logical identity, target after CREATE, phase name, remaining
lifetime and reward history. The centralized critic adds target bit, phase
coordinate, remaining duty and remaining gap for ten fields total; critic fields
never enter an actor, event or treatment path.

### Matched learned arms

All arms instantiate the same 32-wide actor encoder, per-member GRU, anonymous
mean-pooled 32-wide team GRU, primitive head, centralized critic, CREATE mark
head, team treatment `W_T`, and event-held treatment `W_z`. Initialization,
parameter count, observations, rewards, rollout exposure, PPO passes and RNG
namespaces are matched.

- `TEAM_REC`: primitive logits are `base_logits + W_T(h_team)`. The team GRU
  updates every environment step and survives member turnover. The sampled mark
  is recorded but has no primitive path.
- `DUM`: primitive logits are `base_logits`. Team recurrence and the sampled
  mark are recorded but neither treatment reaches primitive logits.
- `EHC`: primitive logits are `base_logits + W_z(m*z)`. CREATE samples
  `m in {-1,+1}` from creator features; signed learned embedding `m*z` is held
  unchanged across terminal LEAVE, gap and successor JOIN. Team recurrence is
  recorded but has no primitive path.

Unused links remain instantiated but receive no gradient through primitive
behavior. Event/mark PPO exposure is matched across arms. Primitive action
probability and CREATE mark probability form the declared joint policy; stored
draw replay owns their exact old log probabilities. Per-member state deletes on
terminal LEAVE, freezes only on temporary absence, and resets at a new JOIN.
Team and held state reset only at episode start.

Use the accepted G1 optimizer contract unchanged: Adam `3e-4`, gamma `0.99`,
GAE lambda `0.95`, PPO clip/value clip `0.20`, value coefficient `0.50`, primitive
and mark entropy coefficient `0.01`, gradient clip `0.50`, and four full-rollout
passes. This reuse is implementation control, not a G1 rescue.

### Budget, provenance and backend

```text
replicates=5
environments=16
horizon=64
updates=160
episodes_per_arm_minimum=2560
ppo_passes=4
evaluation_episodes_per_cell=256
evaluation_profiles=iid_deterministic,iid_stochastic,heldout_deterministic,heldout_stochastic
bootstrap_repetitions=10000
backend=cpu
torch=2.7.0+cpu
torch_threads=1
```

One fixed seed registry owns model initialization, source ledgers, nuisance,
primitive draws, mark draws, evaluation, audit and bootstrap, with a disjoint
offset per replicate. Numeric seed labels are implementation-only provenance:
changing them before launch cannot change an estimand, but after launch they are
frozen and never swept. No CPU/CUDA comparison or cross-backend resume exists.

### Estimands and source identification

For each arm, primary utility `U` is held-out deterministic successor accuracy.
The primary gain is `G_team = U_EHC - U_TEAM_REC`; the link gain is
`G_link = U_EHC - U_DUM`. Use paired hierarchical bootstrap over replicate and
sign-mated source clusters for means and 95% intervals.

Before gain interpretation, formal evidence must reproduce the information
gate, both constructive oracle utilities `1.0`, fresh per-member/reactive bound
`0.5`, exact sign/mapping/lifetime balance, actor-trace bit independence, creator
state deletion and successor zero initialization. It must also contain at least
128 natural held-out EHC successor episodes per replicate.

The access floor remains `0.80`; the meaningful gain margin remains `0.10`.
These are the only result-scale thresholds.

### Minimal EHC consequence battery

On held-out EHC episodes, record:

- natural CREATE mark accuracy `P(m=b)`;
- exact-snapshot held-mark flip action-TV across the full successor sequence;
- paired natural-minus-flipped successor utility;
- deterministic held-out EHC utility.

The support battery passes only when mark-accuracy LCB is above `0.75`, both
flip action-TV and utility-drop LCBs are above `0.10`, and held-out EHC utility
LCB reaches `0.80`. These consequences do not replace either gain estimand.

### First-match result

Apply exactly in this order:

1. `INVALID_OPERATIONAL_HANDOFF_G2`: any runtime, finite-value, probability,
   gradient, replay, lifecycle, state ownership, RNG, checkpoint, backend,
   reference or schema invariant fails.
2. `SOURCE_NON_IDENTIFIABLE_HANDOFF_G2`: any information-gate, constructive
   control, balance, anonymity or natural-quota predicate fails.
3. `NO_ACCESS_HANDOFF_G2`: maximum arm utility UCB is strictly below `0.80`.
4. `UNDERPOWERED_ACCESS_HANDOFF_G2`: maximum arm LCB is below `0.80` while its
   UCB reaches `0.80`.
5. `EHC_HANDOFF_SUPPORTED_G2`: both gain LCBs exceed `0.10` and the complete
   consequence battery passes.
6. `TEAM_REC_SUFFICIENT_HANDOFF_G2`: `UCB(G_team) <= 0.10`.
7. `LINK_NULL_HANDOFF_G2`: `UCB(G_link) <= 0.10`.
8. `REPRESENTATION_ONLY_HANDOFF_G2`: both gain LCBs exceed `0.10` and at least
   one battery interval confidently fails its threshold.
9. `MIXED_UNDERPOWERED_HANDOFF_G2`: every other valid numerical pattern.

A battery interval confidently fails only when its UCB is at or below the
registered threshold. Crossing intervals fall through to mixed/underpowered.
No lower-precedence diagnostic relabels an earlier branch.

### Artifact and launch contract

The active runner exposes `train`, `evaluate`, `analyze` and reduced `exercise`.
A conclusion requires `formal=true`, the exact integrated 40-character source
commit, five complete replicates, final update-160 checkpoints, 60 evaluation
cells, source controls, held-out audit rows and 10,000 bootstrap repetitions.
The analyzer rederives metrics and first-match selection from referenced rows.
Per-file hashes are not an authority gate.

`exercise` is always `formal=false`, uses reduced counts, covers collection,
replay, one optimization, checkpoint reload, evaluation and analysis, and must
be rejected by formal validation. The formal authorization token is
`AUTHORIZE_CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_FORMAL_CPU_V1`.

Formal iteration 3 becomes launchable only after Project Manager accepts the
implementation and bounded exercise on one integrated source commit. The
registered silent experiment operator then owns exactly one foreground
`train -> evaluate -> analyze` run. Three conclusion-bearing iterations remain
until a valid formal G2 result is produced.

## Closed formal result

The exact run at
`logs/formal_cross_lifecycle_handoff_g2_cpu_20260723_9a72dc6_r1` completed from
source commit `9a72dc6a0f776aa3e6dfa96d86f5265f12717ace`. TEAM_REC and EHC both
attained held-out utility 1.0, DUM attained 0.5, `G_team` was exactly 0.0 and
`G_link` was exactly 0.5. Source identification and exact-snapshot held-mark
consequences passed.

Frozen first-match step 6 therefore selected
`TEAM_REC_SUFFICIENT_HANDOFF_G2`. The result consumes conclusion-bearing
iteration 3 and leaves two iterations. The exact G2 source/comparison is closed
without rerun, tuning, renaming or rescue. Full disposition and the
label-symmetry measurement correction are in
`docs/research/cdc/EVIDENCE_NOTES/20260723_CROSS_LIFECYCLE_HANDOFF_G2_FORMAL_RESULT.md`.
