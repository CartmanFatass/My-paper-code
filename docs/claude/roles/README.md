# Delegated Roles

Every delegated role on the `Claude` branch runs on the **same model Codex uses**
for the equivalent profile, so the comparison isolates the controller rather than
confounding controller and workers (D10, D11, D13).

These are **not** Claude Task subagents. They are Codex CLI tasks. The
`.claude/agents/*.md` definitions were retired — their `PreToolUse` hooks did not
apply to Codex tasks and would have read as protection that was not there.

## Bindings

| Role | Brief | Model | Effort | Dispatched by | Write |
|---|---|---|---|---|---|
| Project Manager | `project-manager.md` | `gpt-5.6-sol` | xhigh | controller | **yes** |
| Implementer | `implementer.md` | `gpt-5.6-sol` | high | **PM** | inherits PM |
| Reviewer | `reviewer.md` | `gpt-5.6-sol` | xhigh | controller | no |
| Scout | `scout.md` | `gpt-5.6-luna` | medium | controller | no |

Models and efforts are sourced from `.codex/agents/*.toml`. If Codex changes a
binding there, change it here in the same boundary or the comparison silently
stops being controlled.

Two deviations from Codex's org chart, both deliberate:

- **Scout is controller-dispatched.** It cannot be a child: `spawn_agent` accepts
  only `gpt-5.6-sol` and `gpt-5.6-terra`, and Luna is rejected server-side. Luna
  works fine as a top-level task. Platform-forced, not chosen (D12).
- **Reviewer is controller-dispatched.** Codex has the PM spawn it. Here it is
  briefed independently so the audit is not filtered through the party being
  audited, and so read-only is real rather than prompt-text (D13).

There is deliberately **no verifier**. Codex delegates verification to a fourth
profile; this controller keeps it in its own loop (D11). Verification is never
delegated and a worker's claim that tests pass is never evidence.

## Dispatch

```bash
export CODEX_HOME="C:/Users/fires/.codex-claude"
node "$CLAUDE_PLUGIN_ROOT/scripts/codex-companion.mjs" task "<brief + assignment>" \
  --model <model> --effort <effort> [--write]
```

**`CODEX_HOME` must be set on every invocation.** Omitting it silently falls back
to `~/.codex`, which is Codex Desktop's runtime — the other controller's session
state, memories and history. A silent fallback contaminates the comparison and
leaves no trace, so treat an unset `CODEX_HOME` as a dispatch error.

- **Omit `--write` for scout and reviewer.** This maps to a real app-server
  sandbox (`sandbox: write ? "workspace-write" : "read-only"`), so read-only is
  enforced, not merely instructed. Only the PM gets `--write`.
- Send the role brief and the assignment together as the task text. A Codex task
  starts with no repository context and does not read these files on its own.
- One task per assignment. Only the PM may spawn, and only implementers.
- One writer owns a file set at a time; never run two write-capable tasks on the
  same scope.
- After any write-capable run, **check `git status` yourself.** The sandbox
  permits commits; only the assignment text forbids them.

## Sessions

Reuse threads. Do not open a new session per dispatch — context carries across
`--resume-last` (verified: a token stored in one turn was recalled after resume).

| Role | Session policy |
|---|---|
| Project Manager | **One persistent thread per work package.** Record the id in `../SESSION_STATE.md`. |
| Implementer | Lives inside the PM's thread tree. |
| Reviewer | **Always fresh — never resume.** Uncontaminated context is the point. |
| Scout | Fresh. Stateless lookups. |

`--resume-last` resolves the most recent thread **in this repository**, not per
role. Any fresh dispatch becomes "latest", so a scout run after the PM silently
hijacks the next resume.

Every task prints `Resuming thread <id>`. **Verify it against the recorded PM
id.** On mismatch, stop — do not continue into the wrong context. Resume the
intended thread explicitly with `codex exec resume <PM_THREAD_ID>`, accepting
that the raw path loses the plugin's subagent-drain handling, so prefer it only
when no children are expected.

## What the platform does not give us

`spawn_agent`'s entire schema is `task_name`, `message`, `model?`,
`reasoning_effort?`, `fork_turns?`. There is **no `agent_type`**, so the
`developer_instructions`, `sandbox_mode` and `approval_policy` in
`.codex/agents/*.toml` are unreachable from the CLI path. Role identity is
prompt-deep only, and a spawned child inherits its parent's write capability.

`fork_turns` lets a child inherit the parent's context. Useful for handing an
implementer the PM's reasoning; do not use it for anything meant to be
independent.

## Assignment contents

An assignment is incomplete without all of: the outcome, the exact file scope,
what is explicitly out of scope, the acceptance condition, and the execution
environment facts (interpreter path, backend, test command).
