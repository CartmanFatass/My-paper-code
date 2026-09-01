# ONLGR Pro preactivity revision-bound mathematical closure delta

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager
Candidate: `ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1`
Base revision: `ONLGR-PRO-PREACTIVITY-CORRECTION-20260812-01`
Frozen prospective delta: `ONLGR-PRO-PREACTIVITY-MATH-DELTA-20260812-02`
Status: `FROZEN_PENDING_REVISION_BOUND_REREVIEW`
Closure: `NOT_CLOSED_REVIEW_DELTA_REQUIRED`

## Scope and evidence boundary

This is a result-blind, preactivity mathematical audit of exactly:

- `ONLGR_VARIABLE_K_SCIENCE_CARD.md`; and
- `ONLGR_B1_EXTERNAL_PRO_PRE_RESULT_SCIENTIFIC_INTAKE.md`.

No production result exists. No implementation, test, runtime artifact,
Agentify page, Gemini material, Git state, or other direction entered the
judgment.

The required professional order was completed:

1. registered RL Principles child
   `/root/em_onlgr_variable_k/onlgr_pro_revision_math_principles` returned the
   full `RL_PRINCIPLE_ANALYSIS_PACKET`; then
2. registered independent Critic child
   `/root/em_onlgr_variable_k/onlgr_pro_revision_math_critic` received the same
   base revision plus that complete packet and returned the full
   `CRITIC_ASSESSMENT_PACKET`.

The Critic's conditional decision was `CLOSED_IF_DELTA_APPLIED`. Project
procedure additionally requires the exact owner-frozen delta itself to receive
revision-bound re-review before closure. Therefore this artifact freezes the
delta but does **not** declare mathematical closure. CM acceptance and
production remain withheld.

## Owner reconciliation by audited item

| Item | Owner judgment | Consequence |
|---|---|---|
| Exposure-offset categorical law and score | `DELTA_REQUIRED` | Freeze the mark sigmoid, full likelihood, event/mark score, shared-trunk caveat, and point-mass rows. |
| Right-closed exposure and censoring | `PASS_WITH_LOGGING_DELTA` | The clock is correct; distinguish the virtual startup component from observed episode exposure. |
| Forced safety score and GAE | `PASS` | Zero current actor score never truncates return, bootstrap, trace, or earlier credit. |
| Joint PPO ratio | `PASS_WITH_RNG_DELTA` | One joint factorized ratio and one clip are correct; freeze conditional agent-draw independence. |
| Schedule/episode actor and critic objective | `DELTA_REQUIRED` | Actor objective passes; freeze the behavior-critic lambda-return target, terminal base case, stop-gradient, critic boundary set, and coefficient application. |
| Zero entropy | `PASS` | Entropy coefficient remains exactly zero; marked entropy is diagnostic only. |
| TIMING-ONLY information cut | `INTERPRETATION_DELTA_REQUIRED` | It is task-content-blind but retains reward-relevant tenure/action-state summaries; it cannot localize event timing versus mark choice. |
| PROB identity | `DELTA_REQUIRED` | Check the probability vector and full event/mark-logit Jacobian, not values alone. |
| RAND-IID next-`k` | `DELTA_REQUIRED` | Freeze a dedicated RNG domain, action-independent exogenous draw ordinal, exact uniform map, and terminal censoring. |
| Marked partition MPI/HPI | `DELTA_REQUIRED` | Define `F`, the exact learned-output-selected common cell set and denominator, and its conditional claim. |
| Single-shift yoke | `DELTA_REQUIRED` | Define event times/dwell rotation exactly, recompute state, and freeze `M_exp`, common support, and `Psi` denominators. |
| P/W Bonferroni, sign-flip, LOO | `PASS_WITH_ANALYZER_DELTA` | The 97.5% co-primary intervals pass; freeze exact non-gating sensitivity formulas. |
| Activity, nondegeneracy, oracle, service | `DELTA_REQUIRED` | Move activity to the first retained learned-state/result effect; add stochastic KEEP and exact common-sample diagnostic gates. |
| Claim ceiling | `INTERPRETATION_DELTA_REQUIRED` | Replace timing-specific language with content access in the marked policy; no head localization. |

