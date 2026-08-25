# Shared Git-Visible Source Manifest

access_mode: read_only_git

Both blind divergent reviewers must inspect these sources. The open GPT-5.6
Pro reviewer must not read any current-round Gemini raw response, Codex
synthesis, convergent prompt/response or final disposition.

## Current design question

- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/00_REVIEW_BRIEF.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`

## Binding F0/F1 architecture and implemented boundary

- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_architecture/50_DISPOSITION.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/50_DISPOSITION.md`
- `ha_ctse_process/variable_roster_event.py`
- `tests/ha_ctse_process_variable_roster_event_test.py`
- `ha_ctse_process/collectors.py`
- `ha_ctse_process/train.py`

Inspect enough implementation context to verify what a real environment and
training integration would have to supply. Do not mistake the fail-closed
deterministic boundary for a complete trainer.

## Prior access failures and positive anchors

- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/FINAL_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`
- `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/R51_AMDT_RESULT.json`
- `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/R52_ARFA_RESULT.json`
- `docs/external-review/gpt5_6_pro/20260717_r53_rcma_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260717_r53_rcma_result/R53_RCMA_RESULT.json`
- `docs/external-review/gpt5_6_pro/20260717_r54_hfsr_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260717_r54_hfsr_result/R54_HFSR_RESULT.json`

Use these results to prevent another no-access or threshold-only gate. Their
exact retired task/model/gain contracts may not be renamed or rescued.
