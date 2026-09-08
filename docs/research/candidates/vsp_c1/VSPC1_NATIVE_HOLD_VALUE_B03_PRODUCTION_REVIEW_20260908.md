# VSPC1 B03 — independent normalization review

No material finding was found in the production source or the exact launch command
after direct inspection and the focused check evidence. This is independent
technical evidence, not approval, permission, or a scientific disposition.

Contract: [B03 CM specification](VSPC1_NATIVE_HOLD_VALUE_B03_CM_SPEC_20260908.md)
and [B03 card sections 3–6](VSPC1_NATIVE_HOLD_VALUE_B03_SCIENCE_CARD_20260908.md).
Checkout: `codex/direction-vsp_c1`, clean starting revision
`b16d269d700401615f9adcdc191ac1114a9191c2`; complete input
`e5cc7ce67cf9dfa4ebd95324bf5c67423bc9977a` includes the accepted optional
`entropy_coef=.01` interface. The reviewer edited only this document and ran no
models, tests, native invocation, standalone fixture, or scientific replay.

## Numerical and credit path

The new `ValueMoments` owns only two integer counts and scalar CPU FP32 mean/M2
tensors. Empty scale is one; populated scale is the square root of population
variance floored at `1e-8`. The merge uses the old mean delta, batch central M2,
and the declared count weighting. Targets flatten in episode/time layout, so the
512 native target rows enter once per rollout, without agent or epoch replication.
The moment update is under `no_grad`, and normalized targets detach. There are
no learned moment parameters, optimizer entries, random draws, extra critic
forwards, or model/output/optimizer rescaling.

In the changed source collector, decoding occurs immediately after the critic
forward and before the existing finite-value check. Collection stores the native
decoded value and does not update moments. In `update`, native returns-to-go and
the saved values form the original once-normalized detached advantages before
the sole moment merge. Only the target tensor then changes units. The four epochs
reuse those same advantages and normalized targets; the critic raw output is fit
with normalized MSE. The existing actor density, masks, native reward path,
entropy coefficient, joint gradient clipping and Adam calls remain intact.

This implements the selected changing-value-coordinate method. It intentionally
does not preserve decoded outputs when moments update; the card excludes a PopArt
output-preservation claim. Statistical moments are scientific critic state, not
parameter displacement or independent training observations.

## Ownership, state publication and defaults

The study creates a new moment instance inside each learned-arm iteration, outside
the actor/critic optimizer. Both training episode calls share that arm's old state;
the update mutates it once. Both arms opt into the same `.01` entropy coefficient
and normalization path. Learned evaluation passes the existing state only for
decode; H receives neither critic nor moments. Before/after learned evaluation and
after H snapshots expose its frozen counts/state.

Each completed rollout records post-update moments and normalized loss units.
Final checkpoints contain their own moment snapshot alongside actor/critic state,
and configuration labels the normalization and entropy coefficient. Readback checks
the checkpoint and summary moments against the retained arm snapshot. Exceptions
copy the current moment state into the incomplete arm record, including a moment
merge completed before an interrupted epoch. This avoids relabeling partial moment
counts as a complete fit. As in the accepted source, interrupted updates preserve
actual Adam counts but return loss records only after a complete update.

Default `value_moments=None` and `normalize_value=False` leave the prior numerical
expressions, identity/configuration and call arguments unchanged. The `entropy_coef`
parameter remains available to other UCOPE callers; B03 explicitly selects `.01`.
Direct comparison with complete input `e5cc7ce67` shows no diff in the B01/B02
runners, gated critic, UCOPE policy/environment, or native environment/adapter.
No prior model/checkpoint/moment state is loaded for the new8201 fit.

## Focused evidence and source budget

The reviewer inspected both new test files and the retained
`temp/directions/vsp_c1/engineering/native_hold_value_b03/focused_result.json`.
The original exact focused command initially stopped during collection because
B02/B03 shared the module name `test_binding.py`: recorded exit 1, 2.02 s pytest / 3.01197 s
observed process wall. Adding a test-package `__init__.py` resolved that collision;
the same command then passed 17 cases, exit 0, 2.54 s pytest / 3.5546191 s observed
wall. Total observed process wall was 6.5665891 s, within 300 s. CM retained this
result and removed its verified invocation-owned scratch. The package marker adds
no production behavior. No standalone fixture or native invocation followed.

