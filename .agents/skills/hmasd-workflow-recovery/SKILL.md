---
name: hmasd-workflow-recovery
description: Classify and repair one observed HMASD workflow failure safely.
---

# HMASD Workflow Recovery

## Purpose

Give Root one bounded, materially distinct recovery route for a repeated
workflow failure while preserving each authoritative source. Recovery repairs
causal breaks; it does not replay unknown effects, reinterpret science, or
become a generic approval layer.

## Inputs

- Root's exact effect classification and observed failure: pure research,
  manager lifecycle, partial code/worktree, running or unknown run, memory,
  Git conflict/stale base, push outcome, external send, late result, runtime
  mapping, or Dashboard.
- The authoritative state path, revision/checkpoint/base SHA, logical identity,
  durable generation, process or Agentify operation reference, and compaction
  boundary when relevant.
- Ignored runtime-agent/worktree maps when present, the durable references from
  which they can be reconstructed, and all prior recovery attempts.
- The original assignment, affected direction/run/round identity, and safe route
  candidates.

The retired `runtime_agents` map is not recreated. Runtime task and worktree
references are Root-owned reconstructable caches under `.codex/runtime/`; a
legacy worktree journal is read/imported only after receipt and Git/path
validation, and it is never written back. Canonical-only state is valid, while
legacy-ahead or same-revision conflicting dual journals fail closed.

## Bounded cycle

1. At startup, resume, or a compaction boundary, reconcile durable state and
   revisions before effectful work. Revive a matching manager generation; if its
   ignored runtime mapping is missing, reconstruct that mapping once from the
   registry, worktree, task/runtime, and other authoritative references. Rotate generation
   only when durable state proves the current session untrustworthy.
2. Classify the effect before acting, read the authoritative source, and observe
   the newest checkpoint, process, remote SHA, or Agentify operation. Preserve
   original bytes. Reproduce a pure failure once only when doing so cannot repeat
   an unknown external effect.
3. Deduplicate prior attempts by failure identity, effect class, route, and
   authoritative revision/checkpoint. Choose the smallest safe materially
   distinct route and attempt it once. The budget is at most three materially
   distinct routes across Root wake-ups; repeated observations do not consume a
   new attempt and are never replayed as new work.
4. Apply the matching recovery-matrix route:
   - **Pure research task failed:** start a new assignment only after proven
     failure; old partial prose is evidence, not an accepted result.
   - **Manager missing after resume:** revive the matching logical identity and
     generation or reconstruct its runtime map once; never create a blind
     duplicate manager.
   - **Partial code work:** inspect patch and worktree state, then resume or retain
     it for recovery; never apply a patch twice.
   - **Run says RUNNING or has unknown outcome:** inspect PID identity, output,
     and manifest, observe or mark `UNKNOWN`, and never relaunch or start a
     successor blindly.
   - **Memory refusal:** reduce, batch, or shard; never ask the user to approve
     overcommit.
   - **Git conflict or stale base:** preserve the conflict and return to Root for
     a new integration plan; never auto-resolve scientific or semantic conflict.
   - **Push outcome unknown:** fetch and compare the remote tip before any push;
     never push again from an unknown outcome.
   - **External commitment unknown:** trust and observe the existing Agentify
     operation; never resend.
   - **Late specialist output:** compare generation and checkpoint, archive it as
     superseded evidence, and never overwrite newer accepted state.
   - **Dashboard failure:** restart the read-only derived service or continue
     without it; never block the workflow.
5. Reconcile the authoritative source after the one route. Return one precise
   resume condition, or, only after the deduplicated three-route budget has no
   safe route left, one precise exhausted user-visible blocker.

One Root wake-up permits one safe reproduction and one repair attempt. A new
wake-up or explicit user response is required for a different route; no polling
loop exists.

## State writes

- Write only the state owned by the repaired helper through its documented CLI
  and expected-revision CAS.
- Reconstruct ignored runtime maps from durable references without changing
  Portfolio, direction, run, external, or Git authorities.
- Record deduplicated materially distinct attempts in the relevant authoritative
  source; do not create a duplicate recovery ledger.
- Never mutate Agentify send state, scientific claims, accepted checkpoints,
  Portfolio lifecycle, or Dashboard snapshots. Runtime ownership may change only
  when runtime mapping is the explicit repair target.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-workflow-recovery-manager"` and
payload:

```json
{
  "kind": "recovery",
  "failure_class": "<research|manager|code-worktree|run|memory|git|push|external-send|late-result|runtime|dashboard>",
  "observed_refs": [],
  "attempts": [],
  "outcome": "RESUMABLE",
  "resume_condition": "<one exact condition or null>"
}
```

Use `outcome: "EXHAUSTED"` and `materiality: "USER"` only when every safe,
materially distinct route within the three-attempt budget is exhausted. Return
exactly one user-visible blocker that names the failure class, observed
authoritative references, attempted routes, and the user action that can resume
work.

## Failure handling

Preserve bytes on schema, version, revision, generation, or checkpoint conflict
and stop rather than guessing. A late result is read-only superseded evidence
until Root reconciles it. Unknown run state returns an observation condition
without relaunch; unknown external commitment returns an observation condition
without resend. A missing Reviewer, test, Dashboard, or Advisor result is an
evidence gap, not a recovery trigger by itself.

## Deletion condition

Delete this Skill when Root's native reconciliation and the helper CLIs provide
an equivalent one-reproduction/one-repair boundary with explicit resume and
exhaustion results and no separate recovery authority.
