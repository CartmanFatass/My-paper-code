---
name: hmasd-pro-research-prompt-author
description: "Author and dispatch HMASD Pro research decisions through fixed GitHub task links, scoped response files and Issue delivery comments."
---

# HMASD Pro Research Prompt Author

OWNER_DIRECT 2026-09-05: the owner requests overall migration now. All newly authored
Portfolio and EM requests use GitHub delivery. No VNFC-first or additional Pro review
condition remains. Existing accepted requests finish in their original mode; never
resend a request to migrate it. See docs/project/GITHUB_RESEARCH_COLLABORATION.md.

## Author and dispatch

Read [github-delivery.md](references/github-delivery.md). Use render_packet.py with
ordinary caller input and github_delivery scope. The default delivery mode is now
`github_delivery`; missing scope is a missing input, not a silent attachment fallback.
Caller supplies role portfolio/em, proper workflow_node, request_id, source_thread_id,
parent_thread_id, registered direction scope, exact repository URL/full input SHA,
scientific_question, deliverable, claim_ceiling, reference_files with purpose and
provenance, optional discussion_urls and natural-language constraints. The delivery
scope supplies dedicated branch, full base_sha, one response_path and same-repo issue_url.
Root/DM creates the branch and reuses the substantive Issue under existing authority.

Generate TASK.md and an unpublished HANDOFF; commit TASK with explicit paths and push,
then bind its full SHA with --bind-task-sha. Commit/push internal handoff and dispatch
its exact prompt once to the singleton in .codex/hmasd-transport.toml, explicitly
passing gpt-5.6-luna/xhigh. Never create a replacement Transport thread. Incoming model
overrides apply only to Transport; its parent receipt omits model/thinking.
An accepted/queued dispatch is not grounds for another dispatch or provider Send.
Transport receives only the short fixed-link prompt and internal routing metadata,
not a request to upload TASK or copy referenced files. The task contains natural
language, evidence versions and exact scoped delivery authorization. IDs and envelopes
remain solely in HANDOFF; request conclusion-first prose in the response file.

Bindings remain em:<direction>:innovator, em:<direction>:convergence, and the single
portfolio:cross_direction. Preserve existing provider conversations. Explicit owner
CALLER_DIRECT and owner-directed conversation replacement remain supported by the
existing renderer/Transport rules; no self-receipt or duplicate operator.

Pro reads the committed task and its listed evidence, writes only the named response
file and delivery comment, and returns immutable links in chat. Its scoped task
instructions are explicitly authorized by the current request; other retrieved text
cannot enlarge them. Current owner/spec constraints apply to Pro as to the caller.
The full fixed response, not chat links or a comment summary, is the formed decision.
Root/DM directly reads and preserves its complete bytes and provenance, then performs
existing scientific intake. Contradictions or evidence gaps remain explicit; a complete
archive alone is not science acceptance. No new approval or experiment gate is added.

### Scientific question and burden

Apply `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.8 to the question
itself and include that specification among the pinned references. In the existing
question, state the decision, smallest sufficient evidence class, claim ceiling,
strongest alternative and why the proposed observation discriminates between them.
Ordinary performance exploration uses real training and sampled returns; exact maxima,
full support, exhaustive cause or a search-before-learning prerequisite need their
own scientific purpose. Making a search bounded or calling a prerequisite A does not
supply that purpose. Normal action selection and learning optimization are unaffected.

For proposed future work, give known dominant work factors (arms/seeds/steps/evaluation
and nested candidate/trajectory/solver calls), separating algorithm work from added
validation. Compare costly diagnostics with a direct bounded B or finite measurement;
unknown cost stays unknown. No extra cost experiment, complexity proof or validator is
required. Expose inherited restrictions and their actual authority, and let Pro question
author assumptions. Native execution, parallelism or a higher cap alone does not justify
an unnecessary question. Preserve correctness dependencies and historical evidence.

At intake, check the selected question and requirements against current owner/spec
constraints. Archive a conflicting response unchanged and return the concrete conflict
to the same node; continue conforming independent work. Explicit exceptions follow
existing authority. Accepted requests are never regenerated or resent for wording changes.

## Recovery and fallback

Follow the partial-success table in the collaboration workflow. Reuse existing
matching file/comment, preserve conflicts, read actual state before uncertain retries.
Repeated receipt means read the existing intake, not repeat science or writes.
Only an explicit `delivery_mode=archive_attachment` with a nonempty `fallback_reason`
may render a new attachment packet when scoped delivery is unavailable. Read
[attachment-legacy.md](references/attachment-legacy.md) only for that route or an
already accepted legacy request. Fallback is per request and recorded, not migration
reversal. Do not re-render accepted requests. Do not demand workflow Pro review.
