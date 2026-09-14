---
name: hmasd-loop-dispatch
description: Use when Clerk processes direction events, records DM lifecycle decisions, integrates accepted work or recovers an unfinished handoff.
---

# HMASD event coordination

DM owns its entire direction lifecycle; Clerk coordinates and records; Root is the user entry.
Portfolio is a report for the user. Read current routes/state from .codex/hmasd-dm-sessions.toml
and procedure from docs/project/CLERK_OPERATIONS.md. Owner instructions take precedence.

On an actionable event:
1. Reconcile the actual owner, newest owner boundary and event/evidence revision.
2. Integrate accepted facts and complete the unfinished consequence; delivered is not applied.
3. DM independently selects/executes its next bounded object or records continue/defer/PARK/CLOSE/
   reopen/recast/family/C-promotion. No Portfolio approval; direction Pro Convergence independently reviews science, with DM responses
   and corrections recorded. Review does not transfer lifecycle authority.
4. If an ACTIVE DM has neither work nor a decision, return the specific unfinished management
   question to that DM. Do not demand a Portfolio permission packet, infer a scientific stop or
   repeat identical reminders indefinitely.
5. Record the DM's actual lifecycle and next condition. Report vacancies honestly; never
   automatically send a Portfolio request, create a replacement or revive another direction.
6. Update the existing user-facing Portfolio report and notify Root of material changes or a
   concrete user-control exception. Fact-only updates need no ACK. End the handled event turn.

Use app messages between independent tasks; final alone is not delivery. Use compact wait_threads
only for missing progress facts; native children return to their actual DM. Real provider/run/review
work has an ID, owner and event. Empty intentions do not count as advancing work. An enabled
50-minute heartbeat is interruption recovery, not a planning trigger.

Portfolio consultation/cross-direction adjustment requires an explicit owner request. Reporting
or advice alone does not authorize implementation. Preserve accepted old request/handle bindings;
archive pending answers as advice without automatically applying obsolete global dispositions.
Ordinary direction work continues independently. Root/Clerk cannot make scientific judgments,
expand resource commitments or impose approval gates. Actual frozen evidence and resource
constraints remain; a DM can prospectively revise its direction choices with a reasoned new record.
