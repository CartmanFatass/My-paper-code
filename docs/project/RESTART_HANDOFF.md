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
| 6 | **`user_world_seed` + episode-world fingerprint** | **NOT DONE — task 14** |

150 focused tests pass. `scripts/d7_s_clone_conformance_check.py` reports
`CLONE_CONFORMANCE_PASS` on the real environment across all seven conditions
including 1A, 1B and cross-limb, with **zero reconstruction replays**.

## The one open deliverable

**Task 14 — episode-world provenance.** Pro Q2(b): construction-time OS entropy
is not adequate evidence provenance, and "do nothing" was explicitly refused.

- a `user_world_seed` derived from existing episode provenance under a **disjoint
  namespace**, controlling initial user positions, cluster assignments and
  centres, user/cluster waypoints, initial motion and pause state — separate from
  topology, energy-permutation and continuation seeds;
- an episode-world fingerprint recorded after env initialization;
- the event-history fingerprint at `t_e` carried in the artifact.

The distribution must not change — it only becomes reproducible. This touches
`envs/pettingzoo` user generation, so treat the protected-semantics boundary
carefully.

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
