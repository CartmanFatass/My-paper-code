# HA-CTSE Current Work

Updated: 2026-07-16

## Controller

- **Active controller:** Codex on branch `aggressive`, working directly in
  `C:\project\HMASD`.
- **Versioning:** Git only; push with `git push My-paper-code aggressive`.
- **Project boundary:** IMOD is operational reference only, not HMASD evidence.
- **Shared GPU scheduler:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9`.
- **External review:** the three authorized automated GPT-5.6 Pro rounds are
  complete. Further exchange uses the manual default in `AGENTS.md`.

## Objective

Use the valid `PASS_R41B_SOURCE_ACCESS` checkpoint to test one real native
temporal mechanism. The pure categorical KEEP/SET reinterpretation selected in
Pro round 3 is retired without training because source audit proves it is
behaviorally identical to the original full refresh.

The active candidate is R42-IRR: a zero-output, task-blind
incumbent-roster-conditioned residual on the existing MAT individual logits at
the original `k0=50` clock. It must preserve the exact R41B policy at
initialization and use the existing high-level advantage; it adds no reward,
duration action, independent KEEP head, team latent, or age input.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Commit and push the completed R42-IRR external overlay, paired runner,
   analyzer, and frozen experiment contract as one pre-launch boundary.
2. Run the registered local paired gate after reporting its exact parameters to
   the user: two concurrent 16-env arms, 320K steps per arm, seed `42041`.
3. Read the single result JSON once, disposition its M0--M3 branch, and record
   only the terminal result boundary.

## Immediate Constraints

- R42 must freshly extract and execute `ref/hmasd.tar` without porting it into
  the current trainer. Preserve the original HMASD `q_D/q_d` source-algorithm
  terms and do not add shaping or a new intrinsic reward.
- Track the source archive in this repository and use the enclosing project Git
  commit as its version identity; do not add hashes or checksums.
- Alice--Bob is a toy environment and runs locally. R41B used 32 envs, seed 1,
  the original 937 outer updates, 2,998,400 transitions, and 14,055 optimizer
  steps per path. It is the positive source anchor, not an algorithm variant.
- Intrinsic reward must remain environment-agnostic and may not consume task
  identities, goals, contacts, phases, success predicates, distances, or
  external reward.
- Do not begin open-roster or variable-`N` implementation before the fixed-`N`
  temporal gate.
- The R42 preflight against the real R41B checkpoint passed with zero action,
  likelihood, value, entropy, replay, and base-gradient error; the residual
  direct policy-gradient norm was `0.2221746`. Do not add another smoke or test
  stage before the paired run.
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
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/` — R41B
  evidence, all three Pro rounds, and the final source-level disposition.
- `docs/external-review/legacy/` — legacy external-review evidence.
