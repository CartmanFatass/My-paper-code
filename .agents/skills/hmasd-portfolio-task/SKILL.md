---
name: hmasd-portfolio-task
description: Use when the DM designated by Root prepares Portfolio Pro decision materials, checks the complete Portfolio response, or maps its conforming decision to execution.
---

# HMASD Portfolio materials and Pro intake

Portfolio is the existing `portfolio:cross_direction` Pro node. Root is the execution coordinator;
it chooses a relevant recently active DM as author and response checker. The DM supplies science
and recommendations but does not replace Pro's final decision. ROOT_OPERATIONS.md maintains this
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

A relevant DM authors one cross-direction packet; other DMs may supply their direction facts.
Root can request missing facts but does not rewrite scientific content. If the author becomes
unavailable, Root explicitly transfers the remaining scope and evidence to another relevant DM.

## Publish and route

Use `hmasd-pro-research-prompt-author` with `workflow_node=portfolio_decision` and
`caller_role=portfolio`. These choose the node, not the author's native role. Bind every in-scope
direction in `direction_ids`. Include the current Portfolio snapshot, applicable principle/spec
sections and only needed experience/card/evidence references at their exact published revisions.
Include the machine-generated exposure line (zero new exposure when appropriate) and any required
per-arm projection; no consultation-only exposure experiment is needed.

Reuse `portfolio:cross_direction` and the existing Transport endpoint. The new request's source is
the actual DM author, parent is the existing Root task, operator is Transport. Root dispatches the
committed exact handoff, Transport returns its factual receipt only to Root, and Root forwards the
complete response to the designated DM using `followup_task`. Preserve in-flight identities and
accepted bytes; an author transfer or missing receipt does not authorize another Send.

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
an execution mapping to Root. Pro is final under AGENTS §4.8; Root applies and integrates without
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
