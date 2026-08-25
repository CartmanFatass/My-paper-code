# R28-G1 Causal-Capacity-Calibrated Skill Forcing

Date: 2026-07-13

Status: G0 complete and accepted as `PASS_TARGET_NULLS`. The focused G1
implementation freeze in Section 6.1 was accepted on 2026-07-13, and the scoped
code/test/runner package is implemented. Two later one-update local engineering
smokes were blocked by genuine natural-domain support OOD before reward
application; no formal topology or three-arm training run was executed. The
current disposition lives in `memory/ExpRecord.md` and
`docs/research/decisions/R26_R27_R28_FAILURE_REVIEW_20260713.md`; the frozen contract below
is retained as evidence and is not launch authority.

## 1. Decision

R27-G2 closes the upstream capacity question narrowly: under a forced hold, the
frozen R25 arm0 executor produces persistent, label-consistent action processes
and a separate local effect through native H40. R26 remains negative for natural
observational windows.

The next target is therefore not another passive `q_d` probe and not Gate C as
reward. R28-G1 designs a low-level forcing signal from fixed-length deterministic
action-process features, residualized against capacity-matched context,
pre-window, and sham-label nulls.

The offline calibration on the existing R27 shards is complete. Final and
update30 passed unchanged, update25 failed only its train-test-gap guard, and
the family classification is `PASS_TARGET_NULLS`. The frozen final scorer is
the only allowed target/null input to G1. It may not be refit, retuned, or
swept. Reward-on training remains blocked pending topology validation and
explicit launch approval.

## 2. Causal claim and boundary

Active edge:

```text
distinct z_i -> naturally expressed, behaviorally differentiated skills
```

Hypothesis:

```text
Given an actor already proven capable under forced hold, a small bounded
action-process residual applied to the low policy can make naturally executed
z_i windows more differentiated than matched probe-only and sham-reward
controls, without shortcut dominance or task collapse.
```

The preceding G0 diagnostic hypothesis is narrower: terminal action-process
features from a forced hold contain held-out target-label information beyond
capacity-matched assignment context and pre-intervention behavior, that
increment disappears under sham labels, and the calibrated residual remains
higher for hold than matched pulse at native horizons 20/30/40.

Promotion level: level 3, small clipped reward, only after the offline target
calibration passes. This is not a long-run task or HMASD-parity test.

Upstream evidence:

- R27-G2: `PASS_BEHAVIOR_EFFECT`, A/B1/B2/B3/C PASS at update25, update30,
  and final; 192/192 structured decision shards valid.
- R27-G1: immediate low-actor `z_i` sensitivity exists.
- R26-G1a: natural behavior-window evidence remains FAIL/MIXED.
- R24-1: the old `q_d/q_D` evidence line remains blocked.
- R25: `q_A` actionability is learnable, but its reward arm regressed at the
  1M verification read and remains default-off.

Allowed claim after a future R28 PASS: the selected forcing target caused more
natural, shortcut-resistant individual-skill differentiation over the tested
160k continuation. It would not establish team complementarity, useful team
intent, decoupled-lifetime benefit, long-run task gain, or HMASD parity.

## 3. Candidate target

Score one terminal ten-step window for each completed natural skill assignment.
The window must remain inside one episode, one policy version, and one unchanged
focal skill. A 10/20/30/40-step assignment contributes exactly one window:
steps 1-10, 11-20, 21-30, or 31-40 respectively. This prevents longer
durations from receiving more intrinsic-reward opportunities.

```text
a_det_t = tanh(mu_theta(o_t, h_t, z_i))

F_post = concat over four action dimensions of:
         mean(a_det), temporal_std(a_det), least_squares_slope(a_det)
         # fixed width 12, matching the independent R27 B3 summary

phi_0 = frozen source-policy pre-FiLM actor-base encoder

C = stop-gradient, label-independent null context:
    phi_0(observation at assignment), agent id, native duration/horizon id,
    and phase bin

F_pre = the same 12-feature summary from the ten steps immediately before the
        assignment, only when those steps share one policy version and do not
        cross an episode boundary
```

