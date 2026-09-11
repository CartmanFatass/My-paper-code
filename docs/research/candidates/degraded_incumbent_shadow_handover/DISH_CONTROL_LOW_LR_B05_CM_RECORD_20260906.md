# DISH B05 seed101 technical record

**Delivered: technically complete paired B05 at integrated SHA `1d87e02194158d6bca0eaa4e7f70a1c1098bb121`.**
Both final learners and all twelve reference/final rows collected. [Machine-readable technical acceptance](control_low_lr_b05_20260906/TECHNICAL_ACCEPTANCE.json) contains full rows, counts, native facts and exact cost allocation. Scientific intake remains with DM.

Implementation base: `18812ba5e62b6e1a877558f735c7bf979386be5b`.
CM branch `codex/cm-dish-b05-seed101-20260906`, worktree
`C:/Projects/HMASD-worktrees/cm-dish-b05-seed101-20260906`.
Contract: [card](DISH_CONTROL_LOW_LR_B05_SCIENCE_CARD_20260906.md) sections 2-4,6-7.

Engineering scope section 4 additions: **none**. Explicit seed/result-name arguments reuse the
existing path; no new guards, schedulers, diagnostics, retry or compatibility machinery.
B04 defaults remain seed89 and B04 name. B05 fixes seed101 and B05 result name while
SHA256 retains ASCII `DISH-CONTROL-LOW-LR-B04/seed/101`.

The seed reaches shared initialization, training reset factory and NativePersistentTrainingFlow.
The unchanged flow creates its own recurrent state, master-addressed sampler, reset factory,
trainer and policy. Native training state is new per arm; saved common initial model bytes and
recorded complete reset rows supply reference and both learners. The explicit object name
changes result identity only. All B02/B03/r06/native paths remain unchanged.

## Acceptance before execution

One focused test `tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05/test_seed_binding.py`
exercises initializer/reset/flow arguments, shared bytes and separate state, seed101 reset rows,
all sixteen LR records, three runner summaries and synthetic paired publication. Learner and
native episode execution are substituted only inside this test; real reset construction and LR
serialization are exercised. It cannot prove actual learning counts or outcomes. Reuse B04
accepted LR persistence, corrected boundary, count-0 reference and native termination coverage
as directed by card section 7; do not rerun the historical suite.
Independent reviewer `rev_ah_dish_b05_seed` found no material defect in the actual RNG/result
identity diff and protected downstream chain. It confirmed separate mutable states, B04 defaults,
and inherited LR/replay/termination/reduction. Initial seed-only source scope: 41 added / 18 deleted non-test lines;
runners 158 and 7 lines. The subsequent minimal shared publication wall readings implement
the card's exact S/2 allocation; independent follow-up review found no material gap. Final collection uses the exact formulas
below rather than the inherited conservative `charged_wall_seconds` field and retains stdout P. No runtime acceptance asserted. Static AST parse of all five changed/new
Python implementation/test files and `git diff --check` passed. No seed101 execution yet.

## Frozen execution and cost plan

Execution node `wsl_4070`, remote detached worktree
`/home/wu/hmasd-worktrees/dish-b05-seed101-20260906`, exact integrated/pushed SHA supplied by Root.
No Windows fallback is selected. Interpreter `/home/wu/.venvs/hmasd/bin/python`;
CPU FP32 policy/float64 native, Torch/OMP/MKL/OpenBLAS one thread, `MAX_JOBS=1`;
`PYTHONPATH` equals cwd. Output relative to cwd:
`temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906` (R below).
Each command is detached via configured `agent-task`; actual node admission (>=4 GiB physical
and effective) joins its invocation with `&&`. Outer `/usr/bin/time -v` includes imports,
build/load, operation and publication; outer timeout bounds the operation. Commands, accepted
handles and final measured S will be recorded before their launches.

Logical argv, in order (PY denotes the interpreter above):

1. `PY -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b05-seed101 tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05` (<=300s; charged in S).
2. `PY scripts/run_dish_control_low_lr_b05.py shared --seed 101 --out R/shared --admission R/shared.memory.json`.
3. `PY scripts/run_dish_control_low_lr_b05.py run --arm CONTROL --seed 101 --shared R/shared --shared-preparation-seconds S --out R/control --admission R/control.memory.json`.
4. `PY scripts/run_dish_control_low_lr_b05.py run --arm LOW_LR --seed 101 --shared R/shared --shared-preparation-seconds S --out R/low_lr --admission R/low_lr.memory.json --control-summary R/control/summary.json`.

