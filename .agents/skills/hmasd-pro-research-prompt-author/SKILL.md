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

Apply evidence-spec §11.8 while authoring, not only as a citation. Include the current
evidence spec and applicable authority among the caller-selected pinned references.
Start from the decision the next observation should inform. Do not silently replace a
performance question with proof of an exact maximum, full support or complete cause.
When proposing such a diagnostic, compare its decision value and known work with a
direct bounded B or finite measurement. Finite, deterministic and zero-learner do not
mean cheap. A packet that selects future work must discuss that work's cost even though
the consultation itself runs no experiment; unknown cost is not zero or evidence of
cheapness. Use existing facts, not a mandatory new cost-measurement experiment.

Expose inherited restrictions that exclude a simpler experiment and their actual
owner/specification basis. Permit Pro to question author assumptions; do not constrain
an overbudget return to exact implementation, higher budget or PARK alone. Asking for
an exact claim does not establish that the claim is worth pursuing. Ordinary B need
not resolve the full policy-class maximum or mechanism before learning. Preserve real
correctness dependencies and historical results. Renaming a forbidden B prerequisite
as an A object does not remove the prerequisite. This reasoning belongs in the existing
question and intake, not a separate checklist, proof or launch gate.

On receipt, Root/DM tests the selected question's necessity as well as implementation
fidelity. If Pro adds a conflicting prerequisite, cite the exact source and conflict
and reopen that node for correction; archive the answer unchanged. A requested explicit
specification exception follows existing scope/authority, never implicit precedence.
Already accepted packets are not regenerated or resent to adopt new wording.

Replacing exhaustive search with beam search, best-of-many or another bounded policy
search does not repair an unnecessary search-before-learning dependency. Ordinary MARL
performance exploration defaults to real training and sampled return comparison, not
an oracle/headroom search. Search needs its own scientific purpose (for example, an
explicit planning algorithm or separately chosen diagnostic); a smaller search budget
alone supplies no such purpose. Normal action selection and training optimization are
not a pre-learning search over policies or future trajectories.

Before selecting prospective work, describe its dominant multiplicative factors in the
existing question: arms, seeds, environment steps, evaluation points/episodes, and nested
candidate/trajectory/solver calls. Separate algorithm-required work from added validation.
Joint-action, horizon, subset and cross-product explosions require reconsidering the
question; native code and parallelism do not justify them. Prefer an adequate sampled
comparison or fewer unnecessary dimensions, preserving the stated comparison. No universal
overhead ratio, complexity proof, cost experiment or new validator is required. Unknown
counts/costs stay explicit, not zero; do not claim measured inflation without a baseline.


## Recovery and fallback

Follow the partial-success table in the collaboration workflow. Reuse existing
matching file/comment, preserve conflicts, read actual state before uncertain retries.
Repeated receipt means read the existing intake, not repeat science or writes.
Only an explicit `delivery_mode=archive_attachment` with a nonempty `fallback_reason`
may render a new attachment packet when scoped delivery is unavailable. Read
[attachment-legacy.md](references/attachment-legacy.md) only for that route or an
already accepted legacy request. Fallback is per request and recorded, not migration
reversal. Do not re-render accepted requests. Do not demand workflow Pro review.
