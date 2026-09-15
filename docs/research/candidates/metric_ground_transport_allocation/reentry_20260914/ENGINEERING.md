# Reentry protocol implementation and bounded verification

At 2026-09-14T06:30:15Z, the DM completed the first concrete implementation batch
on codex/mgtap, based on1c5887704d42bd97db0835501338b657850ac352.
No legacy learner, native environment, policy, runtime registry or other direction
was modified.

## Implemented

- Separate selection/holdout masters and private-stream address contract.
- Equal three-candidate opportunity and per-arm OWN validation-score maximization.
- Deterministic exact ties preserving the inherited LR first.
- Complete32-world panel validation, finite J, rate/endpoint/address/stage binding.
- Holdout rates must match the saved validation argmax and selection provenance;
  no holdout row is accepted as selector input.
- Ordered holdout primary, inclusive MEI band and conditional-panel SE.
- Work-count generator reading the same constants; no learning or simulation.

## Checks actually executed

Python3.11.9, local C:/Users/fires/AppData/Local/Programs/Python/Python311/python.exe.

```text
python -m unittest discover -s tests/experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01 -p test_protocol.py -v
```

13 tests passed, unittest-reported duration0.010s, process exit0.
[Full terminal test output](TEST_OUTPUT.txt) is retained.
Synthetic score fixtures are NOT experiments, added native evidence or measured returns.
The protocol imports no Torch, native host or model and fits no parameters.

```text
python -m experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01.protocol --out docs/research/candidates/metric_ground_transport_allocation/reentry_20260914/PLANNED_EXPOSURE.json
```

This emitted [planned exposure](PLANNED_EXPOSURE.json):8 planned fits,
589824 team ticks,4096 Adam calls,13434880 actor row uses.
No simulation was used to count a known loop.

The original305-line user copy and archived copy compare equal after CRLF-to-LF
normalization. Byte/hash provenance is in[SOURCE_RECEIPT.json](SOURCE_RECEIPT.json).
The full two answer bodies, not a summary/link, are archived.
git diff --check completed without whitespace errors.

## Remaining implementation, not completed acceptance

The full eight-fit native runner has NOT been implemented or executed in this batch.
It must instantiate new candidate-owned actors/critics/optimizers/RNGs; persist all
candidate evidence; save and hash the selection record before holdout fitting;
and bind the actual native command, source, current admission and supervisor.
The selection record is an auditable stage fence, not a security guarantee that
a caller cannot forge an input object. Runtime wiring and persistence need focused
tests/review; these13 pure tests do not establish native end-to-end integrity.

Proportionate independent review of the completed changed behavior remains pending.
No reviewer/monitor/transport child or new Pro/Portfolio request was started.
No pending or uncertain Send is created. Historical uncertain identities are untouched.

## Cost and preservation

This batch performed local source/record reading, protocol implementation, synthetic
tests, count calculation and archival normalization only. Native exposure is zero.
Do not read the unittest duration as full support cost; full support/provider/lifetime
totals remain UNKNOWN. No file or worktree was deleted and no deletion refusal bypassed.

## Complete runner implementation batch (prospective continuation)

L0: implement one runnable eight-fit MGTAP-LR-SELECTION-B01 entry point and focused
synthetic wiring/publication tests, reusing the accepted native learner. Authoring
checkout is C:/Projects/HMASD-worktrees/dm-n5-continue-20260904, branch codex/mgtap,
starting HEAD1fb4259905f0a803f515b40131bea9c7417eec61, initially clean.
The Implementer owns only new `mgtap_lr_selection_b01/study.py` and its focused
`test_study.py`; DM retains card/protocol changes, Git, technical acceptance and launch.
Other writers' documentation and request files are preserved.

The current card §§2–5 supplies the exact native semantics, three-candidate order,
fresh state/RNG ownership, stage fence, eight-fit exposure, primary, output and limits.
Use existing `mgtap_early_exposure_b02/study.py`, `conditional_pooling.py`, and
`ucope/uav_motion_prefix_b01/learner.py` as read-only dependencies; do not modify frozen
learners or other directions. Focused tests must exercise candidate order and fresh
state, selected per-arm rates, a persisted selection record before holdout construction,
all panels/raw output and the primary, and failure partials. They are synthetic checks,
not native science, and must not create extra empirical evidence.

