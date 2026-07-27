# The frozen "bit-identical prefix replay" was never bit-identical

Date: 2026-07-26 · branch `untied-k` · zero-compute + one bounded conformance
exercise (~4 min) · **no scientific result is read here**

## Claim

The superseded D7.S contract's fixed-history mechanism — *"bit-identical prefix
replay from reset — identical topology coordinates, initial-energy permutation,
**user-motion and channel streams**, source-control decisions before `t_e` …
asserted by a state hash before forking"* — **does not hold in the
implementation**, and the state hash it names structurally cannot detect the
failure.

Discovered before launch by `scripts/d7_s_clone_conformance_check.py`, written
to prove the shared-prefix clone path against the real environment rather than
against the test suite's fake env.

## Measured facts

Registered environment, Scenario-7 `S7-S3`, `user_distribution =
forced_relay_cluster`, `randomize_users = True`.

| Observation | Result |
|---|---|
| `reset(seed=S)` twice on the **same** env object | user positions **identical** |
| Two **fresh** env objects, **same** `seed=S` | user positions differ, `max|Δ| = 6547 m` |
| Two `build_pinned_env(...)` with identical args | user layout, cluster centres, waypoints, velocities all differ before a single step |
| UAV positions, `np_random` token after construction | **identical** |
| Two independent `replay_prefix(...)` to the same `t_e` | 24 attributes differ: `user_positions` (`max|Δ| = 4193 m`), `sinr_matrix`, `connections`, `last_user_rates_mbps`, `cluster_*`, `serving_set_changes`, `uav_joins_count`, `packet_id_counter`, … |

So the user population is fixed by **construction-time** state that
`reset(seed=…)` does not re-derive. `build_pinned_env` constructs a fresh env on
every call, so every call produced a different user world.

## Why the guard could not catch it

`compute_state_hash` hashes exactly: UAV positions, battery ratios, charging
mask, station occupancy, station queue, lifecycle mask, duty map.

It contains **no user state, no cluster state, no channel state**. The
assertion that was supposed to enforce the fixed-history guarantee was computed
over the one surface that stayed identical, while the surface that diverged by
kilometres was never inspected. The hash passed on every fork.

This is the same defect class as the already-ruled topology-provenance issue
(ground-BS and charging-station layout drawn from an unseeded RNG at
construction, Pro ruling 2026-07-26). The section 9 pinning procedure restores
BS and station coordinates after reset for exactly this reason. **Nobody
extended that reasoning to the user population.**

## What this invalidates

Under the superseded replay-every-prefix realization, each replicate — KEEP,
and every candidate's selection and evaluation streams — called `replay_prefix`
independently and therefore ran **against a different user population**.

`U*_m,src = V_SET − V_KEEP` would then have been dominated by user-layout
variance rather than by the focal intervention, and the contract's requirement
that *"SET and KEEP remain CRN-paired"* was not met at the prefix level. That is
a validity failure of the frozen design, not a cost or power problem. The 2-4
day projection that got the run cancelled was, in hindsight, buying a broken
comparison.

## What this vindicates

The R2 shared-prefix realization is **not merely an optimization**. One
canonical replay materialized as an immutable snapshot, with every continuation
cloned from it, is the first realization in which all arms of an event actually
share one user world. Correctness was the stronger reason for the change than
cost, and neither the ruling nor the Project Manager knew it at the time.

## Consequence for Stage-B condition 1

Condition 1 requires a clone continuation to be *"byte- or exact-numerically
identical to one obtained by the previous independent replay route under the
same continuation seed."*

As written it is **unsatisfiable, and inverted**: the reference route is
nondeterministic across calls, so the condition asks the correct mechanism to
reproduce the broken one. `verify_clone_equivalence_against_replay` returns
`equivalent=False` for this reason and not because cloning is faulty —
conditions 2-5 all pass on the real environment (mutation isolation, RNG
isolation, topology preservation, complete-state restoration), and `deepcopy`
of the real env costs 4 ms.

The scientifically meaningful restatement, for External Pro to rule on:

> Two continuations cloned from the **same** snapshot under the same
> `stream_seed` must be identical, and two clones under **different**
> `stream_seed` must differ only through the continuation stream.

That is checkable, and it tests the property the estimand actually needs.