**Per-arm cost projection:** reuse [EXPOSURE_AND_COST.json](control_low_lr_b05_20260906/EXPOSURE_AND_COST.json),
B04 same-scale measured S=15.84s, CONTROL=210.07s, LOW_LR=206.49s, fully charged 217.99/214.41s.
No new calibration. Each arm N=65536 ordinary ticks, 512 optimizer steps; native calls
2N+2E+H <=1572864. Unknown E/H and node load remain unknown. B05 projected full pair is of
order 432.40s conditionally, below 1800s/arm and 3600s total. Actual focused check, common
initializer/reference and build/load are S/2 per arm. Shared reducer/publication executes in
LOW_LR's existing timed path. Minimal direct wall readings report its duration P in the final
stdout record, after the summary/paired files are written. Final S = focused + initializer/reference
+ P; charge CONTROL wall + S/2 and LOW_LR wall - P + S/2. Before either arm, reserve 30s for P;
outer timeout <=1800 - (measured preparation + 30)/2. The inherited runner's slightly larger
internal allowance does not supersede this outer bound. The reserve is not extra runtime and
is not charged as measured work. Final acceptance checks actual P and both exact charged totals.
No budget is deducted for unmeasured contention. Invocation wall sum, study elapsed critical
path (including control-plane gaps) and aggregate CPU are reported separately.

**Post-learner path coverage:** focused synthetic paired reduction plus publication/readback
exercises the reused primary path. No historical publication replay dependency exists.

Stop after one pair of sixteen updates and twelve reference/final rows, or nonfinite training,
primary-threatening failure or exhaustion of the fully charged caps. No scientific retry,
extra seed, checkpoint selection, extra evaluation or resume is authorized. CM retains launch
observation until independent monitor ACK and then collection/technical acceptance; DM owns science.

scope: none

## Runtime observations (collection in progress)

Root integrated and pushed exact launch SHA `1d87e02194158d6bca0eaa4e7f70a1c1098bb121`.
The detached remote checkout uses this SHA. Initial fetch through a non-login shell stalled
in git-remote-https; its exact preparation processes were terminated before checkout/compute,
then the configured `zsh -lic` network route fetched successfully. This is a Git access fact,
not an experiment failure or altered execution node. Login-shell gitstatus UI warnings did
not prevent successful fetch/checkout.

- `dish_b05_seed101_focused_20260906`: exit1 before test body; pytest temporary-directory
  parent absent. Admission passed. Outer1.15s, retained logs; no scientific model/episode.
- `dish_b05_seed101_focused2_20260906`: mkdir-parent ordinary launcher repair, fresh admission,
  one focused pass. Exit0, 1 passed in0.79s; outer1.07s. The cache_dir warning is the inherited
  pytest configuration with cacheprovider disabled. Total charged focused cost2.22s.
- `dish_b05_seed101_shared_20260906`: exit0, one initializer and four complete1200-tick rows;
  empty actor/snapshot/critic Welford. Outer7.11s; cumulative preparation9.33s.
  Master `cd461a1f466eb5cf40c42dc71d29e103a9dbf00f292d5673a8560069585e01c0`;
  reset phases2,3,0,1. Reference mean297.25 (rows96,330,323,440), retained independently
  of the still-unobserved paired learner comparison. No effect-based decision followed.
- `dish_b05_seed101_control_20260906`: accepted at same source; outer1780.335s ceiling
  =1800-(9.33+30)/2. Shared input is the new shared directory, not historical checkpoints.

All accepted handles dispatched directly to configured independent monitor. Shared-handle
adoption ACK received via Root; CM collected its terminal artifacts. CONTROL adoption ACK received from Root (tracking commit4202358fe); its terminal
notification remains pending. Routine polling released to the monitor. The final evidence will retain exact command strings, terminal supervisor evidence,
receipts, OS timing, and final stdout containing publication duration P.

### Exact accepted commands

