# MGTAP B01 native ground-geometry execution and cost handoff — 2026-09-09

## Assignment and readiness status

- Direction/object: `metric_ground_transport_allocation` /
  `MGTAP-NATIVE-GROUND-GEOMETRY-B01`
- Parent and integration owner: `/root`
- Original DM: `/root/dm_mgtap_p51_geometry_question`
- P74 assignment: complete the execution/cost plan for the already frozen
  `REL`/`DENSE` comparison
- Scientific exposure in this preparation: **zero**
- New model, environment episode, optimizer call, evaluation, cost probe,
  profiler and native invocation: **zero**
- Readiness: **READY_FOR_A_NEW_EXPLICIT_EXECUTION_ASSIGNMENT**

This handoff supplies the exact prospective two-master route and its cost
screen. It makes no new scientific choice and does not itself authorize a
launch. B01 remains governed by its card, including masters 8201/8202,
primitive G, native team reward, the complete `+/- .01` rule and the 1800-second
arm / 3600-second pair limits.

The current authoring checkout is
`C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`, branch `codex/mgtap`.
It is clean at source-ready commit
`4f65eefb1b15e44b42d694376630fba0c230cc6c` and tracks `origin/codex/mgtap`.
The B01 code surface is byte-identical to accepted source
`db34b6c14100f19ac197b1eaa53c55be22aaf34b`; the latest descendant adds only
the synchronized role configuration and the additive main UCOPE helper
registration. The five shared UCOPE files and `.codex` role/config paths compare
cleanly with current main at the boundary checked here. Main-only MGTAP B03
paths are unrelated and are not imported into this B01 source surface. The
current main ref observed at this boundary is
`c09d7edb6b91023a91be8900d1f83e7542a1629d`; the explicit source-surface guard
for `.codex` and the five UCOPE files returned clean, as did the B01-surface
comparison from `db34b6c14` to this HEAD.

Relevant records are:

- `MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md`, frozen at
  `7e880cb33`
- `MGTAP_NATIVE_GROUND_GEOMETRY_B01_CLOSURE_INTAKE_20260909.md` at
  `3905d3e16`
- `MGTAP_NATIVE_GROUND_GEOMETRY_B01_TECHNICAL_RESTART_HANDOFF_20260909.md` at
  `c2cca317b5b1ec58e4bb8435df867d30288f288f`
- `MGTAP_NATIVE_GROUND_GEOMETRY_B01_ENGINEERING_20260908.md`
- P74 research resume handoff
  `docs/research/portfolio/handoffs/2026-09-09-research-resume-p74.md`

## Exact workload and source cost law

The calculation below was run with the card configuration (`horizon=256`,
`train_episodes=512`, `eval_episodes=32`, two learned arms, two masters,
two-episode rollouts and four optimizer epochs); it is a count calculation,
not a simulation or runtime probe.

| quantity | per learned fit | one master pair | two masters |
| --- | ---: | ---: | ---: |
| training episodes | 512 | 1,024 | 2,048 |
| training team steps | 131,072 | 262,144 | 524,288 |
| two-episode rollouts | 256 | 512 | 1,024 |
| Adam calls | 1,024 | 2,048 | 4,096 |
| learned-policy evaluation episodes | 32 | 64 | 128 |
| learned-policy evaluation team steps | 8,192 | 16,384 | 32,768 |
| fixed-zero-velocity H episodes | — | 32 | 64 |
| H team steps | — | 8,192 | 16,384 |
| complete episodes | — | 1,120 | 2,240 |
| total team steps | — | 286,720 | 573,440 |

Training and evaluation collection has five actor rows per team step. With the
four full-rollout update epochs, the actor-row count per learned fit is

```text
5 * (131072 * (1 + 4) + 8192) = 3,317,760 actor rows.
```

The source-derived branch work per actor row is 4,664 matrix-weight products
and 610 inner `tanh` outputs for REL, versus 2,752 and 16 for DENSE. Thus each
fit has 15,474,032,640 REL branch products or 9,130,475,520 DENSE branch
products. These arithmetic counts exclude common raw/GRU/critic work,
backward/Adam work and environment work; they do not supply a seconds-per-row
coefficient. H has no actor branch and is charged to the DENSE arm's evaluation
and publication remainder.

The frozen per-arm law is:

```text
C_a = C_init,a
    + 131072*c_env+actor,a
    + 1024*c_update,a
    + 8192*c_eval,a
    + C_publication,a
```

For one master, REL and DENSE run serially in one complete pair process. The
DENSE charge includes its 8,192 learned-policy evaluation steps, the additional
8,192 H steps, and pair publication. The pair law is therefore the sum of the
two arm charges, with common startup assigned to the actual phase where it is
observed. The two pair invocations remain separate; the offline aggregate is a
separate process and must be timed and reported in study accounting.

