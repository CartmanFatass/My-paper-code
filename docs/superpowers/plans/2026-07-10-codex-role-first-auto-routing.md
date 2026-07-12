# Codex Role-First Auto-Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace model-prefixed Codex custom-agent identities with fifteen stable semantic roles while keeping routine model selection in the dispatch layer and preserving Spark as the sole fixed explicit-only exception.

**Architecture:** Role TOMLs and `.codex/config.toml` define semantic ownership, permissions, and registration only. The controller records `gpt-5.6-luna / medium`, `gpt-5.6-sol / high`, `gpt-5.6-sol / max`, or `auto/unpinned` in each dispatch brief; only `SparkExplicitSimplePatcher` pins a model inside its TOML. A static validator enforces the registry, optional-model contract, routing documentation, and unchanged runtime limits, while a fresh Codex session performs two read-only loading smokes.

**Tech Stack:** TOML, Markdown, Python 3 `tomllib`, PowerShell, Git, Codex project-scoped custom agents.

## Global Constraints

- Codex-side files only: do not edit `.claude/**`, `CLAUDE.md`, shared memory, experiment records, experiment artifacts, algorithm code, or remote-run assets.
- Do not add top-level `model` or `model_reasoning_effort` to `.codex/config.toml`; the controller model remains GUI/session selected.
- Preserve `multi_agent = true`, `multi_agent_v2 = false`, `max_threads = 12`, `max_depth = 1`, and `job_max_runtime_seconds = 1800`. The original value `6` was superseded by the user-approved cache-aware lifetime policy on 2026-07-11.
- The fourteen non-Spark role profiles omit `model`, `model_reasoning_effort`, and `service_tier`.
- `SparkExplicitSimplePatcher` remains fixed to `gpt-5.3-codex-spark` with low reasoning and requires `Legacy Spark opt-in: explicitly requested`.
- Default routing is simple -> `gpt-5.6-luna / medium`, ordinary -> `gpt-5.6-sol / high`, frontier -> `gpt-5.6-sol / max`; bounded low-risk support work may use `auto/unpinned` only when the dispatch says so explicitly.
- Core algorithm and quality-critical numerical implementation may use only the controller, `PlanImplementer` on Sol High, or `PlanImplementerFrontier` on Sol Max.
- Final whole-branch review always uses `ImplementationReviewerFrontier` on Sol Max.
- Preserve unrelated working-tree edits and stage only files owned by the current task. Do not stage `.claude/**`, `memory/**`, or unrelated project documents.
- Project custom-agent config does not hot reload reliably; dynamic acceptance requires a fresh Codex session or app restart after static migration.

---

## File Structure

**Runtime registry and role profiles**

- Modify: `.codex/config.toml` - register exactly fifteen semantic role names and preserve runtime feature/concurrency settings.
- Rename and modify: fourteen `.codex/agents/*.toml` files - retain role behavior and sandbox boundaries while removing model-family identity and model pins.
- Modify: `.codex/agents/spark-explicit-simple-patcher.toml` - retain the fixed Spark exception and update references to semantic escalation owners.

**Controller and dispatch policy**

