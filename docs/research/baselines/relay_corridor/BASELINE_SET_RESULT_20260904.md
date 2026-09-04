# Relay corridor baseline set — reused evidence and open cells

Status: **PARTIAL — REUSE ONLY; NO NEW RUN LAUNCHED**

Object: MARL exploration guidance A2, ordinary baseline evidence assembly

Claim ceiling: **B — EXPLORE**, bounded to the homogeneous relay corridor point below. This file
does not reinterpret FSD E2 and is not a Portfolio decision, launch card, registry, or launch gate.

Exact configuration snapshot:
`experiments/baselines/relay_corridor/baseline_set.json`

## Result first

The existing FSD E2 evidence supplies seven valid learned D0 fixed-`k` cells and the complete exact
reference grid. It binds `k=20` as the strongest *observed learned* fixed-clock comparator in both
seeds. It does **not** supply a complete paired learned sweep: `k=1` has no valid completion and
`k=2` lacks seed 2. No rerun is needed to use `k=20` as the comparator for the already-declared E2
population; a future claim about the full learned grid must fill the missing cells under a newly
frozen object.

There is no flat MAPPO-style or independently tuned HMASD-as-shipped result on this host in the
located evidence. Code availability elsewhere in the repository is not counted as a result.

## Bound host and learner

- Host: `N=6`, `K=2`, `Z=4`, `H=400`, `Delta=0.4`, Bernoulli hazards
  `lambda_regions=(0.02,0.02)`, `rho=0`, `c_probe=0`, `role_decode=argmax`, no churn and no E5
  coupling.
- Learner route: HMASD base route through `RelayCorridorHMASDDriver`; every D0 arm uses the fair D0
  construction `policy_interruption_mode=d2`, `c=c_Z=inf`, `k_max=k_Z=k`, `age_feature=off`.
- Per completed run: 20 rollouts, 16 lanes, 128,000 transitions, 320 training episodes and four
  matched deterministic evaluations. Evaluation uses a 4,096-tape set at master seed 770001,
  interval 5, with 512 episodes at intermediate checkpoints and 2,048 at the final checkpoint.
- Seeds: 1 and 2 where present. Existing results are not rewritten into a new paired or
  common-random-number claim.

## Direct observations

The accepted E2 result reports:

| D0 arm | seed | final evaluation return | episode SE | wall minutes | baseline status |
| --- | ---: | ---: | ---: | ---: | --- |
| `k=1` | 1 | — | — | — | quarantined at 8/20; excluded |
| `k=1` | 2 | — | — | — | quarantined at 8/20; excluded |
| `k=2` | 1 | 0.181548421 | 0.000110889 | 157.31 | valid |
| `k=2` | 2 | — | — | — | dropped before launch |
| `k=5` | 1 | 0.287241292 | 0.000201669 | 96.79 | valid |
| `k=5` | 2 | 0.287209880 | 0.000162159 | 92.88 | valid |
| `k=20` | 1 | **0.301320475** | 0.000400109 | 63.37 | valid; learned best |
| `k=20` | 2 | **0.304232422** | 0.000417492 | 62.97 | valid; learned best |
| `k=40` | 1 | 0.261021159 | 0.000680077 | 55.93 | valid |
| `k=40` | 2 | 0.175042155 | 0.000595981 | 55.22 | valid |

The exact reference ordering at the same host point is `20, 5, 40, 2, 1`, with
`J_switch=0.39202` and:

| `k` | exact `J_fixed_k` |
| ---: | ---: |
| 1 | 0.001 |
| 2 | 0.197 |
| 5 | 0.3053168128 |
| 20 | 0.3133920282449043 |
| 40 | 0.2681497980245237 |

The learned top agrees with the exact-reference top in both seeds. All seven accepted D0 cells
have nonzero transitions, optimizer updates, evaluations and finite positive exposure lines under
the E2 evidence acceptance.

## Missing, inference, and strongest counterevidence

Missing facts:

- valid learned `k=1` cells and learned `k=2`, seed 2;
- a tuned flat MAPPO-style result on the relay corridor;
- a separately tuned HMASD-as-shipped result on the relay corridor;
- evidence outside the homogeneous two-region population.

Inference, not observation: the agreement of the learned and exact top makes `k=20` the best
available fixed-clock comparator for this host. It does not prove that the learner grid is fully
tuned or that `k=20` transfers to another host.

Strongest counterevidence: the learned sweep is asymmetric, the `k=1` attempt was deliberately
stopped, and the same E2 study found no finite D2 arm beating the learned `k=20` arm in raw return.
The set therefore supports a bounded fixed-clock comparator, not a general algorithm ranking.

## Cost and next minimum action

No result-bearing operation was launched for A2, so there is no new per-arm projection or resource
receipt. The historical retained arms cost 55.22–157.31 minutes each on their recorded local CPU
route; E2 records the fitted per-rollout law as approximately
`64.6 s + 0.769 s * coordinator_optimizer_steps`. Those observations do not admit or project a
new remote run.

If a future object needs the complete learned D0 grid, its smallest action is a newly frozen
A/RECON or B card that names the missing cells, measures a short pilot of the most expensive arm on
the selected node, records a per-arm projection, and only then launches remote-first. Paired seeds
and common random numbers may be fixed prospectively in that card/config; they must not be asserted
retroactively for these results.

## Evidence sources

- `docs/research/candidates/flexible_skill_duration/FSD_E2_INTERRUPTION_COST_SWEEP_RESULT_EVIDENCE_20260904.md`
- `docs/research/candidates/flexible_skill_duration/FSD_E2_INTERRUPTION_COST_SWEEP_INTAKE_20260904.md`
- `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md`
- Historical runner source at commit `92243f413f22100cb19757687de33abda4b519d1`, path
  `scripts/run_flexible_skill_duration_e2.py`; that commit is not an ancestor of the current main
  snapshot, so the configuration is preserved as evidence rather than advertised as a current
  executable route.
