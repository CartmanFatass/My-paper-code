# Codex Agent Model-Tier Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Codex's generic-name agent profiles with explicit model-prefixed GPT-5.6 role names, retain exactly one opt-in Spark 5.3 simple-task role, and verify the resulting configuration statically.

**Architecture:** The runtime registry in `.codex/config.toml` and every standalone TOML profile become the source of truth for a model-prefixed agent name. Luna owns simple tasks, Terra owns medium-complexity non-core work, Sol owns core/high-risk work, and Spark is an explicit-only legacy exception. The protocol validator encodes the complete name/model/effort matrix so documentation drift and accidental generic aliases fail locally.

**Tech Stack:** TOML custom-agent profiles, Python standard-library `tomllib`, PowerShell, ripgrep, Git.

## Global Constraints

- Scope is Codex-side only: do not modify `.claude/**`, `CLAUDE.md`, shared handover docs, shared memory, experiment code, or run artifacts.
- Runtime names must be model-prefixed and unique: no generic-name aliases remain registered.
- Luna is the default for simple bounded tasks; Terra is only for medium-complexity non-core work; Sol is required for core/high-risk work; Spark is explicit-only.
- `SparkExplicitSimplePatcher` must remain the sole `gpt-5.3-codex-spark` profile and must require `Legacy Spark opt-in: explicitly requested` in its dispatch brief.
- Preserve `multi_agent = true`, `multi_agent_v2 = false`, thread limits, and the existing literal `service_tier = "fast"` on priority profiles.
- Do not enable `max`, `ultra`, Pro mode, API multi-agent beta, or automatic model downgrade/fallback.
- Preserve unrelated dirty worktree changes. In particular, do not stage or commit existing user modifications in `AGENTS.md`.
- Do not launch experiments, access remote systems, or spawn subagents for this migration.
- Maintain `.superpowers/sdd/progress.md` while executing the plan.

## File Structure

- `.codex/config.toml`: registers the model-prefixed runtime names and points each to its matching profile file.
- `.codex/agents/*.toml`: one profile per model-prefixed agent, with explicit model, reasoning effort, sandbox, approval policy, nicknames, and role-boundary instructions.
- `AGENTS.md`: Codex controller routing and model-floor policy.
- `.codex/agents/README.md`: detailed Codex-only agent/runtime policy.
- `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`: dispatch briefs that name the new runtime agents and enforce Spark opt-in.
- `scripts/validate_hmasd_subagent_protocol.py`: static validator for the registry/profile contract and routing policy terms.
- `.superpowers/sdd/progress.md`: local execution ledger for this migration.

## Target Profile Contract

```python
EXPECTED_PROFILES = {
    "LunaCodebaseScout": ("luna-codebase-scout.toml", "gpt-5.6-luna", "low"),
    "LunaSimplePatcher": ("luna-simple-patcher.toml", "gpt-5.6-luna", "low"),
    "LunaTestRunner": ("luna-test-runner.toml", "gpt-5.6-luna", "low"),
    "SparkExplicitSimplePatcher": (
        "spark-explicit-simple-patcher.toml", "gpt-5.3-codex-spark", "low"
    ),
    "TerraImplementer": ("terra-implementer.toml", "gpt-5.6-terra", "high"),
    "TerraFastReviewer": ("terra-fast-reviewer.toml", "gpt-5.6-terra", "medium"),
    "TerraExpManager": ("terra-exp-manager.toml", "gpt-5.6-terra", "medium"),
    "TerraExternalReviewManager": (
        "terra-external-review-manager.toml", "gpt-5.6-terra", "medium"
    ),
    "TerraLongTimeMemoryManager": (
        "terra-long-time-memory-manager.toml", "gpt-5.6-terra", "high"
    ),
    "TerraResultAnalyst": ("terra-result-analyst.toml", "gpt-5.6-terra", "high"),
    "SolPlanImplementer": ("sol-plan-implementer.toml", "gpt-5.6-sol", "high"),
    "SolImplementationReviewer": (
        "sol-implementation-reviewer.toml", "gpt-5.6-sol", "high"
    ),
    "SolWorkflowAuditor": ("sol-workflow-auditor.toml", "gpt-5.6-sol", "high"),
    "SolPlanImplementerFrontier": (
        "sol-plan-implementer-frontier.toml", "gpt-5.6-sol", "xhigh"
    ),
    "SolImplementationReviewerFrontier": (
        "sol-implementation-reviewer-frontier.toml", "gpt-5.6-sol", "xhigh"
    ),
}
```