- Modify: `AGENTS.md` - replace model-prefixed role routing with semantic roles plus dispatch-time route selection.
- Modify: `.codex/agents/README.md` - document the same runtime contract, role catalog, routing floors, reload behavior, and failure handling.
- Modify: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` - rename templates and add an explicit `Model route:` field to every dispatch block.

**Validation**

- Modify: `scripts/validate_hmasd_subagent_protocol.py` - enforce the semantic profile registry, optional model fields, Spark exception, unchanged runtime settings, no controller pin, routing text, and obsolete-name rejection.

No new runtime source, experiment, or memory files are created.

---

### Task 1: Migrate The Runtime Registry And Role Profiles

**Files:**
- Modify: `scripts/validate_hmasd_subagent_protocol.py`
- Modify: `.codex/config.toml`
- Rename: `.codex/agents/luna-codebase-scout.toml` -> `.codex/agents/codebase-scout.toml`
- Rename: `.codex/agents/luna-simple-patcher.toml` -> `.codex/agents/simple-patcher.toml`
- Rename: `.codex/agents/luna-test-runner.toml` -> `.codex/agents/test-runner.toml`
- Rename: `.codex/agents/terra-implementer.toml` -> `.codex/agents/implementer.toml`
- Rename: `.codex/agents/terra-fast-reviewer.toml` -> `.codex/agents/fast-reviewer.toml`
- Rename: `.codex/agents/terra-exp-manager.toml` -> `.codex/agents/exp-manager.toml`
- Rename: `.codex/agents/terra-result-analyst.toml` -> `.codex/agents/result-analyst.toml`
- Rename: `.codex/agents/terra-external-review-manager.toml` -> `.codex/agents/external-review-manager.toml`
- Rename: `.codex/agents/terra-long-time-memory-manager.toml` -> `.codex/agents/long-time-memory-manager.toml`
- Rename: `.codex/agents/sol-workflow-auditor.toml` -> `.codex/agents/workflow-auditor.toml`
- Rename: `.codex/agents/sol-plan-implementer.toml` -> `.codex/agents/plan-implementer.toml`
- Rename: `.codex/agents/sol-implementation-reviewer.toml` -> `.codex/agents/implementation-reviewer.toml`
- Rename: `.codex/agents/sol-plan-implementer-frontier.toml` -> `.codex/agents/plan-implementer-frontier.toml`
- Rename: `.codex/agents/sol-implementation-reviewer-frontier.toml` -> `.codex/agents/implementation-reviewer-frontier.toml`
- Modify: `.codex/agents/spark-explicit-simple-patcher.toml`

**Interfaces:**
- Consumes: the approved role catalog and routing policy in `docs/superpowers/specs/2026-07-10-codex-role-first-auto-routing-design.md`.
- Produces: fifteen registered runtime role names and `EXPECTED_PROFILES: dict[str, str]` mapping each semantic name to one TOML filename.

- [ ] **Step 1: Change the validator contract first**

Replace the profile identity constants with the exact semantic mapping below. Split common fields from the Spark-only model fields so ordinary profiles are required to omit model pins.

```python
COMMON_RUNTIME_FIELDS = (
    "name",
    "description",
    "sandbox_mode",
    "approval_policy",
    "nickname_candidates",
    "developer_instructions",
)

EXPECTED_PROFILES = {
    "CodebaseScout": "codebase-scout.toml",
    "SimplePatcher": "simple-patcher.toml",
    "TestRunner": "test-runner.toml",
    "FastReviewer": "fast-reviewer.toml",
    "Implementer": "implementer.toml",
    "PlanImplementer": "plan-implementer.toml",
    "ImplementationReviewer": "implementation-reviewer.toml",
    "ExpManager": "exp-manager.toml",
    "ResultAnalyst": "result-analyst.toml",
    "ExternalReviewManager": "external-review-manager.toml",
    "LongTimeMemoryManager": "long-time-memory-manager.toml",
    "WorkflowAuditor": "workflow-auditor.toml",
    "PlanImplementerFrontier": "plan-implementer-frontier.toml",
    "ImplementationReviewerFrontier": "implementation-reviewer-frontier.toml",
    "SparkExplicitSimplePatcher": "spark-explicit-simple-patcher.toml",
}

OBSOLETE_AGENT_NAMES = {
    "LunaCodebaseScout",
    "LunaSimplePatcher",
    "LunaTestRunner",
    "TerraImplementer",
    "TerraFastReviewer",
    "TerraExpManager",
    "TerraResultAnalyst",
    "TerraExternalReviewManager",
    "TerraLongTimeMemoryManager",
    "SolWorkflowAuditor",
    "SolPlanImplementer",
    "SolImplementationReviewer",
    "SolPlanImplementerFrontier",
    "SolImplementationReviewerFrontier",
}

REQUIRED_REVIEWER_NAMES = {
    "FastReviewer",
    "ImplementationReviewer",
    "ImplementationReviewerFrontier",
}
```

Update `check_toml()` to enforce common fields:

```python
for field in COMMON_RUNTIME_FIELDS:
    if field not in data:
        raise AssertionError(f"{path} missing runtime field: {field}")
```

Inside the existing `for name, filename in EXPECTED_PROFILES.items()` loop in
`check_agent_identity_contract()`, enforce the Spark exception and the
non-Spark omission contract:

```python
if name == "SparkExplicitSimplePatcher":
    if data.get("model") != "gpt-5.3-codex-spark":
        raise AssertionError(f"{profile_path} must pin gpt-5.3-codex-spark")
    if data.get("model_reasoning_effort") != "low":
        raise AssertionError(f"{profile_path} must use low reasoning")
    if "Legacy Spark opt-in: explicitly requested" not in instructions:
        raise AssertionError(f"{profile_path} missing explicit Legacy Spark opt-in contract")
