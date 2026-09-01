# RISP event-conditioned Bayes implementation threshold

Status: `EXACT_RESULT_COMPLETE`

This exact zero-learning certificate completed on 2026-08-30 and is recorded in
`RISP_ECR_R01_RESULT_INTAKE.md`; it must not be rerun. The prospective support law does not modify
the historical fixed-five-schedule host or inherit its result polarity.

## Successor boundary — 2026-08-31

No witness-independent prevalence successor is frozen for implementation. The mathematically
complete `PC3-IID-REFERENCE` candidate was not adopted because its behavior occupancy, stopping,
duration, opportunity, next-`k`, regret, and materiality choices are convenience conventions rather
than an independently target-grounded law. Do not create or enumerate a prevalence package from
that candidate. Reconsider only with a complete intended-target generative/utility law or a robust
lower bound over an independently justified law class, as recorded in
`RISP_PROSPECTIVE_POPULATION_LAW_DECISION_AUDIT_20260831.md`.

## Controllers and information

- `RAW_HISTORY_BAYES`: all deployable public history, never hidden state; independent ceiling.
- `FULL_BAYES_K`: full ordered action, ACK, completed-duration, event, and clock history.
- `FULL_BAYES_K_ERASED`: ordered actions/ACKs and current decision information but no earlier
  duration allocation, timestamps, schedule label, or reconstructing clock; marginalizes the frozen
  twin population exactly.
- `LAST_ACK_BAYES`: current decision information and only final action/ACK/completed duration; older
  history is exactly marginalized.
- `LAST_ACK_G`: existing fixed last-action/ACK map with its exact rational masses; prior, duration,
  and time inputs remain zero.

Printed order `LEFT < CENTER < RIGHT` breaks ties. Controllers replay public histories; stored
beliefs are certificates and never injected inputs.

## Host, clocks, and endpoint

Retain the tri-sector law

\[
P_k=\tfrac13J+(15/16)^k(I-\tfrac13J),
\]

with ACK success `4/5` on completion-sector match and `1/5` otherwise, and uniform initial belief.
Keep renewal index, primitive start/end, completed duration, next action-visible duration,
ACK/update event, and next-hold credit distinct. Ordering is hold completion, motion, ACK, private
update, then next action. Hidden sector, future duration/reward, cross-agent data, and experimenter
posterior are forbidden.

For current belief `b` and next duration `k`, native value is

\[
Q(a\mid b,k)=k[-3/5+(6/5)(bP_k)(a)].
\]

RAW directly sums hidden paths and must match FULL-BAYES-K rowwise in posterior, action, and value.
Realized hold utility lies in `[-k,+k]`; physical-time-normalized return lies in `[-1,+1]`.
Scientific RNG, seeds, optimizers, updates, checkpoints, and sampling are zero. Reachability uses
exact positive path mass under a full-support uniform reference-action law; twin sides receive equal
weight.

## Frozen reachable twins

Prior-history twins start from the uniform belief, receive equal population weight, end at primitive
time 12 with final `(LEFT,+,4)`, and expose next `k=4`:

```text
[(CENTER,+,4), (CENTER,+,4), (LEFT,+,4)] -> RAW next CENTER
[(CENTER,+,4), (CENTER,-,4), (LEFT,+,4)] -> RAW next LEFT
```

All three completed segments have duration 4. Their last packet and current decision information
are identical; only the earlier ACK differs. The registered census must use exactly these two
histories under the full-support uniform reference-action law, with no search or substitute prefix.

The fresh prospective duration-order support law admits two prefixes ending at time 28 with action/
ACK sequence `CENTER+, CENTER+, CENTER+, LEFT+`, final `(LEFT,+,8)`, next `k=4`, and durations:

```text
[4,4,12,8] -> RAW next LEFT
[4,12,4,8] -> RAW next CENTER
```

These prefixes are not part of the historical five-schedule ABI. They are explicitly registered in
`RISP-ECR-R01-SPEC-V1`. Prediction and ACK conditioning do not commute, so fixed symmetric
persistence can still create an order-dependent action flip.

## Acceptance and stop

Emit `CERTIFIED_RENEWAL_INDEXED_BAYES_WITNESS` only if every history has positive exact mass; twin
common keys match while pre-last priors differ; clocks/ACK law/utility reconcile; RAW and FULL agree
rowwise; all unique actions reproduce; K-ERASED has positive equal-weight regret on duration twins;
LAST-ACK-BAYES and G have positive regret where identical views span opposite RAW actions; and no
historical coordinate/result or APFI artifact enters a controller.

Any tie, unreachable row, RAW/FULL mismatch, leakage, arithmetic/native mismatch, incomplete census,
or partial artifact is `INVALID_CERTIFICATE`. Do not search replacement histories, alter weights or
ties, add a learned arm, or rerun the same identity.

The maximum claim is exact fixed-host evidence that older outcome history and completed-duration
order change next native action/value beyond last-ACK and duration-erased views. It gives no natural
prevalence, learned advantage, arbitrary-K, coordination, variable population, UAV, safety, or
deployment claim. APFI remains provenance only.

## Isolated implementation surface

```text
experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/
  contract.py
  exact_probability.py
  controllers.py
  reachable_twins.py
  reference_host.py
  native_backend.py
  native_backend.cpp
  analysis.py
  artifact.py
  cli.py
  schemas/

tests/experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/
  test_contract_and_views.py
  test_exact_bayes_and_raw_ceiling.py
  test_reachable_twins.py
  test_clocks_and_endpoint.py
  test_native_equivalence.py
  test_artifact_and_cli.py
  test_dependency_firewall.py
```

APIs load/validate the contract, replay public history, decide under each controller, enumerate
twins, compute RAW Bayes, analyze a complete census, and publish atomically. Schemas cover spec,
public history, twin census, and complete result; rationals use reduced numerator/denominator pairs.
Use a fresh native registry key and never modify historical B1/B2/B3/G-init schemas or resume paths.

## CLI and non-result checks

```text
python -m experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01 describe
python -m experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01 check --spec PATH --output PATH
python -m experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01 certify --spec PATH --output-root PATH
```

Only `describe` and `check` are pre-result eligible and may not evaluate registered controller
actions/returns. Expose no seed, witness, subset, duration, weight, tie, endpoint, threshold, retry,
resume, or legacy-result overrides. Planning ceiling is one CPU/thread, no GPU/network, 600 seconds,
1 GiB RSS, and 256 MiB durable output.

Focused tests cover exact normalization/Bayes recursion, RAW/FULL equivalence on TEST-only fixtures,
duration-erasure nonreconstruction, last-ACK marginalization, exact G fractions, positive
reachability, pairing, clock order, physical-time accounting, native/reference equality, malformed
input atomicity, complete-only analysis, canonical bytes, and dependency firewalls.

## Evidence

- `DIRECTION.md`
- `RISP_G_INITIALIZATION_REACHABILITY_SCIENCE_CARD_R01.md`
- `RISP_B3_R03_RESULT_INTAKE.md`
- `experiments/candidates/renewal_indexed_score_plasticity/`