### Task 1: Create the Progress Ledger and Contract Validator

**Files:**
- Create: `.superpowers/sdd/progress.md`
- Modify: `scripts/validate_hmasd_subagent_protocol.py`
- Test: `scripts/validate_hmasd_subagent_protocol.py`

**Interfaces:**
- Consumes: the TOML `[agents]` registry and every `.codex/agents/*.toml` profile.
- Produces: one zero-exit static contract check that later tasks use as their completion gate.

- [ ] **Step 1: Record execution ownership and task state**

Create `.superpowers/sdd/progress.md` with this exact initial ledger:

```markdown
# Codex Agent Model-Tier Migration Progress

- [ ] Task 1: Static contract validator
- [ ] Task 2: Runtime registry and TOML profiles
- [ ] Task 3: Codex routing documentation and dispatch templates
- [ ] Task 4: Static verification and reload handoff
```

- [ ] **Step 2: Add the expected profile contract before changing the profiles**

Add `CONFIG = ROOT / ".codex" / "config.toml"`, the `EXPECTED_PROFILES` mapping above, and a `GENERIC_AGENT_NAMES` set containing the retired runtime names:

```python
GENERIC_AGENT_NAMES = {
    "codebase-scout",
    "simple-patcher",
    "test-runner",
    "SparkImplementer",
    "PlanImplementer",
    "PlanImplementerFrontier",
    "ImplementationReviewerFast",
    "ImplementationReviewer",
    "ImplementationReviewerFrontier",
    "ExpManager",
    "ResultAnalyst",
    "ExternalReviewManager",
    "LongTimeMemoryManager",
    "WorkflowAuditor",
}
```

Implement `check_agent_identity_contract()` to parse `CONFIG`, extract only
the nested registry tables with `config_file` from its `agents` table (leaving
the numeric global limits out), verify that this registry has exactly the
`EXPECTED_PROFILES` keys, check each `config_file` path, then compare every
profile's `name`, `model`, and
`model_reasoning_effort` against the mapping. Require the Spark profile's
developer instructions to contain `Legacy Spark opt-in: explicitly requested`.
Call this check before document-term checks in `main()` so the pre-migration
test fails on the identity mismatch rather than on stale prose first.

- [ ] **Step 3: Run the new contract against the old registry**

Run:

```powershell
python scripts/validate_hmasd_subagent_protocol.py
```

Expected: FAIL, reporting that the old generic runtime registrations do not
match the expected model-prefixed profile contract.

- [ ] **Step 4: Update validator documentation requirements**

Require `AGENTS.md`, `.codex/agents/README.md`, and the dispatch template to
contain `LunaSimplePatcher`, `TerraImplementer`, `SolPlanImplementer`, and
`SparkExplicitSimplePatcher`. Replace the old reviewer-name requirement with:

```python
REQUIRED_AGENT_NAMES = {
    "TerraFastReviewer",
    "SolImplementationReviewer",
    "SolImplementationReviewerFrontier",
}
```

- [ ] **Step 5: Leave the task pending until the runtime profiles are migrated**

Do not treat the expected pre-migration failure as a final error. Mark Task 1
as complete in the ledger only after Task 2 makes this same command pass.

### Task 2: Replace the Runtime Registry and Profile Files

