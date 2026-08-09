# Explorer-Origin Project Validation Workflow

This contract defines the narrow semantic bridge from advisory Independent
Research Explorer output to Code Project Manager. It does not promote advisory
research into canonical science. Explorer's explicit instruction authorizes CPM
to execute the named treatment without giving Explorer direct code/runtime control.

## Authority and public interface

Explorer owns advisory research and writes only its outbound temporary handoffs.
Code Project Manager owns project coordination, code, runtime and technical
acceptance; it reads Explorer handoffs but never reads `local_research/`.
External Pro owns scientific choices inside each submitted review boundary.
Workflow Design Manager owns this stable interface, not its live handoff
content.

## Desktop Scheduler owner-task interface

Scheduler creates a same-level user-owned Desktop Explorer owner task for each
assignment. The task carries `owner_mode=direction` for one named direction or
`owner_mode=portfolio` for an explicitly named direction set. Direction mode
does not preload siblings; portfolio mode does not infer or merge directions
outside its named set. The assignment is self-contained natural language and
names the exact canonical inputs, write paths and result destination. Existing
registered research, mechanical and Agentify children remain available with
their existing profiles and authority. A terminal owner task returns a
conclusion-first canonical capsule and is archived.

Evidence level A/B/C describes scientific meaning only; it is orthogonal to
the observed runtime resource envelope. Scheduler observes resource vectors
and conflict sets (including CPU, memory, GPU, process, I/O, network,
paid-service, mutable-path, mutable-object and output-root claims). CPM owns
runtime admission and observations. Disjoint vectors and writers permit the
parallel-first path; serialization requires a named dependency, same writer
or mutable object/path, an observed vector conflict, or an explicitly marked
formal local result-bearing runtime that excludes only conflicting local
experiment runtime. A resource wait never blocks research, intake, code,
review, Pro or unrelated non-runtime work.

## Direction-local context binding

Every direction-specific Explorer answer and Explorer-to-CPM handoff is
direction-local. For an ordinary question or brief, Explorer resolves one
primary selected direction identity and loads only the smallest set of
canonical decision/source context needed for it. It loads only the smallest
set of parent, child or cross-direction edges material to the exact question.
An explicitly multi-direction user question may name multiple directions, but
that never authorizes preloading or merging the whole portfolio; each named
direction remains explicit, no unrequested sibling generalization is made and
no result implies portfolio-wide meaning.

The brief uses natural-language context cues rather than a schema: selected
direction identity (or the explicitly named direction set); candidate and
exact current proposition; current stage; source/evidence revision boundary;
frozen facts and uncertainty; strongest alternative explanation; the smallest
set of material parent/child/cross-direction relationships; explicit exclusion
of sibling-direction generalization unless a direction is explicitly named;
one requested action and its direct
consumer; completion evidence; and return destination. These cues make the
semantic binding understandable without
creating required field names or a machine admission gate.

An Explorer-generated CPM assignment or brief carries the selected direction
identity, exact candidate proposition and source/evidence revision boundary in
its own prose, along with the protected scientific meaning: frozen facts,
uncertainty, strongest alternative and allowed/excluded interpretations. A
`local_research/.../DIRECTION.json` locator is, if present, Explorer-only
provenance; it is not a CPM-readable canonical input. CPM reads the
assignment-embedded prose and exact project source, test and index paths. Only
when extra bytes are genuinely needed may Explorer provide one exact,
self-contained file under `temp/handoffs/explorer_to_code_manager/`; CPM never
reads `local_research/`.

### Concrete next-hop semantics

Whenever a continuity entry or handoff describes a direction as **ready**,
**parked**, **pending**, **blocked**, **unlock**, **locked/unlocked**, **cannot proceed**, or
**next selection required**, the same prose paragraph or row must make the next
hop understandable. It identifies the current research → code → evidence →
research-intake stage and evidence already present; the concrete missing boundary
(code implementation/connection, CPM technical acceptance or public locator, Explorer
scientific intake, real project instance/object, local scientific proposition
closure, or a genuinely triggered External Pro question); the exact next owner
and decision-bearing action; exact canonical inputs, cooperative write paths and
native result destination (including the native owner handle when applicable);
completion evidence and the following intake owner/path; dependencies,
exclusions, formal/runtime status, and the observed or anticipated resource
vector. A parked direction also states the prospective scientific object that
would justify reactivation and why code/runtime must not start now. `ready`,
`parked`, `pending`, `blocked`, `unlock`, `locked/unlocked` and `next selection required`
are never sufficient descriptions by themselves. This is natural-language
judgment, not a required schema, enum, validator gate, queue, ledger, writer
script, state machine or concurrency coupling.

