# Anchor-policy conditional action advantage (G20R)

```text
status=DESIGN_FROZEN_BOUNDED_SCREEN
algorithm=ANCHOR_POLICY_ACTION_ADVANTAGE_G20R
supersedes=ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20
authority=external_pro_20260724_g20_credit_rule_zero_fixed_point_r2
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

This note is the evidence action Pro scheduled in
`docs/external-review/rounds/20260724_g20_credit_rule_zero_fixed_point_r2/21_PRO_OPEN_RAW.md`,
section 9. It freezes the repaired estimator before any behavioural screen. It
adopts Pro's decision and adds no scientific authority of its own; every
engineering choice below is Project-Manager owned and marked where it is a free
choice rather than a consequence.

## What changed, and what did not

Retired: the leave-one-out contrast over the centered residual table. It is
inert at the entry state the design itself mandates — established in
`docs/research/cdc/EVIDENCE_NOTES/20260724_CENTERED_COUNTERFACTUAL_RESIDUAL_G20_ZERO_FIXED_POINT.md`
and confirmed by Pro.

Retained unchanged: the exact-zero fast anchor and its bitwise fast-parameter
freeze, exact active-set centering of the applied pre-tanh residual, the G17 and
G18 sources, rewards, observations, active masks, lifecycle contracts, tanh
Gaussian sampling and exploration scale, and the deletion of gradient
projection. Adam everywhere. The base `ContinuousRosterPolicy` file stays
untouched.

Changed: **what carries member-resolved credit**. Not the correction
representation, but the member's executed action.

## 1. The action variable carrying credit

Credit attaches to the **executed environment action** — the post-tanh requested
effort actually submitted to the source, before battery clipping. The residual
table is one parameterization of how the action distribution is shifted; it is
not what depletes battery or produces service. In G18 the transition and reward
are functions of requested and battery-clipped executed effort.

The residual head remains the only trainable actor surface: it shifts the
pre-tanh mean, so the executed action's log-probability depends on it, and that
is the gradient path.

## 2. The token decision history

The policy is token-factorized: members are routed in a frozen anonymous order
and each member's action is sampled conditioned on the prefix. For member at
routing position `j` at environment step `t`, the decision history `h_{j,t}` is
exactly:

- the critic state and the member's local observation;
- the active mask and the anonymous active-set context;
- the member's lifecycle state and per-member recurrent state;
- the routing position `j`;
- the action prefix — every action already sampled at this step for positions
  `< j`.

`h_{j,t}` **excludes** `a_{j,t}` itself and every action at positions `> j`.

## 3. Estimator

Post-token slow action-value, suffix marginalized:

```text
Q_j(h_{j,t}, a_{j,t}) = E_suffix~pi [ G^slow_t | h_{j,t}, a_{j,t} ]
```

Anchor baseline, an **expectation under the frozen anchor policy** rather than a
single deterministic anchor action (Pro's preferred form):

```text
b_j(h_{j,t}) = E_{a~pi_0(.|h_{j,t})} [ Q_j(h_{j,t}, a) ]
```

Member-resolved slow advantage, detached, multiplying only that token's
likelihood ratio in the PPO clip surrogate:

```text
A_slow[j,t] = Q_j(h_{j,t}, a_{j,t}) - b_j(h_{j,t})
```

Inactive rows receive exactly zero credit and contribute no term.

The deterministic variant `Q_j(h_j, a_j) - Q_j(h_j, a_j^anchor(h_j))` is **not**
adopted. Pro records it as a lower-cost ablation that is more sensitive to
critic extrapolation and exploration scale; it is out of scope for this screen
and is not a fallback if the primary underperforms.

### Free engineering choices

| Choice | Value | Why |
|---|---|---|
| baseline sample count `K` | `8` per active token | a critic forward, not a rollout; `K=8` keeps baseline noise well under the observed advantage spread |
| advantage held across PPO passes | fixed at collection | mirrors how G19/G20 fixed `old_*` fields; avoids drift within an update |
| normalization | masked mean and `unbiased=False` std over active tokens in the update batch, `eps=1e-8` | unchanged from G20 |

## 4. Suffix marginalization, and the continuation policy

`Q_j` is realized as a **prefix critic**: it consumes the critic state, the
active mask, the routing position `j`, and the action prefix through and
including position `j`, and regresses the realized slow return.

Because the suffix was sampled on-policy at collection time, regressing on the
realized return marginalizes the suffix automatically under the policy that
generated it. No explicit suffix rollout is performed.

The continuation policy defining `Q_j` is therefore the **current delayed-phase
policy at collection time**, held fixed across that update's PPO passes. This is
the on-policy requirement: `Q_j` is not reused across collections.

## 5. Critic inputs, horizon, detach boundaries

- **Inputs**: `(critic_state, active_mask, position j, action prefix ≤ j)`.
  Never the residual table, and never a member identity beyond routing position.
- **Target**: discounted slow return, `gamma = 0.99`, terminal bootstrap zero —
  the same construction as the closed G19 slow-return target.
- **Detach**: `A_slow` is detached before it weights any score. The `Q_j`
  regression is detached from the residual head — the prefix it consumes is a
  collection-time constant. Every fast parameter including `log_std`, the base
  critic and the immediate baseline head is frozen in the delayed phase.

## 6. Baseline independence — analytic

`b_j` is a function of `h_{j,t}` alone, and `h_{j,t}` excludes `a_{j,t}` by
construction. Therefore

```text
E[ grad_theta log pi_theta(a_j | h_j) * b_j(h_j) ] = 0
```

and subtracting it introduces no score-function bias. This is structural, not
empirical: it holds because the baseline never receives the factual token.

This is precisely what the retired full-table form violated. Holding every other
factual row fixed lets later actions — which may descend from `a_j` — enter the
baseline, making it action-dependent.

## 7. Pre-freeze design check

Run per `AGENTS.md` → *Pre-freeze design check*, before freezing, on a throwaway
probe with a deliberately action-sensitive synthetic `Q`. Both rules evaluated
at the **identical** mandated entry state (residual output layer exactly zero):

```text
retired rule  — leave-one-out over the residual table
  max |A_slow|                    = 0.0

