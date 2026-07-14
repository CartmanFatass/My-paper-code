# HA-CTSE Experiment Dashboard

Updated: 2026-07-14

Purpose: compact factual state for current experiments and standing evidence.
The controller records a meaningful launch/result transition here before acting;
completed detail stays in frozen designs, raw run artifacts, or
`memory/LTM/EXPERIMENT_ARCHIVE.md`.

## Protocol

Required dashboard columns:

```text
ID | Status | Stage | Location | Next Read | Key Evidence | Decision
```

Status vocabulary: `planned`, `launch-ready`, `running`, `completed`,
`stopped`, `failed`, `invalid`, `superseded`, `blocked`,
`standing-reference`.

Standing references are fixed comparison data. Do not rerun the HMASD baseline
or R25 arm0/arm2 unless a new design proves them incomparable and the user
explicitly approves the exception.

## Current Dashboard

| ID | Status | Stage | Location | Next Read | Key Evidence | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| EXP-20260714-r30-fixed-clock-paired-320k | stopped — superseded before completion | hierarchy-L2 reward-pure temporal-controller mechanism gate | local CUDA; `logs/r30_fixed_clock_paired_320k_20260714_115559`; commit `b670eb6` | none | legacy arm completed; treatment retry was stopped when the user selected the faster Alice--Bob mechanism screen | Preserve the incomplete logs; no M1-M4 scientific outcome exists. |
| EXP-20260714-r29-t10-paired-320k | completed — `PRELIMINARY_FAIL`; online family retired | preliminary hierarchy-L2 mechanism-matched reward comparator | local CUDA; `logs/r29_t10_paired_320k_20260714_010026` | none | implementation valid; R26 probe `PASS` versus reward `MIXED`; paired score CI crosses zero; task reward degraded `31.56%`; GPT-5.6 Pro verdict `RETIRE` | Keep R29 diagnostic-only. Do not promote, retune, or expand seeds; move to the reward-off stochastic realized-effect edge. |
| EXP-20260713-r29-g0-counterfactual-action-information | completed — `PASS_COUNTERFACTUAL_ACTION_INFORMATION_TARGET` | hierarchy-L1 reward-off target gate | local CUDA; `logs/r29_action_information_20260713_230631` | none | 3/3 checkpoints PASS; active means `0.017050`/`0.017990`/`0.019208`; inactive max `5.96e-8` | Accept the support-native target only. Next test is a direct mechanism-matched reward comparator, not a separate smoke. |
| EXP-20260713-r28-forced-execution-support-transport | completed — `FAIL_STOCHASTIC_SUPPORT_TRANSPORT` | reward-off matched-domain causal diagnostic | local CUDA; `logs/r28_support_transport_20260713_222807` | none | 1,024 paired rows/mode; deterministic OOD `0.068359`, stochastic OOD `0.823242`; 64 rows/cell | Random action execution alone breaks frozen support. Retire the forced-deterministic scorer family from online reward use. |
| EXP-20260713-r28-g1-causal-skill-forcing-reward | blocked — `BLOCKED_SUPPORT_OOD`; formal experiment not run | prelaunch engineering for promotion stage 3; planned formal comparator was baseline hierarchy L2 | local smokes `logs/r28_g1_engineering_smoke_20260713_212008` and `logs/r28_g1_engineering_smoke_20260713_213746`; no formal run root | none; cross-round failure review complete | same-config one-update OOD `0.950617`/`0.9375`; support kill in both; zero R28 reward applied; no mapping defect found | Retire the frozen G1 launch package. Do not refit/relax/repeat or infer reward efficacy; next action is a reward-off matched-domain transport diagnostic. |
| EXP-20260713-r28-g0-action-process-target-calibration | completed — accepted `PASS_TARGET_NULLS` 2026-07-13 | diagnostic-null calibration before any level-3 reward | cloud RTX 4090 CUDA; run `logs/r28_g0_action_process_target_20260713_175600`; commit `3eb22d5` | none; preserve scorer as frozen input to later review | final and update30 PASS; update25 FAIL only on train-test gap; validated scorer `r28_g0_scorer_final.pt`; zero env steps/policy updates | Accept the offline target/null gate only. This freezes the final scorer and permits focused G1 package implementation review; it does **not** authorize reward implementation launch or any team/cooperation claim. |
| EXP-20260712-r27-g2-forced-z-trajectory-effect | completed — accepted `PASS_BEHAVIOR_EFFECT` 2026-07-13 | level-2 reward-off forced-`z_i` trajectory/effect intervention | cloud RTX 4090 CUDA; run `r27_g2_overnight_20260713_095408`; commit `6c06cde` | none; preserve beside R26 natural negative | 192/192 `OK` shards; aggregate validation `valid=true`, `scientific_status=PASS`; A/B1/B2/B3/C PASS at update25/update30/final | Accept forced persistent conditional behavior and local effect through native H40 only. Record `FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`; do not infer natural selection, reward usefulness, cooperation, task gain, or async-lifetime benefit. |
| EXP-20260711-r27-g1-low-actor-capacity-autopsy | completed — accepted 2026-07-12 | reward-off immediate-capacity autopsy | cloud CUDA; 64 reset groups; R25 arm0 update25/update30/final | none | `dist/r27_g1_capacity_autopsy_cloud64_20260712_151313_extracted/`; result read under `logs/r27_g1_result_read_20260712/` | `STATIC_USED_OBSERVATIONAL_MISS`: immediate `z_i`-conditioned action-distribution sensitivity exists; persistence/effect were not established by this gate. |
| EXP-20260711-r26-g1a-individual-skill-screening | completed — accepted natural observational negative 2026-07-12 | reward-off natural behavior-window screen | local CUDA; six frozen R25 checkpoints | none | `logs/r26_g1a_screening_20260711_105522/` | Primary arm0 family FAIL: final FAIL and update25/update30 MIXED. Arm2 is contextual only. Preserve this result unchanged beside R27 forced evidence. |
| EXP-20260710-r25-qa-verification-1m | standing-reference | 1M HA-CTSE verification | cloud CUDA, 64 env, arm0/arm2 | none | `dist/logs_cloud_r25_qa_verification_1m/`; `gate_read_r25_seed1.md` | arm0 outperformed q_A arm2 late; q_A reward remains default-off. Single-seed parity remains open; do not rerun these arms. |
| EXP-20260709-r24-frozen-qd-null-probes | completed — accepted FAIL 2026-07-09 | frozen `q_d` diagnostic-null probes | cloud archive plus local analysis | none | `dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/` | Under tested policies/setup, 3/4 collapsed. Old `q_d/q_D` reward line remains blocked; no target/coefficient sweep. |
| REF-20260617-hmasd-baseline-s7s1-seed1 | standing-reference | HMASD S7-S1 reference | local 32 env; stopped cleanly at 2.112M/3.2M steps | none | `logs/hmasd_baseline_read_20260709/metric_extract.md` | Coverage first reached 0.7 at 480k and 0.9 at 800k; late mean 0.9639. Reference-only because env/update exposure differs; do not rerun. |

