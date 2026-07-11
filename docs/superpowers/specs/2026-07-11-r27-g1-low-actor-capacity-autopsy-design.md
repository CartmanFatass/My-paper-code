# R27-G1 Low-Actor Capacity Autopsy Design

Date: 2026-07-11

Status: user-approved design; implementation and experiment launch are pending.

## 1. Decision To Support

R26-G1a failed its primary arm0 family gate: none of update 25, update 30,
or final produced a checkpoint PASS against the pre-registered held-out behavior
criteria. The next decision is not whether to add another discriminator or
intrinsic reward. It is:

```text
Does the current strict-HMASD MAPPO low actor have usable z_i-conditioned
control capacity that training failed to exploit, or does recurrent execution
wash out the existing skill FiLM path?
```

R27-G1 is a reward-off architecture autopsy. It separates structural capacity,
recurrent-state washout, missing specialization pressure, and diagnostic
invalidity before any actor redesign or forcing objective is authorized.

## 2. Evidence And Causal Position

The active R25/R26 low actor is not skill-blind. It is:

```text
MLPBase(o_i) -> skill FiLM(z_i) -> GRU -> continuous action head
```

At the R26 dimensions it has hidden size 256, four individual skills, four
continuous action dimensions, 558,344 actor parameters, and a 2,560-parameter
pre-GRU skill FiLM. The actor hidden state is reset at episode reset, not at an
ordinary individual skill renewal. A newly selected skill therefore inherits
hidden state accumulated under previous skills.

R26-G1a established that naturally assigned labels do not leave a sufficiently
strong held-out behavior signature. It did not distinguish:

1. the architecture can express skill-conditioned actions, but sparse task
   training gives it no reason to use `z_i`;
2. the pre-GRU FiLM is attenuated by the recurrent state/path;
3. the static skill path itself has weak usable capacity;
4. the observational behavior-window instrument missed a real action-level
   effect.

The causal edge remains `z_i -> persistent executable behavior`. R27 stays on
promotion levels 0-1 of the project research discipline. It does not authorize
q_A, q_d, q_D, team-discriminator, or other intrinsic reward paths.

## 3. Scope

### In scope

- Load the existing R25 arm0 update25, update30, and final checkpoints without
  optimizer state.
- Run frozen CUDA collection with the natural policy only to obtain generic
  low-actor snapshots at individual renewal events.
- Enumerate every individual skill on identical observations and hidden states
  without mutating the live rollout state.
- Measure separation at FiLM output, post-GRU hidden output, and continuous
  action distribution.
- Compare zero hidden state with the real pre-renewal rollout hidden state.
- Train disposable cloned actors on a synthetic skill-to-action codebook as a
  positive capacity control.
- Run an equal-capacity fake-label sham for the synthetic control.
- Produce a pre-registered root-cause classification and machine-readable
  evidence.

### Out of scope

- No environment reward, communication field, task outcome, coverage,
  throughput, QoS, backhaul, topology label, or recovery flag in any input,
  loss, or gate.
- No PPO, critic, high-level policy, assignment policy, collector semantics,
  environment dynamics, or checkpoint-format change.
- No update to the source checkpoint or its optimizer.
- No forced multi-step environment rollout; that remains a later causal gate.
- No post-GRU FiLM, action-head residual, hidden-state reset, hypernetwork, or
  skill-indexed recurrent implementation in R27-G1.
- No q_A/q_d/q_D or new intrinsic reward.
- No arm2 result may rescue the primary arm0 classification.

## 4. Frozen Snapshot Contract

For each arm0 checkpoint, run `NResets=64` on CUDA with fixed reset seeds. At
every natural individual renewal event, record:

```text
checkpoint_id, checkpoint_update,
reset_id, reset_seed, episode_id, env_id, agent_id,
observation, pre_renewal_actor_hidden,
natural_skill, previous_skill, duration_idx, skill_age,
episode_done_mask
```

The record must not contain task reward or communication-specific diagnostics.
Collection uses `torch.no_grad()`, evaluation mode, and
`load_optimizers=False`. The script hashes the source checkpoint before and
after collection and fails if the hash changes.

Rows are grouped by reset. Any fitted synthetic control uses one deterministic
60/20/20 train/validation/test reset split. No row from one reset may cross a
split boundary.

## 5. Static Skill-Sensitivity Audit

For each snapshot row and every skill `z in {0, ..., K-1}`, evaluate the actor
under two hidden-state conditions:

```text
zero_h:    h_actor = 0
rollout_h: h_actor = the recorded pre-renewal hidden state
```

The evaluation must not write back hidden state. Capture:

- the skill FiLM `gamma` and `beta`;
- the FiLM-modulated observation feature;
- the post-GRU actor feature;
- the continuous action mean and log standard deviation.

