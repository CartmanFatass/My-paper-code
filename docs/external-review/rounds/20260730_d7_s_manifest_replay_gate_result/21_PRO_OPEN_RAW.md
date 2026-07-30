# Scientific ruling — D7.S manifest-replay gate result

**Stage reviewed:** `a666b86caab06990d931ae346b637617ad6993c1`

## Overall disposition

# **KEEP THE GATE RED; REACTIVATE AND BROADEN THE ENVIRONMENT-CANONICALIZATION REPAIR; DO NOT YET FREEZE A1 OR A2**

The result supports an important but narrower positive:

> The schema-2 manifest reproduces the nine registered world arrays and, within one runtime, the observed event, candidate, and primary-\(G\) outputs over the exercised stable and flex continuations.

It does **not** yet certify Route A for conclusion-bearing use.

The failed `pre_step_state_fingerprint` is not a reason to weaken assertion 6 to “the manifest arrays match.” It exposes that the environment has no canonical post-initialization state after the topology, world manifest, and energy profile are installed. The identified station-distance caches are one carrier; `current_graph_potential` and the cached public `state` establish that the problem is broader than station logistics alone.

The correct smallest result is:

```text
MANIFEST_WORLD_REPLAY_SUPPORTED_ON_THE_EXERCISED_PATH

but

ENVIRONMENT_PRESTEP_CANONICALIZATION_NOT_ESTABLISHED
MANIFEST_REPLAY_NOT_CERTIFIED
```

The requested rulings are:

| Decision | Ruling |
|---|---|
| **5a — narrow assertion 6 or repair the environment?** | **Repair the environment. Retain complete identity, but evaluate it at the actual first-action boundary.** |
| **5b — A1 or A2?** | **Neither is frozen. A1 remains the first candidate to test; A2 remains the mandatory fallback.** |
| **5c — is cross-process enough?** | **No. A corrected cross-machine replay must pass before A1 is selected or the manifest enters the audit path.** |
| **5d — is construction-dependent `state` inside the claim?** | **Yes. It is inside the registered evidence surface and cannot be exempted from this gate on current evidence.** |

No confirmatory population may yet be instantiated.

---

# 1. Decision 5a — assertion 6

## Ruling: **do not narrow its state surface**

The earlier requirement was not merely:

> load the nine user-world arrays correctly.

It was:

> after loading the registered world and rebuilding its consequences, the episode begins from one identified pre-step environment state.

That distinction remains necessary. The current failure shows that the manifest-defined arrays coexist with derived environment fields inherited from an earlier construction state.

## 1.1 Move assertion 6 to the correct temporal boundary

The current probe computes `pre_step_state_fingerprint` immediately after manifest application, but **before** applying the registered energy permutation. Only afterward does it call `apply_energy_profile`. fileciteturn181file0L245-L276

That is not the actual first-action boundary of the audit.

The correct ordering is:

```text
construct/reset environment
pin and verify topology
apply and verify world manifest
apply registered energy permutation
run one canonical post-initialization refresh
compute complete pre-step identity
only then execute the first action
```

This matters because the measurement already shows that `uav_return_energy_margins` and `uav_return_threshold_ratios` converge when the energy profile is applied. Requiring those two arrays to agree at an intermediate state that is never stepped from is unnecessary.

That temporal correction is **not** a narrowing of assertion 6. At the final pre-action boundary, the complete registered identity must still match.

## 1.2 Reactivate more than the narrow station-cache patch

The station-distance diagnosis is well supported:

- `reset()` initializes charging stations and then computes `last_min_station_distance_before/after`;
- the registered station coordinates are restored later;
- the cached distances are not recomputed at that point. fileciteturn185file0L194-L220 fileciteturn185file0L222-L248

But the required correction is broader than:

```text
recompute last_min_station_distance_before
recompute last_min_station_distance_after
```

During reset, Scenario 7 also computes:

- return thresholds and margins;
- `current_graph_potential`;
- and the cached global `state`.

Those calculations occur before the final pinned world is established. fileciteturn185file0L240-L276

The selected scientific object should therefore be a **canonical post-pin initialization barrier**:

> Once topology, manifest world, initial energy, and other registered episode inputs are final, every derived state that may enter an action, transition, observation, event certification, reward component, or continuation fingerprint is recomputed from those final inputs.

