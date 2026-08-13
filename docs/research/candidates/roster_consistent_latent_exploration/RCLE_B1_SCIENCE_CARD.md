# Roster-Consistent Latent Exploration B1 science card

```text
direction=roster_consistent_latent_exploration
candidate=RCLE-B1
revision=RCLE-B1-SCIENCE-20260813-03
owner=EM_roster_consistent_latent_exploration
scientific_activity_started=false
mathematical_closure=NEW_CHATGPT_EXTERNAL_PRO_CONVERSATION_NOT_AUTHORIZED
external_gemini=NEW_CONVERSATION_NOT_AUTHORIZED
construction_authorization=none
compute_authorization=none
```

## Conclusion first

RCLE-B1 is a meaning-complete, result-blind, direct variable-`N` candidate worth
authoritative mathematical/causal closure. It asks whether a correctly paired
actor-facing information signal organizes an episode-persistent common latent
into several task-valid, roster-adaptive exploration strategies, improving a
fixed four-probe hidden-lock objective after one shared policy is trained at
`N={4,8}` and frozen at held-out `N=12`.

The host deliberately makes roster handling nontrivial. Each agent must infer a
role from its local scalar cue and the cardinality-normalized roster mean, and
then apply one common cyclic rotation. A fixed route distribution that ignores
the roster cannot solve the accepted-roster family merely by becoming more
concentrated at larger `N`. The actor receives no roster count, identity, slot,
padding, raw roster tensor, reward label, or hidden lock.

The strongest comparator, `COMMON-Z`, has the identical common latent, actor,
posterior, observations, samples, updates, parameters, stochastic action law,
and useful work, but the information score never multiplies the actor policy
score. `SHUFFLED-MI` retains the true-label diagnostic posterior and the same
actor-facing coefficient while replacing the paired score by a conditionally
mean-zero random-label score. `INDEPENDENT-ENTROPY` uses the same actor with
episode-persistent private rather than common latents and a per-agent
cardinality-normalized entropy objective with the same maximum auxiliary scale.

Even a complete positive result would show only a finite-budget benefit of
semantic actor-facing information for an already supplied common correlation
device on this exact accepted-roster mean-field toy. It would not prove that
normalization is necessary, that MI is globally optimal, that coordination is
possible without shared randomness, or that the method handles arbitrary `N`,
churn, variable `k`, continuous control, or UAV missions.

No provider send, source construction, stochastic probe, training run, compute
allocation, production action, or Git action is authorized by this card.

## Five-line science card

- **Question.** Does correctly paired, task-valid outcome information make one
  persistent common latent cover several roster-adaptive joint strategies and
  improve hidden-lock discovery at frozen held-out `N=12` beyond common
  randomness or random auxiliary-score exposure?
- **Treatment.** `RCLE`: one shared decentralized actor conditions on an
  episode-common four-valued latent and receives a normalized variational score
  only through the unique valid relative rotation realized by the team.
- **Comparators.** `COMMON-Z` detaches that actor score; `SHUFFLED-MI` replaces
  it by a centered independent-label score while retaining true-pair posterior
  learning; `INDEPENDENT-ENTROPY` replaces the common latent with private
  persistent latents and matched normalized route entropy.
- **Observable.** Frozen `N=12` four-probe hidden-lock success, valid-strategy
  coverage, the `N=4`-anchored latent-to-rotation map at `N=8,12`, task-valid
  information, relative-rotation agreement, and common/persistent-latent cuts.
- **Strongest alternative and ceiling.** A common latent, finite-sample symmetry
  breaking, or coherent optimizer geometry may already suffice; a positive can
  identify only a bounded incremental effect of the registered paired score in
  this toy, not generic variable-roster or UAV superiority.

## 1. Source provenance and evidence boundary

The local corpus motivates ingredients and limits only.

- `P17-CL003` establishes that MAVEN samples a shared latent at episode start
  and conditions decentralized behavior on it for episode-persistent committed
  exploration. `P17-CL004` supplies the variational lower-bound primitive
  `H(Z)+E log q(Z|trajectory)` and explicitly leaves a posterior-gap risk.
