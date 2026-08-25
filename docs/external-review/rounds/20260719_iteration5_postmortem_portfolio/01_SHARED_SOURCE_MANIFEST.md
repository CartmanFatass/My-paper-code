# Shared Source Manifest

Both blind divergent reviewers use the same scientific evidence boundary. The
open Pro reads the Git-visible files at the pinned commit. Gemini reads these
files locally plus the explicitly allowlisted paper PDFs in
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md`.

## Current control and evidence

- `docs/project/CURRENT_WORK.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/IMPLEMENTATION_PLAN.md`
- `docs/project/ExpRecord.md`
- `docs/external-review/rounds/20260719_iteration5_postmortem_portfolio/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260719_iteration5_postmortem_portfolio/03_ITERATION5_RESULT.json`

## Iteration 5 implementation surface

- `ha_ctse_process/dynamic_roster_spatial_testbed.py`
- `ha_ctse_process/process_semantics.py`
- `scripts/run_iteration5_process_semantics.py`

## Retained architecture and prior dispositions

- `docs/research/designs/F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`
- `docs/external-review/rounds/20260718_stage_c_skill_bottleneck_portfolio/50_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260718_iteration4_semantic_null_convergence/50_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/FINAL_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`

## Literature synthesis

- `docs/research/literature/n_k_many_agent_deep_dive/SYNTHESIS.md`
- `docs/research/literature/n_k_many_agent_deep_dive/CODE_INDEX.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P01_ACE.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P02_ACAC.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P03_InforMARL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P04_Sable.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P05_ExpoComm.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P06_SafeM3UCRL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P07_CTMARL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P08_IARO.md`

## Exclusions

- No current-round raw response, reconciliation, convergent question or
  disposition is evidence for either blind divergent reviewer.
- Untracked reports, broad source-code mirrors, stopped runs and historical
  workflow prose are outside the evidence boundary.
- Literature mechanisms are sources of design principles, not modules that
  must be accumulated.
