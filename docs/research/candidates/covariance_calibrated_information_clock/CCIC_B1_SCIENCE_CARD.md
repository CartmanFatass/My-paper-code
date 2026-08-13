# CCIC B1 science card

```text
direction=covariance_calibrated_information_clock
revision=CCIC-B1-SCIENCE-20260812-04
supersedes_revision=CCIC-B1-SCIENCE-20260812-03_PRO_REVISION_REQUIRED
owner=EM_covariance_calibrated_information_clock
object=result-blind prospective B1 discriminator
scientific_activity_started=false
mathematical_closure=revision_04_PREPARED_NOT_SENT
cm_release=withheld
production_authorization=none
chatgpt_external_pro=PREPARED_NOT_SENT
external_gemini=PREPARED_NOT_SENT
```

## Conclusion first

This revision freezes a small, causal test of a distinct algorithm family: a
lineage-aware, covariance-calibrated information clock used by one
decentralized shared policy across roster size `N` and externally imposed skill
period `k`. The decisive test is not generic mean-field pooling. It asks whether
the clock assigns zero *new information value* to a successfully received
literal retransmission, assigns increasing information to partially correlated
and conditionally independent new origins, and converts that distinction into
better sense/relay/commit timing at held-out `N` and/or held-out `k`.

The frozen first discriminator contains an analytic HMM/GLS Bayes object as a
theory-only ceiling and a separately named numerical reference as teacher. The
deployed path is decentralized: every agent receives the same abstract packets
through a matched one-round all-gather,
computes the same fixed-rank sufficient statistics locally, runs the same
shared actor, and executes its own action. No deployed arm receives a privileged
global covariance matrix or centralized inference result.

The strongest alternative is simpler lineage-aware unique-origin counting, or
a sufficiently expressive replication-safe set encoder, rather than learned
covariance. If a frozen equivalence or reverse-superiority rule favors either,
the corresponding extra covariance or analytic-clock machinery is deleted.
Nothing in this card authorizes CM,
construction, tests, training, evaluation, provider contact, or production.

## Five-line science card

- **Question.** Under a frozen Gaussian cooperative sense/commit process, does
  a learned covariance-calibrated clock cause one shared decentralized policy
  to ignore literal retransmissions yet exploit new correlated/independent
  origins on held-out `N` and/or `k`?
- **Treatment.** `CCIC-R1`: quotient immutable evidence lineage, learn a
  diagonal-plus-rank-one conditional residual covariance, compute distributed
  GLS increments `(q_hat, J_hat)`, propagate belief in physical time, and feed
  those quantities to the one shared frozen actor.
- **Comparators.** A capacity/exposure/work-matched nonlinear replication-safe
  set encoder (`RI-STRONG`), an information-matched flexible calibration head
  (`INFO-FLEX`), a scalar equicorrelation effective-sample-size arm
  (`ESS-SCALAR`), and a lineage-deduplicated independence/count arm
  (`ORIGIN-COUNT`), with numerical-reference, received-count, mean-pooling, and shuffled-clock
  diagnostics.
- **Observable.** Paired normalized error-delay-sensing loss, numerical-reference excess loss,
  posterior log score/Brier score, `J` ordering, exact-copy equivalence, action
  sensitivity to information, and inference/communication exposure across the
  frozen `2 x 2` train and `3 x 3` evaluate grid.
- **Strongest alternative and ceiling.** A positive result may still be a
  provenance-counting or flexible set-learning effect. At maximum, B1 supports
  a causal timing benefit in this frozen toy on only the held-out axes and
  comparator boundaries that pass; it cannot establish universal information
  estimation, general MARL coordination, arbitrary-`N`/`k` robustness, or UAV
  benefit.

## 1. Scientific object and nonclaims

### 1.1 Target distinction

The elementary information unit is one physical sensing draw, identified for
the whole episode by `origin_key=(origin_id,capture_tick)`, not a received
packet. Every agent keeps the same episode-persistent set of assimilated keys.
A key enters the Bayes update at most once; a later relay of that key has
increment `(Delta q,Delta J)=(0,0)`. A 32-bit origin ID may identify lineage
across time, while capture tick distinguishes fresh physical draws. Two cases
with the same received values and packet count can therefore
require opposite precision updates:

- `DUPLICATE`: rows carry the same immutable origin ID and the same captured
  random variable. They are literal copies and add no likelihood factor after
  the first successful receipt.
- `INDEPENDENT_REPEAT`: rows carry distinct origin IDs and were separate
  conditional draws. Even if their represented values happen to be equal, each
  likelihood factor is valid and information adds.

Equality of represented values is never a duplicate rule. Provenance is an
execution-visible input in this toy. Without trustworthy lineage, the two cases
are not identifiable and the exact-copy claim must be deleted.

### 1.2 Transport boundary

Copy invariance is conditional on matched successful receipt, latency,
available sufficient-origin set, topology, consensus rounds, packet size, and
bandwidth contention. Here `packet size` means the frozen one-real-symbol plus
64-metadata-bit accounting unit, not a finite encoding of the scalar.
Retransmission may legitimately improve delivery
reliability or reachability in another environment. B1 tests information-value
invariance after receipt, not general communication-value invariance.

### 1.3 Result-blindness and theory boundary

No direction result is an input to this object. The local `docs/new-libs`
corpus supplies background mechanisms and claim boundaries only; it is not
experimental evidence for CCIC. In particular, parameter sharing, mean-field
approximations, and message information bottlenecks do not establish learned
duplicate rejection, one frozen policy across held-out `N`, or variable skill
period `k`.

## 2. Frozen cooperative process

### 2.1 Physical time and latent state

An episode has primitive physical ticks `t = 0,...,30`. The hidden task state is

\[
Y_t\in\{-1,+1\},\qquad P(Y_0=+1)=1/2,
\]

and independently at every primitive transition

\[
P(Y_{t+1}=-Y_t)=q_f=0.04.
\]

The externally supplied skill period is constant within an episode. Training
uses `k in {1,3}` and evaluation adds held-out `k=5`. A nonterminal team action
chosen at `t` occupies exactly `k` primitive ticks and the next decision occurs
at `t+k`. At `t=30`, or whenever fewer than `k` ticks remain, only commit
actions are legal.

### 2.2 Roster and evidence regimes

Training uses `N in {2,5}` active agents and evaluation adds held-out `N=8`.
Roster membership is constant within B1. Every `SENSE` block ends with one
abstract packet row per active agent. Conditional on the new hidden state
`Y_{t+k}`, the delivered real-valued evidence has signal gain `mu=0.75` and
unit marginal residual variance.

The evidence regime and its overlap code are public episode context from
`t=0`; the realized covariance and hidden state are not public. The three
equally weighted evidence regimes are:

1. `DUP` (`rho=1`, literal copy): draw one origin
   \(Z=\mu Y+\epsilon_0\), then deliver `N` packet rows with the same origin ID
   and exactly the same represented value. The unique-origin count is `M=1`.
