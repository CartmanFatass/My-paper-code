# Decision ledger — template

One ledger per contract, alongside it. Copy this file, keep the header, replace
the example row.

## Why the three axes are separate

The first version of this ledger had one field with values
`accepted / modified / rejected / open`. That overloads three unrelated things —
**who decides**, **where the decision is in the workflow**, and **what was
ruled** — and the external ruling required them split.

The concrete failure it caused: a decision the Project Manager made under its own
authority was observationally identical to one still waiting for scientific
authority. Both read as `open`. So the standing sweep for protected choices with
no ruling could not tell a pending decision from one that had silently bypassed
the reviewer, which is the exact class the ledger exists to police.

| Axis | Values | Means |
|---|---|---|
| `authority` | `PROTECTED_PRO`, `PM_ENGINEERING` | who is entitled to decide it |
| `state` | `DISCOVERED_UNTRIAGED`, `AWAITING_PRO_RULING`, `DECIDED`, `DEFERRED_OUT_OF_SCOPE`, `BLOCKED_UNRESOLVED`, `SUPERSEDED` | where it is |
| `ruling` | `ACCEPTED`, `MODIFIED`, `REJECTED` | what was decided, where applicable |

A Project Manager decision is `PM_ENGINEERING` + `DECIDED`. It is **never**
recorded as a reviewer acceptance.

## Fields

| Field | Content |
|---|---|
| `id` | stable; referenced by findings, questions and certificates forever |
| `protected_object` | estimand, threshold, branch, data split, policy snapshot, comparator, measure |
| `authority` / `state` / `ruling` | the three axes above |
| `alternatives` | what was considered |
| `smallest_consequence` | what reversing it changes — a quantity, a branch, or a proposition |
| `evidence_paths` | contract, code, source, counterexample |
| `implementation_binding` | the concrete symbol or function |
| `ruling_source` / `ruling_artifact` / `revision` | who ruled, in which archived reply, at what revision |
| `depends_on` / `affects` | other decision ids |
| `re_review_trigger` | what change reopens it |

## Rules that make it load-bearing

**No generic open entry may remain when a gate closes.** Implementation may begin
past a deferral only when it is `DEFERRED_OUT_OF_SCOPE`, has no implementation
binding on the current path, cannot change the current claim, and carries an
explicit `re_review_trigger`.

**Always blocking**, whatever the schedule pressure: an unresolved estimand,
probability or credit factorization, branch meaning, threshold, support, measure,
comparator, data split, snapshot, or source-identifiability decision.

**Every `PM_ENGINEERING` classification must state why reversing it cannot change
a registered quantity, branch, comparator or proposition.** The classification is
a claim, and an unjustified one is how a protected decision gets made quietly.

**Standing sweep** for the adversarial reader: flag a protected decision routed to
`PM_ENGINEERING`; a `PM_ENGINEERING` decision whose smallest consequence reaches a
branch; any `DECIDED` entry with no ruling artifact; and any protected choice
present in the contract or code with **no ledger entry at all**.

## Certificate voiding

Any change **by any actor** to a protected decision, its implementation binding,
or a bound evidence artifact voids the affected certificate — including a Project
Manager amendment to a nominally engineering choice, when it changes a bound
runtime observable. The earlier reviewer-only rule was too narrow.

Invalidate the transitive closure over `depends_on` / `affects`, and **fail
closed**: if impact cannot be localized confidently, void the whole gate
certificate rather than guessing at scope.

## Example row

```yaml
id: G20R2-014
protected_object: epsilon_audit -- Stage A resolution floor
authority: PROTECTED_PRO
state: SUPERSEDED
ruling: REJECTED
alternatives:
  - pre-registered scalar constant measured before the anchor exists
  - in-situ replicate-split null at the fast anchor
  - cross-replicate action-effect energy with no floor at all
smallest_consequence: >
  Decides the Stage A branch directly. The measured floors (0.051, 0.035) were
  the same order as the identification quantities they gated (0.005, 0.042).
evidence_paths:
  - docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md
  - scripts/calibrate_epsilon_audit_g20r2.py
  - docs/external-review/rounds/20260725_g20r2_prefreeze_grill/21_PRO_OPEN_RAW.md
implementation_binding: stage_a_source_effect(epsilon_audit=...)
ruling_source: external_pro
ruling_artifact: 20260725_g20r2_prefreeze_grill/21_PRO_OPEN_RAW.md
revision: 2026-07-25
depends_on: [G20R2-002]     # Stage A estimand definition
affects: [G20R2-021]        # Stage A branch selection
re_review_trigger: >
  Any change to the suffix replicate count, the K-action centering rule, or the
  audited policy snapshot.
```

That row records a decision that was **rejected outright**: the floor was replaced
by a cross-replicate estimator that needs no floor. It is kept rather than deleted
so the alternatives, and the reason the obvious one failed, survive — a later
reader who proposes a scalar floor should find out here that it was tried.
