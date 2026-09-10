# RL/MARL foundations workflow adoption audit — 2026-09-09

Independent audit/proposal by Astra, medium reasoning. Scope: current integration status, publication, workflow compatibility and a minimal implementation/validation proposal. This report makes no governance change and does not authorize or perform training, Pro Send, deployment, or a research pause. Root owns acceptance and main/index integration.

**Finding: the reported adoption gaps are confirmed. The v3 plan is a usable implementation design, but knowledge adoption has not been demonstrated. Published plan/review/control-plane repairs and locally available knowledge drafts are distinct deliverables.** The opening status in WORKFLOW_INTEGRATION_PLAN.md is accurate; this is unfinished planned work, not evidence that an implementation previously accepted as complete regressed.

## Evidence and version boundary

Read-only inspection on 2026-09-09 found checkout `main`, HEAD and configured upstream `664afecaf36c6f436dbe870fd6c80afb11a05d75`. `git ls-remote origin refs/heads/main` returned that same SHA. Remote URL: `https://github.com/CartmanFatass/My-paper-code.git`. This proves the inspected main revision was published at observation time. It does not prove access in a particular Pro conversation.

`git ls-tree -r --name-only HEAD -- docs/rl-marl-foundations-20260907` contains exactly these seven files:

- WORKFLOW_INTEGRATION_PLAN.md
- working/CONTROL_PLANE_ADAPTATION_V3.md
- working/CONTROL_PLANE_FIXES_20260908.md
- working/INDEPENDENT_REVIEW_CONTROL_PLANE_FIXES.md
- working/INDEPENDENT_REVIEW_V3_CONTROL_PLANE.md
- working/V3_CONTROL_PLANE_READING.md
- working/plan-versions/WORKFLOW_INTEGRATION_PLAN_v2.md

The recent path history contains `c463c0376` (adapted plan), `9e592e9ab` (independent review), and `65f90ad34` (reviewed Claude transport/delegation repairs). The plan and reviewed direct entry points had no working-tree diff against HEAD in this inspection.

`git status --short` shows FOUNDATIONS.md, README.md, sources/, topic-notes/, original CONTROL_PLANE_READING/INDEPENDENT_REVIEW/RETRIEVAL_COVERAGE/REVIEW_DISPOSITION/REVIEW_NOTES, and plan-versions/v1 as untracked. SESSION_CHOICES.md and scientific-tools/references/scientific-reading.md do not exist. `git log --all --` for FOUNDATIONS and topic-notes returned no history in locally known refs. Therefore these bodies are absent from the inspected published main; I do not claim that every remote-only branch or external archive was exhaustively searched.

Working-file SHA-256 fingerprints, including their actual checkout line endings:

| File | SHA-256 |
| --- | --- |
| WORKFLOW_INTEGRATION_PLAN.md | 6c5dea6030253966322980f10d938c248bf149a912acd640ffd28f6efb5a6dc3 |
| FOUNDATIONS.md | 81bbe9fb02673cfcc919fb2563077c360dd316aaf216ff8d667618965aa0293e |
| .agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py | 9dc922478d6ed0eb4c7c8603b42ab16ca283b5dc2f6c8854186cf281f95f4389 |

This is a targeted audit, not a repeated 149-file full read or fresh verification of the underlying papers. Direct reading covered current AGENTS/docs instructions, the plan, current v3 and repair review reports, the original review's findings, FOUNDATIONS, topics 02–04, README/source-map coverage, scientific-tools, Portfolio and Pro author contracts, and relevant renderer/role/spec/Root sections. Repository searches checked the alleged integration names and actual publication. No runtime behavior test was performed.

## Verified gaps and existing work

