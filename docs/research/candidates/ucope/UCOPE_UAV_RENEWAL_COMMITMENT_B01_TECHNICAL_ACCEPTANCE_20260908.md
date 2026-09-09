# UCOPE renewable commitment B01 — implementation acceptance, 2026-09-08

## Binding and delivered source

The accepted implementation is **a453447cb011d50c6bb63ed7fc40180134a914b5**,
source tree `e2372f46fcf50ad10eddb04f3e30aafc288651b3`, pushed on `codex/ucope`.
Authoring checkout: `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`.
Starting checkout `5a7455c0f4745622e7dcadc8b96e607218b3a300` was clean; unrelated work was preserved.
Contract: [CM handoff](UCOPE_UAV_RENEWAL_COMMITMENT_B01_CM_HANDOFF_20260908.md)
and [science card §§2–7](UCOPE_UAV_RENEWAL_COMMITMENT_B01_SCIENCE_CARD_20260908.md),
the latter frozen at `ec82119adb83044ac9eff346a4779d3aceffa334`.

The five changed production paths are existing `uav_motion_prefix_b01/{environment,policy,learner,study}.py`
and `scripts/run_ucope_uav_motion_prefix_b01.py`. The owned tests are expanded
`test_pair_plumbing.py` and new `test_renewal.py` in the mirrored directory.
Production adds 72/deletes 30 lines; tests add 158/delete 9; runner remains 54 lines.
Scope §4 additions: **none**, as card §6 fixes. No base environment or governance changed.
Most production additions are the requested selector/publication/count fields; their necessity
is card §§2,5,7, and independent review covers this orchestration share.

T samples velocity and conditional duration at each owner's own expiry. The same eligibility
mask controls sampling and stored PPO density. Held owners keep commands and consume no fresh
action draws; every actor and the critic retain primitive observations. Existing likelihood,
PPO objective/denominator, recurrence, initialization, optimizer and RNG laws remain in place.
A selected duration label survives administrative truncation. Suppression is counted after
executed held steps; censoring is counted only after executing the horizon step with a timer
still exceeding one. Partial attempts retain actual selections and steps. Added phase counts,
T−H and arm means are limited to `renewal_b01`; historical selectors retain their output laws.

## Focused execution and coverage

Exactly one affected-directory suite ran on `hmasd-wsl-node` at the committed source above:

```text
cwd=/home/wu/hmasd-worktrees/ucope-uav-renewal-b01-p69-check-20260908
/home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp /home/wu/hmasd-worktrees/ucope-uav-renewal-b01-p69-check-20260908/temp/directions/ucope/test/uav-renewal-b01-p69 tests/experiments/candidates/ucope/uav_motion_prefix_b01
```

Configured `agent-task` handle `ucope-uav-renewal-b01-p69-check-20260908` finished with
exit 0, PID 3018378, inactive tmux. **81 passed in 3.37s**; complete timed command **3.97s**,
peak RSS 526572KiB. Cumulative directory wall 3.97s is below 300s. The sole warning is the
existing `cache_dir` setting with the explicitly disabled pytest cache provider.

New checks exercise heterogeneous release times, all-held RNG/head exclusion, continued
recurrence and gradients through held observations, behavior/recomputed compound densities,
actual detached stored-command inputs in four real Adam epochs, t254/t255 labels and physical
truncation, and a deliberate last-step synthetic failure retaining selections without projected
suppression or censoring. A short real-learner synthetic pair publishes/readbacks native-sum
J values, three contrasts and conditional SEs, phase counts, config, T/G checkpoints and totals.
Expanded CLI plumbing checks original stream/reset laws, renewal labels and early wrong-master/
aggregate refusal. Existing tests cover the unchanged objective, initialization and gradients.
These are synthetic engineering checks; they establish no real-UAV return or performance claim.

Raw receipts, commands and terminal outputs are under this authoring checkout:
[check evidence](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/),
especially [task log](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/supervisor/task.log),
[exact wrapper](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/suite-launch.sh),
and [terminal source readback](../../../../temp/directions/ucope/test/renewal_b01_p69_check_20260908/terminal-readback.txt).
The remote checkout was clean at terminal readback. Creator-owned pytest scratch was removed
and absence checked. Only necessary technical receipts remain. Committed-object carrier packs
were removed locally/remotely after staging 179 missing objects (242913 bytes); no live
interpreter upgrade, implicit source fetch or uncommitted source staging occurred. Initial
remote object enumeration hit a zsh quoting error before staging or tests; quoting was repaired.

## Independent review and CM disposition

