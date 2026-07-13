# GPT-5.6 Pro R29 Review Disposition

- Source: GPT-5.6 Pro / ChatGPT web, returned manually by the user.
- Received: 2026-07-14.
- Related claim: whether the pointwise R29 action-density ratio is the right
  natural on-policy individual-skill reward and what experiment should follow.
- Raw evidence: `RESPONSE_RAW.md` in this directory.

## Decision

**MODIFY and accept as R29-T10.**

Accepted:

- retain the uniform four-skill mixture, collection-policy recomputation,
  detached reward, coefficient `0.05`, clip `0.05`, and low-level-only reward;
- replace independent pointwise scoring with a fixed-candidate recurrent replay
  over each complete natural skill lifetime, scoring only its final 10 actions;
- add the clipped scalar once at the lifetime's final primitive step so low GAE
  transports it backward;
- require the actual-skill replay likelihood to match stored PPO likelihood
  within `2e-5` on every replayed row;
- report mean-versus-variance symmetric-KL components and compare
  `probe_only` directly with `real_reward`.

Modified:

- a nonterminal lifetime that reaches its exact selected length on the final
  rollout row is complete even when the segment manager labels the flush
  `update`; shorter update flushes, episode endings, and early renewals remain
  excluded;
- the actual-skill candidate uses PPO's stored old-policy squashed log
  likelihood with the common tanh Jacobian removed. Two real launches showed
  that CUDA GRU output changes by `1e-3` when the replay batch shape differs,
  even from the same stored hidden state. The stored likelihood is the exact
  natural collection-policy source; unanchored recurrent drift is reported
  separately. Other candidates remain fixed through full recurrent replay;
- the user authorized an initial local paired test at 320K additional steps per
  arm. This is single-seed preliminary evidence, not the review's full
  three-seed family conclusion. Remaining seeds are promoted only if the pair
  yields a decision-relevant effect.

Rejected/deferred:

- the original pointwise R29 reward is retired from the online comparator;
- three-seed expansion is deferred pending the authorized paired result;
- no claim about task improvement, cooperation, semantic roles, natural skill
  selection, or exact mutual-information optimization is authorized.
