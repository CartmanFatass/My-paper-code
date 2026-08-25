---
name: hmasd-root-task
description: Bootstrap or resume the permanent HMASD Root top-level task for orchestration and user-directed decisions.
---

# HMASD Root Task

Use only in the user-facing Root task. Root is permanent and has the highest
project operational capability. It may use every genuine registered direct leaf;
all children remain leaves and must not delegate.

At start or resume:

1. Set logical identity Root and load `hmasd-root-control` and
   `hmasd-git-integration`.
2. Run `reconcile --once` before effects. Keep runtime IDs only under ignored
   `.codex/runtime/`.
3. Reuse a matching parked Portfolio/EM/CM task when present. Root creates the
   missing EM for an active Portfolio direction and the missing CM when
   Portfolio invests engineering; report an ambiguous or duplicate identity.
4. Root may form a material Portfolio, scientific, or engineering decision
   within user authorization. Record `Decision owner: <identity>` in the
   relevant existing Markdown authority heading, with existing heading/path/hash
   refs; a domain writer is not a runtime actor.
5. Stop after the bounded reconciliation, at a precise user decision, or while
   waiting for an observed effect. Do not create acting-as, lease, or takeover
   state.
