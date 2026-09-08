# VSPC1 native hold-value B01 — complete CM code specification

This is the selected implementation specification prepared under P49, **not a CM
dispatch or a scientific launch**. Scientific authority is the complete
Convergence response `7ac8ccb01543f82715f38ad33d846c2ec649ecc2`, taken in by
[intake](VSPC1_NATIVE_HOLD_VALUE_CONVERGENCE_INTAKE_20260908.md).
The prospective [card §§2–6](VSPC1_NATIVE_HOLD_VALUE_B01_SCIENCE_CARD_20260908.md)
supplies host, information, learner, RNG, comparison, primary and complete budgets.
This document fixes the bounded changed behavior and original acceptance checks;
ordinary implementation choices within it remain CM's.

## 1. Starting code, checkout and owned surface

Designated authoring checkout:
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch `codex/direction-vsp_c1`.
The P49 worktree contains documentation/Pro input synchronization and the immutable
response; it has not copied or modified UCOPE implementation during preparation.
**Complete committed code input is6374063408208ba67b8cb7c69ebc0babb0f00259.**

Read/reuse at that source:

- `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`:
  `make_real`, `SyntheticAdapter`, feature assembly, `HoldState`, `team_reward`.
- Same package `policy.py`: `Actor`, `Critic`, `templates`, `arm_copy`, `generator`,
  `joint_terms`, `sample`, `snapshot`, `exposure`; `learner.py`: `collect_episode`,
  `recurrent_outputs`, `returns_to_go`, `optimizer_for`, `update`.
- Same package `study.py` is a reference for serial episodes, deadline accounting,
  counters and writing; its T/G assignment and n2 aggregate are not this study.
  `scripts/run_ucope_uav_motion_prefix_b01.py` supplies deferred numerical imports
  and process-start timing. Do not call its real runner or aggregate.
- `envs/pettingzoo/{uav_env,env_adapter}.py` remain unchanged dependencies.
- Existing `tests/experiments/candidates/ucope/uav_motion_prefix_b01/test_agent_clipping.py`
  verifies inherited masks, compound density/reduction and actual update behavior.

**Concrete source integration fact:** at inspected main
`fc9f6f6548b778b28acdcd058567e27998ea72b8`, UCOPE `__init__.py` and `environment.py`
are absent; the named policy/learner/study and core environment/adapter match637406340.
Both missing files exist in the complete source commit. Root must supply that full
committed dependency tree before implementation/capture, either the complete named
source or its normal committed integration with this card/spec. Do not synthesize
a substitute environment, vendor those files into VSPC1, recover them from a live
remote process or pretend current main alone is that source. This is an exact input
need, not an adverse scientific finding or new research task. Source-surface equality
matters; later doc-only commits do not invalidate the code input. Root records the
one resulting full starting SHA supplied equally to all comparison arms.

New owned code only:

- `experiments/candidates/vsp_c1/native_hold_value_b01/{__init__,critic,study}.py`
- `scripts/run_vspc1_native_hold_value_b01.py`
- `tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_critic.py`
- `tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_study.py`

Own the implementation/acceptance evidence for this bounded module; no UCOPE/core,
other direction, governance or baseline changes. Follow `experiments/AGENTS.md`,
`tests/AGENTS.md`, `scripts/AGENTS.md`. You are not alone in the codebase; preserve
other writers' work and serialize overlapping edits/index actions in the supplied
checkout. Root remaps the same relative paths into comparison worktrees when applicable.

## 2. Critic and initialization

Implement `GatedCritic` with the card§3 formula. For136-wide input, r is exactly
[119,123,127,131,135]; x is the ordered complement. Partition original first-layer
columns, keeping its bias with z=W_x x+b1, and keeping the full Br contribution.
The second tanh layer and output remain128→128→1. It must accept every leading
shape used by collection and stacked rollout training and return the source scalar
value shape. Do not add actor history, current action/duration or a new state field.

Keep MLP-V the original full critic. Make one original common template using its
actor-then-critic seed order, then independent copies for both fits; **both** calls
to source actor copying must enable the duration head. Their common tensors and
initial duration weights/biases must correspond, with no shared mutable storage.
GATED-V adds only the bias-free5→128 zero gate (640 parameters). Construct zeros
without an extra RNG draw; do not initialize a random layer and call that zero
exposure. Preserve ordinary FP32 and original common initialization.

The partitioned first-layer arithmetic and gate may have a different floating-point
reduction from the dense MLP. Check ordinary normalized-input FP32 output agreement
at A0 with rtol1e-5/atol1e-6; if the concrete scale warrants another tolerance,
report it to CM with the affected values, without imposing a scientific bit theorem.
Do not require equal actor updates: extra gate gradients can change joint clipping.
Preserve one first-layer calculation of Wx/Br plus one gate map; do not add a second
full critic forward, ensemble or counterfactual call.

