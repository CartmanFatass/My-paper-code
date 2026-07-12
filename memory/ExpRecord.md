# HA-CTSE Experiment Dashboard

Updated: 2026-07-13

Purpose: factual current experiment state. ExpManager records experiment
content, running state, commands, package paths, and result facts here.
LongTimeMemoryManager decides how these facts affect current memory and LTM
archives.

## Protocol

Before launching or recommending an experiment, keep one dashboard row here and
record enough factual detail for LongTimeMemoryManager to decide any archive or
project-memory update.

Required dashboard columns:

```text
ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision
```

Status vocabulary:
`planned`, `launch-ready`, `running`, `completed`, `stopped`, `failed`,
`invalid`, `superseded`, `blocked`, `standing-reference`.

**Standing-reference rule (user directive, 2026-07-10):** rows marked
`standing-reference` are fixed comparison data — the HMASD baseline curve
(REF-20260617) and the completed HA-CTSE baseline/control arms (R25 arm0/arm2
archives). Future experiment designs MUST reuse these archived curves and
checkpoints instead of re-running them; do not include an HMASD arm or a
repeat baseline arm in new runner scripts. A new control arm is justified only
when a config change makes the archived control incomparable (e.g., env-count
or scenario change), and that exception needs explicit user approval in the
experiment brief.

## Current Dashboard

| ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-20260712-r27-g2-forced-z-trajectory-effect | planned — implementation and focused verification complete; Git-based cloud prepare pending server wake-up; pilot and launch not authorized | R27-G2 reward-off forced-`z_i` trajectory/effect intervention | planned cloud CUDA; registered user-provided R25 arm0 update25/update30/final checkpoint slots; 64 reset groups; 55 branches/reset; no scientific run root exists | Controller | notify user before server use; then separate pilot/launch and concurrency decision | `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md`; raw review `docs/external-review/R27_G2_design_review_20260712_Claude.md` | Design disposition `ACCEPTED_WITH_MODIFICATIONS_AS_DESIGN_ONLY`; implementation does not change the scientific contract. Exact decision-grade Stage 1 is 2,124,000 env steps plus diagnostic forwards, estimated 12-20h cloud CUDA. No experiment has run. |
| EXP-20260711-r27-g1-low-actor-capacity-autopsy | completed — downloaded archive verified and controller disposition accepted 2026-07-12 | R27-G1 reward-off low-actor capacity autopsy | cloud CUDA, 64 parallel subprocess envs, exactly 64 total reset groups, exact R25 arm0 update25/update30/final checkpoints; run `logs/r27_g1_capacity_autopsy_cloud64_20260712_151313/` | Controller disposition complete | no rerun; standing evidence for R27-G2 only | `dist/r27_g1_capacity_autopsy_cloud64_20260712_151313_extracted/`; `logs/r27_g1_result_read_20260712/reports/expmanager_intake.md`; `r27_capacity_autopsy.{json,md}` under the extracted run root | Controller accepts `STATIC_USED_OBSERVATIONAL_MISS`, narrowly immediate `z_i`-conditioned action-distribution sensitivity. Static and synthetic families PASS 3/3 with artifact identity PASS. Persistence, downstream effect, reward usefulness, and task improvement remain unverified. |
| EXP-20260711-r26-g1a-individual-skill-screening | completed — six arms succeeded and controller result boundary accepted 2026-07-12 | R26-G1a reward-off screening | local CUDA (RTX 4070 Laptop 8 GB), six frozen R25 checkpoints | Controller disposition complete | no rerun; preserve as natural observational negative beside R27 forced-capacity evidence | `logs/r26_g1a_screening_20260711_105522/`; six per-arm `analysis/r26_g1_behavior.{json,md}` artifacts | Batch succeeded 6/6; all analyzers valid and adequately powered. arm0 final is FAIL, update25/update30 are MIXED, so no arm0 checkpoint passes and the primary arm0 family is FAIL. All arm2 checkpoints are MIXED and contextual only. Reward remains off. |
| EXP-20260710-r25-qa-verification-1m | completed / read + dispositioned 2026-07-10; arm0/arm2 archives now standing-reference (DO NOT RE-RUN — user directive 2026-07-10) | R25 verification tier | cloud CUDA / 64env / 1M steps / two arms (arm0 control, arm2 q_A) | ExpManager + ResultAnalyst + marl-peer-reviewer | all variants read; cross-seed single-seed gate analysis complete | `dist/logs_cloud_r25_qa_verification_1m/` (cloud archive); `gate_read_r25_seed1.md` (result analyst read); peer review Round 6 archived in `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` | arm0 arch-only beats arm2 q_A at 640k-960k (coverage 0.235→0.417 vs 0.052→0.113; throughput 13.76 vs 2.81 Mbps @960k); neither reaches HMASD milestones (0.7@480k, 0.9@800k); q_A reward demoted to default-off by Round 6 peer review (NOT VERIFIED at 1M verification gate under n=1 single-seed setup); parity OPEN (update-count confound: 32 updates vs HMASD ~2×/step). |
| EXP-20260709-r24-frozen-qd-null-probes | completed — 4/4 analyzed (3 CPU, qAoff/seed2 on GPU per user directive); external peer review Round 5 completed; disposition ACCEPTED 2026-07-09 | R24 frozen q_d null probes | cloud archive `dist/logs_cloud_r24_frozen_qd_overnight_20260709_005624/` + local analysis complete | ExpManager + ResultAnalyst + marl-peer-reviewer | all variants read; cross-seed synthesis complete | Archive complete; peer review Round 5 text archived in `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` | R24-1 FAIL accepted 2026-07-09 (Round 5, SUPPORTS_WITH_CONDITIONS). Wording condition: "fail under tested policies and current diagnostic setup" (3 of 4 collapsed). D2 sensitivity re-run approved-deferred with conditions. D3 pivot direction accepted pending deconfound. q_d/q_D rewards remain BLOCKED. |
| REF-20260617-hmasd-baseline-s7s1-seed1 | standing-reference (completed; stopped at 66% budget, clean; DO NOT RE-RUN — user directive 2026-07-10) | HMASD baseline reference curve | local, 32env, rollout 500, metrics-light; `C:\project\tf-logs\hmasd\energy-S7-S1\...\20260617_133148` | ResultAnalyst (read 2026-07-09) | none — reference | `logs/hmasd_baseline_read_20260709/metric_extract.md` | HMASD S7-S1 pace/ceiling reference (seed1): eval coverage >=0.5 and >=0.7 first at 480k, >=0.9 at 800k; plateau ~0.95-0.99 from ~800-960k; final-window (1.76M-2.08M) coverage mean 0.9639, reward mean 380.29; zero-coverage eval episodes gone from 640k. Run stopped externally at 2,112,000/3,200,000 steps, no crash. Caveats: 32env (vs 64env HA-CTSE cloud runs), predates parity metrics (no coverage_eq1 fields), single seed. |
| EXP-20260708-r24-qd-null-control-cloud-handoff | completed | R24 | cloud CUDA / 64env package | ExpManager + controller | ResultAnalyst to read metrics from the completed cloud archive before any q_d/q_D reward decision | `dist/ha_ctse_r24_qd_null_control_cloud_runtime_20260708_190315.zip`; `dist/r24_qd_null_control_log_extract_expmanager_20260708_230322`; `scripts/run_r24_qd_null_control_cloud_64env.sh`; default log root `logs_cloud_r24_qd_null_control_64env` | Cloud archive inspected. Both seeds finished with `exit_code=0` and `total_steps=320000`. Seed1 final eval row: `reward=52.852671269315316`, `coverage_ratio=0.8`, `system_throughput_mbps=8.611111111111114`, `backhaul_connected_step_fraction=0.51`, `zero_throughput_step_fraction=0.49`. Seed2 final eval row: `reward=-4.881497951854478`, `coverage_ratio=0.0`, `system_throughput_mbps=0.0`, `backhaul_connected_step_fraction=0.0`, `zero_throughput_step_fraction=1.0`. No `Traceback`, `RuntimeError`, `NaN`, `OOM`, or `BrokenPipe` matches were found in the runner logs. |
| EXP-20260707-r24-assignment-to-behavior-bridge | completed / blocked | R24 | local CUDA diagnostics | ExpManager | run matched-null forced-audit controls A-D, then reward-off behavior-window q_d probe; set `q_D/q_d` reward decision only after gate pass | `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/r24_forced_behavior_audit.py`; `logs_r24_qd_probe_local_cuda/seed1`; `logs_r24_behavior_audit_local/r24_behavior_audit.csv`; `logs_r24_behavior_audit_smoke/r24_behavior_audit.csv` | forced-audit signal is positive but insufficient for reward gating. q_d probe is near-null (`residual_gain=0.01105`, `positive_frac=0.52855`) and cannot justify reward-on. `q_D` and `q_d` rewards remain blocked pending matched-null controls + behavior-window `q_d` gate pass (`effect_ratio_h50>=1.3` + `h50-h10` growth + `between_within_ratio_h50>1.2`). |
| EXP-20260707-r24-assignment-to-behavior-bridge-overnight | completed | R24 | local CUDA / `logs_r24_overnight_existing_local_cuda/run_20260708_000836` | ExpManager | checked arm-level `runner_status.txt`, `runner_output.log`, audit/train tails, and `_watch/watch_state.json` | `scripts/run_r24_overnight_existing_local_cuda.ps1`; `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/run_r24_qd_probe_local_cuda.ps1`; `scripts/watch_r24_overnight_existing.ps1`; `scripts/codex_r24_alert_handler.ps1`; `logs_r24_overnight_existing_local_cuda/run_20260708_000836/arm*` | one-click local overnight runner completed with `NResets=64`, `NumEnvs=16`; all five arms finished with `exit_code=0`. |
| EXP-20260707-r23-next-mechanism-matrix | completed / mixed (local 16env, single seed) | R23-next | local CUDA; cloud candidate | ExpManager | optional cloud 64env rerun for a matched-env task read + q_D-probe upgrade | `logs_r23_next_mechanism_matrix_local`, `scripts/run_r23_next_mechanism_matrix_local_cuda.ps1`, `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh` | q_A actionability VALIDATED (Z->xi learnable: arm2 residual_gain +0.222, forced-Z KL 0.059->0.070). q_D target audit NULL across all targets/H (underpowered caveat) -> xi->recoverable-joint-effect still unestablished. Task encouraging @160k (cov 0.303 ~3x control) but confounded. Next lever = individual-skill/discoverer half + stronger q_D probe, NOT more q_D targets. Local 32env OOMs (31.6GB box); use 16env locally or 64env cloud. |
| EXP-20260706-r23-actionable-team-intent | completed / mixed | R23 | cloud CUDA seed1 | ExpManager | none unless comparing to R23-next | `dist/logs_cloud_r23_actionable_team_intent_64env` | Architecture capacity passed; g-info objective and q_D target failed/null. This motivates q_A residual and q_D target audit. |
| EXP-20260705-r21-team-intent | completed / negative | R21 | cloud CUDA seed1 | ExpManager | none | `dist/logs_cloud_r21_team_intent_64env`, `memory/R21_AUTOPSY_REPORT.md` | Z was near-inert; sampled team code did not create recoverable team effect. No seed2 or sweep on this design. |

