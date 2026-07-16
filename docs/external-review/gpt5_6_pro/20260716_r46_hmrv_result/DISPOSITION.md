# R46-HMRV-G0 Controller Disposition

Date: 2026-07-16

## Verdict

`VALID_FAIL_R46_HMRV_SUBSTRATE`

The registered local CUDA gate is implementation-valid. Balanced Bernoulli
support and the true-Q comparator exposed action-specific delayed value, but the
exact heterogeneous-maintenance dynamics did not produce the registered
same-check agent/context-specific sign heterogeneity.

## Direct evidence

- M0 passed: 64,000 steps, 16 environments, 100 episodes per environment,
  9,600 usable checks, 19,200 focal rows, four critics with 570 optimizer steps
  each, and zero policy, low, skill, or intrinsic optimizer steps.
- Behavior propensity was exactly 0.5. All pre/post action, health, service, and
  reward traces replayed exactly. There were 3,962 zero-reward and 6,412
  full-service blocks.
- M1 passed. Agent/action ESS ranged from 4,708 to 4,892 and maximum persistent-
  environment weight share ranged from 0.0656 to 0.0679.
- M2 passed. True/sham weighted MSE was 10.6079/10.9186; the ratio-gain 95%
  interval was [0.02669, 0.03189]. Top-minus-bottom doubly robust score was
  2.7944 with interval [2.5504, 3.0374].
- M3 failed. Agent 0's top-quartile doubly robust score remained negative, and
  pooled same-check predicted-sign discordance was exactly zero. Both ordered
  degradation strata (1,2) and (2,1) also had zero discordance with [0,0]
  intervals.

## Binding conclusion

The positive-control support and prediction path work, but the registered
process does not create the required simultaneous KEEP-versus-RENEW sign split.
Under the pre-registered branch, the exact HMRV dynamics, three-block estimand,
and positive-control substrate are retired without seed, data, capacity,
threshold, clipping, reward, or environment rescue.

This result does not authorize S7, open-roster, variable-N, a renewal actor, or
task/environment-specific intrinsic reward. A successor requires one
structurally different causal edge selected through the result review.
