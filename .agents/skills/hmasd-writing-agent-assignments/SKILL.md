---
name: hmasd-writing-agent-assignments
description: Use when designing a task-scoped subagent or Root-relayed owner interface, writing a concrete assignment or message, or reviewing whether an interface preserves enough meaning and action capability.
---

# HMASD Writing Agent Assignments

This Skill is a reusable writing and reasoning aid for parents who delegate a
bounded task or prepare a Root-relayed owner interface. It protects the semantic contract
between requester and child without creating another authority, validator,
queue, approval state, or acceptance owner. The parent remains responsible for
the assignment, routing and acceptance boundaries already defined by the role
and workspace contract. In the active CLI topology, Root is the sole user,
cross-owner relay and lifecycle actor; same-level L1 owners use only their
registered L2 allow-list, and an L2 leaf returns only to its single parent.

When an L1 Role declares a scope-key field, the assignment names the concrete
semantic scope represented by that field. Multiple instances of that Role may
run in one Root tree only on distinct scope-key values, and the `(role,
scope_key)` pair is unique. The key locates semantic ownership/concurrency; it
is not a ticket, queue, ledger, registry, admission token or continuity/session
identity. Same writable paths or shared semantic contracts that remain
unfrozen are dependencies and serialize the affected slices.

Workspace, worktree, lifecycle, convergence and Git mechanics are defined once
by `docs/project/SESSION_WORKSPACE_CONTRACT.md`. This Skill only makes the
assignment's exact paths and validation consequence understandable; it does
not restate or create a worktree or lifecycle procedure.

## When to use it

Use this Skill when a parent is designing a subagent or Root-relayed
interface, writing the concrete brief or message that will be sent, or
reviewing whether an existing interface preserves enough meaning and
capability. It applies to code, research, review, browser, transport and other
non-code work. The trigger is the communication problem, not a particular
file format or child model.

### Root-facing L1 display labels

When writing a Root-dispatched L1 assignment or its progress/report wording,
apply the defining `l1_user_facing_display_contract` in
`docs/project/SESSION_WORKSPACE_CONTRACT.md`, under its `L1 user-facing
display names` heading: use `WM_<purpose>` for Workflow
Manager control-plane work, `EM_<direction>` for the actual Independent
Research Explorer Manager, and `CM_<purpose_or_direction>` for Code Manager
work. Keep suffixes short and informative, and do not rename immutable
internal task IDs or registered profile/types. A WM suffix may name a
research-routing target but must remain visibly workflow work; research
execution belongs under EM. For WM research-routing changes, preserve the
clarity fields `research_execution=false` and `science_state_changed=false`;
only a separate authorized EM science result that actually exists can supply
different research or science evidence. The label change itself performs no
research and changes no science state.

For direction-scoped owner assignments, keep the scope explicit and narrow:
EM may receive only `direction:<id>`, while CM may receive only
`direction:<id>` or `shared:<component>`. Every `<id>` or `<component>` is a
safe atom matching `[a-z0-9][a-z0-9._-]{0,63}`; reject empty values, extra
colons, separators, whitespace and `..`. Do not create a portfolio scope,
integration scope, standing/fresh domain-convergence lane or all-shared scope.
Root owns macro/portfolio comparison, ranking, pause/continue, dependencies
and complete-map acceptance; direction/shared CM acceptance is final for its
slice, Root mechanically integrates and runs union Tests/Static, and semantic
conflicts return to the owning CM(s) or a temporary named shared CM. Formal or
project-canonical science remains at the user/External Pro boundary.

### Risk, reviewer and manager-capacity guidance

Classify the assignment package by semantic consequence before dispatch, never
by file count. `high` covers authority, topology, cross-owner or shared-contract
impact and requires the registered read-only Auditor. `bounded_contract` covers
a stable cross-file contract within one owner; a clear route may skip a new
Auditor when WDM records its rationale. `low_causal_repair` covers wording, a
recognizer or one bounded assertion family that preserves accepted meaning;
WDM may skip the Auditor with rationale even when tightly coupled files exceed
one. This is a routing choice, not an admission state, gate or second owner.

Use the canonical Session keys `workflow_change_risk_tiers` and
`workflow_route_table_policy` when naming this consequence. Planning first
consults `docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md`: a clear row supplies
the defining source, direct consumers and focused tests; a missing, ambiguous,
conflicting or authority-crossing route uses the bounded registered Auditor
instead of repository rediscovery or guessing.

