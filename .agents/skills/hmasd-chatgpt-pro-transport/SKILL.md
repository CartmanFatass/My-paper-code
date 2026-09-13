---
name: hmasd-chatgpt-pro-transport
description: "Use when an author-owned native Transport subagent executes or observes an exact Agentify Pro handoff, including model verification, ambiguous sends, recovery, archival and native parent receipts."
---

# HMASD Agentify Pro transport

Each DM creates/reuses one native Luna/high Transport child with fork_turns=none and the exact
assignment plus this skill. Use registered HMASDTransport; if unavailable in an existing runtime,
use a default native child explicitly pinned to gpt-5.6-luna/high with these instructions.
Root uses this same leaf role only for its Portfolio vacancy replacement under
hmasd-portfolio-task. In that case source and receipt parent are Root and the archive returns
directly to Root. In the normal direction route,
DM authors science, sends the handoff and waits natively. Transport executes only the assigned
Send/observation/archive operation and returns directly to DM. No singleton app task, Root receipt
forwarding or CUA default path. Root coordinates cross-direction dependencies and integrates the
DM's conforming decision. Portfolio scientific authority remains portfolio:cross_direction.

## Inputs and ownership

Read the canonical HANDOFF at its exact committed SHA, fixed TASK URL and matching existing
request state before browser actions. New handoffs use dispatch_mode=REUSE_DM_TRANSPORT,
source_thread_id=parent_thread_id=the author's actual native ID, and operator_thread_id=its distinct
Transport child ID, operator_reuse_required=true, operator_model=gpt-5.6-luna,
operator_thinking=high. IDs may be exact runtime UUIDs or canonical native paths; never invent
app-task URLs for them. Validate with scripts/validate_request.py. A preparation-only task does
not authorize Send. Pass the exact prompt; no rewriting scientific content or copying TASK inputs.

Bindings remain em:<direction>:innovator, em:<direction>:convergence and portfolio:cross_direction.
Read provider selection/exclusion policy from .codex/hmasd-transport.toml. Current provider is
GPT-6 Astra / Pro, independently of the Luna executor model. Preserve fixed scientific SHAs,
request IDs, registered conversation identity and all prior failed/accepted attempts.

Only one active writer may own an exact provider conversation. Different bindings can proceed
concurrently; Portfolio remains one shared binding owned by the current author (DM or Root vacancy request).
Resolve outstanding writer/operation state from the existing shared transport registry and current
DM assignment before acting. All worktrees use the absolute registry_path in the live
C:/Projects/HMASD/.codex/hmasd-transport.toml; never resolve a worktree-local default. Read
[state-schema.md](references/state-schema.md) for its existing records. Reuse its registry_lock for brief read-modify-write operations;
record request/operator ownership before Send, and retain it through uncertain Send or generation.
A second request on a still-owned conversation waits; never infer release from a task timeout.
Do not hold the registry file lock across browser waits or create a new global scheduler.

## Agentify execution

Use current callable Agentify tools, not historical API names. Read
[agentify.md](references/agentify.md) for exact strict arguments and observation-only recovery.
Inspect agentify_tabs/status and the assigned tab. Use a dedicated non-protected tab for the
binding; do not act on the default/protected browser root or another request's tab. A ready
logged-in Chrome CDP provider surface and visible product/effort determine readiness.

Preflight exact productModel="GPT-6 Astra" (or visibly verified "Latest") and reasoningEffort="Pro".
Never downgrade the provider model for speed. A wrong/unknown model permits non-sending repair,
not Send. Login or unavailable tool state is a concrete prerequisite, not scientific authority.

For a new, demonstrably unsent GitHub-delivery request, call agentify_review_query with a stable
binding key, immutable operation idempotency key, exact prompt bytes/hash, registered conversation
URL/ID, inspected tab and absolute responsePath. Record the exact arguments and returned receipt.
Use bounded windows (at most 60000 ms per call here) and keep observing until terminal or a
concrete external blocker. The parent DM's native long wait provides periodic context reuse;
Transport never broadcasts unchanged progress to maintain a cache.

No second Send follows from timeout, missing archive, child replacement, failed receipt or an
unknown UI effect. IN_PROGRESS continues the SAME operation. verifyExisting=true is safe as
observe-only ONLY when that Agentify operation already records sendAttempted=true. With
sendAttempted=false it may Send; use it only under the existing explicit Send assignment and
proven nonacceptance. With unknown or externally accepted Send state, use non-sending observation
and reconcile provider message identities; never create a fresh strict operation to observe it.
Preserve the whole response once formed even when transport status or delivery labels disagree.

## Archives and DM receipt

Agentify's strict archive saves exact assistant UTF-8 bytes and a verified hash/size/path receipt.
With GitHub delivery that assistant text may be only a chat receipt: store it as
<archive_id>__04_CHAT_RECEIPT.md, not the scientific answer. Retrieve the exact scoped GitHub
RESPONSE.md at its immutable commit or the paired downloadable full RESPONSE.md. Preserve the
full answer as <archive_id>__02_RESPONSE.md; downloaded fallback also goes to the repository
sidecar archive/CHAT_FALLBACK_RESPONSE.md. Never synthesize GitHub archive/RESPONSE.md, truncate,
paraphrase or overwrite differing bytes. Verify paired message identity, path, bytes and SHA-256.
Two different candidate answers are ARCHIVE_CONFLICT and both are retained for DM resolution.

Send one factual native receipt to parent_thread_id using collaboration.send_message while DM
waits, then native final when the assigned lifecycle completes. Include request/binding IDs,
operation receipt, exact Send acceptance/uncertainty, archive paths/hashes, provider message IDs,
cleanup state and any missing facts. Deduplicate by request and response identity; a native final
is the same completion, not another work dispatch. Save pending/delivered receipt state in the
existing request record. If DM is interrupted/unavailable, preserve the pending receipt for
same-parent recovery; delivery success is not science acceptance. Do not use an app-task fallback.
DM reads the full response, checks conformance and resolves scientific intake; transport cannot
select science or substitute a local answer. Close only owned non-protected tabs after confirmed
archive/receipt or verified recoverable conversation identity. No ACK loop or empty-worker polling.

## Accepted requests and recovery

Never regenerate or rebind accepted historical HANDOFFs to fit new defaults. First reconcile the
old executor, its exact request and provider message, archive and receipt. If all archived/delivered,
leave it as evidence. If work remains, the owning DM explicitly assigns observation-only takeover
with original immutable handoff and a separate current native return route; old effect uncertainty
continues to prohibit Send. Record actual executor/parent recovery facts without changing originals.
Do not run a historical singleton validator against the new endpoint config as permission to resend.
The structural legacy code paths remain for old evidence/fixtures; they are not new dispatch modes.

For explicit attachment inputs, retain the accepted original bytes and input mode. Strict Agentify
review_query promptPath means text to paste, NOT an upload; never silently turn an attachment into
paste. If no available Agentify upload path satisfies the frozen input contract, return that exact
capability gap to DM while preserving observation of accepted requests. New normal work uses
fixed GitHub task links. No provider stop, regenerate, continue-response action or new prompt is
implied by natural-completion observation. Owner pause/stop and scientific budgets stay binding.
