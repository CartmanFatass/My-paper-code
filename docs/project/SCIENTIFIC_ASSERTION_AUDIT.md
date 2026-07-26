# Pro-assisted scientific assertion audit

```text
purpose=prevent_wrong_scientific_assertions
scientific_acceptance_owner=external_pro
code_acceptance_owner=project_manager
external_scientific_authority=exclusive_within_user_goal_and_review_boundary
audit_model=two_stage_triggered
review_stack=false
backward_compatibility=false
evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md
code_science_audit_mode=contract_diff_only
code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
new_algorithm_design_during_code_audit=forbidden
new_evidence_search_during_code_audit=forbidden
```

This workflow protects conclusions, not engineering completeness. External Pro
owns scientific decisions; Project Manager owns code decisions. The two stages
inspect different objects and do not duplicate acceptance: Pro accepts the
scientific contract and its code-science correspondence, while PM accepts
implementation correctness and operability.

Each stage must pass the PM workflow value test: name the false scientific
assertion it can prevent and confirm that its complete packaging, waiting,
repair and compute cost is smaller than the implementation or experiment waste
it avoids. When a direct proof-sized diagnostic is cheaper and preserves the
same scientific safety, use the diagnostic. Review availability is not itself
a reason to add a review.

## When it triggers

The design stage triggers before freezing a new conclusion-bearing contract
that creates or changes any of the following:

- estimand, benchmark source, positive/negative control or null;
- reward, credit, gradient path, initialization or causal mechanism;
- normalization, threshold, confidence procedure or result branch;
- checkpoint/sample/exclusion/seed selection that could change the result;
- the interpretation connecting an intervention or behavior to a capability.

The code-science stage triggers after integration and before formal compute when
code newly realizes or materially changes one of those claim-bearing elements.
It does not trigger for pure operational repair, logging/schema mechanics,
performance-preserving kernels with an appropriate oracle, or an exact contract
and commit already audited. If a repair changes only one stage, repeat only
that stage.

## Stage A: design assertion audit

Project Manager first tries to falsify the draft without training:

1. Evaluate every learning signal at the forced initial state and establish a
   live gradient path for every claimed trainable component.
2. Write the relevant optimal-policy set. A positive control is valid only when
   every optimal solution needs the target behavior; merely allowing that
   behavior is insufficient.
3. Construct a witness for each gate and branch. Confirm the gate can fail for
   its intended reason and that a correct expected mechanism can pass its
   threshold. Check every denominator for zero.
4. Confirm the planned probe distinguishes a working mechanism from a broken
   one despite initialization, masks, saturation and clipping.
5. Freeze every result-sensitive choice before observation: final checkpoint,
   normalization, clustering/unit of analysis, confidence procedure, sample
   exclusion, seed block and first-match precedence.
6. Ask which load-bearing decision the contract makes without explicitly
   asking. Do not turn a PM-written uncertainty into external authority by
   repetition.
7. Apply the evidence-complexity gate before design freeze: state `H`, fixed
   `K_search`, hypothetical-transition upper bound and projected wall clock.
   Reject nested rollout/replanning, horizon-growing enumeration or search
   above `O(H*K_search)`, `K_search<=16` and `16*H` hypothetical transitions
   per controller episode. A violation is `NON_EXECUTABLE_EVIDENCE_DESIGN`,
   not a scientific result.

Then Project Manager packages one `DESIGN_ASSERTION_AUDIT` question. Pro receives
the draft design, current scientific principles, relevant evidence and exact
repository paths. Ask Pro to seek counterexamples and missing decisions, not to
confirm the plan. Pro freezes the scientific distinction and required
properties; PM owns the cheapest bounded controller, witness, diagnostic and
other implementation realization inside
`docs/project/EVIDENCE_COMPLEXITY_POLICY.md`. PM archives the raw answer and
implements its exact scientific disposition. PM may ask a focused clarification
or report a code-side
infeasibility, but it cannot select among scientifically different answers.
Final freeze occurs only after Pro resolves or explicitly scopes out the
scientific defects.

