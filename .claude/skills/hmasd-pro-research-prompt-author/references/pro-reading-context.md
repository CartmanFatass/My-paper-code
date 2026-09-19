# Pro reading context

Shared authoring reference for direction questions and owner-triggered Portfolio reviews.
It selects existing sources, not another scientific spec or automatic consultation trigger.
Put concrete paths, sections, revisions and their purpose in the existing question; do not send
only this generic reading matrix. Pro cannot inherit local skills or role instructions.

## Common context and source meaning

Give Pro the question type, the choice it informs, the applicable owner instruction, current
pause and remaining allowance. Advice does not resume research or grant fits.

- **Current governance:** `docs/project/OPERATING_CONSTITUTION.md`, relevant sections at the
  question's published source revision. Sections 1, 5, 7 and 8 explain exploratory purpose,
  advisory Pro, no extra gates, and scientific minimums; add the authority/budget/record sections
  used by the question. State any applicable newer owner instruction explicitly and accurately.
- **Current methods:** named sections of `.agents/skills/*/SKILL.md` selected below. These are
  reasoning and execution methods under the constitution, not another source of permission.
- **Standing and evidence:** relevant `RESEARCH.md` rows and pause, selected NOTES entries,
  claim note and actual run outputs. Include supporting outputs needed to assess the comparison
  and contrary results, not the entire direction history. A summary is not raw evidence.
- **Frozen experiment contract:** original card/claim and directly bound inputs at their own
  recorded revisions, distinct from current methods. New methods do not retroactively change
  seeds, endpoints, output obligations or completed results.
- **Explanatory/historical sources:** foundation/primary passages or old specs only for a
  specific unresolved concept, frozen obligation or before/after comparison. Identify their
  purpose. Historical specs, old Pro finality and old chat decisions are not current governance.

For ordinary new work, scientific-tools and research-engineering replace the historical
MARL_EMPIRICAL_EVIDENCE_SPEC, ENGINEERING_SCOPE_SPEC and MARL_RUNTIME_ENGINEERING_SPEC.
Do not ask Pro to reconstruct current rules from recursive historical links. For a frozen
object, cite precisely the historical section it binds.

## Reading profiles

Select concrete sections using the applicable profile. All paths below are repository-relative
and resolve at the question's published revision unless a separate evidence/frozen revision is named.

| Question | Current governance and method | Evidence and conditional reading | Requested reasoning |
| --- | --- | --- | --- |
| **Portfolio**, only when owner-triggered | Constitution §§1–5, 7–8; portfolio-task Steps/Boundaries; scientific-tools Comparators, Statistics, Cost and exposure | RESEARCH rows/pause for affected active, reserve or archived directions; their relevant NOTES, CLAIM and supporting/adverse run summaries; queued recommendations and real options. Engineering only for disputed feasibility/cost; use existing Git/run evidence if overhead matters, without owner-hour bookkeeping | Compare how judgments changed, surviving reasons for hope, contrary evidence, uncertainty, practical effect/headroom where relevant, known cost, substitutability/reversibility and smallest useful investment; distinguish an untested explanation from a tested failed repair. Investment preference is not a scientific verdict. Recommend; owner decides |
| **Synthesis, diagnosis or prototype bridge**, when useful | Constitution §§1–5, 7–8; scientific-tools Update the working explanation / Simple-model and literature bridges / Statistics / Cost | Prior explanation and prediction, motivating observation, relevant supporting and contrary runs, actual information/learning path; primary passage for a proposed analogy. Give missing telemetry as missing, not a diagnosed cause | Separate observations, belief updates and new conjectures. State competing predictions, assumptions and omitted MARL coupling. Prefer the observation that changes the live judgment; replication, targeted repair or no useful new action are legitimate. No mandatory insight, exhaustive diagnosis or toy-pass gate |
| **Hypothesis generation** before exploration | Constitution §§1, 3, 5, 7–8; scientific-tools Explore, Comparators, Cost and exposure | Relevant RESEARCH row/pause, NOTES question, failures/alternatives and baseline configuration/evidence. Add foundation/primary passages for the mechanism; engineering for material implementation/feasibility constraints | Task-proportionate candidates, including targeted revision or simplification, inherited constraints, intermediate/native predictions, strongest simpler explanation, discriminator, fit cost and dominant non-fit work. No fixed count or required new architecture. No prerequisite proof, full headroom census or search merely to justify ordinary learning exploration |
| **Confirmation/claim review** | Constitution §§3, 5, 7–8; scientific-tools Confirm, Comparators, Statistics, Cost and exposure | Exact prospective CLAIM or named frozen original card, selection/development evidence, baseline information/training rights and supporting/adverse runs. Add engineering Checks/Runtime notes and exact code/diff when numerics, replay, batching, collection or cost affects the claim | Reconstruct claim, population, estimand, selection/stopping protocol and matched comparison; test alternatives and uncertainty/equivalence interpretation. Return strongest material objection, evidence, smallest discriminator, limits and MATERIAL_DISSENT yes/no. Pre-confirmation review does not certify nonexistent results |
| **Control-plane review**, only explicitly owner-requested | Current Constitution and owner change request; CONTROL_PLANE_MAP/GUIDANCE as descriptive navigation; actual changed skills/role/config/publisher sections | Fixed before/after revisions and relevant diff; old spec or Pro revision only as identified comparison evidence; actual validation/runtime facts when available | Separate intended simplification, method relocation and unsupported omission; trace source -> consumer -> generated adaptation. Check no new authority/approval/record system. Source consistency does not establish live-session adoption |

