---
name: hmasd-pro-research-prompt-author
description: "Use when a DM or Root authors an HMASD Pro research question for fixed GitHub task delivery through the independent Transport task, with explicit author, parent and executor routing."
---

# HMASD Pro Research Prompt Author

Portfolio and EM requests use GitHub delivery. Preserve accepted request content
and reconcile existing Send state before continuation.
See docs/project/GITHUB_RESEARCH_COLLABORATION.md.

## Author and dispatch

Read [github-delivery.md](references/github-delivery.md). Use render_packet.py with
ordinary caller input and github_delivery scope. The default delivery mode is now
`github_delivery`; missing scope is a missing input, not a silent attachment fallback.
Caller supplies role portfolio/em, proper workflow_node, request_id, source_thread_id,
parent_thread_id, registered direction scope, exact repository URL/full input SHA,
scientific_question, deliverable, claim_ceiling, reference_files with purpose and
provenance, optional discussion_urls and natural-language constraints. The delivery
scope supplies the corresponding direction's existing branch, full base_sha, one response_path
and same-repo issue_url. Reuse that branch and substantive Issue; if the direction has no
branch, actual Pro authoring work is a reason to establish its one shared direction branch.
Do not create an extra branch per Pro round. Only a concrete special isolation need uses a
temporary branch, with its reason and retirement event in the existing handoff. Portfolio-wide
requests reuse the designated non-main control-plane checkout; main writes remain outside
Pro's scope. Never rebind an accepted request to another branch as cleanup.
Read the current delivery HEAD and preserve unrelated changes when adding the response;
normal advances do not replace fixed input evidence. Synchronize local writers before their
next push. Completing one Pro round does not retire a shared direction branch still in use.
After branch cleanup, resolve the branch/checkout from the current command and actual remote
ref before rendering. A historical HANDOFF is evidence of its own round, not a default branch
registration. Return the new request ID, full HANDOFF commit and fixed TASK URL together so
Root can load the authored bytes independently of main's same-path copy. A prepared unsent
task with changed delivery scope is republished and rebound before dispatch; accepted tasks
retain their exact content and follow the workflow's explicit delivery-correction route.

Follow the current assignment's operation and return route. A preparation-only task
returns its ready handoff; it does not dispatch Transport. A command may already include
transport of the completed DM-authored request, so no extra planning vote is needed.
For a command that includes dispatch, use the following sequence.

Generate TASK.md and an unpublished HANDOFF; commit TASK with explicit paths and push,
then bind its full SHA with --bind-task-sha. Commit/push internal handoff and dispatch
its exact prompt once to the independent Transport in .codex/hmasd-transport.toml.
The endpoint is configured Luna/high; app dispatches and receipts omit model/thinking.
Reuse it; do not create a Transport per request. Native DM/CM authors normally give Root
the exact request ID, HANDOFF commit/path, fixed TASK URL and named native return target;
Root sends the app message. Set source to the actual author UUID, parent to Root's app UUID,
and operator to Transport's UUID. An explicitly authorized native direct dispatch uses that
same parent; source is never a receipt fallback. Root authors Portfolio requests and is their receipt parent. If the author is already the configured Transport endpoint, local CALLER_DIRECT
avoids self-dispatch; merely being Root no longer selects that exception.
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
The DM or Root directly reads and preserves the complete bytes and
provenance, then performs existing scientific intake. Transport returns one factual receipt to
the declared parent; Root forwards native-direction receipts to the original DM with native
collaboration. Transport observes Pro requests; Root continues direction and experiment work.
No scheduled automation is added. Read docs/project/ROOT_OPERATIONS.md for current routing. Contradictions or evidence gaps remain explicit; a complete
archive alone is not science acceptance. No new approval or experiment gate is added.

### Fixed scientific and method sources

For new scientific requests, use scientific-tools scientific-reading mode locally.
List the applicable empirical specification, relevant FOUNDATIONS passages and only
needed topics/primary sources in reference_files; purpose names exact sections and
use, provenance states the source's scope. Pro reads those passages directly; no
local skill or unlisted linked dependency is needed. TASK adopts only the named
applicable specification requirements; knowledge remains explanatory evidence.
SESSION_CHOICES is listed only when its choices are current task inputs.

Each reference may supply an optional full commit_sha; omission inherits the full
commit_or_ref scientific input SHA. Empty, short or moving versions are invalid in
both output modes. Preserve every science card/evidence item's effective repository,
path and SHA; pin newer method sources separately without moving frozen science.
Before publication, verify each listed path exists at its exact Git object and its
commit is reachable from an observed published remote ref. This proves publication,
not current Pro access. Inspect the same effective mapping in TASK/PROMPT and its
embedded manifest. Preserve READY, accepted and uncertain packet bytes.

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
[attachment-delivery.md](references/attachment-delivery.md) only for attachment delivery.
Record the fallback per request. Do not re-render accepted requests.