Bounds: one runner under600 lines, this research attempt under2000 non-test source
lines, focused test budget5 minutes for this directory; no scientific run, remote
execution, additional candidate/seed, changed endpoint, child delegation, or Git commit
by the Implementer. Return actual diff/check output and precise residual issues to DM.
Independent Sol/high changed-path review follows; it is technical evidence, not a
lifecycle grant. Required §4 items and the corrected4GiB admission plan are explicit
in the prospectively updated card. Native exposure remains zero.

Actual Implementer dispatch: `/root/im_s_m_mgtap_lr_runner`, model gpt-5.6-sol,
reasoning medium, fork_turns=none; batch MGTAP_LR_RUNNER_IMPL_20260914.
Parent is this DM App task01a09cd8-676e-7513-806d-a86b7e104518, native /root.

### Implementation delivery and first DM consequence

Batch MGTAP_LR_RUNNER_IMPL_20260914 returned the two assigned files only:
study.py273 lines and test_study.py184 lines. The Implementer reports py_compile and
the combined protocol/study pytest checks:16 passed,16 subtests passed in1.93s,
command wall2.924s. One initial wiring failure passed train rows into the eval-only
selector; the same batch corrected explicit stage+phase projection and the rerun passed.
Its two task-owned scratch directories were removed and verified absent by the creator.
No Git mutation, native/reward run, remote execution or admission was performed by it.

DM read both full files and received the writer release. Actual next consequence:
independent read-only Sol/high Reviewer /root/rv_s_h_mgtap_lr_runner, minimal fresh
context, batch MGTAP_LR_RUNNER_REVIEW_20260914, covers the full changed protocol/runner,
state/RNG lifetime, scientific consumers and publication. DM flagged a concrete point
for assessment: fit-local limits versus top-level COMPLETE; its reachable meaning,
not a hypothetical hostile-input guard, determines whether correction is required.
Technical acceptance and real execution remain pending; passing synthetic tests are
not a native scientific observation.

The scientific design review was separately published as TASKbceb608c441c7c94ebbded02f011c7eb4d85f675,
HANDOFF7f0a2c0b4b0f231f028d12fe12a9b7cd269db9c3 and dispatched to the registered
independent iab Transport. At this boundary App delivery is confirmed, provider
acceptance has not yet been returned; no claim of a completed scientific review follows.

### Independent review findings and selected corrections

The Reviewer returned two concrete engineering findings, no material protected scientific
behavior defect: P2 the runner's elapsed_wall is body-only, omitting import/setup and final
publication; P3 stdlib TemporaryDirectory ignores pytest --basetemp and uses OS temp.
DM accepts both. The same Implementer corrects explicit body-only timing names/scope and
routes test scratch through the invocation-owned pytest root, followed by focused checks.
No new object, seed, endpoint, RNG/learning change or generic telemetry layer is selected.

The exact [command](COMMAND.sh) supplies authoritative complete-command wall and peak RSS
through existing GNU time, surrounding timeout, shell setup, memory admission, imports,
learning/evaluation, checkpoints/summary/stdout and exit. It excludes agent-task queue/setup,
Git/SSH/staging, provider/DM work and later archival; those remain separate scope/UNKNOWN.
The serial14400s external watchdog is an ordinary technical plan, not a new owner cap.
It does not retry a stopped run. Admission on wsl_4070 immediately precedes the learner
in the same detached command;4GiB physical and effective available remain required.
This file is prepared, NOT a launch receipt. Exact published SHA and detached worktree
are bound before dispatch; no process is accepted by writing a command.

DM accepts the reviewer's per-fit-limit classification for this fixed producer: with
diagnostics=False, the only possible appended collector diagnostic concerns served-users,
which MultiUAVEnv.step supplies numerically. It is not used by J/selection; any fit-local
diagnostic remains in that fit's output rather than being silently deleted. No new generic
diagnostic gate is added. Primary finiteness, complete panels/counts and thrown learner
failures remain binding. If this protected producer or claim changes, reassess the actual
dependency; optional resource/diagnostic gaps are not automatically scientific polarity.

