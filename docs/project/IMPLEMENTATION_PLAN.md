# Async commitment roster G3 information-gate plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hash handoffs
> are disabled.

```text
active_implementation=ASYNC_COMMITMENT_ROSTER_G3_INFORMATION_GATE
implementation_status=AUTHORIZED
design=docs/research/designs/ASYNC_COMMITMENT_ROSTER_G3.md
backend=cpu
torch_threads=1
formal_run_status=forbidden_for_this_gate
closed_G0_G1_G2_mutation=forbidden
backward_compatibility=not_required
```

## Goal

Build the smallest exhaustive source gate showing that a lifecycle-owned,
unordered roster of standing commitments can causally control an asynchronous
editor and complementary external utility. Retain TEAM_REC as a constructive
simpler explanation. This gate identifies a source boundary only; it cannot
support algorithm adoption or consume a conclusion-bearing iteration.

## Task 1 — Pure roster transition model

**Status:** pending.

Create one active-line module for anonymous active counts 2/3/4, lifecycle-owned
commitments, JOIN/RENEW/temporary absence/rejoin/terminal replacement, balanced
physical packing and exhaustive standing-roster permutations. The external
utility is the fraction of unique active commitments.

**Focused proof:** exact case balance; physical-slot invariance; terminal delete,
temporary freeze/rejoin restore and fresh JOIN ownership; no future/lifetime or
identity leakage; exact utility identity.

## Task 2 — Constructive controls and roster intervention

**Status:** pending.

Implement ROSTER_EDITOR, TEAM_REC_ORACLE, INDEPENDENT_EDITOR and SHUFFLED_ROSTER
as pure deterministic/enumerated controls. Snapshot before the edit, replace one
retained commitment, and verify the adapted roster choice and value consequence
under an otherwise identical continuation.

**Focused proof:** both constructive controls equal 1.0; nulls equal their
enumerated expectations and remain below 1.0 by active-count stratum; the
roster-only intervention changes the selected commitment and improves utility;
no primitive-logit, PPO, gradient or learned parameter path exists.

## Task 3 — Runner and bounded acceptance

**Status:** pending.

Add one `formal=false` runner and a focused test file. The runner writes the
fixed PASS/FAIL/INVALID result and compact deterministic telemetry. Run focused tests and one fresh CPU exercise
with one thread. Inspect exact ownership,
permutation invariance, intervention isolation, scalar loops and persistence.

**Acceptance:** focused tests pass; fresh artifact is nonformal; all exhaustive
references and metrics close; no temporary residue; no closed G2 import or
compatibility reader.

## Successor decision

After a pass, perform a zero-compute sufficiency audit. A learned G3 comparison
is admissible only if the gate yields a precise permutation-equivariant roster
editor versus matched TEAM_REC and independent/no-roster controls, with
held-out active-count/lifetime transport and label-invariant mediation. Freeze a
separate formal contract before using either remaining conclusion-bearing
iteration.
