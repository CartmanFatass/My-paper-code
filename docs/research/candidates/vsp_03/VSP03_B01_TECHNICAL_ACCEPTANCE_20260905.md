# VSP03 B01 source acceptance and launch freeze

The selected source is technically ready for its one fresh admitted invocation. No training,
environment episode or optimizer step has run before this acceptance. Implementation exists;
runtime check, outcomes, cost and resource conformance remain unobserved.

CM copied only the four owned files from the semantic implementer's separate worktree
`C:/Projects/HMASD-worktrees/impl-vsp03-b01-20260905` into the CM worktree. The complete diff is
new `b01.py` (415 lines), package marker (1), runner (26), and mirrored `test_math.py` (87).
Non-test total 442; runner 26. No scope section 4 addition. Ordinary required parameter
handling, scientific counters, JSON/state I/O and the explicit cap do not introduce a framework.

CM inspected the complete source and tests. Independent reviewer
`/root/dm_amx_k1_vsp03_design/cm_am_vsp03_b01/rev_ah_vsp03_b01` reported no material finding
on final b01.py bytes SHA-256 `39481f270f2d26349f872b5965754b918f0e5cfd6517e7f043afc1571fd195ed`.
CM's copied bytes match that reviewed file. Review examined armed latch, ordering, all40ticks,
service endpoints, integer reward, valid rows, true MC returns, pairing, joint loss/step,
three endpoints, F, output readback and the whole cap. Initial F count and final cap-reporting
concerns were resolved before this acceptance. The reviewer executed only static parsing and
scalar count arithmetic, confirming 1,314+257 parameters and planned 36,360episodes/1,454,400ticks.

Implementer executed this local focused test command in its worktree:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD-worktrees/impl-vsp03-b01-20260905/temp/directions/vsp_03/test/non_rollout_math tests/experiments/candidates/vsp_03/vsp03_b01/test_math.py
```

Four tests passed and one failed during fixture setup because the basetemp parent did not exist
(pytest5.24s; command6.947s). Creating only that direction-local parent and rerunning only
`test_math.py::test_primary_component_publication_without_simulation`, basetemp `publication_only`,
passed (pytest1.94s; command2.973s). Thus five distinct tests passed. Existing cache_dir warning
comes from disabling cacheprovider. `python -m py_compile` on module and runner also passed.
No repeated whole suite/smoke was run. These tests constructed two synthetic initialization
models and tiny scalar heads, generated only addressed random arrays and backpropagated a
three-row analytic loss; they executed zero environment ticks and zero optimizer steps.
They establish initialization, MC arithmetic, reductions/detachment, RNG addressing and JSON I/O;
they cannot establish the full runtime chain or scientific performance.

The exact selected eight-case check remains inside the admitted invocation, using deterministic
scripted actions and the selected T model, one backward but zero optimizer steps, clearing
gradients and consuming no training action stream. Its exposure is recorded separately.
The real final states are saved/read back; main endpoint rows and curves are read back.
The internal status is evaluated with the terminal timing/exit witness during collection.

## Frozen execution

Node `wsl_4070`, SSH `hmasd-wsl-node`, CPU float32, one compute thread, one scientific process.
Remote cwd `/home/wu/hmasd-worktrees/vsp03-b01-seed1-r01`, a detached worktree at the source
acceptance commit containing this document, committed/pushed before remote preparation.
The exact SHA will be supplied in the accepted-handle message and recorded by runner summary.
No uncommitted source is transferred. External `timeout 1800s` bounds imports through process
completion; runner starts timing before heavy imports and checks the same1800s logical cap.

Supervisor task name: `vsp03-b01-seed1-r01-20260905`.
Preflight and exact runner command inside that task:

```text
cd /home/wu/hmasd-worktrees/vsp03-b01-seed1-r01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vsp_03/exp/vsp03_b01_seed1_r01_memory.json && timeout 1800s /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b01.py --seed 1 --out temp/directions/vsp_03/exp/vsp03_b01_seed1_r01
```

Actual-node admission must report physical and effective available memory at least4GiB.
Output and resource receipt are the above cwd-relative paths. Supervisor log and exit witness
are `/home/wu/.agent-tasks/vsp03-b01-seed1-r01-20260905/{task.log,exit_code,status}`.
Complete bound includes imports, eight-case check, sequential T/G128full batches each, all
evaluations, F, publication/readback. First normal full batches measure C; E/O stay unknown
until measured. Complete per-arm projection is null while required terms remain unmeasured.
No pilot, seed change, selected endpoint change, extra configuration or cap extension follows.

Configured Python3.10.21/NumPy1.26.3/Torch2.7.0+cu118 is the declared remote runtime; no installation
or live interpreter upgrade. GPU is unused. Float32 CPU portability is prospective, without
cross-host bit equality. Current arrays are batch-local (at most128x40 tape and1152x6 observations),
two small model states plus endpoints; actual RSS is still a runtime measurement.

The existing root tracker was found completed/available. Upon supervisor acceptance, wake it
with the exact task/node/SHA/cwd/log/receipt and DM name; retain observation until its ACK.
Completion, cap or concrete required-path failure ends this attempt; no automatic successor.
