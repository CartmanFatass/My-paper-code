# UCOPE learned short renewal /8702 — E0 partial evidence, 2026-09-10

**INCOMPLETE; final primary unobserved.** This is the preserved record of one
accepted B/EXPLORE invocation, not a second complete training comparison.
The frozen [card](UCOPE_UAV_SHORT_LEARNED_RENEWAL_CONTINUOUS_B01_8702_SCIENCE_CARD_20260910.md)
and launch source are **b6c75d5cf8e1781bb0e3c6824ab2dc9cb32dbce9**. No scientific
retry, resume, replacement, extra model or evaluation was invoked for this intake.

## Rule applied verbatim and result boundary

Card §5: “Final T/G completeness governs
the primary; complete allocation requires all three full fits, nine panels and H.”
It also says: “An exception stops later fits and preserves partial facts.”

T stopped before its 2048-episode endpoint. F/G training/evaluation and H were
never reached. All six contrasts at all three panels have empty matched
vectors and null means/conditional SEs. Final T/G completeness is false and
the published reading is null; **no UP, WITHIN or DOWN branch applies**.
No historical control is imputed. This attempt supplies no recurrence result,
stable superiority/harm, headroom, causal duration benefit or family closure.
B objects have no C consumption state; the one-invocation allocation is used.

## Direct failure and the narrower source inference

The preserved limit is exactly:

```text
execution: ValueError: input operand has more dimensions than allowed by the axis remapping
```

There are 477861 attempted environment/adapter `step` calls but 477860 returned
team steps. The collector increments the attempt counter immediately before
`env.step(sent)` and the returned-step counter immediately after it. Combined
with the ordered rows and completed rollout prefix, this narrows the failure
to T's next training episode, index 1738, reset seed 870211738, after 164
returned ticks: the 165th step attempt. Episode/step identification is an
inference from those counters and source, not a retained frame or traceback.

The exact operation, input shape and failing native state/action were
not retained. The exception may occur before or after backend state mutation
inside that call; its return was not available. Static inspection of the
bound collector, adapter and vectorized environment does not uniquely locate
the cause. No environment/learner repair is claimed from error text alone.
The log contains no nonfinite-learning or timeout exception; the recorded
3476 optimizer epochs and reported parameter displacements are finite. This
does not substitute for a missing traceback or reconstruct unsaved tensors.

## Actual exposure and retained measurements

| Quantity | Observed |
| --- | ---: |
| Independent training instances attempted / complete comparisons | 1 / 0 |
| Fits started / completed | 1 / 0 |
| Completed training / evaluation episodes | 1738 / 128 |
| Serialized episode / rollout rows | 1866 / 869 |
| Adam calls / finite serialized epochs | 3476 / 3476 |
| Returned training / evaluation team steps | 445092 / 32768 |
| Completed-episode steps / partial returned steps | 477696 / 164 |
| Environment step attempts / returned team steps | 477861 / 477860 |
| Explicit resets / constructor resets | 1867 / 1 |
| F/G fitted or evaluated episodes; H episodes | 0; 0 |
| Saved final fitted checkpoints | 0 |

The partial episode has no serialized return and no optimizer update. Its
564 velocity/duration draws and 263 duration-2 choices include sampling before
the failed call; 260 suppressed decisions count returned held steps. Duration
4 was never selected. T's total head-forward exposure is 9159898 rows from
`2*(all training+evaluation duration decisions) + 4*(duration decisions in
completed rollout rows)`: collected partial rows are not replayed. T/F/G
copies are constructed before the fit loop by source; only T reached its
optimizer/environment and produced fit evidence.

Two T-only panels survive, each on the declared 64 evaluation worlds:

| T training checkpoint | Mean native J | Conditional mean SE |
| --- | ---: | ---: |
| 512 | 0.10497156306673558 | 0.009270105439687574 |
| 1024 | 0.1498504958382924 | 0.007480603341524169 |