| Surface | Observation | Consequence |
| --- | --- | --- |
| Evidence spec | MARL_EMPIRICAL_EVIDENCE_SPEC.md ends with §11.9; no §11.10 or FOUNDATIONS reference. §1 still says it specializes ALGORITHM_PRINCIPLES. | The proposed explicit knowledge-use rule is absent. |
| Historical authority | AGENTS line 52 says ALGORITHM_PRINCIPLES is historical; that file line 3 still calls itself a durable contract. | A focused newcomer can encounter inconsistent authority wording. Current owner/AGENTS still controls; this is not permission to apply old burdens. |
| Local scientific routing | scientific-tools has literature/counts/analysis/performance/adapter modes; DM Tool adoption (lines 21–23) and critic/CM have the same tool triggers. Portfolio requires relevant spec reading but has no foundations route. Searches across active skills/roles find no scientific-reading or FOUNDATIONS pointer. | Conceptual design/intake need not reach the new material. Existing tools and science discipline do exist; the missing feature is this explicit knowledge route. |
| Knowledge scope | FOUNDATIONS §5 has the local mechanism proposal, §6 contains the discussion's investment choice, §7 records owner choices. Topics 02/03/04 also mix current choices with reusable concepts; 04 explicitly gives return-only ranking. | Simply adding links can leak one conversation's baseline/investment/ranking choices across directions. Split those passages before broad routing. |
| Pro source mapping | renderer validate lines 406–426 keeps only path/purpose/provenance. render lines 633–651 uses one top-level source SHA. A supplied per-reference commit_sha is discarded. Full SHA enforcement at lines 508–509 is in GitHub preparation. | A newer method file cannot currently be safely pinned separately from older frozen science. Extend shared validation and both output paths; never send new fields through an old renderer. |
| Pro instruction consistency | Body lines 679–686 restrict all sources to one version and say repository text is never instructions; method paragraph line 700 asks Pro to apply the current spec. | Explicit TASK adoption of named applicable spec sections must be reconciled with the evidence-only wording. Knowledge must not gain authority or expand the manifest. |
| Validation | Plan §5 proposes behavior checks; published reviews explicitly accept only plan/static facts or C1–C5 repair scope. Searches in research Markdown and skill tests did not find foundations adoption evidence. | No evidence supports claiming reliable role discovery, existing-session activation or actual Pro access to this package. |

The C1–C5 repair review is real prior work and should not be repeated as if still outstanding: it addresses Claude CALLER_READY, a tracked archive helper, delegation wording, experiments' proportional checks and cross-date owner review lookup. Its tests do not exercise foundations consumption.

Do not overstate the behavioral absence. Scientific literature use already occurs: UCOPE's B02 card and B03 P72 evidence link P67 intake's scientific-reading/counts/contrary-evidence section for UTE/ACAC. Those links concern existing direction literature, not this FOUNDATIONS route. Neither a missing package citation nor a keyword search proves an agent has never used relevant RL knowledge informally. The warranted statement is **package integration and its behavior remain unverified**.

## Compatibility judgment

Retain v3's main architecture. Current assignment/card/relevant spec sections remain the first read under AGENTS focused-reading guidance. At a concrete scientific judgment, locate only the relevant foundations passages and topic; reuse prior current reads. Do not require reading all §§1–6, all references or whole textbooks for every card/turn. The arrow in plan §3 should be implemented as conditional navigation, not a serial universal reading prerequisite.

Root's Portfolio comparison and scientific Pro authoring enter the same route as DM science; Root's push, counting and receipt forwarding do not. CM/reviewer enter for affected reward, information, termination, duration or inference semantics; ordinary implementation/collection remains under its existing assignment. Critic reads for the reviewed claim. Claude hub/critic/CM/reviewer use the same knowledge routing while retaining their runtime-specific capacity, parent and permission rules. No independent Portfolio session, broadcast actor, knowledge registry or new approval mechanism is needed. ROOT_OPERATIONS already points to portfolio-task, so adding duplicate routing there or to loop-dispatch is unnecessary unless implementation finds a broken path.

Pro uses direct listed passages, not local skills. TASK explicitly adopts the named applicable spec requirements at their fixed version; all other retrieved material remains evidence and cannot expand scope. The original scientific author chooses references, Root dispatches exact bytes to independent Transport, and Transport returns facts to Root for Portfolio intake or forwarding to the original DM. Preserve source/parent/operator, delivery scope, model settings, binding and accepted request bytes. No rewriting READY/accepted/uncertain packets merely to update knowledge wording.

