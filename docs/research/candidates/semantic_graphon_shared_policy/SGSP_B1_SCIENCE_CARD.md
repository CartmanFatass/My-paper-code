# SGSP B1 science card

```text
direction=semantic_graphon_shared_policy
revision=SGSP-B1-SCIENCE-20260813-03
supersedes_revision=SGSP-B1-SCIENCE-20260813-02_PRO_CLOSED
owner=EM_semantic_graphon_shared_policy
object=result-blind prospective direct-variable-N discriminator
scientific_activity_started=false
mathematical_closure=revision_03_PREPARED_NOT_SENT_SAME_CONVERSATION
cm_release=withheld_for_revision_03_closure
construction_authorization=none
compute_authorization=none
chatgpt_external_pro=revision_02_CLOSED_revision_03_PREPARED_NOT_SENT
external_gemini=RECOVERY_EXHAUSTED_NO_PROVIDER_TURN
```

## Conclusion first

SGSP remains a meaning-complete and decision-changing candidate after accepting
all seven exact prospective defects in the result-blind revision-01 ChatGPT Pro
ruling. Revision 02 received Pro `CLOSED` after freezing the common initializer, complete Adam/batch update,
full dense-reference actor-input audit, tape-conditioned endpoint envelope,
`EDGE-PE`-versus-anonymous estimand, exhaustive branch precedence, and earliest
stochastic-materialization activity boundary. Before any stochastic
materialization, CM then identified one literal conflict between an `N`-bearing
counter address and handoff wording that called worlds nested. Revision 03
chooses the address-consistent rule: roster sizes use disjoint stochastic
namespaces and no cross-`N` member prefix; pairing is within each exact `N` only.
No data or implementation fact informed either revision. B1 asks whether a
correct observable two-block semantic graphon is a useful finite-budget
inductive bias for one shared policy deployed unchanged at roster sizes outside
the training set. It is not admitted merely by beating an anonymous mean. Its
primary comparator is an information-, parameter-, optimization-, action-,
communication-, and useful-work-matched permutation-equivariant edge policy
whose edge-kernel class strictly contains the treatment's class.

The physical toy is deliberately dense, but the deployed graphon and comparator
summaries use two block sufficient statistics and never materialize an `N x N`
object. Their deployment cost is `O(2N)` time and `O(N)` input storage. A direct
dense `N x N` computation exists only as a small-simulator reference. This
respects the project complexity boundary and avoids inheriting a linear
allocator's incompatible `no_nxn_object` guard.

The decisive outcome is result-blind. A graphon-specific promotion requires a
material held-out-`N` advantage over the stronger edge comparator, common
support and two-sided endpoint availability, exact permutation equivariance,
an action-sensitive semantic-coordinate reassociation cut, and complete
capacity/work evidence. If SGSP beats only the anonymous mean while matching or
losing to the edge comparator, the fixed-graphon-specific family is deleted.
Nothing here transfers a threshold, result, or scientific fact from another
direction. Nothing authorizes provider contact, implementation, tests, or
compute.

## Five-line science card

- **Question.** On a dense two-role cooperative decision task, can a known
  semantic block-graphon anchor improve held-out-roster task return over a
  strictly more flexible matched edge kernel, with one frozen shared policy?
- **Treatment.** `SGSP-W`: a shared encoder and actor conditioned on an exact
  implicit two-block graphon summary, with only a small bounded learned
  role-pair calibration around the known physical graphon.
- **Comparators.** `EDGE-PE`, the same policy with a strictly wider learned
  directed role-pair edge family, is primary; `ANON-MEAN`, a sender-anonymous
  population mean with the same actor shape, is a diagnostic control.
- **Observable.** Paired team correctness return at `N={6,16}` after training
  only at `N={8,12}`, plus semantic reassociation return, action-probability
  total variation, dense-reference agreement, identity-permutation equality,
  common support, and useful-resource ledgers.
- **Strongest alternative and ceiling.** A positive result may be a finite-data
  regularization benefit of a correct two-block prior. B1 cannot establish
  universal graphon learning, general graphs, arbitrary `N`, churn, learned
  coordinates, UAV value, or a theorem-level mean-field guarantee.

## 1. Provenance and scientific boundary

The local corpus is inspiration and a claim boundary, not evidence for SGSP.

- P12 motivates label-conditioned graphon neighborhood measures and block
  discretization. Its finite-`N` rates and approximate-equilibrium results do
  not establish a learned frozen policy at held-out `N`, and its labels/order
  are assumed rather than learned here.
- P08 motivates the fixed-width anonymous neighbor-mean control and its known
  inability to preserve multimodal or role-conditioned population structure.
  Multiple roster experiments in that literature are not evidence for one
  frozen cross-`N` policy.