## Current Gate Detail

### EXP-20260714-r30-fixed-clock-paired-320k

- Causal edge: removing the active duration action and replacing expired-only
  edits with a fixed `k0=10` all-agent autoregressive `KEEP/SET(skill)` check
  should permit lifetimes beyond the old four-block cap without short-segment
  high-sample bias, while retaining asynchronous edits and switch-skill supply.
- Upstream authorization: GPT-5.6 Pro returned `MODIFY R30`; its four algorithm
  corrections are accepted. The user authorized a local CUDA short run of up
  to 320K transitions per experiment with 16 environments. This is one
  mechanism seed, not parity, long-run efficacy, or a semantic-skill claim.
- Comparator/null: `legacy_duration` and `r30_fixed_clock_ar_edit` both start
  from the registered R25 arm0 1M/update32 checkpoint, seed `30031`, matched
  environment streams, deterministic expected bridge context, the unchanged
  low policy, and raw environment reward only. The legacy arm retains frozen
  duration choices `(1,2,3,4)`; the treatment changes only the temporal high
  controller, critic/buffer grain, and required checkpoint migration.
- Exposure: arms run concurrently on local CUDA with 16 spawned subproc envs,
  S7-S1, six agents, rollout `501`, and +320,000 transitions per arm to
  1,320,000 total steps/update72. The non-check-aligned rollout makes the
  critic-only continuation observable. Each arm receives 40 rollout/high-PPO
  updates, 15,570 recurrent low-actor and 15,570 low-critic minibatch updates
  (`15` epochs), followed by 20 deterministic evaluation episodes. Expected
  wall clock is 5-10 hours.
