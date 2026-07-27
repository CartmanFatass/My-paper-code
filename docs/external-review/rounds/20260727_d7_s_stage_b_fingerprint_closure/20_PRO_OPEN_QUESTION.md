# Stage B, second pass — the completeness blocker, and what closing it exposed

Your last ruling was `MISMATCH / NO LAUNCH` with one blocking item:
`full_state_fingerprint` did not cover the continuation-sensitive state R3 §C
makes load-bearing, so conditions 1C, 2 and 5 were not conclusive.

That blocker is closed. This round asks you to judge the closure, and carries one
decision that closing it forced into the open.

No verification labor is requested. Every number below is measured, with its
provenance named; nothing asks you to confirm an inventory.

Read at `stage_commit` on `untied-k`, pushed.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`
- `scripts/audit_d7_s_event_aligned.py`
- `envs/pettingzoo/scenario_base.py`
- `tests/audit_d7_s_event_aligned_test.py`
- `tests/pool_d7_s_event_aligned_shards_test.py`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_SIX_MORE_GUARDS_THAT_CANNOT_FAIL.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_WORLD_REPLACEMENT_BOOKED_AS_HANDOVER.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_PINNED_ENV_IDENTITY_IS_WITHIN_PROCESS_ONLY.md`

## What was implemented

**1. The blocker.** `full_state_fingerprint` is now a recursive canonical
encoder (`_encode_fingerprint_value`), not a three-shape dispatch. It covers
`None`, scalars, strings, dicts, arbitrarily nested lists/tuples, sets, and any
object exposing `__dict__` — which is what reaches a routing or source-controller
object's internal tables without hand-listing classes. Cycles resolve to a
bounded marker, seeded with the environment's own id so a back-reference like a
routing protocol's `self.env` terminates.

Anything with no rule raises `FingerprintCoverageError`. **Silence is no longer
an available third option**, which is the part of your closure list we treated as
load-bearing: the defect was never the omission, it was that the omission was
invisible. `FINGERPRINT_EXCLUDED_ATTRS` carries a written justification per
entry.

`EventSnapshot` now takes `duty_positions_at_te` and `service_centroids_at_te` as
**required** arguments, so the second half of the gap cannot reopen by omission.

**2. A defect in our own fix, found before you saw it.** The dict branch
initially canonicalized by sorting on `repr(key)`. For a key whose class defines
no `__repr__` that reprs as `<Foo object at 0x...>`, so the sort order was
address-dependent and identical state digested differently in different
processes — fatal for pooled shards, invisible in one process. It now sorts on
the encoded key. This is the blocker's own shape reintroduced one layer down.

**3. Six more guards that could not fail**, swept for internally rather than
waiting for you to find the third one, since you had found two in two consecutive
rounds. Each carries a concrete production mutation that used to leave the suite
green, and a demonstrated red-then-green. Three of them could move the result
branch. Detail in the evidence note; the most dangerous was bootstrap
determinism asserted as `f(x) == f(x)`, which a version ignoring its seed would
have passed while collapsing a variance component and over-narrowing `LCB95(U*)`.

**4. `_rng_state_token` raises** instead of degrading to the constant `"none"` on
attribute drift. It is the sole RNG coverage inside the fingerprint.

**5. An environment defect.** `env.uav_leaves_count` was 6 before the episode had
stepped: `regenerate_user_world()` diffed two pair-disjoint user worlds and
booked the outgoing serving cluster as departures. Serving-set state at `t_e` is
exactly what the fingerprint covers. Fixed by extracting
`_reset_connection_baseline()` and calling it before the rebuild; `reset()`
behaviour is byte-identical.

**Verification.** 197 focused tests pass. Clone conformance re-run against the
rewritten fingerprint on a clean hosted runner (`30278575924`):
`CLONE_CONFORMANCE_PASS`, all seven conditions, zero reconstruction replays.

## Q1 — the three Stage B questions

For the diff as a whole: does the code instantiate the frozen R3 contract; could
a test pass through the wrong mechanism; could an alternate implementation
explanation change the registered conclusion?

Return `ALIGNED`, `MISMATCH` (naming the frozen assertion and the conflicting
code path), or `SCIENTIFIC_AMBIGUITY` (naming one previously unstated
result-changing choice).

## Q2 — the decision closing the blocker forced open

Asking what the new fingerprint actually certifies produced a fact no test had
asserted in either direction.

**Two `build_pinned_env` calls with identical `episode_seed`, `coords`,
`coord_hash` and `user_world_seed` produce different `full_state_fingerprint`
values** — 4 distinct in 4 constructions — and they never converge, still
distinct after 20 steps.

