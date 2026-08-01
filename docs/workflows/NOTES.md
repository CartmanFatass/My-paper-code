# Notes on the world

Raw notes on how this project actually runs. Facts here are observed from the
repository and confirmed in session, not assumed. Canonical terms are marked
**bold** on first definition.

## Runtime and tools

- **Claude Code** is the agent runtime, as of 2026-07-24. It replaced Codex; the
  `.codex/` tree is deleted and its five agent profiles are now
  `.claude/agents/*.md`.
- Python is the registered interpreter
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, `torch 2.7.0+cpu`,
  **CPU backend, torch threads 1**. Never `conda run`. Collections run at 16
  parallel environments (`FORMAL_NUM_ENVS`).
- Git remote is GitHub `CartmanFatass/My-paper-code`. Branches in play:
  `aggressive` (previous exploration direction), `untied-k` (current — the
  skill-period-k unbinding direction), `new-test`, `Claude`.
- External review runs through registered **Pro conversations** via the
  Agentify Desktop local HTTP API (`/review-query`, receipt-verified; browser
  transport retired 2026-08-01). Both `untied-k` reviewers are registered in
  `docs/external-review/REVIEWER_CONVERSATIONS.json`.

## Roles

- **Project Manager (PM)** — the persistent session. Sole owner of workflow,
  scientific reconciliation, acceptance, Git, review transport, experiment
  assignment, and successor selection. There is no Controller and no persistent
  Monitor.
- **Subagents** — nine bounded children under `.claude/agents/`, tiered by the
  work: opus for judgment about protected semantics, sonnet for bounded
  construction, haiku for lookup, transcription and execution. No child commits,
  spawns a successor, or accepts its own work.
- **External Pro** — owns only the scientific answer to the exact submitted
  question. No workflow, code, or compute authority.

## Channels processed

| Channel | What arrives | Where it lands |
|---|---|---|
| Formal run artifacts | `train -> evaluate -> analyze` output | `logs/<run-id>/` |
| External Pro replies | one raw scientific answer per round | `docs/external-review/rounds/<round-id>/21_PRO_OPEN_RAW.md` |
| Run classification | status, evidence, decision | `docs/project/ExpRecord.md` dashboard row |
| User-facing summary | Chinese iteration report | `docs/report/ITERATION_<n>.md` |
| Live state | active boundary, grant accounting | `docs/project/CURRENT_WORK.md` |

## Terminology

- **Conclusion-bearing iteration** — one pass that produces a registered
  scientific result. 19 consumed to date.
- **Autonomous research grant** — a standing user authorization to continue
  without re-asking. Currently `ACTIVE_TEN_ITERATION_TOY_FIRST_UAV_PROMOTION_CHAIN`
  with `iterations_remaining=8` and `intermediate_authorization_prompts=forbidden`.
- **Protected semantics** — reward, probability factorization, gradients/detach,
  recurrent state, masks, clocks, lifecycle, RNG, replay, credit, checkpoint
  meaning. Changing one requires an explicitly accepted scientific boundary.
- **Formal compute** — a conclusion-bearing run. `formal_compute_authority=user_only`.
- **Toy first** — algorithm discovery runs on toy environments by default; a
  heavy UAV run needs a recorded PM promotion decision.
- **Proof-sized test** — the smallest proof that can change the decision. Not
  coverage, not a full suite.
- **Freshness fence** — the exact identity block submitted to the Pro
  conversation. An accepted matching fence is never resubmitted.
- **Terminal payload** — the single `COMPLETE`/`ERROR` return from the
  experiment operator. It carries mechanical facts, never acceptance.

## The documented loop (AGENTS.md, "Research and execution loop")

1. User sets goal and protected/formal authority.
2. PM selects the smallest bounded action.
3. If external science is needed: author, commit, push, transport, archive, reconcile.
4. PM implements, verifies, repairs, accepts — directly or via a bounded child.
5. Before a conclusion-bearing run, PM freezes the evidence contract.
6. PM spawns one `hmasd-experiment-operator`; it silently runs and returns once.
7. PM validates artifacts and records the smallest supported update.
8. PM writes `docs/report/ITERATION_<n>.md` in Chinese before advancing.
9. PM does Git integration and selects the next in-authority action.

## Observed friction (2026-07-24)

Migrating the runtime silently broke three workflow contract tests, five file
paths, and one whole Skill route — none of it visible until the tests were run
by hand. Nothing runs those tests automatically.
