# FSD UAV individual-renewal B01 technical acceptance

P69 source-only assignment in `C:/Projects/HMASD-worktrees/codex-fsd`, `codex/fsd`.
Started clean at `3fa896737cf805ce63da048ddfa8873f2c5cc18b`, with exact baseline
code `335425e92cda16677fd1f4181e2c31730887e911` and published scientific input
`b317b1edde00d05a075b5f5ec5a8bb8e18d9cdba`.
Contract: [CM specification §§1–6](FSD_UAV_INDIVIDUAL_RENEWAL_B01_CM_SPEC_20260908.md),
[card §§2–7](FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md).

## Delivered source and protected boundaries

New runner `scripts/run_fsd_uav_individual_renewal_b01.py` uses the ordinary E0
configuration/environment/parameter helpers. Its shared arm builder sets I's
individual cost .25 before either learner or evaluator construction; D0 has
both numeric costs +infinity and I's team cost is numeric +infinity. Common
k/individual/team caps10, latent6/6, six UAVs/fifty users, H500 and ordinary
learner settings remain. Only configuration cost metadata encodes `Infinity`;
scientific values pass finite checks before JSON-compatible conversion.

The new collector passes original actions and sampled step_data into native
movement and storage, with unscaled scalar rewards. It stores terminal next
values first, then takes both subsequent observation and global state from
reset info. Five full16×500 rollouts use actual preceding updates and ordinary
D2 storage/GRU/credit. At all-terminal edges zero bootstrap requires no extra
skill/action sampling. Per-rollout losses, raw returns, D2 decisions/causes/token
switches/segment counts, real wrapped optimizer counts and parameter exposure
are published before ordinary buffer clearing. Same-token and no-gap I data
remain valid; unused parameter exposure may be null.

The separate evaluator reuses E0's active-module/normalizer synchronization,
with an overridden constructor that uses the same arm-aware builder. All
construction, synchronization, buffer/lane resets and deterministic no-gradient
scoring are inside E0's training-RNG-preservation context. Evaluation RNG and
32 private lane seeds start at780503; training RNG and16 lane seeds start770503.
Only the final update-five endpoint is constructed. Evaluation does not store
training transitions or perform updates; its recorded segment/storage counts
can therefore be zero while decision/switch counters reflect scoring.

The endpoint retains U and J=6U/500 plus native coverage, quality and altitude
components from existing reward info. I's in-cap pair readout checks identity,
seed law, required learning/endpoint counts, actual specified arm configs and
common fields; it publishes32 ordered differences, mean, sample SD and conditional
SE. Missing/damaged D0 preserves the completed I endpoint with an incomplete pair.
The original positive/inclusive±.01/opposite branches are unchanged. Actual
nonfinite data stops the affected path and leaves readable last trustworthy
facts. No old checkpoint, public corridor mask or rescue endpoint is used.

The six read-only paths (agent, config, UAV base/scenario1/adapter and E0) were
compared against the exact baseline and remain unchanged. Old corridor files,
old tests and DM science/owner files were not edited. Runner424 lines and test488
lines;424 new non-test source lines satisfy600/2000 budgets. Engineering scope§4:
none per card§6; no new execution framework, guard, registry or telemetry system.

## Focused checks and correction record