Do not repair the six observed fields individually and assume the list is exhaustive. The same initialization barrier should own the invariant.

## 1.3 The environment change is now in scope

This is an environment-realization correction, not a result rescue:

- the historical R4 artifacts already remain invalid;
- no adverse valid result is being changed;
- no threshold, population, comparator, or branch is moved;
- fresh evidence would use a new, explicitly corrected environment realization.

The project’s result semantics permit correcting the smallest invalid implementation while preserving the historical observation. fileciteturn171file0L186-L208

---

# 2. Decision 5b — A1 versus A2

# **Do not freeze either yet**

The current result materially raises A1, but it does not establish it.

## What the cross-process result supports

Two independent local processes using the same manifest produced equal:

- world fingerprints;
- event metadata;
- duty-map identity;
- stable and flex unit digests;
- and post-prefix world digests.

The manifest replaced a different construction-time world on both sides, so this was an actual replay exercise rather than a coincidentally matching initial environment. fileciteturn175file0L18-L39

That is good proof-sized evidence for:

> manifest replay is internally deterministic within the observed runtime and exercised trajectories.

## Why it does not yet select A1

A1 is the proposition that an initial manifest plus a frozen runtime class is sufficient over the full conclusion-bearing process. The current evidence has three gaps.

### Gap 1 — no cross-machine exercise

Both executions were local processes. The design itself leaves A1 versus A2 open until full-horizon equality is established across independently provisioned runners. fileciteturn176file0L53-L66

### Gap 2 — the gate does not directly record continuation exogenous trajectories

`post_roll_world_digests` is captured after the prefix event search. It includes the RPGM transitions encountered **before event certification**, not the user and cluster trajectories produced inside every subsequent 139- and 550-step continuation fork. fileciteturn181file0L275-L286

The later `unit_stable_digest` and `unit_flex_digest` cover the serialized audit units. They establish equality of the recorded estimand outputs, but they are not a lossless record of the per-step user/cluster trajectories. fileciteturn182file0L3-L16

Two divergent exogenous trajectories can, in principle, produce equal aggregate or branch-relevant quantities. The previous ruling required both:

- exogenous trajectory equality;
- and primary-\(G\)/branch equality.

The current gate proves the second more strongly than the first.

### Gap 3 — no liveness witness for the post-initialization trig path

The full horizon was long enough to permit waypoint or cluster-target regeneration, but the artifact does not record whether any of the post-initialization trigonometric writers actually fired.

A meaningful A1 gate must report a positive liveness witness such as:

```text
post_manifest_user_waypoint_regenerations > 0
or
post_manifest_cluster_target_regenerations > 0
```

on at least one compared development trajectory. If all relevant generators remained dormant, equality would leave the exact A1-versus-A2 risk untested.

## Binding decision rule

Freeze this conditional decision now:

```text
Corrected cross-machine A1 gate passes
    -> select A1: manifest + registered execution runtime

Corrected gate first diverges in an exogenous continuation trajectory
    -> select A2: exogenous-process / random-tape replay

Gate is incomplete or does not exercise post-initialization generation
    -> A1 versus A2 remains UNTESTED
```

This preserves A2 as a live fallback rather than prematurely accumulating it.

---

# 3. Decision 5c — cross-process or cross-machine?

# **Cross-machine must come first**

Cross-process equality is sufficient to continue development work. It is not sufficient to:

- freeze A1;
- wire manifest replay into the conclusion-bearing audit;
- bind the fresh manifest inventory;
- or authorize a formal source result.

The next gate should use the same committed development manifest bytes on two independently provisioned cloud jobs.

For manifest replay, the jobs need not expose different CPU models. The previous ruling correctly distinguished:

- **generator portability**, for which heterogeneous runtimes matter;
- **byte-manifest replay**, for which two independently provisioned executions of the same immutable inputs are already informative.

The design records job identity rather than requiring differing CPU features for exactly this reason. fileciteturn176file0L187-L199

## Before that run

The cross-machine run should occur only after:

1. the canonical post-initialization barrier closes;
2. assertion 6 is moved to the actual post-energy, pre-action boundary;
3. the horizon gate records complete exogenous trajectories or lossless per-step digests;
4. post-initialization user/cluster regeneration liveness is demonstrated;
5. all required horizon fields are fail-closed rather than optional.

