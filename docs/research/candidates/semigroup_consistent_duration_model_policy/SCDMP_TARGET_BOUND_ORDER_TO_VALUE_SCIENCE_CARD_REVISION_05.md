# SCDMP target-bound order-to-value definition science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-TARGET-BOUND-ORDER-TO-VALUE
revision=SCDMP-TBOV-SCIENCE-20260815-05
supersedes_revision=SCDMP-TBOV-SCIENCE-20260815-04_PRO_REVISION_REQUIRED
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

For a boundary state, `k` and sign pair, the registered order-blind oracle sees
the state, `k`, signs and event counts but not the presented orientation. It
rolls each held action on both `w_F` and `w_R`, chooses the action maximizing the
equal `0.5/0.5` mean of their two true word rewards, and breaks ties
lexicographically. The order-aware oracle instead chooses separately for the
presented literal word. These are exact analytic finite-action rules, not fitted
policies or post-data function classes.

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

One shared parameterization is prospectively fit from complete-word/true-
boundary rows whose external durations are only

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
useful-call opportunities. No complete target word, target true-boundary
decision row, target episode or target final-value coordinate enters any
optimizer or scaler population. Equivalently, no complete-word or true-boundary
training row has external `k in K_target`.

This is not wholesale unseen-numeric-duration training. The registered
contiguous-segment atoms of a `k=10` fit row include numeric segment inputs
`ell=6` and `ell=8`; its literal factor `p_10=C^4 S_sigma C^4` also contains
`p_6=C^2 S_sigma C^2` and `p_8=C^3 S_sigma C^3` as directly supervised
contiguous segments, while `q_k=G_gamma` is a supervised length-one segment.
For target `k=12`, numeric `ell=12` and the long factor length `11` remain
outside the fit segment-length support. The frozen generalization question is
therefore held-out complete-word recombination and action selection at held-out
true-boundary fixed/switch regimes, plus length extrapolation at `k=12`; it is
not unseen numeric-duration or wholly unseen-factor transfer at `k=6,8`.

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
64 arm-independent headroom-qualification episodes per target regime, 128 final
episodes per arm and target regime, and 64 diagnostic episodes per arm and
seen-duration regime. Within a Stage B seed, all arms share its materialized
rows and tapes and clone its one byte-identical base checkpoint.

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

The final deployed Stage B actor of every arm uses only its own direct complete-
word reward output. For every
`M in {FREE-DIRECT,CORRECT,REVERSED}`, freeze

```text
DEPLOY_SCORE_M(x,w,u) = G_theta_M(x,u,w,|w|)
DEPLOY_ACTION_M(x,w)  = lexargmax_{u in {-1,0,+1}^4}
                        DEPLOY_SCORE_M(x,w,u).
```

All three deployed actors therefore enumerate the same 81 actions through the
same one-call direct-score architecture, with the oracle's lexicographic tie
rule. There is no extra terminal potential, transition-derived bonus or arm-
specific score term. `F_C,G_C,F_R,G_R` are used only in the Stage A hard-wired
assay and the selected Stage B `ORDER-TR` or `ORDER-Q` auxiliary; a deployed
Stage B actor never calls a correct or reversed recursive path. Relation
direction is a training-package treatment, not an inference-path treatment.

For each panel and seed, number its `N=4096` checkpoint-fit action-word rows in
their seed-keyed materialization order. For row `r` of length `k_r`, the exact
ordered scale-atom list is

```text
T_r = [(a,ell): a=0,...,k_r-1; ell=1,...,k_r-a]
```

in increasing `(a,ell)` order. It contains every nonempty contiguous segment,
including the complete word `(0,k_r)` exactly once. A segment starting at
`a>0` uses the true deterministic state after the preceding `a` events as its
input; its atoms are the nine absolute terminal-state coordinates and its
undiscounted cumulative segment reward.

Every row has weight `1/N`, and every atom within row `r` has weight
`1/|T_r|`. Thus fit durations and rows retain their exact balanced row weight,
and a longer word receives no extra scale weight because it has more segments.
For each terminal coordinate `j` and for reward, compute the weighted population
mean and variance

```text
mu_Y  = sum_r sum_t [Y_r,t / (N |T_r|)]
var_Y = sum_r sum_t [(Y_r,t-mu_Y)^2 / (N |T_r|)]
s_Y   = max(sqrt(var_Y), 1e-6).
```