else:
    forbidden_pins = sorted(
        field for field in ("model", "model_reasoning_effort", "service_tier")
        if field in data
    )
    if forbidden_pins:
        raise AssertionError(f"{profile_path} pins routing fields: {forbidden_pins}")
```

Add config guards after loading `.codex/config.toml`:

```python
features = config.get("features", {})
if features.get("multi_agent") is not True:
    raise AssertionError("multi_agent must remain true")
if features.get("multi_agent_v2") is not False:
    raise AssertionError("multi_agent_v2 must remain false")
for field, expected in (
    ("max_threads", 12),
    ("max_depth", 1),
    ("job_max_runtime_seconds", 1800),
):
    if raw_agents.get(field) != expected:
        raise AssertionError(f"agents.{field} must remain {expected}")
for field in ("model", "model_reasoning_effort"):
    if field in config:
        raise AssertionError(f"project config must not pin controller {field}")
```

- [ ] **Step 2: Run the validator and confirm the new contract fails against old registrations**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected: exit code `1` with an agent registry mismatch naming missing semantic roles and unexpected model-prefixed roles.

- [ ] **Step 3: Rename profiles and rewrite role metadata**

Use `git mv` for the fourteen tracked profiles. In every renamed profile:

- Set `name` to the semantic role from `EXPECTED_PROFILES`.
- Remove `model`, `model_reasoning_effort`, and `service_tier`.
- Remove Luna/Terra/Sol from `description`, `nickname_candidates`, the opening identity sentence, escalation-owner names, and role comparisons.
- Preserve `sandbox_mode`, `approval_policy`, status protocol, file ownership, experiment boundaries, review package rules, and core/non-core safeguards.
- Add this guard to every non-Spark profile's `developer_instructions`:

```text
Follow the model route in the controller's dispatch brief. If an explicit
route cannot be honored, return BLOCKED rather than silently substituting a
different model or reasoning effort. If an auto/unpinned task reaches core,
high-risk, or final-review scope, return BLOCKED for explicit Sol routing.
```

Use these exact semantic nicknames:

| Role | `nickname_candidates` |
| --- | --- |
| `CodebaseScout` | `["Codebase Scout", "Repository Mapper", "Context Scout"]` |
| `SimplePatcher` | `["Simple Patcher", "Small Fixer", "Mechanical Patcher"]` |
| `TestRunner` | `["Test Runner", "Focused Verifier", "Failure Triage"]` |
| `FastReviewer` | `["Fast Reviewer", "Mechanical Review", "Small Diff Review"]` |
| `Implementer` | `["Implementer", "Non-Core Implementer", "Multi-File Worker"]` |
| `PlanImplementer` | `["Plan Implementer", "Core Implementer", "SDD Implementer"]` |
| `ImplementationReviewer` | `["Implementation Reviewer", "Code Reviewer", "Quality Gate"]` |
| `ExpManager` | `["Experiment Manager", "Bundle Manager", "Experiment Steward"]` |
| `ResultAnalyst` | `["Result Analyst", "Metric Analyst", "Gate Analyst"]` |
| `ExternalReviewManager` | `["External Review Manager", "Cross Review Manager", "Review Archive"]` |
| `LongTimeMemoryManager` | `["Memory Manager", "LTM Manager", "Memory Steward"]` |
| `WorkflowAuditor` | `["Workflow Auditor", "Config Auditor", "Protocol Auditor"]` |
| `PlanImplementerFrontier` | `["Frontier Implementer", "Algorithm Implementer", "Max Implementer"]` |
| `ImplementationReviewerFrontier` | `["Frontier Reviewer", "Final Reviewer", "Architecture Reviewer"]` |

In `spark-explicit-simple-patcher.toml`, retain its model and effort fields and replace escalation references with `SimplePatcher` and `Implementer`.

- [ ] **Step 4: Replace the config registry**

Keep the existing `[features]` and `[agents]` scalar settings, then register the fifteen names from `EXPECTED_PROFILES`. Each entry uses the corresponding `./agents/<filename>` and semantic descriptions/nicknames from Step 3. Do not add aliases or top-level model settings.

The first and last registrations demonstrate the exact shape:

```toml
[agents."CodebaseScout"]
description = "Read-only HMASD codebase scout for bounded mapping and evidence gathering."
config_file = "./agents/codebase-scout.toml"
nickname_candidates = ["Codebase Scout", "Repository Mapper", "Context Scout"]

