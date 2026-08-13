# CCIC B1 science card

```text
direction=covariance_calibrated_information_clock
revision=CCIC-B1-SCIENCE-20260812-03
owner=EM_covariance_calibrated_information_clock
object=result-blind prospective B1 discriminator
scientific_activity_started=false
mathematical_closure=not_requested
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

The frozen first discriminator contains an analytic HMM/GLS Bayes oracle as a
teacher and ceiling only. The deployed path is decentralized: every agent
receives the same fixed-bit packets through a matched one-round all-gather,
computes the same fixed-rank sufficient statistics locally, runs the same
shared actor, and executes its own action. No deployed arm receives a privileged
global covariance matrix or centralized inference result.

The strongest alternative is simpler lineage-aware unique-origin counting, or
a sufficiently expressive replication-safe set encoder, rather than learned
covariance. If either matches CCIC, the corresponding extra covariance or
analytic-clock machinery is deleted. Nothing in this card authorizes CM,
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
  (`ORIGIN-COUNT`), with oracle, received-count, mean-pooling, and shuffled-clock
  diagnostics.
- **Observable.** Paired normalized error-delay-sensing loss, oracle regret,
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
bandwidth contention. Retransmission may legitimately improve delivery
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
128-bit packet row per active agent. Conditional on the new hidden state
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
sensitivity to genuinely new evidence. The oracle ordering at `N=5` is

\[
J_{DUP}=0.5625 < J_{CORR}=0.9375 < J_{IND}=2.8125.
\]

### 2.3 Packet and consensus law

Each packet is exactly 128 accounted bits: a 64-bit represented scalar, a
32-bit immutable origin ID, a 16-bit capture tick, an 8-bit overlap code, and
an 8-bit validity/check field. At each decision epoch, every agent sends one
packet through a complete-graph, one-round all-gather; every successful row is
delivered to every agent. Receipt is deterministic in B1. A `RELAY` action
resends the last row with the original origin ID and capture tick; before any
sense it sends a valid null row. A relay creates no new evidence origin.
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

### 3.3 Teacher policy

The oracle uses the exact HMM update, true covariance, and backward dynamic
program under `L`. Its continuation expectation is the one-dimensional
Gaussian-mixture expectation induced by the next `q`. The implementation target
uses a log-odds grid `[-16,16]` at spacing `0.01`, 64-node Gauss-Hermite
quadrature, linear interpolation, and exact endpoint clipping. Numerical action
ties within `1e-12` choose `SENSE` over `RELAY`; a commit/commit tie at
`ell=0` uses the public action bit and otherwise chooses the posterior-MAP sign.

The mathematical oracle is the exact Bellman integral. The numeric teacher is
accepted as its approximation only if a preactivity refinement on expanded
log-odds grid `[-24,24]` at spacing `0.005` with 128-node quadrature changes
every action value on the original coarse grid by at most `1e-4` and changes no
non-tie optimal action. Otherwise no training starts and the numeric object is
not called an oracle.

The teacher supplies behavior-cloning labels on training cells and an oracle
loss ceiling during evaluation. It is centralized for analysis only. No
deployed arm calls the dynamic program, reads true `rho`, or receives an oracle
posterior.

## 4. Shared actor, treatment, and arms

### 4.1 One frozen shared actor

For each training seed, one actor is trained once from oracle-teacher states and
then frozen and reused unchanged by every deployable arm. Its five inputs
are clipped posterior log odds `ell/16`,
`log(1+J_next)/log(5.5)`, `t/30`, `(30-t)/30`, and `k/5`. The architecture is
`5 -> 32 -> 32 -> 4` with SiLU activations. It is trained for exactly 1,500
Adam updates, batch size 128, learning rate `1e-3`, betas `(0.9,0.999)`, epsilon
`1e-8`, no weight decay, on exactly 9,216 teacher states: 768 from each of the
12 training `(N,k,rho)` cells. There is no centralized
critic and no arm-specific actor fine-tuning.

The expected-next-information input is computed by each arm from a public
metadata-only template for the next batch: public regime, roster, expected
origin lineage pattern, overlap code, and quality, with represented values set
to zero. It never uses a future realized measurement. This makes the first
decision well-defined and gives every arm the same prospective information.

At execution, each agent locally runs this actor on the arm's reconstructed
belief and expected information from one additional `SENSE` block. The analytic
oracle is therefore a teacher/ceiling, not the deployed actor.

### 4.2 `CCIC-R1` treatment

Agents quotient the current table by composite `origin_key`, reject
inconsistent same-key payloads, and remove every key already in the persistent
assimilated ledger. Only remaining new keys update belief; relay-only tables
have zero likelihood and information increment. A shared covariance network
receives only `(o,s)` and has
architecture `2 -> 16 -> 2` with SiLU, exactly 82 trainable scalars. It emits

\[
d=10^{-4}+\operatorname{softplus}(a),\qquad
u=\operatorname{softplus}(b),
\]

and constructs on the unique-origin set

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
   n_{eff}=M/[1+(M-1)\widehat\rho],\quad
   \widehat J=\mu^2n_{eff}/\widehat\nu,
   \]
   with the corresponding weighted mean likelihood. `rho_DUP` is fixed to zero
   after lineage quotienting; the three marginal variances and the `CORR`/`IND`
   correlations leave five trainable scalars. This is the simplest
   covariance-aware alternative and is exact for the homogeneous Stage-1
   family.
2. **`RI-STRONG`.** Quotient lineage, map each unique `(z,o,s)` through a
   `4 -> 7 -> 4` SiLU encoder on `(z,o,s,log M)`, mean-pool, append `t/30` and
   `k/5`, and use a `6 -> 2` linear head. The first output is the batch
   likelihood increment; the second gives
   `J_hat=1e-4+softplus(raw_J)`. It has exactly 81 trainable scalars versus
   CCIC's 82 and can represent interactions between value and unique-origin
   count. It receives the same packets and has the
   same update count, batch size, optimizer, initialization family, and
   hyperparameter-search budget. This is the primary
   information/capacity/exposure/work-matched nonlinear baseline; a mean-only
   ablation is never the strongest comparator.
3. **`INFO-FLEX`.** Reuse the frozen CCIC covariance estimator and give its
   `(ell_minus,q_hat,J_hat,k)` to a `4 -> 11 -> 2` SiLU head with 79 additional
   scalars. Its first output is posterior log odds and its second is converted
   to positive information by `1e-4+softplus`. It replaces the
   analytic HMM/LLR calibration with a flexible learned mapping. Because it has
   extra capacity, it is an intentionally advantaged diagnostic. CCIC can make
   an analytic-calibration claim only if it also beats this arm.
4. **`ORIGIN-COUNT`.** Quotient lineage, assume unique origins are conditionally
   independent with unit variance, and use `q=mu*sum(z)` and `J=mu^2*M`. This is
   the strongest simple provenance-count/dedup explanation.

Every learned fusion arm uses exactly 1,500 Adam updates, batch size 64,
learning rate `3e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay, and
the same 9,216 labeled snapshots, 768 per training cell. There is one frozen
configuration and no adaptive hyperparameter search. `RI-STRONG` minimizes the
equal-weight mean of squared errors for `Delta ell/16` clipped to `[-1,1]` and
`log(1+J)/log(5.5)`; `INFO-FLEX` uses the same normalized targets for posterior
`ell` and `J`. They use oracle targets only in training; no teacher value is
available at execution.