For every row, compute all unordered skill-pair differences. Primary metrics:

```text
skill_action_skl_zero_h
skill_action_skl_rollout_h
skill_action_stdmean_distance_zero_h
skill_action_stdmean_distance_rollout_h
skill_film_feature_between
skill_post_gru_feature_between_zero_h
skill_post_gru_feature_between_rollout_h
hidden_retention_ratio = rollout_h_SKL / max(zero_h_SKL, 1e-8)
```

`skill_action_skl_*` is the symmetric KL between the diagonal Gaussian action
distributions. `skill_action_stdmean_distance_*` is the Euclidean distance
between action means after division by the shared action standard deviation.

### Static inactive control

Use the same actor and parameters but replace the realized FiLM transform by
the identity transform `gamma=1`, `beta=0` during the diagnostic forward pass.
No module is deleted. The inactive path must produce zero skill-pair separation
up to numerical tolerance; otherwise the audit is INVALID.

### Static threshold

A checkpoint has non-decorative static action capacity under a hidden-state
condition only when all are true:

1. mean pairwise symmetric KL is at least `0.02` nats;
2. standardized action-mean distance is at least `0.20`;
3. the reset-cluster bootstrap 95% lower confidence bound of active minus
   inactive symmetric KL is above zero;
4. all values are finite and sampling/evaluation parity checks pass.

The arm0 static family has a condition-level result only when at least two of
update25, update30, and final agree. The three checkpoints are stability
snapshots, not independent seeds.

Recurrent washout is flagged only when, in at least two checkpoints:

```text
zero_h passes static capacity,
rollout_h fails the 0.02-nat threshold,
hidden_retention_ratio < 0.50.
```

## 6. Synthetic Learnability Positive Control

Static checkpoint sensitivity can be weak because training ignored `z_i` even
when the architecture is capable. Test learnability on disposable actor clones.

### Dataset and target

Use the final arm0 checkpoint snapshot split. Build a fixed skill-action
codebook from a seeded orthogonal matrix in normalized continuous-action space.
Each skill receives one target action-mean vector with norm `0.5`; the codebook
is fixed before training and emitted in metadata. Balance skill labels within
each split independently.

### Active clone

Clone the complete low actor, preserve its architecture, and optimize only the
clone's actor parameters to map `(observation, rollout_h, true_skill)` to the
skill's target action mean. The environment, critic, PPO, and source checkpoint
are not involved.

### Capacity-matched fake-label sham

Instantiate an identical clone with the same parameter count, initialization,
optimizer, batches, and target rows. Replace the input skill with a
deterministic matched-marginal fake label independent of the target's true
skill. The sham keeps the FiLM module active and trains every parameter; only
the causal label correspondence is broken.

### Training contract

- CUDA only for the scientific run; no CPU fallback.
- Adam with learning rate `3e-4`.
- Batch size `256`.
- Maximum `1000` optimizer steps.
- Validate every `25` steps.
- Early-stop patience `20` validation checks.
- Minimum validation-loss improvement `1e-4`.
- Fixed seeds `17`, `23`, and `41` for both active and sham clones.
- Test split is evaluated once from the best validation state and never affects
  stopping.

Primary synthetic metrics:

```text
synthetic_code_accuracy
synthetic_code_macro_f1
synthetic_target_mse
synthetic_active_minus_sham_accuracy
synthetic_train_minus_test_accuracy
```

Decode predicted action means by nearest codebook vector. A synthetic seed
passes only when:

1. active held-out code accuracy and macro-F1 are both at least `0.90`;
2. active minus sham held-out accuracy is at least `0.50`;
3. the reset-cluster bootstrap 95% lower confidence bound for active minus sham
   accuracy is above zero;