Tiny deterministic module/parameter tests exercise the actual collector/update
functions with stubbed observations/actions and a no-op optimizer step. Independent
expected quantities check the two-batch `n=4,mean=4,M2=20` merge and floor, native
decoded value14 from old mean10/scale2/raw2, and cumulative `n=6,mean=6,M2=70`
for the update example. They compare native advantages across all four epochs,
normalized versus default-native MSE, and the expected pre-clipping critic gradient.
They also check detachment, FP32 scalar state and absence of moment parameters.
These are engineering gradients on tiny generic modules, not a scientific fit.

Full-schedule stubs check all8201 identities/private RNG domains, the `.01` entropy
binding, final-only endpoints, distinct arm moments, exactly256 merges/131072 rows
per arm, and frozen learned-evaluation/H state. Both checkpoint moment snapshots
round-trip and each rollout records its actual post-merge counts. The requested
partial branch raises after the first merge and before Adam; its published summary
retains `n=512,updates=1` with zero Adam/complete rollouts and INCOMPLETE status.
The former B02 binding and B01 no-run CLI checks also pass. Stub schedule counts
are metadata evidence and do not represent executed native exposure.

Tool-computed initial production delta is 127 added and 13 removed lines: learner
9/2, study41/11, new initializer1, moment module41 and runner35. This is within
the 2,000-source/600-runner limits. Runtime-spec general requirements and scope-spec
sections 4–5 identify no prohibited addition: direct scalar moments and their
existing-checkpoint serialization implement card section 3's scientific state.
There is no new worker, registry, resume/retry path or telemetry framework.
The existing single-process CPU FP32 topology and numerical thread limits remain.

Complete configured work is 512 moment merges of 512 scalar targets across both
arms, or 262,144 native target rows and 1,048,576 four-epoch value-loss row terms.
The selected 286,720 team steps, 2,048 Adam calls and 96 final evaluations remain
unchanged. These are computed work counts, not executed exposure or cost measurements.
Incremental native runtime and scientific behavior remain unmeasured.

## Exact launch command

Accepted source: `7a8ed3aa5d25ded71164aa338749d09318124dcf`, committed/pushed by CM.
The reviewer inspected the literal script, `launch_binding.json`, and the remote
readback file beneath `temp/directions/vsp_c1/engineering/native_hold_value_b03/`.
A read-only byte comparison independently found 655 bytes, eight LF-terminated
lines, no CR, and identical local/remote-readback content. CM's staged `/bin/bash -n`
exited 0 in 0.4038779 s; its readback command exited 0 in 0.5733178 s. No scientific
payload was executed. The full literal command and submission are recorded in
[technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B03_TECHNICAL_ACCEPTANCE_20260908.md#exact-root-command-staged-not-submitted).

- Local script: `launch_8201_7a8ed3aa5d25.sh` under that engineering directory.
- Node: `hmasd-wsl-node`; staged script:
  `/home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh`.
- Bound detached cwd:
  `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25`.
- Output:
  `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25`;
  admission is its sibling `native_hold_value_b03_8201_7a8ed3aa5d25_admission.json`.
- Requested supervisor handle (not submitted): `vspc1_hold_value_b03_8201_7a8ed3aa5d25`.

The shell changes to the exact bound cwd and joins fresh admission to the fixed8201
runner using `&&`; the configured interpreter and output match the binding. H,
normalization and object/card identities come from the reviewed B03 entry point.
There is no alternate seed, retry, fixture, resume or external hard-KILL wrapper.
The enclosing `/usr/bin/time` interval includes admission and process exit, so it
is an upper bound on scientific wall, not exact learner-only time. The source's
continuous 1,800 s/arm and 3,600 s/pair checks and partial-publication path remain;
indivisible overruns must still be reported as breaches, without extra budget.

Only command staging and syntax are established here. Root retains exact-source
checkout staging and the pre-submit cwd/source comparison required by
ROOT_OPERATIONS.md, followed by the separately authorized single submission and
terminal observation. Future cap assessment must combine the enclosing interval
with the internal arm split and report any unpartitioned startup/exit residual
conservatively. Native performance, normalization overhead, actual moment/Adam
counts, complete exit-cap conformance and admission remain unmeasured by this
engineering review. No reviewer execution or additional scientific gate follows.
