# HMASD Codex Semantic MVP Acceptance Report

**Decision:** `ADOPT_SHADOW`  
**Run:** 2026-08-16, isolated worktree `C:\project\CPTest\temp\mvp`  
**Recommendation rationale:** local ACTIVE semantics and the 120-second runtime wait passed at real MCP/store/hook entrypoints, but B–I are not live native Codex child/MCP-host lifecycle tests; the unmanaged Codex CLI task could not start; and the normal MCP startup/configuration gate failed. Keep the overlay in SHADOW until genuine lifecycle evidence and a supported Codex MCP startup surface are available.

## Exact versions and hashes

| Item | Value |
|---|---|
| Python executable | `C:\Users\wu\.conda\envs\SB3\python.exe` |
| Codex | `codex-cli 0.147.0` |
| MCP | `2.0.0` |
| Original hooks SHA-256 | `43a1bc54499176fd7e746747cec14a5260a1511d62e56b1c7f5d9b625fcf6d15` |
| SHADOW hooks SHA-256 | `98373a4c6bb4bfcc858b1cdf8f3265a26db0d10347e1c188ac0dc223dab940c9` |
| ACTIVE hooks SHA-256 | `8dda51737888193a8dfcb1b4e09e85b0d84a60f084191fa98fde7c7d646e3237` |
| Final hooks SHA-256 | `43a1bc54499176fd7e746747cec14a5260a1511d62e56b1c7f5d9b625fcf6d15` |
| Original/final config SHA-256 | `6223bc0c304b62424dfd5656b23334ee573f24910591e6e4d31c7bbab0eba4dd` |
| ACTIVE config SHA-256 | `8b3141954e2efd61fd1023debc7c7e6e1d0b57d5c35e20bcec9dd2e94cc36cf1` |

## Test gate

- Semantic MVP unit suite: **99 passed** (`python -m pytest tests/codex_semantic_mvp -q`).
- Full repository pytest collection: **not clean**; three scenario-7 modules fail collection with `ModuleNotFoundError: No module named 'tests._scenario7_fixtures'` (`scenario7_channel_cache_test.py`, `scenario7_events_certificates_test.py`, `scenario7_reward_safety_test.py`). These failures are outside the MVP package and were not changed.
- Codex startup check: `codex --version` returned `codex-cli 0.147.0` after rollback.
- MCP startup/configuration gate: `codex mcp list --json` failed with `Error: failed to load configuration` / `系统找不到指定的路径。 (os error 3)`.
- The likely pre-existing cause is the missing absolute `model_catalog_json` reference `C:\Projects\HMASD\runtime\model-catalog-v2-workaround.json`. Task 9 only appended the semantic-MVP config block; this evidence does not attribute the failure to Task 9.
- `codex --version` succeeding is only a binary/version check, not normal MCP startup evidence.
- Agentify: not invoked; configuration unchanged after rollback.

## Thresholds

| Threshold | Result | Basis |
|---|---:|---|
| `unit_test_failures` (MVP suite) | 0 | 99 passed |
| `shadow_behavior_changes` | 0 at hook-entrypoint level | neutral hook responses; live CLI task unavailable |
| `lost_reports` | 0 | B: two reports observed and intaken; H: one report observed |
| `duplicate_reports_after_dedupe` | 0 observed | fresh stores; one report per child |
| `automatic_continuation_loops` | 0 at entrypoint level | D/E/F guard counts bounded to one; native model behavior unobservable |
| `managed_wait_agent_calls` | 0 | B and H audit counts |
| `semantic_hazard_to_global_transition` | 0 | C remains ACTIVE with `NOT_ASSERTED` |
| `portfolio_review_to_automatic_disposition` | 0 at entrypoint level | G close rejected; no disposition tokens; native session behavior unobservable |
| `rollback_hash_mismatches` | 0 | SHADOW and final ACTIVE disable both exact |

