# SCDMP target-bound order-to-value ChatGPT Pro closure request

```text
provider=chatgpt
purpose=authoritative_definition_mathematical_and_causal_closure
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-ORDER-TO-VALUE
revision=SCDMP-TBOV-SCIENCE-20260815-01
conversation=continue_exact_existing_scdmp_direction_conversation
definition_only=true
scientific_activity_started=false
```

Continue the exact SCDMP conversation in which you closed the stability-first
B3 object and later concurred with its branch-2 result interpretation. B3 is
complete and immutable. Its observations, thresholds, seeds, checkpoints,
acceptance and claims are not inputs here. The only inherited motivation is
that a new target-bound object should isolate hard-wired relation direction at
one shared competent checkpoint and connect the assay to direct variable-`k`
value.

Review the exact indivisible prospective definition
`SCDMP-TBOV-SCIENCE-20260815-01`, whose owner identity is:

`docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_TARGET_BOUND_ORDER_TO_VALUE_SCIENCE_CARD.md`

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

For even `k>=4`, `h=k/2-1`, define the exact reversal twins

```text
w_F=C^h S_sigma C^(k-2-h) G_gamma,
w_R=reverse(w_F)=G_gamma C^(k-2-h) S_sigma C^h.
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

## Model, shared checkpoint and containing comparator

One segment model predicts terminal state and cumulative reward for
`(x,u,w,k)`. It has one token GRU and shared state/action trunk; direct,
correct and reversed paths use the same inputs, outputs and action scorer. A
per-seed `FREE-DIRECT` base checkpoint is trained only by direct complete-word
and segment truths at fit durations, then byte-identically shared.

The checkpoint must pass untouched fit and disjoint target direct-prediction
competence, output variance and action-score sensitivity gates. Failure changes
checkpoint support/representation in a new closed revision and is not evidence
against physical order.

For literal prefix `p` and suffix `q`, the identical hard-wired paths are

```text
F_C=F(F(x,u,p),u,q)
G_C=G(x,u,p)+G(F(x,u,p),u,q)

