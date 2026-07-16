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

Resolve the invalid R43-NRC fixed-anchor boundary before any further algorithm
run. The paired gate completed with a valid implementation contract, but the
fixed source-continuation arm lost the registered R41B service anchor. The NRC
arm therefore has no interpretable scientific verdict.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Commit and push the R43 result, fixed-anchor diagnostics, and one tracked
   GPT-5.6 Pro question.
2. Give the user the standard manual handoff prompt and wait for the raw reply.
3. Do not rerun R43 or start a successor until the review selects one exact
   causal edge and minimum evidence boundary.

## Immediate Constraints

- R41-derived gates execute a fresh `ref/hmasd.tar` extraction rather than
  porting it into the current trainer. Preserve the original HMASD `q_D/q_d`
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
- R43 run
  `logs/r43_nrc_reset_censored_320k_20260716_121756_retry2` completed
  `INVALID_R43_FIXED_ANCHOR_LOST`. M0 passed, but fixed final win/key0/key1 was
  `0.52/0.54/0.81`, below the registered `0.80/0.85/0.85` anchor. Treatment
  outcomes are quarantined and do not retire NRC.
- The source R41B checkpoint evaluates at win `0.89` on seed 1 and `0.93` on
  the R43 seed-43041 reset stream. The R43 fixed final checkpoint evaluates at
  `0.61` and `0.52` on those streams. A same-seed two-update comparison between
  untouched source continuation and the R43 fixed wrapper produced exactly
  zero parameter difference across all five trained modules. This localizes
  the invalidity to source-continuation instability rather than the R43 fixed
  wrapper or evaluation stream; the exact next comparator is under review.
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
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/` — invalid R43
  result, fixed-anchor diagnostics, and the pending decision question.
- `docs/external-review/legacy/` — legacy external-review evidence.