Use IEEE float64 two-pass accumulation in ascending row then `(a,ell)` order,
with population denominator one (not `n-1`); apply the floor after the float64
square root, then cast each final `s_F,j,s_G` once to IEEE float32. Truth is
generated in float64 and cast once to float32 at loss input. Model parameters,
forward/backward arithmetic, gradient clipping, AdamW moments and updates are
IEEE float32. The constants are computed before the first checkpoint update,
are shared unchanged by that seed's checkpoint and, in Stage B, all three arms,
and never use fit-support, target-support, assay, headroom or evaluation atoms.

For any supervised segment target `(F*,G*)`, define

```text
D_theta(x,u,w,ell;F*,G*)
  = 0.5 * [mean_j ((F_theta,j-F*_j)/s_F,j)^2
           + ((G_theta-G*)/s_G)^2].
```

The common direct loss uses the same `T_r` list: it first averages `D_theta`
equally over `T_r`, then averages rows equally. Longer words therefore receive
no extra objective weight merely because they have more segments. The same
formula, scales, deterministic reduction order, row weighting and
orientation/action weighting apply in every arm.

### Independently competent shared checkpoint

For each seed in either panel, one `FREE-DIRECT` base model is trained only on
that panel's fresh external-`K_fit` checkpoint block with direct truth for the
complete fit words and all their legal contiguous segments. Its loss equally weights standardized
terminal-state and cumulative-reward squared errors. No recursive relation,
hard-wired path comparison, target coordinate or target value enters this
checkpoint.

Within Stage A, the checkpoint is frozen and byte-identically shared by the
correct and reversed assay paths. Within each independently generated Stage B
seed, the fresh checkpoint is frozen and byte-identically cloned by all three
post-checkpoint arms. A panel's checkpoint ensemble qualifies only if:

- for full-word predictions define
  `E=sqrt(0.5*[mean_j MSE(F_j)/s_F,j^2 + MSE(G)/s_G^2])`, with rows,
  orientations and actions equal-weighted. The mean comparator predicts the
  checkpoint-fit full-word population means computed by equal row weight in
  the same fixed float64 order;
- for every seed, the ratio `E_model/E_mean` on untouched `K_fit` support is at
  most `0.65`;
- on that panel's disjoint target-support full words, the across-seed mean of
  the ten ratios is at most `0.85` and its one-sided 95% upper t bound is below
  `0.95`;
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

For fixed state-envelope widths

```text
a_state=(0.50,0.30,0.40,0.24,0.80,0.40,0.40,0.40,0.40),
D_state(x1,x2)=sqrt(mean_j((x1_j-x2_j)/a_state_j)^2),
```

define exactly three seed-level physical estimands for every
`s` and `k in {6,8,12}` on that seed's 256 assay base rows `b` and all 81
actions `a`:

```text
T_s,k = median_b,a D_state(x*_F(b,a),x*_R(b,a))

R_s,k = median_b,a |G*_F(b,a)-G*_R(b,a)| / k.
```

For the action component, let `a*_F,a*_R` be the separate order-aware oracle
actions and `gap_F,gap_R` their best-minus-second-best true word-reward gaps.
A base row is action-eligible only when both gaps exceed `0.02*k`. Define

```text
f_s,k = fraction of eligible rows with a*_F != a*_R,
g_s,k = mean over those reversal rows min(gap_F,gap_R)/k,
h_s,k = mean_b {0.5[G*_F(b,a*_F)+G*_R(b,a*_R)]
                -0.5[G*_F(b,a*_B)+G*_R(b,a*_B)]}/k,
A_s,k = min(f_s,k/0.30, g_s,k/0.04, h_s,k/0.08),
```

where `a*_B` is the exact registered order-blind oracle. If there is no
eligible row, set `f_s,k=0`; if there is no reversal row, set `g_s,k=0`.
`h_s,k` is always computed on all 256 rows. Thus the physical family is
literally

```text
PHYS={T_s,k, R_s,k, A_s,k : k in {6,8,12}},   |PHYS|=9,
margins={0.12, 0.06, 1.0} per k.
```

Across the ten Stage A seeds, every member receives a one-sided lower and a
separately declared one-sided upper t bound at confidence `1-0.05/9`. All nine
lower bounds must exceed their margins to qualify physical opportunity. If any
upper bound lies below its margin, the opportunity required by this exact
screening object is excluded and the order treatment is removed from this
object's Stage B menu. If neither condition holds, physical opportunity is
nonidentified. Neither outcome deletes an unrun trained package elsewhere.

### Sole primary wrong-relation separation endpoint

On every assay base row, orientation and legal action, compare the hard-wired
path with the true complete-word outcome. For `Z in {C,R}` define within seed
and target duration