- P17's toy and SMAC evidence uses fixed task rosters. It supplies no frozen
  held-out-`N` result, cardinality normalization, or RCLE efficacy.
- `B01-CL003/004` motivates separating scalability, CTDE, parameter sharing,
  and credit assumptions. `B01-CL005` explicitly withholds any conclusion that
  one learned policy generalizes to held-out agent counts. The parameter-sharing
  discussion also warns that identical policies can exclude necessary role
  differentiation unless agents receive valid structural cues.

Repository-relative source locators are:

```text
docs/new-libs/corpus/papers/P17/overview.md
docs/new-libs/corpus/papers/P17/claims.jsonl
docs/new-libs/corpus/papers/P17/chunks/P17-C0004.md
docs/new-libs/corpus/papers/P17/chunks/P17-C0005.md
docs/new-libs/corpus/papers/B01/overview.md
docs/new-libs/corpus/papers/B01/claims.jsonl
docs/new-libs/corpus/papers/B01/chunks/B01-C0052.md
```

The use of a roster mean, relative roles, task-valid outcome statistic,
held-out `N=12`, and every treatment/control below is a new prospective RCLE
hypothesis, not a reported result from P17 or B01.

## 2. Accepted-roster mean-field host

### 2.1 Roster sizes and accepted law

Training uses only `N in {4,8}`, equally weighted by episodes and optimizer
updates. After training, every actor, posterior, preprocessing rule, running
statistic, and hyperparameter is frozen before evaluation at `N=12`.

For one campaign, sample the environment parameter

\[
\Xi\sim\operatorname{Uniform}[0.3,0.7].
\]

Retain this same sampled `Xi` while drawing candidate rosters

\[
X_i\mid\Xi=\xi\stackrel{\mathrm{iid}}\sim
\operatorname{Beta}(8\xi,8(1-\xi)),\qquad i=1,\ldots,N.
\]

For a candidate roster, define the unit-mass empirical mean

\[
\mu_N=\frac1N\sum_{i=1}^N X_i.
\]

The four disjoint, exhaustive relative-role bins are

\[
B_i=\begin{cases}
0,&X_i<\mu_N/2,\\
1,&\mu_N/2\le X_i<\mu_N,\\
2,&\mu_N\le X_i<(1+\mu_N)/2,\\
3,&X_i\ge(1+\mu_N)/2.
\end{cases}
\]

Accept a candidate roster exactly when

\[
A_N=\left\{\max_{b\in\{0,1,2,3\}}
\frac1N\sum_i\mathbf1[B_i=b]\le\frac12\right\}.
\]

Otherwise resample only `X_1:N`, retaining `Xi`, until acceptance. Accepted
agents are exchangeable but not independent; their law is the iid candidate
law conditioned on `A_N`. Redrawing `Xi` after rejection is forbidden because
it would change its marginal differently by roster size. More than 4096
candidate draws for one retained `Xi` stops that registered run incomplete; it
does not redraw `Xi`, weaken `A_N`, or count as algorithm evidence. Storage rows
are independently permuted after acceptance and row order never becomes a
feature.

The rejection rule removes a constant-absolute-route shortcut: because no base
role exceeds one half of the roster, a policy that ignores `(X_i,mu_N)` cannot
make three quarters of agents share one relative rotation merely by choosing
one raw route.

### 2.2 Information boundary

At both decisions, agent `i` receives only:

- its local scalar `X_i`;
- the public cardinality-normalized mean `mu_N`;
- the phase indicator;
- the common latent `Z` in the three common-latent arms, or its private latent
  `Z_i` in `INDEPENDENT-ENTROPY`; and
- its own first action at the second decision.

Every latent is uniform on `{0,1,2,3}` and persists across both decisions. The
actor receives no `N`, raw sum, ID, slot, rank, roster-length tensor, padding,
mask count, other agents' cues/actions, `B_i`, `D_i`, validity, winning
rotation, hidden lock, reward, posterior state, seed, or arm label. The mean is
a genuine zero-message broadcast environmental statistic at decentralized
execution; no centralized actor or agent-to-agent message is claimed.