The full repository collection issue means the overall repository `unit_test_failures` threshold cannot be claimed as zero; the zero above is explicitly scoped to the MVP suite. The MCP startup/configuration gate also remains unfulfilled.

## Canary results

### A — SHADOW

The real hook entrypoint recorded `SESSION_STARTED`, `SUBAGENT_STARTED`, `PRE_TOOL_USE_OBSERVED` (including a `wait_agent` observation), `SUBAGENT_STOPPED`, and `STOP_OBSERVED`. Every response was `{"continue":true}` and no model-visible context was added. The bounded CLI command failed immediately with `Error: 系统找不到指定的路径。 (os error 3)`; this is an execution-surface limitation, not a canary pass. SHADOW was disabled and exact rollback verified.

### B — valid two-child managed workflow

At the entrypoint level, MCP returned two `EVENT` waits at cursors 7 and 10. Reports A and B were both persisted, each Root intake resolved its obligation, tasks ended `INTAKEN`, and one `COMPLETED` closure receipt was created. Native `wait_agent` count in the harness was 0. This does not establish a live native Codex child/MCP-host lifecycle.

### C — semantic hazard

At the entrypoint level, the raw prose terms were `blocked` and `stop`. The typed packet remained `LOCAL_AUTHORITY_BOUNDARY` with `global_disposition=NOT_ASSERTED`; state was `ACTIVE`, task lifecycle `RETURNED_TYPED`, and one Root intake obligation existed. No global disposition was generated. Native lifecycle behavior is unobserved.

### D/E — envelope repair

D issued one entrypoint repair continuation and accepted a valid envelope. Whether a real Codex child avoided a second research pass is unobservable in this harness. E issued one entrypoint repair continuation, then accepted the second invalid return as `RETURNED_UNTYPED`; no entrypoint loop occurred and Root intake remained available. Native continuation behavior is unobserved.

### F — Root Stop guard

At the entrypoint level, the first Stop was blocked once with the neutral obligation continuation. The active-hook second pass was neutral and recorded `LOOP_PREVENTED`. After intake and closure, Stop was neutral. Native Root turn behavior is unobserved.

### G — portfolio liveness marker

At the entrypoint level, the explicit portfolio obligation kept the workflow `ACTIVE`; premature closure raised `ValueError: workflow has open obligations`, and one Stop guard was recorded. No automatic pause, retirement, inactivity, or exploration decision was emitted. Native session behavior is unobserved.

### H — exact long wait

The final entrypoint-level run waited `120.5s` against `timeout_s=300`, then returned `EVENT` promptly after the delayed synthetic report. `wait_agent_audit_count=0` and `report_count=1`. Model continuation at 60 seconds and context-polling chatter are unobservable in this harness, so they are not claimed as passed Codex behavior. The earlier short-session attempt ended before a report and is not counted.

### I — fail-open (PARTIAL)

A deterministic failure injected into the actual Stop hook path returned neutral and recorded `STOP_GUARD_FAIL_OPEN`; the workflow's semantic rows were not changed, and the event-count increase was the expected fail-open audit event. A separate subprocess pointed to a file as its state directory and returned neutral (`exit 0`, `{"continue":true}`) but failed before SQLite initialization, so no audit could be persisted. Canary I is therefore PARTIAL, not a full pass.

## Final rollback state

`codex-semantic-mvp-disable.ps1` printed `ROLLBACK_VERIFIED=true`; `.codex/hooks.json` exactly matches the original hash, `.codex/config.toml` exactly matches the original hash, `activation-state.json` reports `mode=off`, and the MCP block has `enabled = false`. Agentify was not invoked and configuration was unchanged.

## Adoption boundary

This run supports **SHADOW adoption only**. It explicitly rules out `ADOPT_ACTIVE_MVP`: genuine native Codex child/MCP-host lifecycle evidence is missing, and the `codex mcp list --json` startup/configuration gate failed. The full repository unit collection is also not clean. This is not a rejection of the local implementation; ACTIVE remains disabled and recoverable.
