# Scale-normalized open-roster G8 derivation

Date: 2026-07-23

## Starting evidence

G5/G6 establish an absolutely usable direct recurrent open-roster policy
through N=16. G7 freezes those checkpoints and validly returns
`NO_MODERATE_BEYOND_COUNT_G7`: the moderate deterministic CI95 lower bound is
`0.8590299`, and one replicate degrades further in the far and joint bands.
Persistent duty remains exactly solved; the failure is in large-roster short
allocation. G7 is closed and cannot be retrained, tuned or relabeled.

## Scale-sensitive inputs

The G5 actor contains three distinct quantities whose magnitude grows outside
its training support:

1. the active member embeddings are summed, so context norm can grow with N;
2. both environment observations and the set-context coordinate use an
   unbounded log-count representation, with the environment coordinate crossing
   its declared value 1 at N>16;
3. autoregressive action-prefix counts are raw counts, so later members receive
   inputs up to N although training stopped at N=7.

`CE-CONTEXT-SUM-GROWTH`, `CE-COUNT-COORDINATE-OOD` and
`CE-PREFIX-COUNT-GROWTH` are all consistent with G7. The formal result does not
identify a unique cause, and no unique-cause claim is needed to build a usable
algorithm.

## Bounded component screen

Before freezing a new formal algorithm, run one nonformal CPU one-thread
factorial screen over:

```text
active_aggregation in {sum, mean}
count_coordinate in {log1p, bounded_fraction}
autoregressive_prefix in {raw_count, active_fraction}
bounded_fraction(N)=N/(N+1)
active_fraction(action)=prefix_action_count/N
```

All eight variants keep the architecture shape, reward, observations other than
the count coordinate, lifecycle ownership, task distribution, PPO update,
action factorization and training seeds matched. Use one replicate, 60 updates,
four environments per update, four PPO passes and 32 deterministic evaluation
episodes on IID, held-out, moderate, far and joint domains. A variant is
eligible only if replay, lifecycle, finite-update and source-control checks all
pass. Rank eligible variants by the minimum of its five domain means, then by
joint and held-out means. This screen is a prototype decision aid, not formal
evidence and consumes no iteration.

If the winner is separated by less than `0.01` from another variant, prefer the
variant that normalizes fewer axes. Otherwise select the measured winner. This
rule is frozen before the screen and prevents post-hoc aesthetic selection.

## Prospective successor

The selected representation will be trained from fresh seeds on the unchanged
G5 training profiles and evaluated on IID, held-out and all three G7 stress
domains. Formal acceptance remains absolute usability, not advantage over G5.
G5/G6 and G7 keep their exact closed meanings whatever G8 returns.

## Prototype disposition

The complete CPU screen at
`logs/nonformal_scale_normalized_g8_screen_20260723_pm1` selected only
`autoregressive_prefix=active_fraction`, while retaining the active embedding
sum and original log-count coordinate. Its minimum five-domain mean is
`0.8317871`, exceeding the runner-up by `0.0563965`; the `0.01` tie rule is not
invoked. All eight variants were finite, lifecycle-valid and replay-exact.

The active successor is therefore renamed
`PREFIX_NORMALIZED_OPEN_ROSTER_G8`. The screen remains nonformal and does not
identify a unique cause for G7.

```text
next_boundary=PREFIX_NORMALIZED_OPEN_ROSTER_G8_EXECUTABLE_DEFINITION
formal_compute=authorized_after_implementation_acceptance_and_git_freeze
prototype_iteration_cost=0
iterations_remaining=9
asynchronous_skill_lifetime=frozen
```
