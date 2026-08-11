# Explorer-Origin Project Validation Workflow

This contract defines the narrow, Root-routed semantic bridge from advisory
Independent Research Explorer output to Code Project Manager. It does not
promote advisory research into canonical science. Explorer returns a
self-contained request and locator to Root; Root assigns CPM and routes the
request, and CPM returns its technical result to Root for routing back to
Explorer. Explorer's explicit instruction authorizes CPM to execute the named
treatment without giving Explorer direct code/runtime control.

## Authority and public interface

Explorer L1 owns decomposition, selection, dependency/concurrency, science
synthesis and continuity semantics, cross-direction comparison, and advisory
portfolio/local-research semantic intake and decision authoring. Explorer L1 is
read-only: it semantically authors the exact advisory decision and handoff and
returns the complete accepted proposal to Root. An assigned Writer may
physically write or remove only exact Explorer-approved ordinary or
outbound-temporary bytes, never continuity. Root owns user communication,
cross-owner relay, lifecycle and accepted physical writes; Root alone writes
continuity after an accepted proposal and revision check and has no scientific
comparison or intake authority. CPM owns project coordination, code, runtime
and technical acceptance; it never reads `local_research/` or contacts Explorer
directly. External Pro owns scientific choices inside each submitted review
boundary. Workflow Design Manager owns this stable interface, not its live
handoff content or relay mechanics.

## Direction-local context binding

Every direction-specific Explorer answer and Root-routed Explorer -> Root -> CPM handoff is
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

For a result-bearing handoff, the same prose should explain the treatment's
 prospective runtime class and units and whether its direction-local predecessor
 and intake barrier are closed. The scientific A/B/C evidence level is
 independent of runtime class; it is a separate scientific description and
never determines units or barrier closure. CPM never infers class, units or
barrier closure from a science label or `local_research/`. If a cue is
genuinely missing, CPM preserves the original handoff and returns exactly one
concrete clarification to Root for routing while unrelated work continues; it
does not guess, rewrite the artifact or create `BLOCKED`.

CPM's reverse result, returned through Root, begins with its conclusion and
mirrors that same primary direction or explicitly named direction set,
candidate, proposition, stage,
revision boundary and material relationship binding before technical
observations, counts, adjustments and locators. It never imports another
direction or implies portfolio-wide
meaning. A Codex-native message fallback carries the same binding and content.

If the direction, proposition or revision binding is missing or contradictory,
the receiver preserves the original handoff/artifact and returns exactly one
concrete semantic clarification to Root for routing to the sender. It continues
unrelated work; neither role guesses, merges directions, rewrites the artifact
or creates a `BLOCKED` state.
Portfolio, index, README and continuity surfaces remain pointer-only
navigation or phase-barrier views and do not become duplicate decision records.

## Strong action-bearing semantic minimum

Every Explorer brief, CPM result and Codex-native fallback is a human-readable,
conclusion-first action brief. It must state in complete prose (a label may
follow, but never replace the prose):

- the current evidence and exact paths or other concrete locators;
- which facts and choices are frozen, and which facts or choices remain
  unfrozen;
- why CPM is needed now, or why CPM is not needed now, and why Explorer is
  needed now, or why Explorer is not needed now;
- the exact owner and the permitted action now, including concrete inputs and
  locators;
- the evidence that will demonstrate completion; and
- the return destination and the scientific/intake boundary after return.

Status-only text is insufficient. `parked`, `ready`, `pending`, `accepted`,
`blocked`, `waiting for CM`, `intake complete`, `next selection required` and
`CODE_ACCEPTED` (or any equivalent terminal/status token) may appear only after
that complete meaning is written. A receiver preserves the original brief and
asks one exact clarification when this meaning is missing or contradictory; it
does not infer an action from a token.

## Explorer scientific dispositions and action map

