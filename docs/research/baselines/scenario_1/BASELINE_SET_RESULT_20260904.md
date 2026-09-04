# UAV scenario 1 baseline set — exposure evidence and executable gap

Status: **INCOMPLETE — EXPOSURE/INTEGRITY EVIDENCE ONLY; NO NEW RUN LAUNCHED**

Object: MARL exploration guidance A2, ordinary baseline evidence assembly

Claim ceiling: **B — EXPLORE, integrity and exposure only** for the existing E0 runs. The E0
contract expressly forbids performance comparison, so this file does not rank its returns.

Exact configuration snapshot:
`experiments/baselines/scenario_1/baseline_set.json`

## Result first

Scenario 1 has four reusable learner-exposure runs: HMASD `off` and fair D0 at `k=10`, seeds 1 and
2. Each completed 10 rollouts, 80,000 transitions, nonzero optimizer updates, two evaluations and
finite positive parameter displacement. The frozen 1,536-row E0 probe set is available by recorded
content digest and a tracked 32-row sample.

These are not a complete baseline set. There is no located flat MAPPO result on
`envs.pettingzoo.scenario1.UAVBaseStationEnv`, no D0 fixed-`k` sweep on that host, and no tuned
HMASD performance object. The repository's `mappo` algorithm switch is attached to
`train_multiproc_config_1.py`, whose `base` scenario constructs `UAVRoutedRelayEnv`, not scenario
1. That implementation fact cannot be substituted for a scenario-1 result or runner.

## Bound host and existing runs

- Environment: `envs.pettingzoo.scenario1.UAVBaseStationEnv`, 6 UAVs, 50 users, episode and
  rollout length 500.
- Training: 16 lanes, 10 rollouts, four Torch threads; training lane seeds `seed+rank`.
- Evaluation: 8 lanes with seeds 10,000–10,007, after rollouts 5 and 10.
- `off`: HMASD base learner with `policy_interruption_mode=off`.
- fair D0: the same learner with `policy_interruption_mode=d2`, `c=c_Z=inf`,
  `k_max=k_Z=k=10`, `age_feature=off`.

Directly observed summaries:

| arm | seed | transitions | final evaluation return counter | last coordinator exposure | wall minutes |
| --- | ---: | ---: | ---: | ---: | ---: |
| HMASD `off` | 1 | 80,000 | 22.648224557 | 0.059045880 | 37.7 |
| fair D0 `k=10` | 1 | 80,000 | 35.863022693 | 0.056921070 | 39.9 |
| HMASD `off` | 2 | 80,000 | 32.348382445 | 0.056212268 | 37.8 |
| fair D0 `k=10` | 2 | 80,000 | 26.444298837 | 0.062527609 | 39.9 |

The return values are reproduced only to identify the runs. Per the frozen E0 contract they are
counters, **not comparative observations**.

Git fact: seed-1 manifests record `9a8cd9011f42848d6643cda5d912461ee851739b`; seed-2 manifests
record `fbe2c9d1723d1645ebbf70a3bb8b313f68ed1951`. The E0 narrative records that the rebase moved
the runner/result commits to `619f4b4cdbf39ad5ffd7162105737297a3f603d7` and the latter seed-2
commit; the runner blob at those two commits is identical. The manifest SHA is therefore retained
as a run fact, not mislabelled as the first commit that contains the tracked runner path.

## Probe and RNG facts

The full E0 probe set contains 1,536 probes from HMASD `off`, seed 1, rollouts 1, 5 and 10, sampled
with NumPy probe seed 20260902. Its recorded content digest is
`1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c`; the tracked 32-probe sample
is `docs/Claude_docs/experiments/E0_probe_set_sample_seed1.json`.

Existing arms use the same training lane-seed schedule and the same fixed evaluation seeds. The
E0 result establishes rollout-1 parity checks, not a general paired-return/CRN baseline claim.
Paired seeds and common random numbers are specified only as a requirement for a future baseline
card/config and do not rewrite these runs.

## Missing, inference, and strongest counterevidence

Missing facts:

- a performance-authorized HMASD-as-shipped baseline on scenario 1;
- a flat MAPPO-style runner and result on the exact `UAVBaseStationEnv` host;
- a tuned D0 fixed-`k` sweep rather than the single integrity arm at `k=10`;
- a common performance budget, evaluation schedule and prospective tuning rule across all three
  families.

Inference, not observation: the four valid E0 runs demonstrate that the HMASD and fair-D0 learners
move on this host, making the host technically usable for a future baseline object. They do not
establish which family is strongest.

Strongest counterevidence: the apparent return ordering reverses between seeds, and the contract
forbids interpreting either difference. Treating the seed-1 ordering as a baseline ranking would
therefore contradict both the frozen non-goal and the seed-2 counterexample.

## Cost, publication coverage, and next minimum action

No result-bearing operation was launched for A2. Historical local-CPU wall times are 37.7–39.9
minutes per existing arm; they are not a projection for the remote GPU route or for flat MAPPO.
There was no fresh post-learner failure, so no new publication-path exercise is required by this
assembly.

The smallest next action is one scenario-1 A/RECON baseline card plus a minimal runner that applies
the existing `hmasd.baselines.apply_algorithm_config(..., "mappo")` to the exact E0
`UAVBaseStationEnv` batched loop, without changing the host or evaluation law. Before any sweep it
must pilot the most expensive arm on the actual remote node, project each arm separately, freeze
the tuning grid/budget and paired RNG law, commit and push the source, then use one remote
`agent-task` containing fresh `admit-memory && runner`. A2 does not authorize that launch.

## Evidence sources

- `docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_20260902.md`
- `docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_RESULT_20260902.md`
- `docs/Claude_docs/experiments/E0_probe_set_sample_seed1.json`
- `scripts/run_flexible_skill_duration_e0.py`
- `hmasd/baselines.py` (flat MAPPO implementation switch only; no scenario-1 result)
- `train_multiproc_config_1.py` (its `base` host is not `UAVBaseStationEnv`)
