# The instrument's back half: the primary result path has no guards

Second systematic sweep of `scripts/audit_d7_s_event_aligned.py`, covering the
region the first pass could not reach. The earlier note recorded that
"everything beyond roughly `:1743` is unswept" and that the file "must not be
read as audited". This closes most of that gap.

```text
commit under test = 740877ba
baseline          = tests/audit_d7_s_event_aligned_test.py, 183 passed
regions           = A :1750-:2332  replay, event roll, prefix determinism
                    B :2333-:2902  fingerprint, clone isolation, snapshot, fork
                    C :2903-end    episode execution, pooling, orchestration
```

Regions A and C are reported here. **Region B was dispatched at the same time
and has not returned; this note does not cover it and the fingerprint/clone
region must still not be read as audited.**

## The worktree trap fired again, on both sweeps

Both children were dispatched with `isolation: "worktree"` and both arrived
checked out at `4866eb4e` — an unrelated line — exactly as on the previous
dispatch. Both detected it, ran `git reset --hard 740877ba`, and reported the
commit they actually ran at, which is the only reason their findings mean
anything.

Two for two is no longer an anomaly. The rule in `AGENTS.md` — tell every
worktree child to report its commit, and treat a report without one as
unverified — is load-bearing and should not be relaxed.

## Verified by the Project Manager, not taken on report

Three findings were re-run on the main tree by the Project Manager, each mutation
applied, the full suite measured, then reverted with `git diff --quiet`
confirming clean. These are the load-bearing ones because each reaches a recorded
result field.

| Mutation | `file:line` | Suite |
|---|---|---|
| `B_stable` fold reads `null` as treatment and `constructive` as baseline — flips the sign of `B_stable` | `:3336-3340` | **183 passed** |
| `all_seed_controlled` replaced by the literal `True` | `:3729-3731` | **183 passed** |
| the entire qualifying-event construction branch disabled (`if stable_ok and flex_ok:` → `if False:`) | `:2168` | **183 passed** |

The third is the widest of the three: **no test in the suite drives the real
event-selection algorithm through to a qualifying event.** Every test that needs
an event either builds the dict as a literal fixture or monkeypatches
`roll_prefix_and_find_event` away. The one test that does call it for real is
built to make certification *fail* and asserts `event is None`.

The second matters because `all_seed_controlled=True` is the R3 §E provenance
that distinguishes this run from ep64, and it was cited as such in the round
question and relied on in the ruling.

## Reported and not independently re-run

Ranked by whether they reach a recorded result field.

**Reaching the primary result path**

- **Limb assignment is swappable.** `_process_audit_result:3397-3398` appending
  `unit_stable`/`unit_flex` to the opposite accumulators leaves the suite green;
  those feed `compute_t_m_bootstrap`'s `u_star_stable`/`u_star_flex` arguments
  directly. Same shape as the verified `B_stable` finding, on `U*`.
- **`topology_hash_ok` and `arm_distinct_ok` are never independently driven
  false** at `assemble_audit_result:3702-3703`; each can be replaced by `True`
  with the suite green. Both feed `conformance_ok`, which is branch 1 — the
  highest-precedence result branch. The helpers' own unit tests are real; it is
  the *wiring* that is unguarded.
- **The `null` schedule's REJOIN branch is unguarded** at `:1799` while its LEAVE
  twin is covered. A rejoin during a null continuation would silently re-run
  `constructive_mixed_update`, contaminating the null comparator toward the
  treatment arm — the `B_m` carrier, in the direction that flatters the claim.
- **Cutoff and depletion masks can be zeroed** at `:1833-1834` with the suite
  green. They feed the window latch and then `compute_G`'s `-5·cutoff` and
  `-10·depletion` terms. No fixture drives a battery to either threshold.

**Reaching the fixed-history identity**

- **Five of seven fields of `real_env_state_snapshot` can be zeroed** with the
  suite green (`:1849-1857`); only `battery_ratios` has a paired negative. This
  snapshot is what `compute_state_hash` hashes for the prefix-replay equality
  assertion, so the hash the contract leans on ranges over one field of six the
  docstring enumerates.
- **`replay_prefix`'s replay loop never executes in any test** — the single test
  that calls it passes `recorded_actions=[]`. Dropping every other recorded step
  leaves the suite green.

**Governance and lower severity**

- `_derived_seed`'s `tag` can be collapsed so `episode_seed == energy_seed` for
  every episode, suite green.
- `resolve_run_plan`'s `topology_seeds_override` branch has no test; a
  `--topology-seeds` override could be silently dropped.
- `_pinned_worker_env`'s pin and restore halves are both untested.
- `assemble_audit_result:3754`'s compound gate has both operands unranged.
- `_accumulate_episode_leave_stats` is unguarded only at exactly `T_E_MAX`.
- `main()` has **zero test coverage of any kind** — no test calls it.

## What this does and does not mean

**It does not say the recorded result is wrong.** The production code is correct
as written, and run `30289161086` executed that code. Every number in
`logs/d7s_audit_2_30289161086/` is what the correct code computes.

**It says the mechanical-validation evidence is weaker than it reads.** The
round's ruling leaned on conformance, support, topology identity, CRN pairing and
episode-world provenance having "passed". Three of those verdicts are produced by
code no test can break. A passing conformance report is currently evidence that
the code ran, not evidence that it is right.

The distinction matters and must not be collapsed in either direction: a sweep
that reports only hits over-claims, and a green suite quoted as coverage
over-claims harder. That second failure is the one this whole line of work
exists to stop.

## Deliberately not swept

Region B in full. Within A and C: `extract_step_metrics`'s three pass-through
fields, `step_once`'s ordering and fallback, `evaluator_forward_replay`'s
accumulation, most of `build_leave_candidate`'s remaining fields, `_target_id`,
`roll_prefix_and_find_event`'s `t_e` realization and hash ordering,
`_run_indexed_in_pool`'s body, the two thin episode workers,
`_compute_audit_episode`'s internal guards, `_new_episode_block_report`,
`_json_default`'s six branches, and `topology_unit_for_serialization`. The
pooler's own refusal conditions live in `scripts/pool_d7_s_event_aligned_shards.py`,
a separate file that was **not** swept and was wrongly assumed to be in region C
when the sweep was scoped.
