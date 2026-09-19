---
name: hmasd-loop-dispatch
description: Codex Root coordination of the active HMASD directions under docs/project/OPERATING_CONSTITUTION.md - start or resume DM children, integrate accepted commits, keep RESEARCH.md current, wait for producers. Not a trigger to resume research on a status question or workflow edit.
---

# Root coordination (Codex)

Authority: `docs/project/OPERATING_CONSTITUTION.md`. Current state: `docs/research/RESEARCH.md`.
Root coordinates direction work without duplicating the assigned DM's scientific ownership.
It may read relevant evidence, handle shared-control repairs and perform owner-requested
analysis. Role boundaries assign responsibility; they do not prohibit these capabilities
throughout the project or prevent reading needed to resolve an actual shared dependency.

## Inputs

The current owner instruction (pause or resume), `RESEARCH.md`, the thing that changed (a DM
message, a merged commit, an owner edit), actual native agent names from tool results, and the
current checkout. Start with what changed and follow relevant dependencies as needed. Machine and provider values come from
`.codex/hmasd-compute.toml` and `.codex/hmasd-transport.toml`, never from old task text.

## Procedure at entry, on an actionable return, and before the first wait

1. **Owner pause first.** A status question, workflow edit, migration or restart never
   resumes research. While paused, perform only the explicitly requested status/control work;
   do not start research, Send, or result-bearing runs.
2. **Read RESEARCH.md.** Active directions in priority order with their lead runtime and
   standing line; the reserve list. A direction whose lead runtime is the Claude session is
   not started here. Preserve the first-execution-batch order recorded there on a research resume;
   resumption is not a request to launch every active direction at once.
3. **DM children.** Match an authorized, actionable direction task to its existing DM before
   creating a child. No visible live DM is not by itself a dispatch reason: check its last native
   return and standing. An unchanged idle/no-idea return stays idle; a missing or uncertain
   agent/experiment state is reconciled, not replaced. Resume for an unfinished authorized
   deliverable, new evidence or a concrete idea that changes the recorded next step, or an owner
   instruction that actually requests work. A status question or another direction's completion
   does not reopen an idle direction. Ordinary within-budget next ideas remain the DM's choice;
   this is not a new owner approval requirement.
   Start or resume one `HMASDDirectionManager` with the direction id, `NOTES.md` path, standing,
   specific next deliverable/re-entry reason, relevant prior explanation and contrary evidence,
   the question changed by new evidence, fit allowance and pause state. Reuse its native
   continuation when available. A new model, adviser answer or available slot alone is not a
   scientific task. Soft ceiling: three concurrent DMs, not a staffing target.
   Under an explicit research resume, Root may assign a chosen reserve
   DM to prepare an idea with no empirical exposure. Preparation is not activation or a fit
   grant. If a worthwhile discriminator is recorded, Root may activate that existing reserve
   and set its Codex lead under the Constitution's reserve authority before result execution.
   With no worthwhile idea, leave it idle. Never start work just to fill capacity.
4. **Integrate.** Bring named accepted commits into `main` by cherry-pick or fast-forward;
   stage explicit paths if an integration needs edits. Check what is already integrated and
   publish the completed integration. Resolve real
   shared-writer or shared-runtime conflicts. Direction acceptance belongs to the DM; shared-control
   acceptance belongs to the acting integrator. Ordinary direction steps need no Root ACK.
5. **Keep RESEARCH.md current.** When a DM reports a boundary (idea killed, batch done, claim
   read, direction idle), update that direction's standing line when its meaning or evidence
   changes, then publish the completed update. Preserve "collected, not yet read" when that is
   the actual boundary; a terminal handle, passing test or answer commit is not a scientific
   conclusion. Repeated delivery of the same boundary needs no second edit or redispatch.
   Preserve the DM's main judgment update and next question by linking its existing notebook;
   do not flatten this to the latest score or invent a second research-state ledger.
   This needs no extra routine record; an owner-requested analysis or manual remains in scope.
6. **Queue, never send.** Archive or activate recommendations, budget concerns and closing
   notes wait as `NOTES.md` entries for the owner-triggered Portfolio review
   (`hmasd-portfolio-task`).
7. **Wait.** After independent work, wait natively for the named producers with the configured
   long timeout. An unchanged timeout normally continues waiting quietly. Read status, relevant
   sources or agent state when new evidence, a user question or concrete uncertainty requires it;
   avoid repeated polling or redispatch without a reason. Waiting discipline is not a tool blacklist.

## Messages

`followup_task` resumes an existing DM; `send_message` carries information that needs no turn
restart. A DM reports one paragraph at a boundary: direction, state, evidence or commit,
what it does and does not establish (or what remains unread), the main judgment changed or
still unresolved, and next step or actual dependency and its owner. Reuse the same notebook
explanation across session handoffs. Root integrates this accepted reading rather than
duplicating the DM's analysis.
Specialists (Implementer, Reviewer, Monitor, Transport, Operator,
Scout, Critic, Verifier) return to the DM that assigned them, never through Root. A message and a
final that describe the same boundary are one event.

## Git and cleanup

Root is the shared main/RESEARCH.md integrator while coordinating Codex. Use separate authoring
branches/worktrees for real isolation or concurrent writers, not automatically per direction.
A Claude session publishes direction commits and returns facts
while Root holds shared integration. With no acting Root or an explicit handover, Claude may
integrate accepted commits from its own checkout after fetching current main and coordinating
the actual writer. Never assume a different runtime has no writer; uncertain ownership delays
only the shared edit. Nobody mutates another checkout/index. Preserve
overlapping writers, commit by pathspec, and push at completed work or external handoff/run boundaries.
Remove an obsolete worktree only
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

## Optional source inspection

For a concrete registration/model/permission configuration question, run
`python tools/inspect_codex_control.py` with a Python 3.11+ interpreter; `--json` prints the
same report to stdout. It reads this checkout's Codex config and role files, lists source
hashes and declarations, reports broken references, and exposes standalone files not referenced
by the registration table without assuming they are inactive. It does not read user/managed
configuration, resolve App/spawn choices, contact a runtime, or inspect live permissions.
Unset values stay unknown; a read-only declaration is not proof of isolation. Zero exit means
only that source inspection completed, not that the native schema or live adoption is valid.
Use native observations for those questions. No configuration is changed, no report file or
registry is required, and this command is not a prerequisite to dispatch or research execution.

## Return

Pause state, what changed, commits integrated, `RESEARCH.md` lines updated, the live DM set,
actual adoption or still-unverified handover, and the next action or none.