These are unpaired T measurements with no G/F/H outcome available. They do
not answer the final comparison. Their SE describes evaluation variation
conditional on this partial training history, not training-population
uncertainty. Every episode ID/vector remains in the result summary. Recorded
whole-duration-head displacement is 1.0471975803375244 at512,
1.035123586654663 at1024 and1.3008228540420532 at the exception. Both completed
evaluation panels report zero parameter displacement and zero optimizer calls.
Binary final weights are absent, so those exposure reductions are not backed
by a final tensor readback. Earlier 8701 DOWN and all previous hover losses
and fixed-law gains remain separate evidence.

## Receipts, timing and verification

The Monitor's exact receipt was copied from
`C:/Users/fires/Documents/Codex/2026-09-09/hmasd-folr-b02-monitor-20260909/outputs/ucope-uav-short-learned-renewal-continuous-b01-8702-20260910-terminal.txt`.
It observed failed/exit1, PID3096219 and inactive tmux at
2026-09-10T19:34:12.8256214Z. Remote start/exit were
2026-09-11T03:22:48+08:00 /2026-09-11T03:32:51+08:00: 603 supervisor seconds.

GNU time recorded **603.07s whole command**, **559032KiB peak RSS**. Nested
T/publication elapsed was593.9362493799999s, leaving9.133750620000114s
unlocalized outer residual. No cause is assigned to that residual. Charging
the entire300s support reserve gives a conservative903.07s total, below the
5400s study cap and1800s sole-fit cap; no cap breach is recorded. Support and
nested times are not added twice. Aggregate CPU and cgroup-specific telemetry
remain `resources_unmeasured`. Actual adjacent canonical admission passed at
19:22:48.906934Z with physical/effective15243468800 bytes against4294967296.

Collection verified **all10 native/supervisor files and12 declared source/test
paths** against remote hashes and exact Git source; tracked remote status was
clean. Offline analysis checked every1866 episode and869 rollout row, reward
sum divided by256, all3476 finite epoch records, chronological resets/panels,
counter residuals, both full T vectors and all18 absent contrasts. These checks
created no new environment, model, RNG, learner or evaluator. `summarize_runs.py`
was not used because no final per-training-instance endpoint exists; episode
rows or checkpoints cannot stand in for independent completed training units.

Raw evidence and source/readback receipts:
`temp/directions/ucope/exp/ucope-uav-short-learned-renewal-continuous-b01-8702-20260910/collection/`.
Collection was2.793069099992863s internally /3.1248226s outer tool; offline
analysis was0.06423809999250807s through publication /0.2903575s outer tool.
Source checks and failed/successful engineering-test attempts remain in the
prospective intake. The test total is unchanged; no native/synthetic rerun
was used to classify this failure. No Scope Spec §5 breach is established.

## Predictions and decision

Prospective probabilities .20/.20/.55 for final T−G>0.01, T−F>0 and T−H>0
are all **unscorable**, with event and Brier fields null. Missing outcomes are
not false forecasts. Owner prediction was not taken; main/direction reviews
contain no unapplied reply. The [intake](UCOPE_UAV_SHORT_LEARNED_RENEWAL_CONTINUOUS_B01_8702_INTAKE_20260910.md#5-terminal-partial-result-intake)
selects preservation and a minimal future exception-reporting repair, with no
new scientific allocation. The exact failing operation remains unresolved.
The [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-10_learned-renewal-continuous-8702-incomplete.md)
and [full partial summary](UCOPE_UAV_SHORT_LEARNED_RENEWAL_CONTINUOUS_B01_8702_RESULT_SUMMARY_20260910.json)
retain the bounded reading.

Verified recovery: the [preservation record](UCOPE_UAV_SHORT_LEARNED_RENEWAL_CONTINUOUS_B01_8702_PRESERVATION_20260910.json)
retains the38-entry local archive, its SHA256 and the exact remote source
reference. Original local partial evidence remains alongside the archive.