Each package requires exactly one integrated advisory Reviewer, dispatched only
after the paths and direct evidence are frozen. The Reviewer is read-only and
advisory; its review cannot accept the package or replace WDM/Root ownership.
For one writable WDM L1 assignment, its exact final frozen bytes (including
disjoint Implementers) are one singleton package reviewed together; after the
checks and this one Reviewer, WDM may semantically accept it before returning
to Root. A fresh convergence WDM is needed only when Root combines two or more
independently reviewed candidates or the actual union differs from every
reviewed package. The fresh WDM uses one Reviewer and owns union acceptance.
Use the canonical Session keys `workflow_singleton_package`,
`workflow_singleton_acceptance` and
`workflow_multi_candidate_convergence_trigger` when carrying these meanings.
Skipping the Auditor never means skipping this Reviewer.

Manager capacity is an actionability check: an L1 dispatch requires useful
owned work and a useful action or matching leaf capacity. This is guidance for
choosing actionable work, not a quota, reservation, scheduler or pool, and it
does not create a queue or an admission mechanism.

Keep the shared display naming intact: use `WM_<purpose>` for Workflow Manager
control-plane work, `EM_<direction>` for the actual Independent Research
Explorer Manager, and `CM_<purpose_or_direction>` for Code Manager work. The
Session contract and registered Roles define the shared worktree, child Git,
routing and acceptance boundaries; this Skill only ensures the assignment
states the semantic action and exact paths.

## The normal path: compile a task model

Before choosing paths or a wire shape, understand the task in ordinary prose.
Compile a self-contained natural-language model that lets a capable child act
without reconstructing parent history. Explain, in whatever order best fits
the task:

Every assignment message starts with concise outcome-first prose. State the
requested outcome and the next responsible actor, and say why the outcome
matters. Make the concrete files, objects or decisions in scope, their
relationship, the owner of each action or decision and the consequence of
missing or unresolved work understandable without inherited context. Define
each non-obvious task-local term when it first appears, then append the factual
tail described below. The prose may use any concise form: no named heading or
token is required, and an unheaded message is valid and not noteworthy. Prefer
ordinary words to a new abbreviation; keep an exact canonical field name only
when it is needed and gloss its meaning once.

- why the task exists now and the concrete user-visible, operational or
  scientific outcome that matters;
- the concrete failure, conflict or limitation to resolve, when one is known;
- how the named modules, people, pages, files or sessions interact and which
  one owns each relevant state or action;
- decisions already frozen by the user, design or authority boundary;
- protected meaning, invariants, exclusions and consequences that must remain
  true;
- ordinary local judgment the child may use, including reversible choices;
- bounded recovery when an observation is incomplete or an action fails, and
  what must not be duplicated or silently invented;
- the evidence that demonstrates the requested outcome, including what would
  distinguish a partial or recognition-only result from completion.

Only after that explanation append factual anchors such as exact paths,
commands, schemas, result locations, model labels or `fork_turns` settings.
Those anchors narrow execution; they do not carry the task's meaning. A parent
is a context compiler, not a field copier. A shorter brief is correct when it
contains enough meaning for the bounded task.

An actionable assignment therefore has both layers: the ordinary explanation
and the smallest task-relevant factual tail. Depending on the task, that tail
may identify scope, paths or artifacts, the requested action or current status,
commands or observed evidence, an unresolved blocker and next owner, and
residual uncertainty when applicable. Narrative alone cannot pin the work to
the right objects, while fields alone cannot explain why the work matters;
neither is sufficient. Do not require irrelevant fields or a giant fixed schema, and do
not invent a hash—hashes remain only supplied locators or genuine integrity
boundaries already required by the existing contract.

### Native payload and file-backed assignment boundary

When the caller supplies no assignment-file locator, the complete native
payload in the brief is the exact authoritative assignment. The child must not
search for, reconstruct or infer an assignment file; missing required meaning
fails closed to the parent instead of triggering discovery. If a file-backed
assignment is required, the parent supplies its exact path, hash and authority.
That hash is a supplied locator or integrity fact, not a workflow admission,
acceptance or continuity mechanism. Mandatory Role/Skill immediate references
remain allowed and are distinct from assignment reconstruction. `rg` remains
valid for explicitly named fields or evidence locators; this boundary limits
unsourced assignment discovery, not search generally.

### Validation ownership and evidence scope

