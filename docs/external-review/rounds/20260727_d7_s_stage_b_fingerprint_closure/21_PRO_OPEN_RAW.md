# Scientific ruling — D7.S Stage B fingerprint closure

**Stage reviewed:** `8cb5a232c2928aa8d6c5c173557da96c2038a329`

## Overall verdict

# **ALIGNED**

The sole blocker from the preceding Stage B ruling is closed.

The current realization now instantiates R3’s load-bearing requirement:

> A concrete, evaluator-certified event state is captured directly from the live environment; every conclusion-bearing continuation starts from an independently cloned copy of that state; and every continuation-sensitive state object either participates in the canonical identity or causes a loud coverage failure.

The precise scope of that assertion is:

> **`full_state_fingerprint` is a process-portable canonical identifier of a concrete state, used here to establish within-event snapshot/clone identity. It does not assert that `build_pinned_env(...)` is a complete seed-to-state reconstruction function.**

The cross-construction station-logistics discrepancy is a known environment-provenance limitation, but it does not reach the frozen D7.S estimand or its paired comparisons. It is therefore not a Stage B blocker.

**Scientific launch decision:** yes. The D7.S audit may return to the project’s ordinary conclusion-bearing compute-authorization path at this stage commit, with:

```text
n_select = 2
n_eval   = 2

initial topologies:
20260726–20260733

conditional expansion:
20260734–20260741
```

This review does not itself grant compute authorization.

---

# Q1 — Stage B alignment

## 1. Does the code instantiate R3?

**Yes.**

R3 requires the complete identity surface to cover continuation-sensitive physical, user, lifecycle, communication, routing, service-set, RNG and source-controller state, as well as the duty map, duty targets and service centroids. It explicitly requires inclusion by default and a written exclusion or loud failure for anything not covered.

The realization now satisfies that contract in four material respects.

### A. Recursive, fail-closed state coverage

The former three-shape dispatch has been replaced by a recursive encoder covering:

* arrays and typed scalar leaves;
* strings and bytes;
* dictionaries;
* arbitrarily nested lists and tuples;
* sets and frozensets;
* custom mutable objects through their `__dict__`;
* cyclic object graphs through bounded cycle markers.

Dictionary and set ordering is canonicalized over the encoded values rather than Python object representation or insertion order. An unsupported type raises `FingerprintCoverageError`; it cannot disappear silently. The explicit exclusions are restricted to fixed configuration, separately encoded RNG state, unused Gym spaces, and inactive rendering handles.

The RNG is not merely excluded. `_rng_state_token` separately encodes the actual `RandomState` or `Generator` state and now raises on missing or unknown RNG forms rather than degrading to a constant value.

### B. The external continuation state is bound into the same identity

The fingerprint recorded at event certification now includes:

* `duty_map`;
* `duty_positions`;
* `service_centroids`.

Those objects are therefore no longer side data that can change while condition 1C remains green.

`EventSnapshot` requires the duty positions and centroids as constructor arguments, stores copies, incorporates them into its initial fingerprint, and reuses them when checking source integrity and clone restoration.

### C. The tests can now fail against the defect they claim to guard

The closure tests do not merely compare two outputs produced from the same unchanged input. They independently mutate state forms the superseded implementation could not see:

* nested `routing_paths`;
* nested serving sets;
* packet dictionaries inside a list;
* mutable state inside a custom controller object;
* an unsupported object type;
* a real environment’s routing dictionary.

Each mutation must change the fingerprint, and an unknown type must raise.

Separate tests alter only the duty positions or only the service centroids and establish that event identity changes. They also drive the production `capture_event_snapshot` entry point rather than only testing a lower-level constructor.

Cross-process tests now establish that the encoder and registered stream seed are stable under different `PYTHONHASHSEED` values. The opaque-key test reverses physical object creation order between processes, directly exercising the former address-dependent dictionary sorting defect.

The broader guard sweep also added non-degenerate negative controls for bootstrap seed sensitivity and shard-order invariance rather than relying on fixed-seed or identical-topology fixtures.

### D. The world-replacement counter corruption is corrected

`regenerate_user_world()` replaces the user world rather than advancing it. The former implementation compared the new serving sets against the discarded world and booked phantom handovers, joins and leaves before the episode had stepped. That state was itself part of the event identity.

