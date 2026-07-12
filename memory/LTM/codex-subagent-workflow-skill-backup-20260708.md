---
name: codex-subagent-workflow
description: Use when configuring, auditing, or repairing Codex project subagents, project memory entrypoints, main-controller protocols, official custom-agent settings, model settings, handoff boundaries, or subagent lifecycle cleanup.
---

# Codex Subagent Workflow

## Overview

This skill is a Codex adapter for Superpowers-style subagent work. It does not
replace active Superpowers workflow skills. When a Superpowers skill is active,
follow that skill's process shape first and use this skill only for Codex
project-local custom-agent setup, role mapping, runtime settings, memory hooks,
and lifecycle cleanup.

Source-of-truth order:

1. The user's current explicit request.
2. The active Superpowers skill body, when one is being used.
3. Project `AGENTS.md` and `.codex/agents/README.md`.
4. This skill's Codex adapter rules.

Core principle: the active Codex session is the controller; subagents are
bounded workers. Delegating memory, experiments, review, or evidence extraction
does not delegate project governance.

## Required Superpowers Background

When doing implementation-plan execution or multi-agent investigation, use the
relevant Superpowers skill directly:

- `superpowers:dispatching-parallel-agents` for multiple independent problem
  domains.
- `superpowers:subagent-driven-development` for same-session execution of an
  implementation plan with task briefs, reports, review packages, progress
  ledger, status handling, and review loop.
- `superpowers:executing-plans` for inline execution when subagent-driven
  development is not being used.
- `superpowers:requesting-code-review` for broad code-review handoffs.
- `superpowers:writing-skills` before editing this or any other skill.

This skill must not restate those workflows as a competing procedure. It should
only explain how HMASD maps those workflows onto Codex custom agents and project
memory boundaries.

## Adapter Responsibilities

Use this skill to configure or audit Codex-specific pieces that Superpowers does
not know about:

- project-local `.codex/config.toml` and `.codex/agents/*.toml` files;
- explicit model, reasoning, sandbox, approval, nickname, and supported service
  tier settings;
- no built-in role fallback when custom agents are unavailable;
- main-controller ownership and subagent lifecycle cleanup;
- HMASD role mapping for Superpowers handoffs;
- project memory hooks and LongTimeMemoryManager boundaries;
- ExpManager, ResultAnalyst, ExternalReviewManager, and WorkflowAuditor role
  boundaries;
- validation that the official Codex config has loaded.

Do not use this skill to override an active Superpowers execution loop, review
loop, task-brief format, review-package contract, or blocked-status handling.

## Required Files

For a project-local setup, create or audit:

- `AGENTS.md`: project-level Codex entrypoint.
- `.codex/config.toml`: official Codex project config. For multi-agent v2, keep
  it minimal: enable `multi_agent` and `multi_agent_v2`; do not list role-to-file
  mappings here.
- `.codex/agents/<role>.toml`: official Codex custom agent file.
- `.codex/agents/README.md`: controller, spawn, lifecycle, and handoff protocol.
- `memory/CURRENT_WORK.md`: compact current state and workflow pointers.
- `memory/LTM/`: long-term archive; do not load by default.

Do not use `.claude/` for Codex-only configuration.

## First-Read Contract

Make `AGENTS.md` tell future Codex sessions to read, in order:

1. `.codex/config.toml`
2. `.codex/agents/README.md`
3. `memory/CURRENT_WORK.md`
4. `memory/ALGORITHM_PRINCIPLES.md`
5. `memory/IMPLEMENTATION_PLAN.md`
6. `memory/ExpRecord.md`

Also add `AGENTS.md` and `.codex/config.toml` as pointers in
`memory/CURRENT_WORK.md`, so memory-first continuations find the controller
protocol.

## Official Custom Agent Contract

Official custom agent files must define `name`, `description`, and
`developer_instructions`. Optional runtime fields such as `model`,
`model_reasoning_effort`, `sandbox_mode`, `approval_policy`,
`nickname_candidates`, `service_tier`, `mcp_servers`, and `skills.config` can be
set there so subagents do not silently inherit unsuitable defaults.

