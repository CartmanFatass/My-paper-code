# Scientific ruling — D7.S conformance suite v2

**Stage reviewed:** `34f148e47b6779065246f5bc0caafe4dbbb8bf4c`

## Overall disposition

# **FREEZE AFTER MODIFICATION — STEP 1 IS STILL NOT CLOSED**

The amended suite fixes the five conceptual blockers identified in the preceding review:

* N5 now uses an injective map;
* `IDLE_OR_OTHER` has been added;
* N1, N2 and N6 are intended as classified rejection tests;
* provenance is meant to reach the production path;
* and the unmarked sentinel prevents a superficially green result while the repair surface is absent.

The recorded pre-repair outcome,

```text
4 failed, 3 passed, 14 xfailed
```

is a valid record of what the current test file does.

The suite is not yet closeable because P6e is not the only remaining problem. Four additional realization defects would either let a false implementation pass or make a correct implementation fail for an unrelated reason:

1. P6e inspects source text instead of production behavior.
2. N6 recursively calls its own monkeypatched function on the LEAVE path.
3. N3 does not prove validation precedes reverse lookup when no `invert_duty_map` helper exists.
4. The provenance fixtures and assertions do not yet faithfully exercise the five source classes.
5. P3/P4 do not fully pin the lifecycle-batch semantics they claim to protect.

The suite should be amended once more, rerun against the unchanged old implementation, and recorded as a **v3 pre-repair baseline**. The current v2 baseline remains historical evidence and should not be overwritten.

---

# 1. Case dispositions

## P1 — unassigned rejoiner fills an uncovered duty

**ACCEPT.**

It isolates the legitimate REJOIN behavior that the targeted repair must preserve.

---

## P2 — already-assigned rejoiner gets no second duty

**ACCEPT.**

It directly exercises the selected `(b1)` correction and currently fails for the intended reason.

---

## P3 — simultaneous LEAVE/REJOIN ends injectively

**AMEND.**

The present assertion requires only:

```text
leaves/rejoins are correct;
output is injective.
```

An empty map, or an injective map that still contains the leaving UAV, could satisfy those conditions.

P3 must also assert:

* the leaving UAV is absent from the result;
* every holder belongs to the final action-capable UAV set;
* the expected number of duties is covered;
* the newly active rejoiner is assigned at most one duty.

For the current fixture, pin either the exact expected map or the complete expected holder and covered-duty sets. Injectivity alone is not the full positive semantics.

---

## P4a — multiple already-assigned rejoiners

**AMEND.**

Splitting P4 was correct. The current test improves on v1 by pinning coverage count and ensuring each rejoiner holds at most one duty.

It should additionally assert:

```text
set(output holders) == final action-capable UAV set
```

for this fixture. `len(first) == 4` does not exclude a stale leaving holder combined with an omitted active UAV.

---

## P4b — multiple unassigned rejoiners

**REWRITE THROUGH THE REAL BATCH ENTRY POINT.**

The current test manually executes:

```python
for u in (1, 2):
    constructive_mixed_update(..., event="REJOIN", event_uav=u)
```

and then calls that result evidence of canonical batching.

That only proves determinism under the order chosen by the test. It does not prove that `update_duty_map_on_transitions`:

* discovers the rejoiners in canonical order;
* applies the same order;
* or fills the expected uncovered duties.

Construct a batch with two REJOIN edges and no LEAVE edge, drive `update_duty_map_on_transitions`, and assert the exact expected map. This is the only honest production-path witness for multi-rejoin ordering.

---

## P5 — LEAVE regression

**ACCEPT.**

A green-before-and-after regression is appropriate. It protects the choice of targeted REJOIN repair over a full rebatch and ensures reduced-fleet rematching plus locked-incumbent behavior remain unchanged.

---

# 2. Provenance witnesses P6a–P6e

## P6a — one record per action and correct tag

**AMEND.**

### Fixture defect

The shared `_Env` fixture defines `_nearest_charging_station`, but not `_calculate_power_consumption`.

The real source logic calls:

```python
env._calculate_power_consumption(...)
```

when deciding whether a noncharging UAV should return to a station.

Therefore a faithful provenance implementation will cause several P6/N4 tests to fail with an unrelated `AttributeError`.

Add a deterministic `_calculate_power_consumption` implementation and explicitly bind the relevant return-reserve constant in the fixture.

### Ambiguous expected tag

For UAV 2, P6a currently accepts either:

```text
STATION_RETURN
IDLE_OR_OTHER
```

despite describing itself as independently predicting the branch.

With battery ratio `0.02` and a nonnegative transit-energy term added to the default `0.10` reserve, the intended branch is deterministically `STATION_RETURN`. Require that exact tag.

A positive producer test that accepts either of two semantically different sources does not establish producer correctness.

---

## P6b — `IDLE_OR_OTHER`

**AMEND SLIGHTLY.**

The current test checks only that the dock bit is zero.

For the registered no-duty stationary branch, require the complete expected action:

```text
horizontal motion = 0
vertical motion   = 0
dock request      = 0
```

