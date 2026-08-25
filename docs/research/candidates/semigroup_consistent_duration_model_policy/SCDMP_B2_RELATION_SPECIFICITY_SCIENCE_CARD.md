# SCDMP B2 competence-first relation-specificity science card

```text
direction=semigroup_consistent_duration_model_policy
candidate=SCDMP-B2-RELATION-SPECIFICITY
revision=SCDMP-B2-SCIENCE-20260813-02
supersedes_revision=SCDMP-B2-SCIENCE-20260813-01_PRO_REVISION_REQUIRED
owner=EM_semigroup_consistent_duration_model_policy
predecessor=SCDMP-B1-SCIENCE-20260812-05
predecessor_result_is_evidence_for_b2=false
artifact_status=FROZEN_OWNER_COMPOSITE_PRE_PRO
scientific_activity_started=false
chatgpt_external_pro_math_closure=required_in_existing_scdmp_conversation
external_gemini=PREPARED_NOT_SENT
cm_construction_authorized=false
tests_authorized=false
compute_authorized=false
production_authorized=false
second_surface_authorized=false
uav_authorized=false
```

## Decision and single family-eliminating question

This prospective object is meaning-complete and worth external mathematical
closure as the one remaining high-information SCDMP discriminator. Conditional
static CM review says it is constructable in the existing one-CPU resource
class. It asks only:

> Once every arm is independently prediction-competent, does the direction of
> the mathematically correct nonautonomous semigroup/reward-cocycle auxiliary
> produce an order-specific improvement in correct-relation error, true target
> prediction, and oracle-action regret over both a stronger composition-free
> directly supervised model and a deliberately wrong order-reversed relation,
> when auxiliary gradient magnitude and useful model work are prospectively
> matched?

The answer can retain or eliminate this exact relation-specific learning route
before another task-value experiment. B2 itself cannot establish task-return or
failure-robustness value. It never reuses a B1 result, effect, threshold, seed,
tape, checkpoint or empirical calibration. B1 only motivates the question and
supplies a controlled host/architecture definition.

Revision 01 was frozen and published but never constructed or made
scientifically active. Its same-conversation ChatGPT External Pro ruling was
`REVISION_REQUIRED`. Revision 02 preserves every DGP, arm, information path,
objective, gradient law, seed, tape, competence/activity/support/headroom gate,
primary contrast and margin, adverse/non-harm family, deletion upper bound,
activity boundary, ledger, strongest alternative and claim ceiling. It changes
only branch 4: its two-endpoint OR now uses branch-specific Bonferroni 97.5%
lower bounds, and a failed matched-specificity conjunction is no longer
mislabelled as evidence for generic regularization.

## Exact inherited surface and explicit exclusions

The following **definitions**, not evidence, are incorporated unchanged from
`SCDMP_B1_SCIENCE_CARD.md`:

- deterministic fixed-four-agent ring state, action hold, micro-dynamics,
  node/edge rewards and `T=240` episode score;
- deployable boundary information, visible duration/context word and absence of
  mid-skill decisions;
- training word tables at `k={2,4,8}`, target word tables at `k={6,12}`, and
  the six fixed/switching evaluation regimes;
- the 26,148-parameter shared `F/G_node/G_edge` architecture, exact word GRU,
  factorized fixed-cycle actor and lexicographic action tie rule;
- raw-bit-to-float transforms, reset-variable order, scaler population/API,
  physical output bounds and standardized residual definitions; and
- the exact deterministic monoid-action and undiscounted reward-cocycle
  equations for a held joint action.

This card overrides B1's arms, loss, gradient law, seeds and stream namespaces,
audit reset states, training arm order, estimands, margins, inference,
interpretation branches, activity boundary, resource ledger and claim ceiling.
B1's observations and thresholds are forbidden inputs to B2 design,
checkpointing or interpretation. No B1 output can be pooled with B2.

The varying axis remains externally supplied skill duration `k`; `N=4` is
fixed. All three arms see the same local physical state, complete ordered
forecast word, duration, previous joint action and fixed-degree messages. No arm
sees an oracle, future state/reward, evaluation statistic, another arm's output
or its own identity.

