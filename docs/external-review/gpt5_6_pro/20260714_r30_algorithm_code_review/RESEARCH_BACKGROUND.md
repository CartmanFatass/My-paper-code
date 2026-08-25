# R30 Review Background

## Research Objective

HMASD uses a fixed synchronized high-level interval and obtains useful
cooperative structure from a team skill, autoregressive individual skill
assignment, a skill-conditioned low-level discoverer, discriminator-style
semantic pressure, and entropy/exploration terms.

HA-CTSE keeps the low-level skill bottleneck but asks a different temporal
question:

```text
global information/check clock k0
!=
per-agent realized skill lifetime T_i
```

Different agents may need different lifetimes under stable relay, tracking,
recovery, or other general cooperative roles. The intended contribution is not
merely a larger duration action set. It is asynchronous skill processes that
remain learnable, differentiated, and useful under sparse team reward.

## Role Of OPT

OPT provides a compact interaction context:

```text
c_tau = f_OPT(state, joint observations)
```

Its sparse/diverse prototypes summarize interaction structure. `c_tau` is not
an executable team skill and may not bypass individual skill conditioning in
the low actor. HA-CTSE may use `c_tau` as high-level context while preserving:

```text
a_i,t ~ pi_l(a_i,t | o_i,t, z_i,t)
```

The current standalone implementation contains its own OPT-style compact
encoder; `hmasd/networks.py` and `hmasd/ha_ctse.py` provide the earlier HMASD /
OPT integration reference.

## Current Pre-R30 Temporal Implementation

The active source setting uses six agents, four skills, `k0=10` primitive
steps, and duration candidates `{1,2,3,4}` check blocks. The current high policy
samples:

```text
pi(skill, duration | context)
= pi_skill(skill | context) * pi_duration(duration | context)
```

Only expired agents enter the autoregressive selection loop. A chosen duration
sets a countdown; completed variable-length process segments become the high
PPO samples. This creates three structural problems:

1. the same check does not contain a policy token for every agent;
2. short lifetimes generate more high-policy samples per environment time;
3. duration can become a shortcut for skill identity.

## Accepted R30 Direction

R30 removes duration as an action. Every `k0` check contains an ordered token
for every agent:

```text
KEEP or SET(other_skill)
```

Actual lifetime is the run length of `KEEP`. The applied working roster gives
later agents the skills retained or selected by earlier agents, restoring a
complete MAT-style autoregressive joint decision at each check without forcing
every agent to switch.

High learning moves from variable segments to fixed check transitions. Low
process segments continue across `KEEP` and close on `SET`, episode terminal,
or policy-update invalidation.

## Evidence That Constrains The Semantic Side

- R27-G2 showed that forced persistent skills have conditional execution
  capacity and can induce a local effect. This was forced evidence, not natural
  skill use.
- Natural R26 observations did not establish stable realized differentiation.
- R29-G0 found natural state-conditional action information, but the R29-T10
  online reward produced a valid single-seed preliminary failure: it did not
  preserve the natural process signal and failed task safety.
- Therefore actor-density separation is diagnostic-only. R30 must not restore
  it or add a new semantic reward.

R30 only preserves a clean future semantic interface: equal-length `W=k0`
windows, skill-only and duration-blind, task-generic realized effects, low GAE
only. Conditional switch-skill entropy preserves label supply but cannot prove
behavioral meaning.

## Scope Of This Review

The requested decision is whether R30 is the correct temporal controller and
how to implement it safely in the current code. Team intent/reward,
communication-specific intrinsic shaping, `q_d/q_D`, DADS, and post-R29 effect
target selection are out of scope.
