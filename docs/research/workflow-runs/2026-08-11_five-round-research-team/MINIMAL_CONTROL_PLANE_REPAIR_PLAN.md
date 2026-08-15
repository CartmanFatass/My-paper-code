# Minimal control-plane repair plan

```text
policy_status=USER_APPROVED_P0_AMENDMENT_ACTIVE
policy_version=2
frozen_at=2026-08-11T23:06:06.4010054-07:00
freeze_basis=log-grounded diagnosis plus bounded Critic and Principles review
```

## Purpose and authority

This is the frozen implementation baseline corresponding to
[`SESSION_WORKFLOW_DIAGNOSIS.md`](SESSION_WORKFLOW_DIAGNOSIS.md). It preserves
agreed decisions across context compaction. Freezing prevents silent semantic
drift during implementation; it does not prohibit later diagnosis or redesign.
A policy change requires an explicit user-approved amendment recorded in this
file and the append-only workflow log.

## Version-2 P0 amendment

The user approved P0-1 through P0-16 after the RISP r07 wall-slice incident.
Version 2 makes the following controls authoritative:

- a child, CM, Operator, recovery or transport return is evidence only and
  cannot command retry, stop, pause, retirement, successor creation or portfolio
  allocation;
- fixed wall times and resource forecasts are optimization and scheduling
  thresholds, not scientific stopping rules;
- one-attempt, no-retry, no-resume, terminal and error labels have no scientific
  or routing force;
- when no complete question-relevant data exist, CM owns unchanged-science,
  same-coordinate, result-blind atomic continuation across resource slices;
- the scientific activity boundary freezes treatment/data conditions but not
  process continuity; complete-panel conditions gate claims, not engineering
  completion;
- CM reports engineering facts and never recommends a scientific park or
  portfolio reallocation;
- no fixed direction count, pause/retire quota, six-phase readiness sequence,
  receipt, hash, archive, commit or push admits or terminates research;
- exact provider no-resend after a visible/provider turn or concrete
  conversation identity remains a side-effect safety rule, but transport failure
  cannot pause the direction; and
- separate owner-authored decision packets preserve observed fact, exact object,
  remaining unknown, scientific implication, real alternatives and requested
  authority so a compressed child label cannot become a Root/portfolio command.

Historical contrary text is diagnosis evidence only. Current `AGENTS.md`, Role
charters and active skills implement this amendment.

## Single routing rule

> Work that does not change scientific meaning is handled by its designated
> semantic owner. Scientific meaning includes the question, treatment,
> comparator, observable, claim ceiling, and the conditions or interpretation
> of already observed data. Operator returns execution facts and failures to
> CM; CM may repair and retry unchanged-science engineering without Root, EM,
> or Pro approval. A scientific-object change returns to the same EM. Only a
> cross-direction priority, park, or reallocation decision returns to Root.

This rule replaces the former collection of intermediate approval gates.

### Plain-language rule

Roles do not share a workflow status vocabulary and do not infer decisions from
labels. They say the concrete fact and its owner:

- “the code does not exist yet” means CM may implement it;
- “the scientific definition is incomplete” means the same EM completes it;
- “this run produced no usable scientific data” does not reject its treatment
  or direction;
- “Root is not prioritizing this direction now” is a portfolio choice that
  includes the cost reason and a concrete condition for reconsideration.

Legacy words such as `FILTERED`, `ABSENT`, `PARKED`, `FAILED`, `READY`, or
`TERMINAL` are historical text, not cross-role commands. The repair does not
replace them with another taxonomy. Owners communicate facts and next actions
in ordinary language.

## Four-step research loop

### 1. EM defines the scientific question

EM produces a short natural-language science card containing:

- the question;
- treatment and comparator;
- the result to observe;
- the strongest alternative explanation;
- the maximum claim supported by any outcome.

The card may be short, but it must be meaning-complete. It states or links every
fact needed to distinguish treatment from comparator, compute the observable,
and decide when question-relevant scientific activity has begun. When relevant,
that includes host dynamics, tensor/data schemas, initialization, scientific
counts and caps, and science-bearing seeds. An ambiguity in those facts returns
to EM for clarification; this is definition work, not an approval gate.

Existing implementation affects cost only. If a valuable scientific object is
missing, EM defines it and CM constructs it.

### 2. CM implements and obtains technically complete output

CM owns the entire engineering closure:

