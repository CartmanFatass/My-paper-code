# G49 single-channel structural-collapse code-science alignment audit

```text
semantic_author=research_operations_manager
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_mode=read_only_contract_diff
round=20260729_g48_duplicated_immediate_single_channel_collapse_code_science_alignment_audit
audit_target_commit=aa94030834ca161d6da4014210fd89b70cf2d40c
design_stage_commit=fc8288b53401cea1642110994305272905e56c5f
compute_budget=zero
submission_limit=exactly_one
recovery_submission_limit=zero
answer_now=forbidden
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External GPT-5.6 Pro, the exclusive scientific authority for this
bounded read-only audit. Read only the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the exact `stage_commit`. Do not run
tests or compute, edit code/CDC, reopen G48, propose a different treatment,
select a successor, or authorize formal/nonformal execution.

## Audit question

Does `audit_target_commit` implement the frozen G49 claim: the exact
structural collapse of `NATIVE6_G31_DUPLICATED_IMMEDIATE` to
`NATIVE6_G31_SINGLE_IMMEDIATE`, with no change to source, observation, reward,
environment, action distribution, optimizer, checkpoint selection, or G48
evidence semantics?

Check mechanically:

1. The reduced route removes only the second immediate target, normalization,
   loss, backward/gradient construction and duplicate-only diagnostics. It
   leaves the accepted G48 immediate target, normalization order and zero-scale
   law unchanged.
2. For every PPO pass, the actual reference bytes satisfy literal
   `0.5*(g_I1+g_I2) == g_I`, with entropy added exactly once in both routes;
   no removed operation consumes RNG, mutates buffers, fires a result-changing
   hook, changes scaling, or alters liveness gates.
3. Actor and log-std parameters, parameter order, Adam exposure and storage,
   Adam hyperparameters (`lr=1e-3`, `betas=(.9,.999)`, `eps=1e-8`, no weight
   decay/amsgrad), counters, moments and post-pass bytes remain equal for both
   PPO passes, with no clipping, minibatches or optimizer reset.
4. The inductive equality extends to actions, log probabilities,
   reward/roster/lifecycle traces and the canonical final actor checkpoint;
   `D_SC=0` is a structural equality claim, not statistical noninferiority.
5. The reduced artifact schema rejects second-channel fields, duplicate flags,
   route labels and dummy compatibility fields while comparing the canonical
   actor/log-std/Adam/update/source/final-checkpoint projection. No hidden
   second channel remains.
6. The accepted predecessor, native-six/no-carry actor, no baseline/no slow
   critic, common fast anchor, source ledgers, active masks, autoregressive
   prefix, member-owned action noise, PPO likelihood/clipping, entropy-once,
   final-only checkpoint and formal-authority gates are unchanged. The focused
   and protected regression evidence is only proof-sized and does not authorize
   a scientific run.

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
target-bound counterexample and the smallest correction. Do not propose
redesign or compute.
