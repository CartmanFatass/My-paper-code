# Independent MARL constructive mathematical review

```text
review_mode=PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW
review_scope=one_exact_advisory_candidate_only
project_state_effect=none
code_authority=none
compute_authority=none
portfolio_ranking=forbidden
```

Review only the exact candidate and evidence contained in the submitted prompt.
Do not request another candidate, rank the portfolio, authorize implementation
or compute, or decide project adoption.

Return every heading exactly once.

### REVIEW_IDENTITY

Repeat the review and candidate identities.

### FORMAL_OBJECT_AND_ASSUMPTIONS

State the mathematical object, stochastic process, agent information and
strategic assumptions. Identify any undefined object.

### DERIVATION_AND_CAUSAL_PATH

Trace the proposed mechanism through information, action, credit and update
dynamics. Separate derivation from analogy.

### ESTIMAND_AND_IDENTIFICATION

Define the estimand, sampling or randomization unit and necessary identification
conditions.

### SIMPLE_NULL_OR_EQUIVALENCE

Give the strongest simple null, reduction or observationally equivalent account.

### COUNTEREXAMPLES_AND_BOUNDARIES

Give bounded counterexamples, failure regimes and non-transferable assumptions.

### COMPLEXITY_AND_INTERFACES

State required interfaces and whether evidence complexity remains bounded.

### IDENTIFYING_TOY

Specify the smallest non-executed toy design that separates the mechanism from
the strongest alternative. Do not authorize execution.

### CONSTRUCTIVE_CORRECTIONS_AND_INSPIRATION

Return exact bounded corrections and any source-bound scientific inspiration.

### RESIDUAL_UNCERTAINTY

List material unresolved limits.

### INDEPENDENT_RESEARCH_DIRECTION_PACKET

Return `review_mode`, `review_id`, `candidate_id`, `correction_count`,
`scientific_opportunity_count` and `formal_project_effect=none`.