- worktree and temporary files;
- implementation and debugging;
- focused checks;
- whether Reviewer, Verifier, or Scout is useful;
- dependencies, environment, launcher, ABI, and resource probes;
- Operator dispatch;
- retained-result creation and installation.

CM should debug and run through the same real launcher, environment, ABI, and
root lifecycle used for the intended execution. A separate rehearsal is a CM
choice, not a fixed gate, and does not require a Root-authored spec or a
six-phase substitute.

CM establishes that the intended experiment executed and that its output is
technically complete and conforms to the observable defined by EM. EM alone
decides its scientific meaning, claim, and next discriminator.

### 3. EM interprets the result

CM returns only the information needed for scientific interpretation:

- whether output relevant to the scientific question was produced;
- the observed result;
- material activity and anomalies;
- what remains unknown.

EM decides whether the observation supports, contradicts, fails to separate,
or motivates another discriminator.

### 4. External Pro converges the result and informs the next loop

Each of the five target completed loops retains one result-convergence Pro
question because this belongs to the original task. A pre-result Pro question
is optional and used only when its answer can change the experimental design.

Pro-visible content is limited to:

- the natural-language scientific question;
- the GitHub repository;
- branch `aggressive`;
- relevant repo-relative paths.

Do not send commit hashes, SHA values, raw/blob URLs, byte counts, receipts,
local paths, or requests to review code correctness.

Pro is asked about:

- whether the scientific conclusion follows;
- the strongest alternative explanation;
- the claim ceiling;
- the most valuable next discriminator.

One Pro question means one scientific request, not one fragile network call.
Transport observation or recovery does not create a new scientific request.
Do not automatically resend or click Stop, Continue, Retry, or Answer now.

## Engineering-failure semantics

### Before a relevant scientific observation exists

Import, compilation, PATH, MSVC, Ninja, RSS FFI, PowerShell, fresh-root,
serialization, launcher, and dependency failures remain inside the same CM
treatment workflow. CM may repair and retry without creating a new scientific
identity or emitting EM/Pro workflow events.

CM reports engineering cost, elapsed work, bottlenecks, completion projections
and cheaper semantics-preserving realizations to EM. CM never recommends a
scientific park or portfolio reallocation. A cost fact reaches Root only when EM
requests portfolio judgment, the lease must expand, or a real cross-scope
resource conflict exists. This is never permission for ordinary repair or
continuation.

There is no need for a global activity taxonomy. The practical boundary is:

> Before output relevant to the scientific question exists, failures are CM
> engineering work. After such output exists, any change that may alter its
> conditions returns to EM.

The science card supplies the direction-specific criterion for when such output
begins; the control plane does not invent a universal activity taxonomy.

### After a relevant scientific observation exists

- Do not silently change seeds, thresholds, treatment, or comparator.
- Invalid or ambiguous output returns to the same EM.
- EM determines whether further work is a replication of the same treatment or
  a new treatment.

### Numerical precision

The control plane performs no default numerical-precision audit.

- CM selects normal tolerances appropriate to the computation.
- Training evidence is interpreted through effect sizes, variance, and
  behavior across seeds when applicable.
- Float bit identity is not a default implementation, run, handoff, or archive
  condition.
- If numerical precision actually changes stability, a branch, or scientific
  interpretation, record the issue in the nearest milestone summary and return
  the scientific implication to EM.

Exact IDs or counts may remain exact when their meaning is inherently discrete.
Byte identity may be used by a tool for a literal copy, but Root does not
manually audit it and it is not a research-workflow gate.

## Role responsibilities

### Root

Root's primary work is multi-direction research exploration:

- discover and compare constructible directions;
- expand promising family-level findings into high-value single directions and
  invoke EM or CM whenever that can change the answer or obtain evidence;
- prioritize by expected scientific discrimination, cost, and reuse;
- advance another direction while one waits;
- synthesize mechanisms and counterexamples without transferring evidence;
- relay only science-changing information between owners;
- perform necessary final Git integration/publication.

Single-direction and multi-direction work are one research process at different
resolutions. There is no fixed WIP count or slot gate. Actual compute commands
may be sequenced around a concrete host conflict, but an occupied machine does
not make a scientific direction ineligible and does not prevent Root from using
EM/CM on other promising questions.

Root does not create temporary specs, copy results, generate
handoffs, inspect receipts, calculate hashes or byte counts, repair launchers,
edit CM tests/configuration, write EM interpretations, or maintain checkpoint
logs. Root integrates owner-prepared artifacts only when a real downstream
consumer needs repository visibility or at final publication.