**Files:**
- Modify: `.codex/config.toml`
- Rename: `.codex/agents/codebase-scout.toml` to `.codex/agents/luna-codebase-scout.toml`
- Rename: `.codex/agents/simple-patcher.toml` to `.codex/agents/luna-simple-patcher.toml`
- Rename: `.codex/agents/test-runner.toml` to `.codex/agents/luna-test-runner.toml`
- Rename: `.codex/agents/spark-implementer.toml` to `.codex/agents/spark-explicit-simple-patcher.toml`
- Rename: `.codex/agents/implementation-reviewer-fast.toml` to `.codex/agents/terra-fast-reviewer.toml`
- Rename: `.codex/agents/exp-manager.toml` to `.codex/agents/terra-exp-manager.toml`
- Rename: `.codex/agents/external-review-manager.toml` to `.codex/agents/terra-external-review-manager.toml`
- Rename: `.codex/agents/long-time-memory-manager.toml` to `.codex/agents/terra-long-time-memory-manager.toml`
- Rename: `.codex/agents/result-analyst.toml` to `.codex/agents/terra-result-analyst.toml`
- Rename: `.codex/agents/plan-implementer.toml` to `.codex/agents/sol-plan-implementer.toml`
- Rename: `.codex/agents/implementation-reviewer.toml` to `.codex/agents/sol-implementation-reviewer.toml`
- Rename: `.codex/agents/workflow-auditor.toml` to `.codex/agents/sol-workflow-auditor.toml`
- Rename: `.codex/agents/plan-implementer-frontier.toml` to `.codex/agents/sol-plan-implementer-frontier.toml`
- Rename: `.codex/agents/implementation-reviewer-frontier.toml` to `.codex/agents/sol-implementation-reviewer-frontier.toml`
- Create: `.codex/agents/terra-implementer.toml`
- Test: `scripts/validate_hmasd_subagent_protocol.py`

**Interfaces:**
- Consumes: `EXPECTED_PROFILES` from Task 1.
- Produces: exactly fifteen registered profiles with a model-prefixed `name` and an explicit model/effort pair.

- [ ] **Step 1: Rename profiles without losing their required terminal-status contract**

Move each profile to its listed target path. Preserve the required fields,
approval policy, sandbox setting, nickname candidates, and six short-reply
fields. Change the TOML `name`, `description`, model, and reasoning effort to
the exact target contract.

- [ ] **Step 2: Make the Luna profiles the simple-task default**

Set these fields:

```toml
name = "LunaSimplePatcher"
model = "gpt-5.6-luna"
model_reasoning_effort = "low"
```

Apply the same Luna/low pairing to `LunaCodebaseScout` and `LunaTestRunner`.
Their developer instructions must state that they handle only bounded simple
work and must escalate core or multi-file consistency work.

- [ ] **Step 3: Restrict Spark to the explicit legacy exception**

Set the renamed Spark profile to:

```toml
name = "SparkExplicitSimplePatcher"
model = "gpt-5.3-codex-spark"
model_reasoning_effort = "low"
```

Its developer instructions must require the literal line:

```text
Legacy Spark opt-in: explicitly requested
```

and must reject multi-file, core, experiment, or implicit-cost-fallback work
with `NEEDS_CONTEXT`.

- [ ] **Step 4: Add Terra and Sol profiles at their assigned boundaries**

Create `TerraImplementer` with `gpt-5.6-terra` and `high` reasoning. Its
instructions must own bounded medium-complexity, multi-file, non-core work and
must stop on core algorithm/numerical semantics. Set the remaining Terra and
Sol profiles according to `EXPECTED_PROFILES`; preserve `service_tier = "fast"`
only in the renamed Sol plan/frontier-final profiles that already carried it.

- [ ] **Step 5: Replace the configuration registry atomically**

Make `[agents]` register only the fifteen model-prefixed names, with each
`config_file` pointing to the matching renamed TOML file. Preserve the
`[features]` and `[agents]` numeric defaults unchanged. Do not leave an old
generic `[agents."..."]` registration behind.

- [ ] **Step 6: Run the profile contract independently of documentation**

Run:

```powershell
python -c "import pathlib,runpy,tomllib; root=pathlib.Path('.'); cfg=tomllib.loads((root/'.codex/config.toml').read_text(encoding='utf-8')); registry={name: value for name,value in cfg['agents'].items() if isinstance(value,dict) and 'config_file' in value}; expected=runpy.run_path('scripts/validate_hmasd_subagent_protocol.py')['EXPECTED_PROFILES']; assert set(registry)==set(expected); [tomllib.loads((root/'.codex'/entry['config_file'].removeprefix('./')).read_text(encoding='utf-8')) for entry in registry.values()]; print('profile_contract_ok')"
```

Expected: `profile_contract_ok`. Full documentation validation waits until
Task 3.