The environment now clears the connection, routing, service-set and lifecycle-counter baseline before rebuilding the regenerated world.

---

## 2. Could a test still pass through the previously wrong mechanism?

**Not through the mechanism identified by the frozen blocker.**

The old failure mode required one of the following:

* a nested mutable structure silently omitted;
* an unknown state type silently skipped;
* an address-dependent canonical order;
* duty geometry omitted from event identity;
* RNG state collapsing to a constant;
* or clone/source comparison operating on a hand-picked subset.

Each of those paths is now either:

* explicitly encoded;
* independently mutated in a test;
* observed across a process boundary;
* or converted into a loud failure.

Within the listed evidence and frozen state domain, I find no remaining path by which the old incomplete-fingerprint mechanism can satisfy conditions 1C, 2 and 5.

This is not a claim that the encoder is a universal serialization format. The disclosed unlength-prefixed string encoding is acceptable for the current closed state domain because none of the reachable strings contains a structural delimiter. Introducing arbitrary user-controlled strings is a re-review trigger. Likewise, the action and observation spaces may remain excluded only while they remain immutable configuration and the scripted audit never invokes `.sample()`.

---

## 3. Could an alternate implementation explanation change the registered conclusion?

**Not without violating a current fail-closed condition or a declared exclusion.**

Two implementations can no longer disagree about a nested routing, service, packet, controller or duty-geometry object while presenting the same complete event fingerprint—unless they introduce:

* a new unsupported value type, which raises;
* or a new explicit exclusion, which is a reviewable semantic change.

The concrete captured state, its auxiliary duty state, and the RNG state now form one identity surface. Each continuation clone is checked against that surface before use, and mutation of the immutable source is checked again after cloning.

Therefore the appropriate Stage B label is **ALIGNED**, not `SCIENTIFIC_AMBIGUITY`.

---

# Q2 — What does “complete-state identity” mean?

## Ruling

R3 §C freezes **identity of the concrete event state**, not complete reconstruction of that state from the registered seeds.

The exact formulation should be:

> `full_state_fingerprint` is deterministic across processes when presented with the same logical state. In D7.S it certifies that event certification, the immutable source snapshot, and all continuation clones refer to that same concrete state. It does not certify that two fresh calls to `build_pinned_env` with equal inputs generate the same complete environment state.

That distinction reconciles all the evidence.

## What is reproducible across constructions

The registered topology plus `user_world_seed` reproduces:

* user positions;
* user velocities;
* user and cluster waypoints;
* pause states;
* cluster assignments and centres.

The focused suite explicitly establishes that the episode-world fingerprint and UAV/user positions agree across independently constructed pinned environments.

This satisfies the substantive R3 §E requirement that the user world be a recorded, reproducible, topology-conditioned episode draw.

## What is not reproducible

The complete environment state remains construction-dependent because `reset()` derives several station-relative logistics fields before the registered charging-station coordinates are restored. The first environment step recomputes those fields, but one stale graph-potential difference remains accumulated in:

* `episode_graph_pbrs_sum`;
* the corresponding entry in `last_constrained_reward_metrics`.

The complete fingerprints of two fresh constructions therefore differ even with identical registered inputs.

The test suite correctly preserves both sides of this boundary:

* the episode user world must reproduce across constructions;
* the complete environment fingerprint presently must not be interpreted as seed-to-state reconstructibility.

## Why this does not alter D7.S

The construction-dependent remainder does not reach the registered result for four independent reasons:

1. D7.S computes its primary (G) from the QoS, capped return-cost, cutoff and depletion components. It never consumes the PBRS accumulator.
2. Every calibration or audit episode constructs one environment and forks all of its treatment limbs from one live event snapshot. The construction-dependent offset is shared before treatment.
3. The user-world provenance record itself reproduces.
4. Shard pooling never compares complete event fingerprints across independently created environments.

Thus the discrepancy is neither:

* an unregistered source random factor entering (G);
* nor a failure of SET/KEEP pairing;
* nor a failure of clone identity.

## Required scope annotation

The repository should record this narrower language:

* **User-world reconstruction:** supported by topology plus `user_world_seed`.
* **Concrete event-state identity:** supported by `full_state_fingerprint`.
* **Complete seed-to-environment reconstruction:** not currently supported.

This is a clarification of what the existing evidence proves. It changes no estimand, threshold, branch, population or implementation and does not require another design-freeze round.

