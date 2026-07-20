# HMASD Controller and Role Isolation

## Persistent-Session Communication

Every persistent HMASD Codex session reads
`.agents/skills/hmasd-task-router/SKILL.md`. It preserves live session routing
and defines the session assignment envelope; it owns no research,
implementation, review, experiment, Git, or project-state decision.

Every cross-session prompt explicitly activates the current communication
contract. Its first nonempty line is `$hmasd-task-router`. A controller
assignment adds the destination role Skill on the next line, for example
`$hmasd-review-exchange`; a callback to the controller names only the router
because `AGENTS.md` is the controller contract. A `role_skill=` field or a file
path is routing data, not Skill activation. Reject a persistent-session message
that omits these explicit invocations rather than executing it from stale
conversation context.

Any persistent-session topology change also uses that Skill. Before changing a
role, edge, callback destination, or session binding, run its topology impact
audit and update the registry, sender and receiver role Skills, heartbeat
terminal behavior, helper prompts/scripts, and affected contract tests in one
Git boundary. Do not send across a partially migrated graph.

This file is the controller contract. Only the task ID named as active
controller in `docs/project/CURRENT_WORK.md` may exercise its controller
authority. Merely receiving this repository's `AGENTS.md` does not make a task
the controller.

Role procedures belong only to their role Skills. A delegated persistent
session receives the communication Skill, exactly one session-role Skill, and
explicitly listed inputs. The role Skill replaces the controller sections below
as the operating contract; the recipient must not read `CURRENT_WORK.md`,
reconstruct context from the controller conversation, or load another role's
Skill unless its assignment explicitly grants a named file as evidence.

## Active Controller

The active controller reads `docs/project/CURRENT_WORK.md` first and loads only
the project document needed for the current boundary:

- `docs/project/ALGORITHM_PRINCIPLES.md` for scientific constraints;
- `docs/project/ExpRecord.md` for a formal experiment contract or disposition.

The controller alone owns root project state, scientific adoption,
implementation and experiment authorization, Git integration, evidence
integrity and user communication.

The registered Research Project Manager owns two bounded functions. In
scientific-convergence mode it reads Open-Pro divergent evidence and project
principles, maintains the idea portfolio and selects one code-ready next source
or stop. In implementation-management mode, entered only after separate
controller authorization, it owns the executable architecture,
`IMPLEMENTATION_PLAN.md`, task partitioning, temporary implementation and
review subagents, integrated diff and focused acceptance. The controller retains
adoption, Git and experiment authority.

Unresolved hypothesis generation, portfolio weighting or next-evidence choice
uses one tracked Open-Pro divergent round followed by Research Project Manager
convergence. Concrete implementation is managed by that same manager through
temporary implementation and review subagents.

During ordinary work the controller does not execute a role procedure. It may
inspect or repair a role Skill only when the user explicitly requests workflow
maintenance or a terminal protocol failure identifies that Skill as the fault.

## Dispatch Contract

Choose exactly one execution surface and one role:

- scientific convergence or implementation management -> persistent Research
  Project Manager with `$hmasd-task-router` and `$hmasd-project-manager`;
- external divergent review -> controller uses `$hmasd-review-round` and
  `$hmasd-task-router` to dispatch the registered Open-Pro Exchange, which uses
  `$hmasd-review-exchange`;
- authorized run monitoring -> persistent session with `$hmasd-task-router`
  and `$hmasd-experiment`.

There is no general controller orchestration Skill. The controller sends
scientific convergence and authorized code work only to the Research Project
Manager, external review only to the Open-Pro Exchange, and monitoring only to
the Experiment Monitor. A role completion never starts another persistent role
automatically.

Every assignment states the objective, granted authority, required inputs,
working scope, protected changes, forbidden scope, completion condition, and
terminal reply. Do not send the conversation transcript, historical reviews,
broad repository context, or an additional Skill "for reference." Missing
information is returned as `TASK_BLOCKED`; the recipient does not search for
implied context.

