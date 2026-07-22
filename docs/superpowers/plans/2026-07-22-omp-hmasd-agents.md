# OMP HMASD Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create four native, controller-dispatchable OMP HMASD agents while preserving the existing Manager-owned Codex profiles and the repository's single-writer and authority invariants.

**Architecture:** Add standalone Markdown agent definitions under `.omp/agents/` with minimal OMP tool allowlists and preserved role prompts. Track those definitions explicitly, then update `AGENTS.md` and `CURRENT_WORK.md` so direct controller dispatch is legal only outside a Manager write lease and under a frozen, user-authorized assignment.

**Tech Stack:** OMP task-agent YAML frontmatter, Markdown system prompts, repository control Markdown, Git ignore rules.

## Global Constraints

- Do not alter `.codex/agents/*.toml`.
- Use exact agent names `hmasd-code-scout`, `hmasd-implementer`, `hmasd-verifier`, and `hmasd-reviewer`.
- No OMP agent receives the `task` tool or child-spawn authority.
- A mutating OMP assignment requires direct user authorization, frozen scope and acceptance criteria, no active Research Project Manager write lease, and one writer per file set.
- Subagents receive no scientific adoption, formal experiment, Git integration, project-control, or persistent-role authority.
- This workflow-only change does not resume research, implementation, or formal compute.

---

### Task 1: Native OMP Agent Surface and Controller Boundary

**Files:**
- Modify: `.gitignore:47-61`
- Create: `.omp/agents/hmasd-code-scout.md`
- Create: `.omp/agents/hmasd-implementer.md`
- Create: `.omp/agents/hmasd-verifier.md`
- Create: `.omp/agents/hmasd-reviewer.md`
- Modify: `AGENTS.md:23-83`
- Modify: `docs/project/CURRENT_WORK.md:33-36,68-76`
- Modify: `docs/superpowers/specs/2026-07-22-omp-hmasd-agents-design.md:22-25`

**Interfaces:**
- Consumes: OMP agent discovery from project `.omp/agents/*.md`; the existing semantic source in `.codex/agents/*.toml`; the Manager write lease in `AGENTS.md`.
- Produces: Four exact OMP task-agent names discoverable at runtime and a controller dispatch contract that cannot overlap a Manager mutating lease.

- [ ] **Step 1: Verify the native agents are initially unavailable**

Invoke the OMP `task` tool with a bounded no-modification assignment for `hmasd-code-scout` before creating `.omp/agents/`.

Expected: the tool reports `Unknown agent "hmasd-code-scout"` and lists currently available agents. No subprocess runs.

- [ ] **Step 2: Make OMP Markdown agents durable repository tooling**

Insert this rule immediately after `!.claude/agents/*.md` in `.gitignore`:

```gitignore
# Native OMP task-agent definitions are durable project tooling.
!.omp/agents/*.md
```

Run:

```bash
git check-ignore -v .omp/agents/hmasd-code-scout.md
```

Expected after the edit: exit code 1 with no matching ignore rule.

- [ ] **Step 3: Create the read-only code scout**

Create `.omp/agents/hmasd-code-scout.md` with exactly:

```markdown
---
name: hmasd-code-scout
description: Read-only HMASD code scout for bounded interface mapping and safe parallel-work discovery.
model: openai-codex/gpt-5.6-luna
thinking-level: medium
tools: read, grep, glob, lsp
spawns: []
blocking: false
autoload-skills: false
---

You are the HMASD code scout. Produce a bounded evidence map that helps the
controller or Research Project Manager design and partition one implementation.
You never choose the scientific route, write the implementation plan, edit
files, review the final package, or execute experiments.

The assignment is the complete task-specific context. Read only the named files
and immediate interfaces required to answer its mapping questions. Do not load
role Skills, controller documents, historical reviews, or broad repository
history unless explicitly assigned.

Stable HMASD context: the project targets one stronger general MARL algorithm
for runtime-variable membership and variable individual lifetime. Protected
boundaries include reward, probability support and factorization, gradients and
detach paths, credit, recurrent state, masks, clocks, lifecycle ownership, RNG
and CRN coupling, replay, optimizer exposure, checkpoint/resume, evaluation
estimands, and formal result meaning. Ordinary recurrent MARL is a comparator,
not a research admission gate. Active-line development rejects legacy and
compatibility paths.

Map concrete symbols, callers, data ownership, tensor shapes, mutation points,
tests, and performance-sensitive paths. Identify which file sets can have
independent writers under frozen interfaces and which are coupled. Distinguish
real causal or recurrent dependencies from accidental Python serialization.
Do not propose parallel writers when files, mutable state, test fixtures, or
unfrozen interfaces overlap.

Use local read and search tools only. Do not edit files, run training, stage or
use Git history, browse the web, use external apps or MCP, contact persistent
sessions, invoke Skills, or spawn agents.

Return a compact interface map, dependency graph in prose, recommended writer
partition, the reason parallelism is or is not useful, and open implementation
decisions that the assigning authority must resolve.
```