Centralized training may compute the team outcome and joint policy score. The
deployed actor remains factorized over agents conditional on the public mean
and latent.

### 2.3 Two-step route action and valid relative rotation

Each agent chooses two binary actions. The raw route is

\[
R_i=2A_i^1+A_i^2\in\{0,1,2,3\}.
\]

Its relative rotation and the team fractions are

\[
D_i=(R_i-B_i)\bmod4,\qquad
F_k=\frac1N\sum_i\mathbf1[D_i=k].
\]

The team outcome is valid when

\[
V=\mathbf1[\max_kF_k\ge3/4].
\]

Validity requires at least 3, 6, and 9 agents at `N=4,8,12`. Because `3/4` is
greater than one half, the winning rotation `K*` is unique whenever `V=1`.
Define the semantic trajectory outcome

\[
Y_{\rm sem}=\begin{cases}K^\star,&V=1,\\ \bot,&V=0.\end{cases}
\]

No argmax, tie rule, posterior input, or label exists for an invalid episode.
This prevents subquorum histograms, harmless action-frequency watermarks,
reward, episode length, and count-lattice artifacts from serving as the
actor-facing information channel.

### 2.4 Hidden-lock campaigns and task value

One campaign holds one accepted roster fixed and samples

\[
H\sim\operatorname{Uniform}\{0,1,2,3\}
\]

from an RNG namespace independent of `Xi`, roster proposals, row permutation,
probe order, latent values, action sampling, and optimizer noise. `H` is never
observed by any actor, posterior, baseline, or preprocessing path.

A common-latent campaign contains exactly four frozen-parameter probes, one for
each `Z=0,1,2,3`, in a fresh random order. Each probe uses independent action
uniforms. There is no update, recurrence, hidden state, belief, or reward input
between probes. The episode reward is

\[
R=V\,\mathbf1[K^\star=H],
\]

and the campaign task value is

\[
C=\max_{p=1,\ldots,4}R_p.
\]

For `INDEPENDENT-ENTROPY`, a campaign instead contains four equally charged
probes with fresh iid private latent arrays; it receives no best-of-private
selection or common latent. All four probes still use the same accepted roster
and hidden lock.

For any common-latent probe, averaging over the independent hidden lock gives

\[
E_H[R\mid Z=z]=\tfrac14P(V=1\mid Z=z).
\]

Thus task return rewards task-valid execution but supplies no systematic
preference for which rotation a latent should realize. Campaign value is
exactly the fixed-budget coverage of the four possible locks. Correctly paired
semantic information is the candidate-specific pressure toward distinct valid
rotations.

Training crosses every accepted roster with all four hidden locks and all four
common latent values before one update. Parameters remain fixed throughout
that block. Evaluation uses the identical four-probe campaign meaning without
updates.

## 3. Shared actor and common work

Every arm uses one parameter-shared stochastic actor. Its 11-scalar input is

```text
[X_i, mu_N, X_i-mu_N,
 phase_1, phase_2,
 previous_action_available,
 signed_previous_action_or_zero,
 one_hot_latent_0..3]
```

and its exact network is

```text
Linear(11,32) -> tanh -> Linear(32,32) -> tanh -> Linear(32,2).
```

The two output logits define the temperature-one binary categorical law. At
phase one, the previous-action fields are zero. At phase two,
`previous_action_available=1` and the signed value is `-1` or `+1`. This is
1,506 trainable actor scalars. There is no critic, recurrent state, per-`N`
head, normalization state, or deterministic deployment selector. Frozen
evaluation continues to sample the same categorical law; greedy decoding and
best-checkpoint selection are forbidden.

All arms also contain a parameter-disjoint `4 x 4` posterior-logit table
`q_phi(z|K*)`. Invalid outcomes use the exact fixed posterior `1/4` and do not
update the table. Every arm computes route entropy, true-label posterior loss,
semantic scores, validity, rotations, and all diagnostics. Corresponding actor
and posterior tensors start byte-identically within a paired seed. Arms differ
only in latent coupling and which already computed auxiliary scalar enters the
actor update.

