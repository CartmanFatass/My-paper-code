# GPT-5.6 Pro Review Entry: R29-T10 Preliminary Result

This file is the single entry point for the R29-T10 external review. The user
will provide an exact Git commit SHA in ChatGPT. Read every path below at that
same commit; do not mix files from a later branch head.

No ZIP upload is required. If a listed file cannot be read through the GitHub
connector, identify that file explicitly rather than inferring its contents.

## Review question

Read first:

- `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/GPT5_6_PRO_QUESTION.md`

## Prior review and research background

These files define HMASD's role, OPT's separate representational role, the
HA-CTSE innovation starting point, the negative constraints accumulated before
R29, and the rationale that produced R29-T10:

- `docs/external-review/gpt5_6_pro/20260713_r29_action_information/RESEARCH_BACKGROUND.md`
- `docs/external-review/gpt5_6_pro/20260713_r29_action_information/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260713_r29_action_information/DISPOSITION.md`
- `memory/ALGORITHM_KNOWLEDGE_BASE.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `docs/research/designs/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md`

## Current contract and result

- `memory/CURRENT_WORK.md`
- `memory/ExpRecord.md`
- `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/r29_t10_pair.json`
- `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/r29_t10_pair.md`

## Implementation

- `ha_ctse_process/r29_action_information.py`
- `ha_ctse_process/r29_action_information_reward.py`
- `scripts/analyze_r29_t10_pair.py`

## Raw evidence used by the paired decision

Probe-only arm:

- `logs/r29_t10_paired_320k_20260714_010026/runs/probe_only/seed29031/metadata/run_manifest.json`
- `logs/r29_t10_paired_320k_20260714_010026/runs/probe_only/seed29031/metrics/train_updates.csv`
- `logs/r29_t10_paired_320k_20260714_010026/runs/probe_only/seed29031/metrics/eval_episodes.csv`
- `logs/r29_t10_paired_320k_20260714_010026/evidence/probe_only/analysis/r26_g1_behavior.json`
- `logs/r29_t10_paired_320k_20260714_010026/evidence/probe_only/analysis/r26_g1_behavior.md`

Real-reward arm:

- `logs/r29_t10_paired_320k_20260714_010026/runs/real_reward/seed29031/metadata/run_manifest.json`
- `logs/r29_t10_paired_320k_20260714_010026/runs/real_reward/seed29031/metrics/train_updates.csv`
- `logs/r29_t10_paired_320k_20260714_010026/runs/real_reward/seed29031/metrics/eval_episodes.csv`
- `logs/r29_t10_paired_320k_20260714_010026/evidence/real_reward/analysis/r26_g1_behavior.json`
- `logs/r29_t10_paired_320k_20260714_010026/evidence/real_reward/analysis/r26_g1_behavior.md`

## Required response

Return one self-contained response that:

1. chooses exactly one route: `PROMOTE`, `MODIFY ONCE`, or `RETIRE`;
2. separates direct evidence from inference;
3. if modifying, names one causal defect, one minimal algorithm change, and one
   falsifiable comparator;
4. explains whether the mean-versus-variance KL split changes the mechanism
   diagnosis;
5. states which scientific conclusions remain prohibited; and
6. specifies only the next evidence-bearing causal test, without coefficient
   sweeps, threshold relaxation, semantic-classifier rewards, or task-specific
   intrinsic rewards.

The user will return the full raw response for archival and disposition.