The R27 artifact schema supports this construction: applying `tanh` to
`live_pre_tanh_mean` provides post-intervention deterministic actions,
`prefix_pre_tanh_mean[-10:]` provides the pre-intervention window, and the
reference branch's initial `local_observation` provides the common assignment
context. The registered frozen R25 checkpoint is needed only to compute
`phi_0`; no environment replay is required.

The frozen encoding is exact:

```text
phi_0 width       256  # two source actor-base Linear+ReLU layers
agent one-hot       6
duration one-hot    4  # native 10/20/30/40
phase one-hot       3  # min(floor(episode_step / 100), 2)
C width            269
stream width        12  # F_post, F_zero, or F_pre
head input width   281
```

For R27, prefix lengths 50/150/250 map to phase bins 0/1/2. Each head has one
linear four-class softmax layer. It receives its own train-only column mean and
population standard deviation with a `1e-6` floor; the head architecture,
parameter count, optimizer, stopping rule, and device remain identical.

No selected communication, coverage, service, topology, backhaul, reward-sum,
or Gate-C effect field may enter `F_post` or `F_pre`. `phi_0` is a frozen
generic observation encoder and appears only in null heads; it is never a
positive process feature or usefulness multiplier. Raw task metrics remain
evaluation diagnostics.

Fit three equal-width, equal-depth heads, with zero-padding so their parameter
counts and optimization contracts match:

```text
q_full(z_i | F_post, C)
q_context(z_i | F_zero, C)
q_pre(z_i | F_pre, C)
```

The train split fits the heads, the validation split applies the common stopping
rule and selects one temperature per head from the fixed 401-point log-spaced
CUDA grid `[0.05, 10.0]`, choosing the lowest-temperature first minimizer. The
test split is read once. The exact
scaler, temperatures, and head weights from the passing final-checkpoint gate
become an immutable scorer artifact; R28-G1 does not refit them online.

For a valid window, define:

```text
s_real_i =
    log q_full(z_i | F_post, C)
    - max(log q_context(z_i | F_zero, C),
          log q_pre(z_i | F_pre, C))

r_real_i = clip(0.02 * center_group(s_real_i), -0.05, +0.05)
```

The sham control uses the same frozen heads and computation but replaces
`z_i` with a within-group deterministic derangement `z_tilde_i`. The
derangement is generated from the registered RNG seed and segment order, changes
across policy updates, preserves the group label marginal, and has no stable
mapping from a real skill to a sham skill:

```text
s_sham_i = score(z_tilde_i; F_post, F_pre, C)
r_sham_i = clip(0.02 * center_group(s_sham_i), -0.05, +0.05)
```

No application-layer hash is used. Groups are
`(policy_update, agent_id, duration_id)`; a group without all four labels or
enough rows receives zero reward. A missing valid `F_pre` makes the window
ineligible for reward rather than silently weakening the null.

The single segment reward is divided equally over its terminal ten primitive
low-level rewards. It never enters the high-level return. The scorer, features,
labels, centering, and support gate are detached. Policy gradients reach the
actor only through the low-level PPO advantage induced by stored scalar reward;
there is no gradient through `a_det` or the frozen scorer.

## 4. Leakage, support, and update-clock contract

- The scorer artifact is fit only on the registered R27 train resets,
  temperature-calibrated only on validation resets, tested once, and then
  frozen. Online refitting or same-rollout fitting is prohibited.
- No action window, recurrent state, segment, pre-window, or redistributed
  reward may cross an episode, skill assignment, or PPO policy-update boundary.
- Reset recurrent hidden state only where the existing collector contract does;
  R28 does not add a hidden reset.
- Heads use grouped train/validation/test splits by reset or environment stream,
  never random window-row splits.
