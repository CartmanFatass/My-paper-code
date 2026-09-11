# CRTO residual complete-cycle endpoints B04 technical evidence

Object `CRTO-RESIDUAL-CYCLE-ENDPOINTS-B04`, B/EXPLORE. This is CM technical
evidence under the frozen science card; DM owns scientific intake and independently
applies its first-matching rule.

## Accepted source and protected path

Launch source `c53f3bb19c91d01ef87cb2c4b9737811eb10d795` was committed and pushed
on `cm-crto-b02-20260904` before remote preparation. Frozen card `53576cb1a` was
cherry-picked as `4d5ccabf6`. Only the new B04 module, initializer, runner and mirrored
tests implement the object; historical B01/B02/B03 and shared source are unchanged.

The three representations use B01 predictor/calibration/packet/Sattolo helpers,
canonical recipient histories and labels, explicit original RNG namespaces, FP32
and fresh seed-0 parameters/Adam states. RAW, TRUE_RESIDUAL and
CALIBRATED_DERANGEMENT each train to 258 with in-memory snapshots at 33 and 258.
All training finishes before evaluation. Ordinary legal maxima and first-printed
ties use finite signed G16 and nonnegative regret; no cycle mean or paired order.

The local numerical loop preserves B02 arithmetic while replacing inherited time
limits with the new 1200-second training-plus-forward-plus-scoring arm cap and
1500-second invocation cap. Waiting through other arms is not charged to an arm.
LONG movement must be finite positive; SHORT movement finite. Actual representation
labels replace the helper's RAW-only exposure label. No historical anchor gate,
old global mutation, hidden clock offset, checkpoint I/O or resume is added.

Calibration retains 64 disjoint K4/K8 tapes and all eligible horizon examples;
FP32 whitening, pooled midpoint empirical CDF, clipping/adverse-sign/zero-padding
packet law are unchanged. Full TRUE packets are deranged within original
split/regime/elapsed/cost cells, split ordinals 0/1, using fixed Sattolo mappings.
No regrouping by side or event/onset, EVAL-driven fitting or donor resampling occurs.

## Engineering scope and verification

Engineering-scope section 4 additions: **none**. Final research code is 250 physical
lines: module 213, runner 36 and initializer 1; tests add 175 lines. Substantive
orchestration is 72/250 = 28.8% (41 module, 30 runner, 1 initializer; neutral
whitespace excluded from numerator). The initial draft exceeded 30%; duplicate CLI,
timing, output-root and fixed-projection plumbing was removed without padding the
denominator or dropping required scientific measurements. This was a prelaunch
implementation finding, not a failed experiment or accepted budget deviation.

Independent Reviewer found no remaining material issue in final source, tests and
engineering artifacts. Local focused suite: 10 passed in 6.13 seconds including one
toy smoke, with no test failure/repeat. Toy wall was 2.9087911 seconds; missing Windows
peak RSS was marked `resources_unmeasured`, and the toy emitted no scientific branch.
Final fixed-projection-check removal and restored thread-contract field received
static review and syntax checks after that suite. No numerical operation changed.

Focused checks cover numerical loop operations, fresh equal parameter states and
Adam state, effective new time bounds, representation/packet binding, whole-packet
donors and split RNG ordinals, keyed recipient/donor exposure, all B01 branches,
and actual-sized publication. The offline fixture exercises three representations,
33/258 exposures, six 16-row readouts, 48/16 donor maps and calibration metadata.
Synthetic packets/calibration/predictions are explicitly labelled; native labels
reuse accepted B02 fixture evidence. This is new-object engineering coverage, not
learner evidence or repair of the historical A01 publication gap/native crash.

Exact committed remote source passed all 10 checks in 3.30 seconds, including one
prelaunch smoke. The existing pytest unknown `cache_dir` warning remained. Git
fetch/exact-SHA checkout succeeded through configured `zsh -lic`; shell gitstatus
and background gc/repack warnings did not prevent source materialization or tests.

Remote prelaunch check:

```sh
mkdir -p temp/directions/commitment_residual_triggered_options/test && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/commitment_residual_triggered_options/test/b04-prelaunch-20260904 tests/experiments/candidates/commitment_residual_triggered_options/residual_cycle_endpoints_b04
```

Owner-item skill was read and applied. Owner review queries on CM and Root integration
worktrees returned `[]` at the implementation boundary; another integration query
immediately before launch also returned `[]`. Fresh integration compute configuration
still declares remote-first `wsl_4070`; no owner override or routing change was observed.

## Cost and exact accepted invocation

Non-result `project-cost --seed 0` emitted the carded historical Windows stage law,
without asserting a remote calibration speedup. Shared preparation residual is
296.1136604 seconds. Factor-3 forecasts are RAW 1016.1804163734375,
TRUE_RESIDUAL 1077.5582726085938, CALIBRATED_DERANGEMENT 990.31155315 seconds;
shared 1307.3682797320312 seconds. All arm forecasts are below 1200, shared below
1500. Each arm forecast conservatively includes preparation; actual shared machine
time is charged once. No sweep or additional pilot was performed.

The one accepted process is `crto_residual_b04_c53f3bb1_01`, node `wsl_4070`,
SSH `hmasd-wsl-node`, detached cwd `/home/wu/hmasd-worktrees/crto-b04-c53f3bb1`.
Supervisor directory `/home/wu/.agent-tasks/crto_residual_b04_c53f3bb1_01/` retains
runner.sh, task.log, status, start_time and exit_code. Default tracker
`/root/tracker_tl_experiments` acknowledged this exact handle/SHA; CM released
routine polling and retained collection/acceptance. Quiet stdout is expected: the
runner saves the full summary once instead of duplicating its JSON on stdout.

