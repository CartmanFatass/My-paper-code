---
name: hmasd-pro-research-prompt-author
description: "Use when DM authors an independent scientific review request, a DM conducts direct Portfolio scientific dialogue, or the request-owning DM publishes a scoped Portfolio consultation for fixed GitHub task delivery through the registered independent browser Transport task, with explicit author, parent and executor routing."
---

# HMASD Pro Research Prompt Author

DM-owned Portfolio scientific exchanges and the request-owning DM-owned capacity requests may use the direct Codex in-app browser route
in PEER_DM_COORDINATION.md and hmasd-portfolio-task. The GitHub delivery requirements below
apply to requests using this delivery workflow, not as gates on that direct vacancy route.


Root is the user entry; the independent the request-owning DM performs only delegated mechanical coordination.
Read docs/project/PEER_DM_COORDINATION.md for event handling and writes. DM/Pro retain scientific
judgment. the request-owning DM routes missing science or complex engineering repair to the relevant Astra DM;
it never turns a helper failure into a scientific stop or adds a Root ACK gate.

Requests choosing this delivery workflow use GitHub delivery; direct Portfolio dialogue may use the supported browser route. Preserve accepted request content
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
the request-owning DM can load the authored bytes independently of main's same-path copy. A prepared unsent
task with changed delivery scope is republished and rebound before dispatch; accepted tasks
retain their exact content and follow the workflow's explicit delivery-correction route.

Follow the current assignment's operation and return route. A preparation-only task
returns its ready handoff; it does not dispatch Transport. A command may already include
transport of the completed DM-authored request, so no extra planning vote is needed.
For a command that includes dispatch, use the following sequence.

The dispatch owner (DM for direction nodes; the relevant DM for Portfolio science; the request-owning DM for mechanical capacity requests under hmasd-portfolio-task)
uses the registered independent Luna/high browser Transport task in the live control checkout.
Use execution_mode=REUSE_SINGLETON and actual author App source_thread_id=parent_thread_id;
operator_thread_id is the registered Transport task. The current renderer retains this supported
independent-session mode. Read C:/Projects/HMASD control configuration even when authoring in an
older direction checkout. Commit/push TASK, bind its full SHA with --bind-task-sha, then
commit/push the exact HANDOFF; send the bound
HANDOFF commit, request identity and current return route with send_message_to_thread.
Transport uses Codex iab and sends the complete archive directly to its author. No native child,
Agentify operation or Root forwarding. Preserve accepted legacy packets and supply a separate
migration execution route after old executor release; do not regenerate already accepted inputs.
For explicitly owner-requested Portfolio consultations the request-owning DM owns the dispatch/full-plan record; only one writer may
own portfolio:cross_direction at a time. Accepted historical packets remain immutable; reconcile
old execution before any takeover, without resending. Uncertain dispatch requires same-request
reconciliation. Authoring-only assignments stop at their published handoff.
Bindings remain em:<direction>:innovator, em:<direction>:convergence and portfolio:cross_direction.

Pro reads the committed task and its listed evidence, writes only the named response
file and delivery comment, and returns immutable links in chat. Every newly rendered GitHub
task also instructs Pro that, when the connector cannot expose or complete those scoped writes
after actual-state readback, it must finish the same review and attach the entire answer as a
downloadable `RESPONSE.md`. Transport downloads and hash-archives that exact artifact as `<archive_id>__02_RESPONSE.md` and repository sidecar `archive/CHAT_FALLBACK_RESPONSE.md`; the
fallback does not claim GitHub delivery or authorize another Send. Its scoped task
instructions are explicitly authorized by the current request; other retrieved text
cannot enlarge them. Current owner/spec constraints apply to Pro as to the caller.
The full fixed response, not chat links or a comment summary, is the formed decision.
The parent directly reads and preserves the complete bytes/provenance. DM intakes direction-node
answers; the request-owning DM records the full Portfolio plan and affected DMs check their scientific requirements. Transport
returns one factual receipt directly to that parent through App task messages.
No scheduled automation is added. Read docs/project/ROOT_OPERATIONS.md for current routing. Contradictions or evidence gaps remain explicit; a complete
archive alone is not science acceptance. No new approval or experiment gate is added.

### Scientific review and Portfolio finality

Direction Pro independently reviews evidence; DM responds and owns ordinary research execution.
Portfolio is the global scientific synthesizer and final direction-level interpreter under
docs/project/PORTFOLIO_DECISION_PROTOCOL.md. Include that protocol's web-context instruction in
every new Portfolio TASK/prompt, with fixed source manifest and actual accessible repository
contents. Cover global context, affected direction report/review/contrary evidence, applicable
spec and focused foundations. A local file citation is not provider access. Lifecycle questions
are authorized direction reports, not per-experiment permission requests. Archive complete
answers and apply conforming decisions; preserve accepted historical requests without resending.

### Fixed scientific and method sources

For new scientific requests, use scientific-tools scientific-reading mode locally.
For Portfolio, include the relevant principles in empirical-spec §§7–8 and calibration in
§§11.7–11.10, plus the specific experience/intake sources that affect the choice.
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

At intake, DM reads the complete review and responds to its material scientific findings.
Correct concrete defects, bound claims and record the DM decision; do not turn review into funding
or lifecycle approval. A genuinely unresolved scientific issue can receive focused reviewer
follow-up, not automatic repeated consultation. Respect current owner/spec constraints. Accepted requests are never regenerated or resent for wording changes.

## Recovery and fallback

Follow the partial-success table in the collaboration workflow. Reuse existing
matching file/comment, preserve conflicts, read actual state before uncertain retries.
Repeated receipt means read the existing intake, not repeat science or writes. A downloadable
Markdown output produced by the accepted GitHub-delivery turn is archived under that request;
it is distinct from the `archive_attachment` input mode and requires no new prompt.
Only an explicit `delivery_mode=archive_attachment` with a nonempty `fallback_reason`
may render a new attachment packet when scoped delivery is unavailable. Read
[attachment-delivery.md](references/attachment-delivery.md) only for attachment delivery.
Record the fallback per request. Do not re-render accepted requests.