## Fresh seeds, corpus and immutable data support

There are eight paired algorithm seeds `s in {100,...,107}`. All three arms for
one seed start from byte-identical tensors and share one corpus, scaler set,
locked minibatch sequence, audit panel and scored tape. The fresh stream
namespaces are:

```text
initialization: PCG64(810000+s)
batch order:    PCG64(820000+s)
corpus resets:  PCG64(830000+s)
scored regime r:PCG64(850000+1000*s+r), r=0,...,5
```

They use the B1 raw `random_raw`, `U0`, `Umid`, Box-Muller, QR-sign and reset
draw laws literally. No other RNG API is allowed. The audit panel below has no
random draw. Paired arms reuse materialized objects and never advance their own
environment stream.

For each seed, generate 192 fresh 64-step behavior episodes: 64 at each
training duration, with the same class/word/action counterbalance as B1. The
first 48 episodes per duration form the fit set and the remaining 16 form the
untouched train-support probe. Build endpoint banks `E_2,E_4,E_8` and
composition banks `C_22,C_44` with the same complete-row granularity and
bank/stratum weighting as B1.

Every `C_22/C_44` row is constructed from the **original** `k=4/8` trajectory.
It retains the true split state, prefix node/edge rewards and suffix node/edge
rewards while that original rollout is generated. It is forbidden to replay
the environment to reconstruct a split row. Thus all arms receive identical
complete row objects and the corpus ledger has no hidden DGP work.

Each seed's four target-only fit-set scalers use its fresh `E_2/E_4/E_8` atoms,
the exact `10,752`-atom order, NumPy `1.26.3`, float64 population standard
deviation with `ddof=0`, float64 `1e-3` floor and one float32 cast specified in
B1. The three arms share those four constants. Each seed also stores the four
fit-set target means over the same ordered atoms. The arm-independent
`MEAN-REF` competence reference predicts these means for every requested
terminal coordinate and node/edge cumulative reward; it is never trained,
acted from or counted as an arm.

## Three arms and exact intervention

Every arm has the same architecture, parameter count, initialization, endpoint
loss, data rows, update count, optimizer, action scorer and exact actor.

1. **FREE-DIRECT** is the strong composition-free comparator. Its auxiliary
   directly supervises the whole word, prefix and suffix from stored truth.
   It receives more direct split-target information than the relation arms and
   is intentionally advantaged.
2. **SCDMP-CORRECT** uses the correct held-action semigroup and reward-cocycle
   relation.
3. **SCDMP-ORDER-SHUFFLE** is identical to CORRECT except that the two segment
   words are applied in reverse order only inside the recursive auxiliary. The
   direct whole-word prediction still receives the original word.

For one composition row let the original word be `W=pq`, true start be `y`,
true split state be `y_p`, true terminal be `y_W`, and true cumulative node or
edge rewards be `R_p,R_q,R_W`. Here `|p|=|q|=2` in `C_22` and `|p|=|q|=4` in
`C_44`. The joint action `u` is held throughout. Define the standardized direct
loss

```text
ell(y,u,w;y*,Rn*,Re*) =
    ||bar(F(y,u,w)-y*)||^2/2
  + mean_nodes bar(Gn(y,u,w)-Rn*)^2
  + mean_edges bar(Ge(y,u,w)-Re*)^2.
```

`L0` is the same equal-bank/equal-stratum endpoint loss over `E_2,E_4,E_8` for
every arm. Auxiliary losses use the same `C_22,C_44` batches and reduction:

```text
Laux_FREE = mean_pair,row [
    ( ell(y,u,W;y_W,Rn_W,Re_W)
    + ell(y,u,p;y_p,Rn_p,Re_p)
    + ell(y_p,u,q;y_W,Rn_q,Re_q) ) / 3 ].
```

For CORRECT, with every inner and outer call gradient-connected,

