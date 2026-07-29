# Reconciliation — 20260730_d7_s_conformance_suite_v2

Ruling: `21_PRO_OPEN_RAW.md`, archived byte-exact (17099 chars, UTF-8, no BOM,
round-trip verified). Scientific decisions are Pro's; the code-side consequence
is mine.

## The ruling

**FREEZE AFTER MODIFICATION — step 1 is still not closed.** The v2 suite is
*"materially better, but not the final frozen repair gate."*

Six remaining blockers, verbatim:

```text
P6e observes source text rather than production behavior;
N3's ordering poison is optional and can be vacuous;
N6 recursively calls its monkeypatched self;
the fake environment cannot execute the real station-return rule;
P6a and P6c do not fully distinguish the claimed action sources;
P4b bypasses the real multi-rejoin batch path.
```

**The most important part of this ruling is prospective:**

> this ruling closes the remaining scientific choices prospectively;
> PM authorizes and performs implementation after the v3 baseline exists;
> the repaired suite must pass fail-closed;
> no conclusion-bearing experiment is authorized.

So after six named amendments and a hash-bound v3 baseline, **no further Pro
design round is required before implementing the repair** — provided no protected
semantic choice changes. That is the first time authority to implement has been
delegated forward in this line of work.

## P6e — my flag was right, and the answer is (b3)

I raised P6e myself as the one amendment I could not make honestly. Pro
**rejected the source-text assertion** and selected a **behavioural variant of
(b3), strengthened with a production-consumer spy** — assert that the executably
covered set computed inside a real `step_once` disagrees with raw map membership
on a constructed phantom state, and spy to prove production actually consumes it.

Flagging it rather than shipping it was the correct call: it was the same
defect class as A3's sampler, and it would have sat in a frozen suite reading as
coverage.

## Three defects I introduced while fixing three others

### N6 recurses

My `_old_rejoin` falls through to `audit.constructive_mixed_update` for non-REJOIN
events — but I monkeypatched that same symbol, so the LEAVE path re-enters my own
stub. The case cannot do what it claims. **Rewrite before freeze.**

### N3's poison is optional and can be vacuous

```python
if hasattr(audit, "invert_duty_map"):
    monkeypatch.setattr(...)
```

If that symbol never exists, nothing is poisoned and the test passes having
checked nothing about ordering. A guard behind an `if` that may never hold is not
a guard.

### The fake environment cannot execute the real station-return rule

`_Env` is too thin for N4b and P6c to exercise the genuine energy branch, so
those cases cannot distinguish the sources they claim to.

## Four claims of mine Pro corrected

- **"All five blocking issues are addressed"** — not yet; P6e was explicitly
  unresolved and N3/N6 added new defects. I overstated the completion.
- **"N1, N2 and N6 each drive a production entry point"** — N1 and N2 do; **N6
  recurses** and reaches nothing.
- **"P6d requires one canonical generator"** — it requires *behavioural equality
  on its tested fixture*. Architectural uniqueness needs code review or broader
  branch coverage; a passing P6d does not prove it.
- **"Every remaining case is xfail against an unbuilt surface"** — not literally:
  sentinel, P2, P3 and P4a are unmarked hard failures. My own baseline table said
  so correctly while the question's prose did not.

## What Pro confirmed

- the baseline `4 failed, 3 passed, 14 xfailed`, and which cases sit where;
- **the replacement N5 and the five-tag expansion are conceptually correct**;
- P1, P4b and P5 pass; sentinel, P2, P3 and P4a fail.

## The v3 work, exactly

1. rewrite P6e behaviourally (b3 + production-consumer spy);
2. fix N3 (unconditional ordering proof) and N6 (no self-recursion);
3. complete the fake environment so the real station-return rule executes;
4. strengthen P3/P4 and the P6 action semantics — P4b must go through the real
   multi-rejoin batch path, and P6a must predict a single expected tag rather
   than accepting either;
5. rerun the amended suite against the **unchanged** implementation;
6. record and **hash-bind** a v3 pre-repair baseline.

Then ordinary PM authority may authorize the atomic implementation. The repaired
suite must pass **fail-closed**: no failures, XFAILs, XPASSes or skips, with the
older unconditional strict xfail removed in the same change.

`D7.3` and `D8` remain blocked. **No conclusion-bearing compute is authorized**
and no fresh topology panel may be instantiated or inspected.

## Standing note on the pattern

Across rounds 7–10 the same defect recurred in five costumes: A3's sampler built
the property it tested; my `covered|coverage` grep could not reach the
counterexample; N1/N2 asserted facts about their own fixtures; P6e grepped source
text; N3's poison sits behind an `if` that may never fire. Every one is **a check
that cannot fail for the reason it exists**.

The counter-discipline that actually worked, twice, was the paired-negative
scoring rule from obligation C: a mutation that cannot be constructed is neither
caught nor missed, and must be recorded as its own outcome. That is what surfaced
the non-injectivity in the first place.
