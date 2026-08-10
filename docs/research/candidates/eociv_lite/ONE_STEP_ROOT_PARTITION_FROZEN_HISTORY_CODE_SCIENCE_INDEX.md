# EOCIV-B7 one-step root-partition frozen-history discriminator

`EOCIV-B7-ONE-STEP-ROOT-PARTITION-FROZEN-HISTORY-DISCRIMINATOR` is an
isolated ordinary-B package for `CAND-VAP-EOCIV-LITE@adversarial-revision-v8`.
It asks whether two exact four-way partitions of the same frozen 4x4
root-by-shock on-policy panel produce different immediate held-out
owner-correct semantics after one ordinary learner/Adam step per branch.

The implementation is
`experiments/candidates/eociv_lite/one_step_root_partition_frozen_history.py`;
the one-shot CLI is
`scripts/run_eociv_b7_one_step_root_partition_frozen_history.py`; focused
contract tests are in
`tests/experiments/candidates/eociv_lite/test_one_step_root_partition_frozen_history.py`.

## Protected executable binding

- Real `EocivSiblingRosterEnv`, legitimate actuation/action receipts, and
  `SEGMENT_LATCH_RNN` are used throughout.
- The learner is normalized terminal GAE (`gamma=0.99`, `lambda=0.95`) with
  external team reward, actor plus half-scaled critic loss, Adam at `3e-4`,
  unchanged parameter order/groups, and one joint global clip at `0.5`.
- One shared seed-`91030` initialization yields three separately retained
  24-update histories. Actor parameters, complete Adam state, counters,
  normalization declaration, RNG state, and structural manifests are retained
  as material state; digests are witnesses, not substitutes.
- Every history/profile panel is collected once from its immutable anchor. The
  16 complete real trajectories are frozen before eight exact anchor clones
  are formed. Clustered and Latin ensembles each use every trajectory exactly
  once, and each branch makes exactly one learner call and Adam update.
- Retained model artifacts contain only the unchanged anchor and eight final
  one-step endpoints per history/profile cell. There is no checkpoint
  selection and no learning after the branch step.
- Immediate CORRECT/SWAPPED evaluation reuses the registered realized natural
  shock and action-noise objects across anchor, all endpoints, and both arms.

The full activity identity is 918 unique complete episodes, 44,064 real
transitions and policy calls, 288 prefix episodes, 144 common-data collection
episodes, 486 evaluation episodes, 144 learner/trainer/Adam/clip calls, 288
physical trajectory references, and 576 learner-batch episode references. The
last count is deliberately two replay channels (actor and half-scaled critic)
for each of four physical trajectories in each of 72 branches; it must not be
collapsed into the physical-reference count.

## Artifact lifecycle and boundary

The CLI exposes `claim`, `train`, `evaluate`, `analyze`, `validate`, and the
composed `lifecycle` command. Every result-bearing phase refuses an existing
phase artifact. A technical-only exercise uses a smaller frozen plan, never
admits a scientific terminal, and cannot pass `validate --require-full`.

The exact terminal precedence is:

1. `B7_INVALID_OR_UNIDENTIFIED`
2. `B7_ROOT_SEMANTIC_EDGE`
3. `B7_GENERIC_OPTIMIZATION_ONLY`
4. `B7_ROOT_LOCAL_NULL`
5. `B7_HISTORY_MODERATED_OR_JOINT`

The result preserves all cell returns; grand/history/profile/root and
leave-one-profile/root-index aggregates; per-history variance contrast;
pre-step actor, half-scaled-critic and joint gradient geometry; exact/allclose
`.grad` fidelity; clip scale/fidelity; one-step Adam delta/projections; moment,
RNG, root, shock, trajectory, common-data, receipt and activity witnesses.

This package does not read or reconstruct any earlier-treatment artifact,
checkpoint, optimizer state, RNG state, seed, root, trajectory or result. No
terminal authorizes retry, rescue, sweep, added cells, C, formal compute,
promotion, retirement, or External Pro.
