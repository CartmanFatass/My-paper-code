# Scoped GitHub delivery

This reference contains the publication sequence and partial-success cases. Shared method and actual request authority apply; no additional workflow manual is required.

Use ordinary Author inputs plus delivery_mode=github_delivery and github_delivery:
branch (the shared direction branch), base_sha (full SHA), response_path (this
node's pro_packets/<round>/archive/RESPONSE.md), issue_url (same repo Issue).
Pin input commit_or_ref to a full SHA. Include applicable current specifications in
reference_files. The scientific author reuses the direction branch, creating it on demand only
if absent. An extra branch needs a concrete special isolation reason in the handoff. Pro writes
only the specified response file and a delivery-link comment. Retain discussion
snapshots as pinned references. Do not use a moving branch as task input.
The base SHA records the delivery baseline, not an immutable expected branch HEAD. Pro adds
only its response on the current descendant HEAD, preserving other paths. Local authors fetch
and reconcile that delivery before their next push; no force-push or new branch per round.

The top-level full commit_or_ref is the default scientific input version. Each
reference may declare a distinct full commit_sha; omission inherits the default.
The manifest prints each effective path/SHA mapping in the one named repository.
Preserve all science card/evidence mappings; newer method sources may be separately
pinned. TASK explicitly adopts only named applicable specification sections at those
versions. Other retrieved content cannot expand scope or the listed dependencies.

1. Run render_packet.py REQUEST.json --out-dir <new packet folder>. It creates
   TASK.md and HANDOFF.json with TASK_NOT_PUBLISHED and dispatch_required=false.
2. Commit TASK.md with explicit paths and push immediately. Resolve its full SHA.
3. Run render_packet.py --bind-task-sha <full SHA> --handoff-path <HANDOFF.json>.
   This compares committed TASK bytes before forming its fixed link. The caller
   confirms the commit is actually pushed, and branch/Issue exist, before dispatch.
   No generated file can include the hash of its own not-yet-created commit.
4. Commit/push updated internal handoff. Dispatch its exact dispatch_prompt once
   through the runtime-specific author-owned Transport route (Codex followup_task; Claude caller-direct metadata and native Sonnet dispatch).
   Native authors (DM, or owner-triggered Portfolio request) are their own receipt parent and dispatch to their reusable Agentify
   Transport child; its native receipt returns directly to that parent. Intake belongs to the designated author DM; Portfolio dispatch requires an owner-triggered review.
   New mode uses existing paste request support; do not upload TASK or prepend
   attachment-only/read-only instructions. No request/routing fields enter prose.
   OWNER_DIRECT 2026-09-06: the short prompt and TASK delivery section share the same
   final readback instruction. Before replying, Pro makes fresh GitHub reads of the
   delivery branch HEAD, the response at that commit and this round's Issue comment.
   The input-evidence SHA stays fixed; delivery is checked at the delivery commit.
   The final receipt follows those reads: confirmed delivery links, confirmed partial
   delivery with its remaining gap, or a downloadable complete `RESPONSE.md` when the
   GitHub connector cannot expose or complete the scoped write actions. In that fallback,
   label GitHub delivery unconfirmed and attach the full answer rather than a summary.
   Missing write receipts or failed reads do not establish that no write occurred;
   inspect actual state before retrying, retaining all confirmed results.
5. On delivery, read full response by exact commit. For the Markdown output fallback,
   Transport downloads the provider-generated `.md`, binds it to the accepted request and
   paired assistant node, records byte count and SHA-256, preserves the complete Transport
   artifact as `<archive_id>__02_RESPONSE.md`, and retains the same bytes as repository
   sidecar `archive/CHAT_FALLBACK_RESPONSE.md`. The scoped GitHub `archive/RESPONSE.md`
   remains reserved for actual connector delivery. If both exist, preserve both and compare
   hashes; different bytes are `ARCHIVE_CONFLICT` and neither is overwritten. Check target and changed scope,
   retain raw bytes and comment snapshot in the existing archive, then perform the
   existing scientific intake. The short chat receipt belongs separately as
   `<archive_id>__04_CHAT_RECEIPT.md`; it never occupies the response artifact. No hand copying.

Partial success is retained. Existing matching file/comment is reused; conflicting
content is never overwritten. Uncertain writes are read back before retries.
Repeated notifications reuse existing request/commit/path intake and do not run
science again. Comments do not automatically wake Codex/Pro; existing Transport
performs observation throughout its native assignment. No webhook or scheduler is added.

All new requests default to github_delivery. Their rendered TASK and transport prompt include
the downloadable Markdown output fallback above. `archive_attachment` is a read-only
capability fallback requiring explicit delivery_mode and nonempty fallback_reason;
unsent requests may explicitly fall back to it; accepted requests require actual-state reconciliation
before any new prompt. Do not regenerate a previous request to change its mode.
The output fallback is part of one accepted GitHub-delivery prompt and never authorizes a
duplicate Send.

## Partial success and uncertainty

| Observed state | Action |
| --- | --- |
| Send accepted or acceptance uncertain | Observe the existing request; reconcile exact message identity before any continuation. A timeout does not authorize another Send. |
| File write timed out or write receipt is missing | Read the target branch and commit. Reuse confirmed output; report unresolved state when reads fail. Missing receipts do not prove no write occurred. |
| Matching response/comment already exists | Read and reuse it without rewriting the response or repeating its scientific decision. |
| Existing content conflicts or ownership is unclear | Preserve all content and report the exact conflict; do not overwrite or force-push. |
| Response exists, comment is missing | Verify the Issue. Only confirmed absence permits completing the same authorized comment; retain the response. |
| Comment exists, chat receipt or notification is missing | Recover the immutable delivery links and notify once; do not create another response or comment. |
| Shared direction branch advances | Add only the scoped response on current descendant HEAD, retaining fixed evidence and unrelated files. Reconcile the remote commit before local pushes; report non-descendant history or target conflicts. |
| Accepted legacy TASK forbids branch-base changes | Preserve its exact Send and reply. New workflow wording does not amend the accepted TASK. Root arranges a bounded delivery correction after reconciling actual file/comment state; only explicitly authorized delivery correction may use a distinct request/output; preserve scientific evidence. |
| Cleanup removed or renamed a delivery target | Reconcile the affected request and recovery ref before further writes. Correct unsent handoffs and publish/bind their new TASK; preserve accepted/uncertain handoffs and Root resolves restoration or explicit correction. Branch cleanup alone never authorizes a replacement conversation or another Send. |
| Main advances after input was bound | Keep each original effective input path/SHA mapping. The author assesses scope/specification conformance at intake; unrelated commits do not invalidate the response. |
| Provider access is unavailable | Record the precise unreadable paths or unavailable action and any confirmed partial delivery. A local tool's access does not establish Pro access. |
| GitHub write actions are unavailable after actual-state readback | Complete the review in the same accepted turn and attach the full answer as downloadable `RESPONSE.md`. Transport downloads and hash-archives it; do not send a second scientific prompt merely to change delivery mode. |
| A conclusion needs correction | Ask the same node a new explicit question with a new output path and links to the prior response; preserve the original answer. |
