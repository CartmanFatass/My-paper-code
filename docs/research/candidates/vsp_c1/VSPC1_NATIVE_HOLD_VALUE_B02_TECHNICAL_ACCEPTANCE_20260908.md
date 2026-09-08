# VSPC1 B02 binding: technical acceptance

Source binding accepted under the [B02 CM specification](VSPC1_NATIVE_HOLD_VALUE_B02_CM_SPEC_20260908.md)
and [B02 card sections 2-6](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md).
The independent [production review](VSPC1_NATIVE_HOLD_VALUE_B02_PRODUCTION_REVIEW_20260908.md)
finds no material source issue. This is engineering acceptance only: no B02 model,
native environment, learner execution or scientific output was created.

The designated checkout `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
`codex/direction-vsp_c1`, was clean at
`4ee933d1971b6ffdf0dee6c60203bf98caf4fad3` before this assignment.

## Changed and preserved surface

Only `native_hold_value_b01/study.py` gains explicit `object_id` and `card` keyword
arguments with unchanged B01 defaults. The object is passed to checkpoint save and
readback; the card is passed to the summary. No global mutation or identity registry
is added. The new `scripts/run_vspc1_native_hold_value_b02.py` accepts only seed 8102
and required output, then calls the unchanged configuration with that seed and
B02 object/card. Parser rejection precedes scientific imports and state creation.

The protected-surface comparison against accepted B01
`65c89368ab0fc7402fb0e24254447629e829a12d` is empty for the B01 runner, gated critic,
UCOPE package and native environment/adapter. The B01 runner remains byte-identical
and retains real 8101 / engineering 9001 bindings. Common initialization, per-arm
private streams, reward, recurrence, compound collection/update, PPO, final-only
sampling, H, norms, counts, primary arithmetic and complete caps are unchanged.
8102 does not load any 8101 checkpoint.

Scope-spec section 4 additions: none. The production diff adds 42 lines and removes
6, including the 35-line new runner, within the 2000/600 limits. No synthetic runner
fixture, profile, fourth CM comparison or extra scientific invocation follows.

## Exact focused evidence

Executed once with the configured local scientific interpreter:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b02_binding tests/experiments/candidates/vsp_c1/native_hold_value_b02/test_binding.py tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_study.py::test_cli_fixed_configuration_without_running_fixture
```

Exit 0; 6 passed in 2.07s, observed command wall 3.0432563s, within 300s. The sole
warning is the existing unknown `cache_dir` option when the requested command disables
cacheprovider. Result retained at
`temp/directions/vsp_c1/engineering/native_hold_value_b02/focused_result.json`.

Checks cover fixed 8102 propagation; rejection of 8101, 9001 and fixture mode before
scientific state; unchanged B01 no-run CLI; summary and both checkpoint identities;
all 810200000-based seed domains; independent matched generator objects; fixed
final-only schedule, complete primary and unchanged reading. Real actor, critic,
gate and environment constructors are forbidden/stubbed. Templates, optimizer,
collector, update, snapshot and movement are stubs. The 286720/2048 schedule counters
in this check are stub-produced metadata, not executed scientific exposure.

Invocation-owned scratch was resolved to this checkout's exact
`temp/directions/vsp_c1/test/native_hold_value_b02_binding` directory. Automatic review
rejected recursive deletion; narrower explicit leaf-file and empty-directory removal
succeeded after result retention. `Test-Path` returned False. New B02 test/runner
bytecode files were also removed. No other invocation or scientific artifact was removed.
The rejected combined test/cleanup tool call occurred before process acceptance;
the test command above is the only executed focused invocation.

## Cost, publication and remaining delivery

Per-arm planning reuses the card's B01 evidence and unchanged cost law; no new
calibration was performed. B01 enclosing wall 308.63s and conservative arm bounds
170.7764s/157.3350s are references, not a B02 timing guarantee. Caps stay 1800s per
learned arm and 3600s for the complete pair. Post-learner B02 summary/checkpoint
binding and readback are exercised by the full-schedule stubs; unchanged computation
and native publication reuse accepted B01 checks and completed collection.

Exact-source command binding is completed after this source commit/push. The final
section will contain the literal LF wrapper, detached SHA/cwd, output, admission,
handle and syntax-only staging result. Root alone integrates/submits/observes the
one separately authorized pair after fresh remote admission. The same CM collects
and DM intakes all outcomes; this engineering task does not launch it.
