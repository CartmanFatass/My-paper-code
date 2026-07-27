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
scientific_principles=docs/project/ALGORITHM_PRINCIPLES.md
evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md
review_stack=false
routine_preimplementation_code_science_review=forbidden
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

One loop per result, eight steps (user-prescribed 2026-07-26). Every stage
must pass the **workflow value test**: name the false scientific assertion it
can prevent, and confirm its complete packaging, waiting, repair and compute
cost is smaller than the waste it avoids. A stage that cannot name one does
not run.

1. **Pro scientific decision.** External Pro selects the direction or evidence
   action, inside the user goal (`docs/project/RESEARCH_GOAL.md`).
2. **Code decisions.** Project Manager makes every implementation binding —
   realization, controllers, constants, factoring — records them in the
   iteration record, and at most discloses them to Pro. A choice crosses to
   Pro only if reversing it would change a registered quantity or a branch.
3. **Pro reviews the key decisions — zero experiments run.** The Stage A
   design assertion audit closes in one round: initial-state signals,
   positive-control necessity, gate witnesses, frozen result-sensitive
   choices, the load-bearing decision the contract makes without asking
   (`docs/project/ALGORITHM_PRINCIPLES.md` section 4), and the cost gate of
   `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`. Questions carry decisions —
   any number of them — and never assign verification labor to Pro.
4. **Converge the execution plan.** Freeze the contract only after Pro
   resolves or explicitly scopes out the defects. The audit is a compact
   section of the round's reconciliation, never a separate reviewer, approval
   file or checklist artifact.
5. **Implement.** Bounded children against the frozen contract, focused
   tests, per `$hmasd-agile-research-development`.
6. **Review and tests.** Project Manager reads the diff and reruns the focused
   checks itself. Stage B (below) triggers only for claim-bearing code; the
   local adversarial reviewer is dispatched only on a PM-named wrong-claim
   risk.
7. **The experiment.** Fail-fast asserts and per-episode progress telemetry.
   At most one smoke, sized to the minimum that proves a genuinely untested
   path, inside the nonformal cap. Rehearsal beyond that is the defect, not
   diligence.
8. **Pro scientific decision on the result.** Mechanical validation first,
   then one round: smallest unit retired or supported, portfolio delta, next
   action. Then the Chinese iteration report `docs/report/ITERATION_<n>.md`,
   ending with the round's time-distribution table (research advancement /
   verification & ceremony / waste) and one line naming what the next round
   cuts; research advancement below half is recorded as an incident. The
   report is mandatory under standing authority but is
   not another review, approval or scientific evidence source.

No child launches a successor. Automatic continuation belongs only to Project
Manager. Freeze evidence semantics, not theory.

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

**First check whose load it is.** The script counts heavy Python processes and
cannot tell another line's run from one this conversation just launched, so it
reports `COMPUTE_BUSY` for our own in-flight work too. Read the reported
`heavy_pids` before acting:

- **another line's** — the rule above applies; wake in an hour and re-check.
- **our own run** — the wakeup is wrong. That run already reports completion, and
  sleeping an hour beside a job that will notify is a stall dressed as
  compliance. Wait on its completion and do documentation-only work meanwhile.

`cpu_avg_pct` well under `cpu_ceiling` with `heavy_python = 1` is the signature of
the second case.

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

#### A guard test needs a paired negative

Adopted 2026-07-27 after an internal sweep found six unfailable guards on the
D7.S instrument, on top of the two external review had already named. Every one
shared a cause: **the tests were written from the implementation, so both sides
of the comparison came from the same code path.**

A test claiming a guard protects `X` must carry a perturbation of `X` that
drives the guard **red**. A positive assertion alone is not a guard.

- `assert f(x) == f(x)` may not stand alone. It needs `assert f(x) != f(x')`,
  and `x'` must be drawn from `X`'s **whole declared domain** — every field the
  digest enumerates, not the one the author had in mind.
- Fixtures made degenerate or randomness-free for tractability delete exactly
  the variance the property is about. An environment whose `step()` draws no
  randomness cannot witness a determinism claim.
- Use realistic values, not `42`. A seed small enough that the production
  reduction is the identity never exercises the reduction.
- Anything the artifact calls **registered, stable or reproducible** must be
  observed reproducing **across a process boundary**. That is what the word
  means to a reader of the paper, and single-interpreter tests assume it rather
  than check it — including against `PYTHONHASHSEED` salting, which is invisible
  inside one process and fatal across pooled shards.

The failure this prevents is specific: a guard that cannot fail reads as
coverage forever after, so the defect it was meant to catch is not merely
undetected, it is recorded as checked.

### Stage A and Stage B — the only two audits, both triggered