- Operational transition: the first launch root ending `115241` failed before
  any environment step or optimizer update because the reward-pure legacy arm
  strictly rejected four retired sampled-team residual weights. Commit
  `b670eb6` adds an explicit allowlisted drop of only those weights and resets
  the high optimizer in both arms. The replacement root ending `115559` was
  stopped incomplete on 2026-07-14 when the user selected the faster role-free
  Alice--Bob mechanism screen; it has no M1-M4 outcome.
- M1 implementation gate: every real decision row has exactly six valid edit
  tokens, maximum teacher-forced replay log-probability error is `<=1e-5`, at
  least one continuation row is observed, and all continuation rows have zero
  actor tokens. Any failure is implementation-invalid and permits only repair
  of the failed path under this same contract.
- M2 lifetime breadth: over the final 10 updates, eligible spell events must
  satisfy `min(P(T>4*k0), P(T<=4*k0)) >= 0.05`. Episode-terminal right-censored
  spells are excluded; a short spell is counted when `SET` ends it at or before
  four blocks, and a long spell once when `KEEP` carries it beyond four blocks.
- M3 asynchronous supply: over the final 10 updates, full-synchronous `SET`
  rows are `<=0.50`, empirical `H(Z|SET)/log(4) >=0.80`, and every skill has at
  least `0.05` of switch selections.
- M4 task safety: relative deterministic reward degradation versus legacy is
  `<=0.10`, and absolute worsening of zero-throughput step fraction is
  `<=0.10`.
- Outcome branches: M1 fail -> repair only and resume the same gate; M1 pass
  but M2 or M3 fail -> retire the current R30 formulation without keep entropy,
  semantic reward, or coefficient sweep; M4 fail -> block promotion for task
  safety; all pass -> accept R30 only as the next core temporal controller and
  move to the separate reward-off realized-effect diagnostic.
- Prohibited while open: extra seeds or arms, duration/keep/switch sweeps,
  sampled team intent, intrinsic/team/process/topology reward, edit/switch or
  lifetime payment, metric redesign, and claims of MAT/HAPPO theorem, reduced
  joint action space, HMASD parity, semantic differentiation, task improvement,
  long-run stability, or cross-environment generalization.
- Status sources: `<run-root>/runner_status.txt`, both arms' single
  `metrics/train_updates.csv` and `metrics/eval_episodes.csv`, and
  `<run-root>/result/r30_fixed_clock_pair.json`.

### EXP-20260714-r29-t10-paired-320k

- Causal edge: a detached recurrent terminal-block density ratio added to the
  low reward should make persistent natural skill-conditioned behavior more
  distinguishable than computing the same ratio without reward injection.
- Upstream authorization: R29-G0 established a support-native action signal;
  GPT-5.6 Pro recommended R29-T10; the user authorized one local 320K run per
  arm. This does not authorize a three-seed conclusion.
- Comparator/null: `probe_only` and `real_reward` start from the same R25 arm0
  1M checkpoint and seed `29031`. Both replay every fixed candidate skill over
  the same complete natural lifetime and compute the same final-10-step score;
  only `real_reward` adds the detached clipped scalar to the terminal low reward.
- Exposure: two arms run concurrently on local CUDA, each with 16 subproc envs,
  rollout 500, skill interval 10, lifetimes `(1,2,3,4)`, and +320K environment
  steps. This is 40 policy-update cycles and 15,000 recurrent low-PPO minibatch
  optimizer steps per arm (`15` epochs, `800` sequence chunks, batch `32`).
  Final task evaluation uses 20 deterministic episodes; final natural-process
  evidence uses 64 reset groups and the unchanged R26 analyzer. Expected total
  wall clock is 5-10 hours.
- Preliminary decision metrics: actual-skill replay likelihood error must stay
  `<=2e-5`; complete segments and all four skills must be represented. Over the
  final 10 policy updates, `real_reward - probe_only` R29-T10 mean must be
  `>=0.05` with a positive paired-update bootstrap lower bound and no negative
  per-skill mean difference. R26 transfer requires real PASS while probe is not
  PASS and a `>=0.05` real-minus-probe full-minus-prior accuracy gain.