The dated pause statements in old plan/review records describe their own scope. They must not override current owner authorization to advance research. Conversely, this audit does not resume anything independently.

## Recommended minimal implementation

Use the existing v3 sections as the implementation contract, with the following bounded work and acceptance.

1. **Publish usable knowledge and provenance first.** On the existing main checkout under one editing owner, move only local-choice passages from FOUNDATIONS §§5–7 and topics 02–04 into SESSION_CHOICES.md; keep original §7 as navigation. Preserve distinctions between expressed owner choices, mechanism hypotheses and unfrozen implementation. Revise README's scope. Publish FOUNDATIONS, all four topics, source map and the existing provenance/review files needed by their links and the plan, including original review/v1. Preserve old review bytes rather than rewriting their verdicts. Check relative links against the committed tree. This first commit creates no new operative reading requirement.
2. **One coherent activation change.** Add short §11.10 and fix only the historical-authority introductions. Extend scientific-tools description/body and add its single references/scientific-reading.md route. Add short scientific/conditional pointers in AGENTS, Codex DM/critic/CM/reviewer, portfolio-task, and corresponding Claude hub/critic/CM/reviewer. No duplicate knowledge body or compulsory reading for mechanical roles. Keep §11.8–§11.9 and frozen semantics intact.
3. **Include Pro compatibility in that activation batch.** In prompt-author SKILL and renderer, permit optional per-reference full commit_sha; absence inherits a validated full top-level SHA. Normalize one effective repository/path/SHA mapping; keep path deduplication. Print that same mapping in TASK/PROMPT/manifest for GitHub and archive_attachment. Preserve the current entire scientific-method paragraph and add short explicit spec adoption/direct reading wording. Amend only conflicting singular-version phrases in direct delivery docs and GITHUB_RESEARCH_COLLABORATION. Do not change Transport validation/materialization/binding/state machine: its similarly named reference_files are attachment byte metadata, not this author source manifest.
4. **Publish, then activate actual consumers.** Root commits explicit paths with required trailers/scope and pushes immediately. Choose a real full SHA from the published activation commit for new method references; do not hard-code its not-yet-known self SHA. Synchronize required committed control-plane bytes into the actual authoring checkout at its clean boundary. Through the next natural scientific assignment/return, provide existing Root/DM/Claude consumers the version and short supplemental-reading pointer. An old loaded skill is not automatically updated by editing disk. Record actual uptake in the existing scientific intake/acceptance, with no separate production reading ledger.

Two publication batches solve the dependency ordering without moving a frozen scientific SHA. A method-source SHA may differ from the science-input SHA. For every new packet, inspect all science-path effective SHAs, not just top-level commit_or_ref. Verify each declared path exists at its exact Git object, the containing commit is reachable from the observed remote published ref, and the fixed TASK uses that map. Provider access is a separate observation. New report links should name immutable commits where a frozen review/source is intended; local Windows-only source-map links remain provenance/access limitations, not automatically usable Pro dependencies.

No root governance edit is performed by this audit. Implementation follows actual owner authorization or the existing proper-node specification delegation, not authority inferred from a reviewer saying the plan is feasible. Within an authorized implementation there is no additional repository ACK step.

## Validation that can demonstrate use

Keep validation proportional and attach evidence to the implementation's normal acceptance record. Scratch belongs to one invocation under temp/ and is cleaned by its creator. Use existing author/Transport tests plus necessary mapping cases; do not start training or a test Pro round.

