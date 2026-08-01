# External Pro open question: VSP-ASYNC-ESCROW exact-gap recheck

```text
review_type=EXPLORER_TOY_DESIGN_ASSERTION_AUDIT_RECHECK
workflow_id=EXPLORER-TOY-VALIDATION-2026-07-31-P1
candidate_id=CAND-VSP-02
candidate_contract_id=TOY-SCI-VSP-ASYNC-ESCROW-P1-R1
assignment_identity=round=20260801_explorer_toy_validation_p1_vsp_02_design_assertion_recheck_v6|question=docs/external-review/rounds/20260801_explorer_toy_validation_p1_vsp_02_design_assertion_recheck_v6/20_PRO_OPEN_QUESTION.md
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

The prior v5 audit returned exactly one gap: the sixteen Stage-A labels did not
freeze, per row, the initial escrow and immutable record, exact physical and
arrival times and UUIDs, ordered receipts, expected state transitions and
reward ownership, release_count, and terminal status. The attached refinement
packet claims to materialize that matrix as T01-T16, with explicit isolated
frame branches for T16 and no paper-evidence claim.

Audit only whether that exact refinement closes the prior gap while preserving
the candidate direction and all previously frozen semantics. Check that all
sixteen original labels remain exactly once and in order; each row is
implementable and contains the required state, event, receipt, timing, reward
ownership, release-count and terminal fields; duplicate/replay/version,
watermark, interruption and censoring behavior remain explicit; T07 covers the
complete equal-time precedence; T14/T15 are the only zero-release rows; and
T16 keeps its two isolated representations without creating scientific
evidence. Do not add requirements outside the prior gap and do not redesign the
mechanism.

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

Do not authorize code or compute, create a CPM assignment, schedule VSP-05,
compare directions, merge candidates, or interpret a toy result. Stop after
this one zero-compute exact-gap recheck.
