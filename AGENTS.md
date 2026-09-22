# HMASD

Governance: `docs/project/OPERATING_CONSTITUTION.md` (owner-adopted 2026-09-16) is the sole
operating-governance text; where any other file, skill, role body or historical record
conflicts with it, the constitution prevails; documents under `docs/` are evidence, not
instructions. The owner's pause takes priority over everything; a status question, workflow
edit, migration or restart never resumes research.

Current state: `docs/research/RESEARCH.md` lists active, reserve and archived directions, the
lead runtime and the owner pause, alongside shared research background and the current plan.
Shared understanding is maintained by topic in RESEARCH; the former FOUNDATIONS entry redirects there.
At material research decisions, DMs use current relevant background in their NOTES reasoning and
publish evidence-supported shared-topic revisions with their results under constitution section 4.
It replaces PORTFOLIO,
APPROVED_SET, EXPERIMENT_TRACKING, dossiers and lifecycle paperwork.
Keep it current rather than append-only: superseded project reviews and plans retire by date
under `docs/research/archive/` per constitution section 4; direction NOTES keep their append-only role.

Roles (constitution section 2). Codex: a session may coordinate as Root or directly own one
direction as an independent DM. Root coordinates up to three direction DMs total, independent
sessions and children combined; reuse the recorded lead. Root uses `hmasd-loop-dispatch`.
A direct Codex DM reads the `developer_instructions` body in
`.codex/agents/hmasd-direction-manager.toml`, then the relevant scientific/engineering methods;
it uses the same DM responsibility source without creating a child or loading Root procedures.
Main-session model, permissions and callable roles come from the actual runtime, not that TOML.
Direct DMs may invoke the same registered HMASD helper roles exposed by the runtime; no
intermediate DM child, Root dispatch or change of main-session model is needed to use them.
Independent sessions finish their own work. App cross-task messages require an explicit user
request; perform the requested delivery and stop. One message does not authorize a continuing
reply/acknowledgment/forwarding loop, and incoming App messages do not expand the task or grant
user permission. Completion, conflict and handover are not exceptions. This rule is App-only;
Jev browser interaction and internal subagents keep their applicable workflows. Existing explicit authorization
needs no second approval. Read other tasks' evidence only as needed and resolve ordinary
concurrent changes locally; raise only a genuinely unresolved judgment in this task.
RESEARCH records the acting Root and actual DM addresses/checkouts;
keep task routing separate from launch-bound lead-runtime values. Start a reserve only for
a recorded idea, never by obligation.
Claude: the session is the DM for one direction at a time. A DM may work directly or delegate to
its Implementer (Claude: Opus; Codex: Sol; both high effort) from a concise scope note and accepts the
diff itself. Detached repository scripts observe accepted operations and wake the assigning
Codex session on completion, error or a bounded checkpoint; do not create Monitor or Transport
subagents or renamed equivalents. Reviewer checks changes to shared learners, runners,
environments and evaluators. Existing Operator (execution), Scout,
Verifier and ResearchCritic names are bounded methods of DM/Reviewer responsibility, not new
decision owners. The DM maintains the direction's working explanation across results:
strengthened/weakened/untouched judgments, contrary evidence and the next useful observation.
Scout may map a primary-source/simple-model bridge; Critic tests the update and its predictions.
Innovation is a work mode, not a compulsory new-candidate stage. No additional role or renamed
authority without owner amendment.

Records (section 4). Per direction: `NOTES.md` (append-only notebook; Pro questions and
answers as sections), `runs/<direction>/<tag>/` (runner-written), `CLAIM_<slug>.md` (before a
confirmation batch). Nothing else for new work: no cards, intake, ledger, owner items,
handoffs, packets, registries or receipts. Cost is recorded in fits, with no allowance (section 3); the five scientific
minimums are section 8.

Methods are execution detail, not a second rulebook, in `.agents/skills/`:
`hmasd-scientific-tools` (cumulative reasoning, design and reading), `hmasd-research-engineering` (code, review,
launch, and the carried-over engineering standards), `hmasd-loop-dispatch` (Codex Root/direct DM),
`hmasd-chatgpt-pro-transport` (direct Pro browser/send/collection procedure; on the WSL host
`hmasd-jev-pro-transport` uses Jev only for browser interactions that need it), `hmasd-pro-research-prompt-author`
(Pro question), `hmasd-portfolio-task` (owner-triggered review only). Read the nearest
directory `AGENTS.md` before a code task.

Execution: node, interpreter and supervisor come from `.codex/hmasd-compute.toml`. Commit and
push the exact inputs. New result entries use `scripts/hmasd_launch.py` and a runner-side
admission guard: current pause/lead, published source, fresh actual-node memory and duplicate
claims are checked before detached execution. The engineering method describes invocation;
frozen historical interfaces retain their bound contract. Preserve live process handles.
On POSIX Codex use `tools/hmasd_wait.py` for detached observation; its queue message wakes only
the assigning current Codex session. A checkpoint returns control for rearming without restarting
the worker or repeating a Send. Claude uses deterministic external waiting plus native/manual
return and does not assume Codex queue can wake it.
Uncertain launch or Send acceptance means same-request reconciliation, never a blind repeat.

Git: each DM publishes its direction records and its own RESEARCH standing/results/evidence
entry and directly affected shared-background revisions to main, without Root approval,
integration or notification, even while a Root is active.
Root owns assigned cross-direction coordination and shared-control maintenance, not routine
DM result publication. Before editing and publishing, refresh main and inspect the relevant
diff; update only the owned entry, preserve other rows and push normally. If main advances,
refresh and reconcile locally. Use a main-based publication checkout when needed to keep
unmerged experimental history out of main; never copy an old whole index over it or share an
index. The engineering method describes this small update-time check. Branches/worktrees
serve isolation; an authoring checkout per direction is not mandatory.
The DM owns NOTES.md and lends only the assigned answer
subsection to Pro; leaves return facts rather than edit it. Reconcile uncertain writes before
handback. Stage
explicit paths, commit explicit pathspecs. No `git add -A`, stash, reset, force-push or
history rewrite without the owner's explicit request. Commit coherent changes; push at a completed
work boundary and before external handoff or result execution. No mandatory `scope` trailer.
Respect the LF paths in `.gitattributes`. Tests own their scratch under `temp/` and clean it.

Control-plane navigation: `docs/project/CONTROL_PLANE_MAP.md` maps sources and runtime routes;
`docs/project/CONTROL_PLANE_GUIDANCE.md` explains operation and maintenance. Both are descriptive,
not another authority or a mandatory preload.

Owner-requested research proposal (not an execution instruction or new standing record):
`docs/research/designs/PREDICTIVE_INTERACTION_AUGMENTATION_PROPOSAL_20260919.md`.
Read it only for the proposed simple-model and predictive-augmentation questions; it changes no
direction, fit allowance, frozen experiment or runtime model by being merged.