### Correction recheck and DM technical acceptance

The same Implementer released corrected study.py281 lines, SHA256
e5a23642fe6e11e27d23d6345a1273be1a298030685983736be5cac7b6ab3ef9,
and test_study.py192 lines, SHA256
726d26f5f6cc209c498cec23b4de6fdabf28b3637a8d620752c02575670ea071.
Actual focused correction checks: py_compile and the combined protocol/study pytest
suite,16 passed and16 subtests passed in2.12s, complete check-command wall3.154s.
The invocation-owned scratch was inspected for containment, removed by its creator,
and verified absent. These are synthetic checks, not native exposure.

Independent same-batch correction recheck MGTAP_LR_RUNNER_REVIEW_20260914 cleared
both findings with no remaining material defect. It also inspected the12-line command
and ran non-executing bash -n successfully (exit0); it did not repeat the passing suite,
change repository state or perform admission/native work. DM read the corrected timing
and scratch paths and accepts the review's actual coverage, not just its verdict.

DM direct-command L0: goal is the full-command launch/timing boundary for the selected
eight-fit study; only reentry_20260914/COMMAND.sh in this authoring checkout is owned;
card §3 scientific semantics, masters8251/8252, CPU FP32/thread1 and no retry are preserved;
acceptance is independent syntax/boundary review plus actual exact-SHA staging and fresh
4GiB physical/effective admission before native execution; bounds are one12-line command,
the existing agent-task supervisor and14400s ordinary watchdog, no new framework or pilot.

Scientific-review §3's three concrete producer/consumer dependencies are covered by the
actual changed-path inspection: complete six candidate fits and count checks; own-score
selection JSON and byte hash persisted before the holdout pair factory; fresh8252 model,
optimizer, environment and private RNG construction, taking only selected LR labels.
The hash alone is not proof of temporal isolation. Raw learning/evaluation records,
count facts, checkpoints and the actual complete command receipt remain to be obtained.

DM technical acceptance is therefore complete for the reviewed source and prepared
command. This establishes readiness to perform the selected ordinary experiment, not
that remote source/admission/launch or any scientific result exists. The next concrete
action is commit/push, exact detached staging, current admission and agent-task dispatch.

### DM direct completed-output audit scope

L0 goal: collect the one completed programme, verify raw byte preservation and recompute
the already fixed selection/primary without scientific execution. Owned source is only
reentry_20260914/analyze_intake.py and its generated intake/CSV/archive records in this
authoring checkout; native inputs are the named completed output plus supervisor files.
Protected semantics are the existing protocol's own-score selector, exact ties, one fresh
holdout pair and conditional paired-world primary. The audit reuses that pure reducer;
it never imports Torch, constructs a model/RNG, loads checkpoints, fits or evaluates.
Acceptance checks compare all20 native/supervisor member hashes with direct remote reads,
all eight complete training/evaluation/rollout paths, original reward_sum/256 J, selected
configuration/hash and raw-panel primary with the published result; archive members are
read back byte-for-byte. Counts derive from these completed records, not a simulation.
Bounds are one data-only local pass and the supplied run-summary tool on only two final
run endpoints, no exclusion/search/extra scientific row or generic audit framework.
No new scientific producer or estimand is introduced; DM inspection and exact comparison
to the already independently reviewed reducer are proportionate for this mechanical audit.

Actual audit and supplied run-summary commands both exited0. The data-only check reports
PASS for20 remote hashes/archive readbacks, all8fits/2304episodes/1024rollouts and exact
selection/primary recomputation. Completed counts match589824teamticks/4096Adam/
13434880actorrowuses. Generic descriptive input contains only2final endpoint rows,
explicitly paired; it reports n=1 and sample_sd=null, not32training replications.
All native/checkpoint bytes are retained in NATIVE_EVIDENCE.zip (6666445bytes) and original
local/remote outputs. This audit performed no new scientific execution or checkpoint load.