```text
RMSE_Z,s,k = sqrt(mean_b,a,o,j
                  ((F_Z,s,k(b,a,o)-x*_s,k(b,a,o))/a_state_j)^2)

MAE_Z,s,k  = mean_b,a,o |G_Z,s,k(b,a,o)-G*_s,k(b,a,o)|/k

REG_Z,s,k  = mean_b,o [G*_s,k(b,a*_o,o)-G*_s,k(b,a_Z,o)]/k,
```

where orientation `o` is equal-weighted, `a*_o` is its true order-aware oracle
action, and `a_Z` maximizes that path's predicted `G` over the 81 actions with
the frozen lexicographic tie rule. Reductions occur in the printed order using
float64 evaluation values and equal weights; `RMSE` takes one square root only
after the joint mean over rows, actions, orientations and state coordinates.

Require every `T_s,k,R_s,k,h_s,k` to be finite and strictly positive. Then

```text
dF_s,k = (RMSE_R,s,k-RMSE_C,s,k)/T_s,k
dR_s,k = (MAE_R,s,k-MAE_C,s,k)/R_s,k
dQ_s,k = (REG_R,s,k-REG_C,s,k)/h_s,k

dF_s = (dF_s,6+dF_s,8+dF_s,12)/3
dR_s = (dR_s,6+dR_s,8+dR_s,12)/3
dQ_s = (dQ_s,6+dQ_s,8+dQ_s,12)/3
S_order,s = min(dF_s/0.20,dR_s/0.20,dQ_s/0.10).
```

This is intentionally a pooled, equal-target-duration three-component assay;
per-`k` components are mandatory diagnostics but are not separate selection
gates. The exactly ten Stage A seeds are the independent inference units. Each
of `{dF_s,dR_s,dQ_s}` receives a simultaneous one-sided lower and a separately
declared upper t bound at confidence `1-0.05/3`. A successful assay requires
the three lower bounds to exceed `0.20,0.20,0.10`, respectively. Exact paired
sign-randomization accompanies but does not replace the bounds. No alternate
rowwise ratio, atom weighting, `k` pooling, error norm, checkpoint, split,
component or seed may be selected after data.

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

Let `L_PHYS_i,U_PHYS_i` be the nine physical-family bounds and `m_i` their
printed margins; let `L_F,L_R,L_Q,U_F,U_R,U_Q` be the three-component assay
bounds; and let `COMP_A` mean that every Stage A checkpoint competence gate is
complete and passed. Freeze the literal predicates

```text
PHYS_EXCLUDED = any_i(U_PHYS_i < m_i)
PHYS_PASSED   = all_i(L_PHYS_i > m_i)
ASSAY_DENOM_OK = all_{s,k} [finite(T_s,k) AND finite(R_s,k)
                            AND finite(h_s,k)
                            AND T_s,k>0 AND R_s,k>0 AND h_s,k>0]
ACTION_ADVERSE = (U_Q < -0.05)
SELECT_TR      = (L_F > 0.20) AND (L_R > 0.20) AND (L_Q > 0.10)
SELECT_Q       = (NOT ACTION_ADVERSE) AND
                 (L_F > 0.20) AND (L_R > 0.20) AND (U_Q < 0.05)
ASSAY_NEGATIVE = (U_F < 0.05) OR (U_R < 0.05).
```

Apply exactly this first-true branch order:

1. **DELETE-FROM-OBJECT--PHYSICAL-OPPORTUNITY-EXCLUDED** if
   `PHYS_EXCLUDED`. Remove both labels from this object's menu; make no trained-
   treatment or family futility claim.
2. **PHYSICAL-OPPORTUNITY-INDETERMINATE** if not `PHYS_PASSED`. Instantiate no
   treatment and make no physical absence claim.
3. **STAGE-A-ASSAY-DENOMINATOR-NONIDENTIFICATION** if not `ASSAY_DENOM_OK`.
   Instantiate no Stage B treatment and make no physical-futility, assay-
   negative or trained-treatment claim. No floor, absolute value, pooled
   denominator, seed removal or replacement is legal.
4. **MODIFY-CHECKPOINT** if not `COMP_A`. Redefine support/representation only
   in a new Pro-closed revision; do not interpret order or proceed to value.
5. **ASSAY-ACTION-ADVERSE--DELETE-FROM-OBJECT** if `ACTION_ADVERSE`. Remove both
   labels from this object's menu; report only shared-checkpoint action adversity.
