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

All three returned. Region B was the most rigorous: 90 anchored single-line
mutations, every anchor asserted to match exactly once and every mutant parsed
before any test ran, plus **20 reachability probes** — the same lines mutated to
reference an undefined name, so a red suite proves the line executes. That second
pass is what separates *executed but unasserted* from *never executed*, and it
found three lines the suite never enters at all. The other two sweeps did not do
this, so their green rows are weaker evidence than region B's.

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
| **every reported `g_total` halved** (`float(np.sum(g_series))` → `* 0.5`) | `:2888` | **183 passed** |
| **R2 blocking condition 5** deleted (`if clone_fingerprint != self.full_fingerprint:` → `if False:`) | `:2677` | **183 passed** |
| `B_stable` fold reads `null` as treatment and `constructive` as baseline — flips the sign of `B_stable` | `:3336-3340` | **183 passed** |
| `all_seed_controlled` replaced by the literal `True` | `:3729-3731` | **183 passed** |
| the entire qualifying-event construction branch disabled (`if stable_ok and flex_ok:` → `if False:`) | `:2168` | **183 passed** |

The first row is the worst finding in this repository to date. `g_total` is the
scalar every `B_m` and every `U*` is built from — `b_value` at `:3017-3024` is a
difference of two `g_total`s, and the paired contrast `U* = mean(eval_set) −
mean(eval_keep)` at `:3118-3120` is built from them too. **Its magnitude can be
scaled arbitrarily and no test objects.**

One methodological note against my own first attempt: my initial run of the
`g_total` mutation reported 183 passed with the mutation **not applied**, because
the heredoc invoked `python`, which is not on PATH here. A green suite on
unmutated code is exactly the false verification the sweeper definition warns
about. Both rows above were re-run with the mutated line printed off disk
immediately before pytest.

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

## Region B — the clone conditions and the G accumulator

**Three of the five R2 blocking conditions can be deleted with the suite green.**
Conditions 1C (event identity) and 4 (topology preservation) have provoking
fixtures and go red. Conditions **2** (mutation isolation, `:2636`), **3** (RNG
isolation, `:2657`) and **5** (complete-state restoration, `:2677`) can each be
replaced by `if False:` at 183 passed — and reachability probes prove all three
execute on every clone. They run; nothing ever violates them.

This is what "zero invalidated pairs" in the recorded run is made of. A
`CloneIsolationError` from those three is the only mechanism by which conditions
2–5 reach anything: it sets `event_invalid`, flows to `invalidated_pairs`, into
`compute_conformance_ok` at `:3705`, into `decide_branch(conformance_ok=…)` at
`:3787`, and out as branch 1 `INVALID_EVENT_ALIGNED_AUDIT`.

**`window_g_from_step_metrics` and `_baseline_masks` have no test at all** — 22
of 22 mutations green. Between them they produce every `g_total` in the run.
Zeroing the `-5·cutoff` and `-10·depletion` terms, swapping the two masks so each
weight attaches to the other's events, and halving the total are all invisible.
The only mention of `window_g_from_step_metrics` in the test file is a
`monkeypatch.setattr` that replaces it.

**The clone objects themselves are genuinely independent** — making the clone
*be* the source, and making it a shallow copy, both go red. That guard is real.

**`_rng_state_token` discriminates for `RandomState` only.** Its `Generator`
branch and both of its refusal sites are never entered by any of the 183 tests —
not merely unasserted, unreached.

**`verify_clone_conformance` is never called on the production audit path.** Its
four asserted booleans can all be hardcoded `True` at 183 passed, including the
`assert f(x) == f(x)` shape where the second "independent clone" is replaced by
the first result object. It does not reach `decide_branch`; it feeds the
standalone `CLONE_CONFORMANCE_PASS` certificate, three of whose seven conditions
are therefore computed by code that cannot report failure.

**The string branch's missing length prefix produces real collisions**, measured
rather than argued: `enc(["p","q"]) == enc(["p,str:q"])`, and at the
`full_state_fingerprint` level a two-attribute state and a one-attribute state
can produce an identical digest. Enumerating a real environment found 109 string
leaves across 19 attributes and **none currently carries a structural
delimiter**, so the recorded run is unaffected — but nothing constrains that, and
the string branch can be collapsed to a constant with the suite green.

**The SET arm's defining mechanism is mutually masked.** The focal-target
override and the virtual-LEAVE duty re-match each independently move the focal,
and the one test asserting SET differs from KEEP is satisfied by either. So the
override — forcing the focal toward its target for `DELTA` steps — can be removed
entirely at 183 passed.

## What this does and does not mean

**It does not say the recorded result is wrong.** The production code is correct
as written, and run `30289161086` executed that code. Every number in
`logs/d7s_audit_2_30289161086/` is what the correct code computes.

**It says the mechanical-validation evidence is weaker than it reads.** The
round's ruling leaned on conformance, support, topology identity, CRN pairing and
episode-world provenance having "passed". Those verdicts are produced by code no
test can break: three of the five clone conditions, the provenance flag, the
topology-hash and arm-distinctness wiring. A passing conformance report is
currently evidence that the code ran, not evidence that it is right.

**And the magnitude of the result itself is unguarded.** `g_total` can be scaled
by an arbitrary constant with the suite green. That does not sit in the same
category as the conformance flags: those affect whether a run is *admitted*,
while this affects *what number it reports*. Nothing in the suite would notice
either.

The distinction matters and must not be collapsed in either direction: a sweep
that reports only hits over-claims, and a green suite quoted as coverage
over-claims harder. That second failure is the one this whole line of work
exists to stop.

## Deliberately not swept

Within A and C: `extract_step_metrics`'s three pass-through
fields, `step_once`'s ordering and fallback, `evaluator_forward_replay`'s
accumulation, most of `build_leave_candidate`'s remaining fields, `_target_id`,
`roll_prefix_and_find_event`'s `t_e` realization and hash ordering,
`_run_indexed_in_pool`'s body, the two thin episode workers,
`_compute_audit_episode`'s internal guards, `_new_episode_block_report`,
`_json_default`'s six branches, and `topology_unit_for_serialization`. The
pooler's own refusal conditions live in `scripts/pool_d7_s_event_aligned_shards.py`,
a separate file that was **not** swept and was wrongly assumed to be in region C
when the sweep was scoped.