Otherwise an arbitrarily moving no-duty UAV could still pass as `IDLE_OR_OTHER`.

---

## P6c — action matches its provenance

**EXPAND TO FULL ACTION SEMANTICS.**

The test currently verifies only the docking bit for `CHARGING` and `DUTY`.

That is insufficient:

* `CHARGING` could move while requesting docking;
* `DUTY(d)` could fly toward the wrong target while not requesting docking.

Compare the complete returned action against an independently constructed expected action for each source class:

```text
DUTY(d)
CHARGING
STATION_RETURN
OVERRIDE
IDLE_OR_OTHER
```

This may be one parameterized test or several smaller tests. The expected action should be derived from the hand-constructed state, not from the provenance producer’s internal helper.

---

## P6d — action projections are bit-identical

**RETAIN, BUT NARROW ITS CLAIM.**

Bit identity on one fixture proves that the two exposed projections agree on that fixture. It does **not** by itself prove that only one canonical generator exists; two duplicated implementations can agree on one input.

The architectural “one canonical generator” condition remains a PM-owned implementation review item. P6a–P6c plus P6d supply behavioral coverage across the five branches.

---

## P6e — production integration

# **REJECT THE SOURCE-TEXT ASSERTION**

The current test succeeds when a function name appears anywhere in `inspect.getsource(step_once)`. It can pass through:

* a comment;
* dead code;
* an unused branch;
* or a wrapper whose output never reaches the conclusion-bearing path.

It can also reject a conformant realization that uses a differently named shared canonical routine.

The question’s criticism of P6e is correct.

---

# 3. P6e ruling

# **Select a behavioral variant of (b3), strengthened with a production-consumer spy**

Freeze the following semantic triple for each primitive step:

[
(A_t,;P_t,;C_t)
]

where:

* (A_t) is the exact action dictionary passed to `env.step`;
* (P_t) contains exactly one source-provenance record for every action in (A_t);
* (C_t) is the executable covered-duty set derived from the **input pre-action duty map** and (P_t).

The provenance must correspond to the action actually executed at that step, before the post-step lifecycle map update.

## Required behavioral P6e

Use a minimal step-capable fake environment that records the actions passed to `env.step`. Give it an **injective** raw map in which one holder is non-duty-directed—for example, charging or under a focal override.

Call the real `step_once` and require all of the following:

1. The action dictionary recorded by `env.step` is bit-identical to the action dictionary in the step record.
2. Exactly one provenance record exists per executed UAV action.
3. The non-duty-directed holder is tagged `CHARGING`, `STATION_RETURN`, or `OVERRIDE` as appropriate.
4. The production executable-coverage consumer is invoked with that exact raw map and exact provenance.
5. The resulting (C_t) excludes the non-duty-directed holder’s raw duty and therefore differs from `set(duty_map.keys())`.
6. The provenance and (C_t) are carried forward in the step record or delivered to the next registered conclusion-bearing consumer.

A spy around `executable_covered_duties` is appropriate. A grep or source-text assertion is not.

## Return shape

It is acceptable to adopt a realization binding such as:

```text
step_result["action_provenance"]
step_result["executably_covered_duties"]
```

but the exact key names are not protected science. Renaming them later does not require Pro review as long as the behavioral P6e remains unchanged.

What is protected is that the actual production step—not an unused wrapper—carries (A_t), (P_t), and (C_t) consistently.

The current `step_once` calls the actions-only function and returns no provenance or executable coverage, confirming that this is a real pre-repair failure surface.

---

# 4. Negative-test dispositions

## N1

**ACCEPT AS A DIRECT VALIDATOR UNIT WITNESS, but correct the description.**

It does not itself drive the transition or action-production entry point; it calls the named validator directly. That is useful because N6 and N2 separately prove production integration.

Do not claim all N1/N2/N6 independently drive full production paths.

---

## N2

**ACCEPT.**

It calls the public action-synthesis surface with a non-injective map and requires a classified refusal before actions or provenance are returned.

---

## N3

# **REWRITE**

The current poison is installed only when an optional `invert_duty_map` helper happens to exist:

```python
if hasattr(audit, "invert_duty_map"):
    monkeypatch.setattr(...)
```

When that helper does not exist, `reached["inversion"]` remains false by construction, and N3 reduces to a weaker copy of N2. It can pass even if a dictionary inversion occurs before validation.

Use one of these two valid realizations:

### Preferred: guarded mapping plus validator spy

* monkeypatch the named validator with a spy that marks `validated=True` before delegating;
* pass a mapping whose read operations used for inversion fail unless `validated=True`;
* use a valid injective map so execution proceeds through validation and inversion;
* require the validator spy to have fired first.

This does not require a particular inversion-helper symbol.

### Acceptable binding

Freeze a named `invert_duty_map` helper as a PM implementation binding and require all reverse lookup to go through it. Then the current poison approach becomes valid, but absence of the helper must fail rather than silently skip the poison.

---

## N4a/N4b

