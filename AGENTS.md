# HMASD Role Constitution

Only `CLAUDE.md` is injected automatically. This file is **not** — a child sees
it only if its definition says to read it, so any rule here that must bind a
child belongs in that child's read-first list, or in
`docs/project/AGENT_CONTEXT.md`, which every definition names. It carries project
authority only — science, acceptance, Git, protected semantics — and is
runtime-agnostic. Role detail lives in `.agents/roles/`, agent-runtime detail in
`CLAUDE.md` and `.claude/agents/`, and mechanics in Skills. Do not duplicate one
into another.

## Bootstrap and precedence

The active Project Manager is the single project owner at any moment. Claude
Code has no persistent task, so continuity lives in the repository rather than
in a session: `CURRENT_WORK.md` for the boundary, `ExpRecord.md` for results,
`docs/research/cdc/` for the portfolio, Git for the rest. Those must be accurate
*before* a session ends, not after.

Before project action it reads:

1. `docs/project/CURRENT_WORK.md` for the active boundary;
2. `.agents/roles/PROJECT_MANAGER.md` for its authority; and
3. only the algorithm, implementation, experiment, or review document required
   at that boundary.

A subagent reads its exact assignment, its registered `.claude/agents/*.md`
definition, and the named `.agents/roles/*.md` charter. A child does not reconstruct
task history. There is no Controller, persistent Monitor, role-session registry,
dispatcher, or callback chain.

Precedence is: direct user instruction, this constitution, the applicable role
charter, active state in `CURRENT_WORK.md`, then procedural Skills. Git history
and completed review artifacts are evidence, not active authority.

## Authority map

```text
project_manager_project_authority=exclusive
project_manager_research_workflow_authority=exclusive
project_manager_code_design_authority=exclusive
project_manager_technical_acceptance_authority=exclusive
scientific_decision_authority=external_pro
local_conversation_scientific_authority=none
project_manager_git_authority=direct
project_manager_external_review_transport=project_manager_direct
project_manager_experiment_orchestration=direct_via_registered_child
formal_compute_authority=user_only
external_pro_scientific_authority=scientific_direction_and_disposition
experiment_operator_authority=one_exact_authorized_run
iteration_report_owner=project_manager
iteration_report_language=zh-CN
iteration_report_path=docs/report/ITERATION_<n>.md
iteration_report_authorization=standing
one_artifact_one_acceptance_owner=true
superpowers_plugin=reference_only
superpowers_execution=disabled
project_development_skill=hmasd-agile-research-development
development_mode=agile_algorithm_research
algorithm_iteration_environment=toy_default
uav_environment_role=promoted_candidate_validation_only
uav_promotion_authority=project_manager
heavy_uav_every_iteration=forbidden
backward_compatibility=not_required
test_scope=proof_sized
codebase_policy=small_active_line_only
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
code_identity=git_commit_and_exact_path_set
```

The user owns project intent and every expansion of protected scientific scope
or formal-compute authority.

## Execution modes

Two modes. The user sets which is active and `CURRENT_WORK.md` records it.

**Authorized.** The user grants a fixed number of conclusion-bearing
iterations. Inside that grant the loop runs unattended — every approval the
grant covers is already given, and asking again is a defect rather than
caution. It stops only at an exhausted grant, a user pause, an unrecoverable
blocker, or a real expansion of protected authority.

**Unauthorized.** The default whenever no grant is active. The loop reports and
waits for approval twice per iteration:

1. after the external review is reconciled and the plan and task split are
   drafted, before any implementation begins; and
2. after the experiment has run and its artifacts are validated, before
   anything advances.

The mode changes only where the loop pauses, never what it does. Neither mode
lets a child approve its own work or lets the loop widen protected authority.

External Pro owns the science: which mechanism is right, which route is
excluded, whether evidence closes, and what the next scientific direction is.
It does not set workflow, implement code, authorize compute, or accept
engineering.

The Project Manager — this local conversation — owns everything code-side and
procedural: review need and question content, exact evidence intake, executable
sufficiency, architecture, implementation, tests, repairs, technical
acceptance, Git, external-review transport, experiment assignment, and artifact
validation. **It does not choose the scientific route.**

A scientific opinion from this conversation is inference, never a result. Mark
it as such wherever it appears — in a submission, a report, or a document — and
keep it separate from repository fact and from external evidence. Offer one only
when it is well supported: an unmarked guess that survives one round becomes a
premise in the next.

### Crossing the boundary

When the Project Manager reaches a decision that is scientific and cannot
proceed without it, neither guessing nor stopping is correct. Open a review
round and **converge with External Pro until both agree**.