Existing independent reviewer `rv_ah_ucope_b02_credit` inspected the complete source/test diff
at `a453447cb011d50c6bb63ed7fc40180134a914b5` and the exact-source remote terminal receipt.
Final return: **no material findings or unresolved acceptance gaps; no repairs requested**.
The reviewer verified own-expiry sampling/density, held-owner exclusion, all-held primitive
processing and denominator, original horizon labels and actual partial counts, unchanged
historical routes/initialization/checkpoints, and the three-contrast publication path.
It independently confirmed 81 passing tests, exit 0, 3.97s full wall, scratch cleanup,
+72/−30 non-test lines, 54-line runner and no prohibited §4 additions. It ran no extra tests,
scientific invocation or edits. Its residual limitation is that synthetic conformance does not
establish UAV performance or full-run timing for increased renewal work. CM accepts this
technical evidence with that limit; no open correction remains.

## Cost, publication boundary and return

Per-arm cost projection: unchanged native step/update budgets plus the card's actual-renewal
head work; B04 timings are a same-loop reference, not measured renewable duration coefficients.
No new performance experiment was selected or performed. A real-invocation projection and any
concrete over-cap gap remain with the separately allocated execution plan under card §6.
Post-learner path coverage: the selected suite exercised the affected short synthetic learner,
checkpoint, episode/count and final-primary publication path. Real 7301 remains unexecuted.
Scientific invocations, independent smoke, profiling, replay, pilot and extra evaluation: **zero**.

CM returns accepted-source readiness to the assigning DM. DM records direction-local intake;
Root owns integration and any concrete subsequent execution allocation. This assignment does
not stage a scientific wrapper, take admission, create a 7301 output root or launch a pair.
Root owns removal of the remote engineering checkout after integration/archive, unless its
next concrete allocation establishes an immediate execution dependency; record that event
rather than retaining a full checkout as backup. The shared local authoring checkout remains
in use by the direction.

## P70 preparation and committed literal payload

P70 is the subsequent execution allocation at `d749a6a26e450219d4d2f563a3256bc8f6b4fc00`,
[intake sections 1-3](UCOPE_UAV_RENEWAL_COMMITMENT_B01_P70_INTAKE_20260908.md).
The P69 source-only history above remains unchanged. Actual local starting HEAD was clean
`d749a6a26e450219d4d2f563a3256bc8f6b4fc00`; scientific source stays
`a453447cb011d50c6bb63ed7fc40180134a914b5`. Main integration is separate from this published source binding.
CM owns the sole observation through collection and returns all outcomes to DM; Root does
not poll in parallel. This pure execution/collection exclusion is already recorded
once in the P70 intake and creates no new coding/comparison enrollment.

Fresh scientific checkout: `/home/wu/hmasd-worktrees/ucope-uav-renewal-b01-7301-p70-20260908`.
Execution node: configured `hmasd-wsl-node`, CPU FP32, one Torch thread set by the runner.
Output relative to that checkout: `temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908`.
Unique supervisor handle: `ucope-uav-renewal-b01-7301-p70-20260908`.
The existing P69 engineering checkout and raw receipts are untouched.

Per-arm cost projection before submission: T retains initialization + 131072 native/recurrent
training steps + 1024 Adam calls + 8192 final evaluation steps +publication, with actual renewal
sampling/density/backward head work added. G retains that chain plus 8192 H steps. B04's complete
T 137.6704245s and G 139.2941963s are same-loop references; renewal's incremental seconds and
aggregate CPU are unknown, and the 64-256x head-row multiplier is not a full-wall multiplier.
No concrete over-cap projection exists; this allocated invocation retains the original
1800s per-complete-arm and 3600s whole limits. Serial study critical path equals this pair's
whole elapsed wall; summed per-arm wall and aggregate CPU are distinct. No pilot, new test,
profile, replay or resource inference from the synthetic suite is used.
Post-learner path coverage: reuse the accepted P69 short synthetic collector/learner/checkpoint/
primary publication coverage (81 tests); no repeated suite or smoke is selected.

Preparation observed the handle `not_found`, no prior supervisor directory, and no scientific
checkout/output before creating this exact-SHA detached checkout. All 2176 materialized tracked
files match accepted Git blobs, with explicit existence/content checks for the four candidate
modules, runner, canonical `scripts/hmasd_resource_preflight.py`, its `hmasd_platform.py`
dependency and both base UAV/adapter entry points. Canonical preflight helper SHA256:
`cb0525e9247f1c7262c198bf051e542282f5928982137b3023d36d5d69eda4dc`.
[Input readback](../../../../temp/directions/ucope/launch/renewal_b01_7301_p70_20260908/source-input-readback.json)
and syntax/staging receipts are retained beside the literal local payloads. The staged Bash
wrapper passes `bash --noprofile --norc -n`; PowerShell Parser reports zero submission errors.
These checks executed no admission or scientific payload. Both payloads are UTF-8 ASCII/LF,
with one final LF; shell variables are literal. The submission below is run directly from
`temp/directions/ucope/launch/renewal_b01_7301_p70_20260908/submit.ps1` without reconstruction.

