# SCDMP target-bound order-to-value definition science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-ORDER-TO-VALUE
revision=SCDMP-TBOV-SCIENCE-20260815-03
supersedes_revision=SCDMP-TBOV-SCIENCE-20260815-02_OWNER_COMPLETENESS_REVISION
owner=EM_semigroup_consistent_duration_model_policy
stage=definition_only
artifact_status=FROZEN_OWNER_COMPOSITE_PRE_PRO
chatgpt_external_pro_math_closure=required_in_existing_scdmp_conversation
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
`ORDER-TR`, modify it to `ORDER-Q`, delete its eligibility for instantiation in
this exact object, or return an indeterminate definition. Assay deletion means
only "not selected and not run here"; it is not a futility claim about the
unrun trained package. Only the selected or modified treatment can enter an
independent, separately evaluated direct-value confirmation panel.

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
`k` and public roles. They receive no previous action, future state, reward,
oracle action, result, arm identity or hidden event.

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
Exact sign/orientation balance and the symmetric state law below prevent a fixed
sign or direction shortcut. Literal token position remains visible by design:
`FREE-DIRECT` is allowed to learn it, while CORRECT-versus-REVERSED asks whether
the physically right composition direction matters beyond that containing
alternative.

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

### Prospective product-coordinate law

Every independently materialized boundary state is drawn in float64 from the
following product law:

```text
y     ~ Uniform[-0.25, 0.25]
v     ~ Uniform[-0.15, 0.15]
psi   ~ Uniform[-0.20, 0.20]
omega ~ Uniform[-0.12, 0.12]
b     ~ Uniform[-0.40, 0.40]
z_i   ~ Uniform[-0.20, 0.20] independently for i in {FL,FR,RL,RR}.
```

All continuous coordinates are mutually independent and independent of
`k,sigma,gamma`, word orientation and action. Within every fit, support, assay,
qualification or training block, `sigma,gamma in {-1,+1}` and the two literal
orientations are exactly balanced; permitted `k` values are exactly balanced.
When a block size is not divisible by the discrete cell count, the remainder is
assigned by one seed-keyed random permutation fixed before materialization.

Checkpoint-fit and fit-support rows use only `K_fit`. Each row draws one of the
81 actions uniformly with block counts differing by at most one, rolls the full
word exactly, and retains truth for the complete word and every legal contiguous
segment under that held action. Each Stage A assay or Stage B target-
qualification base row uses `K_target`, includes both twin orientations, and
enumerates all 81 held actions from the identical boundary state.

Each Stage B post-checkpoint training base row uses `K_fit`, includes both twin
orientations and all 81 legal actions, and retains complete-word, canonical-
segment and true-intermediate-state targets. Thus `ORDER-TR`, `ORDER-Q`,
REVERSED and `FREE-RESIDUAL` receive identical state/word/action support and
useful-call opportunities; no arm receives a target-`k` training row.

An evaluation episode resets once from the same product state law. At each true
boundary its sign pair and literal orientation are drawn independently of the
state from a seed-keyed tape that is exactly balanced within each arm-by-regime
block; all arms share that tape. The chosen action then generates the next
boundary state through the frozen dynamics, so later states are on-policy rather
than redrawn. Fixed and switch regimes determine `k` exactly as specified above.
Failure remains absorbing. No reset, row or tape realization exists in this
definition stage.

### No coordinates exist in this definition stage

This card freezes the DGP, word families, `k` regimes, estimands, branches and
future coordinate law, but binds no realization. A later empirical portfolio
decision must prospectively bind two mutually independent panels and fresh,
blinded, mutually disjoint blocks for:

1. Stage A checkpoint fitting and untouched fit support;
2. Stage A target support and the hard-wired order assay;
3. Stage B fresh checkpoint fitting and untouched fit/target support;
4. Stage B post-checkpoint arm training; and
5. Stage B final fixed/switch-`k` value evaluation.

The Stage A selection panel has exactly ten paired algorithm-seed blocks. Each
seed has 4,096 checkpoint-fit action-word rows, 1,024 untouched fit-support
action-word rows and 256 order-twin boundary base rows per target `k` for target
support and the all-action assay.

