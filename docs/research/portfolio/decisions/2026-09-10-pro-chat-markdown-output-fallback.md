# Pro GitHub failure: downloadable Markdown output fallback

**OWNER_DIRECT, 2026-09-10.** Every newly rendered Pro GitHub-delivery request now carries
one in-turn failure path. When the GitHub connector cannot expose or complete the authorized
response-file, commit or Issue-comment actions after reading actual repository state, Pro still
completes the scientific review and attaches its entire answer as a downloadable Markdown
document. A missing write action is a delivery limitation, not permission to return only a gap.

Transport downloads the document only after natural completion and binds it to the accepted
request and paired assistant node. It records the provider filename, byte count and SHA-256,
stores the complete Transport attempt response as `<archive_id>__02_RESPONSE.md`, and retains
the same bytes in the repository as `archive/CHAT_FALLBACK_RESPONSE.md`. A distinct short chat
receipt uses `<archive_id>__04_CHAT_RECEIPT.md`. The scoped GitHub
`archive/RESPONSE.md` remains reserved for actual connector delivery. If both response artifacts
exist, preserve both and compare hashes; different bytes are `ARCHIVE_CONFLICT` and neither is
overwritten.

This output fallback is part of the original accepted prompt. It does not authorize another
Send, change the scientific question, relax evidence/specification checks, claim a GitHub
commit/comment, or replace designated-DM conformance intake. It is distinct from the existing
`archive_attachment` input mode used to supply an unsent question.

The rule is implemented in the prompt renderer and synchronized across `AGENTS.md`, the GitHub
collaboration and Root routing documents, Prompt Author instructions/references, Transport
instructions/state schema, and focused renderer tests. The independent high-risk review found
one archive-path ambiguity; the final mapping above resolves it. The focused suite passes all
80 tests. No scientific invocation, model, environment, optimization, evaluation or additional
Pro Send was introduced by this control-plane change.

## Current request application

The owner independently asked the existing Pro conversation to provide Markdown for
`2026-09-10-four-slot-rolling-refill-01`. Pro generated
`FOUR_SLOT_ROLLING_REFILL_RESPONSE.md`; Root captured a confirmed browser download at
`C:/Users/fires/Downloads/FOUR_SLOT_ROLLING_REFILL_RESPONSE.md`. The file is 47,134 bytes,
SHA-256 `bb7763097d3aceabdbe85d6f06193e3cc79b4be2cc9140c64c616340d30d388f`.

During that turn, actual GitHub delivery also completed at commit
`1ea43d8fbc846807d71d4d894136f357f65551b6` with Issue17 comment `5629259208`.
Root fetched the exact Git object and verified the downloaded file is byte-for-byte identical
to the committed `archive/RESPONSE.md`. The downloaded bytes are retained separately as
[`CHAT_FALLBACK_RESPONSE.md`](../pro_packets/20260910_four_slot_rolling_refill/archive/CHAT_FALLBACK_RESPONSE.md),
with [download facts](../pro_packets/20260910_four_slot_rolling_refill/archive/CHAT_FALLBACK_DOWNLOAD_FACTS.json).
Scientific conformance and application remain with the designated Portfolio DM.