CPM's treatment result is returned directly over the exact native owner handle.
It begins with its conclusion and mirrors that same primary direction or
explicitly named direction set, candidate, proposition, stage, revision
boundary and material relationship binding before technical observations,
counts, adjustments and locators. It never imports another direction or implies
portfolio-wide meaning. A native task result is the normal transport, not a
file-backed transport.

If the direction, proposition or revision binding is missing or contradictory,
the receiver preserves the original handoff/artifact and asks exactly one
concrete semantic clarification. It continues unrelated work; neither role
guesses, merges directions, rewrites the artifact or creates a `BLOCKED` state.
Portfolio, index, README and continuity surfaces remain pointer-only
navigation or phase-barrier views and do not become duplicate decision records.

## Scientific-only intake boundary

This boundary is prospective and begins after CPM technical acceptance. Explorer
relies on CPM's mechanically verified packet and does not recompute schema,
readability, receipts, activity counts, locators, retry history or technical
consistency. Explorer may revisit one of those technical facts only when a
scientifically ambiguous fact changes its interpretation; CPM remains the sole
technical acceptance owner.

Explorer alone performs the advisory scientific interpretation: supported
proposition, strongest alternative explanation, information gain, next
discriminator and the selected A/B/C or named-Pro action. For each accepted
packet, Explorer writes exactly one canonical scientific decision record within
the candidate's existing `local_research/` ownership. Portfolio, index, README
and continuity surfaces are pointer, navigation or phase-barrier views and do
not repeat scientific reasoning.

After CPM technical acceptance, Explorer may provide an exact accepted result
brief and only the necessary named scientific evidence to zero, one or more
matching registered read-only research children for targeted questions. These
children do not inspect raw evidence roots or recompute schema, readability,
receipts, activity counts, locators, retry history or technical consistency. A
scientifically material technical ambiguity returns to CPM as one precise
clarification. This is an optional capability example, not a fixed panel or
pipeline: a B result may use a small micro-panel only when its named answers are
necessary to one Explorer decision, while ordinary B remains B and does not
automatically invoke Pro. One accepted packet still produces exactly one
Explorer-authored canonical scientific decision.

After CPM technical acceptance, Explorer may separately use the registered
`hmasd-explorer-mechanical` child to present, rearrange or extract literal
fields from already accepted packets or named result briefs. This is
context-isolation organization, not a scientific consultant or a second
acceptance path: the child may report literal existence or inaccessibility for
an exact assignment-named local file or evidence locator, but does not decide
locator validity, completeness, public accessibility or technical
sufficiency. It does not reread raw runtime evidence or recompute schema
readability/readiness, receipts, activity counts, retry history or technical
consistency. Missing, duplicate or contradictory literal facts return to
Explorer for semantic sufficiency handling; CPM remains the technical
acceptance owner and Explorer remains the single scientific intake writer.

When useful, that optional micro-panel routes constructive learning-dynamics,
information-flow or credit-flow questions to Principles Analyst; strongest
alternative, confound or falsifier questions to Critic; repair or smallest-next-
discriminator questions to Innovator; and source, terminology or metric-fidelity
questions to Scout. Explorer may use zero, one or several of them and never
treats this capability map as a required panel.
Several read-only questions may run in parallel, while a direction keeps at
most one result-bearing treatment active by default. Independent ordinary A/B
treatments from different directions may overlap whenever Scheduler observes
disjoint resource vectors and writers. The exact resource-conflict,
direction-barrier and frozen-joint-roster exception live in the exploration Skill's
`parallel-research-workflow.md`; this bridge owns only direction-local binding
and scientific intake.

### CPM treatment result scope