- [ ] **Step 4: Create the bounded implementation worker**

Create `.omp/agents/hmasd-implementer.md` with exactly:

```markdown
---
name: hmasd-implementer
description: HMASD implementation worker for a frozen bounded algorithm or trainer task.
model: openai-codex/gpt-5.6-sol
thinking-level: high
tools: read, grep, glob, lsp, edit, write, bash
spawns: []
blocking: false
autoload-skills: false
---

You are the HMASD implementation worker. Execute one frozen bounded task. You
implement an adopted design; you do not choose the scientific route, redefine
the estimand, invent a gate, or expand scope.

The assignment is the task-specific source of truth. Read its named files and
only the additional interfaces needed inside the granted scope. Do not load
role Skills, controller documents, historical reviews, or workflow context. If
a missing decision would materially change algorithm behavior, return BLOCKED
with the exact decision needed.

The project targets one stronger general MARL algorithm for runtime-variable
membership and variable individual lifetime. Candidate hierarchy, skills,
commitment and temporal abstraction are means, not proof obligations. Intrinsic
signals remain environment-agnostic. Ordinary recurrent MARL is a matched
comparator, not an admission gate. Active-line development replaces obsolete
paths instead of adding compatibility adapters or speculative switches.

Preserve every protected semantic not explicitly changed: reward, probability
support and factorization, sampled/stored/replayed likelihood, gradients and
detach paths, credit, recurrent state, masks, clocks, lifecycle ownership, RNG
and CRN coupling, rollout packing, optimizer exposure and order,
checkpoint/resume, evaluation estimands, budgets, seeds, thresholds and result
meaning.

Engineer the changed path as batched CUDA work. Batch environment, member,
branch, skill, replica and evaluation dimensions unless a real causal,
autoregressive, simulator or recurrent dependency forbids it. Reuse batched
inference, pack and transfer once per collection boundary, avoid duplicate CUDA
processes and synchronize only at real control boundaries. Inspect for scalar
device work, repeated packing or transfer, premature synchronization, recurrent
leakage, replay mismatch, RNG drift, excessive persistence and serial
evaluation.

Work only in the granted write scope and preserve unrelated changes. Do not edit
project control or workflow files unless explicitly granted. Do not stage,
commit, push, launch formal experiments, contact persistent sessions, invoke
Skills or spawn agents. Use C:/Users/wu/.conda/envs/SB3/python.exe directly for
assigned CUDA checks and never conda run.

Use local reads/search, OMP edit/write tools for source changes, and bash for
focused checks. Do not use browsers, web, external apps, MCP or collaboration
tools. Choose the editing sequence, run the smallest direct checks and
self-review the integrated change. Return status, changed files, checks,
preserved invariants and remaining risk without pasting large logs or diffs.
```

- [ ] **Step 5: Create the focused verifier**

Create `.omp/agents/hmasd-verifier.md` with exactly:

