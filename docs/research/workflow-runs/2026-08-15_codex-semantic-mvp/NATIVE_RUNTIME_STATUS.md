# Native Codex Runtime Status

**Disposition:** `LIVE_NATIVE_HOOK_UNVERIFIED`

The feature worktree is currently **ACTIVE**. Its live `.codex/config.toml`
contains the inline TOML hook block (all five lifecycle handlers) and the
managed MCP is enabled. The doctor check reports `mode=active` and
`server_enabled=true`; `codex mcp list --json` succeeds and lists
`hmasd_orchestrator` enabled.

## Strict native smoke result

The strict smoke run used `codex-cli 0.147.0` and returned a real `thread_id`.
The audit did not change: it remained **5 lines and 2039 bytes** before and
after the run. The test therefore correctly failed with
`NATIVE_HOOK_EVENT_REQUIRED`; a successful CLI response is not hook-delivery
evidence. `npm view @openai/codex version` also reports `0.147.0`, so this is
the current npm latest in the recorded environment.

The bundled WindowsApps `codex.exe` could not start because of **Access
Denied**. That launch failure is separate from, and does not repair, the
missing audit event. Related upstream tracking is [#26383](https://github.com/openai/codex/issues/26383)
and [#33097](https://github.com/openai/codex/issues/33097).

Project entrypoint tests pass; prior evidence records the latest full unit
result as **139** and the focused activation/smoke result as **56**. This does
not verify live native hook delivery. Do not merge or push this feature as
`out-of-box` until an upstream CLI release fixes or re-proves native hook
delivery.

## Exact rerun

After a newer upstream CLI is available, run from the feature worktree:

```powershell
Set-Location C:\project\CPTest\temp\mvp
pwsh -NoProfile -NonInteractive -File .\scripts\codex-semantic-mvp-test.ps1 `
  -RepoRoot . -NativeSmoke -NativeTimeoutSec 120
```

The run passes only when the CLI returns one real `thread_id`, the audit cursor
grows with at least one recognized `mode=active` hook event for that same
session, and the command prints `NATIVE_SMOKE_VERIFIED=true`. It must also
leave `.codex/config.toml` and `runtime/codex-semantic-mvp/activation-state.json`
byte-for-byte unchanged and must not report `NATIVE_HOOK_EVENT_REQUIRED`.