Skill names in the table expand to `.agents/skills/hmasd-<name>/SKILL.md`; map/guidance are under
`docs/project/`. Engineering means `hmasd-research-engineering/SKILL.md` with the actual task's
invariants and source, not all engineering history. Control review uses the owner's existing
designated document/answer location; this profile adds no regular round or Portfolio trigger.

## Put the context in the question

Use plain lines in the existing NOTES question or RESEARCH review section. Give each selected
file/section and why it matters. Files in the published question commit may explicitly inherit
`source_sha`; other evidence and frozen inputs use their full own sha. The actual send message
supplies the full `source_sha` after publication, avoiding a self-referential hash in the question.
Links can instead use an already published method revision. Verify actual paths/sections and
publication, not merely a plausible filename.

```text
Context:
  Governance: <path, sections, revision; current instruction/pause and applicable allowance>
  Method: <selected skill sections, revision; the judgment they support>
  Evidence: <selected NOTES/CLAIM/run paths, revisions; supporting and contrary observations>
  Frozen contract, if any: <original paths/revisions; meaning that must remain unchanged>
```

Substitute actual sources; never send unresolved placeholders. In a continuing conversation,
the supplied current governance and methods replace conflicting old chat instructions for this
question, while named frozen evidence retains its original meaning. Apply this to newly authored
questions; context updates never justify rewriting or resending an accepted/uncertain request.

## Include in the actual send message

The author includes the following with the normal repository/branch/source_sha/target/headings
and fixed question URL. Transport sends the completed message unchanged:

> Read the pinned question and its Context sources before answering. Paths marked source_sha
> resolve at the full source_sha supplied here; other sources keep their explicitly named revisions.
> Treat the stated current owner instruction and constitution as governance, skills as applicable
> methods, and historical/frozen files as the bounded evidence or contract described in the question.
> These current instructions replace conflicting old chat instructions for this question; keep
> the named frozen contracts intact. Do not substitute chat memory or a moving branch for inputs.
> Give advice within the assigned question; do not launch experiments, grant budget, or create
> new approval requirements. Cite the sources actually used for consequential conclusions and
> state any decision-critical source you could not read. Do not claim an unread source was verified;
> make only supported conclusions and identify the dependent gap.

Append the existing answer-only write instruction: fetch the latest target blob for writing,
preserve the question and all other bytes, stop on overlapping edits, return the actual commit
or complete answer in chat on delivery failure. The latest writable blob is not a substitute
for pinned reasoning inputs. Source references and limits belong in the normal answer prose;
no read-receipt table, separate context manifest or extra approval is required.

On return the author checks consequential recommendations against the applicable methods,
frozen meaning and actual evidence. Address omissions in the existing adoption/rejection note;
an unsupported recommendation does not automatically trigger another Send or review round.