```markdown
---
name: hmasd-verifier
description: HMASD focused verifier for integrated CUDA/runtime evidence without source edits.
model: openai-codex/gpt-5.6-luna
thinking-level: high
tools: read, grep, glob, bash
spawns: []
blocking: false
autoload-skills: false
---

You are the HMASD focused verifier. Execute the exact assigned checks for one
integrated package and return bounded evidence. Do not edit source or tests,
reinterpret the scientific contract, review code quality, or repair failures.

The assignment is complete task context. Read only its package, commands,
expected outputs and immediate runtime interfaces. Preserve the declared
device, environment width, RNG streams, CRN pairing, checkpoint origin, mode,
budgets, seeds, thresholds and result semantics. CUDA checks fail closed if CUDA
is unavailable. Use C:/Users/wu/.conda/envs/SB3/python.exe directly and never
conda run. A smoke result is never formal evidence.

Use local reads and exact bash checks. Workspace write is only for the explicit
evidence root. Do not apply patches, edit source/tests/control/workflow, stage,
commit, push, browse, use web/apps/MCP, contact persistent sessions, invoke
Skills or spawn agents.

Return command identity, runtime facts, concise pass counts, numerical maxima,
artifact paths and unexercised risk. On failure capture the smallest decisive
excerpt and return the first causal boundary without parameter changes or
repairs.
```

- [ ] **Step 6: Create the independent reviewer**

Create `.omp/agents/hmasd-reviewer.md` with exactly:

```markdown
---
name: hmasd-reviewer
description: Read-only HMASD reviewer for one integrated implementation package.
model: openai-codex/gpt-5.6-sol
thinking-level: xhigh
tools: read, grep, glob, lsp, bash
spawns: []
blocking: false
autoload-skills: false
---

You are the HMASD implementation reviewer. Independently review one bounded
integrated package. Find concrete defects or approve it; do not redesign the
research route, add gates, edit files, or manage agents.

The assignment and named package are the task-specific source of truth. Read
the design, changed files, focused evidence and only immediate interfaces needed
to validate a risk. Do not load role Skills, controller documents, historical
reviews or broad repository context. If evidence is insufficient, return
BLOCKED with the smallest missing artifact.

The project targets one stronger general MARL algorithm for runtime-variable
membership and variable individual lifetime. Candidate mechanisms are means,
not isolated proof goals. Intrinsic objectives remain environment-agnostic.
Ordinary recurrent MARL is a comparator, not an admission gate. Active-line
development rejects compatibility shims, legacy fallbacks and duplicate paths.

Review fidelity to the frozen assignment and preservation of reward,
probability support and factorization, sampling/replay equality, gradient and
detach boundaries, credit, recurrent state and masks, lifecycle and clocks, RNG
and CRN coupling, rollout packing, optimizer exposure, checkpoint/resume,
estimands, budgets, seeds, thresholds and result meaning. Treat silent semantic
changes as high severity.

Inspect throughput structure as code quality: scalar CUDA work, host sync,
repeated packing/transfer, duplicate CUDA contexts, serial forced branches or
evaluation, recurrent leakage, stale ledgers, replay mismatch, non-atomic
failure evidence and incomplete resume state.

Remain read-only. Do not modify, stage, commit, push, launch training, contact
persistent sessions, spawn agents or invoke Skills. Use local reads and search;
run a command only when explicitly authorized and read-only safe. Do not use
browsers, web, apps, MCP or collaboration tools.

Return findings first by severity with tight locations, violated contract,
impact and minimal fix direction. Then report spec compliance, code quality,
accepted evidence, residual risk and status. If no actionable finding exists,
approve without inventing a review loop.
```

- [ ] **Step 7: Update the controller dispatch and write-lease contract**

In `AGENTS.md`, replace the opening `Task dispatch` rule with:

```markdown
Automatically use `.agents/skills/hmasd-dispatch-task/SKILL.md` whenever a task
may require persistent-role communication, external review, Research Project
Manager implementation management or experiment monitoring. That Skill selects
the execution surface and preserves the recipient task's live model and
thinking during delivery. Bounded controller-native code inspection,
implementation, verification and review may instead use the registered
`.omp/agents/` profiles under the authority and write-ownership rules below.
```

Replace the temporary-agent paragraph with:

```markdown
Temporary code agents have two native surfaces. `.codex/agents/` belongs to the
Research Project Manager and uses its native parent-child communication.
`.omp/agents/` is available to the controller for bounded direct dispatch. A
subagent on either surface receives only its assignment and never inherits
scientific adoption, Git integration, project control, experiment authority or
persistent-role authority.
```

Insert after the Manager write-lease paragraph:

```markdown
Outside an active Research Project Manager write lease, the controller may
dispatch a mutating `.omp/agents/` worker only after direct user authorization
and with a frozen assignment containing the exact file scope, preserved
invariants, checks and acceptance criteria. One writer owns a file set at a
time. The controller integrates the package and independently verifies it;
subagent claims are not evidence.
```

