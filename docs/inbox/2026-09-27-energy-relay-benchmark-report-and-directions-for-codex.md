# energy_relay_benchmark: report for Codex and proposed directions (2026-09-27)

Written by the Claude DM of `energy_relay_benchmark` at the owner's request ("write a report in
docs/inbox for Codex, give some Directions to it"). This is evidence and advice, not authority:
`docs/project/OPERATING_CONSTITUTION.md` prevails, Root keeps cross-direction coordination, and
nothing here opens a direction, assigns a lead or asks for a reply. Every number below is read
from committed records under `docs/research/candidates/energy_relay_benchmark/` and
`runs/energy_relay_benchmark/`; the notebook entries are named where a claim needs its context.

**Corrections (2026-09-27, after the owner's check; the text below is already corrected):**
(1) The B01 traces do NOT hold action proposals, submitted actions or full observations
(`experiments/candidates/energy_relay_benchmark/b01/evaluation.py::evaluate_world` stores per-step
positions, modes, shield entries/exits, charging, waiting, battery, dock bit, guard counts, return
margins, station choices/distances/occupancy/queues, heuristic targets, rewards and metrics). D2's
pre-clip action diagnosis and D4's imitation warm start therefore need new collection with an
extended trace, not the stored files. (2) D3 names a phenomenon, not an explanation: before any
reward/credit hypothesis the two signals must be made comparable (worlds, policy snapshot, action
mode, aggregation), and a squashed decode of the same weights is a different policy, not an
evaluation correction. (3) The first version cited the 30-day freeze and "answer DECIDE-1/2/4
first"; both were withdrawn in the direction's own follow-up
(`docs/Claude_docs/reviews/RESET_RESPONSE_AND_FIRST_STUDY_20260926.md`, section 10: freeze and
Root-dissolution wording withdrawn, venue class deferred as non-blocking). Nothing below waits on
them. (4) Allocation done by Root on 2026-09-27 (`docs/Claude_docs/inbox/CODEX_TWO_DM_ALIGNMENT_20260927.md`):
D1 (+ D4 as a revisable successor) → `energy_relay_baselines`, D2 + D3 → `energy_relay_diagnostics`;
this direction keeps the accepted B02 study and its declared readings only, and will not declare
the cross-seed or imitation follow-ups itself. Updated 2026-09-27 (Root commit 4220ecd4f, owner
ceiling raised to five tracks by eda9fae04): four Codex DMs — D4 moved to `energy_relay_imitation`
(DM3, BC-only closed loop first), D5's native S4 part to `energy_relay_availability` (DM4, 0-fit
references first), Milan deferred, D6 engineering on need; DM1 keeps D1 and chooses its comparison
after this direction's complete development curve is published; DM2 unchanged.

摘要（中文）：在冻结的 S7-S2/H3000 宿主上，本方向已用零训练参照把"学习器亏在哪里"定量化——
中心式固定航点启发式 .774 QoS/步、局部信息启发式 .597、B09 学习器 N .328；亏损在部署（布局）而非
护盾的离站时机；仅靠生产护盾的站点访问，一支闲置机队就有 .23，两站航点包再加 .147。第 1 阶段一个
1.2M 曝光的 SET 开发 fit 在 40 万转移达到 N 的水平，60 万时确定性 .325 / 采样 .345，仍远低于 .597；
训练时信号与冻结评估信号脱节，确定性评估下贴墙停驻是评估模式依赖的现象。首个进程在第 117 个
rollout 因原生内存故障退出，已从 c03 续跑（学习器状态完整恢复），c06 与留出集读取预计 05:15–06:30
UTC 之后完成。下面给 Codex 的建议方向按 TRIED / RECORDED / NEW 标注，并说明可复用的工具与节点时间。

## 1. State of the direction (facts)

Host: frozen S7-S2/H3000 (8 UAVs, 3000-step episodes, B06 production shield enter 0.00 / exit
0.05 with 3 m/s return pricing, backhaul guard). Development worlds 955001–955032; hold-out
957001–957032 reserved, read once. Practical QoS/step threshold .03 (B01).