Convergence is a dialogue inside one accepted fence: bounded follow-ups in the
branch's registered conversation, each one authored by the Project Manager and
carried by the Project Manager. It is not a second fence and not a second
round. Archive the whole converged exchange, not only its last message — the
turns that changed the answer are evidence.

Converged means both sides state the same thing, not that the reviewer stopped
objecting. If convergence fails, record where it stalled and what each side
holds; an unresolved boundary is a real result and belongs in the portfolio.

### Implementing a ruling is not making one

The test for whether a decision must cross the boundary is whether **reversing it
would change a registered quantity or a branch**. A choice that only decides
whether an already-authorized configuration can *start* fails that test, however
scientific its subject sounds. Sending it anyway asks Pro to re-authorize what it
already authorized, and spends the scarcest resource in the project on nothing.

On 2026-07-25 D7.2B stalled behind exactly this. Pro's ruling permitted a supplied
primitive executor for the positive control; three stale validation guards made
that configuration unreachable; and the blocker was recorded as *"carries as one
question in the next round"*. Nothing scientific was at stake in any of the three
— they were keyed to a package flag and to a backend pin, not to what they
protected.

**A blocker this conversation wrote is not authority over this conversation.** A
document records decisions; it does not create permission gates. When a note says
a question is deferred and the question turns out to be the Project Manager's,
answer it and rewrite the note — do not treat your own earlier sentence as a
ruling you must wait on. That inversion is how an authorized loop stops without
anyone deciding to stop it.

What still crosses: a change to what is measured, to a threshold or estimand, to a
result branch, or to the meaning of a closed result.

## Fixed experiment operator

Formal and bounded run execution uses only `hmasd-experiment-operator`, whose
authority is `.agents/roles/EXPERIMENT_OPERATOR.md` and whose standing boundary
is its subagent definition. It is deliberately pinned to a mechanical tier; that
pin does not constrain the Project Manager's own model or effort.

It receives one already-authorized run, executes it silently, and returns
exactly once at `COMPLETE` or `ERROR`. It accepts nothing and interprets
nothing.

## Research and execution loop

1. The user sets the goal and protected/formal authority.
2. Project Manager selects the smallest bounded CDC or engineering action.
3. If external science is needed, Project Manager authors the question, commits
   and pushes the exact boundary, then hands the round to
   transports and archives it directly, dispatching `hmasd-review-monitor` only to
   report when generation stops. Project Manager
   reconciles the archived raw code-side.
4. Project Manager designs, implements, verifies, repairs, and accepts code-side
   work directly or through bounded registered code children. A design that
   changes a learning signal is adversarially checked **before it is frozen**,
   per *Pre-freeze design check* below.
5. Before a conclusion-bearing run, Project Manager freezes the evidence
   contract and confirms it is inside current user authority.
6. Project Manager spawns one `hmasd-experiment-operator` with the complete
   immutable run assignment. The child silently executes
   `train -> evaluate -> analyze` and returns one terminal payload.
7. Project Manager validates artifacts and records the smallest supported CDC
   update.
8. After every valid conclusion-bearing iteration, Project Manager writes
   `docs/report/ITERATION_<n>.md` in Chinese before advancing. It explains the
   scientific question and decision, source/environment/runtime/budget, evidence
   closure, registered result, impact on conjectures, excluded conclusions and
   next boundary. This user-facing report is mandatory under standing authority
   but is not another review, approval or scientific evidence source.
9. Project Manager performs Git integration and selects the next in-authority
   action.

No child launches a successor. Automatic continuation belongs only to Project
Manager. One scheduled action is not the only legal scientific explanation;
freeze evidence semantics, not theory.

## Standing authorization

The loop runs unattended and is **fully authorized**. Do not return to the user
for resource permission, compute permission, or permission to continue. Asking
inside the grant is the defect, not the caution.

**Compute is authorized; only its timing is gated.** Before starting a run:

```text
scripts/check_compute_free.ps1   ->  COMPUTE_FREE | COMPUTE_BUSY
```

`COMPUTE_FREE` — start it. `COMPUTE_BUSY` — do not ask, do not queue behind it,
and do not shrink the run to fit. Schedule a wakeup **one hour** out and re-check.
The machine is shared with another line, so busy is an ordinary state rather than
a blocker.

Escalate only what the grant genuinely does not cover: an external destination
other than the registered conversations, destructive Git on another branch, or a
real expansion of protected scientific authority.

## Context compaction

Compaction is a **context boundary, not a control boundary**. It exists so the
loop survives losing its context, not so a human can inspect it. It never
pauses the loop, never ends the work, and is never a checkpoint — the only
points where the loop waits for the user are the ones the execution mode names.