6. **SELECT-ORDER-TR** if `SELECT_TR`. Transfer only label `ORDER-TR`.
7. **MODIFY-TO-ORDER-Q** if `SELECT_Q`. Transfer only label `ORDER-Q`.
8. **ASSAY-NEGATIVE--DELETE-FROM-OBJECT** if `ASSAY_NEGATIVE`. Remove
   `ORDER-TR` eligibility from this object and make no claim about the unrun
   800-update package.
9. **ASSAY-INDETERMINATE** otherwise. No threshold, seed, split, checkpoint or
   treatment changes automatically.

Physical qualification and per-seed denominator validity precede every
checkpoint-assay interpretation. Exclusion and adverse branches precede
selection, and the `dQ` adverse branch explicitly precedes `ORDER-Q`. The two
selection branches are disjoint because
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
replaced.

If checkpoints qualify, compute the arm-independent target headroom registry
before any arm update. For each Stage B seed `s` and target regime
`r in {6,8,12,6->12,12->6}`, use its 64 disjoint headroom-qualification reset
and exogenous event tapes. Run the true order-aware and registered order-blind
oracles on paired copies of each tape; each oracle evolves its own on-policy
state, and switch regimes change `k` at primitive step 180. Define

```text
H_s,r = mean_64 [J_order-aware,s,r - J_order-blind,s,r],
```

where each `J` is total 360-step reward divided by 360. Every one of the 50
`H_s,r` values must be finite and strictly greater than `0.08`. Otherwise the
result is `STAGE-B-TARGET-HEADROOM-NONIDENTIFICATION`; no arm is instantiated,
no regime or seed is removed, and no zero floor, absolute value, Stage A
headroom or substitute denominator is legal. The qualification tapes are never
used for arm training or final evaluation.

If both checkpoint and headroom registries qualify, every arm receives exactly
800 post-checkpoint updates with batches of 256 complete-word base rows, AdamW
learning rate `3e-4`, `beta=(0.9,0.999)`, `eps=1e-8`, weight decay `1e-5`, and
global gradient-norm clip `1.0`. There is exactly one final checkpoint after
update 800 and no early stopping, checkpoint sweep, second budget or budget
search.

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
H_s,r    = the frozen arm-independent qualification denominator above.
```

Every target-regime denominator is the already frozen arm-independent
qualification value `H_s,r` above; final arm episodes never redefine it.
For control `X in {FREE,REVERSED}` define seed-level target averages, weighting
the five target regimes equally,

```text
V_J,s(C,X) = mean_r [(J_C,s(r)-J_X,s(r))/H_s,r],
V_P,s(C,X) = mean_r [P_X,s(r)-P_C,s(r)].
```

`V_J(C,X)` and `V_P(C,X)` denote the across-seed means of those ten independent
seed-level values; every t bound is computed from the seed-level vector.

Seen-duration fixed `4` and `10` produce only per-regime non-harm checks. Their
return improvement is the raw arm-minus-control reward per primitive step; the
target-regime return improvement is normalized by `H_s,r` as above. The update
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

Define target-regime improvements

```text
DeltaJ_s,r(C,X)=(J_C,s(r)-J_X,s(r))/H_s,r
DeltaP_s,r(C,X)=P_X,s(r)-P_C,s(r),
```

and seen-regime improvements with raw `J_C,s(r)-J_X,s(r)` plus the same
`DeltaP`. These are the 28 per-regime contrasts: two endpoints by two controls
in each of five target and two seen regimes. One separate
non-harm family gives every member a one-sided lower bound at confidence
`1-0.05/28`. One separate adverse family gives every member a one-sided upper
bound at the same confidence. Adverse absence never supplies non-harm. Exact
paired sign-randomization results accompany but never replace any bound.

The smallest useful aggregate target effects are `0.10` of oracle-over-order-
blind return headroom and `0.05` absolute failure probability. The per-regime
harm margins are `-0.04` for target-normalized or seen raw return improvement
and `-0.03` for failure-probability improvement.

### Frozen Stage B interpretation

Let `LJ_F,LJ_R,LP_F,LP_R` be the four benefit-family lower bounds for return
and failure versus FREE and REVERSED; let `UJ_F,UJ_R,UP_F,UP_R` be the
corresponding futility-family upper bounds. Let `h_i` be each registered
per-regime harm margin and define

```text
FULL_NONHARM = all_i(L_NONHARM_i > h_i)
ADVERSE      = any_i(U_ADVERSE_i < h_i)

RETURN_VALUE = FULL_NONHARM AND (LJ_F>0.10) AND (LJ_R>0.10)
FAILURE_VALUE= FULL_NONHARM AND (LP_F>0.05) AND (LP_R>0.05)

