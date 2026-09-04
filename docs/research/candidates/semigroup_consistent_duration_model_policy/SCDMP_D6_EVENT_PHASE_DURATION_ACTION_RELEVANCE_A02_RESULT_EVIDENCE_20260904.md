# SCDMP D6 event-phase duration-action relevance A02 — result evidence (2026-09-04)

## E0 identity

- Object: `SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02`
- Evidence class: A/RECON
- Evidence attempt: `A02_ATTEMPT_01_20260904`
- Launch SHA: `c8010f2f14a23d36476c0e1d4f129f888917275d`
- Fixed seed: `9173`
- Prospective projection: `62.04781499574892 s < 1,800 s`
- First matching branch: `A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED`
- Integrity: `true`
- Population established: `false`
- Exposure: `NO_LEARNED_PARAMETERS — exposure not applicable`

This is a valid finite population observation under the card's explicit early-stop branch. It is
not a technical failure and contains no duration-policy contrast because the declared population
did not survive to its scheduled event in every required cell.

## Resource admission and launch receipt

The runner took its mandatory admission immediately before native host construction. Receipt facts:

```text
passed=true
available_physical_bytes=13,330,087,936
effective_available_bytes=13,330,087,936
minimum_available_bytes=4,294,967,296
measurement_source=GlobalMemoryStatusEx
```

The invocation was accepted detached once at
`2026-09-04T07:45:45.0208923-07:00`, PID `6236`. The process terminated; the supervising shell
could not recover its exit code after termination. This does not affect the complete summary and
empty stderr. There was no retry or resume.

Runtime artifacts and SHA-256:

| artifact | repository-relative runtime path | SHA-256 |
| --- | --- | --- |
| summary | `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_event_phase_duration_action_relevance_a02/A02_ATTEMPT_01_20260904/summary.json` | `e29a2392f86fe0e92448e4737c67a8f88844090c6d157b58a6eeb2496726d800` |
| admission | `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_event_phase_duration_action_relevance_a02/A02_ATTEMPT_01_20260904_admission.json` | `5be780c2160f576b7234664ef4a3a54c979da37f85b0610918a56ad66db599ed` |
| stdout | `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_event_phase_duration_action_relevance_a02/A02_ATTEMPT_01_20260904.stdout.log` | `e452cfa9acaa6aa0b1512ac0d5a8175007482d56905cb4982356dedce6a271a1` |
| stderr | `temp/directions/semigroup_consistent_duration_model_policy/exp/d6_event_phase_duration_action_relevance_a02/A02_ATTEMPT_01_20260904.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Stdout contains only the admission JSON. Stderr is empty.

## Complete published inventory

| quantity | observed count |
| --- | ---: |
| source trajectories | 2 |
| source renewals | 60 |
| source transitions | 546 |
| candidate missions | 321 |
| candidate renewals | 7,051 |
| candidate transitions | 64,138 |
| evaluator calls | 321 |
| native missions | 323 |
| native transitions | 64,684 |
| models | 0 |
| training datasets | 0 |
| optimizer updates | 0 |
| AdamW steps | 0 |
| learner evaluations | 0 |

The published identities reproduce exactly:

```text
native_missions    = source_trajectories + candidate_missions = 2 + 321 = 323
native_transitions = source_transitions + candidate_transitions = 546 + 64,138 = 64,684
evaluator_calls    = candidate_missions = 321
```

## Partial terminal inventory at the frozen stop

The summary contains 21 partial terminal rows totaling exactly 321 completed missions:

| base state | countdown | clock/graph groups observed | terminal count per group |
| --- | ---: | --- | --- |
| `K7-tick-091` | 7 | `7/HR`, `7/RH`, `13/HR`, `13/RH` | each `16 timeout` |
| `K7-tick-091` | 78 | `7/HR`, `7/RH`, `13/HR`, `13/RH` | each `16 timeout` |
| `K7-tick-182` | 7 | `7/HR`, `7/RH`, `13/HR`, `13/RH` | each `16 timeout` |
| `K7-tick-182` | 78 | `7/HR`, `7/RH`, `13/HR`, `13/RH` | each `16 timeout` |
| `K7-tick-273` | 7 | `7/HR`, `7/RH`, `13/HR`, `13/RH` | each `16 timeout` |
| `K7-tick-273` | 78 | `7/HR` only | `1 safe_dock` |

Independent sums are `320 timeout`, `1 safe_dock`, and zero native failures. Every published
`failure`, `attitude_loss`, `cable_overload`, `formation_loss`, and `gantry_contact` count is zero.

The exact stop reason is:

```text
K7-tick-273 terminated before its countdown 78 event or the event could not be applied
```

The row identifies a safe dock in the first observed `K7-tick-273`, countdown `78`, clock `7`, HR
group before the event was applied. The summary does not publish a tape index for that stopped
mission, so none is inferred here.

## Frozen rule applied verbatim

The ordered card begins:

1. `A02_NO_RESULT_RESOURCE_REFUSAL` if projection/admission is absent or refused or the invocation
   never begins;
2. `A02_INVALID_EVIDENCE` for incorrect/incomplete execution, pairing, timing, counts, cap or
   publication;
3. `A02_EVENT_PHASE_POPULATION_NOT_ESTABLISHED` if either source lacks the exact common renewals, a
   base state terminates before its scheduled event, the event cannot be applied under unchanged
   native semantics, or the public countdown/order cannot be represented.

Branch 1 does not match: projection and fresh admission passed and the invocation began. Branch 2
does not match: the summary declares `integrity_valid=true`, its counts and receipts are complete
for the declared stop, and no deviation is recorded. Branch 3 matches because a required base-state
mission safe-docked before the countdown-78 event. First-match ordering stops there.

Consequently no `Y` table, `K_b,d`, `K_d`, four `N` quantities, `SHORT_ALIGNMENT`, or
`LONG_ALIGNMENT` is produced. Their absence is required by the matched branch, not missing learner
instrumentation and not a zero contrast.

## Runtime, resources and deviations

```text
wall_seconds=4.797502100002021
peak_rss_bytes=null
resources_unmeasured=true
```

The missing peak-RSS measurement leaves this non-resource result valid under the telemetry rule.
The unavailable supervisor exit code is recorded as an operational observation; the summary,
receipt, stdout, stderr and hashes are present. No scientific, numerical, RNG, checkpoint or
side-effect deviation is known. No model, optimizer, checkpoint or learned parameter existed.

## Finite E0 claim ceiling

This result establishes only that the exact A02 `.92/.25` host/source/calendar/policy construction
failed its all-cells population requirement because one declared late-state/countdown mission
terminated before its scheduled event. It does not establish a `k=7` or `k=13` value contrast,
event-phase alignment, D6/D8 competence, parameter-sharing value, regularization, negative
transfer, unseen-duration transfer, semigroup invariance, D2 interruption value, general MARL
value, safety or deployment.
