# Reconciliation — 20260729_d7_s_duty_map_injectivity

Ruling: `21_PRO_OPEN_RAW.md`, archived byte-exact from the emitted source
(21923 chars, UTF-8, no BOM, round-trip verified). Scientific decisions are
Pro's; below is the code-side consequence, which is mine.

## The ruling

**SELECT (a1): the double hold is a realization defect.** `duty_map` must be a
**partial injection** from executable duties to physical UAVs. A UAV may hold at
most one executable duty, because the source controller emits exactly one
physical action per UAV and obtains it by inverting the map. A non-injective map
is not a legitimate multi-duty state; it is an internally inconsistent controller
state.

**Branch (b): a phantom duty is UNCOVERED.** A map key is an assignment claim
only. Coverage requires an executable action-bearing incumbent.

**Branch (c):** A reopened at A1–A4 (solver and Hall-witness lemmas retained);
B's `1200/1200` retired as feasibility evidence; C was never closed and needs an
injectivity/executable-coverage precondition.

**R4:** the JSON stays immutable and `PART_A_CONTRADICTION` is not rewritten, but
its authoritative status becomes
`INVALID_R4_REALIZATION: DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`. It is
citable only as a descriptive external-return observation of the historical code
paths, including their noninjective behaviour.

## Where the question was wrong, and how

Pro falsified one of my §4 claims outright, and it is the load-bearing one.

I wrote that the defect "reaches any result only through the actions actually
flown", and that no registered quantity reads the duty map. **That is false.**
Verified in source at Pro's direction:

- `_stable_candidates_at` (`scripts/audit_d7_s_event_aligned.py:2627`) iterates
  `for d, u in sorted(duty_map.items())` — raw `(d, u)` pairs. A UAV holding two
  duties appears **twice** as a stable-certification candidate.
- `_flex_survivors_at` (`:2663`) assigns `survivors[u] = {...}`, keyed by UAV, so
  the same UAV's two entries **collapse to one**, retaining whichever duty was
  iterated last.

So the defect also changes the **conditioning set and the focal-action identity**,
not just the trajectories. The masked focal measurements are affected too.

**How I got it wrong is the part worth keeping.** I checked
`extract_step_metrics` and `step_once`, confirmed neither reads the duty map, and
then stated a claim about *every* registered quantity. I verified one consumer
and generalized to all consumers. The grep I ran (`covered|coverage`) could not
have found `_stable_candidates_at`, because that function reads the map without
using either word. A search whose vocabulary is drawn from the claim cannot
falsify the claim.

This is the same failure as A3 one level up: A3 asserted injectivity and checked
it with a generator that built injective maps; I asserted a scope and checked it
with a search confined to that scope.

## What Pro corrected in my favour

- **A3 is rescuable, not to be replaced.** My "no replacement is written here,
  the conclusion is not rescuable by a smaller edit" was too strong. A3 follows
  immediately once the treatment domain becomes the injective executable
  assignment relation. No derangement over holder–duty tokens is needed.
- **"Both arms emit phantom duties" holds only at the high level** — the raw map
  claims an assignment no duty-directed action executes. At representation level
  they differ: duplicate-holder overwrite versus inactive-holder staleness. The
  note already said the census detects only the former; Pro confirmed that
  acknowledgement was correct.
- **The 33.33% is a development-topology observation, not a population
  estimate.** It establishes recurrence, not the rate on the R4 panel. I did label
  it development-only; recording the constraint explicitly so it is never quoted
  as a rate.
- **The same-step LEAVE+REJOIN onset explanation is locally supported** and
  agrees with the code ordering, but must not be generalized as the only future
  route to non-injectivity once the controller changes.
- **C's `UNCONSTRUCTIBLE` bucket is honest but does not establish witness
  completeness.** The witness may detect its mutations while still accepting a
  non-injective starting map.

## Semantics now frozen

```text
ASSIGNMENT   the executable duty assignment is a partial injection: each
             executable duty has at most one holder, and each action-bearing
             UAV holds at most one executable duty.

COVERAGE     a duty is covered iff exactly one action-bearing UAV's scripted
             action is generated from that duty target. Raw map membership
             alone does not establish coverage.

LIFECYCLE    simultaneous LEAVE/REJOIN transitions produce ONE injective
             post-transition assignment over the final action-capable UAV set.
             A rejoining UAV already assigned during the same transition batch
             cannot receive a second duty.

R5 DOMAIN    R5 deranges eligible incumbents over the EXECUTABLY COVERED duty
             set. Non-action-bearing, charging, failed, overridden or phantom
             assignments are outside the treatment domain.

FAILURE      noninjective executable map / lossy inversion / claimed coverage
             without an action-bearing holder
               -> INVALID SOURCE-CONTROL REALIZATION
               -> no matching, no effect estimate, no synthetic zero
```

Pro notes the frozen scientific object is the **injective post-transition map**,
not one particular conditional statement. A guard in the REJOIN branch is one
permitted realization, not the contract.

## Next action, as scheduled

A **zero-compute source-assignment correction** freezing: partial-injection
semantics; executable coverage; atomic lifecycle transition behaviour; R5's
revised treatment domain; fail-closed handling of non-injective maps; the R4
invalid-realization disposition.

Only after that correction is accepted through the ordinary implementation
boundary: repair the development source controller; add direct injectivity and
phantom-coverage negatives; rerun A1–A4 and B; revise and rerun C; then resume
D–F.

**No fresh confirmatory topology panel may be selected before those development
obligations close.** The predeclared panel rule in
`docs/research/designs/D7_S_R5_OBLIGATION_G_FRESH_PANEL_RULE.md` is unaffected —
it fixes the rule, not a selection, and Pro's constraint is on selecting.

`D7.3` and `D8` remain blocked. This review authorizes neither implementation nor
compute.

## Post-fence material carried forward

Not seen by Pro; it was measured after the fence at `db7ad266` and does not
justify a follow-up turn. It goes to the next touchpoint:

- Duplication is **absorbing** on the development topology: one onset per
  episode, `dup_steps == 1500 - onset` in all eight, so no episode ever leaves
  the state once it enters.
- **The mechanism is now measured, and it localizes the repair.** Checking
  injectivity *between* the LEAVE and REJOIN phases across every simultaneous
  step in 8 episodes: `dup_after_leaves` is False in **all 249**, `dup_out` is
  True in **all 249**. The LEAVE phase produces an injective map every time; the
  REJOIN phase re-creates the duplicate every time. Duplication is not persistent
  state — it is continuously re-created, once per simultaneous LEAVE+REJOIN step.
  **The LEAVE branch needs no change.** This is direct implementation evidence for
  the correction scheduled in §9, and it agrees with the ruling's lifecycle
  clause.
- Two earlier explanations of mine were wrong and are retracted in the evidence
  note — "the LEAVE re-match never checks injectivity" (false: with empty
  `locked_duties` it re-matches injectively) and "no LEAVE fires after the onset"
  (false: 3-24 fire per episode). Both were produced by reading the code to
  explain a measurement instead of measuring the explanation. Recorded because the
  pattern, not the two facts, is the reusable part.
