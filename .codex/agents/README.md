# Codex Project Agents

This directory is for HMASD project-local Codex subagent profiles.
It is intentionally separate from `.claude/` and is the source of truth for
Codex subagent routing in this project.

Use `manifest.yaml` as the index. The user's requested model alias is
`gpt5.3-spark`; the Codex subagent tool currently exposes that model as
`gpt-5.3-codex-spark`.

Each profile frontmatter includes:

- `model` and `requested_model_alias`.
- `model_reasoning_effort` for Codex config naming.
- `reasoning_effort` for `spawn_agent` parameter naming.
- `service_tier`.
- `sandbox_mode`.
- `approval_policy`.
- `nickname_candidates`.

When spawning a Codex subagent, use the closest built-in `agent_type`:

- `explorer` with `codebase-scout.md`.
- `worker` with `simple-patcher.md`.
- `default` or `worker` with `test-runner.md`.
- `worker` with `exp-manager.md` for experiment scripts, packages, commands,
  logs, factual `memory/ExpRecord.md` updates, and structured handoffs to
  LongTimeMemoryManager.
- `worker` with `external-review-manager.md` for copy-paste Claude/GPT-5.5
  Pro/Gemini review rounds, inbox/archive files, and structured handoffs to
  LongTimeMemoryManager.
- `worker` with `long-time-memory-manager.md` for compact current work,
  principles, plans, project-level interpretation, and LTM archive decisions.
