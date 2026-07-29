# Scientific ruling — D7.S conformance-suite freeze

**Stage reviewed:** `ffabb41f83312e8606a99a114c9803404a7735a1`

## Overall disposition

# **FREEZE AFTER MODIFICATION**

The pre-repair baseline is useful and the central red-to-green procedure is correct. The current suite accurately records several real failures—especially P2–P4 and N6–N8—and correctly preserves P5 as a regression witness for the targeted `(b1)` repair. The recorded baseline of `6 failed, 4 passed, 4 xfailed` is internally consistent with the test file.

The suite is **not yet complete enough to freeze as the binding repair gate**. Four defects are load-bearing:

1. **N5 is incompatible with the frozen fail-closed semantics.** It passes a non-injective map to the future provenance producer and expects a result, whereas the correct implementation must reject that map before generating actions or provenance.
2. **The provenance schema is incomplete**: it has no state for an unassigned/idle UAV even though the production action path emits a stationary action when no duty exists.
3. Several supposed paired negatives—especially N1, N2 and N6—currently demonstrate that a violation exists, but do not establish that the production entry point or final guard rejects it.
4. The `xfail` arrangement is acceptable for recording the old baseline, but the standard test command could eventually succeed with the provenance interface still absent unless final acceptance explicitly prohibits all remaining XFAILs.

Accordingly, **step 1 is not yet closed**. Amend the suite, rerun it unchanged against the old implementation, and supersede the current baseline before landing the repair.

---

# 1. Case-by-case disposition

| Case   | Ruling                        | Required change                                                               |
| ------ | ----------------------------- | ----------------------------------------------------------------------------- |
| **P1** | **ACCEPT**                    | None                                                                          |
| **P2** | **ACCEPT**                    | None                                                                          |
| **P3** | **ACCEPT**                    | Retain as the real batching-path positive                                     |
| **P4** | **MODIFY**                    | Assert the expected multi-rejoin result, not only determinism and injectivity |
| **P5** | **ACCEPT**                    | Retain green-before-and-after as the `(b1)` regression guard                  |
| **P6** | **MODIFY**                    | Expand provenance semantics and bind them to the production action path       |
| **N1** | **REWRITE**                   | Current test is only a mathematical observation, not a production rejection   |
| **N2** | **REWRITE**                   | Call the actual action entry point and require fail-closed rejection          |
| **N3** | **MODIFY**                    | Distinguish it from N2 and require the correct failure reason                 |
| **N4** | **MODIFY**                    | Exercise both `CHARGING` and `STATION_RETURN`, and test the coverage consumer |
| **N5** | **REPLACE**                   | Current construction contradicts fail-closed injectivity                      |
| **N6** | **REWRITE**                   | Convert from a duplicate of P3 into an injected old-behaviour mutation        |
| **N7** | **ACCEPT WITH STRENGTHENING** | Verify the batch path actually invokes the final assertion                    |
| **N8** | **ACCEPT WITH STRENGTHENING** | Require the registered invalid-realization reason, not any exception          |

---

## P1, P2 and P3

These are faithful.

* P1 preserves the legitimate REJOIN behavior: an unassigned rejoiner may fill one nearest uncovered duty.
* P2 directly exercises the identified defect: an already-assigned rejoiner may not receive a second duty.
* P3 reaches the actual transition-batching entry point and requires the complete simultaneous LEAVE/REJOIN batch to end injectively.

No amendment is required.

---

## P4 — deterministic is not enough

P4 currently asserts only:

```text
two runs return the same map;
the returned map is injective.
```

That can pass through an incorrect implementation that simply ignores all REJOINers. Deterministic omission is still deterministic and injective.

P4 must additionally establish the registered multi-rejoin semantics. At minimum, freeze and assert:

* the exact number of covered duties after the batch;
* every already-assigned rejoiner receives no additional duty;
* every genuinely unassigned rejoiner fills at most one uncovered duty;
* available uncovered duties are processed under the frozen canonical rejoin order;
* the exact expected map, or an equivalently complete set of assignment assertions.

It is acceptable to split P4 into:

```text
P4a — multiple already-assigned rejoiners are skipped deterministically
P4b — multiple unassigned rejoiners fill uncovered duties deterministically
```

The current case mainly exercises the first situation because the LEAVE rematch can already assign the rejoining UAVs before the REJOIN loop runs.

---

## P5 — a green regression belongs in a red-to-green suite

