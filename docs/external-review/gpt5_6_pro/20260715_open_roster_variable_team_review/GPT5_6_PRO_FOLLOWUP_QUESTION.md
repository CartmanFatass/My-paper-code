# GPT-5.6 Pro Follow-up: Open-Roster Sequencing Audit

Date: 2026-07-15

## Purpose

Audit the controller's disposition of the two variable-team responses. The
question is not whether open-roster control is interesting in general. The
question is whether it should replace the current fixed-`N` native-HMASD toy
credit anchor now, and what the single smallest causal step should be.

## Repository files to inspect

Read all of the following before deciding:

1. `memory/CURRENT_WORK.md`
2. `memory/ALGORITHM_PRINCIPLES.md`
3. `memory/ExpRecord.md`, especially the current R39 toy rows and result blocks
4. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/GPT5_6_PRO_RESPONSE_RAW_1.md`
5. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/GPT5_6_PRO_RESPONSE_RAW_2.md`
6. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/DISPOSITION.md`
7. `ha_ctse_process/r30_fixed_clock.py`
8. `ha_ctse_process/standalone_agent.py`
9. `ha_ctse_process/config_r39_toy_fixed_primitives_direct_state_high3_block_shared_refresh.py`
10. `scripts/diagnose_r39_joint_roster_factorization.py`

Relevant current evidence:

- The high-32 toy policy passed exact roster-factorization supervision with
  minimum correct-roster mass `0.999487`.
- In sampled training, correct rosters received raw block return `4.900994`
  versus `1.816988` for incorrect rosters, and standardized actor weights
  `+2.120720` versus `-0.192793`.
- Therefore model capacity and reward timing/storage are closed; the remaining
  failure is the standalone shared joint-credit learner.
- The current controller selects a minimal fixed-`N` native-HMASD toy anchor
  using the original coordinator likelihood and native team/agent advantages
  before changing the roster representation.

## Controller disposition to audit

The controller accepted open-roster control as a future architecture axis but
rejected the two responses' immediate `R39-OR0` / S7-first recommendation. Its
accepted sequence is:

```text
fixed-N native-HMASD toy credit anchor
-> exogenous active-mask/set-roster on the same toy
-> cross-episode variable N
-> within-episode membership censoring
-> dynamic-roster full-refresh/shared-lifetime/per-agent KEEP-SET comparison
-> S7 transfer
```

It also deferred learned membership selection, low-critic replacement, fixed
ISAB capacity, specific numerical gates, and any novelty claim. It prohibits
team-size/join/survival or benchmark-specific intrinsic rewards.

## Requested decision

Return one explicit verdict: `ACCEPT DISPOSITION`, `MODIFY DISPOSITION`, or
`REJECT DISPOSITION`.

Then answer all of the following:

1. Is the fixed-`N` native-HMASD toy anchor a necessary causal predecessor to a
   set-equivariant/open-roster implementation? If not, identify the exact
   repository fact or estimator argument that makes it unnecessary.
2. Select exactly one immediate next causal edge. Do not propose parallel
   native-toy, Set-R30, and S7 tracks.
3. Give the smallest implementation boundary and smallest evidence-bearing toy
   run for that edge. Do not create a standalone audit/test workstream.
4. State the required probability, time, information, credit, recurrent-state,
   and checkpoint contracts. Explicitly distinguish exogenous membership from
   policy-selected membership.
5. Identify which parts of the two raw responses should be accepted, modified,
   deferred, or rejected. Treat quoted choices such as `M=8`, parameter-ratio
   tolerances, reward ratios, and team-size sets as unregistered proposals, not
   established facts.
6. State the single abandonment branch and the only next action following each
   possible result.

Do not use UAV-specific intrinsic reward, team-size reward, join/survival
reward, task predicates, reward shaping, a new sampled team latent, `q_D`, or a
learned agent order. Do not use an immediate S7 run merely because S7 provides
failure machinery. Do not revive retired R29--R38 mechanisms or rescue them by
retuning, more seeds, larger models, or changed thresholds.
