---
name: hmasd-writing-agent-assignments
description: Use when designing a subagent or cross-session interface, writing a concrete assignment or message, or reviewing whether an interface preserves enough meaning and action capability.
---

# HMASD Writing Agent Assignments

This Skill is a reusable writing and reasoning aid for parents who delegate a
bounded task or hand work across sessions. It protects the semantic contract
between requester and child without creating another authority, validator,
queue, approval state, or acceptance owner. The parent remains responsible for
the assignment, routing and acceptance boundaries already defined by the role
and workspace contract.

## When to use it

Use this Skill when a parent is designing a subagent or cross-session
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

For a Desktop Research Scheduler owner task, preserve this prose-first model
for every owner and child assignment. The scheduler factual tail may name exact
`threadId`, `hostId`, owner mode, workspace path, allowed write paths, result
locator and bounded Desktop action. Keep that tail distinct from the machine
binding at
`temp/sessions/research_scheduler/bindings/<assignment_id>.json`: the binding
has only
`assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active` and
is mutation-boundary identity, not task context, a queue or a semantic
completion gate.

## Important distinctions

Keep these concepts separate when writing or reviewing an interface:

In short, distinguish file-only communication from low-semantic communication;
`fork_turns=none` from zero context; deterministic script observations from
semantic sufficiency/acceptance; model strength from assignment quality; and
tool recognition from proven action capability.

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
