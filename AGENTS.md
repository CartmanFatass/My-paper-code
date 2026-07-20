# HMASD Controller and Role Isolation

## Persistent-Session Communication

Every persistent HMASD Codex session reads
`.agents/skills/hmasd-task-router/SKILL.md`. It preserves live session routing
and defines the session assignment envelope; it owns no research,
implementation, review, experiment, Git, or project-state decision.

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

The controller alone owns root project state, adoption of external scientific
decisions, implementation and experiment authorization, Git integration,
evidence integrity, and user communication. The dedicated Code Implementation
Manager owns concrete executable architecture, `IMPLEMENTATION_PLAN.md`, code
implementation, engineering-quality application, and focused verification
inside one controller-authorized boundary. Its internal coding workflow is not
prescribed by project documents.
The registered Code Implementation Manager has standing, permanent, exclusive
write authority over `docs/project/IMPLEMENTATION_PLAN.md` whenever it has
accepted a valid `START_CODE_WORK`. It may create, replace, or clear that plan
without per-edit approval. The assignment still bounds the scientific scope;
this standing grant does not authorize experiments, Git, or a successor route.
Unresolved hypothesis generation, portfolio weighting, or next-evidence choice
is sent through one tracked external-review round. The controller directly
coordinates the three registered Exchange sessions but does not silently
replace a missing convergent disposition.
When an accepted convergent disposition has already selected the evidence
source but omits code-ready scientific constants, the controller sends one
tracked focused follow-up to that same registered Convergent Exchange. Do not
reopen Gemini or Open-Pro divergence, the source choice, or the portfolio.

During ordinary work the controller does not execute a role procedure. It may
inspect or repair a role Skill only when the user explicitly requests workflow
maintenance or a terminal protocol failure identifies that Skill as the fault.

## Dispatch Contract

Choose exactly one execution surface and one role:

- complete code implementation or repair workflow -> persistent session with
  `$hmasd-task-router` and `$hmasd-code-manager`;
- complete external review -> controller uses `$hmasd-review-round` and
  `$hmasd-task-router` to dispatch the three registered, one-reviewer-per-session
  exchanges; each exchange uses `$hmasd-review-exchange`;
- authorized run monitoring -> persistent session with `$hmasd-task-router`
  and `$hmasd-experiment`.

There is no general controller orchestration Skill. The controller sends code
work only to the Code Implementation Manager, external-review stages directly
to their registered Exchange sessions, and monitoring only to the Experiment
Monitor. A role completion never starts another role automatically.

Every assignment states the objective, granted authority, required inputs,
working scope, protected changes, forbidden scope, completion condition, and
terminal reply. Do not send the conversation transcript, historical reviews,
broad repository context, or an additional Skill "for reference." Missing
information is returned as `TASK_BLOCKED`; the recipient does not search for
implied context.

The Code Implementation Manager uses its native coding workflow and remains
responsible for the complete integrated diff and focused verification. The
controller does not prescribe internal roles, models, effort settings,
delegation, or review ceremony.

After a mutating `START_CODE_WORK` is accepted, the Code Implementation Manager
holds the sole tracked-worktree write lease. Until it sends
`CODE_GIT_PUSH_REQUIRED` or `CODE_BLOCKED`, the controller performs no project
edit, staging, commit, or push. Urgent controller work first terminates the code
task at a clean boundary and then redispatches from a new pushed commit.

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
The controller communicates directly with each registered Exchange session for
external review; Exchange sessions never communicate with one another.
The controller communicates only with the Code Implementation Manager for code;
The controller alone writes reconciliation and disposition files and creates
the Git-visible boundary required before each downstream reviewer stage.

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
