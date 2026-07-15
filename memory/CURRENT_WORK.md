# HA-CTSE Current Work

Updated: 2026-07-16

## Controller

- **Active controller:** Codex on branch `aggressive`, working directly in
  `C:\project\HMASD`.
- **Versioning:** Git only; push with `git push My-paper-code aggressive`.
- **Project boundary:** IMOD is operational reference only, not HMASD evidence.
- **Shared GPU scheduler:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9`.
- **External review:** manual GPT-5.6 Pro handoff under `AGENTS.md`.

## Objective

Obtain an evidence-backed fixed-`N` positive anchor by reproducing the HMASD
paper's Alice--Bob environment with unchanged standard fixed-`k` HMASD. Only a
positive reproduction may authorize testing R30 per-agent `KEEP/SET` on the same
task and checkpoint.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Submit the tracked R41 reproduction question for manual GPT-5.6 Pro review:
   `docs/external-review/gpt5_6_pro/20260715_r40_simple_spread_access_result/GPT5_6_PRO_QUESTION.md`.
2. Archive the raw response and record its disposition.
3. Implement only the accepted registered branch.

## Immediate Constraints

- R41 must reproduce the paper environment and standard fixed-`k` HMASD; do not
  substitute another toy substrate, add `KEEP/SET`, alter the learner, or add
  shaping or intrinsic reward.
- Intrinsic reward must remain environment-agnostic and may not consume task
  identities, goals, contacts, phases, success predicates, distances, or
  external reward.
- Do not begin open-roster or variable-`N` implementation before the fixed-`N`
  positive anchor.
- Completed branch decisions in `memory/ExpRecord.md` and the cited research
  decision files are binding. Reopen one only through a new registered causal
  edge, not by retuning budgets, seeds, thresholds, rewards, or model size.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — research contract.
- `memory/IMPLEMENTATION_PLAN.md` — active staged core work.
- `memory/ExpRecord.md` — formal contracts and decisions.
- `docs/research/decisions/R39_NATIVE_TOY_CREDIT_FAILURE_REVIEW_20260715.md` —
  R39 boundary.
- `docs/research/decisions/R35_R40_SUBSTRATE_FAILURE_REVIEW_20260715.md` —
  R40/R41 boundary.
- `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/`
  — variable-team disposition.
- `docs/external-review/gpt5_6_pro/20260715_r40_simple_spread_access_result/`
  — current external-review entry.
- `docs/external-review/legacy/` — legacy external-review evidence.
