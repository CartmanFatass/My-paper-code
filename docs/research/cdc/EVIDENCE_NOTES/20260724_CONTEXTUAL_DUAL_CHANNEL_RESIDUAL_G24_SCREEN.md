# Contextual dual-channel residual G24 bounded screen

Date: 2026-07-24

## Evidence identity

```text
source_commit=75ba0a4578d8945bfa83aa96b7f8eecfcbf5d499
run=logs/nonformal_contextual_dual_channel_residual_g24_20260724_75ba0a4_pm1
formal=false
iteration_consumed=false
runtime=cpu, torch 2.7.0+cpu, one thread
status=COMPLETE
branch=NONFORMAL_NO_DELAYED_ACCESS_CONTEXTUAL_RESIDUAL_G24
```

The source commit is integrated, both source controls pass, every update and
reported quantity is finite, replay error is exactly zero, the frozen anchor
maximum difference is exactly zero, and the maximum independently normalized
channel-loss identity error is `2.91e-11`.

## Registered metrics

G17 remains compatible:

- final IID utility: `0.95761`;
- final held-out utility: `0.94602`;
- gain: `0.32128`;
- effort/mix correlations: `0.98103` / `0.99026`;
- effort/mix MAE: `0.01966` / `0.01747`.

G18 does not obtain delayed access:

- anchor utility: `0.52012`;
- final utility: `0.58333`;
- gain over anchor: `0.06322`;
- spike utility: `0.0`;
- rotating-effort share: `0.50503`;
- minimum step utility: `0.0`.

The first-match branch is therefore exact. No lower-precedence mechanism
diagnostic can relabel the missing delayed-access result.

## Scientific disposition

G23's local residual reached `0.95111` G18 utility and `0.85332` spike utility.
Replacing that representation with the wider direct actor-set context causes a
large regression under the same dual-channel optimizer, budget, sources and
gates. Wider contextual input is not the missing correction and G24 is closed
without rescue or UAV promotion.

The nearest unresolved distinction is whether the better G23 local residual
can represent the constructive delayed controller at all when PPO credit is
removed. A supervised, source-side teacher fit can answer that cheaply. It is
diagnostic only: it cannot become a learned algorithm result, formal evidence,
or a candidate for UAV promotion.
