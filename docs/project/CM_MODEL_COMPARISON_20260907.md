# Three prospective CM same-spec comparisons

OWNER_DIRECT 2026-09-07: compare models on **newly assigned real CM work**, not historical
replays, for three batches. Every arm receives the **same code spec**, task and starting code.
Codex arms report token consumption and completion time. Other arms use the installed headless
Claude Code, Grok Build and omp clients. Gemini 3.8 Flash **High** is owner-selected.

This named core task authorizes only the fixed headless process launches, matched-input
recording/checks and existing Codex token accounting needed for these three comparisons
(ENGINEERING_SCOPE_SPEC section 4). The check compares source content, not commit identity.
No general scheduler, retry system, research admission gate or standing telemetry is added.

## Capture the next three new assignments

Root owns dispatch and records; the assigning DM owns the real code spec. At the next three
new CM engineering assignments after this instruction, before any participant begins solving,
capture the task verbatim, the complete code spec, applicable CM role instructions, required
input paths at their exact committed source revision, owned paths, scientific invariants and
original acceptance commands. Do not choose familiar completed tasks, replay old work, or enroll
an already-started CM assignment. Corrections to an existing assignment are not a new batch.
Pure result-bearing launches/observation or science decisions are not engineering comparisons;
record any such exclusion briefly without converting them to old-task benchmarks.

Freeze one `code-spec.md`, one `task.md` and one `prompt.md` per batch. The common prompt includes
the same role instructions and full task/spec text for every arm, without model-specific
summarization, translation, extra hints or different acceptance conditions. Record the SHA-256
of these bytes and full starting Git SHA in `batch.json`. Source/spec capture is for this
owner-requested comparison only, not a new gate on ordinary research experiments.

Batch roots: `temp/cm-model-comparison/20260907/batch-01/` through `batch-03/` on the local
control plane. Root records the actual assignment time, sender, fresh native identities, CLI
versions, requested/resolved models, paths, start/end facts and final artifacts there. Maintain
the three-row progress table below at clean boundaries. Stop enrolling after three batches;
no standing benchmark service or extra scheduler follows. Existing goal drives the work.

## Participants and identical deliverable

| Arm | Execution route | Requested model / effort |
| --- | --- | --- |
| baseline | Fresh native configured `hmasd-cm` for the real assignment | Current configured CM: `gpt-6-astra` / `medium`; retain actual recorded setting |
| sol | Fresh native default agent, supplied the same CM role text | `gpt-5.6-sol` / `high`, `fork_turns=none` |
| claude | Claude Code headless | `opus` / `high`; record actual resolved Opus ID, no fallback |
| grok | Grok Build headless | `grok-4.6` / `high` |
| omp | omp headless | `google-antigravity/gemini-3.8-flash-high` / `high` |

Use separate detached local worktrees at the **same starting SHA** for all five arms. This is
the concrete temporary-isolation exception for these three comparisons; no authoring branch
is created. Preserve the direction's designated authoring checkout for later normal integration.
All participants implement the newly assigned engineering deliverable directly and return their
diff plus evidence from the same focused acceptance commands. End the timed task at that return.
No participant reads another arm's output, branches, sessions or solution. Each receives the
same clarification only if the original code spec is amended; record a material amendment and
do not call unmatched runs comparable. Do not edit a frozen spec differently for each model.

The common prompt explicitly overrides ordinary commit/delegation behavior for this comparison:
work only in the supplied test worktree and owned paths; leave changes for collection; do not
commit, push, message other tasks, spawn children, launch research experiments, send Pro requests,
or modify shared/runtime configuration. All arms can run the same original bounded engineering
checks. Preserve scientific launch budgets: comparison copies do not multiply experiment calls.
Independent scientific-risk review and production integration occur afterwards through the
normal DM/CM/Root route, outside the measured implementation task. The benchmark does not
automatically select a winner's code or change production models.

Remap absolute authoring paths to each arm's own worktree using one common relative-path rule
in the shared prompt; preserve the raw original task and code spec separately. Do not give
different code contents to accommodate a model. Explicitly state any runtime/tool differences:
this compares the requested model/client combinations, not an isolated model-only causal effect.