Use a minimal project `.codex/config.toml` for multi-agent v2:

```toml
[features]
multi_agent = true
multi_agent_v2 = true
```

Do not add legacy role mappings such as
`[agents."PlanImplementer"] config_file = ...` under multi-agent v2; custom
agents are discovered from `.codex/agents/*.toml`.

Codex loads project-scoped `.codex/` config only for trusted projects. Plan for
a new session or app restart after changing project config or custom agent
files. In a fresh session, force tool discovery if needed with a `tool_search`
query for project custom agents, then inspect the returned `spawn_agent` schema.
The setup is loaded only if the schema lists the project custom roles, not
merely built-ins.

## No Fallback Policy

Do not create or maintain a project `manifest.yaml` fallback. The official
runtime source is minimal `.codex/config.toml` feature flags plus
`.codex/agents/*.toml` standalone agent files.

Spawn project subagents only by official custom agent name. If a required custom
agent is not exposed by the current `spawn_agent` schema, stop delegation and
report a config-loading problem.

The usual fixes are trusting the project, starting a new Codex session,
restarting the app or IDE extension, or repairing `.codex/config.toml` / the
role TOML file. Do not use built-in `worker`, `explorer`, or `default` as a
project-role substitute.

Superseded note (2026-07-08): this backup is not an active skill. Current
project rules use `PlanImplementer` with `gpt-5.5` high reasoning for
accepted-plan implementation and reserve `PlanImplementerFrontier` with
`gpt-5.5` xhigh reasoning for rare bounded implementation tasks that explicitly
require architecture or algorithm judgment while editing. Spark roles should
omit `service_tier` unless the runtime and user explicitly require otherwise.

## Main Controller And Memory Boundary

The active Codex session is the main controller. The controller owns user
communication, task understanding, algorithm discussion, code/execution
decisions, subagent coordination, integration, git boundaries, and final
explanation.

LongTimeMemoryManager is a memory service. It may assess memory impact,
maintain compact memory, and archive records, but it does not own project
governance or execution decisions.

Memory delegation is not governance delegation. The controller may ask
LongTimeMemoryManager to maintain memory, but must not outsource user intent
understanding, algorithm discussion, implementation direction, experiment
interpretation, or user-facing conclusions.

## Lifecycle Protocol

Use this sequence whenever a project subagent is spawned:

1. Spawn the official custom agent by name when it is exposed by the current
   `spawn_agent` schema.
2. If the custom agent name is unavailable, run tool discovery once if it has
   not already happened in this session. If the schema still lacks the custom
   role, stop delegation and surface the config-loading problem instead of using
   a built-in substitute.
3. Capture the returned agent id and nickname.
4. Wait only when the result is needed for the next controller step.
5. Integrate the final result or blocker.
6. Call `close_agent` unless the same subagent immediately needs a follow-up.
7. Before final response, confirm completed subagents are closed.

Close blocked, interrupted, superseded, or abandoned subagents after recording
the blocker and next owner.

## Superpowers Workflow Adapter

When a Superpowers workflow skill is active, do not invent a parallel Codex
workflow. Use the active Superpowers process and map its handoffs onto HMASD
Codex roles:

- Implementer handoffs map to `PlanImplementer` for accepted-plan core code,
  or `PlanImplementerFrontier` only when the task brief justifies bounded xhigh
  architecture/algorithm judgment during implementation.
- Implementer handoffs map to `SparkImplementer` for bounded non-core
  mechanical implementation from a complete task brief.
- Investigation handoffs map to `codebase-scout`, `ResultAnalyst`,
  `ExpManager`, `test-runner`, or `WorkflowAuditor` when their role boundary
  matches the Superpowers task.
- Reviewer handoffs map to `ImplementationReviewer` when the active Superpowers
  skill calls for a review or when the user/project workflow asks for a
  milestone, high-risk, or final review.

