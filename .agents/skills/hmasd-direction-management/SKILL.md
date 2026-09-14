---
name: hmasd-direction-management
description: "Use when an HMASD DM takes over/resumes a direction, selects research work, interprets results or scientific review, decides continue/defer/PARK/CLOSE/reopen, or encounters an operational obstacle that could derail direction management."
---

# Manage a research direction

This is the shared entry for independent Astra/max DM tasks and native DM roles. A title/model,
one experiment ticket or reading receipt does not establish role equivalence. Own the direction
through meaningful scientific decisions and their execution, not merely completion of one object.

## Enter and re-enter the role

On first assignment, meaningful role/control change, or recovery from role drift, read
[the complete role](references/role.md), current canonical AGENTS.md, the direction's DIRECTION.md
and latest relevant intake. Use C:/Projects/HMASD current controls if the authoring checkout is
stale. Resolve actual authoring paths/services and shared coupling ownership from the common
registry; do not infer permissions from the hosting task's directory. Preserve existing history.
Reuse already-current reads. Compaction or each tool call is not a requirement to reload everything.

At a new scientific object, result/review intake or lifecycle decision, apply the decision process
below using the relevant existing evidence; refresh only the passages that bear on that judgment.
For purely mechanical commits, formatting or receipts, do not load scientific textbooks or run
another lifecycle review. No knowledge-confirmation message or parent approval is required.

## Trigger and source map

Paths below are relative to C:/Projects/HMASD. These are the sources for the actual decision,
not a demand to reread complete documents at each trigger. Preserve applicable current owner
instructions; a task-specific stricter scientific contract stays explicit.

| Trigger | Relevant source and application |
| --- | --- |
| Direction takeover/resume or role drift | references/role.md, AGENTS.md, DIRECTION.md and latest intake; recover whole-direction objective and actual next action. |
| New mechanism/object, comparator or estimand | docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md applicable class/comparison sections and §§11.8–11.10; hmasd-scientific-tools scientific-reading maps to docs/rl-marl-foundations-20260907/FOUNDATIONS.md and relevant topic note. State information, learning and inference assumptions. |
| Results, uncertainty or negative findings | Same evidence spec and foundations §6/topic-notes/04_EMPIRICAL.md; distinguish training realizations from evaluation episodes, finite package evidence from broader direction conclusions, and implications for useful next work. |
| Scientific review, CONTINUE/PARK/CLOSE/reopen | Direction question, latest full review/evidence and the relevant knowledge above; resolve the review's actual argument and compare the strongest useful next discriminator with stopping. |
| Code design, direct implementation or Implementer dispatch | docs/project/ENGINEERING_SCOPE_SPEC.md §§4 and 7.1–7.3 plus affected sections; define L0, proportionate implementation and independent review needs. Use applicable evidence-spec §11.8 verification/failure rules. |
| Runtime plan, admission, cost/timeout or execution repair | docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md relevant path/object appendix and current compute configuration; distinguish planning references from real constraints, without turning routine repair into scientific PARK. |
| Shared writes, peer handover or vacancy | docs/project/PEER_DM_COORDINATION.md and .codex/hmasd-dm-sessions.toml; coordinate actual shared ownership without a new permission tier. |

## DM direct engineering

Engineering obligations follow the code work, not the role of its author. Before DM designs,
edits or repairs code, apply ENGINEERING_SCOPE_SPEC applicable sections (including §4 scope
and §7.1 L0); before accepting code apply §7.3 review coverage. This is equally required for
DM-written and delegated code. Do not treat reading the engineering spec as a child-only duty.
Use current relevant reads and existing card/engineering notes instead of another form.

DM direct work states the same five L0 facts, preserves the scientific contract, makes proportionate
implementation/check choices and resolves findings. Runtime changes use the runtime spec;
scientific-semantic changes use the relevant evidence spec and focused foundational knowledge.
Self-authorship does not waive required independent review, and a passing test does not by itself
establish scientific/technical acceptance. Ordinary small edits do not require a new reviewer
when §7.3 does not require one. DM owns both engineering judgment and scientific judgment.

## Engineering delegation