revised rule  — executed action vs anchor-policy baseline
  max |A_slow|                    = 1.469231
  per-member std across samples   = [0.4862, 0.2041, 0.2525, 0.1628]
  per-member mean (expect ~0)     = [-0.0206, 0.0161, 0.0058, -0.0000]
  inactive row exactly zero       = True

gradient reaching the residual head at entry
  max |d loss / d residual|       = 0.31272459
  per-member gradient             = [-0.263068, 0.312725, -0.048397, -0.001260]
```

Answering the five questions:

1. **Signals at the mandated initial state** — advantage nonzero and
   member-distinct; the retired rule is exactly zero on the same setup.
2. **Live gradient path at entry** — yes, `0.3127`, member-distinct. The
   per-member gradients sum to approximately zero, as the centering operator's
   Jacobian requires.
3. **Trivially satisfied invariants** — none found. Zero-residual equivalence
   still holds exactly, but it no longer implies zero credit.
4. **Result branch firing for a non-scientific reason** — one was found and is
   fixed in section 9: the old branch order would classify a non-identified
   action critic as behavioural no-access. A dedicated branch now precedes it.
5. **Initialization cancelling the credit definition** — no. The baseline is an
   expectation over resampled anchor actions, so it cannot coincide with the
   factual action except on a measure-zero event.

The probe also caught a defect **in itself** worth recording: with the sampled
action left differentiable through the mean, the score cancels analytically and
the gradient reads a false `0.0`. Detaching the action, exactly as replay sees
it, is what the numbers above use.

Limit: this check settles what a derivation or probe settles. It cannot
establish that a *learned* critic will identify action dependence — that is
section 9's branch, and it needs data.

## 8. Bounded screen

Paired dual-source protocol, phase counts, evaluation sizes and thresholds
mirror the G20 screen exactly; Pro authorized reusing the numerical thresholds
because the source, compatibility claim and delayed-mechanism claim are
unchanged. Only the estimator and the seeds differ.

```text
replicates=1
num_envs=8
ppo_passes=2
g17_fast_updates=100
g17_delayed_updates=100
g18_fast_updates=100
g18_delayed_updates=300
g17_eval_episodes_per_domain=48
g18_slot_permutations=3
baseline_samples_K=8
formal=false
```

Fresh seeds, disjoint from every earlier package including G20:

```text
g17_model=2819000
g17_train_ledger=2829000
g17_action=2839000
g17_evaluation_ledger=2849000
g17_evaluation_action=2859000
g18_model=2919000
g18_action=2939000
```

## 9. Re-registered result system

Pro ruled the previous mapping does not survive. First match wins.

1. `INVALID_ANCHOR_ACTION_ADVANTAGE_G20R` — operational, replay, lifecycle,
   source-control, centering, zero-residual-equivalence or gradient-ownership
   failure; **or** a structurally zero residual gradient at delayed entry;
   **or** a baseline observed to depend on the factual token.
2. `NONFORMAL_NON_IDENTIFIED_ACTION_CRITIC_G20R` — the learned `Q_j` does not
   identify action dependence: the mean over active tokens of the spread of
   `Q_j` across the `K` resampled anchor actions is below `0.01 x` the standard
   deviation of the realized slow return. **This branch precedes every
   behavioural branch**, so a critic that never learned action sensitivity is
   never reported as absence of delayed access.
3. `NONFORMAL_NO_G17_COMPATIBILITY_ANCHOR_ACTION_G20R` — unless final G17 IID
   and held-out means are at least `0.90`, gain over zero at least `0.10`,
   minimum episode at least `0.80`, both mapping correlations at least `0.90`,
   and both MAEs at most `0.05`.
4. `NONFORMAL_NO_DELAYED_ACCESS_ANCHOR_ACTION_G20R` — unless final G18 utility
   is at least `0.95`, gain over its frozen fast anchor at least `0.10`, and
   spike utility at least `0.90`.
5. `NONFORMAL_NO_DELAYED_MECHANISM_ANCHOR_ACTION_G20R` — unless rotating-member
   low-phase effort share is at least `0.75`.
6. `NONFORMAL_ANCHOR_ACTION_ADVANTAGE_PROMISING_G20R`.

Only branch 6 licenses preparing a formal contract. No branch supports a UAV
claim, a variable-period claim, or reopening a closed candidate. No same-package
retry or hyperparameter sweep.

## 10. Smallest propositions

**Smallest supported by branch 6** — on the Q4-scoped registered G18 source, an
anchor-relative conditional action advantage over a frozen fast anchor can carry
member-resolved delayed credit while preserving the accepted G17 immediate
mapping. It supports nothing about variable periods, UAV transport, or delayed
sources whose optimum changes the immediate aggregate.

**Smallest refuted by branch 4 or 5** — this anchor-relative action-credit
realization is insufficient on the registered G18 source. It does **not** retire
active-set centering, per-agent counterfactual credit as a class, P2 as a
candidate, or the exact-zero anchor.

**Refuted by branch 2** — nothing scientific. A non-identified critic is an
estimator failure and licenses no update to P2.

## 11. Proof-sized acceptance

- exact zero-residual equivalence to the base policy under deterministic,
  sampled and teacher-replay modes;
- exact active-set centering: applied residual sums to zero over active members
  per coordinate and batch row (tolerance `1e-6`); inactive rows exactly zero;
- baseline independence: `b_j` is computed from a tensor set that provably
  excludes `a_{j,t}`, asserted structurally, and `b_j` is unchanged when
  `a_{j,t}` alone is perturbed;
- non-inertness: at an exactly zero residual output layer with an
  action-sensitive `Q_j`, the advantage is nonzero and member-distinct and the
  residual gradient is nonzero — the direct regression against the retired rule;
- gradient ownership: the delayed actor loss and the `Q_j` regression have no
  gradient on fast actor parameters, `log_std`, base critic or baseline heads;
  the `Q_j` regression has none on the residual head;
- prefix integrity: `Q_j` receives no action at position `> j`;
- exact replay and inactive-row zero likelihood on both sources with a nonzero
  residual active;
- one finite update per phase; the delayed phase begins exactly once with an
  exactly zero residual output layer;
- first-match branch precedence, including that branch 2 precedes branch 4.

## 12. Files

- `ha_ctse_process/anchor_action_advantage_g20r.py` — policy subclass, prefix
  critic `Q_j`, anchor-baseline advantage, both update rules;
- `scripts/screen_anchor_action_advantage_g20r.py` — bounded paired screen
  writing `result.json` under
  `logs/nonformal_anchor_action_advantage_g20r_<date>_<commit>_pm1/`;
- `tests/ha_ctse_process_anchor_action_advantage_g20r_test.py` — the proofs
  above.

`ha_ctse_process/continuous_roster_policy.py`, both source modules, and every
closed G17/G18/G19/G20 artifact remain unchanged evidence at their commits. The
retired `ha_ctse_process/centered_residual_g20.py` package stays in the tree as
the evidence that produced the fixed-point finding; it is not extended.
