# DISH B07 CM implementation and acceptance — 2026-09-08

Delivered the B07 one-pair study and runner, raw-own mean across live behavior and recurrent
replay, and the original focused synthetic acceptance. No scientific initializer, native
state/episode, learner update, result invocation, smoke, extra seed or Pro Send was executed.
This record belongs to its containing delivery commit; the exact commit is returned to DM
with the push receipt. Starting checkout was clean at fc52d630de39429383cb12ad7ec8e7b2877f67b6,
branch codex/pro-dish-post-b06-20260907, in
C:/Projects/HMASD-worktrees/dm-dish-b06-scientific-intake-20260907. Source at the bound
5b9390ba2da7c2002a512505c2a13f3045a57ab1 was preserved outside the owned diff.

## Delivered paths and boundaries

- `experiments/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07/{__init__.py,study.py}`:
  common initialization without shared evaluation, four own initial rows per mode, two real
  LOW_LR flows in DIRECT then OWN order, update16 evaluations, complete and partial reduction,
  TRAIN/EVAL exposure, and shared/exclusive cost allocation.
- `scripts/run_dish_own_command_mean_b07.py`: fixed seed127 interface, exact launch SHA field,
  CPU/dtypes, caps and exception/partial publication, RSS scope and terminal cost readback.
- `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py`:
  three ordinary optional propagation seams; previous DIRECT and LR defaults retained.
- `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py`:
  one `_motion_mean`; live/replay ranks use raw physical-copy inputs, and repeated motion
  likelihood reuses the differentiable returned mean.
- The adjacent `production_recurrent_trainer.py` and `production_training.py`: carry mode
  into collection, PersistentTrainer, the update engine and post-update policy reconstruction.
- `tests/experiments/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07/test_own_command_mean.py`:
  the one focused module. This document is the only owned CM record.

Live raw actor is [width,4,54]; replay is [fragments,ticks,4,54]. Owner-before chooses copies
[owner,3-owner], preserving vehicle0 xy then vehicle1 xy. Motion uses raw fields8:10, while
encoder/GRU normalization remains untouched. Mode is a flow/policy argument, not a model,
checkpoint, RNG or native-arm addition. Both real flows remain STRUCTURED at LR3e-5.
The underlying action projection/application, noise streams, Bernoulli/masks, PPO/AdamW,
Welford, private labels, promotion, update1024 constant and sole-checkpoint access are unchanged.
B07 uses existing B04 direct update16 bytes, not the r06 sole-checkpoint accessor.

Section4 machinery added: **none**, as card §6 and CM spec §5 prescribe. Added non-test
source: **286 lines**, deleted20; new study155, package1, runner90, shared-path additions40.
The runner is90 lines (<600), and total286 (<2000). Tests/documentation are excluded.
No new orchestration framework is present; the independent reviewer found no unnecessary
machinery. Native and real full-training behavior are unobserved by this engineering task.

## Original focused command and evidence

