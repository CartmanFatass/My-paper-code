# Science card: DISH-RENEWAL-BOUNDARY-A01 (A/RECON, ordinary policy-to-native renewal boundary)

Direction `degraded_incumbent_shadow_handover` (DISH, N3). Frozen 2026-09-05 by the Claude
research hub (Root and DM) from the `PRO_FINAL` post-B02 Convergence decision
(`DISH_POST_B02_CONVERGENCE_INTAKE_20260905.md`; archived response
`pro_packets/20260905_post_b02_convergence/archive/RESPONSE.md`, commit
`bc0808401af81c367b560cd553497707b8c682dd`). Card wording is the DM's under the unattended
delegation; the object, its inputs, measurement and bound are the Pro node's selection and are
not changed here. Static facts cited below come from the hub's read-only scout of 2026-09-05
(`file:line` against `main` at d34f06fb6).

## 1. Question and class

**Question.** On the unmodified B02 ordinary evaluation path, does the top-level `renew` flag the
retained policy actually consumes at primitive tick n agree with the native command-update
opportunity at that same tick, and which motion command does the native step actually
incorporate?

**Class.** `A/RECON`, seedless, one retained controller configuration, no treatment/control
effect. Zero training, zero optimizer steps, zero backward, zero passive-label work, zero
new learners. A objects have no consumption state (evidence spec §6.1, §11.1).

**Claim ceiling.** An observed agreement, disagreement or uninformative boundary on two fixed
32-tick windows, with the corresponding command records. Not a performance result, not a
training diagnosis, not an equivalence theorem, not a qualification of later switched periods
or other coordinates, and not a B02 reinterpretation by itself (a dependent reinterpretation is
a later explicit intake).

## 2. Binding structure (what is fixed)

- **Host and path.** The accepted A03 ground-terminal host and the B02 ordinary evaluation
  path exactly as `forecast_package_b02/study.py` runs it: initial `native.observe()`
  (`study.py:126`), then per tick `policy.step_rows(observation, sampler=None,
  global_tick=tick, deterministic=True)` → `native.step(rows)` → `apply_native_promotion`
  (`study.py:131-150`). Same call order, deterministic sampling (`sampler=None` is never
  dereferenced; no RNG is consumed), FP32 policy, float64 native state, `torch.set_num_threads(1)`,
  original host law, role mapping and thresholds.
- **Retained policy.** The seed-61 FORECAST_PACKAGE final update-16 checkpoint
  (`checkpoint_update16.pt`, sha256 `504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`,
  recorded in `b02_20260905/forecast_package.checkpoint.sha256`), loaded with
  `forecast_package=True` and its original Welford normalization from the checkpoint; two fresh
  `RecurrentRolloutState.fresh("STRUCTURED", width=1)` instances, one per window, used
  sequentially. Not an earlier, best or newly fitted checkpoint; `optimizer` never used.
- **Windows.** Two original B02 coordinates, each the first 32 ordinary native ticks from the
  B02 reset (tick 0 included), built by the existing `_reset_row(master, coordinate)` with the
  B02 master:

  | Window | Coordinate (`EvaluationCoordinate(0, regime, schedule, "SPEED_4", 0)`) | Expected reset phase (B02 summary) |
  | --- | --- | ---: |
  | 1 | TARGET_VISUAL_MASK / K8 | 4 |
  | 2 | TARGET_VISUAL_MASK / K4_TO_K12 | 2 |

  The phase is read back from the actual reset row and reported; a different value is reported,
  not corrected. The windows stop before the K4-to-K12 switch and before degradation onset.
- **Measurement (one compact row per live tick, both windows).** Policy side: observation tick
  and top-level `observation["renew"]` as consumed by `step_rows`
  (`production_recurrent_trainer.py:311`), emitted `raw_action` and prepare/commit proposals.
  Native side, from a `.copy()` of `_State` taken immediately before the `step()` call and a
  second read immediately after: pre-step `tick`, `countdown`, `k_active`, `k_epoch`, `owner`,
  `actuator_owner`; held motion `a` before and after the step; the native command-admission
  Boolean for this tick defined as `pre-step countdown == 0` (the same predicate native uses,
  `rbhr_r06_production_backend.cpp:510` and `:432`); the returned `_StepOutput` fields
  `renew`, `service`, energy increment, legal-transfer and hard-event indicators, `terminal`.
  Reads go through the existing `native_state(batch)` access (`study.py:51-52`); no native ABI
  change.
- **Decisive counts.** Over the 64 live ticks: native renewal with policy renewal false; policy
  renewal with native renewal false; matched renewal; matched non-renewal. For every tick with
  either flag true, the record keeps the emitted command, the held command before and after,
  and whether the held command changed and to what value (floating-point differences at their
  actual scale; no universal epsilon).
- **Protected.** No refresh, replacement or reconciliation of the flag; no A03 prepared path;
  no extra native tick; no forced nonzero command; no injected readiness or ownership; native
  state copied for measurement only, never supplied to the policy; no change to
  `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/` (shared by every DISH
  attempt) or to `forecast_package_b02/study.py` and the B01 helpers it imports.

