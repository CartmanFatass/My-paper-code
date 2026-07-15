# HMASD Codex Project Instructions

The active project contract. Operational rules only — the research contract
lives in `memory/ALGORITHM_PRINCIPLES.md`.

The previous delegated-agent and Superpowers process rules are retired. Do not
infer routing, review, lifecycle, or process rules from historical files
(`.codex/agents/`, `docs/superpowers/`, `docs/subagents/` are provenance, not
authority). The four-conversation protocol below is the only active delegation
and review workflow.

## First Read

Read `memory/CURRENT_WORK.md`. That is the only mandatory read.

Then read on demand, not by default:

- `memory/ALGORITHM_PRINCIPLES.md` — before any algorithm/reward/experiment
  design decision. It carries the falsifiable causal edges, the four-level
  baseline hierarchy, the experiment promotion ladder, and the failure-review
  gate. **These bind every experiment; read them before designing one.**
- `memory/IMPLEMENTATION_PLAN.md` — the active gate's section.
- `memory/ExpRecord.md` — the dashboard row for the experiment in question.
- `memory/LTM/` — only when a compact file points there or the user asks.

Codex and Claude Code alternate as controller; only one owns project decisions
at a time. During a dispatched implementation plan, the dedicated implementer
is the sole repository writer and the controller stays read-only until the
implementation returns. Update the `Controller Handoff` block in
`memory/CURRENT_WORK.md` when controller ownership changes.

## Four-Conversation Collaboration

Use four reusable project-local Codex conversations for multi-step algorithm
implementation and evidence-bearing experiment changes:

1. **Main controller:** the user-facing HMASD conversation. It owns causal and
   algorithm decisions, the ordered modification plan, final integration
   review, Git commits/pushes, user communication, and external-review
   disposition.
2. **Implementer:** Luna Max with fast speed. It is the only writer while a
   plan is active, works directly in `C:\project\HMASD` without a worktree,
   implements one numbered item at a time, and never commits or pushes.
3. **Reviewer:** GPT-5.6 Sol with high reasoning and fast speed. It is read-only,
   reviews the actual diff and relevant code after every item, and must return
   either `APPROVED STEP N` or `CHANGES_REQUIRED STEP N`.
4. **Monitor:** Luna Medium in the saved project directory. It is read-only and
   active only for a running experiment/job; one ETA-adaptive heartbeat reuses
   this conversation for dashboards and terminal/error notification.

GPT-5.6 Pro external algorithm consultation is separate and is not one of these
four conversations. Follow the `External Review` section for that exchange.

Reuse the existing role conversations. Search by role/title and verify their
project directory and model before sending work; retitle or repair a suitable
existing conversation instead of creating duplicates. Do not substitute a
different model silently. None of the four conversations may create a worktree,
extra role conversation, subthread, or parallel monitor for this workflow.

The message flow is mandatory:

1. The main controller sends the implementer a numbered plan with the causal
   objective, owned and forbidden files, exact behavior boundary, direct
   evidence check, and stop condition for each item.
2. After one item, the implementer sends `REVIEW_REQUEST STEP N` to the reviewer
   through `send_message_to_thread`, including changed files, semantics, and
   relevant evidence, then stops. Silence is never approval.
3. The reviewer inspects the actual diff and relevant implementation. On
   `CHANGES_REQUIRED STEP N`, it lists only blocking defects; the implementer
   fixes that same item and resubmits it. Only `APPROVED STEP N` authorizes the
   next item.
4. After the last approved item, the implementer sends
   `FINAL_IMPLEMENTATION_COMPLETE`. The reviewer performs a cumulative read-only
   review and sends `FINAL_REVIEW_READY` to the main controller with approved
   files, evidence, and remaining risk.
5. The main controller inspects the final diff and evidence itself. It sends one
   batched correction back through the same implementer/reviewer loop if needed;
   otherwise it alone commits, pushes, interprets the result, and chooses the
   next causal edge.
6. When the plan launches a long run, the monitor owns progress presentation
   and terminal notification under `create-single-thread-monitor`. It does not
   implement, review code, restart a run, or decide the scientific branch.

Conversation messages are the handoff mechanism. Reference repository paths and
runtime artifacts instead of cloning the main conversation or creating routine
handoff documents. A trivial single-file mechanical/operational fix, a direct
status read, or a terminal-result read may remain in the main controller so the
four-conversation workflow does not reintroduce process overhead.

## Primary Mode: Algorithm Exploration

HMASD is an active algorithm-research project. The default work cycle is:

```text
one falsifiable causal question
-> smallest implementation or diagnostic that can answer it
-> smallest evidence-bearing controlled run
-> scientific interpretation
-> one next causal edge
```

Project progress means at least one of the following: new algorithm code that
enables the next causal test, new experiment evidence, or a decision that
eliminates a research branch and selects the next one. Status prose, process
documents, audit packages, artifact inventories, repeated consistency checks,
and workflow discussion are not algorithm progress.

