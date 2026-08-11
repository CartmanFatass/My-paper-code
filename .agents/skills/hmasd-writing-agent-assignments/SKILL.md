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

For a writable L1 assignment, the default worktree unit is exactly one
Root-managed worktree. All disjoint L2 writers under that L1 use the invoking
assignment's named worktree, same frozen base and exact disjoint paths, with no
child Git authority or helper/lifecycle action. Their outputs form one L1
slice candidate, which Root commits or records only after all writers finish.
An independent candidate or release lifecycle requires a new L1 assignment;
L2 has no worktree lifecycle. Distinct concurrent L1 assignments and later
union convergence each use their own Root-managed worktree.

## When to use it

Use this Skill when a parent is designing a subagent or Root-relayed
interface, writing the concrete brief or message that will be sent, or
reviewing whether an existing interface preserves enough meaning and
capability. It applies to code, research, review, browser, transport and other
non-code work. The trigger is the communication problem, not a particular
file format or child model.

## The normal path: compile a task model

Before choosing paths or a wire shape, understand the task in ordinary prose.
Compile a self-contained natural-language model that lets a capable child act
without reconstructing parent history. Explain, in whatever order best fits
the task:

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

For WDM assignments, Root's `fork_turns=1` is a caller-action background
setting for the L1, while a WDM's registered Workflow Implementer dispatch uses
explicit `fork_turns=none`; neither setting creates authority or continuity.
Disjoint-slice completion order has no semantic priority, and a scoped packet
is candidate-ready only until Root integration and fresh convergence acceptance.

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

A child result begins with a natural-language conclusion: what was found or
changed, why it satisfies (or cannot yet satisfy) the outcome, which direct
consequence was checked, and what residual uncertainty remains. It may then
append a compact factual tail with paths, commands, statuses and evidence.
Do not require fixed headings, field names, a record schema or a mechanical
`COMPLETE` token as the admission condition. A terminal token is useful only as
an anchor after the actual result has been inspected.

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