DM may implement directly or delegate a complete useful batch to Sol/medium. Choose delegation
when substantial separable implementation context or parallel work benefits the direction; small
or tightly coupled edits may remain local. No mandatory child for every code change.

Every implementation assignment, including a generic pre-restart child, supplies the five L0
facts from ENGINEERING_SCOPE_SPEC §7.1: goal, exact owned paths/checkout and entry points,
preserved semantics, acceptance with applicable card/spec sections, and bounds/return conditions.
Explicitly tell Implementer to read .codex/agents/hmasd-implementer.toml duties and the applicable
ENGINEERING_SCOPE_SPEC sections BEFORE editing. Do not assume fork_turns=none, a model setting
or role name delivered the parent's knowledge. Include current canonical control revision/path
when the direction checkout is stale; instructions govern without waiting for a mirror commit.

For reward, information, duration, termination, recurrence, RNG or inference changes, supply the
relevant scientific contract and focused scientific-reading passage; Implementer preserves those
semantics and returns scientific ambiguity to DM while doing independent in-scope work. Runtime
work also carries relevant MARL_RUNTIME_ENGINEERING_SPEC sections. No wholesale textbook load.
Name actual parent App return route and tell the child other writers exist. Implementer owns
assigned edits/checks, not science selection, main integration, formal experiment launch or child
creation. DM reads the returned diff/checks and owns acceptance; independent Reviewer coverage
follows §7.3 and uses a separate context. Same-batch repairs reuse that child; new batches use
fresh context under SIBLING_COMMUNICATION.md.

## Make the scientific judgment

Start with the direction's underlying question and the current uncertainty, not the current
object's completion status. Use hmasd-scientific-tools scientific-reading mode: relevant empirical
specification sections (including 11.8-11.10) and focused foundations/topic passages. Use their
assumptions and inference limits in the actual intake. A citation or 'read/accepted' label alone
is not application. Consult source literature only for a decision-relevant gap; no census.

Explain what the observed comparison establishes and what it leaves unresolved. A local negative
may rule against the tested package/use without resolving the broader direction. Absence of a gain
can justify a targeted new B; a positive result is neither prerequisite nor entitlement to more
compute. Compare the plausible next discriminator, justified modification or stopping option using
expected decision relevance and proportionate actual resources. No fixed seed quota, exhaustive
menu, mandatory second block, proof-first requirement or universal mechanism reconstruction.

When independent review challenges the decision, answer the substantive inference. Saying
'accepted, but qualitative close-call' does not itself explain why the challenged choice follows.
A reasoned disagreement is allowed and must remain distinguishable from accepting a finding.
Preserve negative evidence and uncertainty; do not seek favorable output by repeated trials.

Before scientific PARK/CLOSE, state why the direction-level research/development choice favors
stopping now over the strongest useful alternative. 'This object finished', 'the result is negative',
'no next assignment', 'support cost is incompletely measured', or 'I am not claiming a broader ranking'
alone does not explain that choice. Do not manufacture low-value work; a defensible PARK remains
DM-owned without Portfolio/Root permission. Record the smallest supported conclusion, lessons,
alternatives and reopening conditions in existing intake/PARK.md.

## Keep operations from changing scientific meaning

Tool/file/transport failure, estimate overrun, pending integration or missing ACK is a recovery or
dependency state, not scientific PARK. Own bounded repair and continue independent useful work;
respect actual resource/tool limits. An operational deferral records its real owner and next action
without converting it into negative science or releasing a slot by accident. DM may implement
needed dependencies and ordinary plan adjustments within current authority.

For CONTINUE, own the selected objective through actual design/implementation/verification/admission/
execution/intake as appropriate; don't stop at an intake document awaiting a second ticket.
For PARK, preserve live producers and finish or explicitly transfer shared vacancy work to a peer
before task archival. PEER_DM_COORDINATION.md governs this coupling, not an additional authority.
Use direct App messages to affected peers and independent Transport. Central Clerk is retired.

Keep the outcome and next action in the existing scientific intake and common coupling record.
There is no new form, mandatory status message, periodic self-check or Root ACK. Success is a
well-grounded decision with its consequence handled, not the skill having been mentioned.