## Population status

The successor selection **rule** may remain frozen. Its application remains held.

Strictly speaking, the ascending rule plus the exclusion list and \(K=8\) already determines the eventual seeds. The important scientific distinction is not “selected versus unnamed,” but:

```text
precommitted and uninstantiated
versus
constructed, generated, or inspected
```

No candidate topology or manifest may be instantiated before the corrected cross-machine gate passes. fileciteturn177file0L49-L81

---

# 4. Decision 5d — does construction-dependent `state` matter?

# **Yes**

The construction-dependent `state` is inside the registered evidence surface for three reasons.

## 4.1 It is a public decision-time input

Scenario 7’s energy observation directly contains:

- `uav_return_threshold_ratios`;
- `uav_return_energy_margins`.

The same arrays are also appended to the global state. fileciteturn192file0L61-L106 fileciteturn192file0L148-L202

Thus the discrepancy is not merely an unused debugging cache. A policy, critic, event classifier, or later D7.3 predictor consuming the registered observation/state surface would see a different history.

The project’s final claim concerns learned decision-time behavior. A provenance repair that certifies only the scripted controller while leaving the policy input construction-dependent would not certify the source for the next research stage.

## 4.2 `current_graph_potential` is consumed by the transition/reward path

Scenario 7 carries `current_graph_potential` forward as the next step’s “before” potential and updates it after stepping. fileciteturn186file0L14-L33

D7.S’s analyzer-defined primary \(G\) excludes PBRS, so this particular field may not have changed the recorded primary-\(G\) units in the observed episode. That does not make it outside environment identity.

A single observed equality cannot prove it never changes:

- event support;
- state-dependent controller behavior;
- later policy inputs;
- or another conclusion-bearing environment quantity.

## 4.3 The frozen gate explicitly selected complete identity

Narrowing assertion 6 after it fails would replace:

> one registered episode state

with:

> whatever subset happened not to affect this one scripted result.

That is not an acceptable post-result definition.

### Live alternative, not selected

A narrower **causal-state fingerprint** could be scientifically valid if a prior, zero-compute read-set proof established that every excluded field is unreachable from:

- actions;
- transitions;
- event/candidate construction;
- primary \(G\);
- and every decision-time input used by the claim.

No such proof is present. Because `state` is explicitly a public input, it would not satisfy that exclusion in any case.

---

# 5. Challenges to §3

## 5.1 “Construction-borne, not replay-borne” needs qualification

The **origin** of the six differences is construction-borne: the same mismatch occurs between two plain constructions with no manifest.

But their **survival after replay** is a Route A integration defect.

The accurate statement is:

> The manifest payload does not create these values, but the current manifest application path fails to canonicalize or replace construction-derived state that remains live at the pre-step boundary.

Replay is exonerated as the source of the original bytes. It is not exonerated as a complete evidence-population reconstruction mechanism.

## 5.2 The six fields are not all station-distance-derived

The two `last_min_station_distance_*` caches are station-distance-derived.

The return threshold/margin arrays are downstream of station distance and battery.

But `current_graph_potential` is a graph-service potential computed from communication, user/UAV geometry, and backhaul capacity—not from charging-station distance. fileciteturn189file0L198-L238

`state` is a composite cache containing base state, energy state, station state, and stage identity. fileciteturn192file0L148-L202

The evidence therefore establishes **at least two stale initialization families**:

1. station/return-energy-derived state;
2. topology/world/radio-derived potential and public state.

The proposed station-only explanation is too narrow.

## 5.3 Assertion 6 currently fires at an intermediate state

As noted above, the probe fingerprints before applying the energy profile. Two of the reported mismatches disappear on the formal initialization path afterward. fileciteturn181file0L259-L276

The correction is to move—not delete—the assertion.

## 5.4 The current a8 gate is not fail-closed on horizon completeness

The gate skips a horizon field when it is absent on both sides:

```python
if field not in ha and field not in hb:
    continue
```

fileciteturn183file0L191-L202

Likewise, the probe records `snapshot_state_hash=None` when the snapshot object exposes no such field, and equality of two `None` values can look like a witness. fileciteturn181file0L289-L296