- P22 motivates separating finite-population error from graph/kernel mismatch.
  Its uncontrolled-particle bounds do not become policy, value, or deployment
  guarantees. B1 records these errors separately and makes no rate claim.

The only prior-direction fact used here is a portfolio trigger supplied by
Root: a previous host did not answer its own question. That fact supplies no
SGSP likelihood, margin, threshold, comparator result, or causal evidence.

## 2. Frozen dense two-block cooperative process

### 2.1 Roster, observable coordinate, and ties

Every episode has an even roster size. Training samples only

```text
N_train={8,12}
```

and evaluation adds held-out sizes on both sides:

```text
N_heldout={6,16}.
```

Exactly `N/2` agents have public semantic role `SCOUT` and exactly `N/2` have
public semantic role `RELAY`. The graphon coordinate is

\[
u_i=1/4\quad\text{for SCOUT},\qquad
u_i=3/4\quad\text{for RELAY}.
\]

Ties are deliberate. All members of a role share the same coordinate; there is
no within-role rank, tie breaker, or hidden identity coordinate. A fresh opaque
handle and a fresh row position are assigned uniformly every episode. Neither
is a policy input. The coordinate is observed without noise by every deployed
arm wherever that arm is defined to use it. B1 does not learn, estimate, sort,
or impute `u`.

### 2.2 Dense graphon and self edge

Let block index `b_i=0` for `SCOUT` and `b_i=1` for `RELAY`. The known physical
step graphon is

\[
W=\begin{bmatrix}1&0.2\\0.2&1\end{bmatrix}.
\]

It is symmetric, nonnegative, dense, and independent of `N`. Every ordered
pair contributes, including the self edge `j=i`. The population normalization
is always `1/N`, not degree, `1/(N-1)`, training-roster normalization, or an
unnamed library default.

For simulator truth only, a dense reference forms

\[
m_i^{dense}=\frac1N\sum_{j=1}^N W_{b_i b_j}x_j.
\]

The deployable implementations must instead use the exact block sums

\[
S_b=\frac1N\sum_{j:b_j=b}x_j,\qquad
m_i=W_{b_i0}S_0+W_{b_i1}S_1.
\]

No learned or physical `N x N` tensor is permitted in a deployable arm.

### 2.3 Context distribution

Each one-step cooperative episode first draws a public evaluation stratum but
not the latent orientation:

```text
regime in {SAME, OPPOSED}, with probability 1/2 each
```

Within `SAME`, draw `c` uniformly from `{-1,+1}` and set
`(c_0,c_1)=(c,c)`. Within `OPPOSED`, draw `c` uniformly and set
`(c_0,c_1)=(c,-c)`. Then independently for every agent,

\[
x_i=0.6c_{b_i}+\epsilon_i,\qquad \epsilon_i\sim N(0,1).
\]

All stochastic world objects are explicitly `N`-separated. The latent
orientation uses address
`(phase,seed,N,regime,episode,orientation)`. The Gaussian member tape uses
`(phase,seed,N,regime,episode,role,within_role_slot,gaussian)`. The action tape
uses the same address with terminal field `action`, and the row permutation
uses `(phase,seed,N,regime,episode,identity_permutation)`. These addresses never
contain arm, cut, opaque handle, or row order. Slots are semantic generator
addresses, not policy inputs.

Different values of `N` therefore occupy disjoint counter namespaces: a world
at `N=6` is not a prefix of a world at `N=16`, and training worlds at `N=8`
are not prefixes of those at `N=12`. The same orientation, member messages,
action uniforms, and identity permutation are reused across arms and every
defined intact/reassociation or canonical/permuted replay within one exact
`(phase,seed,N,regime,episode)` cell. There is no pathwise cross-`N` contrast.
The within-seed minimum over held-out sizes is the minimum of two independently
generated cell summaries conditional on the same seed-specific trained
checkpoints. Continuous noise makes an exact zero field probability zero; if a
binary64 evaluation equals zero, the fixed target is `+1`.

### 2.4 Legal action and reward

Every agent takes exactly one legal action from

```text
{SERVE_NEG, SERVE_POS}.
```

The correct role action is

\[
y_i=\mathbf 1[m_i^{dense}\ge 0].
\]

All agents share the cooperative team return

\[
R=\frac1N\sum_{i=1}^N\mathbf 1[a_i=y_i]\in[0,1].
\]

Actions do not alter the already drawn field, but each action changes the
realized return by exactly `1/N` when it crosses correctness. This is a
one-decision cooperative contextual bandit, not a temporal-control or churn
claim. The simulator records per-agent correctness solely to compute the exact
counterfactual training baseline; the deployed actor never observes `y`, `m`,
reward, or latent `c` before acting.