`dish_b05_seed101_focused_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_focused_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && mkdir -p temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.time.txt /usr/bin/timeout --signal=ALRM 300s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.memory.json && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b05-seed101 tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.stderr.log'"'"''
```

`dish_b05_seed101_focused2_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_focused2_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && mkdir -p temp/directions/degraded_incumbent_shadow_handover/test && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.time.txt /usr/bin/timeout --signal=ALRM 298.85s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.memory.json && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b05-seed101 tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.stderr.log'"'"''
```

`dish_b05_seed101_shared_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_shared_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.time.txt /usr/bin/timeout --signal=ALRM 3567.78s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_control_low_lr_b05.py shared --seed 101 --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.memory.json'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.stderr.log'"'"''
```

`dish_b05_seed101_control_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_control_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.time.txt /usr/bin/timeout --signal=ALRM 1780.335s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_control_low_lr_b05.py run --arm CONTROL --seed 101 --shared temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared --shared-preparation-seconds 9.33 --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.memory.json'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.stderr.log'"'"''
```


## CONTROL collection and final arm dispatch

CONTROL terminal exit0 from supervisor, ended2026-09-07T11:43:56+08:00, duration211s.
Actual outer wall210.63s, user192.97s + system22.96s, maxRSS622072KiB. Sixteen completed
updates,65536 ordinary transitions,512 optimizer steps; all sixteen LR records[0.0003,0.0003]
and finite loss/gradient flags. Four complete1200-tick final rows, service178,491,153,301,
mean280.75; no final legal transfers or seven hard-event classes. Training reports3 legal
transfers and1915 invalid commits. Initial norm38.261779002554604 matches shared initialization;
nonzero L2 displacement8.425011334270215. Full rows/curves retained for final collection.

A control-plane observation delay occurred after CONTROL already finished: Root reported the
existing global monitor heartbeat had been PAUSED, corrected it to ACTIVE, and obtained the
terminal notification. This idle gap is included in study elapsed critical path but is not
learner machine wall; no live process was migrated or relaunched. Root's correction is outside
this CM's source/experiment scope. LOW_LR adoption explicitly requests the same global heartbeat
be ACTIVE and confirmed in its ACK.

LOW_LR accepted handle `dish_b05_seed101_low_lr_20260906` at unchanged integrated source,
same fresh admission/1780.335s outer ceiling, no scientific setting changed after CONTROL.
Its paired publication reads this CONTROL summary and this seed101 shared reference.

```sh
/usr/local/bin/agent-task run dish_b05_seed101_low_lr_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/low_lr.time.txt /usr/bin/timeout --signal=ALRM 1780.335s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/low_lr.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_control_low_lr_b05.py run --arm LOW_LR --seed 101 --shared temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared --shared-preparation-seconds 9.33 --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/low_lr --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/low_lr.memory.json --control-summary temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control/summary.json'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/low_lr.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/low_lr.stderr.log'"'"''
```

LOW_LR monitor adoption ACK received via Root: same global heartbeat
`hmasd-experiment-monitor` confirmed ACTIVE; tracking commit `c609e69bc`.
Routine LOW_LR observation released; CM retains terminal collection.

## Final technical acceptance

LOW_LR terminal exit0, ended2026-09-07T12:22:12+08:00, supervisor duration213s,
outer212.86s. Root forwarded terminal tracking commit99d2aa736. All five admitted
invocations retained, including the1.15s setup failure. No learner rerun, retry, new seed,
intermediate checkpoint, extra evaluation, or outcome-based change occurred.

One focused plumbing/publication test passed; independent source reviews had no material
finding. Final direct artifact checks independently recomputed means and each paired/before-after
row; checked SHA/seed/master metadata, common recorded resets, initial norms, zero Welford,
all16 LR readbacks per arm, finite loss/gradient flags, actual counts, complete horizon accounting,
all five admissions, supervisor terminal facts and fully charged caps. These checks do not
establish a population-performance or safety claim.