### 4.4 Diagnostics, not superiority baselines

- `ORACLE`: true HMM/GLS dynamic-program ceiling.
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

Diagnostics cannot satisfy a superiority claim. If `J-SHUFFLE` or `J-CLAMP`
matches CCIC, the information-clock causal claim is unsupported.
`ORACLE`, `J-SHUFFLE`, and `J-CLAMP` receive complete paired rollouts.
`RECEIVED-COUNT` and `MEAN-RI` are restricted to the collision/shadow tables and
do not add environment trajectories.

## 5. Replication-collision family falsifier

Before outcome evaluation, construct two legal shadow packet tables with
`N=5`, represented value `z=+0.75` in every row, the same tick, bit count, and
successful receipt:

- `COLLIDE-DUP`: all five rows carry one origin ID and `o=1`.
- `COLLIDE-IND`: the five rows carry five distinct origin IDs and `o=0`.

The first demands `M=1`, `q=0.5625`, and `J=0.5625`; the second demands
`M=5`, `q=2.8125`, and `J=2.8125` under the oracle. This audit is a contract
state, not a claim about the probability of exact equality under a continuous
distribution. Treating equal values as copies fails the audit. Treating the
same lineage five times as five likelihood factors also fails it.

A second shadow family fixes `N=5` and traverses `rho={1,0.5,0}`. The required
oracle ordering is `0.5625 < 0.9375 < 2.8125`. Passing only the endpoints
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

