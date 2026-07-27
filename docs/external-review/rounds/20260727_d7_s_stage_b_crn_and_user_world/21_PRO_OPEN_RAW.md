# Scientific ruling — D7.S Stage B CRN and user-world provenance

**Stage reviewed:** `4b9977b5c5209138f7c224c6aa1fa04a71ddfbaf`

## Overall disposition

# **MISMATCH**

The CRN repair is correct, and the `n_select=2 / n_eval=2` scientific floor remains valid. The topology-conditioned user-world construction should also be retained, with a correction to R3’s probability-model wording rather than a change to the bootstrap hierarchy.

However, the implementation does **not** yet instantiate R3’s load-bearing complete-state fingerprint:

> `full_state_fingerprint()` claims to cover all continuation-sensitive state but actually serializes only NumPy arrays, numeric scalars, and flat numeric lists or tuples. It silently excludes dictionaries, nested containers, sets, custom mutable objects, and the external duty-target/service-centroid state.

That directly conflicts with R3 §C and allows clone/restoration tests to pass while conclusion-bearing routing, service-set, packet, cache, or source-controller state is absent from the identity assertion.

Therefore the D7.S audit does **not** launch at this stage commit.

The answers are:

| Question  | Ruling                                                                                                                                |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1**    | `MISMATCH`                                                                                                                            |
| **Q2(a)** | The shared evaluate-token repair is the correct realization of continuation-level CRN                                                 |
| **Q2(b)** | `n_select=2`, `n_eval=2` stands                                                                                                       |
| **Q3(a)** | The causal estimand survives, but its probability measure must be restated as topology-conditioned; bootstrap levels remain unchanged |
| **Q3(b)** | Do not randomize the remote corner independently per episode                                                                          |
| **Q4**    | No launch. Single blocker: the incomplete complete-state fingerprint and the resulting non-conclusive clone/restoration guard         |

---

# Q1 — Stage B verdict

## 1. Does the code instantiate the frozen R3 contract?

**No.**

Several important parts are aligned:

* the event snapshot is now captured directly from the live environment in which certification occurred;
* reconstruction through a second fresh environment has left the conclusion-bearing path;
* `full_sync_SET` is restricted to shared check boundaries;
* the stable limb no longer locks the non-focal flexible duty;
* episode-world provenance is serialized and carried through shard pooling.

The decisive mismatch is R3 §C.

R3 requires the load-bearing fingerprint to cover every continuation-sensitive surface, explicitly including:

* routing paths and reusable channel/radio caches;
* handover and service-set state;
* source-controller scheduling state;
* duty map, duty targets, and service centroids;
* plus the physical, user, cluster, energy, lifecycle, and RNG state. It permits either a canonical recursive digest or exact deep comparison; the requirement is coverage.

The implementation iterates over environment attributes but records only:

* `np.ndarray`;
* numeric and boolean scalars;
* flat numeric lists or tuples.

Everything else falls through without being hashed. Dictionaries, lists of dictionaries, nested lists, sets, deques, and custom mutable objects are not included.

That exclusion is material rather than formal. The environment contains, among other things:

* mutable `metrics`;
* mutable `active_packets`;
* routing and routing-cache structures;
* service-set and handover histories.

The environment’s subsequent transition logic reads such state. For example, routing paths are snapshotted and used before routes are recomputed, while packet and routing caches are mutable continuation state.

There is a second part of the same mismatch. R3 requires duty targets and service centroids to be stored with—and covered by—the event-state identity. The event does hold those objects separately, but `EventSnapshot` fingerprints only the environment and `duty_map_at_te`; its constructor receives neither `duty_positions_at_te` nor `service_centroids_at_te`.

Thus two continuation inputs can differ while condition 1C, mutation isolation, and complete-state restoration all continue to pass.

---

## 2. Could a test pass through the wrong mechanism?

**Yes.**

The current focused tests establish that the fingerprint distinguishes worlds when an included NumPy array—such as `user_positions`—is changed. The mutation-isolation test similarly changes UAV position and battery arrays.

Those tests do not establish the R3 invariant for omitted state. A faulty clone could, for example:

* share or alter a nested `routing_paths` dictionary;
* alter a packet or routing-cache dictionary;
* alter `user_serving_sets`;
* or retain the wrong duty-position/service-centroid objects;

and still return the same `full_state_fingerprint`.

The same implementation and test suite therefore share an incomplete operational definition of “complete state.” This is precisely the class of Stage B failure in which a test passes because it adopts the same narrowed symbol binding as the code.

`copy.deepcopy` may in fact copy those structures correctly. That is not enough. R3 made the conformance assertion load-bearing because the scientific result must not depend on an unverified assumption about object-copy behavior.

---

## 3. Could an alternate implementation explanation change the registered conclusion?

**Yes.**

Consider two implementations that produce identical array and scalar fingerprints:

* **Implementation A:** routing paths, service sets, caches, packet state, duty targets, and centroids are deeply isolated.
* **Implementation B:** one or more of those nested structures are aliased, stale, or taken from a different event object.

Both can pass the current conditions 1C, 2, and 5. They need not produce the same:

* action guard decisions;
* reassignment continuation;
* QoS trajectory;
* legal candidate consequences;
* (B_m);
* (U^*_{m,\mathrm{src}});
* (T_m);
* or final result branch.

That is a direct conflict with a frozen assertion, so the correct overall label is `MISMATCH`, not merely `SCIENTIFIC_AMBIGUITY`.

The user-world variance question does expose a separate previously unstated scientific choice. I resolve that choice below, but it does not remove the fingerprint mismatch.

---

# Q2 — Continuation-level CRN

## Q2(a) — Is the repair correct?

**Yes.**

The correct CRN unit is:

[
(\text{topology},\text{block},\text{episode},\text{limb},
\text{event},\text{evaluation replicate}).
]

For each evaluation replicate (r):

* KEEP and every SET candidate must begin from independent clones of the same event snapshot;
* they must receive the same continuation base stream;
* the selected SET evaluation and KEEP evaluation must be paired using the same replicate index.

During candidate selection, by contrast, each candidate retains its own independent selection stream. Selection and evaluation remain disjoint namespaces.

That is exactly the distinction now implemented:

```text
phase = evaluate  -> EVAL_SHARED_CANDIDATE_TOKEN
phase = select    -> candidate-specific z_id
```

The audit path now derives the same evaluation seed for KEEP and SET at the same replicate index, while calibration gives `constructive_mixed`, `null`, and the stable-limb conformance control the same continuation base stream within their limb.

This matches R2’s frozen statement that two evaluation streams estimate selected SET and KEEP while sharing continuation base streams under CRN.

The defect was real and conclusion-bearing: production callers previously used `"KEEP"`, each `z_id`, or the schedule name as the seed input, so (U^*) and (B_m) were differences between independent continuation streams. The previous guard tested only `f(x)=f(x)` rather than the production caller.

### Scope of this ruling

CRN is required **within a limb**. Stable and flex estimate different quantities over different horizons, so the `limb` field may remain in `stream_seed`; cross-limb CRN is not required.

This ruling confirms base-stream CRN as frozen. It does not silently strengthen the contract into counter-based exogenous randomness indexed by entity and timestep. A future finding that SET changes the number or ordering of exogenous RNG draws would reopen the CRN realization, but the listed evidence does not establish such a contradiction.

---

## Q2(b) — Does `2/2` remain admissible?

**Yes. Freeze remains:**

```text
n_select = 2
n_eval   = 2
```

No volume change is warranted.

The earlier justification for `n_eval=2` required a non-degenerate paired empirical difference. The implementation now actually provides that:

* two independent evaluation replicate indices;
* SET and KEEP paired within each replicate;
* evaluation independent of the two candidate-selection streams;
* topology and episodes remaining the primary inferential units.

The correction therefore strengthens rather than weakens the admissibility of the `2/2` floor.

The interpretation remains narrow:

> The audit can resolve the registered source-level materiality branch under a minimally replicated empirical maximization; it cannot establish precise candidate rankings or a precision effect-size estimate.

Candidate instability must continue to appear through the registered selection-frequency and entropy diagnostics rather than being hidden behind the point winner.

No prior D7.S event-aligned result needs retraction because none was published. Any internal numbers generated before this repair remain non-evidence because their (U^*) and (B_m) contrasts were unpaired.

---

# Q3 — User-world factorization

## Q3(a) — Does the estimand survive unchanged?

**The causal contrast survives; the population measure does not survive verbatim.**

The local quantities remain unchanged:

[
U^*_{m,\mathrm{src}}
====================

## V^{\mathrm{SET}}_m

V^{\mathrm{KEEP}}_m,
]

[
T_{\mathrm{stable}}
===================

U^**{\mathrm{stable}}
+
0.10B*{\mathrm{stable}},
\qquad
T_{\mathrm{flex}}
=================

## U^*_{\mathrm{flex}}

0.10B_{\mathrm{flex}}.
]

What must be corrected is the probability model under which they are averaged.

The proper factorization is:

[
T \sim P_T,
\qquad
W\sim P(W\mid T),
]

[
\theta_m
========

\mathbb E_{T}
\left[
\mathbb E_{W,E\mid T}
\left[
U^*_{m,\mathrm{src}}(T,W,E)
\right]
\right].
]

Here:

* (T) is the pinned BS/station topology;
* the categorical remote-corner choice is determined by the BS quadrant in (T);
* the cluster offsets, individual user positions, motion, waypoints, and pauses remain episode-level stochastic draws conditional on (T);
* (E) includes the separately generated energy profile and other registered episode factors.

The implementation evidence establishes that user generation is a deterministic function of episode seed plus BS quadrant. The remote corner is a four-way branch on that quadrant; the remaining user geometry comes from the episode RNG.

### Bootstrap structure

**No new bootstrap level is needed.**

The existing hierarchy already has the right structure:

1. resample topology;
2. resample calibration episodes and audit events within topology;
3. resample selection and evaluation streams within events.

The remote-corner factor now loads the topology level. Residual user-world variation loads the episode level. That is exactly what the two-level topology/episode bootstrap can represent.

