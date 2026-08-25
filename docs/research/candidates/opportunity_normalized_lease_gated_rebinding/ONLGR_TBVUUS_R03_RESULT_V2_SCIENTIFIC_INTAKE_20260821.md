# ONLGR TBVUUS r03 RESULT_V2 scientific intake

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager  
Object: `ONLGR-TBVUUS-R03-FULL-PANEL`  
Science revision: `ONLGR-TBVUUS-SCIENCE-20260821-03`  
Intake disposition: complete; same-Pro result convergence accepted  
Registered result branch: `VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS`

## Intake boundary

The canonical `RESULT_V2` envelope was technically accepted before this
scientific intake. This EM read its analysis payload only after the exact
Root/CM milestone authorized that access. The legacy `RESULT.json` was not
opened, hashed, copied, moved, deleted, quarantined, parsed, or used.

This intake accepts the CM's technical envelope and release provenance as
technical facts. It does not redo technical acceptance, invoke analysis,
change a threshold, select a row, or reinterpret any runtime fact as science.

## Frozen result-map application

The first four ordered preconditions all clear:

- the package, pairing, endpoint, ROAD-fit, and SHAM audits are valid;
- every arm has `5,120` scheduled `t=0` decisions, ROAD/RAW/SHAM each have
  `5,120` action shells, and NEVER has none;
- `4,936` encounters and all `128` replicates contain an effective ROAD patch,
  well above the frozen support floors of `512` and `96`;
- NEVER is competent (`mean=0.87370849609375`,
  `tail=0.838427734375`) and retains the required headroom; and
- ROAD and NEVER have zero registered hard failures, while the paired
  ROAD-minus-NEVER override interval is exactly `[0,0]`, so `ROAD_NONHARM=true`.

The four claim-bearing gates are:

| Gate | Mean | Nominal 95% interval | Sample SD | Frozen status |
|---|---:|---:|---:|---|
| ROAD-minus-NEVER mean | -0.04778320312500001 | [-0.04844332953877, -0.04712307671123001] | 0.0037742077692129042 | `MATERIALITY_RULE_NONPASS` |
| ROAD-minus-NEVER tail | -0.04633789062499999 | [-0.04961886512947887, -0.04305691612052111] | 0.01875864865741959 | `MATERIALITY_RULE_NONPASS` |
| ROAD-minus-SHAM mean | 0.0010717773437499993 | [0.0004137479323603788, 0.0017298067551396196] | 0.003762218364591367 | `MATERIALITY_RULE_NONPASS` |
| ROAD-minus-SHAM tail | 0.0019775390625000003 | [-0.001216802377989227, 0.005171880502989228] | 0.018263332644668135 | `MATERIALITY_RULE_NONPASS` |

All four point estimates fall below their prospectively registered margins
(`0.02` for mean and `0.05` for tail). There is no
`SIGN_POWER_NONIDENTIFYING` gate. Neither pair of required gates passes, so
branches 5, 6, 7, and 8 do not apply. The exhaustive first-match map therefore
registers branch 9, `VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS`, exactly as the
canonical result reports.

The nominal ROAD-minus-RAW contrast is large and positive:

| Endpoint | Mean | Nominal 95% interval |
|---|---:|---:|
| mean | 0.80469482421875 | [0.8032362223069853, 0.8061534261305148] |
| tail | 0.79208984375 | [0.7895271456174157, 0.7946525418825844] |

Under the frozen card, this contrast is descriptive only. It suggests that the
road-constrained patch avoided the severe degradation of the raw two-sample
patch, but it cannot qualify ROAD, select an ingredient, enlarge the claim, or
open a successor.

## Scientific interpretation

For this exact fixed-`t=0` action package, the ROAD payload did not meet either
registered matched-SHAM materiality margin, and the complete ROAD package's
registered mean and tail contrasts against competent NEVER are both negative
with intervals wholly below zero. This is direct evidence about valid target
service for the exact one-shot package; it is not a hard-safety failure and is
not a general claim that target-state updating, timing-dependent control, or
voluntary adaptation is useless.

The strongest surviving alternative is highly local. BOOT-only NEVER is
already competent, the synchronized `t=0` shell imposes a one-second blackout
and buffer clear, and the exact public road registry may chiefly prevent the
catastrophic raw-patch error rather than improve on the incumbent estimate.
The near-zero ROAD-minus-SHAM effects show that the registered ROAD payload
recovers very little value at this instant even after matching the shell.
Other times, degraded-incumbent regimes, map error, computation and packet
costs, terminal energy, replanning, or another estimator law were not tested.

## Claim ceiling and continuation

The result supports only this statement: on the fresh paired coordinates and
frozen analytic host, the exact one-shot ROAD package was valid, supported,
hard-nonharmful, and comparator-identified, but did not satisfy any of the four
prospective utility materiality gates. Its ROAD-minus-NEVER service contrasts
were negative and its ROAD-minus-SHAM payload contrasts were much smaller than
the registered margins. ROAD remained far better than the nominal RAW patch.

It does not establish equivalence, absence of every smaller payload effect,
physical harm, optimal timing, repeated-action value, route heterogeneity,
arbitrary or adaptive `k`, variable `N`, real-aircraft transfer, safety
certification, deployment value, or general algorithm superiority.

Because only `ROAD_PATCH_DIRECT_UTILITY_QUALIFIES` could make the frozen
`ROAD-PATCH GLOBAL-TIME vs TWO-STRATUM-TIME` successor eligible, that timing
successor is not eligible. No rerun, retune, threshold change, alternate row
selection, or same-coordinate follow-up is scientifically authorized.

The same-conversation Pro convergence confirms the direction-level
recommendation of no current empirical investment in this ROAD-PATCH family. A
future revisit would require an independently motivated mechanism change or
new failure regime that can prospectively explain a material payload advantage
over matched SHAM; it would be a new direct-value object, not a rescue of this
screen.

## Exact sources

- Frozen science card:
  `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_SCIENCE_CARD.md`
- Same-Pro closure intake:
  `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_EXTERNAL_PRO_CLOSURE_INTAKE.md`
- CM result-v2 technical acceptance:
  `temp/handoffs/code_manager_to_explorer/ONLGR_TBVUUS_R03_CM_RESULT_V2_TECHNICAL_ACCEPTANCE_20260821.md`
- Authorized canonical result:
  `C:/Projects/HMASD/artifacts/onlgr_tbvuus_r03_full_panel_20260821/RESULT_V2.json`
- Same-Pro convergence intake:
  `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TBVUUS_R03_EXTERNAL_PRO_RESULT_CONVERGENCE_INTAKE_20260821.md`
