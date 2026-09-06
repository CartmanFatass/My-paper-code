Claim tested: After deriving the policy's ordinary renewal permission from the current native countdown at the Python wrapper boundary, the retained FORECAST_PACKAGE policy's fresh commands are incorporated by native at every admission tick on the two A01 windows, with zero same-tick permission disagreements and the held vector equal to native's unchanged projection of the emitted command.
Binding structure: systems / information flow at the policy-to-native action boundary of one learning controller during handover.

# DISH-RENEWAL-BOUNDARY-A02-CORRECTION — science card (2026-09-06)

Class: **A/RECON** (interface correction with native acceptance observation). Direction
authority: `PRO_FINAL — CONTINUE`, post-A01 Convergence response archived at
`ed4363a2e4c0b578eac64ca19da6ef5e27b64a17` (sha256 `866736a2…`), taken in by
`DISH_POST_A01_CONVERGENCE_INTAKE_20260906.md`. Predecessor: `DISH-RENEWAL-BOUNDARY-A01`
(branch 1, one-tick lag, `DISH_RENEWAL_BOUNDARY_A01_RESULT_INTAKE_20260905.md`). Frozen by the
hub as DM on 2026-09-06 before implementation. Zero training; no learner is purchased by this
object; A objects have no consumption state.

## 1. Question

On the unmodified B02 ordinary evaluation path, does a Python ordinary-decision boundary
correction that sets `renew_now(n) = [current native countdown == 0]` per lane make the flag
the policy consumes at tick n agree with native admission at tick n, and are the resulting
fresh commands incorporated through native's unchanged projection law, on the two A01 windows?

## 2. The correction (frozen contract)

- **Where.** The ordinary wrapper outputs of `NativeBatch` in
  `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py`:
  the initial ordinary observation (`observe`), the ordinary `step`/`rollout` observation and
  `reset_selected`. The observation key `renew` becomes the operational permission derived
  from each lane's current state countdown (`countdown == 0`) without advancing the
  environment; the raw completed-transition flag is retained under a separate key
  (`renew_completed`). Repeated reads do not advance state. The generic decoder
  `_decode_step_outputs`, the prepared/B01 paths (`complete_b01_tick`), source-clone outputs
  and every non-ordinary consumer keep their current meaning; the distinction is explicit in
  the small existing Python boundary, with no registry, compatibility layer or native export.
- **Consumers.** `production_recurrent_trainer.py` `step_rows` (line 311) and the collector's
  fragment fields `renew`, `prepare_mask`, `commit_mask` (lines 506–508) consume the corrected
  `observation["renew"]` unchanged in code; the behaviour-log-probability eligibility follows
  the same flag. Loss, update, normalization, recurrent order and heads unchanged.
- **Native.** No change to `rbhr_r06_production_backend.cpp`: renewal law, projection
  (raw magnitude ≤ 3, change ≤ 1.5, result ≤ 3 per vehicle), preparation latch, intent
  emission, CAS, certificates, ownership, passive labels, reward, energy, terminal handling.
- **Information.** The current countdown is already actor feature 42; the correction grants
  no target truth, private history, future noise or SOURCE payload.
- **Not preserved.** Realized trajectories: fresh motion and proposal sampling move to the
  intended clock; a stochastic run may consume draws at different ticks. This is a declared
  behaviour change, not a bit-identical optimization and not a repair of B02's results.

## 3. Acceptance observation

