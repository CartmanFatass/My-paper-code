# Claude Session State

Updated: 2026-07-22

Compact live state for the Claude Code controller on branch `Claude`. Keep this
short and current. Durable reasoning goes in `DECISIONS.md`, not here.

## Branch

`Claude`, cut from `aggressive` at `58e7a24`. No upstream yet. Codex Desktop
continues independently on `aggressive`; this branch is not kept mergeable.

## Objective

Establish the Claude-side workflow contract, then resume the
`EVENT_HELD_COMMITMENT_LINK_G0` line on the CPU backend.

## In the working tree, uncommitted

- `ha_ctse_process/noncalendar_commitment_testbed.py` — `FORMAL_EXECUTION_BACKEND`
  changed `"cuda"` → `"cpu"`. Protected constant; needs a review pass before commit.
- `CLAUDE.md` — replaced the `AGENTS.md` pointer stub with the Claude controller
  contract.
- `.gitignore` — added `!docs/claude/*.md` negation.
- `.claude/agents/` — **all four definitions deleted**. Delegated work now runs
  on Codex models (D10/D11); the briefs live in `docs/claude/roles/`.
- `docs/claude/roles/` — new: `README.md` (bindings + dispatch contract),
  `project-manager.md`, `scout.md`, `implementer.md`, `reviewer.md`.
- `docs/project/AGENT_CONTEXT.md` — environment facts corrected.

## Delegation runtime

`codex-cli 0.145.0` installed globally; ChatGPT auth already active. Plugin
`setup --json` reports `ready: true`. Both models probed live and reachable at
Codex's exact efforts: `gpt-5.6-luna`/medium and `gpt-5.6-sol`/xhigh.

Isolated runtime at `C:\Users\fires\.codex-claude` (config + copied `auth.json`),
keeping session state out of Codex Desktop's `~/.codex`. **`CODEX_HOME` must be
exported on every dispatch**; unset it silently uses the other controller's home.

Nested spawn verified working (`CHILD_SAID: NESTED_OK`). Platform limits found
and recorded in D12: no `agent_type` on `spawn_agent`, and Luna is rejected
server-side as a child model despite the catalog loading correctly.

Thread reuse verified (`--resume-last` recalled a token across turns).

### Active threads

| Role | Thread id | Policy |
|---|---|---|
| Project Manager | *(none yet — record on first dispatch)* | persistent per work package |
| Reviewer | n/a | always fresh, never resumed |
| Scout | n/a | fresh |

Before resuming, check the `Resuming thread <id>` line against the PM id above.
On mismatch, stop — a fresh dispatch from another role has become "latest".

Nothing committed. Nothing running.

## Focused suite on CPU

`tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`, 78s:
**30 passed, 3 failed, 21 errors.**

- 21 errors: one root cause — the `streamed_exercise_root` module fixture hard-
  asserts `device.type == "cuda"` (test file lines 174–176).
- `test_dense_batch_invariance_is_measured_not_assumed` — fails because it
  asserts CPU *must* lack batch invariance. On this host the probe measures
  exactly `0.0`; invariance holds. See D5.
- `test_shared_event_heads_are_row_stable_…` — `mark_component` replay error
  `2.384e-07` (= 2⁻²², one float32 ULP) vs bitwise `0.0` on CUDA.
  `report["passed"]` is still True; only the strict bitwise assertion fails.
- `test_registered_backend_activation_never_falls_back` — assumes both backends
  are available on the host; this box has no CUDA.

`test_collector_protected_outputs_pinned_digest` **passed**: the CPU digests
pinned on the previous machine reproduce bit-for-bit here.

## Next actions

1. Repair the 3 tests to measure the active host rather than assert the old
   host's numbers, and de-hardcode the CUDA fixture. Keep fail-closed.
2. Run the **real** fork on this host — the decisive test for P1b, whose
   synthetic probe no longer reproduces. Falsifier: if `fork_single_opportunity`
   is not bitwise exact here, P1b stands and CPU cannot produce the fork evidence.
3. Close `formal_evaluate` coverage (P8) before any run is launched.

## Blocked / open

- P1 blocks the `A_KEEP`/`A_RENEW` C gates on **any** backend — the fork engine
  is deterministic-only while Replacement C is defined on held-out stochastic.
  Independent of the CPU question.
- No external GPT-5.6 Pro round has been opened from this branch yet.

## Environment

Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`
(python 3.10.20, torch 2.7.0+cpu, no CUDA on this host). Repo root
`C:\Projects\My-paper-code`. Remote is `origin`.