**ACCEPT AFTER THE SHARED FIXTURE IS COMPLETED.**

The separation into docked `CHARGING` and noncharging `STATION_RETURN` is correct, and both exercise the production coverage consumer.

Add the missing power-consumption method to `_Env`, as noted above.

---

## N5

**ACCEPT.**

The replacement is faithful:

* raw map remains injective;
* the override takes physical action authority;
* the overridden raw duty is excluded from executable coverage;
* the case remains distinct from charging and station return.

---

## N6

# **REWRITE BEFORE FREEZE**

The current monkeypatch contains a recursion defect.

After replacing:

```python
audit.constructive_mixed_update = _old_rejoin
```

the fallback path inside `_old_rejoin` calls:

```python
audit.constructive_mixed_update(...)
```

which is now `_old_rejoin` itself. A LEAVE event therefore recurses instead of invoking the original implementation.

Capture the original before monkeypatching:

```python
real_update = audit.constructive_mixed_update
```

and delegate non-REJOIN events to `real_update`.

Also require the refusal reason to be `DUPLICATE_HOLDER`, rather than accepting any `SourceAssignmentInvariantError`.

With those amendments, N6 becomes the required proof that the real transition batch invokes the final validator.

---

## N7 and N8

**ACCEPT.**

They correctly establish:

* a named callable validator;
* acceptance of valid injections;
* classified refusal of duplicate holders;
* and rejection rather than silent “repair” by deleting a duty.

---

# 5. Assessment of the amended baseline claims

## Supported

The following are repository facts:

* current result is `4 failed, 3 passed, 14 xfailed`;
* P1, P4b and P5 currently pass;
* sentinel, P2, P3 and P4a currently fail;
* the remaining cases are conditionally xfailed because their required interfaces are absent.

The replacement N5 and the expansion to five provenance tags are conceptually correct.

## Incorrect or overstated

### “All five blocking issues are addressed”

Not yet. P6e is explicitly unresolved, and N3/N6 introduce additional test-realization defects.

### “N1, N2 and N6 each drive a production entry point”

N1 invokes the validator directly. N2 invokes the public action surface. N6 is intended to reach the batch path but currently recurses.

### “P6d requires one canonical generator”

It requires behavioral equality on its tested fixture. Architectural uniqueness must be established through code review or broader branch coverage.

### “Every remaining case is xfail against an unbuilt surface”

Not literally: sentinel, P2, P3 and P4a remain unmarked hard failures. The baseline table itself states this correctly.

### “P6a independently predicts every branch”

It currently permits either `STATION_RETURN` or `IDLE_OR_OTHER` for one UAV and therefore does not independently predict that branch.

---

# 6. Authorization ruling

## At this stage commit

# **THE ATOMIC REPAIR IS NOT YET READY**

The binding suite still requires the amendments above and a new unchanged-old-code baseline. Landing the repair against the present suite would leave P6e non-behavioral and N3/N6 unable to guard the claims assigned to them.

## After the exact amendments

Once the PM:

1. rewrites P6e behaviorally;
2. fixes N3 and N6;
3. completes the fake environment;
4. strengthens P3/P4 and P6 action semantics;
5. reruns the amended suite against the unchanged implementation;
6. records and hash-binds a v3 pre-repair baseline;

then **no additional scientific-design round is required before implementing the repair**, provided no protected semantic choice is changed.

At that point the ordinary Project Manager authority may authorize the atomic implementation containing:

* targeted REJOIN exclusion;
* final injectivity validator;
* canonical provenance-producing action synthesis;
* production executable-coverage derivation;
* production (A_t/P_t/C_t) integration;
* removal or conversion of the older unconditional strict xfail;
* and the unchanged frozen conformance cases.

The scientific principles assign code realization and technical acceptance to the Project Manager and explicitly state that an external review response does not itself authorize code or compute.

Therefore the boundary is:

```text
this ruling closes the remaining scientific choices prospectively;
PM authorizes and performs implementation after the v3 baseline exists;
the repaired suite must pass fail-closed;
no conclusion-bearing experiment is authorized.
```

After repair:

1. run the conformance suite with no failures, XFAILs, XPASSes or skips;
2. run the broader focused suite, removing the old unconditional strict xfail atomically;
3. rerun A1–A4 and B;
4. revise and rerun C;
5. only then resume D–F.

No fresh topology panel may be instantiated or inspected.

---

# Final disposition

The v2 suite is materially better, but it is **not the final frozen repair gate**.

The smallest remaining blockers are:

```text
P6e observes source text rather than production behavior;
N3's ordering poison is optional and can be vacuous;
N6 recursively calls its monkeypatched self;
the fake environment cannot execute the real station-return rule;
P6a and P6c do not fully distinguish the claimed action sources;
P4b bypasses the real multi-rejoin batch path.
```

Amend those cases, record the v3 old-code baseline, and then proceed through the ordinary implementation boundary without another Pro design round unless the implementation introduces a new protected choice.

`D7.3` and `D8` remain blocked. No conclusion-bearing compute is authorized.