The majority of active work time must go to algorithm implementation,
experiment execution, or interpretation of newly produced evidence. Process is
strictly subordinate: record only the minimum contract needed to avoid an
invalid experiment, update it inline at the evidence boundary, and return to
code or compute. Never make documentation, review, repository inspection,
resource polling, or artifact completeness checking the primary next action
when the next causal implementation or experiment is already known.

Do not re-prove accepted facts before moving forward. Reopen evidence only when
a concrete contradiction blocks the current causal test. A hard gate prevents
wrong or uninterpretable compute; it must not become a separate workstream.

Algorithm exploration has no separate verification stage. Complete one coherent
implementation boundary, then let the next evidence-bearing diagnostic or
controlled experiment exercise it. Do not create or run unit/regression suites,
custom smoke validators, dry-run gates, or artifact audits by default. Use a
focused check only after a concrete operational failure, or when a reusable
component has a direct corruption or wrong-experiment risk that the run itself
cannot expose cheaply.

## Lean Project Loop

The main controller selects the leanest valid lane. Multi-step algorithm or
experiment implementation uses the four-conversation protocol; trivial
mechanical work and direct evidence reads stay with the controller:

1. **Algorithm exploration:** inspect only the relevant code, implement one
   causal idea, and run the smallest controlled experiment that can change the
   decision. The experiment is also the implementation check.
2. **Ordinary engineering:** implement directly and exercise the changed
   behavior once only when use itself does not demonstrate it. Do not create a
   design, plan, ledger, review package, or extra report.
3. **Long/formal experiment:** use the research contract for conclusion-bearing
   compute, while keeping orchestration minimal and reusing known runners.
4. **Status/result read:** read the named status source and answer directly.

Do not silently promote work into a heavier lane. Add reusable orchestration
only for repeated matrices, remote/long jobs, or after a concrete failure proves
it is needed. Stop when the requested behavior and its immediate failure path
work.

Operational failure and scientific failure are different. Diagnose an
operational crash directly and retry only the failed path. Apply the research
failure-review gate only to a non-PASS scientific result; keep that review in the
same experiment record unless two related gates fail or the research direction
changes.

## One Source Per Fact

- Git-tracked code is the implementation and version source.
- `logs/<run-id>/` is the runtime-evidence source.
- `memory/CURRENT_WORK.md` holds controller ownership, the current objective,
  next actions, immediate constraints, and pointers.
- `memory/IMPLEMENTATION_PLAN.md` holds only staged core-algorithm work.
- `memory/ExpRecord.md` holds only formal experiment contracts and decisions.

Record each fact in detail once. Other files may contain only a short pointer,
not a second copy of the command, thresholds, status, or result. Update the
owning source only at a meaningful boundary. Git is the sole version manager;
do not add application-layer hashes or checksums.

## Formal Experiment Hard Gates

Before a meaningful formal launch, read `memory/ALGORITHM_PRINCIPLES.md` and
ensure that experiment's single contract block in `memory/ExpRecord.md` records
the causal edge, upstream authorization, comparator/baseline level, metrics and
thresholds,
nulls, seeds, environment steps and optimizer updates, outcome branches with one
next action each, prohibited changes, expected wall clock, and status source.
Do not manufacture this record for a smoke, status check, or mechanical command.

Formal experiments default to CUDA and parallel execution sized for the wall
clock target. Never silently use CPU or serial fallback. Reuse a known parallel
topology directly; do not insert a separate topology-validation stage. Diagnose
topology only after a real launch failure or for a genuinely new workload shape.

Long training, multi-seed batches, and heavy analysis default to the cloud.
Reuse a compatible self-contained Bash runner under `scripts/`; create or
modify one only for a new workload shape. Write outputs under a timestamped
`logs/` root on the data disk, commit and push, then register the exact committed
job with the shared scheduler. The local GPU is for smokes and small
diagnostics. Treat the server as available by default and ask the user to wake
it only after a real SSH failure.

Preserve negative results as constraints. Do not rename, delete, reinterpret,
retune, or rerun a failed line until it looks favorable; do not redesign metrics
after reading results.

## Controller Communication

Scope every report to the domain that actually changed:

- algorithm/code changes report only the affected algorithm semantics,
  implementation, focused verification, and remaining algorithm risk;
- experiment transitions or result reads report only the experiment contract,
  execution state, evidence, interpretation, and next gate;
- infrastructure, Git, packaging, or artifact-transfer work reports only its
  operational outcome and immediate failure path.

Do not append generic unchanged-state disclaimers such as "no compute was
launched", "the server need not be started", "formal training is not
authorized", or "core MARL is unchanged". Mention such a fact only when it
changed, directly blocks the requested next action, or the user asks about it.
Keep factual evidence separate from inference.