The Stage B confirmation panel has exactly ten different paired algorithm-seed
blocks. Each seed has 4,096 fresh checkpoint-fit action-word rows, 1,024 fresh
untouched fit-support action-word rows, 256 fresh checkpoint-qualification twin
base rows per target `k`, 4,096 fresh post-checkpoint all-action twin base rows,
128 final episodes per arm and target regime, and 64 diagnostic episodes per
arm and seen-duration regime. Within a Stage B seed, all arms share its
materialized rows and tapes and clone its one byte-identical base checkpoint.

Only the selected treatment label and this frozen training law transfer from
Stage A to Stage B. No Stage A seed, checkpoint, parameter, optimizer state,
fit/support/assay row, reset coordinate, RNG state or tape may enter Stage B.
Exact identities, coordinates, minibatch tapes and episode tapes do not exist
now. None may be imported from B1, B2 or B3.

## Shared model, containing comparator and path definitions

### One directly supervised segment model

The shared model accepts `(x,u,w,ell)` for any legal contiguous word segment,
where `ell=|w|` is the actual segment duration, and returns

```text
F_theta(x,u,w,ell) -> terminal state prediction,
G_theta(x,u,w,ell) -> cumulative word reward prediction.
```

It uses one 32-dimensional token GRU, a two-layer width-128 state/action trunk,
and separate two-layer width-128 transition and reward heads. Numeric
`ell/12` is visible in addition to the literal segment tokens. A direct complete-
word call has `ell=k`; a recursive segment call has only that segment's actual
length. The model receives no separate full-word `k` during a shorter segment
call and no arm, regime or target-duration indicator. The future CM may change
only implementation-equivalent layout, not the function inputs, outputs or
shared-parameter semantics.

The learned actor scores every legal held joint action by predicted cumulative
word reward `G` only and applies the same lexicographic tie rule as the oracle.
There is no extra terminal potential, transition-derived bonus or arm-specific
score term. Every compared path uses the same action set and scoring code.

For each seed, let `s_F,j=max(sd_fit(F_true,j),1e-6)` and
`s_G=max(sd_fit(G_true),1e-6)`, computed once from that seed's checkpoint-fit
block and then fixed. For any supervised segment target `(F*,G*)`, define

```text
D_theta(x,u,w,ell;F*,G*)
  = 0.5 * [mean_j ((F_theta,j-F*_j)/s_F,j)^2
           + ((G_theta-G*)/s_G)^2].
```

The common direct loss first averages `D_theta` equally over the complete word
and all retained contiguous segments within one action-word row, then averages
rows equally; longer words therefore receive no extra weight merely because
they have more segments. The same formula, scales, row weighting and
orientation/action weighting apply in every arm.

### Independently competent shared checkpoint

For each seed in either panel, one `FREE-DIRECT` base model is trained only on
that panel's fresh `K_fit` checkpoint block with direct truth for complete
words and all legal contiguous segments. Its loss equally weights standardized
terminal-state and cumulative-reward squared errors. No recursive relation,
hard-wired path comparison, target coordinate or target value enters this
checkpoint.

Within Stage A, the checkpoint is frozen and byte-identically shared by the
correct and reversed assay paths. Within each independently generated Stage B
seed, the fresh checkpoint is frozen and byte-identically cloned by all three
post-checkpoint arms. A panel's checkpoint ensemble qualifies only if:

- its untouched `K_fit` composite RMSE is at most `0.65` of a training-target
  mean predictor;
- on that panel's disjoint target support population, its direct full-word composite RMSE
  is at most `0.85` of the same coordinate-local mean predictor and the
  across-seed one-sided 95% upper bound is below `0.95`;
- every predicted physical coordinate has finite positive variance between
  `0.25` and `4.0` times its true variance; and
- at least `90%` of unique-oracle target word-states have predicted legal-action
  score range at least `0.03*k`.

These are new target-bound qualification rules, not inherited thresholds.
Stage A failure modifies the direct checkpoint representation/support only in
a new Pro-closed definition before any order treatment can be selected. Stage B
confirmation-checkpoint failure yields checkpoint nonidentification and cannot
select a seed, reuse Stage A checkpoints, reseed or repair after observation.
Neither is evidence against physical order or the SCDMP family.

### Identical hard-wired correct and reversed paths

For every even `k`, the only legal relation factorization is

```text
h = k/2-1
p_k = C^h S_sigma C^h       with ell_p=k-1
q_k = G_gamma               with ell_q=1
w_F = p_k q_k
w_R = q_k p_k.
```

There is no alternate half-word, before-`S`, before-`G` or data-selected split.
For a presented forward twin, the correct and reversed paths are

