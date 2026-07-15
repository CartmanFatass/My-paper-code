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

Establish the fixed-`N` positive anchor by running the original HMASD package
stored at `ref/hmasd.tar` and its `Alice_and_Bob` environment. The current
repository may provide only external launch, telemetry, evaluation, and result
analysis. Only a registered R41 PASS may authorize native-categorical R30 on
the same task and seed-1 final checkpoint.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Launch `scripts/run_r41_official_hmasd_local.ps1` on local CUDA.
2. Run one seed worker with 32 rollout environments; seeds `1..5` execute
   sequentially under the registered M0--M2 contract.
3. Read the final analyzer result and select only its registered branch.

## Immediate Constraints

- R41 must freshly extract and execute `ref/hmasd.tar` without porting it into
  the current trainer. Do not add `KEEP/SET`, shaping, or any reward beyond the
  original HMASD `q_D/q_d` source-algorithm terms.
- Track the source archive in this repository and use the enclosing project Git
  commit as its version identity; do not add hashes or checksums.
- Alice--Bob is a toy environment and runs locally. Preserve the original
  32-environment per-seed batch; limit aggregate load by using one seed worker,
  not by changing optimizer exposure.
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
