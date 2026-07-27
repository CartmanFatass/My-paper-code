# The window-latch guard asserted a diagnostic, not the field that reaches `G`

Sixth instance of the unfailable-guard habit, found 2026-07-27 at `2574f57b` by
the sweep the previous instance suggested: **read each test's name as a
specification and check its quantifier.**

This one is in `scripts/audit_d7_s_event_aligned.py` — the analyzer that produces
the published event counts — not in the environment.

## What the guard was

`window_latched_counts` implements the frozen section-7 convention: within a
window, count **at most the first** false→true transition per UAV per type. One
test guards it:

```python
def test_window_local_counts_at_most_one_transition_per_uav():
    window = np.array([[False], [True], [False], [True]])   # shape (4, 1)
    result = audit.window_latched_counts(window, np.zeros_like(window))
    assert result["cutoff_count"] == 1
```

## Two independent reasons it cannot fail

**1. The fixture has one UAV.** The name quantifies over UAVs and the fixture has
a single column, so nothing varies the dimension the property is about. A
**fleet-global** latch passes.

**2. It asserts an output that is structurally incapable of violating the
property.** `cutoff_count` is `int(np.sum(cutoff_counted))` over a **boolean
array**. It cannot exceed one per UAV for *any* implementation, latch or no
latch. This is the clamp-asserting-its-own-bounds shape again, and it is why
removing the latch entirely is invisible here.

**3 — the aggravating fact: it is not even the field that reaches the result.**

```text
:2877  new_cutoff_count=int(latched["cutoff_per_step"][i + 1])   -> compute_G
:2886  cutoff_incidence=latched["cutoff_count"]                  -> diagnostic only
```

`compute_G` subtracts `5·new_cutoff_count + 10·new_depletion_count`, taken from
**`cutoff_per_step`**. The test asserts `cutoff_count`, which feeds only a
diagnostic. **The field that enters the primary quantity had no test at all.**

## Measured

| Mutation | Effect | Suite |
|---|---|---|
| `& ~counted` → `& (not counted.any())` | latch becomes fleet-global | **180/180 green** |
| `& ~counted` removed entirely | a recurrence recounts | **green**, incl. the original test |

The second is the one that shows the assertion is on the wrong output: with the
latch gone, `cutoff_per_step` for the original fixture goes `[0,1,0,0] →
[0,1,0,1]` — a phantom cutoff entering `G` as an extra `−5` — while
`cutoff_count` stays `1` and the test stays green.

## The repair

A three-UAV fixture with staggered first transitions and a recurrence for UAV 0
in the same fixture, asserting **both** outputs:

```python
window = np.array([
    [False, False, False],   # step 0 = t_e baseline
    [True,  False, False],   # uav0 first          -> counts
    [False, True,  False],   # uav0 recovers, uav1 first
    [True,  True,  True],    # uav0 RE-transitions (must not recount), uav2 first
])
assert result["cutoff_count"]    == 3
assert list(result["cutoff_per_step"]) == [0, 1, 1, 1]
```

Both reds observed, and they are caught by *different* assertions — which is the
point of writing both:

- fleet-global latch → `assert 1 == 3` on the count;
- latch removed → `[0, 1, 1, 2] != [0, 1, 1, 1]` on the per-step series.

240 tests green after the repair. Production code unmodified.

## The variant this adds to the rule

**Assert the field that reaches the result, not the one that is convenient.**
A guard on a diagnostic sibling of the real output reads as coverage of the real
output. Before writing an assertion, trace the value to the estimator: if the
quantity under test is never read by `compute_G`, the pooler, or the branch
decision, the guard is on a bystander.

This is the first instance where the test was not merely weak but **aimed at the
wrong quantity**, and it was found by the cheapest possible sweep — comparing a
test's name to its fixture shape. Five of the six instances so far would have
been caught by reading the name as a specification.
