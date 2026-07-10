# Codex Role-First Subagent Routing Design

**Status:** User-approved design; awaiting written-spec review before implementation.

**Scope:** Codex-side custom-agent configuration and workflow only.

## Goal

Replace HMASD's model-prefixed Codex subagent identities with stable semantic
roles. Keep role definitions independent from routine model selection so the
controller can choose the appropriate GPT-5.6 route for each dispatch without
duplicating roles for every model and reasoning combination.

The target defaults are:

- Controller: selected in the Codex GUI or session; project config does not
  pin its model or reasoning effort.
- Simple work: `gpt-5.6-luna` with medium reasoning.
- Ordinary work: `gpt-5.6-sol` with high reasoning.
- Frontier work: `gpt-5.6-sol` with max reasoning.
- Low-risk support work: may use Codex automatic routing when the dispatch is
  explicitly marked `auto/unpinned`.
- Cost-controlled legacy work: `SparkExplicitSimplePatcher` remains fixed to
  `gpt-5.3-codex-spark` and requires literal opt-in.

This design supersedes the model-prefixed role naming and fully pinned model
map proposed in `2026-07-10-codex-agent-model-tier-design.md`. The older file
remains historical context and is not an active implementation target.

## Scope And Boundaries

In scope:

- `.codex/config.toml` and `.codex/agents/*.toml`.
- Codex-facing role and routing rules in `AGENTS.md` and
  `.codex/agents/README.md`.
- Codex dispatch templates and the local static subagent protocol validator
  when they encode affected role names or routing policy.
- Static validation and fresh-session runtime loading checks.

Out of scope:

- `.claude/**`, `CLAUDE.md`, and Claude-side role configuration.
- Shared project memory, experiment records, experiment code, algorithm code,
  remote execution, and experiment launch or analysis.
- Performance benchmarking or model-by-effort evaluation profiles.
- Pinning the main controller's model in repository configuration.
- Enabling `multi_agent_v2` or changing the existing concurrency limits.

## Architecture

### Stable Semantic Roles

Each `.codex/agents/*.toml` profile defines a stable role identity, role
instructions, sandbox boundary, and task constraints. Except for the explicit
Spark exception, semantic role profiles omit `model`,
`model_reasoning_effort`, and fixed `service_tier` values.

This separation has two consequences:

1. Role names continue to describe ownership after the available model list or
   preferred model tier changes.
2. One role can be dispatched with an explicit route or can inherit Codex's
   automatic model selection when the task is eligible.

`.codex/config.toml` registers the semantic roles and preserves the documented
agent concurrency settings. It does not set top-level `model` or
`model_reasoning_effort`, because the user selects the controller model in the
GUI or active session.

### Target Role Catalog

| Semantic role | Responsibility | Default class |
| --- | --- | --- |
| `CodebaseScout` | Read-only codebase mapping and bounded discovery | Simple |
| `SimplePatcher` | Trivial, single-file, mechanical, non-core edits | Simple |
| `TestRunner` | Focused tests, failure capture, and bounded triage | Simple |
| `FastReviewer` | Small isolated mechanical-diff review | Simple |
| `Implementer` | Bounded medium-complexity, multi-file, non-core implementation | Ordinary |
| `PlanImplementer` | Accepted-plan core implementation | Ordinary |
| `ImplementationReviewer` | Standard nontrivial implementation review | Ordinary |
| `ExpManager` | Experiment operations and factual run-state records | Ordinary |
| `ResultAnalyst` | Bounded metric, gate, and anomaly extraction | Ordinary |
| `ExternalReviewManager` | External-review archiving and handoff preparation | Ordinary |
| `LongTimeMemoryManager` | Memory-only consistency and archive maintenance | Ordinary |
| `WorkflowAuditor` | Read-only workflow and configuration consistency audit | Ordinary |
| `PlanImplementerFrontier` | Rare core implementation requiring architecture or algorithm judgment while editing | Frontier |
| `ImplementationReviewerFrontier` | High-risk, architecture, concurrency, contract, and final whole-branch review | Frontier |
| `SparkExplicitSimplePatcher` | Explicit cost-controlled trivial non-core patching | Explicit Spark |