```text
dF_C  = F(y,u,W) - F(F(y,u,p),u,q)
dGn_C = Gn(y,u,W) - Gn(y,u,p) - Gn(F(y,u,p),u,q)
dGe_C = Ge(y_i,y_j,u_i,u_j,W)
        - Ge(y_i,y_j,u_i,u_j,p)
        - Ge(F_i(y_i,u_i,p),F_j(y_j,u_j,p),u_i,u_j,q).
```

For ORDER-SHUFFLE, only recursive order changes:

```text
dF_S  = F(y,u,W) - F(F(y,u,q),u,p)
dGn_S = Gn(y,u,W) - Gn(y,u,q) - Gn(F(y,u,q),u,p)
dGe_S = Ge(y_i,y_j,u_i,u_j,W)
        - Ge(y_i,y_j,u_i,u_j,q)
        - Ge(F_i(y_i,u_i,q),F_j(y_j,u_j,q),u_i,u_j,p).
```

`Laux_CORRECT` and `Laux_SHUFFLE` apply the same F/node/edge standardized-square
reduction as one B1 composition row. There is no detach, target model, hidden
swap, word relabeling or actor call at the split. Each arm performs exactly
three output-relevant auxiliary model calls per row with the same tensor-shape
multiset. FREE's suffix call starts at true `y_p`; the relation arms' outer call
starts at their predicted intermediate. This deliberately strengthens FREE but
makes exact pathwise Jacobian matching impossible. B2 claims only matched
blockwise connectivity and gradient magnitude, never identical information or
pathwise gradients.

On homogeneous training words `p=q`, CORRECT and SHUFFLE are identical. The two
mixed word rows in each duration/class cell are the order-active training
intervention; homogeneous rows are identity controls. All rows remain in every
arm's training reduction. Only mixed REAL target rows can support a
relation-specific conclusion. Mixed SHAM rows and untouched homogeneous
train-support rows are controls and cannot substitute for REAL evidence.

## Exact auxiliary-gradient strength contract

Use PyTorch `2.7.0+cpu`, NumPy `1.26.3`, CPU only, and set, before importing
NumPy or Torch,

```text
CUDA_VISIBLE_DEVICES=
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
BLIS_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1
```

Then call `torch.set_num_threads(1)`, `torch.set_num_interop_threads(1)` and
`torch.use_deterministic_algorithms(True)`. The claim is deterministic on this
pinned CPU host, not cross-hardware bit identity.

The immutable parameter tuple is:

```text
node_1.weight,node_1.bias,node_2.weight,node_2.bias,
action_embedding.weight,action_embedding.bias,
word_gru.weight_ih,word_gru.weight_hh,word_gru.bias_ih,word_gru.bias_hh,
f_1.weight,f_1.bias,f_2.weight,f_2.bias,f_3.weight,f_3.bias,
gn_1.weight,gn_1.bias,gn_2.weight,gn_2.bias,
ge_1.weight,ge_1.bias,ge_2.weight,ge_2.bias.
```

Every name must be present, unique and `requires_grad=True`; every
`torch.autograd.grad` call uses that ordered tuple with `allow_unused=False`,
and every returned value must be non-`None`. For a gradient tuple `g`, define
its norm by visiting that printed parameter order, applying
`g.detach().to(dtype=torch.float64).contiguous().view(-1)`, computing
`torch.sum(g64*g64,dtype=torch.float64)` single-threaded, adding the 24 scalar
sums left-to-right in float64, and applying `torch.sqrt` once.

For seed `s`, before any optimizer step compute the common update-zero endpoint
gradient `g0_init` from the exact locked update-zero endpoint minibatch and the
card's bank/stratum/row reduction on one canonical initialized model and set

```text
B_s = norm(g0_init)
T_s = float64(0.25) * B_s.
```

Require finite `B_s>1e-12`. `T_s/B_s=0.25`, not a separate raw loss
coefficient, is the sole auxiliary-strength parameter. At every arm/update,
compute fresh, disjoint graphs for endpoint gradient `g0` and raw auxiliary
gradient `ga`. Let `A=norm(ga)`. Require every component finite and

```text
A >= float64(0.01) * B_s.
```

