# Research execution responsibilities

## Current Windows control endpoints

OWNER_DIRECT2026-09-12: use Windows C:/Projects/HMASD and PowerShell. Root task is
01a095b7-850f-7401-ad4e-5e4320d285f1. Current independent endpoints are Transport
01a095ca-7b4a-7940-8acf-fca1b52c784d, Monitor01a095d0-21ee-7c02-9d97-3681b5678200,
and Relay01a095ca-8676-74e1-b78c-ea459d41e905. Their live .codex/hmasd-*.toml files
are the executable routing source. New work and successor recovery receipts use these
endpoints; historical fixed request metadata is not a live routing instruction.
Keep current tracking free of obsolete snapshots and endpoints. Consult Git for history.
No browser Send may overlap a retired executor: reconcile its stopped/acceptance receipt first.

The current Root task is the execution coordinator; DM owns direction
science and the former CM engineering responsibilities. Portfolio is the persistent Pro node,
not a native session. Authority, budgets and owner pause/stop instructions remain in AGENTS.md.
The current consolidation record is `docs/research/portfolio/decisions/2026-09-10-control-plane-consolidation.md`.

OWNER_DIRECT 2026-09-10: directions run as independent rolling chains. A direction advances from
its own evidence, decision, dependencies and resource admission without waiting for a named batch,
Portfolio bundle, sibling result/intake/cleanup or global stage boundary. Its result, blocker, Pro
wait, failed admission or closeout affects only that direction. Root integrates and replaces ready
work continuously; a prior `no successor` closes only its named allocation. Cross-direction choices
still use Portfolio authority while independent authorized work continues.

OWNER_DIRECT 2026-09-11: once Root has dispatched all currently ready independent work, it ends
the turn if only long-running DM, accepted legacy CM, Monitor or Transport dependencies remain.
The independent relay wakes Root for actionable native completion; Monitor and Transport retain
their direct Root receipt routes. Root does not keep the dispatch turn open with native/app waits,
timers or status polling. Each wake re-enters the normal ready-work pass.

## Maintained sources

| Rule | Maintained source |
| --- | --- |
| Authority, decisions, delegation, capacity, Git and resource invariants | AGENTS.md §§2–8 and the evidence specification |
| Complete owner assignments and integration | This document |
| Code-task L0–L3 detail, delegation and high-risk review | ENGINEERING_SCOPE_SPEC.md §7 |
| Ready-work ordering and waits | hmasd-loop-dispatch Skill |
| Portfolio principles and decision evidence | MARL_EMPIRICAL_EVIDENCE_SPEC.md §§11.3,11.7–11.10 |
| Portfolio material preparation, Pro intake and application handoff | hmasd-portfolio-task Skill |
| Native/app addressing and return routes | SIBLING_COMMUNICATION.md |
| Experiment observation, adoption and terminal handover | EXPERIMENT_MONITOR.md |
| Scientific reading, literature, analysis and empirical tools | hmasd-scientific-tools Skill |
| Pro question publication and exact references | hmasd-pro-research-prompt-author Skill |
| Pro Send, identity, archive and receipt state | hmasd-chatgpt-pro-transport Skill |
| Owner intervention and execution trace | hmasd-owner-item Skill and owner/README.md |

Skills live under `.agents/skills/`; the owner README is under `docs/research/portfolio/owner/`.
Role configurations keep role/model boundaries and link to these sources instead of copying the
whole procedure. Change a rule at its maintained source and update affected entrypoints together.
Historical decisions, snapshots and benchmark materials remain evidence, not competing procedures.

## Complete deliverables and owners

| Owner | Deliverable |
| --- | --- |
| Root | Ready-work dispatch within existing decisions; dependencies and working-set replacement; main integration, current tracking, exact Pro dispatch/receipt forwarding and operational application |
| Direction DM | Card/predictions, object decisions, direct implementation or optional Implementer assignment, review disposition, published inputs, bounded execution, monitor handover, collection, technical acceptance, scientific intake, cleanup and continuation |
| Designated Portfolio DM | Decision materials grounded in Portfolio principles/specs/experience, complete Pro-response conformance and intake, execution mapping or exact conflict returned to Pro |
| Implementer | One owned code/check deliverable to DM; no scientific selection, Git/index work or result-bearing launch |
| Reviewer | Independent high-risk engineering evidence, with findings returned to the engineering owner |
| Scout / Verifier / Critic | One bounded factual, runtime or scientific-criticism question directly for the parent; no new child chain |
| Operator, when useful | Exact launch/handover/collection or cleanup batch from accepted inputs; DM retains acceptance |
| Independent Monitor | Observe adopted accepted handles; send adoption/terminal facts to Root, without collecting full results or interpreting science |
| Independent Transport | Execute exact authored Pro requests, observe and archive, return one factual receipt to the bound Root parent |
| Portfolio Pro | Final decision on the bound cross-direction question within current owner/specification constraints |

DM may use optional specialists when a complete independent task saves work or enables useful
parallelism. It does not rebuild a CM layer or delegate individual shell steps. Root does not
retype DM launch commands, repeat its tests or redo its scientific intake. Neither a child's
completion nor a Monitor exit-zero receipt is technical/scientific acceptance.

For shared control-plane engineering without a direction owner, Root owns the edit/check/review
and acceptance batch, optionally using an Implementer and high-risk Reviewer directly. A shared
scientific-code change is assigned to one existing relevant DM, with affected DMs supplying their
constraints. Only the assigning owner resolves out-of-scope decisions; specialists return precise
gaps rather than inventing another authority layer.

## Portfolio material and response route