FREE_SUFFICIENT = FULL_NONHARM
                  AND ((LJ_R>0.10) OR (LP_R>0.05))
                  AND (UJ_F<0.10) AND (UP_F<0.05)

EXACT_DELETE = FULL_NONHARM
               AND (UJ_F<0.10) AND (UJ_R<0.10)
               AND (UP_F<0.05) AND (UP_R<0.05).
```

Apply exactly this first-true branch order:

1. **STAGE-B-CHECKPOINT-NONIDENTIFICATION** if the independent confirmation
   checkpoint registry is incomplete or fails. No arm interpretation or
   replacement is authorized.
2. **STAGE-B-TARGET-HEADROOM-NONIDENTIFICATION** if any of the 50 frozen
   `H_s,r` values is nonfinite or at most `0.08`. No arm interpretation or
   denominator substitution is authorized.
3. **ADVERSE** if `ADVERSE`. Reject only the exact selected package on this task
   and budget; adverse absence does not imply non-harm.
4. **VARIABLE-K RETURN VALUE** if `RETURN_VALUE`.
5. **VARIABLE-K FAILURE ROBUSTNESS** if `FAILURE_VALUE`. If both positive
   predicates pass, return value is controlling by precedence and failure value
   is reported only as an additional satisfied modifier.
6. **CONTAINING-FREE SUFFICIENT** if `FREE_SUFFICIENT`. Correct order has a
   useful aggregate endpoint effect over REVERSED, all non-harm checks pass,
   and useful incremental return and failure superiority over the containing
   FREE learner are both excluded. Delete the selected recursive auxiliary for
   this exact target and budget; make no general direct-model sufficiency claim.
7. **EXACT-TREATMENT DELETION** if `EXACT_DELETE`. Delete only the exact trained
   selected treatment/package.
8. **VALID INDETERMINATE** otherwise. No seed, budget, coefficient, threshold,
   `k`, surface or treatment change follows.

Return-value and failure-robustness branches are alternatives within the one
four-member simultaneous benefit family: either may establish project-relevant
variable-`k` value without opening a second full-alpha route. No representation-
only or latent-separation branch exists in Stage B.

## Scientific activity and immutability boundaries

The current definition stage contains no scientific activity. Reading,
authoring, Pro/Gemini consultation and CM static feasibility/cost review do not
instantiate a task coordinate or treatment.

If empirical work is later authorized:

- Stage A scientific activity begins immediately before the first Stage A seed
  identity is drawn, coordinate is materialized or scale atom is evaluated,
  whichever occurs first. From that moment all ten Stage A seed identities,
  coordinate blocks, scalers, architecture, training rule, inference families
  and assay branches are immutable.
- Stage B scientific activity begins immediately before the first Stage B seed
  identity is drawn, coordinate is materialized or scale/headroom atom is
  evaluated, whichever occurs first. From that moment all ten different Stage
  B seed identities, the transferred treatment label, controls, checkpoint law,
  scalers, headroom registry, data, coefficients, budget, endpoints and branch
  law are immutable.
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
composition redundant. In addition, numeric segment durations `6` and `8` and
the exact `p_6,p_8` factors are already supervised inside `k=10` fit words, so a
gain at external `k=6,8` may reflect recombination of optimization-visible
pieces rather than unseen-duration extrapolation.

The shared-checkpoint assay isolates hard-wired direction from arm-specific
training history, and the independent confirmation panel prevents selection on
the same checkpoint randomness used for value inference. Neither proves that a
later training gain is uniquely mediated by algebra. The deterministic, fully
observed word also excludes unknown-event adaptation and partial observability.

The maximum positive Stage B claim is:

> On this exact deterministic four-carrier payload/formation task, a treatment
> form selected by a ten-seed hard-wired order assay transferred to a separate
> ten-seed confirmation panel, where one shared finite-budget model/policy
> optimized only on complete-word and true-boundary rows at external
> `k={4,10}` and used unchanged at fixed `k={6,8,12}` and switches
> `6<->12` achieved the registered simultaneous-family return or failure-
> robustness improvement over both a containing direct learner and a matched
> reversed-order package, conditional on the frozen physical, competence,
> wrong-relation, headroom and non-harm qualifications.

It is an exact-task finite-budget, held-out-complete-word and held-out-true-
boundary-regime inductive-bias claim. Because segment inputs `ell=6,8` and
factors `p_6,p_8` are optimization-visible, it is not unseen-numeric-duration
or wholly unseen-factor generalization at those two targets; only `k=12`
includes the registered length extrapolation. It is not arbitrary-`k`,
variable-`N`, unique semigroup mediation, equal-optimizer-trajectory,
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