## Active Experiment Detail

### EXP-20260712-r27-g2-forced-z-trajectory-effect

Factual record for the controller-frozen R27-G2 design. The user authorized
implementation and focused verification on 2026-07-12; both are complete.
No pilot, scientific run root, or scientific result exists yet.

- Project provenance/validation policy (2026-07-12 user decision): Git is the
  sole source-version manager. Active HMASD workflows do not add content
  digests for source, checkpoints, state, packages, shards, aggregates, or
  downloaded results. R27-G2 registers checkpoint paths plus loaded update and
  total-step metadata, compares module/ValueNorm/environment/RNG/runtime values
  directly where scientific validity requires it, and rebuilds derived
  aggregates from the current structured shards. Archives are checked by their
  native readers and expected inventory. This policy change launched no
  experiment and changes no statistical threshold.

- Status: `planned`; design disposition
  `ACCEPTED_WITH_MODIFICATIONS_AS_DESIGN_ONLY`
- Hypothesis: when one focal agent's label is held through the live recurrent
  executor, the frozen R25 arm0 actor produces temporally sustained and
  held-out label-consistent action-process differences that exceed a matched
  10-step pulse; a separate effect gate tests the benchmark-local focal full
  observation.
- Causal edge / mechanism path:
  `individual z_i -> focal low-actor FiLM -> live recurrent action process ->
  persistent executable behavior`, with local effect as separate supporting
  evidence.
