# R46-HMRV-G0 Controller Disposition

Date: 2026-07-16

## Verdict

`VALID_FAIL_R46_HMRV_SUBSTRATE`

The registered local CUDA gate is implementation-valid. Balanced Bernoulli
support and the true-Q comparator exposed a small action-conditioned prediction
gain, but the registered learned `6 -> 32` Q/DR pipeline did not recover the
required same-check agent/context-specific sign heterogeneity.

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

The support contract works, but the registered learned Q/DR sign-transport path
does not recover the required simultaneous KEEP-versus-RENEW sign split. Direct
enumeration of the registered finite process shows that the transition kernel
itself does contain oracle sign heterogeneity; this run therefore must not be
interpreted as evidence that heterogeneous renewal value is absent. Under the
pre-registered branch, the exact combination of HMRV dynamics, three-block
estimand, six-field context, `6 -> 32` true-Q/action-blind-sham estimator, and
M2/M3 read is retired without seed, data, capacity, threshold, clipping, reward,
or environment rescue.

GPT-5.6 Pro selected one structurally different successor:
`R47-NSOPM-G0`, a reward-off gate from natural task-blind process support to
stable process modes and then skill-conditioned causal mode occupancy. It does
not authorize S7, open-roster, variable-N, a renewal actor, or
task/environment-specific intrinsic reward.