| Check | Required evidence |
| --- | --- |
| Deterministic author regression | Old full-SHA input still inherits; distinct full method SHA works in both modes; empty/moving effective versions rejected; path duplicate rejected; all scientific mappings unchanged; delivery/binding/routes unchanged. Existing singleton/CALLER_DIRECT and immutable/uncertain-request protections still pass. |
| Positive scientific behavior | Give an actual role a bounded scientific question without naming the answer file. Observe its tool read of the route and relevant passage, then a judgment using a concrete assumption. Example: partial-observation comparison distinguishes actor-available summary from critic-only information; frozen-parameter adaptation does not freeze recurrent state. |
| Inference and semantic behavior | A seed/episode/checkpoint example distinguishes training unit from evaluation repetitions and avoids assumed pairing/fixed seed quotas. A duration/termination CM case reads only relevant passages and preserves the card, reward and budget. |
| Negative behavior | Formatting/push/receipt or accepted technical collection does not preload the textbook, trigger grilling or request knowledge confirmation. A different direction keeps its own endpoint/baseline; reading only §6/topic04 does not import return-only/MAPPO/local investment choices. |
| Root/critic/Claude and stale context | Reuse the same short materials for each relevant entry path. Existing sessions receive the one-time natural handoff and actually supplement their prior context before their next scientific judgment. Report which runtime was exercised; a Codex role simulation does not prove Claude behavior. |
| Offline restricted Pro consumer | It can resolve only manifest-listed fixed files, apply explicitly adopted spec and use the relevant concept without unlisted skills/links. Output supplies exact accessed paths/versions and remaining gaps. This proves manifest self-consistency, not current Pro connectivity. |
| Real use | At the next already-authorized scientific card/intake, record which passage materially supported or changed the reasoning, the relevant assumption and its limit. Root verifies the actual read/decision artifact. At the next already-authorized new Pro request, independent Transport's normal archive plus the response establish actual access and substantive use, or record the exact unavailable source. |

Run a small pre-change positive/negative baseline, then the corresponding changed-role cases. A model already knowing the concept can produce a correct answer without opening the material; that is useful science but does not validate route discovery. Conversely, opening a file without using its content does not validate adoption. No obligation to make a different scientific selection just to exhibit an effect: a supported unchanged decision can demonstrate use when its assumptions and limits are concrete.

Static checks and offline behavior can accept the implemented control plane while honestly retaining “current Pro access not observed.” The first authorized real request closes that observation naturally; an optional explanatory source gap is not an automatic A/B launch block. A decision-critical unavailable source follows the existing node's gap procedure. Do not treat an exhaustive list of all possible future roles/scenarios as a gate for ongoing experiments.

## Handoff and remaining uncertainty

Delivered only this report. No governance edits, staging, commits, experiments, Send, remote source mutation or deployments were performed. Existing knowledge drafts and other writers' files are preserved. Root is next owner for accepting this audit and deciding/assigning an authorized implementation.

There is no blocker to the audit. Missing integration, untracked knowledge and absent behavioral evidence are the implementation work remaining. Publication facts are bounded to the observed main revision and locally known history; source-book access claims were read as prior provenance, not newly reverified. Actual Pro access, actual Claude runtime behavior and all live sessions' loaded contexts remain unobserved. This report does not claim that every future model invocation will follow the new route.

## Additional owner scope: reduce Root's mechanical workload

This section incorporates the owner's follow-up before report completion. Additional direct reads: ROOT_OPERATIONS in full; EXPERIMENT_MONITOR in full; loop-dispatch in full; CM execution/publication/return sections; Operator role; Transport's current GitHub/receipt contract; recent EXPERIMENT_TRACKING entries and selected UCOPE closeout statements. No live processes or browser state were polled.

**Conclusion:** current governing rules mostly suffice. Root should retain scientific allocation/Portfolio judgment, real acceptance and main integration, but should not become the default preparer, collector, poller, archive clerk or execution-worktree remover. A short responsibility clarification in the maintained ROOT_OPERATIONS table, plus precise future handoffs, is preferable to another role or workflow. Two narrow wording gaps merit correction when implementation is authorized.

### Concrete evidence, including where delegation already works

