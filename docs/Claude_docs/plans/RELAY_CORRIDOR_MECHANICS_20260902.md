# Relay corridor mechanics (companion to ADR 02)

Provenance: drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`) on 2026-09-02
from `ADR_02_CONVERGENCE_PROMPT_GPT_PRO_20260902.md`, then finalised after Part IV of
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`. This version applies Part IV §IV.8.1
decisions 1–3 and items IV.4, IV.5, and IV.7 without changing any formula, proposal grid, or margin
value. Status: finalised mechanics definition; implementation evidence does not yet exist.

---

## State

The public state is a ragged set of region, zone, and agent records. Regions carry an identifier,
change flag, dwell age, one-step-lag cue \(y_{r,t}=\theta_{r,t-1}\), reserved probe fields, and a
reserved E5 coupling field fixed to zero while coupling is disabled; agents carry an identifier,
pinned region, zone, held role, lease-freshness flag, and segment age. If a switch occurs between
\(t-1\) and \(t\), the change flag is immediate but \(y_{r,t}\) still carries the old latent; on the
next public state the cue carries the new latent. At reset the lag is degenerate and the cue is
defined as \(y_{r,0}=\theta_{r,0}\); this is the reading under which greedy equals the switching
oracle exactly at \(K=2\) (owner decision recorded in review Part VII.5, applied to the finalised
page as one sentence). The current latent and renewal epoch are host-private,
exposed only to exact oracles or an enabled probe. E2–E4 are time-homogeneous by construction, so no
`time_homogeneous` flag is exposed. Raggedness is a family boundary property; with \(\rho=0\) and
fixed \(N\), E2–E4 do not change live cardinality. This follows the ragged-boundary, temporal-depth,
and state-visible-change requirements in environment advice §3 P4–P6 and §4, ledger §9.3, and review
Part IV §§IV.4 and IV.7.

## Entities

There are two regions, \(Z\) ordered corridor zones, and \(N\) agents. Each zone belongs to one
contiguous region; each agent is assigned a region and zone at reset and stays there. \(N,K,Z,H\)
are parameters; there is no \(N\bmod K\) rule. E2–E4 fix churn rate \(\rho=0\). Entity RNG keys are
`(master seed, episode, entity id)`; region-event keys replace `entity id` with `region id`, as
required by advice §3 P5–P6 and review F2.7.

## Action

The full HMASD stack is retained. Configure `n_z = K`; the low-level policy emits a continuous
\(K\)-vector each step, and the host takes its argmax as role
\(a_i\in\{0,\ldots,K-1\}\). The existing team code \(Z\) remains in the learner, but the E2–E4 host
adds no team-coupling reward while the reserved E5 switch is off. The ADR-01 adapter emits
\(e_i=\text{RENEW}\) exactly for \(i\in S_t\), and `KEEP` otherwise. Thus agent \(i\) supplies
\((a_i,e_i)\). Reset installs the initial lease before scoring; every later `RENEW` consumes one
zero-service step and stamps the current regional epoch. The learner receives the shared mean reward
\(r_t\); per-agent service indicators are logged. ADR 01 revision 3 supplies \(c,c_Z,k_{\max},k_Z\),
per-agent segment closure, and \(k_Z=H\) for E3/E4. This is review Part IV §IV.8.1 decision 1 and does
not alter ADR 01.

## Latent

Region \(r\) has \(\theta_r\in\{0,\ldots,K-1\}\), initially uniform. Zone \(q\) requires

$$
a^*(q,\theta_r)=(q+\theta_r)\bmod K.
$$

A switch draws a different \(\theta_r\) uniformly, increments the regional epoch, and invalidates all
regional leases. Thus any event makes a held plan stale until renewal, even if a later latent label
repeats.

## Hazard

E3 draws one Bernoulli event per region per transition at rate \(\lambda_r\);
\(\lambda_1=\lambda_2\) is homogeneous, while \(\lambda_1\ne\lambda_2\) is E3. E4 instead holds
\(\theta_r\) for positive-integer duration \(D\). Deterministic episodes start with a full dwell of
length \(D\), so events occur at \(D,2D,\ldots\) and fixed boundaries at
\(0,D,2D,\ldots\) are aligned; no stationary residual-life phase is sampled. Deterministic \(D\) has
variance \(0\); discrete exponential means geometric, with mean \(\mu\) and variance
\(\mu(\mu-1)\); discrete lognormal uses
\(D=\max(1,\lfloor X+\tfrac12\rfloor)\), with log-location calibrated to \(E[D]=\mu\) and variance
summed from its CDF-bin masses. Only \(E[D]\) is matched, implementing review F2.4–F2.5, §4.1
decision 6, II.9, and IV.5.

## Reward

Before costs,

$$
r_t=\frac{\Delta}{N}\sum_i
\mathbf 1\!\left[
e_i=\text{KEEP},\
\text{lease}_i\text{ fresh},\
a_i=a^*(q_i,\theta_{r_i})
\right],
\qquad 0<\Delta\le1.
$$

`RENEW`, stale leases, and wrong roles contribute zero. The outage is the host's physical switching
cost; ADR-01 \(c\) remains a policy-gap threshold. The displayed scalar is the shared mean delivered
to the learner, while every indicator inside the sum is logged for later asynchronous-credit analysis
(review Part IV §IV.7).

## Probe

