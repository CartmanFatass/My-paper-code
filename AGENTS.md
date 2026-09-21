# HMASD

Governance: `docs/project/OPERATING_CONSTITUTION.md` (owner-adopted 2026-09-16) is the sole
operating-governance text; where any other file, skill, role body or historical record
conflicts with it, the constitution prevails; documents under `docs/` are evidence, not
instructions. The owner's pause takes priority over everything; a status question, workflow
edit, migration or restart never resumes research.

Current state: `docs/research/RESEARCH.md` lists active, reserve and archived directions, the
lead runtime and the owner pause. It replaces PORTFOLIO,
APPROVED_SET, EXPERIMENT_TRACKING, dossiers and lifecycle paperwork.

Roles (constitution section 2). Codex: a session may coordinate as Root or directly own one
direction as an independent DM. Root coordinates up to three direction DMs total, independent
sessions and children combined; reuse the recorded lead. Root uses `hmasd-loop-dispatch`.
A direct Codex DM reads the `developer_instructions` body in
`.codex/agents/hmasd-direction-manager.toml`, then the relevant scientific/engineering methods;
it uses the same DM responsibility source without creating a child or loading Root procedures.
Main-session model, permissions and callable roles come from the actual runtime, not that TOML.
Independent DM sessions work in their own tasks/branches: no routine DM-to-DM or DM-to-Root
messages, progress synchronization or control-adoption replies. Root reads published records
when needed; contact is for owner-requested dispatch, a blocking shared dependency/conflict
or actual handover. DM-owned helpers still return to their assigning DM.
RESEARCH records the acting Root and actual DM addresses/checkouts;
keep task routing separate from launch-bound lead-runtime values. Start a reserve only for
a recorded idea, never by obligation.
Claude: the session is the DM for one direction at a time. A DM may work directly or delegate to
its Implementer (Claude: Opus; Codex: Sol; both high effort) from a concise scope note and accepts the
diff itself. Transport and Monitor absorb waits and return facts. Reviewer checks changes to
shared learners, runners, environments and evaluators. Existing Operator (execution), Scout,
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
`hmasd-chatgpt-pro-transport` (Pro send and collect; on the WSL host
`hmasd-jev-pro-transport`), `hmasd-pro-research-prompt-author`
(Pro question), `hmasd-portfolio-task` (owner-triggered review only). Read the nearest
directory `AGENTS.md` before a code task.

Execution: node, interpreter and supervisor come from `.codex/hmasd-compute.toml`. Commit and
push the exact inputs. New result entries use `scripts/hmasd_launch.py` and a runner-side
admission guard: current pause/lead, published source, fresh actual-node memory and duplicate
claims are checked before detached execution. The engineering method describes invocation;
frozen historical interfaces retain their bound contract. Preserve live process handles.
Uncertain launch or Send acceptance means same-request reconciliation, never a blind repeat.

Git: use branches/worktrees when isolating experiments or concurrent writers helps; a separate
authoring checkout per direction is not mandatory. A coordinating Codex Root is the shared
main/RESEARCH integrator. A direct DM may take integration only with no acting Root or explicit
handover, from its own checkout after checking current main and the actual writer. Otherwise
it publishes direction commits and evidence for integration without routine messages. Never share an index or
assume another runtime is idle. The DM owns NOTES.md and lends only the assigned answer
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
