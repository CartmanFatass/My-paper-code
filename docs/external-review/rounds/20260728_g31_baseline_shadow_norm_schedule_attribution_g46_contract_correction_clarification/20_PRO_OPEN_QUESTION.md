# External Pro: G46 contract-correction clarification

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=DESIGN_ASSERTION_AUDIT
round=20260728_g31_baseline_shadow_norm_schedule_attribution_g46_contract_correction_clarification
correction_only=true
design_audit_compute=0
prior_round=20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit
prior_stage_commit=8cb6fb8872e64c93f6d699ad24dd549704462aaa
```

You are External GPT-5.6 Pro, the exclusive scientific authority for this
focused contract clarification. Read only the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the pushed stage commit. The prior G46
question was submitted once and its archived response is a transport fact in
the allow-list. Do not resubmit that question, implement code, run proof,
nonformal or formal compute, edit CDC, or select a different successor.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_baseline_shadow_norm_schedule_attribution_g46_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`

## Clarification required before any G46 freeze

The archived G46 response identifies exactly two unresolved, result-sensitive
fields: the piecewise definition of `q_norm` and the unit-direction equality
tolerance. Resolve only those fields.

1. Give one unambiguous piecewise mathematical definition of `q_norm` with the
   exact numerator and denominator, the `m_B=m_raw=0` case, the `m_B=m_raw>0`
   case, the `m_B>0,m_raw=0` case, and all nonfinite/invalid cases. State
   exactly how the strict `q_norm > 1e-6` activation gate applies.
2. Give one exact unit-direction equality rule for nonzero assigned credit
   gradients: either a single numeric tolerance with its comparison operator
   and metric, or explicit exact bitwise equality. Do not provide alternatives
   or leave an inherited identifier unspecified.
3. Return exactly one terminal token:

```text
G46_CONTRACT_FROZEN
G46_CONTRACT_REMAINS_UNFROZEN
```

Return `G46_CONTRACT_FROZEN` only when both fields are fully closed and state
the smallest next boundary without redesigning the arms, estimand, margin,
branch order, or evidence volume. If either field remains underdetermined,
return `G46_CONTRACT_REMAINS_UNFROZEN` and name only the missing field.

This clarification authorizes no implementation, Git operation, nonformal
exercise, formal run, or scientific iteration.
