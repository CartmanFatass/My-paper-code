# HMASD Subagent Agents Superpowers Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden HMASD project subagents and `AGENTS.md` around Superpowers-style status, pre-flight, review-package, batch-fix, dispatch-template, and no-blind-retry behavior.

**Architecture:** Keep the current custom-agent roster and explicit runtime model settings. Add a protocol layer shared by `AGENTS.md`, `.codex/agents/README.md`, role TOML instructions, reusable dispatch templates, and a validation script. The main controller remains responsible for user intent, integration, interpretation, git boundaries, and subagent lifecycle; subagents return bounded file-backed evidence and short status.

**Tech Stack:** Markdown protocol files, Codex custom-agent TOML, Python standard library validation with `pathlib`, `re`, and `tomllib`.

## Global Constraints

- Do not edit `.claude/` or Claude-specific files.
- Do not change existing agent `model`, `model_reasoning_effort`, `service_tier`, `sandbox_mode`, `approval_policy`, or `nickname_candidates` values unless validation finds a missing required runtime field.
- Keep the current custom-agent roster; do not create a separate main-controller subagent.
- Keep the main controller responsible for user understanding, task routing, algorithm discussion, implementation decisions, experiment interpretation, integration, final reporting, and git boundaries.
- Keep high-concurrency dispatch for clean independent waves; do not add fixed low agent-count caps.
- Keep `ImplementationReviewer` at batch, milestone, high-risk, or final gates; do not restore automatic review after every small task.
- Keep git/stage/commit/push controller-owned unless the user explicitly asks for git actions.
- Do not add a project manifest fallback or built-in role fallback.
- Subagents must not paste large diffs, full logs, full CSVs, long transcripts, or large traceback clusters into chat; write file artifacts and return compact status.
- A subagent returning `BLOCKED` must not be retried with the same model, same prompt, and same missing context unchanged.

---

## File Structure

- Modify `AGENTS.md`: add the canonical project protocol for status enum, pre-flight review, review packages, batch review fixes, dispatch templates, and blocked handling.
- Modify `.codex/agents/README.md`: add the detailed controller/subagent protocol that mirrors `AGENTS.md`.
- Create `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`: reusable prompt templates for implementation, experiment, metric, review, test, scout, audit, and batch-fix handoffs.
- Modify `.codex/agents/plan-implementer.toml`: strengthen status enum, blocked handling, and batch-fix handling for core work.
- Modify `.codex/agents/spark-implementer.toml`: strengthen status enum, blocked handling, and batch-fix handling for mechanical work.
- Modify `.codex/agents/simple-patcher.toml`: add the shared short-status contract for trivial patches.
- Modify `.codex/agents/implementation-reviewer.toml`: require review-package input and structured findings.
- Modify `.codex/agents/test-runner.toml`: add the shared short-status contract and bounded evidence output.
- Modify `.codex/agents/codebase-scout.toml`: add the shared short-status contract and evidence-only output.
- Modify `.codex/agents/exp-manager.toml`: add the shared short-status contract, checkpoint exit status, and no-blind-retry rule.
- Modify `.codex/agents/result-analyst.toml`: add the shared short-status contract and missing-evidence status.
- Modify `.codex/agents/workflow-auditor.toml`: add the shared short-status contract for audits.
- Modify `.codex/agents/external-review-manager.toml`: add the shared short-status contract and raw-archive evidence response.
- Modify `.codex/agents/long-time-memory-manager.toml`: add the shared short-status contract for memory sync and missing-evidence status.
- Create `scripts/validate_hmasd_subagent_protocol.py`: verify protocol coverage, TOML parseability, explicit runtime fields, template coverage, and absence of known bad workflow phrases.
- Modify `memory/CURRENT_WORK.md`: after protocol changes land, add one compact pointer that HMASD subagents now use status enum, pre-flight, review-package, batch-fix, and dispatch-template protocols.

---

### Task 1: Add Canonical Protocol To `AGENTS.md`

**Files:**
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: existing controller, parallelism, fixed hook, and lifecycle sections.
- Produces: root project protocol that later README, TOML, templates, and validation tasks must match.

- [ ] **Step 1: Insert a status protocol section after `## Subagent Runtime Rules`**

Insert this exact section:

