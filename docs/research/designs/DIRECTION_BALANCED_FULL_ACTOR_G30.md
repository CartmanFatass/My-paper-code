# Direction-balanced full actor G30

```text
status=FORMAL_CLOSED_NO_DELAYED_ACCESS
formal=true
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Frozen algorithm delta

Reuse the two-phase full actor, independently normalized immediate/successor
advantages, state-only critics and exact-zero residual. Replace G29's realized
parameter projection with a pre-Adam direction-balanced composition. For each
nonzero global actor gradient divide by its exact float64 norm, take the equal
half-sum, cast once to actor dtype, apply the existing global gradient clip and
advance ordinary Adam once.

Both-zero, immediate-zero and successor-zero branches are exact and contain no
epsilon threshold. No projection, lattice repair, learned gate, raw-norm
rescale, optimizer rollback or second step is allowed. Adam moments receive the
direction-balanced gradient; cross-G28/G29 resume is forbidden.

## Screen contract

- G17 fast/direction-balanced updates: `100/100`; G18: `100/300`.
- Eight environments, two PPO passes, Adam `1e-3`, CPU one thread.
- G17 evaluation uses 48 IID and 48 held-out episodes; G18 uses all three
  registered slot layouts.
- Fresh seeds: G17 model/ledger/action/evaluation-ledger/evaluation-action
  `6119000/6129000/6139000/6149000/6159000`; G18 model/action
  `6219000/6239000`.
- Replay `<=1e-6`; direction-balanced raw immediate dot `>=-1e-7`; exact
  composition identity `<=1e-7`; lifecycle, ownership, inactive rows, finite
  global norms, ordinary Adam step count and zero residual fail closed.
- Behavioral thresholds and first-match order remain exactly G28/G29: invalid,
  no G17 compatibility, no G18 access, no G18 mechanism, promising.

## Protected semantics

Sources, observations, rewards, factorization, recurrent/lifecycle state, RNG,
PPO clipping, advantage normalization, critics, budgets, thresholds and result
precedence are frozen. Only actor-gradient magnitude semantics and its fresh
checkpoint identity change. There is no oracle input, formal mode or UAV
promotion.

## Proof-sized acceptance

1. Aligned, obtuse, exact-opposite, both-zero and either-one-zero cases match
   the closed-form composition and nonnegative float64 raw dot.
2. The output is parallel to the exact unit-direction half-sum; no epsilon,
projection or hidden rescale is present.
3. Gradient clipping preserves direction, ordinary Adam advances exactly once,
   and checkpoint state receives the composed gradient.
4. A high-dimensional near-opposite float32 case remains finite and inside the
   unchanged `-1e-7` bound.
5. G17/G18 replay, lifecycle, actor/critic/residual ownership and first-match
   semantics pass before one integrated paired screen.

## Nonformal screen disposition

The exact screen at source `0d7574f9f73c3a9226dfe7f76ff58468b7a930e5`
is operationally valid and selects
`NONFORMAL_DIRECTION_BALANCED_FULL_ACTOR_PROMISING_G30`. It passes every frozen
G17 compatibility, G18 access and G18 mechanism gate. This licenses formal
confirmation without changing the algorithm, sources or thresholds.

## Formal executable definition

```text
authorization_token=AUTHORIZE_DIRECTION_BALANCED_FULL_ACTOR_G30_FORMAL_CPU_V1
formal_replicates=3
g17_fast_updates_per_replicate=100
g17_direction_balanced_updates_per_replicate=100
g18_fast_updates_per_replicate=100
g18_direction_balanced_updates_per_replicate=300
num_envs=8
ppo_passes=2
g17_eval_episodes_per_domain_per_replicate=128
g18_slot_permutations_per_replicate=3
bootstrap_repetitions=10000
backend=cpu
torch_threads=1
```

Fresh replicate-indexed seed bases are G17 model/ledger/action/evaluation
ledger/evaluation action `7119000/7129000/7139000/7149000/7159000`, G18
model/action `7219000/7239000`, and bootstrap `7260030`. Replicate `r` adds `r`
to each source seed. No G28/G29/G30-screen checkpoint is resumed.

Formal training must preserve the screen's replay, lifecycle, ownership,
exact-zero residual, direction-dot, composition-identity, finite-state and
single-Adam-step invariants. Zero and final checkpoints bind algorithm, source
commit, formal flag, source, replicate, both completed phase counts and the
complete configuration.

The formal analyzer computes the same hierarchical 95% intervals and applies
this first-match order:

1. `INVALID_DIRECTION_BALANCED_FULL_ACTOR_G30` on artifact or operational
   failure;
2. `NO_G17_COMPATIBILITY_DIRECTION_BALANCED_G30` unless IID and held-out
   utility LCBs are at least `0.90`, held-out gain LCB is at least `0.10`, every
   episode is at least `0.80`, both minimum mapping correlations are at least
   `0.90`, and both maximum MAEs are at most `0.05`;
3. `NO_DELAYED_ACCESS_DIRECTION_BALANCED_G30` unless G18 utility LCB is at
   least `0.95`, paired zero-checkpoint gain LCB is at least `0.10`, and spike
   utility LCB is at least `0.90`;
4. `NO_DELAYED_MECHANISM_DIRECTION_BALANCED_G30` unless rotating-effort-share
   LCB is at least `0.75`;
5. `UNSTABLE_DIRECTION_BALANCED_FULL_ACTOR_G30` unless every replicate's mean
   G18 utility is at least `0.90`; or
6. `USABLE_DIRECTION_BALANCED_FULL_ACTOR_G30`.

One valid formal analysis consumes conclusion-bearing iteration 20. Before
launch, the same runner must close a bounded nonformal exercise with one
replicate, one fast and one direction-balanced update per source, two
environments, one PPO pass and four G17 evaluation episodes. Its only valid
branch is `NONFORMAL_DIRECTION_BALANCED_FORMAL_PATH_EXERCISE_COMPLETE`; a
formal-required analyzer must reject those exercise artifacts.

## Formal disposition

The exact formal run at source `1e4fbb735107b2a924bb3fd4f682c251ab62fb72`
is operationally valid and selects
`NO_DELAYED_ACCESS_DIRECTION_BALANCED_G30`. G17 and every lower-precedence G18
gate except spike access pass. Spike-utility CI95 is
`[0.87611, 0.89346, 0.92093]`, whose lower bound misses the frozen `0.90`
floor. G30 is closed without rerun, threshold, budget, seed or UAV rescue.
