# Durability Kernel V1 Synthetic Acceptance

Accepted capabilities:

```text
single transition kernel
single mutating session owner
effect journal
at-most-one automatic attempt
evidence-based reconciliation
terminal incidents
atomic one-shot operator resolution
fault-injection recovery of write claims
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
disposition accepts this kernel.
