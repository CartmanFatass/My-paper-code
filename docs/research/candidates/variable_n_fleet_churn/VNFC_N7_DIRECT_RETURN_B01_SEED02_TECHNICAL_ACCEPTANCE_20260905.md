# B01 independent seed02 technical acceptance

The selected second independent seed pair completed exit0 on unchanged source
33e08f440c2117dcfd9457d825f42fef7b38ccd7. Both learners completed64 rounds and published
initial/32/64 evaluations plus the fixed BCRH reference. This is engineering completeness;
DM owns the two-seed scientific intake. No further invocation is selected.

## Invocation and complete cost

Selection/card: pushed5a956b736, VNFC_N7_DIRECT_RETURN_B01_SEED02_CARD_20260905.md,
whose final command was executed exactly. Node wsl_4070, agent-task
vnfc_b01_seed02_33e08f440_20260905_01; detached cwd
/home/wu/hmasd-worktrees/vnfc_b01_seed02_33e08f440_01. Fresh admission passed with
15,673,942,016 physical/effective available bytes. Training2026090503/evaluation2026090504,
original namespace, CPUfloat64, one compute thread, original optimizer and native action path.
No source change, resume, smoke, pytest, calibration or diagnostic invocation was added.
Existing Python -X faulthandler recorded no fatal event.

External whole wall **306.68s**, user305.06+system.77=**305.83 CPU-s**; peak RSS562,660KiB.
Runner through final publication/readback306.273766864s. The outer900s limit controlled,
although unchanged runner config/output retains its original2700 field. Actual completion
fits both. The prior431.170369s conditional projection overestimated this invocation by
124.490369s; neither that estimate nor this outcome establishes a guaranteed future bound.
Final stdout's same-run maximum-unit cost law projects328.549531s: MAPR129.530782,
DIRECT150.383305, BCRH37.746742, plus shared setup/worlds/overhead/publication10.888702s.
These projected arm costs remain distinct from external measured complete wall.

Cumulative formal investment: prior476.61+306.68=**783.29wall** and
prior468.78+305.83=**774.61CPU-s**. This includes failed formal01 and both completed seeds.
The original2700s total is unchanged; arithmetic remainder1916.71s selects no additional work.
Including the two measured engineering checks gives808.90wall/800.40CPU-s. Earlier diagnostic
costs retain their separately incomplete timing and are not silently counted as zero.

## Exposure and artifacts

Each learner:2048 complete training episodes,12288 joint transitions,2048 optimizer steps and
backward calls,192 evaluation episodes. Each round retains192 transitions and32 steps from
four epochs/eight minibatches24. Fixed BCRH has64 episodes and384 complete calls.
Saved arrays retain4096 training rows,448 evaluation rows and128 curve rows:4544 total episodes,
1,090,560 native ticks. Evaluations use all64 paired worlds,32 per zone, at the three frozen
checkpoints. All six model+optimizer checkpoints were written/read back by the runner.

Raw summary, full training/evaluation/curve JSON, task log, memory and whole time are tracked
under evidence/b01_seed02_20260905_01/. Remote originals remain below cwd at
 temp/directions/variable_n_fleet_churn/b01_seed02_20260905_01/output/.
Six checkpoint files also copied to the CM worktree at
 temp/directions/variable_n_fleet_churn/b01_seed02_20260905_01/checkpoints/.

MAPR final relative parameter displacement .3045346768; DIRECT .2701411556.
DIRECT residual output parameter norm moved0 to .4435164986. Actual update activity does not
by itself establish comparator competence or a scientific advantage.

## Unselected raw readouts

| Primary contrast | Aggregate | Zone1 | Zone2 |
| --- | ---: | ---: | ---: |
| MAPR final minus initial | .1994531250 | .2433333333 | .1555729167 |
| DIRECT final minus initial | .1955208333 | .2726562500 | .1183854167 |
| MAPR minus DIRECT final | .0039322917 | -.0293229167 | .0371875000 |
| MAPR final minus BCRH | -.0609114583 | -.0827604167 | -.0390625000 |
| DIRECT final minus BCRH | -.0648437500 | -.0534375000 | -.0762500000 |

| Aggregate checkpoint/reference | R_fail_60 | U_total | U_intact | J_ext |
| --- | ---: | ---: | ---: | ---: |
| Both initial | .0423958333 | .2058820104 | .3323040675 | .1241389219 |
| MAPR midpoint | .2413281250 | .5268386959 | .5659770980 | .3840834105 |
| MAPR final | .2418489583 | .5436170700 | .5997945132 | .3927330142 |
| DIRECT midpoint | .1869010417 | .4018939828 | .4000116117 | .2943975122 |
| DIRECT final | .2379166667 | .5421655101 | .5605803008 | .3900410884 |
| BCRH fixed | .3027604167 | .5695671011 | .6156169395 | .4361637589 |

All signs, paired rows, context metrics and20-second recovery observations remain in the raw
output. No best checkpoint, seed or zone selection is introduced. Two completed training draws
remain a small exploratory sample; this document makes no population superiority or equivalence
claim. Previous HMAC failure, SIGSEGV and recovered core remain preserved and unexplained;
success does not retrospectively resolve or erase them.

CM read-only arithmetic over every saved episode reconstructed all three service endpoints and J_ext, counted1,090,560 ticks and zero native flags, and reconciled every round's32 optimizer steps. No discrepancy was found; computed_readback.json records this narrow check. It is not a model replay or universal numerical-equivalence claim.