Randomness uses counter-addressed Philox with stream-specific keys. Latent
flips use `(master,11,episode,physical_tick)`; common residuals use
`(master,13,episode,physical_tick)`; idiosyncratic residuals use
`(master,17,episode,physical_tick,origin_index)`; public action uniforms use
`(master,19,episode,physical_tick)`. None contains `N`, `k`, `rho`, or arm.
Minibatch order uses `(master,23,module_id,update)` and initialization uses
`(master,29,module_id,parameter_index)`. `N` selects a nested source prefix,
`k` selects reachable ticks, `CORR` mixes common and idiosyncratic base draws,
`IND` uses only idiosyncratic base draws, and `DUP` reads origin zero and
replicates it. Thus all axes transform one potential tape and arm order never
changes a draw.

There is no adaptive stopping. All 32 seed blocks are required. A missing or
invalid block is reported and no efficacy conclusion is drawn; it is not
replaced after scientific activity. Engineering repair before activity may
preserve this exact science object, but any science-bearing change returns to
this EM.

Thirty-two seeds are a resource-bounded Stage-1 choice, not an assertion of
prospective 80% power for the `0.02` smallest effect. The simultaneous interval
itself is the precision gate: if it does not exclude zero for a mean advantage
of at least `0.02`, the axis is unresolved. No branch may translate a wide
interval into evidence of no effect.

### 6.3 Exposure and work matching

Within a cell and tape, all arms have identical potential tapes, packet schema,
transition/receipt rules, legal support, public-uniform rule, per-decision call
opportunity, horizon, and reward accounting. Realized histories and call counts
may differ endogenously after actions or commit. `CCIC-R1` and `RI-STRONG`
differ by one trainable scalar (82 versus
81), receive exactly the same 1,500 updates and samples, and have no search
variants. Their measured per-decision scalar-operation count and peak temporary
state must be reported per call and cumulatively per episode. A common offline
potential-state replay calls both fusions at every reachable opportunity to
measure per-call work. A primary superiority claim is unavailable if either
exceeds the other's median replay per-call work by more than 10%; that
comparison is exposure-confounded. Online total calls and operations are
endogenous timing outcomes, charged by the loss and reported rather than forced
equal.

The exposure audit must also show that duplicate multiplicity, received `N`,
future values, reward, held-out-cell moments, and actor outputs cannot enter the
CCIC covariance network. Unique-set dimension affects only the declared sums.

## 7. Observables and inference

### 7.1 Endpoints

For every seed and cell report:

- mean `L_norm` and paired excess loss relative to `ORACLE`;
- posterior negative log score and Brier score at every decision and commit;
- physical commit tick, sense count, relay count, and task error rate;
- predicted `q`, `J`, unique count, received count, and oracle discrepancy;
- actor plan probabilities, selected plan, packet bits, inference calls,
  scalar-operation count, and peak temporary state;
- exact-copy collision outputs and `rho`-ordering outputs.

