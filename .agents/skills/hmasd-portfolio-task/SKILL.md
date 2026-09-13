---
name: hmasd-portfolio-task
description: Use when DM prepares or intakes direction-related Portfolio decisions, or Root requests and intakes a new direction to fill a formally vacated slot in the four-direction working set.
---

# HMASD Portfolio materials and Pro intake

Portfolio is the existing `portfolio:cross_direction` Pro node. DM authors and intakes ordinary
direction-related questions. Root authors and intakes only vacancy replacement after a formal
direction pause/closure leaves fewer than four occupied slots. Pro selects the new direction and
bounded investment; Root creates its DM from the complete conforming decision. ROOT_OPERATIONS.md maintains this
responsibility split. Existing Direction Pro nodes remain separate.

## Ground the question

Start with the assigned question and current affected Portfolio rows/intakes. Read only relevant
sections of `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`: §8.1 maintains Portfolio principles,
§7 lifecycle meanings and §§11.7–11.10 investment/evidence calibration. AGENTS §§2,4.7–4.8 maintain
final authority, specification changes and asynchronous owner overrides. Use scientific-tools for
scientific reading or analysis, not for mechanical routing.

Prepare a decision-ready packet from:

- the specific choice, options, recommendation and operational consequences;
- applicable Portfolio principles, evidence class, claim ceiling, MEI/headroom and frozen limits;
- empirical and engineering experience, prior decisions and their actual effects, with exact
  evidence sources, scope, contrary results and known complete costs;
- uncertainties, the smallest useful investment and the evidence that would change the choice.

Explain how the principles/specifications/experience bear on each option. Do not just attach a
reading list. Ask Pro to state its choice, decisive reasons, uncertainty, revisit condition and
bounded consequences. Historical experience informs judgment but cannot silently amend a spec.
If a rule change is necessary, name the rule, necessity and scope for the proper node.

A relevant DM authors a scientific cross-direction packet; other DMs may supply direction facts.
For vacancy replacement, Root instead assembles the final DM disposition/evidence, remaining
occupied/reserved slots, current priorities and resource constraints, and asks Pro to select the
next new direction and bounded initial assignment. Cite DM scientific facts without inventing
local scientific recommendations. Reuse a pending replacement request; no request per timeout,
object completion or temporary blocker. Existing overlap above four drains without forced stops.
Root can request missing facts but does not rewrite scientific content. If the author becomes
unavailable, Root explicitly transfers the remaining scope and evidence to another relevant DM.

## Publish and route

Use `hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision` and
`caller_role=portfolio`. These choose the node, not the author's native role. Bind every in-scope
direction in `direction_ids`. Include the current Portfolio snapshot, applicable principle/spec
sections and only needed experience/card/evidence references at their exact published revisions.
Include the machine-generated exposure line (zero new exposure when appropriate) and any required
per-arm projection; no consultation-only exposure experiment is needed.

Reuse `portfolio:cross_direction`. Source and parent are the actual author (DM, or Root for
vacancy replacement); operator is that author's reusable native Luna/high Agentify Transport
child. The author dispatches the exact committed handoff, waits natively, receives the full
archive and performs conformance intake. Root integrates a DM's resulting operational mapping;
for its own replacement request it records and applies the complete Pro decision directly.
Serialize the shared portfolio:cross_direction binding; do not overlap another accepted request.
An existing accepted packet retains its original binding through observation-only recovery.


## Read the complete response and return an application mapping

Read and preserve the full immutable Pro response, not just the receipt or a summary. Check the
bound question, evidence class, current owner instructions, applicable specs, scientific meaning
and declared budget. An incomplete response or concrete conflict goes back to the same Pro node
with exact evidence; no local substitute or new approval tier follows. Independent conforming work
continues. Direction/Portfolio questions have no local provisional disposition on a Pro blocker.
Reconcile actual full-response delivery before treating a transport status as absence of a
decision. Short chat receipts and their hashes are separate from full Git response bytes and
hashes. A verified complete response enters this conformance check while Transport repairs its
receipt bookkeeping. If no decision exists, Transport retains the original request recovery;
do not create a replacement Portfolio question solely to escape an operational blocker.

For a complete conforming decision, record the actual choice, reasons, limits, opposing evidence
and affected direction/actions in the existing Portfolio decision record. Return that record and
an execution mapping to Root, or apply it directly when Root owns the vacancy question. Pro is final under AGENTS §4.8; Root applies and integrates without
waiting for per-item owner ratify. Root does not rewrite scientific conclusions during integration.
A specification change follows AGENTS §4.7 and does not itself accept code or launch an experiment.

Use `hmasd-owner-item` to provide the Chinese decision packet and actual application trace.
`PRO_FINAL / OWNER_DELEGATED` records the Pro decision under owner standing delegation;
`ROOT_INTEGRATED` means integration, not a second verdict. Record planned/applied/blocked truthfully,
keep owner replies distinct and apply real asynchronous overrides at clean boundaries. Historical
unratified proposals are not automatically authorized by this prospective workflow change.

Update only the supported lifecycle/object unit under evidence-spec §7. A direction-node
recommendation to stop a package is not a whole-direction Portfolio mutation. A second recast
continues at the lowest ACTIVE sequencing priority under §11.7; do not silently PARK it. Working-set
scheduling changes no scientific meaning, lifecycle or allocation. Preserve per-result and
all-attempts-per-valid-result costs with node/device and honest unknowns in current Portfolio records.