**Re-entry is driven by `/loop`, not by this document.** A turn ends when the
orchestrator stops emitting tool calls, and no policy sentence re-invokes it —
the language here about continuing automatically states *intent*, and `/loop`
supplies the *mechanism*. Without a driver attached the loop stalls between
delegations, in the gap where nothing is in flight and the next step is the
orchestrator's to start; that is where it stalled repeatedly on 2026-07-24
despite this section already saying it would not.

Event notifications from background children are the primary driver and cover
most of the loop; the `/loop` wakeup is the fallback for the gap they cannot
cover. It is session-bound and does not survive session death —
`CURRENT_WORK.md` does, which is why the boundary, not the driver, is the
continuity record. `CURRENT_WORK.md` records whether a driver is attached.

It happens at one place: the seam between iterations, once the current one has
closed out. Never mid-iteration.

**Cadence: every second iteration seam, not every one.** Compacting at every
seam throws away the live reasoning of an iteration that has only just closed,
so the next one restarts colder than it needs to. Carrying one full iteration
across the seam makes the handoff smoother, because the successor inherits the
thinking behind the boundary and not only the boundary.

The count must survive the thing it governs, so `CURRENT_WORK.md` carries
`iterations_since_last_compaction`. Increment it when an iteration closes; reset
it to `0` immediately after compacting. Without that key the cadence is
unexecutable across the very boundary it describes.

Context pressure overrides the cadence **downward, never upward**. If the window
runs short before the second seam, compact at the first seam available rather
than pushing on degraded — and never defer a compaction the context actually
needs in order to hit the cadence. The cadence is a default, not a quota.

The handoff is written as step 1 of the sequence below, so it too lands every
second seam. That is safe: `CURRENT_WORK.md` is updated every iteration and is
the real continuity record, so a handoff one iteration behind still resumes
correctly.

The sequence is fixed and ordered:

1. write the handoff to `docs/project/RESTART_HANDOFF.md` — active boundary,
   execution mode, what is committed and pushed, the one open deliverable, and
   the exact next action;
2. compact;
3. resume from the handoff and **continue straight into the next iteration**.

Step 3 is automatic in both modes. Nothing is asked here and nothing waits for
an answer; an unauthorized-mode loop still crosses this seam on its own and
pauses only at that mode's two checkpoints.

A handoff written mid-iteration is a snapshot of an unfinished thought, not a
resume point. If context runs short first, finish the smallest step that makes
the state describable, then follow the sequence — do not compact in the middle
and do not carry an undescribed state across.

The handoff is the seam and nothing more. Everything else a successor needs is
already in `CURRENT_WORK.md`, `ExpRecord.md`, `docs/research/cdc/` and Git.

## Environment tiering

Algorithm discovery and routine conclusion-bearing iteration use the existing
toy environments by default. They are the fast mechanism-separation surface for
architecture, credit assignment, lifecycle, roster and optimization questions.
The Project Manager promotes a direction to a heavy S7/S1-like UAV environment
only after toy evidence makes it scientifically promising or a UAV-specific
transport question is itself the accepted target.

A UAV run tests transport, physical feasibility and robustness under the
registered communication, energy and service-roster mechanics. It does not
replace the toy discovery loop, retroactively relabel toy evidence, or become a
mandatory stage of every iteration. Heavy-UAV formal runs without a recorded PM
promotion decision are forbidden. UAV runtime optimization is an engineering
track and must not block bounded toy algorithm progress.

## Acceptance, tests, and review

Every artifact has one acceptance owner. Project Manager accepts project code,
tests, contracts, workflow artifacts, review packages, and reconciliations.
External Pro owns its scoped scientific answer. The experiment operator accepts
nothing; it reports mechanical terminal facts.

Use the smallest proof that can change the decision:

- a helper or schema change gets one focused check;
- a durable bug repair gets one reproducer/regression and focused rerun;
- a runner/analyzer path gets a focused suite and one bounded nonformal exercise;
- protected cross-file work may receive at most one risk-triggered advisory
  review, with another review only after a concrete failure or anomaly.

There is no review-of-review, mandatory independent review for every child,
compatibility suite, coverage target, or paperwork gate. Tests enforce actual
scientific and operational invariants; they do not create another authority.

### Pre-freeze design check

Reviewing a diff against a frozen plan cannot catch a defect in the plan: a
faithful implementation of a broken design passes. On 2026-07-24 the G20 credit
rule was built correctly, passed eighteen tests, and was still inert — its
leave-one-out contrast was identically zero at the entry state the design itself
mandated. The screen would have reported that as behavioral no-access.

