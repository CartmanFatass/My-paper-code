# DISH forecast package B03 — result intake (2026-09-06)

Object `DISH-FORECAST-PACKAGE-B03` (B/EXPLORE, card
`DISH_FORECAST_PACKAGE_B03_SCIENCE_CARD_20260906.md`). Both arms completed on `wsl_4070` from
exact committed and pushed source `ad01757c43cb3a3df6549b024367b5f9307246b8` in the detached
worktree `/home/wu/hmasd-worktrees/n3-b03-20260906`, output root
`temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b03_20260906_r3/`
(node), copied to `b03_forecast_package_20260906/` here (both `summary.json`, `/usr/bin/time`
records, admission receipts, launch scripts, checkpoint hashes). CM record
`DISH_FORECAST_PACKAGE_B03_CM_RECORD_20260906.md`. DM: the Claude research hub. Decision
authority for this intake: object tier, `OWNER_DELEGATED` (unattended, 2026-09-03 instruction).

## 1. Execution facts (observation)

- Shared preparation (task `n3_b03_focused_20260906`): B02 + B03 focused tests on the node,
  `21 passed in 4.37s` including `test_package.py`; `C = 4.94 s`, charged 2.47 s per arm; admission
  14.6 GiB physical and effective.
- Two CONTROL launch attempts failed before any RNG, model or learner work (an operator SSH
  quoting defect; then `ModuleNotFoundError: experiments` at 2.48 s because the objective's frozen
  command omitted `PYTHONPATH`, which B02's commands had set). Both records are preserved under
  `forecast_package_b03_20260906/` on the node; no exposure, no polarity. Attempt 3 is the
  object's single complete invocation per arm.
- CONTROL (task `n3_b03_control_20260906_r3`, PID 1956772, 17:19:30Z): exit 0, `/usr/bin/time`
  wall 211.04 s, runner pre-publication wall 196.83 s, CPU 214.38 s, peak RSS 625.9 MB.
- FORECAST_PACKAGE (task `n3_b03_forecast_package_20260906_r3`, PID 2064720, 17:27:03Z,
  launched after the CONTROL summary was `COMPLETE`): exit 0, wall 196.18 s, pre-publication
  185.55 s, CPU 203.98 s, peak RSS 628.3 MB.
- Both arms: seed 73, master `b938a93e7b41…`, `renewal_boundary` recorded as corrected
  (`3f4d447f6`), initial model norm 38.2499630 identical; 65,536 ordinary training transitions,
  16 updates, 512 optimizer steps, `next_mask` 65,504, 4,800 evaluation ticks each; every loss
  and gradient norm finite; checkpoints `0ca1bb23…` (CONTROL) and `330ee804…` (package) retained
  on the node. Summed pair charge 211.04 + 196.18 + 4.94 = 412.16 s of the 3,600 s ceiling.
- Telemetry: wall, CPU and RSS measured; scratch unmeasured (`resources_unmeasured`, telemetry
  rule; no resource claim is made).

## 2. Frozen rule applied verbatim and the observed readout

Card §4: "`Delta_B03 = (1/4) Σ_r (J[FORECAST_PACKAGE,r] − J[CONTROL,r])` over the four paired
rows, no trigger or sign filtering. Publish both arm means and the four paired differences;
retain energy, the seven hard-event categories, terminal outcomes, ordinary legal transfer
counts and service before/after any transfer."

| Development condition (speed 4, slot 0, block 0) | CONTROL service | Package service | Difference | CONTROL energy | Package energy | Package hard events |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| TARGET_VISUAL_MASK / K8 | 452 | 92 | −360 | 271,451.68 | 257,479.80 | none |
| TARGET_VISUAL_MASK / K4_TO_K12 | 458 | 222 | −236 | 276,468.20 | 258,068.76 | none |
| TERRAIN_RELAY_MASK / K8 | 449 | 129 | −320 | 270,979.28 | 259,524.08 | none |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 483 | 311 | −172 | 274,347.34 | 262,414.77 | invalid_commit 17, separation_breach 1 |

`Delta_B03 = −272.0` mean service ticks (CONTROL mean 460.5, package mean 188.5) against MEI
+24. All eight episodes stepped 1,200 ticks to the fixed horizon; the package's TERRAIN
K4_TO_K12 episode also records a native `separation_below_15` cause at the horizon (final
separation 14.71) with one `separation_breach` and 17 `invalid_commit` events; CONTROL has zero
hard events in every row. No legal transfer in any row; all service is pre-transfer,
incumbent-only. Package energy is 4–7 % lower per row than CONTROL.

Training-side observations (both arms, per-update training service over 32 lanes × 128
ticks):

| Update | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CONTROL | 4016 | 3392 | 2034 | 1891 | 1435 | 1017 | 1011 | 1044 | 850 | 2764 | 4093 | 3812 | 2208 | 883 | 483 | 435 |
| Package | 4016 | 3417 | 2297 | 2037 | 1635 | 781 | 238 | 251 | 571 | 2684 | 3800 | 1833 | 457 | 376 | 958 | 1340 |

Update 1 is identical (same initial parameters, same exogenous streams). Both arms' training
service falls from 4,016 of 4,096 lane-ticks to a few hundred by update 16; the update-10
collection rises in both (a reset boundary, `next_mask` 4,064). The package's mean loss and
gradient norm explode at updates 2 and 10–13 (loss 60,428 → 6.54 M; gradient norm 1.71 M) and
recover to O(30) by update 15; CONTROL's peak gradient norm is 875 at update 10. Service-label
eligible transitions: CONTROL 18,775, package 7,972. Parameter displacement: CONTROL L2 8.61
(relative 0.225), package 7.51 (0.196); training legal transfers 1 (CONTROL) and 0; training
`invalid_commit` 2,184 (CONTROL) and 1,275; 32 training terminals each.

## 3. Reading under the card's rule

Card §5, third row, is first applicable: **"adverse service, hard events or an adverse
energy/service tradeoff stay adverse whatever a proxy shows."** The package loses 172–360
service ticks on every development condition, the mean loss is 11 times the MEI, and the only
hard events of the pair occur in the package arm; the package's lower energy is a proxy that
does not offset lost service. The result is **ADVERSE for the joint forecast package at this
exposure**, from one paired training replicate on four development conditions; it does not
scale the package and it buys no further seeds for the unchanged package.

What it is not: not an equivalence claim, not stable inferiority (one seed), not component
attribution (the NLL term and the sigmoid interface enter together; the package's loss
explosions at updates 2 and 10–13 are observed, their cause is not localized), not a claim
about the boundary correction's own service value, and not a reinterpretation of B02 (whose
inside-MEI observation stands as an outcome of the executed lagged interface; B03 and B02 are
not two replicates of one algorithm).

