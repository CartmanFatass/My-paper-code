# Immediate-tangent protected full actor G27 derivation

Date: 2026-07-24

## Accepted evidence

Formal G18 proves that an unrestricted full actor with independently normalized
immediate and successor credit learns every delayed battery gate, but it fails
G17 compatibility across fresh seeds. G23--G26 protect the fast actor exactly,
yet their additive residual representations cannot close the accepted delayed
mapping. The remaining bottleneck is not source access but the choice between
full capacity and immediate-policy protection.

## Counterexamples

### CE-EQUAL-CHANNEL-WEIGHTS-DO-NOT-PROTECT-IMMEDIATE-BEHAVIOR

Two equally weighted normalized losses can have opposing actor gradients. Their
sum may reduce the immediate objective even though its scalar weight is fixed.
This matches the formal G18 G17 failure.

### CE-FROZEN-ANCHOR-PROTECTION-CAN-REMOVE-NEEDED-CAPACITY

Bitwise anchor preservation prevents catastrophic overwrite but forces all
delayed correction through a small additive head. G25 and G26 reject both local
and prefix-contextual versions under the same representation gate.

### CE-FIRST-ORDER-PROTECTION-IS-NOT-A-GLOBAL-GUARANTEE

Projecting a successor gradient into the immediate tangent half-space prevents
a locally opposing step; it does not guarantee final G17 compatibility. The
unchanged first-match G17 behavioral battery remains authoritative.

## Smallest new algorithm

`IMMEDIATE_TANGENT_PROTECTED_FULL_ACTOR_G27` keeps the two-phase fast anchor,
state-only slow critic/baselines, independently normalized immediate and
successor PPO channels, action distribution, replay and sources. In the delayed
phase it enables the complete base actor (member/context encoders, recurrent
core, action head, current-observation residual and `log_std`) while keeping the
unused core critic and every G19/G26 residual frozen.

For the ordered actor parameter tuple, compute channel gradients `g_i` and
`g_s`. Apply:

```text
g_s' = g_s                                      if <g_s,g_i> >= 0
g_s' = g_s - <g_s,g_i>/||g_i||^2 * g_i         otherwise
g_actor = 0.5 * (g_i + g_s')
```

If `||g_i||=0`, no projection is applied. Critics receive only their existing
detached state-only losses through a separate optimizer. No residual output,
oracle label, source field or future actor input is added.

## Bounded screen contract

Retain the G19--G24 paired budgets and thresholds:

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
formal=false
```

Fresh seeds:

```text
g17_model=3919000
g17_train_ledger=3929000
g17_action=3939000
g17_evaluation_ledger=3949000
g17_evaluation_action=3959000
g18_model=4019000
g18_action=4039000
```

Operational validity requires exact channel normalization, actor/critic
optimizer ownership, frozen zero residual and core critic, finite updates,
replay at most `1e-6`, lifecycle/source closure, and every projected successor
dot immediate at least `-1e-7`. Record conflict frequency and pre/post dots.

First match:

1. `INVALID_IMMEDIATE_TANGENT_PROTECTED_FULL_ACTOR_G27`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_TANGENT_PROTECTED_G27`;
3. `NONFORMAL_NO_DELAYED_ACCESS_TANGENT_PROTECTED_G27`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_TANGENT_PROTECTED_G27`;
5. `NONFORMAL_IMMEDIATE_TANGENT_PROTECTED_FULL_ACTOR_PROMISING_G27`.

Only branch 5 licenses a formal executable definition. The screen consumes no
conclusion-bearing iteration and no outcome licenses UAV promotion.
