# HMASD, OPT, and HA-CTSE Research Background

This document is the orientation layer for the GPT-5.6 Pro consultation. It
distinguishes source-paper ideas, historical HA-CTSE designs, accepted negative
evidence, and the current R29 research question. Where an older document in the
package conflicts with this document or `memory/CURRENT_WORK.md`, the newer
current files control.

## 1. Research problem

The project studies cooperative multi-agent reinforcement learning with sparse
team reward. The active benchmark is a six-UAV communication-service task, but
the algorithm must remain task-generic: coverage, backhaul, relay recovery,
QoS, and throughput are evaluation diagnostics and may not become intrinsic
reward inputs.

The long-term HA-CTSE hypothesis is that global information refresh and local
behavioral commitment should not be forced onto one clock:

```text
global interaction/check clock k
!= per-agent realized executable-skill lifetime T_i
```

Different agents may occupy different roles and therefore need different
behavioral persistence. The enlarged asynchronous policy class is useful only
if it can learn differentiated, persistent, and eventually cooperative skills;
merely permitting variable lifetimes is not enough.

## 2. What HMASD contributes

HMASD (Yang et al., NeurIPS 2023) is the primary hierarchical-skill reference.
Its relevant structure is:

```text
team skill Z
-> autoregressive individual assignment z_i | Z, z_1:i-1
-> low-level actor pi_l(a_i | o_i, z_i)
```

Every fixed high-level interval, the coordinator samples a synchronized team
skill and individual skills. Autoregressive assignment allows later agents to
condition on earlier assignments, encouraging complementary roles. The
low-level actor receives only local observation and individual skill.

HMASD also supplies dense exploration/skill pressure through team and
individual discriminators, approximately `log q_D(Z|s)` and
`log q_d(z_i|o_i,Z)`, together with skill/action entropy in its variational
objective. Its ablations indicate that the hierarchy, discriminator-derived
intrinsic pressure, and autoregressive coordinator are load-bearing. The
project therefore treats HMASD's important contribution as a closed internal
drive that makes sampled latents executable and behaviorally meaningful, not
as a classifier architecture to copy mechanically.

Limits of direct transfer:

- HMASD assumes synchronized refresh, whereas HA-CTSE's purpose is asynchronous
  individual persistence.
- Same-check autoregressive prefixes become sparse when only one or two agents
  renew, so HMASD coordination semantics cannot simply be retained unchanged.
- Single-step label recovery can exploit state/context or scheduling shortcuts
  and does not establish persistent behavioral effect.
- A discriminator on a recognized deterministic state feature is vacuous; a
  sampled commitment latent and a recognized situation representation have
  different mathematical roles.

## 3. What OPT contributes

OPT (Liu et al., TPAMI 2024) is an interaction-representation reference, not a
hierarchical controller. It decomposes entity interactions into sparse and
diverse prototypes, using sparsemax-style selection, contrastive disagreement,
and aggregation weights `omega` to form a compact interaction representation
`c`.

Conceptually:

```text
(state, joint observations)
-> interaction prototypes and omega
-> compact descriptive representation c
```

OPT recognizes interaction structure; it does not select a team commitment or
an executable skill. The project initially tried to derive a team code directly
from `c`, but learned that a bottom-up description is not automatically a
top-down intervention. If no objective requires the derived code to affect
decisions, it becomes decorative.

The accepted division of labor is therefore:

```text
OPT-like substrate: recognize current interaction structure
sampled hierarchy: choose commitments/responses
low-level skill: execute z_i through pi_l(a_i | o_i, z_i)
```

The current R29 question does not modify or reward the OPT representation. OPT
remains context/recognition substrate and historical motivation for separating
description from control.

## 4. HA-CTSE innovation starting point

HA-CTSE began from two observations:

1. HMASD's synchronized fixed interval can be a poor inductive bias when agents
   require different persistence.
2. Removing synchronization also removes or weakens the very coordination and
   intrinsic-pressure mechanisms that made HMASD learn.

The intended synthesis is not "HMASD plus OPT." It is:

```text
recognize interaction structure globally
-> maintain asynchronous individual skill processes
-> rebuild a task-generic intrinsic drive compatible with those processes
-> later recover complementary team composition without bypassing skills
```

The durable low-level invariant is:

```text
a_i ~ pi_l(a_i | o_i, z_i)
```

Compact context, team code, recognized situation, and communication-specific
features must not enter the low-level actor directly. Otherwise `z_i` ceases to
be the executable bottleneck and the hierarchy degenerates into contextual
flat control.

## 5. Design evolution and accepted negative evidence

### Process-posterior phase

Early HA-CTSE variants attempted to classify active skill from variable-length
process segments and use that posterior as intrinsic reward. Across several
rounds, apparent signal was dominated by duration, segment length, reward sum,
agent identity, or context. Future-outcome and topology-role residual variants
also failed to produce a reliable, task-generic positive reward. These failures
rule out adding more classifier heads or relaxing shortcut controls.

### Recognition and team-intent phase

