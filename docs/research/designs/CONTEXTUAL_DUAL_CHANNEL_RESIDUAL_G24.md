# Contextual dual-channel residual G24

```text
status=PROTOTYPE_ACCEPTED_SCREEN_NEXT
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen delta

G24 is G23 with one representation change. The unrestricted delayed proposal
reads actor-side member encoding, active-set context, current hidden state and
current observation directly. It no longer uses the frozen post-RNN candidate
or autoregressive prefix. Dual-channel residual-only Adam, fast anchor, sources,
budgets, thresholds and branch order are unchanged.

The proposal is computed once per step, added before the existing tanh-Normal
distribution and masked to exact zero on inactive rows. No centering,
critic-state access, slot identity, source label or future reference is allowed.

## Bounded screen

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

Fresh screen seeds:

```text
g17_model=3419000
g17_train_ledger=3429000
g17_action=3439000
g17_evaluation_ledger=3449000
g17_evaluation_action=3459000
g18_model=3519000
g18_action=3539000
```

First-match outcomes retain the exact G19--G23 thresholds:

1. `INVALID_CONTEXTUAL_DUAL_CHANNEL_RESIDUAL_G24`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_CONTEXTUAL_RESIDUAL_G24`;
3. `NONFORMAL_NO_DELAYED_ACCESS_CONTEXTUAL_RESIDUAL_G24`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_CONTEXTUAL_RESIDUAL_G24`; or
5. `NONFORMAL_CONTEXTUAL_DUAL_CHANNEL_RESIDUAL_PROMISING_G24`.

Operational validity additionally requires residual permutation/padding
error at most `1e-7`, inactive exact zero, dual-channel loss identity, residual-only
ownership, finite updates, exact anchor, replay at most `1e-6` and
source/lifecycle controls. Only branch 5 licenses formal design; no branch
supports UAV promotion.

## Proof-sized acceptance

- exact zero-output equivalence in all three execution modes;
- direct active-set contextual proposal with no critic/source field;
- permutation/padding invariance and inactive exact zero;
- exact dual-channel composition and residual-only Adam;
- bitwise anchor, replay/lifecycle/source and precedence retention.

## Implementation acceptance

The active implementation is
`ha_ctse_process/contextual_dual_channel_residual_g24.py`; the generic hook
returns `None` for all prior policies. G24 alone supplies one contextual
proposal tensor per step and masks inactive rows exactly before the base actor
consumes it.

Seven focused and 37 focused-plus-retained tests pass on the registered CPU
one-thread runtime. They close exact zero-output/common-mode behavior,
permutation and padding error at most `1e-7`, inactive exact zero, dual-channel
loss identity, residual-only Adam, replay and bitwise anchor preservation. This
accepts only the bounded screen, not formal compute or delayed access.
