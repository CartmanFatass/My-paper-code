# Claude runtime

@AGENTS.md

The Claude session is the DM for one direction at a time (constitution section 2): no Root/DM
split. Research work uses the `hmasd-research-hub` skill. The session may implement, launch and
observe directly. When useful it delegates a bounded task to `hmasd-implementer` (Opus, high effort),
`hmasd-experiment-operator` or `hmasd-experiment-tracker`; it accepts the returned work.
The tracker observes one bounded window and returns facts; `hmasd-pro-transport`
sends one committed Pro question and collects the answer; `hmasd-reviewer` reviews core changes.

Interpreters: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (3.10, torch, pytest) and
`C:/Users/fires/.conda/envs/hmasd-science-tools/python.exe` (3.11, analysis; also runs
`tools/publish_claude_control.py`). Never install into either.

Shared methods live in `.agents/skills`; role bodies come from `.codex/agents` and the
explicit adapters in `tools/publish_claude_control.py`. Claude agent frontmatter (including
model/tools) is directly maintained; generated bodies are not. Republish after source changes;
`--check` reports differences and unexpected HMASD outputs, never deletes files automatically.

Root remains the shared main/RESEARCH integrator while coordinating Codex. The Claude session
publishes its direction branch and returns facts, taking shared integration only with no
acting Root or explicit handover and a checked writer boundary. Use real native returns;
unavailable cross-runtime messaging is a pending integration fact, not a fabricated tool.
On a control revision, reread affected methods at a safe boundary and report actual adoption;
never relaunch or resend accepted/uncertain operations to refresh a session.

Opus/high is the requested Implementer setting, not evidence of effective native effort.
Read-only role text and Bash availability do not establish a Codex-equivalent sandbox. Inspect
actual runtime settings when validating a migration; preserve an unverified status if they
cannot be observed. Do not invent an unsupported frontmatter field or call source drift a
live-runtime check. This is not a new check before every research run.

Non-direction deliverables, when needed, use `docs/Claude_docs/<category>/`.
