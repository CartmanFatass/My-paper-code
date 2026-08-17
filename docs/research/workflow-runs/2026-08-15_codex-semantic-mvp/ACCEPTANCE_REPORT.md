# Codex Semantic MVP Acceptance Report

## Accepted live surface

The live configuration is [`.codex/config.toml`](../../../../.codex/config.toml),
not `.codex/hooks.json`. It contains one managed MCP block and one managed TOML
hook block. The hook block declares all five lifecycle handlers:

- `SessionStart`
- `SubagentStart`
- `SubagentStop`
- `Stop`
- `PreToolUse`

On Windows each handler specifies the same `command` and `commandWindows`
value. This is required for Desktop's Windows command selection. The semantic
state directory remains relative to the repository: `runtime/codex-semantic-mvp`.

## Activation and trust

Activate from the repository root with the SB3 interpreter configuration
already present in the repository:

```powershell
.\scripts\codex-semantic-mvp-enable.ps1 -RepoRoot . -Mode Active
```

The script validates and atomically updates only its delimited TOML blocks;
it never overwrites legacy `hooks.json`. It accepts a previous managed block
without `commandWindows` solely in order to migrate it, and rejects malformed,
duplicate, or conflicting hook definitions.

Codex intentionally does not execute an unmanaged command hook until that
exact hook definition is trusted. After a fresh checkout or a hook-command
change, approve the five repository hooks in Codex Desktop's Hooks UI. An
automation may instead query `hooks/list` and write each returned `currentHash`
as that hook's `trusted_hash` in the user-level `hooks.state` through
`config/batchWrite`. The trust records are machine/user state, not portable
repository configuration; the repository itself has no absolute runtime
directory.

After a hook-command change, trust the five repository hooks from the
repository root:

```powershell
& C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe -m tools.codex_semantic_mvp.trust_hooks --repo-root .
```

Use the doctor command after activation for configuration and runtime health:

```powershell
& C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe -m tools.codex_semantic_mvp.doctor --repo-root .
```

`doctor` validates the repository-owned configuration shape. Actual delivery
is established only by a new audit record from a fresh native session.

## Native Desktop proof

On 2026-08-16, a fresh Desktop task `01a00720-35b3-7eb0-90b6-9a0a057e8384`
spawned one native child with `model=gpt-5.6-luna`, `reasoning_effort=max`,
and `fork_turns=1`. The child completed with the expected smoke token, and
the repository audit log then contained both a `SUBAGENT_STARTED` and a
`SUBAGENT_STOPPED` event for that same session and turn. This is the accepted
end-to-end proof that active subagent semantic protections are delivered by
Desktop rather than merely rendered in configuration or stdout.

The activation regression suite additionally checks all five emitted handler
tables, Windows command parity, mode transitions, conflict rejection,
byte-exact legacy preservation, and atomic failure compensation.

## Operational note

`hooks.state` keys may contain an absolute source identity because Codex uses
the exact configuration source to scope trust. That user-local security key is
distinct from the semantic runtime path, which remains repository-relative and
portable.