### Explorer Manager

EM owns the scientific question, treatment/comparator definition, result
interpretation, claim ceiling, and next discriminator. EM or its Artifact
Writer writes the scientific documents it owns.

### Code Manager

CM owns source and test changes, worktree contents, temporary engineering
files, implementation repair, environment and launcher work, real-entry
validation, Operator dispatch, and retained results. CM does not send routine
engineering checkpoints to Root.

### Experiment Operator

Operator executes the CM-supplied command and returns the observation needed by
CM: whether question-relevant output began, the terminal result, and the direct
failure when it did not. Operator does not repair or interpret: it returns the
facts directly to CM, which owns unchanged-science recovery without a Root
round trip.

### External Pro and transport

External Pro supplies scientific adjudication and next-step inspiration.

For every active promising algorithm direction, Root normally opens one
direction-specific Pro conversation during direction formation. The first turn
is constructive innovation rather than approval: strengthen the mechanism,
matched comparator, shortcut controls, toy-to-UAV transfer logic and smallest
answer-changing experiment. EM and CM continue concurrently; the answer is not a
gate. After valid data and same-direction EM interpretation, Root returns to the
same conversation for adversarial result validation and the next discriminator.
Weakly aligned work receives no automatic Pro session.
Transport owns page mechanics and raw-answer capture without exposing transport
metadata to Pro.

### Logging

The owner of an action owns the truth of its event. A simple script only appends
that owner's record; it owns no meaning or decision. Luna maintains and
summarizes the factual log without becoming an approval or acceptance owner.

### On-demand tools

Reviewer, Verifier, and Scout are tools selected by their current owner when
they reduce material uncertainty. They are not mandatory stages.

## File ownership rule

> A file is created and modified by the owner of its meaning. Root Git
> authority does not make Root the default file author or mechanical operator.

| File/object | Owner |
|---|---|
| Science card, design, result interpretation, Pro science question | EM |
| Source, tests, runner, environment scripts, temporary specs/config, result | CM |
| Execution output | Operator/CM |
| Raw Pro response | Transport |
| Event fact | Owner that performed the action |
| Event-file append mechanics | Stateless logging script |
| Cross-direction portfolio decision and necessary integration commit | Root |

If a role or tool prevents the semantic owner from writing its file, repair
that permission or tool once. Do not normalize Root manually doing the work.

Local CM-to-Operator and CM-to-EM handoffs do not wait for Root Git, logging, or
archive work. Root may relay the concise science-changing packet where the role
topology requires it, but does not prepare or mechanically validate it.
Transport captures and lands the raw Pro response; EM owns scientific intake.

## Controls removed or moved later

Remove from ordinary research flow:

- idea-stage native-host gates;
- absence-of-code `FILTERED` decisions;
- preactivity no-retry;
- new scientific treatment identities for engineering repair;
- Root-authored temporary readiness specifications;
- CODE_SCIENCE_INDEX formatting as admission;
- checkpoint Git publication;
- intermediate SHA, byte-count, and line-ending audits;
- fixed six-phase readiness for ordinary exploratory work;
- provisional round numbers and replacement-loop identities;
- default float64 bit-level validation.

Retain only where the next consumer actually needs them:

- Git commit for executed code;
- scientific configuration and seeds;
- retained result;
- raw External-Pro response;
- final archive integrity.

These retained items document the outcome; they do not create scientific
validity.

## Git policy

Publish only when a downstream consumer needs repository-visible content.
Typical useful boundaries are:

1. accepted runnable code;
2. result plus science question for Pro;
3. Pro response plus EM final intake.

These are not three mandatory commits. Compatible boundaries may be combined.
Commit count is not a gate or performance target. Git provides normal code
identity; do not add manual SHA/bytes/CRLF reporting to the research workflow.

## Logging policy: mandatory, append-only, and non-gating

Minimal control does **not** mean minimal accountability. A durable log is
required so the user can reconstruct owner actions, retries, failures,
scientific activity, and unresolved work without trusting Root's chat summary.

The existing `events.jsonl` is immutable historical evidence. It is never
deleted, truncated, squashed into a summary, or silently rewritten. Workflow
repair starts a separate successor file, `events_v2.jsonl`, whose first record
links back to the historical log and these two maintained documents. The new
file is a continuation of logging, not a replacement for evidence already
collected.

Five research milestones remain mandatory anchors:

1. `QUESTION_READY`
2. `CODE_READY`
3. `RUN_TERMINAL`
4. `EM_INTAKE`
5. `PRO_CONVERGED`

They are a minimum, not the only permissible records. The active log also
records every material event needed to audit the workflow:

- a change to the scientific question, comparator, observable, or claim;
- an owner handoff;
- each actual Operator launch and terminal, including preactivity failures;
- the concise engineering repair made before another launch;
- a result creation, replacement, invalidation, or interpretation;
- each Pro send and transport terminal, without exposing transport metadata to
  Pro;
- a Root pause, resume, portfolio allocation, park, or direction decision;
- a material unresolved blocker or correction to a prior record.

Routine compiler invocations, individual focused-test commands, hash checks,
byte counts, line-ending checks, and intermediate receipts do not each need a
central event. The owner keeps sufficient local engineering output and records
one truthful repair summary. Every launch attempt and terminal must still
appear centrally, so preactivity retry permission cannot be used to hide
repeated failures. A delayed or failed log append is explicit audit debt to be
backfilled by the original fact owner; it never blocks retry, handoff,
interpretation, Pro, or portfolio movement, and Root does not transcribe it.

Each entry uses a small descriptive record, not a state machine:

- timestamp;
- owner;
- direction or portfolio scope;
- treatment when one exists;
- natural-language action and outcome;
- whether question-relevant scientific activity started: `true`, `false`, or
  `unknown`;
- whether scientific meaning changed: `true`, `false`, or `unknown`;
- next owner or next action;
- optional repository-relative artifact paths when they help a human inspect
  the work.

Event labels are descriptive and extensible. The append tool does not validate
milestone order, infer approval, require prior state, rename treatments, or
check hashes, bytes, line endings, receipts, numerical precision, or round
numbers. A logging failure never upgrades or invalidates science, but the
missing factual record must be restored promptly and visibly.

Each append is atomic and serialized so concurrent writers cannot overwrite,
interleave, or truncate records. Append failure is returned visibly to the
caller; correction is another appended record, never an in-place rewrite.

The semantic owner invokes a small stateless append script directly. Root does
not transcribe or rewrite other owners' reports, and Luna may summarize the log
but cannot decide what happened. Log updates can ride with ordinary code,
result, or archive publications; they do not require a Git checkpoint per
event. The complete successor log is included in the final archive.

## Current implementation status

### Coverage of the confirmed diagnosis

| Confirmed problem | Frozen repair mechanism |
|---|---|
| Final-grade controls applied before scientific meaning was complete | Meaning-complete EM science card precedes CM implementation; mechanics are loaded only when a real consumer needs them |
| Preactivity engineering failure consumed a scientific identity | Operator returns facts to CM; unchanged-science repair/retry stays in the same treatment and every attempt remains logged |
| Direction, treatment, implementation, attempt, run, archive, and round were conflated | Engineering suffixes are historical locators only; owners state concrete facts and never infer object changes from a label |
| Readiness did not reproduce the real Operator path | CM exercises the actual launcher, environment, ABI, resource probe, and root lifecycle; extra Reviewer/Verifier use is optional and risk-specific |
| Precision was spent on files while scientific semantics remained inconsistent | Science card must define the meaning-bearing dynamics, schemas, counts, caps, and seeds; normal numerical tolerances replace default bit equality |
| Root became the mechanical bottleneck | Semantic owners write their assignment-scoped artifacts; CM owns engineering closure; Root keeps portfolio work and necessary final Git integration |
| External Pro became a file verifier | Pro receives only the scientific question, repository, `aggressive`, and relevant relative paths; transport mechanics stay internal |

The two bounded pre-freeze reviews found no need for another approval stage or
workflow state machine. Their narrow clarifications—complete science meaning,
Operator-to-CM return, plain language, distinct historical locators, non-gating
logging, and atomic append—are incorporated above.

This frozen plan is minimal at the policy level, but it has **not yet been applied to
the active role contracts and tools**. It must not be reported as an operating
workflow merely because this document exists.

### What is already correctly specified

- one routing rule replaces intermediate approval choreography;
- missing code is engineering work rather than scientific rejection;
- CM retains preactivity repair and retry inside the same treatment;
- the real launcher/environment/ABI path replaces a mandatory readiness
  substitute;
- Reviewer, Verifier, and Scout are on-demand tools;
- ordinary numerical work uses normal tolerances rather than float-bit gates;
- Pro sees only the scientific problem, repository, `aggressive`, and relevant
  repository-relative paths;
