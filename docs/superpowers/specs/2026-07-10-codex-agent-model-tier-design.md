# Codex Agent Model-Tier Upgrade Design

**Status:** User-approved design; awaiting written-spec review before implementation.

**Scope:** Codex-side agent runtime and workflow only.

## Goal

Migrate HMASD's Codex custom agents to the current GPT-5.6 family while
preserving role boundaries, explicit reasoning settings, and the project's
review and experiment-control gates. Keep exactly one opt-in
`gpt-5.3-codex-spark` role for explicitly requested simple work; make Luna the
default tier for simple work.

## Scope And Boundaries

In scope:

- `.codex/config.toml` and `.codex/agents/*.toml`.
- Codex-facing role-routing and model-tier guidance in `AGENTS.md` and
  `.codex/agents/README.md`.
- Codex-facing dispatch templates and the local static protocol validator when
  they encode the affected role names or model policy.

Out of scope:

- `.claude/**`, `CLAUDE.md`, and
  `docs/subagents/claude-codex-handover-spec.md`.
- Shared memory files, experiment configuration, algorithm code, experiments,
  remote execution, and model API request schemas.
- `multi_agent_v2`, which remains disabled because this runtime exposes the
  v1 Codex subagent surface.

The shared cross-controller model table will intentionally remain unchanged in
this Codex-only pass. A later cross-controller sync must reconcile it before a
Claude-side workflow upgrade.

## Evidence And Migration Policy

The live Codex runtime advertises `gpt-5.6-sol`, `gpt-5.6-terra`, and
`gpt-5.6-luna`; the current project role profiles remain pinned to GPT-5.5,
GPT-5.4, GPT-5.4-mini, or Spark. Official migration guidance requires a
role-aware migration, not a blind string replacement. Therefore:

- Preserve each role's current reasoning effort unless a stronger safety or
  reliability reason is stated below.
- Do not make `max`, `ultra`, Pro mode, programmatic tool calling, or API
  multi-agent beta a default workflow behavior.
- Keep the current literal `service_tier = "fast"` on the three existing
  priority roles. Current config guidance maps that legacy value to priority
  request semantics, so changing the literal is unnecessary migration risk.
- Keep `multi_agent = true`, `multi_agent_v2 = false`, `max_threads = 6`, and
  `max_depth = 1` unchanged.

## Target Role Map

| Role | Target model | Effort | Default routing |
| --- | --- | --- | --- |
| `codebase-scout` | `gpt-5.6-luna` | low | Default for bounded read-only mapping. |
| `simple-patcher` | `gpt-5.6-luna` | low | Default for trivial, single-file, non-core edits. |
| `test-runner` | `gpt-5.6-luna` | low | Default for focused assigned tests and failure capture. |
| `SparkImplementer` | `gpt-5.3-codex-spark` | low | Explicit-only legacy exception for small, non-core work. |
| `TerraImplementer` (new) | `gpt-5.6-terra` | high | Medium-complexity, bounded multi-file non-core implementation. |
| `ImplementationReviewerFast` | `gpt-5.6-terra` | medium | Small isolated mechanical-diff review. |
| `ExpManager` | `gpt-5.6-terra` | medium | Experiment operations and factual records. |
| `ExternalReviewManager` | `gpt-5.6-terra` | medium | Raw external-review archiving and handoffs. |
| `LongTimeMemoryManager` | `gpt-5.6-terra` | high | Memory-only consistency and archive work. |
| `ResultAnalyst` | `gpt-5.6-terra` | high | Bounded, error-sensitive metric and gate extraction. |
| `PlanImplementer` | `gpt-5.6-sol` | high | Accepted-plan core implementation. |
| `ImplementationReviewer` | `gpt-5.6-sol` | high | Standard nontrivial review. |
| `WorkflowAuditor` | `gpt-5.6-sol` | high | Workflow/configuration consistency audit. |
| `PlanImplementerFrontier` | `gpt-5.6-sol` | xhigh | Rare core implementation requiring judgment while editing. |
| `ImplementationReviewerFrontier` | `gpt-5.6-sol` | xhigh | High-risk and final whole-branch review. |

## Routing Rules

1. Luna is the default simple-task tier. It is selected for read-only mapping,
   focused test execution, and trivial one-file mechanical patches. Do not route
   a simple task to Terra merely because it writes a file.
2. `SparkImplementer` is not a default or cost-fallback role. Its dispatch brief
   must contain `Legacy Spark opt-in: explicitly requested` and must limit the
   work to simple, non-core files. A missing opt-in is a routing error; select
   Luna or Terra instead.
3. `TerraImplementer` is the medium-complexity non-core tier. It owns bounded
   multi-file mechanical work such as coordinated runner/package changes,
   manifests plus their consumers, specified cross-file field propagation, and
   non-core tests that require consistency across files. It is not the default
   simple-task route and must stop and escalate at core algorithm or numerical
   semantics.
4. Sol remains the floor for core algorithm implementation and quality-critical
   review. Existing task-review and final-review gates do not change.
5. An `NEEDS_CONTEXT` or `BLOCKED` result never authorizes an automatic model
   downgrade or Spark fallback. The controller must change context, scope,
   owner, or plan under the existing no-blind-retry rule.

### Task-Size Classifier

- Simple and bounded: Luna by default.
- Medium-complexity and non-core, especially multi-file consistency work: Terra.
- Core algorithm or quality-critical review: Sol.
- Explicit user/controller request for the legacy Spark exception: Spark only
  within its simple, non-core scope.

## Planned File Changes

1. Register `TerraImplementer` in `.codex/config.toml` and replace the
   descriptions that make `SparkImplementer` the default mechanical worker.
2. Update all existing `.codex/agents/*.toml` model values and reasoning
   efforts to the table above; add `terra-implementer.toml`; narrow
   `spark-implementer.toml` to the explicit-only exception.
3. Update `AGENTS.md` and `.codex/agents/README.md` so role routing, model
   floors, reviewer tiers, and reload instructions match the new policy.
   Preserve unrelated uncommitted content in `AGENTS.md`.
4. Update Codex-facing dispatch templates to include `TerraImplementer` and the
   required Spark opt-in line, while retaining the mandatory dispatch brief and
   terminal-status contracts.
5. Extend `scripts/validate_hmasd_subagent_protocol.py` with an exact expected
   model/effort profile map and a guard that permits Spark only for
   `SparkImplementer`.

## Validation And Reload

Static validation after implementation:

1. Parse every TOML profile through `tomllib`.
2. Run `python scripts/validate_hmasd_subagent_protocol.py`.
3. Check the diff for whitespace errors and search active Codex profile files
   for unexpected old model names.
4. Verify every config registration points to an existing TOML profile and that
   every expected profile has an explicit model and effort.

Runtime validation is a separate post-restart gate: start a fresh Codex session
or restart the app, inspect the `spawn_agent` role schema, and confirm that the
roles resolve to the target GPT-5.6 model/effort values. The current session
will continue to expose the old locked role profiles and cannot prove a hot
reload.

## Risks And Mitigations

- Role config may not reload in the active session: require fresh-session
  schema verification and do not claim runtime migration before that check.
- A Spark name can accidentally attract default routing: make the opt-in phrase
  mandatory in both documentation and the profile instructions, and use a
  validator check.
- Shared Claude/Codex docs can drift: leave them untouched by user direction
  and record their later reconciliation as an explicit residual task.
- Model migration must not weaken algorithm governance: retain the current
  core/non-core boundary, model floors, review gates, and no-fallback rule.
