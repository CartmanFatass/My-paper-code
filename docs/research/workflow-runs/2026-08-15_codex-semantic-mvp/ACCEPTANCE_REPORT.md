# HMASD Codex Semantic MVP Acceptance Report

**Decision:** `DO_NOT_MERGE_OUT_OF_BOX`
**Run:** 2026-08-16, isolated worktree `C:\project\CPTest\temp\mvp`  
**Recommendation rationale:** project entrypoint tests pass, and the feature worktree's ACTIVE configuration contains inline TOML hooks plus an enabled managed MCP. The doctor reports `mode=active` and `server_enabled=true`, and `codex mcp list --json` succeeds. Strict NativeSmoke on `codex-cli 0.147.0` returned a real `thread_id`, but the audit remained 5 lines/2039 bytes and the test correctly failed `NATIVE_HOOK_EVENT_REQUIRED`. Live native hook delivery is **NOT verified**; do not merge or push this as `out-of-box` until an upstream CLI release fixes or re-proves it.

## Exact versions and hashes

| Item | Value |
|---|---|
| Python executable | `C:\Users\wu\.conda\envs\SB3\python.exe` |
| Codex | `codex-cli 0.147.0` (npm latest is also `0.147.0`) |
| MCP | `2.0.0` |
| Original hooks SHA-256 | `43a1bc54499176fd7e746747cec14a5260a1511d62e56b1c7f5d9b625fcf6d15` |
| SHADOW hooks SHA-256 | `98373a4c6bb4bfcc858b1cdf8f3265a26db0d10347e1c188ac0dc223dab940c9` |
| ACTIVE hooks SHA-256 | `8dda51737888193a8dfcb1b4e09e85b0d84a60f084191fa98fde7c7d646e3237` |
| Final hooks SHA-256 | `43a1bc54499176fd7e746747cec14a5260a1511d62e56b1c7f5d9b625fcf6d15` |
| Pre-repair config SHA-256 | `6223bc0c304b62424dfd5656b23334ee573f24910591e6e4d31c7bbab0eba4dd` |
| Revised baseline/final config SHA-256 | `7e48dd600f2e7cf582c12ec3e870e48b18da4f79178f4f94396a9da8f2b53f47` |
| Pre-repair ACTIVE config SHA-256 | `8b3141954e2efd61fd1023debc7c7e6e1d0b57d5c35e20bcec9dd2e94cc36cf1` |

## Test gate

- Project entrypoint tests pass; prior evidence records the latest full unit result as **139** and the focused activation/smoke result as **56**.
- Full repository pytest collection: **not clean**; three scenario-7 modules fail collection with `ModuleNotFoundError: No module named 'tests._scenario7_fixtures'` (`scenario7_channel_cache_test.py`, `scenario7_events_certificates_test.py`, `scenario7_reward_safety_test.py`). These failures are outside the MVP package and were not changed.
- Codex binary check: `codex --version` returned `codex-cli 0.147.0`; `npm view @openai/codex version` returned `0.147.0`.
- MCP configuration listing: with the feature worktree ACTIVE, `codex mcp list --json` succeeds and lists `hmasd_orchestrator` enabled with its intended relative `runtime/codex-semantic-mvp` state argument.
- The listing proves config loading/listing only; it is not a usable runtime-handshake proof for either MCP server. No `model_catalog_json` workaround remains.
- Agentify: not invoked; the listing does not assert Agentify runtime state.

## Thresholds

| Threshold | Result | Basis |
|---|---:|---|
| `unit_test_failures` (project entrypoints) | 0 | latest full unit result 139; focused result 56 |
| `shadow_behavior_changes` | no task-output deviation observed; hook delivery unverified | ordinary CLI returned requested text; runtime audit had no new native hook records |
| `lost_reports` | 0 | B: two reports observed and intaken; H: one report observed |
| `duplicate_reports_after_dedupe` | 0 observed | fresh stores; one report per child |
| `automatic_continuation_loops` | 0 at entrypoint level | D/E/F guard counts bounded to one; native model behavior unobservable |
| `managed_wait_agent_calls` | 0 | B and H audit counts |
| `semantic_hazard_to_global_transition` | 0 | C remains ACTIVE with `NOT_ASSERTED` |
| `portfolio_review_to_automatic_disposition` | 0 at entrypoint level | G close rejected; no disposition tokens; native session behavior unobservable |
| `rollback_hash_mismatches` | 0 | SHADOW and final ACTIVE disable both exact |

The full repository collection issue means the overall repository `unit_test_failures` threshold cannot be claimed as zero; the zero above is explicitly scoped to the MVP suite.

## Canary results

### A — SHADOW

With the repaired configuration, an unmanaged read-only `codex exec` task exited 0 and returned `SHADOW_CANARY_A_ORDINARY_OK`; no task-output deviation was observed. The CLI emitted its hook-trust-bypass notice, but `runtime/codex-semantic-mvp/audit.jsonl` received no new native hook record or hook response, so actual SHADOW hook delivery and native noninterference remain unverified. A bounded child request first failed in ephemeral mode because no thread was available. A non-ephemeral retry returned the model text `NATIVE_CHILD_RESULT NATIVE_CHILD_OK`, but its only collaboration event was a `wait` with an empty receiver list; it is not evidence that a child was spawned or returned. SHADOW was disabled and exact rollback verified.

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

## Historical rollback check

The earlier rollback check printed `ROLLBACK_VERIFIED=true`; `.codex/hooks.json`
matched the original hash and the disable path restored `mode=off` with MCP
disabled. That historical check does not describe the current feature
worktree, which is ACTIVE. `model_catalog_json` remains absent and Agentify was
not invoked.

## Adoption boundary

The local project entrypoints are passing, but genuine native Codex hook
delivery remains unverified. Do not merge or push as `out-of-box`; wait for an
upstream CLI release to fix or re-prove the native hook path, then rerun the
strict smoke below. Related upstream tracking: [#26383](https://github.com/openai/codex/issues/26383)
and [#33097](https://github.com/openai/codex/issues/33097).

## Native smoke operation

The bounded native smoke path is explicit and does not enable or disable hooks.
It protects `.codex/config.toml` and `activation-state.json` byte-for-byte; the
native hook is expected to append diagnostic `audit.jsonl`/SQLite evidence.
Run it only after the live config contains the reviewed inline TOML hook block
with all five lifecycle handlers and `--mode active`, plus the enabled managed
MCP section:

```powershell
pwsh -NoProfile -NonInteractive -File scripts/codex-semantic-mvp-test.ps1 `
  -RepoRoot . -NativeSmoke -NativeTimeoutSec 120
```

The command snapshots the `runtime/codex-semantic-mvp/audit.jsonl` byte cursor
and line count, invokes a safe ordinary `codex exec` with
`--dangerously-bypass-hook-trust`, then requires a newly appended recognized
native hook event. A successful CLI exit or stdout response alone is rejected
with `NATIVE_HOOK_EVENT_REQUIRED`; missing or incomplete inline TOML is rejected
before execution. Test doubles can be supplied with `-CodexCommand` for local
contract tests without contacting a model. The focused activation/smoke
evidence is **56** under the SB3 Python interpreter. A pass requires
`NATIVE_SMOKE_VERIFIED=true`, one real `thread_id`, and at least one newly
appended recognized `mode=active` audit event for that session; unchanged audit
bytes/lines must fail with `NATIVE_HOOK_EVENT_REQUIRED`.
