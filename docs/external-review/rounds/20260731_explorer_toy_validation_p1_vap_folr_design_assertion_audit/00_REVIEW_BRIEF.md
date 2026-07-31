# Explorer toy design-assertion audit: VAP-FOLR-CORE

```text
review_type=EXPLORER_TOY_DESIGN_ASSERTION_AUDIT
workflow_id=EXPLORER-TOY-VALIDATION-2026-07-31-P1
candidate_id=CAND-VAP-FOLR-CORE
candidate_contract_id=TOY-SCI-VAP-FOLR-CORE-P1-R1
candidate_index=0
evidence_tier=nonformal_toy
compute_budget=zero
scientific_iteration_cost=zero
cpm_dispatch_authorized=false
```

This package contains exactly one candidate. The other cohort units remain
queued and live; they are not evidence, controls, comparators or alternatives
in this review.

External Pro must decide only whether the exact pre-code gate named by the
candidate is sufficient to freeze one implementable, proof-sized, sixteen-
trace nonformal toy contract. Do not redesign the candidate, add code or
compute, compare directions, merge contracts, or issue a project result.

The only permitted terminal disposition is one of:

```text
TOY_CONTRACT_FROZEN
ADVISORY_REFINEMENT_REQUIRED
PARK_CANDIDATE
```

If refinement is required, name one concrete exact gap only. A frozen
disposition permits Operations to prepare a complete CPM assignment; it does
not itself authorize code or toy compute.
