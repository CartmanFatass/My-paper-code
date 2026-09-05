# A01 technical acceptance and launch record

Technical acceptance: the frozen retained-prefix diagnostic exists at pushed source
`bfe4952beeff9cff237d5b16325c02e5c0c08664`. Three focused reading tests passed, and the
single actual toy CLI publication smoke passed with exact native endpoint bytes and
recurrent hidden state against the original prefix loop. No scientific output yet.

## Source, scope and review

CM branch `cm/n3-dish-funnel-a01-20260904` assembled both accepted histories at
`6cb0e3cc796c49ab946e588a3f50cbae4e4688bb`. Implementer used its own worktree.
Only new `funnel_a01.py` (249 lines), `scripts/run_dish_prefix_trigger_funnel_a01.py`
(66), and corresponding `test_funnel_a01.py` (159) were added. Non-test total315;
conservative orchestration89/315=28.3%; engineering scope section4: none.
Production R06/B01 bytes remain unchanged from e0541d0c.

Independent reviewer `/root/dm_amx_n3_continue/cm_am_n3_dish_c04/rev_ah_n3_c04_precision`
returned no material findings. Early pending-intent overcount was fixed before commit:
count only the next boundary at origin+1, including first terminal boundary and excluding
stale padding. Terminal first occurrence counts once. Original policy pass, normalization,
RNG, native ordering, precision, checkpoint and padding are preserved. Separate boundary
latches, pre-emission version, completion latch conjunctions and copied-state counter
deltas implement the card convention. No production kernel or learning change.

## Exact-source verification

Node `wsl_4070`, cwd `/home/wu/hmasd-worktrees/dish-prefix-a01-bfe4952b`, detached at
the source above. A committed Git bundle supplied exact pushed objects; no uncommitted
source was transferred. Python `/home/wu/.venvs/hmasd/bin/python`.

First command after `cd`:
```
/home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --durations=0 --basetemp temp/directions/degraded_incumbent_shadow_handover/test/a01_bfe4952b tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/test_funnel_a01.py && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_prefix_trigger_funnel_a01.py project-cost
```
Task `dish_prefix_a01_verify_bfe4952b_01`: 3 passed,1 setup error in1.00s.
Exact failing `Path.mkdir(mode=0o700)` reproduced `FileNotFoundError`; parent did not
exist. This was test scratch preparation, not an executed smoke failure. Created only
the missing scratch parent; source unchanged. Second command ran only the unexecuted node:
```
/home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --durations=0 --basetemp temp/directions/degraded_incumbent_shadow_handover/test/a01_bfe4952b_smoke tests/experiments/candidates/degraded_incumbent_shadow_handover/first_trigger_source_scout_b01/test_funnel_a01.py::test_real_toy_publication_smoke_and_original_prefix_identity && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_prefix_trigger_funnel_a01.py project-cost
```
Task `dish_prefix_a01_smoke_bfe4952b_01`: exit0,1 passed in1.08s; smoke call0.10s,
supervisor wall2s. Existing pytest cache_dir warning under disabled cache provider.
Both original logs remain under `/home/wu/.agent-tasks/<task>/task.log`.
Tracker observed both accepted tasks; CM collected terminal logs. No repeated passing suite.

Direct project-cost: `1.5 * (0 * 10.672341100056656 + 300)`, projected450s,
cap600s, within_cap=true; one replay path receives full cost.

## Frozen result invocation

Only the original seed11 checkpoint, SHA256
`0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa`,2070711bytes.
Prospective supervisor task `dish_prefix_funnel_a01_seed11_a1`, same exact cwd/source.
Single command:
```
cd /home/wu/hmasd-worktrees/dish-prefix-a01-bfe4952b && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_prefix_funnel_a01_20260904/a1_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_prefix_trigger_funnel_a01.py run --seed 11 --checkpoint /home/wu/hmasd-worktrees/dish-b01-c04-e0541d0c/temp/directions/degraded_incumbent_shadow_handover/exp/n3_b01_c04_20260904/seed11_a1/checkpoint.pt --admission temp/directions/degraded_incumbent_shadow_handover/exp/n3_prefix_funnel_a01_20260904/a1_admission.json --out temp/directions/degraded_incumbent_shadow_handover/exp/n3_prefix_funnel_a01_20260904/a1
```
Actual node requires physical/effective memory>=4GiB. Receipt outside absent result child;
one Torch CPU thread,FP32 policy,float64 native,16 original rows,1200 ticks each,
per-tick600s cap. No source fork or training. Full-size reference match and actual
measurements remain unverified until collection. Toy publication coverage does not establish
a scientific result. No extra seed or successor authorized.
