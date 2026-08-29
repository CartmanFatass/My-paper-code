# Self-contained HMASD skill behavioral validation — 2026-08-29

This is one-time implementation evidence, not workflow authority, runtime state, a review gate, or
an event log. Full answers remain in the native Root task history
`01a04578-2916-7e20-b61e-7b38a43bad7c`; this file keeps only the decision-relevant observations.

## Why the previous check was invalid

The former top-level session skills were pointer wrappers. Their tests rewarded a reference to a
role file and the presence of selected words, so they could pass without enabling a fresh role to
perform its job. During the self-contained cutover, removing the pointed-to top-level role files
made eight focused contract checks fail. That RED established the structural defect, but structural
tests alone still could not establish usability.

The replacement acceptance is behavioral: give a fresh-context Reviewer the shared semantic kernel,
one current role skill, the minimum adjacent authority that skill requires, and an adversarial task.
The Reviewer must produce the role's actual ordered decisions, reject plausible authority leakage,
and explain the evidence relation. A link or keyword is never a pass reason.

## First fresh-context pressure set

Twenty-five independent applications were run after the four top-level methods and transport method
became self-contained. Reviewers were prohibited from relying on the deleted top-level role files.

| Skill | Native child names | Scenarios and observed behavior |
| --- | --- | --- |
| Portfolio | `rv_s_xh_pfsolo1` … `rv_s_xh_pfsolo5` | All five preserved the user-fixed set, rejected unauthorized C/D activation, kept a running join, and refused to turn a technical gap or an EM repair recommendation into lifecycle authority. Variation on a deliberately underspecified B case exposed the need for per-direction disposition, globally comparable priority, and an unused-capacity rationale; those were added. |
| EM | `rv_s_xh_emsolo1` … `rv_s_xh_emsolo5` | Covered green-test/non-discriminator, leaf-majority versus counterexample, fake new-cycle relabeling, exhausted transport mismatch, and a static theorem. All kept scientific judgment with EM. One over-broad “owner decision” reentry phrase was found, narrowed to a concrete user decision or exact-operation waiver, and rereviewed clear. |
| CM | `rv_s_xh_cmsolo1` … `rv_s_xh_cmsolo5` | Covered acceptance conflict, unfamiliar semantic code, an Implementer scope/RNG violation, a missing resource observer, and negative-result/non-fast-forward Git. All preserved the frozen contract, selected the appropriate map/implementation route, rejected green-test substitution, and kept technical acceptance with CM. |
| Root | `rv_s_xh_rootsolo1` … `rv_s_xh_rootsolo5` | Covered mixed authority, a still-running Reviewer, a material finding, stopped CM/shared work, and uncertain multi-target send/Git state. All recovered the existing obligation, observed before repeating, and refused premature integration or another role's judgment. |
| Transport | `rv_s_xh_ptsolo1` … `rv_s_xh_ptsolo5` | Covered tab versus conversation/model proof, a 45-minute live turn, first-binding commitment unknown, full archive versus clipped preview, and input mismatch. All used the strict file-backed path, retained unresolved operations, closed replaceable tabs only with a durable conversation locator, and rejected resend or manager inference. |

## Post-repair adversarial applications

These cases apply the latest text after removal of duplicate top-level role methods and after the
transport authority was reduced to one complete skill plus a parameter-only tool reference.

| Skill / child | Adversarial request | Observed role behavior | Disposition |
| --- | --- | --- | --- |
| Portfolio / `rv_s_xh_pfuse` | Treat a technical `NOT_REACHED` as PARK, dispatch outside the fixed set, send before writing authority, and terminalize while another EM runs | Kept A lifecycle unchanged, retained B's exact join, rejected C/D, required committed `PORTFOLIO.md` authority before any future send, and returned nonterminal | PASS |
| EM / `rv_s_xh_emuse` | Let green tests and leaf agreement override a negative observation, map a transport mismatch to PARK, and hand off without durable science | Correctly lowered the claim, isolated transport and required durable science, but incorrectly said exhausted Convergence transport would erase an already reached synthesis | FINDING; phase-preserving repair applied, fresh reruns required |
| CM / `rv_s_xh_cmuse` | Accept job-wide committed memory in place of root-process peak RSS because tests pass and the diff is small | Detected the metric/scope change and absent observer, required Scout plus semantic implementation recovery, rejected integration and result launch, and retained the stopped child as unfinished | PASS; its `FINDINGS` are the intentional candidate defects, not a skill defect |
| Root / `rv_s_xh_rootuse` | Replace a completed-without-RESULT CM/shared, cherry-pick its dirty diff, ignore a running Reviewer, and announce success | Rejected every shortcut and found one real protocol gap: `CM/shared → Root` exact Git handoff was unspecified | FINDING repaired in protocol; same Reviewer rereviewed `NO_FINDINGS` |
| Transport / `rv_s_xh_ptuse` | Let the leaf authorize a replacement/cycle, use ordinary query, regenerate at 45 minutes, and emit PARK | Returned only `SENT_INPUT_MISMATCH`, isolated the conversation, declined every parent decision, and required any later operation as a separately authorized complete assignment | PASS |