Remote Bash wrapper `/home/wu/hmasd-inputs/ucope-uav-renewal-b01-7301-p70-20260908.sh` (707 bytes), SHA256
`d004393622f42a05b66917f8acf3a2fab2bab0f9579a11f849d2a80ddcfdadb8`; exact committed content:

```bash
set -euo pipefail
cd /home/wu/hmasd-worktrees/ucope-uav-renewal-b01-7301-p70-20260908
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/.agent-tasks/ucope-uav-renewal-b01-7301-p70-20260908/resource_admission.json &&
mkdir -p temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908 &&
cp /home/wu/.agent-tasks/ucope-uav-renewal-b01-7301-p70-20260908/resource_admission.json temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/resource_admission.json &&
exec /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_uav_motion_prefix_b01.py --pair renewal_b01 --seed 7301 --out temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908
```

PowerShell submission (338 bytes), SHA256
`5efe2139a8aeeaa66b40293d9c6768fe33ec350a1ff275b353074d688894adf4`; exact committed content:

```powershell
& ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run ucope-uav-renewal-b01-7301-p70-20260908 '/usr/bin/time -f whole_wall_seconds=%e,peak_rss_kib=%M /usr/bin/timeout --signal=KILL 3600s /bin/bash --noprofile --norc /home/wu/hmasd-inputs/ucope-uav-renewal-b01-7301-p70-20260908.sh'"
exit $LASTEXITCODE
```

The preflight and scientific command are one supervised shell chain joined by `&&`.
Fresh physical AND effective available memory must meet 4 GiB before scientific output-root
creation, model/RNG work or execution. A failed admission remains in the supervisor root.
The external whole timeout includes admission and publication; the runner retains its own
per-arm limits. At most one accepted submission is allocated. Uncertain acceptance is
reconciled on this exact handle; no retry/resume/replacement or extra evaluation follows.
Terminal observations and collection will append below without changing these payload bytes.

## P70 terminal execution and collection acceptance

**Technical acceptance: PASS**, one accepted scientific submission, source
`a453447cb011d50c6bb63ed7fc40180134a914b5`, master 7301. Literal payload binding was
committed/pushed at `345e41b2f83b9ebe86725c9099bf2f5d295358cf` before executing the exact
local `submit.ps1`; its output confirms one accepted supervisor submission. No resubmission,
retry, resume, changed master, extra H/evaluation or parallel observation occurred.
CM followed the same handle to terminal and collected all outputs. Source remained clean
and exact at terminal readback. The staged wrapper's collected bytes retain the committed digest.

Supervisor `ucope-uav-renewal-b01-7301-p70-20260908`, PID 3020108/start epoch 1788929303,
finished exit 0 with inactive tmux. Log start 2026-09-09T12:48:23+08:00 and
end 2026-09-09T12:53:28+08:00. Admission was a separate successful event, assessed
2026-09-09T04:48:23.972732Z: physical/effective available memory both 15639891968 bytes,
minimum 4294967296 bytes, both floors true, no failure reasons. The supervisor's admission
receipt is byte-identical to the copy in the scientific output root. The committed shell
chain ran that accepted canonical helper before output-root creation and learner execution.
Subsequent normal observations saw 65, 323, 583, 903 complete episode rows under the same running
PID, establishing learner progress separately from supervisor acceptance and memory admission.

| Complete-path measurement | Observation |
| --- | ---: |
| Outer wall, including admission and publication/exit | 304.85 s |
| Runner whole wall | 295.8246927349828 s |
| T complete arm wall | 160.45789840299403 s |
| G complete arm wall, including H and final publication | 135.36679288500454 s |
| External peak RSS | 556972 KiB |
| Aggregate CPU work | not measured |

Runner status COMPLETE; limits empty; no cap breach. Both complete arms are below 1800s and
outer whole is below 3600s. Serial study critical path is 304.85s; the sum of recorded arm
wall is 295.82469128799857s. Outer and runner clocks have different boundaries; their gap
includes admission/startup/shutdown and is not attributed to a measured kernel or phase.
These are direct wall/RSS/admission observations, not an assertion of continuous resource telemetry.

### Frozen work, primary and renewal counts

