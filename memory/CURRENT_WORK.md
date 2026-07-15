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

Run a resource-bounded local access pilot using the original HMASD package in
`ref/hmasd.tar` and its `Alice_and_Bob` environment. This pilot asks whether the
source learner produces a clear positive signal before committing to the full
five-seed reproduction; it cannot retire the paper-task route by itself.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Launch `scripts/run_r41_official_hmasd_local.ps1` on local CUDA.
2. Run seed 1 with 16 rollout environments for 937 outer updates and
   1,499,200 environment steps.
3. Read the final analyzer result and select only its registered branch.

## Immediate Constraints

- R41A must freshly extract and execute `ref/hmasd.tar` without porting it into
  the current trainer. Do not add `KEEP/SET`, shaping, or any reward beyond the
  original HMASD `q_D/q_d` source-algorithm terms.
- Track the source archive in this repository and use the enclosing project Git
  commit as its version identity; do not add hashes or checksums.
- Alice--Bob is a toy environment and runs locally. The pilot uses 16 envs and
  one seed while preserving the original 937 outer updates and 14,055 optimizer
  steps per path. A PASS does not replace the full original-budget reproduction.
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
  — raw R40/R41 review and accepted disposition.
- `docs/external-review/legacy/` — legacy external-review evidence.