P5 is valid and should remain green before and after the repair. It protects the scientific decision to select targeted REJOIN correction `(b1)` rather than a full atomic rebatch `(b2)`:

* reduced-fleet LEAVE rematching must remain intact;
* locked incumbents must remain preserved;
* the leaver must not retain a duty;
* the result must remain injective.

“Red-to-green suite” describes the suite’s purpose, not a requirement that every individual test begin red. Regression witnesses are necessary to detect an over-broad repair.

---

## P6 — the semantic idea is right; the current coverage is too narrow

P6 currently checks one all-duty-directed configuration and locally derives coverage from the returned provenance.

That is not enough to establish the new provenance surface. The suite must additionally prove:

1. exactly one provenance record exists for every physical UAV action;
2. each tag matches the branch that actually generated the action;
3. the action returned by the provenance path is bit-identical to the action used by the production path;
4. the conclusion-bearing `step_once` or its successor actually carries this provenance forward;
5. executable coverage is derived from the provenance in production rather than being recomputed locally only in the test.

Otherwise `scripted_source_actions_with_provenance` can be a correct but unused decorative wrapper while `step_once` continues calling the old actions-only function. The present production path still calls `scripted_source_actions` and receives actions alone.

One canonical action generator must own both outputs. A valid realization is:

```text
canonical action synthesis -> (actions, provenance)

scripted_source_actions(...)
    = projection returning only actions

scripted_source_actions_with_provenance(...)
    = full projection
```

Duplicating the action logic in two functions is not acceptable.

---

## N1 — currently a definition check, not a repair guard

N1 constructs:

```python
violating = {0: 2, 1: 2}
assert not _is_partial_injection(violating)
```

This proves that the test helper recognizes a duplicate holder. It does not prove that:

* the REJOIN path refuses the old behavior;
* the batch-level final assertion catches it;
* or the action generator rejects it.

N1 may remain as a tiny diagnostic lemma, but it does **not** count as the required paired negative.

Replace it with one of these equivalent production-facing constructions:

* inject the old REJOIN behavior into the transition batch and require the final assertion to reject it; or
* produce the historical `{0:2, 1:2}` output through the old behavior and pass it to the named assignment validator, requiring the registered invalid-realization failure.

---

## N2 — the current test never calls the action generator

N2 manually performs the lossy inversion and verifies that information disappeared.

That is a useful explanation of the historical defect, but it does not test:

> A raw non-injective map must not reach action generation.

The revised N2 must call the actual public action-synthesis entry point with a non-injective map and require:

```text
no actions returned;
no provenance returned;
registered invalid-source-assignment error emitted;
failure occurs before any reverse lookup is used.
```

The historical implementation performs the reverse lookup immediately and silently overwrites one duty.

---

## N3 — presently duplicates N2 and can pass for the wrong reason

N3 calls the proposed provenance function with a non-injective map and accepts any `Exception`.

Two problems follow.

First, its observable behavior is nearly identical to the corrected N2. It does not prove the ordering “validation before inversion.”

Second, `pytest.raises(Exception)` can pass because of:

* a missing fake-environment attribute;
* an unrelated lookup failure;
* malformed target geometry;
* or any other exception.

Freeze a specific invalid-realization classification, for example:

```text
SourceAssignmentInvariantError
reason = NONINJECTIVE_RAW_ASSIGNMENT
```

The exact Python class name is an implementation binding, but the reason must be specific and testable.

To keep N2 and N3 distinct:

* **N2:** the public production entry rejects a non-injective raw map.
* **N3:** a mutation that bypasses or delays the validator is caught, proving that validation is upstream of reverse lookup/action emission.

---

## N4 — the construction is valuable but incomplete

N4 deliberately uses an injective map, which is correct and important: map-shape checks cannot detect a duty whose holder is charging or returning to a station.

Keep that structure, but amend it in three ways.

### Exercise both source branches

The current test sets:

```python
uav_charging[1] = True
```

and therefore exercises only the docked `CHARGING` case. It does not exercise `STATION_RETURN`, despite its name and stated requirement.

Add a separate or parameterized station-return case with a noncharging UAV whose energy rule takes control of the action.

### Assert the provenance tag itself

Require:

```text
provenance[u] == CHARGING
```

or:

```text
provenance[u] == STATION_RETURN
```

rather than only checking the absence of its duty from a locally created set.

### Exercise the production coverage consumer

The test currently computes:

```python
covered = {p[1] for p in prov.values() if p[0] == "DUTY"}
```

inside the test. A repair could produce correct provenance but leave every conclusion-bearing consumer using `duty_map.keys()`.

The suite must exercise the actual `m_exec`/coverage derivation used by the source controller or audit.

---

## N5 — reject and replace

N5 passes this non-injective map:

```python
{0:0, 1:1, 2:2, 3:0}
```

to the future provenance function and expects it to return actions and provenance.

That directly contradicts the frozen fail-closed rule:

```text
noninjective executable map
lossy assignment inversion
    -> INVALID SOURCE-CONTROL REALIZATION
    -> no estimate and no synthetic zero
```

Under the correct implementation, N5 must terminate at the same invariant error as N2/N3. It can never reach its coverage assertion.

### Replacement N5

Use an **injective** raw assignment whose holder executes a non-duty action. The cleanest distinct case is an override:

```text
raw map:       duty d assigned to UAV u
action source: OVERRIDE
result:        duty d is not in m_exec and is not covered
```

This tests a genuine phantom claim without violating injectivity and remains distinct from N4’s charging/station-return cases.

---

## N6 — currently duplicates P3 rather than injecting a negative

N6 invokes the same transition batch as P3 and asserts that its output is injective.

Before repair, both fail for the same reason. After repair, both pass for the same reason. N6 does not independently establish that the **guard** rejects a mutated duplicate-holder batch.

Rewrite N6 so that it deliberately reintroduces the old behavior—for example, by monkeypatching the REJOIN helper or supplying an old-behavior transition callback—and then require the universal final assertion to fail.

This is the batch-integration counterpart to N7’s direct validator test.

---

## N7 and N8 — retain, but make the failure specific

N7 correctly requires a named callable final assertion and verifies that it accepts a valid injection and rejects a duplicate holder. N8 correctly prohibits “repairing” a bad map by silently dropping one duty.

Strengthen them by requiring:

* the registered invariant-error classification;
* an explicit reason such as `DUPLICATE_HOLDER`;
* and, through N6 or a separate spy, proof that the real transition-batch path calls the assertion.

A named validator that is never invoked by production is no protection.

---

# 2. Provenance-interface ruling

## Freeze the semantics now; do not freeze only what the repair chooses to expose

The concern in §3.1 is valid. Leaving provenance entirely to the repair would allow the implementation to define the observable that certifies itself.

Freeze the semantic object before repair:

```text
exactly one action-source record per physical UAV action

DUTY(d)
CHARGING
STATION_RETURN
OVERRIDE
IDLE_OR_OTHER
```

The proposed four-case enum is incomplete. The production action path has an ordinary branch in which `duty_id` is absent and the UAV is commanded to remain at its current position. That action is neither duty-directed, charging, station return nor override.

The tag must describe the branch that actually generated the action:

* override takes precedence when present;
* docked-in-place action is `CHARGING`;
* energy-directed station motion is `STATION_RETURN`;
* a target selected from `duty_positions[d]` is `DUTY(d)`;
* a no-duty stationary action is `IDLE_OR_OTHER`.

## Exact Python API

The precise function name and tuple representation are **realization bindings**, not protected scientific semantics.

The proposed interface is acceptable for this realization:

```python
scripted_source_actions_with_provenance(...)
    -> (actions, provenance)
```

but a semantically equivalent typed record or shared canonical action routine would also conform. Changing the symbol name alone should not require a new scientific review.

What is protected is:

* exhaustive and mutually exclusive source classification;
* one record per action;
* duty identity on `DUTY(d)`;
* production integration;
* fail-closed behavior on invalid assignments.

## What prevents self-certification?

The suite must test provenance in three independent directions.

### Producer correctness

Given hand-constructed pre-action states, independently predict the expected source branch and compare it with the returned tag. Cover:

```text
OVERRIDE
CHARGING
STATION_RETURN
DUTY
IDLE_OR_OTHER
```

### Action consistency

Verify that the returned action is the action implied by the claimed source:

* `DUTY(d)` points toward duty (d);
* `STATION_RETURN` points toward the selected station and requests docking;
* `CHARGING` holds position and requests docking;
* `OVERRIDE` follows the override;
* `IDLE_OR_OTHER` does not invent a duty.

### Consumer correctness

Feed forged or mutated provenance into the executable-coverage consumer and require it to reject:

* a charging action labelled `DUTY`;
* two UAVs claiming the same duty;
* a raw covered-duty claim with no corresponding `DUTY(d)` record;
* a provenance duty not present in the validated assignment.

Finally, require the production `step_once` path to expose or consume this exact provenance. A standalone correct wrapper that no conclusion-bearing path uses is insufficient.

---

# 3. `xfail` versus hard failure

## Pre-repair baseline

The four provenance cases may remain `xfail` for the **pre-repair historical baseline**. They accurately record that the interface does not yet exist and prevent collection from failing before the behavior cases can be enumerated.

They need not be converted into ordinary hard failures immediately.

## The current explanation of `strict=True` is false

The suite defines:

```python
pytest.mark.xfail(not _HAS_PROVENANCE, strict=True, ...)
```

When the interface appears, `not _HAS_PROVENANCE` becomes false and the xfail mark is inactive. A passing test is then an ordinary PASS, not an XPASS(strict) failure. Therefore the statement that a case “turns red the moment the interface lands without its mark being removed” is inaccurate.

This differs from the older unconditional strict xfail in `audit_d7_s_event_aligned_test.py`, which **will** become XPASS(strict) after the defect is fixed unless its marker is removed atomically.

## Final acceptance must be fail-closed

A normal pytest run can exit successfully with remaining XFAILs. Therefore the repair gate must freeze one of these equivalent requirements:

### Preferred

Run the final acceptance suite with:

```text
pytest --runxfail ...
```

and require every test to pass.

### Acceptable alternative

Require the result summary to contain:

```text
0 failed
0 xfailed
0 xpassed
0 skipped
```

and add an unmarked hard sentinel asserting that the provenance interface exists.

The final result may not be accepted as “green” when provenance tests remain XFAIL.

The old unconditional strict xfail in the broader focused suite must be removed or converted in the same atomic repair change; otherwise the full test suite will correctly fail on XPASS.

---

# 4. Assessment of the factual claims

## Supported

The following statements are correct:

* the recorded baseline is `6 failed, 4 passed, 4 xfailed`;
* P3 and P4 exercise the real transition-batching entry point;
* P4’s determinism assertion passes while injectivity fails;
* P5 is a legitimate before-and-after regression guard;
* N4’s injective-map construction is the correct way to show why map shape alone is insufficient.

## Incorrect or overstated

### “The fourteen cases faithfully realize all six positives and eight negatives”

Not yet. N1, N2 and N6 do not currently test rejection by the production guard, and N5 cannot pass under the frozen fail-closed contract.

### “The provenance interface has four exhaustive cases”

False. It omits the production no-duty/idle action.

### “N4 covers CHARGING/STATION_RETURN”

False as executed. It covers only `uav_charging=True`.

### “Strict xfail requires the mark to be removed”

False for the conditional xfail used in the new suite.

### “The suite is frozen”

Premature. Its overall structure is strong, but the amendments above alter several predicates and require a new old-code baseline.

---

# 5. Revised freeze procedure

The next sequence is:

1. Amend P4, P6, N1–N6 and the provenance schema as ruled above.
2. Add production-path provenance integration and specific invalid-realization reasons.
3. Rerun the **amended** suite against the unchanged old implementation.
4. Preserve the current baseline document; create a superseding pre-repair baseline for the amended suite.
5. Freeze the amended test source and its baseline hash.
6. Land atomically:

   * targeted REJOIN repair;
   * final injectivity assertion;
   * canonical provenance-producing action path;
   * executable-coverage consumer;
   * removal of the older unconditional xfail;
   * any implementation bindings required by the amended suite.
7. Run the final suite in fail-closed mode and require no failures, XFAILs, XPASSes or skips.
8. Only then rerun A1–A4, B and the revised C.

No conclusion-bearing topology panel may be selected before those development obligations close.

---

# Final disposition

The suite has the right architecture and several good non-vacuous witnesses, but **step 1 is not closed at this commit**.

The smallest blocking issues are:

```text
N5 contradicts fail-closed injectivity;
provenance omits IDLE_OR_OTHER;
the provenance path is not bound to production;
N1/N2/N6 are observations rather than rejection tests;
final acceptance can pass with provenance cases still XFAIL.
```

After those are corrected and a new pre-repair baseline is recorded, the suite may be frozen and used as the atomic gate for the targeted source-controller repair.

`D7.3` and `D8` remain blocked. This review authorizes neither implementation nor compute.