No delta changes an arm, actor input, schedule, seed, episode count, materiality
threshold, resource cap, or treatment identity. The service sign gate makes an
existing claim condition exact and consumes already-declared service rows. The
registered maximum remains `6,750,208` team ticks.

## Exact prospective delta

The following clauses are indivisible. Any alternative changes the object and
requires a fresh professional review.

### D1. Marked categorical law, likelihood, and score

Let `h_theta` be the conditional-mark logit and
`rho=sigmoid(h_theta)`. For a routine agent row with `e>0`, let
`y=1[action!=KEEP]` and, conditional on `y=1`,
`m=1[action=REFRESH-SAME]`. For ONLGR define

```text
lambda = softplus(g_theta)
u = 1-exp(-e*lambda)

log pi = (1-y)*[-e*softplus(g_theta)]
         + y*{log[1-exp(-e*softplus(g_theta))]
              + m*log(rho) + (1-m)*log(1-rho)}.

grad_theta log pi
  = e*sigmoid(g_theta)*(y-u)/u * grad_theta g_theta
    + y*(m-rho)*grad_theta h_theta.
```

Thus the event coefficient is `-e*sigmoid(g_theta)` for `KEEP` and
`e*sigmoid(g_theta)*(1-u)/u` for either non-`KEEP` mark. RAW uses the same
categorical factorization with event-score term
`(y-u)*grad_theta g_theta` for `u=sigmoid(g_theta)`. The conditional mark term
is present only on a sampled non-`KEEP` row.

The two heads share the actor trunk. A sampled `KEEP` has no direct
`h_theta`/mark-logit term, but its event loss may update shared-trunk parameters
that also affect later `rho`; no wording may call the mark policy immutable on
`KEEP`. `e=0`, fully masked, dummy, and forced rows are point masses and
contribute no actor likelihood or score.

### D2. Exposure, virtual startup, reward segments, and terminal base

Keep the card's right-closed exposure interval and record its closed form:

```text
I_i(t) = {b_prev+1,...,t}
e_i(t) = max(0, t-max(b_prev,ell_i-1)).
```

An action at boundary `t_j` precedes tick-`t_j` service. Its SMDP segment owns
rewards on `[t_j,t_{j+1})`; therefore an action or forced-safety cost at `t_j`
appears exactly once in `R_j`, never in `R_{j-1}`.

At tick zero, `e_policy=8` is the frozen initialization offset. For physical-
exposure diagnostics also record
`e_observed=|I_i(0) intersect {0,...,H-1}|=1` and `e_virtual=7`.
The tick-zero action is flagged `initial_anchor_action`; virtual slots never
enter observed eligible-physical-tick denominators. Always report startup-
inclusive and post-startup behavior separately when an event-rate diagnostic
would otherwise mix them.

Let actual global routine or safety boundaries be
`t_0<...<t_{K-1}<t_K=H`. Terminal `H` owns no action, likelihood, entropy,
exposure reset, or critic row; it supplies `V^-(s_H)=0` and retains rewards only
through tick `H-1`. A coincident safety/routine time is one actual boundary.

### D3. Behavior-frozen GAE and critic target

Before the first PPO epoch, cache the rollout actor log-probabilities and the
behavior critic `V^-`. Set `V^-(s_H)=0` and `A^-_K=0`. For
`j=K-1,...,0`, compute once:

```text
R_j = sum_{d=0}^{Delta_j-1} gamma_tick^d * r_{t_j+d}
Gamma_j = gamma_tick^Delta_j
Lambda_j = lambda_tick^Delta_j
delta^-_j = R_j + Gamma_j*V^-(s_{j+1}) - V^-(s_j)
A^-_j = delta^-_j + Gamma_j*Lambda_j*A^-_{j+1}
G^lambda_j = stopgrad(V^-(s_j)+A^-_j).
```

Cache `A^-` and `G^lambda` unchanged for all four PPO epochs. For every genuine
stochastic routine joint row,

```text
omega_j = exp(log pi_theta(a_j|s_j)-log pi_behavior(a_j|s_j)).
```

Use cached `A^-_j` in the already-frozen schedule/episode-balanced actor
surrogate. For actual critic-boundary set `B_cn`, including masked routine and
forced-safety rows but excluding terminal `H`, use exactly

```text
L_critic = (1/4)*sum_c (1/8)*sum_n
             (1/|B_cn|)*sum_{j in B_cn}
             (V_phi(s_j)-G^lambda_j)^2.
```