2. `CORR` (`rho=0.5`): deliver `M=N` distinct origins
   \[
   Z_i=\mu Y+\sqrt{0.5}\,C+\sqrt{0.5}\,\epsilon_i.
   \]
3. `IND` (`rho=0`): deliver `M=N` distinct origins
   \[
   Z_i=\mu Y+\epsilon_i.
   \]

All `C`, `epsilon_0`, and `epsilon_i` are standard normal and independent across
capture ticks unless the equations explicitly share them. A scalar observed
overlap code `o in {1,0.5,0}` and an observed quality value `s=1` accompany
each packet. `o` is exogenous metadata whose relation to covariance must be
learned; it is not an oracle covariance matrix.

This is the complete Stage-1 correlation family. `DUP` tests exact lineage
quotienting, `CORR` tests nonbinary covariance calibration, and `IND` tests
sensitivity to genuinely new evidence. The exact analytic information table is

| `N` | `J_DUP` | `J_CORR` | `J_IND` |
|---:|---:|---:|---:|
| 2 | 0.5625 | 0.75 | 1.125 |
| 5 | 0.5625 | 0.9375 | 2.8125 |
| 8 | 0.5625 | 1.0 | 4.5 |

Thus `DUP<CORR<IND` at every training and held-out roster, not merely at
`N=5`.

### 2.3 Packet and consensus law

The Stage-1 statistical channel is idealized: each packet contains one
noiseless mathematical real scalar `z`, a 32-bit immutable origin ID, a 16-bit
capture tick, an 8-bit overlap code, and an 8-bit validity/check field. The
fixed public quality value `s=1` is episode context and is not transmitted.
Communication is therefore accounted as **one real scalar symbol plus 64
metadata bits per row**, not as a literal finite-bit encoding of a Gaussian
random variable. B1 makes no bit-rate, rounding, quantization, or finite-word
channel claim. Every arm uses this identical abstract packet and accounting
unit.

At each decision epoch, every agent sends one packet through a complete-graph,
one-round all-gather; every successful row is delivered to every agent.
Receipt is deterministic in B1. A `RELAY` action resends the last row with the
original origin ID and capture tick; before any sense it sends a valid null
row. A relay creates no new evidence origin.
The assimilated-key ledger is updated only after a valid new composite key is
incorporated and is identical at all agents under deterministic receipt.

All arms receive the identical packet table, masks, lineage, `o`, `t`, `k`, and
public action random number. All arms have one fusion call and one actor call
per agent per decision. No arm obtains future packets, rewards, hidden state,
oracle statistics, or held-out normalization at execution.

### 2.4 Decentralized actions and joint support

Every agent has the same local action set

```text
{SENSE, RELAY, COMMIT_MINUS, COMMIT_PLUS}
```

and the same actor parameters for every agent, `N`, `k`, and evidence regime.
After all-gather, every agent independently reconstructs the same sufficient
summary and actor logits. A common public uniform variate selects a common plan,
so the joint support consists of the four diagonal joint plans in which all
active agents execute the same named action. At nonterminal states the deployed
law is `(1-0.02)*softmax(logits) + 0.02/4`; at terminal states it is the same
mixture restricted and renormalized over the two commit signs. Thus all arms
have exactly the same legal joint-action support.

Commit terminates the episode. Let `tau` be its physical tick, `S` the number
of sense blocks, `R` the number of relay blocks, and `Y_tau` the hidden state at
commit. Team loss is

\[
L=1\{\widehat Y\ne Y_\tau\}+0.20\,\tau/30+0.02S+0.01R,
\qquad L_{norm}=L/1.8.
\]

The team return is `-L`. This reward and every action cost are common to all
agents and arms. The primitive horizon, potential evidence tape, legal support,
and costs are held fixed within a pair; realized delivery histories may differ
after arms choose different actions.

## 3. Analytic Bayes/GLS teacher and ceiling

### 3.1 Unique-origin likelihood

For one capture batch with `M` unique origins,

\[
Z\mid Y\sim N(Yh,\Sigma),\qquad h=\mu\mathbf 1,
\]

where

\[
\Sigma=(1-\rho)I+\rho\mathbf 1\mathbf 1^T
\]

for `CORR` and `IND`, while `DUP` is quotiented to `M=1`. Define

\[
q=h^T\Sigma^{-1}Z,\qquad J=h^T\Sigma^{-1}h.
\]

Then the observation log-likelihood ratio is `2q` and

\[
J=\frac{\mu^2 M}{1+(M-1)\rho}.
\]

For a prior log odds `ell`, a no-observation transition across `k` physical
ticks is

\[
\ell^-_{t+k}=2\operatorname{atanh}\left((1-2q_f)^k
\tanh(\ell_t/2)\right),
\]

and a sense update is `ell_(t+k) = ell^-_(t+k) + 2q`.

### 3.2 Singular duplicate law

Let `A` be an `N x M` replication map with exactly one `1` per row and at
least one `1` per column. Therefore `A` has full column rank. If `X=AZ`,
`Omega=A Sigma A^T`, `Sigma` is positive definite, the mean is `AYh`, and the
distribution is interpreted on its actual support `col(A)`, then

\[
A^T(A\Sigma A^T)^+A=\Sigma^{-1}.
\]

Consequently

\[
(Ah)^T\Omega^+X=q,\qquad (Ah)^T\Omega^+(Ah)=J.
\]

The likelihood on `col(A)` uses the Moore-Penrose inverse and
pseudodeterminant. Adding an off-support nugget to each copied row changes the
model and is forbidden: it would manufacture fictitious independent evidence.
If the received vector is not on `col(A)`, if lineage is inconsistent, or if a
column has no received representative, this identity does not apply and the
packet set is invalid rather than silently regularized.

### 3.3 Analytic Bayes object and numerical reference

The mathematical Bayes object uses the exact HMM update, true covariance, and
the Bellman integral under `L`. Its continuation expectation is the
one-dimensional Gaussian-mixture expectation induced by the next `q`. This
analytic object defines the ideal decision problem but is not claimed to be
computed with a certified uniform error bound.

The centralized computed arm and labeler is therefore named
`NUMERICAL-REFERENCE`, never `ORACLE`. Its frozen fine construction uses a
log-odds grid `[-24,24]` at spacing `0.005`, 128-node Gauss-Hermite quadrature,
float64 value arrays, linear interpolation, and endpoint clipping to `-24` or
`+24`. At every state, minimize action value. Values within absolute `1e-12`
are tied and resolved by the total priority

```text
SENSE > RELAY > COMMIT_PLUS > COMMIT_MINUS
```

after removal of illegal actions. Thus the terminal tie at `ell=0` chooses
`COMMIT_PLUS`; no hidden random tie rule enters labels.

