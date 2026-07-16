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

Resolve one source-clock contradiction before implementing the accepted
`MODIFY R43-NRC` route. GPT-5.6 Pro confirmed R42 as a valid failure and selected
a true renewal factor, conditional non-incumbent skill assignment, and separated
renewal/skill credit. The source collector, however, auto-resets successful
Alice--Bob environments between global high checks without a new high action;
this conflicts with the response's forced initial RENEW on every episode reset.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Commit and push the raw R42/R43 response, accepted disposition, source vector
   wrapper, and focused source-clock correction question.
2. Give the user the fixed manual GPT-5.6 Pro correction prompt and archive the
   returned raw response before interpretation.
3. Implement only the resulting single reset/segment/credit contract; do not
   guess between source-global and per-reset high actions.

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
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/` — R42 raw results,
  accepted R43 response, disposition, and pending source-clock correction.
- `docs/external-review/legacy/` — legacy external-review evidence.
