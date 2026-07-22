# OMP HMASD Task Workflow Migration Design

Date: 2026-07-22
Status: Approved by user
Supersedes: `docs/superpowers/specs/2026-07-22-omp-hmasd-agents-design.md`

## Goal

Replace the persistent Research Project Manager and Experiment Monitor Codex
sessions with native OMP task agents. Keep only the Open-Pro Exchange as a
persistent role session because it owns external browser-conversation
continuity, heartbeat recovery and exact natural-response archival.

The migration also replaces the Manager-owned Codex code-agent surface with one
native OMP task tree and deletes the superseded Codex agent registrations after
the OMP path passes runtime capability and end-to-end workflow checks.

## Authority Model

### External GPT-5.6 Pro

External Pro owns scientific direction:

- conjectures and scientific definitions;
- mechanism-family and research-route selection;
- estimands and evidence meaning;
- retained lemmas, counterexamples and portfolio meaning;
- the next scheduled evidence-bearing research action.

No local role silently replaces or reconverges this scientific judgment.

### Project Manager OMP task agent

The OMP Project Manager owns algorithm realization and code-side decisions
within the scientific direction selected by external Pro. This is substantive
algorithm authority, not merely mechanical implementation management. It
chooses and freezes the executable form of:

- network and module architecture;
- observations carried into the adopted algorithm without changing the Pro's
  scientific object;
- recurrent state, masks, clocks and lifecycle ownership;
- probability support and factorization;
- sampling, storage and replay equality;
- gradient, detach and credit paths;
- rollout packing, optimizer exposure and update order;
- RNG and common-random-number coupling;
- checkpoint/resume meaning;
- batched environment, member, branch, skill, replica and evaluation paths;
- replacement ledger, file ownership, checks and integration order.

The Manager may make these protected algorithm decisions without per-choice
Controller approval when they remain inside the assigned Pro direction,
resource authorization, file scope and result contract. It freezes
`docs/project/IMPLEMENTATION_PLAN.md`, selects the code-agent task graph,
integrates the package and performs one bounded repair cycle.

The Manager must return blocked rather than change the Pro's conjecture,
mechanism direction or estimand; expand formal compute, budgets or experiment
authority; select a new scientific route; perform Git integration; alter
project-control authority; or operate the external reviewer.

### Controller

The Controller is the project entry point and control plane. It owns:

- workflow and role-topology design;
- routing and necessary handoffs;
- direct lightweight evidence intake from the archived Pro response;
- provenance checks and durable CDC record application without reinterpreting
  the Pro decision;
- resource-consuming action and formal-compute authorization;
- Git integration and pushed boundaries;
- evidence integrity, terminal disposition and user communication.

There is no independent Research Intake agent. Intake is a small control-plane
operation, and a mandatory Intake subagent would add a lossy relay between the
scientific authority and the algorithm authority. The Controller may use a
read-only scout for a bounded mechanical evidence comparison, but that scout is
not an authority role and does not produce an adoption decision.

The Controller does not design the core algorithm or override the Project
Manager's in-scope algorithm realization. After receiving a Manager package it
checks authority, evidence and integration boundaries rather than redesigning
the algorithm.

### Open-Pro Exchange

The Open-Pro Exchange remains the only persistent non-Controller session. It
owns the registered external conversation, reviewer-visible question,
heartbeat, exact raw archival and terminal transport result. It does not choose
science, manage implementation, authorize compute or modify project control.

### Experiment Monitor OMP task agent

The Monitor is a low-cost, read-only background task agent for one authorized
run. It may read only its assignment, authoritative run status, registered
progress sources and `hub` process/log state. It never launches, restarts,
repairs, extends or scientifically interprets an experiment.

### Code task agents

The Project Manager may spawn exactly these bounded child roles:

- Code Scout: read-only interface and safe-writer-boundary mapping;
- Implementer: one frozen write package;
- Verifier: exact runtime/CUDA/replay/resume checks without source repair;
- Reviewer: fresh independent package review without edits.

One writer owns a file set at a time. Child agents receive no scientific,
project-control, Git, experiment or successor-dispatch authority.

## Runtime Topology

```text
External GPT-5.6 Pro
        <-> Open-Pro Exchange persistent session
        -> archived raw + transport result
Controller
        -> direct evidence intake and workflow/resource gate
        -> OMP Project Manager background task
              -> Code Scout (optional, read-only)
              -> Implementer task(s), disjoint writers only
              -> Verifier (when runtime evidence is required)
              -> Reviewer (mandatory final independent review)
              -> integrated package result automatically delivered
        -> authorized persistent hub experiment process
        -> low-cost OMP Monitor background task
              -> authoritative status + registered progress + hub state
              -> terminal result automatically delivered
```

Only `controller <-> open_divergent_exchange` remains in the persistent session
registry. OMP task agents use `task`/`hub` job identity, automatic result
delivery, `agent://` artifacts and `history://` transcripts; they never use the
persistent session route resolver or callback protocol.

## Project Manager Task Contract

A Project Manager task starts only after:

1. external Pro has returned one archived scientific decision;
2. the Controller has verified provenance and applied the direct evidence
   intake;
3. the Controller has authorized one bounded implementation action;
4. no other Manager or mutating OMP task holds the tracked-worktree lease.