4. sham accuracy is no greater than `1/K + 0.10` (`0.35` for R26's `K=4`);
5. active train-minus-test accuracy gap is no greater than `0.20`;
6. the source checkpoint hash remains unchanged.

Synthetic learnability passes only when at least two of the three fixed seeds
pass. Thresholds must not be changed after observing R27 data.

## 7. Root-Cause Classification

R27 emits exactly one primary classification plus supporting reasons.

### `CAPACITY_PRESENT_OBJECTIVE_MISSING`

- synthetic learnability passes;
- recurrent washout is not flagged;
- rollout-hidden static capacity fails in at least two checkpoints.

Meaning: the architecture can learn a skill-action mapping, but the current
task/PPO objective did not make the trained actor use `z_i`. The next design may
study an individual skill-use/forcing objective. It still may not inject reward
until that objective has its own accepted reward-off/small-reward plan.

### `RECURRENT_WASHOUT`

- synthetic learnability passes;
- recurrent washout is flagged by the exact zero-h/rollout-h rule.

Meaning: inherited recurrent state suppresses otherwise available skill
sensitivity. The next architecture experiment may compare post-GRU FiLM with a
capacity-matched inactive and fake-label sham. Hidden-state reset is not the
default repair because it destroys temporal memory and changes collector
semantics.

### `STATIC_PATH_CAPACITY_WEAK`

- synthetic learnability fails in at least two seeds; or
- both zero-h and rollout-h static capacity fail in at least two checkpoints
  and the active synthetic clone does not separate reliably from the sham.

Meaning: the existing FiLM path has not demonstrated usable capacity under the
fixed training contract. The next design may compare post-GRU FiLM and a direct
action-head residual, each with capacity-matched inactive/sham controls. No
reward work is authorized.

### `STATIC_USED_OBSERVATIONAL_MISS`

- rollout-hidden static capacity passes in at least two checkpoints;
- R26-G1a observational behavior separation remains failed.

Meaning: the trained actor changes its immediate action distribution with
`z_i`, but the R26 behavior window did not establish persistent modes. This
does not automatically override the R26 decision tree. It requires a focused
review before any forced multi-step causal audit is authorized.

### `UNDERPOWERED` or `INVALID`

Use `UNDERPOWERED` when reset support or action/skill coverage cannot support
the bootstrap and split. Use `INVALID` for checkpoint mutation, CPU fallback,
non-finite values, inactive-control leakage, source/runtime path mismatch, or
online-versus-diagnostic action-distribution disagreement. Repair the
instrument and repeat the same gate without changing thresholds.

## 8. Output Contract

Each checkpoint writes below one assigned run root:

```text
command.txt
runner_status.txt
collector_manifest.json
capacity_snapshots/*.npz
static_capacity.json
static_capacity.md
```

The synthetic control writes:

```text
synthetic_control.json
synthetic_control.md
```

The batch writes:

```text
r27_capacity_autopsy.json
r27_capacity_autopsy.md
batch_status.txt
```

The final Markdown must show every threshold, per-checkpoint static result,
per-seed synthetic result, inactive/sham behavior, classification reasons,
checkpoint hashes, parameter counts, and prohibited next actions.

## 9. Expected Cost And Execution Site

- Scientific device: local CUDA, NVIDIA RTX 4070 Laptop GPU; never silently
  fall back to CPU.
- Expected wall time: approximately 2.5-3.5 hours. The estimate uses R26's
  measured pace of roughly 45 minutes per 64-reset checkpoint, plus bounded
  active/sham synthetic fitting and report generation.
- This is a diagnostic, not a 320k/1M training run.
- A fresh timestamped run root and a pre-launch `memory/ExpRecord.md` entry are
  mandatory.

## 10. Likely Implementation Boundary

Create or modify only after this written spec is approved:

- Create `ha_ctse_process/low_actor_capacity_audit.py` for detached metrics,
  codebook construction, clone training, bootstrap, and classification.
- Create `scripts/audit_r27_low_actor_capacity.py` for checkpoint
  reconstruction, frozen snapshot collection, and per-checkpoint execution.
- Create `scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1` for the exact
  three-checkpoint batch and dry-run.
- Create focused tests under `tests/` for action-distribution parity, inactive
  control zero separation, active/sham synthetic controls, split isolation,
  checkpoint immutability, thresholds, and classification.

Avoid modifying the training loop, reward composition, policy checkpoint
format, `StrictHMASDMAPPOLowLevelPolicy`, or the live actor in R27-G1. If the
audit cannot be implemented without changing those components, return to
design review rather than widening scope silently.

## 11. Verification Requirements

Focused tests must prove:

- frozen audit outputs match the live actor action distribution for identical
  observation, skill, hidden state, and deterministic flags;
- enumerating skills does not mutate agent hidden state or checkpoint weights;
- inactive FiLM produces zero skill-pair separation within numerical tolerance;
- synthetic active control passes on a synthetic fixture and fake-label sham
  remains near chance;
- reset-grouped train/validation/test splits have no overlap;
- test metrics never affect early stopping;
- bootstrap groups by reset rather than row;
- every root-cause classification branch is reachable from synthetic fixtures;
- CPU scientific launch fails explicitly;
- dry-run covers exactly arm0 update25, update30, and final and contains no
  reward, PPO continuation, q_A, q_d, or q_D flags.

## 12. Decision Boundary

R27-G1 is complete when the audit assigns one pre-registered classification and
the result has been reviewed against the failure and baseline matrices. It does
not itself change the algorithm. The controller must present the factual result,
scientific interpretation, next authorized edge, and prohibited actions before
any R27 Stage B implementation begins.