OPT-like recognition substrate showed useful dwell/outcome/role structure, but
naively forcing renewal on recognized situation changes caused synchronized
churn. A later sampled team-intent design was autopsied: forced-team-code
assignment KL was about `0.002` both at initialization and after training, so
the channel was architecturally and objectively decorative. Its near-episode
lifetime also collapsed the intended two-clock distinction. The current work
does not revive team reward or team intent while individual-skill use remains
unresolved.

### R24/R25 constraints

Frozen individual/team discriminator null probes largely collapsed, so the old
`q_d/q_D` line remains blocked. A q_A/actionability reward arm did not beat the
architecture-only R25 arm0 reference late in training, so q_A is default-off
and is not part of R29.

### R26: natural observational negative

Natural rollouts from mature R25 policies did not show robust process-level
individual skill differentiation. This is preserved as evidence that the
current policy does not naturally use its skill channel strongly enough.

### R27: forced causal capacity positive

R27-G1/G2 intervened on the individual skill while holding the mature policy
fixed. Persistent forced `z_i` changed action distributions and local
trajectories through the native horizon. This proves that the recurrent
low-level actor has conditional skill capacity:

```text
forced persistent z_i -> distinct action/trajectory effect
```

It does not prove natural selection, reward usefulness, cooperation, credit,
or task improvement. The key scientific state is therefore "capacity exists,
natural use is missing."

### R28: support failure of the forced scorer

R28 learned a process/action scorer on forced deterministic trajectories and
passed its internal nulls. Online reward integration then encountered severe
support mismatch. A paired transport diagnostic changed only environment
execution from deterministic to policy-matched stochastic actions:

```text
deterministic OOD = 0.068359
stochastic OOD    = 0.823242
```

Random action execution alone reproduced the temporal action-standard-
deviation shift. The forced-deterministic R28 scorer family is retired from
online reward use. It may not be refit, widened, threshold-relaxed, or renamed.

### R29: support-native action information

R29 avoids a separately trained scorer. At the actual natural on-policy
observation and stored pre-step recurrent state, it evaluates the executed
action under every counterfactual skill-conditioned policy. The current-skill
log likelihood is compared with their uniform mixture. Because every candidate
uses the same squashed action, the tanh Jacobian cancels.

All three mature checkpoints passed the reward-off target gate. The signal is
small but consistently positive and skill-wide; inactive-FiLM controls are
zero. This establishes an on-support policy-native differentiation statistic,
not its usefulness as reward.

## 6. Current implementation semantics

For rollout row `(o_t, h_t, z_t, a_t)`, R29 computes:

```text
r_AI = log pi_theta(a_t | o_t, h_t, z_t)
       - log [ (1/K) sum_z' pi_theta(a_t | o_t, h_t, z') ]
```

Implementation boundaries:

- `o_t`, pre-step recurrent actor state `h_t`, executed `a_t`, actual `z_t`,
  and old PPO log likelihood come from the collection rollout.
- All skill counterfactuals start from the same `(o_t,h_t)`.
- The actual-skill recomputed squashed log likelihood must match PPO's stored
  old likelihood within `2e-5`; otherwise the run fails closed.
- The score is detached before PPO. Current scaling is
  `clip(0.05 * r_AI, -0.05, 0.05)`.
- `probe_only` computes metrics without modifying reward; `real_reward` adds the
  score only to primitive low-level rewards before low-level GAE.
- High-level segment return, high policy/critic, collector, environment,
  skill-renewal decisions, and team mechanisms are unchanged.
- The feature is default-off.

## 7. Core considerations for innovation

The next algorithm must satisfy all of the following simultaneously:

1. **Support-native:** operate on natural on-policy data without importing a
   forced/deterministic trajectory support envelope.
2. **Task-generic:** no communication field or environment reward may define
   the intrinsic target.
3. **Skill-bottleneck preserving:** the low actor remains
   `pi_l(a_i|o_i,z_i)`.
4. **On-policy correct:** reward uses the collection policy and stored recurrent
   state; executed actions and PPO likelihood semantics must align.
5. **Persistent rather than cosmetic:** instantaneous action separation is not
   enough; the mechanism should plausibly create temporally coherent effects.
6. **Non-shortcut:** it must not reduce to duration, agent, usage-frequency, or
   context classification.
7. **Scale-safe:** intrinsic reward is a bootstrap signal, not a replacement for
   environment reward or a source of destructive PPO ratios.
8. **Causal economy:** change one mechanism and compare it with a matched
   reward-off/probe control. Do not substitute a sweep or another probe family.

## 8. The unresolved R29 tension

R29 is attractive because it is exact, online, policy-native, and avoids a
learned discriminator. Its weakness is equally clear: it measures conditional
action separation at one visited state. It may reward arbitrary mean or
variance separation, remain self-referential as the policy changes, and ignore
whether differentiated actions create persistent state effects or useful team
behavior. The uniform skill mixture is also not the learned skill marginal.

The immediate research decision is therefore not whether the implementation is
well tested. It is whether this objective is the right mathematical bridge
from R27's latent capacity to natural, persistent, useful skill behavior—and,
if not, what single support-native replacement best follows from the evidence.