This makes the maximum scale factor `T_s/A` equal to 25 and prevents a
near-zero auxiliary direction from being amplified into apparent activity. A
failure is never floored, skipped or repaired.

Compute `scale=T_s/A` in float64. For each parameter in printed order cast
`g0` and `ga` once to float64, form `g64=g0+scale*ga`, require finite, cast once
to float32 and assign `.grad`. Then call exactly

```text
torch.nn.utils.clip_grad_norm_(
    ordered_parameters, 1.0, norm_type=2.0,
    error_if_nonfinite=True, foreach=False)
```

and one separate Adam step for that arm with `lr=1e-3`,
`betas=(0.9,0.999)`, `eps=1e-8`, `weight_decay=1e-5`. Weight decay is inside
Adam and excluded from `B_s,g0,ga,T_s`. Stored float32 auxiliary components
approximate the float64 target norm; no bit-equality claim is made.

This matches the pre-combination global auxiliary norm, model-call shapes,
blockwise differentiable connectivity and useful output work. It does not match
the angle between endpoint and auxiliary gradients, post-combination clipping,
Adam coordinate moments, pathwise Jacobians, curvature or evolving relative
endpoint strength. Those residual optimization explanations remain in the
claim ceiling.

The one-time `B_s` graph is discarded without an optimizer step, parameter
mutation or cursor advance. The unchanged initialized tensors and already
materialized update-zero rows are then cloned byte-for-byte into the three
arms. At update zero each arm recomputes its own `g0` and `ga` under the same
law used at every later update.

## Training schedule and scientific activity

Use exactly 1,000 updates per arm/seed. The fresh `PCG64(820000+s)` stream,
Fisher-Yates law, bank/stratum order, cursor wrap and eight rows per stratum are
the B1 laws, now shared by three arms. Every update contains all endpoint banks,
both composition pair types, REAL and SHAM, and all word rows. Step arms in
fixed order `FREE-DIRECT`, `SCDMP-CORRECT`,
`SCDMP-ORDER-SHUFFLE`; there is no stochastic layer or shared mutable optimizer
state. Each arm has its own Adam state. The final update is the sole checkpoint.

Before computing `B_100`, materialize the locked update-zero rows and require
that they contain all three endpoint durations, both composition pair types,
REAL and SHAM, all four word rows, at least two distinct joint actions and every
scalar action. Report the complete-row denominators. Failure occurs before
scientific activity and permits only an unchanged-science construction repair;
it never permits a new seed, batch, threshold or treatment.

Question-relevant scientific activity begins immediately before the first
`torch.autograd.grad(L0)` invocation used to compute `B_100`, after corpus,
scaler, bank, batch, parameter-name and update-zero coverage conformance. Any
later missing/nonfinite gradient, `B_s<=1e-12`, `A<0.01*B_s`, incomplete arm or
resource termination is a scientific nonidentifying outcome, not a preactivity
engineering retry. No threshold, arm, seed or optimizer adjustment is allowed
after this boundary.

## Fresh audit, physical headroom and legal action path

For each seed build 64 deterministic physical audit states: 32 at `k=6`, 32 at
`k=12`, crossed exactly as in B1 over REAL/SHAM, four mixed target-word rows,
four cyclic slot offsets and two severities. Replace B1 reset values by:

```text
MILD:   e=(-0.08,+0.03,+0.08,-0.03), v=(0.16,0.24,0.18,0.22)
SEVERE: e=(-0.21,+0.07,+0.21,-0.07), v=(0.08,0.32,0.12,0.28)
q_base=(+1,-1,+1,-1).
```

Apply the same left slot rotation and severity crossing law. Warm each reset for
48 primitive steps at `k=4`; at boundary `b=0,...,11`, use table row
`(w+b) mod 4` and joint-action index
`(g+37*(s-100)+b) mod 81`. The resulting state is shared by arms. Pair the
target word with its literal reverse. No B1 audit state, action offset or
prediction is reused.

Truth and learned action scores are evaluated by the exact node/edge
factorization and the same cycle dynamic program. For each state/word, roll or
predict the 3 node actions and 9 directed neighbor-action factors, then solve
the cycle with the frozen lexicographic tie rule. Never enumerate or roll 81
joint-action trajectories and never rank more than the factorized legal action
representation. All predicted outputs enter the deployed score.