```text
F_C,F(x,u) = F_theta(F_theta(x,u,p_k,k-1),u,q_k,1)
G_C,F(x,u) = G_theta(x,u,p_k,k-1)
             + G_theta(F_theta(x,u,p_k,k-1),u,q_k,1)

F_R,F(x,u) = F_theta(F_theta(x,u,q_k,1),u,p_k,k-1)
G_R,F(x,u) = G_theta(x,u,q_k,1)
             + G_theta(F_theta(x,u,q_k,1),u,p_k,k-1).
```

For the presented reverse twin, `C,R` is the literal `q_k`-then-`p_k` path and
`R,R` is the paired `p_k`-then-`q_k` path. Thus

```text
(F_C,R,G_C,R) = (F_R,F,G_R,F)
(F_R,R,G_R,R) = (F_C,F,G_C,F),
```

but each is compared with the true transition, reward and oracle action for
its own presented literal word. `RMSE_C`, `MAE_C` and `regret_C` equal-weight
the literal-correct path over both twin orientations; the `_R` quantities
equal-weight the paired opposite path. Higher `dF,dR,dQ` therefore always means
that literal physical order is better, and presenting the reverse twin cannot
flip an estimand's sign.

The two paths share the exact checkpoint, parameters, segment inputs, two call
shapes, precision, action enumeration and score rule. Only segment order
differs. Their event multiset is identical. No coefficient, optimizer history,
checkpoint, call count or capacity differs.

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
positions. It is chosen optimally on the assay population. The nine registered
physical components are the three per-`k` transition gaps, three per-`k` reward
gaps, the aggregate unique-oracle reversal fraction, its aggregate mean smaller
oracle gap, and aggregate order-aware headroom. Across the ten Stage A seeds,
each component receives a one-sided lower and a separately declared one-sided
upper bound at confidence `1-0.05/9`; exact seed summaries accompany them.

All nine simultaneous lower bounds must exceed their stated margins to qualify
physical opportunity. If any simultaneous upper bound lies below its margin,
the opportunity required by this exact screening object is excluded and the
order treatment is removed from this object's Stage B menu. If neither condition
holds, physical opportunity is nonidentified and no treatment is instantiated.
Neither outcome deletes semigroup learning or an unrun trained package
elsewhere.

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

The exactly ten Stage A paired seeds are the independent inference units. Each
of the three equal-target-`k` aggregate components receives a simultaneous
one-sided lower bound and a separately declared simultaneous one-sided upper
bound at confidence `1-0.05/3`. A successful assay requires every lower bound
to exceed its unscaled denominator margin, equivalently every component lower
bound of `S_order` to exceed `1`. Exact paired sign-randomization results
accompany but do not replace the bounds. No latent metric, checkpoint, split,
word, `k`, component or seed can be selected after data.

### Named learnable treatment and frozen assay branches

The initial named treatment is `ORDER-TR`: from the common checkpoint, continue
direct training while adding literal-correct transition-semigroup and reward-
cocycle consistency for both presented twin orientations. Its matched wrong-
relation control applies the identical loss and graph to the paired opposite
path. All direct and recursive branches are fully differentiable; no target,
branch or path is detached.

For path `Z in {C,R}`, its exact auxiliary is

```text
L_TR,Z = mean_orientation,a 0.5 * [
           mean_j ((F_direct,j-F_Z,j)/s_F,j)^2
           + ((G_direct-G_Z)/s_G)^2 ].
```

`F_direct,G_direct` are the live complete-word outputs at `ell=k`; `F_Z,G_Z`
are the live two-call composed outputs above. The mean covers both literal twin
orientations and all 81 actions on each Stage B training base row.

The predeclared modification is `ORDER-Q`: retain the same direct model and
paths, but replace the transition/reward consistency penalty by an action-score
consistency loss across all 81 held actions,

```text
L_Q,C = mean_orientation,a ((Score_direct(x,a,w_orientation,k)
                             - Score_C(x,a,w_orientation))/s_G)^2,
L_Q,R = mean_orientation,a ((Score_direct(x,a,w_orientation,k)
                             - Score_R(x,a,w_orientation))/s_G)^2.
```

The direct and composed scores in both `ORDER-Q` losses are fully
differentiable through the same live model; there is no stop-gradient, teacher,
target network or asymmetric gradient path. CORRECT and REVERSED differ only
in the frozen literal-correct versus paired-opposite composition above.

The branch order is:

1. **DELETE-FROM-OBJECT--PHYSICAL-OPPORTUNITY-EXCLUDED:** any registered
   physical/action/value upper bound is below its margin. Remove `ORDER-TR` and
   `ORDER-Q` from this object's Stage B menu. This is exact screen exclusion,
   not trained-treatment or family futility.
2. **PHYSICAL-OPPORTUNITY-INDETERMINATE:** no physical upper bound excludes a
   margin, but not all physical lower bounds pass. Instantiate no treatment and
   make no physical absence claim.
3. **MODIFY-CHECKPOINT:** all physical lower bounds pass but the Stage A shared-
   checkpoint competence panel fails. Redefine checkpoint support or
   representation in a new Pro-closed revision; do not interpret order or
   proceed to value.
4. **ASSAY-ACTION-ADVERSE--DELETE-FROM-OBJECT:** physical and competence gates
   pass but the simultaneous upper bound of `dQ` is below `-0.05`. Remove
   `ORDER-TR` and `ORDER-Q` from this object's Stage B menu before any positive
   or modification branch. This says only that the shared-checkpoint correct
   path is action-adverse under the registered screen.
5. **SELECT-ORDER-TR:** all three `S_order` component lower bounds pass. Transfer
   only the frozen label `ORDER-TR` to the independent Stage B panel.
6. **MODIFY-TO-ORDER-Q:** after the adverse branch is excluded, the `dF` and
   `dR` lower bounds pass their margins while the simultaneous upper bound of
   `dQ` is below `0.05`. Transfer only the already defined label `ORDER-Q` to
   the independent Stage B panel.
7. **ASSAY-NEGATIVE--DELETE-FROM-OBJECT:** with every qualification passed,
   either the simultaneous upper bound of `dF` or `dR` is below `0.05`. Remove
   `ORDER-TR` from this object's Stage B menu. The checkpoint did not expose
   the registered minimum relation-direction separation; the unrun 800-update
   package is not scientifically deleted.
8. **ASSAY-INDETERMINATE:** every other complete outcome. No threshold, seed,
   split, checkpoint or treatment changes automatically.

Exclusion and adverse branches precede selection, and the `dQ` adverse branch
explicitly precedes `ORDER-Q`. Branches 5 and 6 are disjoint because
`LB(dQ)>0.10` and `UB(dQ)<0.05` cannot both hold. The Stage A packet is atomic:
all target `k`, all three components, qualifications and confidence bounds must
exist. Partial component selection is forbidden. Stage A can remove a treatment
from this exact object's menu, but only Stage B can support scientific deletion
of a trained treatment.

## Stage B: selected-treatment external-`k` value object

After Stage A transfers exactly one treatment label, Stage B uses its independent
ten-seed confirmation panel and new disjoint checkpoint-fit, support, training
and evaluation coordinates. Each Stage B seed first trains a fresh base
checkpoint for 600 updates under the identical frozen checkpoint law. No Stage
A parameter, optimizer state or random identity enters. Within that seed,
every arm then clones the byte-identical qualified fresh checkpoint and receives
the same full-word and segment rows, direct loss, update count, minibatch order,
optimizer, clipping, action scorer and legal actions.

If the complete Stage B checkpoint ensemble fails its frozen competence panel,
the result is `STAGE-B-CHECKPOINT-NONIDENTIFICATION`; no post-checkpoint arm is
instantiated, no Stage A checkpoint is substituted and no seed is repaired or
replaced. If it qualifies, every arm receives exactly 800 post-checkpoint
updates with batches of 256 complete-word rows, AdamW learning rate `3e-4`,
`beta=(0.9,0.999)`, `eps=1e-8`, weight decay `1e-5`, and global gradient-norm
clip `1.0`. There is exactly one final checkpoint after update 800 and no early
stopping, checkpoint sweep, second budget or budget search.

The three arms are:

1. `FREE-DIRECT`, continuing only direct full-word and segment supervision;
2. the assay-selected `ORDER-TR-CORRECT` or `ORDER-Q-CORRECT`; and
3. its exactly matched `ORDER-TR-REVERSED` or `ORDER-Q-REVERSED` control.

The relation arms add the selected fully differentiable auxiliary on the same
rows. To match useful calls without a recursive constraint, `FREE-DIRECT` adds
the frozen

```text
L_FREE = mean_orientation,a 0.5 * [
           D_theta(x,a,first,|first|;x_mid*,G_first*)
           + D_theta(x_mid*,a,second,|second|;x_terminal*,G_second*) ].
```

