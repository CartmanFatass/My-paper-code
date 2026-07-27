# The pooler's smoke gate was untested because its sibling gate kept catching the fixture

Tenth instance, found 2026-07-27 at `5fe1556f` by pointing iteration 29's
mechanical sweep at a surface no earlier sweep had touched: the shard pooler,
`scripts/pool_d7_s_event_aligned_shards.py`.

The sweep disables each refusal guard in turn (`condition -> False`) and reruns
`tests/pool_d7_s_event_aligned_shards_test.py`. It reads nothing.

## Result: four of seven guards, and two of three identity fields

```text
caught     contract_identity_mismatch         1 failed, 7 passed
UNGUARDED  smoke_without_allow_smoke          8 passed
UNGUARDED  smoke_flag_mixed_across_shards     8 passed
caught     topology_seed_overlap              1 failed, 7 passed
caught     seed_union_not_frozen              1 failed, 7 passed
UNGUARDED  at_least_two_shards                8 passed
UNGUARDED  shard_columns_same_length          8 passed

UNGUARDED  drop identity field "contract"             8 passed
caught     drop identity field "contract_id"          1 failed, 7 passed
UNGUARDED  drop identity field "procedure_version"    8 passed
```

Eight tests guarded seven refusals; four refusals had no test that could see
them removed.

## The new shape — two guards masking each other

The file contains a test named, in full,
`test_smoke_shard_is_refused_without_allow_smoke`. The name is exactly right.
Deleting the gate it names left the file **8/8 green**.

The cause is a pair, not a single test:

```python
if smoke_shards and not allow_smoke:                     # gate A
    raise SystemExit("refusing to pool smoke shard(s) ...")
if len({bool(s.get("smoke")) for s in shards}) > 1:      # gate B
    raise SystemExit("smoke-flag mismatch across shards: ...")
```

The fixture pooled one `smoke=True` shard with one `smoke=False` shard — a
**mixed** pair, which violates both gates at once — and asserted
`pytest.raises(SystemExit, match="smoke")`. Both messages contain the word
`smoke`. So whichever gate survived a deletion refused the pool and matched the
regex. Each gate was individually deletable **because the other one covered for
it**, and the assertion was too coarse to tell them apart.

Neither gate is redundant. They refuse different things and only a fixture that
violates exactly one can see either.

## Why gate A is the one that matters

Gate A is `SMOKE_NOT_A_RESULT`. The shape a **real** smoke run produces is not
a mixed pair — it is a **uniformly smoke** set, where gate B is silent by
construction. That case had no test at all.

Measured directly, gate A deleted, two uniformly-smoke shards:

```text
guard PRESENT :  REFUSED : refusing to pool smoke shard(s) ...
guard DELETED :  ACCEPTED  smoke flag on pooled output = True
```

with the test file green throughout. So the guard standing between smoke output
and a pooled scientific result was, in test terms, absent.

**Stated at its true severity and no higher.** The pooled dict still carries
`smoke: True` onward, so a careful downstream reader could notice. This is a
refusal, not a label, and the refusal was untested — but it is not the case
that a smoke result could reach a paper with nothing at all marking it. Saying
otherwise would repeat the error of over-accepting a plausible finding.

## Why the identity fields went untested — the fixture builder had no affordance

`_assert_identity` quantifies over every name in `CONTRACT_IDENTITY_FIELDS`.
`_write_shard` accepted a `contract_id=` keyword and **nothing else**. There was
no way, in the test file's own vocabulary, to write a shard with a wrong
`contract` or a wrong `procedure_version`.

This is worth separating from carelessness. The test author was not lazy about
the other two fields; the helper made those cases unwritable, and the missing
coverage followed from the helper's signature. **A fixture builder with no
affordance for a field is why that field goes untested** — the same shape as
this project's own rule that a duty without an affordance produces an invention
rather than a refusal, one level down.

## Repair

- `_write_shard` gained a general `overrides=` parameter, so every top-level
  shard field is now perturbable.
- `test_every_contract_identity_field_is_checked` parametrizes over all three
  fields and asserts each name is actually in `CONTRACT_IDENTITY_FIELDS`, so
  adding a fourth field without a case fails loudly rather than silently.
- The existing smoke test now matches `refusing to pool smoke shard` — one
  gate's own wording, not a word both share.
- `test_uniformly_smoke_shards_are_refused_without_allow_smoke` covers the shape
  a smoke run actually produces.
- `test_a_smoke_flag_mix_is_refused_even_when_smoke_is_allowed` unmasks gate B
  by standing gate A down with `allow_smoke=True`, so a mixed pair can only be
  refused by the gate under test.
- `test_pooling_fewer_than_two_shards_is_refused` and
  `test_internally_inconsistent_shard_columns_are_refused` cover the two
  refusals nothing had exercised. The second matters more than it looks: the
  five per-topology columns are `zip`ped, and **`zip` truncates in silence**, so
  a short column would drop whole topologies out of a pooled result with no
  error.

Eight tests became fifteen. The pooler was not modified.

## The paired negative — the sweep, rerun

```text
guards unguarded : 0 of 7   []
fields unguarded : 0        []
```

Each guard is now caught, and the failure counts distinguish them (the identity
sweep fails 4, the parametrized field cases 1 each), which is the check that the
new tests refuse for their own stated reasons rather than incidentally.

### One tooling note

The sweep restores the file by rewriting the original string and asserts
equality on that string, which passed. `git status` still showed the file
modified — a line-ending round trip through `write_text` on Windows, with no
content difference (`git diff --stat` empty). **A script that rewrites tracked
files should verify its restore with `git diff --quiet`, not with a string
compare**, because the string compare cannot see what the repository will
record. Reverted before commit; the pooler is unmodified.

## Corollary added to the guard rule

**One fixture violating two guards tests neither.** When a fixture is illegal in
more than one way, each surviving guard refuses it and the test passes no matter
which one you delete. Give each guard a fixture that violates only it, and match
on that guard's own message rather than on a word its siblings share.