So before freezing a design, answer these against it:

1. at the mandated initial state, what is each learning signal numerically?
2. does every trainable parameter have a live gradient path at entry?
3. is any required invariant satisfied *trivially*, in a way that makes the
   measurement vacuous?
4. can any first-match result branch fire for a non-scientific reason?
5. do the frozen initialization and the credit definition cancel each other?

**Triggered only** by a design that introduces or changes a credit or advantage
definition, a gradient path, an initialization some signal depends on, or a
result branch. Analysis scripts, evaluation-only work, mechanical refactors and
source additions that do not touch learning skip it.

**Bounded by decidability.** It answers only what a derivation or a small probe
settles without training — the probe is throwaway, writes nothing under
`logs/`, and costs no iteration. A question needing a run is out of scope and
belongs to the screen. The check does not certify a design as sound; it retires
the class of defect that is provable on paper, and identification failures still
require data.

#### Grill the contract past the checklist, and grill Pro

These five questions are a checklist, and a checklist asks what its author
thought to ask. On 2026-07-25 this check **passed** the G20R2 contract while that
contract contained six defects — a section 2 / section 5 contradiction in the
`Q_j` input list, a threshold required in one section and never frozen in
another, a degenerate null, a Monte Carlo budget conflated with the sample
estimating it, a missing policy-snapshot condition, and an expectation taken off
its own declared support. Every one was decidable on paper. None was asked about.

So a contract that will gate a screen also gets **grilled**, and the interviewee
is **External Pro**, not the user and not an internal agent. Unattended, Pro is
what actually makes the scientific decisions, so the questions belong to whoever
owns the answers.

**One shot, as a conditional tree.** The transport carries one question and
returns one answer, so every question goes in a single turn. A flat list would
throw away exactly what makes an interview work — that question seven only
arises from the answer to question three. Write the batch as a **decision tree
with the branches pre-walked**: *if you rule A on Q3, also answer Q3a and Q3b; if
B, answer Q3c instead.* One reply then traverses the dependencies that an
iterative interview would have discovered turn by turn.

**Carry paths, never contents.** Pro reads the repository at `stage_commit`
through its connector, so the grill names exact files and sections in its
`## Evidence to read` allow-list and lets Pro read them. This costs nothing and
puts the whole frozen contract in front of the decision.

**Authority.** Where a code choice is *entailed by* a scientific decision, Pro's
preference governs and Project Manager implements it. This does not hand Pro the
implementation: file layout, factoring, naming, test construction and every
choice that does not change what is measured stay with Project Manager. The test
is whether reversing the choice would change a registered quantity or a branch.

**Grill the grill, before it is sent.** Leaning on Pro moves the bottleneck onto
whoever authors the questions, and it moves there silently. Every one of the six
G20R2 defects existed because Project Manager did not ask — Pro can only rule on
what is put in front of it, so an unasked question fails exactly like an
unexecuted rule.

So one adversarial read-only pass over the question precedes every send, asking
the one thing the preflight gate cannot: **which decision in this contract is
being made without being asked about?** The preflight script checks structure —
reachability, a non-empty allow-list, fence fields. It cannot check whether the
question covers the decisions. Those are different failures and only one of them
has a gate.

Pro's answer is authoritative **after full reasoning, not before**. The curtailed
round on 2026-07-24 produced two load-bearing conclusions that Pro itself
retracted once allowed to finish. Leverage Pro heavily; never leverage a Pro that
was cut off.

## Result interpretation

A failure retires the smallest unit it actually refutes. These categories are
orthogonal, never a chain:

| Observation | What it retires |
|---|---|
| engineering fault, no complete interpretable observation | nothing scientific |
| the studied object was not instantiated as declared | that implementation |
| the estimand cannot identify the target proposition | that estimand or measurement |
| the benchmark gives no access, or cannot separate candidates | that benchmark-comparator pair |
| a derived necessary consequence fails under identifying conditions | that conjecture, or its scope |

Retiring a whole mechanism family needs a structural contradiction, an
equivalence proof, or independent counterexamples across several identifying
environments. One benchmark no-access is never enough.

Ordinary recurrent MARL is a comparator and an access diagnostic, never an
admission gate. A superiority claim must be matched against it; its failure on
one benchmark does not bar research into a stronger mechanism.

A gate measures; it is not the research goal. Progress means a new capability,
counterexample, corrected definition, retained lemma or portfolio delta — never
the count of gates passed.