Training seeds, not episodes or ticks, are the inferential replicates.

### 7.2 Primary held-out contrasts

For each comparator in
`{RI-STRONG, INFO-FLEX, ORIGIN-COUNT}`, define paired seed-level
differences `d = mean(L_norm_CCIC - L_norm_comparator)` on:

1. held-out `N`: equal average over `N=8`, `k in {1,3}`, and all three regimes;
2. held-out `k`: equal average over `k=5`, `N in {2,5}`, and all three regimes.

This creates six prespecified primary contrasts. A contrast supports CCIC
only when its mean is at most `-0.02` and its one-sided 95% simultaneous upper
confidence bound is below zero. Use a studentized paired max-`T` procedure from
100,000 common nonparametric resamples of the 32 paired seed blocks, generated
from inference seed `8675309`; take the maximum centered studentized statistic
across all six contrasts. If a contrast has zero seed variance, its interval is
its exact point value and it is omitted from the studentized maximum; a nonzero
constant therefore cannot masquerade as zero.
The jointly held-out `(8,5)` corner is multiplicity-controlled secondary
evidence and cannot rescue either primary axis.

`ESS-SCALAR` is a prespecified co-treatment/reduction test, not an arm that the
rank-one parameterization must outperform in the homogeneous family where the
scalar formula is exact. On each axis, report the paired CCIC-minus-ESS
difference with a simultaneous two-sided interval and equivalence margin
`[-0.005,+0.005]`. Equivalence or ESS superiority triggers the scalar-deletion
branch; it does not erase support for the broader covariance-calibrated clock
when the covariance arms beat the non-covariance alternatives.
The two ESS reduction contrasts form their own two-sided max-`T` family with
the same 100,000 paired-seed bootstrap resamples.

For each of `J-SHUFFLE` and `J-CLAMP`, define two paired diagnostic contrasts as
`mean(L_norm_diagnostic-L_norm_CCIC)` on the same held-out-`N` and held-out-`k`
surfaces. The four contrasts form one one-sided max-`T` family. A diagnostic
supports clock causality only when its mean degradation is at least `0.01` and
its simultaneous lower 95% bound is above zero. Failure by either diagnostic
on an otherwise positive axis removes the clock-causality claim for that axis.

### 7.3 Exact-copy equivalence family

For CCIC, compare `N=5` and `N=8` against `N=2` under `DUP`, separately for the
two training `k` values. Successful support requires the two-sided 95%
simultaneous intervals for paired `L_norm` differences to lie inside
`[-0.005,+0.005]`, using the same max-`T` construction over four equivalence
contrasts. In addition, `q`, `J`, and actor probabilities on the paired
post-receipt shadow states must agree within absolute `1e-10`. This is an
information-value equivalence claim under matched receipt, not a transport
claim.

### 7.4 Mechanism gates

All of the following are required before any efficacy claim:

1. lineage collision audit passes both `COLLIDE-DUP` and `COLLIDE-IND`;
2. learned `J` is invariant to literal duplicate multiplicity and orders
   `DUP < CORR < IND` at `N=5`;
3. the actor has reward-independent information sensitivity as defined below;
4. `J-SHUFFLE` and `J-CLAMP` do not match CCIC on the relevant held-out surface;
5. paired packet, inference, capacity, search, and work conditions pass;
6. the oracle itself separates the information regimes in expected loss. This
   is a deterministic preactivity feasibility check: at the initial belief,
   `N=5,k=3`, exact quadrature under the frozen DP must give expected
   `L_norm_ORACLE(DUP)-L_norm_ORACLE(IND) >= 0.01`. If it does not, no training
   or stochastic evaluation starts. This check is not empirical evidence for a
   learned arm.

## 8. Preactivity certificate and activity criterion

### 8.1 Required certificate before scientific activity

The owner-prepared implementation may not consume a training label, reward, or
evaluation tape until a machine-readable certificate shows:

- the DGP constants, axes, loss, seed formula, stream keys, counts, and stop
  rule equal this revision;