Before activity, compare it against a coarse construction on `[-16,16]` at
spacing `0.01` with 64-node quadrature. On every coarse-grid state, the fine
interpolated action values must differ by at most `1e-4`, and every action whose
coarse gap exceeds `1e-12` must retain its minimizer. Otherwise no training or
stochastic evaluation begins. Passing is only a numerical-stability contract;
it does not turn either grid into the exact Bellman oracle or supply a uniform
tail/interpolation theorem.

`NUMERICAL-REFERENCE` supplies deterministic labels on the frozen state grid
below and receives a complete evaluation rollout as a centralized reference.
No behavior-policy rollout generates its label states. No deployed arm calls
the dynamic program, reads true `rho`, or receives a reference posterior or
action.

## 4. Shared actor, treatment, and arms

### 4.1 One frozen shared actor

For each training seed, one actor is trained once from numerical-reference states and
then frozen and reused unchanged by every deployable arm. Its five inputs
are clipped posterior log odds `ell/16`,
`log(1+J_next)/log(5.5)`, `t/30`, `(30-t)/30`, and `k/5`. The architecture is
`5 -> 32 -> 32 -> 4` with SiLU activations. It is trained for exactly 1,500
Adam updates, batch size 128, learning rate `1e-3`, betas `(0.9,0.999)`, epsilon
`1e-8`, no weight decay, on exactly 9,216 label states: 768 from each of the
12 training `(N,k,rho)` cells. There is no centralized
critic and no arm-specific actor fine-tuning.

The 768 states in each cell are the exact Cartesian product of `j=0,...,23`
and `m=0,...,31`. Let `T_k=floor(30/k)`. Their physical tick and prior log odds
are

\[
t_{k,j}=k\left\lfloor\frac{(j+1/2)T_k}{24}\right\rfloor,
\qquad \ell_m=-15.5+m.
\]

The cell's true prospective `J_next` completes each label state. The target is
the one-hot action selected by the fine `NUMERICAL-REFERENCE` under the total
tie priority above. Actor loss is mean categorical cross-entropy over the 128
minibatch rows. There is no rollout behavior policy, outcome filtering, state
selection, or adaptive relabeling.

The expected-next-information input is computed by each arm from a public
metadata-only template for the next batch: public regime, roster, expected
origin lineage pattern, overlap code, and quality, with represented values set
to zero. It never uses a future realized measurement. This makes the first
decision well-defined and gives every arm the same prospective information.

At execution, each agent locally runs this actor on the arm's reconstructed
belief and expected information from one additional `SENSE` block. The
numerical reference is therefore a centralized teacher/reference, not the
deployed actor; the analytic Bayes object remains a theory-only ceiling.

### 4.2 `CCIC-R1` treatment

Agents quotient the current table by composite `origin_key`, reject
inconsistent same-key payloads, and remove every key already in the persistent
assimilated ledger. Only remaining new keys update belief; relay-only tables
have zero likelihood and information increment. A shared covariance network
receives only `(o,s)` and has
architecture `2 -> 16 -> 2` with SiLU, exactly 82 trainable scalars. For unique
row `i`, its two raw outputs are explicitly named `(a_i,b_i)` and it emits

\[
d_i=10^{-4}+\operatorname{softplus}(a_i),\qquad
u_i=\operatorname{softplus}(b_i).
\]

Let `D=diag(d_1,...,d_M)` and `u=(u_1,...,u_M)^T`. It constructs on
the unique-origin set

\[
\widehat\Sigma=D+uu^T.
\]

The network cannot see represented evidence values, received roster count,
unique-origin count, duplicate multiplicity, `t`, `k`, reward, action, future
data, or evaluation statistics. It is trained only from labeled training-cell
residuals `r=Z-mu*Y` using Gaussian residual negative log likelihood.

At every action interval, CCIC first applies the exact known-`q_f` HMM
transition for elapsed physical `k`, then adds `2*q_hat` only for new keys.
`J_hat` is the current batch's Fisher-information increment and the prospective
next-batch actor input; it is never summed across latent-state transitions as
if it were posterior precision for a static state. Every comparator applies the
same physical-time transition before its declared evidence update.

For rank one, every agent obtains the same GLS result from five additive sums

\[
S_1=\sum d_i^{-1},\quad S_z=\sum z_i/d_i,\quad
S_u=\sum u_i/d_i,\quad S_{uz}=\sum u_i z_i/d_i,\quad
S_{uu}=\sum u_i^2/d_i,
\]

then computes

\[
\widehat q=\mu\left(S_z-\frac{S_uS_{uz}}{1+S_{uu}}\right),\qquad
\widehat J=\mu^2\left(S_1-\frac{S_u^2}{1+S_{uu}}\right).
\]

No matrix or global classifier is transmitted. Each agent computes the row
parameters and sums from the same received table. Cholesky/Woodbury operations
must remain positive definite; invalid or nonfinite outputs fail closed.

### 4.3 Deployable comparators

1. **`ESS-SCALAR`.** Quotient lineage, fit one marginal variance and one
   nonnegative equicorrelation per observed overlap code by the same residual
   likelihood, and use
   \[
   \widehat q=
   \frac{\mu\sum_{i=1}^{M}z_i}
        {\widehat\nu[1+(M-1)\widehat\rho]},\qquad
   \widehat J=
   \frac{\mu^2M}
        {\widehat\nu[1+(M-1)\widehat\rho]},
   \]
   so `n_eff=M/[1+(M-1)\widehat\rho]` is only a derived report. The Gaussian
   likelihood uses
   `Sigma_hat=nu_hat[(1-rho_hat)I+rho_hat*11^T]` on unique rows. For code `o`,
   `nu_hat_o=1e-4+softplus(alpha_o)`. For `CORR` and `IND`,
   `rho_hat_o=0.999*sigmoid(beta_o)`; `rho_DUP` is fixed to zero after lineage
   quotienting. The three `alpha` and two `beta` values are exactly five
   trainable scalars. This is the simplest
   covariance-aware alternative and is exact for the homogeneous Stage-1
   family.
2. **`RI-STRONG`.** Quotient lineage, map each unique `(z,o,s)` through a
   `4 -> 7 -> 4` SiLU encoder on `(z,o,s,log M)`, mean-pool, append `t/30` and
   `k/5`, and use a `6 -> 2` linear head. The first raw output `g_delta`
   represents the invertible target `asinh(Delta ell/8)` and is decoded as
   `Delta ell_hat=8*sinh(g_delta)` with no clipping. The second gives
   `J_hat=1e-4+softplus(raw_J)`. It has exactly 81 trainable scalars versus
   CCIC's 82 and can represent interactions between value and unique-origin
   count. It receives the same packets and has the
   same update count, batch size, optimizer, initialization family, and
   hyperparameter-search budget. This is the primary
   information/capacity/exposure/work-matched nonlinear baseline; a mean-only
   ablation is never the strongest comparator.