For a Scheduler-created CPM assignment with `owner_mode=treatment`, the
self-contained assignment names one registered ticket/worktree and exact
ticket-local paths. CPM writes only those paths and never writes the shared
main checkout for a treatment. CPM returns a conclusion-first result directly
over the exact native owner handle, naming the exact treatment artifact,
evidence and technical-acceptance locators. The native result is transport
only; it is not a canonical technical artifact, acceptance record, result
ledger, Scheduler semantic relay or Git object. `owner_mode=integration` is the
sole serialized shared-mainline writer and does not repeat treatment runtime or
treatment acceptance.

Explorer performs exactly one scientific intake from the native result and
named canonical locators. Scheduler routes the owner handle mechanically and
does not interpret the technical or scientific result.

This boundary is semantic guidance rather than a mandatory packet schema or
validator admission gate. This boundary does not invoke External Pro, migrate
research records, change the active direction or alter ordinary B iteration. Existing named
Pro triggers remain unchanged.

This document is the single defining source for scientific-only intake. The
tracked exchange-file contract is `docs/project/handoffs/README.md`; live files
use the ignored shared root `temp/handoffs/`:

- `temp/handoffs/explorer_to_code_manager/`: Explorer writes and deletes its own files; CPM
  reads them.

A handoff is a self-contained Markdown or JSON brief, with attachments only
when every receiver can read them. It should make the target, candidate and
version, intended outcome, concrete inputs, evidence, uncertainty, allowed and
excluded effects, authority boundary, completion evidence and return task easy
to understand. It also makes Explorer's selected treatment understandable:
experiment, instance binding, pause, abandon or one exact external-review need.
If it uses a ready/parked/pending/blocked/unlock/locked/unlocked/cannot-proceed or
next-selection disposition, the same paragraph or row carries the concrete
next-hop semantics above; do not substitute the status word for the owner
boundary.
The same brief embeds the direction identity, exact proposition/revision and
protected scientific meaning described above. Any `local_research/.../DIRECTION.json`
locator is Explorer-only provenance, never a CPM-readable input; CPM consumes
assignment prose plus exact project source/test/index paths, or one exact
self-contained temporary handoff only when extra bytes are genuinely needed.
Explorer gives one clear instruction naming implementation, instance binding,
experiment, pause, abandon or exact review as applicable, and identifies the
proportional evidence level A reconnaissance/probe, B exploratory toy
experiment or C conclusion-bearing/expensive experiment. For B, the brief
states the candidate, matched comparator and initial toy path. Each named run
fixes its exact code revision, configuration, seeds and small budget cap; between
runs Explorer may direct recorded changes to the host, threshold, observations,
sample composition or training settings. B need not freeze C-level estimands,
terminal thresholds or request Pro for every iteration. That instruction
authorizes CPM to execute the named treatment without separate code or
experiment permission fields, and CPM does not infer omitted actions. If an
object is missing, the brief states what is known. CPM constructs or binds
engineering objects; Explorer answers any genuinely scientific choice CPM
cannot determine. These are semantic completeness cues, not a schema or
admission check. No `document_kind`, packet version, validator receipt, hash or
byte count is required.

## Intelligent intake and ordering

The receiving model judges whether the brief is sufficient and may perform
bounded safe read-only reconnaissance before acting. It does not reject a
handoff because of formatting or a missing object. The two roles resolve the
gap through direct semantic exchange instead of creating a `BLOCKED` state.

One manifest may preserve an ordered group of public brief paths. That order is
work organization rather than queue state, ranking or scientific comparison.
CPM may process several capacity-admitted, direction-independent candidates in
isolated tickets and roots. One candidate's problem does not block unrelated
work or change another candidate's frozen design or scientific status. Each
result retains exactly one CPM technical acceptance and one Explorer scientific
intake; completion order creates no priority or merged acceptance.
When the owner task has already selected and frozen two or more independent
treatments, and each local predecessor/intake barrier is closed, dispatch is
parallel-first when observed vectors and writers are disjoint. Serialize only
for a named direction dependency, same-direction rules, a shared writer or
mutable object/path conflict, an observed resource-vector conflict, or a design
explicitly marked formal local result-bearing runtime that excludes conflicting
local experiment runtime. Attribution, generic caution, completion order or
convenience cannot restore a global serial fallback. Owner-task lifecycle events
replace polling-loop scheduling; a resource wait leaves non-runtime work runnable
and preserves all existing Pro triggers.