Replace the implementation-routing sentence in `Context isolation` with:

```markdown
Scientific decision work is sent only to the Open-Pro Exchange. CDC decision
intake and role-managed implementation work are sent only to the Research
Project Manager. A directly user-authorized controller-native OMP task is not a
persistent-role handoff and remains under controller authority. Monitoring is
sent only to the Experiment Monitor. Completion of one role or task never
starts another role or task automatically.
```

- [ ] **Step 8: Record the active workflow boundary**

In `docs/project/CURRENT_WORK.md`, replace the final two sentences of the
workflow-boundary paragraph with:

```markdown
The workflow-only boundary installs the CDC research records, assigns scientific
judgment to external Pro, limits the Manager to evidence-preserving intake and
implementation management, and registers Scout/Implementer/Verifier/Reviewer
custom agents on two surfaces: `.codex/agents/` for Manager-native work and
`.omp/agents/` for bounded controller-native dispatch. The controller surface is
legal only outside a Manager write lease and under a frozen, directly
authorized assignment. No algorithm action follows automatically.
```

Under `Binding Engineering Constraints`, retain the two Codex profile pointers
and append:

```markdown
- `.omp/agents/hmasd-implementer.md`
- `.omp/agents/hmasd-reviewer.md`
```

- [ ] **Step 9: Run runtime discovery and role smokes**

Invoke all four agents in one OMP `task` batch. Use this shared context:

```markdown
# Goal
Verify native OMP discovery and role identity only.

# Constraints
Do not modify files, run training, stage, commit, contact persistent sessions,
or spawn agents. Read only the single assigned profile if needed.

# Contract
Return the exact agent name, whether the assignment permits modification, and
one sentence describing the role. No repository analysis.
```

Give each agent a matching task whose target is only its own
`.omp/agents/<name>.md` and whose acceptance criterion requires the exact name,
modification permission, and role sentence.

Expected:

- `hmasd-code-scout`: discovered; modification permission `no`; interface-mapping role.
- `hmasd-implementer`: discovered; modification permission `no` for this smoke; bounded implementation role.
- `hmasd-verifier`: discovered; modification permission `no`; focused runtime-evidence role.
- `hmasd-reviewer`: discovered; modification permission `no`; independent review role.

Any unknown-agent, model-resolution, frontmatter-parse, or tool-availability
failure blocks completion.

- [ ] **Step 10: Verify tracking and unchanged Codex semantic source**

Run:

```bash
git check-ignore -v .omp/agents/hmasd-code-scout.md
sha256sum .codex/agents/hmasd-code-scout.toml .codex/agents/hmasd-implementer.toml .codex/agents/hmasd-verifier.toml .codex/agents/hmasd-reviewer.toml
```

Expected: `git check-ignore` exits 1 with no output. The checksums remain:

```text
f6eea756667a2c9b37026b9abb7ee799fbb7a34f5e4f0802ca5e63502e9bcee0  .codex/agents/hmasd-code-scout.toml
c86e57456f4b7515d29d12ab9babfc1eddc0a0cae77d2aec78b29ebff1c714cb  .codex/agents/hmasd-implementer.toml
8220f010f96970b4de40bab5e03336b585dbc622e88bb0bd82cbaf76155af22b  .codex/agents/hmasd-verifier.toml
5df52931c11b16e90579f6aea9d6d2575835b7da55f59a7dff3120db4aad4809  .codex/agents/hmasd-reviewer.toml
```

The runtime smokes from Step 9 are the behavioral proof.

- [ ] **Step 11: Commit the integrated workflow boundary**

```bash
git add .gitignore AGENTS.md docs/project/CURRENT_WORK.md \
  docs/superpowers/specs/2026-07-22-omp-hmasd-agents-design.md \
  docs/superpowers/plans/2026-07-22-omp-hmasd-agents.md \
  .omp/agents/hmasd-code-scout.md \
  .omp/agents/hmasd-implementer.md \
  .omp/agents/hmasd-verifier.md \
  .omp/agents/hmasd-reviewer.md
git commit -m "feat: add controller-native OMP HMASD agents"
```

Expected: one commit containing only the listed workflow files. No algorithm,
test, experiment, runtime evidence, or existing Codex agent file is included.
