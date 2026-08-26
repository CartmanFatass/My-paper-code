---
name: hmasd-operations-manual
description: Use when the parked HMASD Workflow-Clerk receives one exact program-generated protocol defect or legacy incompatibility.
---

# HMASD Clerk Operations Manual

Accept only a program-produced defect with `failure_scope`, producing command,
field path, `ref=null|typed`, actual value/ref, expected contract, and
responsible owner.
Valid cases are an exact missing/mismatched field/ref, mechanically unroutable
legacy data, a conflict between exact facts, or a genuine decision explicitly
assigned to an owner.

Read only cited material. Preserve the original scope; state the missing or
conflicting fact and return it to Root. In v1 protocol recovery,
`responsible_owner` is fixed to Root: Clerk never changes it from a target or
prose. Then park.

Ordinary packets/returns, native create/send/wait, redelivery, fan-in,
`UNKNOWN` Effects, task identity conflicts, and Root/user overrides never wake
Clerk. Do not select an owner from prose, publish/dispatch/create/wait/retry,
write an authority, perform an Effect, or create a queue, record, gate, or
private state.
