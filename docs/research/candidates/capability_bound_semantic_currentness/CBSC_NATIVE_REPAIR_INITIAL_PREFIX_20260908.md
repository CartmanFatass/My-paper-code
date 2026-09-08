# CBSC native repair: faithful non-learning initial prefix

**Normal completion / historical fatal not reproduced.** The original seed21223
setup and all32 initial RAW evaluation-tape projections completed, with64
before/after projection indices. The TEST_ONLY process stopped before scores or
learning. This is diagnostic engineering evidence, not crash-fix completion.

## Authorized discriminator and source boundary

Following the [synthetic isolation pass](CBSC_NATIVE_REPAIR_TEST_ONLY_20260908.md),
Root supplied a new owner-authorized discriminator: one faithful non-learning
P32 initial-projection prefix, using its existing21223 tape-generation/setup
order and model/trainer initialization, indexed progress, separate engineering
output, complete wall<=120s and fresh admission. Normal completion required a
concrete next hypothesis, not a crash-fix claim. No production edit, new seed,
study, pair, scores, train step, relabelling or FRRIE continuation was authorized.

Delivered72-line standalone reproducer:
`tests/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/test_initial_projection_prefix.py`.
Pushed source `2177880ca74b4afd9cf0445d33cb66cb9a8d9c09`, authoring branch
`codex/cbsc`, checkout `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`.
The complete `omrc_b01` and `opportunity_credit_b04` production directories have
zero diff against P32 source `d2753be86c12bfa63c404ac2cac513b914371115`.
No scope-spec §4 machinery or production change was added. No child was used.

The reproducer directly invokes original `run.run_arm` with RAW-GRU,21223,
`b05=True`, `engineering=False`; its original setup builds384 TRAIN tapes,
32 EVAL_STOCHASTIC tapes, training/action-uniform digests, the model and
OpportunityTrainer, flattened initial parameters and initial norm, in that
original order. The original initial `_project_panel` executes with the original
fresh-adapter double replay and exact tensor/work equality checks.

A TEST_ONLY wrapper retains the32 tapes' public tokens, prints each
`build_observations` call index/tape/pass immediately before it and its completion
afterwards, then raises a private `PrefixComplete` exception at initial-panel
return. It never returns to `run_arm` after that call. Source-flow inspection
therefore places the stop before fixed-rule scoring, held-out score evaluation,
rollouts, training, checkpoints and scientific publication. The wrapper restores
the original functions when exiting. Failure/timeout also cannot pass the stop.

Deliberate differences: the original script's argparse/git query are omitted;
launch_sha/output are TEST_ONLY; wrappers add Python frames, progress I/O,
public-byte serialization and a result write. Thus timing, allocation history
and call stacks are perturbed. No claim of native process-state identity follows.
The binary is the current prefix's original deterministic public tape input;
P32 did not retain bytes or a faulting token index for direct historical comparison.

## Frozen execution, cost and observations

One accepted handle `cbsc-test-only-initial-prefix-20260908`, PID2774241, on
`wsl_4070`, detached exact-SHA cwd
`/home/wu/hmasd-worktrees/cbsc-test-only-initial-prefix-20260908`.
P32 lexical interpreter retained:
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`.
Observed Python3.12.3, Torch2.7.0+cu118, CPU FP32, Torch threads1.

Frozen argv/cwd/output/source/cap/omission record: `launch.json` in the local
collection root
`temp/directions/capability_bound_semantic_currentness/test/initial_prefix_20260908_control/`.
Existing `agent-task` encloses the same outer GNU-time, TERM115s/KILL5s,
numeric-library thread limits, non-login inner shell, adjacent admission `&&`
and `exec python -X faulthandler <test> <fresh TEST_ONLY output>` chain.
The configured `zsh -lic` staged committed bytes; `git fetch --refmap=` avoided
the old remote-tracking namespace collision without changing or deleting refs.

Before launch: one engineering process, original416 generated tapes/setup and
32x2x152 adapter calls; normal complete time unknown, cap120s. Historical P32's
15.25s fatal wall was explicitly not a normal-completion forecast. There is no
per-arm sweep. Post-learner publication is outside this test; indexed logs,
input bytes and a TEST_ONLY JSON are its primary outputs.

Admission at2026-09-08T14:25:02.752836Z passed: physical/effective available
15,649,153,024bytes against4,294,967,296bytes. Start14:25:02Z/end14:25:09Z;
terminal exit0, tmux inactive. Complete outer wall7.23s, peak RSS538,160KiB;
aggregate CPU unmeasured. Actual wall is below120s.

Collected assertions established:

- Before/after indices each cover0..63 exactly; tape index is `i//2` and pass
  `i%2`, covering all32 tapes twice. There are9,728 adapter process calls.
- Original replay equality passed; final tensor shape `[32,152,168]`, FP32.
  Original returned work is26,320 appended bytes, counting one projection per
  tape as the original engine does, not double-counting its replay check.
- `TEST_ONLY_initial_public_tokens.bin` has82,688bytes, ordered tape-major then
  token-major,17bytes per token and152 tokens per tape. It contains public input
  only. Evaluation tape digest:
  `59552a14a9681fb47fce5816cd5e8c6839bf3f57e832f5927ec3852c8bfa441a`.
- `TEST_ONLY_prefix_result.json` records completion, runtime, shape, work and
  zero score evaluations/learning updates. Those zeroes are supported by the
  enforced source boundary, not inferred merely from process exit.
- The output directory contains only that binary and TEST_ONLY JSON. No
  updates/checkpoint/scientific summary exists.416 tape constructions and
  model/optimizer initialization are not learner interactions or updates.

Supervisor records, original task.log, status/log retrieval, admission and output
were copied into the local root above; both copies exited0. Local readback
assertions checked all index tuples, byte count, the two-file output set and
reported zero learning/scores. AST/path and whitespace checks passed. No repeated
target run or broader suite followed.

## Current hypothesis and next responsible owner

The same source/setup/input law on the same named interpreter completed once.
That rules out an inevitable failure of this prefix in the observed instrumented
execution; it does not establish historical safety or identify the writer.

Concrete next hypothesis: **the fatal depends on process/heap-layout or timing
state, including a perturbation removed by the test wrappers, rather than being
forced solely by the deterministic initial tapes and RAW FIFO operation.** This
is a hypothesis, not an attribution to Python, Torch, hardware or a shared FRRIE
cause. A discriminating follow-up would retain the same initial-prefix stop and
input, reducing pre-projection wrapper I/O/allocation while preserving the
no-learning boundary, or target another specifically identified native operation;
neither was launched by this assignment. Root/DM owns that next bounded selection.

No production repair is evidenced, no before/after repair claim is available,
and no scientific goal, study, pair or score collection was resumed.