### 2.5 Common stochastic support

Every arm produces two logits and deploys

\[
\pi_A(a\mid o)=0.96\,\operatorname{softmax}(\ell_A)_a+0.02.
\]

Thus both legal actions have probability at least `0.02` in every state, arm,
seed, roster, and regime. Paired evaluation uses the same counter-addressed
uniform action variate after inverse identity-permutation addressing. There is
no invalid action, mask difference, termination difference, or endogenous
trajectory-support difference in this one-step process.

## 3. Frozen deployed policy family

### 3.1 Shared message encoder and actor

Each arm and training seed owns one parameterization, shared across every
agent and both training roster sizes. That same checkpoint is evaluated
unchanged at all four roster sizes. No `N`-specific head, normalization,
adapter, embedding table, retraining, finetuning, or held-out calibration is
allowed.

The sender encoder is

\[
q_j=[x_j;\tanh(Ax_j+a)]\in\mathbb R^{33},
\]

where `A` is `32 x 1`. Its first coordinate is the raw message, so the correct
graphon field is representable without asking a nonlinear encoder to preserve
sign. The actor input is

```text
[normalized_population_summary(33), weighted_mass(1), receiver_role_onehot(2)]
```

and the shared actor is `36 -> 32 -> 2` with `tanh` hidden activation.

For each registered seed `s` and each common weight matrix `L` in
`{encoder_A, actor_hidden_weight, actor_head_weight}`, initialize

\[
\theta[L,r,c]=
\sqrt{\frac{6}{fan\_in(L)+fan\_out(L)}}
\left(2U(s,\text{initialization},L,r,c)-1\right),
\]

where every `U` is uniform on `[0,1)` under a counter namespace disjoint from
all world, action, permutation, and evaluation tapes. Set encoder bias, actor
hidden bias, actor head bias, and every role-pair `gamma` exactly to binary64
zero. Copy all common tensors bitwise into `SGSP-W`, `EDGE-PE`, and
`ANON-MEAN` before update 1. No framework or library initializer is legal.

Training uses float64 and exactly `480` updates. Every update contains `64`
independently generated worlds, exactly `16` from each `N_train x regime`
cell. Compute the arithmetic mean of the displayed per-world loss over all 64
worlds, so each of the four cells has weight exactly `1/4`. Accumulate that mean
in float64 in lexicographic order `(N, regime, within-cell episode index)`,
differentiate once, and clip the single concatenated gradient vector over all
trainable parameters to Euclidean norm `2` before updating optimizer moments.
Apply Adam with learning rate `4e-4`, `beta1=0.9`, `beta2=0.999`,
`epsilon=1e-8`, bias correction enabled, `amsgrad=false`, and
`weight_decay=0`. There is no validation selection, early stopping,
hyperparameter search, checkpoint choice, or post-hoc seed replacement. The
only evaluable checkpoint is the parameter state immediately after optimizer
update 480.

The common team-reward policy-gradient loss uses the exact one-step
counterfactual baseline. For sampled joint action `a`,

