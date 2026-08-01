# Independent MARL adversarial scientific review

```text
review_mode=PRO_ADVERSARIAL_SCIENTIFIC_REVIEW
review_scope=one_exact_revised_advisory_candidate_only
constructive_correction_disposition_required=true
project_state_effect=none
code_authority=none
compute_authority=none
portfolio_ranking=forbidden
```

Review only the exact revised candidate and constructive-correction disposition
contained in the submitted prompt. This is a new scientific audit, not a closure-only check.
Do not request another candidate, rank the portfolio,
authorize implementation or compute, or decide project adoption.

Return every heading exactly once.

### REVIEW_IDENTITY

Repeat the review, candidate and revised-advisory identities.

### CORRECTION_DISPOSITION_AUDIT

Assess whether applied, rejected and parked constructive corrections are
scientifically coherent without treating conformity as acceptance.

### CONFOUNDS_AND_LEAKAGE

Attack information leakage, target leakage, support mismatch and uncontrolled
confounds.

### CAPACITY_AND_OPTIMIZER_EXPOSURE

Test whether capacity, parameter exposure or optimization alone explains the
claimed effect.

### TEMPORAL_AND_RECURRENCE_FAILURES

Challenge recurrence, delayed credit, renewal and history dependence.

### PARTNER_COADAPTATION_AND_GAME_EFFECTS

Challenge partner adaptation, equilibrium selection and strategic dependence.

### ALTERNATIVE_EXPLANATIONS_AND_CONTROLS

Name the strongest remaining alternatives and minimum separating controls.

### VALIDATION_CONTRACT

State the smallest non-executed validation contract and decisive observables.

### RESIDUAL_UNCERTAINTY_AND_NEW_OPPORTUNITIES

List unresolved risks and any new bounded, source-linked scientific opportunity.

### DIRECTION_DISPOSITION

Exactly one of `VALIDATION_READY`, `REVISION_REQUIRED`, `PARK`, or `UNRESOLVED`.

### INDEPENDENT_RESEARCH_DIRECTION_PACKET

Return `review_mode`, `review_id`, `candidate_id`, `disposition`,
`required_revision_count`, `scientific_opportunity_count` and
`formal_project_effect=none`.