- The G0 artifact freezes feature normalization and a shrinkage
  class-conditional `F_post` support envelope from train/validation evidence.
  For each `(duration, label)`, use diagonal train variance shrunk as
  `0.90 * class_variance + 0.10 * pooled_duration_variance`, floor every
  component at `1e-6`, and set the squared standardized-distance boundary to
  the validation-set 95th percentile using linear quantile interpolation.
  A future window outside that envelope receives zero intrinsic reward. The
  rollout OOD fraction is logged and an excessive fraction disables the reward
  for that rollout rather than extrapolating classifier confidence.
- Sham labels, split seeds, feature normalization, early stopping, temperature
  scaling, support rules, and all thresholds are frozen before a result read.
- All non-R28 intrinsic paths are off: old `q_d/q_D`, `q_A`, g-info, team
  reward, process posterior reward, effect residual reward, topology/P2 shaping,
  and duration-entropy forcing.

This target replaces the prototype P3-4 discriminator score if implemented; it
must not be stacked beside it. `enable_team_conditioned_qd_probe` remains a
diagnostic-only legacy path and cannot inject reward.

## 5. R28-G0 offline target calibration

Result (2026-07-13): accepted `PASS_TARGET_NULLS` from cloud run
`logs/r28_g0_action_process_target_20260713_175600`. The validated artifact is
`r28_g0_scorer_final.pt`; it authorizes G1 package review only and carries no
reward-launch authorization.

Inputs: exactly the 192 R27-G2 decision-grade `r27-g2-reset-v2` shards from
run `095408` and the three registered frozen R25 checkpoints. The checkpoints
are forward-only context encoders; there is no environment replay. The stopped
run's 11 partial shards and the quarantined pilot are excluded.

For every hold branch, construct one sample at each native terminal horizon:

```text
duration 10 -> branch steps  1..10
duration 20 -> branch steps 11..20
duration 30 -> branch steps 21..30
duration 40 -> branch steps 31..40
```

The label is the forced target skill, including for a matched pulse after it
returns to the natural label; that is what makes the pulse a persistence null.
`F_pre` is always the final ten
pre-intervention prefix steps. Matched non-natural pulse branches provide the
persistence null at durations 20/30/40; duration 10 has no pulse contrast
because the registered pulse itself holds the target for all ten steps.

Device and cost: CUDA fitting, zero environment steps and zero policy updates,
expected under 30 minutes. CPU fallback is invalid. This is a bounded
diagnostic, not a scientific training launch.

Per checkpoint use the frozen R27 split:

```text
test resets       0..11
validation        12..23
train             24..63
fit seed          28021
sham seed         28022
bootstrap seed    28023
bootstrap reps    10,000 reset clusters
```

The frozen linear-softmax head contract reuses R27-B3's optimizer scale:
train-only standardization with a `1e-6` floor, Adam learning rate `3e-3`,
weight decay `1e-4`, at most 1,000 steps, validation every five steps,
patience 20 validations, and minimum validation improvement `1e-4`. The
The categorical encoding, temperature grid, and support-envelope estimator are
now frozen above; changing any of them after execution starts makes the run
`INVALID`.

Calibration metrics and thresholds, all computed on held-out reset groups:

- `q_full` overall accuracy and macro-F1 each at least `0.40`, every native
  duration's accuracy at least `0.40`, and overall accuracy's reset-cluster
  95% lower bound above chance `0.25`;
- `q_full - q_context` and `q_full - q_pre` accuracy-gain estimates each at
  least `0.05`, with reset-cluster bootstrap lower bounds above zero;
- mean calibrated `s_real` has a reset-cluster bootstrap lower bound above
  zero;
- pooled matched hold-minus-pulse `s_real` difference over durations 20/30/40
  has a bootstrap lower bound above zero, with a positive point estimate at
  every one of those durations;
- predictions scored against the registered within-group sham derangement have
  accuracy at most `0.35`;
- train-minus-test accuracy is at most `0.20` for every gated head;
- at least 48 valid reset groups, at least 14 resets in each prefix family,
  train/validation/test support at least 32/9/9 resets, and each prefix family
  contributes at least 10/3/3 resets to those splits;