- the analytic `J` values above and the singular replication-map identity hold
  under the stated support conditions;
- the two collision tables produce their exact oracle values;
- all packet schemas, legal joint supports, actor calls, and communication bits
  match across arms;
- static feature tracing proves the CCIC covariance network cannot receive
  forbidden multiplicity, future, reward, held-out, or actor-output inputs;
- the oracle DP has at least 24 eligible information-sensitive base states among
  the 96 base `(t,k,ell)` states formed by `t in {5,10,15,20}`,
  `k in {1,3,5}`, and the eight signed values generated from
  `abs(ell) in {0.25,0.75,1.25,1.75}`. Each base state is evaluated at all three
  frozen `J_next` values, for exactly 288 actor evaluations;
- all output roots are fresh and the projected bound is no more than 90 wall
  minutes, 4 GiB peak RSS, 8 CPU threads, 240,000 learned optimizer updates,
  and 60 million primitive environment ticks.

The resource ledger is literal: eight arms receive full rollouts
`{CCIC,ESS,RI-STRONG,INFO-FLEX,ORIGIN-COUNT,ORACLE,J-SHUFFLE,J-CLAMP}`, for a
worst-case `32*27*256*30*8 = 53,084,160` evaluation ticks. The shared snapshot
bank adds at most `32*9,216 = 294,912` one-tick draws; 288 shadow evaluations
per seed and offline work replay remain below the 60-million ceiling. Learned
updates are exactly `32*(one actor + four learned fusion modules)*1,500 =
240,000`. `RECEIVED-COUNT` and `MEAN-RI` have shadow-only evaluations.

These checks are feasibility/contract checks, not evidence that CCIC works.

### 8.2 When scientific activity begins

Question-relevant scientific activity begins at the earliest of:

1. the first optimizer update using a generated training label, residual, or
   oracle-teacher target from this DGP;
2. the first actor/fusion evaluation on a frozen stochastic train or evaluation
   tape; or
3. the first computation of a result-bearing endpoint from such data.

Pure schema tests, hand-written collision constants, symbolic identities, and
resource projection before those events are preactivity.

### 8.3 Reward-independent activity gate

After training but before reading task return, evaluate the 96 frozen base
shadow states at all three `J_next` values (288 actor evaluations per seed).
Among base states where the oracle plan differs between endpoint
`J_next` values, at least 80% must satisfy

```text
P(SENSE | J_IND) >= P(SENSE | J_CORR) >= P(SENSE | J_DUP)
```

within `1e-8`, and at least 25% must have
`P(SENSE | J_IND)-P(SENSE | J_DUP) >= 0.10`. The estimator must also satisfy
`J_DUP < J_CORR < J_IND`. Failure means the proposed clock was not materially
active; returns cannot answer the causal question.

## 9. Result-blind interpretation map

1. **Both-axis specific support.** All mechanism/work/equivalence gates pass;
   CCIC meets the corrected superiority rule against all three primary
   comparators on
   both held-out axes. Support is limited to covariance-calibrated timing in
   this toy across the tested `N` and `k` values.
2. **One-axis support.** The full rule passes only for held-out `N` or only for
   held-out `k`. Claim only that axis; do not say the algorithm spans both.
3. **Covariance-aware but not analytic.** CCIC and `INFO-FLEX` beat
   covariance-blind arms, but CCIC does not beat `INFO-FLEX`. Support
   covariance-aware timing, not the analytic calibration mapping.
4. **Scalar suffices.** `ESS-SCALAR` is equivalent to or better than CCIC on
   all gates and task loss. Delete learned low-rank fusion for the homogeneous
   surface and retain the scalar clock for the next discriminator.
5. **Flexible set encoder suffices.** `RI-STRONG` matches or beats CCIC with
   work matching. The structured covariance advantage is unsupported; prefer
   the replication-safe set learner unless a heterogeneous second surface is
   answer-changing.
