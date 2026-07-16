# Shared Git-Visible Source Manifest

access_mode: read_only_git

Both divergent reviewers must inspect these sources. The open GPT-5.6 Pro
reviewer must not read any current-round Gemini raw response, Codex synthesis,
convergent prompt/response or final disposition.

## Binding design and project state

- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/00_REVIEW_BRIEF.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_architecture/50_DISPOSITION.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/IMPLEMENTATION_PLAN.md`

## Production code anchors

- `ha_ctse_process/r30_fixed_clock.py`
  - `FixedClockAREditPolicy`
  - `HighCheckValue`
  - `HighCheckRow`
  - `HighCheckBuffer`
- `ha_ctse_process/standalone_agent.py`
  - `RecurrentLowLevelPolicy`
  - `StrictHMASDMAPPOLowLevelPolicy`
  - `StandaloneProcessAgent.__init__`
  - `_r30_maybe_assign_skills`
  - `record_environment_step`
  - `truncate_high_rows_for_update`
  - `start_high_continuations_after_update`
  - `act_low_batch`
  - `low_bootstrap_values`
  - `update_high_from_checks`
  - recurrent low replay/update helpers
- `ha_ctse_process/train.py`
  - `checkpoint_payload`
  - `load_checkpoint`
  - `load_checkpoint_metadata`
  - `apply_checkpoint_structure`
  - `train_loop`
- `scripts/r49_orse.py`
- `scripts/run_r49_orse_gate.py`

Inspect enough surrounding code to verify shapes, RNG ownership, state
continuity, actor/critic inputs, replay and checkpoint boundaries. Do not treat
function names or the brief as evidence when the implementation contradicts
them.

## Narrow literature grounding

- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P01_ACE.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P02_ACAC.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P03_InforMARL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P04_Sable.md`
- `docs/research/literature/n_k_many_agent_deep_dive/SYNTHESIS.md`

Use these only to challenge event ownership, duration credit, active-set
representation and recurrent scalability. They do not override repository
evidence or authorize module accumulation.