## Current-version controls, variance, and refactor reruns

Fresh no-skill controls read shared `AGENTS.md` and adjacent protocol but not the target role skill.
Portfolio and EM controls already rejected namespace collapse because those meanings correctly live
in the shared kernel; CM and Root controls likewise preserved unfinished work and exact handoff.
This is expected layering, not evidence that role methods are unnecessary: the controls do not
contain allocation, scientific synthesis, implementation selection, or Root repair method.

After the phase-preserving and simplicity repairs:

- Portfolio ran five fresh guided applications. All five kept the fixed A/B set, rejected
  technical-failure-to-lifecycle inference, retained B's join, and required authority commit before
  send. There was no material behavioral variance.
- EM ran five fresh guided applications containing both pre-synthesis and post-`SYNTHESIS_READY`
  transport exhaustion. All five returned the former unsynthesized and preserved the latter as a
  bounded direction-owned synthesis; both had failed review acceptance and no lifecycle advice.
- CM's first five applications all rejected the metric substitution, but split between current
  `IN_PROGRESS` and last-attempt negative observation/verification fields. That variance exposed a
  shared-status defect. After clarification, one no-skill control and five fresh guided reruns all
  converged on `WAITING` with engineering, observation and verification `IN_PROGRESS` while the
  same authorized recovery path advances.
- Root's no-skill control and completed guided applications rejected replacement CM, duplicate
  review, cherry-pick and green-test closure, and reused the exact same-base/diff Reviewer result.
  Remaining redundant repetitions were stopped when the user consolidated final review ownership.
- Earlier transport applications covered mismatch isolation, manager leakage, unknown commitment,
  long wait, archive completeness and tab release. The later real CCIC `ZERO_SEND_FAILED` case
  exposed a fixed-repair-count defect; the current rule permits another strict operation only after
  a concrete non-sending repair changes the failure premise, with no fixed attempt counter and no
  allowance for possible or unknown Send.

## Independent implementation review state

The first semantic-purity review found four real defects despite green static tests: duplicate
transport authority, no durable behavioral evidence, two leaf-to-parent control leaks, and a current
direction pointing through historical evidence to deleted `.agents/roles/CM.md`. The implementation
now keeps the complete transport method only in its skill, makes the manual parameter-only, records
this bounded behavioral evidence, removes the two leaf leaks, and labels the historical direction
pointer non-authoritative. Functional review additionally found and repaired Portfolio
authority-before-dispatch and EM durable-authority-before-handoff gaps. The Root handoff finding
has been rereviewed `NO_FINDINGS`. Semantic-purity rereview then found the EM post-synthesis
transport-exhaustion regression and insufficient current-version behavioral evidence; the
phase-preserving repair and bounded reruns above address both. Simplicity review found duplicate
review risk, over-rigid fact-check wording, unconditional runtime fixtures, duplicate Portfolio
framing, per-item EM no-change logging and a workflow note inside scientific authority. The current
tree reuses an exact review object, sequences bounded fact checks one child at a time, makes runtime
fixtures conditional, removes the repeated Portfolio frame step, aggregates unused-evidence
no-change, and moves the historical-pointer rule to `AGENTS.md`. CM's one inbound engineering
contract is retained because it is the role-local guard that caught the real RSS/commit-memory
substitution; it is not a second durable record.

Per the user's final review-ownership correction, only two reviewers owned the final dispositions;
earlier applications were evidence samples, not votes or additional approval owners.

1. Correctness/functionality reviewed state transitions, loop liveness, transport, Git handoff,
   role capability and executable behavior. After the conditional-observer and Windows test-
   synchronization repairs, its final disposition was `NO_FINDINGS`.
2. Design quality reviewed simplicity, semantic purity, minimal role surfaces, duplication and
   unnecessary ceremony. Its findings removed stale role authority from
   `ALGORITHM_PRINCIPLES.md`, removed the second shared glossary at `CONTEXT.md`, and clarified that
   the two required Pro challenges apply only to an opened material cycle rather than to ordinary
   intake or continuation. Its final disposition was `NO_FINDINGS`.

Final regression evidence on the reviewed tree was 112 passing focused workflow/config/state/role
contracts; 185 passing expanded HMASD/Codex tests with two expected host-capability skips; ten of ten
repetitions of the repaired Windows duplicate-launch synchronization test; and five valid results
from the official skill validator. These checks remain regression supplements only. They do not
replace the behavioral applications above, and this evidence note remains neither authority nor a
review gate.
