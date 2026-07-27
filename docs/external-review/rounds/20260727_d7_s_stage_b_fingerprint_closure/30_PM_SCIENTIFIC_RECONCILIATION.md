# PM scientific reconciliation — Stage B round two, fingerprint closure

Ruling archived at `21_PRO_OPEN_RAW.md`. Transport facts at
`50_MECHANICAL_INTAKE_RECORD.md`.

```text
disposition = ALIGNED
launch      = YES (scientific), compute authorization still the user's
blockers    = 0
```

## What was ruled

**Q1 — `ALIGNED`.** The sole blocker from the preceding ruling is closed. All
seven implementation defects it names are now inactive: nested continuation
state silently missing, unknown types silently skipped, address-dependent dict
canonicalization, duty geometry absent from event identity, RNG coverage
degrading to a constant, world replacement booked as pre-episode handover, and
guards that could pass vacuously.

The ruling is explicit that this does **not** make the earlier `MISMATCH` wrong —
the implementation it implicated was replaced.

**Q2 — within-process identity, as we read it.** R3 §C freezes identity of the
concrete event state, not reconstruction of that state from registered seeds.
Our scope statement was upheld verbatim in substance:

> `full_state_fingerprint` … certifies that event certification, the immutable
> source snapshot, and all continuation clones refer to that same concrete
> state. It does not certify that two fresh calls to `build_pinned_env` with
> equal inputs generate the same complete environment state.

All four of our grounds for "it reaches nothing" were adopted unchanged.

**The station-logistics reorder must NOT be done now.** It would change step-zero
state and every subsequent trajectory, and the ruling refuses to let that be
smuggled into the frozen run. It is a parked environment correction with four
named reactivation triggers.

**Q3 — the audit launches**, at `n_select=2 / n_eval=2` over the eight registered
topologies, expansion only under the already-frozen §9 predicate.

## The hosted-ceiling framing was demoted, and I had it half wrong

I sent the ceiling as a live concern. The ruling puts it in its place: an
operational scheduling risk, **not a scientific blocker**, and it states plainly
that cost projection is informational rather than authority to shrink the
scientific predicate.

Separately, my own number moved after the fence. A third hosted sample landed at
`0.0784 s/step` against `0.0923` and `0.0864` — ±9% around `0.0857`. **The step
that looked like a cost of the fingerprint rewrite was runner variance.**
Declining to attribute it in the question is what kept the ruling usable; had I
asserted a cause, I would have asked for a ruling on a fiction.

The ruling's recovery rule is stricter than what I had written down and replaces
it: on a killed shard, never pool a partial topology, preserve every completed
whole-topology shard, rerun the failed topology **whole at the same stage commit
and contract**, and pool only once the seed union matches a frozen set.

## Verified rather than accepted

The ruling asserts the pooler sorts by topology seed before inference and calls
the audit module's own assembler rather than reimplementing bootstrap or branch
logic. Checked directly: `pool_d7_s_event_aligned_shards.py:204`
(`rows.sort(key=lambda row: row[0])`) precedes `:217`
(`audit.assemble_audit_result(...)`, imported from the audit module at `:43`).
It holds.

The remaining load-bearing claims — `compute_G` never reading a PBRS field, one
env per episode with all limbs cloned from it, `episode_world_fingerprint`
reproducing, no cross-shard fingerprint equality — are our own measurements from
this iteration and were reported to the ruling as such.

## Two conditional re-review triggers, recorded because they are easy to trip

- **The unlength-prefixed string encoding** is acceptable only while no reachable
  string carries a structural delimiter. Measured now: 61 distinct strings, zero
  such. **Introducing arbitrary user-controlled strings is a re-review trigger.**
- **`observation_spaces`/`action_spaces` may stay excluded** only while they
  remain immutable configuration and the scripted audit never calls `.sample()`.

## Required scope annotation

The ruling requires the repository to record the narrower language. Three
statements, to be carried wherever the fingerprint is described:

- **User-world reconstruction** — supported by topology plus `user_world_seed`.
- **Concrete event-state identity** — supported by `full_state_fingerprint`.
- **Complete seed-to-environment reconstruction** — not currently supported.

This is a clarification of what existing evidence proves. It changes no estimand,
threshold, branch or population, and needs no further design-freeze round.

## What is now the only thing between here and a result

**Compute authorization, which is the user's alone.** The ruling says so in its
own words: "This review does not itself grant compute authorization."

Nothing else is outstanding. No further Stage B review is required unless the
frozen contract, the recursive fingerprint domain, the environment binding, CRN
semantics, replicate volume, topology set, inference or result mapping changes.