Every child brief must state, in ordinary language, the validation layer the
child owns, its exact paths, the smallest direct evidence that can demonstrate
that layer, and which later evidence belongs to WDM or Root. The validation
layer is a real boundary: a writer may own its assigned wording or focused
test, but does not own an integrated diff, a cross-slice conclusion, canonical
state, Git integration or final acceptance unless its Role explicitly says so.
Name the direct postcondition (for example, the changed file and its focused
test) and name the later WDM or Root observation that remains outstanding.

Do not assign a writer the whole suite. Keep test work to the smallest focused
checks that exercise the owned paths and consequence; the WDM decides whether
broader or integrated evidence is still needed. Exact paths constrain the
child's action, while direct and later evidence explain the meaning of those
paths. These are semantic brief contents, not a second schema or admission
gate, and they do not grant validation or acceptance authority.

For a WDM package, name one focused causal-family check after all consumed
producer, consumer and test bytes are frozen and before package acceptance.
State that its result is reusable only while those bytes remain unchanged. Keep
the canonical ownership split: `slice_local` for the writer,
`integration_cross_slice` for WDM and
`runtime_fresh_smoke_after_root_integration_reload` for Root.

### Small reverse-intake patch brief

For an Explorer Direction Action Map reverse intake, the self-contained brief
must carry a small semantic delta rather than the full map. State the canonical
source locator, candidate-target locator, Git revision locator, exact old/new
text or unified patch, and the frozen semantics and consequences. Name one exact
assignment-specific temporary `.patch` destination under
`temp/sessions/independent_research_explorer/<root-assignment>/state-proposals/`.
The Writer copies the supplied payload exactly and performs only destination,
payload-presence and UTF-8/LF checks. It must not load Explorer Mechanical or
another unrelated Skill, normalize or merge text, infer a target or interpret
scientific meaning. No full-map message, split/encoded payload, hash, digest,
byte count, length or JSON receipt is a workflow admission or acceptance
condition; a Git revision is only a source locator.

### Native default temporary-task exception

When an L1 has no listed specialist leaf that can perform the bounded task, a
native default child may be used only as the narrow temporary L2 exception
defined by the active role and router. Its self-contained brief must state,
before factual anchors:

- why no listed specialist matches or can perform this task, and why the
  specialist-first condition is satisfied;
- the exact caller-owned temporary paths and the mode, which is read-only
  unless the brief explicitly grants writes only to those exact temporary
  paths;
- every frozen authority limit: no spawn, user/sibling/cross-owner/cross-branch
  contact, canonical-state or Git write, owner acceptance, routing, compute,
  external-review, science, code-acceptance, runtime or transport authority,
  no durable, project-code or non-temporary write, and return only to the
  invoking L1 for any Root relay or acceptance;
- the expected observable completion product and the direct evidence that
  distinguishes completion from recognition or a status-only response; and
- the literal caller-action anchors `agent_type="default"`,
  `model="gpt-5.6-luna"`, `reasoning_effort="high"`, and
  `fork_turns="1"`, with the last being a caller action whose one forked turn
  is background only, not a profile/TOML field.

This exception does not create a generic profile or Role and never displaces a
matching professional leaf. The brief must preserve the named caller's
task-scoped temporary root and the existing Root-to-L1-to-L2 return boundary.

For a cross-owner dependency, describe the Root relay explicitly: the sending
owner returns the smallest complete request or conclusion to Root, Root assigns
the receiving same-level owner, and the receiver returns its acceptance or
result to Root. Do not encode direct sibling contact, manager-session or
replacement-task continuity. A production Agentify request names only the
parent-specific transport leaf and its requester partition; WDM is not a
production transport parent.

## Important distinctions

Keep these concepts separate when writing or reviewing an interface:

In short, distinguish file-only communication from low-semantic communication;
`fork_turns=none` from zero context; deterministic script observations from
semantic sufficiency/acceptance; model strength from assignment quality; and
tool recognition from proven action capability.

### Progress-event communication

If a parent reports progress, use exactly the five Session-defined names:
`DISPATCHED`, `WRITES_COMPLETE`, `TESTS_COMPLETE`, `REVIEW_READY` and
`TERMINAL`. The owner and meanings come from
`docs/project/SESSION_WORKSPACE_CONTRACT.md`, which is the single reporting
source. Each name remains a status-only, non-accepting observation. Emit each
named observation at most once; adjacent relevant observations may share one
outcome-first report with evidence and the next actor, so five separate
messages are not required.
The canonical pointer is
`workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report`.

These observations are never acceptance, a scheduler, queue, ledger,
background callback, retry state or admission. They are not a second state
machine and do not create continuity. `fork_turns=none` remains
background-context isolation, not zero context: the child still needs the
self-contained brief and may not infer meaning from an event name.

