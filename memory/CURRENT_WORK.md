# HA-CTSE Current Work

Updated: 2026-07-16

## Controller

- **Active controller:** Codex on branch `aggressive`, working directly in
  `C:\project\HMASD`.
- **Versioning:** Git only; push with `git push My-paper-code aggressive`.
- **Project boundary:** IMOD is operational reference only, not HMASD evidence.
- **Shared GPU scheduler:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9`.
- **External review:** three sequential automated GPT-5.6 Pro rounds are
  authorized for the post-R41A boundary. Reuse the existing `HMASD Algorithm
  Consultation` conversation, archive each full response before disposition,
  and do not submit rounds in parallel. After these three rounds, return to the
  manual default in `AGENTS.md`.

## Objective

Run the accepted R41B full-source access reproduction, then use its exact result
for automated GPT-5.6 Pro round 2 of 3. Round 1 accepted R41A as a valid reduced-
exposure no-access result and selected one 32-environment, 2,998,400-transition,
seed-1 original-source reproduction as the only next edge.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Commit and push the archived round-1 response, accepted disposition, and
   exact R41B contract.
2. Run R41B locally on CUDA and read its single registered result JSON.
3. Package that result as round 2; round 3 must depend on the archived and
   dispositioned round-2 answer.

## Immediate Constraints

- R41A must freshly extract and execute `ref/hmasd.tar` without porting it into
  the current trainer. Do not add `KEEP/SET`, shaping, or any reward beyond the
  original HMASD `q_D/q_d` source-algorithm terms.
- Track the source archive in this repository and use the enclosing project Git
  commit as its version identity; do not add hashes or checksums.
- Alice--Bob is a toy environment and runs locally. R41B uses 32 envs, seed 1,
  the original 937 outer updates, 2,998,400 transitions, and 14,055 optimizer
  steps per path. It is the full-source access gate, not an algorithm variant.
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
