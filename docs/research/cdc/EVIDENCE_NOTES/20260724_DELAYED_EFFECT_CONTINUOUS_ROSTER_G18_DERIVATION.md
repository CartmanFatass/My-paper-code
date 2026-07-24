# Delayed-effect continuous roster G18 derivation

Date: 2026-07-24

## Accepted premise

Formal G17 establishes a usable continuous dynamic-roster controller only when
the source scores the current action immediately and actor credit uses
`gamma=0`. Its held-out utility LCB is `0.93726` and its conditional demand
mapping is strong. That result is closed and is not rerun or relabelled here.

The next target is policy-dependent future service availability: present
effort may change later battery, charging need, backlog or actuator capacity.
This is the nearest missing capability before any UAV promotion.

## Counterexamples

### CE-GAMMA0-FUTURE-BLIND

Take two current actions with equal current service reward but different energy
use. One leaves enough battery for a later high-value service interval and one
does not. With `gamma=0`, both receive the same actor advantage regardless of
how exactly battery is observed or encoded. A better representation cannot
repair a deliberately omitted future consequence.

### CE-LONG-GAE-EXOGENOUS-NOISE

G17 empirically shows the opposite failure. With `gamma=0.99, lambda=0.95`,
independently resampled later demand was attributed to the current action and
the policy learned a near-constant mean. More exposure, exploration-scale
changes, a direct observation residual and active-count curriculum did not
repair it. Restoring the full long GAE trace is therefore not the default
future-credit solution.

### CE-INACTIVE-ROW-CREDIT-LEAK

When a member leaves for charging, team reward continues while that lifecycle
row has no physical action. Assigning those rewards to inactive likelihoods can
create apparent charging credit without a causal action. Any future source must
keep inactive likelihood exactly zero, preserve the lifecycle row according to
the declared leave/rejoin contract, and attach later value only through a state
transition caused while the member was active.

## Smallest algorithm correction

The minimal candidate is one-step TD actor credit:

```text
delta_t = r_t + gamma * (1-terminal_t) * V(s_{t+1}) - V(s_t)
actor_advantage_t = delta_t
gamma=0.99
gae_lambda=0.0
```

Unlike `gamma=0`, this admits the value of the next policy-dependent state.
Unlike long GAE, it does not explicitly accumulate a tail of later TD errors
into the current actor update. The critic still propagates longer consequences
recursively. This is not proof of lower variance or UAV success; it is the
smallest algebraic bridge worth testing.

Necessary conditions for a delayed-effect source are:

1. the current action changes a persisted next-state quantity;
2. that quantity is visible to the critic and only causally available fields
   are visible to the actor;
3. an exact constructive controller establishes source access;
4. a current-reward-only controller is a real counterexample, not merely a
   weaker implementation;
5. leave/rejoin, fresh join and terminal leave retain explicit state ownership;
6. source controls, replay, inactive likelihood and checkpoint identity remain
   fail-closed;
7. success is measured by external service/availability utility, not a custom
   reward for charging or battery diversity.

## Scout boundary

The UAV environment's motion power, charging-station geometry, queueing, radio
state, safety reward and metric duplication are semantically coupled and are
excluded. G18 may reuse only generic active-mask/lifecycle bookkeeping,
bounded continuous actions, vectorized state arithmetic and the existing GAE
formula. The delayed toy will be a fresh module if the credit candidate passes.

## Cheapest next separating action

Before constructing a new battery source, run one bounded nonformal
compatibility screen on the already identified G17 immediate source:

```text
candidate=ONE_STEP_TD_BOOTSTRAP_G18
gamma=0.99
gae_lambda=0.0
current_observation_residual=true
initial_log_std=-1.0
learning_rate=1e-3
updates=100
num_envs=8
ppo_passes=2
eval_episodes_per_domain=48
model_seed=1918000
train_ledger_seed=1928000
action_seed=1938000
evaluation_ledger_seed=1948000
evaluation_action_seed=1958000
formal=false
```

The fixed selection gate is source/replay/finite closure plus IID and held-out
means at least `0.90`, joint gain at least `0.10`, minimum episode at least
`0.80`, both effort/mix correlations at least `0.90`, and both MAEs at most
`0.05`. Passing licenses only a fresh delayed battery/charging toy prototype.
Failure retires this exact TD(0) candidate without seed, budget, threshold or
hyperparameter tuning. The screen consumes zero conclusion-bearing iterations.

## TD(0) compatibility disposition

The exact bounded screen completed operationally on CPU with one thread and
selected `NONFORMAL_TD0_NOT_COMPATIBLE_G18`. Replay error was exactly zero and
the lifecycle/finite checks closed, but the candidate reached only:

```text
iid_mean=0.7116935448
heldout_mean=0.7110608015
gain_mean=0.1252746248
minimum_episode=0.5713264087
minimum_effort_correlation=0.2095120069
minimum_mix_correlation=0.6283625645
maximum_effort_mae=0.1169463049
maximum_mix_mae=0.1099299892
```