Apply value coefficient `0.5` exactly once. There is no value clipping. The
critic's within-episode row mean is intentional; the actor remains a
`1/256`-scaled row sum. Forced, masked, and dummy boundaries never terminate
or reset this recursion.

### D4. Conditional joint action law and random domains

At each routine row,

```text
pi(a_T,a_R|s) = product_{i:e_i>0} pi_i(a_i|o_i),
```

with every `e_i=0` agent represented by a unit point-mass factor. Use distinct
counter domains `ACTION_T` and `ACTION_R`. Their uniforms are conditionally
independent across roles given the current state and paired across arms only by
matching counter identities. Sum stochastic-agent log-probabilities, exponentiate
one joint ratio, and clip that ratio once. Never average agent scores or clip
per-agent, event, or mark ratios separately.

### D5. Full PROB identity and Jacobian conformance

At every frozen-score probe point let

```text
q=sigmoid(g)
rho=sigmoid(h)
S=(1-q)^e=exp(-softplus(g)*e)
u=1-S
u_g=e*q*S
p=(S,u*rho,u*(1-rho)).
```

The exact Jacobian with rows `(KEEP,REFRESH-SAME,REBIND)` and columns `(g,h)` is

```text
J_(g,h) p = [ -u_g,                 0
               rho*u_g,             u*rho*(1-rho)
               (1-rho)*u_g,        -u*rho*(1-rho) ].
```

For every declared cell and exposure/partition point, ONLGR and
`PROB-EXP-IDENTITY` must agree in float64 on both `p` and this Jacobian with
maximum absolute component difference at most `1e-10`. Identical parameter
Jacobians then follow by the shared-network chain rule. A value or Jacobian
failure is formula/implementation nonconformance and blocks the exposure-link
mechanism interpretation.

### D6. RAND-IID conditional independence and censoring

For each IID evaluation seed `s`, episode `n`, and exogenous routine draw
ordinal `r`, define

```text
U^K_{s,n,r} = PRF(domain='RAND_IID_NEXT_K',s,n,r).
K_{r+1} = 4  if U^K < 1/3
          16 if 1/3 <= U^K < 2/3
          32 otherwise.
```

The domain is disjoint from `MODE`, `SENSOR_T`, `SENSOR_R`, `INITIAL_STATE`,
`ACTION_T`, `ACTION_R`, `SAFETY`, `TIE`, optimizer, and every deterministic-
panel namespace. The same `U^K` is paired across arms. Emit the draw only after
the current routine joint action. `r=0` is the draw after the tick-zero action
and increments exactly once per emitted routine draw, including after a masked
or deterministic-`KEEP` routine boundary. It is unaffected by arm, action,
lease, state, reward, or censoring. Hence for the pre-draw filtration `F_r`,

```text
Pr(K_{r+1}=k | F_r,A_r)=1/3, k in {4,16,32}.
```

If `tau_r+K_{r+1}>=H`, set the realized terminal duration to `H-tau_r` and
create no boundary, action, likelihood, entropy, exposure reset, or additional
`K` observation at `H`.

### D7. TIMING-ONLY independence and exact interpretation

In native and RAND-IID no-safety panels, independently cross or domain-separate
initial plan age and all retained TIMING-ONLY clock/action namespaces from mode,
binding, and sensor namespaces. Under the frozen zero task-content placeholders,
retained actor inputs arise only from role, exogenous cadence, initial tenure,
and the arm's prior task-content-blind actions. The full-state critic and reward
are legitimate training signals, not deployment observation leakage, and the
critic shares no actor representation. The safety panel supplies no evidence
for this content-access claim.

Replace every `history-free timing/tenure` phrase with
`feed-forward task-content-blind tenure/cadence/own-action-state heuristic`.
Replace every strongest-branch phrase `task-state-conditioned timing` with:

> benefit from access to current binding, mismatch, and partner-content
> coordinates in the marked intervention policy beyond the registered
> tenure/cadence ablation.

The current shared-trunk ablation cannot localize that benefit to the event head
rather than the conditional mark head. Such localization would require a new
event-only/mark-only arm and a fresh review.

### D8. Marked partition support and estimands