- the frozen support envelope covers at least 90% of held-out real-label test
  windows. The future rollout kill threshold is an OOD fraction above 0.20.

A checkpoint passes only if it is valid, adequately powered, and all target
gates pass. Family `PASS_TARGET_NULLS` requires the final checkpoint and at
least one of update25/update30 to pass. Thus the scorer actually used by the
planned final-checkpoint continuation is never licensed by two earlier
checkpoints alone. Results cannot tune features, grouping, thresholds, or
support rules.

R28-G0 branches:

- `PASS_TARGET_NULLS`: freeze the passing final-checkpoint scaler,
  temperatures, heads, and support envelope; permit focused implementation
  review of the future level-3 package, but do not launch it.
- `FAIL_TARGET`: abandon this score. Preserve R27 capacity evidence and the R26
  observational negative; no reward test or alternative classifier sweep.
- `MIXED_TARGET`: review the single disagreement (checkpoint stability,
  duration, pre-null, or pulse contrast); no reward implementation.
- `UNDERPOWERED`: increase support only with unchanged features and thresholds.
- `INVALID`: repair the identified instrument defect and repeat the unchanged
  calibration at most once.
- crash: preserve logs and repair only the operational cause.

## 6. Future R28-G1 level-3 experiment (not authorized)

Source: cloned R25 arm0 final checkpoint, loaded as 1,000,000 environment steps
/ update 32. This is a new continuation and must not overwrite or rerun the
standing R25 arm0/arm2 references.

Mechanism-matched arms:

```text
A probe_only   : frozen scorer computes real and sham scores; injection is zero
B sham_reward  : same frozen scorer/compute/clip; inject per-update sham score
C real_reward  : same frozen scorer/compute/clip; inject real score, low-level only
```

All other flags, networks, optimizer states, ValueNorm, environment, rollout,
evaluation, and checkpoint loading are identical. The scorer artifact, support
gate, sham RNG, parameters, and compute exist identically in all three arms and
have no optimizer. This is a level-2 mechanism-matched HA-CTSE comparator for a
level-3 reward intervention, not an HMASD comparison.

Provisional fixed exposure for later review:

- paired continuation seeds `28031, 28032, 28033`;
- 160,000 environment steps per arm, 1,440,000 total;
- 16 vector environments, rollout length 500, exactly 20 PPO updates per arm;
- low PPO epochs 15, existing optimizer/loss/advantage contract unchanged;
- evaluations at +80k and +160k, 20 episodes each;
- cloud RTX 4090 CUDA only; minimum three concurrent arm workers after a
  separate topology check; no serial or CPU fallback;
- expected end-to-end wall clock 6-10 hours if the three-worker topology passes.

The final runner must state its measured topology and revised wall-clock estimate
before launch. A failed topology check stops rather than reducing to serial.

### 6.1 Focused implementation review freeze (accepted 2026-07-13)

The live trainer can support this experiment without changing actor/critic,
PPO, GAE, optimizer, environment, or high-level-return semantics, but the old
P3-4 forcing path cannot be reused. It fits a same-rollout head from sampled
actions/effect fields and therefore violates the frozen deterministic-action
target. Implement G1 as a separate `r28_g1_reward` module.

Frozen lifecycle and source validation:

- Require the R25 arm0 final source at `total_steps=1,000,000`, `update_idx=32`,
  six agents, four skills, continuous strict-HMASD MAPPO low actor,
  `skill_interval=10`, and duration candidates `(1,2,3,4)`.
- Load all source policy, critic, optimizer, and ValueNorm state first. Then
  attach the G0 heads/support envelope and deep-copy the loaded source
  `low.actor_base` as frozen `phi_0`. Never read the subsequently updated actor
  base for scorer context.
- Save that frozen actor-base state in every G1 continuation checkpoint so a
  crash resume cannot accidentally freeze the already-updated actor. The
  scorer and encoder have no optimizer and all tensors remain detached.