```markdown
## Subagent Terminal Status Protocol

Every project subagent that returns task results must put one of these statuses
in the first line or first field of its short chat reply:

- `DONE`: assigned work completed, required artifact or report written, and no
  known concern needs controller action.
- `DONE_WITH_CONCERNS`: useful work completed, but residual risk, partial
  evidence, skipped optional checks, or non-blocking caveats remain.
- `NEEDS_CONTEXT`: the subagent needs a specific missing file, threshold,
  requirement, command output, permission, or user/controller decision before it
  can continue usefully.
- `BLOCKED`: the assigned task cannot proceed without a changed plan, changed
  ownership boundary, unavailable runtime, failed dependency, permission,
  model/role escalation, or corrected input artifact.

The controller response is status-driven:

- For `DONE`, integrate the report or artifact, run required checks, update the
  progress ledger when applicable, and close the subagent.
- For `DONE_WITH_CONCERNS`, integrate useful results, decide whether the
  concern is acceptable, needs a batch review, or needs a follow-up task, then
  close the subagent after capturing the concern.
- For `NEEDS_CONTEXT`, provide the specific missing context or split the task;
  do not resend the same prompt unchanged.
- For `BLOCKED`, do not retry with the same model, same prompt, and same
  missing context unchanged. The controller must choose one: supply new
  context, split the task smaller, change owner, escalate model/tier, revise
  the plan, inspect file-based status, or ask the user.

Short chat replies should contain only: status, report/artifact path, changed
files, commands/tests run, concise concerns/blockers, and next owner. Large
evidence belongs in files, not chat.
```

- [ ] **Step 2: Insert a pre-flight section after `## Plan-Bound Implementation Dispatch`**

Insert this exact section:

```markdown
## Pre-Flight Wave Review

Before dispatching an implementation, experiment, analysis, review, or audit
wave, the controller must do a pre-flight review. The review should be written
as a compact wave table in controller notes or a task brief, not pasted into
every subagent prompt.

Pre-flight must check:

- task id and short goal;
- requirements source: plan path, task brief path, user request, or controller
  brief;
- assigned custom agent and tier;
- owned files/directories and forbidden files/directories;
- report, status, package, metric, or review-package output path;
- required command, test, or artifact check;
- dependencies between tasks;
- write conflicts, run-directory conflicts, memory-row conflicts, shared
  process conflicts, and unresolved architecture decisions;
- whether a task is core/high-risk and should stay with the controller or use
  PlanImplementer, or whether it genuinely needs a PlanImplementerFrontier
  xhigh work package;
- whether any question must be batched back to the user before execution.

If pre-flight finds conflicts or missing decisions, batch the questions and ask
once before launching the wave. Do not discover predictable file ownership,
runtime, or plan conflicts one subagent at a time.
```

- [ ] **Step 3: Insert a review package section after `## Superpowers Parallelism Pattern`**

Insert this exact section:

```markdown
## Review Package Protocol

Reviewers should not reconstruct context from chat or read huge pasted diffs.
For batch, milestone, high-risk, and final review gates, the controller must
prepare a review package file when the change is larger than a trivial patch.

The review package should include:

- review goal and risk level;
- user request or accepted plan path;
- task brief paths and report paths;
- changed files and ownership boundaries;
- concise diff summary and exact commands used to inspect the real diff;
- tests/checks run with pass/fail status;
- known concerns from implementers or the controller;
- specific review questions;
- forbidden scope for the reviewer.

`ImplementationReviewer` reads the review package, task briefs, reports, and
repository diff. It returns findings ordered by severity. If fixes are needed,
the controller batches accepted findings into one fix brief for one suitable
implementer, then runs one follow-up verification and review pass when needed.
Do not spawn one fixer per finding.
```

- [ ] **Step 4: Add template pointer to `## Plan-Bound Implementation Dispatch`**

At the end of `## Plan-Bound Implementation Dispatch`, add:

```markdown
Use `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` for
standard dispatch shapes. Prefer passing file paths over repeating long plan
history in prompts.
```

- [ ] **Step 5: Update fixed hook wording for review and blocked handling**

In `## Fixed Workflow Hooks`, make sure the implementation-plan bullet includes these exact sentences:

```markdown
Before dispatching a wave, run the Pre-Flight Wave Review. Every dispatched
subagent must use the Subagent Terminal Status Protocol. If a subagent returns
`BLOCKED`, do not retry the same prompt unchanged; resolve the blocker through
new context, smaller task scope, owner/model escalation, plan revision, file
status inspection, or a user question.
```

In the review sentence of the same bullet, make sure it includes:

```markdown
For larger gates, prepare a review package file and route accepted findings
through one batch-fix brief rather than one fixer per finding.
```

- [ ] **Step 6: Verify `AGENTS.md` protocol phrases**

Run:

```powershell
rg -n "Subagent Terminal Status Protocol|Pre-Flight Wave Review|Review Package Protocol|DONE_WITH_CONCERNS|Do not retry with the same model|review package file|batch-fix brief" AGENTS.md
```

Expected: matches for every phrase.

---

### Task 2: Mirror Detailed Protocol In `.codex/agents/README.md`

**Files:**
- Modify: `.codex/agents/README.md`

**Interfaces:**
- Consumes: `AGENTS.md` canonical sections from Task 1.
- Produces: detailed subagent protocol used by future controllers and role maintainers.

- [ ] **Step 1: Add `## Terminal Status Protocol` after `## Lifecycle Protocol`**

Insert this exact section:

```markdown
## Terminal Status Protocol

Every project subagent result must start with one status:

- `DONE`: work complete, artifact/report written, no controller action required
  beyond integration and normal checks.
- `DONE_WITH_CONCERNS`: work useful and mostly complete, but caveats, partial
  evidence, skipped checks, or residual risk remain.
- `NEEDS_CONTEXT`: a specific missing file, threshold, requirement, permission,
  command result, or decision is required before useful progress can continue.
- `BLOCKED`: the task cannot proceed without a changed plan, changed owner,
  runtime availability, permission, model/tier escalation, or corrected input.

Required short reply fields:

```text
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Artifact/report: path or none
Changed files: list or none
Commands/tests: concise pass/fail summary or none
Concerns/blockers: concise or none
Next owner: controller | named subagent | user | none
```

Subagents must not paste large logs, full CSVs, giant diffs, long transcripts,
or traceback clusters into chat. Write those to bounded evidence files and
return the paths. A `BLOCKED` result must include the exact blocker, files or
commands involved, and what must change before retrying.
```

- [ ] **Step 2: Add `## No-Blind-Retry Rule` after the status section**

Insert this exact section:

```markdown
## No-Blind-Retry Rule

If a subagent returns `BLOCKED` or `NEEDS_CONTEXT`, the controller must not send
the same prompt back to the same role with the same context and expect a better
result. The next action must change at least one of:

- provide the missing file, command output, threshold, or decision;
- split the task into a smaller brief;
- change the owner to a more suitable role;
- escalate to a stronger model/tier when the task is genuinely harder;
- inspect status/checkpoint files before resuming long-running experiment work;
- revise or abandon the plan;
- ask the user for the blocking decision.

For long-running experiment work, prefer checkpoint-and-resume through files
over chat-heavy retries.
```

- [ ] **Step 3: Add `## Pre-Flight Review` before `## Parallel Execution`**

Insert this exact section:

```markdown
## Pre-Flight Review

Before spawning a wave, the controller builds a compact pre-flight table:

| Task | Agent | Requirements | Owns | Must not touch | Output | Checks | Dependencies | Conflict risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Do not launch the wave until predictable conflicts are resolved: overlapping
write scope, shared run directories, shared package paths, shared
`memory/ExpRecord.md` rows, shared processes, incompatible tests, missing
thresholds, missing task briefs, or unresolved architecture decisions.

When conflicts require user input, batch those questions before dispatch.
```

- [ ] **Step 4: Add `## Review Packages And Batch Fixes` after `## Progress Ledger`**

Insert this exact section:

```markdown
## Review Packages And Batch Fixes

For non-trivial batch, milestone, high-risk, or final reviews, prepare a review
package file before spawning `ImplementationReviewer`. The reviewer should read
the package, referenced briefs/reports, and repository diff rather than asking
the controller to paste large diffs into chat.

Minimum review package fields:

- review goal and risk level;
- user request or accepted plan path;
- task brief and report paths;
- changed files and ownership scope;
- commands/tests run;
- known concerns and residual risk;
- exact review questions;
- forbidden scope.

If review finds multiple issues, the controller decides which findings are
accepted and sends one batch-fix brief to one suitable implementer. Do not
spawn one fixer per finding. After fixes, run the focused checks and only
re-review the affected package when risk justifies it.
```

- [ ] **Step 5: Add template pointer after implementation dispatch guidance**

In the section that says implementation subagents should not receive open-ended prompts, add:

```markdown
Use `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` for
standard handoff prompts and return formats.
```

- [ ] **Step 6: Verify README protocol phrases**

Run:

```powershell
rg -n "Terminal Status Protocol|No-Blind-Retry Rule|Pre-Flight Review|Review Packages And Batch Fixes|DONE_WITH_CONCERNS|same prompt back|one batch-fix brief" .codex\agents\README.md
```

Expected: matches for every phrase.