The migration removes the old `Luna*`, `Terra*`, and `Sol*` role aliases. Model
families remain routing choices rather than role identity, with Spark retained
in its name because its explicit-only fixed-model behavior is the purpose of
that exception.

## Routing Policy

### Default Routes

The controller first selects the semantic role and then selects the execution
route:

| Task class | Route | Reasoning | Typical roles |
| --- | --- | --- | --- |
| Simple | `gpt-5.6-luna` | medium | `CodebaseScout`, `SimplePatcher`, `TestRunner`, `FastReviewer` |
| Ordinary | `gpt-5.6-sol` | high | `Implementer`, `PlanImplementer`, `ImplementationReviewer`, experiment and memory service roles |
| Frontier | `gpt-5.6-sol` | max | `PlanImplementerFrontier`, `ImplementationReviewerFrontier` |
| Eligible support | `auto/unpinned` | selected by Codex | Low-risk read-only scans, document organization, metadata extraction, and similarly bounded support work |
| Explicit cost option | `gpt-5.3-codex-spark` | profile-fixed | `SparkExplicitSimplePatcher` only |

These are workflow defaults, not role-profile pins. The dispatch brief records
the selected explicit route or the literal `auto/unpinned` choice. An explicit
route must be applied through the runtime dispatch surface supported by the
active Codex version; unsupported overrides are errors, not permission to
silently substitute another model.

### Auto-Routing Eligibility

Automatic routing is allowed only when all of the following hold:

- The task is low-risk and bounded.
- The task does not modify core algorithm or quality-critical numerical code.
- The task is not a final review, architecture review, high-risk review, or
  shared-state/API/data-contract review.
- The dispatch brief explicitly says `Model route: auto/unpinned`.
- The role's normal ownership and sandbox boundaries still apply.

If an auto-routed agent encounters core semantics, risky architecture, final
review scope, or a larger ownership boundary than the brief permits, it must
return `BLOCKED`. The controller then creates a revised dispatch using explicit
Sol High or Sol Max. It must not continue under the auto route.

### Core And Review Floors

Core algorithm and quality-critical numerical implementation remain restricted
to the controller, `PlanImplementer` on explicit Sol High, or
`PlanImplementerFrontier` on explicit Sol Max. Luna, Terra selected by an
automatic router, and Spark are not valid core implementation routes.

Task reviews remain mandatory for subagent-driven implementation. Small,
isolated mechanical diffs may use `FastReviewer` on Luna Medium. Standard
multi-file or judgment-heavy reviews use `ImplementationReviewer` on Sol High.
Architecture, high-risk, concurrency, shared-state, API/data-contract, and
final whole-branch reviews use `ImplementationReviewerFrontier` on Sol Max.

### Spark Exception

`SparkExplicitSimplePatcher` is the only profile that retains an explicit
`model` and `model_reasoning_effort`. Its dispatch brief must contain exactly:

```text
Legacy Spark opt-in: explicitly requested
```

Spark is never an automatic fallback, never a response to an unavailable
Luna/Sol route, and never eligible for core, numerical, multi-file, or review
work. Without the opt-in phrase it returns `NEEDS_CONTEXT` without editing.

## Dispatch Contract

The existing Mandatory Dispatch Brief Gate remains in force. Each dispatch
adds one routing field:

```text
Model route: gpt-5.6-luna / medium
```

or:

```text
Model route: gpt-5.6-sol / high
Model route: gpt-5.6-sol / max
Model route: auto/unpinned
```

The brief still names the semantic role, TOML profile, requirements source,
owned and forbidden scope, output path, checks, dependencies, terminal status,
next owner, and lifetime policy. For Spark it also includes the required
literal opt-in.

The controller records the actual runtime route returned by the agent surface
when available. A mismatch between an explicit requested route and the actual
route is a concern requiring controller action; it is not silently accepted.

## Configuration Migration

Implementation will perform one coordinated Codex-side migration:

1. Create or rename the fourteen non-Spark TOML profiles to semantic filenames
   and semantic `name` values. Remove their model, reasoning, and service-tier
   pins while preserving role instructions and sandbox boundaries.
2. Retain `spark-explicit-simple-patcher.toml` with its fixed Spark model,
   reasoning setting, and explicit-opt-in guard.
