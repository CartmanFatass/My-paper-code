# External Pro: G47 code-science alignment audit

```text
semantic_author=research_operations_manager
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_mode=read_only_contract_diff
round=20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit
audit_target_commit=744ebe8495c18a6e36e851da384ccd21351615e1
implementation_code_commit=744ebe8495c18a6e36e851da384ccd21351615e1
accepted_design_stage_commit=bcb494886e6fa9966a9a3c86e39fdd1af9851b81
accepted_design_source_commit=af7d6b1f1ad55f24e25202b39414203677a7813b
compute_budget=zero
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro, the exclusive scientific authority for this
bounded contract diff. Read only the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the exact `audit_target_commit`. Do not
implement, run tests or compute, edit CDC, authorize a run, select a successor,
reopen design, or reactivate G33. Stop after one scoped disposition.

## Exact question

Does the implementation at
`744ebe8495c18a6e36e851da384ccd21351615e1` instantiate the frozen G47
post-G46 structural deletion between:

- `NATIVE6_G31_RAW_NORM_SHADOW_BASELINE`, which retains the accepted G46 RAW
  actor, log_std, credit-baseline module, baseline optimizer exposure and
  baseline checkpoint state; and
- `NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE`, which removes the complete
  baseline-only module and state while retaining the actor path?

The intended treatment is exactly the causal-disconnection deletion identified
by the G47 design review. It is not a new credit rule, utility comparison,
learned scale, or alternate training algorithm.

## Frozen conformance points

1. Provenance and projection must bind the accepted G46 formal source,
   accepted aligned implementation and alignment stage. Both arms must start
   from one accepted G46 RAW branch-start state, copy actor/log_std bitwise,
   remain storage-disjoint, and consume zero model RNG during projection.

2. The reduced arm must genuinely remove the credit-baselines module, its
   true-state input consumer, forward/loss/backward/gradient path, optimizer
   membership and Adam state, liveness gate, checkpoint keys and output schema.
   No zero, constant, dummy, frozen or compatibility replacement may remain.

3. A static certificate must be reconstructed before any trajectory. Every
   baseline-to-actor, entropy, action/log-probability, checkpoint-selection,
   evaluation and source/lifecycle dependency count must be zero; shared
   actor/baseline storage and retained-gradient coupling must also be zero.

4. Actor optimizer factorization must preserve class, hyperparameters,
   retained parameter order, step counters, `exp_avg` and `exp_avg_sq`
   bitwise. There is no global clipping, joint normalization, loss-count
   scaling, scheduler, or global optimizer state.

5. Both arms must retain the accepted actor objective: target-only residuals
   `x_I=r_t` and `x_S=G_(t+1)`, separate channel centering, independent
   per-channel RMS scaling, literal `0.5*(g_I+g_S)`, and one common entropy
   term. The reduced replay schema contains no baseline output fields.

6. The proof-sized dynamic guard, when used, is only one accepted branch-start,
   one shared 8-episode by 48-step stored batch (384 real transitions), two
   PPO passes per arm, two actor optimizer steps per arm, zero bootstrap,
   `K_search=0`, zero hypothetical transitions, no nested rollout or
   replanning, and no formal statistical run. It must verify actor gradients,
   actor/log_std parameters, actor Adam state, pre-tanh means, actions,
   token/joint log-probabilities and canonical retained checkpoint bytes.

7. Artifact validation and reload must reject missing retained keys, extra
   baseline keys in the reduced arm, ordinal parameter remapping, synthesized
   baseline defaults and reference-only checkpoint selection evidence. The
   runner remains C++-backend required with no Python fallback, and its
   result-bearing lifecycle must remain fail-closed.

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
or `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY`

The response must contain all eight sections and exactly one disposition line.
If and only if the disposition is MISMATCH, include one concrete target-bound
counterexample and the smallest correction; do not propose redesign or compute.