[agents."SparkExplicitSimplePatcher"]
description = "Explicit-only legacy Spark patcher for simple, single-file, non-core tasks."
config_file = "./agents/spark-explicit-simple-patcher.toml"
nickname_candidates = ["Spark Explicit Patcher", "Spark Legacy Patcher", "Spark Opt-In Patcher"]
```

- [ ] **Step 5: Run the focused runtime-profile validation**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected: `HMASD subagent protocol validation ok`. At this stage the validator's documentation-term assertions still reflect the pre-migration prose and will be migrated in Task 2.

- [ ] **Step 6: Review and commit Task 1**

Run:

```powershell
git diff --check -- .codex\config.toml .codex\agents scripts\validate_hmasd_subagent_protocol.py
git status --short
```

Expected: no whitespace errors; only the intended Codex runtime profiles, config, validator, and pre-existing unrelated dirty files appear.

Stage only Task 1 paths and commit:

```powershell
git add .codex\config.toml scripts\validate_hmasd_subagent_protocol.py
git add -A -- ".codex/agents/*.toml"
git commit -m "refactor: adopt semantic Codex agent roles"
```

### Task 2: Migrate Controller Rules And Dispatch Templates

**Files:**
- Modify: `scripts/validate_hmasd_subagent_protocol.py`
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`

**Interfaces:**
- Consumes: semantic role names from Task 1 and the routing classes in the approved design.
- Produces: one consistent controller/worker contract in which role identity is semantic and every dispatch records an explicit or automatic route.

- [ ] **Step 1: Make the documentation assertions expect semantic routing**

Replace old model-prefixed required terms in `REQUIRED_TEXT` with semantic names. For `AGENTS`, `README`, and `TEMPLATE`, require these exact policy anchors in addition to their existing status, output-root, review-package, and no-blind-retry anchors:

```python
ROUTING_TERMS = (
    "Model route:",
    "auto/unpinned",
    "gpt-5.6-luna",
    "gpt-5.6-sol",
    "CodebaseScout",
    "SimplePatcher",
    "TestRunner",
    "FastReviewer",
    "Implementer",
    "PlanImplementer",
    "ImplementationReviewer",
    "ExpManager",
    "ResultAnalyst",
    "ExternalReviewManager",
    "LongTimeMemoryManager",
    "WorkflowAuditor",
    "PlanImplementerFrontier",
    "ImplementationReviewerFrontier",
    "SparkExplicitSimplePatcher",
)
```

Add an active-file obsolete-name scan over `AGENTS`, `README`, `TEMPLATE`, `CONFIG`, and every TOML profile. The scan must use token boundaries and report the file and obsolete role. Do not scan historical specs or plans.

- [ ] **Step 2: Run the validator and confirm documentation now fails**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected: exit code `1`, naming the first missing routing term or obsolete model-prefixed role in an active document.

- [ ] **Step 3: Rewrite `AGENTS.md` routing sections without changing governance**

Apply semantic names throughout active Codex workflow rules. Preserve the existing First Read, controller communication, experiment hard gate, mandatory dispatch brief, runtime output, test hygiene, terminal status, review package, memory boundary, and experiment ownership rules.

Replace the model-family identity prose with this policy:

```text
Role profiles are semantic and normally omit model, reasoning, and service-tier
pins. The controller selects the role first, then records one route in the
dispatch brief: simple -> gpt-5.6-luna / medium; ordinary -> gpt-5.6-sol / high;
frontier -> gpt-5.6-sol / max; eligible low-risk support -> auto/unpinned.
SparkExplicitSimplePatcher is the only fixed-model exception.
```

Update the Mandatory Dispatch Brief Gate to require `Model route:` and update all role references using this exact mapping:

```text
LunaCodebaseScout -> CodebaseScout
LunaSimplePatcher -> SimplePatcher
LunaTestRunner -> TestRunner
TerraFastReviewer -> FastReviewer
TerraImplementer -> Implementer
TerraExpManager -> ExpManager
TerraResultAnalyst -> ResultAnalyst
TerraExternalReviewManager -> ExternalReviewManager
TerraLongTimeMemoryManager -> LongTimeMemoryManager
SolWorkflowAuditor -> WorkflowAuditor
SolPlanImplementer -> PlanImplementer
SolImplementationReviewer -> ImplementationReviewer
SolPlanImplementerFrontier -> PlanImplementerFrontier
SolImplementationReviewerFrontier -> ImplementationReviewerFrontier
```

State that auto/unpinned is opt-in per dispatch, cannot enter core/high-risk/final-review scope, and must return `BLOCKED` for explicit Sol re-dispatch when that boundary is reached. Remove obsolete claims that role names state model families, Terra is the ordinary tier, standard Sol uses xhigh, or profile TOMLs pin service tiers.

- [ ] **Step 4: Rewrite `.codex/agents/README.md` to match the controller contract**

Apply the same mapping and routing text as Step 3. Update the role catalog, implementation routing, reviewer routing, automatic hooks, experiment workflow, parallel-wave examples, fixed hooks, and runtime reload section. Preserve operational details such as bounded logs, `ExpRecord.md` ownership, review verdicts, and context-budget checkpoints.

Document these exact failure rules:

```text
- Missing semantic role in runtime: stop; do not use built-in fallback.
- Unsupported explicit route: BLOCKED; do not inherit or downgrade silently.
- Auto task reaches core/high-risk/final-review scope: BLOCKED; re-dispatch on Sol High or Sol Max.
- Spark without literal opt-in: NEEDS_CONTEXT and no edit.
- Old model-prefixed role still visible: restart required; runtime loading is unverified.
```

- [ ] **Step 5: Rename dispatch templates and add the route field**

Rename every template heading and identity line to the semantic role. Immediately after each task id/goal block, add one exact route line:

```text
Model route: gpt-5.6-luna / medium
```

for `SimplePatcher`, `TestRunner`, `CodebaseScout`, and `FastReviewer`; use:

```text
Model route: gpt-5.6-sol / high
```

for `Implementer`, `PlanImplementer`, `ImplementationReviewer`, `ExpManager`, `ResultAnalyst`, and `WorkflowAuditor`; use:

```text
Model route: gpt-5.6-sol / max
```

for both frontier roles. The `CodebaseScout` template may explicitly replace its Luna line with `Model route: auto/unpinned` only when its brief also states that the scope is bounded and low-risk. Keep the Spark profile fixed and retain its literal opt-in.

For the reviewer-choice template, encode the complete choice table:

```text
Reviewer profile/model route:
- FastReviewer -> gpt-5.6-luna / medium for small isolated mechanical diffs.
- ImplementationReviewer -> gpt-5.6-sol / high for standard nontrivial reviews.
- ImplementationReviewerFrontier -> gpt-5.6-sol / max for architecture,
  high-risk, concurrency, shared-state, API/data-contract, and final reviews.
```

- [ ] **Step 6: Run documentation and protocol validation**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected: `HMASD subagent protocol validation ok`.

Run the active-file name check independently:

```powershell
rg -n "LunaCodebaseScout|LunaSimplePatcher|LunaTestRunner|TerraImplementer|TerraFastReviewer|TerraExpManager|TerraResultAnalyst|TerraExternalReviewManager|TerraLongTimeMemoryManager|SolWorkflowAuditor|SolPlanImplementer|SolImplementationReviewer" AGENTS.md .codex scripts\validate_hmasd_subagent_protocol.py docs\superpowers\subagent-templates\hmasd-dispatch-templates.md
```

Expected: no output. The Spark name is intentionally excluded from the obsolete-name expression.

- [ ] **Step 7: Review and commit Task 2**

Run:

```powershell
git diff --check -- AGENTS.md .codex\agents\README.md docs\superpowers\subagent-templates\hmasd-dispatch-templates.md scripts\validate_hmasd_subagent_protocol.py
git status --short
```

Expected: no whitespace errors and no out-of-scope file newly changed by this task.

Stage only Task 2 paths and commit:

```powershell
git add AGENTS.md .codex\agents\README.md docs\superpowers\subagent-templates\hmasd-dispatch-templates.md scripts\validate_hmasd_subagent_protocol.py
git commit -m "docs: route semantic Codex agent roles"
```