The physical/order and common-support gates are:

1. for every seed, mixed REAL reversal twins have median maximum true-score
   difference per primitive step at least `0.020` and oracle action reversal on
   at least `0.20` of twins;
2. every mixed SHAM twin agrees to `1e-10` in true score and oracle action;
3. separately for every seed, at least 61 of its 64 target audit states have
   all eight continuous boundary-input coordinates `(e_1,v_1,...,e_4,v_4)`
   inside the corresponding coordinatewise minimum/maximum over that seed's
   complete fit-set endpoint-bank boundary inputs; visible `q` is checked by
   exact membership in `{-1,+1}` rather than pooled into this fraction;
4. separately for every seed, every joint action occurs at least four times in
   each of its three direct-duration fit banks; and
5. for each of FREE and SHUFFLE, the across-seed mean fraction of REAL audit
   word-states with true oracle regret at least `0.015` per primitive step is at
   least `0.25`, and mean regret over all REAL states is at least `0.008`.

Failure of any item makes the family discriminator nonidentifying. Pooled or
SHAM headroom cannot substitute.

## Per-arm competence and intervention activity

For arm `m` and seed `s`, compute the same equal-output composite standardized
RMSE on the untouched train-support probe and on all mixed REAL target
word-state-action panels. The latter are exactly the seed's 64 REAL word-state
instances (target and reverse counted separately), all 81 joint actions, and
eight F coordinates plus four node and four directed-edge outputs. Within each
output family, average standardized squared residuals over word-states, joint
actions and coordinates/slots, take one square root, then average the F, node
and edge RMSEs equally. The untouched train-support reduction is identical
except that it uses every complete probe-bank row and its behavior joint action.
Divide each arm RMSE by its seed's `MEAN-REF` RMSE on that same population.
Every reference RMSE must be finite and strictly above `1e-12`; otherwise the
competence question is nonidentifying.

Every conclusion-bearing arm must satisfy all of:

- every seed's train-support ratio is at most `0.70`;
- the across-seed mean target-REAL ratio is at most `0.75`, and its one-sided
  95% upper t bound is below `0.90`;
- no nonfinite output, no more than `0.02` of physical predictions at an F
  bound, and, for every seed, arm, physical coordinate and slot, the variance
  over the same 64 REAL by 81-action prediction panel divided by the positive
  true-terminal variance is in `[0.20,5.0]`; and
- on at least `0.90` of REAL audit word-states, predicted best-minus-worst legal
  score range is at least `0.015*k`, separately for every arm and seed.

These are fresh relative competence rules, not B1's absolute thresholds.
Every true-terminal variance denominator is computed over the same 64 by 81
atoms for its coordinate/slot and must be finite and strictly greater than
zero. A nonfinite or nonpositive denominator is branch 7; it is never skipped,
pooled, floored or replaced.

The intervention itself is active only if every update passes the gradient-
norm law and the SHUFFLE wrong-relation first-stage contrast defined below
clears its margin. Action relevance is a separate conclusion gate: the one-
sided 95% lower bounds for the mean CORRECT-versus-FREE and CORRECT-versus-
SHUFFLE action-disagreement fractions on REAL targets must each exceed `0.125`.
Each seed fraction uses the same 64 word-states and one selected joint action
per arm/word-state.

Homogeneous identity is a preactivity structural conformance gate requiring no
model forward: separately for every seed and every homogeneous fit-bank row in
`C_22,C_44`, the stored token arrays `p` and `q` must be byte-identical, and the
serialized direct/prefix/suffix word-and-input call specification produced by
the relation builder must be byte-identical under CORRECT and SHUFFLE order.
A failure is an unchanged-science construction defect before activity.