F_R=F(F(x,u,q),u,p)
G_R=G(x,u,q)+G(F(x,u,q),u,p).
```

They share the exact checkpoint, parameters, calls, inputs, precision, action
enumeration and scoring. `FREE-DIRECT` predicts the complete ordered word
without a recursive constraint, sees complete-word and segment truths, and has
the same model/function inputs. Its unconstrained hypothesis class contains the
maps allowed by either relation treatment.

No coordinate is bound now. A later empirical authorization would bind exactly
ten fresh paired seed blocks and disjoint checkpoint-fit, order-assay, arm-
training and final-value coordinates. The frozen prospective counts are 4,096
checkpoint-fit transitions, 1,024 untouched support transitions, 256 assay
twin states per target `k`, 4,096 Stage B training transitions, 128 episodes per
arm/target regime and 64 per arm/seen diagnostic regime. Nothing transfers from
B1/B2/B3.

## Stage A sole primary and treatment consequence

True-physics qualification requires, at every target `k`, material normalized
twin transition and reward separation; at least 30% unique-oracle action
reversals with useful oracle gaps; and an order-aware oracle advantage over the
best state/`k`/event-count/sign rule that cannot see event positions.

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

All target `k`, all components and simultaneous one-sided paired-seed bounds
form one atomic panel. There is no latent-only success. The initial named
learnable treatment `ORDER-TR` continues direct training with the correct
transition-semigroup and reward-cocycle auxiliary; its control uses the
identical reversed relation.

One exact prospective modification, `ORDER-Q`, replaces that auxiliary with
action-score consistency across all 81 held actions:

```text
L_Q,C=mean_a(Score_direct-Score_C)^2,
L_Q,R=mean_a(Score_direct-Score_R)^2.
```

Frozen precedence is:

1. physical/action/value qualification failure deletes order treatment for
   this target;
2. physical qualification with checkpoint incompetence modifies checkpoint
   support/representation in a new revision and stops;
3. lower bounds passing all `dF,dR,dQ` margins selects `ORDER-TR`;
4. `dF,dR` lower bounds pass but the `dQ` upper bound is below `0.05`, with
   physical action/value headroom intact, modifies prospectively to `ORDER-Q`;
5. after all qualifications, `dF` or `dR` upper below `0.05`, or `dQ` upper
   below `-0.05`, deletes exact `ORDER-TR` for this task/checkpoint; and
6. every other complete pattern is assay-indeterminate with no automatic
   threshold, seed, checkpoint or treatment change.

Thus the order assay selects, modifies or deletes a named learnable treatment;
it cannot terminate at representation separation.

## Stage B direct external-k value

Only a Stage A selection or modification permits Stage B. All three arms clone
the shared checkpoint and receive identical fresh data, direct loss, 800
updates, minibatches, AdamW rule, clipping, action search and one final
checkpoint:

- containing `FREE-DIRECT` with an output-connected direct residual objective;
- selected `ORDER-TR-CORRECT` or `ORDER-Q-CORRECT`; and
- its identical-graph `ORDER-TR-REVERSED` or `ORDER-Q-REVERSED` control.

Every standardized direct and auxiliary/residual loss has common coefficient
one; no calibration, adaptive scaling, early stopping, checkpoint sweep or
budget search exists. The estimand is the total finite-budget package effect,
not a common optimizer trajectory or unique mediation.

For each target regime, record return per primitive step `J`, payload failure
probability `P`, and positive order-aware-oracle minus best-order-blind headroom
`H`. For each control `X`, equal-weight target endpoints are

```text
V_J(C,X)=mean[(J_C-J_X)/H],
V_P(C,X)=mean[P_X-P_C].
```

Useful margins are `0.10` of return headroom and `0.05` absolute failure
probability; per-regime harm margins are `-0.04` and `-0.03`. Ten paired seeds,
branch-local simultaneous one-sided t bounds and exact sign-randomization are
prospectively fixed. Seen `k={4,10}` supplies non-harm only.

Precedence is adverse; direct variable-`k` return value over both controls;
failure robustness over both controls; containing-FREE sufficient when the
correct arm qualifies against reversed but both useful upper bounds versus
FREE are excluded; exact-treatment deletion when useful upper bounds versus
both controls are excluded; otherwise valid indeterminate. A positive requires
target-regime and seen-regime non-harm. No representation-only Stage B branch
exists.

## Activity and claim boundary

This definition stage has no scientific activity. In a later separately
authorized empirical object, Stage A activity begins immediately before the
first base-checkpoint update, and Stage B activity begins immediately before
the first post-checkpoint arm update. Each packet and every coordinate,
treatment, budget, endpoint and branch then becomes immutable. Stage A and B
coordinate blocks are disjoint.

The strongest alternative is finite-budget supervision and optimizer geometry:
the visible full word lets the more flexible direct learner learn order without
explicit composition, while an auxiliary changes curvature, gradient alignment,
clipping and optimizer history. Even a positive is only an exact deterministic
fixed-`N=4` payload-task, finite-budget, `k={4,10}` to
`k={6,8,12}`/switch-regime inductive-bias result. It cannot establish arbitrary
`k`, variable `N`, unique semigroup mediation, another surface, general payload
robotics, UAV, safety or real-flight value. Stage A alone cannot claim task
value.

## Required disposition

Return exactly one leading disposition:

- `CLOSED` if the complete definition is mathematically and causally coherent,
  the containing comparator and identical-path assay support the branch law,
  Stage A validly selects/modifies/deletes the named treatment, the disjoint
  Stage B endpoints can support the bounded variable-`k` claim, and no
  science-bearing ambiguity remains; or
- `REVISION_REQUIRED` with every exact mathematical/causal defect, unreachable
  or overlapping branch, shortcut, comparator failure, missing observable,
  activity-boundary defect and the maximum defensible claim.

Also state the strongest alternative explanation and the single highest-value
prospective correction or discriminator. Do not review code, tests, hashes,
receipts, runtime feasibility, cost, portfolio priority or production authority.
