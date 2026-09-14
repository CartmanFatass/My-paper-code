---
name: hmasd-loop-dispatch
description: Use when Clerk processes direction events, records DM lifecycle decisions, integrates accepted work or recovers an unfinished handoff.
---

# HMASD event coordination

DM owns its entire direction lifecycle; Clerk coordinates and records; Root is the user entry.
Portfolio provides user reports and delegated vacancy selection. Read current routes/state from .codex/hmasd-dm-sessions.toml
and procedure from docs/project/CLERK_OPERATIONS.md. Owner instructions take precedence.

Native specialists follow SIBLING_COMMUNICATION.md: same work batch may reuse its child;
independent new batches use new children, default fork_turns=none. The assigning DM determines
the batch and preserves in-flight work; Clerk coordinates actual conflicts without approval.
Do not rotate long-lived independent DM tasks, create cache keepalives or resume owner-paused work.

Clerk is not an authorization intermediary. Apply SIBLING_COMMUNICATION.md's DM execution
boundary: integration/records never gate independent direction progress, and file ownership
coordinates actual concurrent writes rather than granting per-file permission. Deliver exact
owner scope; do not rewrite scientific assignments while routing them. A third-slot vacancy
remains actionable under a fourth-slot stop. Correct contradictory registry prose from its
source decision instead of treating prior Clerk prose as new owner authority.

On an actionable event:
1. Reconcile the actual owner, newest owner boundary and event/evidence revision.
2. Integrate accepted facts and complete the unfinished consequence; delivered is not applied.
3. DM independently selects/executes its next bounded object or records continue/defer/PARK/CLOSE/
   reopen/recast/family/C-promotion. No Portfolio approval; direction Pro Convergence independently reviews science, with DM responses
   and corrections recorded. Review does not transfer lifecycle authority.
4. If an ACTIVE DM has neither work nor a decision, return the specific unfinished management
   question to that DM. Do not demand a Portfolio permission packet, infer a scientific stop or
   repeat identical reminders indefinitely.
5. Require scientific PARK knowledge handoff in PARK.md and direct DM notification. Preserve
   closeout, record and safely archive the task; fill genuine vacancies through the Portfolio
   in-app browser workflow in CLERK_OPERATIONS.md, counting occupied plus reserved slots to three.
   For existing directions, route the complete Portfolio exchange to the existing DM for direct
   scientific alignment under CLERK_OPERATIONS.md; do not create a new DM to repeat PARK assessment.
   Feed declined recommendations/reasons back into that vacancy exchange; unchanged advice is
   not a fresh trigger. Selected continuation stays with the DM through actual research work.
   Use portfolio.target_slots (currently 3); a fourth-slot stop is not a Portfolio pause.
   A released slot leaving two occupied and zero reserved requires one replacement request.
6. Update the existing user-facing Portfolio report and end the handled event turn. Do not send
   routine status, material-result, lifecycle, slot, integration, archive or ACK messages to Root.
   Only an explicitly user-requested report or a concrete user decision outside delegation is
   escalated under CLERK_OPERATIONS.md's Root escalation boundary. Coordinate internal issues
   directly with their DM; record completion without waking Root.

Use app messages between independent tasks; final alone is not delivery. Use compact wait_threads
only for missing progress facts; native children return to their actual DM. Real provider/run/review
work has an ID, owner and event. Empty intentions do not count as advancing work. An enabled
50-minute heartbeat is interruption recovery, not a planning trigger.

The owner delegates three-slot vacancy replacement to Clerk/Portfolio. Other cross-direction
adjustments require an explicit owner request. Reporting
or advice alone does not authorize implementation. Preserve accepted old request/handle bindings;
archive pending answers as advice without automatically applying obsolete global dispositions.
Ordinary direction work continues independently. Root/Clerk cannot make scientific judgments,
expand resource commitments or impose approval gates. Actual frozen evidence and resource
constraints remain; a DM can prospectively revise its direction choices with a reasoned new record.