- Comparator and baseline level: diagnostic and within-mechanism controls at
  the lowest sufficient hierarchy. Every comparison uses the same stochastic
  natural prefix, exact fresh-environment action replay, complete runtime
  restoration, frozen team code/non-focal skills/clocks, and deterministic
  post-branch execution. Controls are one unforced reference, matched
  natural-label holds, 10-step pulses, and paired inactive labels.
- Registered source checkpoint slots: R25 arm0 update25/update30/final only, registered
  by path and loaded update/step metadata. They are temporal observations, not
  independent seeds. R25 arm2 and HMASD are standing references outside this
  executor intervention and are not rerun.
- Exact unit and matrix: 64 reset groups, seeds 1..64, one prefix context per
  reset with 50/150/250 steps assigned 22/21/21, and 55 branches per reset
  (1 reference + 24 hold + 18 pulse + 12 inactive). One 50-step branch yields
  nested gated windows 1-10, 11-20, and 31-40. H50 is descriptive stress only.
- Prefix policy sampling seed is `27100 + reset_id`; prefixes must use isolated
  reset jobs/processes or sequential reseeding because the source samples from
  global Torch RNG.
- Source duration correction: R25 uses `skill_interval=10` and duration
  candidates `[1,2,3,4]`, hence native individual targets 10/20/30/40
  primitive steps. The external review's assumed `{3,7,13,24}` source
  durations do not apply.
- Primary metrics: Gate A immediate static replication; B1 late instantaneous
  label-swap controllability and retention on hold-induced states; B2 hold-
  minus-pulse late deterministic executed-action (`tanh(mu)`) magnitude,
  separation, and ratio; B3 fixed 12-feature executed-action per-agent
  held-out linear label decoding; Gate C benchmark-local hold-minus-pulse focal
  full-observation effect at H40.
  Thresholds, bootstrap seeds, decoder split/optimizer, support floors, and
  classification precedence are frozen in the design file before any pilot.
- Null/validity contract: fresh replay observation/state/RNG/runtime parity;
  live-versus-diagnostic distribution/hidden parity; same-natural-label
  bitwise identity; paired focal-only inactive-label identity; deterministic
  CUDA; per-step matched environment-RNG equality through H40; no policy RNG
  consumption, non-finite values, checkpoint-file/full-`state_dict` mutation,
  episode crossing, focal failure, or CPU fallback. A contract failure is
  `INVALID`; inadequate support is `UNDERPOWERED`.
- Decision-grade support: 64 reset clusters per checkpoint, at least 48 valid,
  prefix-stratum floors 14/14/14, hold-cell floor 40 distinct resets, and each
  pair contrast in at least 40 distinct resets. Decoder floors are
  train/validation/test 32/9/9 with per-prefix floors 10/10/10 and 3/3/3.
  Ten-thousand-reset-cluster bootstrap; no checkpoint pooling as seeds.
- Family gate: Gate B must pass at least two of three checkpoints. Stable
  effect requires B+C at least two of three, but only after all three
  checkpoints are valid and adequately powered. Any invalid/underpowered
  checkpoint makes the family invalid/underpowered. Partial valid patterns are
  `MIXED`; the exact decay/no-hold-advantage/chance-decoding pattern is
  `TRANSIENT_ACTION_NUDGE`, while other all-negative patterns are
  `NO_PERSISTENT_SEPARATION`.
  Three-of-three fully valid negative checkpoints trigger abandonment review
  for this frozen checkpoint family, not automatic representation removal.
- Core MARL impact: diagnostic only. The design changes no reward,
  actor/critic/FiLM/GRU architecture, optimizer/loss/advantage logic, training
  collector, environment dynamics, credit assignment, team intent, or latent
  semantics.
- Expected cost/device: exactly 708,000 environment steps per checkpoint and
  2,124,000 total, plus diagnostic forwards and decoder fitting. Conservative
  decision-grade estimate 12-20 hours on cloud CUDA. An optional, separately
  authorized eight-reset wiring pilot is under 90,000 environment steps and
  may cost 30-60 minutes with a safe flat 64-job queue or about 3-5 hours
  with only eight reset workers. No CPU fallback.