6. **Counting suffices.** `ORIGIN-COUNT` matches CCIC, or only the exact
   duplicate endpoint passes while `CORR` ordering fails. Retain provenance
   quotienting; delete the covariance-calibration claim.
7. **Oracle succeeds, estimator fails.** Oracle information changes optimal
   timing and beats baselines, but learned CCIC fails calibration/activity.
   The estimator is the failed object; the analytic information-clock
   principle remains unresolved.
8. **Oracle fails.** The oracle does not separate expected task loss across the
   information regimes. Stage 1 lacks an information-timing tradeoff and gives
   no reason to invest in learned clocks on this surface.
9. **Clock not causal.** `J-SHUFFLE` or `J-CLAMP` matches CCIC, or return changes
   without calibrated `J`. No covariance-information causal claim.
10. **Exposure explanation.** A gain disappears after the frozen packet,
    capacity, inference, or work conditions are applied. Attribute the result
    to unmatched exposure/work, not covariance.
11. **Core falsification.** Literal duplicate multiplicity changes CCIC `q`,
    `J`, action probabilities, or paired loss beyond the equivalence boundary,
    or independent equal-valued origins are collapsed. Reject this revision's
    information-value invariance.
12. **Activity failure or incomplete seeds.** No efficacy interpretation,
    regardless of observed return. Repair only through the proper scientific or
    engineering owner route.
13. **Held-out threshold not met.** If the corrected interval is wide, report
    the held-out axis as unresolved. If it precisely excludes the `0.02` SESOI,
    report no material effect at that threshold. Trained-cell improvement alone
    is interpolation and never supports variable-`N` or variable-`k`
    robustness.
14. **Uniform advantage including `IND`.** If CCIC gains equally when evidence
    is independent, investigate representation/optimization or posterior
    temperature rather than crediting covariance specificity.

## 10. Strongest alternative, deletion map, and claim ceiling

### Strongest alternative

Trusted lineage plus unique-origin count may contain all useful structure in
this toy; alternatively, `RI-STRONG` may learn the relevant conditional
precision without an explicit covariance model. Both are scientifically
stronger explanations than a mean-pooling-only comparison. `INFO-FLEX` is the
strongest explanation for any apparent benefit attributed specifically to the
analytic clock mapping.

### Deletion map

- Delete low-rank covariance if `ESS-SCALAR` matches it.
- Delete covariance calibration if `ORIGIN-COUNT` matches it or intermediate
  correlation is not ordered.
- Delete analytic-calibration specificity if `INFO-FLEX` matches it.
- Delete structured-fusion specificity if `RI-STRONG` matches it.
- Delete exact-copy claims if lineage is unavailable or the collision audit
  fails.
- Delete the `k` claim if only `N` passes, and vice versa.
- Delete task-value claims if only posterior metrics improve.
- Delete general communication-redundancy language; the frozen claim is only
  conditional information value after matched receipt.

### Maximum claim

Even the strongest positive outcome supports only this statement:

> In the frozen cooperative Gaussian HMM toy, under trustworthy evidence
> lineage, matched successful receipt and communication, and the tested
> conditional covariance family, one frozen decentralized shared policy using
> a learned covariance-calibrated information clock caused lower paired
> error-delay-sensing loss than the named matched alternatives on the specific
> held-out `N` and/or `k` surfaces that passed, while remaining equivalent under
> literal packet replication.

It does not support universal Bayes optimality of the learned estimator,
semantic duplicate detection, arbitrary correlation or bias robustness,
arbitrary roster/churn or duration generalization, real-UAV benefit, generic
mean-field or information-bottleneck claims, or superiority of analytic
calibration unless `INFO-FLEX` is also beaten.

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

The Pro and Gemini requesters are mutually blind and `PREPARED_NOT_SENT`.
Before production, this exact complete revision requires a same-direction
ChatGPT External Pro `CLOSED` disposition and this EM's intake. Root retains
portfolio and sequencing authority; CM retains implementation and runtime
authority. No such closure, release, construction, or activity has occurred.
