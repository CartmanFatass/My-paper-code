# HA-CTSE Experiment Dashboard

Updated: 2026-07-13

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
| EXP-20260713-r28-g1-causal-skill-forcing-reward | planned — implementation complete; formal training not authorized | level-3 mechanism-matched three-arm continuation | no formal run root opened | none until a formal launch is authorized | zero G1 formal steps; former remote topology job superseded unqueued | Formal launch remains blocked on a separately authorized matching topology check. |
| EXP-20260713-r28-g0-action-process-target-calibration | completed — accepted `PASS_TARGET_NULLS` 2026-07-13 | diagnostic-null calibration before any level-3 reward | cloud RTX 4090 CUDA; run `logs/r28_g0_action_process_target_20260713_175600`; commit `3eb22d5` | none; preserve scorer as frozen input to later review | final and update30 PASS; update25 FAIL only on train-test gap; validated scorer `r28_g0_scorer_final.pt`; zero env steps/policy updates | Accept the offline target/null gate only. This freezes the final scorer and permits focused G1 package implementation review; it does **not** authorize reward implementation launch or any team/cooperation claim. |
| EXP-20260712-r27-g2-forced-z-trajectory-effect | completed — accepted `PASS_BEHAVIOR_EFFECT` 2026-07-13 | level-2 reward-off forced-`z_i` trajectory/effect intervention | cloud RTX 4090 CUDA; run `r27_g2_overnight_20260713_095408`; commit `6c06cde` | none; preserve beside R26 natural negative | 192/192 `OK` shards; aggregate validation `valid=true`, `scientific_status=PASS`; A/B1/B2/B3/C PASS at update25/update30/final | Accept forced persistent conditional behavior and local effect through native H40 only. Record `FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`; do not infer natural selection, reward usefulness, cooperation, task gain, or async-lifetime benefit. |
| EXP-20260711-r27-g1-low-actor-capacity-autopsy | completed — accepted 2026-07-12 | reward-off immediate-capacity autopsy | cloud CUDA; 64 reset groups; R25 arm0 update25/update30/final | none | `dist/r27_g1_capacity_autopsy_cloud64_20260712_151313_extracted/`; result read under `logs/r27_g1_result_read_20260712/` | `STATIC_USED_OBSERVATIONAL_MISS`: immediate `z_i`-conditioned action-distribution sensitivity exists; persistence/effect were not established by this gate. |
| EXP-20260711-r26-g1a-individual-skill-screening | completed — accepted natural observational negative 2026-07-12 | reward-off natural behavior-window screen | local CUDA; six frozen R25 checkpoints | none | `logs/r26_g1a_screening_20260711_105522/` | Primary arm0 family FAIL: final FAIL and update25/update30 MIXED. Arm2 is contextual only. Preserve this result unchanged beside R27 forced evidence. |
| EXP-20260710-r25-qa-verification-1m | standing-reference | 1M HA-CTSE verification | cloud CUDA, 64 env, arm0/arm2 | none | `dist/logs_cloud_r25_qa_verification_1m/`; `gate_read_r25_seed1.md` | arm0 outperformed q_A arm2 late; q_A reward remains default-off. Single-seed parity remains open; do not rerun these arms. |
| EXP-20260709-r24-frozen-qd-null-probes | completed — accepted FAIL 2026-07-09 | frozen `q_d` diagnostic-null probes | cloud archive plus local analysis | none | `dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/` | Under tested policies/setup, 3/4 collapsed. Old `q_d/q_D` reward line remains blocked; no target/coefficient sweep. |
| REF-20260617-hmasd-baseline-s7s1-seed1 | standing-reference | HMASD S7-S1 reference | local 32 env; stopped cleanly at 2.112M/3.2M steps | none | `logs/hmasd_baseline_read_20260709/metric_extract.md` | Coverage first reached 0.7 at 480k and 0.9 at 800k; late mean 0.9639. Reference-only because env/update exposure differs; do not rerun. |

## Current Gate Detail

### EXP-20260713-r28-g1-causal-skill-forcing-reward

- Causal edge/hypothesis: given the R27-proven forced executor capacity, a
  bounded residual for `distinct z_i -> naturally expressed, behaviorally
  differentiated skills` makes natural real-label behavior exceed matched
  probe-only and sham-reward continuations without task collapse.
- Comparator/baseline level: level-3 mechanism experiment with paired
  `probe_only`, marginal-preserving `sham_reward`, and `real_reward` arms. R25
  arm0/HMASD are fixed references and are not rerun.
- Frozen source/nulls: exact R25 arm0 final at 1,000,000 steps/update 32; sole G0
  final scorer; capacity-matched context and pre-window heads; same-row sham
  labels; common real-label support. No communication/task field enters the
  intrinsic score.
- Exposure/topology: seeds 28031/28032/28033; +160,000 steps (updates 33..52),
  16 envs, rollout 500, low PPO epochs 15; three arms concurrent per seed;
  deterministic 20-episode evaluations at +80k/+160k. Expected end-to-end cost
  is 6-10h only after a separate three-worker topology PASS; serial/CPU fallback
  is forbidden.
- `HMASD-R28-G1-TOPOLOGY-20260713-195737` was never queued or executed and is
  superseded. Formal training remains unauthorized.
- Metrics/thresholds: real R26 PASS at least 2/3 while each control is below 2/3;
  clustered `real - max(probe,sham)` full-minus-prior gain estimate >=0.05 and
  95% lower bound >0; pooled held-out `s_real` and `s_real-s_sham` lower bounds
  >0; entropy >=0.80; OOD <=0.20; per-rollout reward/env ratio <=0.05; zero
  kill-switch events; every seed return regression <=10% and zero-throughput
  worsening <=0.10 versus its better matched control. Bootstrap seeds are
  28034/28035/28036 with 10,000 reset-cluster repetitions.
- Outcome branches/single actions: PASS -> design one separate long-run
  verification; FAIL -> retire this target and complete the R26/R27/R28 failure
  review; MIXED -> review one causal disagreement only; UNDERPOWERED -> repeat
  support collection only; INVALID -> repair the evidence path/instrument and
  repeat the unchanged gate once; crash -> operational repair only.
- While open: do not refit the scorer, change thresholds/seeds/exposure,
  actor/critic/PPO/GAE/collector semantics, other rewards, task fields, standing
  references, or reinterpret the edge as cooperation/team complementarity.
- Status source: this dashboard. No G1 formal compute evidence or topology
  marker exists yet.

## Completed Evidence and Archive Pointers

The completed G0 protocol is frozen in the R28 design and its row points to the
raw run artifacts. R27-G2 and prior completed detail are in
`memory/LTM/EXPERIMENT_ARCHIVE.md`; earlier imported records remain in
`memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`.