- Validate typed scorer fields, dimensions, finiteness, experiment/checkpoint
  names, and registered paths. Do not add a hash or checksum identity layer.

Window and clock contract:

- Capture `tanh(mu_theta)` from the exact recurrent actor forward that produced
  each rollout action; do not reconstruct it from sampled actions and do not
  advance the GRU a second time. Store it as detached rollout evidence.
- Add a separate per-environment episode-step counter. The scorer phase is
  `min(floor(episode_step_at_assignment / 100), 2)`; the existing interleaved
  rollout index is not an episode step and may not be substituted.
- A row is structurally eligible only when its natural segment length is
  exactly `10 * duration_candidate`, its terminal ten deterministic actions
  are present, and its preceding ten deterministic actions come from the same
  episode and PPO policy version. Initial, episode-truncated, and
  update-truncated assignments receive zero.
- Reward attribution uses only the row's final ten rollout indices. Divide one
  segment reward equally over those ten low-level rewards. Never add it to
  segment/high-level returns.

Support, grouping, and sham contract:

- Evaluate the support envelope against the executed real label. This common
  real-label support mask is used by all three arms and by both real and sham
  scoring; the sham label must not create a different OOD population.
- Compute rollout OOD fraction over structurally eligible rows before group
  filtering. If it is above `0.20`, inject zero R28 reward for the entire
  rollout and record a support kill-switch event. A future PASS permits no such
  event.
- On in-support rows, group by `(policy_update, agent_id, duration_id)`. A group
  is rewardable only when all four real labels occur and a label-marginal-
  preserving fixed-point-free row derangement exists, equivalently the largest
  label count is at most half the group size. There is no additional arbitrary
  row-count threshold.
- Seed sham construction with `numpy.random.SeedSequence([28022,
  policy_update, agent_id, duration_id])`. Randomize row order and label-block
  order, enumerate valid circular shifts of the label multiset, and choose one
  with that RNG. This preserves the exact group marginal, changes with the
  update, has no fixed label, and introduces no stable real-to-sham map.
- Score real and sham labels through all three frozen heads on the same rows.
  Center `s_real` and `s_sham` separately within the same rewardable group, then
  apply the fixed `0.02` scale and `[-0.05,+0.05]` clip.

Arm and guard contract:

- Use one explicit arm selector: `probe_only`, `sham_reward`, or
  `real_reward`. Every arm computes and logs both scores, both centered rewards,
  common support, and common group eligibility. Only the selected scalar is
  eligible for low-level injection; `probe_only` always injects zero.
- Force all non-R28 policy reward paths off after checkpoint metadata is
  applied, including the source checkpoint's inherited prototype-discriminator
  reward, q_A, q_d/q_D, team/team-transition rewards, old skill forcing,
  process/outcome/effect/topology/P2 rewards, g-info objective, and duration/Z
  entropy forcing. Diagnostic-only heads may remain only when their optimizer
  cannot update policy modules and their compute is identical across arms.
- Define the per-rollout ratio as:

  ```text
  mean(abs(selected distributed R28 reward)) /
  max(mean(abs(original individual environment reward)), 1e-8)
  ```

  If it exceeds
  `0.05`, inject zero for that rollout and record a ratio kill-switch event.
  Non-finite scores/rewards, index crossing, or recurrent-evidence mismatch
  fail before PPO rather than being silently zeroed.

Evaluation and family-decision evidence:

- Keep the existing 20-episode matched task evaluation at +80k and +160k. At
  +160k, run the unchanged frozen R26 natural-window analysis for every arm and
  seed. Extend its collection pass only with a separate R28 deterministic-action
  sidecar; do not change R26 features, splits, fits, thresholds, or reports.
- Export R26 held-out row correctness for the already-fitted full/prior models
  as decision evidence. For common `(seed, test_reset)` clusters define
  `g_arm = mean(1[full correct] - 1[prior correct])` and
  `delta = g_real - max(g_probe_only, g_sham_reward)`. Use 10,000 cluster
  bootstrap repetitions with seed `28034`; require mean delta at least `0.05`
  and its 95% lower bound above zero.
