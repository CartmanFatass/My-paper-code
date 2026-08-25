# SCDMP target-bound order-to-value definition science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-ORDER-TO-VALUE
revision=SCDMP-TBOV-SCIENCE-20260815-01
owner=EM_semigroup_consistent_duration_model_policy
stage=definition_only
old_exact_objects_immutable=true
old_evidence_threshold_seed_acceptance_transfer=false
coordinate_realizations_bound=false
construction_authorized=false
source_change_authorized=false
test_or_probe_authorized=false
training_or_evaluation_authorized=false
compute_or_lease_authorized=false
fusion_or_second_surface_authorized=false
scientific_activity_started=false
```

## Decision and target-bound question

This card defines one prospective fixed-four-carrier payload/formation task in
which an externally supplied skill duration `k` is the length of a visible
physical-event word. Each carrier chooses once at the boundary and holds its
action for all `k` primitive steps. A mass-shift event and a gust event do not
commute: reversing the same event multiset can change payload transition,
cumulative reward, the optimal held joint action and direct external-`k` task
value.

The direction-local question is:

> After one directly supervised model is independently competent, does its
> correct hard-wired event composition separate from the identical reversed
> path strongly enough at transition, reward and held-action value to select a
> learnable order treatment; and, on disjoint fresh data, does the selected
> treatment improve held-out and switched-`k` payload value over both a
> strictly containing `FREE-DIRECT` learner and its order-reversed control?

The hard-wired assay is not a latent endpoint. Its prospective branches select
`ORDER-TR`, modify it to `ORDER-Q`, delete the exact order treatment, or return
an indeterminate definition. Only the selected or modified treatment can enter
the separately evaluated direct-value comparison.

This is a new target-bound definition. The completed B1/B2/B3 convoy objects
motivate the use of a shared checkpoint and identical hard-wired paths, but no
old DGP row, equation constant, threshold, margin, seed, tape, checkpoint,
acceptance, estimate or claim is an input.

## Payload/formation task

### State, four carrier actions and held-action boundary

Four carriers occupy fixed public corner roles `FL,FR,RL,RR` around one rigid
payload. At a true skill boundary the deployable state is

```text
x = (y, v, psi, omega, b, z_FL, z_FR, z_RL, z_RR).
```

`y,v` are lateral payload displacement and velocity; `psi,omega` are payload
yaw and yaw rate; `b` is the signed lateral center-of-mass offset of the
payload; and `z_i` is carrier `i`'s signed tether-extension error. Forward
progress is exogenous and identical across arms while the payload remains
intact.

Each carrier chooses `u_i in {-1,0,+1}` once. The 81 joint actions are ordered
lexicographically in public role order and are held unchanged for the complete
word. Define normalized lateral force and yaw moment

```text
f(u) = (u_FL + u_FR + u_RL + u_RR)/4,
m(u) = (u_FL - u_FR + u_RL - u_RR)/4.
```

No mid-word observation, replanning, communication or termination is legal.
All arms receive the same current state, complete ordered event word, numeric
`k`, previous joint action and public roles. They receive no future state,
reward, oracle action, result, arm identity or hidden event.

### Physical events and noncommuting micro-dynamics

The alphabet is

```text
E = {C, S+, S-, G+, G-},
```

where `C` is ordinary carrying, `S_sigma` is a signed internal payload mass
shift, and `G_gamma` is a signed lateral gust. The labels have no reward term;
they matter only through the physical update.

Let `sigma,gamma in {-1,+1}` and use the following fixed normalized constants:

```text
delta_b=2/5, b_max=4/5,
a_v=a_omega=4/5,
c_f=c_m=2/5,
c_g=1/2, c_bg=3/2,
c_b=1/10, c_z=1/5.
```

For event `e_j`, first update the load offset

```text
b^+ = clip(b + sigma*delta_b * 1[e_j=S_sigma], -b_max, b_max).
```

Then update the payload and formation:

```text
g_j = gamma * 1[e_j=G_gamma]
v'     = a_v*v     + c_f*f(u) + c_g*g_j
omega' = a_omega*omega + c_m*m(u) + c_b*b^+ + c_bg*g_j*b^+
y'     = y + v'
psi'   = psi + omega'