\[
B_i=\sum_{a_i'\in\{0,1\}}\pi_i(a_i')R(a_i',a_{-i}),\quad
A_i=R-B_i,
\]

and the loss is

\[
-\frac1N\sum_i\operatorname{stopgrad}(A_i)\log\pi_i(a_i)
-0.01\frac1N\sum_i H(\pi_i).
\]

This is centralized training with a known reward counterfactual and
decentralized shared execution. The baseline changes variance, not the legal
policy inputs or reward objective, and is identical across arms.

### 3.2 `SGSP-W` treatment

`SGSP-W` has four learned directed role-pair residual scalars `gamma_bb'`. Its
positive edge multiplier and weighted summary are

\[
r^{SGSP}_{bb'}=0.25\tanh(\gamma_{bb'}),\qquad
\omega^{SGSP}_{bb'}=W_{bb'}\exp(r^{SGSP}_{bb'}),
\]

\[
D_b=\frac1N\sum_j\omega^{SGSP}_{b b_j},\quad
M_b=\frac1N\sum_j\omega^{SGSP}_{b b_j}q_j,\quad
Z_b=M_b/(D_b+10^{-12}).
\]

The actor receives `[Z_b,D_b,onehot(b)]`. The learned calibration can correct a
small misscaling but cannot discard the semantic graphon anchor: every
residual log multiplier lies in `[-0.25,0.25]`.

### 3.3 Primary `EDGE-PE` comparator

`EDGE-PE` has the identical encoder, actor, four directed role-pair scalars,
initial tensors, inputs, output support, samples, updates, optimizer, and
summary equations, except

\[
r^{EDGE}_{bb'}=2\tanh(\gamma_{bb'}),\qquad
\omega^{EDGE}_{bb'}=W_{bb'}\exp(r^{EDGE}_{bb'}).
\]

Its residual log-multiplier interval `[-2,2]` is eight times wider. It can
invert the nominal same-role/cross-role preference because the maximum
cross/same ratio exceeds one. For every treatment residual table strictly
inside its bounds, a comparator table exists exactly via

\[
\gamma^{EDGE}_{bb'}=
\operatorname{atanh}\left(r^{SGSP}_{bb'}/2\right).
\]

Thus, for this two-block observation class, `EDGE-PE` is a strict functional
superfamily, not a weaker mean baseline. Its directed edge table is the
strongest useful comparator for this exact toy; sender-content-dependent or
multi-layer attention would add information/capacity not needed to represent
the physical operator and would test a different family.

Both arms use the same number of parameters:

```text
encoder=64
edge_table=4
actor_hidden=1184
actor_head=66
total=1318
```

Both execute the same output-relevant scalar operations: one encoder per row,
four role-pair exponentials, two receiver-role block reductions, and one actor
per row. The constants `0.25` and `2` change no operation count. No ignored
output, frozen padding head, dummy multiply, or ledger-only work is permitted.
Forward and backward opportunities, minibatches, initialization draws, Adam
states, message symbols, summaries, and action calls are equal in every claim
cell. The comparator is intentionally more expressive; no capacity deficit can
explain a treatment advantage.

### 3.4 `ANON-MEAN` control

`ANON-MEAN` uses the same sender encoder and actor shape but replaces the sender
population input by

\[
Z^{mean}=\frac1N\sum_jq_j,\qquad D^{mean}=1.
\]

It receives the true receiver role but no sender role or edge association. It
has no edge table, so it has `1314` parameters and lower useful work than the
two primary arms. It is deliberately a diagnostic of anonymous compression,
not the capacity-matched causal comparator and cannot by itself establish an
SGSP-specific benefit.

## 4. Exact implicit implementation, permutation, and collision objects

### 4.1 No dense deployed object

For `SGSP-W` and `EDGE-PE`, compute `sum(q_j)` and the count separately for the
two sender roles once, then form the two receiver-role summaries from four
scalar edge coefficients. Apply the relevant receiver summary to every member
of that role. This is `O(2N)` arithmetic and `O(N)` input storage. A dense
`W_ij` may be formed only inside a fixed small reference routine used to check
the implicit result; it is forbidden from the learned forward path, backward
path, evaluator, allocator, or exported checkpoint.

For arm `A in {SGSP-W,EDGE-PE}`, define the complete arm-specific dense
reference

\[
D_i^{A,dense}=\frac1N\sum_j\omega^A_{b_i b_j},\qquad
M_i^{A,dense}=\frac1N\sum_j\omega^A_{b_i b_j}q_j,
\]

\[
Z_i^{A,dense}=M_i^{A,dense}/(D_i^{A,dense}+10^{-12}).
\]

Let `D_i^{A,implicit}`, `M_i^{A,implicit}`, and `Z_i^{A,implicit}` be the
corresponding block-sufficient-statistic outputs, and define

\[
E_{finite}=\max_{A,i}\max\left(
|D_i^{A,implicit}-D_i^{A,dense}|,
\|M_i^{A,implicit}-M_i^{A,dense}\|_\infty,
\|Z_i^{A,implicit}-Z_i^{A,dense}\|_\infty
\right).
\]

The preactivity deterministic fixture and every evaluated seed must have
`E_finite <= 1e-10` in float64. The scalar physical target
`m_i^{dense}` remains a separate simulator object and is never substituted for
`M_i^{A,dense}`. B1 has
`E_graph=||W_runtime-W_frozen||_max=0` by construction. Finite computation
error and graph mismatch are reported separately; neither is interpreted using
a P22 rate.

### 4.2 Identity-permutation replay

For every evaluation world, create one independently sampled nonidentity row
permutation. Permute complete agent tuples `(x,b,u,opaque_handle)` and the
counter-addressed action uniforms together, run the policy, inverse-permute
agent logits and actions, and compare to the canonical order. For every arm,
seed, size, and regime:

```text
max_abs_logit_error <= 1e-10
inverse_permuted_actions_equal = true
team_return_equal = true
```

This is an identity/row-order equivariance condition, not a statistical
endpoint. Cross-role permutations are allowed because the semantic coordinate
travels with the agent tuple. A violation invalidates the learned packet and
returns to CM as technical nonconformance; it is not evidence against SGSP.

### 4.3 Anonymous collision certificate

For each even `N`, define two hand-written worlds. In world A all SCOUT messages
are `+1` and all RELAY messages are `-1`; in world B the signs are swapped. For
either receiver role, the anonymous sender mean is zero in both worlds, yet the
correct graphon field changes from `+0.4` to `-0.4` or vice versa. Therefore
the anonymous input is exactly equal while the legal correct action flips.

This certificate proves only an information loss of anonymous mean compression
on the frozen support extension. It is not performance evidence and cannot
promote SGSP over `EDGE-PE`.

### 4.4 Edge nesting and capability certificate

Before activity, enumerate role-pair residual tables at `-0.20,0,+0.20` and
verify the analytic parameter transform above reproduces each SGSP weight,
summary, actor input, and—under copied common actor weights—logit to `1e-10` in
`EDGE-PE`. A second table with residual `(+1.5,-1.5,-1.5,+1.5)` must produce a
weight table unavailable to SGSP and must change the first raw summary
coordinate on the collision worlds. This establishes nesting and usable extra
edge capacity without a learned outcome.

## 5. Causal semantic reassociation and action sensitivity

`SENDER-ROLE-REASSOC` is an evaluation-only paired intervention. On the same
held-out `OPPOSED` world and checkpoint, replace every sender role at the
aggregation port by `1-b_j`. Leave the receiver's true role input, message
value `x_j`, physical target/reward, opaque handles, row order, action uniforms,
and all learned parameters unchanged. The operation preserves the coordinate
multiset and legal actions but breaks which message is associated with which
semantic block. It is not ordinary row permutation.

The intervention is applied to both `SGSP-W` and `EDGE-PE`. `ANON-MEAN` is
unchanged by construction and is not in the reassociation contrast. For arm
`A`, size `N`, and seed `s`, define

\[
C^A_s(N)=\bar R^{A,intact}_s(N,OPPOSED)
-\bar R^{A,reassoc}_s(N,OPPOSED),
\]

and the paired action sensitivity

\[
T^A_s(N)=\frac1{E N}\sum_{e,i}
\operatorname{TV}(\pi^{A,intact}_{e,i},
                    \pi^{A,reassoc}_{e,i}).
\]

Because actions are binary, TV is the absolute difference in `SERVE_POS`
probability. Define graphon-advantage attenuation

\[
I_s(N)=
[\bar R^{SGSP,intact}_s-\bar R^{EDGE,intact}_s]
-[\bar R^{SGSP,reassoc}_s-\bar R^{EDGE,reassoc}_s].
\]

Reassociation changes a legal actor input and can change a legal action; it is
not credited merely for changing an internal statistic. Graphon-specific
causal attribution requires the registered return, TV, and attenuation gates
in Section 8. A summary change with no action change is nonidentifying.

## 6. Seeds, pairing, evaluation, and atomic evidence

Use exactly 16 training-seed blocks:

```text
4103, 4127, 4153, 4177, 4201, 4229, 4253, 4273,
4297, 4327, 4357, 4387, 4409, 4441, 4463, 4483
```

Within a seed, all arms share initialization tensors for common modules,
training worlds, training action uniforms, evaluation worlds, evaluation
action uniforms, and identity permutations. Arm-specific parameters occupy a
separate counter namespace but start at the same zero values. Training and
evaluation phases are disjoint. Evaluation uses exactly `256` worlds per
`N x regime` cell and no trained checkpoint sees evaluation values before
update 480 is complete.

The seed is the inferential unit; worlds and agents are not replicates. A seed
packet is atomic and valid only if it contains all three arms, four sizes, two
regimes, intact/reassociation panels where defined, identity replay, dense
reference audit, common-support audit, parameter/work/communication ledgers,
checkpoint identity, and finite-value checks. A missing required seed is not
replaced after activity. Efficacy interpretation requires all 16 valid seed
packets. Partial means, best seeds, pooled agents, or pooled worlds are
inadmissible.

## 7. Frozen estimands and interval law

For arm `A`, seed `s`, roster `N`, and regime `g`, let
`mu^A_s(N,g)` be mean intact team return over the 256 evaluation worlds. The
held-out claim cells are

```text
H={(6,SAME),(6,OPPOSED),(16,SAME),(16,OPPOSED)}.
```

For each cell, define paired seed contrasts

\[
d^{GE}_s=\mu^{SGSP}_s-\mu^{EDGE}_s,\qquad
d^{GM}_s=\mu^{SGSP}_s-\mu^{ANON}_s,\qquad
d^{EM}_s=\mu^{EDGE}_s-\mu^{ANON}_s.
\]

For each contrast family, form ordinary equal-seed Student-`t` confidence
intervals with Bonferroni simultaneous two-sided family coverage `95%` across
the four cells: each endpoint uses quantile
`t_{15,1-0.05/(2*4)}`. Zero sample variance yields the algebraic point interval
only if all 16 values are bitwise equal; otherwise a nonfinite or undefined
interval invalidates the family.

The independently chosen material return margin is

```text
delta_R=0.025
```

or 2.5 percentage points of team correctness. It is fixed for this `[0,1]`
one-step endpoint before data and is not inherited from another direction.

Relation labels are:

- `SGSP_MATERIALLY_BETTER`: all four `GE` lower endpoints exceed `+0.025`;
- `EDGE_MATERIALLY_BETTER`: all four `GE` upper endpoints are below `-0.025`;
- `PRACTICALLY_EQUIVALENT`: every `GE` interval lies inside
  `[-0.025,+0.025]`;
- `REGIME_OR_SIZE_INTERACTION`: at least one interval is wholly above
  `+0.025` and at least one is wholly below `-0.025`;
- `UNRESOLVED`: every other configuration.

`SGSP_BEATS_ANON` analogously requires all four `GM` lower endpoints above
`+0.025`. `EDGE_BEATS_ANON` requires all four `EM` lower endpoints above
`+0.025` under the same four-cell two-sided 95% Bonferroni Student-`t` law.
Failure to obtain either anonymous label is nonidentification, not evidence of
equivalence to `ANON-MEAN`. Relation labels do not override hard validity or
causal gates.

### 7.1 Two-sided endpoint availability

Encode `SERVE_POS` as action `1` and select it iff the registered
`u_{s,e,i} < pi(SERVE_POS)`, where `u` is the paired uniform `[0,1)` action
tape. For each seed and held-out cell with `E=256` worlds, define the exact
arm-independent sampled-return support envelope

\[
U_s(N,g)=\frac1{EN}\sum_{e,i}\left[
y_{e,i}\mathbf1\{u_{s,e,i}<0.98\}
+(1-y_{e,i})\mathbf1\{u_{s,e,i}\ge0.02\}\right],
\]

\[
L_s(N,g)=\frac1{EN}\sum_{e,i}\left[
y_{e,i}\mathbf1\{u_{s,e,i}<0.02\}
+(1-y_{e,i})\mathbf1\{u_{s,e,i}\ge0.98\}\right].
\]

Let `bar_U`, `bar_L`, and `bar_mu_EDGE` be equal-seed means over all 16
registered seeds. The material SGSP-positive side is available only if

\[
\bar U(N,g)-\bar\mu_{EDGE}(N,g)>\delta_R,
\]

and the material EDGE-positive reverse side is available only if

\[
\bar\mu_{EDGE}(N,g)-\bar L(N,g)>\delta_R.
\]

Both strict inequalities must hold in every held-out cell for the primary
all-cell relation to be two-sided and identifying. Oracle return `1` is
reported descriptively but is not the admissible policy-family envelope. The
exact anonymous collision pair remains a deterministic support certificate,
not a substitute for this tape-conditioned headroom audit.

If either side is unavailable, the corresponding saturated cell is reported
without converting absence of a material difference into equivalence or family
deletion.

## 8. Mechanism gates

The semantic mechanism family contains three quantities over held-out
`OPPOSED` cells:

```text
min_N C^SGSP(N), threshold 0.075
min_N T^SGSP(N), threshold 0.10
min_N I(N), threshold 0.015
```

For each quantity, first take the minimum over `N={6,16}` within seed. Across
the 16 seeds, form a one-sided lower Student-`t` bound. The three bounds use a
Bonferroni family error `0.05`, hence quantile `t_{15,1-0.05/3}`. All three
lower bounds must exceed their thresholds. These thresholds distinguish a
visible return loss, a nontrivial legal-action probability change, and
attenuation of the SGSP-versus-edge advantage; they are frozen here, not
borrowed.

In addition, every seed must pass:

- common legal support and finite logits/probabilities;
- identity-permutation replay;
- `E_finite<=1e-10` and `E_graph=0`;
- parameter, useful-work, communication, optimizer-opportunity, and input
  equality between `SGSP-W` and `EDGE-PE` in every claim cell;
- the preactivity collision and exact edge-nesting certificates; and
- static absence of opaque handle, row position, held-out `N`, reward, target,
  latent orientation, or future/evaluation statistic from deployed inputs.

Failure of a structural item invalidates the packet. Failure of a stochastic
mechanism bound makes any task-return separation nonidentifying for semantic
graphon causality, but may still motivate a differently defined architecture
only through a new prospective object.

## 9. Resource and communication matching

`SGSP-W` and `EDGE-PE` must be matched exactly, cell by cell, on:

- 1,318 trainable scalars and Adam states;
- the same 64 training worlds per update, 480 updates, and 256 evaluation
  worlds per cell;
- one sender scalar per agent, one public role bit/coordinate per agent, one
  encoder call per row, two block reductions, one shared actor call per agent,
  and two legal action probabilities;
- identical forward/backward module shapes and identical counts of additions,
  multiplications, comparisons, `tanh`, `exp`, division, and reductions; and
- `O(2N)` deployed aggregation time, `O(N)` input storage, constant edge-table
  storage, and zero learned `N x N` objects.

All counted computations are output-relevant. Operation replay must use actual
valid tuples for each of `N={6,8,12,16}` and both regimes, report per-seed and
per-cell values, and obtain a ratio exactly `1` for all matched counts. Immutable
simulator target computation and the dense reference are separately reported
and excluded from deployed-policy work for both arms. `ANON-MEAN` is explicitly
smaller and is not used to establish resource-matched superiority.

No production runtime is authorized by this card. If later released, the CM
must give Root a separate resource proposal/lease request before any
question-relevant run. A B3 generator or row-order utility may be reused, but
this direction requires an isolated evaluator/model path because its dense
simulator reference intentionally conflicts with B3's inherited
`no_nxn_object` contract. The deployed path itself must remain implicit and
linear.

## 10. Scientific-activity boundary and preactivity certificate

Scientific activity begins at the earliest materialization, generation,
inspection, summarization, or use of any registered stochastic object. This
includes a common initialization draw, latent orientation, Gaussian
training/evaluation world, action uniform, identity permutation, or
seed-addressed stochastic policy output.

Provider review, source inspection, hand-written collision worlds, symbolic
nesting calculations, static schemas/leakage review, exact operation formulas,
resource projections, and deterministic arithmetic fixtures or valid tuples
containing no registered stochastic draw remain preactivity. Every arm,
coordinate, kernel, optimizer law, initializer, seed, threshold, endpoint,
support/headroom rule, counter map, and result branch must be frozen before the
first registered stochastic object is materialized. Once activity begins, none
may change in response to values.

Before activity, a CM-owned certificate must establish:

1. literal `N`, role counts, coordinate ties, graphon, self-edge, normalization,
   DGP, target, action, reward, epsilon support, and counter namespaces;
2. exact dense-versus-block equality and no `N x N` object in any deployed
   forward/backward/evaluator path;
3. anonymous collision and exact edge nesting/capability fixtures;
4. policy schemas, parameter arithmetic, initialization pairing, optimizer,
   update schedule, final-checkpoint rule, and common-support law;
5. identity permutation and sender-role-reassociation semantics, including
   which fields move and which remain fixed;
6. static forbidden-input audit and confirmation that B3's old `G-PERMUTE` is
   not substituted for the edge comparator or identity replay;
7. actual valid-tuple work/communication opportunity replay with exact equality
   for the two primary arms in every roster/regime cell; and
8. a fresh atomic result root and a direction-scoped compute proposal that fits
   project limits without construction or launch until separately authorized.

A failed prospective certificate is a feasibility/conformance fact and returns
to the same owner. It is not treatment evidence. CM may repair unchanged
science after release; any science-bearing change requires this EM and a new
complete Pro closure cycle.

## 11. Result-blind interpretation, deletion, and revisit rules

Read every result in this literal precedence order:

1. hard structural validity and complete atomic evidence;
2. two-sided endpoint availability;
3. the mutually exclusive primary `GE` relation;
4. the registered `SGSP_BEATS_ANON` and `EDGE_BEATS_ANON` labels;
5. the semantic return, TV, and attenuation gates; and
6. the catch-all `BOUNDED_NONIDENTIFICATION` rule.

The resulting branches are:

1. **Promote the fixed semantic-graphon family.** Require valid complete
   evidence, two-sided endpoint availability, `SGSP_MATERIALLY_BETTER`,
   `SGSP_BEATS_ANON`, and all three semantic mechanism bounds. The maximum
   reading is a finite-budget benefit of a correct two-block graphon anchor
   over the frozen wider matched edge family on this toy's held-out sizes.
2. **Graphon-specific family deletion after an anonymous diagnostic.** If
   `SGSP_BEATS_ANON` but `EDGE_MATERIALLY_BETTER` or
   `PRACTICALLY_EQUIVALENT` holds with two-sided availability, delete the
   fixed-graphon-specific family. Beating `ANON-MEAN` alone supports only the
   registered anonymous-compression collision/non-sufficiency diagnostic; it
   is not a resource-matched causal topology claim. A generic edge/set family
   may be reconsidered without inheriting an SGSP margin or causal result.
3. **Bounded generic-edge evidence.** If `EDGE_MATERIALLY_BETTER` and
   `EDGE_BEATS_ANON` holds while `SGSP_BEATS_ANON` does not, delete `SGSP-W`
   and record only bounded evidence for this frozen generic role-pair edge
   family. Do not promote a graphon anchor or general topology family.
4. **Action-insensitive or nonattenuating advantage.** If reassociation changes
   an internal summary but the return or TV gate fails, no semantic graphon
   mechanism is identified. If SGSP superiority holds but only attenuation
   fails, the maximum reading is a policy-class/regularization advantage
   without semantic-graphon attribution. Neither case activates the UAV bridge.
5. **Interaction.** `REGIME_OR_SIZE_INTERACTION` may select one prospective
   discriminator targeted to the named regime/size when support is valid. It
   is never averaged into a positive result.
6. **Technical invalidity or incomplete evidence.** Permutation, leakage,
   dense-deployment, lifecycle, or artifact failures return to CM for
   unchanged-science repair when possible. Missing question-relevant data and
   invalid packets are not negative treatment evidence.
7. **Failed endpoint availability.** Saturation is reported without equivalence,
   family deletion, or efficacy interpretation. Revisit only with a prospective
   cell that restores a two-sided material range.
8. **Catch-all bounded nonidentification.** Every otherwise-unlisted complete,
   structurally valid configuration—including `SGSP_MATERIALLY_BETTER` with
   failed anonymous or mechanism requirements, `PRACTICALLY_EQUIVALENT`
   without the registered anonymous condition, and primary `UNRESOLVED`—is
   `BOUNDED_NONIDENTIFICATION`. It authorizes no efficacy promotion, no
   topology-value statement, no threshold change, no seed addition, and no
   automatic rerun.

## 12. Second surface and UAV bridge

A fully attributed B1 positive activates, but does not itself support, one
second surface: a two-dimensional two-zone cooperative surveillance/relay toy.
Agents have observable mission roles and a public sector coordinate along a
monitored perimeter; dense soft couplings represent overlapping sensing fields
and relay/interference reach. One frozen shared policy must train at two fleet
sizes and evaluate at a held-out size. The same strongest edge comparator,
anonymous control, full identity permutation, semantic-coordinate
reassociation, useful-work match, and finite-versus-kernel-mismatch ledger must
be retained. That surface must separately show that its graphon summary changes
`SCAN`, `TRACK`, `RELAY`, or `HOLD`, not merely an internal score.

Only after a positive second surface should the family be mapped to a UAV
simulator: heterogeneous aircraft assigned observable `SCOUT`/`RELAY` roles and
perimeter sectors monitor a wildfire or search boundary while maintaining a
communication chain. The varying axis is fleet size between sorties; dropout
or in-episode churn is a later, separate claim. Observations are local target
uncertainty, battery/link state, mission role, sector coordinate, and received
neighbor messages. Dense physical coupling is soft field-of-view overlap and
link/interference influence. Actions are sense/track/relay/hold or motion
primitives. Candidate benefits are detection/tracking loss, relay success,
energy-normalized task return, and lower-tail mission failure against the
matched edge policy.

This bridge is credible only when the semantic coordinate is observable and
stable, the runtime kernel is validated rather than silently assumed, and
deployment remains implicit/sparse or fixed-block—not a dense `N x N` policy
object. Geometry error, role reassignment, graph mismatch, delayed packets, and
continuous motion are new scientific conditions, not covered by B1.

## 13. Claim ceiling

At maximum, B1 can say:

> In the frozen balanced two-role dense contextual toy, with the correct
> observable semantic block coordinate and one policy shared across training
> `N={8,12}` and held-out `N={6,16}`, a positive role-pair kernel tightly
> constrained around the correct observable two-block graphon produced a
> material, action-sensitive finite-budget return advantage over the frozen
> wider information/capacity/useful-work-matched permutation-equivariant edge
> kernel.

It cannot say the treatment is uniquely expressive or prove that graphon
correctness, rather than generic shrinkage or optimization conditioning, caused
the advantage; there is no equal-width wrong-anchor/alternative-center control.
It also cannot claim asymptotic optimality, an approximate Nash equilibrium,
arbitrary roster size, in-episode churn, graph-mismatch robustness, learned
semantic coordinates or graphons, sparse/heterogeneous graph superiority,
arbitrary role count, or UAV simulation/deployment benefit. P12/P22 rates,
previous direction outcomes, and the proposed bridge never upgrade this
ceiling.