3. **`INFO-FLEX`.** Reuse the frozen CCIC covariance estimator and give its
   `(ell_minus,q_hat,J_hat,k)` to a `4 -> 11 -> 2` SiLU head with 79 additional
   scalars. Its first raw output `g_ell` is decoded as posterior log odds
   `8*sinh(g_ell)` and its second is converted to positive information by
   `1e-4+softplus`. It replaces the
   analytic HMM/LLR calibration with a flexible learned mapping. Because it has
   extra capacity, it is an intentionally advantaged diagnostic. CCIC can make
   an analytic-calibration claim only if its frozen primary advantage interval
   rule also passes against this arm.
4. **`ORIGIN-COUNT`.** Quotient lineage, assume unique origins are conditionally
   independent with unit variance, and use `q=mu*sum(z)` and `J=mu^2*M`. This is
   the strongest simple provenance-count/dedup explanation.

Every learned fusion arm uses exactly 1,500 Adam updates, batch size 64,
learning rate `3e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay, and
the same 9,216 labeled snapshots, 768 per training cell. There is one frozen
configuration and no adaptive hyperparameter search. `RI-STRONG` minimizes the
equal-weight mean of squared errors for `asinh(Delta ell/8)` and
`log(1+J_hat)/log(5.5)` against the corresponding exact GLS targets.
`INFO-FLEX` represents posterior log odds with the same invertible transform,
`ell_hat=8*sinh(g_ell)`, and minimizes equal-weight squared errors for
`asinh(ell_posterior/8)` and normalized positive `J`. There is no target
clipping before either inverse. Nonfinite decoded values fail closed.

For every training cell, the fusion snapshot bank uses the same 768
`(j,m)` rows as the label grid, with row index `r=32*j+m`. Cell index `c` is
lexicographic in ascending `N`, ascending `k`, then
`DUP,CORR,IND`. Row parity fixes `Y=(-1)^(j+m)`; its unique
residual vector is generated from the declared training-snapshot Philox stream
and the cell's exact `rho`, then `Z=mu*Y+r`. For fusion targets, `ell_m` is the
pre-action posterior; apply the exact `k`-tick HMM map to obtain `ell_minus`,
then use `Delta ell=2q` and `ell_posterior=ell_minus+2q`. `CCIC` and
`ESS-SCALAR` fit the
per-snapshot unique-origin residual loss

\[
\tfrac12\{\log\det\widehat\Sigma+
r^T\widehat\Sigma^{-1}r+M\log(2\pi)\}.
\]

`RI-STRONG` and `INFO-FLEX` use the targets
above. Training order is `CCIC`, `ESS-SCALAR`, `RI-STRONG`, `INFO-FLEX`, then
the actor; the completed CCIC estimator is frozen before the INFO-FLEX head is
trained. Each batch loss is the arithmetic mean in ascending batch-slot order.
All parameters, forward/backward values, reductions, and Adam state are
float64. They use numerical-reference or exact analytic targets only in
training; no target or reference value is available at execution.

At execution, RI-STRONG sets the post-batch belief to
`ell_minus+Delta ell_hat`; its prospective actor information is its second
output on the public zero-valued next-batch template. INFO-FLEX uses its decoded
posterior output for the observed batch. For prospective actor information it
evaluates the same frozen head on `(T_k(ell_current),0,J_hat_template,k)` and uses
only the second output; the unused posterior output cannot enter the actor.
CCIC and ESS use their analytic declared maps. Every arm applies the same exact
physical-time HMM transition before its batch-specific map, and no arm receives
a future realized value.

### 4.4 Diagnostics, not superiority baselines

- `NUMERICAL-REFERENCE`: the frozen fine HMM/GLS DP teacher/reference above;
  it is not labeled an exact oracle.
- `RECEIVED-COUNT`: treats every received row as independent, exposing count
  inflation.
- `MEAN-RI`: mean-pools represented values without unique-origin count,
  exposing the replication collision.
- `J-SHUFFLE`: at fixed `(seed,k,t,episode)` orders the nine `(N,rho)` metadata
  classes lexicographically and rotates their CCIC `J_next` values by one
  class. This breaks the information/context assignment while preserving the
  balanced evaluation-wide marginal `J` distribution. Shuffling within a cell
  is forbidden because Stage-1 `J_next` is deterministic from metadata and such
  a shuffle would be a no-op.
- `J-CLAMP`: replaces CCIC `J_next` by its training-cell grand mean.

Diagnostics cannot satisfy a superiority claim. If either `J-SHUFFLE` or
`J-CLAMP` fails its frozen lower-bound degradation rule, the information-clock
causal claim is unsupported on that axis.
`NUMERICAL-REFERENCE`, `J-SHUFFLE`, and `J-CLAMP` receive complete paired rollouts.
`RECEIVED-COUNT` and `MEAN-RI` are restricted to the collision/shadow tables and
do not add environment trajectories.

## 5. Replication-collision family falsifier

Before outcome evaluation, construct two legal shadow packet tables with
`N=5`, represented value `z=+0.75` in every row, the same tick, packet accounting, and
successful receipt:

- `COLLIDE-DUP`: all five rows carry one origin ID and `o=1`.
- `COLLIDE-IND`: the five rows carry five distinct origin IDs and `o=0`.

The first demands `M=1`, `q=0.5625`, and `J=0.5625`; the second demands
`M=5`, `q=2.8125`, and `J=2.8125` under the analytic GLS law. This audit is a contract
state, not a claim about the probability of exact equality under a continuous
distribution. Treating equal values as copies fails the audit. Treating the
same lineage five times as five likelihood factors also fails it.

A second shadow family fixes `N=5` and traverses `rho={1,0.5,0}`. The required
analytic ordering is `0.5625 < 0.9375 < 2.8125`. Passing only the endpoints
supports binary deduplication, not covariance calibration.

The temporal collision fixture first assimilates key `(7,5)` with value
`+0.75`, then delivers the same key/value at the next decision; its required
increment is exactly `(0,0)`. A paired fresh-evidence fixture instead delivers
the equal value under key `(7,10)` with `o=0`; it must receive one new
independent likelihood factor.

## 6. Train/evaluate axes, tapes, and counts

### 6.1 Factorial

The training support is the full `2 x 2` cross

```text
N_train = {2,5}
k_train = {1,3}
rho_family = {DUP, CORR, IND}
```

After all weights and normalization constants are frozen, evaluate the full
`3 x 3` grid

```text
N_eval = {2,5,8}
k_eval = {1,3,5}
```

at all three evidence regimes. The held-out-`N` surface is `N=8,k in {1,3}`;
the held-out-`k` surface is `k=5,N in {2,5}`; `(8,5)` is the jointly held-out
corner. No cell-specific retraining, threshold, temperature, normalization,
rank, or policy is permitted.

### 6.2 Seeds and paired tapes

There are exactly 32 training-seed blocks. Block `b=0,...,31` uses master seed
`1009 + 7919*b`. Each block generates one actor and one instance of every
learned fusion arm. Evaluation uses exactly 256 episodes per
`(N,k,rho)` cell and arm, all paired within seed block.

Randomness uses counter-addressed `Philox4x32-10`. Its 64-bit key is the
seed represented as `(low32(seed),high32(seed))`; training and evaluation use
the block's master seed, while inference uses the fixed seed `8675309`. Its four unsigned 32-bit
counter words are `(phase,stream,item,address)`. One addressed call returns four
words. A uniform is `(word+0.5)/2^32`; a standard normal is the inverse standard
normal CDF of that uniform. Only lane zero is used unless a rule explicitly
requests another lane. All ranges below are disjoint, so no logical draw is
reused.

The phase words are `1=TRAIN_SNAPSHOT`, `2=TRAIN_OPT`, `3=EVAL`, and
`4=INFERENCE`. Within `TRAIN_SNAPSHOT`, streams are `11=common residual` and
`12=idiosyncratic residual`; `item=768*c+r` for lexicographic training-cell
index `c=0,...,11` and row
`r=0,...,767`; common residual uses `address=physical_tick*16` and
idiosyncratic residual uses `address=physical_tick*16+origin_index`. Within `EVAL`, streams
are `1=Y0`, `11=latent flip`, `13=common residual`, `17=idiosyncratic residual`,
and `19=public action uniform`; `item=episode in {0,...,255}` and `address=0`
for `Y0`, `physical_tick` for scalar streams, or
`physical_tick*16+origin_index` for idiosyncratic residuals. `Y0=+1` iff its
uniform is at least `0.5`; each flip occurs iff its uniform is below `q_f`.

No evaluation address contains `N`, `k`, `rho`, or arm. `N` selects a nested
source prefix, `k` selects reachable physical ticks, `CORR` mixes common and
idiosyncratic base normals, `IND` uses only idiosyncratic normals, and `DUP`
reads origin zero and replicates it. Thus all axes transform one potential tape
and arm order never changes a draw. Training and evaluation cannot collide
because their phase words differ.

Within `TRAIN_OPT`, `stream=29` initializes parameters and `stream=23` selects
minibatches. Module IDs are `0=CCIC`, `1=ESS-SCALAR`, `2=RI-STRONG`,
`3=INFO-FLEX`, and `4=actor`. Initialization uses
`item=module_id,address=parameter_index` in row-major layer order. Every linear
weight uses Glorot uniform
`[-sqrt(6/(fan_in+fan_out)),+sqrt(6/(fan_in+fan_out))]`; every bias is exactly
zero, as are all standalone ESS raw scalars. Adam first/second moments are
exactly zero. For minibatch slot `s`, use
`item=module_id*1500+update,address=s` and index
`floor(9216*U)` with replacement. Updates are numbered `0,...,1499`; slots are
`0,...,63` for fusion modules and `0,...,127` for the actor. `INFERENCE` uses
only stream `31` for the 100,000 bootstrap resamples, with
`item=resample,address=slot`; it maps `floor(32*U)` to a common seed-block index
for every contrast family. No training or evaluation draw uses that phase.

There is no adaptive stopping. All 32 seed blocks are required. A missing or
invalid block is reported and no efficacy conclusion is drawn; it is not
replaced after scientific activity. Engineering repair before activity may
preserve this exact science object, but any science-bearing change returns to
this EM.

Thirty-two seeds are a resource-bounded Stage-1 choice, not an assertion of
prospective 80% power for the `0.02` smallest effect. The simultaneous interval
itself is the precision gate: if its upper bound is not below `-0.02`, the
population-advantage relation is unresolved unless the separately defined
lower-bound rule excludes such a material advantage. No branch may translate a
wide interval into equivalence or evidence of no effect.

### 6.3 Exposure and work matching

Within a cell and tape, all arms have identical potential tapes, packet schema,
transition/receipt rules, legal support, public-uniform rule, per-decision call
opportunity, horizon, and reward accounting. Realized histories and call counts
may differ endogenously after actions or commit. `CCIC-R1` and `RI-STRONG`
differ by one trainable scalar (82 versus
81), receive exactly the same 1,500 updates and samples, and have no search
variants. Their measured per-decision scalar-operation count and peak temporary
state must be reported per call and cumulatively per episode. A common offline
potential-state replay calls both fusions on the exact multiset

```text
{(seed,N,k,rho,episode,t):
 seed=0..31, every 27 evaluation cells, episode=0..255,
 t in {0,k,2k,...,30-k}}