Here `first,second` follow the presented literal orientation and `x_mid*` is
the true deterministic intermediate state. `L_FREE` is output-connected, uses
the same two segment-call shapes and all 81 actions, and supplies stronger
direct supervision rather than a relation. The fixed `s_F,s_G` scales, direct,
relation and residual components all use the exact formulas above.
The direct loss has coefficient `1`, and the selected relation or matched
FREE-residual loss has one common coefficient `1` in every arm for all 800
updates. There is no calibration or adaptive scale. No later gradient,
checkpoint, target score or result may tune, stop, amplify or select an arm.
The causal estimand is the total finite-budget algorithm-package contrast; it
is not a common-optimizer-trajectory or unique-mediation effect.

### Direct variable-`k` endpoints

For target regime `r`, arm `M` and Stage B paired seed `s`, record:

```text
J_M,s(r) = episode reward per primitive step,
P_M,s(r) = payload/formation failure probability,
H_s(r)   = J_true_order_oracle,s(r) - J_best_order_blind,s(r).
```

Every target-regime `H_s(r)` must exceed `0.08`; otherwise that regime is not
value-qualified.
For control `X in {FREE,REVERSED}` define seed-level target averages, weighting
the five target regimes equally,

```text
V_J,s(C,X) = mean_r [(J_C,s(r)-J_X,s(r))/H_s(r)],
V_P,s(C,X) = mean_r [P_X,s(r)-P_C,s(r)].
```

`V_J(C,X)` and `V_P(C,X)` denote the across-seed means of those ten independent
seed-level values; every t bound is computed from the seed-level vector.

Seen-duration fixed `4` and `10` produce only per-regime non-harm checks. Their
return improvement is the raw arm-minus-control reward per primitive step; the
target-regime return improvement is normalized by `H_s(r)` as above. The update
budget and paired-seed count are frozen above; only the fresh random identities
and materialized coordinates await a later empirical authorization.

The four aggregate target benefit contrasts form one indivisible family:

```text
B = {V_J(C,FREE), V_J(C,REVERSED),
     V_P(C,FREE), V_P(C,REVERSED)}.
```

Every lower bound used by either positive route is a paired-seed one-sided
Student-t bound with `df=9` and confidence `1-0.05/4=0.9875`. Thus return and
failure are two readings of one simultaneous benefit family, not two
independent full-alpha opportunities. A separate four-member futility family
uses one-sided upper bounds at the same `0.9875` confidence for containing-FREE
and exact-treatment-deletion branches.

Define 28 per-regime improvement contrasts: normalized return and failure
improvement for two controls in each of five target regimes, plus raw return and
failure improvement for two controls in each of two seen regimes. One separate
non-harm family gives every member a one-sided lower bound at confidence
`1-0.05/28`. One separate adverse family gives every member a one-sided upper
bound at the same confidence. Adverse absence never supplies non-harm. Exact
paired sign-randomization results accompany but never replace any bound.

The smallest useful aggregate target effects are `0.10` of oracle-over-order-
blind return headroom and `0.05` absolute failure probability. The per-regime
harm margins are `-0.04` for target-normalized or seen raw return improvement
and `-0.03` for failure-probability improvement.

### Frozen Stage B interpretation

Interpret one complete atomic packet in this order:

1. **STAGE-B-CHECKPOINT-NONIDENTIFICATION:** the independent confirmation base-
   checkpoint panel fails a required competence or completion condition. No arm
   treatment is interpreted and no replacement is authorized.
2. **ADVERSE:** for either control or any target/seen regime, a member of the
   simultaneous adverse family has an upper bound below the registered return
   or failure harm margin. Reject only the exact selected package on this task
   and budget.
3. **VARIABLE-K RETURN VALUE:** both benefit-family lower bounds for `V_J`
   exceed `0.10` and all 28 simultaneous non-harm lower bounds pass.
4. **VARIABLE-K FAILURE ROBUSTNESS:** both benefit-family lower bounds for
   `V_P` exceed `0.05` and all 28 simultaneous non-harm lower bounds pass.
5. **CONTAINING-FREE SUFFICIENT:** all non-harm bounds pass; at least one
   benefit route qualifies against REVERSED under the same four-member benefit
   family; neither benefit route qualifies against `FREE-DIRECT`; and the
   futility-family upper bounds of both aggregate value effects versus FREE are
   below their useful margins. Delete the selected recursive auxiliary for
   this target at the frozen budget; direct ordered modeling is sufficient.
