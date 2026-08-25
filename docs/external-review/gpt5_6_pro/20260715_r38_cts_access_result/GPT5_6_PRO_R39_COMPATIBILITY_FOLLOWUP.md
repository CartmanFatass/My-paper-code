# GPT-5.6 Pro Follow-up: Repair the R39 S7 Compatibility Boundary

Date: 2026-07-15

## Requested decision

Audit the repository facts below and return exactly one verdict:

```text
ACCEPT / MODIFY / RETIRE R39-S7 HMASD-compatible temporal decoupling
```

If the route remains viable, specify one executable two-stage design:

1. the smallest honest current-interface fixed-`k` HMASD positive-anchor gate;
2. the HMASD-native fixed-`k` versus per-agent KEEP/SET gate that may run only
   after that positive anchor exists.

Close the mathematical and implementation ambiguities listed below. Give one
next causal edge and one abandonment branch per stage. Do not propose parallel
routes.

## Corrections to the previous response

The previous response assumed a final 2.112M HMASD checkpoint. That checkpoint
does not exist. The useful historical `best_model.pt` was last saved at 1.760M
steps. Its old final-episode coverage was `0.9250`; `0.9639` is the mean of the
last three evaluation points, not the checkpoint metric.

More importantly, the historical checkpoint is not compatible with current
S7:

- historical stack: six agents, state 236, observation 252, action dimension 3,
  former load-balance S7 contract;
- current `config_1.py` S7-S1: eight agents, action dimension 4, Scenario-7
  interface v3 and the current QoS/safety environment contract;
- the checkpoint lacks current `policy_interface` / `training_interface`
  metadata and depends on removed `config_paper_adaptation.Config`;
- current `HMASDAgent.load_model` correctly rejects it;
- no current-interface positive fixed-`k` HMASD checkpoint is registered.

Therefore the old checkpoint may remain a historical access reference only. It
cannot initialize either R39 arm through partial or `strict=False` loading.

## Architecture mismatch to resolve

The repository's standalone R30 is not HMASD-compatible warm start:

- original HMASD high policy is Transformer `SkillCoordinator`, with
  `pi(Z|x) prod_i pi(z_i|Z,z_<i,x)`, team/agent value heads, and its own PPO
  optimizer;
- `FixedClockAREditPolicy` is a separate MLP over compact context, bridge,
  working roster, and age, with separate KEEP and skill heads plus a scalar
  high-check critic;
- its loader, optimizer, buffer, and trainer are different, and its
  `force_refresh_every_check` mode does not call the original HMASD joint
  assignment path;
- standalone R30 does not preserve the full original `q_D/q_d` update loop.

Commit `aaba845` has now fixed one prerequisite defect: PPO recomputation in
`SkillCoordinator.evaluate_training_batch` teacher-forces the stored
`Z,z_<i>` rather than newly sampling its conditioning chain.

The treatment must now remain inside the original HMASD trainer/collector and
reuse the same coordinator, low actor/critic, discriminators, normalizers,
checkpoint schema, update order, observation contract, and external reward as
the fixed arm. A disabled/full-refresh treatment must call the original joint
assignment path exactly.

## Questions that must be closed

1. **Positive source anchor.** With no compatible checkpoint, should Stage A
   train current-interface fixed-`k` HMASD from scratch? Freeze an exact budget,
   evaluation contract, access thresholds, and failure meaning. Distinguish a
   failed current substrate from a temporal-algorithm failure. Do not use the
   old 3D checkpoint as weights.
2. **Team `Z` lifetime.** In partial KEEP/SET checks, is `Z` held until an
   explicit full refresh, renewed every check, or replaced by a deterministic
   representation? State one choice and explain how it preserves the original
   `q_d(z_i|o_i,Z)` semantics without silently reinstating a shared lifetime.
3. **Exact action probability.** Define the behavior and PPO-replay
   factorization for the per-agent KEEP/SET sequence, including how an edited
   skill is scored conditionally on the incumbent roster and preceding edits.
   Sampling and recomputation must use the same stored sequence and support.
4. **Warm-start initialization.** Define how new KEEP/partial parameters are
   initialized so disabled/full-refresh mode is exactly original HMASD, while
   both experimental arms still have mechanism-matched parameter and optimizer
   exposure.
5. **Credit and clocks.** Define the block return/advantage, bootstrap,
   per-environment check clock, age reset on KEEP versus SET, episode/reset and
   rollout-boundary behavior, and recurrent hidden-state behavior on one
   agent's skill change.
6. **Smallest abandonment gate.** Specify M0 compatibility, positive fixed-arm
   access, async service noninferiority, and genuine desynchronization metrics
   with unambiguous confidence-bound directions. State the exact next action
   for each mutually exclusive outcome.

## Non-negotiable constraints

- No new toy or replacement environment and no ordinary-MAPPO prerequisite.
- No environment-specific intrinsic reward, potential shaping, S7 task field,
  goal/contact/distance/success input, or external-reward-derived auxiliary
  signal.
- No partial transplant of the old checkpoint, no standalone R30 treatment,
  no new sampled team latent, no new classifier, and no resurrection of retired
  R29--R38 reward/effect/benchmark routes.
- Do not solve missing compatibility by relaxing strict loading, changing the
  current environment interface, or calling two different high policies a
  matched temporal comparison.
- The historical HMASD run is reference-only. The actual causal comparator must
  be a current fixed-`k` HMASD arm from the same positive checkpoint and code as
  the treatment.
- A 320K treatment gate may establish mechanism only; it cannot establish full
  HMASD parity or a final paper claim.

## Repository files to inspect

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/ExpRecord.md`
- `docs/external-review/gpt5_6_pro/20260715_r38_cts_access_result/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260715_r38_cts_access_result/CORRECTION_RAW.md`
- `docs/external-review/gpt5_6_pro/20260715_r38_cts_access_result/DISPOSITION.md`
- `config_1.py`
- `hmasd/networks.py`
- `hmasd/agent.py`
- `hmasd/utils.py`
- `hmasd/ha_ctse.py`
- `ha_ctse_process/r30_fixed_clock.py`
- `ha_ctse_process/train.py`
- `train_multiproc_config_1.py`

Answer the requested decision directly. Separate repository fact from inference,
and provide one implementation-ready route rather than a menu.
