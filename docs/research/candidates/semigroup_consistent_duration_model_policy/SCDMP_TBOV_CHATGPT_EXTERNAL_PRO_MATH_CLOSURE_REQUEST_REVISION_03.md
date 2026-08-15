# SCDMP target-bound order-to-value ChatGPT Pro closure request

```text
provider=chatgpt
purpose=authoritative_definition_mathematical_and_causal_closure
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-ORDER-TO-VALUE
revision=SCDMP-TBOV-SCIENCE-20260815-03
conversation=continue_exact_existing_scdmp_direction_conversation
definition_only=true
scientific_activity_started=false
```

Continue the exact SCDMP conversation. You returned `REVISION_REQUIRED` for
`SCDMP-TBOV-SCIENCE-20260815-01`, identifying four defects: an unspecified
relation factorization/duration argument, reuse of selection checkpoints for
confirmation, two unadjusted positive routes, and an assay-level futility claim
about an unrun treatment. The owner accepts all four defects. Before resubmission,
the owner also made the formerly implicit product-coordinate law and exact
action-level `ORDER-TR`, `ORDER-Q` and `FREE-RESIDUAL` losses explicit. This
complete successor repairs everything prospectively; no scientific activity or
coordinate exists. B1/B2/B3 and revisions 01/02 remain immutable, and none of
their evidence, thresholds, seeds, checkpoints, acceptance or claims is an
input.

Review the exact indivisible prospective definition
`SCDMP-TBOV-SCIENCE-20260815-03`, whose owner identity is:

`docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_TARGET_BOUND_ORDER_TO_VALUE_SCIENCE_CARD_REVISION_03.md`

No task coordinate, source change, construction, test, probe, checkpoint,
training, evaluation or result exists. This request asks only whether the
scientific definition, branch law and bounded claim are mathematically and
causally closed.

## Target and physical order

Four public-role carriers hold one joint lateral-control action for an
externally supplied event-word duration `k`. State is payload lateral position
and velocity, yaw and yaw rate, signed center-of-mass offset, and four tether-
extension errors. Each carrier chooses `u_i in {-1,0,+1}`; the normalized force
and moment are

```text
f=(u_FL+u_FR+u_RL+u_RR)/4,
m=(u_FL-u_FR+u_RL-u_RR)/4.
```

The visible physical alphabet is carry `C`, signed internal mass shift `S+/-`
and signed gust `G+/-`. A shift first changes the current mass offset; a gust's
yaw impulse is proportional to that current offset. The deterministic update is

```text
b+ = clip(b + sigma*(2/5)*1[e=S_sigma], -4/5, 4/5)
g  = gamma*1[e=G_gamma]
v'     = (4/5)v + (2/5)f + (1/2)g
omega' = (4/5)omega + (2/5)m + (1/10)b+ + (3/2)g*b+
y'     = y+v'
psi'   = psi+omega'.
```

The four tether errors use the same state, corner signs and carrier actions:

```text
z'_FL=(4/5)z_FL+(1/5)( y'+psi'-b+)-(2/5)u_FL
z'_FR=(4/5)z_FR+(1/5)( y'-psi'-b+)-(2/5)u_FR
z'_RL=(4/5)z_RL+(1/5)(-y'+psi'+b+)-(2/5)u_RL
z'_RR=(4/5)z_RR+(1/5)(-y'-psi'+b+)-(2/5)u_RR.
```

Reward is one minus a fixed quadratic payload/yaw/tether/action cost, plus
state-based envelope penalties. Failure is absorbing after any tether error
exceeds `1.35` or yaw exceeds `0.95`. Event labels have no direct reward.

For even `k>=4`, `h=k/2-1`, freeze the only legal factorization and exact
reversal twins

```text
p_k=C^h S_sigma C^h,       |p_k|=k-1
q_k=G_gamma,               |q_k|=1
w_F=p_k q_k,
w_R=q_k p_k=reverse(w_F).
```

They contain the same signed physical event multiset. From center-of-mass
offset `b=-sigma/5`, shift-before-gust and gust-before-shift make the gust yaw
impulse use offsets of opposite sign. Their transitions and state-only rewards
therefore differ, and the future true-oracle qualification additionally
requires useful held-action reversals and value headroom.

One shared parameterization is fit only at `K_fit={4,10}` and used unchanged at
fixed `K_target={6,8,12}` and switches `6->12` and `12->6` in a 360-step
episode. Numeric `k` and the full word are deployable information. No per-`k`
head, retraining or mid-word action is legal.