For cell `x`, arm `a`, and partition `P`, retain the card's marked distribution
`(S_a,x(P),R_a,x(P),B_a,x(P))` and define

```text
F_a,x(P)=1-S_a,x(P)
C_s={x: for both a in {ONLGR,RAW} and every P,
         F_a,x(P) in [0.05,0.95],
         and |F_ONLGR,x([32])-F_RAW,x([32])|<=0.05}.
```

Require `|C_s|>=12`. Compute both

```text
MPI_a(s)=|C_s|^-1 sum_{x in C_s} max_{P,Q} TV_a,x(P,Q)
HPI_a(s)=|C_s|^-1 sum_{x in C_s} max_{P,Q}
          |[-log S_a,x(P)]-[-log S_a,x(Q)]|
```

on exactly `C_s`. Report `C_s` and every exclusion reason. The existing MPI
thresholds remain unchanged. MPI and HPI are descriptions conditional on cells
selected by both learned outputs; they are not population-wide invariance or a
causal mediator.

### D9. Exact one-shift cyclic yoke

For an arm, let native voluntary joint-event times be
`tau_1<...<tau_q` with ordered joint action tuples `A_1,...,A_q`. A joint event
is a routine boundary at which at least one agent executes a voluntary
non-`KEEP`; the tuple includes the other agent's simultaneous action. Require
equal `q>=3` in paired ONLGR/RAW episodes. Set `m=q-1` and

```text
D_r=tau_{r+1}-tau_r, r=1,...,m
s=1+((17*p+31*c+n) mod (m-1)).
```

Preselect that one shift before any legality check. Keep the ordered tuples
`A_1,...,A_q`, fix `tau^Y_1=tau_1`, and define

```text
tau^Y_{r+1}=tau^Y_r+D_{1+((r-1+s) mod m)}, r=1,...,m.
```

Then `tau^Y_q=tau_q`; initial and terminal censored blocks remain fixed. Impose
`A_r` only at `tau^Y_r` and impose joint `KEEP` at every other routine callback.
Rotate durations only, never physics, sensor, mode, or destination state.
Recompute binding, plan age, busy, lease, mask, and exposure under the imposed
path. Reject unless every `tau^Y_r` is a pre-existing legal routine callback
and every card-declared action/tactic/dwell/lease/cause/simultaneity,
time-weighted binding-occupancy, total-exposure, and destination-local equality
holds. There is no fallback, second shift, repair, approximation, or outcome
selection.

For a supported arm/pair define, with `i in {T,R}` and `r=2,...,q`,

```text
M_exp = sum_{i,r}|e^Y_{i,r}-e^N_{i,r}|
        /(2*sum_{i,r}e^N_{i,r}),
```

requiring equal native/yoked total exposure and a positive denominator. For
seed ordinal `p` and schedule `c`, let `C_pc` be the unchanged original-slot
set supported in both arms. Require `|C_pc|>=15` of the fixed 16 and use

```text
M_{a,p,c}=|C_pc|^-1 sum_{n in C_pc} M_{a,p,c,n}.
```

Retain the card's `M_exp` materiality thresholds. Compute every native and
yoked return mean on that same `C_pc` and

```text
Psi_p=(1/7)*sum_c[
       (J_ONLGR-J_RAW)_native,Cpc
       -(J_ONLGR-J_RAW)_yoked,Cpc].
```

This is learned-path/post-treatment common-support sensitivity to one
predeclared rotation, not a mediator, population causal contrast, or explanation
of the native effect.

### D10. Exact primary sensitivity statistics

For paired seed effects `d_s` in either `P` or `W`, use

```text
CI_97.5 = mean(d) +/- t_{0.9875,7}*sd(d)/sqrt(8).
```

Define the non-gating exact two-sided sign-flip value as

```text
p_flip=2^-8 sum_{epsilon in {-1,+1}^8}
       1[|mean_s epsilon_s*d_s| >= |mean_s d_s|],
```

including equality and explicitly conditional on sign exchangeability and the
observed effect magnitudes. Report all eight leave-one-seed-out values
`LOO_q=(1/7)*sum_{s!=q}d_s`; construct `W` inside each seed before deletion.
Never select a subset or alternate statistic after results. Secondary 95% gates
are conjunctive components of their named stronger claims and do not authorize
standalone omnibus claims.

### D11. Scientific activity and validity

