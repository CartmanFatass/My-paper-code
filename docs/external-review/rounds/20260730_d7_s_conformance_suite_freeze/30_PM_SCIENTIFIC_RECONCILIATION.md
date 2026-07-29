# Reconciliation — 20260730_d7_s_conformance_suite_freeze

Ruling: `21_PRO_OPEN_RAW.md`, archived byte-exact (21026 chars, UTF-8, no BOM,
round-trip verified). Scientific decisions are Pro's; the code-side consequence
is mine.

## The ruling

**FREEZE AFTER MODIFICATION. Step 1 is NOT closed at this commit.**

Five smallest blocking issues, verbatim:

```text
N5 contradicts fail-closed injectivity;
provenance omits IDLE_OR_OTHER;
the provenance path is not bound to production;
N1/N2/N6 are observations rather than rejection tests;
final acceptance can pass with provenance cases still XFAIL.
```

The architecture was judged sound — *"the suite has the right architecture and
several good non-vacuous witnesses"* — but several predicates change, so a **new
old-code baseline is required**. The current baseline document is superseded, not
deleted.

## What Pro confirmed

- the recorded baseline `6 failed, 4 passed, 4 xfailed`;
- P3 and P4 exercise the real transition-batching entry point;
- P4's determinism assertion passes while injectivity fails;
- **P5 is a legitimate before-and-after regression guard** — my §3.2 choice was
  right, and a green case does belong in a red-to-green suite;
- **N4's injective-map construction is the correct way to show why map shape
  alone is insufficient** — my §3.3 choice was right.

## Five things I got wrong

### 1. My `strict=True` claim was false — verified myself

The suite docstring said a case *"turns red the moment the interface lands
without its mark being removed"*. **False for a conditional xfail.** When
`not _HAS_PROVENANCE` becomes False the mark is inactive, so a pass is an
ordinary PASS.

Checked empirically rather than taken on assertion:

```text
conditional xfail, condition False, test passes   -> PASS
unconditional strict xfail, test passes           -> XPASS(strict) -> FAILED
```

The property I described belongs to the **older unconditional** strict xfail in
`audit_d7_s_event_aligned_test.py` — which Pro notes must be removed or converted
in the same atomic repair, or the full suite will correctly fail on XPASS. I
attached a true statement to the wrong marker.

### 2. N5 contradicts the contract I myself froze

N5 passes `{0:0, 1:1, 2:2, 3:0}` — **non-injective**, UAV 0 holds duties 0 and 3
— to the provenance function and expects actions back. The fail-closed rule I
wrote one round earlier says a non-injective map yields *no estimate at all*.
Under a correct implementation N5 terminates at the same invariant error as
N2/N3 and can never reach its coverage assertion.

I wrote a case that requires the system to violate my own frozen contract in
order to pass.

**Replacement:** an **injective** raw map whose holder executes a non-duty action
— an `OVERRIDE` — so the duty is a genuine phantom without breaking injectivity,
and remains distinct from N4's charging/station-return cases.

### 3. N1, N2 and N6 are observations, not rejection tests

N1 and N2 assert properties *of the violating value* rather than that the
production guard rejects it. N6 invokes the same batch as P3 and asserts the same
thing — before repair both fail for one reason, after repair both pass for one
reason, so N6 never independently shows the **guard** rejects a mutated batch.

N6 must instead deliberately reintroduce the old behaviour (monkeypatch the
REJOIN helper or supply an old-behaviour transition callback) and require the
universal final assertion to fire. That is the batch-integration counterpart to
N7's direct validator test.

### 4. The provenance enumeration is not exhaustive

It omits the production **no-duty/idle** action. `IDLE_OR_OTHER` is required.

### 5. N4 does not cover what I claimed

I described it as covering `CHARGING`/`STATION_RETURN`. **As executed it covers
only `uav_charging=True`.** It must exercise both source branches, assert the
provenance tag itself, and drive the production coverage consumer.

## The structural point behind three of these

N1, N2, N6 and N5 fail in the same way: **a test that asserts a property of a
value it constructed, rather than that production rejects that value.** N2 checks
that a lossy inversion loses; N1 checks that a duplicate map is non-injective.
Both are true by construction and neither can fail if the guard is deleted.

That is the same defect as A3's sampler and as my `covered|coverage` grep, in a
third costume: **the check never touches the thing it is supposed to protect.**
Pro's phrasing is the durable one — *"a named validator that is never invoked by
production is no protection"* — so N7/N8 additionally need a spy proving the real
transition-batch path calls the assertion.

## Fail-closed final acceptance

A normal pytest run exits successfully with remaining XFAILs, so the repair gate
must require one of:

- **preferred:** `pytest --runxfail ...` with every test passing;
- **acceptable:** a summary containing `0 failed, 0 xfailed, 0 xpassed,
  0 skipped`, plus an unmarked hard sentinel asserting the provenance interface
  exists.

**A result may not be accepted as green while provenance tests remain XFAIL.**

## Next

Amend per the case-by-case dispositions, record a **new** pre-repair baseline
superseding the current one, freeze the amended source and its baseline hash,
then land atomically: targeted REJOIN repair, final injectivity assertion,
canonical provenance-producing action path, executable-coverage consumer, removal
of the older unconditional xfail, and any required implementation bindings. Run
the final suite fail-closed. Only then rerun A1–A4, B and the revised C.

No conclusion-bearing topology panel before those close. `D7.3` and `D8` remain
blocked; neither implementation nor compute is authorized.
