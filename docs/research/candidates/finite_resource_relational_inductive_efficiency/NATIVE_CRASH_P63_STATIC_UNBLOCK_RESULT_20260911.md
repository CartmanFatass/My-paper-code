# P59/P63 source-only technical unblocking — 2026-09-11

## Initial L0: current technical assignment

This prospective record is retained. The rejected wrapper, narrower accepted
command and one coverage correction are documented under the result below.

1. **Deliverable:** reconcile the P63 readiness/access record, recover the actual
   recorded observation method and establish a bounded source-only observation
   for the P59 factory path. Apply a minimal production correction only if direct
   evidence attributes a defect; otherwise return the exact missing fact and
   executable exit condition. This is Root's owner-directed September 11 technical
   continuation, not a new scientific object or a P63 launch.
2. **Ownership:** DM works directly in the existing
   `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`, clean
   start 855003909b458d653f5cd95118969d034a251089. Own this technical record,
   `native_crash_repair/inspect_factory_source.py` under the FRRIE experiment
   directory, the later intake/brief and this check's temp directory. The six
   source inputs are the P59 diagnostic, `rng.py`, `tapes.py`, R02 `tapes.py`,
   R02 `experiment.py` and `contracts/core.py`; all have an empty diff against
   5831dafaab0e47d0c13fe1cbefcc94e5a817b1bc. Preserve unrelated main work.
3. **Preserved semantics:** parse source as data without importing or executing
   it. Construct no scientific model, environment, optimizer, RNG, tape, learner
   or native ABI call. Preserve every historical record and original budget;
   local Python 3.11.9 is only the source parser and is not a substitute for
   P59's system312 execution environment. No production source change is currently
   supported. Engineering Scope §4 needs/adds none.
4. **Acceptance:** map all eight retained traceback locations to the current
   unchanged source; distinguish a function definition from an evaluated
   expression; report actual loaded workload modules and timing. Read the output
   against P59 collection and P63 readiness, under evidence-spec §§3–4, 5.1 and
   11.8.5–7, and Engineering Scope §§7.1–7.3. A source map cannot identify a native
   faulting instruction or corrupting writer. Any actual high-risk production
   correction would need the independent review specified in §7.3.
5. **Budget/stop:** one local stdlib-only AST observation, externally bounded to
   10 s, within the 300 s directory test budget. Keep stdout/stderr and process
   wall/peak-memory observations in this task's evidence; remove only its owned
   test scratch after retention. Stop with a source-supported correction or a
   precise attribution gap. Zero scientific invocation, P63 allowance use, R09
   retry, Pro Send or scientific selection.

## Result and technical acceptance

**Source-only observation is established; no production fault is attributable.**
The observer reads Python text with `ast.parse` and reports source locations. It
does not import or execute the inspected modules. Direct execution succeeded;
the original combined process/deadline/cleanup wrapper was rejected before any
operation. The narrowed method and its actual measurements are recorded below.

### Recovered methods and actual acceptance

