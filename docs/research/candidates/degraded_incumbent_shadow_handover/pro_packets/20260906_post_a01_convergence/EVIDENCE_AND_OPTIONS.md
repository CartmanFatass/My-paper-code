# DISH post-A01 Convergence: evidence and options (DM proposal, 2026-09-06)

Claim: on the unmodified B02 ordinary path the policy's renewal flag lags the native renewal
admission by one primitive tick, so with period k > 1 no fresh policy command was incorporated in
the observed windows. Binding structure: information flow at the policy-to-native action boundary
of one learning controller during handover; no partner co-adaptation is involved in this A.

Proposal only, for the existing `em:degraded_incumbent_shadow_handover:convergence` node, written
by the Claude research hub as DM after the intake of `DISH-RENEWAL-BOUNDARY-A01`. It is not a
frozen card, an accepted source change, a launch or a Portfolio action.

## What the A measured (observation)

- One retained checkpoint (FORECAST_PACKAGE, seed 61, update 16, sha256 `504329d6…dc66`), two
  32-tick ordinary windows of two initial coordinates (K8 then K4), zero training, zero parameter
  movement (norm `39.149200792042365` before and after each window).
- Native admission with policy `renew` false: **12** (4 in window 1 at t = 4, 12, 20, 28; 8 in
  window 2 at t = 2, 6, …, 30). Policy `renew` true with native admission false: **12** (the
  tick after each admission). Both true: **0**. Both false: **40**. Held-command changes: **0**.
- At every admission tick the policy consumed `renew = 0`, copied the held command and emitted
  `[0, 0, 0, 0]`, which native incorporated (held vector stays zero for all 64 ticks). At every
  following tick the policy consumed `renew = 1` and emitted a nonzero fresh motion vector
  (window 1 t = 5: `[-1.1746, 1.3738, 0.7295, -1.0287]`), which native did not incorporate
  (`pre_countdown` 7 or 3). Prepare/commit proposals (`prepare = [1, 0]`; `commit = [1, 0]` in
  window 2) were likewise emitted only on non-admission ticks; `cas_applied` stayed 0.
- Tick 0 flags are correct (`renew = 0` with countdown 4 and 2), so the reset boundary adds
  nothing to the counts. DM predicted branch 1 with 4 and 8 disagreements; observed 4 and 8.
- Runner wall 0.090 s formal, 0.065 s check; peak RSS 363 MB; the 120 s bound is closed.

## Mechanism read from source (inference, not measured by the A)

- Native (`rbhr_r06_production_backend.cpp`): `renew = (countdown == 0)` is computed before the
  decrement; the held command is written only under that condition; the countdown is advanced
  afterwards; the returned `renew` is the flag of the transition just completed.
- Python (`production_backend.py`, `_StepOutput.renew`) passes that flag through unchanged into
  `observation["renew"]`; `production_recurrent_trainer.py` reads it at line 311 for the ordinary
  step rows and stacks the same field as `renew`, `prepare_mask` and `commit_mask` at lines
  506–508 when it builds training fragments. So the training collection very likely consumed the
  same lagged flag; that is a source read, not a measurement, and this A did not run the
  collection path.
- Consequence for B01/B02 (inference): in ordinary rollouts on this host the learned motion
  command reached native only when the policy's copied held command coincided with it, which in
  these windows never happened. B02's identical 470-tick service in both arms is consistent with
  this; it is not thereby explained.

## Options the DM sees

1. **One bounded timing/interface correction object on the ordinary path** (DM recommendation,
   offered for challenge). Align the flag the policy consumes at tick n with native's admission
   at tick n: either expose the *current* countdown-zero condition at the wrapper boundary, or
   have the wrapper derive `renew_now = (countdown == 0)` from the returned state without touching
   the native ABI. No reward, information, action-space, learner, loss or host change. Acceptance:
   the same two windows re-run at the new sha must read "both true" at every admission tick and
   "both false" elsewhere, with the fresh command incorporated on admission ticks; a focused test
   on the K8 and K4 schedules; the existing B02 focused test unchanged. Then an explicit intake
   decides which B01/B02 interpretations depend on the mismatch. No learner is trained by this
   object. Cost: engineering only, inside the ordinary scope budgets; the acceptance run is the
   A01 runner again (under 1 s on `wsl_4070` plus build and preflight).
2. **Reinterpret B01/B02 now on the source read, without a correction.** Cheapest; but the
   training-side lag is inferred, and any later learner would still run on the lagged path.
3. **Go directly to a new B on the corrected path** (correction plus training in one object).
   Buys learning before the correction is verified through native behavior; the previous Pro rule
   asked for the correction to be tested through native behavior first.
4. **Pause the RETAIN/COPY/SHADOW exploratory family at this boundary.** Keeps everything
   recorded; defers the correction. The DM does not recommend this: the defect is local,
   measured, and cheap to correct, and until it is corrected no learner result on this host can
   be read as a motion-policy result.

## What the DM asks the node not to do

- Do not require a full training-path replay, a census of every schedule, or an epsilon gate on
  command differences before selecting the correction (spec §11.8).
- Do not revise B02's raw outcomes; only interpretations that depend on the mismatch, and only
  through an explicit later intake.
- Do not treat this A as a service, learning or equivalence result.