OWNER_DIRECT 2026-09-11: resolve recurring Pro transport stalls. Transport retains
ownership through same-request recovery, complete-response archival and actual
parent delivery. Root dispatches a concrete recovery action when a recoverable
blocker returns; it does not leave a failed click as an indefinite direction park.
Uncertain acceptance permits reconciliation only. Proven nonacceptance permits
an exact-payload retry after interaction repair under the Transport skill, with
all prior attempts preserved. A complete verified Git response is routed to its
DM while receipt-label corrections proceed independently. No new Pro question,
scientific budget, provider binding or scheduler follows from this repair.

Root chooses a relevant recently active DM with the current evidence, and names the question,
scope and original sources. One DM authors the complete Portfolio packet; other DMs contribute
facts where needed. The author uses `hmasd-portfolio-task` and Prompt Author, preserving exact
references and contrary evidence. If unavailable, Root explicitly transfers the remaining work
to another relevant DM; Root does not take over scientific drafting.

For a new request the actual author is source, the current Root task is parent and the existing
Transport is operator. `caller_role=portfolio` selects the Pro node, not a native Root identity.
Root checks published artifact/route facts and dispatches the exact handoff. It returns substantive
omissions to the author instead of rewriting the packet. Transport receipts still go only to Root;
Root forwards the complete response to the designated DM using `followup_task`.

New GitHub-delivery prompts include an in-turn downloadable Markdown fallback. If Pro cannot
expose or complete its scoped GitHub writes after checking actual state, it finishes the review
and attaches the full `RESPONSE.md` in chat. Transport downloads it, binds it to the accepted request and paired response, records its byte
count and SHA-256, stores `<archive_id>__02_RESPONSE.md`, and retains the same bytes as repository
sidecar `archive/CHAT_FALLBACK_RESPONSE.md`. The GitHub `archive/RESPONSE.md` remains reserved for
actual connector delivery.
Root forwards that artifact to the designated DM for the same conformance intake. This fallback
does not assert a GitHub commit/comment and does not authorize another Send.

The DM reads the full response and checks the bound question, current owner/spec constraints,
scientific meaning and evidence. It returns the actual decision and operational mapping, or a
concrete conflict for the same Pro node. It does not locally overrule or add approval to a formed
conforming decision. Root applies the conforming decision, updates Portfolio/tracking and assigns
follow-on work within the existing limits. Unresolved questions do not block independent work.
Apply Portfolio consequences direction by direction as each affected path becomes ready.

## Execution inputs and observation

DM freezes the committed command/script, exact node/source/cwd/output/handle, host/device boundary,
budget and stop condition. The assigned executor uses those bytes rather than reconstructing a
similar command. Check staged inputs, including preflight helpers, against accepted sources;
Windows-to-Linux wrappers preserve literal variables and LF bytes and receive a syntax check
without executing the scientific payload. A disagreement returns to the same DM before submission.

Apply AGENTS §§5–7: remote-first where portable, published exact source, fresh destination memory
admission adjacent to each invocation, and no extra invocation from a repair or handover. Cost
projection uses the runner's complete per-arm law. Relevant post-learner publication coverage
follows the empirical/runtime specs and the actual dependent claim, not blanket historical replay.

After acceptance, DM/Operator directly adds the handle to the shared Monitor, using the live
primary-control configuration, not frozen or stale direction copies. The `MONITOR_ADD` payload
must require `get_goal` and continuation of the matching unfinished goal or `create_goal` without
a token budget. Keep adoption pending until the Monitor reports both direct handle state and the
actual unfinished goal state; app delivery alone proves neither. Do not start a second status-polling loop. Root forwards terminal facts to
the original collection owner, then DM completes technical acceptance and separate scientific
intake. Root also receives `MONITOR_GOAL_COMPLETE` after the final terminal notice is delivered and
the active set is empty. Uncertain process or message acceptance is reconciled on the same identity, never retried
as a fresh invocation merely because an observation was lost.

## Current records, integration and cleanup

Root owns main and its index, and integrates named accepted commits after checking what is already
integrated. DM owns its direction branch/checkout and code publication. Preserve one editing owner
for overlapping work. Independent paths can proceed concurrently; every authorized commit pushes
immediately. Do not hold an accepted commit for a sibling result or batch merge. A role migration
does not create a new branch or a new scientific object.

Root maintains `docs/research/portfolio/PORTFOLIO.md` as the current disposition/readiness snapshot
and `EXPERIMENT_TRACKING.md` as accepted handles, owners, terminal facts and pending work. Scientific
statements cite DM intake/Pro authority; Root integration is not another verdict. Batch useful
routine record edits only when they are already ready together; never wait for multiple directions
to manufacture a combined update. Apply actual owner overrides at the affected direction's clean
boundary via hmasd-owner-item.

DM prepares its exact cleanup inventory during collection. Assigned executors preserve unique
source/evidence and verify removed paths absent from disk and worktree registration; Root confirms
main integration/retention and accepts reclamation. Shared authoring and active delivery checkouts
remain while used. A creator cleans its own test scratch under tests/AGENTS.md; Root is not a
routine garbage collector. Never remove live work, evidence or another invocation's scratch.

Existing CM assignments retain their original parent/accepted scope until closeout; the receiving
DM explicitly takes any remaining responsibility. New work uses the consolidated DM role. Preserve
accepted Pro requests and generations, Monitor handles, receipt destinations and historical names.
Codex App supplies messaging/wake/recovery behavior; configuration changes take effect on restart.
Do not add a scheduler, delivery service, reload detector or new heartbeat for this migration.
A workflow edit or restart does not resume or enlarge scientific execution.
