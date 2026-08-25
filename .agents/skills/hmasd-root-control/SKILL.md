---
name: hmasd-root-control
description: Reconcile HMASD work from the permanent Root task, including user-authorized material decisions.
---

# HMASD Root Control

Root has the highest operational capability. It reconciles, creates or resumes
manager tasks when their durable scope requires it, validates archives, and
integrates Git. Within user authorization Root may form a material Portfolio,
scientific, or engineering decision, but records it in the correct existing
Markdown authority heading as `Decision owner: <identity>`, using existing
heading/path/hash refs. JSON writers remain domain writers; the runtime actor
comes from sender/session. Writer ownership is not a runtime role.

## One bounded wake

1. Read durable authorities, referenced Work Packets, effect/run/worktree facts,
   Git, and reconstructable runtime task references.
2. Run `reconcile --once`: at most one bounded action for each runnable
   direction. Serialize the same scope/target/authority revision; unrelated
   directions may proceed in parallel within capacity.
3. Use or create the matching independent Portfolio, EM, or CM task only when
   its defined condition holds; reuse a parked identity and report duplicates.
4. Transfer cross-task work only by an immutable Work Packet with authority
   refs and revisions. Delivery is at-least-once for the same `work_id` and the
   receiver must intake it idempotently. Do not generate a new packet for the
   same authority revision. Completion, waiting, and failure update the
   referenced existing authority or result; they are not packet states.
5. Perform only Root-owned runtime, archive, and mechanical Git effects. Root
   never edits an integration conflict.

## Effects and failures

An unknown run, send, or push is observed, never replayed. A local failure is
limited to its scope: new evidence may form a new Work Packet, while unrelated
directions continue. Do not use bare `BLOCKED` as control state or apply a
global recovery budget. Runtime maps are reconstructable caches, not identity
authority.

Path tier policy only classifies and records paths; it does not create an
approval service or widen `allowed_paths`. Root requires the one user
confirmation bound to an exact shared-core action before that effect. The
existing Markdown confirmation records Action digest, Base SHA, sorted exact
paths, objective/non-goals, and allowed Git effects. Root canonicalizes those
fields as JSON and checks its SHA-256 before execution and again before commit;
after the candidate SHA exists, append its result ref to that confirmation.

An implementation folder name may differ from its direction ID. Ownership comes
from the Work Packet's exact `owned_paths` and authority refs, not folder names;
path policy only classifies those paths.

Use every genuine registered leaf only when it materially helps; all are direct
leaves and may not delegate.