## 4. Treatment and comparators

### 4.1 `RCLE`

All agents receive the same uniform episode latent `Z`. With natural logarithms,
define the normalized true-pair score

\[
s_\phi(z,k)=1+\frac{\log q_\phi(z\mid k)}{\log4}.
\]

The actor-facing semantic information term is

\[
B_{\rm RCLE}=V\,s_\phi(Z,K^\star).
\]

Equivalently, fixing `q(z|bot)=1/4`, its unnormalized expectation is the
variational lower bound

\[
\log4+E\log q_\phi(Z\mid Y_{\rm sem})\le I(Z;Y_{\rm sem}).
\]

It is deliberately a lower bound on the augmented valid/invalid semantic
outcome, not a claim of conditional MI given validity. It can reward
latent-specific validity. A mechanism-positive interpretation therefore also
requires each latent to be valid and the `N=4`-anchored four-rotation map to
persist at `N=8,12`; a high posterior score alone never qualifies.

### 4.2 `COMMON-Z`

`COMMON-Z` has the identical common latent, actor, posterior, posterior update,
task reward, samples, batching, parameters, computations, and RNG namespaces.
Its actor score contains task return only:

\[
B_{\rm COMMON}=0.
\]

The true-pair posterior is still trained and reported diagnostically, but it is
parameter-disjoint and neither its value nor gradient multiplies or enters the
actor score. This contrast isolates actor-facing semantic information beyond
the supplied common correlation device.

### 4.3 `SHUFFLED-MI`

`SHUFFLED-MI` retains the same common latent and trains its posterior on the
true `(Z,K*)` pairs exactly as RCLE. After a rollout, draw
`Z_tilde ~ Uniform{0,1,2,3}` independently of every realized trajectory field.
Define

\[
a_\phi(k)=\frac14\sum_{j=0}^3s_\phi(j,k)
\]

and the centered random-label actor score

\[
B_{\rm SHUFFLED}=V\,[s_\phi(\widetilde Z,K^\star)-a_\phi(K^\star)].
\]

Conditional on the complete rollout, this score has exactly zero expectation.
It retains the same coefficient, posterior computations, stochastic
actor-score path, and auxiliary noise without becoming the active
anti-information penalty produced by an uncentered uniform wrong-label
average. It is a control for centered random auxiliary-score exposure, not an
exact match to RCLE's coherent gradient norm or geometry. That residual
optimizer alternative remains in the claim ceiling.

### 4.4 `INDEPENDENT-ENTROPY`

Each agent receives an iid uniform private latent `Z_i` that persists across
its two actions. The identical actor architecture and one-hot input are used.
For state `S_i=(X_i,mu_N,Z_i)`, define its exact autoregressive route entropy

\[
\mathcal H_i=H(A_i^1\mid S_i)
+E_{A_i^1}H(A_i^2\mid S_i,A_i^1)=H(R_i\mid S_i).
\]

The actor auxiliary is

\[
B_{\rm INDEP}=\frac1{N\log4}\sum_i\mathcal H_i.
\]

It lies in `[0,1]`, so the same numerical coefficient gives the same maximum
episode-level auxiliary contribution as RCLE. Entropy is averaged, never
summed, over agents. A uniform dummy probe label in `{0,1,2,3}`, excluded from
the actor and environment, supplies the same detached posterior-table update
and table work; all common arms compute the same detached entropy work. This
arm is a capacity/work-matched full-package benchmark for persistent private
exploration. It cannot isolate the common-latent factor by itself.

## 5. Frozen learning law

Paired algorithm seeds are

```text
[1103,1217,1321,1451,1553,1693,1789,1877,1999,2081,2179,2293].
```

Each arm and seed receives exactly 2,000 optimizer updates. One update contains
one accepted roster at each training size, all four hidden locks, and four
probes per lock: 16 episodes at `N=4` and 16 at `N=8`. Hidden-lock order, probe
order, and action uniforms are counter-keyed and paired where their semantics
match. There is no replay, checkpoint choice, validation tuning, early stop,
sweep, curriculum, or later adjustment.

For episode `e`, let