- ROOT_OPERATIONS “Complete deliverables and their owners” already assigns committed inputs, staging, bounded launch, observation, collection and technical acceptance to CM; Operator can own a complete mechanical batch. CM role explicitly says Root need not retype or submit commands and CM publishes source/evidence without a separate intermediate instruction. This is a sound basis for lighter Root work.
- EXPERIMENT_MONITOR says an accepted-handle return is not a request for parallel Root polling. Loop step 5 permits Root supervisor checks only for its own handles or lost-observation reconciliation. Merely adding FOUNDATIONS must not create another observer or extra collection step.
- Tracking P71/P72 reclamation records (EXPERIMENT_TRACKING around lines 382–398 at audit time) already show a bounded CM performing archive/removal and Root accepting report, hashes and before/after registration differences. They establish that Root ownership of reclamation does not require personal execution. Existing preservation checks are material to destructive cleanup, not automatically wasted duplication.
- Yet UCOPE P82 intake line 133, P83 intake line 122 and P84 intake line 125 explicitly return later remote check/scientific-worktree/wrapper reclamation to Root, while retaining the shared authoring checkout. This is a recurring **handoff gap**: the return names the decision owner but does not retain the mechanical executor/event. It can force Root to prepare another cleanup batch despite the originating CM knowing the exact handles, paths and evidence. It does not prove Root personally deleted those targets or that any evidence was lost.
- Tracking P72 MGTAP (around lines 401–406) shows Root found material missing reviewer/runtime/aggregate coverage and returned repair to the same scientific chain, then assigned an existing-role CM when native delegation access was unavailable. These were real acceptance/recovery actions, not mechanical work to abolish in the name of efficiency.
- Transport SKILL opening says “Root retains ... experiment observation” without the narrowing present in EXPERIMENT_MONITOR. This is an imprecise current entrypoint, not proof of a second actual poller. Change just that phrase to observation ownership/reconciliation under EXPERIMENT_MONITOR (Root only for explicitly owned/adopted handles), retaining the shared procedure as the sole detailed rule.
- Tracking “Root personal Pro recovery” records FOLR/SCDMP work under an explicit owner exception. ROOT_OPERATIONS/AGENTS now return subsequent Send/observation/archive to Transport. Do not use the exceptional historical recovery to justify ongoing personal Root transport.
- UCOPE P67 intake distinguishes Transport's `scientific_decision_formed=false` on the short-link receipt from the separately delivered full scientific response. That is a concrete receipt interpretation mismatch which can provoke redundant investigations. A link-only chat answer is neither a complete scientific decision nor proof that the delivered response has no decision. Transport checks message/delivery identities and archive facts; DM reads the full immutable response and determines formation/conformance for its node.

### Minimal assignment map

| Work | Existing executor and required return | What Root retains |
| --- | --- | --- |
| Direction knowledge reading, card, references, Pro question | Original DM; exact relevant passages, choices, frozen scientific inputs and prepared published handoff. DM can give CM mechanical packaging with a fixed source manifest, keeping source=actual scientific author. | Actual scientific allocation when needed, cross-direction dependency handling, ready handoff dispatch; do not reconstruct DM's question or source list. |
| Portfolio knowledge use/question | Root selects the scientific question and references. A bounded existing CM may mechanically render/check/publish on the assigned non-main delivery checkout if doing so saves work; Root remains scientific author. | Portfolio judgment and final scientific text/scope acceptance. Small author commands can stay local when delegation costs more. |
| Source, artifacts, routine checks and direction commit/push | CM in the designated direction checkout, through technical acceptance; report explicit commits, affected checks, named evidence and limitations. | Main index, accepted-commit integration and actual affected-boundary review. Do not rerun all tests or republish every direction artifact. |
| Launch/staging/observation/collection | CM, or its existing Operator for one complete exact batch. Return terminal receipt and verified artifacts to CM then DM. | Track ownership and meaningful state changes; reconcile lost observer once and transfer the same handle explicitly. No parallel polling. |
| Mechanical GitHub reconciliation, recovery and archive | Independent Transport, using exact request/TASK, conversation/message identity, fixed delivery path/commit/comment and prior failed facts. Return whether each delivery is verified, unavailable or conflicting. | Dispatch and conflict routing. Root receives factual receipt and forwards direction bytes/immutable pointers promptly to original DM; avoid doing the same provider/file/comment investigation in Root and DM. |
| Scientific response formation/conformance/intake | Original DM for direction response; Root for Portfolio. Read the full immutable answer and preserve original evidence, identify concrete spec conflict and use proper node. | Parent acceptance, cross-direction implications and integration. A necessary scientific read is not duplicate Transport work even if both access the same file for different purposes. |
| Invocation test scratch | Creating test agent/process; clean its own scoped scratch after retaining necessary diagnostics. | No routine garbage collection. Track only a real unresolved blocker; never delete another active invocation's scratch. |
| Terminal remote execution worktree/wrapper reclamation | Prefer originating CM after Root confirms accepted integration/retention decision. CM can reuse its existing suitable executor for the exact mechanical batch; no forced new cleanup specialist. Prepare candidate paths, terminal/no-live-dependency facts and preservation mapping during collection; after trigger, archive/verify/unregister/remove and verify disk plus worktree registration absence. | Root remains accountable for reclamation, integration readiness and preservation/reconciliation acceptance. Shared authoring worktrees and live delivery dependencies remain; no blanket recursive deletion or deletion before verified preservation. |
| Obsolete shared branch/checkout retirement | Root makes the cross-direction/live-writer/PR/pending-delivery decision; assign bounded mechanical preservation/removal to an existing responsible CM if worthwhile. | Main/index, final integration and recovery-reference/retirement decision. Do not delegate away unresolved scientific acceptance. |