z'_FL = a_v*z_FL + c_z*( y' + psi' - b^+) - c_f*u_FL
z'_FR = a_v*z_FR + c_z*( y' - psi' - b^+) - c_f*u_FR
z'_RL = a_v*z_RL + c_z*(-y' + psi' + b^+) - c_f*u_RL
z'_RR = a_v*z_RR + c_z*(-y' - psi' + b^+) - c_f*u_RR.
```

The next state is `x'=(y',v',psi',omega',b^+,z'_FL,...,z'_RR)`.
All arithmetic is deterministic float64 in the future empirical object.

`S_sigma` and `G_gamma` do not commute because the gust yaw impulse uses the
current load offset. For example, from `b=-sigma*delta_b/2`, a gust after the
shift uses `b=+sigma*delta_b/2`, while the same gust before the same shift uses
`b=-sigma*delta_b/2`. The resulting yaw impulse changes sign. Integration and
the state-only formation cost preserve this order difference even though both
words contain exactly the same events and finish with the same load offset.

### Reward, failure and true oracle

After each transition define the formation envelope

```text
q(x') = y'^2 + 0.35*v'^2 + 1.4*psi'^2 + 0.45*omega'^2
        + 0.30*mean_i z_i'^2 + 0.12*mean_i u_i^2.
```

Primitive reward is

```text
r(x,u,e_j,x') = 1 - q(x')
                - 2.5*max(0,max_i|z_i'|-1)^2
                - 3.0*max(0,|psi'|-0.7)^2.
```

A payload/formation failure occurs at the first primitive step with
`max_i|z_i|>1.35` or `|psi|>0.95`. Failure is absorbing for the rest of the
episode with zero progress and reward `-1` per remaining primitive step. The
word reward is the undiscounted sum of primitive rewards. Episode return is
total reward divided by the fixed primitive horizon.

The true audit oracle receives the same boundary state, visible word, held-
action constraint and 81 legal joint actions. It rolls the known deterministic
dynamics once for each action and selects maximum true word reward, breaking
ties lexicographically. It is never a learner input or training target. A
unique oracle action requires the best-minus-second-best true word reward to
exceed `0.02*k`; otherwise that word-state is excluded from the oracle-action
reversal fraction but remains in transition and reward populations.

## External-`k` words, regimes and fresh-coordinate boundary

### Word twins with identical physical event multisets

For even `k>=4`, sign pair `(sigma,gamma)`, and `h=k/2-1`, define

```text
w_forward(k,sigma,gamma) = C^h S_sigma C^(k-2-h) G_gamma
w_reverse(k,sigma,gamma) = reverse(w_forward)
                           = G_gamma C^(k-2-h) S_sigma C^h.
```

Each twin contains one identical signed shift, one identical signed gust and
`k-2` identical carry events. Only physical order changes. Both literal words
are visible; there is no REAL/SHAM label and no token-only negative control.
Sign-balanced words and state reflection pairs prevent a fixed direction or
token-position shortcut.

One shared parameterization is prospectively fit at external durations

```text
K_fit = {4,10}
```

and evaluated without retraining at

```text
K_target = {6,8,12}.
```

The target regimes are fixed `6`, fixed `8`, fixed `12`, `6->12` and `12->6`.
Switches occur only at a true boundary at primitive step 180 of a 360-step
episode; the new `k` and word are revealed before the next held action. Seen-
duration fixed `4` and fixed `10` are diagnostic non-harm regimes, not target
value evidence.

No per-`k` head, separately trained policy, duration-specific optimizer or
target-`k` update is legal. Variable-`k` value means that the one learned
parameterization is used unchanged across all target fixed and switch regimes.

### No coordinates exist in this definition stage

This card freezes the DGP, word families, `k` regimes, estimands, branches and
future coordinate law, but binds no realization. A later empirical portfolio
decision must prospectively bind fresh, blinded and mutually disjoint blocks
for:

1. direct-checkpoint fitting and support qualification;
2. the hard-wired order assay;
3. post-checkpoint arm training; and
4. final fixed/switch-`k` value evaluation.

The later binding must use exactly ten paired algorithm-seed blocks, materialize
all state/word/action rows once, and share them across paths or arms. Each seed
has 4,096 checkpoint-fit word transitions, 1,024 untouched checkpoint-support
transitions, 256 order-twin boundary states per target `k`, 4,096 fresh Stage B
training transitions, 128 final episodes per arm and target regime, and 64
diagnostic episodes per arm and seen-duration regime. Exact seed identities,
reset coordinates, minibatch tapes and episode tapes do not exist now. None may
be imported from B1, B2 or B3. Assay coordinates may never enter post-checkpoint
training or final value evaluation.

## Shared model, containing comparator and path definitions

### One directly supervised segment model

The shared model accepts `(x,u,w,k)` for any legal contiguous word segment and
returns

```text
F_theta(x,u,w) -> terminal state prediction,
G_theta(x,u,w) -> cumulative word reward prediction.
```

It uses one 32-dimensional token GRU, a two-layer width-128 state/action trunk,
and separate two-layer width-128 transition and reward heads. Numeric `k/12`
and segment length are visible. There is no arm, regime or target-duration
indicator. The future CM may change only implementation-equivalent layout, not
the function inputs, outputs or shared-parameter semantics.

The learned actor scores every legal held joint action as predicted cumulative
reward plus the same frozen terminal formation potential, then applies the
same lexicographic tie rule as the oracle. Every compared path uses the same
action set and scoring code.

### Independently competent shared checkpoint

For each future paired seed, one `FREE-DIRECT` base model is trained only on
the fresh `K_fit` checkpoint block with direct truth for complete words and
all legal prefix/suffix segments. Its loss equally weights standardized
terminal-state and cumulative-reward squared errors. No recursive relation,
hard-wired path comparison, target coordinate or target value enters this
checkpoint.

The checkpoint is frozen and byte-identically shared by the correct and
reversed assay paths and, if selected, cloned by all post-checkpoint training
arms. It qualifies only if:

- its untouched `K_fit` composite RMSE is at most `0.65` of a training-target
  mean predictor;
- on the disjoint target assay population, its direct full-word composite RMSE
  is at most `0.85` of the same coordinate-local mean predictor and the
  across-seed one-sided 95% upper bound is below `0.95`;
- every predicted physical coordinate has finite positive variance between
  `0.25` and `4.0` times its true variance; and
- at least `90%` of unique-oracle target word-states have predicted legal-action
  score range at least `0.03*k`.

These are new target-bound qualification rules, not inherited thresholds.
Failure modifies the direct checkpoint representation/support before any order
treatment can be selected; it is not evidence against physical order or the
SCDMP family.

### Identical hard-wired correct and reversed paths

For a word split into its literal prefix `p` and suffix `q`, define the correct
path on the one frozen checkpoint:

```text
F_C(x,u,pq) = F_theta(F_theta(x,u,p),u,q)
G_C(x,u,pq) = G_theta(x,u,p) + G_theta(F_theta(x,u,p),u,q).
```

The reversed path differs only in segment order:

```text
F_R(x,u,pq) = F_theta(F_theta(x,u,q),u,p)
G_R(x,u,pq) = G_theta(x,u,q) + G_theta(F_theta(x,u,q),u,p).
```

The two paths share the exact checkpoint, parameters, inputs, calls, precision,
action enumeration and score rule. Their event multiset is identical. No
coefficient, optimizer history, checkpoint, call count or capacity differs.
For each complete word, the split is immediately before its `S` token for the
forward word and immediately before the same physical `S` token in the reverse
word; the companion split before `G` is reported but cannot be selected.

`FREE-DIRECT` is the containing comparator: the same model directly maps the
complete ordered word to transition and reward with no recursive constraint.
Its hypothesis class contains the mappings available to either hard-wired
path, it sees all segment and full-word truths, and it has the same deployable
information and action scorer.