E2–E4 fix \(c_{\text{probe}}=0\) and have no probe action; reserved state fields stay zero. A later
family mode may enable a region probe that fills those same fields with current \(\theta_r\). Its
registered information value \(v\) is the exact dynamic-program return gain from that reveal, so
enabling it does not change the state layout. At \(K=2\), the immediate change flag and old cue identify
the only possible new latent, so \(v\) is not the first-object quantity; \(K=3\) is the registered
family point where the cue and probe value become meaningful. The probe remains outside the current
E2–E4 ladder fixed in plan §§4–6 and 11.

## Structure cut

D0 is the same learner with \(c=c_Z=\infty\) and fixed caps. It loses setup service at each boundary
and post-event service until the next boundary. Greedy sees the lagged cue, change/freshness flags,
identities, and occupancy, but not current \(\theta_r\). At \(K=2\), a switch must choose the only
different latent, so the change flag plus \(y_{r,t}\) identifies the new latent and greedy equals the
switching oracle by construction. At \(K\ge3\), the flag does not select among the \(K-1\) alternatives;
the next cue does. This names the duration structure cut required by review F2.3 and applies Part IV
§§IV.2, IV.4, and IV.8.1 decision 2.

## Reference policies and margins

Enumerate a latent-aware switching oracle, one latent-aware oracle per fixed \(k\), all open-loop
zone-role maps/fixed periods, and greedy. Let \(w_r=N_r/N\) and

$$
C(k,\lambda)=\frac{1-(1-\lambda)^k}{k\lambda}.
$$

For the proposal below, exact E3 values are

$$
J_{\mathrm{sw}}
=\Delta\sum_r w_r\frac{1+(H-1)(1-\lambda_r)}{H},
$$

$$
J_k
=\Delta\sum_r w_r
\left[C(k,\lambda_r)-\frac1k+\frac1H\right],
\qquad
J_{\mathrm{open},k}=\frac{J_k}{K}.
$$

Register

$$
m=J_{\mathrm{sw}}-\max_kJ_{\mathrm{open},k},
\qquad
m_{\mathrm{dur}}=J_{\mathrm{sw}}-\max_kJ_k.
$$

**Inference, large \(H\) and equal region weights:**

$$
m_{\mathrm{dur}}\approx
\Delta\left[
\frac{2-\lambda_1-\lambda_2}{2}
-\max_k\left(
\frac{C(k,\lambda_1)+C(k,\lambda_2)}2-\frac1k
\right)
\right].
$$

The \(1/k\) term is renewal outage. At \((\lambda_1,\lambda_2)=(0.005,0.02)\) and \(k=20\), the
repository's \(C\)-table values \(0.9539\) and \(0.8310\) give \(0.0580\) at \(\Delta=0.4\); exact
finite-\(H\) enumeration below gives \(0.057037\). The difference is the \(1/H\) correction and the
rounding of the displayed \(C\)-table, not a separate finite-state DP effect (review Part IV §IV.7).
This directly instantiates ledger K-1 and §9.2 and review II.7/II.10.1 decision 2. For the first object
at \(K=2\), \(m\) is registered and reported but is not an E2–E4 acceptance criterion; greedy's and
the learner's ceiling is exactly \(J_{\mathrm{sw}}\). The acceptance-scale margin is
\(m_{\mathrm{dur}}\). \(K=3\) is retained as the family point where \(m\), the cue, and \(v\) are
meaningful.

## Enumeration recipe

E3's per-region dynamic-program state is `(theta, freshness, fixed-phase)`; E4 adds renewal age
\(0{:}H\). Open-loop enumeration is \(K^Z\) zone-role maps times the fixed periods plus
`never-renew`. The two regions combine by agent weights. Finite states and known transition
probabilities make the expected returns exact—up to declared floating arithmetic—without training or
Monte Carlo.

## Proposed grids

**Proposal:** \(N=6\), three agents per region; \(K=2\); \(Z=4\); \(H=400\); and D0
\(k\in\{1,2,5,20,40\}\). Thus \(H=10\) times the largest fixed \(k\), as scoped by review II.8 and
II.10.1 decision 3. \(K=3\) is a registered family point for later latent-information questions, not
a change to this first-object grid.

| level  | \((\lambda_1,\lambda_2)\) | \(\Delta\) |   \(m\) | \(m_{\mathrm{dur}}\) |
| ------ | ------------------------: | ---------: | ------: | -------------------: |
| small  |            \((.005,.02)\) |         .4 | .226025 |              .057037 |
| medium |            \((.005,.10)\) |         .6 | .356468 |              .144358 |
| large  |             \((.02,.20)\) |        1.0 | .580747 |              .271219 |

The best fixed \(k\) is respectively \(20,5,5\). **Proposal for E4:** \(E[D]=20\); variances are
\(0\), \(380\), and \(687.309\) for deterministic, geometric, and mean-calibrated rounded-lognormal
shape \(1\). The open-loop census is \(2^4\times6=96\) candidates; the largest per-region E4 DP has
\(2\times2\times40\times401=64{,}160\) states. These are analytic design values, not measured
results.

## Speed note

One vectorized NumPy step performs two event updates, indexed target-role gathers, freshness/renew
masks, one Boolean reduction over `[batch,N]`, and cue/age updates. The E5 coupling switch and its
reserved public field remain off and zero, so they add no active mechanics. The step has no geometry,
pairwise agent loop, or native call. Approximately \(10^4\) steps/s/core is the advice §3 P7 target,
not a measurement. The actual E5 coupling rule is deliberately deferred until E5 is scheduled, per
review Part IV §IV.8.1 decision 3.