Posttraining homogeneous probe defects are descriptive only. At corpus
generation, retain read-only virtual half-split views from the original
untouched `k=4/8` support traces, with no replay and no admission to a fit bank,
normalizer, update or checkpoint rule. For every seed this population is all
REAL/SHAM probe boundaries whose complete word is `A^4,B^4,A^8` or `B^8`:
128 `k=4` rows plus 64 `k=8` rows, exactly 192 rows per seed. For each arm,
evaluate one common
prefix-then-suffix graph because `p=q`, compute the same per-pair and F/node/
edge standardized RMS reduction as `Dcorr`, and report `Dhom_m`. Comparisons
among arms have no gate and cannot replace mixed REAL evidence.

## Estimands and inference

The unit of inference is eight independent paired algorithm seeds. Audit action
panels and scored episodes are within-seed observations, not replicates. Use
one-sided Student-t bounds with `df=7`; exact `2^8` paired sign-randomization
p-values accompany but never replace bounds.

On the exact 64 REAL word-state by 81-joint-action panel define for each
arm/seed:

- `Dcorr_m_REAL`: equal-weight standardized correct-relation defect over both
  legal target decompositions and F/node/edge outputs;
- `Dwrong_m_REAL`: the corresponding order-reversed recursive-relation defect;
- `Epred_m_REAL`: standardized true whole-word endpoint/reward RMSE;
- `Q_m_REAL`: mean true oracle regret per primitive step of the arm's selected
  action; and
- corresponding SHAM quantities under identical reductions.

For `k=6`, the two legal decompositions are the literal first-two/last-four
and first-four/last-two splits; for `k=12`, they are the first-four/last-eight
and first-eight/last-four splits. For each split, `Dcorr` uses the direct word
against prefix-then-suffix recursion and `Dwrong` against suffix-then-prefix
recursion, with the exact F/node/edge equations above. Within an F, node or
edge component, average standardized squared residuals equally over the two
splits, 64 word-states, 81 actions and coordinates/slots, then take one square
root; average the three component RMS values equally. `Epred` uses the same
reduction without a split index. `Q` first selects one action with the frozen
learned actor, evaluates that action and the frozen true oracle under `R+H`,
and averages their nonnegative true-score gap divided by `k` over the 64
word-states. SHAM uses the corresponding 64 SHAM instances.

Higher values favor CORRECT in seven effect contrasts; the eighth contrast is
the required SHUFFLE intervention-fidelity check:

```text
C_FREE = Dcorr_FREE_REAL    - Dcorr_CORRECT_REAL
C_SHUF = Dcorr_SHUFFLE_REAL - Dcorr_CORRECT_REAL
W_SHUF = Dwrong_CORRECT_REAL-Dwrong_SHUFFLE_REAL
P_FREE = Epred_FREE_REAL    - Epred_CORRECT_REAL
P_SHUF = Epred_SHUFFLE_REAL - Epred_CORRECT_REAL
A_FREE = Q_FREE_REAL        - Q_CORRECT_REAL
A_SHUF = Q_SHUFFLE_REAL     - Q_CORRECT_REAL
ORDER  = (Dcorr_SHUFFLE_REAL-Dcorr_CORRECT_REAL)
         -(Dcorr_SHUFFLE_SHAM-Dcorr_CORRECT_SHAM).
```

A relation-specific, action-relevant mechanism requires the one-sided 95% lower
bounds to exceed:

```text
C_FREE,C_SHUF,W_SHUF > 0.040 standardized units
P_FREE,P_SHUF        > 0.020 standardized units
A_FREE,A_SHUF        > 0.004 normalized reward per primitive step
ORDER                > 0.020 standardized units.
```

All eight gates form one intersection-union claim; each must pass, so no
multiplicity opportunity is created by the conjunction. Failure to reject any
component is not evidence of absence.

Scored evaluation uses the same six regimes and 32 episodes per arm/seed/regime
as B1 but the fresh B2 tapes. Define, for `X in {FREE,SHUFFLE}`, the eight
paired seed values and their across-seed means by

```text
dJ_CX,s(r)    = mean_episode[J_CORRECT-J_X | REAL,seed=s,r]
dfail_CX,s(r) = mean_episode[failure_X-failure_CORRECT | REAL,seed=s,r]
dJ_CX(r)      = mean_s dJ_CX,s(r)
dfail_CX(r)   = mean_s dfail_CX,s(r).
```