## Stage A: hard-wired order assay and treatment decision

### Physical/action/value qualifications

Before interpreting a learned path, the exact true DGP on the disjoint assay
population must satisfy all of:

- for every target `k`, the median twin terminal-state distance, normalized by
  the safe state envelope, is at least `0.12`;
- for every target `k`, the median absolute twin cumulative-reward difference
  is at least `0.06*k`;
- at least `30%` of unique-oracle twin word-states select different held joint
  actions, and the mean smaller oracle gap on those reversals is at least
  `0.04*k`; and
- the order-aware true oracle exceeds the best order-blind action rule by at
  least `0.08` reward per primitive step on average across target regimes.

The order-blind rule may use state, `k`, event counts and signs but not event
positions. It is chosen optimally on the assay population. These gates establish
that order is physically and decision relevant rather than a token label.
Failure deletes the exact order treatment for this target task; it does not
delete semigroup learning elsewhere.

### Sole primary wrong-relation separation endpoint

On every assay word-state and legal action, compare the correct and reversed
hard-wired paths with the true complete-word transition and reward. Let

```text
dF = (RMSE_R - RMSE_C) / median_true_twin_state_distance,
dR = (MAE_R  - MAE_C)  / median_true_twin_reward_difference,
dQ = (true_regret(action_R) - true_regret(action_C))
     / order_aware_oracle_minus_order_blind_headroom.
```

Each denominator is computed within target `k` before equal weighting across
`k`; every denominator must be finite and positive. The sole primary endpoint
is the intersection-union wrong-relation separation score

```text
S_order = min(dF/0.20, dR/0.20, dQ/0.10).
```

Ten or more future paired seeds are the independent inference units. A
successful assay requires the simultaneous one-sided 95% lower confidence
bound for each unscaled component to exceed its denominator margin, equivalently
the lower bound of every component of `S_order` to exceed `1`. Exact paired
sign-randomization results accompany but do not replace the bounds. No latent
metric, checkpoint, split, word, `k`, or component can be selected after data.

### Named learnable treatment and frozen assay branches

The initial named treatment is `ORDER-TR`: from the common checkpoint, continue
direct training while adding correct transition-semigroup and reward-cocycle
consistency. Its matched wrong-relation control applies the identical loss and
graph with `p,q` reversed.

The predeclared modification is `ORDER-Q`: retain the same direct model and
paths, but replace the transition/reward consistency penalty by an action-score
consistency loss across all 81 held actions,

```text
L_Q,C = mean_a ( Score_direct(x,a,pq) - Score_C(x,a,pq) )^2,
L_Q,R = mean_a ( Score_direct(x,a,pq) - Score_R(x,a,pq) )^2.
```

The branch order is:

1. **DELETE-TARGET:** any physical/action/value qualification fails. Do not
   train an order treatment on this target.
2. **MODIFY-CHECKPOINT:** physical qualifications pass but shared-checkpoint
   competence fails. Redefine checkpoint support/representation in a new
   Pro-closed revision; do not interpret order or proceed to value.
3. **SELECT-ORDER-TR:** all three `S_order` component lower bounds pass. Freeze
   `ORDER-TR-CORRECT`, `ORDER-TR-REVERSED` and `FREE-DIRECT` for Stage B.
4. **MODIFY-TO-ORDER-Q:** `dF` and `dR` lower bounds pass their margins, while
   the one-sided 95% upper bound of `dQ` is below `0.05`, with physical oracle
   action/value headroom still qualified. Freeze the already defined
   `ORDER-Q-CORRECT`, `ORDER-Q-REVERSED` and `FREE-DIRECT` for Stage B.
5. **DELETE-ORDER-TR:** with all physical and competence qualifications passed,
   either the upper bound of `dF` or `dR` is below `0.05`, or the upper bound
   of `dQ` is below `-0.05`. Delete `ORDER-TR` on this exact task/checkpoint;
   no Stage B treatment is selected.