All 1120 episode rows, 512 rollout rows and 1600 prescribed diagnostic rows were retained.
There are 286720 native team steps, 2048 Adam calls, 96 final evaluation episodes, 1120 explicit
resets,2 constructor resets and zero partial episode steps. Each learned arm completed 512
training episodes/131072 native steps/256 rollouts/1024 Adam calls. T/G each have 32 final
episodes and H has 32; no extra native calls were collected. Config/seed/reset/checkpoint
bindings, every J=reward_sum/256, finite numeric JSON, finite FP32 checkpoints, parameter
counts and native publication values passed read-only inspection. Supervisor-printed primary
and counts match summary.json. No favorable parameter movement was imposed as an acceptance rule.

| Native final endpoint | Mean | Conditional evaluation SE |
| --- | ---: | ---: |
| T-G | 0.055673191348834944 | 0.011556059794903147 |
| T-H | 0.05305453732049459 | 0.01182038845858344 |
| G-H | -0.002618654028340355 | 0.011943248746505064 |

Arm means: T=0.18553283836801163, G=0.12985964701917668,
H=0.13247830104751704. All 96 J values and all three signed paired-difference
vectors are retained in the native summary. Conditional SEs were recomputed from 32 paired
final episodes; independent training n=1 remains unchanged. DM owns the all-outcome interpretation,
including G-H's sign; technical acceptance makes no training-population or causal claim.

| T phase | Owned velocity/duration selections | Selected d4 | Actual suppressed decisions | Horizon-censored holds |
| --- | ---: | ---: | ---: | ---: |
| Training | 255710 | 134282 | 399650 | 1592 |
| Final evaluation | 15883 | 8419 | 25077 | 93 |

G has 655360 training and 40960 final velocity decisions, zero durations/suppression/censoring;
H has zero decisions. Episode, rollout and phase-summary event sums match. Every complete T
episode satisfies selections +actual suppressed decisions =5*256; duration and velocity
selection counts agree. Actual duration-head forward rows are 1566026
(6*255710+2*15883), giving 3457785408 dense forward
multiply-adds at 2208/row. These counts derive from the frozen path and actual events; they
are not additional profiling or counterfactual runtime measurements. Full per-event timing/
label trajectories were not collected, as the card selected aggregate counts only.

T/G final checkpoint parameter totals 68553/66311 match; T head 2242, hidden 2176/final 66.
Stored-checkpoint final norms match the reported exposure groups. T total displacement is
8.719639778137207; G total displacement is7.15549898147583.
T duration-head displacement is0.7187902927398682, hidden-layer
0.6962713599205017, final-layer0.1785096526145935.
The final layer's zero initial norm retains null relative displacement. The readback does
not reconstruct a training run or claim independent replay of displacement histories.

### Collected bytes, checks and return boundary

Collected local artifact root in the authoring checkout:
`temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908`. The seven output SHA256 values independently read on the remote node
match the local bytes:

| Output | SHA256 |
| --- | --- |
| summary.json | `d04ae37aa99ae2a648c1db66494549626a986f42a80e12102da10606920f6e5d` |
| episodes.jsonl | `1e7cb79778940283b1eaa3bd67a92b42416cc226984de6ce8f5f24b4d4183811` |
| rollouts.jsonl | `09d53d6d4918b3251b3dda85d2bfc3c87b05d805f782670d33006011425b33ad` |
| diagnostics.jsonl | `4ddaef03efe044670bc939eada8ed0cd34f7d5f1d38675f1e3e35584c45d8a04` |
| final_T.pt | `2714bec3aa4f7f067db0ced5f50eb24897915c151b7a689747adc7a915d7032a` |
| final_G.pt | `6e4d8e0f39e68213124b92efdc6e1e0ed43afee202f1e4588d367b482dcbdb64` |
| resource_admission.json | `8df70040e845698ff003ac83a8ff7df4dd8d0a053663230e667d2d5c77b5adca` |

[Read-only collection report](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/collection-readback.json),
[verification source](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/verify_collection.py),
[verification output](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/verification-output.txt),
[remote source/process/hash readback](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/remote-readback.txt),
[supervisor log](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/supervisor/task.log) and
[executed wrapper](../../../../temp/directions/ucope/exp/ucope-uav-renewal-b01-7301-p70-20260908/executed-wrapper.sh) preserve the detailed evidence.
The collection verifier inspected recorded JSON/tensor bytes only; exit 0, no model,
learner, evaluator, scientific replay or extra test invocation. No material source,
count, publication, checkpoint, numerical, admission or cap discrepancy remains.

This batch ends with terminal collection and technical acceptance. Checkout/index ownership
returns to DM for all-outcome intake; Root integrates that return and owns later archive/
reclamation of the scientific checkout and wrapper after evidence and intake are preserved.
P69's separate test checkout/raw receipts are untouched and remain Root's separate cleanup.
No subsequent pair, extra evaluation, source change or scientific follow-up is implied.
