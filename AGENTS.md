# HMASD Controller Contract

## Entry and authority

The active OMP root task is the sole Controller. Read
`docs/project/CURRENT_WORK.md` first, then only the artifact needed for the
current action. The research method is defined once in
`docs/project/RESEARCH_WORKFLOW.md`; do not restate it in task prompts or other
workflow files.

The current autonomous research chain is paused by the user. During the pause,
no external submission, research-agent wave, implementation or experiment may
start. Workflow cleanup requested by the user is authorized.

The Controller owns research scheduling, executable algorithm realization,
local-agent coordination, Git integration, experiment authorization and user
communication. It may push only `Claude`; it must not mutate `aggressive` or
another branch.

## Evidence and control

Git branch and commit are the sole artifact identity and provenance mechanism.
Do not create per-file hashes, source manifests, receipt schemas, response
markers, stable-snapshot cycles, archival validators, workflow topology tests or
duplicated handoff ledgers. Do not replace scientific judgment with file
completeness checks.

Observed evidence remains fixed in meaning. Corrections use a new commit and
state the delta; a negative result is never renamed as success.

`docs/project/CURRENT_WORK.md` is the only active control-plane file.
`docs/project/ExpRecord.md` exists only for an actual
experiment contract or disposition. Historical external reviews and research
notes are evidence, not approval gates.

## Agents and write ownership

Active local profiles are `hmasd-code-scout`, `hmasd-research-scout`,
`hmasd-implementer`, `hmasd-frontier-implementer`, `hmasd-reviewer`,
`hmasd-verifier` and `hmasd-exp-manager`. Children do not spawn successors and
never perform Git operations.
`hmasd-research-scout` is a bounded read-only scientific explorer: each
Controller assignment names exactly one approach family, and the scout returns
concrete scientific objects or explicitly `NON_IDENTIFYING` evidence. It never
implements, computes, selects or accepts science, or schedules successors.

Use agents dynamically only for genuinely independent approaches or file
scopes. Preserve early scientific independence and require concrete outputs.
One writer owns a file scope at a time. The Controller integrates and commits.
Review and repair follow the single-gate rule in
`docs/project/RESEARCH_WORKFLOW.md`; do not add another review policy here.

The persistent `experiment_monitor` observes only one already-authorized run. It
does not launch, restart, repair, extend or scientifically interpret it.

## External review

External Pro review is optional and used only at the boundaries named in
`RESEARCH_WORKFLOW.md`. Open Pro generates distinct conjectures,
counterexamples, hidden assumptions, corrected definitions and retained lemmas;
it does not choose the only legal successor or write an implementation plan.
The Controller selects the next action.

When external review is used, the Controller operates the pinned authenticated
BrowserMCP tab directly. A pushed `Claude` commit is the evidence boundary. Save
the natural response as ordinary scientific evidence only when useful. Do not
delegate browser transport or create validation/archival machinery. Reconcile an
indeterminate submit once from the visible conversation; never duplicate
blindly.

## Protected algorithm semantics

Strict authorization applies to reward and intrinsic signals, probability
factorization, gradients and detach paths, recurrent state, masks, clocks, RNG,
replay, credit and checkpoint meaning. Intrinsic mechanisms may not consume
external reward, task fields, identity, roles, goals, success predicates or
progress measures.

When implementation is the selected discriminator, the Controller compares 2–3
executable designs and freezes only the smallest sound plan: exact files,
interfaces, protected invariants, focused check and expected observation. A
formal run additionally requires current authority and a concise
`ExpRecord.md` contract.

## Active-line development

Backward compatibility is not required. Delete superseded code, workflow
scripts, schemas, profiles, tests and inactive fallbacks in the same Git
boundary. Git history is the archive. Preserve unrelated user changes and unique
scientific evidence.

Verification exercises the changed behavior. Performance inspection covers
avoidable allocation or copies, repeated packing/transfer, premature
synchronization, recurrent leakage, replay mismatch, RNG drift and serial
evaluation.