```text
review_stack=false
routine_preimplementation_code_science_review=forbidden
audit_model=two_stage_triggered
code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

**Stage A (design assertion audit)** triggers before freezing a contract that
creates or changes an estimand, benchmark source, control or null, a
reward/credit/gradient/initialization mechanism, a normalization, threshold,
confidence procedure or result branch, or the interpretation connecting a
behavior to a capability. Its content is step 3 of the loop and
`ALGORITHM_PRINCIPLES.md` section 4 — including asking Pro which load-bearing
decision the contract makes without asking, which is the whole surviving
function of the former standalone grill stage. It is decided on paper, without
training; it does not certify a design as sound, it retires the defect class
that is provable before compute.

**Stage B (code-science alignment audit)** triggers after implementation
acceptance and before formal compute, when code newly realizes or materially
changes a claim-bearing element. One question to Pro naming the exact pushed
commit and asking only: does the code instantiate the frozen contract; could a
test pass through the wrong mechanism; could an alternate implementation
explanation change the registered conclusion. Pro returns exactly `ALIGNED`,
`MISMATCH` (naming the frozen assertion and the conflicting code path) or
`SCIENTIFIC_AMBIGUITY` (naming one previously unstated result-changing
choice) — never a new design, controller, search, threshold or evidence
volume, and no style, taste, coverage or generic bug hunting. An unchanged
reviewed commit is never resubmitted; there is no review of the review.

Neither stage triggers for operational repair, logging/schema mechanics, or
mechanical refactors. If a repair changes only one stage, repeat only that
stage.

#### Retained lemma — persistence necessity under anonymous reward

Positive-control necessity is now `ALGORITHM_PRINCIPLES.md` section 4; the
D7.2B failure that taught it is in the round archive. The project-specific
retained lemma, load-bearing for the D7.S line:

> At a supported mixed-urgency history, if reward **and transition** are equivariant
> under agent permutation, the relevant agent states and capabilities are
> exchangeable at zero cost, the joint action support is closed under that
> permutation, and every optimal post-check allocation is reachable by a full-sync
> permutation **with the same future state and return**, then individual persistence
> is not necessary.

The broad converse ("permutation-invariant reward makes role exchange free")
was ruled false: position, energy, queue state, internal memory, transition
latency and non-transferable service state all make persistence necessary
under an anonymous reward. The margin estimand is in
`D0_CARRIER_AND_ESTIMAND.md`: `U*_stable,src / B_H <= -0.10`,
`U*_flex,src / B_H >= +0.10`.

#### Question form for Stage A rounds

Write dependent questions as a **decision tree with the branches pre-walked**
(*if you rule A on Q3, also answer Q3a; if B, Q3c instead*) so one reply
traverses what an iterative interview would discover turn by turn. Carry exact
paths in the `## Evidence to read` allow-list, never file contents — Pro reads
the repository at `stage_commit`. Where a code choice is entailed by a
scientific decision, Pro's preference governs; everything that does not change
a registered quantity or branch stays with Project Manager. Pro's answer is
authoritative **after full reasoning, not before** — never curtail a round.

## Result interpretation

Result semantics — smallest implicated unit, mixed/underpowered handling, the
prohibition on rescuing a valid negative, and what a broad retirement requires
— are `docs/project/ALGORITHM_PRINCIPLES.md` section 6, and bind every result
read in this repository.

**Scenario-7 world provenance (Pro ruling 2026-07-26, Stage B).** The topology
rule below was correct and incomplete. The *user* population is also fixed by
construction-time state that `reset(seed=)` does not re-derive: two freshly
constructed environments carrying the same seed differ in user positions by
kilometres. Equal coordinate hashes therefore do **not** imply a shared episode
world.

The standing rule is consequently:

> Any prior result reused as a causal comparator or paper-level premise must
> establish that its compared arms shared the **complete episode world**, not
> merely the same coordinate topology.

Audited on reuse; no repository-wide retrospective audit is required. The ep64
single-topology diagnostic is retired as causal evidence under this rule — its
environment was constructed fresh per arm, and because the construction-time
worlds were never recorded, no unpaired reanalysis can recover the comparison
either. Topology identity itself is unchanged: it remains the ground-BS and
charging-station geometry, with the user world a nested episode-level random
factor carried by a registered `user_world_seed` rather than by OS entropy.

**Scenario-7 topology provenance (Pro ruling 2026-07-26).** The environment
draws its ground-BS and charging-station layout at construction from an
unseeded RNG, so two runs share a topology only if that was explicitly
arranged. Any Scenario-7 result reused as a causal comparator or paper-level
premise must first establish whether its compared arms shared one topology;
when that is unprovable, the artifact is preserved but its conclusion is
scoped to its realized/unknown topology and it is never used as a matched
causal control. Audited on reuse — no global invalidation, no blocking of
unrelated lines.

Ordinary recurrent MARL is a comparator and an access diagnostic, never an
admission gate. A superiority claim must be matched against it; its failure on
one benchmark does not bar research into a stronger mechanism.

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
