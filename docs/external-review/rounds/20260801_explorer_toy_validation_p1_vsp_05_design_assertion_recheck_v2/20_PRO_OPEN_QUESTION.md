# External Pro open question: VSP-SEMANTIC-HANDOFF exact-gap recheck

```text
review_type=EXPLORER_TOY_DESIGN_ASSERTION_AUDIT_RECHECK
workflow_id=EXPLORER-TOY-VALIDATION-2026-07-31-P1
candidate_id=CAND-VSP-05
candidate_contract_id=TOY-SCI-VSP-SEMANTIC-HANDOFF-P1-R1
assignment_identity=round=20260801_explorer_toy_validation_p1_vsp_05_design_assertion_recheck_v2|question=docs/external-review/rounds/20260801_explorer_toy_validation_p1_vsp_05_design_assertion_recheck_v2/20_PRO_OPEN_QUESTION.md
evidence_tier=nonformal_toy
compute_budget=zero
scientific_iteration_cost=zero
cpm_dispatch_authorized=false
allowed_outputs=TOY_CONTRACT_FROZEN|ADVISORY_REFINEMENT_REQUIRED_WITH_ONE_EXACT_GAP|PARK_CANDIDATE
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded candidate-scoped recheck. Use the connected GitHub repository
connector for `https://github.com/CartmanFatass/My-paper-code.git`, branch
`aggressive`, and read only the exact evidence allow-list in
`01_SHARED_SOURCE_MANIFEST.md` at the pushed stage commit for this package.
Do not use a local working tree. Do not activate Answer now.

The prior audit identified one gap only: the pre-code Stage-A gate had 23
trace-family labels and separate M01-M16 attribution cases, but they were not
reconciled into one exact finite matrix with per-row initial FSM/ledger/epoch
state, observation and event order, expected gate/residual/handoff actions and
counts, terminal state, and fixed H and K for an O(H*K) audit.

The attached refinement claims to close exactly that gap by freezing H=23,
K=16, 368 fixed applicability cells, one row for every original trace-family
label in original order, explicit M01-M16 attribution coverage, state/action
counts and terminal outcomes, and isolated control/negative branches.

Audit only whether this refinement closes the prior gap without changing the
candidate direction or adding a mechanism. Check exact 23-row order, complete
M01-M16 coverage, per-row initial state and ordered events, expected gate,
residual, handoff and action counts, terminal state, fixed H/K, and the
O(H*K) bound. Ensure safe/unsafe cases are semantically assigned rather than
covered by unrelated rows; controls and post-latch/invariance rows must not
be treated as new scientific candidates. Do not compare candidates, reopen
VAP/VSP-02, authorize code or compute, or interpret toy results.

Return exactly one terminal lane and no additional summary:

```text
TOY_CONTRACT_FROZEN
```

or

```text
ADVISORY_REFINEMENT_REQUIRED_WITH_ONE_EXACT_GAP
exact_gap=<one concrete missing or ambiguous contract item>
```

or

```text
PARK_CANDIDATE
reason=<one bounded reason>
```

Stop after this one zero-compute exact-gap recheck.
