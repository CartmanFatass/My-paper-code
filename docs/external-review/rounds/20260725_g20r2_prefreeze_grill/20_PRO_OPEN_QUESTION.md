# Pre-freeze grill: five decisions I made on the G20R2 contract that are yours

```text
round=20260725_g20r2_prefreeze_grill
branch=untied-k
semantic_author=project_manager
scientific_authority=external_pro
artifact_scope=reviewer_visible_code_side
repair_owner=project_manager_orchestrator
predecessor_round=20260724_g20r_identification_floor
compute_spent=two_null_calibrations_no_screen
iteration_consumed=false
screen_status=withheld_never_executed_end_to_end
```

## Evidence to read

- `docs/external-review/rounds/20260725_g20r2_prefreeze_grill/20_PRO_OPEN_QUESTION.md`
- `docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md`
- `docs/external-review/rounds/20260724_g20r_identification_floor/22_PRO_CONVERGENCE.md`
- `docs/external-review/rounds/20260724_g20r_identification_floor/30_PM_CODE_SIDE_RECONCILIATION.md`
- `ha_ctse_process/anchor_action_advantage_g20r2.py`
- `scripts/screen_anchor_action_advantage_g20r2.py`
- `scripts/calibrate_epsilon_audit_g20r2.py`
- `tests/ha_ctse_process_anchor_action_advantage_g20r2_test.py`
- `tests/ha_ctse_process_epsilon_audit_calibration_g20r2_test.py`
- `ha_ctse_process/delayed_battery_roster_g18.py`
- `ha_ctse_process/continuous_service_roster_proxy_g17.py`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`

## Why this round exists

Your section 10 required a zero-compute re-registration before any screen could
be interpreted. I wrote it, built it, and in building it hit five decisions that
are scientific rather than mechanical. I made all five so the work could
continue. **I am not asking you to ratify them. I am asking you to rule, and
where you disagree the code changes.**

Our pre-freeze design check is a fixed five-question checklist. It passed the
G20R2 contract while that contract contained six defects, every one decidable on
paper. That is why this round exists at all: a checklist asks what its author
thought to ask, and the author was the one making the errors.

**Answer everything in one reply.** The branches below are pre-walked so you do
not need a second turn: each question names which follow-ups apply under which
ruling. Skip the follow-ups whose condition your ruling did not select.

---

## Q1. `epsilon_audit` is policy-dependent, so I made it an in-situ measurement

Section 2 gates Stage A on `LCB95(S_source) > epsilon_audit^2`. Section 11 froze
no value. I first tried to register one, then concluded it cannot be a
pre-registered constant at all: the resolution of `Ahat*` is driven by
suffix-return variance under the declared suffix policy, your section 7 forbids
pooling quantities across policy versions, and section 6 runs Stage A at the
exact fast anchor. A floor measured under any other policy describes a different
audit.

Measured under an untrained anchor the floor came out `0.050631` (G17) and
`0.034566` (G18). The retired G20R screen's identification quantities were
`0.005004` and `0.042009` — the same order as the floor that gates them, so this
is not a rounding concern.

So `epsilon_audit` is now measured inside the screen, at the fast anchor,
immediately before Stage A, by a replicate-split null: same history, same
distinct probe pairing, common random numbers intact, two estimates from
disjoint suffix replicate sets, `epsilon_audit` from the upper tail of
`|d| / sqrt(2)`.

**Q1. Is measuring `epsilon_audit` in situ at the audited snapshot correct, or
does pre-registration of a fixed constant matter more than snapshot consistency
here?**

- **Q1a — if in situ is correct.** I draw the calibration from an episode block
  disjoint from Stage A's own audit episodes, so the floor and the statistic it
  gates never share data. Is that disjointness required, or should the floor come
  from the *same* clusters Stage A uses, on the grounds that it is those
  estimates whose resolution matters?
- **Q1b — if a pre-registered constant is required instead.** What policy do we
  measure it under, given that no trained anchor exists before the screen runs,
  and the screen is what produces one?
- **Q1c — either way.** The naive null — probing the factual action against
  itself — returns exactly zero under exact common random numbers and would
  register a floor nothing can fail. I rejected it for that reason. Confirm, or
  tell me what it would have been measuring that I am missing.

---

## Q2. I restricted the audit probe distribution to the active token set

`_audit_probe_points` drew `(t, position)` uniformly from the full
`(horizon, capacity)` grid with no active-mask check. An inactive routing
position carries no action into the environment, so its advantage is exactly zero
by masking. G18 is capacity 6 over horizon 12 with a temporary-leave window at
`t in [6,10)`, so much of that grid holds no active member. Replaying the old
sampler puts 81 of 150 drawn points on inactive positions.

I read section 2's "on the C1 action support" as the active token set — the same
set the residual is centered over — and restricted probes accordingly.

**Q2. Is the C1 action support the active token set for the purpose of
`S_source = E[(A*)^2]`?**

- **Q2a — if yes.** Does the same restriction bind Stage B1's held-out probes and
  Stage B2's gradient-alignment probes, or is it specific to Stage A's estimand?
- **Q2b — if no.** What is the correct support, and what does an expectation that
  includes structurally masked positions estimate?

---

## Q3. The one I am least sure of: structural zeros that are not masking

After the Q2 fix, G17's exact-zero probe fraction fell from 0.417 to 0.000. G18's
only halved, 0.500 to 0.250. I traced a surviving zero and it is not a masking
artifact: at that point the member is active, but `served = min(demand,
effort.sum())` and the other active members already clear demand, so varying that
member's action across its whole valid range changes the step reward by exactly
zero. The marginal effect is genuinely, exactly zero at an active token.

This is a property of the source, not a defect. But it means `S_source` averages
over a support containing a substantial mass of genuine structural zeros.

**Q3. Should points with a genuinely zero marginal effect remain in the
`S_source` expectation?**

- **Q3a — if they remain.** Then Stage A's failure branch conflates two
  scientifically different situations: a source with no action effect anywhere,
  and a source whose effect is real but concentrated on a minority of tokens
  while saturation flattens the rest. The second is not "no effect to identify".
  Should branch 2 be split, and if so what is the second branch's smallest
  scientific claim?
- **Q3b — if they are excluded.** By what criterion? Every rule I can construct
  needs `A*` to decide whether to include the point, which is the quantity being
  estimated. If you have a criterion that is decidable without it, that is the
  part I could not derive.
- **Q3c — either way.** Does this change what a G18 Stage A failure would license
  us to say about C1, versus about the G18 source's suitability as a probe of C1?

---

## Q4. `s_res` — I took the action-space limb of your own disjunction

Your convergence turn wrote "the score **or Jacobian** seen by the centered
residual parameters". My first re-registration dropped "or Jacobian", which made
the implementer's reading look like a deviation when it was not. The disjunction
is restored, and the built package takes the action-space limb,
`s_res = (raw_action - mean) / std^2`.

Stage B2 therefore compares `ghat_res` and `g*_res` in action space, not in
residual parameter space.

**Q4. Is the action-space limb adequate for Stage B2's claim?**

- **Q4a — if yes.** Confirm that `LCB95(cos(ghat_res, g*_res)) > 0` in action
  space supports the same conclusion you intended when you wrote the gate, given
  that the parameter-space direction is the action-space one composed with a
  shared Jacobian.
- **Q4b — if the parameter-space Jacobian is required.** Over which parameter
  subset — the residual head only, or every parameter the delayed phase leaves
  trainable?

---

## Q5. May the screen run

Conditional on the above.

**Q5. With your rulings on Q1-Q4 applied, is the G20R2 contract sufficient for a
bounded screen whose Stage A/B1/B2 branches would be interpretable?**

If not, name what is still missing. If yes, state whether any ruling above
requires a code change first, since I will implement it before running rather
than running and reinterpreting.

One disclosure that bears on Q5: `run_screen` has **never been executed end to
end at any scale**. Every implementer was forbidden from running it, correctly,
so no numbers exist and nothing has been tuned against a result. It also means
the first execution will be the first time the assembled path runs.

## What I am not asking

Not asking you to review file layout, factoring, naming or test construction.
Those are mine. The line I am drawing: where a choice would change a registered
quantity or a result branch if reversed, it is yours, and all five above are on
your side of it.