---

### Task 3: Create Dispatch Template File

**Files:**
- Create: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`

**Interfaces:**
- Consumes: protocol sections from Tasks 1 and 2.
- Produces: reusable dispatch prompt shapes for the controller.

- [ ] **Step 1: Create the template file**

Create `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` with this content:

````markdown
# HMASD Subagent Dispatch Templates

Use these templates when the controller delegates bounded work. Prefer file
paths over pasted history. Replace bracketed fields before dispatch.

## Shared Short Reply Contract

Every subagent returns only:

```text
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Artifact/report: [path or none]
Changed files: [list or none]
Commands/tests: [concise pass/fail summary or none]
Concerns/blockers: [concise or none]
Next owner: controller | [subagent name] | user | none
```

If status is `NEEDS_CONTEXT` or `BLOCKED`, include the exact missing context or
blocker and what must change before a retry is useful.

## Pre-Flight Wave Table

```text
Wave goal:
Authorization source:
Progress ledger:

| Task | Agent | Requirements source | Owns | Must not touch | Output/report | Checks | Dependency | Conflict risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [T1] | [Agent] | [path/request] | [paths] | [paths] | [path] | [command] | [none/T0] | [low/medium/high + reason] |

Questions to batch before dispatch:
- [question or "none"]
```

## PlanImplementer Dispatch

```text
You are PlanImplementer for HMASD.

Requirements source:
- [plan path or task brief path]

Classification:
- Core/high-risk because [reason].

Owned files/directories:
- [paths]

Forbidden files/directories:
- [paths]

Report path:
- [path]

Required checks:
- [commands]

Commit policy:
- Do not stage or commit unless the controller explicitly says so.

Instructions:
- Read the requirements source first.
- Implement only the assigned scope.
- If the task needs architecture judgment beyond the brief, return BLOCKED.
- Write the full report to the report path.
- Return only the Shared Short Reply Contract.
```

## SparkImplementer Dispatch

```text
You are SparkImplementer for HMASD.

Requirements source:
- [plan path or task brief path]

Classification:
- Non-core mechanical because [reason].

Owned files/directories:
- [paths]

Forbidden files/directories:
- [paths]

Report path:
- [path]

Required checks:
- [commands]

Commit policy:
- Do not stage or commit unless the controller explicitly says so.

Instructions:
- Make only the mechanical change described in the requirements source.
- If the task expands into core algorithm, training, reward, model, optimizer,
  collector, environment dynamics, credit assignment, q_A/q_D, team-intent, or
  shared behavioral config semantics, return BLOCKED.
- Write the full report to the report path.
- Return only the Shared Short Reply Contract.
```

## ExpManager Dispatch

```text
You are ExpManager for HMASD.

Experiment task:
- [prepare package | launch | progress check | metric extraction | ExpRecord factual update]

Requirements source:
- [ExpRecord path, plan path, user request, or controller brief]

Experiment/run paths:
- [paths]

Status/checkpoint paths:
- runner_status.txt: [path]
- runner_output.log: [path or none]
- expmanager_checkpoint.md: [path]

Record policy:
- Update memory/ExpRecord.md factual fields when experiment state changes,
  unless this dispatch says read-only/no persistent record.

Required checks:
- [process/log/CSV/error/package checks]

Instructions:
- Use bounded reads.
- Write large evidence to files.
- If context grows large, checkpoint and return DONE_WITH_CONCERNS or
  NEEDS_CONTEXT with exact resume instructions.
- Return only the Shared Short Reply Contract.
```

## ResultAnalyst Dispatch

```text
You are ResultAnalyst for HMASD.

Analysis question:
- [metric/gate/anomaly/typical-step question]

Artifacts to read:
- [paths]

Gate definitions:
- [thresholds or "missing; return NEEDS_CONTEXT if needed"]

Output files:
- metric_extract.md: [path]
- gate_read.md: [path or none]
- error_extract.md: [path or none]

Instructions:
- Analyze existing artifacts only.
- Do not launch experiments or update memory/ExpRecord.md unless explicitly
  assigned.
- Separate metric facts from controller interpretation.
- Return only the Shared Short Reply Contract.
```

## ImplementationReviewer Dispatch

```text
You are ImplementationReviewer for HMASD.

Review package:
- [path]

Referenced requirements:
- [brief/report/plan paths]

Risk level:
- [batch | milestone | high-risk | final]

Review focus:
- [correctness, regression, spec compliance, tests, data contracts, integration]

