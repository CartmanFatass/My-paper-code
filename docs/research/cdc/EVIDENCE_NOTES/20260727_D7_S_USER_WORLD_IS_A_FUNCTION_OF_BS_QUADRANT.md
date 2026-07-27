# The user world is a function of the BS quadrant, and the divergence is a coin flip

Measured 2026-07-27 during task 14 (R3 section E, episode-world provenance).
Corrects and sharpens `20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`,
which is right that fresh envs diverge but wrong to imply they always do.

## What was measured

60 pairs of freshly constructed `UAVEnergyAwareRelayEnv`, both `reset(seed=12345)`:

```text
fresh envs shared user world   : 21 / 60  (35 %)
BS center in same quadrant     : 21 / 60  (35 %)
"same users" == "same quadrant": 60 / 60
```

Perfect agreement, 60 out of 60. Two further deterministic checks confirm the
mechanism: BS layouts pinned to `(0.05, 0.05)` and `(0.10, 0.10)` — same
quadrant, different coordinates — give **bit-identical** user worlds, while
`(0.05, 0.05)` against `(0.95, 0.95)` diverges.

## The mechanism

`_generate_forced_relay_cluster_positions` (`scenario_base.py`) reads
`ground_bs_positions` exactly once, to compute `bs_center` and select the
opposite corner for the remote cluster. That selection is a **four-way discrete
branch on quadrant**. Every other input to user generation comes from
`self.np_random`, which `reset(seed=)` re-seeds.

So:

> The user world is a deterministic function of **(episode seed, BS quadrant)**.
> It is not a function of the BS coordinates, and it is not continuous noise.

The BS layout is drawn at construction from `RandomState(None)`, so the quadrant
is the single unseeded input — which is why the divergence exists at all, why it
is kilometre-scale rather than jitter, and why it appears only ~65 % of the time.

## What this corrects

The prior note's headline — "two fresh envs, same seed, differ in user
population by 6547 m" — is a true observation of one draw, read as if it were a
guarantee. It is a ~65 % event. Three consequences:

1. **`tests/env_user_population_determinism_test.py` was flaky and had been
   passing on luck.** `test_fresh_envs_with_the_same_seed_do_not_share_users`
   and `test_state_hash_cannot_see_the_user_divergence` both fail whenever the
   two constructions happen to share a quadrant, i.e. about a third of runs.
   Both now pin the BS quadrants apart explicitly, so the same fact is asserted
   deterministically. This was found by observing the suite fail and then pass
   with no code change between the two runs.

2. **The ep64 retirement is strengthened, not weakened.** Building the
   environment fresh per arm did not make the arms uniformly unpaired — it made
   them a *mixture*, each pair matched with probability ~0.35, with no record of
   which. Unrecoverable heterogeneity is worse evidence than uniform
   mismatch, because it cannot even be corrected for in principle. The Pro
   Stage B ruling (`Q2c` option ii) stands on firmer ground than when it was
   made.

3. **Equal coordinate hashes still do not imply a shared episode world**, which
   is the standing rule in `AGENTS.md`. Unchanged. But the converse is now
   sharp: a shared world requires a shared *quadrant*, which topology pinning
   already guarantees — so once the topology is pinned, the user world is
   reproducible from a seed. That is what made task 14 tractable without
   touching `reset()`.

## What was NOT changed

`reset(seed=)` semantics are untouched, so no prior comparison changes meaning.
Reproducibility is added at the pinning layer (`build_pinned_env` step 8 →
`regenerate_user_world`), which is opt-in and used only by the D7.S audit.

## Provenance

- Measurement: 60-trial construction sweep, `--` scratch script, not retained.
- Deterministic re-statement: `tests/env_user_population_determinism_test.py`,
  `test_the_user_world_is_a_function_of_the_bs_quadrant`.
- Task-14 implementation: `envs/pettingzoo/scenario_base.py`
  (`regenerate_user_world`), `scripts/audit_d7_s_event_aligned.py`
  (`build_pinned_env` step 8, `episode_world_fingerprint`,
  `episode_world_provenance`).
