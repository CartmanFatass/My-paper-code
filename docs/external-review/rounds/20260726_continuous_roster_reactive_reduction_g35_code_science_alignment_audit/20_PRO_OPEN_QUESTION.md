# External Pro open question: G35 code-science alignment

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=49b3ba9399b056bd601863d6b0f2305c222f1f66
implementation_code_commit=42b9f85a7820ec5f4a3a7507d3a4e644b27fbc56
index=docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md
frozen_contract=docs/external-review/rounds/20260726_continuous_roster_reactive_reduction_g35_design_assertion_audit/21_PRO_OPEN_RAW.md
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed audit target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. The index is navigation, not a substitute for
reading the named implementation.

Question: does PM's accepted implementation instantiate the exact G35-P0
matched REC-versus-CS carry treatment, shared current-state access,
fresh-paired exposure, G31 credit identity, G32/G34 source pairing, registered
estimands, 0.05 margin, whole-episode confidence procedure and first-match
semantics frozen in the design audit, without introducing an arm-specific
capacity, information, optimization, evidence or checkpoint route?

Check only these conformance points:

1. Identical state keys, shapes, trainable masks, parameter counts and
   initialization; one nonserialized carry constant; exact cell equations
   `u=GRUCell(x,e+c*h)` and `h_next=c*u`; CS storage always zero and REC
   lifecycle storage frozen/restored/deleted as specified.
2. Identical current fields, active-set context, anonymous routing, action
   prefix, tanh-Gaussian distribution, centralized critic and common
   zero-initialized current readout. Confirm no age, previous action, true time
   or current demand field is removed from CS.
3. Forced-initial equality and live-gradient audit for every registered group
   before an optimizer step; exact fresh seed blocks; materialization of both
   paired trajectories before either update; unchanged G31 immediate and
   successor credit; exact training exposure and final-only checkpoints.
4. Exact G32 capacity-8 fixed training source and G34-P0 paired fixed/random
   capacity 6/8/12 evaluation source; 33 cells per replicate; identical action
   streams; strict arm/mode/capacity checkpoint loading; zero evaluation
   updates; lifecycle and serialized trace recomputation.
5. Absolute access predicates, confident-failure predicates, learned gain,
   equal-capacity REC-minus-CS estimand, inclusive current-state 0.05
   noninferiority and strict recurrent-advantage comparisons; one whole-episode
   paired hierarchical bootstrap plan; exact first-match priority.
6. Whether malformed parameters, gradients, exposure, checkpoints, cells,
   episode identities, traces, resampling units or route labels can pass to a
   conclusion-bearing branch.
7. Zero-search complexity, exact 28,032-transition nonformal and
   1,069,056-transition formal inventories, 3,600 formal optimizer steps and
   the matching-preflight/formal-token gate. Do not evaluate style, general
   code quality or unregistered scientific scope.

The positive recurrent branch may support only a finite-budget inductive-bias
advantage; it may not be relabeled as task-level recurrence necessity.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the exact target instantiates the frozen
  contract and no indexed test/probe can pass through a result-changing wrong
  mechanism.
- `AUDIT_DISPOSITION=MISMATCH` only with the exact frozen assertion and exact
  conflicting code path or behavior, plus the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one previously unstated
  result-changing scientific choice that prevents conformance judgment.

Do not introduce or request a new algorithm, controller, solver, source,
search, threshold, evidence volume, experiment or formal run. Do not accept or
redesign PM's code. Stop after the single scoped disposition.