Forbidden scope:
- Do not edit files.
- Do not request pasted large diffs; inspect repository files/diff from the
  package instructions.

Output:
- Findings first, ordered by severity.
- Include file/line references when available.
- If no issues, say no issues found and list residual test gaps or risk.
- Return only the Shared Short Reply Contract after the findings summary.
```

## Batch Review Fix Dispatch

```text
You are [PlanImplementer or SparkImplementer] for HMASD.

Accepted review findings:
- [finding ids and exact required fixes]

Review package:
- [path]

Owned files/directories:
- [paths]

Forbidden files/directories:
- [paths]

Report path:
- [path]

Required checks:
- [commands]

Instructions:
- Fix the accepted findings as one batch.
- Do not address rejected/deferred findings.
- If a finding requires architecture or algorithm judgment beyond this brief,
  return BLOCKED for that finding and continue only independent accepted fixes.
- Write the full report to the report path.
- Return only the Shared Short Reply Contract.
```

## TestRunner Dispatch

```text
You are test-runner for HMASD.

Commands:
- [commands]

Related changes:
- [paths]

Output file for large failure evidence:
- [path or none]

Instructions:
- Run only the assigned commands.
- Do not edit files unless explicitly assigned.
- Summarize pass/fail, key error, likely owner, and whether failures appear
  related to current changes.
- Return only the Shared Short Reply Contract.
```

## CodebaseScout Dispatch

```text
You are codebase-scout for HMASD.

Question:
- [focused mapping question]

Read scope:
- [paths]

Forbidden actions:
- No edits, no tests unless explicitly asked, no memory updates, no git.

Instructions:
- Use rg or rg --files first.
- Return concise file/symbol references and uncertainty.
- Return only the Shared Short Reply Contract.
```

## WorkflowAuditor Dispatch

```text
You are WorkflowAuditor for HMASD.

Audit scope:
- [paths]

Audit questions:
- [questions]

Forbidden actions:
- Read-only; no edits, no subagent spawning, no git.

Instructions:
- Report findings first, ordered by severity.
- Cite exact file paths and lines when available.
- Return only the Shared Short Reply Contract.
```
````

- [ ] **Step 2: Verify template sections**

Run:

```powershell
rg -n "Shared Short Reply Contract|Pre-Flight Wave Table|PlanImplementer Dispatch|SparkImplementer Dispatch|ExpManager Dispatch|ResultAnalyst Dispatch|ImplementationReviewer Dispatch|Batch Review Fix Dispatch|TestRunner Dispatch|CodebaseScout Dispatch|WorkflowAuditor Dispatch" docs\superpowers\subagent-templates\hmasd-dispatch-templates.md
```

Expected: matches for every section name.

---

### Task 4: Harden Implementation, Review, Test, Scout, And Audit TOMLs

**Files:**
- Modify: `.codex/agents/plan-implementer.toml`
- Modify: `.codex/agents/spark-implementer.toml`
- Modify: `.codex/agents/simple-patcher.toml`
- Modify: `.codex/agents/implementation-reviewer.toml`
- Modify: `.codex/agents/test-runner.toml`
- Modify: `.codex/agents/codebase-scout.toml`
- Modify: `.codex/agents/workflow-auditor.toml`

**Interfaces:**
- Consumes: Shared Short Reply Contract from Task 3.
- Produces: role instructions that force consistent status and bounded evidence.

- [ ] **Step 1: Append no-blind-retry language to implementer TOMLs**

In `.codex/agents/plan-implementer.toml` and `.codex/agents/spark-implementer.toml`, add this paragraph before the existing `Return only short status in chat:` block:

```text
If you are missing a required file, threshold, command result, ownership
decision, or architecture decision, return NEEDS_CONTEXT with the exact missing
item. If the task cannot proceed within assigned scope or needs a changed plan,
return BLOCKED. Do not keep retrying silently, and do not continue with guessed
requirements.
```

- [ ] **Step 2: Add batch-fix behavior to implementer TOMLs**

In the same two implementer TOMLs, add this paragraph after the previous paragraph:

```text
When assigned accepted review findings as a batch-fix task, fix only the
accepted findings listed by the controller. Do not address rejected or deferred
findings. If one finding is blocked but others are independent and in scope,
complete the independent fixes and report DONE_WITH_CONCERNS with the blocked
finding identified.
```

- [ ] **Step 3: Replace `simple-patcher` final instructions**

In `.codex/agents/simple-patcher.toml`, make sure its `developer_instructions` ends with:

```text
Return only short status in chat:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: path or none.
Changed files: list or none.
Commands/tests: concise pass/fail summary or none.
Concerns/blockers: concise or none.
Next owner: controller, named subagent, user, or none.
```

- [ ] **Step 4: Replace `ImplementationReviewer` final instructions**

In `.codex/agents/implementation-reviewer.toml`, append:

```text
For non-trivial reviews, expect a review package path. Read the package,
referenced briefs/reports, and repository diff instructions instead of asking
for pasted history or large diffs. If the review package is missing for a
non-trivial review, return NEEDS_CONTEXT and name the missing package.

