# Controller Disposition: VALID_FAIL R31, ACCEPT R32-IFEPG

Date: 2026-07-14

Source: GPT-5.6 Pro / ChatGPT web

Raw evidence: `RESPONSE_RAW.md`

Decision: **ACCEPT**

## R31 disposition

R31-CFEI is a valid scientific failure on its direct forced-skill M2:
median between/within effect ratio `0.889613`, cluster CI
`[0.763227, 1.078315]`, with skills 0 and 1 below one. R31 online reward and
all window/prior/posterior/coefficient/null-threshold rescue variants remain
retired.

The registered absolute near-zero matched-shuffle hard gate was mathematically
invalid. A mismatched effect evaluated against the receiver label generally has
non-positive expected residual; `-2.068` is a disruption diagnostic, not an
independent failure. This correction does not authorize a rerun because M2
already failed independently.

## Accepted unique route

R32-IFEPG directly optimizes randomized fixed-window intervention effects. It
uses two independent stochastic replicas to form the signed U-statistic effect
separation, then applies one PPO-clipped auxiliary update to focal action
likelihoods. It has no posterior, intrinsic reward, value loss, GAE, entropy
bonus, task-reward input, or high-policy update. Gradients are restricted to
`low.actor_film.parameters()`.

The first authorization is only the paired Alice--Bob mechanism gate:

- same frozen adaptive-R30 checkpoint and context bank;
- `probe_only` versus `real_update`;
- 20 auxiliary updates, 32 contexts/update, four skills, two independent
  replicas, `W=10`, one epoch, PPO clip `0.10`, grad clip `0.5`;
- heldout common-random-number M1/M2 evaluation and 64 paired natural episodes
  for task-agnostic coverage transport and R30 lifetime safety;
- no task PPO and no normal-trainer R32 path.

Only M0-valid and M1--M3 PASS may authorize later sparse-source production
integration. Any valid metric failure retires direct interventional FiLM effect
policy gradient; there is no UNDERPOWERED branch.
