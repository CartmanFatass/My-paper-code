# Independent MARL single-direction scientific audit

```text
review_mode=INDEPENDENT_RESEARCH_DIRECTION_AUDIT
review_scope=one_exact_advisory_candidate_only
project_state_effect=none
code_authority=none
compute_authority=none
formal_workflow_promotion=forbidden
portfolio_ranking=forbidden
global_winner_selection=forbidden
```

## Question

Audit only the candidate identified by `review_candidate_id` in the attached
mechanically generated direction packet. Determine whether its scientific
problem, mechanism and proposed validation are sufficiently defined to justify
advisory validation. Treat source results, Explorer inference and new mechanism
hypotheses as distinct evidence classes.

Do not request or assess the other portfolio candidates. A parent, sibling or
interface may be mentioned only when it is already present in the packet and is
necessary to state this candidate's boundary. Do not compare directions, rank
the portfolio, select a global winner, propose implementation, authorize
compute, interpret formal project state or decide project adoption.

## Exact evidence allow-list

- The attached `22_DIRECTION_INPUT.md`, including its identity manifest and
  candidate-bounded raw campaign records.

No repository path, project state, external source or unstated candidate is an
input. Evidence locators inside the packet are provenance records, not
permission to open their source files during this review.

## Required response

Return every heading below exactly once.

### DIRECTION_DISPOSITION

Exactly one of `VALIDATION_READY`, `REVISION_REQUIRED`, `PARK`, or `UNRESOLVED`,
with a concise reason.

### REVIEW_IDENTITY

Repeat the exact campaign ID, workflow commit and sole candidate ID.

### PROBLEM_FORMULATION

State whether the candidate names the relevant stochastic-control or MARL
problem precisely enough to test.

### MECHANISM_CAUSAL_PATH

Trace how the proposed mechanism changes state, information, action, credit or
updates and how that path could produce the claimed effect.

### RL_MARL_DRIVER

Assess the learning signal, exploration source, exploitation cost, temporal
process and strategic multi-agent dependence. Identify any missing driver.

### ALTERNATIVE_EXPLANATIONS

Name the simplest explanations that could reproduce the observation and say
whether the proposed comparisons separate them.

### IDENTIFICATION_AND_CONTROLS

Assess the estimand, sampling or randomization unit, matching, negative
controls, uncertainty and leakage boundaries.

### SOURCE_TO_MECHANISM_BOUNDARY

Separate source-supported facts, transferred primitives, Explorer inference
and untested new hypotheses. Do not upgrade a locator or author claim into
independent verification.

### INTERFACE_DEPENDENCIES

List only interfaces strictly required by this candidate. Do not review the
other direction behind an interface.

### REQUIRED_REVISIONS

Give exact bounded revisions and reacceptance conditions. Use `none` only when
the disposition is `VALIDATION_READY` and no material correction remains.

### VALIDATION_CONTRACT

State the minimum discriminating advisory validation, decisive observables,
failure interpretation and named simple fallback. Do not authorize execution.

### RESIDUAL_UNCERTAINTY

List unresolved scientific or evidential limits that remain after the proposed
validation.

### INDEPENDENT_RESEARCH_DIRECTION_PACKET

Provide a concise machine-readable block containing:
`campaign_id`, `workflow_commit`, `candidate_id`, `disposition`,
`required_revision_count`, `validation_status`, and `formal_project_effect=none`.
