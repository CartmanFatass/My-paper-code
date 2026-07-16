# R45-SDRA Controller Disposition

Date: 2026-07-16

## Verdict

`VALID_FAIL_R45_SDRA_IDENTIFIABILITY`

R45 was implementation-valid and found strong action-conditioned predictive
information, but the frozen Alice--Bob source policy lacked the registered
natural overlap and the learned renewal value did not change sign across
agents or contexts. The Alice--Bob `K=50` natural-support renewal-credit route
and this temporal-mechanism substrate are retired without rescue.

## Direct evidence

- M0 passed: 160,000 steps, 100 updates, 3,200 check rows, 16 structural rows,
  3,184 normal checks, and 6,368 factor rows; all five source optimizers and the
  renewal actor took zero steps. Source state and actor drift were zero,
  source probability error was `4.768e-7`, binary replay and prefix mismatch
  were zero, and zero/final deterministic traces were exact.
- Frozen service remained positive at win/key0/key1 `0.93/1.00/0.93`.
- M1 failed. KEEP ESS was `33.59` for agent 0 and `3.30` for agent 1, below
  `64`; maximum environment weight shares were `0.1475` and `0.6156`, above
  `0.10`. Agent-1 RENEW also exceeded the cluster-share ceiling at `0.1353`.
- M2 passed under the user-approved nontrivial threshold. Weighted MSE was
  `0.03830` for true-Q versus `0.37667` for the action-blind sham; the
  sham/true ratio-gain 95% interval was `[3.3623, 18.4246]`. Top-minus-bottom
  doubly robust score was `0.52794`, interval `[0.40826, 0.70587]`.
- M3 failed. Both agents' bottom-quartile doubly robust scores remained
  positive, and same-check predicted-sign discordance was only
  `0.000314` with interval `[0, 0.000942]`, far below the `0.20` point and
  `0.10` lower-bound gates.

## Binding conclusion

Natural source rows contain action-specific outcome information, so critic
capacity or a disconnected prediction path does not explain the failure. But
the identified contrast is overwhelmingly common-mode RENEW-positive rather
than agent-specific KEEP/RENEW heterogeneity, while rare KEEP support is too
concentrated for the registered causal claim.

This permanently retires:

- Alice--Bob `K=50` natural-support SDRA renewal credit;
- further renewal-actor training on this substrate;
- rescue through more data, seeds, critic capacity, propensity clipping,
  threshold changes, forced actions, or task-specific reward/intrinsic terms.

It does not retire general asynchronous skill learning, joint co-adaptation,
other benchmarks with genuine heterogeneous timing demand, S7 hypotheses,
open rosters, or variable team membership. No successor is implemented before
one new causal edge and abandonment gate are selected.
