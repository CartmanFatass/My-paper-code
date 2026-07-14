# HMASD R30 Algorithm And Code Review Package

Target code/design commit:
`f62baf626f6f37903b3929c4732952f95d2bc2ab`

Purpose: one pre-implementation external review of R30 fixed-clock
autoregressive `KEEP/SET(skill)` editing against the current pre-R30 code.

## Review Files

- `REVIEW_ENTRY.md`
- `QUESTION.md`
- `RESEARCH_BACKGROUND.md`
- `CODE_MAP.md`
- `PACKAGE_MANIFEST.md`

## Algorithm And Memory Files

- `docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/LTM/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md`
- `docs/external-review/gpt5_6_pro/20260714_fixed_clock_keep_set/DISPOSITION.md`

## Primary Code

- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/config.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/g_info_objective.py`
- `ha_ctse_process/process_posterior.py`
- `ha_ctse_process/skill_effect_discovery.py`

## HMASD / OPT Reference Code

- `hmasd/networks.py`
- `hmasd/ha_ctse.py`
- `hmasd/agent.py`
- `hmasd/baselines.py`

The ZIP contains source text only: no checkpoints, logs, datasets, generated
results, environment assets, or secrets. Git is the version source; no package
hashes or checksums are used.
