# E0 — exposure line and frozen probe set on scenario 1 (`off` versus D0)

Design written by Claude Code (Fable 5.1) on 2026-09-02 after the owner approved E0 ("E0批准 不冲突即可").
Governing texts: `../plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` §5 (E0 row: "learner moves;
probe set fixed for C1/C2 metrics") and `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §4,
§5.2 and §11.4. Claim ceiling: **B — EXPLORE, integrity and exposure only.** This document is the
whole launch contract; nothing in §11.4 beyond it may hold the run.

## 1. Question, claim ceiling, non-goals (spec §4.1)

Question: on UAV scenario 1 with the accepted D2 code, do the `off` learner and the fair D0 learner
(`policy_interruption_mode = "d2"`, `c = c_Z = inf`, `k_max = k_Z = k = 10`) both run as real
learners with nonzero transition, update and evaluation counts, and does each move its parameters
within its budget (the exposure line)? Secondary: freeze the probe set on which C1 (variance of
high-level value targets) and C2 (discriminator accuracy, label agreement between checkpoints) will
be measured in E1 and later.

Non-goals: no performance comparison between arms, no claim about D2 helping or hurting, no finite
`c`, no corridor, no seed-count claim. The D0-versus-`off` numbers are integrity checks (boundaries
equal, first-rollout skills equal), not results.

## 2. Algorithm, environment, comparator (spec §4.2)

- Learner: HMASD base route, `hmasd/agent.py` at the commit recorded in the run manifest (the
  worktree HEAD at launch, `main` at or after `b251d0f2d`).
- Environment: `UAVBaseStationEnv` scenario 1 (`envs/pettingzoo/scenario1.py`), `n_uavs = 6`,
  `n_users = 50`, `episode_length = 500`, wrapped per lane in `ParallelToArrayAdapter`
  (`envs/pettingzoo/env_adapter.py`); `num_envs = 32` lanes with seeds `base_seed + rank`.
- Rollout loop: the batched loop the Phase 0 fingerprint driver mirrors from
  `train_multiproc_config_1.py` (`agent.step` batched → env step with terminal-state storage →
  `store_transition_batch` → per-env reset bookkeeping → discoverer bootstrap → `agent.update` →
  `clear_buffers`), as in `tests/flexible_skill_duration_d2_test.py::_run_rollout`. `main.py`'s
  single-environment loop is not used because it does not exercise the batched assignment path
  that carries D2.
- Config: `config_1.Config` defaults (`k = 10`, `rollout_length = 500`, `gamma = 0.99`,
  `ppo_epochs = 15`, `lr_coordinator = 1e-4`, `use_valuenorm = True`), `n_agents = 6` from the
  environment, `total_timesteps` replaced by the rollout count `R` fixed in §4.
- Arms: `off`; D0 = `d2` with `interruption_cost_c = interruption_cost_c_Z = inf`,
  `skill_cap_k_max = 10`, `team_cap_k_Z = 10`, `age_feature = "off"`.
- Seeds: seed 1 for both arms. Seed 2 for both arms only if seed 1 of one arm finished within
  45 minutes; otherwise recorded as not run.
- Comparator for the integrity checks: `off` versus D0 on the same seed.

## 3. Measurements (spec §4.3, §4.4, §5.2)

Per rollout, per arm, machine-written to `metrics.jsonl`:

- environment transitions this rollout and cumulative; episodes completed;
- coordinator optimizer steps, discoverer optimizer steps, discriminator optimizer steps (cumulative);
- `M` high-level rows this rollout (`off`: valid mask count; D0: `rows_M` from `get_d2_metrics`);
- mean episode return over the rollout's completed episodes; mean high-level segment reward;
- exposure line: `||theta - theta_0|| / ||theta_0||` in float64 for the coordinator, the discoverer
  (low-level actor and critic), the team discriminator and the individual discriminator, against
  parameters captured at construction;
- D0 only: the full `get_d2_metrics()` dict (cause counts must be `reset` and `team_cap` only;
  `gap`, `team_gap`, `cap` must be zero; `S_t_fraction` must be 1.0 at decision steps);
- wall time of the rollout and of the update;
- evaluation (every 5 rollouts and after the last): 8 deterministic episodes on 8 evaluation
  lanes with seeds `10_000 + rank`; mean and standard deviation of the return; evaluation count.

Integrity checks on rollout 1, before the first update, `off` versus D0 at the same seed:

- the boundary mask (`[T, E]`) is identical, and `M = 32 * 500 / 10 = 1600` in both arms;
- the team and agent skills of rollout 1 are identical (Phase 2 smoke check 2 predicts this);
- the high-level target scale ratio `off / d2` on rollout 1 is within `[1.03, 1.06]`
  (`tau(1 - gamma)/(1 - gamma^tau) = 1.0458` at `tau = 10`, spread by the reward mix).

After the first update the arms diverge by construction (different targets); no later parity is
expected or checked.

## 4. Budget and stop rule

1. Timing run: 2 rollouts of the `off` arm at the §2 configuration with `torch.set_num_threads(1)`
   and again with 4 threads; keep the faster setting and record both. Not evidence.
2. Choose `R` so that one arm takes at most 60 minutes at the measured rate, with `R >= 10`
   (at least `160,000` transitions per arm). Record `R` and the estimate before launch.
3. Resource preflight immediately before every arm:
   `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py admit-memory --out <run_dir>/preflight.json`; a failed or missing receipt refuses the arm.
4. Stop rule: the arm stops at `R` rollouts, or at the first non-finite loss or return, which is
   recorded as an instability observation. Any instrumentation failure (missing metric, crashed
   evaluation, unwritten receipt) makes the arm an incomplete attempt: it is quarantined under
   `<run_dir>/QUARANTINED` with the traceback and yields no observation (spec §6.2). No resume,
   no salvage.

## 5. Probe set (plan §5 E0, concerns C1 and C2)

From the `off` arm at seed 1, at rollouts `1`, `ceil(R/2)` and `R`, sample 512 transitions each
uniformly at random (probe RNG seed 20260902) and record `(state, observations, team_skill,
agent_skills, env_step, rollout_index, lane)`: 1,536 probes. Save as
`temp/directions/flexible_skill_duration/probes/E0_probe_set_seed1.npz` (local only; `*.npz` is
gitignored) and record its sha256, shape and generation recipe in the result document. A
32-probe sample with the same fields is written as
`docs/Claude_docs/experiments/E0_probe_set_sample_seed1.json` so the recipe is checkable. Later
C1/C2 measurements use the full local file; if it is lost, the recipe regenerates it on the same
machine from the same seed, and the sha256 says whether it matched.

## 6. Outputs

- Runner: `scripts/run_flexible_skill_duration_e0.py` (checked with `git check-ignore -v`), argument
  `--arm {off,d0} --seed S --rollouts R --num-envs 32 --output-root <dir>`; it writes
  `manifest.json` (code sha, config dump, arm, seed, machine identity, torch and numpy versions,
  thread setting, start and end time), `preflight.json`, `metrics.jsonl`, `summary.json`, the
  final checkpoint, and `probe_set` outputs for the `off` arm.
- Run directory: `temp/directions/flexible_skill_duration/exp/E0_20260902/<arm>_seed<S>/`.
- Result document: `docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_RESULT_20260902.md`
  with the §4 integrity items, the timing run, `R`, per-arm tables (counts, exposure lines at
  rollouts 1, `R/2`, `R`, evaluation means), the three integrity checks with their numbers, the probe
  set record, verbatim summary lines, and a could-not-verify list.

## 7. What is not used, and why

`scripts/hmasd_run.py prepare/execute/reconcile` is not used: it requires a registered direction
id and a claim binding, and spec §11.4 says such manifests may not hold a B launch. The runner writes
its own manifest with the same facts. This is recorded as a deviation from the CLAUDE.md practice,
not from the spec.

## 8. Interpretation boundary (spec §4.7)

Whatever E0 shows is bounded to scenario 1 with six UAVs and fifty users, one machine, one or two
seeds, `R` rollouts, and the measurements above. It says whether the two learners run and move; it
says nothing about which is better, about finite `c`, or about the corridor.