Return findings first, ordered by severity. For each finding include severity,
file/line when available, issue, risk, and suggested fix direction. If there
are no findings, say no issues found and list residual test gaps or risks.

Return only short status in chat after the findings:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: review package path or none.
Changed files: none.
Commands/tests: checks inspected or none.
Concerns/blockers: concise or none.
Next owner: controller, named subagent, user, or none.
```

- [ ] **Step 5: Append short-status contract to test/scout/audit TOMLs**

In `.codex/agents/test-runner.toml`, `.codex/agents/codebase-scout.toml`, and `.codex/agents/workflow-auditor.toml`, append:

```text
Return only short status in chat:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: path or none.
Changed files: list or none.
Commands/tests: concise pass/fail summary or none.
Concerns/blockers: concise or none.
Next owner: controller, named subagent, user, or none.

Use NEEDS_CONTEXT for a specific missing input. Use BLOCKED when the task cannot
proceed without changed scope, permissions, runtime state, or owner/model
choice. Do not paste large evidence into chat; write it to a file when needed.
```

- [ ] **Step 6: Verify implementation/review/test/scout/audit TOMLs**

Run:

```powershell
Get-ChildItem .codex\agents -Filter *.toml | Where-Object { $_.Name -in @('plan-implementer.toml','spark-implementer.toml','simple-patcher.toml','implementation-reviewer.toml','test-runner.toml','codebase-scout.toml','workflow-auditor.toml') } | ForEach-Object { rg -n "DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED|Next owner" $_.FullName }
```

Expected: each listed TOML has matches for all four terms.

---

### Task 5: Harden Experiment, Metric, External Review, And Memory TOMLs

**Files:**
- Modify: `.codex/agents/exp-manager.toml`
- Modify: `.codex/agents/result-analyst.toml`
- Modify: `.codex/agents/external-review-manager.toml`
- Modify: `.codex/agents/long-time-memory-manager.toml`

**Interfaces:**
- Consumes: Shared Short Reply Contract from Task 3.
- Produces: context-budgeted evidence roles with recoverable status semantics.

- [ ] **Step 1: Append final reply contract to `exp-manager.toml`**

Append this paragraph near the end of `developer_instructions`, before the final closing `"""`:

```text
Return only short status in chat:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: expmanager_checkpoint.md, runner_status.txt, metric_extract.md,
error_extract.md, package handoff, or none.
Changed files: list or none, including memory/ExpRecord.md when changed.
Commands/tests: concise pass/fail/running summary or none.
Concerns/blockers: concise or none.
Next owner: controller, ResultAnalyst, LongTimeMemoryManager, user, or none.

Use DONE_WITH_CONCERNS when a checkpoint/resume handoff is written and useful
work completed but more phases remain. Use NEEDS_CONTEXT for a specific missing
path, threshold, command, or decision. Use BLOCKED when status files cannot be
created before a long-running launch, required permissions are missing, runtime
state prevents progress, or the controller must revise the phase plan. Do not
retry a blocked phase silently.
```

- [ ] **Step 2: Append final reply contract to `result-analyst.toml`**

Append this paragraph near the end of `developer_instructions`:

```text
Return only short status in chat:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: metric_extract.md, gate_read.md, error_extract.md, or none.
Changed files: list or none.
Commands/tests: concise extraction/check summary or none.
Concerns/blockers: concise or none.
Next owner: controller, ExpManager, LongTimeMemoryManager, user, or none.

Use NEEDS_CONTEXT when gate thresholds, artifact paths, or required columns are
missing. Use BLOCKED when artifacts are absent, unreadable, corrupt, or outside
assigned scope. Do not invent thresholds or scientific interpretation.
```

- [ ] **Step 3: Append final reply contract to `external-review-manager.toml`**

Append this paragraph near the end of `developer_instructions`:

```text
Return only short status in chat:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: raw archive path, handoff path, index path, or none.
Changed files: list or none.
Commands/tests: concise archive/check summary or none.
Concerns/blockers: concise or none.
Next owner: controller, LongTimeMemoryManager, user, or none.

Use NEEDS_CONTEXT when raw pasted text, source model name, date, or archive
target is missing. Use BLOCKED when raw external text cannot be preserved before
summary or handoff work. Summaries are indexes, not evidence.
```

- [ ] **Step 4: Append final reply contract to `long-time-memory-manager.toml`**

Append this paragraph near the end of `developer_instructions`:

```text
Return only short status in chat:
Status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
Artifact/report: memory files changed, archive path, or none.
Changed files: list or none.
Commands/tests: concise consistency check summary or none.
Concerns/blockers: concise or none.
Next owner: controller, ExpManager, ExternalReviewManager, user, or none.

Use NEEDS_CONTEXT when the controller conclusion, raw external review archive,
experiment factual record, or target memory file is missing. Use BLOCKED when a
requested memory update would require project-governance decisions instead of
memory maintenance. Do not promote summaries as evidence when raw archives are
required.
```

- [ ] **Step 5: Verify experiment/evidence/memory TOMLs**

Run:

```powershell
Get-ChildItem .codex\agents -Filter *.toml | Where-Object { $_.Name -in @('exp-manager.toml','result-analyst.toml','external-review-manager.toml','long-time-memory-manager.toml') } | ForEach-Object { rg -n "DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED|Next owner" $_.FullName }
```

Expected: each listed TOML has matches for all four terms.

---

### Task 6: Add Protocol Validation Script

**Files:**
- Create: `scripts/validate_hmasd_subagent_protocol.py`

**Interfaces:**
- Consumes: `AGENTS.md`, `.codex/agents/README.md`, `.codex/agents/*.toml`, and `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`.
- Produces: non-zero exit on missing protocol phrases, invalid TOML, missing runtime fields, missing templates, or known bad workflow phrases.

- [ ] **Step 1: Create validation script**

Create `scripts/validate_hmasd_subagent_protocol.py` with this exact content:

```python
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / ".codex" / "agents" / "README.md"
TEMPLATE = ROOT / "docs" / "superpowers" / "subagent-templates" / "hmasd-dispatch-templates.md"
AGENT_DIR = ROOT / ".codex" / "agents"

STATUS_TERMS = ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED")
RUNTIME_FIELDS = (
    "name",
    "description",
    "model",
    "model_reasoning_effort",
    "sandbox_mode",
    "approval_policy",
    "nickname_candidates",
    "developer_instructions",
)

REQUIRED_TEXT = {
    AGENTS: (
        "Subagent Terminal Status Protocol",
        "Pre-Flight Wave Review",
        "Review Package Protocol",
        "Do not retry with the same model",
        "batch-fix brief",
    ),
    README: (
        "Terminal Status Protocol",
        "No-Blind-Retry Rule",
        "Pre-Flight Review",
        "Review Packages And Batch Fixes",
        "one batch-fix brief",
    ),
    TEMPLATE: (
        "Shared Short Reply Contract",
        "Pre-Flight Wave Table",
        "PlanImplementer Dispatch",
        "SparkImplementer Dispatch",
        "ExpManager Dispatch",
        "ResultAnalyst Dispatch",
        "ImplementationReviewer Dispatch",
        "Batch Review Fix Dispatch",
        "TestRunner Dispatch",
        "CodebaseScout Dispatch",
        "WorkflowAuditor Dispatch",
    ),
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\b2" + r"-3 agents\b", re.IGNORECASE),
    re.compile(r"old2", re.IGNORECASE),
    re.compile(r"not a hard " + r"cap", re.IGNORECASE),
    re.compile(r"not a " + r"cap", re.IGNORECASE),
    re.compile(r"fallback to (worker|explorer|default)", re.IGNORECASE),
    re.compile(r"one fixer per finding", re.IGNORECASE),
    re.compile(r"automatic review after every small task", re.IGNORECASE),
)


def read_text(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require_terms(path: Path, terms: tuple[str, ...]) -> None:
    text = read_text(path)
    for term in terms:
        if term not in text:
            raise AssertionError(f"{path} missing required term: {term}")
    for status in STATUS_TERMS:
        if status not in text:
            raise AssertionError(f"{path} missing status term: {status}")


def check_forbidden(path: Path) -> None:
    text = read_text(path)
    for pattern in FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        if match:
            raise AssertionError(f"{path} has forbidden phrase: {match.group(0)!r}")


def check_toml(path: Path) -> None:
    data = tomllib.loads(read_text(path))
    for field in RUNTIME_FIELDS:
        if field not in data:
            raise AssertionError(f"{path} missing runtime field: {field}")
    instructions = str(data["developer_instructions"])
    for status in STATUS_TERMS:
        if status not in instructions:
            raise AssertionError(f"{path} developer_instructions missing {status}")
    for phrase in ("Status:", "Artifact/report:", "Changed files:", "Commands/tests:", "Concerns/blockers:", "Next owner:"):
        if phrase not in instructions:
            raise AssertionError(f"{path} developer_instructions missing short reply field {phrase!r}")


def main() -> int:
    try:
        for path, terms in REQUIRED_TEXT.items():
            require_terms(path, terms)
        for path in (AGENTS, README, TEMPLATE):
            check_forbidden(path)
        toml_files = sorted(AGENT_DIR.glob("*.toml"))
        if not toml_files:
            raise AssertionError(f"no TOML files found under {AGENT_DIR}")
        for path in toml_files:
            check_toml(path)
        print("HMASD subagent protocol validation ok")
        return 0
    except AssertionError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run validator and confirm expected initial failure if earlier tasks are incomplete**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected before Tasks 1-5 are complete: non-zero with the first missing protocol term or missing TOML short-reply field.

- [ ] **Step 3: Run validator after Tasks 1-5 are complete**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected after Tasks 1-5 are complete:

```text
HMASD subagent protocol validation ok
```

---

### Task 7: Final Verification And Compact Memory Update

**Files:**
- Modify: `memory/CURRENT_WORK.md`

**Interfaces:**
- Consumes: completed protocol changes and validator result.
- Produces: compact pointer for future sessions.

- [ ] **Step 1: Run full phrase audit**

Run:

```powershell
rg -n "Subagent Terminal Status Protocol|Terminal Status Protocol|Pre-Flight|Review Package|batch-fix|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED|No-Blind-Retry|Shared Short Reply Contract" AGENTS.md .codex\agents\README.md .codex\agents docs\superpowers\subagent-templates
```

Expected: matches in root project instructions, detailed agents README, role TOMLs, and dispatch templates.

- [ ] **Step 2: Run validator**

Run:

```powershell
python scripts\validate_hmasd_subagent_protocol.py
```

Expected:

```text
HMASD subagent protocol validation ok
```

- [ ] **Step 3: Update compact memory**

Add one concise bullet to `memory/CURRENT_WORK.md` under the active workflow or project-protocol section:

```markdown
- Project subagents use a Superpowers-style protocol: status enum
  (`DONE`/`DONE_WITH_CONCERNS`/`NEEDS_CONTEXT`/`BLOCKED`), pre-flight wave
  review, file-based review packages, batch review fixes, dispatch templates,
  and no unchanged retry after blocked/needs-context results.
```

- [ ] **Step 4: Report completion**

Final report must include:

```text
Status: DONE or DONE_WITH_CONCERNS
Changed files:
- AGENTS.md
- .codex/agents/README.md
- docs/superpowers/subagent-templates/hmasd-dispatch-templates.md
- scripts/validate_hmasd_subagent_protocol.py
- .codex/agents/*.toml files changed
- memory/CURRENT_WORK.md
Validation:
- python scripts\validate_hmasd_subagent_protocol.py
Subagents used:
- list or none
Concerns:
- any residual reload requirement for Codex custom-agent TOML changes
```

---

## Self-Review

Spec coverage:

- Unified status protocol is implemented by Tasks 1, 2, 4, 5, and 6.
- Pre-flight review is implemented by Tasks 1, 2, 3, and 6.
- Review package file mechanism is implemented by Tasks 1, 2, 3, 4, and 6.
- Batch review findings are implemented by Tasks 1, 2, 3, and 4.
- Template dispatch prompts are implemented by Task 3 and referenced by Tasks 1 and 2.
- `BLOCKED` and `NEEDS_CONTEXT` no-blind-retry behavior is implemented by Tasks 1, 2, 4, 5, and 6.
- Project-specific adaptation is preserved: main controller governance, high-concurrency clean waves, batch/milestone/final review, no automatic per-task commits, no fallback roles, no `.claude/` edits, and no model-setting churn.

Placeholder scan:

- No placeholder markers are used as implementation requirements.
- Every file to create or modify has an exact path.
- Every validation command has expected output.

Type and name consistency:

- The status enum is consistently `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`.
- The shared short reply fields are consistently `Status`, `Artifact/report`, `Changed files`, `Commands/tests`, `Concerns/blockers`, and `Next owner`.
- The validation script checks the same files and phrases that the plan modifies.
