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

Run the single registered R43-NRC mechanism gate after user approval. GPT-5.6
Pro confirmed the source contradiction and selected reset-censored controller
time. The implementation now supplies a true renewal factor, a conditional
non-incumbent skill factor, and separate renewal/skill-event credit while
preserving the original global `k0=50` clock and source HMASD low/intrinsic path.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Complete one scoped diff review of the R43 implementation and formal
   contract; do not add another test layer.
2. Commit and push the pre-launch boundary, including the raw correction
   response and accepted disposition.
3. Report the exact local paired-run parameters and rationale; launch only
   after explicit user approval.

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
- R43 focused preflight passed on the real R41B checkpoint. The 32-outcome
  probability decomposition error is below `1e-6`; a two-update CUDA check had
  zero replay/prefix error and exact clock/optimizer counts. Do not add another
  smoke or test stage before the paired run.
- R42 run `logs/r42_irr_native_roster_residual_320k_20260716_100824` completed
  valid `VALID_FAIL_R42_IRR_SERVICE`. Fixed/treatment wins were `0.98/0.88`;
  treatment-minus-fixed win CI was `[-0.17,-0.03]`. Treatment discordance was
  `0.10`, full-sync SET was `0.90`, and SET-target entropy was `0.6514`.
- In source Alice--Bob, success sets `done=True`, the vector wrapper immediately
  resets that environment, and the runner still samples high actions only at
  global rollout steps `0/50`. The R42 fixed evaluation averaged `58.56` steps
  and 98/100 episodes ended before step 100, so this is an exercised boundary.
- Completed branch decisions in `memory/ExpRecord.md` and the cited research
  decision files are binding. Reopen one only through a new registered causal
  edge, not by retuning budgets, seeds, thresholds, rewards, or model size.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — research contract.
- `memory/IMPLEMENTATION_PLAN.md` — latest staged core work and terminal state.
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
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/` — R42 result,
  accepted R43 route, source-clock correction, raw responses, and disposition.
- `docs/external-review/legacy/` — legacy external-review evidence.