Each report still begins with ordinary outcome-first prose, names the affected
files or evidence and next actor, and then appends only the factual tail needed
for that observation. The event name never replaces the explanation or grants
acceptance; no named heading or fixed record shape is required.

The Session contract and registered Roles define fork settings, worktree
mechanics, completion order and convergence; this Skill does not duplicate
those procedures.

- File-only communication describes where bytes are read or written. It does
  not imply that the child understands the purpose, conflict or completion
  meaning. Low-semantic communication is any interface whose envelope leaves
  those meanings implicit, even when its files and paths are exact.
- `fork_turns=none` controls inherited conversational background. It is not
  the same as zero context and never excuses omitting a self-contained brief.
- A deterministic script can observe paths, statuses, schemas, URLs or exit
  codes. It cannot decide semantic sufficiency, whether a natural-language
  answer addresses the question, or whether the owning role should accept it.
- A stronger model may improve execution, but model strength cannot repair an
  assignment that withholds outcome semantics, protected meaning or a needed
  action. Assignment quality and model capability are different variables.
- Tool recognition (a selected model, available page, returned token or
  structured status) is not proof that the requested action happened. Require
  action-capability evidence: for example, the actual answer, artifact,
  changed file, sent request, or other observable product plus the relevant
  completion condition.

When the outcome requires a state transition, state the current state, the
permitted transition action and the required post-action observation. Evidence
that the target is recognized or requested is not evidence that the transition
happened. For example, a model parameter or available option does not prove a
High-to-Pro switch; the assignment must require the switch action and observe
the composer in Pro after that action and before sending the dependent prompt.

## Results and recovery

A child result and any parent terminal report begin with concise outcome-first
prose: what was found or changed, why it satisfies (or cannot yet satisfy) the
outcome, why that matters, who acts next, which direct consequence was checked
and what residual uncertainty remains.
The explanation then names the concrete artifact or decision, its relationship
to the assignment and its owner before appending a compact factual tail with
paths, commands, statuses and evidence. A child result mirrors the meanings in
its assignment instead of silently renaming an object, owner or consequence.
Root lifecycle and acceptance reports follow the same writing order when they
return through this boundary, but their existing authority remains unchanged.
The factual tail stays minimal and task-relevant; it does not become a required
record shape. Narrative-only and fields-only terminal results are both
insufficient.
No named heading, field list, record shape or mechanical `COMPLETE` token is a
condition of compliance; an unheaded result is valid and its lack of a heading
is not noteworthy. A terminal token is useful only as an anchor after the
actual result has been inspected.

When observations conflict, preserve completed work and inspect the concrete
postcondition. Use ordinary local judgment and one bounded reversible recovery
when safe; do not duplicate an active send, turn an answer fragment into a
success, or invent missing content. Report the unresolved conflict plainly so
the owning parent can choose the next legal action. Recovery does not transfer
acceptance authority.

When a reverse-intake exchange fails, record the mechanism family precisely:
large message truncation is payload transport; a Writer using the wrong Skill or
path is assignment/path confinement; newline or pipe damage is serialization.
Only a locator or archive that remains wrong after decoding is a semantic-author
or acceptance issue. These observations are evidence for the owner, not a
dispatcher, queue or automatic recovery mechanism.

## Progressive disclosure

Start with the smallest context that can support the task model. Expand only
along a concrete dependency: a direct producer or consumer, state owner,
artifact/checkpoint boundary, protected semantic, authority boundary or test
that expresses the relevant contract. Exact paths and schemas are useful once
the dependency is understood. Do not preload repository history or every
workflow record merely to make a brief look complete.

The references directory contains
`project-cognition-bootstrap-prompt.md` and
`assignment-brief-examples.md`, the general cognition bootstrap and
information-rich examples moved from the code-only Agile Skill. They preserve
the same judgment aids and include a non-code transport example. Read them as
progressive-disclosure aids, never as mandatory templates. Code-specific
orientation remains in the Agile Skill's `references/code-context-guide.md`.

## Boundaries

This Skill does not grant permission to edit, run compute, send an external
message, route work, accept a result or change a role's authority. It does not
replace the role charter, session/workspace contract or user decision. It is
not a schema, not a checklist admission gate, not a packet validator, not a
script, not a queue, not a ledger, not an approval layer and not a second
acceptance owner. Scripts may enforce an
already-decided path or identity boundary, but prose and the owning role decide
whether the task model and result are semantically sufficient.