`parked` is an Explorer-local scientific disposition only when no scientifically
complete frozen CPM successor exists because a meaning-changing scientific
object is missing: an objective, information object, population/support,
intervention, estimand, comparator or equivalent. It is not retired, pending
implementation, pending runtime (pending-implementation/pending-runtime), a
queue state, `BLOCKED` or a global barrier. A missing DTO, adapter, runner, test
connection or other ordinary engineering object routes to CPM and cannot be
parked. `retired` is a separate explicit
terminal disposition. A parked direction reactivates only when its recorded
prospective condition is met and Explorer freezes a successor. Parking never
pauses siblings, active CPM treatments, read-only science or portfolio
exploration; CPM reads a park as no live successor handoff and must not invent an
experiment.

Explorer maintains a mandatory human-readable, owner-local Direction Action Map
in `local_research/RESEARCH_CONTINUITY.md`. This contract defines the map
only; WDM and workflow children do not edit `local_research/`. The exact columns
are:

```text
Direction | current scientific question | existing evidence and paths | missing object | scientific disposition in full prose | whether CPM is needed now and why | exact next owner | exact next action | trigger/dependency | handoff/result locator | runtime class/units when applicable | post-return intake/reactivation action
```

Every cell contains meaningful current facts, not a status-only token. The map
is not a machine schema, queue, scheduler, registry, runtime-admission source
or acceptance source. The CPM Technical Treatment View at
`docs/project/current-work/common/explorer_project_validation.md` is a
CPM-owned projection/pointer only: it contains treatments with complete Explorer
handoffs, while a park without a frozen successor is absent. This slice never
edits that CPM-owned view.

## Low-context reverse intake for the Direction Action Map

This is the single detailed source for correcting a small owner-local map delta.
The full map never travels through an agent message, encoded fragment or split
transport. Explorer L1 retains the canonical source and semantically authors one
small, self-contained delta containing the canonical source locator, candidate
target locator, Git revision locator, exact old/new text or a unified patch, and
the frozen semantics and consequences. The Git revision is only a source
locator; no hash, digest, byte count, length, encoded fragment or JSON receipt
is workflow admission, routing, handoff, recovery or acceptance evidence.

The normal path is deliberately file-backed and low-context:

1. Explorer sends the complete delta brief to the registered Research Artifact
   Writer. The assignment names one exact temporary destination such as
   `temp/sessions/independent_research_explorer/<root-assignment>/state-proposals/<proposal>.patch`.
   The Writer copies the approved payload verbatim and performs only local
   destination, payload-presence and UTF-8/LF checks. It does not load the
   Explorer Mechanical Skill or another unrelated Skill, normalize or merge
   text, infer a target, or interpret scientific meaning.
2. Root retains the canonical source and creates a task-scoped candidate copy.
   Root performs one ordinary exact-text patch against that candidate. An
   anchor occurring zero or more than once stops the operation and preserves
   the original file. At most one concrete small-delta clarification and retry
   is allowed; there is no retry state, queue, receipt schema, automatic
   recovery or validator.
3. Explorer full-reads the complete candidate and semantically accepts or
   rejects it, including unselected lines, archive meaning, locator meaning,
   table meaning and scientific continuity. A Writer completion is not Explorer
   acceptance.
4. After Explorer acceptance, Root checks the exact source/target path and Git
   revision locator and performs the exact-copy installation. Root does not
   explain, reinterpret or rewrite the scientific content.

The bounded fallback is one concrete clarification naming the missing or
contradictory source/target locator, old/new text or frozen consequence. The
original canonical bytes remain untouched while that clarification is made.
No second independent mechanism is introduced.

Reverse-intake defect records distinguish mechanism families: (A) a large
message truncation is a payload-transport failure; (B) a Writer loading the
wrong Skill or writing the wrong path is assignment/path confinement; and (C)
newline or pipe damage is a serialization-family failure. A locator or archive
that remains wrong after decoding is a semantic-author or Explorer acceptance
failure. These three observations must not be reported as one mechanism's
independent recurrence. The WDM defect queue is evidence history only, never a
dispatcher or scheduler. WDM owns this owner/transport/order/path interface;
Explorer owns artifact integrity, map meaning and semantic acceptance.

## Scientific-only intake boundary

This boundary is prospective and begins after CPM technical acceptance. Explorer
relies on CPM's mechanically verified packet and does not recompute schema,
readability, receipts, activity counts, locators, retry history or technical
consistency. Explorer may revisit one of those technical facts only when a
scientifically ambiguous fact changes its interpretation; CPM remains the sole
technical acceptance owner.