\[
G_e=\sum_{i=1}^{N_e}\sum_{t=1}^2
\nabla_\psi\log\pi_\psi(A_{e,i}^t\mid O_{e,i}^t)
\]

be the exact joint policy score and let

\[
\log P_e=\sum_{i=1}^{N_e}\sum_{t=1}^2
\log\pi_\psi(A_{e,i}^t\mid O_{e,i}^t).
\]

For `RCLE`, `COMMON-Z`, and `SHUFFLED-MI`, define the sampled actor scalar

\[
T_e=R_e+\beta B_e,\qquad \beta=0.10,
\]

using the arm's exact `B_e` from Section 4 (`B_COMMON=0`). One complete
32-episode block uses the minimized surrogate

\[
L_{\rm actor}^{\rm common}
=-\frac12\sum_{n\in\{4,8\}}\frac1{16}
\sum_{e:N_e=n}\operatorname{sg}(T_e-c_{n,z_e})\log P_e.
\]

The stopped scalar produces the exact score-function estimator
`sg(T_e-c) G_e`; neither `K*`, validity, posterior values, nor shuffled labels
is pathwise differentiated through the sampled environment.

`INDEPENDENT-ENTROPY` does **not** insert its differentiable entropy into a
stopped score multiplier. Its complete minimized block loss is

\[
L_{\rm actor}^{\rm indep}
=-\frac12\sum_{n\in\{4,8\}}\frac1{16}
\sum_{e:N_e=n}\left[
\operatorname{sg}(R_e-c_n)\log P_e
+\alpha B_{{\rm INDEP},e}
\right],\qquad\alpha=0.10.
\]

Thus its task term uses REINFORCE and its exact autoregressive route entropy is
differentiated analytically through both binary policy distributions. There is
no sampled entropy score and no stop-gradient on `B_INDEP`. This difference is
the mathematically correct gradient of the declared entropy objective and is
part of the comparator definition; numerical coefficient equality does not
claim identical gradient geometry.

There is no extra `1/N` on `G_e`: the joint policy likelihood is a product over
agents, so its log score is a sum. The independent arm's entropy itself is
already normalized by `N`.

Each arm owns action-independent exponential-moving-average baselines initialized
to zero. `RCLE`, `COMMON-Z`, and `SHUFFLED-MI` use buckets indexed by the causal
pre-action `(N,Z)`; `SHUFFLED-MI` never indexes a bucket by `Z_tilde`.
Immediately after its actor step, each populated bucket is updated from the
same block's four hidden-lock episodes by

\[
c_{n,z}\leftarrow0.95c_{n,z}+0.05\,
\operatorname{mean}_{e:N_e=n,Z_e=z}T_e.
\]

For `SHUFFLED-MI`, `T_e` includes its centered sampled random-label scalar;
for `COMMON-Z`, `T_e=R_e`. The independent arm has one bucket per roster size
and, after its actor step, updates

\[
c_n\leftarrow0.95c_n+0.05\,
\operatorname{mean}_{e:N_e=n}R_e.
\]

