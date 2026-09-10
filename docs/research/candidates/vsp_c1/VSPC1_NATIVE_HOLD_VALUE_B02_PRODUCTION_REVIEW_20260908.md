# VSPC1 B02 — independent binding review

No material finding remains in the inspected production binding and corrected launch
command. One material command finding was resolved below. This is independent technical
evidence, not approval, launch permission, or a scientific disposition.

Contract: [B02 CM specification](VSPC1_NATIVE_HOLD_VALUE_B02_CM_SPEC_20260908.md)
and [B02 card sections 2–6](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md).
Starting checkout: `codex/direction-vsp_c1` at
`4ee933d1971b6ffdf0dee6c60203bf98caf4fad3`.
The reviewer owns only this document and performed no model construction, test,
synthetic fixture, native invocation, or scientific replay.

## Changed behavior and protected source

The production diff adds keyword-only `object_id` and `card` inputs to the existing
study with B01 defaults. The object identifier reaches the summary and both checkpoint
save/readback paths; the card reaches the summary. B02's runner supplies the B02
identifiers and `Config(seed=8102)`. It rejects other seeds and the unsupported fixture
flag before importing Torch inside `main` or entering scientific state. It retains
the existing pre-import numerical thread limits, CPU execution, startup clock and
terminal status behavior.

The reviewer directly compared the B01 runner/critic, UCOPE package and native
environment/adapter against accepted B01 `65c89368ab0fc7402fb0e24254447629e829a12d`:
the diff is empty. Shared study defaults remain B01 object/card and original seed
behavior. There is no global identity mutation, checkpoint loading for training,
new RNG consumption, or change to collection, learning, primary arithmetic,
publication failure handling, H reuse, or deadlines. The earlier
[B01 independent review](VSPC1_NATIVE_HOLD_VALUE_B01_PRODUCTION_REVIEW_20260908.md)
covers that unchanged computation.

Direct arithmetic confirms initialization810200011, private training stream
seeds810200021/810200022, constructors810201000, training resets810201000–810201511,
evaluation resets810202000–810202031, and evaluation velocity/duration
seeds810203000–810203031/810204000–810204031. These match the new card. Existing
per-arm and per-episode generator construction preserves private mutable streams.

## Focused evidence

The reviewer inspected `test_binding.py`. It stubs templates, models, optimizer,
generators, collection and updates, and forbids real actor/critic and native/synthetic
environment constructors. The fixed complete schedule checks 1,120 metadata calls,
512 stub updates, 132 distinct private generator objects, final-only evaluation,
H environment reuse, every reset/stream domain, both saved checkpoint identities,
summary readback, B01 defaults and invalid CLI rejection. Its 286,720 step and 2,048
Adam counters are stub schedule evidence, not scientific execution or exposure.
The existing B01 no-run CLI test is the only unchanged check selected alongside it.

CM's exact focused command from the handoff passed six cases in 2.07 s, exit 0,
with 3.043 s tool-observed wall. The only warning is the existing `cache_dir`
configuration with cacheprovider disabled. The reviewer read the retained
`temp/directions/vsp_c1/engineering/native_hold_value_b02/focused_result.json`;
CM reports its exact invocation-owned scratch was removed. No second fixture,
scientific exposure, or reviewer rerun followed.

## Scope and exact command inspection

Source diff: seven added and six removed study lines, plus a 35-line B02 runner.
This is 42 added non-test lines, below the 2,000-source/600-runner budgets.
Runtime-spec general requirements and scope-spec sections 4–5 reveal no prohibited
addition. Simple parameter passing implements the requested identity boundary; it
adds no registry, compatibility shim, worker, resume/retry or new telemetry framework.
Unchanged single-process CPU FP32 learning and existing tensor batching require no
fresh runtime census for this identity-only change.

The accepted source is `0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`.
The reviewer inspected the exact shell text and `launch_binding.json`, and compared
local and remote-readback bytes using a read-only Python command. The corrected
artifact is eight lines/655 bytes, LF-only, ending in LF; the readback is identical.
CM's final `/bin/bash -n` on the staged remote file exited 0 in 0.487 s; its remote
readback command exited 0 in 0.733 s. These checks executed no scientific payload.
The [technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B02_TECHNICAL_ACCEPTANCE_20260908.md#exact-root-launch-artifact-not-submitted)
contains the literal command and supervisor submission line.

Bound command facts:

- Node: `hmasd-wsl-node`; source SHA as above; detached cwd
  `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b02-8102-0ec208899f5e`.
- Staged script: `/home/wu/hmasd-inputs/vspc1_hold_value_b02_8102_0ec208899f5e.sh`;
  local artifact:
  `temp/directions/vsp_c1/engineering/native_hold_value_b02/launch_8102_0ec208899f5e.sh`.
- Existing `agent-task` handle: `vspc1_hold_value_b02_8102_0ec208899f5e`.
- Output:
  `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b02_8102_0ec208899f5e`;
  admission is the sibling `native_hold_value_b02_8102_0ec208899f5e_admission.json`.

The single shell performs `cd`, then fresh actual-node admission, then the fixed8102
runner joined by `&&`. Admission failure prevents scientific state creation.
The configured interpreter and required output agree with the binding. No resume,
retry, alternate seed or fixture argument is present. The enclosing `/usr/bin/time`
reports admission-plus-process wall and peak RSS through exit; this is a conservative
enclosing interval, not exact learner-only time. The existing internal split and
full residual method retain the card's unchanged 1,800 s/arm and 3,600 s/pair limits.

**Resolved material finding — premature hard termination.** The first unsubmitted
script wrapped admission and the learner in `timeout --signal=KILL 3600s`. That clock
starts before the learner's internal clock. At a near-cap run or an indivisible
overrun, SIGKILL can bypass the learner's exception/finalization path and prevent
in-memory partial-step/Adam counts and summary publication. This conflicts with
card section 5's partial-evidence stop behavior. The reviewer requested removal
of that external hard-kill wrapper while retaining existing timing and supervision.
CM removed it, restaged the script, and repeated syntax/readback checks only; DM
confirmed the correction preserves the original caps and records any overrun as
a breach. The corrected bytes inspected here contain no timeout/KILL command.

**Residual execution responsibility.** Only the shell script is staged. The remote
source repository did not yet contain the new commit at CM's read-only check, and
neither this review nor acceptance claims that the detached cwd exists. Root must
integrate/fetch the accepted source, stage the named exact-SHA checkout, and compare
actual cwd/source with this supplied command before its one authorized submission,
under ROOT_OPERATIONS.md. Fresh admission, supervisor acceptance, native counts,
runtime/cap conformance and scientific performance remain unobserved. They are not
established by syntax checks or stub counters.