Original specified commands were run on the fixed scientific Python. Every
pytest invocation used direction-scoped scratch as required by tests/AGENTS.md;
bytecode and diagnostics stayed in the same invocation directory.

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m py_compile scripts/run_fsd_uav_individual_renewal_b01.py tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q --basetemp C:/Projects/HMASD-worktrees/codex-fsd/temp/directions/flexible_skill_duration/test/uav_b01_p69_source_20260908/pytest_retry tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py
git diff --check
```

First focused process:32 passed/1 failed, pytest7.06s, combined syntax/test wall
9.140208s. The fake main failure came from an unnecessary late Windows RSS import
of E3, whose unrelated corridor class constants encountered the fixture's forbidden
real-agent constructor. The runner now reads optional Windows peak RSS directly
through installed psutil; this removes the corridor dependency. No scientific
semantics were changed in that correction.

The original py_compile invocation also hit the Windows path-length limit in
its task-scoped cache. An extended cache prefix with forward-slash source argv
then hit Python3.10's mixed-separator path handling. The exact same two source
files compiled successfully using native backslash argument separators and
`PYTHONPYCACHEPREFIX` set to the extended Windows form of this task's scratch
`pycache` directory. No interpreter setting or installed dependency was changed.

Final captured evidence:

```text
.................................                                        [100%]
33 passed, 14 warnings in 4.26s
py_compile_exit=1; pytest_exit=0; complete_checks_wall_seconds=5.795297
py_compile_exit=0; py_compile_wall_seconds=0.1022448
```

The first exit1 in this final excerpt is the second cache-path attempt, followed
by the successful syntax-only correction. No pytest rerun followed that path-only
correction. After the review correction, the focused pairing regression passed (1 passed in3.23s; process wall4.6118665s). Combined observed checks19.6496163s; the directory remains below300s.
Warnings are existing matplotlib/pyparsing deprecations. `git diff --check` passed.

Task scratch cleanup was attempted after recording evidence. Automatic approval review rejected both verified native PowerShell deletions as "blocked by policy". The ignored scratch directory `temp/directions/flexible_skill_duration/test/uav_b01_p69_source_20260908` remains; no source or scientific artifact depends on it.

The33 fake cases exercise both real numeric config consumers with production
16/32-lane,H500 dimensions but fake models/environments; actual actions/raw rewards/
original step-data/terminal-reset boundaries and all five subsequent updates;
separate evaluator weights/ValueNorm and preserved Python/NumPy/Torch RNG; native
component reporting; full32-value6/500 arithmetic, sample SD/SE, inclusive MEI;
wrong/missing/damaged companions; nonfinite action/loss/primary/parameter failure
publication; fixed CLI rejection; and closed-file cap boundaries. Autouse fixtures
forbid real HMASDAgent/UAVBaseStationEnv construction. No scientific smoke occurred.

## Independent review

Reused configured reviewer:
`/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47/rv_ah_fsd_b03_p47`.
Independent inspection found one unnecessary launch-SHA equality requirement in the pair assembler. It was removed: SHA remains reported metadata, while the card-defined scientific identity, counts and configuration comparisons remain. The existing full32-value pairing test now confirms that a different document-descendant SHA does not block the identical result. Focused regression passed. Final independent disposition: no material finding remains. Reviewer verified the correction and the configuration, action/storage/reset, evaluator/module/ValueNorm/RNG, native primary, counts and cap boundaries by source inspection; inspected focused coverage without rerunning tests. No real runtime or cap-feasibility claim follows.

## Cost, publication coverage and remaining runtime boundary

Per-arm cost projection: existing card scenarios remain1617.82s D0 and16178.2s I,
from1.15×(5×225.2+2×(2392.4−10×225.2)) and its tenfold decision-row stress factor.
The implementation preserves the underlying five16×500 work, common team
rows800/rollout and maximum I joint rows8000/rollout. No added scientific endpoint,
probe or changed multiplier invalidates those scenarios. They are historical
illustrations, not measured current rates or guaranteed bounds, and fit the
original complete3600/18000s caps. Sum cap21600s remains distinct from study
elapsed time, summed invocation wall and aggregate CPU work; none was measured
by source checks. No new timing/profiling pilot was run.

Post-learner publication coverage: fake complete main D0/I runs exercise both
manifest/JSONL/endpoint/summary publication and companion assembly; failure cases
exercise last trustworthy facts and incomplete pairing. This establishes wiring
and arithmetic, not actual native learning quality or future runtime completion.

Exact future commands, from the later accepted-SHA detached remote worktree:

```text
python scripts/run_fsd_uav_individual_renewal_b01.py --arm D0 --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/D0
python scripts/run_fsd_uav_individual_renewal_b01.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/D0/summary.json
```

The fixed CLI intentionally exposes no seed override; the card fixes770503/780503.
The runner records its launch SHA from the later detached checkout without a
source-currentness gate. Subsequent execution still needs Root's explicit full
allocation, committed-source staging, fresh adjacent admission and the existing
supervisor's complete outer D03600/I18000 timeouts with no grace or retry. These
include imports, model construction, all learning, evaluation and closed-file
pair publication; cooperative clocks cannot interrupt a single optimizer update.

No production root, remote source staging, admission receipt, model/environment,
scientific invocation, checkpoint or runtime handle was created by this source
assignment. Root integrates accepted code; DM owns the technical-readiness intake
and completed Root-action return. No automatic scientific successor follows.
