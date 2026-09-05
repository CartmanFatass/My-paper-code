# A02 technical acceptance and invocation

Technical acceptance: pushed source `dd0e01bbc4aa0efd3c22b475585511232c1de4fc`
implements the frozen single prepared point. Three focused synthetic tests passed;
no carded native point was executed by verification. Scientific observation pending.

## Assembly, scope and review

CM branch `cm/n3-dish-funnel-a01-20260904` merged accepted A01 a6ff9d748 and DM card
b2ecdc168 at3168101b3. Own-worktree implementer added only
`scripts/run_dish_ground_source_point_a02.py` and corresponding B01 test file
`test_ground_source_point_a02.py`. DM reduction decision ed2cf34b1 merged atd180865d7;
source bytes remain dd0e01bb. Production/native/B01/A01 bytes unchanged.

Initial147-line wrapper returned scope52/147=35.37%, with no waiver or test dilution.
Authorized reduction removed sys/path bootstrap through module invocation, grouped symbol
imports through ordinary module imports, and redundant in-run admission validation.
Added fixed `--seed 11`; mandatory destination preflight joined by && is the sole admission.
Independent reviewer final count40/135=29.63% non-test orchestration: lines3–8,10,12–14,
100–101,104–118,121–131,134–135. Tests79lines excluded from denominator. Scope section4:none.
Reviewer found no remaining material issue; input/RNG/precision/normal mode and one prepare
without completion/model/policy are preserved. Actual native signals remain distinct from
derived geometry and margin eligibility from receipt. No physics modification.

## Exact-source verification and cost

Node wsl_4070; cwd `/home/wu/hmasd-worktrees/dish-ground-a02-dd0e01bb`, detached at
dd0e01bbc4aa0efd3c22b475585511232c1de4fc. Exact pushed objects transferred by Git bundle.
Test scratch parent created prospectively. Accepted task `dish_ground_a02_verify_dd0e01bb_01`:
```
cd /home/wu/hmasd-worktrees/dish-ground-a02-dd0e01bb && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --durations=0 --basetemp temp/directions/degraded_incumbent_shadow_handover/test/a02_dd0e01bb tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/test_ground_source_point_a02.py && /home/wu/.venvs/hmasd/bin/python -m scripts.run_dish_ground_source_point_a02 project-cost
```
Exit0;3passed in1.06s, all test phases<0.005s; supervisor3s. Existing cache_dir warning
with cache provider disabled. Original log `/home/wu/.agent-tasks/dish_ground_a02_verify_dd0e01bb_01/task.log`.
Synthetic-only arithmetic/readout and actual JSON publication; native factory and master
forbidden in smoke. No previous suite repeated. Tracker observed terminal, CM collected log.
Direct cost law `1.5 * (5 + 5)`=15s, cap60s, within_cap=true, one point receives full cost.

## Frozen single result command

Prospective task `dish_ground_source_a02_seed11_a1`, same exact source/cwd/node:
```
cd /home/wu/hmasd-worktrees/dish-ground-a02-dd0e01bb && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/ground_source_point_a02_20260905/a1_admission.json && /home/wu/.venvs/hmasd/bin/python -m scripts.run_dish_ground_source_point_a02 run --seed 11 --admission temp/directions/degraded_incumbent_shadow_handover/exp/ground_source_point_a02_20260905/a1_admission.json --out temp/directions/degraded_incumbent_shadow_handover/exp/ground_source_point_a02_20260905/a1
```
Require fresh actual-node physical/effective memory>=4GiB. Receipt outside absent result
child. Original seed11 panel0, block0/TARGET_VISUAL_MASK/K8/speed4/slot0/owner0, normalmode,
original addressed RNG/float64. One prepare, zero completedticks/model/learning. Native
point and publication wall are checked against60s; no live interruption/retry machinery.
Tracker observes accepted handle; CM collects existing evidence. No successor authorized.

## Accepted point invocation

Task `dish_ground_source_a02_seed11_a1` accepted once at source dd0e01bbc4aa0efd3c22b475585511232c1de4fc and exact command/cwd above. Before dispatch task not_found, output and receipt absent. PID1653258, start epoch1788602013 (2026-09-05T09:53:33Z). Log `/home/wu/.agent-tasks/dish_ground_source_a02_seed11_a1/task.log`. Receipt assessed2026-09-05T09:53:33.113076Z; physical/effective each12932448256bytes, minimum4294967296, passed/floor flags true, source /proc/meminfo. Tracker `/root/tracker_tl_experiments` directly handed expected15/cap60seconds and DM/CM collector addresses. No additional point or successor.

Timing precision: runner wall is sampled after point/readout/Git/RSS and before JSON publication; supervisor wall also includes process startup/publication/admission. Collection must retain both, rather than describe runner wall as complete process wall.
