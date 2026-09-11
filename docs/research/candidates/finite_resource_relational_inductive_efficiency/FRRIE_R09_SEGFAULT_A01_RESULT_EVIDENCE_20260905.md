# FRRIE R09 fatal-signal A01 result evidence — 2026-09-05

The single prescribed diagnostic exists and is terminal-collected. Candidate first-match branch **A01_DIFFERENT_ORIGINAL_FAILURE**: the original execution raised an AttributeError, with no retained recurring SIGSEGV. This is A/RECON evidence, not a repaired runtime or a valid R09 B result.

## Rule and original observation

Card rule applied verbatim: “No earlier match and a different original exception/signal occurs before natural completion or the cap. Preserve it separately, without calling it the original failure.”

The source, entry, seed, fixed pdb input, pinned node/interpreter, faulthandler flag, unique state and passing adjacent admission were represented; no undeclared source change or duplicate invocation occurred. No fatal signal is reported before the original Python exception. The traceback ends in CPython dataclasses.py:1245, _asdict_inner, at `getattr(obj, f.name)`:
`AttributeError: 'tuple_iterator' object has no attribute 'name'`.

Retained chain: run_frrie_b01_contact_r09.py:9 → experiment.py:560 main → execute:166 evaluation_tapes → dictcomp:167/genexpr:168 → tapes.py:216 evaluation_tape uplink → uniform_float32:113 → block:109 → canonical_bytes:96 → dataclasses.asdict:1238 → _asdict_inner:1245. These are original-byte line numbers. This directly localizes this different failure to evaluation-address serialization; it does not establish the cause of original R09 SIGSEGV or merge historical R04/attempt02 causes.

Existing pdb input retained FIELD_TYPES = ('R02EvaluationAddress', 'tuple_iterator', None). FIELD_INVENTORY lists 12 entries, each type Field, with matching names: seed_label, roster, episode, kind, basin, event_ordinal, slot, public_role, role_local_index, sender, receiver, draw. The inconsistency between local f and that class inventory is observed; responsibility for it is unresolved.

Later pdb commands produce a separate AttributeError for nonexistent seed_block and a separate NameError for number. These are postmortem observation-command errors, not the original failure. Fixed q then EOF reaches module line 1 on debugger re-entry and exits, with no second scientific computation evidenced. No cont/step was supplied after the original exception. No fatal faulthandler stack was emitted; the retained stack is the ordinary exception traceback/pdb stack.

## Execution and resources

Launch source **43eec21e9584c83e5e8d940402d7e4570b454e59**, unchanged and previously pushed. Card and resume were pushed before launch; prospective CM command record cbdd0552d was also pushed before launch. Actual detached cwd:
`/home/wu/hmasd-worktrees/frrie-r09-segfault-a01-43eec21e-20260905`.
Configured node wsl_4070 / observed LAPTOP-U9TDKC8A. Existing /home/wu/.venvs/hmasd/bin/python reports CPython3.10.21 and resolves to /home/wu/.local/share/uv/python/cpython-3.10.21-linux-x86_64-gnu/bin/python3.10. Traceback renders its stdlib path with the cpython-3.10-linux-x86_64-gnu alias. No interpreter/configuration change was made.

Task `frrie_r09_segfault_a01_43eec21e_20260905`, supervisor PID1683892, start epoch1788625283 = 2026-09-05T16:21:23Z; end16:21:42Z. Raw supervisor timestamps render 2026-09-06T00:21:23+08:00 and00:21:42+08:00, the same instants. Observed duration **19 seconds**, terminal finished/exit0/tmux inactive. This exit is debugger/supervisor completion after an uncaught original exception, not original natural completion. No TERM cap reached.

Actual-node admission assessed16:21:23.090023Z reports physical/effective available **15,422,091,264 bytes**, each >=4GiB, passed. Preflight is directly joined by && to exact timeout/Python invocation. Command raw record preserves the supervisor's actual runner. Assigned CPU FP32/Torch1/native32 semantics remain in original source; no learner artifact independently confirms runtime learner settings.

Not a sweep. Original planning observation16s; actual diagnostic19s, below60+5s. Runtime peak RSS, per-arm work/timing and scratch peak are **resources_unmeasured**. Admission is not runtime peak conformance. The nominal unchanged target128 updates/LR.003/exposure.384/initial half-range.05/ratio7.68 is not achieved exposure.

## Artifact boundary and limitations

Terminal read-only inventory has only the504-byte receipt under the direction temp tree. The requested exp output directory and summary do not exist. Remote HEAD remains exact source and Git status clean. No scientific counters, learner rows, contact inventory, cells, checkpoint states or native return are retained: report them as unmeasured, never zero.

Source places output mkdir after evaluation-tape construction and before adapter, model and learner setup. The observed exception is in that preceding tape construction. It does not reveal exact completed draws, episode or address, because fixed address/counter inspection failed. No scientific branch or R09 native-return prediction is scored. DM owns final rule intake; recurrence-with-frame prediction has a contrary diagnostic observation.

No code or test was edited; no extra smoke or focused suite was run. Prior accepted focused check remains historical evidence, not proof of this invocation. Formal publication-size coverage remains an open engineering item. No fallback, repair, second diagnostic or B retry was attempted. Scope: none.

Strongest remaining uncertainty: why the interpreter's local f is tuple_iterator while the class field inventory is intact, and whether that anomaly shares any cause with original SIGSEGV. This one original-chain diagnostic does not settle those questions. Return evidence to DM; any next discriminator requires its own selected bounded contract.

## Raw evidence

All files below are adjacent and preserve this sole invocation:
- FRRIE_R09_SEGFAULT_A01_COMMAND_20260905.txt — actual supervisor runner and exact command.
- FRRIE_R09_SEGFAULT_A01_ADMISSION_20260905.json — actual-node receipt.
- FRRIE_R09_SEGFAULT_A01_TERMINAL_LOG_20260905.txt — full unedited stdout/stderr.
- FRRIE_R09_SEGFAULT_A01_INVENTORY_20260905.txt — terminal source/runtime/status/start/exit/artifact inventory and supervisor list.
- FRRIE_R09_SEGFAULT_A01_CM_RECORD_20260905.md — prospective contract and collection completion.

Raw remote log remains /home/wu/.agent-tasks/frrie_r09_segfault_a01_43eec21e_20260905/task.log; output/receipt paths are fixed in the command record. Tracker adopted the exact handle and notified terminal; no observation owner change caused relaunch.