6. **EXACT-TREATMENT DELETION:** with all qualifications and the complete
   non-harm family passed, all four futility-family upper bounds are below their
   useful margins. Delete only the exact trained selected treatment/package.
7. **VALID INDETERMINATE:** every other complete result. No seed, budget,
   coefficient, threshold, `k`, surface or treatment change follows.

Return-value and failure-robustness branches are alternatives within the one
four-member simultaneous benefit family: either may establish project-relevant
variable-`k` value without opening a second full-alpha route. No representation-
only or latent-separation branch exists in Stage B.

## Scientific activity and immutability boundaries

The current definition stage contains no scientific activity. Reading,
authoring, Pro/Gemini consultation and CM static feasibility/cost review do not
instantiate a task coordinate or treatment.

If empirical work is later authorized:

- Stage A scientific activity begins immediately before the first gradient
  update used to create the first Stage A selection checkpoint. From that
  moment all ten Stage A seed identities, coordinate blocks, architecture,
  training rule, inference families and assay branches are immutable.
- Stage B scientific activity begins immediately before the first gradient
  update used to create the first fresh Stage B confirmation checkpoint. From
  that moment all ten different Stage B seed identities, the transferred
  treatment label, controls, checkpoint law, data, coefficients, budget,
  endpoints and branch law are immutable.
- Stage A and Stage B are separate atomic packets. No coordinate, seed,
  checkpoint, parameter, optimizer/RNG state or tape may be reused across
  panels. Stage B cannot start unless one legal Stage A branch prospectively
  selects or modifies exactly one treatment label.

No result can choose a panel, checkpoint, split, persistence window, seed,
coefficient, budget, target duration, endpoint, margin or partial packet. Any
science-bearing change requires a new complete EM revision and same-conversation
Pro closure.

## Strongest alternative and claim ceiling

The strongest alternative even after a positive result is target-adapted
finite-budget optimization and supervision geometry. Stage A uses target-
specific assay evidence to choose one of two auxiliary forms; Stage B tests
that frozen label on independent checkpoints, but `FREE-DIRECT` is more
flexible and sees direct segment truth while the selected auxiliary changes
curvature, gradient alignment, clipping and optimizer history. `ORDER-TR` may
act as generic multi-path prediction regularization and `ORDER-Q` as generic
all-action ranking regularization. A correct package can win without semigroup
or reward-cocycle structure being uniquely necessary. Conversely, FREE can
learn the ordered mapping directly from visible word positions, making explicit
composition redundant.

The shared-checkpoint assay isolates hard-wired direction from arm-specific
training history, and the independent confirmation panel prevents selection on
the same checkpoint randomness used for value inference. Neither proves that a
later training gain is uniquely mediated by algebra. The deterministic, fully
observed word also excludes unknown-event adaptation and partial observability.

The maximum positive Stage B claim is:

> On this exact deterministic four-carrier payload/formation task, a treatment
> form selected by a ten-seed hard-wired order assay transferred to a separate
> ten-seed confirmation panel, where one shared finite-budget model/policy
> trained at `k={4,10}` and used unchanged at fixed `k={6,8,12}` and switches
> `6<->12` achieved the registered simultaneous-family return or failure-
> robustness improvement over both a containing direct learner and a matched
> reversed-order package, conditional on the frozen physical, competence,
> wrong-relation, headroom and non-harm qualifications.

It is an exact-task finite-budget inductive-bias claim. It is not arbitrary-
`k`, variable-`N`, unique semigroup mediation, equal-optimizer-trajectory,
stochastic or partially observed robustness, general payload robotics, another
surface, UAV, safety or real-flight evidence. Stage A alone supports no direct
task-value claim.

## Definition-stage completion and authority boundary

This revision is complete for same-conversation Pro mathematical/causal closure
and, after closure plus EM intake, static CM feasibility/cost review. Gemini may
propose alternatives but cannot close or select it. CM may assess whether the
DGP, observations, comparator, path construction, independent-panel law,
branch observables and prospective costs are statically bindable; CM may not
construct, test or probe them in this stage.

No source change, environment creation, coordinate realization, checkpoint,
training, evaluation, compute lease, empirical selection, fusion, second
surface or UAV action is authorized. A later empirical step requires a new
dedicated portfolio decision and Operational Root envelope.
