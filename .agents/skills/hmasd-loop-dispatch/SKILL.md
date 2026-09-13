---
name: hmasd-loop-dispatch
description: Use when HMASD Clerk checks direction progress, processes a DM/Portfolio boundary, integrates results, recovers unfinished management or fills a formally vacated slot.
---

# HMASD research dispatch

Root is the user entry; the independent Clerk performs only delegated mechanical coordination.
Read docs/project/CLERK_OPERATIONS.md for event handling and writes. DM/Pro retain scientific
judgment. Clerk routes missing science or complex engineering repair to the relevant Astra DM;
it never turns a helper failure into a scientific stop or adds a Root ACK gate.

Clerk is an event-driven lightweight recorder/integrator and Portfolio-boundary scheduler. DM owns a direction's
research plan, execution, specialist children, intake and next decisions. The independent persistent
Portfolio Pro session owns the overall plan; Clerk coordinates its new requests from DM proposals. ROOT_OPERATIONS.md owns
the direction-management contract; SIBLING_COMMUNICATION.md and .codex/hmasd-dm-sessions.toml own
native versus independent-task routes. Four occupied directions and actual advancing work are
reported separately. Owner pause is checked first; governance/migration does not resume research.

## One changed-event pass

Run on an actionable DM message or formal Portfolio return. An enabled owner-authorized heartbeat
is only a missed-event/interruption recovery backstop, not the normal progress mechanism.
For independent tasks use compact wait_threads snapshots/cursors; expand one affected read_thread
only for missing evidence. Native children return to their actual DM; Clerk does not poll handles.

1. Apply owner boundaries and reconcile any undelivered migration/handoff event. Read current
   ownership, not historical task IDs. Do not create a second executor for accepted work.
2. Integrate ready accepted commits/evidence and update existing tracking/root-log only for changes.
   Deduplicate events by direction, assignment and evidence revision; message delivery and completed
   follow-through are distinct. DM completed-intake events deliver new results without waiting for a scheduled pass.
3. Evaluate the actual next boundary using the table below. Resume the same idle DM only for
   unfinished execution or management, through its registered task route. A DM already progressing
   owns its next steps without Clerk ACK, integration or per-step dispatch.
4. Apply formal Portfolio/owner lifecycle decisions. Recount occupied/reserved slots; first use a
   complete conforming Portfolio plan that already selects/funds a replacement and initial assignment.
   Reserve the released slot and create that DM without asking the same question again. Only an
   unresolved replacement choice/investment needs a bounded Portfolio request. Preserve pending
   request/reservation identities; no local science selection or inferred object-ending vacancy.
5. When a real planning/management event occurs, assemble the changed DM proposals and current
   overall-plan/portfolio references into the next Portfolio agenda. Clerk owns new Portfolio
   Transport/full-plan recording; Pro selects the plan. Release the next queued agenda when the
   binding clears. Do not wait for a vacancy to plan, for every DM to finish, or approve experiments.
6. End the event pass after useful work. Independent DMs keep their own execution turns and
   specialist waits; Clerk need not wait for all of them. While a bounded migration test or Clerk's
   own Transport is outstanding, use the relevant supported wait. No unchanged status broadcasts,
   repeated audit requests, per-DM timers or Relay service.

## Next boundary

| Observation | Action |
| --- | --- |
| Accepted/standing object delegation covers the useful object and remaining budget | DM selects and completes implementation, proportional checks/review, exact publication, fresh admission, detached launch/Monitor, collection/intake and authorized continuation. No repeat Portfolio vote. |
| Next decision changes direction-tier science | DM develops the concrete proposal and uses its Innovator/Convergence node. No Clerk scope approval. |
| No executable continuation/real producer; capacity/lifecycle is unasked | DM assesses surviving options and submits its proposal to Clerk for the overall Portfolio agenda. A no-addition scientific answer does not decide unasked occupancy. |
| Real accepted request/handle/review/resource producer | DM names owner/identity/event and waits after independent work. Clerk records it as actual work. |
| Explicit Portfolio/owner deferral/disposition already covers the boundary | Apply its scope/capacity treatment and revisit condition/owner. End unnecessary agent waiting; report non-advancing honestly. |
| Complete bound Pro answer with unresolved receipt metadata | DM intakes the full answer; Transport reconciles the same request. Metadata does not erase a formed decision. |
| Technical defect or unhandled management returned again | Repair the actual assignment/context/route or shared dependency, not identical reminders forever. No local scientific stop or extra invocation follows. |

A new title/date is not a new scientific question. Compare decision scope, options and consequences:
reuse complete prior answers; obtain an unasked management decision without inventing fresh results.
Portfolio questions request a usable selection and application mapping, not mere observations.
If the posed capacity/lifecycle question remains unanswered, return that specific omission to the
same node; an explicit conforming deferral does not trigger another identical consultation.

An ACTIVE-idle report with no producer and no decided deferral is unfinished direction management.
Neither the finite object nor the direction's slot is released. Resume its DM with the missing
management deliverable; do not invent a research object or choose PARK locally. A final ends a
Codex turn/assignment, not the direction. Independent task final text is collected by Clerk or
explicitly sent cross-task when actionable; native parent delivery does not apply across tasks.

Use the same authoring checkout/branch; Clerk owns main/index and integrates named accepted commits.
Keep one overlapping writer, preserve frozen science/caps and uncertain external effects, and
push each ready commit. CM/Implementer assignments remain suspended; independent high-risk review
and direct DM engineering remain under ENGINEERING_SCOPE_SPEC §7.