The prospective boundary-state product law is independent uniform:

```text
y in [-0.25,0.25], v in [-0.15,0.15],
psi in [-0.20,0.20], omega in [-0.12,0.12],
b in [-0.40,0.40], and each z_i in [-0.20,0.20].
```

It is independent of `k,sigma,gamma`, orientation and action. Every block is
exactly balanced over permitted `k`, all four sign pairs and both orientations;
one seed-keyed pre-materialization permutation assigns any integer remainder.
Checkpoint rows draw one of 81 actions with counts differing by at most one and
retain full-word/all-contiguous-segment truth. Assay and target-qualification
base rows enumerate all 81 actions for both twins. Every Stage B training base
row is at `K_fit`, contains both orientations and all 81 actions, and retains
true intermediates; target `k` never enters training. Episodes reset from the
same product law, then use shared balanced sign/orientation tapes and on-policy
dynamics at subsequent boundaries. No realization is bound now.

## Model, shared checkpoint and containing comparator

One segment model predicts terminal state and cumulative reward for
`(x,u,w,ell)`, where `ell=|w|` is the actual segment duration and numeric
`ell/12` is visible. A complete-word call has `ell=k`; a shorter recursive call
receives only its actual segment length and no separate full-word `k`. The model
has one token GRU and shared state/action trunk; direct, correct and reversed
paths use the same inputs, outputs and action scorer. A per-seed `FREE-DIRECT`
base checkpoint is trained only by direct complete-word and segment truths at
fit durations.

Each seed computes once from its checkpoint-fit truths
`s_F,j=max(sd(F_j),1e-6)` and `s_G=max(sd(G),1e-6)`. For target `(F*,G*)`,

```text
D_theta=0.5*[mean_j((F_theta,j-F*_j)/s_F,j)^2
             +((G_theta-G*)/s_G)^2].
```

The direct loss first equal-averages the complete word and all retained
segments within a row, then equal-averages rows. Every actor scores all 81 held
actions by predicted cumulative word reward `G` only, with lexicographic ties
and no terminal bonus.

Each panel's checkpoint ensemble must pass untouched fit and disjoint target
direct-prediction competence, output variance and action-score sensitivity
gates. Stage A failure changes support/representation only in a new closed
revision. Stage B failure yields confirmation-checkpoint nonidentification with
no reuse, repair or reseeding. Neither is evidence against physical order.

For a presented forward twin, the identical hard-wired paths are

```text
F_C,F=F(F(x,u,p_k,k-1),u,q_k,1)
G_C,F=G(x,u,p_k,k-1)+G(F(x,u,p_k,k-1),u,q_k,1)

F_R,F=F(F(x,u,q_k,1),u,p_k,k-1)
G_R,F=G(x,u,q_k,1)+G(F(x,u,q_k,1),u,p_k,k-1).
```

For a presented reverse twin, the literal-correct path is `q_k` then `p_k` and
the paired-opposite path is `p_k` then `q_k`. Correct and reversed errors and
regrets equal-weight both presented orientations against each orientation's own
true transition, reward and oracle action. Higher `dF,dR,dQ` therefore always
means literal physical order is better; presenting `w_R` cannot flip the sign.
There is no alternate split.

Every actor scores the 81 held actions by predicted cumulative word reward only,
with the oracle's lexicographic tie rule and no terminal bonus. The paths share
the exact checkpoint, parameters, segment inputs, two call shapes, precision,
action enumeration and scoring; only segment order differs.
`FREE-DIRECT` predicts the complete ordered word without a recursive constraint,
sees complete-word and segment truths, and has the same deployable information.
Its unconstrained hypothesis class contains the maps allowed by either relation
treatment.

No coordinate is bound now. A later empirical authorization would bind two
mutually independent panels. Stage A has exactly ten paired selection seeds,
each with 4,096 checkpoint-fit action-word rows, 1,024 untouched fit-support
action-word rows and 256 target assay twin base rows per target `k`. Stage B has
exactly ten different paired confirmation seeds, each with 4,096 fresh
checkpoint-fit action-word rows, 1,024 fresh fit-support action-word rows, 256
fresh target-qualification twin base rows per target `k`, 4,096 all-action twin
arm-training base rows, 128 episodes per arm and target regime and 64 per arm
and seen diagnostic regime. Only the selected
treatment label transfers. No Stage A seed, checkpoint, parameter, optimizer or
RNG state, row, coordinate or tape enters Stage B. Nothing transfers from
B1/B2/B3.