Use the assignment's engineering time budget. If it has none, all arms have the same 3,600-second
administrative limit, including client startup and checks; a timeout remains an incomplete arm,
not a scientific negative. Do not silently retry or replace unavailable models. Preserve partial
logs. A provider failure is reported separately from failure to satisfy the code spec.

## Dispatch and collection

Root captures all inputs and prepares five worktrees before dispatch. Immediately before
each of the five dispatches, record its HEAD and clean `git status --porcelain=v1
--untracked-files=all`; different source or starting edits are not a matched input. Supply identical
`prompt.md` bytes to both fresh native agents (self-contained prompt, no parent-history fork).
Record their actual returned IDs. Never use `create_thread` or change an existing app task's
model/effort for this test. A benchmark arm is not another research-direction slot.

For the other three arms, use the installed local CLIs through the bounded helper:

```text
python tools/model_comparison/run_headless.py --arm <claude|grok|omp> --cwd <arm-worktree> --prompt <same-prompt.md> --out <fresh-arm-output-dir> --source-sha <full-starting-sha> --timeout-seconds <common-limit>
```

Use an available Python 3.11+ interpreter. Launch each helper detached with hidden windows and
stdout/stderr files under the batch root; record its PID and observe through the existing goal.
The helper supplies exact requested models/efforts, uses noninteractive modes, keeps UTF-8 LF
prompt bytes, saves raw streams and measured process wall, and performs no automatic retry.
Claude's safe mode and omp's disabled customizations avoid unrelated hooks; the common prompt
explicitly supplies applicable project/CM instructions to every arm. Existing provider login is
used, without displaying or copying credentials. Inspect raw session model evidence before
acceptance; a requested alias is not proof of a resolved model. Do not run old-task or inference
smoke probes to qualify the clients; CLI help/model/auth reads are sufficient setup evidence.

After return, collect actual modified/untracked owned files and a patch outside each worktree,
plus final response, original focused-check output and any errors. Preserve worktrees until
evaluation and normal integration disposition are recorded. No blind branch cleanup or evidence
deletion is authorized. If a baseline's change is accepted, carry it into the existing direction
authoring checkout once under its ordinary review/commit/push procedure; don't merge all arms.

## Measurements and assessment

Use `codex-task-cost-analysis` and its bundled script with the fixed HMASD interpreter to compute
Codex measurements from completed native sessions. Use exact baseline/Sol IDs for each batch,
`compare --cohort-a <baseline-id> --cohort-b <sol-id> --unit task`, and save both its original
Markdown report and JSON output. Do not manually sum token events or count cache/reasoning tokens
twice. No nested agents are used during the measured tasks; review/integration overhead is
separate. Incomplete Codex sessions excluded by the script are reported as unmeasured/incomplete,
not zero. Report input, cached input, output/reasoning breakdown, total tokens and completion
duration from those script results. Price data are optional context, not the requested metric.

For the other three clients, retain the helper's measured elapsed time and raw transcripts;
token accounting is not required by this request. Verify actual completion rather than equating
exit zero with correctness. Apply the same existing code-spec checks to every arm, with identities
hidden from the correctness reviewer where practical. Record acceptance, material invariant/scope
violations, missing requirements, concrete defects and required repair. Do not add invented tests
or stronger scientific requirements to make an arm fail. Participant-run focused checks are
inside its measured implementation time; only independent post-return verification/review is
outside, and is reported separately if needed. No capability ranking from speed alone.

After all three batches return, publish one comparison with per-batch artifacts, exact model
settings, comparable task outcomes, Codex token/time results, provider failures and limitations.
Three real tasks support an observed task-specific comparison, not a general model ranking.

## Progress (Root updates facts only)

| Batch | New assignment / code spec / source | Baseline + Sol IDs | Other arm roots | State |
| --- | --- | --- | --- | --- |
| 01 | not yet captured | — | — | awaiting next new CM engineering assignment |
| 02 | not yet captured | — | — | awaiting next new CM engineering assignment |
| 03 | not yet captured | — | — | awaiting next new CM engineering assignment |

Ordinary capture/start/completion progress is log-only. Notify Portfolio for missing task/spec,
unavailable requested model, a material comparability conflict, or the final three-batch result.
