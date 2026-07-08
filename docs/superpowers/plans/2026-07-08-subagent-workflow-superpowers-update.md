# HMASD Subagent Workflow Superpowers Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the HMASD Codex subagent workflow to absorb the useful Superpowers subagent practices: explicit status protocol, pre-flight wave review, file-based review packages, batched review fixes, standardized dispatch templates, and validation checks.

**Architecture:** This is a workflow/protocol update, not an algorithm update. Keep the active Codex session as the sole main controller, preserve high-concurrency wave dispatch, and add tighter contracts around subagent status, recovery, review inputs, and blocked handling. The workflow remains official-Codex-custom-agent based: `.codex/config.toml` stays minimal and `.codex/agents/*.toml` remains the runtime source of role settings.

**Tech Stack:** Markdown protocol files, official Codex custom-agent TOML files, Python standard-library validation script using `pathlib`, `re`, and `tomllib` or `tomli` fallback if the active Python is older than 3.11.

## Global Constraints

- Do not edit `.claude/` or Claude-specific files.
- Do not reintroduce project `manifest.yaml` fallback or built-in `worker` / `explorer` / `default` role fallback.
- Do not reintroduce old low-concurrency wording such as `2-3 agents`, `conservative`, or `not a hard cap`.
- Keep the main controller responsible for user intent, algorithm discussion, code/execution decisions, subagent coordination, interpretation, git boundaries, and final explanation.
- Keep LongTimeMemoryManager memory-only; it must not own project governance.
- Keep ExpManager factual/operational and ResultAnalyst artifact-metric focused; neither decides scientific acceptance.
- Keep ImplementationReviewer batched at milestone/high-risk/final gates; do not restore automatic review after every small task.
- Keep git/stage/commit/push controller-owned and batched unless the user explicitly asks for git actions.
- Do not touch algorithm, training, reward, experiment-runner, or test files except for the validation script created by this plan.
- Use `apply_patch` for manual edits.
- The implementation pass may update compact memory after the protocol change lands; LTM archive updates should be routed through LongTimeMemoryManager only if the controller decides the accepted workflow change is archive-worthy.

---

## File Structure

- Modify `AGENTS.md`: project-level controller contract, fixed hooks, status protocol, pre-flight wave review, review package rules, and batch-fix handling.
- Modify `.codex/agents/README.md`: detailed subagent protocol matching `AGENTS.md`.
- Modify `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`: global skill so future Codex workflow repairs reproduce the same contract.
- Modify `.codex/agents/spark-implementer.toml`: implementer status contract and blocked/escalation behavior.
- Modify `.codex/agents/plan-implementer.toml`: same status contract, with stronger core-code escalation language.
- Modify `.codex/agents/test-runner.toml`: status contract for verification and failure triage.
- Modify `.codex/agents/exp-manager.toml`: checkpoint-first behavior for `NEEDS_CONTEXT` and `BLOCKED`, no chat-heavy retries.
- Modify `.codex/agents/result-analyst.toml`: status contract and evidence-file discipline.
- Modify `.codex/agents/implementation-reviewer.toml`: review package input contract and no per-task auto-review assumption.
- Create `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`: reusable prompt skeletons for wave pre-flight, implementer dispatch, experiment evidence dispatch, result analyst dispatch, reviewer dispatch, and batch-fix dispatch.
- Create `scripts/validate_codex_subagent_workflow.py`: local validation for required workflow phrases, forbidden legacy phrases, TOML parseability, explicit role model settings, and key status protocol coverage.
- Optionally modify `memory/CURRENT_WORK.md` after implementation to mention the new status/pre-flight/review-package contract.

---

### Task 1: Add Shared Subagent Status Protocol

**Files:**
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`
- Modify: `.codex/agents/spark-implementer.toml`
- Modify: `.codex/agents/plan-implementer.toml`
- Modify: `.codex/agents/test-runner.toml`
- Modify: `.codex/agents/exp-manager.toml`
- Modify: `.codex/agents/result-analyst.toml`

**Interfaces:**
- Consumes: existing lifecycle protocol in `AGENTS.md` and `.codex/agents/README.md`.
- Produces: shared subagent terminal statuses: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`.