Exact accepted payload:

```sh
cd /home/wu/hmasd-worktrees/crto-b04-c53f3bb1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/residual_cycle_endpoints_b04_20260904/attempt01_admission.json && /home/wu/.venvs/hmasd/bin/python -X faulthandler scripts/run_crto_residual_cycle_endpoints_b04.py run --seed 0 --output-dir temp/directions/commitment_residual_triggered_options/exp/residual_cycle_endpoints_b04_20260904/attempt01 --execution-node wsl_4070
```

The destination admission and learner are adjacent in one supervisor command.
Prospective resource contract: one CPU FP32 thread, expected RSS below 2 GiB,
physical/effective available memory at least 4 GiB, 1200/1500-second caps. Stop is
one complete summary or first admission/integrity/nonfinite/measurement/cap failure.
Observer changes do not authorize a retry, restart or duplicate process.

## Terminal collection

The accepted task finished with exit 0. CM collected complete summary, adjacent
admission and supervisor files; exact SHA, argv including `-X faulthandler`, node
and one-thread measurements agree with the prospective launch. The bounded
implementation and completed observation are technically accepted. DM independently
recomputes the scientific comparisons; no new invocation or post-result source
change occurred.

| Direct observation | Value |
| --- | --- |
| Start / terminal UTC | 2026-09-05 01:34:05 / 01:37:07 |
| Admission UTC | 2026-09-05T01:34:05.531211Z |
| Physical / effective available bytes | 12,950,413,312 / 12,950,413,312; both 4-GiB floors passed |
| Supervisor exit / total duration | 0 / 182 seconds |
| Runner pre-publication wall | 171.8017914000011 seconds |
| Peak RSS | 1,541,214,208 bytes; measured, below expected 2 GiB |
| Predictor tapes / materialized examples | 128 / 32,256 |
| Predictor updates / processed examples | 100 / 12,800 |
| Calibration tapes / examples | 64 / 16,128 |
| RAW/TRUE/DERANGED total gate updates / examples | 774 / 24,768 |
| Forward / scored / unique EVAL rows | 96 / 96 / 16 |
| Environment transitions / common-future branch steps | 54,848 / 3,520 |
| Shared preparation seconds | 120.60043037099967 |

Calibration episodes are 256..319, pooled K values [4,8]; horizon example counts
are 4:12160, 8:3968, 12:0, 16:0. These are the actual unchanged helper outputs;
zero counts at 12/16 are not missing measurements or synthetic sentinel values.
TRAIN/EVALUATION maps respectively contain 48/16 unique recipients and donors,
with zero fixed points. Both 48-entry recipient/donor occurrence maps contain
only 22 at SHORT and 172 at LONG. Preparation and native branches are counted once.

| Arm | Training seconds | Forward seconds | Scoring seconds | Training seconds/update |
| --- | --- | --- | --- | --- |
| RAW | 17.373102220000874 | 0.014060344998142682 | 0.0011217969949939288 | 0.06733760550387935 |
| TRUE_RESIDUAL | 16.70554584999627 | 0.011793982004746795 | 0.0008215380003093742 | 0.06475017771316384 |
| CALIBRATED_DERANGEMENT | 17.073687174000952 | 0.012702049003564753 | 0.0007665220036869869 | 0.06617708206977113 |

Each measured training+forward+scoring sum is below 1200 seconds; complete
supervisor duration is below 1500. Runner wall ends before JSON publication and
is not represented as complete duration. Tracker's later 277-second uptime is
time since launch, not execution time. No requested formal resource telemetry
is missing; these observations do not establish a throughput or speedup claim.

All arms start at L2/RMS/Linf
`18.87916908516977 / 0.10402732933491829 / 0.28862619400024414`.
Six representation-labelled exposure lines retain batch 32, Adam lr .001,
1056/8256 examples, .033/.258 nominal LR exposure and phase/cursor 0/0:

| Arm | Endpoint | L2 displacement / initial L2 | Linf displacement / initial Linf |
| --- | --- | --- | --- |
| RAW | SHORT33 | 0.04623144290540206 | 0.09714726999981826 |
| RAW | LONG258 | 0.1369227563959056 | 0.915735779252775 |
| TRUE_RESIDUAL | SHORT33 | 0.051145195256695676 | 0.0980900727003286 |
| TRUE_RESIDUAL | LONG258 | 0.08801190138964558 | 0.5338464052739748 |
| CALIBRATED_DERANGEMENT | SHORT33 | 0.05260804702233152 | 0.09774886397992377 |
| CALIBRATED_DERANGEMENT | LONG258 | 0.13797244260322725 | 0.9070316204301058 |

All SHORT displacements are finite and all LONG displacements finite positive.
The only runtime log warning is the existing PyTorch non-writable NumPy warning
at shared models.py:186; no exception or fault stack is recorded. It is not a
newly classified failure, and no source was changed to suppress it.

Complete 193,466-byte collected summary is preserved verbatim as
`CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json` beside this E0. It holds
all legal prediction/native-label/action rows, contrasts and emitted B01 rule
field, complete donor maps, calibration population and six exposure lines.
Local collection root:
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/residual_cycle_endpoints_b04_20260904/attempt01_artifacts/`.
The root contains summary.json, attempt01_admission.json, runner.sh, task.log,
status, start_time, exit_code and PID data. Remote evidence remains in place.

DM received this summary before E0 completion for independent scientific
reconstruction. CM and Root integration owner-review queries again returned `[]`
at the terminal boundary. No owner instruction was applied or bypassed.

Remaining limits: this technical acceptance concerns a single exposed-panel,
outcome-informed B/EXPLORE comparison. It supplies no independent replication,
general residual superiority or resolution of the historical native crash.