- Operational note: two launches failed before any optimizer update because
  CUDA GRU replay accumulated `2.6e-3`, then `1.3e-3`, numerical drift when its
  batch shape differed from collection. The scorer now anchors the natural
  column to PPO's stored old likelihood after removing the common tanh Jacobian
  and reports unanchored recurrent drift separately.
- Safety: real normalized skill entropy `>=0.8`, full-rollout intrinsic/env
  mean-absolute ratio `<=0.05`, deterministic task reward degradation `<=10%`
  relative to probe, and zero-throughput step-fraction worsening `<=0.10`.
- Branches: preliminary PASS -> external GPT-5.6 Pro review before deciding on
  the remaining paired seeds; MIXED -> external review of the frozen evidence
  with no retuning; FAIL -> run the research failure review and retire or select
  one externally justified revision; INVALID/crash -> repair only the failed
  operational path and resume the same contract.
- Prohibited while open: coefficient/clip/terminal-window changes, learned
  priors, high-level reward, task-reward changes, extra arms, extra seeds, and
  conclusions about cooperation, task improvement, or exact mutual information.
- Status sources: `<run-root>/runner_status.txt`, each arm's
  `metrics/train_updates.csv` and `metrics/eval_episodes.csv`, final R26 JSON,
  and `<run-root>/result/r29_t10_pair.json`.
- Result: completed `PRELIMINARY_FAIL` on the authorized single seed `29031`;
  `implementation_valid=true`, `r26_transfer_pass=false`,
  `score_pass=false`, and `safety_pass=false`.
- Mechanism evidence: probe-only retained an R26 `PASS` with post-minus-pre
  `0.061090`, full-minus-prior `0.073063`, and label entropy `0.998223`.
  The reward arm was `MIXED`, with post-minus-pre `-0.002817`,
  full-minus-prior `0.014952`, and label entropy `0.997911`. The reward therefore
  did not transfer the accepted natural differentiation signal.
- Paired score evidence: the final-window real-minus-probe mean was `0.031265`
  with bootstrap 95% interval `[-0.005331, 0.064452]`, below the registered
  mean threshold and without a positive lower bound.
- Safety evidence: deterministic task reward was `130.452` for probe versus
  `89.278` for reward, a relative degradation of `0.315623`; backhaul connected
  fraction also fell from `0.7776` to `0.6823`. Healthy label entropy does not
  override the failed task-safety gate.
- Decision: preserve this as a single-seed preliminary negative, not a
  three-seed scientific conclusion. GPT-5.6 Pro returned `RETIRE`; the raw
  response and disposition are under
  `docs/external-review/gpt5_6_pro/20260714_r29_t10_result/`. Retire the online
  same-action density-ratio family, keep R29 diagnostic-only, and move to the
  reward-off stochastic realized-effect edge recorded in
  `memory/LTM/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md`.

### EXP-20260713-r29-g0-counterfactual-action-information

- Hypothesis/edge: on natural on-policy observation and rollout-hidden states,
  the skill-conditioned low actor carries a support-native action signal:
  `z_i -> sampled action likelihood relative to the uniform counterfactual-skill
  mixture`. The density ratio uses the same raw action under all candidates, so
  the tanh Jacobian cancels.
- Comparator/baseline: hierarchy-L1 reward-off diagnostic. Active source-skill
  likelihood is paired with a cyclic-label sham and inactive-FiLM identity
  control under identical states and Gaussian noise.
- Sources/exposure: fixed R25 arm0 update25/update30/final checkpoints and their
  64-reset R27 natural snapshots; 8 Monte Carlo samples per row/skill, seed
  `29001`; reset bootstrap 2,000 reps, seed `29002`; local CUDA with three
  checkpoint workers, expected 2-5 minutes; zero environment steps, optimizer
  updates, and reward-applied steps.
- Checkpoint gate: at least 5,000 rows and 48 resets; natural-label normalized
  entropy `>=0.8`; active mean `>=0.01` nats; every skill mean `>=0.005` nats;
  active-minus-sham reset-bootstrap lower bound `>0`; inactive maximum absolute
  reward `<=1e-6`. Family PASS requires final PASS and at least 2/3 checkpoints.
