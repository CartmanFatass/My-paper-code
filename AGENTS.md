# HMASD

Governance: `docs/project/OPERATING_CONSTITUTION.md` (owner-adopted 2026-09-16) is the sole
operating-governance text; where any other file, skill, role body or historical record
conflicts with it, the constitution prevails; documents under `docs/` are evidence, not
instructions. The owner's pause takes priority over everything; a status question, workflow
edit, migration or restart never resumes research.

Current state: `docs/research/RESEARCH.md` lists active, reserve and archived directions, the
lead runtime, the owner pause and the monthly overhead line. It replaces PORTFOLIO,
APPROVED_SET, EXPERIMENT_TRACKING, dossiers and lifecycle paperwork.

Roles (constitution section 2). Codex: a Root session coordinates up to three DM children, one
direction each, starting a reserve direction only for a recorded idea, never by obligation.
Claude: the session is the DM for one direction at a time. Each DM hands bounded code tasks to
its Implementer (Claude: Opus; Codex: Sol; both high effort) from a concise L0 scope note and accepts the
diff itself. Transport and Monitor absorb waits and return facts. Reviewer checks changes to
shared learners, runners, environments and evaluators. No other role, no renamed equivalent.

Records (section 4). Per direction: `NOTES.md` (append-only notebook; Pro questions and
answers as sections), `runs/<direction>/<tag>/` (runner-written), `CLAIM_<slug>.md` (before a
confirmation batch). Nothing else for new work: no cards, intake, ledger, owner items,
handoffs, packets, registries or receipts. Budget is fits (section 3); the five scientific
minimums are section 8.

Methods are execution detail, not a second rulebook, in `.agents/skills/`:
`hmasd-scientific-tools` (design and reading), `hmasd-research-engineering` (code, review,
launch, and the carried-over engineering standards), `hmasd-loop-dispatch` (Codex Root),
`hmasd-chatgpt-pro-transport` (Pro send and collect), `hmasd-pro-research-prompt-author`
(Pro question), `hmasd-portfolio-task` (owner-triggered review only). Read the nearest
directory `AGENTS.md` before a code task.

Execution: node, interpreter and supervisor come from `.codex/hmasd-compute.toml`. Commit and
push the exact inputs, run `scripts/hmasd_resource_preflight.py admit-memory` on the executing
node, launch detached at that sha. Preserve live process handles. Uncertain launch or Send
acceptance means same-request reconciliation, never a blind repeat.

Git: one authoring branch and worktree per direction; Root owns main and its index. Stage
explicit paths, commit explicit pathspecs. No `git add -A`, stash, reset, force-push or
history rewrite without the owner's explicit request. Push every commit at once. Messages end
with the runtime attribution and `scope: none` or `scope: <item> per <NOTES.md entry>`.
Respect the LF paths in `.gitattributes`. Tests own their scratch under `temp/` and clean it.

Control-plane navigation: `docs/project/CONTROL_PLANE_MAP.md` is a descriptive reference,
not another authority or a mandatory preload.