The assignment contains a stable work ID, pushed source commit, Pro raw and
factual reconciliation paths, adopted scientific direction, resource authority,
working scope, protected semantics, forbidden changes and observable completion
checks.

Acceptance of the background task establishes the sole tracked-worktree write
lease. The lease lasts while that exact Manager job is queued or running and
ends only when it yields a terminal ready/blocked result or is definitely
aborted. The Controller, another Manager and unrelated mutating agents do not
edit, stage, commit or push during the lease.

The Manager may send one non-blocking plan brief through `hub` for visibility,
but this is not another approval gate. Its final task result contains the work
ID, exact changed paths, algorithm decisions, checks, review disposition,
preserved scientific direction and residual risk. Subagent claims alone are
not accepted as verification; the Controller independently exercises the
changed end-to-end path before Git integration.

If the root OMP process aborts the Manager, the lease ends only after the abort
is observed. Partial work remains explicit WIP. The Controller does not
silently resume it or launch a second writer; it first records the boundary and
either issues a fresh assignment that adopts the WIP or removes it.

## Rebuildable Monitor Contract

Formal runs are launched only by the Controller as named `hub` processes with
persistence appropriate to the authorized run. Each run writes a reattachment
manifest under its run root containing:

- stable run ID and `hub` process name;
- absolute run root and authoritative status path;
- registered progress sources and allowed fields;
- deadline and expected terminal payload;
- stable monitor task name `monitor-<run-id>`;
- terminal idempotency key derived from run ID, terminal state and authoritative
  status update identity.

The Controller spawns one low-cost Monitor background task after launch. The
Monitor checks authoritative status before process existence or ETA, waits using
bounded `hub` waits/log reads, and emits only terminal state, actionable
operational error or deadline. Running progress remains inside the monitor job
unless the Controller explicitly asks.

A root OMP restart does not invalidate the persistent run. On recovery the
Controller reads the run manifest and authoritative status, checks `hub` process
state and the current task roster, and recreates the same named Monitor job only
when the run is nonterminal and no matching job exists. If status is already
terminal, a bounded Monitor task may relay that terminal payload immediately.
Repeated terminal results are idempotent by the manifest key.

The Monitor has no heartbeat and no persistent session callback. If it aborts,
the experiment continues independently; recovery creates a new Monitor job. If
the process disappears while authoritative status remains nonterminal, the
Monitor reports an actionable operational error without restarting or repairing
anything.

## Filesystem and Control-Plane Migration

The accepted implementation will:

1. Create native OMP profiles for Project Manager, Experiment Monitor, Code
   Scout, Implementer, Verifier and Reviewer under `.omp/agents/`.
2. Move the unique Manager engineering/scientific implementation references and
   monitor protocol into OMP-agent reference paths.
3. Update `hmasd-dispatch-task` so Project Manager and Monitor work use native
   `task`/`hub`, while only Open-Pro Exchange uses persistent routing.
4. Reduce `session-roles.json` to Controller and Open-Pro Exchange.
5. Update `hmasd-review-round` so the Controller performs direct evidence intake
   and sends only an adopted implementation assignment to the OMP Project
   Manager when resource work is authorized.
6. Delete the superseded persistent `hmasd-project-manager` and
   `hmasd-experiment` Skills, monitor heartbeat schema and role prompts.
7. Delete the superseded `.codex/agents/*.toml` profiles and their registrations
   from `.codex/config.toml` after the OMP path passes capability tests.
8. Update topology audit scripts, contract tests, `AGENTS.md`,
   `CURRENT_WORK.md` and all active workflow references in one Git boundary.
9. Delete the superseded simple-copy design and plan after this replacement path
   works; Git history remains the archive.

Open-Pro Exchange Skill, conversation registry and heartbeat remain active.

## Capability and Evidence Verification

Static frontmatter is insufficient. Verification must exercise the effective
runtime surface for every custom OMP agent:

- exact discovery name, model and thinking level;
- actual tool inventory, including absence of unauthorized mutation or spawn
  tools;
- child-spawn allowlist for Project Manager and no child spawning elsewhere;
- read-only denial behavior for Monitor, Scout, Verifier and Reviewer;
- automatic terminal result delivery and durable `agent://`/`history://` output;
- Manager task-tree execution with one harmless isolated package;
- write-lease start, terminal release and abort handling;
- Monitor observation of a short synthetic persistent `hub` process;
- root-session recovery simulation that rebuilds a missing Monitor from the run
  manifest without duplicating or restarting the process;
- persistent topology audit proving only Open-Pro Exchange remains;
- focused workflow contract tests proving obsolete session events, heartbeats,
  Codex profiles and route edges are absent.

Controller-observed before/after workspace and process evidence is required;
agent self-report is not proof of least privilege or non-mutation.

## Failure Semantics

- Project Manager ambiguity inside algorithm realization is resolved by the
  Manager. A change to external scientific direction or resource authority is a
  terminal blocked result.
- A code child failure returns once to the Manager for one in-scope repair. A
  repeated substantive failure blocks the Manager package.
- A Manager abort leaves explicit WIP and releases no authority until the abort
  is observed.
- A Monitor abort never stops or changes the experiment; it is rebuildable.
- A terminal Monitor result never constitutes scientific interpretation or
  experiment disposition. The Controller owns disposition and durable records.
- Open-Pro transport gaps remain transport evidence and do not authorize local
  scientific substitution.