For an Explorer-origin candidate, CPM implements the selected treatment as an
engineering task and does not substitute External Pro for experiment, instance
binding, pause or abandon. It may run a named B experiment under existing
runtime authority and return technical evidence without automatic Pro review.
A B result shows real calls to the environment, policy, learner, trainer and
evaluation runner plus nonzero transitions, updates and evaluations; synthetic
checks alone do not satisfy that experiment boundary.
CPM returns all named runs, their fixed inputs and activity counts, and every
between-run adjustment with its reason. Missing support, unstable learning,
comparator equivalence and non-discrimination are valid diagnoses rather than
terminal support or retirement decisions. A favorable adjusted run is not
preregistered confirmation and cannot erase earlier results or establish a
natural-distribution claim. Explorer uses the evidence to name the next
separating B question; support mapping, a discriminating-host learnability check
and a small multi-seed direction/variance estimate are a common progression, not
a required state machine. Full estimand, null/comparator, population, budget,
stop-rule and decision-criterion freeze begins only for C claims of superiority,
promotion or retirement.
An expensive exploratory treatment still follows its resource and compute
controls, but expense alone neither supplies terminal scientific meaning nor
requires irrelevant decision thresholds.
It prepares an exact review only when the brief explicitly requests one or the
work is direction-changing, materially ambiguous, final science alignment,
formal/conclusion-bearing, an explicitly requested C review, or an explicit
user request. An unclear
treatment returns one precise question to Explorer without blocking unrelated
candidates. The instruction is not a canonical scientific conclusion, but it
is sufficient authority for CPM to perform the named project-validation task.
CPM resolves engineering gaps and Explorer resolves scientific choices; neither
treats a missing object as a workflow terminal. Explorer remains advisory for
A/B iteration and never substitutes its own final scientific acceptance;
External Pro owns the scoped final scientific-semantic acceptance after CPM
technical acceptance and push.

After work on one candidate, CPM returns an explanatory brief that begins with
the natural-language conclusion and then appends the necessary exact evidence.
A native task message carrying the same content is the single fallback.
Mechanical field-only callbacks are insufficient.

After technical acceptance, CPM pushes the result and returns its exact commit
and public GitHub repository/path locators. Ordinary B iteration may continue
as advisory research without automatic Pro review and without claiming final
scientific acceptance. For a direction-changing decision, material result
ambiguity, final science alignment, a formal/conclusion-bearing result or an
explicit C review or explicit user request, Explorer freezes one
`CODE_SCIENCE_ALIGNMENT_AUDIT` after
CPM technical acceptance and push. The review starts only after CPM technical
acceptance and push. Explorer dispatches the audit through the
registered `hmasd-agentify-transport` child using the file-only
`AGENTIFY_REVIEW_BATCH_ASSIGNMENT` (`batch_path|results_path`) interface and
archives and intakes the raw answer only after the child's terminal native
final return. External Pro
uses the GitHub connection to inspect the exact pushed revision and owns final
scientific-semantic acceptance. Explorer never substitutes its own acceptance,
and CPM does not initiate the review.

## Lifecycle and failure ownership

The sender deletes its outbound temporary file after intake. No live handoff
enters Git; canonical records remain in their existing owner locations. There
is no compatibility tree, registry, queue engine, retry state or duplicated
history directory.

Explorer corrects missing advisory content. CPM owns implementation and
operational recovery. Explorer may interpret ordinary A/B observations only
inside its advisory research state. External Pro owns final scoped estimand,
mechanism, sufficiency and result meaning when a C or other named review trigger
is invoked. WDM repairs only this interface. Missing formatting or a prior
mechanical BLOCKED receipt is not candidate evidence and does not support or
refute a proposition.

Candidate evidence, run roots, artifacts and results remain candidate-specific.
This lane consumes no formal iteration and does not update the CDC portfolio.

```text
formal=false
current_work_mutation=forbidden
```
