# External Pro open question: UAV G0 code-science alignment

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_target_bound_conformance_only
compute_budget=zero
audit_target_commit=c4d54e54978d98430c22c2cf21b789dd73c72d52
implementation_code_commit=c4d54e54978d98430c22c2cf21b789dd73c72d52
readiness_execution_commit=e6d1794362015ad0d79c73f3df169c413e09497e
design_contract_stage_commit=8d171a1b63ff403f0cec7b0539c3894a0f4ba5cc
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded audit. Use the connected GitHub repository connector for
`https://github.com/CartmanFatass/My-paper-code.git`, branch `aggressive`, and
read only the allow-list in `01_SHARED_SOURCE_MANIFEST.md` at exact target
commit `c4d54e54978d98430c22c2cf21b789dd73c72d52`. Do not use a local working
tree, runtime logs, unlisted files, or compute. Do not activate Answer now.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md`
- `docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260730_uav_source_identifiability_g0_code_science_alignment_correction_recheck/21_PRO_OPEN_RAW.md`
- `ha_ctse_process/uav_source_identifiability_g0.py`
- `scripts/run_uav_source_identifiability_g0.py`
- `tests/ha_ctse_process_uav_source_identifiability_g0_test.py`
- `tests/run_uav_source_identifiability_g0_test.py`

Return exactly one of these tokens and no Chinese summary:

`AUDIT_DISPOSITION=ALIGNED`
`AUDIT_DISPOSITION=MISMATCH`
`AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY`

Use `ALIGNED` only when the exact target bytes remain a conformance
implementation of the frozen G0 contract. Use `MISMATCH` only with a concrete
target-bound conflicting path/symbol/behavior and the smallest in-contract
correction. Use `SCIENTIFIC_AMBIGUITY` only when an unstated result-changing
scientific choice prevents a conformance decision. Do not propose redesign,
new evidence, new thresholds, new compute, or a new controller.

Check these exact assertions:

1. In `Control.ORACLE` production execution, both EVENT and NO_EVENT construct
   the pre-action context before target selection, reconstruct target-owned
   internal positions/targets/active mask, freshly recompute common-transducer
   evidence for the exact raw action, and pass `oracle_ownership`,
   `oracle_pre_action_context` and `oracle_common_transducer_evidence` to the
   unchanged real `step_dense` S7-S1 guard. Storage/internal permutation
   checking remains explicit.
2. The selected Oracle behavioral branch uses the accepted tracker and frozen
   tie/ownership semantics, preserves R=273 for registered episode 0 and
   R=NONE for NO_EVENT, and introduces no new controller, heuristic, metric,
   seed, or result-bearing path. Separate behavioral replay certificates are
   compared independently and missing or tampered certificates fail closed.
3. The indexed production regression exercises Oracle EVENT and NO_EVENT through
   `run_g0_episode`, verifies branch-aware certificates and the episode-0 causal
   values, and keeps lifecycle, tracker, ownership and qualification counters
   at their frozen zero values.
4. Result-bearing CLI/readiness fields remain mechanical identity and artifact
   gates only: explicit external-user-grant reference, formal-root identity,
   failed-root/schema binding, source/execution identity and exact token remain
   required; formal and scientific compute remain closed until an independently
   aligned binding exists.

Do not reopen the G0 design or merge G51. Stop after this single scoped
disposition.