- On the R28 deterministic-action sidecar, require pooled held-out mean
  `s_real` and mean `s_real-s_sham` to have reset-cluster 95% lower bounds above
  zero, using 10,000 repetitions and seeds `28035` and `28036`. Also require OOD
  fraction at most `0.20` and zero support/ratio kill-switch events.
- For task safety, select the higher-return matched control separately within
  each continuation seed (ties choose `probe_only`). At +160k, every paired seed
  must satisfy
  `(control_return - real_return) / max(abs(control_return),1e-8) <= 0.10`, and
  its zero-throughput episode fraction may worsen by at most `0.10` absolute.
  Report all seed-level values; do not average away a failed safety seed.

The accepted package adds the separate scorer module, typed checkpoint/CLI
integration, focused synthetic tests, a frozen-result family analyzer, and a
Bash runner. The runner places large outputs under `/root/autodl-tmp`, requires
three concurrent CUDA arm workers, and stops on a failed topology check. Neither
the completed implementation nor a future topology validation constitutes
reward-launch approval.

Primary independent read: run the frozen R26 natural-window analyzer on each
arm's +160k checkpoint without changing its thresholds. Family PASS requires:

- `real_reward` passes the natural behavior gate in at least two of three paired
  seeds, while neither `probe_only` nor `sham_reward` passes in two of three;
- pooled reset-cluster real-minus-best-control improvement in the frozen
  full-minus-prior gain has estimate at least `0.05` and 95% lower bound above
  zero;
- on held-out natural evaluation windows, the frozen real score remains above
  context/pre and per-update sham nulls; scorer OOD fraction stays at or below
  `0.20` and no rollout support kill-switch fires;
- normalized skill-label entropy is at least `0.80` and no reward kill-switch,
  non-finite value, episode/update crossing, or recurrent-state mismatch occurs;
- absolute intrinsic/external reward ratio stays at or below `0.05` per rollout;
- paired external return does not regress by more than 10% from the better
  matched control and zero-service episode fraction does not worsen by more
  than 0.10 absolute. These are safety guards, not intrinsic targets.

Future outcome branches:

- `PASS`: accept only short-horizon natural individual-skill differentiation;
  next action is a separate long-run verification design, not team reward or
  decoupled-lifetime claims.
- `FAIL`: retire this forcing target and complete the R26/R27/R28 review; do not
  sweep coefficients or add another classifier.
- `MIXED`: identify one causal disagreement and perform the failure review; no
  new module or long run.
- `UNDERPOWERED`: support-only repeat with unchanged target and thresholds.
- `INVALID`: one instrument-fix repetition of the unchanged gate.
- crash: operational repair only.

## 7. Prohibited changes while this gate is open

- No `q_A`, old `q_d`, `q_D`, team discriminator, effect residual, Gate-C
  observation, communication field, environment-reward surrogate, or duration
  entropy term in the intrinsic reward.
- No actor/critic/FiLM/GRU architecture change, hidden-state reset, optimizer,
  PPO, GAE, advantage, environment-dynamics, or high-level reward change.
- No natural-renewal Stage 2 rescue, H100 endpoint, q-coefficient sweep, HMASD
  rerun, R25 standing-reference rerun, or task-scale launch.
- No conclusion about team intent, complementarity, credit assignment,
  asynchronous lifetimes, or HMASD parity.

## 8. Status and artifacts

R27 status source:

```text
/root/autodl-tmp/HMASD/r27_g2_remote/controller/current_overnight.env
ORCH_ROOT=.../r27_g2_overnight_20260713_095408
status/orchestration_status.env
runs/decision_grade/r27_g2_forced_trajectory_effect.{json,md}
runs/decision_grade/aggregate_validation_output.log
```

A future G0 implementation must write under
`logs/r28_g0_action_process_target_<timestamp>/` and register its exact command,
device, input run root, split seeds, thresholds, and report paths in
`memory/ExpRecord.md` before execution.
