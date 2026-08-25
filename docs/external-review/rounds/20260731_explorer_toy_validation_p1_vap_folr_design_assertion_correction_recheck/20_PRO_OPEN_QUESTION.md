# External Pro open question: VAP-FOLR-CORE Gate item 3 correction recheck

```text
review_type=EXPLORER_TOY_DESIGN_ASSERTION_AUDIT
workflow_id=EXPLORER-TOY-VALIDATION-2026-07-31-P1
candidate_id=CAND-VAP-FOLR-CORE
candidate_contract_id=TOY-SCI-VAP-FOLR-CORE-P1-R1
source_review_round=20260731_explorer_toy_validation_p1_vap_folr_design_assertion_audit
evidence_tier=nonformal_toy
compute_budget=zero
scientific_iteration_cost=zero
cpm_dispatch_authorized=false
allowed_outputs=TOY_CONTRACT_FROZEN|ADVISORY_REFINEMENT_REQUIRED|PARK_CANDIDATE
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded correction recheck. Use the connected GitHub repository
connector for `https://github.com/CartmanFatass/My-paper-code.git`, branch
`aggressive`, and read only the exact evidence allow-list in
`01_SHARED_SOURCE_MANIFEST.md` at the pushed stage commit. Do not use a local
working tree, unlisted files or compute. Do not activate Answer now. Return no
Chinese summary.

Audit exactly one candidate: `CAND-VAP-FOLR-CORE`. The prior terminal
disposition was `ADVISORY_REFINEMENT_REQUIRED` because Gate item 3 lacked an
exact sixteen-row trace matrix. The refinement packet is the only proposed
change and is explicitly scoped to that gap. Verify mechanically whether it
now specifies all required row fields, exact boundary order, both in-flight
bindings, receipt/deadline semantics, held-out rows and reconciliation of the
original scenario labels. Do not redesign, add a candidate, compare
directions, alter the frozen contract, or infer a scientific result.

Return exactly one terminal lane:

```text
TOY_CONTRACT_FROZEN
```

or

```text
ADVISORY_REFINEMENT_REQUIRED
exact_gap=<one concrete missing or ambiguous contract item>
```

or

```text
PARK_CANDIDATE
reason=<one bounded reason>
```

Do not authorize code or compute, create a CPM assignment, schedule another
candidate or merge directions. Stop after this one zero-compute correction
recheck.
