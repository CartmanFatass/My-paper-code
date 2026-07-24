# Shared source manifest

All paths are read from the remote at `stage_commit` through the GitHub
connector. Nothing is uploaded; the repository is the evidence.

## Read first — the finding and the design it applies to

| Path | Why |
|---|---|
| `docs/research/cdc/EVIDENCE_NOTES/20260724_CENTERED_COUNTERFACTUAL_RESIDUAL_G20_ZERO_FIXED_POINT.md` | the derivation, the numerical confirmation, what it retires, and the proposed repair marked as orchestrator inference |
| `docs/research/designs/ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20.md` | the frozen design under discussion; the credit rule is section "Member-resolved slow credit", the entry mandate is under "Phases, parameters and optimizers" |
| `docs/research/cdc/EVIDENCE_NOTES/20260724_TIMING_CREDIT_IDENTIFIABILITY_G20_DERIVATION.md` | the derivation that made P2 eligible; unaffected by this round and not reopened |

## Scientific contracts

| Path | Why |
|---|---|
| `docs/project/ALGORITHM_PRINCIPLES.md` | project-wide scientific constraints |
| `docs/external-review/OPEN_REVIEW_PRINCIPLES.md` | how to explore within them, and your output responsibility |
| `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/21_PRO_OPEN_RAW.md` | your own bootstrap answer, including the estimator taxonomy adopted by the design and the section-9 pre-registered G20 outcome mapping |
| `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/30_PM_CODE_SIDE_RECONCILIATION.md` | how that answer was adopted code-side, and the P1–P4 portfolio |

## The built package

| Path | Role |
|---|---|
| `ha_ctse_process/centered_residual_g20.py` | the built P2 module. `compute_counterfactual_advantage` (~line 440) is the inert rule; `center_residual_over_active_set` (~line 50) is the centering half, which is exact and not in question |
| `tests/ha_ctse_process_centered_residual_g20_test.py` | the focused proofs. `test_fast_then_delayed_update_keeps_anchor_exact_and_completes_finitely` (~line 181) pins the defect with an explicit comment at ~line 238 |
| `scripts/screen_centered_counterfactual_residual_g20.py` | the bounded screen runner, built and **not executed**; carries the frozen seeds, counts and five-branch first-match system |

## The line this builds on

| Path | Why |
|---|---|
| `ha_ctse_process/anchored_residual_g19.py` | the retired G19 anchor-plus-residual package this one templates from; its shared scalar channel advantage was **not** inert at entry, which is the contrast that isolates the defect |
| `ha_ctse_process/continuous_service_roster_proxy_g17.py` | the accepted immediate-service controller the anchor preserves |
| `ha_ctse_process/delayed_battery_roster_g18.py` | the delayed battery source and its passed information gate |
| `docs/project/CURRENT_WORK.md` | live boundary, the `g20_*` keys recording this finding, and grant accounting |

## Not the subject

The centering mechanism, the Q4 scope restriction, the timing–credit
identifiability derivation, and every closed G17/G18/G19 result. Skill
cardinality and roster mechanics are unchanged background. Anything under
`docs/archive/` is not an active instruction.
