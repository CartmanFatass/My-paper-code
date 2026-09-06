# DISH post-A02 Convergence: evidence and options (DM proposal, 2026-09-06)

Claim: with the ordinary-renewal permission derived from the current native countdown at the
Python wrapper boundary, the policy's consumed flag agrees with native admission on every tick of
the two A01 windows and every fresh command is incorporated through native's unchanged projection;
the learned-motion question that B01/B02 could not test on the lagged interface is therefore
testable now. Binding structure: information flow at the policy-to-native action boundary of one
learning controller during handover; the later comparison involves one learner and one fixed
partner protocol, no partner co-adaptation.

Proposal only, for the existing `em:degraded_incumbent_shadow_handover:convergence` node, written
by the Claude research hub as DM after the intake of `DISH-RENEWAL-BOUNDARY-A02-CORRECTION` and
the qualified B01/B02 reinterpretation. Not a frozen card, not a launch, not a Portfolio action.

## What A02 measured (observation)

- Correction as you specified: `observation["renew"] = [current countdown == 0]` per lane at the
  ordinary wrapper outputs (`observe`, `step`, `rollout`); the raw completed-transition flag kept
  under `renew_completed`; generic decoder, prepared/B01 paths, source clones and native untouched.
  Implemented by Grok Build, reviewed by the Opus reviewer (four findings fixed or recorded) and the
  hub; integrated at `3f4d447f6`; 11 focused tests and the 64-test r06 suite pass.
- Same checkpoint (FORECAST_PACKAGE seed 61 update 16, sha256 `504329d6…dc66`, verified), same two
  windows, zero training, parameter norm unchanged. Formal: `native_out_renew_equals_policy_renew`
  **64/64**, disagreements **0/0**; countdown consistency 12 matched renewals (t = 4, 12, 20, 28
  and t = 2, 6, …, 30) and 52 matched non-renewals, 0 disagreements. At all 12 admissions the
  emitted command is nonzero, differs from the held vector, and the held vector after the step
  equals the independent float64 projection of that command from the previous held vector
  (`admissions_held_equals_projected` 12, `admissions_emitted_equals_held` 0); held changes
  outside admissions 0. Example, window 1 t = 4: emitted `[-1.1996, 1.5664, 1.0252, -0.4977]`,
  held after `[-0.9120, 1.1909, 1.0252, -0.4977]`.
- Behaviour context, not acceptance conditions: service 60/64 (identical count to A01's lagged
  path), energy increments sum 9220.97 versus 8563.59 in A01; no early terminal, no hard event;
  prepare proposals now sample on admission ticks (window 1 all four, window 2 five of eight),
  commit proposals on admission ticks (two and eight); `cas_applied` 0; owner 0 throughout.
- Cost: runner wall 0.092 s formal / 0.064 s check on `wsl_4070`, peak RSS 363 MB, inside the
  120 s bound, which is closed. Both invocations launched once.
- Card row 1 applied (`DISH_RENEWAL_BOUNDARY_A02_RESULT_INTAKE_20260906.md`); your expected counts
  matched; the DM's "service will differ from 60" sub-prediction was wrong. The qualified
  reinterpretation intake keeps B02's 572/447/433/428 and its inside-MEI reading as outcomes of
  the executed interface (learned fresh motion never incorporated at admission), attributes the
  null to nothing, quarantines nothing, and leaves the training-side lag as source-supported
  inference.

## What is still not known (stated as such)

- Whether a learner trained on the corrected path, with its fresh motion actually incorporated,
  produces different ordinary service from the inherited control at matched exposure. B02 did not
  test this: both arms were trained and evaluated with the lag.
- Whether delivered fresh motion changes service at all on this host: A02 shows equal service and
  higher energy on 64 ticks with a checkpoint that was trained under the lag, which is not a
  learning result and not the corrected-path learner.
- Whether the prepare/commit proposal gate saw a matching lag in B01/B02 (CAS never fired).

## Options weighed by the DM

1. **B03: the B02 comparison on the corrected path, as a new object (recommended).** CONTROL versus
   FORECAST_PACKAGE, the unchanged B02 design: host `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`, matched
   initial parameters, 16 complete updates per arm (32 lanes × 128 ticks per update, 4 epochs × 8),
   update-16 checkpoint only, the four paired development conditions (TARGET_VISUAL_MASK and
   TERRAIN_RELAY_MASK × K8 and K4_TO_K12), primary endpoint mean native service ticks over the four
   paired rows, MEI +24 ticks, energy and hard events visible, 1,800 s per complete arm and 3,600 s
   summed, remote-first with fresh admissions, no retry, no substitution. Differences from B02: the
   ordinary boundary is the corrected one (both arms), and the training seed is **a fresh paired
   seed** rather than seed 61 (outcome-blind; the seed-61 pair remains B02's). Honest label: a new
   B/EXPLORE object on the corrected interface, not a repeat of B02; B02's rows are not re-read by
   it. Decision value: it is the first time the package question is asked with the learned motion
   delivered; the row structure of B02's reading rule applies with the same MEI.
2. **A zero-training delivered-motion witness first.** Evaluate the retained B02 update-16
   checkpoints of both arms on the corrected path over the four conditions (≤ 4,800 ticks per arm).
   Seconds of work, but the policies were trained under the lag, so their delivered fresh motion is
   not what a corrected-path learner would produce; the DM does not see a decision it changes before
   option 1 and offers it only as an optional side measurement, not a prerequisite.
3. **Pause the RETAIN/COPY/SHADOW exploratory family at this boundary.** Rejected by the DM: the
   family's package question has not yet been tested with delivered motion, so a pause now would
   rest on a result the reinterpretation intake has just qualified.
4. **Recast the question to motion delivery itself** (learned motion versus a held-only control on
   the corrected path). A different family; not selected while option 1 can ask the existing
   question honestly.

Questions the DM puts to the node with option 1: fresh seed versus seed 61 (the DM proposes fresh);
whether a non-learning held-only reference row should be added to the evaluation (the DM proposes
no, to keep the pair as B02 defined it); whether any acceptance beyond B02's existing focused
coverage plus the a02 tests is needed before launch (the DM proposes no); and whether the B02 cost
reference (642.66 s external wall for the pair) may serve as the per-arm projection basis given the
correction adds no computational work.
