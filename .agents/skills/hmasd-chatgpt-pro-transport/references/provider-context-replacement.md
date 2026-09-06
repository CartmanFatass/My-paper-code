# Provider context replacement

Normal operation reuses the same bound conversation serially. A provider-context
replacement requires the handoff to explicitly set
`reset_invalid_provider_context=true` with complete
`provider_context_reset_evidence`. There are two supported reasons:

- **Owner-directed new conversation:** `reset_authority=OWNER_DIRECT`, the exact
  `owner_instruction`, and `previous_request_id`. This covers an explicit request
  to use a new conversation for a new model. Preserve the entire prior record and
  all accepted-send facts, even if its generation is unfinished. Do not claim that
  its answer was contaminated, blocked, or scientifically negative. Stop the old
  operator's future actions and retire its superseded wake before taking over; an
  accepted provider generation need not be stopped. Use a distinct request ID.
- **Automated contaminated-context recovery:** the immediately previous round is `ARCHIVED`,
its final outcome is `DECISION_NOT_FORMED` or `BLOCKED`, it read exactly zero
repository paths, and acknowledged provider-context contamination is traced to a
named prompt defect. Before reset admission, archive those actual facts in
`archive.provider_context_reset_facts`; compare every caller field to that persisted
record and refuse missing or mismatched facts without mutation. A pending request
or an ordinary bad answer does not qualify for this automated route.

For either reason, the caller must not invent a replacement provider ID. Before page
actions, call `scripts/bind_conversation.py:prepare_context_reset` to retire the
old provider ID and leave the binding with no active provider conversation. The old
ID is permanently unavailable to every binding. Then create no provider conversation
by inference: only after a successful send produces a newly observed webpage
`/c/<uuid>` URL may Transport call `bind` with
`observed_after_successful_send=true` to bind that replacement. A reset flag and its
evidence are routing metadata; never put them in the body, reference manifest, or
provider-visible companion text. That replacement is persisted directly as
`SEND_CONFIRMED` with one send click and durable send evidence; it may proceed only
to generation waiting, never to another Send action. Repeating preparation with the
same request and evidence is idempotent. The legacy `quarantined_conversations`
storage name includes owner-retired conversations; it does not label their science.
