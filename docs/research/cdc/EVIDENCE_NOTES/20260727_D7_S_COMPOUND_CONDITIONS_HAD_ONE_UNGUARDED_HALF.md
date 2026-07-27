# Two certification predicates had a compound condition with one half unguarded

Seventh and eighth instances, found 2026-07-27 at `4a8a15b2` by continuing the
name-as-specification sweep into the section-2 certification predicates. Both
share a shape the earlier instances did not: **a single `if` combining two
conditions, where every fixture violates the same one.**

## 1. `certify_stable` never saw `active=False` — a real gap

```python
if not (active and has_valid_incumbent):
    reasons.append("no_valid_incumbent")
```

Five inputs, four conditions, because `active` is folded into the first conjunct
and **shares its reason string**. Five sibling tests cover
`has_valid_incumbent`, the displacement bound, `scheduled_to_leave_within_delta`
and the empty legal set. **None passes `active=False`.**

Green-leaving mutation — drop `active` from the conjunct:

```python
if not has_valid_incumbent:
```

**181/181 green.** An inactive UAV then certifies as stable, admitting events the
frozen section-2 predicate excludes and **widening the estimand's conditioning
set** — the category this project's own implementer rules call never an ordinary
design gap.

Repaired with an `active=False` case. RED observed (`assert not True`), GREEN
after revert.

## 2. `certify_flex`'s chained comparison — real gap, but defence in depth

```python
if not (prior_check_step < leave_step <= t_e):
```

Every fixture uses `leave_step` in `{479, 480, 485}` against `t_e = 490`, so the
**upper** half is satisfied by construction and only the lower half was ever
violated. Dropping `<= t_e` left **182/182 green**.

**Severity, stated accurately.** The sole production caller (`:2152`) passes
`leave_step=t+1, t_e=t+1`, so the bound is unreachable on today's path. This is
defence in depth, not a live risk. Saying otherwise would make this the eighth
alarming finding when it is the eighth *finding*, and over-accepting a plausible
one is the same failure as under-checking a test.

Repaired anyway — a causally impossible ordering must not certify — with RED
observed.

### A more interesting fact fell out of checking reachability

That same call site passes `prior_check_step=t` with `leave_step=t+1`, so the
**lower** half is structurally true as well. `leave_not_after_preceding_check`
therefore **cannot fire in production at all**: the whole predicate is degenerate
at the only call site.

This follows from the event *being* the leave, so `t_e == leave_step` by
definition, and is consistent rather than wrong. Recorded because a frozen
predicate that the production path cannot trigger looks like coverage in the
contract and is not — and because the next person to read section 2 should know
the check lives for other callers and future changes, not for this one.

## Also swept, and clean

- `focal_eligible_to_act` — all four conditions individually flipped.
- `compute_conformance_ok` — all three conjuncts individually flipped.
- `certify_flex`'s five reason strings — all asserted.
- `survivors[...]["support_ok"]` — the second conjunct of the qualifying filter
  is exercised `False` at test line 245.

Reporting the clean ones matters as much as the findings: a sweep that only ever
reports hits gives no information about what it covered.

## Running tally, eight instances

| Where | Shape |
|---|---|
| CRN seed, fingerprint cluster | external review — both sides same code path |
| six-guard internal sweep | `f(x)==f(x)`, degenerate fixtures, unrealistic seeds |
| S7 return threshold | clamp asserting its own bounds; two copies of one formula |
| S7 cutoff/depletion latch | name quantifies over UAVs, fixture has one |
| analyzer window latch | the above, plus **asserting a diagnostic, not the field `G` reads** |
| `certify_stable` | compound `if`, one half never varied |
| `certify_flex` | chained comparison, upper bound never violated |

**Six of the eight would have been caught by reading the test's name as a
specification and checking its quantifier.** The two here add a corollary:
**a compound condition needs one negative per operand**, because a single reason
string makes two conditions look like one.