| Study | What | Result | Record |
| --- | --- | --- | --- |
| B01 (0 fits, 540 episodes, ≈ 2 h node) | Zero-training references and N's deployment on the production shield | H_central .774 QoS/step (J 2282), H_local .597 (J 1628), N .328 (J 955). Branch (b): the learner's loss is its deployment, not the shield's exit timing; exit width is not an S7 loss. Unregistered: an enter margin .20 lifts N by +.048–.079 (a package effect, mechanism open), lowers H_central. | NOTES "B01 result read by the pre-registered branches"; `b01_ref_a02_readings.json` |
| Stage 0 item 1 (0 fits) | N with sampled actions, two draws | .308 / .318 (pooled .313) vs deterministic .328: the deficit is the policy's, not a deterministic-evaluation artefact; boundary parking .22 sampled vs .50 deterministic, altitude floor .46 vs .70. Evaluation mode became a Stage 1 axis. | NOTES "Stage 0 item 1 result"; `b02_stage0_readings.json` |
| Stage 0 item 2 (0 fits) | Three fixed references | H_spawn .232 (hover at spawn), H_park2 .379 (park at the two stations), H_central with replan period 10 .769. Two-station waypoint package effect +.147 (32/32 worlds; common early window +.269); H's replan period insensitive (−.005). An idle team under the production shield alone reaches .23: shield-forced station visits produce service. | NOTES "Stage 0 item 2 result" and addendum |
| Stage 1 (1 fit, running) | One fixed-exposure SET development fit, 1.2 M transitions, shield on in training, checkpoints every 200k, both evaluation modes per checkpoint | c00 .209 / .243 (det / sampled) = H_spawn's level; c01 (204k) .241 / .250; c02 (402k) .318 / .303; c03 (600k) .325 / .345. Deterministic flat between c02 and c03 at N's level (−.003 vs N); sampled still rising (+.042), +.016 above N with a risk conflict flag (return cost 4.97, min battery .105). 0/32 worlds at .60 (H_local's level). | NOTES c00–c03 entries; `b02_stage1_readings.json` |

Diagnostics that travel with the numbers (c03): boundary parking under deterministic evaluation
receding .43 → .36 of normal-mode UAV-steps (.14 → .09 sampled); service before the first shield
entry .17 → .22 in both modes; first service step 206 / 254 (323 / 290 at c02): the c02 → c03
gain came from the pre-entry phase, not the shield-driven one. Training-time sampled QoS/step is
flat by 10-rollout blocks (.13–.21), a zero-service lane in 61 of 105 rollouts, action entropy
1.156 → 1.043, F-mode share rising .23 → .34, shield entries per rollout ≈ 114 → ≈ 170: the
collection-time policy oscillates through the shield while the frozen evaluations improve.

Operations. The first Stage 1 process died at rollout 117 (702k) at 23:45Z with
`SystemError: Objects/listobject.c:2529: bad argument to internal function` raised from
`np.clip` inside `envs/pettingzoo/relay/energy_aware.py` (`PyList_AsTuple` on a non-list: a
native memory-safety fault in a process holding CUDA, the pybind11 geometry backend and numpy;
one event in ≈ 2.6 M environment steps; not reproducible). It was resumed from c03 (weights,
optimizers, sampler RNG, value-normaliser statistics restored and checked; environment and action
streams re-seeded with a declared seed) as `b02_s1_set_a01r`, accepted 2026-09-27T00:38:32Z.
Expected: c04 ≈ 02:25 UTC, c05 ≈ 03:55, c06 ≈ 05:15; each checkpoint evaluation ≈ 15 min beside
the fit; the once-only hold-out read of c06 against the frozen comparators (already evaluated on
957001–957032 as `b02_holdout_refs_a01`, unread) after that. The direction then writes the Stage 1
result entry, asks for one independent scientific review, and declares Stage 2 or closes.

Measured costs on `wsl_4070` (20 cores, 15.8 GB, RTX 4070 Laptop 8 GB): 168 s per rollout of
2 × 3000 transitions → 1.2 M transitions ≈ 9.3 h; a 64-episode two-mode checkpoint evaluation
≈ 15 min with 8 CPU workers beside the fit; 160 reference episodes ≈ 28 min; runner RSS 2.4 GB;
GPU 6.9 GB free at launch. Two concurrent fits are plausible on memory; throughput under
contention is not measured (contended wall projections have overstated by 2.5× before).

## 2. What the evidence supports, and what it does not

1. **On this host, the competent reference is a fixed-waypoint heuristic, and the gap is large.**
   Any learner claim on S7-S2/H3000 now has a yardstick: H_local .597 (local information, same
   observation class as a decentralised learner) and H_central .774. N and the SET fit at 600k sit
   at .33–.35. This is the "missing heuristic feasibility reference" named in the 2026-09-26
   diagnosis, now measured.
2. **The learner's deficit is deployment, and part of the reference's service is the shield's.**
   A team that never moves scores .23 under the production shield; parking at the two stations
   scores .379; the learners' gains between checkpoints came before the first shield entry. Any
   reading of a learner on this host that does not split service into pre-entry / post-input
   phases and compare against H_spawn and H_park2 will misattribute shield-driven service to the
   policy.
3. **Evaluation mode changes the behavioural description more than the score.** Deterministic
   evaluation shows heavy wall parking (N .50, SET .43 → .36 of normal-mode UAV-steps) that
   sampled evaluation does not (.22, .14 → .09), while QoS differs by ≤ .03 in most panels. The
   canonical evaluation mode is a benchmark decision that has not been taken.
4. **Training signal and evaluation signal disagree.** Flat sampled training QoS with rising frozen
   evaluation QoS, 58 % of rollouts with a zero-service lane, and rising shield entries say the
   learner is optimising something the evaluation does not measure (return-cost term, override
   rate) or exploring under override. This is Pro's pre-registered explanation row with its proxy
   now observed; it is not yet a diagnosis.
5. **Not supported:** that SET (or any learner) will reach H_local at this exposure (the curve is
   half read); that the gap is a capacity problem rather than an objective/credit problem; that
   the enter-margin effect is a policy property (it is a package effect with an open mechanism).

## 3. Proposed directions for Codex

Marking rule: TRIED = executed with results in this repository; RECORDED = written down as a plan
or recommendation, not executed; NEW = neither. Each item names the first bounded study, its cost,
and what can be reused. The T1 track of the 2026-09-26 diagnosis
(`docs/Claude_docs/reviews/RESEARCH_PROGRAM_DIAGNOSIS_AND_RESET_20260926.md`) is what this
direction has effectively been building; the direction's follow-up response
(`RESET_RESPONSE_AND_FIRST_STUDY_20260926.md`, section 10) withdrew the 30-day freeze and the
Root-dissolution wording and deferred the venue class as non-blocking, so nothing here waits on an
owner decision beyond the ordinary rules (declare before running, one writer per path, Root's
cross-direction coordination, the node concurrency ceiling).

### D1. T1 baseline suite on the frozen benchmark task (RECORDED → execute)

Question: with seeds, where do the ordinary learners land relative to H_local / H_central on the
same panel, and what is the S7 seed SD? Arms: HMASD k=10 (B09's recipe, N is its single seed),
SET (this direction's recipe), LOCAL1 (recurrent PPO on local observations); 3 seeds each at
1.2 M transitions, both evaluation modes per checkpoint, hold-out once at the end. Status: HMASD
and SET TRIED at one seed; LOCAL1 on S7 NEW; seed SD on S7 NEW. Cost: 9 fits × ≈ 9.3 h ≈ 3.5
node-days serial; run two at a time only after measuring contended throughput. Reuse:
`scripts/run_energy_relay_benchmark_b02.py train` (SET; `--resume-from` for recovery) and
`evaluate-checkpoint`; the B01 evaluator with phase split, traces and diagnostics; the
`holdout-references` phase; `read_stage1.py` for the curve reading. What it delivers: the
results table and curves that the diagnosis calls paper 1's benchmark section. Reading protocol
to adopt as-is: gaps to H_central / H_local paired by world, H_spawn / H_park2 / N beside them,
milestone = H_local's level, service–risk conflicts reported as conflicts, no selection on the
development panel, hold-out read once.

### D2. Canonical evaluation mode and the wall-parking artefact (NEW, 0 fits first)

Question: is deterministic-mode wall parking a decoding artefact of the continuous action head at
the arena boundary (mean action saturating and being clipped), and should the benchmark evaluate
learners deterministically, with fixed sampled draws, or both? The stored traces cannot answer it:
they hold positions, modes, shield decisions, batteries, guard counts and heuristic targets, not
the proposed or submitted actions and not the observations. First study: 0 fits — extend the B01
trace with the proposed action, the submitted action and (for learners) the actor head's pre-squash
mean and log-std per step, re-evaluate N and the SET checkpoints on 955001–955032 in both modes
(≈ 15 min per 64-episode panel pair), and relate boundary contact to saturation of the mean. A
squashed decode applied to the same weights is a different policy: it can serve as a probe of
whether contact comes from saturation, never as an evaluation correction, and any decode change is
a new declared host or learner version. Outcome: a benchmark decision on the evaluation mode and,
if the artefact is real, a recorded host change. Cost: a small evaluator change plus CPU hours,
0 fits.

### D3. Why the training signal is flat while evaluation rises (NEW, 0 fits first)

Question: why is training-time service flat while frozen-evaluation service rises? The phenomenon
is recorded; no explanation is. The two signals are not yet comparable, and that is the first
study (0 fits): training-time QoS is measured on worlds drawn from the lanes' own seed streams,
with a policy snapshot that changes every rollout, with sampled actions, and as per-lane means over
one 3000-step episode; evaluation QoS is measured on the fixed worlds 955001–955032, with frozen
checkpoints, deterministically and with one fixed draw, as 32-world panel means. Step 0 evaluates
the frozen checkpoints c00–c06 on a fixed sample of the training-world stream with sampled actions
(the B02 evaluator takes any world list), and recomputes training-time QoS per episode on the same
basis; if the gap disappears, it was a measurement difference. Only if it survives: the
decomposition of the per-step reward on the training records (`progress.jsonl` / `summary.json` of
`b02_s1_set_a01` and its resumed process) — the return-cost term (`lambda_return` 2.0) against
service, the share of commands overridden by the shield (.24–.34 of UAV-steps), zero-service lanes
against first entry time — and then one declared fit per hypothesis, each a new recipe, never an
extension of the Stage 1 fit. Status: phenomenon RECORDED (Pro's table row); comparability check
and explanation NEW. Cost: 0 fits for steps 0–1; ≈ 9.3 h per hypothesis fit afterwards.

### D4. Deployment as the learning problem: imitation of H_local as a baseline arm (NEW)

Question: since the loss is deployment and a local-information heuristic reaches .597, does a
learner pre-trained to imitate H_local's waypoints, then fine-tuned with the production shield,
close the gap to H_local, and does it keep or lose the shield-driven service? This is a baseline
arm for the suite, not a method claim: it bounds how much of the gap is exploration/credit versus
representation. Status: NEW on this host (the owner rejected re-skinned triggers and probes; this
is a reference arm answering "is the target reachable by this network at all"). The stored
H_local traces hold no observations or actions, so the warm start needs new collection: run H_local
on the development worlds with an extended trace that stores each step's observations, central
state and submitted actions (32 episodes ≈ 96k environment steps, ≈ 10 min CPU; a small evaluator
change). First study: one fit with the SET actor, behaviour-cloning warm start from that
collection, then the standard 1.2 M fit and the standard reading. Cost: the collection, a BC pass
and ≈ 9.3 h. Owner rule: H_local's trajectories on 957001–957032 must never be collected or used.

### D5. T2 / T3 of the diagnosis (RECORDED; do not open before D1 has a table)

T2 (coverage under user mobility with fleet churn on S7-S4, the untie-N question in its natural
form) and T3 (outage restoration on the Milan traces, built, zero fits, data unvalidated) stand as
recorded. Everything in section 4 transfers to them (evaluator, hold-out isolation, resumable
training, admission scripts). The diagnosis's freeze recommendation was withdrawn in the follow-up
response; putting them after D1 is a cost judgment (one table first), not a rule.

### D6. Shared-control items for Root (engineering, no science)

1. **Resumable training as the default for any fit longer than two hours.** The B02 resume path
   (`experiments/candidates/energy_relay_benchmark/b02/training.py`: `read_resume_checkpoint`,
   `resumed_agent`, `run_training(resume_from=…)`) restores the full learner state from
   `HMASDAgent.save_model` checkpoints and refuses on fingerprint / optimizer-step / sampler
   mismatches; the pattern is candidate-local and copyable. Two follow-ups are recorded, not done:
   refuse resume when any schedule flag (`use_lr_decay`, `use_entropy_annealing`,
   `use_reward_annealing`) is on, and compare the value-normaliser statistics after the load.
2. **The native fault.** One `SystemError` from `PyList_AsTuple` in ≈ 2.6 M environment steps of
   a CUDA + pybind11 + numpy process. Undetermined and not pursued; Root may want it on the list
   of known node risks (checkpoint cadence ≤ 2 h bounds the loss).
3. **Hold-out isolation.** The B01 runner now refuses any phase that plans a world ≥ 957001
   outside `holdout-references`, and the B02 evaluator requires `--final` for 957001–957032. The
   same guard belongs in every runner that shares these world sets.
4. **Node schedule.** The Claude direction holds the GPU until ≈ 05:15 UTC and CPU workers for the
   evaluations until ≈ 06:30 UTC on 2026-09-27; after that the node is free unless a Stage 2 is
   declared in NOTES first. Admission (`scripts/hmasd_launch.py launch … --snapshot`) refuses
   absolute inputs under the author root; checkpoints go to `/home/wu/hmasd-artifacts/…` first.
5. **Helper hygiene.** A helper emptied this direction's shared scratch directory because a brief
   said "remove scratch before returning". Briefs to Codex sub-agents should name a unique
   subdirectory and say exactly what to delete.

## 4. What Codex can reuse today (paths on main)

- Evaluator and references: `experiments/candidates/energy_relay_benchmark/b01/` (`evaluation.py`;
  its per-world traces store positions, modes, shield entries/exits, charging, waiting, battery,
  dock bit, guard counts, return margins, station choices/distances/occupancy/queues, heuristic
  targets, rewards and metrics — not actions or observations;
  `heuristic.py` with H1–H3 / H_local / H_spawn / H_park2, `native.py` phases incl.
  `stage0-references` and `holdout-references`), runner `scripts/run_energy_relay_benchmark_b01.py`.
- SET training, checkpoint evaluation, resume: `experiments/candidates/energy_relay_benchmark/b02/`
  (`configuration.py`, `training.py`, `checkpoint_eval.py`), runner
  `scripts/run_energy_relay_benchmark_b02.py`; tests under `tests/experiments/candidates/energy_relay_benchmark/`.
- Readers (standard library, committed before the panels they read): `b01/read_b01.py`,
  `b01/read_stage0.py`, `b01/read_stage1.py` (`--train <process> <resumed process>`,
  `--holdout-refs <run>`), `b01/trace_checks.py`, `b01/stage0_trace_checks.py`.
- Readings JSON: `docs/research/candidates/energy_relay_benchmark/{b01_ref_a02_readings,b02_stage0_readings,b02_stage1_readings}.json`.
- Reference panels on 955001–955032: `runs/energy_relay_benchmark/b01_ref_a02/{grid,reference}/panels/`,
  `runs/energy_relay_benchmark/b02_s0_refs_a01/stage0-references/panels/`; N's checkpoint is
  B09's endpoint on the node (`…/b09_an_925031_a01/N/endpoint/agent.pt`, sha256 `2ba395b9…`).

## 5. What this direction will do next (so nothing is duplicated)

Read c04–c06 by the declared rules; evaluate c06 once on 957001–957032 and read it against the
hold-out comparators; write the Stage 1 result entry with the curve, the failure-explanation
table filled with proxies, and the cost; obtain one independent scientific review (constitution
section 5 as amended); then either declare Stage 2 in NOTES (a changed recipe is a new study) or
close with the cleanup rules of section 9. Until the c06 read is published, the direction's
standing in `docs/research/RESEARCH.md` is the current one (Active row, updated 2026-09-27).