6. **ASSAY-INDETERMINATE:** every other complete outcome. No threshold, seed,
   split, checkpoint or treatment changes automatically.

Adverse and deletion branches precede selection. The Stage A packet is atomic:
all target `k`, all three components, qualifications and confidence bounds must
exist. Partial component selection is forbidden.

## Stage B: selected-treatment external-`k` value object

Stage B uses new disjoint training and evaluation coordinates. Every arm begins
from the byte-identical qualified checkpoint and receives the same full-word
and segment rows, direct loss, update count, minibatch order, optimizer,
clipping, action scorer and legal actions. The future frozen package uses 600
checkpoint updates followed, if selected, by 800 post-checkpoint updates per
arm, batches of 256 complete word rows, AdamW with learning rate `3e-4`,
`beta=(0.9,0.999)`, `eps=1e-8`, weight decay `1e-5`, and global gradient-norm
clip `1.0`. There is exactly one final checkpoint after update 800 and no
early stopping, checkpoint sweep, second budget or budget search.

The three arms are:

1. `FREE-DIRECT`, continuing only direct full-word and segment supervision;
2. the assay-selected `ORDER-TR-CORRECT` or `ORDER-Q-CORRECT`; and
3. its exactly matched `ORDER-TR-REVERSED` or `ORDER-Q-REVERSED` control.

The relation arms add the selected auxiliary on the same rows. `FREE-DIRECT`
uses an output-connected direct residual objective on the same number and shape
of full-word/segment calls. Transition coordinates and cumulative reward are
standardized once from the checkpoint-fit block; every direct, relation and
residual component is the mean of its standardized squared output residuals.
The direct loss has coefficient `1`, and the selected relation or matched
FREE-residual loss has one common coefficient `1` in every arm for all 800
updates. There is no calibration or adaptive scale. No later gradient,
checkpoint, target score or result may tune, stop, amplify or select an arm.
The causal estimand is the total finite-budget algorithm-package contrast; it
is not a common-optimizer-trajectory or unique-mediation effect.

### Direct variable-`k` endpoints

For target regime `r`, arm `M` and paired seed `s`, record:

```text
J_M,s(r) = episode reward per primitive step,
P_M,s(r) = payload/formation failure probability,
H_s(r)   = J_true_order_oracle,s(r) - J_best_order_blind,s(r).
```

Every `H_s(r)` must exceed `0.08`; otherwise that regime is not value-qualified.
For control `X in {FREE,REVERSED}` define target averages, weighting the five
target regimes equally,

```text
V_J(C,X) = mean_r,s [(J_C,s(r)-J_X,s(r))/H_s(r)],
V_P(C,X) = mean_r,s [P_X,s(r)-P_C,s(r)].
```

Seen-duration fixed `4` and `10` produce only per-regime non-harm checks. The
update budget and paired-seed count are frozen above; only the fresh random
identities and materialized coordinates await a later empirical authorization.

Use simultaneous one-sided paired-seed t bounds with `df=9` within each declared
branch. If a branch contains `M` control-by-regime-by-endpoint members, each
bound uses confidence `1-0.05/M`; branch conjunctions create no selection among
members. Exact paired sign-randomization results accompany but never replace
the bounds.
The smallest useful target effects are `0.10` of oracle-over-order-blind return
headroom and `0.05` absolute failure probability. The harm margins are `-0.04`
headroom-normalized return and `-0.03` failure-probability improvement.

### Frozen Stage B interpretation

Interpret one complete atomic packet in this order:

1. **ADVERSE:** for either control or any target/seen regime, a simultaneous
   upper bound establishes return harm below `-0.04` or failure harm below
   `-0.03`. Reject only the exact selected package on this task and budget.
2. **VARIABLE-K RETURN VALUE:** for both controls, lower bounds for `V_J` exceed
   `0.10`, every target-regime return lower bound exceeds the harm margin, and
   every target/seen failure bound is non-harmful.
