# Controller Disposition: R31-CFEI

Date: 2026-07-14

Source: GPT-5.6 Pro / ChatGPT web

Raw evidence: `RESPONSE_RAW.md`

Decision: **ACCEPT R31**

## Accepted Unique Route

R31 is Natural-window Causal Fixed-window Effect Information (`R31-CFEI`):

```text
natural stochastic R30 windows train the effect/context posteriors
forced stochastic skill branches audit causality reward-off only
fixed W = k0 persistent joint-position effect
signed detached endpoint reward enters low GAE only after the gate passes
```

The first Alice--Bob effect view is normalized agent positions only. Task
identity, button/target fields, contacts, phase, environment reward, actions,
agent identity, skill age, segment length, and OPT compact are excluded from the
target. Forced branches never train or score online reward.

The legacy one-step `TransitionSkillDiscriminator` remains diagnostic-only. In
R31 mode its online reward must fail closed; it cannot be mixed with CFEI.

Every genuine post-edit R30 check opens one exact `W=k0` natural window per
agent. Incomplete terminal or policy-update windows are invalid. Scoring uses
the posterior frozen after the previous rollout, then endpoint reward is
injected, low PPO runs, and only afterward the current natural windows update
the posterior. R30 high PPO remains sparse-task-only.

The signed reward, if later authorized, is interpreted as:

```text
clip(0.02 * stopgrad(delta_CFEI), -0.05, 0.05)
```

This resolves the response's typeset `clip` argument ordering without changing
its stated coefficient, signed score, or clipping boundary.

## Current Authorization

Authorized now: implementation plus the reward-off natural/forced causal gate
using M1 natural residual effect information and M2 between-skill versus
same-skill stochastic-repeat effect separation.

Not authorized yet: online R31 reward, the 160K `probe_only` versus
`real_reward` pair, seed expansion, shared-k comparison, S7, or HMASD parity.
Those become eligible only after the frozen reward-off gate returns PASS.

## Rejected Alternatives

- training the reward scorer on forced/counterfactual windows;
- replaying a fixed teammate action tape after state branches diverge;
- retaining the one-step transition reward as a second intrinsic term;
- using OPT compact or task fields in the first R31 target;
- environment potential shaping, RND, DADS, team reward, or coefficient sweeps;
- interpreting individual persistent effect as cooperative composition.