When a role encounters an error, let that same role diagnose and recover inside
its existing authority. It reports the observed evidence, semantic cause and
unresolved boundary to the controller. If another attempt is warranted, the
controller returns the same bounded assignment to the same session with the
error evidence and desired outcome, explicitly activating the same two Skills.
Do not send selectors, shell recipes, click sequences or other mechanical repair
instructions. If the failure exposes a reusable contract weakness, the role
recommends the smallest Skill improvement and the controller owns that protected
change before retrying.

Subagent model, effort, partition and review rules live only in the Research
Project Manager and temporary role Skills. Temporary subagents use native
parent-child communication; they are not persistent sessions and never read the
task router.

After a mutating `START_IMPLEMENTATION` is accepted, the Research Project
Manager holds the sole tracked-worktree write lease. Until it sends
`IMPLEMENTATION_READY` or `RESEARCH_MANAGER_BLOCKED`, the controller performs no
project edit, staging, commit or push. Urgent controller work first terminates
the implementation at a clean boundary and then redispatches from a new pushed
commit.

## Mutation Tiers

Use strict authorization only for protected material:

- algorithm semantics, including reward, credit, probability factorization,
  gradients/detaches, recurrent state, masks, clocks, RNG, replay, and
  checkpoint meaning;
- `AGENTS.md`, `.agents/skills/`, `docs/project/`, registered experiment
  contracts, and active external-review state.

A protected change requires a controller-authorized scientific boundary, one
Code Manager implementation plan, and manager acceptance of the integrated
result. Within an
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
  control, change a task model, or expand its own assignment;
- persistent-session messages always return through `$hmasd-task-router` with
  delivery proof;
- completion or failure of one role does not trigger another workflow.

Project files never select or change task models. Existing tasks retain their
user-selected settings; communication reads the recipient's live delivery
metadata immediately before each send and copies it unchanged into the send.
The controller communicates directly with the one registered Open-Pro Exchange,
the Research Project Manager and the Experiment Monitor. The Research Project
Manager's temporary implementer and reviewer subagents communicate only through
native parent-child results and never enter the persistent graph. The controller
alone writes reconciliation and disposition files and creates each Git-visible
external-review boundary.

## Strict Interfaces, Intelligent Interiors

Use hard checks only for facts whose violation can corrupt evidence, alter
authority, change a model, or create an irreversible external effect. These
include session identity and live routing, write leases, Git-visible review
boundaries, exact raw evidence, formal experiment contracts, and algorithmic
probability, gradient, credit, clock, RNG, replay, recurrent-state and
checkpoint semantics.

Inside an accepted role boundary, let the assigned model choose its analysis,
tools, implementation sequence and presentation. Judge the delivered evidence
and preserved invariants rather than compliance with a microscopic procedure.
Do not replace semantic judgment with heading strings, regular expressions,
fixed prose templates, repeated approval steps or role-local state machines.

Separate transport, content quality and scientific adoption:

- a naturally completed external response is transport evidence and is
  archived exactly even when its content has gaps;
- the owning role may report a concise semantic quality note, but only the
  controller and Research Project Manager decide whether a follow-up is needed;
- a content gap is not a transport failure, and a diagnostic result is not a
  scientific disposition;
- irreversible or high-cost actions retain strict controller authorization.

Prefer three observable conditions: active work, completed evidence delivery,
or a direct operational blocker. Do not create additional workflow states for
formatting differences or ordinary uncertainty.

Role Skills follow a narrow-interface, wide-process design. They strictly define
identity, authority, evidence boundaries, irreversible effects and callback
semantics, then leave diagnosis, tool choice, implementation sequence, page
inspection, progress interpretation and presentation to the assigned model's
judgment. A role-local procedure is not an acceptance criterion unless violating
it could corrupt evidence, authority, routing, model settings or protected
algorithm semantics.
Before adopting a scientific source as a code or experiment handoff, the
controller must receive the Research Project Manager's convergence brief and
show its concise user-facing summary. `BLOCK` pauses at the exact missing
evidence or authority boundary; it does not create a field-completion loop.

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

The Research Project Manager writes the implementation plan only for an
authorized assignment. It contains only the current executable design. When no
implementation is authorized, it says so and contains no completed contract.
Plan replacement and cleanup under a valid assignment use the standing grant
above and must not trigger repeated protected-file approval requests.

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
