# Attachment delivery

For attachment-mode Author handoffs,
`PROMPT_BODY.md` is the sole scientific
attachment: its `GITHUB_EVIDENCE_MANIFEST` already contains the read-only reference
metadata. Such a handoff must not declare, upload, or synthesize `reference_paths`.
`scripts/validate_request.py` recognizes `source_mode=single_body_attachment`,
requires the sole `PROMPT_BODY.md` upload, and rejects any reference attachment
declaration in that mode.
Use the body bytes verbatim.

Reject every canonical request that lacks a valid `source_thread_id` or
`parent_thread_id`. Reconcile receipt attempts and delivery state before sending;
never guess a destination or duplicate a delivered receipt.

## Attachment materialization

The preferred input is a canonical packet produced by
`scripts/materialize_packet.py`. The packet is one logical object identified by
`packet_id` and a `PACKET_MANIFEST.json`; the body and references may be separate
physical files only because the page upload interface requires it. The manifest is
the authority for order, source path, byte count, and hash. Companion text is
transport UI text and is never a second scientific packet. Materialize and record
the canonical manifest before page actions.
