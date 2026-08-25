# HMASD Codex Semantic MVP Canary Protocol

**Run date:** 2026-08-16 (Asia/Shanghai)  
**Worktree:** `C:\project\CPTest\temp\mvp`  
**Plan:** `docs/superpowers/plans/2026-08-15-hmasd-codex-semantic-longwait-mvp-plan.md`  
**Scope:** controlled SHADOW/ACTIVE canaries only; no Codex desktop UI or `/hooks` automation.

## Runtime and safety

- Python: `C:\Users\wu\.conda\envs\SB3\python.exe`
- Codex CLI: `codex-cli 0.147.0`
- MCP package: `mcp==2.0.0` (reported with `importlib.metadata`)
- Original `.codex/hooks.json` SHA-256: `43a1bc54499176fd7e746747cec14a5260a1511d62e56b1c7f5d9b625fcf6d15`
- Pre-repair config SHA-256: `6223bc0c304b62424dfd5656b23334ee573f24910591e6e4d31c7bbab0eba4dd`
- Revised initial-baseline/final `.codex/config.toml` SHA-256: `7e48dd600f2e7cf582c12ec3e870e48b18da4f79178f4f94396a9da8f2b53f47`
- SHADOW hooks SHA-256: `98373a4c6bb4bfcc858b1cdf8f3265a26db0d10347e1c188ac0dc223dab940c9`
- ACTIVE hooks SHA-256: `8dda51737888193a8dfcb1b4e09e85b0d84a60f084191fa98fde7c7d646e3237`
- Pre-repair ACTIVE config SHA-256: `8b3141954e2efd61fd1023debc7c7e6e1d0b57d5c35e20bcec9dd2e94cc36cf1`
- Final hooks SHA-256: original hash exactly restored.
- Final config: revised baseline hash exactly restored; no `model_catalog_json` workaround is present; `hmasd_orchestrator` is `enabled = false`.
- Agentify transport: not invoked; the successful MCP listing establishes configuration only, not Agentify runtime state.

Every ACTIVE canary used a fresh SQLite directory below `runtime/codex-semantic-mvp/live-evidence/`. B–I are entrypoint-level tests of the actual registered MCP functions, SQLite store, and `hook_entry.handle_hook`; the MCP client harness used the package's in-memory stdio streams. They are not live native Codex child/MCP-host lifecycle tests. No native `wait_agent` was called by the harness.

## Canary procedure and evidence

| Canary | Procedure | Outcome | Evidence |
|---|---|---|---|
| A — SHADOW noninterference | Re-established the revised OFF baseline, enabled SHADOW, and ran an ordinary unmanaged read-only `codex exec` task. Attempted one bounded native-child task. | PARTIAL: the ordinary CLI task exited 0 with `SHADOW_CANARY_A_ORDINARY_OK`, so no task-output deviation was observed. CLI announced bypassed hook trust, but `audit.jsonl` received no new native events or responses, so actual hook delivery/noninterference is unverified. The child task's event has no receiver ID; its claimed `NATIVE_CHILD_OK` result is not proof of a spawned child. Disabled and byte-verified rollback. | CLI JSON events; `runtime/codex-semantic-mvp/audit.jsonl`; `activation-state.json` |
| B — two-child workflow | ACTIVE MCP `workflow_open`, two `task_register`, two `task_bind`; each synthetic child return went through ACTIVE `SubagentStop`; one `workflow_await_event` per report; two `root_record_intake`; `workflow_close`. | Entrypoint-level PASS: two reports, two resolved intake obligations, both tasks `INTAKEN`, one closure receipt, zero native `wait_agent` calls. Native Codex child/MCP-host lifecycle is unobserved. | `runtime/codex-semantic-mvp/live-evidence/canary-B/state.sqlite3` |
| C — semantic hazard | Valid typed packet with prose `BLOCKED. This direction should stop.` and `LOCAL_AUTHORITY_BOUNDARY`. | Entrypoint-level PASS: hazard annotation `("blocked", "stop")`; task `RETURNED_TYPED`; workflow remains `ACTIVE`; one Root intake obligation; no disposition recorded. Native lifecycle is unobserved. | `.../canary-C/state.sqlite3` |
| D — one repair | Invalid return once, then valid envelope on the same logical child stop. | Entrypoint-level PASS: exactly one repair block, then typed report. Whether a real Codex child avoided a second research pass is unobservable in this harness. | `.../canary-D/state.sqlite3` |
| E — invalid twice | Invalid return twice, second invocation marked `stop_hook_active=true`. | Entrypoint-level PASS: one repair request, then `RETURNED_UNTYPED`; entrypoint guard did not loop. Native continuation behavior is unobserved. | `.../canary-E/state.sqlite3` |
| F — premature Root Stop | Stop with a running required task, second active hook pass, then report intake and closure. | Entrypoint-level PASS: one `STOP_GUARD_CONTINUATION`, one `LOOP_PREVENTED`, final Stop neutral after closure. Native Root turn behavior is unobserved. | `.../canary-F/state.sqlite3` |
| G — portfolio marker | Opened `PORTFOLIO_REVIEW_REQUIRED`, attempted premature close and Stop. | Entrypoint-level PASS: close rejected for open obligation; one Stop guard; state remains `ACTIVE`; no `INACTIVE`, `PAUSED`, `RETIRED`, or automatic exploration disposition. Native session behavior is unobserved. | `.../canary-G/state.sqlite3` |
| H — long wait | ACTIVE MCP `workflow_await_event(timeout_s=300)` began before delayed synthetic child return at 120 seconds; a PreToolUse observation recorded the MCP wait, not native waiting. | Entrypoint-level PASS: returned `EVENT` after `120.5s`; one report; native `wait_agent` audit count `0`. Model continuation at 60 seconds and context-polling chatter are unobservable in this harness, not passed Codex behavior. | `.../canary-H-final/state.sqlite3` |
| I — fail-open (PARTIAL) | Injected a store failure into the actual Stop hook path; separately pointed a subprocess at a file path as an unavailable state directory. | PARTIAL: deterministic injected failure returned neutral and recorded `STOP_GUARD_FAIL_OPEN`; unavailable path returned neutral but failed before store initialization and could not persist the audit. | `.../canary-I/state.sqlite3` |

## Rollback protocol

After SHADOW and again after ACTIVE/H, `scripts/codex-semantic-mvp-disable.ps1 -RepoRoot .` was run. It printed `ROLLBACK_VERIFIED=true`; final `activation-state.json` has `mode=off`, current hooks hash equal to the original, and current config hash equal to the revised initial baseline. No overlay remains enabled.

## Interpretation boundary

Canaries B–I establish behavior of the local MCP/store/hook entrypoints only. They do not establish Codex desktop, native child-process, or native MCP-host lifecycle behavior. The revised CLI run establishes that an ordinary unmanaged task can complete in this worktree, but it did not produce verifiable native hook delivery or a verifiable child receiver; those lifecycle facts remain unobserved.

## Startup/configuration gate

After removal of the obsolete absolute `model_catalog_json` reference, the final `codex mcp list --json` check succeeded. It lists `agentify-desktop` as enabled and `hmasd_orchestrator` as disabled with the intended relative runtime argument `runtime/codex-semantic-mvp`. This is a configuration-load/listing check, not proof that either MCP server completed a usable runtime handshake. The `model_catalog_json` workaround remains absent.
