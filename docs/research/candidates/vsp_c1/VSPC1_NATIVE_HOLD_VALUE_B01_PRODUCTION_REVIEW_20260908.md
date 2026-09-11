# VSPC1 native hold-value B01 — independent production review

No material scientific or implementation finding remains in the inspected source after
the reporting corrections below. This is independent technical evidence, not approval,
launch permission, or a scientific disposition.

Review scope: the four new production files under
`experiments/candidates/vsp_c1/native_hold_value_b01/` and
`scripts/run_vspc1_native_hold_value_b01.py`, plus their focused tests. Starting checkout
was `codex/direction-vsp_c1` at `6f3634dfdbb59cf6dc71b6625e86153a9316b167`.
The reviewer edited only this document and ran no learner, fixture, native invocation,
or replay. Production source was inspected before and after CM's reporting corrections.

The contract is [CM specification §§1–5](VSPC1_NATIVE_HOLD_VALUE_B01_CM_SPEC_20260908.md)
and [science card §§2–6](VSPC1_NATIVE_HOLD_VALUE_B01_SCIENCE_CARD_20260908.md).
The review applied the runtime specification's general requirements, then engineering
scope §§4–5; no object appendix changes this object's single-thread topology.

## Findings and dispositions

1. **Complete timing claim corrected.** The original last `observe_time()` precedes
   function return, CLI printing, and interpreter exit. The sole fixture's externally
   observed wall was 3.991 s, while its published internal wall was 3.297 s. The
   difference is unpartitioned launch/exit/observation overhead; it is not a measured
   amount of Python computation. Thus internal `cap_breach=false` alone cannot prove
   the card's complete 1,800 s/arm and 3,600 s/pair compliance. CM added an explicit
   `timing_boundary`, `complete_exit_cap_conformance="unmeasured: ..."`, and
   `mlp_start_pair_elapsed` at the actual arm transition. The later operator must use
   the existing supervisor's terminal process-wall observation, charging pre-main
   startup to GATED-V and exit to MLP-V. No new supervisor or timing experiment was
   introduced. The source now accurately limits its internal claim; full native exit
   compliance remains an execution fact to collect. The DM-confirmed method in
   [technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B01_TECHNICAL_ACCEPTANCE_20260908.md#review-disposition-and-remaining-execution-observations)
   adds the entire nonnegative external/internal residual to each measured arm as a
   conservative upper bound when its startup/exit split is unknown, and uses external
   whole wall as the direct total. An enclosing supervisor interval that also includes
   admission is a conservative bound, not an exact scientific-process measurement.
2. **Original H-cap coverage completed.** Initial tests covered continuous deadlines
   and late publication but did not advance the clock during H. CM added that branch
   to the existing fake-clock test. It checks an MLP cap breach, retained complete
   primary, incomplete H, and retained H counts. The first changed-test run passed.
3. **Partial-loss reporting clarified.** The reused `update` returns loss records only
   after a complete four-epoch update. On an interrupted update, actual Adam counts
   survive but partial epoch-loss records are not returned. CM labels this explicitly
   with `rollout_loss_coverage`; no source learner rewrite or invented losses follow.
   Returned-complete-episode coverage also labels the nonzero-hold diagnostic.

## Direct source evidence

- `critic.py` selects r columns 119/123/127/131/135 and their ordered complement,
  retains first-layer bias and Br, applies the selected multiplicative gate once,
  and reuses the second/output layers. The gate is a directly constructed zero
  parameter, with no random initializer. Both arms use independent duration-capable
  actor copies of the common actor-then-critic template. Zero-gate norm ratios are
  null with a reason; the source duration exposure remains the specified inherited
  diagnostic and is not a meaningful zero-norm relative ratio.
- The unchanged collector assembles critic inputs before sampling, advances five GRU
  histories on held rows, retains primitive rewards, and supplies gamma-one return
  targets to the unchanged four-epoch learner. Both new collection and update calls
  explicitly select `agent_compound`; masks, signed clipping, primitive-row reduction,
  optimizer, and joint actor/critic gradient clipping are reused.
- The study uses separate per-arm private training streams, matched per-episode
  evaluation streams and reset identities, two constructors, final-only sampled
  learned policies, and model-free H in the MLP environment. Primary joins on episode
  plus reset seed, rejects incomplete/duplicate identity sets, retains all three
  differences with conditional SE, and implements strict outer/inclusive inner MEI
  tests. Missing H does not erase complete GATED-minus-MLP data.
- Budget checks retain the first arm's deadline before switching, charge startup and
  common initialization to GATED, and include H, summary/checkpoint readback and
  publication in the MLP timeline. Partial native steps and Adam counts survive
  source exceptions. There is no resume or retry path.
- CLI sets OMP/MKL/OpenBLAS/NumExpr and Torch numerical thread counts to one before
  numerical work. This is serial CPU FP32 computation with the source learner's
  existing independent chunk/agent tensor batching. No new native team, worker,
  mutable shared model, environment backend, or dependency is introduced. Fixture
  imports do not execute the deferred native environment factory.

## Verification evidence and scope

CM reports the exact original focused command completed with 21 passed in 8.12 s,
exit 0; its first H-overrun follow-up completed with 1 passed in 3.69 s, exit 0.
The final changed timing-field check completed with 1 passed in 3.93 s, exit 0.
Total reported pytest time was 15.74 s, with command observation under 22 s;
[technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B01_TECHNICAL_ACCEPTANCE_20260908.md#actual-checks)
records the exact commands and their boundaries.
The original sole fixture exited 0 in 3.991 s. The reviewer read its
`temp/directions/vsp_c1/exp/native_hold_value_b01_engineering9001/summary.json`
and `engineering_readback.json`, and independently counted the emitted JSONL rows:
10 episodes, 80 summed team steps, two rollouts and eight epoch records. Published
counts are 8 Adam calls, 6 evaluation episodes, 2 constructor resets, and 0 UAV calls.
Both arm checkpoints and duration-head identities were read back by CM. Primary and
H endpoints are complete, the three differences have the required dependence, and
the gate has finite absolute displacement with null relative displacement.

The reviewer inspected the actual new tests and inherited clipping tests: column
mapping, shapes, independent storage/common initialization, RNG preservation, gate
gradient support, scripted pre-decision holds, compound plumbing, seeds, final-only
sampling, identity/SE/MEI arithmetic, partial rows, missing H, and publication failures.
These are engineering checks; synthetic values do not establish UAV benefit.

Tool-computed final source counts are 329 lines: initializer 1, critic 42, study 251,
runner 35. These satisfy the 2,000/600 limits. No prohibited §4 item is added without
a card line; there is no prohibited addition to list. Serialization, required identity
readback and deadlines implement the named card outputs and complete budget; no
unnecessary orchestration mechanism was found. Fixed loop arithmetic gives 286,720
real team steps and 2,048 Adam calls, or 80/8 for the explicit fixture.

Residual limits: native incremental gate cost and full native runtime are unmeasured;
aggregate CPU and peak RSS are unmeasured, not zero. The fixture precedes the small
reporting-label additions, which do not change sampling, learning, or primary values.
There was no second smoke. Full process-exit cap determination belongs in the later
existing operator record; a successful synthetic interface check cannot establish it.
