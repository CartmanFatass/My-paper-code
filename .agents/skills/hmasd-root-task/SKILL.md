---
name: hmasd-root-task
description: Bootstrap or resume the permanent highest-capability HMASD Root task for orchestration and user decisions.
---

# HMASD Root Task

Use only in the permanent Root task. Root may use every genuine direct leaf;
children remain leaves and do not delegate.

On start or resume, set identity `Root` and load `hmasd-slice-interface`,
`hmasd-root-control`, and `hmasd-git-integration`. For inbound work, use the
slice interface rather than reconstructing topology from conversation.

Root holds the normal dispatch point and the runtime `tasks.json` CAS. It may
reuse/create a canonical parked manager identity only through Root control.
Record any user-authorized material conclusion under the correct existing
authority heading as `Decision owner: Root` (or its actual owner). An exact
user/Root override needs no Clerk acknowledgment: issue the operation's danger
warning and record the reason.

Workflow-Clerk is parked for an exact program defect or legacy conversion only;
it is never normal packet routing, return handling, native transport, or an
override gate. Do not create a second scheduler, authority, or permission
service.
