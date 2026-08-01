---
name: hmasd-independent-research-pro-review
description: Use from the persistent Independent Research Explorer for one exact direction or methodology Pro review, with direct Agentify transport and local FIFO intake.
---

# HMASD Independent Research Pro Review

## Boundary

This Skill is invoked only by the persistent `INDEPENDENT_RESEARCH_EXPLORER`.
The Explorer owns both independent-research direction reviews and methodology
audits; there is no separate persistent review-operator session. Use only the
new Explorer-owned stable binding declared below; historical bindings are not
reassigned.

This Skill grants no workflow-design, code, runtime, compute, Git, formal
science or project-state authority. The response is advisory input to the
Explorer's local research portfolio only. The Explorer freezes the exact
question, mode, candidate or methodology assignment, source allow-list,
operation identity and item root before transport begins.
Load `$hmasd-agentify-pro-transport` only for the exact receipt-bearing
`prepare -> submit -> verify -> archive` mechanics used below.

## Stable transport binding

Use the registered owner and key exactly as follows:

```text
transport_owner=independent_research_explorer
stable_key=hmasd-independent-research-explorer-pro
execution=persistent_explorer_session_direct
assignment_prefixes=IR_DIRECTION_REVIEW:|IR_METHODOLOGY_REVIEW:
provision_command=provision-direction
item_root=local_research/pro_reviews/<review-id>/
```

At most one nonterminal operation may be active on this key. Do not create or
consult a shared page registry, methodology operator, review child, monitor,
heartbeat or batch transport state. Runtime conversation identity, URL, model
and credentials come only from the live Agentify binding.

## Exact transport sequence

1. Freeze one exact prompt. Its assignment identity begins with exactly
   `IR_DIRECTION_REVIEW:` or `IR_METHODOLOGY_REVIEW:` and declares either
   `PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW`,
   `PRO_ADVERSARIAL_SCIENTIFIC_REVIEW`, or the bounded methodology-audit mode.
2. Run the registered `provision-direction` command for either exact prefix;
   it copies the frozen prompt into that assignment's exact item root. Then run
   Agentify `prepare` once with the Explorer owner, stable key, live
   conversation binding, operation identity and prompt path.
3. Run `submit` once. If the operation is already durable, use
   `submit --verify-existing`, which never sends. A fresh unchanged-question
   operation is allowed only after that check reports `present=false`.
   `--allow-tab-creation` is permitted only for first binding or a tab missing
   after an Agentify restart.
4. Run `verify` and require the transport wrapper's natural-completion receipt.
   Never interrupt generation or activate `Answer now`, `Stop`, `Retry` or
   `Continue`.
5. Run `archive` to the same Explorer-owned item root, then enqueue the exact
   archived response in the Explorer's local FIFO before scientific
   reconciliation. Transport completion never chooses the next candidate.

An incomplete request, missing or conflicting binding, or transport ambiguity
blocks only that operation. Recover the same durable operation first; do not
duplicate a send, switch conversations or reinterpret a blocker as science.
No hash, digest, fingerprint or byte count is a workflow predicate.

## Item records and packet semantics

Each item keeps the frozen prompt, transport selection/request/receipt, exact
raw response, mechanical intake and the typed advisory packet required by its
mode. Keep runtime credentials and Agentify state outside the repository.

For a direction review, archive the complete response before producing the
`INDEPENDENT_RESEARCH_DIRECTION_PACKET`. A constructive review must complete
before the Explorer applies, rejects or parks its corrections in a new
advisory version; only that version may receive a separate adversarial review.
For a methodology audit, return the exact format-complete methodology packet
to the Explorer's local FIFO without adding sources, claims or project
instructions. Neither mode promotes a direction into formal project state.

The Explorer alone selects the next review and continues the authorized
campaign. Workflow Design Manager is neither a campaign approver nor a
transport provisioner or recovery owner. Research children remain available for
source, innovation, principles and critique work; no child performs Pro
transport or monitoring.
