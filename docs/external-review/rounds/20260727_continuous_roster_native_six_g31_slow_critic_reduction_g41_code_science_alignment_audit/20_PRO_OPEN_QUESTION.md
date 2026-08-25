# External Pro: G41 code-science alignment audit

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=dedc8bfa9d4054e55a06bdd8ed8f637142e55ea7
implementation_code_commit=dedc8bfa9d4054e55a06bdd8ed8f637142e55ea7
accepted_design_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_g31_slow_critic_reduction_g41_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SLOW_CRITIC_REDUCTION_G41_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/project/CURRENT_WORK.md`
- `docs/report/ITERATION_31.md`
- `ha_ctse_process/continuous_roster_native_six_g31_slow_critic_reduction_g41.py`
- `tests/ha_ctse_process_continuous_roster_native_six_g31_slow_critic_reduction_g41_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`.
Inspect the exact pushed audit target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. The G41 index is navigation, not a substitute
for reading the named implementation and focused test.

## Question

Does the accepted implementation at `dedc8bfa9d4054e55a06bdd8ed8f637142e55ea7`
instantiate the frozen G41 post-anchor comparison between `NATIVE6_G31_FULL`
and `NATIVE6_G31_NO_SLOW`, with no result-changing alternate mechanism?

Check only these conformance points:

1. The projection is from one accepted G40 common native-six anchor, preserves
   actor/log-std/shared-baseline tensors bitwise, is storage-disjoint, consumes
   no RNG, and removes every standalone slow-critic module, parameter, output,
   optimizer and Adam-state key without adding a replacement.
2. The static certificate reconstructs actual module, parameter, checkpoint,
   optimizer, output-schema and bytecode dependencies and proves zero
   standalone-slow reads into actor, shared baselines, G31 targets,
   normalization, direction balance, PPO, action/prefix, checkpoint,
   evaluation and RNG paths.
3. Retained credit is exactly G31: detached immediate `r_t-b_I`, detached
   realized-successor `G_{t+1}-b_S`, `gamma=.99`, terminal zero, no slow-value
   input, one normalization before both PPO passes, and unchanged source,
   action, lifecycle and no-carry semantics.
4. FULL and NO_SLOW call the identical retained actor/head objective, gradient
   assignment, parameter order, and two-step Adam kernel; FULL alone performs
   a separate slow-return update. Retained parameters and actor/head Adam
   state must be bitwise equal to each other and to accepted G40.
5. Deployment/evaluation exposes actor diagnostics only: actions, prefix,
   token log-probability, inactive zeros, no-carry hidden zeros, reward,
   roster and lifecycle traces must satisfy the frozen exact/tolerance gates.
6. The projected checkpoint must bind the exact accepted G40 source and full
   common-anchor digest, contain only retained state, and reject any slow key.
7. Any dynamic guard is bounded to one C++-backed 8-episode x 48-step batch
   (384 real transitions), two PPO passes, `K_search=0`, no hypothetical
   transitions, no bootstrap and no formal/nonformal runner.

Determine whether malformed parameters, gradients, storage, RNG, checkpoints,
diagnostic fields or a hidden value proxy can bypass these gates. Do not assess
style, general quality, performance, workflow design, or unregistered scope.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the target instantiates the frozen contract
  and no indexed test/probe can pass a result-changing wrong mechanism.
- `AUDIT_DISPOSITION=MISMATCH` only with the exact frozen assertion and the
  conflicting code path or behavior, plus the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one previously unstated
  result-changing scientific choice that prevents judgment.

Do not implement, compute, redesign, reopen G40, or authorize a run. Stop
after the single scoped disposition.