3. **VARIABLE-K FAILURE ROBUSTNESS:** for both controls, lower bounds for `V_P`
   exceed `0.05`, every target-regime failure lower bound exceeds the harm
   margin, and every target/seen return bound is non-harmful.
4. **CONTAINING-FREE SUFFICIENT:** the selected correct arm qualifies against
   REVERSED but not `FREE-DIRECT`, and the upper bounds of both value effects
   versus FREE are below their useful margins. Delete the selected recursive
   auxiliary for this target at the frozen budget; direct ordered modeling is
   sufficient.
5. **EXACT-TREATMENT DELETION:** with all qualifications and non-harm checks
   passed, the upper bounds of both return and failure improvements against
   both controls are below their useful margins. Delete only the exact selected
   treatment/package.
6. **VALID INDETERMINATE:** every other complete result. No seed, budget,
   coefficient, threshold, `k`, surface or treatment change follows.

Return-value and failure-robustness branches are alternatives: either may
establish project-relevant variable-`k` value. No representation-only or
latent-separation branch exists in Stage B.

## Scientific activity and immutability boundaries

The current definition stage contains no scientific activity. Reading,
authoring, Pro/Gemini consultation and CM static feasibility/cost review do not
instantiate a task coordinate or treatment.

If empirical work is later authorized:

- Stage A scientific activity begins immediately before the first gradient
  update used to create the shared direct checkpoint. From that moment its
  coordinate blocks, architecture, training rule and assay branches are
  immutable.
- Stage B scientific activity begins immediately before the first arm-specific
  post-checkpoint gradient update. The selected treatment, controls, data,
  coefficients, budget, endpoints and branch law are then immutable.
- Stage A and Stage B are separate atomic packets. Stage A coordinates cannot
  be reused in Stage B, and Stage B cannot start unless one legal assay branch
  prospectively selects or modifies a treatment.

No result can choose a checkpoint, split, persistence window, seed, coefficient,
budget, target duration, endpoint, margin or partial panel. Any science-bearing
change requires a new complete EM revision and same-conversation Pro closure.

## Strongest alternative and claim ceiling

The strongest alternative even after a positive result is finite-budget
optimization and supervision geometry. `FREE-DIRECT` is more flexible and sees
direct segment truth; the selected auxiliary changes curvature, gradient
alignment, clipping and optimizer history. A correct package can win because
its constraint is a useful regularizer on this event distribution, not because
semigroup structure is uniquely necessary. Conversely, FREE can learn the
ordered mapping directly from visible word positions, making explicit
composition redundant.

The shared-checkpoint assay isolates hard-wired direction from arm-specific
training history, but it does not prove that a later training gain is uniquely
mediated by algebra. The deterministic, fully observed word also excludes
unknown-event adaptation and partial observability.

The maximum positive Stage B claim is:

> On this exact deterministic four-carrier payload/formation task, one shared
> finite-budget model/policy trained at `k={4,10}` and used unchanged at fixed
> `k={6,8,12}` and switches `6<->12` achieved the registered return or
> failure-robustness improvement over both a containing direct learner and a
> matched reversed-order package, conditional on the frozen physical,
> competence, wrong-relation, headroom and non-harm qualifications.

It is an exact-task finite-budget inductive-bias claim. It is not arbitrary-
`k`, variable-`N`, unique semigroup mediation, equal-optimizer-trajectory,
stochastic or partially observed robustness, general payload robotics, another
surface, UAV, safety or real-flight evidence. Stage A alone supports no direct
task-value claim.

## Definition-stage completion and authority boundary

This object is complete for independent same-direction scientific consultation
and static CM review. Pro mathematical/causal closure plus EM intake can close
only its definition. Gemini may propose alternatives but cannot close or select
it. CM may assess whether the DGP, observations, comparator, path construction,
branch observables and prospective costs are statically bindable; CM may not
construct, test or probe them in this stage.

No source change, environment creation, coordinate realization, checkpoint,
training, evaluation, compute lease, empirical selection, fusion, second
surface or UAV action is authorized. A later empirical step requires a new
dedicated portfolio decision and Operational Root envelope.
