# DISH-RENEWAL-BOUNDARY-A01 result and intake (2026-09-05)

Direction `degraded_incumbent_shadow_handover` (DISH, N3). Card
`DISH_RENEWAL_BOUNDARY_A01_SCIENCE_CARD_20260905.md`; CM record
`DISH_RENEWAL_BOUNDARY_A01_CM_RECORD_20260905.md` (implementation by Grok Build, hub-reviewed,
integrated at `ffa23bf8d551add61fba33e3170b106ae57a2be7`). Intake by the Claude research hub as
Root and DM. Evidence: `a01_renewal_boundary_20260905/{formal,check}/` (rows, summary, run log,
memory receipt), copied from the `wsl_4070` output roots.

## 1. What was checked (observation)

- **Launch facts.** Node `wsl_4070`, worktree `/home/wu/hmasd-worktrees/dish_a01_ffa23bf8d` at
  the pushed launch sha; tasks `dish_a01_check_ffa23bf8d_20260905_01` and
  `dish_a01_formal_ffa23bf8d_20260905_01`, both exit 0, `status COMPLETE`. Memory receipts on
  the node passed both floors before each runner. One invocation per profile; no retry.
- **Frozen input.** `checkpoint_update16.pt` (FORECAST_PACKAGE, seed 61) at the remote B02 output
  root, sha256 `504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`, equal to the
  card and to `b02_20260905/forecast_package.checkpoint.sha256`; the runner verified it.
- **Path integrity.** `forecast_package=True`, `RecurrentRolloutState.fresh("STRUCTURED", 1)`
  per window, `step_rows(sampler=None, deterministic=True)`, one `observe()` per window, the B02
  master (`sha256("DISH-FORECAST-PACKAGE-B02/seed/61")`, identical derivation to `study.py`),
  `torch.set_num_threads(1)`. Parameter norm before and after each window
  `39.149200792042365` (zero movement). Reset phases read back: window 1 = 4, window 2 = 2,
  equal to the card's expectation from the B02 summaries.
- **Counts.** 64 live ticks (32 + 32), no early terminal. Decisive counts, overall:
  native admission with policy renew false **12**; policy renew with native admission false
  **12**; both true **0**; both false **40**; held-command changes **0**. Per window: window 1
  (K8) 4/4/0/24, admissions at t = 4, 12, 20, 28; window 2 (K4) 8/8/0/16, admissions at
  t = 2, 6, …, 30.
- **Command record.** At every native admission tick the policy consumed `renew = 0`, copied the
  held command and emitted `[0, 0, 0, 0]`; native incorporated that zero (held vector stays
  `[0, 0, 0, 0]` for all 64 ticks). At every following tick (t = 5, 13, 21, 29 and
  t = 3, 7, …, 31) the policy consumed `renew = 1` and emitted a nonzero fresh motion vector
  (for example window 1 t = 5: `[-1.1746, 1.3738, 0.7295, -1.0287]`), which native did not
  incorporate (`pre_countdown` 7 or 3, admission false). Prepare/commit proposals were also
  emitted only on those non-admission ticks (`prepare = [1, 0]`, and `commit = [1, 0]` in
  window 2). `cas_applied` stayed 0, owner and actuator owner 0/0 throughout.
- **Tick 0.** Both windows: `observation["renew"] = 0` with countdown 4 and 2 (nonzero), so the
  reset-boundary zero is correct here and contributes nothing to the counts.
- **Telemetry.** Runner wall 0.090 s (formal) and 0.065 s (check) after the native library was
  already built on the node; peak RSS 363 MB and 362 MB; `scratch_unmeasured` true. Well inside
  the 120 s complete-object bound. Service ticks observed 60 of 64; energy increments summed
  8563.59 (context only).
- **Check profile.** Window 1, 4 ticks: countdown 4 → 1, no admission (first K8 opportunity is
  t = 4), counts 0/0/0/4, consistent with the formal rows.

## 2. Rule applied (verbatim from the card, section 6)

> Same-tick flag disagreement with the emitted/held-command record showing the corresponding
> incorporation behavior: The local action-delivery risk is real on that window. No
> unchanged-path tuning or repeat seeds as though delivery were established. Any later
> timing/interface correction is a separately selected object that preserves reward and
> information meaning and is tested through native behavior; B02's raw outcomes are preserved
> and only interpretations dependent on the mismatch are revised through an explicit later intake.

**Reading: branch 1 on both windows.** The flag the policy consumes at tick n is the native
flag of tick n−1; with period k > 1 every fresh command lands one tick after the admission
opportunity and every admission incorporates the copied (here zero) held command. This is not
the value-equal case of branch 3: the fresh commands differ from the held vector at every
renewal tick, and none of them was incorporated.

## 3. Bounding observation and the four boundaries

- **Direct observation:** the 64 rows above, on the unmodified B02 evaluation path with the
  retained FORECAST_PACKAGE checkpoint, on two initial 32-tick windows of two coordinates.
- **Inference, stated as such:** (a) the same `_StepOutput.renew` pass-through feeds the
  training collection (`collect_update` consumes successive ordinary outputs, scout map
  2026-09-05), so the B01/B02 learners very likely trained under the same one-tick lag and, on
  this host's motion path, never had a fresh motion command incorporated in ordinary rollouts;
  (b) B02's identical 470-tick service in both arms is consistent with (a). Neither is measured
  by this A; (a) is the object a later explicit intake must confirm before B01/B02 readings are
  revised. Whether prepare/commit proposals suffer the same lag at their own native gate is not
  resolved here (`cas_applied` never fired in these windows).
- **Scientific result versus engineering conformance:** the result is a measured interface
  discrepancy at the declared class; it is not a service or learning result and does not say the
  learned motion would have helped.
- **Direction-local advice versus Portfolio action:** direction-local; nothing Portfolio-tier.
- **Historical provenance versus current authority:** B01, A01–A05 and B02 remain as recorded;
  the Pro decision's rule above governs what may be revised and how.

Predictions: DM predicted branch 1 with about ⌊32/k⌋ disagreements per window (4 and 8); the
observed counts are exactly 4 and 8. Owner slot: not taken (unattended).

## 4. Decisions this intake produces

1. **Object tier:** accept the complete A01 as a valid branch-1 observation, versus treat it as
   an engineering artefact. Recommend and select the first: the checkpoint, path, counts and
   command records are all direct. Owner-delegated decision (unattended, 2026-09-03
   instruction): **accept, branch 1**. `OWNER_DELEGATED`, technical, reversible, owner flag
   none. A objects have no consumption state.
2. **Object tier:** no local correction, no retraining, no repeat, no widening to other
   coordinates or schedules (card branch 1 and the Pro decision forbid all four). Selected by
   the rule; recorded for completeness.
3. **Direction tier:** the next object (a separately selected timing/interface correction that
   preserves reward and information meaning, the dependent reinterpretation of B01/B02, or a
   different disposition) belongs to `em:degraded_incumbent_shadow_handover:convergence`. The
   hub authors the post-A01 Convergence packet with this intake, the rows and the CM record as
   evidence, sends it once through the Sonnet transport, and parks DISH at this clean
   boundary. Recommendation carried in the packet, not decided locally: one bounded correction
   object on the ordinary path (align the consumed flag with the current native countdown at the
   wrapper boundary without touching reward, information or the native ABI), then re-run the
   same two windows as its acceptance check, before any learner is re-run.

Budget: this object spent under 1 s of runner wall on the node plus build and preflight; the
120 s bound is closed. Ledger rows appended in `docs/research/portfolio/audit/2026-09-06.md`.
