# Explorer Pro review transport

This note is the Explorer-local contract for independent-research direction
reviews and bounded methodology audits. It is not a shared registry, a review
queue owner, or a project-state record.

```text
session_owner_role=independent_research_explorer
session_owner_id=019fbded-24cb-7541-aa16-0111b626b945
stable_key=hmasd-independent-research-explorer-pro
transport_owner=independent_research_explorer
execution=persistent_explorer_session_direct
assignment_prefixes=IR_DIRECTION_REVIEW:|IR_METHODOLOGY_REVIEW:
provision_command=provision-direction
item_root=local_research/pro_reviews/<review-id>/
```

Historical review-operator bindings are not reassigned. Explorer research
children remain available for source, innovation, principles and critique work,
but no child, monitor, heartbeat or page registry performs Pro transport.

## One review

For one frozen assignment whose identity begins exactly with
`IR_DIRECTION_REVIEW:` or `IR_METHODOLOGY_REVIEW:`, Explorer invokes the
registered `provision-direction` command and then the Agentify transport Skill
in this order:

```text
provision-direction -> prepare -> submit -> verify -> archive -> local FIFO intake
```

The prompt, assignment identity, operation identity, live conversation binding
and item root are frozen before `prepare`. `submit` is one send. A recovery
uses `submit --verify-existing` on the same operation and never sends; a fresh
unchanged-question operation is permitted only after `present=false`. The
first binding or a tab missing after an Agentify restart may use
`--allow-tab-creation`. Generation is never interrupted and no `Answer now`,
`Stop`, `Retry` or `Continue` action is used.

After natural completion, Explorer archives the exact response in the assigned
item root, performs mechanical intake, and places it in the local FIFO before
scientific reconciliation. Direction reviews return an
`INDEPENDENT_RESEARCH_DIRECTION_PACKET`; methodology audits return the exact
format-complete methodology packet. Constructive review corrections are
applied, rejected or parked in a new advisory version before any separate
adversarial turn.

An incomplete or ambiguous operation blocks only that item. Explorer resumes
the same durable operation or records the transport blocker and continues
unrelated authorized research. No hash, digest, fingerprint or byte count is
used as a workflow predicate, and no result promotes a direction into formal
project state.
