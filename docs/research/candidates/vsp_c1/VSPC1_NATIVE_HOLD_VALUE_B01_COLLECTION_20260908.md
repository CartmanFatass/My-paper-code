# VSPC1 native hold-value B01 collection: technical acceptance

Collected the one completed handle `vspc1_hold_value_b01_8101_65c89368ab0f` on
2026-09-08. Technical collection checks PASS. No source edit, rerun, new arm,
seed, H completion or scientific replay was performed. Scientific intake belongs
to the same VSPC1 DM; this record does not declare formal UAV-validation entry.

The [collection evidence JSON](VSPC1_NATIVE_HOLD_VALUE_B01_COLLECTION_EVIDENCE_20260908.json)
retains the entire unchanged native summary, independently calculated collection
checks, exact supervisor runner and terminal log. The source and acceptance contract
remain [CM spec](VSPC1_NATIVE_HOLD_VALUE_B01_CM_SPEC_20260908.md) and
[technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B01_TECHNICAL_ACCEPTANCE_20260908.md).

## Exact execution and artifact locations

- Node: `hmasd-wsl-node` (configured wsl_4070), source
  `65c89368ab0fc7402fb0e24254447629e829a12d`.
- Detached cwd:
  `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b01-8101-65c89368ab0f`.
  Read-only remote Git check confirms that exact HEAD and clean status.
- Output:
  `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b01_8101_65c89368ab0f`.
- Adjacent admission: same parent, `native_hold_value_b01_8101_65c89368ab0f_admission.json`.
- Supervisor: `/home/wu/.agent-tasks/vspc1_hold_value_b01_8101_65c89368ab0f/`.
- Local byte-preserving scp collection in the designated direction checkout:
  `temp/directions/vsp_c1/collection/native_hold_value_b01_8101_65c89368ab0f/`:
  `output/`, `supervisor/`, `admission.json`, `check_collection.py`,
  `collection_checks.json`. Both checkpoints and all episode/rollout JSONL rows remain
  in this collection and the original remote output.

The retained runner shows `/usr/bin/time` enclosing the3600s timeout and shell that
performs fresh admission followed by the sole runner invocation:

```text
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b01.py --seed 8101 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b01_8101_65c89368ab0f
```

Configured CPU FP32/one process/one numerical thread is unchanged. Existing source
sets numerical thread limits; no runtime thread census or aggregate CPU measurement
was taken, so those are configuration facts, not independently measured CPU usage.

## Checks over collected bytes

Read-only `agent-task status` confirmed `finished`, exit0, PID2782954, tmux inactive;
the retained log records309s supervisor duration. Its status `uptime_seconds` is
elapsed time since start and is not used as finished-run duration. The initial
read-only `agent-task show` query returned usage (unsupported command); collection
then used supported status/logs and the retained supervisor files, without changing
or relaunching the handle.

Executed once from the direction checkout:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' temp/directions/vsp_c1/collection/native_hold_value_b01_8101_65c89368ab0f/check_collection.py
```

Exit0; the combined remote Git observation and local check took3.093s. The script
loads checkpoint tensors without constructing policies or environments, independently
recomputes primary arithmetic from JSONL rows, and performs no collection or update.

- Identity matches object, card, seed8101, launch SHA, full fixed configuration,
  compound ratio grouping and every declared seed domain. Both fits and final endpoints
  are complete; publication readback reports complete, limits empty, partial steps0.
- 1120 complete256-step episode rows:512 training per learner plus32 final evaluations
  for GATED-V, MLP-V and H. Every phase/arm has exactly the declared episode/reset
  identities; native J equals reward_sum/256, and prefix+suffix equals full return
  within ordinary floating-point rounding. No available subset is substituted.
- 512 rollout rows,256 per learner; each records four epochs and four Adam calls,
  totaling2048. All recorded losses, rewards, summaries and checkpoint tensors are finite.
- Counts reconcile to286720 team/native UAV steps (262144 train+24576 eval),2048 Adam,
  96 final evaluations,1120 explicit resets,2 constructors/resets. Per-row duration/d4/
  velocity decisions reconcile with summary and phase counts and the hold law.
- Both saved algorithms and seed/configuration identities match; both have duration
  heads. Actor count32264; critics34817/34177. All checkpoint tensors are FP32 and
  finite, and final total norms agree with summary. Gate shape128-by5, absolute norm
  and displacement1.9885854721069336, relative displacement null as specified.
- All three 32-endpoint J lists,96 pairwise differences, means and conditional SEs recompute
  from declared episode/reset joins and equal the saved primary fields. The three
  difference lists satisfy their dependence identity. No new independent seed is created.

## Direct endpoint and resource facts

| Recorded quantity | Value |
| --- | ---: |
| GATED-V mean J |0.16488608226755597|
| MLP-V mean J |0.1355204237071898|
| H mean J |0.14548553287361884|
| GATED-V minus MLP-V; conditional SE |+0.029365658560366156;0.005274225674828064|
| GATED-V minus H; conditional SE |+0.01940054939393713;0.010345689108976694|
| MLP-V minus H; conditional SE |-0.009965109166429027;0.010730982423058314|
| Recorded rule region |UP|
| GATED-V / MLP-V total relative displacement |0.39465222122515015 /0.46816692102357516|
| Nonzero hold rows, train GATED-V / MLP-V |1491 /1494|
| Nonzero hold rows, evaluation GATED-V / MLP-V |90 /90|

These are retained observations from one matched training pair. DM determines the
scientific reading and any subsequent direction-local decision; neither critic
movement nor the UP code label expands the claim ceiling.

Fresh admission at2026-09-08T18:50:53.547757Z passed: physical and effective available
memory15644909568 bytes, above4294967296. Cgroup maximum/headroom are null, not zero.
External peak RSS555492 KiB (542.47265625 MiB) covers the timed command chain;
aggregate CPU and device utilization are unmeasured. The source summary's earlier
`resources_unmeasured` label is preserved; this collection attaches the actual
external memory observations without rewriting the original summary.

The timed enclosing admission+Python command chain completed in308.63s; supervisor
log duration309s. In-process summary wall289.1486691409955s and MLP transition offset
151.2950373860076s leave a nonnegative19.481330859004515s external/internal residual.
Its admission/startup/exit split is unobserved. Following the DM-accepted conservative
method, add the entire residual to each internally measured arm interval:

| Complete interval bound | Seconds | Unchanged cap |
| --- | ---: | ---: |
| GATED-V conservative upper bound |170.77636824501212|1800|
| MLP-V conservative upper bound |157.3349626139924|1800|
| Whole scientific process, enclosing command upper bound |308.63|3600|

Thus all complete caps conform even under conservative accounting.308.63s includes
admission and is an enclosing bound, not an exact learner-only wall; the residual
is not asserted to belong entirely to MLP. Startup remains GATED's responsibility,
and H/publication/readback/exit remain MLP's. No internal clock is reset or budget
borrowed. Existing in-process `complete_exit_cap_conformance` stays unchanged in the
raw summary; the external terminal evidence resolves its stated observation gap.

## Delivery and remaining owner

Authoring checkout was clean at `73eb187e8faae41f86a21000eaf387dd719e079c` on
`codex/direction-vsp_c1` when collection began. This delivery changes only this
CM collection record and its evidence JSON; source, card, intake and audit are unchanged.
Scope-spec section4 additions:none. There was zero additional scientific exposure
in collection and no additional test/fixture experiment.

No technical gap remains for intake of these collected observations. Root integrates
the collection commit; `/root/dm_vspc1_p49_value_question` owns the scientific intake
and bounded follow-on decision. No extra call is allocated by this record.