## Existing runtime evidence and projection

The following accepted UCOPE UAV runs are the strongest available same-loop
references: fixed five-UAV / 50-user native environment, 256-step episodes,
512 training episodes per learned fit, 32 final evaluations, 1,024 Adam calls
per fit, CPU FP32 and one compute thread. Their actor package is not B01, so
these values are a planning proxy rather than MGTAP measurements.

| accepted reference | learned-arm clocks | complete external wall | peak RSS |
| --- | --- | ---: | ---: |
| UCOPE P21 master 6801 | T 142.355041 s; G+H/publication 141.371892 s | 288.88 s | 553,808 KiB |
| UCOPE P24 master 6901 | T 140.337403 s; G+H/publication 135.448773 s | 284.29 s | 554,072 KiB |
| UCOPE P47 master 7002 | T 138.256568 s; G+H/publication 134.680469 s | 284.84 s | 554,792 KiB |
| UCOPE P57 master 7101 | T 143.644922 s; G+H/publication 139.312841 s | 283.51 s | 554,276 KiB |

The source record
`C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_EXPOSURE_AND_COST_20260907.json`
uses the maximum observed P21 arm wall with external-minus-runner startup
charged to T. Its accepted forecast is:

```text
P_REL_proxy    = 148.267066867 s + delta_REL
P_DENSE_proxy  = 141.371892048 s + delta_DENSE
P_pair_proxy   = 289.638958915 s + delta_REL + delta_DENSE
```

Here `delta_REL` and `delta_DENSE` are unknown MGTAP-specific branch and
package differences. The proxy's analog base is below both B01 limits. The
remaining tolerance before an analog-plus-delta screen would exceed a limit is
1,651.732933 s for REL, 1,658.628108 s for DENSE and 3,310.361041 s for the
pair. These tolerances are arithmetic headroom around a planning proxy, not
measured upper bounds and not a guarantee that MGTAP will fit.

The analog is useful because its loop counts and native host are matched. It
does not identify `c_env+actor`, `c_update`, `c_eval`, initialization,
publication, RSS or CPU-work coefficients for MGTAP. The MGTAP primitive-G
comparison has no UCOPE duration/renewal head, while REL and DENSE add distinct
row branches; therefore no seconds estimate is transferred from the analog's
T/G labels by treating the packages as equivalent. No cost probe or warm-up is
selected under P74. If a later pre-execution projection includes a measured or
otherwise declared delta that exceeds an arm or pair cap, Root refuses that
route and does not change the cap, dtype, device, RNG, comparator or budget.

Evidence paths for the references include:

- `C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_6801_TECHNICAL_ACCEPTANCE_20260907.md`
- `C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_6901_TECHNICAL_ACCEPTANCE_20260907.md`
- `C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md`
- `C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_7101_TECHNICAL_ACCEPTANCE_20260908.md`

Those records report fresh memory admissions and terminal supervisor evidence;
their aggregate CPU work remains unmeasured. They support planning only and
do not establish MGTAP efficacy, headroom or cross-package equivalence.

## Exact prospective remote binding

The configured result node is `wsl_4070` through `hmasd-wsl-node`, with
`/home/wu/.venvs/hmasd/bin/python`, `/usr/local/bin/agent-task`, CPU FP32 and
one Torch/BLAS thread. The exact source-ready SHA is:

```text
4f65eefb1b15e44b42d694376630fba0c230cc6c
```

After a new explicit execution assignment, Root stages that exact commit in a
detached remote worktree:

```text
/home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c
```

The source surface to compare before launch is the three B01 package files,
the B01 entry script, the five shared UCOPE files, and the native dependencies
and `scripts/hmasd_resource_preflight.py` at this SHA. A documentation-only
descendant does not alter those bytes; any source-surface mismatch returns to
the same CM before launch.

Wrappers must be written as literal UTF-8/LF files under
`/home/wu/hmasd-inputs/mgtap-b01-4f65eefb1b15e44b42d694376630fba0c230cc6c/`.
Do not interpolate paths through PowerShell or embed escaped newlines.

Wrapper `run_8201.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8201/admission.json && /usr/bin/time -q -f '%e' -o /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8201/process_wall_seconds.txt /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_native_ground_geometry_b01.py --native --master 8201 --output /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8201 --arm-cap 1800 --pair-cap 3600
```

