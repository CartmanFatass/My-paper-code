# Restart handoff — 2026-07-26, mid-iteration (D7.S Stage B repairs)

Successor PM: read this, then `docs/project/CURRENT_WORK.md`. Written under
context pressure mid-iteration rather than at a clean seam, so "the one open
deliverable" is the load-bearing section.

**This file replaces the iteration-21 handoff, which quoted the ep64 `B_H
+65.965` / `norm_stable −0.6155` numbers as decisive. Those readings are
RETIRED as causal evidence (below). Do not carry them forward.**

## Active boundary

```text
execution_mode=authorized
grant=ACTIVE_TWENTY_ITERATION_OVERNIGHT_GRANT_20260726
iterations_remaining=17          # NOT yet deducted -- this boundary has no result yet
working_branch=untied-k          # everything below is committed AND pushed
active=D7_S_STAGE_B_REPAIRS
```

User rulings that changed the rules today, all in `CURRENT_WORK.md`:

- **No wall-clock cap on the formal experiment.** The 8 h gate is gone. What is
  capped is audit-stage proliferation and audit-driven verification experiments;
  the 20-minute nonformal cap stands. `EVIDENCE_COMPLEXITY_POLICY.md` is
  rewritten around this.
- **Compute sharing:** run alongside the other line at **reduced shard width 4**;
  do not wait for it. (HMASD-new G39 formal training, pid 15276, different repo.)
- **Unresolved branch:** auto-expand to 16 topologies when §9's conditions hold;
  do not return to the user.
- **Iteration accounting:** this whole boundary is **one** iteration, deducted on
  completion. Transport repair and workflow rescope consume none.
- **Transport:** scripts, not a subagent — `scripts/ensure_review_browser.ps1`.

## What happened

Two Pro rounds closed, both archived hash-verified.

1. `20260726_d7_s_replicate_volume_necessity` — froze `n_select=2, n_eval=2`,
   accepted shared-prefix forking → contract R2.
2. `20260726_d7_s_stage_b_shared_prefix_realization` — **MISMATCH** → contract R3.

The finding behind both: **the frozen "bit-identical prefix replay" never held.**
Two freshly constructed envs with the same seed differ in user population by
kilometres, and `compute_state_hash` covers no user, cluster or channel state, so
the guard structurally could not detect it. Evidence note:
`docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`.

Pro then found what I missed: shared-prefix cloning made all arms share **one**
world, but that world was a *reconstruction*, not the one the event was certified
in. Plus two independent defects — `full_sync_SET` running every step instead of
every check, and the stable limb freezing a non-focal flex duty (claim-favouring
for stable persistence).

ep64 is retired as causal evidence: its env was built fresh **per arm**, and the
construction-time worlds were never recorded, so no unpaired reanalysis can
recover it either.

## Repairs — five of six done

| # | Repair | State |
|---|---|---|
| 1 | R3 contract supersedes R2 | done `effd21c` |
| 2 | Direct live-event capture + complete-state fingerprint | done `3c20edd` |
| 3 | `full_sync_SET` cadence + stable-limb lock | done `fd48f1e` |
| 4 | Tests rebuilt on the real mechanism | done `3c20edd` |
| 5 | ep64 retired in the ledger + widened provenance rule | done `7b7bf61` |
| 6 | `user_world_seed` + episode-world fingerprint | **half done `831112f`** — see below |

150 focused tests pass. `scripts/d7_s_clone_conformance_check.py` reports
`CLONE_CONFORMANCE_PASS` on the real environment across all seven conditions
including 1A, 1B and cross-limb, with **zero reconstruction replays**.

## The one open deliverable

**Task 14 — episode-world provenance.** Pro Q2(b): construction-time OS entropy
is not adequate evidence provenance, and "do nothing" was explicitly refused.

**Done (`831112f`, 152 tests pass):**

- `user_world_seed(topology_seed, block, episode_index)` — derived under a
  namespace disjoint from `stream_seed`'s, with a test proving no collision, so
  the user world cannot correlate with the arm streams it must be independent of;
- `episode_world_fingerprint(env, seed_value=)` — records initial user and
  cluster state after initialization;
- the event-history fingerprint at `t_e` was already carried (`3c20edd`).

**Remaining, and it is the substantive half:** the seed does not yet *control*
user generation. The payload says so explicitly —
`seed_controls_generation: False`. Making it true means changing construction
inside `envs/pettingzoo` so the user layout derives from `user_world_seed`
instead of construction-time entropy, then threading the seed through
`build_pinned_env` and recording the fingerprint per episode in the artifact.

That is a **protected-semantics edit**: the distribution must not change, only
become reproducible. Deferred deliberately rather than rushed before a session
switch — a half-applied change to environment semantics is worse than a clean
seam.

**Do this first, before writing any seeding code: locate the source.** The last
append in the evidence note has the full table. Ruled out by measurement: the
global `np.random`, config divergence, `self.np_random`, inherent
nondeterminism of the generation routine, and dependence on BS/station geometry.

A shared-cross-instance-state hypothesis was raised and then **killed** by
repeating each ordering three times — both orderings diverge every time, so
ordering is irrelevant and the one "identical" reading was an artifact. Do not
build on it; it is written up only so nobody re-derives it.

What is solid: **user generation differs across environment constructions within
one process**, source unlocated — but the divergence is **discrete**. Six
constructions with identical config and `np_random` pinned to `RandomState(777)`
produced only **3 distinct layouts**, one repeating byte-exactly three times:

```text
2b07b72d15ba, df8a768cf8c9, df8a768cf8c9, f166386dadd0, df8a768cf8c9, f166386dadd0
```

A continuous fresh draw cannot repeat a byte-exact hash. So this is **not an RNG
problem** — the stream was pinned identically across all six. Look instead for
construction-time state with few possible values that the generation path
branches on: a cluster-assignment vector, a per-instance counter, a cached or
pooled layout, or a container whose iteration order varies. Instrument
`_generate_forced_relay_cluster_positions` directly.

A per-instance `user_world_seed` cannot fix a mechanism nobody has identified;
it would only make the symptom disappear. That is the exact failure this round
exists to stop repeating, which is why locating it comes first.

**The trap to expect:** `tests/env_user_population_determinism_test.py` asserts
that two fresh envs with the same seed do **not** share users. Implementing task
14 will make it fail. That is by design and the failure message says so — it is a
decision point about what prior comparisons meant, not a broken test.

## Exact next action

Implement task 14 → run the D7.S audit at **4-way sharding** under the project's
separate conclusion-bearing compute authorization → Pro result round (step 8 ≡
next iteration's step 1: **one** round, not two) → `docs/report/ITERATION_25.md`
in zh-CN with the mandatory time-distribution table → only then deduct 17 → 16.

`ITERATION_24.md` already exists and was support work, so the next
conclusion-bearing report is **25**.

## Loop state

No `/loop` driver attached — it died with the previous session and was not
re-armed. Nothing is in flight. `check_compute_free.ps1` reports `COMPUTE_BUSY`
because of the other line; the user's ruling overrides the wait — run alongside
at width 4.