### Task 3: Update Codex Routing Documentation and Dispatch Templates

**Files:**
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`
- Test: `scripts/validate_hmasd_subagent_protocol.py`

**Interfaces:**
- Consumes: the fifteen runtime names from Task 2.
- Produces: controller-facing routing rules and dispatch templates that never
  request retired generic names.

- [ ] **Step 1: Update model-floor and role-routing language in `AGENTS.md`**

Replace generic agent references with model-prefixed names. Add the explicit
classifier below near the existing core/non-core routing policy:

```text
Simple bounded work -> LunaCodebaseScout, LunaSimplePatcher, or LunaTestRunner.
Medium-complexity non-core multi-file work -> TerraImplementer.
Core algorithm or quality-critical review -> SolPlanImplementer,
SolPlanImplementerFrontier, SolImplementationReviewer, or
SolImplementationReviewerFrontier according to risk.
SparkExplicitSimplePatcher -> only when the dispatch brief contains
"Legacy Spark opt-in: explicitly requested".
```

Preserve the user's existing dirty additions; patch only the relevant model and
role-routing text.

- [ ] **Step 2: Update the Codex agent README**

Replace old profile/model examples and reviewer tiers with the exact new runtime
names. State that `fast` remains the TOML spelling for priority semantics and
that a new Codex session or app restart is required before `spawn_agent` can
expose the renamed roles.

- [ ] **Step 3: Update dispatch templates**

Rename dispatch headings and profile references to the new runtime names. Add a
dedicated `SparkExplicitSimplePatcher Dispatch` block requiring the literal
opt-in line and a `TerraImplementer Dispatch` block for multi-file non-core
work. Retain all existing status, output-root, ownership, forbidden-scope, and
next-owner fields.

- [ ] **Step 4: Run the protocol validator**

Run:

```powershell
python scripts/validate_hmasd_subagent_protocol.py
```

Expected: `HMASD subagent protocol validation ok`.

### Task 4: Verify the Static Contract and Write the Reload Handoff

**Files:**
- Modify: `.superpowers/sdd/progress.md`
- Test: `.codex/config.toml`, `.codex/agents/*.toml`, `scripts/validate_hmasd_subagent_protocol.py`

**Interfaces:**
- Consumes: all migrated TOML profiles, registry entries, documentation, and validator checks.
- Produces: a verified static migration plus a precise post-restart runtime check.

- [ ] **Step 1: Parse all TOML files and registration targets**

Run:

```powershell
python -c "import pathlib,runpy,tomllib; root=pathlib.Path('.'); cfg=tomllib.loads((root/'.codex/config.toml').read_text(encoding='utf-8')); registry={name: value for name,value in cfg['agents'].items() if isinstance(value,dict) and 'config_file' in value}; expected=runpy.run_path('scripts/validate_hmasd_subagent_protocol.py')['EXPECTED_PROFILES']; assert set(registry)==set(expected); [tomllib.loads((root/'.codex'/entry['config_file'].removeprefix('./')).read_text(encoding='utf-8')) for entry in registry.values()]; print('toml_registry_ok')"
```

Expected: `toml_registry_ok`.

- [ ] **Step 2: Run the full static suite**

Run:

```powershell
python scripts/validate_hmasd_subagent_protocol.py
git diff --check
rg -n 'model = "gpt-5\.(3|4|5)' .codex/agents
```

Expected: protocol validation passes; no whitespace errors; the model search
returns only `SparkExplicitSimplePatcher` for the legacy Spark model and no
old GPT-5.4/GPT-5.5 profile values.

- [ ] **Step 3: Update the progress ledger**

Replace every Task 1-4 checkbox in `.superpowers/sdd/progress.md` with `[x]`,
then append:

```markdown
Runtime reload handoff: Start a fresh Codex session or restart the app, inspect
the `spawn_agent` role schema, and confirm all fifteen model-prefixed names and
their model/effort settings. The current session cannot prove hot reload.
```

- [ ] **Step 4: Preserve the dirty-worktree boundary**

Do not stage or commit `AGENTS.md` if it contains pre-existing user changes.
Report the exact changed files and the fresh-session check as the remaining
runtime validation step.