Thus next-state bootstrap alone does not preserve the already identified
immediate conditional mapping. `ONE_STEP_TD_BOOTSTRAP_G18` is retired without
retry, tuning or formal iteration cost. The earlier “smallest algorithm
correction” is retained as a tested counterexample, not an active candidate.

## Delayed-source information gate

A fresh twelve-step toy now isolates the missing causal structure without UAV
physics. Four members serve low demand for six steps. Two announced rotation
members then leave to charge exactly when demand doubles for four steps; they
rejoin with one fresh lifecycle while one persistent lifecycle leaves
terminally. Battery is persisted by lifecycle, inactive rows receive no action,
and external utility is only served-demand fraction.

The structural gate passes across three slot permutations:

```text
branch=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
constructive_minimum_utility=1.0
myopic_maximum_utility=0.8333333333
minimum_constructive_minus_myopic=0.1666666667
immediate_service_equal=true
next_persistent_battery_delta=0.25
natural_utility=1.0
intervened_utility=0.9583333333
intervened_future_service_deficit=0.5
slot_permutation_invariant=true
formal=false
iteration_consumed=false
```

The current reward at the intervention is identical, but allocating the same
service to a persistent instead of soon-charging lifecycle changes the next
battery state and later spike service under the same continuation. This closes
action-dependent transition, sequence intervention, natural mediation,
simpler-myopic resistance and anonymous slot-transport requirements at the toy
information boundary.

The next bounded algorithm action is
`FAST_SLOW_SEPARATED_CREDIT_G18_ALGEBRA_PROTOTYPE`: retain an immediate reward
residual as the proven G17 actor channel and add a separately centered
successor-value residual for delayed state consequences. It may not use battery
fields in the credit rule, tune the retired TD(0) screen or launch formal
compute before a new evidence contract is frozen.

## Fast/slow algebra disposition

The environment-neutral algebra passed ten focused tests. It preserves a
detached immediate reward residual and adds a separately centered detached
one-step successor-value residual. Terminal bootstrap, discounted slow returns,
inactive likelihood zero, G17/G18 replay and gradients to all three critic heads
closed exactly. No source-specific field enters the credit rule.

The smallest next action is now the frozen nonformal dual-source screen in
`docs/research/designs/FAST_SLOW_SEPARATED_CREDIT_G18.md`. It must demonstrate
both preservation of G17 conditional access and acquisition of the G18 delayed
battery mechanism before any formal contract is prepared. This algebra action
and its bounded screen consume zero conclusion-bearing iterations.

## Dual-source screen disposition

The exact raw-sum screen completed operationally but selected
`NONFORMAL_NO_G17_COMPATIBILITY_SEPARATED_CREDIT_G18`. G17 held-out utility was
`0.63199`; effort and mix correlations were `-0.23714` and `0.04159`. G18
utility was `0.83639`, spike utility `0.50446`, and rotating low-phase effort
share `0.43389`. The candidate is retired without tuning.

The next smallest correction keeps the same two residuals but normalizes their
actor losses separately before fixed equal-weight composition. This directly
tests channel-scale interference without changing the source, credit inputs,
seeds, budget, thresholds or UAV boundary.

The channel-normalized algebra passed eleven focused tests, including exact
invariance to independent positive rescaling of either advantage channel. Its
bounded paired screen is frozen in
`docs/research/designs/CHANNEL_NORMALIZED_SEPARATED_CREDIT_G18.md`.

The screen validly selected
`NONFORMAL_NO_G17_COMPATIBILITY_CHANNEL_NORMALIZED_G18`. It improved G17
held-out utility from `0.63199` to `0.74175` and mix correlation from `0.04159`
to `0.83400`, but did not preserve the accepted immediate mapping. The next
smallest discriminator isolates the slow value critic from actor representation
parameters while preserving the normalized credit channels and full protocol.

The actor/critic-isolation algebra passed twelve focused tests. In particular,
the slow value loss has finite gradients on the independent critic and exactly
no gradient on actor representation or heads. The unchanged paired screen is
frozen in `ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18.md`.

That paired screen selected
`NONFORMAL_ACTOR_CRITIC_ISOLATED_CREDIT_PROMISING_G18`: G17 held-out utility was
`0.92512`, G18 utility `0.97256`, spike utility `0.91657`, and rotating effort
share `0.91285`, with exact replay. The candidate advances to the frozen formal
dual-source contract; no UAV or usable-algorithm conclusion is drawn yet.

## Formal dual-source disposition

Formal iteration 19 completed operationally and selected
`NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18`. The G18 delayed-source gates all
passed with utility LCB `0.98807`, spike-utility LCB `0.96421` and
rotating-effort-share LCB `0.96242`. The earlier nonformal delayed mechanism was
therefore real rather than a single-seed artifact.

However, G17 IID and held-out LCBs were `0.88129` and `0.87025`; minimum effort
correlation was `0.84290` and maximum effort MAE was `0.05746`. The isolated
critic is insufficient because successor-channel actor gradients can still
overwrite the immediate controller. This exact G18 family is closed without
tuning. The smallest new question is whether the G17 policy can be retained as
an explicit fast anchor while a zero-initialized residual alone receives
delayed actor credit.
