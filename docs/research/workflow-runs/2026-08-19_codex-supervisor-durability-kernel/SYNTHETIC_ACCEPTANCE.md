# Durability Kernel V1 Synthetic Acceptance

Accepted capabilities after the REVISION_REQUIRED corrective slice:

```text
single transition kernel
single mutating session owner
effect journal
at-most-one automatic attempt
caller-exhaustive EffectSubmissionResult handling
atomic domain/effect write-start and confirmation
CommandGateway via TransitionKernel
legacy mutation-intent writes disabled
Observer/App Server read-backed reconciliation and operator resolution
pre-write binding/actor eligibility fence
static guard zero-violation package scan
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
