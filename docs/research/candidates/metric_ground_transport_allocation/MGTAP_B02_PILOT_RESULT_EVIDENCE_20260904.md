# MGTAP B02 cost pilot — completed B-development evidence

The exact named pilot completed both arms with all required learner and
evaluation measurements. Per-arm main projections are 11.479243 seconds
(METRIC) and 6.155356 seconds (FREE), each below the 300-second cap. This is
technical acceptance of the pilot and its cost measurement, not main-panel
acceptance or an efficacy result. Seed 1907 is excluded from the main estimand;
the scientific branch is null. No configuration or arm was selected from its
returns.

Card: `MGTAP_B02_CURVES_SCIENCE_CARD_20260904.md`. Exact machine summary:
`MGTAP_B02_PILOT_SUMMARY_20260904.json`. Source/review evidence:
`MGTAP_B02_TECHNICAL_EVIDENCE_20260904.md`.

## Execution and terminal fact

- Launch SHA: `f3595bfe3e90024f3b31eb8a82910304b90543d3`, committed and pushed on
  `codex/cm-n5-b02-20260904`, based on card SHA `22ae3de13`.
- Node: configured `wsl_4070`, host `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`.
- Cwd: `/home/wu/hmasd-worktrees/mgtap_b02_20260904`, detached at launch SHA.
- Accepted supervisor task: `mgtap_b02_pilot_1907_f3595bfe`; PID 102331.
- Supervisor terminal: `finished`, exit 0, logged at
  `2026-09-05T06:42:12+08:00` (`2026-09-04T22:42:12Z`), elapsed 2 seconds.
- Log and exit file: `/home/wu/.agent-tasks/mgtap_b02_pilot_1907_f3595bfe/task.log`
  and `exit_code` in that directory.
- Output root: cwd plus
  `temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907`.
  The same relative output is copied under the CM's local worktree.

Exact accepted command:

```text
cd /home/wu/hmasd-worktrees/mgtap_b02_20260904 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_b02_curves.py --mode pilot --seed 1907 --out temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907
```

Node-local admission at `2026-09-04T22:42:10.330982Z` passed: physical and
effective available memory were both 15,403,864,064 bytes, above 4 GiB. The
adjacent receipt is `admission.json`. No duplicate invocation occurred. CM sent
the accepted handle to DM immediately; CM's first bounded status read observed
the terminal before tracker adoption. No routine polling followed handoff.

The committed remote prelaunch suite passed **9 tests in 4.69 seconds**:

```text
/home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/metric_ground_transport_allocation/test/b02_prelaunch tests/experiments/candidates/metric_ground_transport_allocation/mgtap_b02_curves
```

Warnings were the existing pytest cache option with its plugin disabled and
the inherited decoder's noncontiguous searchsorted input. Neither changed
execution. Initial remote Git fetch in a noninteractive shell remained waiting;
that preparation was terminated and completed with configured `zsh -lic`.
No scientific process existed during that preparation correction.

## Counts, measurements and raw curves

Both arms: INTACT, 60 zero-initialized float64 CPU parameters, one thread,
SGD lr 0.1, momentum 0, weight decay 0, unchanged loss/entropy/clip. Each arm
completed 16 updates, 1,536 training allocation transitions, 9,216 training
agent steps; 1,536 evaluation episodes, 3,072 allocation decisions and 18,432
evaluation agent steps. Pilot totals: 32 updates, 3,072 training transitions,
18,432 training agent steps, 3,072 evaluation episodes, 6,144 evaluation
decisions and 36,864 evaluation agent steps.

Normalized episode-return means; evaluation uses 16 tapes at each of 24
pair/load episodes per N. Epoch rewards are combined as `(R1+R2)/(2N)`.

| Arm | Update | N=4 | N=8 | Equal-N mean | SLACK mean | OVERLOAD mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| METRIC | 0 | 0.242393663194444 | 0.251009114583333 | 0.246701388888889 | 0.224392361111111 | 0.269010416666667 |
| METRIC | 16 | 0.275846354166667 | 0.280327690972222 | 0.278087022569444 | 0.248795572916667 | 0.307378472222222 |
| FREE | 0 | 0.242393663194444 | 0.251009114583333 | 0.246701388888889 | 0.224392361111111 | 0.269010416666667 |
| FREE | 16 | 0.271625434027778 | 0.276513671875000 | 0.274069552951389 | 0.244628906250000 | 0.303510199652778 |

The immediate-allocation oracle mean is 0.668750000000000 at each N; SLACK
0.584722222222222 and OVERLOAD 0.752777777777778. At update 16 the equal-N
oracle gaps are 0.390662977430556 (METRIC) and 0.394680447048611 (FREE).
All N-by-load values remain in the tracked machine summary. This oracle is
diagnostic only and never enters actor inputs or learner labels.

| Arm | First step L2 | Final distance from zero | Cumulative path L2 | Preclip norm min / max |
| --- | ---: | ---: | ---: | --- |
| METRIC | 0.0173697801885942 | 0.217758124818424 | 0.246089405921481 | 0.0988638604475 / 0.195455632373 |
| FREE | 0.0174048953316796 | 0.203073254639948 | 0.238587565451902 | 0.0972492052813 / 0.188481851366 |

Both first losses equal 1.533745098325198; update-16 losses are
1.639004173371940 (METRIC) and 1.629608522481414 (FREE). These are retained
stochastic losses, not monotonicity or convergence claims.

Each `<ARM>_training.json` contains all 16 update rows. Each
`<ARM>_evaluation.npz` contains checkpoint indices `[0,16]`, parameters of
shape `(2,60)` and episode returns of shape `(2,2,12,2,16)`, with explicit
N/pair/load axes. CM checked finite arrays, exact counts/checkpoint indices,
zero initial parameters, equal initial episode returns across arms, and
recomputed every aggregate return from arrays within absolute 1e-15.
All checks passed. Raw arrays and traces remain in the output roots.

## Cost and next boundary

`u_A` is seconds per complete training update; `e_A` is seconds per complete
N=4/8 evaluation panel. The frozen cost law is
`P_A = 2 * 3 * (256*u_A + 17*e_A)`.

| Arm | u seconds/update | e seconds/panel | P seconds over three main seeds | Pilot arm wall seconds |
| --- | ---: | ---: | ---: | ---: |
| METRIC | 0.00714887081358029 | 0.00488800949824508 | 11.4792425384803 | 0.631854710998596 |
| FREE | 0.00373394200096300 | 0.00411785049800528 | 6.15535566427570 | 0.0686737049982185 |

Shared setup/oracle: 0.064980994000507 seconds. Runner total wall:
0.766759787999035 seconds. Peak RSS: 482,607,104 bytes; resources measured.
The supervisor's 2-second wall also includes interpreter/import and preflight
overhead. Arm wall includes actor/optimizer creation and publication; u/e time
only their named units. The first arm pays lazy optimizer startup. The
factor-two projected training/evaluation law is preserved, not replaced by a
different resource metric. Both pilot arms are below 30 seconds; setup below 60.

Main has not launched at this evidence boundary. Both projections fit 300
seconds/arm. The DM may accept the unchanged main seeds 203/211/223, 256 updates
and 17 evaluation points, each separately admitted. They reuse this pilot's
`oracle_returns.npy` by exact remote path. Main wall and total accepted-attempt
wall including this pilot must be reported separately; pilot is not another
training replicate. No source repair, retry, arm drop or scientific deviation
occurred. Full main CLI/grid remains the next runtime coverage boundary.