Mechanism: step 5 overwrites `charging_station_positions` **after** `reset()` has
already derived the station-relative logistics from the construction-time layout,
which `scenario_base.py:328` draws from OS entropy (`RandomState(self.seed_val)`,
`seed_val=None`). Measured at step 0, `uav_return_threshold_ratios` differs
`0.56` versus `0.27` — a 2× spread on the return-to-charge trigger. The first
`step()` recomputes all six affected attributes; what survives permanently is one
contaminated potential difference accumulated into `episode_graph_pbrs_sum`.

**We have established that it reaches nothing**, on four independent grounds:

- `compute_G` is analyzer-computed from component fields and never reads a PBRS
  field, so it cannot enter `G`, `U*` or `B_m`;
- both conclusion-bearing call sites build one env per **episode** and clone every
  limb from it, so all limbs share one offset and it cancels in `SET − KEEP`;
- `episode_world_fingerprint` digests only the nine user/cluster arrays, every
  one measured identical — the R3 §E provenance record reproduces exactly;
- the pooler asserts no cross-shard fingerprint equality, and the one
  cross-construction comparison in the audit (`replay_prefix_to_te`) asserts the
  narrow `compute_state_hash`, whose seven keys are all uncontaminated.

So the instrument is not wrong today. What is now bounded is the **meaning** of
the term R3 §C calls the complete-state identity surface: it certifies
within-process identity — one live environment against its own clones — and not
reproducibility of a pinned environment across invocations. Two paired tests lock
that scope from each side, each observed red against its own mutation.

This is the **third** instance of construction-time OS entropy surfacing where a
construction-time quantity is load-bearing. The first forced task 14's coordinate
pinning; the second produced luck-dependent tests (measured 8 pass / 2 fail over
ten isolated runs at the unfixed parent); this is the third.

**Q2.** Does R3 §C's "complete-state identity surface" mean within-process
identity, which is what the instrument implements and what the audit needs — or
does it mean a pinned environment must be reconstructible from its registered
seeds?

- If **within-process** → we record the scope, change no code, and the seed
  defect stays a known limitation. Confirm this is what you froze.
- If **reconstructible** → seeding `scenario_base.py:328` from the registered
  seed changes step-0 state and therefore every trajectory, so it moves the
  estimand and cannot be a silent repair. Name whether it must be fixed **before**
  this audit runs, or is a separate registered change.

## Q3 — the audit launch

Cost, re-measured at `stage_commit` on a hosted runner rather than carried over.

```text
continuation rate, hosted, this commit : 0.0923 s/step   (run 30278575924)
continuation rate, hosted, prior commit: 0.0864 s/step   (run 30245735762)
local, prior commit                     : 0.0615 s/step
```

At `0.0923` the largest shard (`|Z|=8`) projects to **~6.2 h** against a job that
stops itself at 5.92 h. The previous projection was 5.77 h and sat just inside it.

We are **not** attributing the difference to the fingerprint rewrite. One sample
each, on shared hosted runners, cannot separate a cause from run-to-run
variance — and asserting a cause from two samples is a mistake this project has
already made once and written a rule about. The actionable fact is only that the
projection now straddles the ceiling rather than clearing it.

An overrun is recoverable: a topology cannot be split, but it can be re-run whole
and pooled, because the pooler keys on the seed set rather than run identity, and
`fail-fast: false` preserves every other shard's artifact. So the exposure is one
shard's wall clock, not the run.

**Q3.** Given your answers above, does the audit launch at `stage_commit`?

- If **yes** → confirm `n_select`/`n_eval` and the topology set (8 registered,
  expanding to 16 under §9's conditions).
- If **no** → name the single blocking item.

## Disclosed, not asked

Two implementation bindings we decided and are recording rather than putting to
you, because neither can change a claim:

- **The encoder's string branch has no length prefix**, so the encoding is not
  formally injective — a string containing a structural delimiter could in
  principle mimic nesting. Measured against the real environment: 61 distinct
  string values are reachable, **0** contain any of `, : ; { } [ ] =`, and the
  longest is `energy_runtime_before_charge_steps`. The collision is unreachable
  in this state space.
- **`observation_spaces`/`action_spaces` are excluded** from the digest. They are
  per-run configuration, identical across every clone by construction, and can
  hold a lazily-created `Generator` that the generic encoder cannot walk. This
  audit never calls `.sample()` on them — every arm is a scripted source control.
