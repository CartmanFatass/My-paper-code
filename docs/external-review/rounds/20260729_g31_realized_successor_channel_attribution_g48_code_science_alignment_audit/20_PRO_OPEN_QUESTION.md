# External Pro: G48 code-science alignment audit

```text
semantic_author=research_operations_manager
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_mode=read_only_contract_diff
round=20260729_g31_realized_successor_channel_attribution_g48_code_science_alignment_audit
audit_target_commit=5e2ace7199970634d79219f2858bb53aabf5a57e
implementation_code_commit=5e2ace7199970634d79219f2858bb53aabf5a57e
accepted_design_stage_commit=35a924424f842699dd275949626ef568aee08a22
accepted_design_source_commit=9d5416d69051365e9da35e496949fabd8e9a1493
compute_budget=zero
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro, the exclusive scientific authority for this
bounded contract diff. Read only the paths in `01_SHARED_SOURCE_MANIFEST.md`
from the exact `audit_target_commit`. Do not implement, run tests or compute,
edit CDC, authorize a run, select a successor, reopen design, or reactivate
G33. Stop after one scoped disposition.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/external-review/rounds/20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_g31_realized_successor_channel_attribution_g48.py`
- `scripts/run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48_test.py`
- `tests/run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48_test.py`

## Exact question

Does the implementation at `audit_target_commit` realize the frozen G48
post-anchor comparison between `NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR` and
`NATIVE6_G31_DUPLICATED_IMMEDIATE`, with the sole treatment being the complete
realized-successor channel package?

Check only these target-bound invariants against the accepted G48 design and
the listed evidence:

1. Provenance binds the accepted G47 source, aligned implementation and stage;
   both arms start from identical actor/log-std state, empty identically
   configured actor Adam state, and disjoint storage.
2. The reference uses `x_I=r_t`, `x_S=G_(t+1)`, `G_H=0`,
   `G_t=r_t+0.99G_(t+1)`; the null separately materializes `r_t|r_t` and
   exposes no successor read into actor credit, scaling, checkpoint selection,
   evaluation or result selection.
3. Each channel is centered and independently population-RMS scaled once from
   the complete 384-row trajectory before both PPO passes; credit is literal
   `0.5*(g_1+g_2)` with common entropy added once; all registered actor groups
   are finite in both rows and live in at least one reference channel.
4. Reference-only activation reconstructs `q_target=RMS(z_S-z_I)` and
   complete credit-vector evidence, requires both strict `>1e-6`, treats
   direction distance as descriptive only, and rejects nonfinite or null-sourced
   evidence.
5. Both paired trajectories exist before either update, order is fixed and
   reverse-order proof preserves mate model/Adam/RNG bytes; two PPO passes,
   one actor Adam step per pass, no clipping/minibatches/optimizer reset,
   final-only actor checkpoints and C++ backend/no Python fallback remain bound.
6. Checkpoint reload and analysis fail closed on missing, extra, forged,
   wrong-route, wrong-seed or intermediate evidence; first-match outcomes and
   all registered access/component confidence predicates remain unchanged.
7. Formal entry remains closed until a later exact `ALIGNED` disposition and
   stage plus fresh same-source preflight; no scientific compute is authorized
   by this audit.

## Required response

Return these sections in order:

1. `CODE_SCIENCE_ALIGNMENT`
2. `FROZEN_CONTRACT_CONFORMANCE`
3. `CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE`
4. `MINIMAL_IN_CONTRACT_CORRECTION`
5. `PROTECTED_SEMANTICS`
6. `EVIDENCE_AND_COMPLEXITY`
7. `EXECUTABLE_BOUNDARY`
8. `中文简报`

Then return exactly one separate line:

`AUDIT_DISPOSITION=ALIGNED`
or `AUDIT_DISPOSITION=MISMATCH`
or `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY`.

The response must contain all eight sections and exactly one disposition line.
If and only if the disposition is `MISMATCH`, include one concrete
target-bound counterexample and the smallest correction; do not propose
redesign or compute.
