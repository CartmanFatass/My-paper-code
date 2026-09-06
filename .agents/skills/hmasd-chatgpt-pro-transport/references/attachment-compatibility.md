# Attachment and legacy routing compatibility

An optional `reference_paths` list contains one or more absolute reference files
for bounded noncanonical/legacy transport. Validate and hash every
reference before transport. There is no strict filename or orthogonality requirement:
the provider may normalize/display attachment names, and references may be attached
or otherwise supplied in the page-supported form. Record the provider-visible names
and preserve the byte hashes and intended order where the page permits. The
one-to-one binding-key/conversation rule still applies to the body and all
references together.

For already accepted or explicit fallback attachment-mode Author handoffs only,
`PROMPT_BODY.md` is the sole scientific
attachment: its `GITHUB_EVIDENCE_MANIFEST` already contains the read-only reference
metadata. Such a handoff must not declare, upload, or synthesize `reference_paths`.
`scripts/validate_request.py` recognizes `source_mode=single_body_attachment`,
requires the sole `PROMPT_BODY.md` upload, and rejects any reference attachment
declaration in that mode.
Use the body bytes verbatim and retain any generic legacy reference support only for
non-Author transport requests.

Reject every canonical request that lacks a valid `source_thread_id` or
`parent_thread_id`. Reject legacy
fallback routing fields even when false or null. A legacy request may omit its source
or parent and still execute transport, but without a valid parent it is ineligible for an automatic receipt; mark
its receipt substate `RETURN_RECEIPT_BLOCKED`, do not guess a destination, and do not
send any receipt.

When loading legacy outbox state, normalize only a provably unsent `PENDING` or
`BLOCKED` receipt. Check both the primary and old fallback route: any attempt count,
delivery status, sent timestamp, or terminal delivery state preserves the complete
old receipt as historical evidence and forbids a new send. A valid parent permits
only the zero-attempt migration to `PARENT_SESSION`; no parent records
`required=false` and remains ineligible for return.

## Attachment materialization

The preferred input is a canonical packet produced by
`scripts/materialize_packet.py`. The packet is one logical object identified by
`packet_id` and a `PACKET_MANIFEST.json`; the body and references may be separate
physical files only because the page upload interface requires it. The manifest is
the authority for order, source path, byte count, and hash. Companion text is
transport UI text and is never a second scientific packet. Legacy `prompt_path` /
`reference_paths` input remains accepted, but the operator must materialize and
record the canonical manifest before page actions.
