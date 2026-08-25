# External Pro: G42 code-science alignment audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
round=20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_code_science_alignment_audit
audit_target_commit=43df85e9ebf384f0baf6d44758ef62aeb5e7fe7b
implementation_code_commit=43df85e9ebf384f0baf6d44758ef62aeb5e7fe7b
design_source_commit=da113117d2b1988d859b1ad6161533b0c176d5dd
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_INDEX.md
frozen_contract=docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/21_PRO_OPEN_RAW.md
compute_budget=zero
nonformal_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro acting only under `.agents/roles/EXTERNAL_PRO.md`.
Inspect the exact pushed audit target and the complete allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. This is a read-only code-science conformance
diff. Do not edit or accept code, run compute, reopen design, or reactivate
G33.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/CURRENT_WORK.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_CODE_SCIENCE_INDEX.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_direction_balance_attribution_g42_design_assertion_audit/01_SHARED_SOURCE_MANIFEST.md`
- `ha_ctse_process/continuous_roster_native_six_g31_direction_balance_attribution_g42.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_direction_balance_attribution_g42_test.py`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`

## Conformance question

Does the accepted implementation at `43df85e9ebf384f0baf6d44758ef62aeb5e7fe7b`
instantiate the exact G42 design contract at
`da113117d2b1988d859b1ad6161533b0c176d5dd` without any result-changing path?

Check each point mechanically against the named implementation, tests, index,
and frozen design evidence:

1. The accepted G41 no-slow projection and the three manifest-backed G40 common
   fast anchors (replicates 0|1|2, source commit
   `97a8b237e0cec6c2713dd2a710d324040fa3dfc2`) remain the sole branch-start
   provenance. No random reinitialization or alternate anchor is introduced.
2. The `NATIVE6_G31_DB_NO_SLOW` arm preserves the registered G31
   direction-balanced actor-gradient composition bitwise, while the
   `NATIVE6_G31_NO_DB_NO_SLOW` arm changes only angular composition.
3. The NO_DB arm receives only the two already-formed raw-sum gradient streams
   and the registered scalar global gradient norm. It must not read, rebuild,
   or use the DB direction as a vector or hidden control.
4. Global actor-step scale, zero-gradient handling, cancellation handling and
   non-scale-match handling are frozen and fail closed before any Adam step;
   there is no channel fallback, perturbation, or cancellation-as-evidence path.
5. The realized-successor target, immediate/successor decomposition, shared
   true-current-state two-output baseline, independent channel normalization,
   native-six actor/log_std, source, reward, lifecycle, trajectories, PPO
   exposure, optimizer inventory, paired RNG ownership, and checkpoint rule
   remain unchanged between arms except for the direction composition.
6. Baseline updates, serialized diagnostics, branch order, absolute-access and
   policy-support gates, and final-only checkpoint semantics remain aligned;
   no runner or evidence-volume change silently broadens the claim.
7. The focused tests and code-science index provide direct evidence for the
   above, and no test fixture succeeds through a result-changing mechanism.

The allowed disposition is exactly one of:

```text
AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY
```

`ALIGNED` requires every frozen point to conform. `MISMATCH` requires the exact
frozen assertion, conflicting path/behavior, and smallest in-contract
correction. `SCIENTIFIC_AMBIGUITY` is reserved for a previously unstated
result-changing scientific choice that prevents conformance judgment.

Do not propose a new algorithm, threshold, evidence volume, experiment, or
formal run. Stop after the single scoped disposition.