The 24 values (six regimes, two controls, reward and failure) form the adverse
family. A material adverse result occurs if any one-sided simultaneous upper
bound at per-estimand confidence `1-0.05/24` is below `-0.010` reward per step
or `-0.040` failure probability. Separately, full non-harm requires every
corresponding lower bound at the same per-estimand confidence to exceed those
margins. Absence of an adverse trigger is not non-harm. Returns, failures and
all other B1 physical metrics are reported, but B2 has no positive task-value
route.

## Frozen ordered interpretation

First require exact treatment/configuration identity, no leakage, successful
post-activity completion of all three arms and all scored/audit panels, finite
outputs, resource conformance and a complete retained packet. If any fails,
use branch 7. Given that minimum causal-result core, test branch 1 before any
model-mechanism condition: a complete randomized paired treatment can establish
registered harm even when a competence or headroom first stage fails. If no
adverse bound fires, require every remaining support, physical-order, SHAM,
headroom, competence and intervention-activity condition (gradient law plus
`W_SHUF` fidelity); failure then uses branch 7. Action-disagreement and regret
are downstream effect gates, not intervention-validity gates. Otherwise apply
the first matching branch below:

1. **Adverse exact treatment.** Any adverse-family upper bound crosses its
   margin. Reject CORRECT for this host/budget; model diagnostics remain
   descriptive and cannot activate another study.
2. **Relation-specific action-relevant inductive bias.** All seven effect
   lower-bound gates, the `W_SHUF` fidelity lower-bound gate, both action-
   disagreement gates and full non-harm pass.
   Retain the relation-specific family for a separately frozen direct-value
   experiment. Claim no B2 task benefit.
3. **Relation-specific representation only.** `C_FREE,C_SHUF,W_SHUF,P_FREE,
   P_SHUF,ORDER` pass, but an action-regret, disagreement or non-harm condition
   does not pass and no adverse branch fires. Report model-level specificity
   only; do not progress an algorithm or surface automatically.
4. **FREE-control effect without relation-specific identification.** Define
   `pass_FREE_adj(C_FREE)` as its one-sided **97.5%** lower bound strictly above
   `0.040`, and `pass_FREE_adj(P_FREE)` as its one-sided **97.5%** lower bound
   strictly above `0.020`. Then

   ```text
   FREE_EFFECT = pass_FREE_adj(C_FREE) OR pass_FREE_adj(P_FREE)
   MATCHED_SPEC = pass(C_SHUF) AND pass(P_SHUF) AND pass(ORDER),
   ```

   where each `pass` inside `MATCHED_SPEC` retains its registered one-sided 95%
   lower bound and margin because that set is a conjunction. This branch fires
   exactly when `FREE_EFFECT` is true and `MATCHED_SPEC` is false; `W_SHUF` has
   already passed the common intervention-fidelity prerequisite. Report exactly
   which adjusted FREE contrast or contrasts pass. The result establishes only
   the named bounded model effect relative to FREE on those endpoints. It does
   not identify correct-relation specificity or generic regularization:
   correct-relation learning with imprecise matched-control bounds, generic
   auxiliary optimization, FREE's information/path asymmetry and finite
   optimizer geometry remain unresolved. No algorithm, treatment-deletion or
   later-surface conclusion follows from this branch.
5. **Exact-treatment deletion.** All core, support, headroom and competence
   conditions pass; the gradient and SHUFFLE fidelity checks pass, including
   the lower bound for `W_SHUF`; and the one-sided 95% **upper** bounds for all
   seven CORRECT-favoring effect contrasts (`C_FREE,C_SHUF,P_FREE,P_SHUF,
   A_FREE,A_SHUF,ORDER`) are below their respective minimum useful margins.
   Delete further investment in this exact correct-relation treatment on the
   registered host, architecture and budget. Do not delete every SCDMP or
   another surface.
6. **Valid indeterminate.** The complete experiment is valid but no prior
   branch applies because intervals or mixed gates remain unresolved. Do not
   add seeds, weaken margins or rerun automatically.