For `superpowers:dispatching-parallel-agents`, follow its independent-domain
rule: one focused agent per independent problem domain, dispatched in the same
response when there is no shared state.

For `superpowers:subagent-driven-development`, follow its task brief, report
file, review package, progress ledger, status handling, and review-loop
requirements. This skill supplies Codex custom-agent names and HMASD boundaries;
it does not replace the Superpowers loop.

Superseded note (2026-07-08): review gates are no longer reduced to control
cost. Current project rules keep required task/final reviews and control cost
through reviewer model tiers instead.

## Role Boundaries

- `codebase-scout`: read-only mapping; no edits.
- `simple-patcher`: trivial single-file mechanical fixes only.
- `SparkImplementer`: cost-controlled implementation worker for non-core,
  mechanical tasks from accepted plans or controller-written task briefs.
- `PlanImplementer`: high-tier worker for accepted-plan core implementation
  when a concrete brief makes the handoff worth its communication cost.
- `PlanImplementerFrontier`: xhigh frontier worker for rare bounded core tasks
  that explicitly require architecture or algorithm judgment while editing.
- `ImplementationReviewer`: code review role used when the active workflow or
  user asks for review.
- `test-runner`: focused tests and failure triage.
- `ExpManager`: experiment scripts, packages, launch commands, logs, factual
  `memory/ExpRecord.md` updates, and operational handoffs.
- `ResultAnalyst`: bounded metric extraction, gate tables, anomaly extracts,
  and typical-step comparisons from existing experiment artifacts.
- `ExternalReviewManager`: external model dialogue inbox/archive/index and
  handoffs.
- `LongTimeMemoryManager`: memory-only service for compact memory, principle
  and plan record sync, memory-impact assessment, and LTM archive maintenance.
- `WorkflowAuditor`: read-only audit of Codex subagent TOML, controller
  protocol, workflow docs, model settings, and role-boundary consistency.

Mechanical workers provide facts and handoffs. ExpManager owns experiment operations and factual records. ResultAnalyst owns metric/gate extraction from existing artifacts. LongTimeMemoryManager handles memory impact and archival placement. WorkflowAuditor reports workflow drift only. The main controller owns substantive decisions and user-facing explanation.

## Experiment Evidence Adapter

For ExpManager, prevent context blowups by design. Split experiment work into
atomic phases: package/runner preparation, launch, progress check, operational
extraction, and ExpRecord update. ExpManager should not paste large logs, full
CSVs, traceback clusters, or long command transcripts into chat. It should write
large evidence to run/package-local files such as `runner_status.txt`,
`runner_output.log`, `expmanager_checkpoint.md`, `metric_extract.md`,
`error_extract.md`, or a package handoff, then return only a compact status with
file paths.

For ResultAnalyst, keep analysis bounded and artifact-first. Use it after
artifacts already exist and the user/controller needs metric-heavy gate tables,
typical-step comparisons, or anomaly extracts. It writes large evidence to
run-local files such as `metric_extract.md`, `gate_read.md`, or
`error_extract.md`, returns compact summaries, and leaves experiment launches,
process state, and factual `ExpRecord.md` updates to ExpManager unless the
controller explicitly says otherwise.

Use ExpManager and ResultAnalyst together as a staged evidence workflow:

1. ExpManager prepares the runner, package, command, launch, progress check,
   status files, transcripts, and factual `memory/ExpRecord.md` update when
   experiment state changes.
2. ResultAnalyst reads already-written artifacts such as CSVs, eval rows,
   `runner_status.txt`, `runner_output.log`, manifests, checkpoints, and
   controller-provided gate definitions. It writes large metric evidence to
   run-local extract files.
3. The main controller integrates ExpManager's run-state facts and
   ResultAnalyst's metric/gate evidence, then decides pass/fail/defer,
   acceptance, reward gating, and next action.