Reuse the source actor, collector, return computation and optimizer/update. Do not
copy/rewrite the PPO implementation or change its clipping to isolate the gate.
Original `exposure` can report defined actor/critic/total norm ratios. Additionally
record gate initial/final norm and absolute displacement; relative gate displacement
is null/not-defined for zero initial norm, with a plain reason. No epsilon-denominator
gate ratio or minimum movement threshold. Both duration heads retain source exposure.

## 3. Study plumbing and fixed configuration

Use a small VSPC1 study entry, not a T/G relabel of `ucope.study.run_pair`:

1. Real configuration is exactly seed8101, horizon256, train episodes512, eval32,
   chunk32, four source epochs, ratio grouping`agent_compound` for both arms.
   Scientific names/order are`GATED-V`, `MLP-V`, then reference`H`.
2. `collect_episode` and `update` must both receive
   `ratio_grouping="agent_compound"` explicitly. Default`joint` is not equivalent.
   Both actors must have duration heads; no learning arm is the old no-duration G.
3. Preserve card§4 RNG domains with separate private per-arm training streams and
   per-episode evaluation streams. Both environments are constructed at b+1000;
   H reuses the MLP environment. No new environment constructor or model for H.
4. Collect two complete256-step episodes, perform the source four-epoch update,
   and repeat256 times per fit. Use unaveraged native return-to-go targets, not J.
   Keep the source held-step observations, recurrent state and velocity/duration
   masks; no event forcing, resampled hold, newly filled current duration or skip data.
5. Save the final actor+critic checkpoint for each learned arm with its explicit
   algorithm/configuration/seed identity. Evaluate only these final sampled policies
   on32 matched resets each, then H on those32 resets. Do not use source n2
   `aggregate`, old master sets, best checkpoints or initial/intermediate evaluation.
6. Retain per-episode native rows (including prefix/suffix values already computed),
   per-rollout losses and actual counts. Turn optional local-index/frame collection
   off; the new question does not claim information-path attribution. Count nonzero-r
   rows from returned collected critic inputs, by phase/arm, with no extra forward.
   If an episode is partial, label any completed-episode-only hold count accordingly;
   preserve the source's actual partial native step/decision counters.

One `summary.json` must identify object`VSPC1-NATIVE-HOLD-VALUE-B01`, card path,
mode, seed8101, ratio grouping, configuration/seeds, actual launch SHA, complete
counts, arm fit/endpoint completeness, exposure and resource/budget limitations.
Keep final checkpoints and ordinary JSONL episodes/rollouts. No internal schema
framework, registry, source guard, retry tree or new logger is needed.

Primary construction pairs evaluation rows by declared episode/reset identity,
not list order or inherited labels. For expected32 endpoints, retain all three J
lists and all GATED−MLP/GATED−H/MLP−H differences, means and sample-SD/sqrt(n)
conditional SE. A missing primary endpoint is incomplete; do not silently average
available subsets and call the fixed pair complete. Missing H alone leaves a
trustworthy primary complete and H-relative claims unavailable. Preserve all actual
rows. Reference differences are dependent: `(GATED-H)-(MLP-H)=GATED-MLP`.
Expose UP/WITHIN/DOWN only for a complete primary, with strict±.01 outer tests and
inclusive WITHIN endpoints; no significance or training-population inference in code.

## 4. Process budget and publication

CLI records whole process start before heavy imports, sets OMP/MKL/OpenBLAS/NumExpr
and Torch numerical thread counts to1, and uses CPU FP32. `--out` is required.
Real invocation takes`--seed 8101`; fixture mode is explicit
`--engineering-fixture --seed 9001`. No real scientific budget/host/seed override,
aggregate mode, resume or automatic retry is needed.

Fixture configuration reuses `SyntheticAdapter`: horizon8, train2, eval2, chunk8,
same four-epoch learner, same two duration-capable actors and critic contrast;
mode`ENGINEERING_FIXTURE`, never UAV evidence. Pair counts are80 synthetic team steps,
8 Adam calls,6 evaluation episodes,10 complete scored episodes and2 constructor
resets. No real factory/native environment import or native call in fixture mode.
This fixed small fixture is engineering verification, not another scientific arm.

Complete real caps remain1800s/arm and3600s/pair, GATED then MLP, with startup/common
initialization charged to GATED and all H/pair publication/readback/exit to MLP.
Deadline checks use one continuous process timeline with no phase clock reset.
Record an indivisible overrun. Stop on cap or nonfinite/faithfulness failure,
preserving completed and partial counts/rows/checkpoints. A sign is never a stop
reason. No second arm allowance can repair an over-budget first arm.