- Remote automation (mechanical, no experiment run): HMASD now reuses the
  already-installed AutoDL key pair for the same `root` endpoint through the
  separate non-secret alias `hmasd-autodl`. On 2026-07-12, BatchMode SSH,
  `/root/miniconda3/bin/python3` CUDA availability, required remote tools,
  GNU `screen`, and all three registered non-empty checkpoint paths passed
  preflight. The system filesystem had about 6.6 GiB free, while the distinct
  `/root/autodl-tmp` data filesystem had about 50 GiB free. The wrapper rejects
  package/checkpoint/log/result roots outside `/root/autodl-tmp/HMASD/` and
  requires at least 20 GiB free. On 2026-07-12 it staged
  the registered update25, update30, and final checkpoints under
  `/root/autodl-tmp/HMASD/checkpoint_dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/`.
  The source files under `/root/HMASD/dist/` were not deleted. Authorized long
  work runs in a recorded detached `screen` session; final wait/collection
  revalidates all 192 reset artifacts and regenerates aggregate reports from
  the current structured inputs. The default
  `prepare` remains non-launching. No experiment was launched. `launch` and
  `all` additionally require the exact experiment authorization, a clean
  committed Git source scope, and an explicitly accepted/validated worker-cost
  topology.
- Git workflow update (2026-07-13, mechanical, no remote contact): source now
  comes only from a named, clean data-disk Git checkout updated by
  `fetch`/`checkout`/`pull --ff-only`; the former local ZIP and deployed copy are
  historical review artifacts only. The runner always regenerates its aggregate
  from the current 192 shards. All 154 targeted Python, PowerShell, runner, and
  watcher tests are covered and pass; task-created pytest temporary directories
  were removed. The server remained asleep as requested. A new non-launching
  `prepare` requires committed/pushed source and prior user confirmation that
  the server is awake. A dirty source tree cannot pass the launch gate.
- Local-compute audit after the user's migration request: PID 48760 was an
  `SB3`-environment regression process and had already exited. A full process
  check found no remaining local Python/HMASD/IMOD training or WSL experiment;
  no live experiment state existed to migrate or stop. Future compute-bearing
  HMASD work remains cloud CUDA by default.
- PASS branch: a Gate-B family pass supports persistent conditional control
  under forced hold only. B+C permits only separate design/review of a task-
  generic reward target and its own nulls; Gate C cannot become reward, and no
  reward test or activation is enabled.
- FAIL/MIXED branch: complete the R26/R27 failure review before a core
  algorithm or objective change. Preserve negative constraints.
- UNDERPOWERED branch: increase support only with unchanged metrics and
  thresholds. INVALID/crash branch: repair the instrument/operation and repeat
  the unchanged gate; at most one genuine invalid-fix cycle before escalation.
- Do not change yet: no R27-G2 pilot, launch, natural-renewal Stage 2, H100,
  reward, actor/GRU/FiLM change, or long training. Implementation may only
  encode and verify the frozen diagnostic contract.
- Status source: controller-frozen design
  `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md`; raw
  user-supplied Claude response
  `docs/external-review/R27_G2_design_review_20260712_Claude.md`.
  The exact Claude model/version was not supplied.

**Implemented diagnostic unit**: the strict-source focal-only live-stateful
hook applies active/neutral FiLM, advances actor and critic hidden exactly once,
returns distribution/action/value/new-hidden evidence from the same transition,
and leaves roster/clocks unchanged. Focused verification is complete.

**Open gate**: a separate user decision is required for a pilot or launch.
Before even non-launching server `prepare`, commit/push the intended Git source,
notify the user, and wait for confirmation that the sleeping server is awake.

## Completed Experiment Detail

Long-form detail for completed runs (R27-G1, R26-G1a, R25, R24 x4, R23 x2) was
rotated to `memory/LTM/EXPERIMENT_ARCHIVE.md` on 2026-07-13. The dashboard rows
above carry the status, artifacts, and decision for each; read the archive only
for the underlying numbers.

Only the **active** experiment keeps its full detail in this file.

## Archive Pointers

- Full pre-compaction experiment record:
  `memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`
- LongTimeMemoryManager-owned detailed experiment archive:
  `memory/LTM/EXPERIMENT_ARCHIVE.md`