Entropy never enters that baseline target. Every baseline value and update
target is stopped and baselines have no optimizer parameters. Actor Adam uses
learning rate `1e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay,
global gradient-norm clip `1.0` on the complete arm-specific loss above, and
one update per complete 32-episode block.

The posterior used to score update `u` is the pre-update table. After the actor
step, each arm updates its own posterior once by the equal-roster loss

\[
L_q=-\frac12\sum_{n\in\{4,8\}}\frac1{16}
\sum_{e:N_e=n}V_e\log q_\phi(Z_e\mid K_e^\star).
\]

The independent arm substitutes its detached dummy probe label. There is no
renormalization by the random number of valid episodes. Posterior Adam uses
learning rate `1e-2`, the same betas/epsilon, no weight decay, gradient clip
`1.0`, and one update per block. Every posterior is initialized uniformly.

All affine actor weights use Xavier-uniform initialization with tanh gain and
all biases are zero. PCG64 counter namespaces separately address environment
parameters, roster proposals, row permutations, hidden locks, common/private
latents, probe order, actor sampling, shuffled labels, initialization, and
evaluation. An action, rejection, or arm divergence never shifts another
namespace.

## 6. Oracle, shortcut references, and headroom

The scripted roster-adaptive codebook

\[
R_i=(B_i+Z)\bmod4
\]

is valid for every accepted roster and gives `K*=Z`. Its four-probe campaign
value is exactly one for every hidden lock and every `N in {4,8,12}`. It proves
task, action, relative-role, and campaign headroom but is never a learner input
or training label.

The scripted coherent-collapse reference `R_i=B_i` is valid but realizes only
rotation zero. Its expected four-probe campaign value is exactly `1/4`.
Therefore the host distinguishes coherent execution from strategy coverage.

A fixed route that ignores `(X_i,mu_N)` cannot reach the `3/4` relative-rotation
threshold on an accepted roster by constant-action majority. An iid uniform
private-route reference has high marginal route entropy but no common relative
rotation; its exact finite-`N` validity probability is computed by enumeration
or dynamic programming and reported, not assumed.

Before learned activity, the common host gate must reproduce the scripted
codebook and collapse values at all three sizes, accept both primitive actions
at both phases, verify all four hidden locks and rotations, demonstrate exact
row-permutation invariance of host outcomes, show that no forbidden field
reaches the actor/posterior, and show a nonempty accepted-roster panel for each
size. Gate rosters and learner states are discarded.

## 7. Evaluation and inference

Every final actor and posterior is frozen. Each seed and arm receives 2,048
fresh campaigns at each `N in {4,8,12}`, with exactly 512 campaigns per hidden
lock. Common arms use every latent once per campaign; the independent arm uses
four fresh private-latent arrays. There are no updates, recurrent campaign
memory, selected latents, greedy decoding, or evaluation-based checkpoint or
hyperparameter choice.

For every seed, arm, and roster report:

- campaign task value `C` and per-probe return;
- per-latent valid rate and mean winning agreement `F_K*`;
- distinct valid rotations per four probes and hidden-lock discovery;
- the normalized variational bound for `I(Z;Y_sem)` and posterior accuracy;
- the complete `P(K*=k,V=1|Z=z)` matrix;
- action sensitivity to `X_i`, `mu_N`, and latent;
- actual route/relative-rotation histograms and invalid/tie counts;
- host rejection draws and the retained `Xi` marginal; and
- exact episodes, agent decisions, optimizer updates, parameters, work, and
  anomalies.

For each seed, the `N=4` campaigns are split before looking at outcomes. Within
each hidden-lock stratum, campaign indices `0..255` form the anchor half and
indices `256..511` form the scoring half. Thus each half contains exactly 1,024
campaigns, 256 per hidden lock, and every common latent appears once in every
campaign. The split is fixed by counter index and does not consume extra
episodes.

Use only the anchor half to choose

\[
m_{s,z}=\arg\max_k\widehat P_{s,\mathrm{anchor}}
(K^\star=k,V=1\mid Z=z,N=4)
\]

for seed `s`. A fixed numeric rotation order resolves a tie for reporting, but
any tied row fails the mechanism gate. The four-row map must also be a
bijection in every seed. Neither `N=8` nor `N=12` may be used to select or
realign it.

For every seed, latent, and roster size, define the anchored valid-semantic
fidelity

\[
U_{s,z,N}=\widehat P_s(V=1,K^\star=m_{s,z}\mid Z=z,N).
\]

At `N=4`, `U` is estimated only on the scoring half; at `N=8,12`, it uses all
2,048 campaigns. Also report

\[
S_{s,N}=\frac14\sum_zU_{s,z,N}.
\]

These quantities report whether every latent remains valid and realizes its
same `N=4`-anchored relative rotation. The anchor/scoring split prevents the
anchor selection data from also proving `N=4` fidelity, and a provider or
analyst may not relabel each roster independently.

Two frozen-checkpoint mechanism cuts use the same evaluation campaigns:

1. `PRIVATE-LATENT-CUT` replaces the common `Z` of a trained RCLE actor by iid
   agent latents while preserving each one-agent latent marginal.
2. `TEMPORAL-LATENT-CUT` keeps the first-decision common latent but draws a new
   common latent for the second decision.

They are evaluation-only functional interventions. Their task-value losses
diagnose dependence on cross-agent coupling and temporal persistence; they do
not prove natural mediation.

Seeds, not campaigns, are the independent units. For a paired contrast, let
`d_s` be the seed's mean campaign-value difference at `N=12`. Under the stated
independent Normal seed-effect model, use a one-sided Student-`t` bound with 11
degrees of freedom. The direct algorithm-positive branch requires all three
Bonferroni one-sided `98.333333%` lower bounds for

```text
RCLE-COMMON-Z
RCLE-SHUFFLED-MI
RCLE-INDEPENDENT-ENTROPY
```

to exceed the prospective material margin `0.10` in campaign task value.
Mechanism attribution additionally requires:

- every `N=4` anchor row to have a unique empirical maximizer and the resulting
  map to be a bijection in every seed;
- for all 12 registered `(z,N)` cells, `z in {0,1,2,3}` and
  `N in {4,8,12}`, the one-sided Student-`t` lower bound across the 12 seed
  values `U_{s,z,N}` to exceed `0.70`; these 12 bounds use a Bonferroni
  familywise one-sided level of 95%, hence each marginal bound is
  `99.583333%` with 11 degrees of freedom;
- the one-sided 95% lower bound for intact-minus-`PRIVATE-LATENT-CUT` task value
  to exceed `0.10`;
- the corresponding lower bound for intact-minus-`TEMPORAL-LATENT-CUT` to
  exceed `0.05`;
- finite posterior diagnostics with no direct/invalid shortcut; and
- exact row-permutation outcome invariance and common support/headroom.

These model-based bounds are prospective finite-seed inference, not
distribution-free guarantees. A no-material-effect conclusion for one contrast
requires its one-sided 95% upper bound to be below `0.05`; failure of both the
positive and no-material bounds is unresolved, not equivalence or failure.

## 8. Activity, completeness, and resource ceiling

Question-relevant scientific activity begins only after the complete common
host/oracle/information gate is durably retained and the first full paired
four-arm optimizer block has updated all actors at both training roster sizes.
A source file, import, unit check, generated roster, partial gate, process
launch, posterior-only update, or incomplete arm block is preactivity.

A conclusion requires all 12 paired seeds, 2,000 complete training blocks per
arm, all frozen evaluation campaigns and cuts, finite outputs, the same source
revision and hyperparameters, and no evaluation leakage. Partial output is not
a result and does not support a negative mechanism conclusion.

The registered upper bound is 3,072,000 two-step training episodes plus
1,179,648 ordinary two-step evaluation episodes across all arms and seeds. The
two RCLE-only functional cuts add 589,824 episodes; at most 8,000,000 two-step
episodes are allowed including all gates and diagnostics. The run class is one
CPU worker, at most 2 GiB peak memory and 45 wall minutes. This is a prospective
resource ceiling, not a runtime claim. A breach returns to CM incomplete and
never changes scientific conditions automatically. No run is authorized in the
current stage.

## 9. Frozen interpretation branches

1. **Held-out value plus registered mechanism.** All three primary comparisons,
   semantic alignment, common/persistent cuts, validity, completeness, and
   shortcut controls pass. Retain RCLE as a bounded variable-`N` candidate and
   conclude only that the paired task-valid outcome score organized an already
   supplied common latent into roster-adaptive strategies that improved this
   toy's fixed-budget hidden-lock value. Return the complete result to this EM
   and the same ChatGPT External Pro conversation for convergence before any
   second surface.
2. **Package value without semantic-MI attribution.** RCLE beats the controls
   but the anchored map, posterior restriction, or coupling/persistence cuts do
   not pass. Report only the bounded package effect; do not name normalized MI
   or persistent correlation as the identified cause.
3. **Common randomness is sufficient.** `COMMON-Z` is not materially below RCLE
   and beats the private package while the no-material upper bound closes.
   Delete actor-facing MI from the useful primitive; retain at most the simpler
   common-latent hypothesis for a separately chosen successor.
4. **Random-score explanation.** `SHUFFLED-MI` is not materially below RCLE.
   Correct latent/outcome pairing is not identified; coherent versus random
   optimizer geometry remains the strongest explanation. Do not retain the
   semantic-MI claim.
5. **Independent exploration matches.** `INDEPENDENT-ENTROPY` is not materially
   below RCLE. The full correlated-exploration package has no demonstrated task
   advantage on this assay.
6. **Modes without value.** RCLE produces a stable four-rotation codebook but
   does not improve hidden-lock campaign value. Report organized diversity
   without demonstrated task value and do not advance the exact package.
7. **Training-size success, held-out failure.** The anchored map or value is
   present at `N=4,8` but absent at `N=12`. Cardinality-normalized inputs did not
   yield the protected held-out-size benefit; no variable-`N` claim is allowed.
8. **Oracle headroom but no valid learned behavior.** All learned arms remain
   invalid while the scripted codebook passes. The finite-budget optimization
   question is nonidentified; this is not evidence against representability or
   the general latent family.
9. **Invalid/incomplete.** Any forbidden information path, failed oracle gate,
   missing arm/seed, evaluation adaptation, nonfinite field, changed `Xi`
   rejection law, or resource terminal with incomplete output supports no
   scientific comparison.
10. **Bounded no-effect.** Only the exact package/control pair whose registered
    no-material upper bound closes may be described as lacking a material effect
    on this finite assay. It never deletes persistent-latent exploration in all
    environments.

## 10. Claim ceiling

The maximum positive language is:

> On the frozen accepted-roster relative-role toy, one shared stochastic policy
> trained at `N={4,8}` and evaluated without adaptation at `N=12` used a
> correctly paired task-valid outcome-information score to organize an
> episode-common four-valued latent into several `N=4`-anchored relative
> rotations, and this improved fixed four-probe hidden-lock success over the
> identical common-latent detached-score and centered random-label controls as
> well as the matched private-entropy package.

This does not establish that cardinality normalization is necessary or uniquely
correct, that the variational bound equals true MI, that every latent is useful
outside the registered campaign, that RCLE is asymptotically optimal, or that
the registered controls match every possible optimizer geometry. It does not
support arbitrary `N`, a continuous range of counts, membership churn, variable
`k`, learned termination, dense communication, safety, 2-D transfer, simulation
performance, UAV value, or real-flight claims.

## 11. Prospective second surface and UAV bridge

A complete mechanism-positive B1 would activate, but not validate, a separate
continuous 2-D four-sector search/relay surface. Homogeneous vehicles start at
random positions along a staging arc. Each observes its normalized along-arc
coordinate and the broadcast fleet centroid, from which a roster-relative base
sector is defined. A sortie-persistent common latent rotates those base sectors
among four fork/relay plans. One hidden target sector per four-sortie campaign
rewards a plan only when at least three quarters of the fleet reaches its
relative sector while maintaining collision and relay constraints. One shared
controller trains at two fleet sizes and freezes at a larger held-out size.

That surface must retain `COMMON-Z`, centered `SHUFFLED-MI`, a private-entropy
benchmark, equal four-sortie budgets, relative-strategy diagnostics, and common/
temporal latent cuts. It must add continuous dynamics, local range/bearing,
collision separation, link geometry, energy, and a strong continuous-control
baseline. Only a qualifying 2-D result could motivate a UAV simulator card for
occluded canyon ingress, cooperative sensing, or relay-route selection. B1
provides no evidence about any such surface.

## 12. Current owner handoff

The same-direction CM may now inspect exact revision
`RCLE-B1-SCIENCE-20260813-03` for constructability, hidden ambiguity, and static
cost only. It must not construct a stochastic treatment or run a probe under
the current envelope. Any science-bearing ambiguity returns directly to this
EM. A technically feasible card returns to Root as a decision milestone because
RCLE needs two new, separate provider conversations: one ChatGPT External Pro
conversation for authoritative mathematical closure and one mutually blind
Gemini innovator conversation. Their prepared requesters are independent files;
neither has send authority.