- Result: all three checkpoints PASS. Active means are `0.017050`, `0.017990`,
  and `0.019208` nats; minimum skill means are `0.008170`, `0.013948`, and
  `0.015080`; real-minus-sham lower bounds are `0.043887`, `0.043184`, and
  `0.048487`; inactive maximum absolute reward is `5.96e-8`.
- Branches: PASS -> run one bounded mechanism-matched reward comparator; FAIL -> retire the
  individual action-information target; INVALID -> repair evidence code only;
  UNDERPOWERED -> add snapshot support under the unchanged contract only.
- Fixed while open: source checkpoints/snapshots, rollout hidden state, uniform
  four-skill mixture, cyclic sham, inactive control, common noise, seeds,
  thresholds, zero reward, and zero updates.
- Runner: `scripts/run_r29_action_information_local.ps1`; status source is
  `logs/r29_action_information_20260713_230631/r29_action_information.json`.

### EXP-20260713-r28-forced-execution-support-transport

- Edge/comparator: under the final R25 forced hold, compare deterministic and
  six-agent stochastic environment execution from the same reset/prefix using
  common policy noise; both modes score only their same-forward deterministic
  action means with the frozen G0 support envelope. This is hierarchy-L1,
  reward-off evidence.
- Exposure: final checkpoint only; resets `0..63`, focal agent `reset_id % 6`,
  four labels and four native duration windows per mode; 111,100 environment
  steps, zero optimizer updates and zero reward; local CUDA with four reset
  workers, expected 15-30 minutes.
- Gate: at least 48 paired rows per label-duration cell. Deterministic source
  replication and stochastic transport each require overall and every cell OOD
  `<=0.20`.
- Branches: stochastic PASS -> test forced versus natural renewal under matched
  stochastic execution; stochastic FAIL after deterministic PASS -> retire the
  forced-deterministic scorer family from online reward; deterministic failure
  -> `INVALID` source/evidence repair only; insufficient paired cells -> add
  support only under the unchanged contract; crash -> operational repair.
- Fixed while open: checkpoint, prefix/reset seeds, forced roster, feature
  function, scorer/support, thresholds, common noise, zero reward, and zero
  optimizer updates.
- Result: deterministic overall OOD `0.068359` and cell maximum `0.109375`
  validate source replication. Stochastic overall OOD is `0.823242`; 15/16
  cells exceed `0.20`, and the four action-std residuals average
  `10.60-14.08` sigma. Classification is
  `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`.
- Decision: retire this scorer family from online reward use and return to a
  support-native observational target. No scorer refit, threshold relaxation,
  reward test, or natural-renewal follow-up is authorized by this result.
- Runner: `scripts/run_r28_support_transport_local.ps1`; status source is
  `logs/r28_support_transport_20260713_222807/r28_support_transport.json`.

### EXP-20260713-r28-g1-causal-skill-forcing-reward

- Scientific status: the planned hierarchy-L2 matched three-arm comparator at
  promotion stage 3 was never opened, so R28-G1 has no reward-efficacy result.
- Engineering evidence: seed 28030, CUDA, one environment, +500 steps, and one
  low PPO epoch/update in each exact local smoke. The runs produced 81/80
  structurally eligible rows, OOD `0.950617`/`0.9375`, one support kill each,
  and zero R28 reward-applied steps.
- Diagnosis: G0/G1 feature order, deterministic-action evidence, duration
  indexing, source identity, and support-distance formula match. The second
  run's distance/threshold mean was `94.9766`; all four temporal action-standard-
  deviation residuals were `12.64-20.39` sigma while means/slopes were much
  smaller. This is a genuine forced-to-natural trajectory support mismatch,
  not an `INVALID_MAPPING` repair branch.
- Decision: block and retire this frozen G1 launch package. Preserve the scorer
  and thresholds; do not refit, relax, rerun the same smoke, or launch formal
  training. This does not imply that a support-compatible reward would fail.
- Next causal action: the reward-off matched-domain transport diagnostic in
  `memory/LTM/R26_R27_R28_FAILURE_REVIEW_20260713.md`.
- Frozen unexecuted contract: retained in
  `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md`.
- Status sources: this dashboard and the two local smoke roots above.

## Completed Evidence and Archive Pointers

The completed G0 protocol is frozen in the R28 design and its row points to the
raw run artifacts. R27-G2 and prior completed detail are in
`memory/LTM/EXPERIMENT_ARCHIVE.md`; earlier imported records remain in
`memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`.
