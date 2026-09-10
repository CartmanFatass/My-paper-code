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

## Exact Root launch artifact (not submitted)

Accepted scientific source: `0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`, committed and
pushed before this binding. Later documentation-only commits do not change its
source. Node is `hmasd-wsl-node` / configured wsl_4070. Fixed detached cwd:
`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b02-8102-0ec208899f5e`.

The following exact eight-line script is retained locally at
`temp/directions/vsp_c1/engineering/native_hold_value_b02/launch_8102_0ec208899f5e.sh`
and already staged at
`/home/wu/hmasd-inputs/vspc1_hold_value_b02_8102_0ec208899f5e.sh`.
It is 655 bytes, UTF-8 without BOM, literal LF with no CR. Its remote readback exactly
matches the original bytes; ordinary syntax checking executed no payload:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /bin/bash -n /home/wu/hmasd-inputs/vspc1_hold_value_b02_8102_0ec208899f5e.sh
```

Final syntax check exited 0 in 0.487s; corrected remote readback exited 0 in 0.733s. The output
and admission paths do not yet exist as evidence; no admission or scientific state
was created by these checks. The local `launch_binding.json` records these literal
paths and the exact submission below. The staged script text is:

```bash
#!/usr/bin/env bash
# Accepted source: 0ec208899f5e8b4c190ab7bd9806be2cc30b6fda
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b02-8102-0ec208899f5e &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b02_8102_0ec208899f5e_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b02.py --seed 8102 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b02_8102_0ec208899f5e
'
```

Root's single authorized supervisor submission, after source integration/staging:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b02_8102_0ec208899f5e /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b02_8102_0ec208899f5e.sh
```

Handle: `vspc1_hold_value_b02_8102_0ec208899f5e`. Output:
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b02_8102_0ec208899f5e`.
Fresh admission is its sibling `native_hold_value_b02_8102_0ec208899f5e_admission.json`.

**Source staging remains Root's existing integration step.** A read-only `git cat-file`
check found the remote source repo did not yet contain the new accepted commit;
this record does not claim the named detached cwd is staged. Root must bring the
exact committed source through its existing staging route, create the named detached
checkout, and compare actual cwd and bound source before submitting this already
syntax-checked script, as ROOT_OPERATIONS.md requires. No payload/path reconstruction
or changed source is needed. A discrepancy returns to this CM for a mechanical
correction. The shared direction checkout remains owned by the DM/CM authoring route.

`/usr/bin/time` records the enclosing admission plus scientific process wall and peak
RSS through exit. The study retains its continuous 1800s arm / 3600s pair checks,
internal total and MLP transition; an indivisible overrun remains reportable as a breach.
At collection, startup belongs to GATED, H/publication/readback/exit to MLP; if the
external/internal residual split is unknown, use the entire nonnegative residual
in each conservative arm upper bound. The enclosing command is a bound on scientific
wall, not exact learner-only wall. Missing optional resources do not become a new gate.

The independent reviewer identified that copying B01's external hard-KILL timeout
would introduce an earlier deadline clock, including admission, and could prevent
partial-count/failure publication. That wrapper detail was not frozen by the B02
card. It was removed before submission; the corrected literal artifact above was
restaged and rechecked. The unchanged learner remains responsible for cooperative
cap/nonfinite stops and partial evidence, with the external whole-process observation
used for final cap disposition. No new timeout budget, retry or softened cap follows.
The independent reviewer inspected the corrected artifact and transport evidence.
Root alone integrates/submits/observes the one separately authorized pair after
fresh remote admission; the same CM collects and DM intakes all outcomes. There was
no B02 model, fixture, native invocation or supervisor submission in this assignment.