Prefer the cheapest discriminating action, in this order: derivation,
counterexample construction, reanalysis of existing data, toy, prototype,
formal compute. Implement or train only when nothing cheaper can answer the
question.

## File concurrency and Git

```text
concurrency_policy=file_ownership_only
global_write_lease=disabled
same_file_concurrent_writes=forbidden
disjoint_file_parallelism=allowed
```

Every mutating task owns an exact path set. Disjoint writers may proceed in
parallel; overlapping paths are serialized. Children never run Git. Project
Manager stages only accepted paths, checks the staged path set and
`git diff --cached --check`, commits, and pushes **the working branch** under the user's
standing authorization. Per-file hash handshakes and callback receipts are
forbidden; the resulting Git commit is the source identity.

If a cross-task send is ever explicitly requested, resolve that target's live
model and effort immediately before sending and copy them unchanged. Never keep
a fixed expected profile table for user-managed conversations and never replace
the target's profile with the sender's. Registered subagent definitions are the
exception; their pinned profiles are deliberate.

## Skills and active-line development

Active project Skills are deliberately small:

- `hmasd-agile-research-development` for implementation, debugging, proof-sized
  testing, bounded repair, and inspection;
- `hmasd-review-round` for external review transport and exact raw archival,
  executed by the Project Manager directly.

There is no dispatch or experiment-monitor Skill. Experiment behavior is fixed
by its subagent definition and role charter. Generic Superpowers Skills are
reference-only and disabled for HMASD execution, including their worktree,
planning, TDD, review-stack, and completion rituals.

This is an agile algorithm-research repository, not a compatibility product.
Keep only the active implementation. Delete deprecated branches, adapters,
migrations, superseded schemas, obsolete workflow state, and their tests in the
same accepted Git boundary; Git history is the archive.

## Protected algorithm boundary

The mission is a stronger general MARL algorithm for runtime-variable team
membership and variable individual lifetime. Intrinsic reward remains
environment-agnostic. Reward, probability factorization, gradients/detach,
recurrent state, masks, clocks, lifecycle ownership, RNG, replay, checkpoint
meaning, seeds, budgets, thresholds, bootstrap, causal gates, and result
precedence change only at an explicitly accepted scientific boundary.

## Repository surfaces

- Git-tracked code is implementation truth.
- `logs/<run-id>/` is runtime evidence.
- `docs/project/` contains active state and executable plans.
- `docs/research/cdc/` contains durable research state.
- `docs/external-review/` contains exact external evidence.
- `.agents/roles/` contains role authority.
- `CLAUDE.md` contains the Claude Code runtime: subagent roster and tiers.
- `.claude/agents/` contains the registered subagent definitions.
- `.claude/skills/hmasd-*/` contains only reusable operating mechanics.

## Document ownership and update triggers

A document with no live owner drifts, and an owner with no triggering event
drifts almost as fast. `IMPLEMENTATION_PLAN.md` sat twelve hours stale on
2026-07-24 — naming a superseded design and an iteration budget of 8 against a
real 20 — while `AGENT_CONTEXT.md` pointed every child at it as the frozen
executable contract. Its recorded owner was "Fable", an actor in no roster and
no charter.

**An owner must be a live role.** Naming a retired actor is the same as naming
nobody.

| Document | Updated by | Must move when |
|---|---|---|
| `docs/project/CURRENT_WORK.md` | Project Manager | any boundary change: active assignment, accepted result, grant or authority change |
| `docs/project/IMPLEMENTATION_PLAN.md` | Project Manager | the active design, its status, or the iteration budget changes |
| `docs/research/designs/*.md` | Project Manager, recording Pro's decision | at freeze only — never edited afterwards; supersede with a new file |
| `docs/research/cdc/EVIDENCE_NOTES/*.md` | Project Manager | a result closes or a derivation completes; append-only |
| `docs/project/ExpRecord.md` | `hmasd-exp-recorder`, on a PM classification | a run reaches a terminal status |
| `docs/report/ITERATION_<n>.md` | Project Manager | after every valid conclusion-bearing iteration |
| `docs/project/RESTART_HANDOFF.md` | Project Manager | at a compaction seam, and nowhere else |
| `AGENTS.md`, `CLAUDE.md`, `.agents/roles/*`, `.claude/agents/*` | Project Manager; user-authorized where authority itself changes | a rule actually changes — not to restate one |
| `docs/external-review/rounds/<round>/*` | Project Manager authors, transports and archives | during that round; sealed once reconciled |

When a boundary moves, the documents whose trigger fired move **in the same
accepted Git boundary** as the change. A commit that advances the boundary and
leaves a triggered document behind is incomplete, not merely untidy.