Inputs: checkpoint `checkpoint_update16.pt` (sha256
`504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`, verified before use),
original normalization, B02 master (`sha256("DISH-FORECAST-PACKAGE-B02/seed/61")`), A03 host.
Two sequential width-one instances with fresh zero recurrent states: TARGET_VISUAL_MASK/K8 and
TARGET_VISUAL_MASK/K4_TO_K12, speed 4, slot 0, block 0, at most the first 32 ordinary ticks
each (the A01 windows); deterministic sampling; FP32 policy, float64 native, one thread. No
rerun of the unmodified arm (A01's rows are the reference). Per live tick retain: consumed
flag, current pre-step countdown and tick, raw completed-transition flag, emitted raw vector,
held vector before and after completion, projected expectation from the independent
`project_command`, proposal outputs, `cas_applied`, owner, service, energy increment, events,
terminal. Counts per window and overall: matched renewals, matched non-renewals, disagreements
of each kind, admissions whose held vector equals the projected emitted command, admissions
whose emitted command equals the previous held vector (value-equal), held-vector changes.

## 4. Reading rule (written before the data; Pro section 3, applied in order)

| Observation | Bounded reading | Consequence |
| --- | --- | --- |
| Zero same-tick permission disagreements; at every admission the held vector equals native's projection of that tick's emitted command (float64 scale); no held change away from admission; value-distinguishing commands incorporated | Local ordinary-renewal/command-delivery correction accepted on the observed windows | Complete the correction intake and the qualified B01/B02 reinterpretation intake; no return gain, calibration, competence or source value claimed; a later learning comparison is separately selected |
| Permission aligns, but every admission command equals the held command | Verified clock relation; limited value-discrimination support | Report as such; no lost-service recovery claim, no forced witness, no automatic expansion |
| A disagreement remains, incorporation differs from the native law, or a protected semantic changed | Dependent correction claim not accepted | Preserve the boundary, return the concrete defect or scope gap; no retraining, no open-ended repair |
| Corrected behaviour causes an early terminal, adverse energy/event outcome or truncates a window | Correct interface with poor behaviour is distinguished from an incorrect interface | Preserve the adverse behaviour and actual live boundaries; no manufactured counts |
| Input unavailable, measurement missing, or the 120 s limit exhausted | Report the precise gap with narrower trustworthy facts | No checkpoint replacement, added run or hidden extension; no scientific negative |

Expected counts if both windows stay live and clocks are unchanged: 12 matched renewals
(4 + 8), 52 matched non-renewals (28 + 24), 0 disagreements. Neither positive service nor
legal transfer is an acceptance condition; A01's 60/64 service ticks are context only.

## 5. Predictions on record

- **Pro:** states the expected counts above as expectations, not results; notes the applied
  commands may be poor and delivery may reduce service or increase energy.
- **DM (hub):** first row. 12/52/0; at every admission after tick 0 the emitted command is
  nonzero and differs from the zero held vector (A01 showed nonzero fresh commands one tick
  late), so the held vector changes at each of the 12 admissions and equals the projected
  command; both windows stay live for 32 ticks; service ticks differ from 60 (direction not
  predicted). Prepare/commit proposals now sample on admission ticks; CAS still 0.
- **Owner:** not taken (unattended).

## 6. Exposure, cost and stop

Zero training instances, optimizer steps, backward calls or parameter updates in the
observation; one checkpoint artifact loaded twice (two policy constructions); ≤ 64 ordinary
native steps and ≤ 64 recurrent forwards; verification work counted separately if the retained
B02 focused checks construct models or use backward. **Complete compute limit 120 s** on the
executing node: imports, native build/load, the one consolidated focused regression invocation,
checkpoint handling, both windows, reduction, publication (shared work charged once). Work law
as in the intake. A01 reference: 0.090 s formal / 0.065 s check runner wall warm, 5.16 s local
check cold; not a matching cost law for the corrected code. Remote-first on `wsl_4070` at the
pushed sha in a detached worktree under `agent-task`, fresh ≥ 4 GiB admission immediately
before each invocation, single thread; local fallback only under §5 of `AGENTS.md`. Stop at the
limit or an actual failure; keep outputs; no retry, no widening.

## 7. Bounded CM objective

`DISH_RENEWAL_BOUNDARY_A02_CORRECTION_CM_OBJECTIVE_20260906.md`. Implementation by Grok Build
in a fenced worktree; the diff is reviewed by `hmasd-reviewer` (shared wrapper and trainer
boundary) and the hub before pathspec commit. Stop condition: the corrected boundary, the
extended measurement entry, the consolidated focused regression passing together with the
existing B02 and A01 tests, and the CM record with frozen `check` and `formal` commands.
