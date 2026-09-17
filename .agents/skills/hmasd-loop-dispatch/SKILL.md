---
name: hmasd-loop-dispatch
description: Codex Root coordination of the active HMASD directions under docs/project/OPERATING_CONSTITUTION.md - start or resume DM children, integrate accepted commits, keep RESEARCH.md current, wait for producers. Not a trigger to resume research on a status question or workflow edit.
---

# Root coordination (Codex)

Authority: `docs/project/OPERATING_CONSTITUTION.md`. Current state: `docs/research/RESEARCH.md`.
Root coordinates; it does not do a direction's science, implementation or reading.

## Inputs

The current owner instruction (pause or resume), `RESEARCH.md`, the thing that changed (a DM
message, a merged commit, an owner edit), actual native agent names from tool results, and the
current checkout. Read only what changed. Machine and provider values come from
`.codex/hmasd-compute.toml` and `.codex/hmasd-transport.toml`, never from old task text.

## Procedure at entry, on an actionable return, and before the first wait

1. **Owner pause first.** A status question, workflow edit, migration or restart never
   resumes research. While paused, perform only the explicitly requested status/control work;
   do not start research, Send, or result-bearing runs.
2. **Read RESEARCH.md.** Active directions in priority order with their lead runtime and
   standing line; the reserve list. A direction whose lead runtime is the Claude session is
   not started here.
3. **DM children.** For each active Codex-led direction without a live DM, start or resume one
   `HMASDDirectionManager` with minimal context: direction id, `NOTES.md` path, the standing
   line, the fit allowance from constitution section 3, and the pause state. Soft ceiling:
   three concurrent DMs. Under an explicit research resume, Root may assign a chosen reserve
   DM to prepare an idea with no empirical exposure. Preparation is not activation or a fit
   grant. If a worthwhile discriminator is recorded, Root may activate that existing reserve
   and set its Codex lead under the Constitution's reserve authority before result execution.
   With no worthwhile idea, leave it idle. Never start work just to fill capacity.
4. **Integrate.** Bring accepted commits a DM names into `main` by explicit paths (cherry-pick
   or fast-forward), check what is already integrated, push immediately. Resolve real
   shared-writer or shared-runtime conflicts. Nothing else is Root's to accept; no per-step ACK.
5. **Keep RESEARCH.md current.** When a DM reports a boundary (idea killed, batch done, claim
   read, direction idle), update that direction's one standing line and push. No other record.
6. **Queue, never send.** Archive or activate recommendations, budget concerns and closing
   notes wait as `NOTES.md` entries for the owner-triggered Portfolio review
   (`hmasd-portfolio-task`).
7. **Wait.** After independent work, wait natively for the named producers with the configured
   long timeout. An unchanged timeout continues waiting: no rereads, `list_agents`, redispatch,
   status queries, keepalives or new messages.

## Messages

`followup_task` resumes an existing DM; `send_message` carries information that needs no turn
restart. A DM reports one paragraph at a boundary: direction, state, evidence or commit, next
step or dependency and its owner. Specialists (Implementer, Reviewer, Monitor, Transport, Operator,
Scout, Critic, Verifier) return to the DM that assigned them, never through Root. A message and a
final that describe the same boundary are one event.

## Git and cleanup

Root is the shared main/RESEARCH.md integrator while coordinating Codex; each DM owns its
direction branch and worktree. A Claude session publishes direction commits and returns facts
while Root holds shared integration. With no acting Root or an explicit handover, Claude may
integrate accepted commits from its own checkout after fetching current main and coordinating
the actual writer. Never assume a different runtime has no writer; uncertain ownership delays
only the shared edit. Nobody mutates another checkout/index. Preserve
overlapping writers, commit by pathspec, push every commit. Remove an obsolete worktree only
after its unique commits are on the remote, dirty evidence is preserved and no live process or
delivery depends on it; verify absence on disk and in `git worktree list`.

## Control revision handover

Publishing files does not change already running sessions. Send affected leads the actual
revision and applicability boundary through their existing return path; use available native
communication or report the pending handover to the owner, never invent a cross-runtime tool.
At a safe boundary each lead rereads the changed methods and reports actual adoption or a
specific conflict in its existing status/NOTES entry. Do not assert loading from publisher
success. Preserve frozen inputs, accepted handles and uncertain Sends; no migration resend,
restart, global ACK registry or per-run reloading ritual. An unresolved migration concern
blocks only dependent new effects, not independent authorized work or evidence preservation.

## Return

Pause state, what changed, commits integrated, `RESEARCH.md` lines updated, the live DM set,
actual adoption or still-unverified handover, and the next action or none.