Retain primary if only H or optional diagnostics/resources fail. Publish available
data and concrete dependent limits; no automatic H completion or alternate reader
experiment. Read back primary summary/checkpoint identity as ordinary publication
verification inside the cap, not a provenance gate. Missing telemetry is
`resources_unmeasured`; failed mandatory admission refuses a future invocation.
Resource admission and detached remote execution are the existing external route,
not new code to build. This engineering assignment runs no native invocation.

## 5. Original acceptance checks and original commands

Perform a focused change check, not all historical suites or a replay experiment.
The new tests cover these boundaries in the same bounded deliverable:

- Known feature-column mapping and no current-duration backfill; A0 ordinary FP32
  output correspondence, expected parameter counts, common initialization/duration
  copies, independent storage and no gate-initialization RNG draw.
- A nonzero-r constructed case changes the gate/value path; r0 has no direct gate
  contribution/gradient. Do not assert later learned common weights or actor steps
  must stay identical. Test ordinary return/output behavior, not a formal theorem.
- Actual new study/CLI plumbing gives **both** actors duration heads and passes
  compound grouping to collection **and** update. A scripted engineering hold can
  check pre-decision t0 zeros, countdown3/2/1, eligible masks and recurrent/reward
  rows; no such script enters real mode. Reuse existing clipping tests below for
  signed clipping, owner grouping and masked/primitive-row reduction.
- Synthetic or stubbed study counts, all seed domains, single-pair primary and
  final-only sampling; analytic endpoint arithmetic, strict/inclusive MEI branches,
  negative outcomes, missing primary, missing H, and preservation through publication.
  A fake clock tests whole arm/pair cap accounting including H/late publication,
  without sleeping or running a long workload.
- Gate absolute exposure with undefined zero-norm ratio, defined common/total
  ratios, and clear fixture/real identity. No minimum gate exposure acceptance rule.

Use the configured local scientific interpreter for these short, uncommitted
engineering checks; no package upgrade. Original focused command,≤300s total:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b01 tests/experiments/candidates/vsp_c1/native_hold_value_b01 tests/experiments/candidates/ucope/uav_motion_prefix_b01/test_agent_clipping.py
```

One original complete runner smoke,≤60s, with ordinary artifact readback:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vspc1_native_hold_value_b01.py --engineering-fixture --seed 9001 --out temp/directions/vsp_c1/exp/native_hold_value_b01_engineering9001
```

Check its summary80 steps/8 Adam/6 eval and both checkpoints, both duration heads,
complete three-arm synthetic output, primary dependence and finite defined exposure.
No additional scientific exposure or real-mode probe is an acceptance command.
Record actual command, exit, wall and relevant output/diff; don't merely assert success.
Independent production review is required for the changed value input/initialization,
learning/plumbing and primary boundaries. Review uses the produced diff/evidence;
it does not multiply scientific calls or repeat checks without a concrete gap.

## 6. Full five-item handoff for Root's later implementation assignment

1. **Deliverable:** implement this one disposable native critic comparison and its
   faithful final primary/publication; return code/diff plus the original focused
   acceptance evidence. This assignment ends at engineering acceptance, with no
   native execution or new scientific choice.
2. **Owned paths/entry points:** §1's new VSPC1 module, runner and two test files in
   the existing designated checkout; read-only source637406340 symbols are the reuse
   base. Supply the two named missing committed dependencies before capture. Do not
   copy UCOPE into VSPC1, edit core/UCOPE or alter unrelated work.
3. **Preserved semantics:** card§§2–5 and this spec§§2–4; same duration-capable
   actors, actual pre-decision information, compound-agent masks/reduction, native
   reward/return-to-go, RNG, recurrence, optimizer and matched finite counts. Only
   the selected640-parameter critic gate differs.
4. **Acceptance:** exact commands and changed boundaries in §5; card§§2–6,
   evidence-spec§§4,5.2,11.4,11.8–11.9 and engineering-scope§§4–5. No source is
   accepted merely because the Pro response or fixture completes. Return any
   source/meaning gap precisely to this DM through Root; do not rewrite the contract.
5. **Budget/stop:** ≤2000 new non-test source lines,≤600 runner lines,≤300s focused
   tests and one≤60s fixture smoke; scope§4 none. Use Root's supplied engineering
   execution mode, preserving its identical five-arm capture before any eligible
   new CM coding dispatch. Every arm receives this same complete task/spec/code and
   original checks; no historical replay, model-specific variant or extra native
   call. No CM has begun this task during P49. Once selected code is accepted,
   Root receives its exact source and the still-unexecuted card; any actual
   scientific invocation needs its concrete later route and fresh admission.
