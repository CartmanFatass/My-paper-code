# D7.S conformance suite — amended pre-repair baseline (v2)

Supersedes `D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE.md`, which described the
suite Pro rejected on 2026-07-30 (**step 1 not closed**, five blocking issues).
That document is retained as the record of what was measured and what review
changed; **this one is the live baseline.**

Suite: `tests/d7_s_source_assignment_conformance_test.py`.

## Amended baseline

```text
4 failed, 3 passed, 14 xfailed        (0.7s)
```

| Case | Now | After repair |
|---|---|---|
| **sentinel** repair surface exists (unmarked, hard) | **FAIL** | PASS |
| P1 unassigned rejoiner fills one nearest uncovered duty | PASS | PASS |
| P2 already-assigned rejoiner receives no second duty | **FAIL** | PASS |
| P3 simultaneous batch ends injective | **FAIL** | PASS |
| P4a multiple already-assigned rejoiners skipped deterministically | **FAIL** | PASS |
| P4b multiple unassigned rejoiners fill deterministically | PASS | PASS |
| P5 LEAVE regression (reduced fleet + locked incumbent) | PASS | PASS |
| P6a producer: one record per action, tag matches branch | xfail | PASS |
| P6b `IDLE_OR_OTHER` exists for a dutyless UAV | xfail | PASS |
| P6c action consistency with claimed source | xfail | PASS |
| P6d provenance actions bit-identical to production | xfail | PASS |
| P6e `step_once` carries provenance forward | xfail | PASS |
| N1 old REJOIN output rejected by the named validator | xfail | PASS |
| N2 public action synthesis refuses a non-injective raw map | xfail | PASS |
| N3 validation is upstream of the reverse lookup | xfail | PASS |
| N4a charging holder not executably covered | xfail | PASS |
| N4b station-return holder not executably covered | xfail | PASS |
| N5 override holder leaves a genuine phantom | xfail | PASS |
| N6 the batch path actually invokes the final assertion | xfail | PASS |
| N7 final assertion named, callable, classifies its refusal | xfail | PASS |
| N8 a bad map is refused, not silently repaired | xfail | PASS |

## What changed from v1, and why

**N5 replaced.** v1 passed a **non-injective** map to the provenance function and
expected actions back — contradicting the fail-closed rule frozen one round
earlier, so under a correct implementation it could never reach its assertion.
v2 uses an **injective** map whose holder executes an `OVERRIDE`, giving a genuine
phantom without violating injectivity and staying distinct from N4.

**N1, N2, N6 converted from observations to rejection tests.** v1's N1 asserted a
duplicate map is non-injective and N2 asserted a lossy inversion loses — both
true by construction, neither able to fail if the guard were deleted. All three
now drive a production entry point and require a **classified** refusal.
N6 additionally carries the **spy** proving the transition batch actually calls
the validator: *a named validator that is never invoked by production is no
protection.*

**`IDLE_OR_OTHER` added.** The enum omitted the ordinary no-duty stationary
branch. Now five tags, exhaustive and mutually exclusive.

**Provenance bound to production.** P6d requires the two projections to be
bit-identical (one canonical generator, no duplicated action logic) and P6e
requires `step_once` to carry provenance forward, so a correct-but-unused wrapper
cannot satisfy the suite.

**P4 split.** v1's P4 could pass through an implementation that simply ignores
all rejoiners — deterministic omission is still deterministic and injective. P4a
now pins the covered-duty count and per-rejoiner holdings; P4b covers the
complementary unassigned case and passes today.

**Error classification frozen.** `SourceAssignmentInvariantError` with specific
`reason` values (`NONINJECTIVE_RAW_ASSIGNMENT`, `DUPLICATE_HOLDER`), so
`pytest.raises(Exception)` can no longer pass on a missing attribute or malformed
geometry.

## Fail-closed acceptance — the marks cannot be trusted

Verified empirically:

```text
conditional xfail, condition False, test passes  -> PASS
unconditional strict xfail, test passes          -> XPASS(strict) -> FAILED
```

v1's docstring claimed the conditional form goes red by itself. **It does not.**
So acceptance must be one of:

- `pytest --runxfail ...` with every test passing; or
- a summary containing `0 failed, 0 xfailed, 0 xpassed, 0 skipped`.

`test_sentinel_the_repair_surface_exists` is **unmarked and hard** so the suite
cannot read green before the repair under either rule.

The older **unconditional** strict xfail
`test_rejoin_never_gives_one_uav_a_second_duty` in
`audit_d7_s_event_aligned_test.py` must be removed or converted in the same
atomic repair, or the full suite will correctly fail on `XPASS(strict)`.

## Combined repository state

Both suites together:

```text
tests/audit_d7_s_event_aligned_test.py
tests/d7_s_source_assignment_conformance_test.py

4 failed, 268 passed, 15 xfailed        (~8m02s)
```

Reconciles exactly against the v1 run (`6 failed, 269 passed, 5 xfailed`, 280
cases): the conformance file grew from 14 cases to 21, and 280 + 7 = 287 =
4 + 268 + 15. The audit suite contributes 265 passed + 1 xfailed and is unchanged.

## Regression boundary

Four failures, all named above. A fifth failure, or any failure outside this
file, is a **regression** and not part of the plan. No CI gate runs pytest
(`.github/workflows/d7s-audit.yml` does not invoke it), so the redness is local
and intentional.

> Deselecting these cases is not a fix. The only sanctioned route to green is the
> repair.
