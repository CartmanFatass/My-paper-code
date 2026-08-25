# Durability Kernel V1 Synthetic Acceptance

Accepted capabilities after the third REVISION_REQUIRED corrective slice:

```text
single transition kernel
single mutating session owner
effect journal
at-most-one automatic attempt
caller-exhaustive EffectSubmissionResult handling including adoption
atomic domain/effect write-start, confirmation, and PREPARED cancellation
no domain-only wake claim API
operator TURN_OBSERVED completion uses EFFECT_CONFIRMED or matching OPERATOR_RESOLVED
WakeRecovery.resume_once semantic actor fence
atomic owner+effect prepare; missing owner cannot submit
stored-only resume evidence must be after this write claim
CommandGateway via TransitionKernel
legacy mutation-intent writes disabled
Observer/App Server read-backed reconciliation without domain-only fallback
pre-write eligibility fence on managed-turn, wake, provisioning, and recovery resume
static guard AST/SQL allowlist
doctor reports actual scanner results
```

Absent capabilities:

```text
live App Server acceptance
Stage 5 DAG
automatic approvals
write-capability profiles
additional managed actor kinds
distributed workflow engine
Agents SDK
```

Hard gate: do not resume Stage 5 feature work until an independent synthetic
disposition accepts this kernel. Live Phase 1 / Stage 3 / Stage 4 acceptance
is a later gate. Missing live artifacts are not code defects.