### Task 3: Perform Integrated Static Validation And Prepare Runtime Acceptance

**Files:**
- Verify: `.codex/config.toml`
- Verify: `.codex/agents/*.toml`
- Verify: `AGENTS.md`
- Verify: `.codex/agents/README.md`
- Verify: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`
- Verify: `scripts/validate_hmasd_subagent_protocol.py`

**Interfaces:**
- Consumes: the complete semantic role migration from Tasks 1 and 2.
- Produces: static acceptance evidence plus an exact fresh-session runtime smoke brief; no benchmark profiles or performance results.

- [ ] **Step 1: Parse every TOML and print the effective registry**

Run:

```powershell
python -c "import pathlib,tomllib; root=pathlib.Path('.'); cfg=tomllib.loads((root/'.codex/config.toml').read_text(encoding='utf-8')); regs={k:v['config_file'] for k,v in cfg['agents'].items() if isinstance(v,dict) and 'config_file' in v}; profiles={p.name:tomllib.loads(p.read_text(encoding='utf-8'))['name'] for p in sorted((root/'.codex/agents').glob('*.toml'))}; print(regs); print(profiles)"
```

Expected: two mappings with exactly fifteen entries each; the names and filenames match `EXPECTED_PROFILES`.

- [ ] **Step 2: Run the complete validator and whitespace checks**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
git diff --check
```

Expected: validator prints `HMASD subagent protocol validation ok`; `git diff --check` prints nothing.

- [ ] **Step 3: Confirm scope and controller settings**

Run:

```powershell
git status --short
git diff --name-only 4b8b79d..HEAD
rg -n "^(model|model_reasoning_effort)\s*=" .codex\config.toml
rg -l "^(model|model_reasoning_effort|service_tier)\s*=" .codex\agents --glob "*.toml"
```

Expected:

- No implementation change under `.claude/**`, `CLAUDE.md`, `memory/**`, experiment paths, or algorithm sources.
- The config model-pin search prints nothing.
- The profile pin search prints only `.codex/agents/spark-explicit-simple-patcher.toml`.
- Pre-existing unrelated dirty files remain present and unchanged unless they were explicitly part of Tasks 1 or 2.

- [ ] **Step 4: Record the fresh-session smoke briefs in the controller handoff**

Do not claim hot reload in the current session. After a fresh session or app restart, use the runtime role-list/schema surface to verify that all fifteen semantic roles are exposed and no obsolete role is exposed. Then dispatch these two read-only briefs:

```text
Task id: ROLE-LOAD-LUNA-20260710
Goal: Read AGENTS.md headings and return the first five headings only.
Assigned custom agent: CodebaseScout
TOML profile: .codex/agents/codebase-scout.toml
Model route: gpt-5.6-luna / medium
Read scope: AGENTS.md only
Owned files: none; read-only
Forbidden actions: edits, experiments, memory updates, git actions
Output path: none
Required checks: report the headings and actual runtime route when exposed
Dependencies/conflicts: none; no parallel dispatch needed
Terminal status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED
Next owner: controller
Lifetime policy: leave available after result
```

```text
Task id: ROLE-LOAD-AUTO-20260710
Goal: Read .codex/config.toml and report feature flags plus agent limits only.
Assigned custom agent: CodebaseScout
TOML profile: .codex/agents/codebase-scout.toml
Model route: auto/unpinned
Read scope: .codex/config.toml only; bounded low-risk support task
Owned files: none; read-only
Forbidden actions: edits, experiments, memory updates, git actions
Output path: none
Required checks: report feature flags, limits, and actual runtime route when exposed
Dependencies/conflicts: run after ROLE-LOAD-LUNA-20260710
Terminal status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED
Next owner: controller
Lifetime policy: leave available after result
```

Expected: both return `DONE`; the first honors Luna Medium, the second succeeds through automatic routing, and neither changes files. If the runtime cannot honor the explicit route, returns old names, or omits semantic roles, report `BLOCKED` and require config/trust/restart diagnosis without built-in fallback.

- [ ] **Step 5: Report completion boundary**

If static checks pass but restart smokes have not run, report: `Static migration complete; runtime loading awaits a fresh Codex session.` Do not describe the migration as fully runtime-verified.

If both smokes pass, report the actual routes, zero changed files from the smokes, and full acceptance. No performance benchmark, experiment action, memory update, or additional profile is part of this task.