3. Replace `.codex/config.toml` registrations with exactly the fifteen target
   semantic roles. Preserve `multi_agent = true`, `multi_agent_v2 = false`,
   `max_threads = 6`, `max_depth = 1`, and
   `job_max_runtime_seconds = 1800`.
4. Do not add top-level controller model or reasoning settings.
5. Update active Codex documentation, dispatch templates, and validation rules
   to use semantic names and the routing policy in this specification.
6. Remove old model-prefixed registrations and profile files so stale aliases
   cannot be dispatched accidentally.

The migration must preserve unrelated uncommitted work. It must not edit
`.claude/**`, `CLAUDE.md`, shared memory, experiment artifacts, or algorithm
sources.

## Failure Handling

- Semantic role absent from the runtime schema: stop delegation, report that
  project configuration is not loaded, and require project trust plus a fresh
  session or app restart. Do not use a built-in role as fallback.
- Explicit runtime model/effort override unsupported: return or report
  `BLOCKED`; do not silently inherit, downgrade, or substitute.
- Auto-routed task expands into core or high-risk scope: return `BLOCKED` and
  re-dispatch with explicit Sol High or Sol Max.
- Agent returns `NEEDS_CONTEXT` or `BLOCKED`: follow the existing status
  protocol; do not retry unchanged and do not fall back to Spark.
- Old model-prefixed role still appears after migration: treat runtime loading
  as unverified until a clean restart exposes only semantic names.
- Spark dispatch lacks its opt-in phrase: the Spark agent performs no edit and
  returns `NEEDS_CONTEXT`.

## Verification

### Static Checks

1. Parse `.codex/config.toml` and every `.codex/agents/*.toml` with `tomllib`.
2. Verify config registers exactly the fifteen target semantic roles and every
   registration points to an existing profile.
3. Verify the fourteen non-Spark profiles omit `model`,
   `model_reasoning_effort`, and fixed `service_tier`.
4. Verify `SparkExplicitSimplePatcher` alone pins
   `gpt-5.3-codex-spark` and contains the explicit-opt-in guard.
5. Verify `multi_agent = true`, `multi_agent_v2 = false`,
   `max_threads = 6`, `max_depth = 1`, and
   `job_max_runtime_seconds = 1800` remain unchanged.
6. Verify project config has no top-level controller `model` or
   `model_reasoning_effort`.
7. Run `python scripts/validate_hmasd_subagent_protocol.py` and update its
   assertions to match this specification.
8. Search active Codex configuration and workflow documents for obsolete
   model-prefixed role references, allowing only historical specifications or
   migration notes that are clearly marked historical.
9. Run `git diff --check` and confirm no file outside the approved Codex scope
   was changed by the migration.

### Fresh-Session Runtime Checks

Project-scoped custom-agent configuration is not assumed to hot reload. After
implementation, start a fresh Codex session or restart the app and verify that
the runtime role schema exposes exactly the semantic names.

Run two bounded read-only smoke dispatches:

1. `CodebaseScout` with explicit `gpt-5.6-luna` / medium.
2. An eligible read-only semantic role with `Model route: auto/unpinned`.

The smokes verify loading and route behavior only. They do not benchmark
quality, latency, token use, or cost. Spark does not need a smoke dispatch; its
static configuration and opt-in guard are sufficient for this migration.

## Documentation Basis

This design follows the current official Codex documentation that custom-agent
`model` and `model_reasoning_effort` settings are optional, that omitted values
can inherit or be selected for the task, and that project config is loaded from
trusted `.codex/config.toml` files:

- [Choosing Sol, Terra, and Luna](https://learn.chatgpt.com/docs/models#choosing-sol-terra-and-luna)
- [Custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)
- [Choosing models and reasoning](https://learn.chatgpt.com/docs/agent-configuration/subagents#choosing-models-and-reasoning)
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml)
- [Project config files](https://learn.chatgpt.com/docs/config-file/config-advanced#project-config-files-codexconfigtoml)

## Acceptance Criteria

The implementation is complete only when static checks pass, a fresh runtime
exposes semantic role names, explicit Luna Medium and auto/unpinned read-only
smokes succeed, and no unrelated files were included in the migration. The
controller remains GUI-selected, ordinary work defaults to explicit Sol High,
frontier work defaults to explicit Sol Max, and Spark remains explicit-only.