- P59's exact diagnostic argv, confirmed by a fresh read of its retained
  `/home/wu/.agent-tasks/frrie-p59-input-factory-20260908/runner.sh`, was:

  ```sh
  /home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python -X faulthandler tests/experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/test_training_input_factory.py
  ```

  Its complete admission/env/timeout command remains in the accepted
  [literal handoff](NATIVE_CRASH_P59_INPUT_FACTORY_ROOT_HANDOFF_20260908.md#exact-single-launch-remote-shell).
  The retained runner confirms the same interpreter, exact-cwd PYTHONPATH,
  owned pycache prefix, four thread-limit variables and TERM 115 s + 5 s grace.
  Nothing from that runner was executed during this continuation.
- P63's earlier CM turn reached no operation or literal diagnostic binding.
  Its intended route was retained native context first, then a conditional
  same-fixture native-context diagnostic. There is no rejected shell command
  to recover or silently substitute. The September 10 readiness record correctly
  preserved that uncertainty; it did not prove all technical methods impossible.
- The current combined PowerShell wrapper would have started the parser with
  `Start-Process`, used a 10 s wait/termination bound, redirected output and
  cleaned its own scratch in `finally`. Automatic policy review rejected the
  CreateProcess request before execution with **`rejected: blocked by policy`**.
  It gave no operation-specific reason. Neither proposed directory existed
  afterward; no subprocess, scratch creation or removal from this wrapper ran.
- The narrower command below was accepted directly. It has no process-management,
  filesystem-write or cleanup step and never executes scientific source:

  ```powershell
  python -I -B experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/inspect_factory_source.py
  ```

  The first pass mapped the eight locations quoted by the P59 intake. Fresh
  retained-log readback supplied the ninth, module-level `main()` frame at line
  39. The helper was corrected to include module frames and checked once more.
  This focused coverage correction is the only repeated parser check; neither
  pass generated a fixture or consumed an old invocation allowance.

The Python 3.12 documentation describes this `faulthandler` mode as a Python
traceback containing filenames, function names and line numbers. That explains
the kind of observation P59 retained; it does not supply native registers,
instruction bytes or fault attribution. [Python 3.12 faulthandler documentation](https://docs.python.org/3.12/library/faulthandler.html)

### Source map and direct observations

All six inspected source surfaces are unchanged from P59 source
5831dafaab0e47d0c13fe1cbefcc94e5a817b1bc. The final pass parsed 2,480 lines and
mapped these nine recorded frames:

| Recorded location | Source fact |
| --- | --- |
| `rng.py:133` | `SemanticRNGAddress.validate` declaration; first body line 134; no call expression covers line 133 |
| `rng.py:204` | `canonical_bytes` calls `self.validate()` |
| `rng.py:251` | `block` forms payload using `address.canonical_bytes()` and `block_index.to_bytes()` |
| `rng.py:273` | `uniform_float32` calls `self.block()` inside `int.from_bytes()` |
| `tapes.py:373` | `generate_episode_tape` calls `rng.uniform_float32()` for an uplink entry |
| R02 `tapes.py:247` | the grouped generator calls `generate_episode_tape()` |
| R02 `tapes.py:246` | the grouped factory materializes its tuple |
| diagnostic `:22` | `main` calls `experiment.production_training_inputs()` |
| diagnostic `:39` | module-level `main()` call, not a containing function |

The definition-line mapping does **not** prove that the native fault occurred at
function entry, before the body, or in any particular predicate. The factory's
RNG construction, grouped generation and serialization remain source facts,
not code executed by this observer. No change to those operations is justified.

Fresh read-only access to the existing P59 `task.log` and `process-time.txt`
confirmed the same five completed groups, SIGSEGV/139, 18.59 s and 618,760 KiB.
The log also says the monitored command dumped core; this alone does not prove
that a dump file was retained. These are re-observations of one existing run.

The current node reports core pattern `|/wsl-capture-crash %t %E %p %s`; this is a
current configuration observation, not a reconstruction of September 8 state.
The recorded P59 exit at 2026-09-08T21:23:12Z converts to epoch 1788902592.
This fixed lookup returned exit 0 and no matching filename:

```powershell
ssh hmasd-wsl-node "find /mnt/c/Users/wu/AppData/Local/Temp /mnt/c/Users/wu/AppData/Local/Temp/hmasd-native-crash-20260908-preserved -maxdepth 1 -type f -name 'wsl-crash-178890259*' -printf '%p %s bytes\n'"
```

Its scope is only those two known retention directories and that ten-second
filename prefix. It is not a global dump census or proof that a P59 core never
existed. No unrelated core was examined, no debugger attached or started an
inferior, and no new crash or scientific workload was induced.

### Costs, exposure and deviations

| Quantity | Actual observation |
| --- | --- |
| Accepted source-only parser calls | 2; both exit 0, six files each; initial 8 frames, final 9 |
| Parser wall | 0.0334108000 s + 0.0310218000 s = 0.0644326000 s |
| Exec-tool wall for those calls | 0.2491172 s + 0.2862187 s = 0.5353359 s |
| Read-only artifact/configuration SSH commands | 4; summed tool wall 4.9838216 s; two independent reads overlapped |
| Rejected wrapper accepted operations | 0 |
| Peak RSS / aggregate CPU for current checks | `resources_unmeasured` |
| New scientific RNG/model/environment/optimizer/tape/learner/native-ABI activity | 0 |
| P63 diagnostic/verification allowance used; R09 retry | 0; 0 |

These are selected technical command timings, not total DM task elapsed time,
learner throughput or a new experiment cost law. The original external 10 s
wrapper did not run; the successful direct calls finished below that nominal
limit, but no external deadline or peak-RSS enforcement is claimed for them.
The extra source check followed the newly observed module frame. Both calls
together remain far inside the 300 s directory test budget. No §5 time budget
was exceeded, and no §4 machinery was added.
The source-only helper adds 76 non-test lines and changes no existing source
file. It is below the 600-line runner and 2,000-line attempt limits; its fixed
AST readback is the selected technical observation, not an added launch guard.

Final stdout and tool result are retained directly in
`temp/directions/finite_resource_relational_inductive_efficiency/exp/p63_static_unblock_20260911/`
as `source-summary.json`, `final-tool-result.json` and `accounting.json`.
These were retained after direct execution; they are not outputs of the rejected
redirect wrapper. The parser itself created no files. Its proposed test scratch
was confirmed absent, so this continuation has no pending test cleanup. Existing
P59 raw roots and deferred historical cleanup remain untouched.

The production fault remains unresolved. The companion
[technical intake](NATIVE_CRASH_P63_STATIC_UNBLOCK_INTAKE_20260911.md) records the
readiness update, exact attribution gap and executable exit conditions.

scope: none