R3 §E should, however, be corrected from:

> user worlds contribute through within-topology episode variation

to:

> user worlds are topology-conditioned episode draws: topology-determined geometric factors contribute at the topology level, while residual user/cluster geometry and motion contribute through within-topology episode variation.

Likewise, “the statistical distribution remains unchanged” is too broad. The generator routines and continuous parameters are unchanged, but the **effective joint distribution and variance decomposition** have changed. The old process used a discarded, construction-time BS quadrant; the corrected process conditions the remote cluster on the infrastructure actually used by the episode.

This semantic amendment is ruled in this response and may be recorded without another scientific freeze round.

### Scope of the eight topologies

The initial eight registered topology seeds contain only three of the four possible BS-quadrant classes. That does not invalidate the frozen empirical topology ensemble, but it limits interpretation:

* the initial result is an equal-topology-weighted result over the eight registered topologies;
* it is not a theorem of uniform performance over all four quadrants;
* topology records should expose the quadrant composition;
* the seed list must not be changed post hoc to “balance” the result;
* the frozen expansion to sixteen remains available only under its existing conditions.

No re-registration of the eight topology seeds is required.

---

## Q3(b) — Should the remote corner be independently redrawn per episode?

**No.**

The remote cluster should remain conditional on the pinned infrastructure.

Drawing the corner independently from `user_world_seed` would restore a larger within-topology variance term, but it would do so by deliberately generating episodes in which the supposedly remote cluster may be near the actual base stations. That breaks the physical premise the forced-relay source is intended to instantiate.

The old behavior was not a desirable randomized design. It was an ordering defect:

1. generate users relative to one construction-time BS layout;
2. discard that layout;
3. install a different pinned topology;
4. run the episode without re-establishing the user–infrastructure relation.

The corrected process is scientifically preferable:

[
\text{pin topology}
\rightarrow
\text{draw user world conditional on that topology}
\rightarrow
\text{record seed and fingerprint}.
]

Randomness is preserved through cluster offsets, user positions, waypoints, motion, pauses, episode seeds, and topology sampling. There is no requirement that every source factor vary at every statistical level.

---

# Q4 — Does the audit launch?

# **No.**

## Single blocking item

> **`scripts/audit_d7_s_event_aligned.py::full_state_fingerprint` does not cover the complete continuation-sensitive event state required by R3 §C, and therefore conditions 1C, 2, and 5 are not conclusive.**

This one blocker includes its auxiliary-state manifestation: the fingerprint also does not bind the event’s duty positions and service centroids, even though those are continuation inputs explicitly named by R3.

The in-flight vehicle-probe artifacts must not become scientific evidence. Consistent with the question’s declared handling, margin, (U^*), and (B_m) outputs should remain unread and the run should not be pooled as a D7.S result.

## What closes the blocker

The fingerprint/conformance realization must cover recursive mutable state rather than only arrays and numeric leaves. The closure condition is semantic, not a required coding recipe:

* dictionaries, nested lists/tuples, sets, queues, and relevant custom-object state must be canonically compared or digested;
* routing paths and reusable routing/channel caches must be covered;
* service-set and handover state must be covered where live;
* packet and source-controller mutable state must be covered where it can affect the continuation;
* duty positions and service centroids must be bound to event identity;
* exclusions must be explicit and justified;
* a test must demonstrate that changing a nested routing/service/controller object changes the fingerprint;
* cross-limb clones must begin from the same complete identity surface.

The current direct live snapshot, CRN repair, `2/2` volume, topology seeds, episode counts, horizons, thresholds, bootstrap, and branch semantics need not change.

Once this single mismatch closes through the normal code-science alignment path:

```text
n_select = 2
n_eval   = 2
initial topology set = 20260726 … 20260733
expansion set        = 20260734 … 20260741
```

remain the frozen scientific design.

This review does not itself authorize the conclusion-bearing run.

---

# Smallest updates

## Refuted

1. `full_state_fingerprint` currently implements R3’s complete-state requirement.
2. Passing the present fingerprint-based clone tests proves isolation of routing, service-set, cache, packet, controller, and auxiliary duty state.
3. All user-world variability belongs at the within-topology episode level.
4. The pre-repair production path supplied continuation-level CRN.

## Retained

1. Direct live-event snapshotting is the correct fixed-history architecture.
2. Shared-prefix cloning is scientifically valid once complete-state conformance is real.
3. The CRN repair is correct.
4. `n_select=2`, `n_eval=2` remains the minimum admissible volume.
5. Topology remains the upper inferential unit.
6. User worlds should be sampled reproducibly **conditional on topology**.
7. The eight-topology initial set and conditional sixteen-topology expansion remain frozen.
8. D7.S remains live; there is no update to R30, D7.3, or D8.

## Scheduled next boundary

The next boundary is the minimal Stage B correction of the complete event-state identity surface. After that correction is reviewed against R3, the D7.S audit can return to its ordinary conclusion-bearing compute authorization path.

**D7.3 and D8 remain blocked until a valid D7.S result emits `PERSISTENCE_NECESSARY_SOURCE`.**
