# Shared Source Manifest

The registered Open-Pro Exchange uses this exact Git-visible evidence boundary.

## Current focused round

- `docs/external-review/rounds/20260722_ehc_behavioral_battery_identifiability/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260722_ehc_behavioral_battery_identifiability/01_SHARED_SOURCE_MANIFEST.md`
- `docs/external-review/rounds/20260722_ehc_behavioral_battery_identifiability/20_PRO_OPEN_QUESTION.md`

## Scientific and control constraints

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/project/IMPLEMENTATION_PLAN.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md`

## Prior battery question and Pro correction

- `docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/QUESTION.md`
- `docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/RESPONSE_RAW.md`

## Implemented measurement path

- `ha_ctse_process/event_held_commitment_link.py`
- `ha_ctse_process/noncalendar_commitment_testbed.py`
- `scripts/run_noncalendar_commitment_benchmark_g0.py`
- `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`

## Upstream selected-source contract

- `docs/external-review/rounds/20260720_event_held_commitment_contract_finalization/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/50_NON_ADOPTION.md`

## Exclusions

- No aborted run, partial checkpoint or runtime log is scientific evidence.
- No current-round raw, reconciliation or disposition exists before dispatch.
- Untracked reports, broad source mirrors and unrelated historical reviews are
  outside this boundary.
- Surrounding code may be inspected only when needed to verify probability,
  replay, RNG, mask, recurrent-state, lifecycle or counterfactual semantics.