- [ ] **Step 1: Insert status protocol into `AGENTS.md`**

Add this section after the current lifecycle paragraph that says the controller records agent id and close state:

```markdown
## Subagent Status Protocol

Every project subagent must return one terminal status in its short chat reply:
`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.

- `DONE`: assigned scope completed; report file or concise evidence is ready.
- `DONE_WITH_CONCERNS`: assigned scope completed, but correctness, scope, test,
  evidence, or integration concerns remain.
- `NEEDS_CONTEXT`: the subagent needs specific missing context before it can
  proceed safely.
- `BLOCKED`: the subagent cannot complete the task with the current scope,
  model, permissions, files, or runtime state.

The controller must not ignore escalation statuses. For `NEEDS_CONTEXT`, provide
the missing context or narrow the task before continuing. For `BLOCKED`, change
something before retrying: add context, split the task, upgrade the model, adjust
permissions, inspect status files, or ask the user if the plan itself is wrong.
Do not resend the same prompt to the same role as a blind retry.
```

- [ ] **Step 2: Insert matching status protocol into `.codex/agents/README.md`**

Add the same section after `## Lifecycle Protocol`, keeping wording identical except replacing "Every project subagent" with "Every spawned project subagent".

- [ ] **Step 3: Insert matching status protocol into the global skill**

In `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`, add a `## Subagent Status Protocol` section after `## Lifecycle Protocol` with the same status meanings and the no-blind-retry rule.

- [ ] **Step 4: Update implementer TOMLs**

In `.codex/agents/spark-implementer.toml` and `.codex/agents/plan-implementer.toml`, append this paragraph inside `developer_instructions` before the final reply instructions:

```text
Use the shared terminal status protocol in your short chat reply: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED. If you are BLOCKED, do not keep retrying silently. State the exact blocker, the files or commands involved, and what must change before a retry is useful. If the task expands outside the assigned ownership boundary, stop and return BLOCKED or NEEDS_CONTEXT rather than editing outside scope.
```

- [ ] **Step 5: Update verification and evidence TOMLs**

In `.codex/agents/test-runner.toml`, `.codex/agents/exp-manager.toml`, and `.codex/agents/result-analyst.toml`, append this paragraph inside `developer_instructions`:

```text
Use the shared terminal status protocol in your short chat reply: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED. If evidence is incomplete, use DONE_WITH_CONCERNS when useful work is complete but caveated, NEEDS_CONTEXT when a specific missing file/path/threshold is required, and BLOCKED when the task cannot proceed without a changed plan, permission, runtime state, or model/role boundary.
```

- [ ] **Step 6: Verify status protocol coverage**

Run:

```powershell
rg -n "DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED|Do not resend the same prompt|blind retry" AGENTS.md .codex\agents\README.md .codex\agents\*.toml C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: matches in `AGENTS.md`, `.codex/agents/README.md`, the global skill, and the five TOML files edited in this task.

---

### Task 2: Add Pre-Flight Wave Review

**Files:**
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`
- Create: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`

**Interfaces:**
- Consumes: current parallel-wave rules.
- Produces: a controller-owned pre-flight decision packet before any high-concurrency wave.

- [ ] **Step 1: Create templates directory and file**

Create `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` with this initial content:

```markdown
# HMASD Subagent Dispatch Templates

## Wave Pre-Flight Packet

Use this before dispatching an authorized parallel wave.

```text
Wave goal:
Authorization source:
Progress ledger checked:

Task table:
| Task id | Agent | Tier | Brief path | Report path | Owned files/dirs | Forbidden files/dirs | Dependencies | Required checks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Conflict scan:
- Shared write paths:
- Shared run directories/package paths:
- Shared memory/ExpRecord rows:
- Shared training/reward/config semantics:
- External permissions/remote/money/publish risk:

Dispatch decision:
- Parallel now:
- Sequential first:
- Controller-local:
- User clarification required:
```
```

- [ ] **Step 2: Add pre-flight rule to `AGENTS.md`**

In `## Superpowers Parallelism Pattern`, after the numbered list of four rules, add:

```markdown
Before dispatching a high-concurrency wave, the controller must build a
pre-flight packet: wave goal, authorization source, progress-ledger state, task
table, owned paths, forbidden paths, dependencies, required checks, and conflict
scan. If the conflict scan finds shared writes, shared run directories, shared
package paths, the same `memory/ExpRecord.md` row, shared training/reward/config
semantics, remote/money/publish risk, or unresolved architecture decisions, do
not dispatch that part in parallel. Run it sequentially, keep it controller-local,
or ask the user when the plan itself is ambiguous.
```

- [ ] **Step 3: Add matching pre-flight rule to `.codex/agents/README.md`**

In `## Parallel Execution`, after the existing wave table bullet list, add the same pre-flight packet rule.

- [ ] **Step 4: Add matching pre-flight rule to global skill**

In `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`, add the same rule in the paragraph beginning `Restore parallelism with controlled parallel waves`.

- [ ] **Step 5: Verify pre-flight coverage**

Run:

```powershell
rg -n "pre-flight packet|Wave Pre-Flight Packet|Authorization source|Conflict scan" AGENTS.md .codex\agents\README.md docs\superpowers\subagent-templates\hmasd-dispatch-templates.md C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: matches in all four files.

---

### Task 3: Add Review Package And Batched Fix Protocol

**Files:**
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`
- Modify: `.codex/agents/implementation-reviewer.toml`
- Modify: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`

**Interfaces:**
- Consumes: existing `ImplementationReviewer` batch/milestone/final cadence.
- Produces: review package inputs and one-batch fix loop.

- [ ] **Step 1: Add review package rule to `AGENTS.md`**

In the automatic hook bullet for `ImplementationReviewer`, replace or extend the current wording with:

```markdown
- ImplementationReviewer runs only for batch, milestone, high-risk, or final
  review gates, not automatically after every small task. Review dispatches
  must be file-based: pass the task brief or plan section, worker report path,
  and a review package path containing commit list, diff stat, and relevant diff
  context. Do not paste large diffs into chat. If review returns multiple
  Critical or Important findings, batch them into one fixer handoff rather than
  spawning one fixer per finding.
```

- [ ] **Step 2: Add matching review rule to `.codex/agents/README.md`**

In the throttling section and fixed workflow hooks, ensure the same review package and batch-fix wording appears once.

- [ ] **Step 3: Add matching review rule to global skill**

In the paragraph beginning `Use ImplementationReviewer as a cost-controlled batch`, add:

```markdown
Reviewer inputs should be file paths: task brief or plan section, worker report,
and review package. The review package contains commit list, diff stat, and
relevant diff context. If review returns multiple Critical or Important
findings, dispatch one fixer with the complete findings list, then re-review the
updated package.
```

- [ ] **Step 4: Update ImplementationReviewer TOML**

Append this paragraph inside `.codex/agents/implementation-reviewer.toml` `developer_instructions`:

```text
Prefer file-based review inputs: task brief or plan section, worker report, and review package containing commit list, diff stat, and relevant diff context. Do not ask the controller to paste large diffs into chat. Return findings by severity with file/line references when possible, and include a terminal status: DONE when no blocking findings remain, DONE_WITH_CONCERNS for non-blocking residual risks, NEEDS_CONTEXT for missing review inputs, or BLOCKED when the review cannot proceed.
```

- [ ] **Step 5: Append reviewer and batch-fix templates**

Append this to `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`:

```markdown
## ImplementationReviewer Dispatch

```text
Status contract: return DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.

Read first:
- Task brief or plan section: <path>
- Worker report: <path>
- Review package: <path>

Review scope:
- Spec compliance:
- Code quality:
- High-risk areas:
- Out of scope:

Return:
- Status:
- Critical findings:
- Important findings:
- Minor findings:
- Cannot verify from provided files:
- Residual risk:
```