| Condition | Reference | CONTROL | LOW_LR | LOW_LR - CONTROL | CONTROL - reference | LOW_LR - reference |
|---|---:|---:|---:|---:|---:|---:|
| TARGET_VISUAL_MASK / K8 |96|178|591|413|82|495|
| TARGET_VISUAL_MASK / K4_TO_K12 |330|491|214|-277|161|-116|
| TERRAIN_RELAY_MASK / K8 |323|153|695|542|-170|372|
| TERRAIN_RELAY_MASK / K4_TO_K12 |440|301|568|267|-139|128|
| Mean |297.25|280.75|517.00|236.25|-16.50|219.75|

Seed89's historical Delta is+182.75, displayed beside seed101's+236.25 without replacing
these complete paired observations with an aggregate claim. The negative new row is retained.

Per arm:16updates,65536ordinary transitions,65536next-label steps,512optimizer steps,
65504next-mask count. CONTROL/LOW_LR service-label-eligible counts17208/18957. Total131072
ordinary transitions,1024optimizer steps,32updates,4reference+8final episodes and14400
executed evaluation ticks. Every evaluation reached1200ticks; zero unstepped zero-fill ticks.
Final-only checkpoints retained; no intermediate selection. Initial norm38.261779002554604;
final norms39.12600905730808/38.32273070820353; L2 displacement8.425011334270215/1.956012517033048.
Both configurations report one Torch thread, FP32 training and float64 native; fixed thread
environment appears in exact commands. Native H remains unmeasured and bounded, not zero.

All12 final/reference episodes have0legal transfers and fixed_horizon termination.
Reference invalid_commit counts[0,26,31,0]; CONTROL[0,0,0,0]; LOW_LR[108,0,101,0]. The other
six hard-event classes are zero in every evaluation row. Reference and LOW_LR adverse events
remain visible. All service is temporally before transfer; no packet-source attribution inferred.
Full per-row energy and terminal/native state are in the retained summaries and technical JSON.
Training CONTROL/LOW_LR: legal transfers3/0, invalid commits1915/2074, training terminals32/32,
service29580/29166, energy15191219.70334793/14766450.687113658. Other training hard events zero.

### Complete cost and retained artifacts

- Focused setup+pass2.22s; shared initializer/reference7.11s; preparation9.33s.
- Measured shared paired-read/reduction/publication `P=0.001856654998846352s`, retained in
  `low_lr/final_stdout.json` and raw `low_lr.stdout.log`. `S=9.331856654998846s`.
- CONTROL exact charge `210.63+S/2=215.2959283274994s`.
- LOW_LR exact charge `212.86-P+S/2=217.52407167250058s`.
- Sum machine wall432.82s, including failed setup/check/import/build/load/preflight/evaluation
  and primary publication; each arm<1800s and total<3600s. The30s reserved publication allowance
  is not measured work. Inherited stdout `charged_wall_seconds` is a conservative legacy sample;
  the exact allocation here and in technical JSON governs this B05 record.
- Aggregate OS user+system CPU444.01s; maximum invocation RSS622072KiB. This is a per-process
  maximum, not a simultaneous process-tree sum. Scratch unmeasured, `resources_unmeasured=true`.
- Study elapsed critical path2663s from first supervised check start to final supervised exit,
  including the control-plane monitor delay. Git/SSH transport, artifact copying and documentation
  are outside compute-invocation wall. Do not substitute summed CPU or wall for this elapsed value.
- All five physical/effective admissions pass>=4GiB; minimum observed15656681472bytes.

Compact E0 is [control_low_lr_b05_20260906](control_low_lr_b05_20260906/TECHNICAL_ACCEPTANCE.json):
full summaries/curves/rows/resets, exact [launch commands](control_low_lr_b05_20260906/LAUNCHES.json),
paired result, original stdout/stderr, supervisor logs/status, preflight receipts and outer timing.
Raw checkpoints and initializer are retained at both remote and collected local scratch root:
`temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/`,
under the remote exact-SHA worktree and this CM worktree respectively. `shared/initial_state.pt`
is836667bytes; each `control/checkpoint_update16.pt` and `low_lr/checkpoint_update16.pt`2356639bytes.
No binary evidence was deleted or replaced.

Remaining scientific reading and next object decision belong to DM. No further execution remains
in this CM assignment. Root integrates the final E0/record commit; the monitor can close these
terminal handles after this collection acknowledgement.

scope: none
