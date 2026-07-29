# D7.S — the amended suite, and the one amendment I could not make honestly

All five blocking issues are addressed. `tests/d7_s_source_assignment_conformance_test.py`,
baseline v2 in `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE_V2.md`.

**The decision I need is §4.** Discarding this question's framing is a legitimate
answer, including the claim in §3.4 that one of your amendments cannot be
satisfied before the repair.

## 1. Frozen inputs — not review surface

- Your 2026-07-30 rulings in full: partial injection; executable coverage; the
  amended lifecycle semantics; R5's domain; fail-closed with no synthetic zero;
  the R4 invalid-realization disposition; repair scope **(b1) plus a universal
  final injectivity assertion, not (b2)**.
- The five-tag provenance classification including `IDLE_OR_OTHER`.
- The fail-closed acceptance rule and your correction of my `strict=True` claim.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`.
- `D7.3` and `D8` remain blocked.

## 2. Amended baseline — repository fact

```text
4 failed, 3 passed, 14 xfailed
```

Failing: the unmarked hard **sentinel** (repair surface absent), **P2**, **P3**,
**P4a**. Passing: P1, **P4b**, **P5**. The other fourteen are conditional xfails
against the unbuilt repair surface.

## 3. What I changed, and one thing I could not

### 3.1 N5 replaced

You were right and the error was mine: v1 passed a **non-injective** map to the
provenance function and expected actions back, which contradicts the fail-closed
rule I froze one round earlier. v2 uses an injective map whose holder executes an
`OVERRIDE`, so the duty is a genuine phantom without violating injectivity, and
it stays distinct from N4.

### 3.2 N1, N2, N6 are now rejection tests

Each drives a production entry point and requires a **classified** refusal
(`SourceAssignmentInvariantError` with `reason`), not a property of a value the
test constructed. N6 carries the spy that proves the transition batch actually
calls the validator.

### 3.3 Provenance bound to production

P6d requires the two projections to be **bit-identical**, so one canonical
generator must own both outputs. P6e asserts `step_once` carries provenance
forward.

### 3.4 `[INFERENCE]` P6e is a source-text assertion, and I am not comfortable with it

P6e currently does:

```python
src = inspect.getsource(audit.step_once)
assert PROVENANCE_FN in src
```

That is a **grep against source text**, not a behavioural test. It passes if the
name appears in a comment and fails if the repair achieves production
integration by a different route — a shared canonical routine called under
another name, exactly the realization freedom you granted in your interface
ruling.

I could not find an honest pre-repair behavioural formulation: asserting that
`step_once` *returns* provenance would freeze a return-shape you deliberately
left as a binding. So I have left the weak version in and am flagging it rather
than presenting it as equivalent to the others.

**This is the same defect class the last round rejected** — a check that does not
touch what it protects — and I would rather you rule on it than have it sit in a
frozen suite looking like coverage.

## 4. THE DECISION

**(a) Is the amended suite now closeable as step 1?** If not, name what remains.

**(b) How should P6e assert production integration?** Options I see, none of which
I want to choose unilaterally:

- **(b1)** keep the source-text assertion, accepting it is weak and marking it so;
- **(b2)** freeze a minimal return-shape obligation on `step_once` (for example
  that its returned dict carries a provenance key), converting a realization
  binding into contract;
- **(b3)** assert it behaviourally through the coverage consumer — require that
  the executably-covered set computed inside a real `step_once` disagrees with
  raw map membership on a constructed phantom state;
- **(b4)** something else.

**(c) Does the repair now have everything it needs to be authorized?** Every
remaining case is xfail against an unbuilt surface, and I do not have
implementation authorization. If the answer to (a) is yes, is the atomic repair
change authorized, or is there a further gate first?

## 5. What I have not done

- Not repaired the controller, not built the provenance interface, the validator,
  the error class or the coverage consumer.
- Not weakened any predicate to reduce the failure count — the count went from 6
  to 4 because cases became **xfail against a frozen contract**, not because
  anything was relaxed.
- Not removed the older unconditional strict xfail; you require that in the same
  atomic change as the repair.
- Not rerun A1–A4, B or C. Not selected a topology panel.

## 6. Required response sections

1. Accept or amend, per case where it matters.
2. The (b) ruling on P6e.
3. The (c) authorization ruling.
4. Anything in §2 or §3 you judge false.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `tests/d7_s_source_assignment_conformance_test.py`
- `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CONFORMANCE_BASELINE_V2.md`
- `docs/external-review/rounds/20260730_d7_s_conformance_suite_freeze/30_PM_SCIENTIFIC_RECONCILIATION.md`
- `docs/research/designs/D7_S_SOURCE_ASSIGNMENT_CORRECTION.md`
- `scripts/audit_d7_s_event_aligned.py`
- `tests/audit_d7_s_event_aligned_test.py`
