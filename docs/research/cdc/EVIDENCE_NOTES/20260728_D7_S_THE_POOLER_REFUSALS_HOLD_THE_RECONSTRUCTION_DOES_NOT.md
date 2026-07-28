# The pooler's refusals hold; its reconstruction does not

First sweep of `scripts/pool_d7_s_event_aligned_shards.py` — 274 lines that had
never been mutation-tested. It combined the eight shards of the project's first
formal D7.S audit.

```text
commit under test = 222e9917
baseline          = tests/pool_d7_s_event_aligned_shards_test.py, 15 passed
mutations         = 19, every anchor asserted to match exactly once and the
                    mutated line printed off disk before each run
```

The worktree again arrived at `4866eb4e`, an unrelated commit, and was reset —
**four dispatches, four times.** That trap is not occasional.

## The cited claim holds

An evidence note had recorded, as a reason to trust the run:

> The pooler accepted the eight shards, which is itself a check: it refuses
> unless every shard shares the contract and procedure version, every smoke flag
> is false, the shards' seed sets are pairwise disjoint, and their union equals a
> frozen set.

**All seven `SystemExit` refusal sites are CLEAN**, and the four cited conditions
were each disabled independently with only their own dedicated tests failing.
They do not mask one another — each carries a distinct `pytest.raises(match=…)`
string. The compound frozen-set condition was split and both operands proved
load-bearing.

That sentence was worth something. Recording it plainly, because a sweep that
only ever reports hits gives no information about what it covered, and this file
is the first surface all session to come back substantially sound.

Also clean: the topology-seed sort that the module docstring names as load-bearing
(the bootstrap resamples by list position), the numpy dtype round-trip, and — a
direct check of my own recent change — the `component_invariance_evaluated`
fail-closed default at the `assemble_audit_result` call site, which cannot be
silently flipped.

## What is not sound: the reconstruction key whitelist

`_reconstruct_topology_result` decides which fields survive pooling. Five can be
corrupted with the suite fully green. **Two were verified by the Project Manager
directly**, with the mutated lines printed off disk:

| Mutation | Suite | Reach |
|---|---|---|
| **calibration limbs swapped** (`stable` reads `flex` and vice versa) | **15 passed** | `compute_t_m_bootstrap`'s `B_stable`/`B_flex` inputs — the quantities the branch gates on |
| **`topology_hash_failures` collection replaced by `[]`** | **15 passed** | `topology_hash_ok` → `conformance_ok` → branch 1 |
| qualifying calibration/audit counts swapped | 15 passed | `check_minimum_support` → `support_ok` |
| `invalidated_pairs` dropped | 15 passed | invalidated total → `conformance_ok` |
| `arm_distinctness_pairs` dropped | 15 passed | `arm_distinct_ok` → `conformance_ok` |

The hash-failure one is the worst in kind: a shard whose topology failed its
pinned-coordinate hash assert would be **silently dropped** from the pooled
conformance verdict. That is the shrinking-event-set shape, not a perturbed
value.

## One cause, not five

Every one of these traces to a single fixture. `_topology_result` is the only
builder for value-checking tests, and it makes the corrupted states
indistinguishable from the correct ones: one `qualifying` parameter sets **both**
counts, `invalidated_pairs` is hardcoded empty with no parameter to vary it, the
same arm pair appears in every call, and every value-checking call sets
`b_stable == b_flex`.

This is the *satisfied by the fixture* shape in its purest form — the property
holds because the input already had it, not because the code enforces it. The
repair is mostly to the fixture, not to the assertions.

`arm_distinctness_check([])` returning `True` vacuously, exactly as a
populated-but-uniform list does, is why dropping that field is invisible: the
fixture must contain a pair that would make the check return **False** or the
drop cannot be seen.

## Two findings deliberately not inflated

- **`episode_worlds` dropped** leaves the suite green and reaches
  `episode_world_provenance`, which the code's own comment says is *reported
  rather than gated*. Diagnostic reach, not branch reach.
- **The `arm_distinctness_pairs` int-key coercion** can be dropped with the suite
  green, but the only consumer compares dicts with `!=`, which is insensitive to
  key type as long as both sides are coerced uniformly — and JSON coerces both to
  strings. Recorded as unguarded-but-unreachable rather than a live risk.

The sweep also caught its own weak-fixture false negative: substituting
`calibration_units_d_a`'s source initially looked green, but only because the
substituted value landed in the same Part-A threshold bucket by coincidence. A
more discriminating substitution drove it red, so that field is **clean** — the
first probe was a bad probe, not a gap. Worth recording because the same
coincidence would have produced a confident wrong finding.
