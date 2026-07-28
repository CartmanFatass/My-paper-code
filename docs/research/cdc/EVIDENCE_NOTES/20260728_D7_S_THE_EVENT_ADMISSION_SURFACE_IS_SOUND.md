# The event-admission surface is sound

Sweep of the functions that decide **which events enter the audit at all** —
chosen because R4 needs a fresh evidence population and every quantity it will
report is computed over the set these admit. A defect here does not perturb a
value; it silently changes what is measured, which nothing downstream can detect.

```text
commit under test = b8a4d32c
baseline          = tests/audit_d7_s_event_aligned_test.py, 215 passed
region            = map_rejection_reasons, check_leave_eligibility,
                    certify_stable, certify_flex, transit steps,
                    select_joint_event, build_event_conformance_record,
                    legal_set_targets, focal_eligible_to_act,
                    arm_distinctness_check, compute_conformance_ok
```

The worktree again arrived at `4866eb4e` and was reset — **five dispatches, five
times.**

## The headline: this region is genuinely guarded

Recorded at the same length the failures would get, because a sweep that only
reports hits says nothing about coverage, and this is the first surface all
session to come back substantially clean.

| Target | Independent mutations driven red |
|---|---|
| `check_leave_eligibility` | 7 / 7 — every exclusion reason, and **both operands** of each compound condition separately |
| `certify_stable` | 5 / 5 — including `active` and `has_valid_incumbent` independently |
| `certify_flex` | 8 / 8 — both halves of the chained comparison, both operands of the survivor comprehension, and the tie-break |
| `legal_set_targets` | 4 / 4 — including both domain-bounds operands |
| `transit_steps` / `flex_transit_steps_for_env` | 2 / 2 |
| `arm_distinctness_check` | 2 / 2 |
| `compute_conformance_ok` | 3 / 3 |

**Verified personally**: each of `compute_conformance_ok`'s three conjuncts was
neutralized separately and a **different** test failed for each — the
invalidated-pairs conjunct hit an integration test that reaches `decide_branch`'s
branch-1 precedence, the other two hit their own unit tests. That is what
"independently covered, not mutually masked" actually looks like, and this
function had been flagged in an earlier note as never independently mutated.

Two shapes that had bitten elsewhere in this file were checked and found
**absent** here:

- `arm_distinctness_check` returns `True` vacuously on an empty list, exactly as
  it does on a genuinely distinct set. Both the `any`→`all` swap **and** the
  vacuous-empty-list flip drive red, and the latter also breaks four downstream
  driver tests — so the empty-list branch is load-bearing and is distinguished
  from the genuine-distinctness case.
- `certify_stable`'s `active` conjunct was a repaired defect from 2026-07-27. The
  repair holds.

## What is unguarded is diagnostic only

Three findings, all traced to reported fields rather than to admission or to a
registered quantity.

**Two rejection-map entries** — `EXCLUDE_EMERGENCY` and `EXCLUDE_OFF_SCHEDULE`
can be deleted from `_ELIGIBILITY_REJECTION_MAP` with the suite green. The
CENSORED and QUEUE_OR_OCCUPIED entries in the same dict **do** drive red. The map
feeds `rejected_counts` and `leave_diagnostics` only; the admission decision is
driven by the reason list's truthiness directly, never by the mapped vocabulary.
So a deletion misattributes a diagnostic tally and admits exactly the same events.

**Eleven of fourteen `build_event_conformance_record` field mappings** can be
nulled with the suite green. Only `battery_ratio`, `uav_charging` and
`source_control_schedule_identity` carry a genuine value assertion anywhere.

The reason is a named shape: the test asserts
`required.issubset(record.keys())`, which is a **structurally guaranteed
post-condition** — the function returns a literal dict with all fourteen keys, so
that assertion holds no matter what any mapping computes. It cannot fail.

This reaches `audit_events` in the result JSON and no branch decision or
estimator. But it means eleven of the fields a reader would use to verify
per-event provenance are not backed by test coverage.

## Two functions are dead in production

`select_joint_event` and `focal_eligible_to_act` are both defined, both
well-tested — `select_joint_event`'s conjunction drives three of its own tests
red — and **neither is called from anywhere in the repository except its own
tests**. `roll_prefix_and_find_event` inlines an equivalent loop rather than
calling `select_joint_event`.

Recorded rather than acted on. Their guard quality is real; their reach is nil.
This is the same shape as the branch that could not fire, arriving from the
opposite direction: there, live code with no test; here, tested code with no
caller.

## What this means for R4

The frozen R4 contract retains the event definition, stable and flex
certification, and legal focal SET alternatives unchanged. **Those are exactly
the functions this sweep found guarded.** The event set an R4 run would admit is
decided by code whose guards can fail — which is the precondition that matters
most, because a wrong event set is undetectable in the result.