## Should the station-logistics construction order be changed now?

**No.**

Recomputing the station-relative logistics after topology restoration would change the step-zero state and therefore every subsequent trajectory. That is a legitimate environment cleanup, but it is not required to make the current paired audit valid and must not be smuggled into the frozen run.

Keep it as a parked environment correction. Reactivate it if:

* a future estimand reads graph-PBRS state;
* a conclusion-bearing path requires fresh-environment replay;
* a result must reproduce the entire event state solely from registered seeds;
* or the stale logistics are shown to alter event support, source-control actions or primary-(G) components.

---

# Q3 — Does the audit launch?

## Scientific decision: **YES**

Stage B no longer withholds the D7.S audit.

The frozen volume and population remain:

```text
n_select = 2
n_eval   = 2

initial topology seeds:
20260726
20260727
20260728
20260729
20260730
20260731
20260732
20260733

expansion topology seeds, only under the frozen §9 rule:
20260734
20260735
20260736
20260737
20260738
20260739
20260740
20260741
```

These bindings remain explicit in the conclusion-bearing implementation.

The initial audit must be read on the eight registered topologies. The second eight are not an automatic retry or power rescue; they are used only when the already-frozen expansion predicate permits them.

## Hosted-job ceiling

The projected 6.2-hour worst shard against a 5.92-hour job stop is an operational scheduling risk, not a scientific blocker. The formal evidence contract no longer has an eight-hour launch gate, and cost projection is informational rather than an authority to shrink the scientific predicate.

A topology remains indivisible. If a hosted job kills one shard:

* do not pool a partial topology;
* preserve every completed whole-topology shard;
* rerun the failed topology whole at the same stage commit and contract;
* pool only after the union of seeds matches the frozen initial or expanded set.

The pooler fails closed on contract identity, smoke status, topology overlap and seed-union membership, sorts results by topology seed before inference, and invokes the audit module’s own result assembler rather than reimplementing the bootstrap or branch logic.

The non-degenerate shard-order test confirms that command-line shard ordering cannot alter the pooled bootstrap result.

---

# Smallest scientific updates

## Closed implementation defects

The following are no longer active blockers at this stage commit:

1. nested continuation state silently missing from the fingerprint;
2. unknown state types silently skipped;
3. address-dependent dictionary canonicalization;
4. duty positions and service centroids absent from event identity;
5. RNG coverage silently degrading to a constant;
6. world replacement being booked as pre-episode handover transitions;
7. bootstrap seed and shard-order guards that could pass vacuously.

This does not make the earlier `MISMATCH` wrong. It means the implementation implicated by that ruling has been replaced.

## Retained limitations

* `build_pinned_env` is not a complete seed-to-state generator.
* The exact complete-state fingerprint is not expected to match across fresh environment constructions.
* The current environment carries a construction-dependent PBRS accumulator offset that is outside D7.S’s primary (G).
* The recursive digest remains scoped to the frozen environment state domain and explicit exclusions.

## Unchanged scientific status

This Stage B closure produces no positive or negative update to:

* D7.S source necessity;
* R30;
* D7.3;
* D8;
* or the variable-individual-lifetime thesis.

Those remain pending the conclusion-bearing result. Under the project’s result semantics, implementation alignment is a prerequisite to scientific evidence, not scientific evidence itself.

---

# Retained realization portfolio

| Realization                                                                        | Status                   | Re-review trigger                                                                  |
| ---------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------- |
| Direct live-event capture + recursive fail-closed fingerprint + independent clones | **Selected and aligned** | A new mutable type, exclusion, RNG surface or auxiliary continuation input         |
| Full environment reconstruction from registered seeds                              | Parked enhancement       | A future causal path requires cross-construction event replay                      |
| Narrow UAV-side hash as complete identity                                          | Retired                  | None                                                                               |
| Fresh-environment prefix reconstruction as the conclusion-bearing reference        | Retired                  | Only after a separately registered deterministic whole-world reconstruction design |

## Scheduled next action

The next scientific action is the registered **joint held-out-topology D7.S audit**. No additional Stage B review is required unless the frozen contract, recursive fingerprint domain, environment binding, CRN semantics, replicate volume, topology set, inference or result mapping changes.

**D7.3 and D8 remain blocked until a valid D7.S result emits `PERSISTENCE_NECESSARY_SOURCE`.**