## Batch Fix Dispatch

```text
Status contract: return DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.

Fix all Critical and Important findings from:
- Review report: <path>
- Original task brief: <path>
- Current review package: <path>

Owned files:
Forbidden files:
Required checks:

Write full fix report to:
Return only status, changed files, checks, concerns, and report path.
```
```

- [ ] **Step 6: Verify review package coverage**

Run:

```powershell
rg -n "review package|Batch Fix Dispatch|one fixer|complete findings list|large diffs" AGENTS.md .codex\agents\README.md .codex\agents\implementation-reviewer.toml docs\superpowers\subagent-templates\hmasd-dispatch-templates.md C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: matches in all listed files.

---

### Task 4: Add Standard Dispatch Templates For Core Roles

**Files:**
- Modify: `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`
- Modify: `AGENTS.md`
- Modify: `.codex/agents/README.md`
- Modify: `C:/Users/wu/.codex/skills/codex-subagent-workflow/SKILL.md`

**Interfaces:**
- Consumes: role names `PlanImplementer`, `SparkImplementer`, `ExpManager`, `ResultAnalyst`, `ImplementationReviewer`.
- Produces: reusable lean prompt shapes that avoid context bloat.

- [ ] **Step 1: Append implementer template**

Append:

```markdown
## PlanImplementer Or SparkImplementer Dispatch

```text
Status contract: return DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.

Role:
Core/non-core classification:
Why this role:

Read first:
- Task brief: <path>
- Relevant interface/context file: <path>

Owned files:
Forbidden files:
Required checks:
Report path:
Commit policy: do not commit unless the controller explicitly says this task owns a commit.

Return only:
- Status:
- Changed files:
- Checks run:
- Concerns:
- Report path:
```
```

- [ ] **Step 2: Append ExpManager template**

Append:

```markdown
## ExpManager Dispatch

```text
Status contract: return DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.

Experiment id:
Phase: package/runner preparation | launch | progress check | operational extraction | ExpRecord update
Read first:
- ExpRecord entry or planned row:
- Runner/package/status path:

Required file evidence:
- runner_status.txt or equivalent:
- runner_output.log or equivalent:
- expmanager_checkpoint.md when multi-phase or long-running:

Context budget:
- Do not paste full logs, full CSVs, traceback clusters, or long transcripts.
- Write large evidence to run-local files and return paths.

Return only:
- Status:
- Run state:
- Files inspected/written:
- Key facts:
- Anomalies:
- Next factual read point:
```
```

- [ ] **Step 3: Append ResultAnalyst template**

Append:

```markdown
## ResultAnalyst Dispatch

```text
Status contract: return DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.

Analysis question:
Existing artifact paths:
Gate definitions and thresholds:
Output extract path:

Scope:
- Read existing artifacts only.
- Do not launch, stop, restart, package, or schedule experiments.
- Do not update memory/ExpRecord.md unless explicitly routed.

Return only:
- Status:
- Files inspected:
- Files written:
- Key metric/gate facts:
- Missing evidence:
- Follow-up owner:
```
```

- [ ] **Step 4: Link templates from controller docs**

Add this sentence to `AGENTS.md`, `.codex/agents/README.md`, and the global skill near the file-handoff rules:

```markdown
Use `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md` for lean
dispatch skeletons before writing long custom prompts; prompts should pass file
paths, ownership boundaries, checks, status contract, and report path rather
than pasted history.
```

- [ ] **Step 5: Verify template coverage**

Run:

```powershell
rg -n "PlanImplementer Or SparkImplementer Dispatch|ExpManager Dispatch|ResultAnalyst Dispatch|hmasd-dispatch-templates" docs\superpowers\subagent-templates\hmasd-dispatch-templates.md AGENTS.md .codex\agents\README.md C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: all template section names appear in the template file and the template path appears in the three controller/protocol files.

---

### Task 5: Add Workflow Validation Script

**Files:**
- Create: `scripts/validate_codex_subagent_workflow.py`

**Interfaces:**
- Consumes: project protocol files and `.codex/agents/*.toml`.
- Produces: non-zero exit on missing required phrases, forbidden phrases, TOML parse errors, missing explicit model settings, or absent status protocol.

- [ ] **Step 1: Create validation script**

Create `scripts/validate_codex_subagent_workflow.py` with this content:

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
GLOBAL_SKILL = Path.home() / ".codex" / "skills" / "codex-subagent-workflow" / "SKILL.md"

TEXT_FILES = [
    ROOT / "AGENTS.md",
    ROOT / ".codex" / "agents" / "README.md",
    ROOT / "memory" / "CURRENT_WORK.md",
    GLOBAL_SKILL,
]

REQUIRED_PATTERNS = {
    "status_DONE_WITH_CONCERNS": re.compile(r"DONE_WITH_CONCERNS"),
    "status_NEEDS_CONTEXT": re.compile(r"NEEDS_CONTEXT"),
    "status_BLOCKED": re.compile(r"BLOCKED"),
    "preflight_packet": re.compile(r"pre-flight packet|Wave Pre-Flight Packet", re.IGNORECASE),
    "review_package": re.compile(r"review package", re.IGNORECASE),
    "template_path": re.compile(r"hmasd-dispatch-templates\.md"),
    "no_fallback": re.compile(r"Do not spawn built-in|no project manifest fallback|There is intentionally no project manifest fallback", re.IGNORECASE),
    "controller_governance": re.compile(r"main controller owns|active Codex session is the main controller", re.IGNORECASE),
}

FORBIDDEN_PATTERNS = {
    "old_agent_count": re.compile(r"\b2-3 agents\b", re.IGNORECASE),
    "old2": re.compile(r"old2", re.IGNORECASE),
    "conservative_cap": re.compile(r"conservative|not a hard cap|not a cap", re.IGNORECASE),
    "builtin_fallback": re.compile(r"fallback to (worker|explorer|default)", re.IGNORECASE),
}

REQUIRED_AGENT_FIELDS = [
    "name",
    "description",
    "model",
    "model_reasoning_effort",
    "sandbox_mode",
    "approval_policy",
    "nickname_candidates",
    "developer_instructions",
]

AGENTS_REQUIRING_STATUS = {
    "spark-implementer.toml",
    "plan-implementer.toml",
    "test-runner.toml",
    "exp-manager.toml",
    "result-analyst.toml",
    "implementation-reviewer.toml",
}


def read_text(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def check_text_patterns() -> None:
    combined = "\n".join(read_text(path) for path in TEXT_FILES)
    for name, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(combined):
            raise AssertionError(f"missing required workflow pattern: {name}")
    for name, pattern in FORBIDDEN_PATTERNS.items():
        match = pattern.search(combined)
        if match:
            raise AssertionError(f"forbidden workflow pattern {name}: {match.group(0)!r}")


def check_toml_agents() -> None:
    agent_dir = ROOT / ".codex" / "agents"
    toml_files = sorted(agent_dir.glob("*.toml"))
    if not toml_files:
        raise AssertionError("no .codex/agents/*.toml files found")
    for path in toml_files:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        missing = [field for field in REQUIRED_AGENT_FIELDS if field not in data]
        if missing:
            raise AssertionError(f"{path} missing fields: {', '.join(missing)}")
        instructions = str(data["developer_instructions"])
        if path.name in AGENTS_REQUIRING_STATUS:
            for status in ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"):
                if status not in instructions:
                    raise AssertionError(f"{path} missing status token {status}")


def main() -> int:
    check_text_patterns()
    check_toml_agents()
    print("codex subagent workflow validation ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"codex subagent workflow validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
```

- [ ] **Step 2: Run validation and fix failures**

Run:

```powershell
python scripts\validate_codex_subagent_workflow.py
```

Expected:

```text
codex subagent workflow validation ok
```

- [ ] **Step 3: Run TOML parse check**

Run:

```powershell
python -c "import pathlib, tomllib; [tomllib.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('.codex/agents').glob('*.toml')]; print('toml ok')"
```

Expected:

```text
toml ok
```

---

### Task 6: Sync Compact Memory After Protocol Update

**Files:**
- Modify: `memory/CURRENT_WORK.md`

**Interfaces:**
- Consumes: completed protocol updates from Tasks 1-5.
- Produces: compact pointer so future Codex sessions know this workflow update exists.

- [ ] **Step 1: Update `memory/CURRENT_WORK.md` active plan pointer**

In the `AGENTS.md` bullet under `## Active Plan Pointers`, extend the workflow summary with this exact phrase:

```markdown
standard subagent terminal statuses (`DONE`, `DONE_WITH_CONCERNS`,
`NEEDS_CONTEXT`, `BLOCKED`), pre-flight wave packets, review-package inputs,
batched review-fix handling, and reusable dispatch templates.
```

- [ ] **Step 2: Add plan pointer**

Add this bullet near the other plan pointers:

```markdown
- `docs/superpowers/plans/2026-07-08-subagent-workflow-superpowers-update.md`:
  pending/accepted protocol update plan for Superpowers-style status handling,
  pre-flight wave review, review packages, batched review fixes, dispatch
  templates, and validation.
```

- [ ] **Step 3: Verify memory pointer**

Run:

```powershell
rg -n "DONE_WITH_CONCERNS|pre-flight wave packets|review-package inputs|2026-07-08-subagent-workflow-superpowers-update" memory\CURRENT_WORK.md
```

Expected: matches for status protocol phrase and plan path.

---

## Final Verification

- [ ] **Step 1: Run workflow validator**

Run:

```powershell
python scripts\validate_codex_subagent_workflow.py
```

Expected:

```text
codex subagent workflow validation ok
```

- [ ] **Step 2: Check no old low-concurrency wording returned**

Run:

```powershell
rg -n "2-3 agents|old2|conservative|not a hard cap|not a cap" AGENTS.md .codex\agents\README.md memory\CURRENT_WORK.md C:\Users\wu\.codex\skills\codex-subagent-workflow\SKILL.md
```

Expected: no matches.

- [ ] **Step 3: Check status terms are present in role TOMLs**

Run:

```powershell
rg -n "DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED" .codex\agents\spark-implementer.toml .codex\agents\plan-implementer.toml .codex\agents\test-runner.toml .codex\agents\exp-manager.toml .codex\agents\result-analyst.toml .codex\agents\implementation-reviewer.toml
```

Expected: each listed TOML has matches.

- [ ] **Step 4: Check no fallback manifest has returned**

Run:

```powershell
Test-Path .codex\agents\manifest.yaml
```

Expected:

```text
False
```

- [ ] **Step 5: Inspect final changed files**

Run:

```powershell
git status --short AGENTS.md .codex\agents\README.md .codex\agents\*.toml docs\superpowers\subagent-templates\hmasd-dispatch-templates.md scripts\validate_codex_subagent_workflow.py memory\CURRENT_WORK.md
```

Expected: only files in this plan plus already-existing unrelated dirty files outside the scoped status command.

---

## Self-Review

Spec coverage:
- Superpowers status handling is covered by Task 1.
- Pre-flight plan/wave review is covered by Task 2.
- Review package inputs and batched fix handling are covered by Task 3.
- Lean dispatch templates are covered by Task 4.
- Non-regression validation is covered by Task 5.
- Compact memory pointer is covered by Task 6.
- HMASD constraints about controller governance, no fallback, high concurrency, no `.claude/`, and batched reviewer use are included in Global Constraints.

Placeholder scan:
- The plan intentionally contains no `TBD`, no "implement later", no "fill in details", and no cross-task "similar to" instruction.

Type and naming consistency:
- Status tokens are consistently `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, and `BLOCKED`.
- Template path is consistently `docs/superpowers/subagent-templates/hmasd-dispatch-templates.md`.
- Validation script path is consistently `scripts/validate_codex_subagent_workflow.py`.
