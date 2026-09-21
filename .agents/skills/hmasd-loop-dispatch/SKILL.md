---
name: hmasd-loop-dispatch
description: Enter or resume a Codex session as coordinating Root or independent single-direction DM under the HMASD constitution. Resolve existing session ownership, dispatch to independent tasks or children, integrate shared state and reconcile returns. Status questions and workflow edits do not resume research.
---

# Codex sessions: Root or direct DM

Authority: `docs/project/OPERATING_CONSTITUTION.md`. Current state and session routing:
`docs/research/RESEARCH.md`. Root coordinates; a DM owns science and its three records.
An independent DM session and a DM child have the same scientific responsibility.
Claude remains a single-direction DM through its generated `hmasd-research-hub`.

## Select the session's work

Read the owner instruction, pause, current direction standing and relevant native session
status. Infer the mode from the actual assignment or recorded ownership; do not ask the
owner to repeat an already clear choice.

- **Root:** coordinate a named set of directions, resolve shared dependencies, integrate
  accepted commits and maintain the shared index. Count independent DMs and children
  together toward the soft ceiling of three concurrent direction DMs. Do not fill slots
  without a worthwhile authorized task or duplicate a direct DM's scientific work.
- **Direct DM:** the session itself owns one direction. Explicitly read the
  `developer_instructions` body in `.codex/agents/hmasd-direction-manager.toml`, then the
  relevant notebook and scientific/engineering methods. Main sessions do not automatically
  inherit that child role body. Apply its responsibilities, not its TOML model, effort or
  permissions as alleged current settings. The session's actual native settings and the
  owner's explicit choices still apply. Implement, delegate, review, launch, collect and
  read as the DM; no extra Root child or forwarding layer is needed.
- **Status/control only:** inspect or perform the requested edit. A workflow change,
  restart, unarchive or address repair does not select a new experiment or lift a pause.

If a request changes the session's responsibility, resolve its current ownership and
in-flight work before taking the new assignment. Switching to Root does not silently
abandon a direction, and switching to direct DM does not silently replace its existing
lead. Scientific standing and accepted operations survive the switch. Ask only for an
unresolved scope or ownership choice that cannot be recovered from current evidence.

## Keep the contact recoverable

Use the existing RESEARCH index, with no separate session registry or handoff file:

- Coordination prose identifies the acting Root/shared integrator, its scope and actual
  native return address. Record its authoring checkout/branch when that matters to writers.
- A direction's standing identifies its independent DM task id and host, or its parent task
  and child agent address, plus its authoring checkout/branch. This gives a replacement
  Root a route to the existing producer instead of just a runtime label.
- Keep the launch-bound **Lead runtime** cell stable. Put addresses and explanatory
  session text in standing/coordination prose, not in a value compared by a frozen runner.
  A real lead change must reconcile canonical and published control before dependent runs.

Use only ids/addresses returned by native tools or established records, then verify them
with the runtime before dispatch. A title, a process name, a previous message or an app's
archived/idle state alone does not establish scientific ownership or permission to resume.
An unavailable address is a reconciliation question, not evidence that no DM exists.
Keep unknowns explicit; do not backfill addresses for dormant historical directions.

## Root dispatch and integration

1. **Owner pause and scope first.** Read the current index. Preserve the owner's direction
   choices and first-batch order; a status request never starts research. Do not take over
   a direction assigned to Claude. A new active idea needs its prospective entry; fits are
   recorded cost, not an allowance or entitlement.
2. **Find the existing DM.** Read its latest native return and standing. Reuse an independent
   session or child that already owns the direction. An unchanged idle/no-idea return stays
   idle unless the owner requests work or new evidence/a concrete idea changes the next
   step. An app task being archived is not the direction being scientifically closed.
3. **Use the matching native route.** Tool availability comes from the current runtime,
   not these example names. Independent Codex tasks use `list_threads` (and archived-task
   lookup when needed), `read_thread` or compact `wait_threads` snapshots to resolve status;
   `set_thread_archived(false)` restores a task when the owner's continuation requires it;
   `send_message_to_thread` continues it. This last tool starts/queues work: use it for an
   authorized task, an actionable boundary return or relevant coordination, not a status
   poll. Children use the native agent list, follow-up/message and wait tools. Resolve an
   uncertain dispatch against the same task/turn before sending again.