Explorer L1 alone performs the advisory scientific interpretation and owns the
advisory portfolio/local-research semantic intake: supported proposition,
strongest alternative explanation, information gain, next discriminator and
the selected A/B/C or named-Pro action. For each accepted packet, Explorer L1
semantically authors exactly one advisory scientific decision proposal within
the candidate's existing `local_research/` ownership, returns the complete
accepted proposal to Root, and performs no physical write. Portfolio, index,
README and continuity surfaces are pointer, navigation or phase-barrier views
and do not repeat scientific reasoning. Root alone physically writes continuity
after the accepted proposal and revision check; any assigned Writer remains
limited to the exact Explorer-approved ordinary or outbound-temporary bytes.

After CPM technical acceptance, Explorer may provide an exact accepted result
brief and only the necessary named scientific evidence to zero, one or more
matching registered read-only research children for targeted questions. These
children provide bounded answers only and never replace Explorer L1's
cross-direction comparison, advisory intake or decision. They do not inspect raw
evidence roots or recompute schema, readability,
receipts, activity counts, locators, retry history or technical consistency. A
scientifically material technical ambiguity returns through Root to CPM as one
precise clarification. This is an optional capability example, not a fixed
panel or
pipeline: a B result may use a small micro-panel only when its named answers are
necessary to one Explorer decision, while ordinary B remains B and does not
automatically invoke Pro. One accepted packet still produces exactly one
Explorer-authored advisory scientific decision proposal.

After CPM technical acceptance, Explorer may separately use the registered
`hmasd-explorer-mechanical` child to present, rearrange or extract literal
fields from already accepted packets or named reverse briefs. This is
context-isolation organization, not a scientific consultant or a second
acceptance path: the child may report literal existence or inaccessibility for
an exact assignment-named local file or evidence locator, but does not decide
locator validity, completeness, public accessibility or technical
sufficiency. It does not reread raw runtime evidence or recompute schema
readability/readiness, receipts, activity counts, retry history or technical
consistency. Missing, duplicate or contradictory literal facts return to
Explorer for semantic sufficiency handling; CPM remains the technical
acceptance owner and Explorer remains the sole advisory scientific-intake owner
and decision author; physical writes remain bounded as stated above.

When useful, that optional micro-panel routes constructive learning-dynamics,
information-flow or credit-flow questions to Principles Analyst; strongest
alternative, confound or falsifier questions to Critic; repair or smallest-next-
discriminator questions to Innovator; and source, terminology or metric-fidelity
questions to Scout. Explorer may use zero, one or several of them and never
treats this capability map as a required panel.
Several read-only questions may run in parallel, while Explorer keeps at most
one result-bearing experiment active per direction by default. Independent
ordinary A/B treatments from different directions may overlap when the
capacity contract permits. Runtime/admission, direction-barrier and
frozen-joint-roster mechanics live only in the exploration Skill's
`parallel-research-workflow.md`; this bridge owns direction-local binding and
scientific intake and grants no second runtime procedure. Detailed capacity,
admission, barrier and resource behavior is defined only by that
parallel-research reference.

This boundary is semantic guidance rather than a mandatory packet schema or
validator admission gate. This boundary does not invoke External Pro, migrate
research records, change the active direction or alter ordinary B iteration. Existing named
Pro triggers remain unchanged.

This document is the single defining source for scientific-only intake. The
tracked relay-file contract is `docs/project/handoffs/README.md`; live files
use the ignored shared root `temp/handoffs/`, and Root routes them between the
owner lanes:

- `temp/handoffs/explorer_to_code_manager/`: Explorer L1 semantically authors and
  approves the handoff; its assigned Writer physically writes the exact outbound
  temporary file and may remove it only after Root confirms CPM intake. Root
  receives and routes it to CPM.
- `temp/handoffs/code_manager_to_explorer/`: CPM returns its technical result to
  Root; Root writes and routes the exact reverse temporary copy to Explorer and
  may remove that copy only after Root confirms Explorer intake.

