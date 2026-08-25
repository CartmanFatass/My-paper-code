---
name: hmasd-em-direction-cycle
description: Run one bounded evidence-separated research cycle for one direction.
---

# HMASD EM Direction Cycle

## Purpose

Advance one `EM-<direction>` logical identity through research, divergent
external review, synthesis, and convergence while preserving the direction's
scientific authority. EM reports facts and inferences separately and requests
engineering through durable references rather than spawning CM directly.

## Inputs

- The registry entry and lifecycle decision for exactly one direction.
- `docs/research/candidates/<direction-id>/DIRECTION.md` and its SHA-256.
- The direction's `workflow/research/state.json` and current
  `workflow/external-review/index.json`.
- A frozen research question, evidence-set references, generation, and bounded
  parent assignment.

## Bounded cycle

1. Reconcile registry, direction science, research state, and external index;
   reject stale or cross-direction identity before dispatch.
2. Freeze question/evidence references and deterministic round identity. Dispatch
   two specialists by default, up to four only when the exact question justifies
   disjoint evidence work.
3. Collect local evidence, then run divergent Gemini and Pro review in parallel
   through the external-review Skill when requested. Keep provider results blind
   until local EM synthesis is complete.
4. Separate repository facts, external evidence, inference, and speculation;
   synthesize the direction and author a convergence prompt only after the local
   synthesis.
5. Update EM-owned research state and external pointers once. Every material
   return names `next_action.owner`: retain `EM` for further derivation or
   interpretation, use `CM` with a durable engineering scope/acceptance request,
   or use `TRANSPORT` with a frozen external-review target. EM requests these
   handoffs through durable references rather than spawning the next role.
   Return one material result.

One cycle has one frozen question/evidence set and one synthesis. A wake-up or
parent message is required for another round; no polling or unbounded specialist
fan-out is allowed.

## State writes

- Write direction science only through the assigned `DIRECTION.md` authority
  and only for an explicitly assigned scientific update.
- Write research actionability and active references only to
  `workflow/research/state.json` via the state CLI.
- Write external round pointers only to `workflow/external-review/index.json`
  after transport return; exact archive bytes remain Root-owned.
- Do not write Portfolio registry, engineering state, run manifests, or
  Agentify ledger state.
- At cycle completion, use the provisioned research worktree and Git Integration
  Skill to stage only assignment-owned direction paths, create/apply one commit
  as `em:<direction>`, fetch/compare, and push `omp/workflow`. Report stale base,
  dirty target, non-fast-forward, mixed ownership, or conflict to Root without
  resolving it.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-em"`, logical identity
`EM-<direction-id>`, and payload:

```json
{
  "kind": "em",
  "direction_id": "<direction-id>",
  "question_sha256": "<sha256>",
  "evidence_set_sha256": "<sha256>",
  "conclusion_refs": [],
  "engineering_request_ref": null
}
```

Use `materiality: "DIRECTION"` for a direction result and include checkpoint
SHA plus every changed/state/artifact reference needed for Root reconciliation.

## Failure handling

Preserve the frozen evidence identity. Do not merge a late response into a newer
checkpoint, reinterpret provider output, resend an operation with unknown
commitment, or silently convert speculation into a claim. Return `PARTIAL` for
an evidence gap, `BLOCKED` for a user boundary, and `FAILED` only for an observed
fault; missing review, test, Dashboard, or Advisor output remains fail-open.

## Deletion condition

Delete this Skill when an approved direction-scoped research manager owns the
same authorities, evidence separation, external handoff, and bounded cycle
without requiring a parallel workflow role or duplicate state.