- logging remains mandatory but cannot grant or deny scientific validity;
- Root is assigned portfolio exploration and final Git integration rather than
  routine engineering mechanics.

### Implementation status

Version 1 has been applied. The conflicts identified during review remain part
of the diagnosis history, but they are no longer active contract blockers:

1. Root, EM, CM, and Operator roles now use semantic ownership. CM owns its
   worktree, temporary engineering files, launcher, unchanged-science repairs,
   Operator dispatch, and result installation; Root no longer performs those
   routine mechanics.
2. Reviewer, Verifier, Scout, six-phase readiness, and CODE_SCIENCE_INDEX are
   optional risk tools rather than ordinary mandatory gates.
3. The real production command, environment, ABI/resource probe, and artifact
   lifecycle are the default engineering rehearsal and execution path.
4. `scripts/hmasd_run_observed_command.py` reports terminal command facts and
   the owner-supplied scientific-activity boundary without the disabled skill.
5. `scripts/hmasd_append_workflow_event.py` appends factual, non-gating events to
   `events_v2.jsonl`; logging remains mandatory and is not an approval system.
6. The user authorized resumption, and real direction work resumed without a
   workflow smoke test.

This section records implementation state only. It does not freeze future
diagnosis, owner-level redesign, or the value-driven addition of new directions.

## Value-driven continuation arrangement

### Historical-continuation clarification — 2026-08-14

The version-1 immediate continuation set below is retained as a locator for
its observations and prior repair context. It is historical, not an executable
queue, admission gate, direction allocation, retry quota, or scientific stop
rule. Current direction stages and allocations are governed by the active Root
and portfolio-owner records; a status, attempt, host, provider, archive, Git,
RSS, CPU, dependency, or lease fact can describe mechanics only and cannot
produce a scientific stop or allocation command.

The directions below were the immediate continuation set when version 1 was
first applied. They are not slots, an exhaustive portfolio, or a prerequisite
ordering. Root continues family-level discovery while they run and may add a
promising high-value direction immediately by invoking its EM and CM. A concrete
shared-compute conflict may sequence actual runs, but no direction must wait for
another direction to close before scientific definition, feasibility work, or
implementation begins.

Historical suffixes such as `B5R1`, `B2R2`, `r2`, and `r3` are retained only as
locators for existing artifacts. No suffix proves a new hypothesis, treatment,
loop, or scientific run. Implementation revision, execution attempt,
scientific run, archive, and portfolio loop remain separate objects.

Immediate continuation set after the user authorized resumption:

- **VSP02-B5R1:** use the already naturally completed persistent Pro answer;
  do not resend or operate the page; return it immediately for same-direction
  EM intake, with any unfinished archive retained only as non-gating audit debt.
- **G53-B2:** retain candidate `d019688f...`; CM uses the real launcher,
  performs internal engineering repair as needed, and runs without the former
  six-phase substitute.
- **ACVC:** resume EM and compress the existing work into the short science
  card; missing implementation is not a blocker.

These directions may advance independently whenever their next action is
valuable. RECCT-B4, ACVC, G53-B2, VSP06-B2R3, corrected historical candidates,
and newly discovered questions remain in one dynamic portfolio. Root may start,
deepen, defer, or replace work using expected decision information, dependency
structure, engineering/runtime cost, and current evidence; repository absence
and preset lane occupancy are not admissibility criteria.

The original five completed-loop objective remains a completion target, not a
limit on discovery or on the number of promising directions that may be
developed. Loop numbers are assigned only after completion. VSP02-B4 remains the
first completed loop; every later completion is counted by evidence, not by a
reserved slot.

## Completion condition

A research loop counts only when all five exist:

- a clear scientific question;
- corresponding implementation;
- a valid scientific result as interpreted by EM;
- same-direction EM interpretation;
- a naturally completed External-Pro response and same-direction EM intake.

The raw response may be archived later for audit. Missing or delayed archive,
commit or publication never prevents EM intake, unchanged-science continuation
or portfolio movement.

Technical failure alone is neither a completed loop nor a new direction.

## Maintenance rule

This is the current version-2 implementation baseline. Future diagnosis and
redesign remain allowed. Whenever the user approves a policy change:

- edit the relevant section in place;
- state what changed and why;
- keep the diagnosis and repair plan consistent;
- append the amendment and reason to the workflow log;
- do not rely on chat history alone.

The document preserves memory; it is not another approval system.