## Open questions for External Pro (Stage B)

1. Does the restated condition 1 replace the original, given the reference route
   is nondeterministic by construction?
2. Two Scenario-7 episodes sharing a topology hash do **not** share a user
   population. Does topology identity remain the right comparability unit, or
   must the user layout be pinned and recorded alongside the coordinate hash?
3. Which previously closed Scenario-7 results compared arms built from separate
   env constructions, and are they affected? The ep64 single-topology diagnostic
   is the first to audit — it is already scoped to one realized topology, but
   its arms' user populations have not been checked.

## Status

No result is retired or rescued by this note. It records a repository fact and
the questions it forces. The D7.S audit does not launch until Pro rules on
question 1.

---

## Append 2026-07-26 (after the Stage B fence was sent, so not visible at that `stage_commit`) — the ep64 diagnostic shares the mechanism

Established by reading `scripts/audit_d7_s_persistence_margin.py`, zero compute.

`env = build_env()` sits **inside** the per-arm loop (`:495`, within
`for arm in arms:` at `:491`). Every arm of every episode therefore runs on a
**separately constructed** environment.

`build_env()` (`:419-452`) already documents this defect class from
2026-07-25 — topology drawn at construction before any seed exists, two
constructions differing by 2125 m in `ground_bs_positions` and 1487 m in
`charging_station_positions` — and fixes it by calling `_init_ground_bs()` and
`_init_charging_stations()` after `reset(seed=topology_seed)`, regenerating the
topology deterministically.

**It does nothing about the user population.** So the 2026-07-25 repair pinned
exactly the two surfaces it had measured and left the third moving. Every arm
comparison in that diagnostic —

```text
B_H       = mean(constructive) - mean(null)
U_stable  = mean(set_stable)   - mean(keep_stable)
U_flex    = mean(set_flex)     - mean(keep_flex)
```

— is therefore a comparison across **different user worlds**.

### The distinction that decides how bad this is

Because each arm gets its own independent fresh construction, the user layout is
independent and identically distributed across `(episode, arm)`. That is
**variance, not a directional bias**: the difference of means stays unbiased,
but the design is unpaired where it was believed to be paired.

The consequence is therefore entirely about the interval, not the point:

- if ep64's confidence procedure estimated dispersion **empirically from the
  observed arm samples**, the interval already absorbs the extra variance and
  the reported exclusions of zero remain usable, merely underpowered;
- if it assumed pairing or common random numbers anywhere, the interval is **too
  narrow** and `B_H = +65.965` / `U_stable = -40.602` "CI excludes zero" is
  false confidence.

That is a question about the registered confidence procedure's meaning, so it is
External Pro's, and it is exactly what Q2(c) of the Stage B round asks. This
append sharpens that question; it does not answer it, and it retires nothing.

Note the pattern worth carrying: the 2026-07-25 repair was correct about
everything it measured and silently incomplete about what it had not thought to
measure. The same shape recurred here. A fix that pins *the surfaces we
happened to check* is not a fix for *construction-time nondeterminism*.

### Resolved by reading the estimator: ep64's intervals are not too narrow

The severity question above turned on whether ep64's confidence procedure
assumed pairing. It does not. Established from the code, zero compute:

- `bootstrap_mean_ci` (`:171-182`) resamples the supplied array with
  replacement and takes the mean — a plain empirical percentile bootstrap.
- It is applied to **per-episode differences**: `b_h_ep`, and
  `per_ep["set_stable"] - per_ep["keep_stable"]`, `per_ep["set_flex"] -
  per_ep["keep_flex"]` (`:531-535`).

Because the resampled quantity is the *observed* per-episode difference, any
extra dispersion caused by the two arms living in different user worlds is
already present in those numbers and is therefore carried into the interval. The
bootstrap does not assume the pairing succeeded; it measures whatever spread the
differences actually have.

So the failure mode feared above does not occur:

| | Verdict |
|---|---|
| Point estimates `B_H = +65.965`, `U_stable = -40.602` | unbiased — arm layouts are IID, not systematically ordered |
| Interval width | honestly wide; it absorbed the unpaired variance |
| "CI excludes zero" | **survives**, at lower power than a truly paired design would have given |