## Stage A sole primary and treatment consequence

True-physics qualification requires, at every target `k`, material normalized
twin transition and reward separation; at least 30% unique-oracle action
reversals with useful oracle gaps; and an order-aware oracle advantage over the
best state/`k`/event-count/sign rule that cannot see event positions. The nine
physical components use simultaneous lower and separate upper families at
confidence `1-0.05/9`. All lower bounds must pass to qualify. Any upper bound
below its margin removes treatment eligibility from this object; the interval
between those outcomes is physical nonidentification, not deletion.

On disjoint assay coordinates, compare correct and reversed shared-checkpoint
paths. Define higher-is-better dimensionless components

```text
dF=(transition_R_error-transition_C_error)/true_twin_transition_gap
dR=(reward_R_error-reward_C_error)/true_twin_reward_gap
dQ=(true_regret(action_R)-true_regret(action_C))/oracle_order_headroom.
```

The sole primary is the intersection-union wrong-relation separation score

```text
S_order=min(dF/0.20,dR/0.20,dQ/0.10).
```

The exactly ten Stage A seeds, all target `k`, all components and simultaneous
three-member lower and separate upper families at confidence `1-0.05/3` form
one atomic panel. There is no latent-only success. The initial named learnable
treatment `ORDER-TR` continues direct training with literal-correct transition-
semigroup and reward-cocycle consistency over both twin orientations; its
control uses the paired-opposite relation. Every branch is fully differentiable
through the same live model, with no detach or target network.

For `Z in {CORRECT,REVERSED}`, the exact all-orientation/all-action loss is

```text
L_TR,Z=mean 0.5*[mean_j((F_direct,j-F_Z,j)/s_F,j)^2
                 +((G_direct-G_Z)/s_G)^2].
```

One exact prospective modification, `ORDER-Q`, replaces that auxiliary with
action-score consistency across all 81 held actions:

```text
L_Q,C=mean_orientation,a((Score_direct-Score_C)/s_G)^2,
L_Q,R=mean_orientation,a((Score_direct-Score_R)/s_G)^2.
```

Direct and composed scores are fully differentiable in both losses. CORRECT
versus REVERSED differs only by the frozen literal-correct versus paired-
opposite composition.

Frozen precedence is:

1. any physical upper bound below its margin deletes `ORDER-TR`/`ORDER-Q` from
   this object's Stage B menu, without trained-treatment futility;
2. otherwise incomplete physical lower-bound qualification is
   nonidentification and instantiates no treatment;
3. complete physical qualification with Stage A checkpoint incompetence
   modifies checkpoint support/representation only in a new revision;
4. after all gates, `UB(dQ)<-0.05` is action-adverse and deletes both treatment
   labels from this object's menu before any positive/modification branch;
5. lower bounds passing all `dF,dR,dQ` margins selects `ORDER-TR`;
6. after the adverse branch is excluded, `dF,dR` lower bounds pass but
   `UB(dQ)<0.05` modifies prospectively to `ORDER-Q`;
7. after all gates, `UB(dF)<0.05` or `UB(dR)<0.05` is assay-negative and
   deletes `ORDER-TR` eligibility from this object, without claiming that the
   unrun 800-update package lacks value; and
8. every other complete pattern is assay-indeterminate with no automatic
   threshold, seed, checkpoint or treatment change.

Branches 5 and 6 are disjoint because `LB(dQ)>0.10` and `UB(dQ)<0.05` cannot
both hold. The order assay selects, modifies or removes eligibility of a named
learnable treatment; it cannot terminate at representation separation. Only a
post-training Stage B upper-bound branch can scientifically delete the exact
trained treatment.

## Stage B direct external-k value

Only a Stage A selection or modification permits Stage B. Its treatment label
is frozen, then ten new seeds train fresh base checkpoints for 600 updates under
the identical law. No Stage A checkpoint or stochastic identity transfers.
Failure of the complete Stage B checkpoint competence panel yields checkpoint
nonidentification with no arm training, repair, reuse or reseeding. Within each
qualified fresh Stage B seed, all three arms clone its byte-identical checkpoint
and receive identical fresh data, direct loss, 800 updates, minibatches, AdamW
rule, clipping, action search and one final checkpoint:

- containing `FREE-DIRECT` with `FREE-RESIDUAL`, the equal average of
  `D_theta` on the two canonical literal-order segment calls for both
  orientations and all actions, using the true intermediate state for the
  second call and therefore no recursive constraint;
