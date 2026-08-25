# External Pro: G51 phase-A shadow-baseline module reduction code-science alignment audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
round=20260729_g31_phase_a_shadow_baseline_module_reduction_g51_code_science_alignment_audit
stage_commit=4b605ff64a4624e838092c10c2fc2b536c34eaae
audit_target_commit=4b605ff64a4624e838092c10c2fc2b536c34eaae
design_stage_commit=fb16a412841ad69912d927262dae8f694ea5471a
compute_budget=zero
nonformal_compute_started=false
formal_compute_started=false
answer_now=forbidden
```

You are External GPT-5.6 Pro and the exclusive scientific authority for this bounded read-only conformance diff. Read exactly the paths in `01_SHARED_SOURCE_MANIFEST.md` from `stage_commit`. Do not edit or accept code, run tests or compute, reopen G51 design, authorize a formal run, edit CDC or select a successor.

## Alignment question

Does the accepted implementation at `audit_target_commit` instantiate the frozen G51 design assertion, without a result-changing path? Judge only the exact G51 source, runner, tests, code-science index and allow-listed predecessor evidence.

Check mechanically that:

1. The reference arm retains the accepted G50 Phase-A shadow-baseline apparatus while the reduced arm physically removes only the phase-A `credit_baselines` module and every baseline-only true-state consumer, target/loss, parameter/gradient/Adam/optimizer membership, diagnostic and checkpoint/schema path. No replacement baseline, critic, filler, compatibility field, learned scale or entropy/normalization change is introduced.
2. Both arms start from one complete fresh G50 null initialization with storage-disjoint copies; actor/log_std bytes, actor parameter names/shapes/order/trainable masks and projection state are identical; projection consumes zero model RNG and zero optimizer steps. The actor objective, entropy, source ledgers, paired trajectory/action noise, phase boundary/reset and G49 single-immediate Phase-B route remain unchanged.
3. The reduced actor-only path does not accept or read critic/baseline state; no baseline value can enter actor credit, entropy, action/log-probability, checkpoint selection, evaluation or result selection. Reference actor parameter ordering is the accepted G50 actor prefix; reduced ordering is the same prefix; extra reference parameters are baseline-only and actor Adam hyperparameters/step exposure remain equal.
4. The dependency, autograd and optimizer-order certificates are derived from actual modules/parameters and actual kernels, not caller-authored booleans. The same stored 8x48 Phase-A batch is used for both arms when a dynamic witness is required; the witness is bounded by 384 real transitions, two PPO passes per arm, two actor optimizer steps per arm, four total steps, zero bootstrap, zero Phase-B optimizer steps, and no formal/statistical run. Phase-B equality is established by an actual zero-step G49 gradient/Adam factorization or an equivalent exact certificate, not by absence of evidence.
5. Final evidence rejects deleted reduced-baseline residue, partial/one-arm updates, unknown exceptions and forged success flags; it serializes only the four allowed first-match dispositions. C++ CPU backend identity, no-Python-fallback, fresh-root and exact artifact/checkpoint schema guards are fail-closed. Formal admission remains blocked until this independent audit supplies a matching ALIGNED stage and a later bound runner commits it.

If any point is not aligned, return the exact frozen assertion, conflicting path/behavior and smallest in-contract correction. Do not propose a new algorithm, threshold, evidence volume, experiment, formal run or successor.

Return exactly one terminal disposition token and no alternate token:

```text
AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY
```

`ALIGNED` requires every point to conform. `MISMATCH` requires the exact frozen assertion, conflicting path/behavior and smallest correction. Use `SCIENTIFIC_AMBIGUITY` only for a previously unstated result-changing choice that prevents judgment.