*(PM inference, not a result: this says the estimator is sound, not that the
diagnostic is fit for any particular reuse. Whether ep64 may serve as a causal
comparator remains External Pro's call under the standing topology-provenance
rule.)*

### Append — narrowing where the user-world divergence actually comes from

Investigated to hand the next session a located defect rather than an open
question. Established, all zero-compute:

| Hypothesis | Result |
|---|---|
| Global `np.random` drives it (`uav_env:413` etc.) | **No.** Pinning `np.random.seed(999)` before each construction still gave a 6700 m divergence. Scenario-7 uses `forced_relay_cluster`, so the `"cluster"` branch holding the global draw never executes |
| Config differs between instances | **No.** `cluster_std`, `central_area_ratio`, `area_size`, `n_clusters`, `n_users`, `randomize_users`, `user_movement_model` all identical |
| Generation is inherently nondeterministic | **No.** `_generate_user_positions()` called twice on one object with `np_random` reset between gives identical output |
| Users are placed relative to BS/station geometry | **No.** Two objects differing in `ground_bs_positions` and `charging_station_positions` produced *identical* users |

The generation path itself reads only `self.np_random` (`scenario4:461-502`,
cluster centres by rejection sampling; `:560` user offsets by
`multivariate_normal`).

**A shared-state hypothesis was raised and then killed by a better test.**

An earlier single run appeared to show that ordering mattered — that
`construct, generate, construct, generate` produced identical users while
`construct, construct, generate, generate` did not — which would have implied
mutable state shared across instances. Repeating each ordering three times
refutes it:

```text
ORDER-1  construct a, construct b, gen a, gen b   ->  DIFFER  6644.3 / 6644.3 / 6644.3 m
ORDER-2  construct a, gen a, construct b, gen b   ->  DIFFER  6644.3 / 6883.8 / 6883.8 m
```

Ordering is irrelevant: **both orderings diverge, every time.** The single
"identical" observation did not reproduce and is recorded as a measurement
artifact of that one run, not as evidence. The cross-instance shared-state
hypothesis is **not supported** and should not be built on.

What survives is narrower and solid: **user generation differs across
environment constructions within one process**, and the source is none of the
things ruled out in the table above — not the global `np.random`, not config,
not `self.np_random`, not BS/station geometry, and not inherent nondeterminism
of the generation routine.

### The divergence is DISCRETE, and that is the lead

The repeating magnitudes were followed up rather than left as a curiosity. Six
constructions, identical config, `np_random` pinned to `RandomState(777)`
immediately before each call:

```text
construction 0: layout 2b07b72d15ba
construction 1: layout df8a768cf8c9
construction 2: layout df8a768cf8c9
construction 3: layout f166386dadd0
construction 4: layout df8a768cf8c9
construction 5: layout f166386dadd0
-> 3 distinct layouts across 6 constructions
```

A freshly drawn continuous layout cannot repeat a byte-exact hash three times.
**The latent variable is discrete and small.** Whatever differs between
constructions selects among a handful of outcomes rather than sampling a new
world each time.

This is a measured fact, not an interpretation, and it narrows the search
sharply: look for construction-time state with few possible values that the
generation path branches on — a cluster-assignment vector, a per-instance
counter, a cached or pooled layout, or a container whose iteration order varies.
It is **not** an RNG-stream problem, because the stream was pinned identically
across all six.

Deliberately not guessed further here. The immediately preceding hypothesis in
this note was committed on one run and had to be retracted; the discipline that
caught it is the same one that says to stop at the measurement and let the next
session instrument the generation path directly.

The next session must locate the source before writing `user_world_seed`.
Seeding a per-instance RNG cannot fix a mechanism that has not been identified —
it would only make the symptom disappear, which is the precise failure this
whole round exists to stop repeating.

What is genuinely defective is the **stated rationale**, not the arithmetic:
`bootstrap_ratio_ci`'s docstring (`:136`) justifies resampling episodes rather
than arms by asserting that "arms are CRN-paired inside one" episode. They are
not. The procedure is right and its reason is wrong — which is the dangerous
combination, because a later optimization reasoning from that premise (for
example, exploiting the assumed pairing to tighten the interval) would
introduce the error the current code accidentally avoids. The docstring is
corrected in the same commit as this append.