A handoff is a self-contained Markdown or JSON brief, with attachments only
when every receiver can read them. It should make the target, candidate and
version, intended outcome, concrete inputs, evidence, uncertainty, allowed and
excluded effects, authority boundary, completion evidence and return task easy
to understand. It also makes Explorer's selected treatment understandable:
experiment, instance binding, pause, abandon or one exact external-review need.
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
handoff because of formatting or a missing object. If a concrete semantic gap
remains, the receiving owner returns one precise clarification to Root for
routing; neither owner uses a direct sibling channel or creates a `BLOCKED`
state.

One manifest may preserve an ordered group of public brief paths. That order is
work organization rather than queue state, ranking or scientific comparison.
CPM may process several capacity-admitted, direction-independent candidates in
isolated execution roots. One candidate's problem does not block unrelated
work or change another candidate's frozen design or scientific status. Each
result retains exactly one CPM technical acceptance and one Explorer scientific
intake; completion order creates no priority or merged acceptance. The detailed
parallel-first, direction-local barrier, capacity and resource rules are defined
only in `parallel-research-workflow.md`; this contract does not duplicate them.

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
user request. An unclear treatment returns one precise question through Root to
Explorer without blocking unrelated candidates. The instruction is not a
canonical scientific conclusion, but it
is sufficient authority for CPM to perform the named project-validation task.
CPM resolves engineering gaps and Explorer resolves scientific choices; neither
treats a missing object as a workflow terminal. Explorer remains advisory for
A/B iteration and never substitutes its own final scientific acceptance;
External Pro owns the scoped final scientific-semantic acceptance after CPM
technical acceptance. Root alone performs any separately authorized final Git
mechanics before an exact accepted revision is submitted for review.

After work on one candidate, CPM returns an explanatory brief that begins with
the natural-language conclusion and then appends the necessary exact evidence.
A native task message carrying the same content is the single fallback.
Mechanical field-only callbacks are insufficient.

After technical acceptance, CPM returns the exact technical result, revision
identifier when available, and repository/path locators to Root. Root alone
performs any separately authorized final Git mechanics. Ordinary B iteration
may continue as advisory research without automatic Pro review and without
claiming final scientific acceptance. For a direction-changing decision,
material result ambiguity, final science alignment, a formal/conclusion-bearing
result or an explicit C review or explicit user request, Explorer freezes one
`CODE_SCIENCE_ALIGNMENT_AUDIT` after CPM technical acceptance and any required
Root integration evidence. The review starts only after that acceptance and
evidence. Explorer dispatches the audit through the registered
`hmasd-explorer-agentify-transport` child using the file-only
`AGENTIFY_REVIEW_BATCH_ASSIGNMENT` (`batch_path|results_path`) interface and
archives and intakes the raw answer only after the child's terminal native
final return. External Pro remains outside the agent tree and is reached only
from Explorer through this transport child. The provider conversation and
transport result are evidence for Explorer's review intake, not a new owner or
scientific acceptance. External Pro uses the supplied repository/path locator
and accepted revision to inspect the scoped result and owns final
scientific-semantic acceptance. Explorer never substitutes its own acceptance,
and CPM does not initiate the review.

## Lifecycle and failure ownership

After Root confirms CPM intake, Explorer may assign its Writer to remove the
exact Explorer outbound temporary file. After Root confirms Explorer intake of
a Root-written reverse temporary copy, Root may remove exactly that copy. No
live handoff enters Git; owner records remain in their existing locations. There
is no compatibility tree, registry, queue engine, retry state or duplicated
history directory.

Explorer corrects missing advisory content. CPM owns implementation and
operational recovery. Explorer may interpret ordinary A/B observations only
inside its advisory research state. External Pro owns final scoped estimand,
mechanism, sufficiency and result meaning when a C or other named review trigger
is invoked. WDM semantically repairs only this interface. Missing formatting or a prior
mechanical BLOCKED receipt is not candidate evidence and does not support or
refute a proposition.

Candidate evidence, run roots, artifacts and results remain candidate-specific.
This lane consumes no formal iteration and does not update the CDC portfolio.

```text
formal=false
current_work_mutation=forbidden
```
