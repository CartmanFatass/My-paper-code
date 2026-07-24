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
