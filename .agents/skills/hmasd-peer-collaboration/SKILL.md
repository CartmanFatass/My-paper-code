---
name: hmasd-peer-collaboration
description: Coordination between the Claude DM session and the Codex Root as peer researchers - channels, message shape, inbox convention, shared-working-tree hygiene and disagreement routing under constitution section 2. A method, not a role or an authority.
---

# Peer collaboration: Claude session and Codex Root

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 2 (owner amendment 2026-09-27,
peer status). This page holds the channel details that the amendment delegates to a shared
method. Status: **draft proposed by the Claude session on 2026-09-27**; it takes effect when
Root records agreement (an inbox file, below) and the owner adopts it. Afterwards either peer
may make maintenance edits that do not change meaning (wording, valid links) with an
explicit-path commit and a dated line under "Revisions". A substantive change to channels,
write responsibility, communication scope or disagreement handling needs both peers' agreement
(an `AGREEMENT` exchange); anything touching constitutional permissions or constraints is
adopted by the owner. This method grants no new permission.

## Standing

- The Claude session and the Codex Root are peer researchers. Neither approves, assigns or
  overrules the other. Root's cross-direction coordination and shared-control maintenance for
  the Codex DMs are an assigned service to the project; the Claude side's direction count is
  the owner's concurrency setting.
- Shared truth is written, not messaged: `docs/research/RESEARCH.md` (standing rows and the
  routing block) and each direction's append-only `NOTES.md`. A message carries pointers
  (commit, path, anchor) to committed evidence, never the evidence itself, and never replaces
  the record.
- No status traffic. Progress is read from RESEARCH and NOTES at need; nobody owes a report,
  acknowledgment or periodic message to the other.
- Delivery is not reading. A message may describe a pending draft or an immediate control fault
  with brief necessary facts, marked "uncommitted" with the observation time and source; nobody
  has to commit the other's draft before it can be discussed. When acceptance of a delivery is
  uncertain, check the same request rather than resending; no message register is kept.

## Channels

**Claude → Root.** `codex queue --thread <root session uuid> --message "<text>"` from the
checkout root, run with the Codex App's WSL environment, otherwise the CLI reads the WSL-only
thread store and reports "no rollout found": `CODEX_HOME=/mnt/c/Users/fires/.codex
CODEX_SQLITE_HOME=/home/fires/.codex/sqlite` (the values the App writes into its sessions'
shell snapshots; verified 2026-09-27, queued message `01a0e21d-…` to Root). The current Root
uuid and the Codex DM uuids are the ones in the RESEARCH routing block; the message text
follows the shape below. A long document goes to
`docs/inbox/YYYY-MM-DD-<topic>.md`, committed with its explicit path, and the queue message
points to it. Messages to a Codex DM other than Root are not covered by this method; such a
need goes to Root until the owner extends the standing request.

**Root → Claude.** A Markdown file `docs/Claude_docs/inbox/YYYYMMDD_<topic>_ROOT.md`, written in
the shared working tree and committed with its explicit path (never a whole-tree add). One file
per need; a follow-up on the same topic appends a dated section to the same file, told apart
by its commit and date. The Claude session checks for every commit that touched that directory
since the last commit it has seen (a background poll while the session is active; a
`git log -- docs/Claude_docs/inbox/` check at natural boundaries otherwise) and reads each
delivered file from its own commit (`git show <sha>:<path>`), never from the working copy and
never from a `HEAD` that may have moved on: the commit is the delivery, a half-written file is
never read, and delivery is not reading. A queue message from Root to the Claude session does
not exist; the file is the channel. Claude's reply, when the file asked for one, goes back by
`codex queue`.

