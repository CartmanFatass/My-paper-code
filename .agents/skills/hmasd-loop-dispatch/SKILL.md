---
name: hmasd-loop-dispatch
description: "Use when a DM handles a peer event, updates shared coupling records, integrates accepted work or owns a vacancy handoff."
---

# Peer DM event handling

Read docs/project/PEER_DM_COORDINATION.md and live .codex/hmasd-dm-sessions.toml. Clerk is retired.
Each DM owns its full direction and records; there is no standing event coordinator. On a real
event, resolve the exact owner/decision/revision, perform the next authorized consequence and
update owned fields in the common record. Send only affected peers an actionable App message.
No ACK, integration or file-list permission gate. Native specialists retain existing batch rules.

A completed object is not a direction stop. DM chooses useful next work or records reasoned
PARK/CLOSE with knowledge handoff. The departing DM owns vacancy follow-through or transfers it
to an accepting peer. An orphan vacancy can be claimed by an active DM using the common-record
transaction before Send. Count occupied plus reserved to three. Fourth-slot stop does not stop
third-slot replacement. Preserve exact request/full answer and latest PARK reasoning for Portfolio;
relevant DMs own direct scientific dialogue. Do not recycle unchanged advice through new tasks.

DM integrates its accepted commits under shared main transaction ownership and preserves others'
work. Record real pending producers and next owner/action, not empty intentions. Routine results,
repair, lifecycle and archive events stay in records/direct peer messages, not Root reports.
Only user-requested reports or a concrete user choice outside delegation reach Root. No new
polling service, permission tier, automatic scientific verdict or unconfigured heartbeat coverage.