4. **Create only when needed and authorized.** An explicit owner request for a new standalone
   task uses `create_thread` with a verified project and supported environment; wait for the
   real thread id before recording or addressing it. Do not use a provisional client id as
   a thread id. Without such a request, a new bounded direction assignment may use the
   configured direction-manager child under existing research authority. Do not create a
   sidebar task merely because a subtask exists. Preserve current/default session model
   settings unless the owner explicitly chooses them; a role name does not set a main model.
5. **Give one concrete assignment.** Supply direction, notebook, prior judgment and contrary
   evidence, what changed, next deliverable, declared scope/cost, pause and any actual owner
   deadline, checkout/index ownership and Root return address. The DM accepts the science.
   Independent preparation continues while a real shared dependency is resolved; already
   valid admission does not need another Root ACK for each batch.
6. **Integrate meaningful boundaries.** Bring named accepted commits or the required shared
   index update into main from the integrator's own checkout, preserving other writers.
   A result branch can retain code/runs with pinned evidence links; do not roll an older
   whole index over newer direction work. Update standing when its meaning changes, then
   publish. A terminal process is not a read result: retain collection/interpretation work
   explicitly. Repeated delivery of the same boundary needs no duplicate edit or redispatch.
7. **Wait for actual producers.** For independent tasks prefer bounded `wait_threads` calls
   with the returned cursor; for children use native agent wait. Back off on unchanged
   state and keep it quiet. A queued prompt, active task, accepted launch, terminal handle
   and scientifically read result are different observations. Do not call them all done.

Root may assign reasoning-only preparation to an already chosen reserve, then activate it
under the constitution's existing reserve authority if a worthwhile idea is recorded.
Preparation neither lifts a pause nor starts a result batch. Portfolio recommendations
remain in the existing notebook/index for the owner-triggered review; this method does not
send them to Pro automatically.

## DM returns, independence and handover

At a meaningful boundary, the DM returns direction/state, evidence/commit, what the result
establishes and does not, the main judgment update and the next action or real dependency.
An independent Codex DM sends this to the recorded Root task through the available native
message tool; a child returns to its actual parent. With no assigned Root, report directly
to the owner. Leaves report to their assigning DM, not through Root. The notebook remains
the scientific record; do not create a packet to repeat it.

A Root being idle or temporarily unreachable does not suspend authorized independent work.
Publish the direction evidence, retain the pending integration fact and continue work whose
actual dependencies are met. Before taking shared integration with no acting Root or on an
explicit handover, verify the real writer and published main. Do not infer vacancy just
because a task disappeared from the current list, and never write another checkout/index.

For a real DM or Root replacement, reconcile live processes, uncertain Sends, uncollected
results and writes at a safe boundary. The recipient reads the latest notebook, adopts
existing handles and confirms the concrete responsibility through the native return path;
then update the address in the index. Ordinary progress does not need repeated adoption.
A restored session continues the same work, not a new batch. If the runtime lacks a native
route, report that specific handover limit; do not invent a cross-runtime messenger or
launch a replacement process to obtain a new handle.

## Git and control changes

One acting integrator owns shared main/RESEARCH at a time; each DM owns its notebook and
direction work. Use independent checkouts for concurrent writers, explicit pathspec commits,
and push completed work and exact result inputs. Branches and worktrees are useful isolation,
not a mandatory new checkout per direction. Keep accepted source identities and other writers.
Remove an obsolete worktree only when its unique commits/evidence are preserved and no live
process or delivery depends on it; verify absence on disk and in the worktree list.

Publishing methods does not reload running sessions. Send affected leads the actual revision
and applicability boundary on their recorded route. At a safe boundary they read the affected
methods and report actual adoption or a concrete conflict in the existing return/notebook.
Do not migrate by resend, restart or reloading every run, and do not create an ACK registry.
An unresolved migration concern blocks only the dependent new effect.

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

State the session mode and owned scope, pause state, actual DM/Root route, changes published,
observed progress versus still-unverified adoption, and the next action or actual dependency.
Do not claim live adoption from source publication or scientific completion from dispatch.