**Shape (both directions).** First line `[HMASD peer] <NEED>: <one-line subject>` with NEED one
of `SCOPE` (overlap or boundary of directions/paths), `CONTROL` (shared control or hazard, e.g.
node checkout, lead, pause, admission), `HANDOVER` (an operation or path changes hands),
`READING` (please read a named record before a named decision), `EVIDENCE` (a committed result
that bears on the other's direction), `AGREEMENT` (this method or another shared method). Then
at most about fifteen lines: the facts with commit, path and anchor; the one concrete ask, or
"no reply needed"; a time bound if any. A message carries exactly one need. A reply exists only
when the message asked for one; there is no acknowledgment-only message and no relay of a
third session's text.

## Shared working tree

Both peers author on the same checkout and branch (`/home/fires/hmasd-wsl`, `main`). Therefore:

- Edit a shared file (RESEARCH, AGENTS, CLAUDE, the constitution, skills, role bodies) inside
  one short critical section under `flock .git/hmasd-main-writer.lock` that covers the final
  check against the current file, the necessary edit, staging and the commit; drafting, long
  tests, review and approval waits happen outside the lock. Before staging run
  `git diff -- <file>`; before committing check the staged paths and the full staged diff; stage
  only the hunks you are responsible for. A draft of the other peer that awaits owner adoption
  or a blocked approval stays as it is: nobody commits it on the author's behalf or holds the
  lock for it. Example of the failure: on 2026-09-27 Root's `8f749c901` carried the Claude
  routing-row hunk that sat uncommitted in the tree (acknowledged by Root).
- Direction-owned paths (`experiments/candidates/<direction>/`, its tests, NOTES, `runs/`,
  `temp/directions/<direction>/`) are not edited by the other peer without an explicit
  delegation or handover; the constitution's narrow delegated fixes, the lending of a Pro
  answer subsection and the handover rules stand. A needed change is asked for by message.
- The RESEARCH routing block is the one place for session addresses. Root maintains the Codex
  session rows it is delegated to maintain, each DM keeps its direct publication right for its
  own records, and the Claude rows are maintained by the Claude session; other rows are
  preserved and merged, never rewritten. "Own rows" is not a no-write rule for shared
  knowledge: under constitution section 4 either peer revises shared background that evidence
  affects, preserving the other's direction conclusions and recorded disagreements.
- On the shared node checkout, routine synchronisation and recovery of missing records never
  run `git sparse-checkout set|add`; the cone cleanup deletes other directions' committed run
  directories (recorded in `5cd939656`). When the sparse selection genuinely must change, use
  the published method of `0f5d78903`
  (`.agents/skills/hmasd-research-engineering/references/local-execution.md`): serialise, first
  check the affected outputs and their active consumers, preserve the necessary unique
  evidence, then verify the original handles and evidence; ordinary recovery fetches only the
  exactly verified missing tracked files. Keep one necessary, durable, verifiable canonical copy
  of bulk outputs at the existing result boundary, reusing copies that exist; do not move
  in-flight inputs or change frozen bindings.
- Untracked files of the other peer (helpers' scratch, in-progress packages) are left alone.

## Disagreement

A material direction disagreement between the peers goes first to one adequate independent
scientific review under constitution section 5; each peer then records its substantive opinion
and disposition in its own records, and what remains unresolved goes to the owner. No ruling by
message, no edit of the other's NOTES or RESEARCH row, neither peer declares the other's
agreement, and no review is stacked automatically. Only the contested new investment or
expanded claim waits; existing collection and independently authorised work continue. An
ordinary technical conflict (a shared file, a node resource, an evaluation device) is raised as
one `CONTROL` message with the facts and a proposed resolution; delivery of that message is not
consent to take over or rewrite the other's path.

## What this is not

Not a role, not a reporting line, not research authority, not a per-batch duty. It creates no
new record type: messages are ephemeral, the records stay in RESEARCH, NOTES and Git.

## Revisions

- 2026-09-27 — draft by the Claude session (this page created).
- 2026-09-27 — outbound command needs the App's `CODEX_HOME` / `CODEX_SQLITE_HOME` (added after the first successful send).
- 2026-09-27 — Root's six scoped revisions (`docs/Claude_docs/inbox/20260927_peer_collaboration_ROOT.md`, commit `d648676c1`) adopted item by item: maintenance-only later edits; lock scope and staged-diff check; delivery by commit SHA and "delivery is not reading"; content responsibility including section 4 shared background; node sparse-selection method of `0f5d78903`; disagreement sequence. Both peers agree; awaiting owner adoption.
