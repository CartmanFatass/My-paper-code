# VSPC1 B04 — independent fresh-key binding review

No material binding defect was found after source and focused-check inspection.
Actual exact-source remote checkout and final command inspection remain pending
below. This is independent technical evidence, not approval, permission, or a
scientific disposition.

Contract: [B04 CM specification sections 1–5](VSPC1_NATIVE_HOLD_VALUE_B04_CM_SPEC_20260908.md)
and [B04 card sections 2–5](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md).
Designated checkout: `codex/direction-vsp_c1`, clean assignment input
`0a60f57514709a0eb390253576dc8df8f7d47c21`.
Reviewer ownership is only this document; no test, model, experiment, native
invocation, admission, or commit was executed by the reviewer.

## Changed boundary and preserved computation

The new 35-line runner differs from the accepted B03 entry point only in its B04
object/card and fixed8202 binding. It passes `Config(seed=8202)` with
`normalize_value=True`, rejects other keys and fixture flags before scientific
state, and retains the original numerical-thread setup, startup timing and status
handling. The shared study propagates the supplied object/card/key to summary,
both checkpoints and all reset/generator domains without global mutation or
loading previous state.

The reviewer directly compared the B01/B02/B03 runners, VSPC1 shared study/critic/
normalization modules, complete UCOPE package and native environment/adapter against
accepted source `7a8ed3aa5d25ded71164aa338749d09318124dcf`: the diff is empty.
The existing [B03 numerical review](VSPC1_NATIVE_HOLD_VALUE_B03_PRODUCTION_REVIEW_20260908.md)
therefore supplies unchanged normalization/native-credit, FP32 moment merge,
gradient, checkpoint/partial-state and evaluation/H evidence. No numerical or
historical learner check was repeated for this identity-only change.

The inherited per-arm private generators map8202 to initialization820200011,
training velocity/duration820200021/820200022, constructors820201000, training
resets820201000–820201511, evaluation resets820202000–820202031, and learned
evaluation streams820203000–820203031/820204000–820204031. Counts, moments,
entropy .01, compound PPO, final-only native endpoints and the primary rule are
unchanged. This is a fresh normalized-regime pair, not a relabel of8201.

## Focused evidence and reporting limit

The reviewer read `test_binding.py` and retained
`temp/directions/vsp_c1/engineering/native_hold_value_b04/focused_result.json`.
CM's single original focused command passed seven cases in3.79 s pytest,
5.3719231 s observed process wall, exit0, within300 s. The only warning is the
existing unknown `cache_dir` option with cacheprovider disabled.

The tests verify B04/8202/normalization propagation and rejection of8101,8102,
8201,9001 and fixture mode before scientific state. Full-schedule stubs forbid
scientific model/environment constructors and replace optimizer/collection/update
operations. They check every reset/stream domain, private generator objects,
final-only evaluation, H reuse, complete schedule metadata, both checkpoint
identities and separate frozen moment state. Their286720/2048/96 counters and512
moment merges are stub schedule evidence, not executed scientific exposure.
The package initializer isolates the test module; no existing test helper changed.

**Inherited reporting limit, not a binding regression:** source exposure still
serializes an epsilon-based duration relative number for a zero initial norm,
whereas the gate field is null. For example, retained B03 duration output has
initial norm0 and relative field114033222198.48633. As recognized in B01 acceptance,
that number is not a defined relative displacement. B04 card section5's undefined
duration/gate interpretation must be retained in acceptance/intake; do not claim
the unchanged raw duration field is already null or use it as movement evidence.
No protected source change or additional run is required for this qualification.

## Scope and remaining staging review

Production addition is only the35-line runner, below2000 source/600 runner limits.
Applying runtime-spec general requirements followed by scope-spec sections4–5,
no prohibited item is added and no unnecessary orchestration was found. The thin
binding is required by the object; no registry, worker, retry/resume, new source
guard or telemetry framework is introduced. Unchanged single-process CPU FP32
computation and fixed numerical thread limits need no new runtime census here.

Pending the committed source SHA, actual clean detached remote checkout, direct
HEAD/cwd/required-file evidence, and staged literal-LF script syntax/readback.
Unlike B03's earlier unready-cwd handoff, this contract requires actual source
staging before the command is reported ready. Inspect the requested new B04
handle/output/admission identities without submitting them. Preserve continuous
1800s/arm and3600s/pair accounting through publication/exit, with no early hard-KILL
wrapper. Native runtime, resource admission, moment/Adam counts and performance
remain future execution observations; the current checks establish none of them.