For cleanup, existing AGENTS §6 already permits this split: Root “owns reclamation” is responsibility, while the document's operating model rejects exclusive role permission barriers; current tracking demonstrates delegated execution. No change to preservation or deletion authority is necessary. A useful **minimal future ROOT_OPERATIONS clarification** is: “CM's terminal return includes its exact cleanup inventory and preservation/dependency facts. Root confirms the integration/retention boundary; the originating CM remains the default executor of assigned remote execution-worktree/wrapper closeout and returns verified absence. Root accepts reclamation; shared authoring and live delivery checkouts remain governed by AGENTS §6.” This makes the event and executor explicit without removing Root accountability. Do not retroactively rewrite frozen cards; put the concrete closeout assignment in the existing return/follow-up.

For Pro receipts, existing roles also suffice. Route uncertain delivery back to the same Transport with the precise request and observed discrepancy; route scientific conformance to DM. Use factual language such as “chat is a link receipt; response-file delivery verified at SHA/path; scientific conformance pending DM.” Do not treat a generic `scientific_decision_formed=false` on a receipt as a direction disposition. First improve the existing human-readable receipt/entrypoint wording; this audit does not justify a new receipt schema or Transport state machine. Root still reconciles conflicting facts enough to choose the correct recipient; it need not complete both recipients' investigations itself.

### How to check that Root is actually doing less mechanical work

At the next naturally occurring accepted batch, inspect existing handoffs/returns for three outcomes: (1) CM/Operator completes the technical chain without Root supplying per-command steps; (2) the named CM performs integration-triggered closeout while Root accepts its concrete preservation/removal evidence; (3) Transport resolves a mechanical delivery discrepancy and DM consumes its immutable response, without duplicate browser/Issue hunts by Root. Existing message and artifact records suffice; no time tracker, telemetry service or new production ledger.

Knowledge activation should be prepared as a complete bounded implementation/check/review batch by one existing responsible engineering executor where authorized. Root's remaining contribution is deciding the scope, reviewing actual change/behavior evidence and serializing main publication. Because Root owns main/index, a child should return ready explicit paths rather than operate that index concurrently. Do not turn the two publication stages into per-file permission messages or require Root to run every behavior fixture.

These are proposed responsibility refinements, not claims that all current Root work is avoidable or that every historical return was inefficient. The audit did not reconstruct every live task transcript or measure saved time. No additional mechanical assignments were dispatched by this audit.

## Stage 1 independent acceptance — 2026-09-09

**PASS for the knowledge/session-choice separation, with no required correction.** Root reports owner authorization to implement and requested this bounded independent review. The earlier audit above remains an as-of record; this section updates only the six stage-one working files, not publication or stage-two adoption status.