Before certification, require:

```text
event_found == True
every required horizon field present
no required field is None
stable and flex horizons equal their registered lengths
both audit units valid
trajectory liveness witness present
```

Absence is `UNTESTED`, not equality.

## 5.5 B5 is not fully closed by the current inventory hash

The inventory stores identity and component digests in each entry, but its `set_hash` is computed only from:

```text
relative_dir = payload_hash
```

It does not hash the full recorded identity, layout, or component-digest metadata. fileciteturn180file0L208-L235

Additionally, verification reloads the entries named by the inventory but does not scan for unlisted extra manifests on disk. fileciteturn180file0L255-L289

Before a formal population is generated, either:

- include the complete canonical entry in the set hash and reject unlisted on-disk entries; or
- make the conclusion-bearing runner consume exclusively the inventory entries and prove extras are unreachable.

The current statement that B5 detects an added episode key is not established by this implementation.

## 5.6 The successor population document contains an estimand contradiction

Its §1 still writes the retired ratio conditions:

\[
U^\*_{\mathrm{stable}}/B_H\le-0.10,\qquad
U^\*_{\mathrm{flex}}/B_H\ge+0.10,
\]

then immediately says the R4 absolute-margin contract carries the gates. fileciteturn177file0L40-L47

The successor is supposed to preserve the R4 five-\(G\)-unit absolute criterion. Remove the ratio statement before the final protected contract is frozen. This is a documentation/contract correction, not a threshold change.

---

# 6. Smallest scientific update

## Supported

1. Schema 2 materially improves manifest identity, completeness, generator-version, derived-state, and inventory handling.
2. The manifest-defined nine-array world was reproduced across the two observed processes.
3. The exercised event and primary-\(G\) units were identical within one runtime.
4. A complete environment state is not presently reconstructed after topology/world replacement.
5. At least one stale carrier is the charging-station distance cache.
6. The stale surface also reaches public state and includes a separate graph-potential carrier.

## Not supported

1. That manifest replay is certified.
2. That the six mismatches are all station-distance-derived.
3. That the mismatches are irrelevant to the source claim.
4. That A1 is sufficient across independently provisioned runtimes.
5. That A2 is required.
6. That the exercised episode actually triggered the post-initialization trigonometric regeneration whose portability A1 is meant to test.
7. That the current inventory fully freezes a population.
8. That any confirmatory topology may now be generated.

## Smallest failed unit

```text
final registered topology/world/energy inputs
× derived environment initialization
× complete pre-action state identity
```

This failure does not retire:

- Route A;
- the R4 absolute margin;
- the focal estimands;
- the hierarchical inference;
- R30;
- D7.3;
- or D8.

---

# 7. Retained portfolio

| Route | Status | Raising or lowering observation |
|---|---|---|
| **Canonical post-pin initialization + A1 cross-machine replay** | **Selected next evidence route** | Raised by complete pre-step identity and full-horizon exogenous equality across independent jobs |
| **A2 exogenous trajectory/random-tape replay** | Live fallback | Selected if corrected A1 diverges after initialization |
| Narrow causal-state gate | Parked | Reactivate only with a prior read-set proof; current public `state` prevents immediate use |
| Portable deterministic user-motion implementation | Parked contract change | Raise only if both A1 and A2 are impractical |
| Station-cache-only patch | Rejected as incomplete | Current graph potential and public state establish a second stale family |

---

# 8. Scheduled action

The next scientific action is one **development-only canonicalization and corrected replay-gate cycle**:

1. freeze the true first-action initialization order;
2. canonicalize every derived state from the final topology, manifest, and energy profile;
3. move assertion 6 to that boundary;
4. make a8 fail closed on missing fields;
5. persist lossless exogenous trajectory digests through the stable and flex continuations;
6. add a liveness witness that post-initialization waypoint/cluster regeneration was exercised;
7. rerun locally;
8. then run the same committed development manifest on two independent cloud jobs.

Only a corrected cross-machine `MANIFEST_REPLAY_PASS` may select A1 and release the deterministic fresh-population rule for application.

**The current gate remains failed. The manifest must not yet be wired into a conclusion-bearing path. No confirmatory population or formal compute is authorized.**