7. **Nonidentifying.** Activity, output, resource, support, physical order,
   comparator headroom, per-arm competence, auxiliary gradient activity,
   wrong-control activity or another core condition fails. No positive,
   negative, null, equivalence, adverse or family conclusion is available.

Branch 5 is an intersection of seven upper-bound tests plus a separately
passing wrong-control manipulation check and creates no multiplicity
opportunity. A point estimate, failed lower bound or B1 observation cannot
substitute for its upper bounds.

## Strongest alternative and maximum claim

Even under branch 2, FREE has additional true split labels and lacks nested
Jacobians; CORRECT and SHUFFLE differ in gradient alignment, curvature and
compatibility with endpoint learning; global clipping and Adam can turn equal
pre-combination auxiliary norms into different parameter steps; and finite
capacity/optimization can favor the correct relation without making it uniquely
necessary. Therefore the maximum positive claim is:

> On the exact deterministic, fully observed, fixed-`N=4` convoy, with one
> shared model trained at `k={2,4,8}` and audited at mixed REAL `k={6,12}`
> words, the correct composition direction provided a finite-budget,
> order-specific inductive bias for the registered model-and-actor pathway over
> the named stronger direct-supervision and wrong-relation controls, conditional
> on every competence, activity, headroom, specificity and non-harm gate.

B2 cannot claim improved task return or failure robustness, unique algebraic
mediation, necessary expressivity, arbitrary/unknown `k`, stochastic or hidden-
state consistency, variable `N`, another architecture, ground payload, UAV,
safety or real flight. It cannot activate a second surface.

## Resource and retained-output contract

The exact analytic environment ledger is:

```text
common corpus full-joint steps       98,304
three-arm scored full-joint steps 1,105,920
common audit warm-up steps           24,576
target factor transitions           373,248 analytic microstep-equivalents
reverse factor transitions          373,248 analytic microstep-equivalents
total                              1,975,296
```

The physical full-joint subtotal is `1,228,800`; target and reverse each also
contain `55,296` explicitly counted scalar-agent factor transitions. Optimizer
updates have exactly 216,000 batched model forward calls
(`8*1000*3*(3+2*3)`). The eight `B_s` calibrations add three endpoint-bank
forwards each, so the exact treatment-definition/training subtotal before any
support/audit/scored prediction is `216,024`. Posttraining `Dhom` adds 144
support-evaluation calls (`8*3*2*3`) outside that subtotal. Training also has
24,000 endpoint-gradient traversals, 24,000 auxiliary-gradient traversals,
24,000 float64 auxiliary norms and eight initial `B_s` gradient traversals.
Each of three arms has 26,148 parameters and a separate Adam state.

The hard envelope is one CPU, no GPU, at most 90 minutes wall time and less than
2 GiB peak RSS. Static engineering projection is 25--45 minutes and below 650
MiB, but it is not evidence or a tighter gate. Any resource violation after the
activity boundary is branch 7 and gets no automatic retry.

A retained complete output must contain exact revision/configuration, activity
sidecar, all 24 arm-seed checkpoints, scalers and fit means, every `B_s/T_s`,
every per-update raw auxiliary norm and scale, all competence/activity/support/
headroom facts, the exact 128/64 homogeneous-probe row certificate and `Dhom`
reports, every seed-level primary contrast, all 24 adverse/non-harm
families, physical metrics, resource facts and anomalies. It must preserve an
incomplete fail-closed record after any post-activity interruption and install a
complete result atomically only after every arm/seed/panel is present. CM owns
technical acceptance; the result file contains no scientific branch until this
EM intakes it.

## Authority boundary

This owner freeze authorizes no construction, test, compute or provider action.
Root must first publish the exact composite. The existing SCDMP ChatGPT Pro
conversation must then return literal `CLOSED`, followed by this EM's intake,
before Root may consider CM construction. The independent Gemini requester is
prepared but unsent and cannot replace Pro closure. No new provider
conversation, payload surface or UAV action is authorized by this card.
