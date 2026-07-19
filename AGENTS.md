# HMASD Controller and Role Isolation

## Persistent-Session Communication

Every persistent HMASD Codex session reads
`.agents/skills/hmasd-task-router/SKILL.md`. It preserves live session routing
and defines the session assignment envelope; it owns no research,
implementation, review, experiment, Git, or project-state decision.

Temporary subagents do not use that Skill. They are created for one bounded
implementation assignment, read only their named role Skill and inputs, and
return through the native subagent channel. Cross-session route metadata,
heartbeats, and task registries never enter a subagent prompt.

This file is the controller contract. Only the task ID named as active
controller in `docs/project/CURRENT_WORK.md` may exercise its controller
authority. Merely receiving this repository's `AGENTS.md` does not make a task
the controller.

Role procedures belong only to their role Skills. A delegated persistent
session receives the communication Skill, exactly one session-role Skill, and
explicitly listed inputs. A temporary subagent receives exactly one subagent
role Skill and explicitly listed inputs. In either case, the role Skill replaces
the controller sections below as the operating contract; the recipient must not
read `CURRENT_WORK.md`, reconstruct context from the controller conversation,
or load another role's Skill unless its assignment explicitly grants a named
file as evidence.

## Active Controller

The active controller reads `docs/project/CURRENT_WORK.md` first and loads only
the project document needed for the current boundary:

- `docs/project/ALGORITHM_PRINCIPLES.md` for scientific constraints;
- `docs/project/ExpRecord.md` for a formal experiment contract or disposition.

The controller alone owns root project state, adoption of external scientific
decisions, implementation and experiment authorization, Git integration,
evidence integrity, and user communication. The dedicated Code Implementation
Manager owns concrete executable architecture, `IMPLEMENTATION_PLAN.md`, code
task decomposition, implementation integration, and code review inside one
controller-authorized boundary.
Unresolved hypothesis generation, portfolio weighting, or next-evidence choice
is sent to the External Review Manager; the controller does not silently replace
a missing convergent disposition.

During ordinary work the controller does not execute a role procedure. It may
inspect or repair a role Skill only when the user explicitly requests workflow
maintenance or a terminal protocol failure identifies that Skill as the fault.

## Dispatch Contract

Choose exactly one execution surface and one role:

- complete code implementation or repair workflow -> persistent session with
  `$hmasd-task-router` and `$hmasd-code-manager`; that manager alone creates
  temporary `$hmasd-implementer` and `$hmasd-code-reviewer` subagents;
- complete external review -> persistent session with `$hmasd-task-router` and
  `$hmasd-review-round`; that manager alone dispatches the three registered,
  one-reviewer-per-session exchanges using `$hmasd-review-exchange`;
- authorized run monitoring -> persistent session with `$hmasd-task-router`
  and `$hmasd-experiment`.

There is no controller orchestration Skill. The controller sends code work only
to the Code Implementation Manager, external review only to the Review Manager,
and monitoring only to the Experiment Monitor. A role completion never starts
another role automatically.

Every assignment states the objective, granted authority, required inputs,
working scope, protected changes, forbidden scope, completion condition, and
terminal reply. Do not send the conversation transcript, historical reviews,
broad repository context, or an additional Skill "for reference." Missing
information is returned as `TASK_BLOCKED`; the recipient does not search for
implied context.

The Code Implementation Manager enforces one implementer for a coupled change,
parallel writers only for frozen disjoint scopes, one writer per file, and one
fresh reviewer after integration. The controller neither dispatches these
subagents nor performs implementation review.

## Mutation Tiers

Use strict authorization only for protected material:

- algorithm semantics, including reward, credit, probability factorization,
  gradients/detaches, recurrent state, masks, clocks, RNG, replay, and
  checkpoint meaning;
- `AGENTS.md`, `.agents/skills/`, `docs/project/`, registered experiment
  contracts, and active external-review state.

A protected change requires a controller-authorized scientific boundary, one
Code Manager implementation plan, and an approved reviewer result. Within an
authorized working directory, ordinary helper code, runners, analyzers, tests,
transient files, and non-normative documents may be created, edited, replaced,
or deleted without a per-file approval loop. Do not preserve obsolete ordinary
files merely because deleting them would otherwise require another confirmation.

## Role and Context Firewall

A role Skill is both an authority grant and a context denylist:

- protected paths or semantics not explicitly granted are out of scope;
- ordinary files inside an assigned working scope do not require individual
  enumeration;
- tools and mutations not granted by the role Skill are forbidden;
- a role cannot authorize another role, launch a successor, edit project
  control, change a task model, or expand its own assignment; the sole routing
  exceptions are that the Review Manager may dispatch the fixed reviewer stages
  defined by `$hmasd-review-round` to their pre-registered exchange sessions,
  and the Code Implementation Manager may create bounded native implementer and
  reviewer subagents defined by `$hmasd-code-manager`;
- persistent-session messages always return through `$hmasd-task-router` with
  delivery proof;
- subagents return only through the native subagent channel and never contact a
  persistent session;
- completion or failure of one role does not trigger another workflow.

Project files never select or change task models. Existing tasks retain their
user-selected settings; communication reads the recipient's live delivery
metadata immediately before each send and copies it unchanged into the send.
The controller communicates only with the Review Manager for external review;
it never sends to or receives from a reviewer exchange directly.
The controller communicates only with the Code Implementation Manager for code;
it never sends to or receives from that manager's subagents directly.
The Review Manager never stages, commits, or pushes. When a reviewer-visible
boundary is required, it returns the exact active-round paths; the controller
alone commits and pushes them, then resumes the same manager with the new commit.

## Agile Research and Active-Line Code

MARL exploration remains agile. Preserve multiple scientific explanations while
serializing code mutations and compute for attribution. Do not turn exploratory
questions into chains of arbitrary gates or repeated verification.

Use active-line development. Do not retain backward-compatibility adapters,
deprecated branches, old library interfaces, legacy transport formats, or
superseded checkpoint migrations. Git history is the archive. Replace obsolete
active paths instead of preserving them behind switches.

When an implementation or workflow replacement is accepted, delete its
superseded executable code, recovery scripts, state schemas, generated state
files, compatibility branches, and inactive fallbacks at the same Git boundary.
Do not retain obsolete machinery for possible rollback. Preserve only raw
scientific evidence or an artifact explicitly named by the current control
plane.

The Code Implementation Manager writes the implementation plan only for an
authorized assignment. It contains only the current executable design. When no
implementation is authorized, it says so and contains no completed contract.

## Repository Boundaries

- Git-tracked code is implementation truth.
- `logs/<run-id>/` is runtime evidence.
- `docs/project/` is the controller control plane.
- `docs/research/` contains durable designs.
- `docs/external-review/` contains tracked review evidence.
- `docs/archive/` contains unique historical evidence.

Preserve unrelated user changes and stage only intended files. Git is the sole
version manager; do not add hashes or checksum workflows. The controller may
push `aggressive` with `git push My-paper-code aggressive` under the user's
standing authorization. Role tasks do not commit or push unless their Skill
explicitly grants a narrower boundary.

Update project control only at an accepted implementation, pre-launch boundary,
terminal experiment disposition, accepted external disposition, autonomy-state
change, or explicit controller handoff. Report only the domain that changed.