```

using the potential packet table at that tuple even if an arm would already
have committed. Every tuple has weight one; no cell, episode, action, or
observed outcome reweights the multiset. Report the median scalar-operation
count over all calls and maximum temporary scalar count. A primary superiority
claim is unavailable if either CCIC or RI-STRONG exceeds the other's median by
more than 10%, or if either fails under the same valid input; that comparison
is exposure-confounded. Online total calls and operations are endogenous timing
outcomes, charged by the loss and reported rather than forced equal.

The exposure audit must also show that duplicate multiplicity, received `N`,
future values, reward, held-out-cell moments, and actor outputs cannot enter the
CCIC covariance network. Unique-set dimension affects only the declared sums.

## 7. Observables and inference

### 7.1 Endpoints

For every seed and cell report:

- mean `L_norm` and paired excess loss relative to `NUMERICAL-REFERENCE`;
- posterior negative log score and Brier score at every decision and commit;
- physical commit tick, sense count, relay count, and task error rate;
- predicted `q`, `J`, unique count, received count, and analytic-GLS discrepancy;
- actor plan probabilities, selected plan, packet accounting units, inference calls,
  scalar-operation count, and peak temporary state;
- exact-copy collision outputs and `rho`-ordering outputs.

Training seeds, not episodes or ticks, are the inferential replicates.

### 7.2 Quantitative covariance-calibration panel

Before task returns are read, evaluate CCIC on a fixed shadow panel. For each
seed and each `(N,rho)` in `{2,5,8} x {DUP,CORR,IND}`, use the first potential
`SENSE` batch ending at tick `k` from all 256 evaluation episodes and each
`k in {1,3,5}`, for 768 batches. After lineage quotienting, compare against the
true unique-origin covariance, `q`, and `J`. Define

\[
E_{diag}=\max_i|\widehat\Sigma_{ii}-1|,
\quad
E_{off}=\begin{cases}
0,&M=1,\\
\max_{i\ne j}|\widehat\Sigma_{ij}-\rho|,&M>1,
\end{cases}
\]

\[
E_J=|\widehat J/J-1|,
\qquad
E_q=\sqrt{\frac{1}{768J}\sum_{b=1}^{768}
(\widehat q_b-q_b)^2}.
\]

A seed passes a cell only if all four errors are at most `0.10`. It passes the
calibration panel only if all nine cells pass and its learned information is
strictly ordered `J_DUP<J_CORR<J_IND` separately at every `N in {2,5,8}`.
The overall gate passes only if at least 29 of 32 seeds pass and the
equal-seed mean of each of the 36 named cell-error quantities is at most
`0.10`. Every seed and pooled quantity is reported; no failing cell can be
averaged across roster sizes or correlation classes. This is an empirical
metadata-conditioned covariance/GLS calibration requirement over the tested
family, not a claim for arbitrary covariance.

### 7.3 Primary held-out contrasts

For each comparator in
`{RI-STRONG, INFO-FLEX, ORIGIN-COUNT}`, define paired seed-level
differences `d = mean(L_norm_CCIC - L_norm_comparator)` on:

1. held-out `N`: equal average over `N=8`, `k in {1,3}`, and all three regimes;
2. held-out `k`: equal average over `k=5`, `N in {2,5}`, and all three regimes.

This creates six prespecified primary contrasts. For any contrast vector
`d_1,...,d_32`, use mean `dbar`, sample standard deviation
`s=sqrt(sum_b(d_b-dbar)^2/31)`, and `SE=s/sqrt(32)`. Generate exactly 100,000
common nonparametric seed-block resamples from inference seed `8675309`. For
each family and draw, resample the complete contrast vector with the same 32
indices, center by the original contrast mean, recompute its bootstrap sample
standard deviation, and form the centered studentized statistic. The draw's
max-`T` is the maximum absolute statistic over that family's contrasts. The
critical value is sorted draw number 95,000 in ascending one-indexed order;
the simultaneous two-sided interval is `dbar +/- critical*SE`.

If an original contrast has zero observed seed variance, that contrast is
`INFERENCE_UNRESOLVED` and cannot support superiority, equivalence, reverse
superiority, deletion, or a no-material conclusion. It is not assigned a point
interval and is omitted from the other contrasts' maximum. If a bootstrap
standard error is zero for a nonzero-variance original contrast, that draw's
absolute statistic is `+infinity`, conservatively making the family unresolved
if it enters the 95th percentile.

A primary contrast supports a population advantage of at least the `0.02`
SESOI only when its simultaneous upper bound is strictly below `-0.02`.
Equivalence requires the entire interval inside `[-0.005,+0.005]`; reverse
superiority of the comparator requires the lower bound strictly above `+0.02`.
Every other pattern is unresolved for those relations. An axis-level CCIC claim
requires the primary advantage rule against all three comparators on that axis.
The jointly held-out `(8,5)` corner uses a separately reported three-contrast
family with the same convention and remains secondary; it cannot rescue either
primary axis.

For the result-blind covariance-specificity branch, retain the three regime
components of each primary contrast. For each comparator and axis define

```text
s = d_IND - (d_DUP+d_CORR)/2.
```

The six `s` contrasts form their own simultaneous two-sided max-`T` family.
“Uniform advantage including IND” is available only when, on a supported axis,
all three comparator-specific `s` intervals lie wholly inside
`[-0.005,+0.005]`. Otherwise uniformity is unresolved; non-rejection is not
uniformity. This family diagnoses attribution and cannot create primary support.

`ESS-SCALAR` is a prespecified co-treatment/reduction test, not an arm that the
rank-one parameterization must outperform in the homogeneous family where the
scalar formula is exact. On each axis, report the paired CCIC-minus-ESS
difference with a simultaneous two-sided interval and equivalence margin
`[-0.005,+0.005]`. Equivalence, or ESS reverse superiority defined by a lower
bound above `+0.02`, triggers the scalar-deletion
branch; it does not erase support for the broader covariance-calibrated clock
when the primary advantage rules pass against the non-covariance alternatives.
The two ESS reduction contrasts form their own two-sided max-`T` family with
the same 100,000 paired-seed bootstrap resamples.

For each of `J-SHUFFLE` and `J-CLAMP`, define two paired diagnostic contrasts as
`mean(L_norm_diagnostic-L_norm_CCIC)` on the same held-out-`N` and held-out-`k`
surfaces. The four contrasts form one two-sided max-`T` family under the same
construction. A diagnostic supports clock causality only when its simultaneous
lower 95% bound is strictly above `+0.01`. Failure by either diagnostic
on an otherwise positive axis removes the clock-causality claim for that axis.

### 7.4 Exact-copy equivalence family

For CCIC, compare `N=5` and `N=8` against `N=2` under `DUP`, separately for the
two training `k` values. Successful support requires the two-sided 95%
simultaneous intervals for paired `L_norm` differences to lie inside
`[-0.005,+0.005]`, using the same max-`T` construction over four equivalence
contrasts. In addition, `q`, `J`, and actor probabilities on the paired
post-receipt shadow states must agree within absolute `1e-10`. This is an
information-value equivalence claim under matched receipt, not a transport
claim.

### 7.5 Mechanism gates

All of the following are required before any efficacy claim:

1. lineage collision audit passes both `COLLIDE-DUP` and `COLLIDE-IND`;
2. learned `q` and `J` are invariant to literal duplicate multiplicity, and the
   full quantitative covariance-calibration panel passes at every
   `N in {2,5,8}`;
3. the actor has reward-independent information sensitivity as defined below;
4. `J-SHUFFLE` and `J-CLAMP` each have a simultaneous lower degradation bound
   strictly above `+0.01` on the relevant held-out surface;
5. paired packet, inference, capacity, search, and work conditions pass;
6. the numerical reference itself separates the information regimes in expected loss. This
   is a deterministic preactivity feasibility check: at the initial belief,
   `N=5,k=3`, both the coarse and fine frozen DP constructions must give
   expected
   `L_norm_NUMERICAL_REFERENCE(DUP)-L_norm_NUMERICAL_REFERENCE(IND) >= 0.01`.
   Each term is the corresponding construction's own value at
   `(t=0,ell=0,N=5,k=3,rho)`, divided by `1.8`; no rollout estimate enters.
   If either does not, no training or stochastic evaluation starts. This check
   is not empirical evidence for a learned arm and is not called an exact
   oracle result.

Structural collision, support, packet, and forbidden-input checks must pass for
every arm and all 32 seeds; a missing/nonfinite value is a failure. Learned
calibration and actor-activity gates use their explicit 29-of-32 plus pooled
rules. Work uses the literal replay multiset. Inferential claims use only the
simultaneous seed-level intervals. No majority, pooled average, or task return
may override a failed hard structural gate.

## 8. Preactivity certificate and activity criterion

### 8.1 Required certificate before scientific activity

The owner-prepared implementation may not consume a training label, reward, or
evaluation tape until a machine-readable certificate shows:

- the DGP constants, axes, loss, seed formula, stream keys, counts, and stop
  rule equal this revision;
- the ideal-real statistical channel and one-real-symbol-plus-64-metadata-bit
  accounting are used without a finite-word Gaussian likelihood claim;
- the analytic `J` values above and the singular replication-map identity hold
  under the stated support conditions;
- the two collision tables produce their exact analytic GLS values;
- all packet schemas, legal joint supports, actor calls, and packet accounting units
  match across arms;
- static feature tracing proves the CCIC covariance network cannot receive
  forbidden multiplicity, future, reward, held-out, or actor-output inputs;
- the coarse/fine numerical-reference stability check passes, and the frozen
  state/snapshot grids, losses, targets, counter namespaces, initialization,
  reductions, update order, and minibatch mapping equal this revision;
- the fine numerical reference has at least 24 eligible information-sensitive base states among
  the 96 base `(t,k,ell)` states formed by `t in {5,10,15,20}`,
  `k in {1,3,5}`, and the eight signed values generated from
  `abs(ell) in {0.25,0.75,1.25,1.75}`. Each base state is evaluated at all three
  frozen `N=5` values `J_next in {0.5625,0.9375,2.8125}`, for exactly 288
  actor evaluations;
- all output roots are fresh and the projected bound is no more than 90 wall
  minutes, 4 GiB peak RSS, 8 CPU threads, 240,000 learned optimizer updates,
  and 60 million primitive environment ticks.

The resource ledger is literal: eight arms receive full rollouts
`{CCIC,ESS,RI-STRONG,INFO-FLEX,ORIGIN-COUNT,NUMERICAL-REFERENCE,J-SHUFFLE,J-CLAMP}`, for a
worst-case `32*27*256*30*8 = 53,084,160` evaluation ticks. The shared snapshot
bank adds at most `32*9,216 = 294,912` one-tick draws; 288 shadow evaluations
per seed and offline work replay remain below the 60-million ceiling. Learned
updates are exactly `32*(one actor + four learned fusion modules)*1,500 =
240,000`. `RECEIVED-COUNT` and `MEAN-RI` have shadow-only evaluations.

These checks are feasibility/contract checks, not evidence that CCIC works.

### 8.2 When scientific activity begins

Question-relevant scientific activity begins at the earliest of:

1. the first optimizer update using a generated training label, residual, or
   numerical-reference target from this DGP;
2. the first actor/fusion evaluation on a frozen stochastic train or evaluation
   tape; or
3. the first computation of a result-bearing endpoint from such data.

Pure schema tests, hand-written collision constants, symbolic identities, and
resource projection before those events are preactivity.

### 8.3 Reward-independent activity gate

After training but before reading task return, evaluate the 96 frozen base
shadow states at the three analytic `N=5` values
`J_next in {0.5625,0.9375,2.8125}` (288 actor evaluations per seed).
The eligible set `E` is fixed once, before training, as the base states where
the fine numerical-reference plan differs between endpoint `J_next` values;
the preactivity rule requires `|E|>=24`. For each seed report the two
numerators below over denominator `|E|`. Also pool over the exact denominator
`32*|E|`; every seed has equal weight. At least 29 of 32 seeds and the pooled
counts must both satisfy: at least 80% obey

```text
P(SENSE | J_IND) >= P(SENSE | J_CORR) >= P(SENSE | J_DUP)
```

within `1e-8`, and at least 25% have
`P(SENSE | J_IND)-P(SENSE | J_DUP) >= 0.10`. The estimator must also satisfy
the full quantitative calibration panel, including `J_DUP < J_CORR < J_IND`
at every tested `N`. Failure means the proposed clock was not materially
active/calibrated; returns cannot answer the causal question. Missing or
nonfinite actor probabilities count as failures, never as removed denominators.

## 9. Result-blind interpretation map

1. **Both-axis specific support.** All mechanism/work/equivalence gates pass;
   CCIC meets the primary advantage interval rule against all three comparators
   on both held-out axes. Support is limited to covariance-calibrated timing in
   this toy across the tested `N` and `k` values.
2. **One-axis support.** The full rule passes only for held-out `N` or only for
   held-out `k`. Claim only that axis; do not say the algorithm spans both.
3. **Covariance-aware but not analytic-specific.** CCIC passes every mechanism
   and calibration gate and its primary advantage rule passes against
   `RI-STRONG` and `ORIGIN-COUNT` on an axis, but its interval versus
   `INFO-FLEX` lies inside `[-0.005,+0.005]` or has lower bound above `+0.02`.
   Support the bounded covariance-aware timing family on that axis, not the
   analytic calibration mapping. If the INFO-FLEX relation is neither
   equivalence nor reverse superiority, analytic specificity is unresolved.
4. **Scalar reduction supported.** The simultaneous CCIC-minus-ESS interval is
   wholly inside `[-0.005,+0.005]`, or its lower bound is above `+0.02`, on the
   relevant axis. Delete learned low-rank fusion for the homogeneous surface
   and retain the scalar clock for the next discriminator. Any other failure to
   show CCIC superiority is unresolved, not scalar sufficiency.
5. **Flexible set encoder reduction supported.** The primary simultaneous
   CCIC-minus-RI interval is equivalent or its lower bound exceeds `+0.02`, and
   work matching passes. Structured covariance advantage is unsupported;
   prefer the replication-safe set learner unless a heterogeneous second
   surface is answer-changing. Otherwise `RI-STRONG` merely not being beaten is
   unresolved.
6. **Counting reduction supported.** The primary simultaneous CCIC-minus-count
   interval is equivalent or its lower bound exceeds `+0.02`. Retain provenance
   quotienting and delete covariance calibration on that surface. If only
   exact-copy invariance passes while `CORR` calibration/order fails, binary
   deduplication alone is supported and covariance calibration is falsified;
   counting is not declared sufficient without the interval rule.
7. **Numerical reference separates, estimator fails.** Both frozen reference
   constructions pass their preactivity gap and exhibit information-sensitive
   plans, but learned CCIC fails calibration/activity. The estimator is the
   failed object; the analytic information-clock principle remains unresolved.
8. **Numerical reference fails.** Either frozen numerical construction fails
   the preactivity expected-loss separation. Stage 1 lacks a verified
   information-timing discriminator and stochastic work does not start. This is
   not a theorem that the exact Bayes object has no separation.
9. **Clock not causal.** Either `J-SHUFFLE` or `J-CLAMP` fails to have a
   simultaneous lower degradation bound above `+0.01`, or return changes
   without calibrated `J`. No covariance-information causal claim.
10. **Exposure explanation.** A packet, capacity, inference-opportunity, or
    work gate fails. No primary superiority interpretation is available;
    attribute any raw difference to an unresolved exposure/work alternative,
    not covariance.
11. **Core falsification.** Literal duplicate multiplicity changes CCIC `q`,
    `J`, action probabilities, or paired loss beyond the equivalence boundary,
    or independent equal-valued origins are collapsed. Reject this revision's
    information-value invariance.
12. **Activity failure or incomplete seeds.** No efficacy interpretation,
    regardless of observed return. Repair only through the proper scientific or
    engineering owner route.
13. **Held-out threshold not met.** If the simultaneous interval overlaps
    `-0.02`, report the held-out relation as unresolved. Only a simultaneous
    lower bound strictly above `-0.02` excludes a population advantage of at
    least the `0.02` SESOI against that comparator; call this "no material CCIC
    advantage at the frozen threshold," not equivalence or general no effect.
    Trained-cell improvement alone is interpolation and never supports
    variable-`N` or variable-`k` robustness.
14. **Uniform advantage including `IND`.** On a supported axis, all three
    specificity intervals lie inside `[-0.005,+0.005]`. Retain the primary
    task relation but delete correlation-specific performance attribution and
    investigate representation, optimization, or posterior temperature. If
    the specificity family is not equivalent, uniformity is unresolved.

## 10. Strongest alternative, deletion map, and claim ceiling

### Strongest alternative

Trusted lineage plus unique-origin count may contain all useful structure in
this toy; alternatively, `RI-STRONG` may learn the relevant conditional
precision without an explicit covariance model. Both are scientifically
stronger explanations than a mean-pooling-only comparison. `INFO-FLEX` is the
strongest explanation for any apparent benefit attributed specifically to the
analytic clock mapping.

### Deletion map

- Delete low-rank covariance only if the frozen ESS equivalence or
  reverse-superiority interval rule passes.
- Delete covariance calibration only if the frozen ORIGIN-COUNT equivalence or
  reverse-superiority rule passes, or quantitative intermediate-correlation
  calibration/order is falsified.
- Delete analytic-calibration specificity only if the frozen INFO-FLEX
  equivalence or reverse-superiority rule passes.
- Delete structured-fusion specificity only if the frozen RI-STRONG
  equivalence or reverse-superiority rule passes with work matching.
- Delete exact-copy claims if lineage is unavailable or the collision audit
  fails.
- Delete the `k` claim if only `N` passes, and vice versa.
- Delete task-value claims if only posterior metrics improve.
- Delete correlation-specific performance attribution when the exact
  specificity-equivalence family passes.
- Treat every relation that meets neither superiority, equivalence, nor
  reverse-superiority criteria as unresolved; non-rejection never licenses a
  deletion.
- Delete general communication-redundancy language; the frozen claim is only
  conditional information value after matched receipt.

### Maximum claim

Even the strongest positive outcome supports only this statement:

> In the frozen cooperative Gaussian HMM toy, under trustworthy evidence
> lineage, matched successful receipt and abstract packet accounting, and the tested
> conditional covariance family, one frozen decentralized shared policy using
> a learned covariance-calibrated information clock caused lower paired
> error-delay-sensing loss than the named matched alternatives on the specific
> held-out `N` and/or `k` surfaces that passed, while remaining equivalent under
> literal packet replication.

It does not support universal Bayes optimality of the learned estimator,
semantic duplicate detection, arbitrary correlation or bias robustness,
arbitrary roster/churn or duration generalization, real-UAV benefit, generic
mean-field or information-bottleneck claims, or superiority of analytic
calibration unless the primary advantage interval also passes against
`INFO-FLEX`.

## 11. Prospective second surface and UAV bridge

No second-surface work is authorized. It becomes answer-changing only if B1
shows that covariance-aware timing matters and the scalar/count alternatives
do not fully explain it.

The proposed second surface is a heterogeneous **relay-viewpoint switch**. A
binary landing-zone or target-confirmation state is observed by UAV-like agents
with class-dependent gains, a rank-two weather/illumination factor, a sparse
pose-overlap residual, and exact relay copies carrying capture lineage. At
physical tick 15, the roster switches `3 -> 7` or `7 -> 3`; externally supplied
scan/loiter periods are `k in {2,5,8}`, with one held out. Packet receipt,
delivery reliability, and topology are manipulated separately from
information value. Agents use the same row network, finite-round additive
consensus, and shared sense/relay/commit actor. The decisive comparison is
clone-heavy entry versus genuinely new-viewpoint entry at the same roster size,
then a within-episode switch between them.

The UAV mapping is literal but prospective: origin ID is camera capture ID;
overlap metadata comes from pose/time; common factors represent weather,
illumination, or shared preprocessing; relay storms create exact copies; new
viewpoints create partially independent evidence; `N` changes through launch,
recovery, or link dropout; and `k` is an externally imposed scan, loiter, or
tracking-skill duration. The intended benefit is avoiding false confidence from
relay/co-located evidence while committing sooner when new viewpoints add real
information. B1 cannot establish that bridge.

## 12. Literature provenance and boundaries

The following local sources motivate ingredients, not outcomes:

- `B01` motivates identical parameter sharing for strongly homogeneous agents
  but explicitly does not establish dynamic rosters or held-out-`N` transfer.
- `P08` motivates mean-action summaries; its fixed-size experiments are not one
  frozen learned policy tested across unseen `N`.
- `P14` gives an assumption-bound `O(N^-1/2)` cooperative-MARL/mean-field
  approximation for interchangeable agents; it does not prove CCIC or learned
  held-out-`N` generalization.
- `P12` treats dense heterogeneous graphon interactions with label-indexed
  policies and does not supply this shared-policy result.
- `B03` supplies the decentralized information-structure boundary: execution
  information must arrive through local history/communication.
- `P15` bounds marginal message entropy using covariance and studies an
  information bottleneck; it does not estimate conditional novelty or reject
  duplicates.
- `P17` uses an episode-persistent latent; it is not variable skill period `k`.

The corpus contains no direct variable-`k` theorem and no evidence for the
replication-collision claim. Every CCIC conclusion therefore depends on the
prospective experiment above, not on those papers.

## 13. Owner routing

The complete frozen revision is this file plus:

- `docs/research/candidates/covariance_calibrated_information_clock/CCIC_B1_ROOT_TO_CM_HANDOFF.md`
- `docs/research/candidates/covariance_calibrated_information_clock/CCIC_B1_CHATGPT_EXTERNAL_PRO_MATH_CLOSURE_REQUEST.md`
- `docs/research/candidates/covariance_calibrated_information_clock/CCIC_B1_GEMINI_INNOVATOR_REQUEST.md`
- `docs/research/candidates/covariance_calibrated_information_clock/CCIC_B1_RESULT_BLIND_INTERPRETATION_ACTIVATION_MAP.md`
- `docs/research/candidates/covariance_calibrated_information_clock/CCIC_B1_CHATGPT_EXTERNAL_PRO_V3_REVISION_REQUIRED_INTAKE.md`

The Pro and Gemini requesters are mutually blind and `PREPARED_NOT_SENT`.
Before production, this exact complete revision requires a same-direction
ChatGPT External Pro `CLOSED` disposition and this EM's intake. Root retains
portfolio and sequencing authority; CM retains implementation and runtime
authority. Revision 03 received `REVISION_REQUIRED`; revision 04 has not been
sent. No revision-04 closure, release, construction, or activity has occurred.