Independently trustworthy narrower facts, reportable at their own ceiling:

- Both arms lose training service monotonically-ish from a near-saturated update 1 (98 % of
  lane-ticks) to 10–33 % by update 16, and both final checkpoints serve 38–40 % (CONTROL) and
  8–26 % (package) of the 1,200-tick horizon. On the corrected boundary, sixteen PPO updates at
  3e-4 make the inherited learner worse at service than its initialization on this host, in
  both arms. This is an observation about the learner and objective, not a B03 primary claim.
- The package's `service_label_eligible` count is 42 % of CONTROL's, so the sigmoid interface
  changes how often the native service label fires during training, an actual-support fact
  recorded without a threshold.
- B02's 337 s / 299 s remain planning references; B03 cost 211 s / 196 s at 16 updates.

## 4. Predictions scored

- Node's prospective judgement (card §5): "a ≥ +24 package advantage has no reliable prior;
  inside-MEI, mixed or adverse outcomes are serious" — consistent; adverse observed.
- DM primary prediction (inside-margin or heterogeneous, |Delta_B03| < 24, mixed signs): **wrong**;
  all four rows are strongly negative. The DM's competing prediction (package gain ≥ 24 driven by
  the incumbent): wrong.
- Owner prediction: not taken (unattended).

## 5. Decisions this intake produces

- Object tier (`OWNER_DELEGATED`, unattended): **(a) accept the B03 pair as a valid adverse
  result** and record it; do not launch further seeds for the unchanged package; do not launch a
  package variant (that would be a new outcome-informed B, a direction-tier choice). Alternatives
  listed: (b) treat the package's loss explosions as a defect and quarantine the arm (rejected:
  every loss and gradient norm is finite, the run completed the frozen work, the card names
  non-finite values as the failure condition, and an explosion is a property of the treatment at
  this coefficient, not an instrumentation failure); (c) run a second seed (rejected by the
  card's adverse row). Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
- Direction tier: the family's next object goes to `em:dish:convergence` with this result, the
  both-arms-degrade-from-initialization observation, and B02's qualified reading; the DM's
  options for the node: end the forecast-package family (no further package variants at this
  exposure); an outcome-informed learner-stability object on the corrected boundary (the
  training-service collapse in both arms is the larger fact); or park. Recommendation to be
  argued in the packet, not decided here.
- Portfolio: no change. DISH stays `ACTIVE`/MEDIUM.

Owner brief (Chinese): `docs/research/portfolio/owner/briefs/degraded_incumbent_shadow_handover/2026-09-06_B03-result.md`.

scope: none