Wrapper `run_8202.sh` is byte-identical except for `8202` in the admission
file, output root and `--master` value:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8202/admission.json && /usr/bin/time -q -f '%e' -o /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8202/process_wall_seconds.txt /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_native_ground_geometry_b01.py --native --master 8202 --output /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8202 --arm-cap 1800 --pair-cap 3600
```

The accepted submission commands are:

```text
ssh hmasd-wsl-node '/usr/local/bin/agent-task run mgtap-b01-8201-4f65eefb1b15e44b42d694376630fba0c230cc6c bash /home/wu/hmasd-inputs/mgtap-b01-4f65eefb1b15e44b42d694376630fba0c230cc6c/run_8201.sh'
ssh hmasd-wsl-node '/usr/local/bin/agent-task run mgtap-b01-8202-4f65eefb1b15e44b42d694376630fba0c230cc6c bash /home/wu/hmasd-inputs/mgtap-b01-4f65eefb1b15e44b42d694376630fba0c230cc6c/run_8202.sh'
```

These are prospective literals. No input directory, detached worktree,
supervisor handle, admission receipt or output root exists from this planning
turn. Root chooses the operational order and observes each accepted handle;
there is no score gate between masters, no relaunch and no replacement seed.

## Admission, collection and aggregate contract

Each wrapper joins the node-local memory preflight and native runner with `&&`.
The actual node must report both physical and effective available memory at or
above 4 GiB immediately before that master invocation. A missing or failed
receipt refuses the invocation. A local receipt cannot admit this remote run.

The remote output roots are:

```text
/home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8201
/home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8202
```

After each terminal supervisor state, collect the complete root and supervisor
files into direction-local control-plane roots such as:

```text
C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/exp/mgtap_b01_8201_4f65eefb1b15e44b42d694376630fba0c230cc6c/
C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/exp/mgtap_b01_8202_4f65eefb1b15e44b42d694376630fba0c230cc6c/
```

Collection must retain the admission JSON, `summary.json`, `episodes.jsonl`,
`rollouts.jsonl`, `final_REL.pt`, `final_DENSE.pt`, `process_wall_seconds.txt`
and the supervisor's task log, status, PID/start-time and exit-code witnesses.
Copy by explicit path with SCP and record remote/local size and SHA-256 for
every copied file. No remote evidence is renamed or deleted to repair a
collection mismatch.

The technical collector checks, for each master, the exact source/launch SHA,
master and card binding, `UAV_B_EXPLORE` mode, `horizon=256`,
`train_episodes=512`, `eval_episodes=32`, `agent_compound`, CPU FP32 and
1800/3600 caps; both learned fits must be complete; all 1,120 episode rows,
286,720 team steps, 2,048 Adam calls and 96 evaluation episodes must reconcile;
the three primary/H arms must be complete; and no primary row may be missing,
duplicate, corrupt or shortened. It also checks finite checkpoints, persisted
partial counters, publication status, pair wall and supervisor exit. A cap,
integrity or completion failure preserves the completed facts and returns to
the same CM; it does not authorize retry, resume or replacement.

Only after both master summaries pass technical collection, run the existing
offline aggregate on the exact source. The aggregate is not a training or
evaluation invocation and requires no new model or memory admission. A timed
remote form is:

```bash
cd /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c && /usr/bin/time -q -f '%e' -o /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/aggregate_process_wall_seconds.txt /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_native_ground_geometry_b01.py --aggregate /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8201/summary.json /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/b01_8202/summary.json --output /home/wu/hmasd-worktrees/mgtap_b01_4f65eefb1b15e44b42d694376630fba0c230cc6c/temp/directions/metric_ground_transport_allocation/exp/aggregate_summary.json
```

The collector then requires `errors=[]`, both declared masters present, a
complete primary and the emitted two-pair mean, endpoint sample SD and combined
conditional evaluation SE. The per-master episode values and pair means remain
the scientific evidence; the DM applies the frozen result rule in a later
intake. The aggregate process wall is accounted separately from pair process
walls, and study critical path is reported separately from summed invocation
wall and aggregate CPU work.

## Acceptance and remaining unknowns

This handoff is accepted as a bounded P74 execution/cost plan. It does not
claim that the analog forecast proves affordability, that a passing admission
proves runtime capacity, or that technical completion establishes REL value.
The following remain explicitly unknown until actual B01 execution:

- MGTAP-specific `c_env+actor`, `c_update`, `c_eval`, initialization and
  publication coefficients;
- incremental wall for the REL and DENSE row branches;
- complete process wall and pair remainder after REL;
- peak RSS/activation memory on the MGTAP source;
- aggregate CPU work and study critical path including offline publication;
- any endpoint, polarity or mechanism interpretation.

The P74 convention does not require a new calibration when these costs are
unknown. The existing analog proxy and the large declared cap tolerances supply
the planning record; actual wall, supervisor exit, admission and technical
collection remain mandatory if Root later assigns the execution. No Portfolio
proposal, owner item, new card, recast, successor or UAV-validation entry is
created by this handoff.

## Return

Root may dispatch the two exact wrappers once it accepts this bounded route and
performs its ordinary §11.4 launch checks. The same DM/CM retains technical
collection and DM intake. Until then the source remains unlaunched, with no
additional work selected by this document.
