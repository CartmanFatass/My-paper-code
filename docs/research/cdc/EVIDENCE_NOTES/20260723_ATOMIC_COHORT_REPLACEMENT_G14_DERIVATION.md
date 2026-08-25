# Atomic cohort-replacement G14 derivation

Date: 2026-07-23

## Counterexample

Formal G13 passes episode-random count processes, but every terminal departure
and fresh join occurs in a different membership transaction. That leaves time
for the policy/environment to observe an intermediate smaller roster. A real
runtime roster can replace a cohort atomically: old lifecycle state disappears
and equally many zero-state agents appear while total count does not change.

This is more discriminating than another larger-N profile because log-count and
active-count features are deliberately held constant. Only identity turnover,
lifecycle reset and the atomic membership edit change.

## Source construction

Every episode samples a constant active count, random initial physical keys and
six replacement cohorts. At times 9, 24, 32, 40, 49 and 64, one transaction
terminally removes a random active cohort and joins an equally sized random
never-seen cohort. Moderate, wide and ultra sources use N ranges 12--20, 32--48
and 64--80 with replacement batches 2--6, 6--14 and 10--18.

Capacities 64, 144 and 192 guarantee fresh lifecycle keys without reuse. Exact
event signatures prove that both operations occur in every transaction and
that cohort sizes match. Constructive utility, constant roster schedules, wave
demand and terminal/cold-start hidden-state semantics remain required.

## Evidence boundary

Import the exact three G8 finals with no training. Evaluate 32 independently
generated processes per domain under deterministic and stochastic actions.
Retain the same absolute 0.90 access, 0.85 minimum-replicate and 0.80 stochastic
floors. A valid failure is a real atomic-turnover limit and cannot be rescued by
changing cohort sizes or thresholds after the result.

```text
selected_action=ATOMIC_COHORT_REPLACEMENT_G14
training_operation=none_frozen_g8_checkpoint_import
conclusion_bearing_iteration=15
iterations_remaining_before_run=3
```
