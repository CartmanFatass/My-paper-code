# Shared Source Manifest

Both blind divergent reviewers use the same Git-visible evidence boundary.
Gemini additionally reads the local paper sources allowlisted in
`02_GEMINI_LOCAL_SOURCE_MANIFEST.md`.

## Current control and result

- `docs/external-review/rounds/20260720_supplied_executor_opportunity_contract/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260720_supplied_executor_opportunity_contract/03_SUPPLIED_EXECUTOR_RESULT.json`
- `docs/project/CURRENT_WORK.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/IMPLEMENTATION_PLAN.md`
- `docs/project/ExpRecord.md`

## Current implementation

- `ha_ctse_process/variable_roster_event.py`
- `ha_ctse_process/dynamic_roster_supplied_executor.py`
- `scripts/run_clean_process_supplied_executor_high_path.py`
- `tests/ha_ctse_process_clean_supplied_executor_high_path_test.py`

## Accepted substrate and prior disposition

- `ha_ctse_process/dynamic_roster_clean_process_testbed.py`
- `ha_ctse_process/dynamic_roster_direct.py`
- `scripts/run_clean_process_direct_access.py`
- `docs/external-review/rounds/20260719_clean_process_access_portfolio/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260719_clean_process_access_portfolio/50_DISPOSITION.md`
- `docs/external-review/rounds/20260719_iteration5_postmortem_portfolio/50_DISPOSITION.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`

## Relevant literature synthesis

- `docs/research/literature/n_k_many_agent_deep_dive/SYNTHESIS.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P01_ACE.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P02_ACAC.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P03_InforMARL.md`

## Exclusions

- Current-round raws, reconciliation, convergent question and disposition are
  not evidence for either blind divergent reviewer.
- The checkpoint is not required to audit the registered result and is excluded
  from transport.
- Untracked reports, source mirrors, stopped runs and workflow history are
  outside the evidence boundary.
