# Scoped GitHub delivery

Read docs/project/GITHUB_RESEARCH_COLLABORATION.md and its linked operational design.
Owner authorization applies; no Pro review or additional owner reply is needed for
this workflow. Existing science authority and evidence constraints still apply.

Use ordinary Author inputs plus delivery_mode=github_delivery and github_delivery:
branch (dedicated codex/pro-... branch), base_sha (full SHA), response_path (this
node's pro_packets/<round>/archive/RESPONSE.md), issue_url (same repo Issue).
Pin input commit_or_ref to a full SHA. Include applicable current specifications in
reference_files. Root creates the delivery branch at the stated base; Pro writes
only the specified response file and a delivery-link comment. Retain discussion
snapshots as pinned references. Do not use a moving branch as task input.

1. Run render_packet.py REQUEST.json --out-dir <new packet folder>. It creates
   TASK.md and HANDOFF.json with TASK_NOT_PUBLISHED and dispatch_required=false.
2. Commit TASK.md with explicit paths and push immediately. Resolve its full SHA.
3. Run render_packet.py --bind-task-sha <full SHA> --handoff-path <HANDOFF.json>.
   This compares committed TASK bytes before forming its fixed link. The caller
   confirms the commit is actually pushed, and branch/Issue exist, before dispatch.
   No generated file can include the hash of its own not-yet-created commit.
4. Commit/push updated internal handoff. Dispatch its exact dispatch_prompt once
   using the configured singleton model/effort. CALLER_DIRECT retains its exception.
   New mode uses existing paste request support; do not upload TASK or prepend
   attachment-only/read-only instructions. No request/routing fields enter prose.
5. On delivery, read full response by exact commit. Check target and changed scope,
   retain raw bytes and comment snapshot in the existing archive, then perform the
   existing scientific intake. Full original response belongs in RESPONSE.md;
   the short chat receipt belongs separately with transport facts. No hand copying.

Partial success is retained. Existing matching file/comment is reused; conflicting
content is never overwritten. Uncertain writes are read back before retries.
Repeated notifications reuse existing request/commit/path intake and do not run
science again. Comments do not automatically wake Codex/Pro; existing Transport
and heartbeat perform observation and wakeup. No webhook or service is added.

All new requests default to github_delivery. archive_attachment is a read-only
capability fallback requiring explicit delivery_mode and nonempty fallback_reason;
unsent requests may explicitly fall back to it; accepted requests require actual-state reconciliation
before any new prompt. Do not regenerate a previous request to change its mode.