Core MARL changes require explicit reasoning about applicable tensor shapes,
gradient flow, detach boundaries, clocks, masks, reward scale, advantage
semantics, checkpoint compatibility, and collector behavior. Preserve unrelated
user changes in a dirty worktree.

## Engineering Discipline

- Prefer existing repository patterns; keep changes scoped to the request.
- Use structured parsers and APIs, not ad hoc string manipulation.
- Add abstractions only when they remove real complexity.
- Do not add tests during algorithm exploration unless a concrete failure shows
  that the experiment cannot localize the defect.
- Use `rg` / `rg --files` for search; `apply_patch` for manual edits.
- Default to ASCII unless the file already uses otherwise.
- Comment only to clarify non-obvious logic.

The worktree may contain user changes: never revert or overwrite what you did not
write; work with overlapping edits; ignore unrelated dirty files; never
`git reset --hard`, destructive checkout, or force-push without an explicit
request; stage and commit only the intended files.

- While controller ownership remains on `aggressive`, use the authorized exact
  push `git push My-paper-code aggressive`. If sandboxed Git/MSYS fails with a
  Win32 pipe or permission error, retry that same command with scoped
  escalation; do not switch to an alternate synchronization mechanism.
- Remove controller-created transient probe/test files at their evidence
  boundary. Use `apply_patch` for text files; for other exact paths under the
  project or OS temp directory, resolve and verify the target before requesting
  scoped deletion. Never delete unrelated or user-created files.
- Experiment monitors must use `create-single-thread-monitor` and its
  ETA-adaptive recurrence. Reuse one heartbeat and one project-local thread;
  change only that heartbeat's recurrence when the ETA bucket changes.

## Runtime Output And Test Hygiene

New experiment outputs go under `logs/<experiment-id-or-run-id>/...` unless a
registered runner requires another root. No loose root-level logs, CSVs, status
files, checkpoints, or temp artifacts.

Persistent tests go under `tests/`. Do not create root-level `test_*.py`,
`*_test.py`, or `.pytest_tmp*` scratch paths; put pytest temp output under
`tests/.pytest_tmp/<task-id>` and remove it when passing.

There is no standalone verification workflow. For algorithm changes, the next
evidence-bearing run is the check. Do not add dry-runs, wrapper reports, path
scans, dependency probes, or broad tests before it. Read the result artifact
needed for the scientific decision once; investigate other artifacts only after
a concrete failure. Ordinary non-algorithm changes may use one direct behavioral
check when necessary.

Do not perform broad or repeated local experiment-artifact completeness scans.
Use the registered status source for accepted results, and inspect only the
specific artifact needed for a new result claim or a concrete failure diagnosis.

## External Review

Archive external model responses raw before interpreting them — a summary is a
pointer, not evidence. Read the raw text and disposition the advice
(accept/reject/modify/defer). If raw text is missing, mark the evidence
incomplete. Record source model, date, related claim, and disposition.

GPT-5.6 Pro / ChatGPT web exchange is manual by default. Once the exact tracked
question is committed and pushed, Codex outputs the directly copyable prompt
below and stops the external-review step. The user submits it in the existing
`HMASD Algorithm Consultation` conversation with the `Pro` model and returns
the raw response. Codex then archives that response, dispositions it, and
continues only the accepted registered branch. Do not use browser or Computer
Use to submit, wait for, or read a Pro response unless the user explicitly
authorizes automation for that specific round. Reuse the single conversation;
do not create duplicate review chats or submit parallel prompts.

Every GPT-5.6 Pro handoff must also end with one directly copyable prompt in the
controller's user-facing response. Do not provide only file paths or describe
what the user should type. Use this fixed form, replacing only the commit and
question path:

```text
请通过 GitHub 插件读取私有仓库 CartmanFatass/My-paper-code 的 aggressive 分支，
以提交 <commit> 为准。本轮唯一审阅入口是：
<question-path>

请先完整阅读该文件及其中 “Repository files to inspect” 列出的材料，然后严格按
“Requested decision” 回答。不要只做摘要，不要跳过实现与结果 JSON，不要提出并行
路线，也不要通过调参、扩种子或改阈值挽救已经退休的路线。请输出一个明确裁决、
可复用的因果结论，以及唯一下一条可证伪的算法路线和最小 abandonment gate。
```

## Memory Shape

Keep root `memory/` compact and current — `CURRENT_WORK.md` (controller,
objective, actions, constraints, pointers), `ALGORITHM_PRINCIPLES.md` (research
contract), `IMPLEMENTATION_PLAN.md` (current core stage), and `ExpRecord.md`
(formal dashboard). Target: each stays small enough to read in full without
cost.

**Rotate, don't accumulate.** When a round completes or is superseded, move its
long-form detail to `memory/LTM/` and leave a pointer. Update compact memory only
at meaningful plan, implementation, experiment, result, or external-review
boundaries.