Scientific activity begins at the earliest of:

1. a retained actor-parameter, critic-parameter, or optimizer-state update
   using any learned-arm task transition, including critic-only, `KEEP`-only,
   partial-schedule, or incomplete-mark learning; or
2. retention of any learned-arm trajectory or statistic for a claim-bearing
   result.

Complete four-schedule pairing, primary-arm coverage, and mark-by-role exposure
are validity/support conditions, not delayed activity boundaries. A discarded
dry run with no retained learned state or result remains preactivity.

For every native and IID seed/schedule cell, report for every learned arm the
number of agent-level routine rows with both marks legal and the stochastic
`KEEP`, voluntary `REFRESH-SAME`, and voluntary `REBIND` counts on those rows.
Masked deterministic `KEEP` and forced safety count toward none.

The full marked-ONLGR mechanism claim requires ONLGR, in every claim-bearing
cell, to have at least 64 such legal rows and execute at least four of each
stochastic action. A comparator's collapse remains a valid finite-budget
behavioral result and does not erase a complete primary return contrast; any
claim that directly compares nondegenerate marked behavior between arms must
apply the same `64/4/4/4` gate to every named arm. This distinction is part of
the frozen delta and must be checked in its re-review.

### D12. Oracle headroom and service-versus-cost gate

On the common first 16 paired deterministic episode indices define

```text
P16[s,a]=(1/7)*sum_c (1/16)*sum_{n=0}^{15} J[s,a,c,n]
barP16[a]=(1/8)*sum_s P16[s,a]
H_oracle=barP16[ORACLE]
         -max_{b in {TIMING-ONLY,FIXED-RATE,ALWAYS-KEEP,
                     ALWAYS-REFRESH,ALWAYS-REBIND}} barP16[b].
```

Require the diagnostic point gate `H_oracle>=0.02`; report every baseline value
and the maximizing baseline. This is registered-oracle headroom, not an
optimality or inferential superiority bound.

In `RAND-IID-4-16-32`, define

```text
S_IID[s,a]=(1/32)*sum_n (1/256)*sum_t service_t
C_IID[s,a]=(1/32)*sum_n (1/256)*sum_t
             (0.02*n_refresh_t+0.04*n_rebind_t)
R_IID[s,a]=S_IID[s,a]-C_IID[s,a].
```

Verify this decomposition exactly. In addition to the registered
ONLGR-versus-TIMING-ONLY IID return gate, a content-access service claim
requires

```text
mean_s(S_IID[s,ONLGR]-S_IID[s,TIMING-ONLY])>0
```

with a paired two-sided 95% lower confidence limit above zero. Otherwise report
content-dependent churn/cost regularization or unresolved decomposition, not
service improvement.

### D13. Claim ceiling and required wording

A passing `P` or `W` gate supports only the named finite-budget deterministic-
schedule ONLGR-versus-RAW normalized-return contrast. IID plus operational
partition support may add a useful eligible-exposure-link inductive bias when
next `k` is independent of visible history. The TIMING-ONLY return gate,
service gate, oracle headroom, and full marked-ONLGR activity gate may add only:

> Access to current binding, mismatch, and partner-content coordinates benefited
> the marked intervention policy beyond the registered task-content-blind
> tenure/cadence/own-action-state ablation on this host.

They do not identify event timing versus conditional mark selection. No result
can identify lease causality, `REBIND` causality, a literal hazard, RAW
incapacity, arbitrary `k`, variable `N`, UAV transfer, or a yoke-mediated
mechanism. Partition and yoke facts remain learned-output/post-treatment
support-conditioned diagnostics. Eligible-time diagnostics must distinguish
the virtual startup component from observed physical exposure.

## Closure and review trigger

The base revision is not mathematically closed. The composite

```text
ONLGR-PRO-PREACTIVITY-CORRECTION-20260812-01
+ ONLGR-PRO-PREACTIVITY-MATH-DELTA-20260812-02
```

must receive a new revision-bound mathematical re-review before the owner may
declare closure. Production and CM technical acceptance remain withheld until
that re-review returns and the owner reconciles it.

Any change to TIMING-ONLY inputs, the event/mark head structure, service or
headroom thresholds, yoke support, schedules, seeds, episodes, budget, or the
clauses above replaces this delta and retriggers Principles-to-Critic review.