I read current FOUNDATIONS.md, README.md, SESSION_CHOICES.md and topics 02–04 in full and compared their content with the original passages read during this audit. The originals were untracked, so this is a direct content comparison against the earlier actual reads, not a claim of a Git parent diff. Root independently owns publication-link checks; the stage-two CM owns control-plane implementation and behavior tests.

| Acceptance item | Finding |
| --- | --- |
| Owner choices preserved | SESSION_CHOICES retains existing environment/communication complexity; timely reliable team summary and same-information comparator; fixed-parameter response to movement/failure/recovery; recurrent MAPPO plus central critic; simple-to-later reward choices; return-only local ranking with costs recorded; asynchronous skill framework and optional sharing/combination of historical directions. No original accepted preference is relabelled as unexpressed or universally mandatory. |
| Hypotheses versus implementation | Reusable cooperation/interaction structure remains explicitly replaceable and falsifiable. MAPPO version/adaptation/training configuration remains unfrozen. The text identifies the continuation-investment sentence as the originating discussion's strategy, not a theorem or launch condition. Fixed parameters still allow memory, belief, skill-state and action updates; joining, cross-size generalization and online parameter learning remain later questions. |
| No local-choice leakage | FOUNDATIONS §5 removes the local “we can study” proposal; §6 replaces the local investment strategy with a neutral decision-scope statement; §7 remains a navigation anchor. Topics 02/03 remove their selected task assumptions, and topic04 removes return-only ranking and the local investment policy. Reading only §6/topic04 no longer supplies those local choices as general rules. |
| Conceptual meaning retained | The task/return formulation, partial-observation and recurrent-state distinctions, CTDE information boundary, representation versus finite learning, reward transformation caveats, options/SMDP duration semantics, training-unit versus episode distinction and claim-proportional evidence limits remain. Topic02's conditional recurrent MAPPO discussion is general comparator reasoning, not a requirement to use MAPPO. |
| Citations and provenance | General-concept citations remain at their passages. MAPPO paper/code support previously beside the choices moves with them to SESSION_CHOICES; the same sources remain in topic02. README and FOUNDATIONS still link the source/coverage/correction records and do not upgrade prior partial reading into full-book verification. No new claim of source retrieval or actual Pro/role adoption is made. |
| Authority and scope | SESSION_CHOICES expressly assigns no seed/model/run budget and does not override other cards, resource admission or Portfolio rules. Its Pro paragraph requires explicit manifest inclusion for a task actually using those choices; navigation links confer no extra reading scope. README separates completed document separation from unverified role/Pro use. |

Reviewed working-file SHA-256 (actual checkout bytes):

| File | SHA-256 |
| --- | --- |
| FOUNDATIONS.md | c1f7d6c68fcec55de48ea555346d5d65af8d311e28502be43a2b05436a174247 |
| README.md | 421f931449b524f2a27c4ed9e78aad340846c194e695db2c87ddeb03d81d7e96 |
| SESSION_CHOICES.md | 4729fd4631d4918f93ec0ef3c6aa7b2ac4bbd5c7b07b587881b7ad950ad6503b |
| topic-notes/02_MARL.md | 4dae3729dc54db39599a689712fa1f6ccdb80d5fd2f08e96757bcf8686e6e0b9 |
| topic-notes/03_HIERARCHY_ASYNC.md | 9fd3736fefe5c3cf52432b1ab3d4ed220188b1666bf10163ad55f5dcca69f06c |
| topic-notes/04_EMPIRICAL.md | 99b7e727a890d4e93a64b5c0f44fe588e383b5de56f2da663fb3f864c6d8293c |

At review time FOUNDATIONS and SESSION_CHOICES still appeared untracked. This acceptance is not a publication claim, a stage-two approval, an actual-use test or fresh paper verification. I appended only this review, performed no index/commit operation and did not alter the reviewed files. Root may publish the accepted stage-one bytes after its own link/integration checks within the existing authorization.