## 3. Minimum effect of interest

Integer timing measurement: the useful resolution is **one actual decision-tick discrepancy**
together with its command consequence. No service MEI applies; B02's +24-tick scale and B01's
source-effect scale are untouched.

## 4. Static facts on record before execution (not results)

- `renew` is computed once per native step as `countdown == 0` before the countdown is
  advanced (`:510`, `:432`, advance at `:494`), and the command from `raw_action` is written into
  the held vector `a` only under that predicate (`:472`). The returned `_StepOutput.renew` is
  therefore the flag of the transition just completed. Python passes it through unchanged
  (`production_backend.py:157`, `:299`, `:715`); `step_rows` gates fresh emission on it and
  otherwise copies the held command out of the observation (`production_recurrent_trainer.py:311-326`).
- At reset, `reset_one` zero-fills the output and never sets `out.renew`, so the first
  observation reports `renew = 0` whatever the initial countdown (`:381-393`), while the embedded
  actor-row feature uses the true predicate.
- These are readings of the source, not measurements. They motivate the DM prediction below and
  are exactly what the object tests.

## 5. Predictions on record

- **DM (hub), before execution:** branch 1 on both windows. Reason: the flag consumed at tick n
  is the flag of tick n−1, so with period k > 1 the policy emits a fresh command on the tick
  after each native renewal opportunity and copies the held command on the opportunity itself;
  the counts "native renewal with policy renewal false" and "policy renewal with native renewal
  false" should each be about ⌊32/k⌋ per window (≈4 for K8, ≈8 for K4 in window 2's first 32
  ticks), with the held command changing to the *previous* emitted value at each opportunity.
  Confidence: high on the sign of the discrepancy, moderate on the exact counts (phase and
  early-terminal effects). If the counts are zero, the static reading above is wrong somewhere in
  the wrapper and the object has done its job.
- **Owner prediction slot:** `not taken (unattended)`; may be filled through the owner item.

## 6. Reading branches (prospective, from the Pro decision)

| Observed pattern | Consequence |
| --- | --- |
| Same-tick flag disagreement with the emitted/held-command record showing the corresponding incorporation behavior | The local action-delivery risk is real on that window. No unchanged-path tuning or repeat seeds as though delivery were established. Any later timing/interface correction is a separately selected object that preserves reward and information meaning and is tested through native behavior; B02's raw outcomes are preserved and only interpretations dependent on the mismatch are revised through an explicit later intake. |
| Flags agree at all observed live boundaries and native command handling is consistent with the current input | The timing hypothesis is not supported on the covered initial windows. End this A; no automatic expansion to every phase, schedule or history. A specifically justified B may then address objective scale or behavioral learning. No entitlement to scale B02 unchanged. |
| Flag disagreement but emitted commands equal held commands | Report the interface discrepancy; claim no measured lost service or command-value effect. Identifies which timing contract a prospective comparison must state. |
| Early native terminal, unavailable checkpoint, missing required readout, or time/scope exhaustion | Preserve actual exposure and trustworthy narrower facts; state exactly which boundary remains unobserved. No checkpoint replacement, longer trajectory, new training, automatic retry or expanded diagnostic programme. |

No branch requires positive service, legal transfer or a favorable diagnosis. Zero service in
the windows does not invalidate the timing observation. Completion ends the purchase in every
branch.

## 7. Cost and bound

Work: at most 64 ordinary native steps, 64 recurrent forwards, two policy constructions with one
checkpoint load each, two resets; expected parameter movement zero (report before/after norms).
**Complete compute spending bound: 120 s wall on the executing node** for the whole object,
including any native build, checkpoint load, the one focused measurement-output check, the two
windows, reduction and publication; shared work charged once across scripts. This is a limit,
not a projection; the CM records the projection from measured terms. Telemetry: complete wall,
peak RSS; missing telemetry marks the run `resources_unmeasured` and does not invalidate it.
Exposure line: zero new models trained, zero training transitions, zero optimizer steps; the
consultation itself had zero exposure.

## 8. Execution

Remote-first on `wsl_4070` under `agent-task` with the memory preflight joined by `&&`
immediately before the runner, detached, from a pushed launch sha; a local Windows run is
permitted only under the §5 fallback (the native extension builds under MSVC, so portability is
not the blocker, but no remote refusal exists). Launch conditions are evidence-spec §11.4 only:
§4 integrity, the exposure line, the receipt on the executing node; nonzero learner counts do not
apply to a seedless A. Owned paths: a new sibling module under
`experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/`
(for example `renewal_boundary_a01.py`), one entry `scripts/run_dish_renewal_boundary_a01.py`,
tests under `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/`,
records under this direction folder.

## 9. What technical success cannot establish

That the learned motion would have improved service; that B02's null is explained; that any
other coordinate, later schedule switch, training lane or historical execution behaves the same;
that a correction is warranted or how it should look; SHADOW value or handover feasibility.