Configured interpreter: C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe.
From the designated checkout, the original command was run with invocation-owned tags:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b07-own-command-20260908-cm03 tests/experiments/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07/test_own_command_mean.py
```

| Tag suffix | Actual result | pytest seconds | Process wall charge seconds |
| --- | --- | ---: | ---: |
| cm01 | 7 passed,1 setup error: absent basetemp parent | 2.36 | 3.3619347 |
| cm02 | 8 passed | 2.00 | 2.8518697 |
| cm03 | 11 passed | 1.87 | 2.6727375 |

Raw logs retained outside scratch at
`temp/directions/degraded_incumbent_shadow_handover/b07-cm-check-20260908-01.log`,
`b07-cm-check-20260908-02.log`, and `b07-cm-check-20260908-03.log`.
The first setup issue was fixed by creating the parent and using a short synthetic pair
scratch name. Subsequent checks added reviewer-identified exposure/cap coverage and an
intercepted native terminal/first-transfer check; no unchanged historical suite was repeated.
All runs emit the existing pytest warning about cache_dir while cacheprovider is disabled.

Total required computational check charge **S_check=8.8865419s**, including failures,
well below300s. Independent review was read-only and ran no additional computational checks.
Ordinary editing/source inspection/arithmetic are not scientific exposure. Before this
invocation, a combined test/cleanup shell command was rejected before execution, so it
incurred zero test time.

Coverage establishes both physical owner mappings/ranks, nonzero/zero/raw-versus-normalized
inputs, live action and behavior/replay Gaussian densities, nonrenewal held commands and
Bernoulli terms, differentiable density reaching motion parameters, persistent reconstruction,
master-family plumbing through intercepted initialization/reset/flow/evaluation consumers,
fixed learning/evaluation counts, own initial references, adverse rows, ±24/open-band and
own-initial-loss facts, native post-step first transfer/null, zero terminal remainder,
complete/incomplete summary readback, H bounds, and shared/per-arm accounting. FP32 checks
use rtol1e-6/atol2e-6 for separately assembled means/densities; identical DIRECT/zero-input
expressions use exact equality. This is no cross-platform or full-trajectory equality claim.
The repeated real-engine term was directly inspected to consume the same returned mean;
no synthetic4096 update or real learner was needed to prove that argument seam.

Independent reviewer: native child `review_b07` under this CM, role hmasd-reviewer.
It inspected the full affected diff, tests and actual retained logs. It found two material
reporting gaps (missing native-work bounds and ambiguous final publication charging); both
were repaired in the same review. Final disposition: **no material finding remains**.
Reviewer verified raw/mapping/mode/gradient coherence, preserved defaults/state/native
boundaries, fixed two-learner/16-row composition, reductions, scope limits and partial output.
It explicitly retained the scientific-execution and full-chain resource limitations.

## Charge and prospective execution binding

Remaining actual allowance after required checks: **1795.55672905s per arm**, **3591.1134581s
per pair**. Each arm receives S_check/2=4.44327095s; checks are never charged twice.
The runner additionally deducts a **10s common planning reserve** (5s/arm) from its deadlines
for admission/interpreter startup and terminal/publication/closure outside the in-script
measurement. Thus its initial in-script deadlines allow at most3581.1134581s/pair and
1790.55672905s/arm before further common initialization/import allocation. Reserve is not
reported as already measured wall or as evidence of conformance.

Per-arm projection: card §6's law is2N+2E+H, N65536, E<=N, H<=20E, giving native training
calls131072–1572864, plus512 optimizer steps,2048 batched policy forwards and up to9600
modal evaluation ticks. Reuse card-linked EXPOSURE_AND_COST.json's complete B06 anchor226.02s
and B05 pair432.82s; a conservative same-scale planning point is226.02+S_check/2=
230.46327095s per arm (460.9265419s summed pair), far below the unchanged caps. This is an
anchor-based estimate, not a measured B07 result or guarantee; E/H and own-mean runtime
remain unknown. Pair serial critical path approximates summed arm wall plus common work;
no aggregate-CPU claim is inferred from wall. No fresh pilot is selected or required.

Post-learner publication coverage: the synthetic pair exercises the actual B04 run_arm
seams with intercepted consumers and actual summary serialization/readback, including
incomplete references and cost exhaustion. The native/learner execution itself remains for
Root's later named launch. Summary wall is explicitly pre-final-write; terminal JSON records
cost after substantive publication. A cap crossing at that point conditionally rewrites
summary as INCOMPLETE. Whole-chain collection must consume terminal and OS timing, rather
than treating the earlier summary timestamp as complete cost.

Prospective binding, not staged or submitted:

- Node wsl_4070; SSH hmasd-wsl-node; native float64/policyFP32 CPU, one Torch/BLAS thread.
- Detached exact accepted source SHA under configured agent-task; no authoring branch on node.
- cwd `/home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01`.
- Handle `dish_b07_seed127_20260908_run01`.
- Envelope `temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01`;
  runner output is its `run/` child, preserving the existing mkdir contract.
- Python `/home/wu/.venvs/hmasd/bin/python`; fresh same-node physical/effective memory>=4GiB
  admission adjacent to runner. No admission or detached process exists yet.

The exact runner argv, replacing ACCEPTED_SHA with this accepted delivery's literal SHA:

```text
/home/wu/.venvs/hmasd/bin/python scripts/run_dish_own_command_mean_b07.py --seed 127 --output temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/run --launch-sha ACCEPTED_SHA --prior-shared-seconds 8.8865419
```

Prospective LF bash payload for Root's existing configured detached submission (the envelope
is prepared for logs before invocation; SHA is bound after commit, never queried as a gate):

```bash
#!/usr/bin/env bash
cd /home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01 || exit 1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="$PWD"
/usr/bin/time -f 'whole_chain_wall_seconds=%e\nwhole_chain_exit=%x' \
  -o temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/whole_chain.time \
  bash -c '/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_own_command_mean_b07.py --seed 127 --output temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/run --launch-sha ACCEPTED_SHA --prior-shared-seconds 8.8865419' \
  > temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01/runner.log 2>&1
```

At collection replace planning with measured S_actual =8.8865419 + whole_chain_wall minus
sum(exclusive arm wall), adding any separately measured required publication/collection tail
once. Charged pair is8.8865419 + whole_chain_wall plus that tail; arm charge is its exclusive
wall plus S_actual/2. Preserve OS timer resolution and final accounting-write boundary; the
10s reserve is no proof. If actual complete charge exceeds1800/arm or3600/pair, retain that
fact and partial/trustworthy measurements; no retry or silent conformance claim follows.
Root/DM own final literal-SHA binding, staged-wrapper syntax check and later launch/collection.

## Remaining technical limitation and next owner

Automatic approval review rejected invocation-only scratch cleanup with only “blocked by
policy”, including the explicit verified command `Remove-Item -LiteralPath
'C:/Projects/HMASD-worktrees/dm-dish-b06-scientific-intake-20260907/temp/directions/degraded_incumbent_shadow_handover/test/b07-own-command-20260908-cm02'
-Recurse -Force`. Both failed shell requests were rejected before execution. Per DM direction,
no alternate shell or agent bypass was attempted. Invocation-owned cm02 and cm03 directories
remain under that same test parent; cm01 was never created. They are ignored synthetic
scratch, not evidence roots or another invocation's data. Needed logs are outside them.
Cleanup remains an explicit technical limitation requiring a permitted route; no scientific
conformance claim depends on deletion. No other scratch was touched.

DM next accepts scientific conformance; Root integrates the named pushed commit and executes
only its later bounded named command. Engineering checks do not establish scientific truth,
native-service value, complete runtime cost, or formal UAV validation. No live handle exists.