- selected `ORDER-TR-CORRECT` or `ORDER-Q-CORRECT`; and
- its identical-graph `ORDER-TR-REVERSED` or `ORDER-Q-REVERSED` control.

Every standardized direct and fully differentiable auxiliary/residual loss has
common coefficient one; no calibration, adaptive scaling, early stopping,
checkpoint sweep or budget search exists. The estimand is the total finite-
budget package effect, not a common optimizer trajectory or unique mediation.

For each target regime, record return per primitive step `J`, payload failure
probability `P`, and positive order-aware-oracle minus best-order-blind headroom
`H`. For each control `X`, each Stage B seed supplies equal-weight target
endpoints

```text
V_J,s(C,X)=mean_r[(J_C,s-J_X,s)/H_s],
V_P,s(C,X)=mean_r[P_X,s-P_C,s].
```

The four aggregate contrasts `{V_J vs FREE, V_J vs REVERSED, V_P vs FREE,
V_P vs REVERSED}` share one simultaneous one-sided lower-bound benefit family:
each paired-seed t bound has `df=9` and confidence `1-0.05/4=0.9875`. Return and
failure are therefore two readings of one family, not two full-alpha positive
opportunities. A separate four-member futility family uses one-sided upper
bounds at the same confidence.

The 28 endpoint-by-control-by-regime contrasts have a separate simultaneous
non-harm lower-bound family and a separate simultaneous adverse upper-bound
family, each member at confidence `1-0.05/28`. Target returns are headroom-
normalized; seen `k={4,10}` returns are raw reward-per-step differences and
supply non-harm only. Adverse absence is not non-harm. Exact sign-randomization
is descriptive. Useful margins are `0.10` return headroom and `0.05` absolute
failure probability; harm margins are `-0.04` normalized target/raw seen return
and `-0.03` failure improvement.

Precedence is Stage B checkpoint nonidentification; adverse; return value over
both controls with all non-harm bounds; failure robustness over both controls
with all non-harm bounds; containing-FREE sufficient when at least one benefit
route qualifies against reversed but both useful upper bounds versus FREE are
excluded; exact-treatment deletion when all four useful upper bounds versus
both controls are excluded; otherwise valid indeterminate. The two positive
routes use the same benefit family. No representation-only Stage B branch
exists.

## Activity and claim boundary

This definition stage has no scientific activity. In a later separately
authorized empirical object, Stage A activity begins immediately before the
first Stage A base-checkpoint update. Stage B activity begins immediately before
the first fresh Stage B confirmation-checkpoint update, not the first arm
update. Each panel's ten seed identities, coordinates, treatment law, budget,
endpoint families and branches then become immutable. No seed, checkpoint,
parameter, optimizer/RNG state, row, coordinate or tape crosses panels.

The strongest alternative is target-adapted finite-budget supervision and
optimizer geometry: the visible full word lets the more flexible direct learner
learn order without explicit composition, while Stage A selects between generic
multi-path prediction regularization (`ORDER-TR`) and generic all-action ranking
regularization (`ORDER-Q`), each changing curvature, gradient alignment,
clipping and AdamW history. Independent Stage B checkpoints prevent selection
on the same checkpoint randomness but do not establish unique mediation. Even
a positive is only an exact deterministic fixed-`N=4` payload-task, finite-
budget, `k={4,10}` to
`k={6,8,12}`/switch-regime inductive-bias result. It cannot establish arbitrary
`k`, variable `N`, unique semigroup mediation, another surface, general payload
robotics, UAV, safety or real-flight value. Stage A alone cannot claim task
value.

## Required disposition

Return exactly one leading disposition:

- `CLOSED` if the complete definition is mathematically and causally coherent,
  the containing comparator and identical-path assay support the branch law,
  Stage A validly selects/modifies/removes eligibility of the named treatment,
  the independent Stage B checkpoints and simultaneous endpoint families can
  support the bounded variable-`k` claim, and no
  science-bearing ambiguity remains; or
- `REVISION_REQUIRED` with every exact mathematical/causal defect, unreachable
  or overlapping branch, shortcut, comparator failure, missing observable,
  activity-boundary defect and the maximum defensible claim.

Also state the strongest alternative explanation and the single highest-value
prospective correction or discriminator. Do not review code, tests, hashes,
receipts, runtime feasibility, cost, portfolio priority or production authority.
