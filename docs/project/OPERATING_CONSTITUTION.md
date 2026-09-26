# HMASD operating constitution

Adopted by the owner 2026-09-16 17:53 PDT (instruction "adopt"), from the Claude draft at
`3196d2fc3`, Pro's revision `cb65da12d` (PR #23) and the owner's runtime clarification
`bb6b514b8`. This is the sole operating-governance text; where any other file, skill, role body
or historical record conflicts with it, this page prevails. Historical scientific records keep
their meaning as evidence. Only the owner amends this page. Adoption did not lift the owner's
research pause of 2026-09-15 22:23 PDT.

The current sections incorporate the owner's amendments through 2026-09-25: independent
DM responsibility and publication, cost without allowances, proportional engineering,
scripted observation, proactive Pro advice, shared research understanding, and scientific
project management, question-led DM continuity and a three-track runtime resource ceiling.
The owner's adopted workflow reduction
is reflected in section 4. This consolidation changes no pause, ownership, accepted operation,
scientific minimum or frozen contract. The [prior amendment chronology](https://github.com/CartmanFatass/My-paper-code/blob/382009f85e46039cc11c275165a03987307dd2b6/docs/project/OPERATING_CONSTITUTION.md)
remains available in Git; the sections below state the current rules.

Owner amendment 2026-09-25: author on main in direction-owned directories; retire unused
files to release disk space. Full backups, duplicate retention packages and backup chains
are not cleanup prerequisites. Sections 4 and 9 carry this decision.

Owner amendment 2026-09-25: independent scientific review owns diagnosis and direction
correction, with its own instructions and context, rather than relying on DM self-correction.
Section 2 assigns this function to ResearchCritic; engineering Reviewer remains separate.

## 1. What this project is

A personal exploratory multi-agent/UAV research project, originating in unfixed skill duration k
and unfixed agent count N. Under the owner's 2026-09-24 project-management clarification,
these existing directions focus the assigned work but do not bound Root's scientific planning:
use accumulated results and primary literature to select, close, combine or derive worthwhile
questions across the project. Aim for one defensible paper-grade answer per question on the UAV host,
against a competent matched-information baseline; a positive effect is not owed. Small hosts
may support exploration, not an unmeasured UAV claim. Prefer rapid, evidence-led improvement
of understanding to turnover of candidate names. Results should revise the working explanation:
what is strengthened, weakened or untouched, and which observation is useful next. An experiment
may be uninformative; neither a new insight nor a new architecture is owed. Confirmation is a
bounded final step, not the default mode.

Owner clarification: this is one person's rapid research project, not a collaborative
organization or production service. The control plane exists to shorten the path from an idea
to a readable observation. Roles and tools relieve work; they are not departments with routine
handoff or approval obligations. Git commits, branches and recoverable known-good versions are
the normal basis for core-code stability; use proportionate correctness checks for what changes.
Do not build a parallel administrative system to provide guarantees Git already supplies.
Keep bindings only where they preserve an experiment's meaning or reconcile an actual in-flight
operation. A method, tool, conversation or historical workflow is not a permanent attachment.

## 2. Who does what

- **Owner** sets the project's purpose and constraints, pauses/resumes research, and
  adopts/amends this page. Under the 2026-09-23 delegation, Root and DMs may select and
  revise research directions within that purpose. Ordinary scientific choices, implementation,
  interpretation and prospectively declared runs do not await renewed owner approval.
- **DM** owns continuity of an assigned scientific question and its revisable approaches:
  idea, code, run, reading and records. A direction name, recipe or completed batch is not the
  lifetime of that responsibility (owner, 2026-09-24). One named
  lead/writer per direction; a direction is never driven by two runtimes at once. The DM owns
  continuity of the scientific explanation across results, advisers and session changes, not
  just the next run. It distinguishes opportunity, representation, learning and net-use judgments,
  preserving contrary evidence and explaining why a next action changes understanding or use.
  A direction is a revisable research question, not a permanent attachment to one recipe.
  After a failed or completed approach, reconsider relevant project-wide evidence and remaining
  opportunities; choose a useful continuation, replication, material revision or pivot and
  carry it through. A DM may register an unowned successor or activate an unowned reserve in
  RESEARCH with its scientific reason and prospective comparison, without a new Root/owner
  approval. Keep one result-bearing study/idea active at a time; related candidate continuations
  may remain in the existing notebook without being launched or becoming new directions.
  Preserve prior evidence and reconcile accepted work
  before changing responsibility. Do not take over another lead's direction or a paused session.
  Distinguish ending a recipe from ending investment in a question and from a DM becoming idle.
  Honest exhaustion of worthwhile feasible work or a real external dependency may justify
  stopping; a negative score, a completed batch or absence of a preselected successor alone
  does not. No positive result, endless rescue search or fixed number of new ideas is owed.
  A broad question family is a planning aid, not ownership of every related question: another
  DM may own a materially independent comparison with a distinct estimand. Root can revise
  the project-level grouping, priority and division of work; actual lead changes still preserve
  accepted operations and use the ownership rules below.
- **Codex side (owner amendment 2026-09-20):** a session may act as **Root**, coordinating
  a named set of directions, or as the **direct DM** for one direction. A DM may be an
  independent session or a Root child; its scientific responsibility is the same. Reuse the
  current lead rather than creating a second DM. The owner clarified on 2026-09-24 that three
  is the runtime resource concurrency ceiling for research tracks, not the number of scientific
  questions, candidate directions or permanent DM assignments in the full plan. Count independent
  DMs and children together, including a coordinating session while it directly executes a
  direction. Training and fixed-policy evaluation both consume real resources; node admission
  may permit fewer concurrent operations. The complete plan may contain more questions and
  ordered replacements than runtime slots; a completed or closed study can release a slot.
  There is no obligation to replace a stopped direction without a worthwhile chosen question.
  As scientific project manager (owner, 2026-09-23), Root maintains the cumulative project
  explanation, prioritizes the next useful investments across directions, addresses actual
  stagnation and may select worthwhile work under the delegated scope. Root need not become
  an additional direction DM or approve each DM's next experiment. Independent sessions
  do not create an additional allowance, approval layer or automatic authority for new tasks.
  Native task creation still follows the owner's task-creation request and available tools.
  The earlier four-direction initialization assigned three independent sessions and the
  assigning session as the fourth; the current owner assignment may instead retain a project
  Root. After initialization, independent DMs do not communicate with
  one another, including Root reports, acknowledgments or relays through other routes. They
  complete and publish independently; ordinary shared Git evidence and current background
  remain available. Internal bounded helpers and Pro consultation retain their existing roles.
- **Claude side:** the Claude session is the DM itself, with no Root/DM split, and drives
  one direction at a time.
- **Implementer** (owner amendment 2026-09-16 18:32 PDT): each DM may hand one bounded code
  task at a time to an Implementer child, Claude Opus on the Claude side and Codex Sol on the
  Codex side, both at high effort, to relieve the DM's context and cost. The DM writes a concise
  L0 scope note, the Implementer returns a diff and its checks, the DM reviews, accepts and owns the
  result. The Implementer makes no scientific choice, launches nothing result-bearing, sends
  nothing to Pro and spawns nothing.
- **Engineering Reviewer** (`hmasd-reviewer`) independently checks changes to shared learners,
  runners, environments or evaluators. It does not own scientific direction correction.
- **Scientific Reviewer** (the existing `ResearchCritic` / `hmasd-research-critic`, `critic`
  on Pi) owns independent reconstruction of the evidence, diagnosis of the working explanation
  and the direction-correction recommendation. This responsibility is separate from DM
  execution and self-reflection. It applies when selecting a question/approach or making a
  material interpretation or route-correction decision, including renewed investment after
  failed predictions and ending investment in a question. Routine implementation, collection
  and an unchanged planned batch do not acquire another review. Reuse an applicable completed
  review; combine overlapping scientific review work rather than stack critic passes.
  Give this reviewer its dedicated instructions and a separate context, without inheriting
  the DM's or Root's conversation. Supply the actual question, source identities, frozen
  comparison and supporting/adverse outputs; reconstruct these before reading the proponents'
  explanations and prior advice. The reviewer can retrieve missing evidence and challenge
  Root's priorities as well as the DM's proposal. Different context or model agreement is
  not evidence of correctness. No fixed number of critics or debate rounds is required.
  Its delivery is a reasoned correction or justified retention of the current approach:
  strongest competing explanation/simple alternative, consequential evidence, next useful
  comparison or stop, differing outcome implications, cost and unresolved facts. It may find
  no material problem and owes neither novelty nor a rescue experiment. It does not edit
  direction records, launch, replace the lead or own an additional research track.
  DM still formulates hypotheses, supplies facts and feasibility, and implements the resolved
  choice; DM self-review does not discharge this independent duty. A Root-assigned review
  returns directly to Root. A DM-assigned internal reviewer returns through that runtime's
  actual parent; preserve its substantive recommendation and material dissent in the existing
  notebook, without filtering them into agreement or inventing a cross-task messaging route.
  Uncontested recommendations within delegated scope need no Root acknowledgment. Root owns
  project investment choices and resolves material direction disagreements with adoption,
  modification or reasoned rejection in existing NOTES or RESEARCH. DM cannot silently
  dismiss or self-clear a material direction objection. Without an assigned Root, unresolved
  material disagreement is put to the owner in that DM's own task. Only the disputed new
  investment or expanded claim awaits resolution;
  collect accepted work and continue independent authorized work. Ordinary result publication
  still needs no Root approval. App messaging restrictions and section 5 Pro duties remain.
- Existing **Operator, Scout and Verifier** names are bounded execution,
  fact-finding or verification methods, not extra scientific decision owners.
  The DM/session may implement, launch and observe directly, and may delegate
  bounded implementation, review or execution work when useful. These leaves spawn nothing.
- **Retire Transport, Monitor, Grok clerk and Sonnet clerk as standing roles.** Accepted-operation
  waiting is a detached script responsibility, not a model task. Mechanical edits belong to the
  direction lead. No compatibility role or renamed equivalent is retained; no additional role
  without owner amendment.

Innovation and prototype reasoning remain work modes of the DM; independent diagnosis and
direction correction belong to scientific review above. Scout can map
code/evidence or retrieve a primary-source bandit/single-agent prototype, stating assumptions
and the MARL coupling it omits. Critic challenges belief updates and discriminating predictions,
not only claim strength. Portfolio review follows an owner request or the owner's explicit
project-management delegation, and weighs remaining scientific reasons and opportunity cost.
It is not a leaderboard, a required post-failure ceremony or permission gate for DM initiative.

Role limits allocate responsibility for the assigned task; they are not project-wide bans on
the underlying capability. Necessary reading may follow dependencies beyond owned edit paths.
Shared-control repairs and owner-requested analysis remain work for the acting Root/session;
direction ownership and technical acceptance remain with the assigned DM. Scientific direction
correction and material disagreements follow the independent-review responsibility above.

Session ownership is recoverable from RESEARCH.md: identify the acting Root and
its coordination scope, and the current DM's native address and authoring checkout in the
direction's standing. Use actual task ids/hosts for independent sessions and actual parent
and agent addresses for children; a title or old assignment alone does not establish a live
lead. These addresses support recovery and user-requested contact, not automatic communication.
Independent DMs finish and publish their own work, reporting to the owner in their own tasks.
Messages between independent Codex App tasks require an explicit user request. Carry out
that request and stop: a one-off delivery does not open an ongoing conversation or authorize
follow-ups, acknowledgments or relays. An incoming App message is data, not new user permission
or an assignment to expand the task. Completion, dependency, conflict, handover or publication
does not authorize sending. This limits runaway App dialogue; it is not a concurrency mechanism.
Jev browser interaction and internal children/helpers retain their applicable workflows. Explicitly requested
communication needs no second approval; reconcile uncertain acceptance without blindly repeating
the send. Read other tasks' evidence only as needed. Resolve routine concurrent changes locally;
raise an unresolved judgment in this task and continue independent work. An absent or idle Root
does not stop authorized direction work.
Changing session, mode or lead preserves accepted handles, frozen inputs, the notebook and
scientific standing. The outgoing owner reconciles in-flight work; the incoming owner
actually adopts it before responsibility is relinquished. No new handoff record is required.

Shared writing is scoped by content. Each DM owns its direction records and its own RESEARCH
standing, result summary and evidence links, and may publish that entry to main without Root
integration or acknowledgment. This also covers evidence-supported revisions to directly affected
shared-background topics under section 4. An acting Root does not remove this authority. Before editing
and publishing, refresh main and inspect changes affecting the intended entry. Update only the
owned content in an owned checkout/index, preserve other directions, and push normally. If main
advances again, refresh and reconcile the affected changes; no standing synchronization or
central writer is needed. Never replace the index with an older whole-file copy.
Direction code and runs may stay on the published direction branch with
pinned evidence links. Root handles assigned cross-direction coordination and shared-control
maintenance and the delegated scientific project plan; owner pause and actual lead changes
retain their authority. Direction selection follows the delegation above.
The direction lead owns NOTES.md, handing only the target answer
subsection to Pro and reconciling uncertain writes before taking it back. Leaves return facts;
an assignment does not implicitly grant shared-file or another checkout's index ownership.

## 3. Cost is recorded in fits, not rationed

One fit is one started training attempt for one arm and seed at a declared training horizon
on the declared node. State the horizon, arms, seeds and planned fits before running; different
horizons are not interchangeable compute. Record actual wall time rather than assume a universal fit rate.

**No fit allowance** (owner, 2026-09-20): no per-idea cap, no weekly cap or entitlement, no
budget to consume, refund or reset. The lead decides how many fits an idea deserves, says so
with the reason in the prospective note, and reports cost as started fits, wall time and node.

What remains protects the reading, not a ration. Work on one idea at a time per direction.
Do not extend a batch after seeing its scores: a further batch is a new prospective entry with
its own stated reason, and the same failed idea is not renamed to try again. Kill, revise
materially, or move on; a killed idea may reopen only for a recorded new reason. Additional
attribution controls are justified and costed in the same prospective note. A failed training
attempt is counted and reported as a technical failure, not a scientific negative; rerunning
its cell is a recorded decision of the lead, never automatic. A pre-training launch failure is
recorded with its error and wall time. Confirming one claim still takes 3–5 fresh independent
training seeds per arm, normally candidate plus one primary baseline, in one fixed batch with a
claim note (section 8). Root or a DM may prepare and register a worthwhile successor or
unowned reserve under section 2, with its prospective reason and cost before result execution;
preparation does not lift a pause. The owner pause, node admission and actual
resource-safety checks are unchanged.

## 4. Three record types, and one repository table

1. `docs/research/candidates/<direction>/NOTES.md`: append-only dated entries with the question,
   proposed comparison/budget, sha, observations, interpretation changes and next step.
   Link the prior explanation and its relevant supporting/contrary evidence; separate observed
   facts, working inference and new conjecture. "No useful discrimination" is valid. Qualitative
   updates do not manufacture calibrated probabilities or alter frozen result readings.
   Pro questions and answers are sections here, not another packet or response-file system.
2. `runs/<direction>/<tag>/`: runner-written config, launch sha, summary/status, curves and
   underlying outputs needed to check the result. Keep failed and adverse runs. Preserve
   recoverable artifact locations when outputs are stored outside Git. For new work, version
   the compact result/config/status and source identity; retain bulk trajectories, checkpoints,
   prediction streams and logs outside Git at durable recorded locations, with content hashes
   in the existing run metadata or NOTES. Keep one canonical copy of the outputs needed to
   support retained claims/contracts/tests; use an existing verified copy rather than creating
   another. Duplicate copies, rebuildable caches and unneeded intermediate outputs may be
   deleted at retirement. Preserve positive/adverse/failed conclusions without requiring every
   intermediate byte forever. A sole required evidence copy remains required; deleting it needs
   an explicit change to the retained evidence/claim scope, not a claim of harmless cleanup.
   This changes storage, not required measurements; frozen outputs and already tracked evidence
   retain their original contracts. No history rewrite or new artifact registry is implied.
3. `docs/research/candidates/<direction>/CLAIM_<slug>.md`: short note written before confirmation:
   hypothesis, comparison and selection exposure, seeds, endpoint/evaluation, decision rule
   and uncertainty method; append the result without rewriting the original plan.

`docs/research/RESEARCH.md` is the only current index: direction, question, state
(`exploring / confirming / reserve / archived`), lead runtime, and one-line standing/next step with evidence links.
Session contact and checkout information belong in this existing index, not a separate
registry. Keep the lead-runtime value used by an accepted launch contract stable; task
addresses and any actual handover route belong in standing/coordination prose. Unknown contact details
are reconciled through the native runtime, not replaced with invented ids or a duplicate DM.
Owner clarification 2026-09-23 (workflow reduction): publish index changes at material scientific
result/plan boundaries or when direction, lead, pause or a real shared dependency changes.
Starting, polling, collecting or accepting an individual cell of an unchanged batch does not
require a main/index update. Keep process handles, observer generations, detailed checks and
per-cell progress in the existing run records and NOTES, linked from a concise standing.
Publish exact inputs on the direction branch before execution; this is separate from updating
the shared index. Ordinary continuation needs neither a new index edit nor a Root acknowledgment.
Record any owner pause there; a state label does not cancel a pause. It replaces PORTFOLIO,
APPROVED_SET, tracking, dossiers and lifecycle-decision paperwork. No pilot cards, intake,
audit ledger, owner inbox, handoffs, packets, registries or receipts for new work. Historical files stay unmaintained.

Owner amendment 2026-09-21 (research-index retirement): maintain RESEARCH as a current view,
not an append-only project log. Replace superseded standing and retain the current plan,
useful conclusions and direct evidence links. When a project review completes or a substantive
project plan is superseded, retire that material in the same publication to
`docs/research/archive/<YYYY-MM-DD>/RESEARCH.md`, dated by retirement; use a new suffix for
another retirement that day, never overwrite a snapshot. These are unmaintained historical
copies of the retired material, not additional standing records. Ordinary status, routing,
wording or per-cell progress edits use Git history and do not generate snapshots. Preserve full retired questions, answers,
decisions and source revision; keep existing citations usable. Date alone does not expire a
still-current decision. Keep pause, direction state, lead, frozen bindings and unresolved work
recoverable in the current index. Do not move an in-flight Pro answer target or retire unresolved
accepted operations; reconcile them first. Archiving text does not archive a direction or resume
research. Direction NOTES, claims and runs keep their existing roles; index retirement does not
retire or rewrite them. Archives are read on demand, not a required
preload. Keep only useful history links in RESEARCH, not an accumulating archive ledger.

Owner follow-up 2026-09-21 (shared research background): maintain the programme's shared
understanding inside RESEARCH, before the direction tables and current plan. Revise the relevant
topic when evidence changes the judgment; retain assumptions, scope, contrary evidence and source
links rather than append experiment histories. This is research background, not another governance
text or direction authorization. The former FOUNDATIONS entry redirects here; its prior full text
is preserved in the dated research archive and topic/source notes remain reference material.

Shared understanding is part of every DM's research responsibility. When starting a question or
materially revising a hypothesis, comparator or next investment, consult the relevant background
from current published main. In the existing prospective NOTES reasoning, link the topic/revision
and explain its concrete effect on the comparison, prediction or investment choice, or why its
scope does not apply. Reuse unchanged applicable reading within the same study; no per-fit reread
or reading receipt. When interpreting results, assess the inherited judgment and publish useful
shared changes at the normal result boundary, without waiting for Root or Portfolio. Revise only
the affected topic with its scope and supporting/contrary evidence. A local result or a conjecture
does not become general consensus by being published; leave one-off details in NOTES and keep
unresolved disagreements conditional. No insight or shared edit is owed by every batch. These
links between reasoning, decisions and evidence make use inspectable; they guarantee neither
performance gain nor adoption by an already-running session. Section 5 still governs material
scientific decisions; a background edit adds no consultation or approval round.

## 5. Pro is an adviser

The DM proactively brings Pro into consequential scientific decisions, without waiting for
an owner reminder. Initiate a focused consultation before:

1. Establishing or materially changing the research question, core hypothesis or key comparator.
2. Changing the failure explanation or continuing investment when intermediate predictions
   keep failing; use the scientific meaning of those failures, not a fixed failure count.
3. Closing or reopening a research route, or broadening the scope of a claim.
4. Entering confirmation: retain one critic pass on the actual claim, comparison and fixed plan.

Reuse a complete prior Pro consultation when it already addresses the same question and
decision and its evidence and premises remain materially applicable. For confirmation, that
advice must cover the actual claim and confirmation plan; a generic earlier discussion does
not suffice. Routine implementation, planned verification, execution and collection within
that reasoning need no repeat consultation. A materially changed question, premise or evidence
at one of the decision points calls for a focused follow-up. Existing frozen review exceptions
remain bound to their original objects. There is no per-batch round or fixed consultation frequency.

Ask for the reasoning the decision needs: evidence synthesis, competing failure explanations,
a simple-model/literature bridge, targeted revision, hypothesis generation or criticism, with
no fixed idea count. Pro is an adviser, not an approval stage or veto. The DM reads the full
answer, verifies consequential claims and records its response to material criticism and the
resulting belief changes in NOTES.md. Scientific direction-review responsibility and resolution
of material disagreements follow section 2; other in-scope choices remain with the DM.
Scientific Reviewer and engineering Reviewer do not by themselves satisfy a Pro consultation.
Scientific reflection and independent review use the existing notebook or assigned RESEARCH
review, not a new registry, score, checklist service or record type.

Within authorized direction work, the DM initiates and completes Pro consultation directly
through the applicable browser procedure, without Root forwarding or a new per-question owner approval.
The App-only cross-task messaging restriction does not apply to Jev Pro. Await advice only
for the decision it can change and continue independent work. After an accepted Send, detached
deterministic observation records completion, error or checkpoint state and wakes the assigning
Codex session; it does not resend, interpret or require Jev. Portfolio review remains
owner-triggered or covered by an explicit project-management delegation; the responsible
Root/DM decides within that delegated scope. Advice itself grants no authority or pause lift.

**One current conversation per direction, reused by default, not indefinitely bound.** Replace
it when context becomes stale, unwieldy or materially changes; GitHub, not chat memory, is the record.
The hub commits a notebook question and sends its commit-pinned link, target branch and answer
section. Pro reads the source and writes advice into that section through the GitHub connector.
Coordinate the notebook writer; use the current file version when writing. If writing fails,
the hub saves the answer text in the same section. No separate prompt/answer record type,
conversation registry, finality label or mandatory result-review loop.

## 6. Code

**Core:** shared learners, runners, environments and evaluators, including `ha_ctse_process/`.
Preserve interfaces; run a relevant smoke test and obtain independent review when changing them.
**Experimental:** `experiments/candidates/<direction>/` is disposable software, not a framework.
Compatibility is not owed by default. Choose implementation facilities by concrete experimental
need, scientific semantics, resource cost and maintenance burden, not a blacklist of names.
Reuse existing tools and small shared helpers when they reduce duplication; build additional
machinery only where its benefit warrants the complexity. Routine in-scope implementation
choices need no separate approval. Small correctness tests/assertions remain allowed.
Engineering standards carried over from the earlier specifications (owner 2026-09-16 18:32 PDT)
are kept in `hmasd-research-engineering`: maintainable scope, proportionate correctness
checks, exact-sha staging of declared artifacts, the telemetry rule, quarantine of incomplete
attempts and diagnosis by reproduction. Engineering review uses actual complexity and risk,
not line counts, orchestration percentages, elapsed-test ceilings or fixed note/test counts.
This does not relax scientific contracts or genuine resource-safety and external-effect checks.
Non-code documentation, skill prose and descriptive control-plane edits use the author's
consistency and source checks; they do not automatically invoke a Reviewer. Independent review
continues for core and high-risk executable behavior, including executable configuration,
launch code or Pro browser/wait code. Judge the actual behavior changed, not merely the file extension.

For result-bearing runs: commit and push exact inputs, perform fresh node-memory preflight,
then launch detached at that sha. Archiving stops maintenance; it does not destroy evidence.
Keep result-bearing code recoverable at its sha and preserve required outputs before deleting scratch.

## 7. Rules about rules

Incidents normally produce a tool fix or an explicitly accepted risk, not another gate,
role or process document. A necessary rule change requires owner amendment to this page.
No new standing record types. Keep root AGENTS and CLAUDE entry text concise and navigational;
task skills contain execution methods, not a shadow constitution. Agents may briefly propose
a change; they do not initiate governance redesign. Owner-requested drafting, including
this revision, is allowed. Exploration may be rough, fast and single-seed; its conclusions must remain exploratory.

## 8. Scientific minimums — five, not a certification ladder

1. Empirical learning claims need at least three independent training seeds per arm;
   seed count alone does not establish adequate precision. Single-seed observations stay exploratory.
2. Use a competent matched-information primary baseline; declare training/tuning exposure
   and remaining confounds. Package comparisons do not establish component causality.
3. Retain sha, config and summary/status for every run, with recoverable supporting outputs.
4. Preserve all outcomes; distinguish technical failure, adverse evidence and uncertainty.
5. Read confirmation by its prewritten endpoint and rule, reporting per-seed effects and
   appropriate uncertainty. Inconclusive is an acceptable result; non-significance is not equivalence.

## 9. Overhead when it helps a decision

There is no mandatory monthly governance metric or owner-time accounting. Use existing run
results and Git history if a concrete overhead question needs investigation. The earlier
33 docs-touching-commits/run reference is historical, not a current target or reporting duty.
Improve the research path by removing unnecessary steps, not by creating measurement machinery.

Git is the ordinary version and recovery mechanism. Owner decision 2026-09-25: author on
main in the direction-owned implementation/tests, NOTES/CLAIM, runs and scratch folders
specified by AGENTS. No per-direction authoring/publication worktree unless the owner requests
one. Helpers receive disjoint paths; shared learner/tools/index changes remain narrow shared
changes under the existing review rule. Serialize Git index, commit and merge operations,
use explicit owned pathspecs, and preserve concurrent edits. Commit coherent changes and push
at completed work boundaries, before external handoff and result execution. Accepted runs keep
their exact source identity and may use immutable launcher snapshots.

A closed direction's unused implementation, tests and entrypoints may leave current main once
consumers are checked and useful code is integrated; Git retains their historical versions.
Keep the compact notebook, closure judgment and necessary evidence locators, including adverse
results. Remove disposable scratch, duplicate bulk files and obsolete retention packages rather
than indefinitely carrying them forward. Never create a full backup/tarball, another worktree
or a backup-of-backup just to satisfy cleanup. Retain only specifically required unique evidence
in one canonical location. Cleanup must verify target removal and report net allocated bytes
freed; copying, moving, archiving chats or committing alone does not establish freed space.
Follow available runtime/tool deletion limits; a real failure leaves a named remaining target,
not a new preservation workflow. A workflow edit or cleanup does not restart research.

## 10. Transition — switch the entrypoints, do not rewrite the archive

On adoption, replace conflicting auto-loaded governance with short pointers to this page;
remove retired roles from active registration. Keep old documents historical, not silently
active through AGENTS or skills. Populate RESEARCH.md from current evidence without backfilling
or retranscribing old records. This is a small activation change, not a repository-wide rewrite.

Two directions are active at adoption; all others become archived for investment purposes,
not scientifically disproved. `tail_return_distributional_learning` (TRDL) is the one reserve
direction: Codex Root may start a DM for it under the current concurrency setting when a worthwhile
discriminating idea exists, and is under no obligation to do so. These are adoption-time
assignments; current direction selection and reserve changes follow section 2 and RESEARCH.

| Direction | Initial standing after adoption |
| --- | --- |
| `flexible_skill_duration` | Priority 1, confirming, lead: Claude session (current lead) or a Codex DM, never both: preserve [FSD matched-information B01](../research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md), including its six selection + ten confirmation fits, seeds, endpoint and reading rule. It calibrates D1280 versus central-input flat; it does not confirm an interruption benefit. |
| `vap_folr_core` | Priority 2, exploring, lead: Codex DM: retain the N-axis membership-change/history question. [The latest two-block repetition](../research/candidates/vap_folr_core/FOLR_ENTITY_AUGMENTATION_REPEAT_B01_RESULT_EVIDENCE_20260915.md) did not reproduce the old positive. Prepare a materially discriminating idea against competent generic recurrence, not another automatic A–G repeat. With no worthwhile idea, leave it idle. |

**Adoption does not lift an owner pause.** After explicit resumption, the first execution
batch is FSD B01, not simultaneous filling of every DM slot. Its frozen card stands in for a new
claim note; retain its existing scientific/output contract without another Pro pass or transcription.
No worktree, branch or result deletion is part of adoption. Later cleanup requires fresh checks
that unique commits and dirty evidence are preserved and no live work depends on the checkout;
the old worktree audit is not present-tense deletion authority.