4. ExpManager records follow-up factual experiment status only when the
   controller routes that update. LongTimeMemoryManager syncs accepted
   conclusions into compact memory or LTM when project memory should change.

They may run in the same parallel evidence wave only when ResultAnalyst reads
artifacts that already exist and neither agent writes the same run directory,
package path, source file, or `memory/ExpRecord.md` row. If ExpManager is still
creating artifacts, launching a run, or updating the same experiment record, run
the phases sequentially.

## External Review Evidence

ExternalReviewManager records copy-paste Claude, GPT-5.5 Pro, and Gemini review
rounds. It must preserve raw pasted model text in
`memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` before summarizing.

ExternalReviewManager summaries and handoffs are indexes, not evidence.
LongTimeMemoryManager must read the referenced raw archive text before making a
memory update or recommendation from outside advice. If raw text is missing,
ask for recovery or mark the memory update as incomplete rather than promoting
a summary. The main controller owns whether outside advice is accepted,
rejected, deferred, or used for execution.

## Fixed Project Hooks

These hooks require a routing decision; they do not by themselves override an
active Superpowers skill:

- Plan accepted, changed, completed, or abandoned: update memory directly or ask
  LongTimeMemoryManager to sync compact plan/current records and LTM archive
  entries when needed.
- Code changes verified: ask LongTimeMemoryManager to sync memory only if the
  change affects project direction, algorithm behavior, experiment workflow,
  known risks, or next actions.
- Meaningful experiment launch: ask ExpManager for the factual record, command,
  package, and handoff. Ask LongTimeMemoryManager only if the launch changes
  current objective, plan stage, principle state, or archive-worthy context.
- Experiment logs or results reviewed: ExpManager records factual status in
  `memory/ExpRecord.md`; the controller owns interpretation; LongTimeMemoryManager
  syncs accepted conclusions when memory should change.
- External model review text pasted: ExternalReviewManager archives raw text
  first; LongTimeMemoryManager may update memory only after reading the raw
  archive entry.
- Subagent/workflow config changed: consider WorkflowAuditor when changes touch
  multiple protocol files, model settings, role boundaries, or official
  custom-agent runtime behavior.

## Verification Checklist

Before declaring the setup complete:

- `AGENTS.md` exists at project root.
- `.codex/config.toml` exists with minimal v2 feature flags.
- Every official `.codex/agents/*.toml` role has `name`, `description`,
  `developer_instructions`, explicit `model`, `model_reasoning_effort`,
  sandbox, approval, and nicknames.
- The live `spawn_agent` schema exposes project custom roles such as
  `PlanImplementer`, `SparkImplementer`, `ImplementationReviewer`,
  `ExpManager`, `ResultAnalyst`, `ExternalReviewManager`,
  `LongTimeMemoryManager`, `WorkflowAuditor`, `codebase-scout`,
  `simple-patcher`, and `test-runner`.
- There is no project fallback manifest and no built-in project-role fallback.
- README and AGENTS state the active Codex session is the controller.
- README and AGENTS state LTM is memory-only and does not own project
  governance.
- README, AGENTS, and ExpManager TOML include file-based status and
  context-budget rules for long-running or evidence-heavy experiment work.
- Superpowers execution-plan implementation defers process shape to the active
  Superpowers skill while this skill supplies Codex custom-agent mapping,
  runtime settings, lifecycle cleanup, and HMASD boundaries.
- Completed subagents are closed with `close_agent`.
- `memory/CURRENT_WORK.md` points to `AGENTS.md` and `.codex/config.toml`.
- External-review archive templates include a `### Raw Pasted Text` section,
  and LTM instructions require reading it before decisions.
- No legacy attention-pointer semantics are reintroduced.


---

## Backed Up Auxiliary File: agents/openai.yaml

```yaml
interface:
  display_name: "Codex Subagent Workflow"
  short_description: "Configure Codex project subagents and controller lifecycle."
  default_prompt: "Set up or audit Codex project subagents, controller protocol, project memory entrypoints, and lifecycle rules."
```