Before implementation starts, PM performs an alignment read from the code side.
If the Pro disposition is ambiguous in code, structurally unreachable,
internally inconsistent with the named implementation surface, or contradicted
by a concrete code-level counterexample, PM sends one
`IMPLEMENTATION_ALIGNMENT_CLARIFICATION` in the same review lineage. State the
exact objection and the one scientific invariant that needs clarification; do
not ask Pro to design a solver or evidence search and do not select a scientific
option locally. Pro clarifies or corrects the scientific disposition. A real
scope expansion returns to the user.

The audit may be a compact section in the design/reconciliation; it does not
require a separate internal reviewer, approval file or checklist artifact.

## Stage B: code-science alignment audit

After PM implementation acceptance:

1. Run the proof-sized focused checks and one bounded exercise when a
   runner/analyzer path is material.
2. Push one exact commit containing the design and implementation.
3. Author a `CODE_SCIENCE_ALIGNMENT_AUDIT` question naming the reviewed design,
   implementation, runner/analyzer, focused evidence and the exact diff/base
   boundary. Instruct Pro to read those paths directly from the remote commit.
4. Ask only whether the code instantiates the scientific contract, whether a
   test/probe could pass through the wrong mechanism, and whether an alternate
   implementation explanation could change the registered conclusion.

This is a read-only conformance diff, not another design stage. Pro returns
exactly one of `ALIGNED`, `MISMATCH` or `SCIENTIFIC_AMBIGUITY`. `MISMATCH` must
name the exact frozen assertion and exact conflicting code path or behavior.
`SCIENTIFIC_AMBIGUITY` must name one previously unstated result-changing choice.
Neither output may introduce an algorithm, controller, solver, search,
threshold, evidence volume or experiment that was absent from the frozen
contract.

Do not ask for style, architecture taste, broad refactoring, coverage,
compatibility or generic bug hunting. PM remains the code acceptance owner;
Pro owns only whether that accepted code is scientifically aligned. PM executes
the smallest repair implied by an in-scope mismatch and reruns the smallest
affected evidence. At most one correction-only recheck may inspect the repaired
claim-bearing diff; it cannot reopen design. An unchanged reviewed commit is
never resubmitted and there is no review of the review.

## Result intake

Before scientific interpretation, PM mechanically checks in this order:

1. artifact/source/runtime closure and operational validity;
2. access and identifiability branches before behavioral branches;
3. actual optimizer-step exposure and whether behavior left initialization,
   not merely whether gradients or parameters were nonzero;
4. exact budget/code/branch scope of any historical evidence invoked;
5. exact registered first-match branch reproduction.

PM then submits a `FORMAL_RESULT_SCIENTIFIC_DISPOSITION` boundary to Pro. Pro
owns the smallest unit retired, retained mechanisms/lemmas, CDC/portfolio
change, excluded interpretations and next scientific action. The frozen
registered branch is never rescued after observation. Pro may narrow future
interpretation but cannot relabel a valid completed result.

## Evidence economy and automatic continuation

Be strict only where an error could create a false scientific assertion:
degenerate signals/nulls, mismatched controls, non-identifying sources,
intervention-to-natural leaps, result-sensitive post-selection and branches
that answer a different claim. Recoverable engineering detail gets the smallest
focused proof and does not block research.

Choose actions in the order derivation, counterexample, existing-evidence
analysis, toy, bounded prototype and formal compute. Use a cheap measurement
before arguing about a causal explanation. Failed directions retain the
smallest scientific record; obsolete apparatus is deleted and Git history is
the archive.

An exact small-N simulator may retain dense physical pair calculations as a
reference, but it is not a scalable deployment claim. A dynamic-agent algorithm
must target bounded-neighborhood `O(N*k_neighbor)` or hierarchical
`O(N*logN)`. Sparsifying or approximating the physical model changes science and
therefore returns to Stage A instead of being hidden as a performance repair.

An experiment operator terminal return or naturally completed Pro response
wakes Project Manager. With an active grant, no live owned operation and no real
authority blocker, PM either executes the exact Pro-selected action or opens the
smallest missing Pro scientific decision; it never fills that decision locally
or ends in an idle gap.
