# GPT-5.6 Pro Focused Continuation — EHC Behavioral-Battery Identifiability

You are the registered independent Open GPT-5.6 Pro scientific reviewer. This is
a focused continuation in the same conversation, not a new portfolio round.
Read every file listed below. In particular, bind
`docs/project/ALGORITHM_PRINCIPLES.md` and
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md`.

## Repository files to inspect

- `docs/external-review/rounds/20260722_ehc_behavioral_battery_identifiability/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260722_ehc_behavioral_battery_identifiability/01_SHARED_SOURCE_MANIFEST.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/project/IMPLEMENTATION_PLAN.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md`
- `docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/QUESTION.md`
- `docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/RESPONSE_RAW.md`
- `ha_ctse_process/event_held_commitment_link.py`
- `ha_ctse_process/noncalendar_commitment_testbed.py`
- `scripts/run_noncalendar_commitment_benchmark_g0.py`
- `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`
- `docs/external-review/rounds/20260720_event_held_commitment_contract_finalization/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/50_NON_ADOPTION.md`

No valid formal result exists. Do not use aborted runs as scientific evidence.

## Scientific object under review

Keep the primary mechanism-matched estimand
`G = U_EHC - U_DUM` fixed. Audit only whether the implemented replacement
battery distinguishes learned context-sensitive event-held commitment from a
representation-only link with arbitrary, random or otherwise non-consequential
renewal timing.

The implemented battery consists of:

1. minimum eligible natural KEEP and RENEW counts as support only;
2. complete uncensored opportunity-count bins `K==1`, `K==2`, `K>=3`;
3. lifecycle-stratified same-state primitive-action total variation under a
   deranged commitment mark;
4. exact-snapshot common-random-number KEEP-versus-RENEW continuations at
   naturally selected KEEP rows and naturally selected RENEW rows, scored by
   unchanged external utility and clustered by the original paired episode;
5. `COMMITMENT_SUPPORTED` only when `G`, support, K spread, action TV and both
   directional natural counterfactual advantages pass.

The tracked design prose still contains superseded `CV(T)`, physical-time-bin
and logit-norm gates. Treat this as a factual repository mismatch, not as a
second scientific proposal.

## Required response

Use these exact sections:

1. **Decision and scope** — choose exactly one:
   `BATTERY_IDENTIFIABLE_AS_IMPLEMENTED`,
   `BATTERY_REQUIRES_MINIMAL_CORRECTION`, or
   `BATTERY_CANNOT_IDENTIFY_COMMITMENT_UNDER_THIS_SOURCE`.
2. **Plural live conjectures** — retain two to four structurally different
   explanations for what a positive battery could mean and state each scope.
3. **Derivation and intervention consequences** — derive what K support,
   action TV, each directional natural counterfactual advantage and their joint
   pass do and do not identify. Include natural and held-out consequences.
4. **Concrete counterexamples** — attack the battery with at least: a random
   nondegenerate event head, a context-insensitive hazard, a useful mark with
   arbitrary timing, and selection/support or counterfactual-conditioning bias.
5. **Retained lemmas and smallest refuted unit** — state the strongest claims
   that survive and the smallest measurement unit, if any, that fails.
6. **Minimal correction or freeze** — if correction is required, specify only
   the smallest scientific measurement change and its estimand; otherwise state
   the exact evidence semantics that must be frozen. Do not write an
   implementation plan.
7. **One scheduled research action** — choose one next evidence action by
   information gain, cost and reversibility; state comparator, estimand,
   mutually exclusive outcomes, prohibited rescues and why this action does not
   invalidate other legal explanations.
8. **Reactivation conditions** — state what later evidence would reactivate
   every serious unscheduled explanation.
9. **Concise Chinese user brief** — summarize the decision, decisive reason,
   next action and what remains uncertain.

Do not authorize implementation or compute. Do not change reward, `G`, arms,
budget, seeds, thresholds outside the smallest refuted measurement unit, or the
ordinary/capacity comparator. One scheduled action is not one legal successor.
