---
name: hmasd-workflow-recovery
description: Classify and repair one observed HMASD workflow failure safely.
---

# HMASD Workflow Recovery

## Purpose

Give Root's recovery manager one bounded, materially distinct recovery route
for a repeated workflow failure while preserving each authoritative source.
Only Root invokes and owns this recovery manager; EM, CM, BrowserTransport,
Dashboard, and helpers neither acquire recovery authority nor form a second
control plane. Recovery repairs causal breaks; it does not replay unknown
effects, reinterpret science, or become a generic approval layer.

## Inputs

- Root's exact effect classification and observed failure: pure research,
  manager lifecycle, partial code/worktree, running or unknown run/result,
  memory, Git writer conflict/stale base, push outcome, external send,
  BrowserTransport runtime mapping, late transport or specialist result,
  invalid PARKED lifecycle, or Dashboard.
- The authoritative state path, expected revision/checkpoint/base SHA, logical
  identity, durable requester generation, process identity or exact Agentify
  operation reference, provider conversation reference, and compaction boundary
  when relevant.
- Current OMP runtime agent/worktree maps, including a missing
  `BrowserTransport` row when observed, and the durable references from which
  an ignored row can be reconstructed.
- The original assignment, affected direction/run/round/transport identity,
  current requester generation, and all prior recovery attempts.

## Bounded cycle

1. At startup, resume, or a compaction boundary, reconcile durable state,
   expected revisions, OMP runtime maps, and generations before effectful work.
   Revive a matching manager generation; if its ignored runtime mapping is
   missing, reconstruct that mapping once from the registry, worktree, Hub, and
   other authoritative references. Rotate generation only when durable state
   proves the current session untrustworthy.
2. Classify the effect before acting, read the authoritative source, and
   observe the newest checkpoint, process identity, remote SHA, OMP runtime
   mapping, or exact Agentify operation. Preserve original bytes. Reproduce a
   pure failure once only when doing so cannot repeat an unknown run, result, or
   external effect.
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
   - **BrowserTransport runtime row missing:** recover the singleton logical
     identity `BrowserTransport` with agent type `hmasd-browser-transport` once
     from current OMP runtime maps, exact Agentify operation refs, and the bound
     provider conversation. Reconcile the reconstructed row before use; never
     create a second transport, invent a provider binding, or send during this
     repair.
   - **Partial code work:** inspect patch and worktree state, then resume or
     retain it for recovery; never apply a patch twice.
   - **Run or result says RUNNING or has unknown outcome:** inspect the exact
     process identity, output, manifest, and accepted-result refs, then observe
     or mark `UNKNOWN`; never relaunch the command, start a successor, or
     recreate a result while run/result state is unknown.
   - **Memory refusal:** reduce, batch, or shard; never ask the user to approve
     overcommit.
   - **Git writer conflict or stale base:** freeze both writer phases, preserve
     the exact allowlist/base/conflict evidence, and return to Root for a new
     integration plan. Fail closed without applying or pushing; never
     auto-resolve scientific/semantic conflict, rebase, or transfer writer
     authority across the stale handoff.
   - **Push outcome unknown:** fetch and compare the exact `omp/workflow` remote
     tip before any push; never push again from an unknown outcome.
   - **External commitment unknown:** observe the same exact Agentify operation
     and bound provider conversation; never resend, create another operation,
     or substitute a fresh conversation.
   - **Transport tuple `VERIFY_COMMITMENT + UNRESOLVED + OBSERVE_ONLY +
     SEALED`:** observe that same operation and conversation. It never
     authorizes activation, prompt change, or replacement operation.
   - **Late transport or specialist output:** compare requester generation and
     checkpoint. A transport result for a stale requester generation is
     superseded evidence: retain its exact refs read-only and never overwrite
     the newer requester's state.
   - **Invalid PARKED direction:** `PARKED` without a non-null
     `reactivation_condition_ref` is invalid. Preserve bytes and return the
     exact registry/revision conflict to Root; never reinterpret it as
     `CLOSED`, reactivate it, or refill its capacity.
   - **Dashboard failure:** restart the read-only derived service or continue
     without it; never block the workflow or treat Dashboard output as
     authority.
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
  Portfolio, direction, run, external, provider-conversation, or Git
  authorities. A BrowserTransport row repair records runtime liveness only.
- Record deduplicated materially distinct attempts in the relevant
  authoritative source; do not create a duplicate recovery ledger.
- Never mutate Agentify send state, scientific claims, accepted checkpoints,
  Portfolio lifecycle, PARKED reactivation conditions, or Dashboard snapshots.
  Runtime ownership may change only when runtime mapping is the explicit repair
  target.

## Returned result envelope

Return the common v2 envelope with `role: "hmasd-workflow-recovery-manager"` and
payload:

{
  "schema_version": 2,
  "role": "hmasd-workflow-recovery-manager",
  "logical_identity": "hmasd-workflow-recovery-manager",
  "generation": 1,
  "assignment_id": "example-recovery-assignment-001",
  "status": "COMPLETED",
  "materiality": "LOCAL",
  "summary": "Observed a resumable recovery condition.",
  "changed_paths": [],
  "state_refs": [],
  "artifact_refs": [],
  "checkpoint_sha": null,
  "decision_requests": [],
  "next_actions": [],
  "payload": {
    "kind": "recovery",
    "failure_class": "runtime",
    "observed_refs": [],
    "attempts": [],
    "outcome": "RESUMABLE",
    "resume_condition": null
  }
}
```

Use `outcome: "EXHAUSTED"` and `materiality: "USER"` only when every safe,
materially distinct route within the three-attempt budget is exhausted. Return
exactly one user-visible blocker that names the failure class, observed
authoritative references, attempted routes, and the user action that can resume
work.

## Failure handling

Preserve bytes on schema, version, revision, generation, requester generation,
checkpoint, PARKED reactivation, writer-phase, or base conflict and stop rather
than guessing. A stale-generation result is read-only superseded evidence until
Root reconciles it. Unknown run or result state returns an observation
condition with no relaunch. `VERIFY_COMMITMENT + UNRESOLVED + OBSERVE_ONLY +
SEALED` returns an observation condition for the same operation and never
activates again. A missing Reviewer, test, Dashboard, or Advisor result is an
evidence gap, not a recovery trigger by itself.

## Deletion condition

Delete this Skill when Root's native reconciliation and the helper CLIs provide
an equivalent one-reproduction/one-repair boundary with explicit resume and
exhaustion results and no separate recovery authority.
