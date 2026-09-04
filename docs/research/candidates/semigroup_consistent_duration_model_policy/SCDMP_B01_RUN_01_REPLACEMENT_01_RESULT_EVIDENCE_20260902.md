# SCDMP B01 result — `RUN-01-REPLACEMENT-01-ATTEMPT-01` (2026-09-02)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the frozen contract
`SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md` after the owner-approved section 11
recast recorded in `SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md`.

**Question.** Conditional on two prespecified, independently trained, competent graph/order-erased
foundations; six first-eligible treatment-common reachable public states under identity pre-event
`p` and one constrained-balanced latent-`q` prefix pattern; external `k ∈ {7, 13}`; and fresh
held-out paired disturbance tapes — do development-selected graph-matched first actions show a
repeatable positive native full-mission return gap over both the order-swapped mapping and the
strongest development-selected graph-blind common action?

**Claim ceiling: `B/EXPLORE`.** Everything below is a direct observation on the actually observed
panel. Nothing here establishes stable superiority, a seed-superpopulation effect, a `q` main
effect or interaction, learned graph recognition, duration-policy or semigroup value, generality in
state / `k` / foundation, transfer beyond the named simulator, or any lifecycle decision. The card
supplies the reading rule and this document does not go past it.

| Fact | Value |
| --- | --- |
| Study family | `SCDMP-MF-RS-MK-ORDER-VALUE-B01` |
| Named base run | `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01` |
| Evidence attempt | `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01` |
| Launch commit sha (HEAD at launch) | `c5c1655e91b2f021bf4491f65265113680cf9649` — "Turn the SCDMP receipt and telemetry gates into recorded fields" |
| Working-tree cleanliness at launch | `git status --porcelain` over `experiments/candidates/scdmp_variable_k`, `scripts/run_scdmp_mf_rs_mk_b01.py`, `tests/experiments/candidates/scdmp_variable_k`, `docs/research/candidates/semigroup_consistent_duration_model_policy` returned **nothing**. Other, unrelated directions were dirty (a concurrent session) and were not touched |
| Source-identity base commit | `dbd85cbe98bc8705cc5dc0ea72eb20480551e167`; owned-tree aggregate `043270bca13044a7af86c4fc88553e58745f22dcd325d547990de1dfc397414b`; `git diff` 317,550 B, sha256 `d0059b2f36e7e6f2f336eb8a26f45e5996bff83b5c74e5308b8ed54edd69f621` |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, device CPU |
| Machine | Windows 10.0.26200, AMD64 Family 25 Model 117 Stepping 2 (AuthenticAMD), 16 logical CPUs |
| Native host | `mf_rs_native.cpp` 19,286 B sha256 `94ed52b6…f086ed`; DLL 146,432 B sha256 `c57aa75d…2a8a5`; MSVC `/nologo /std:c++20 /O2 /EHsc /LD /W4`, x64, ABI version 3, max batch width 144 |
| Result root (gitignored) | `temp/directions/semigroup_consistent_duration_model_policy/exp/RUN-01-REPLACEMENT-01/SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01` |
| Ordered branch published | **`PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL`** (branch 5 of 8), `complete_full_chain: true` |

---

## 1. The recast in force, and what it changed about this launch

Per owner decisions 1 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`:

- the `PERFORMANCE_READY` receipt is **not** a launch condition. No receipt exists; the run was
  launched with `--performance-assessment temp/scdmp-b01/A-R2/assessment.json` and the assessment
  was recorded, not enforced;
- missing resource telemetry would have been recorded as `resources_unmeasured: true`, not
  quarantined. It did not arise: telemetry was fully measured;
- the fresh `4 GiB` physical/effective admission remained a launch condition and passed twice
  (§2).

### The assessment recorded (a field, not a gate)

`<root>/performance-assessment.json`, verbatim:

```json
{"assessment_id":"SCDMP-MF-RS-MK-ORDER-VALUE-B01-A-R2","assessment_note":null,"assessment_path":"C:\\Projects\\HMASD\\temp\\scdmp-b01\\A-R2\\assessment.json","assessment_performance_readiness":"REVIEW_REQUIRED","assessment_projection":{"conservative_projected_total_seconds":350.1191929995366,"fixed_overhead_seconds":60.0,"formula":"sum(measured_stage_wall * fixed_full_missions / measured_missions * 2.0) + 60.0","margin_to_1800_seconds":1449.8808070004634,"projected_work_seconds":290.1191929995366},"assessment_status":"PERFORMANCE_OBSERVATION_COMPLETE","gating":false,"initial_telemetry_unmeasured_reason":null,"ordered_branch":null,"readiness_receipt_note":"not_supplied","readiness_receipt_path":null,"readiness_receipt_status":null,"recorded_only_reason":"evidence spec 11.4: a performance readiness capacity gate may not hold a B launch","run_01_performance_disposition":"REPAIR_REQUIRED","schema":"SCDMP_MF_RS_MK_B01_PERFORMANCE_ASSESSMENT_V1","scientific_polarity":null,"section11_recast_record":"docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md"}
```

The disposition is `REVIEW_REQUIRED` and the pre-recast constant
`RUN_01_PERFORMANCE_DISPOSITION = "REPAIR_REQUIRED"` is recorded beside it. Neither held the
launch. The A-R2 projection of `350.119` s against the 1,800 s cap is recorded as reviewer
evidence only; §6 gives the measured wall.

## 2. Resource admission (a launch condition, unchanged)

Two admissions, both passing, `MINIMUM_AVAILABLE_MEMORY_BYTES = 4 GiB`,
`measurement_source: GlobalMemoryStatusEx`:

| Receipt | `assessed_at` | available physical = effective | `passed` |
| --- | --- | ---: | --- |
| Standalone preflight, `…/RUN-01-REPLACEMENT-01/preflight.json` | 2026-09-02T21:55:11.321370Z | 14,472,634,368 B (13.48 GiB) | `true` |
| Invocation admission taken by the runner immediately before any root, master, model or checkpoint, sealed at `<root>/admissions/invocation-000000.json` | 2026-09-02T21:55:29.522196Z | 14,285,918,208 B (13.30 GiB) | `true` |

Command for the first:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py admit-memory \
  --out temp/directions/semigroup_consistent_duration_model_policy/exp/RUN-01-REPLACEMENT-01/preflight.json
```

## 3. Command actually run

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_scdmp_mf_rs_mk_b01.py --run-01 \
  --receipt      .../exp/RUN-01-REPLACEMENT-01/admission.json \
  --result-root  .../exp/RUN-01-REPLACEMENT-01/SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01 \
  --confirm-run-id SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01 \
  --performance-assessment temp/scdmp-b01/A-R2/assessment.json
```

with `TMPDIR`/`TEMP`/`TMP` set to `…/exp/RUN-01-REPLACEMENT-01/native-tmp` (deviation D2, §9).
`frozen_argv` and `frozen_cwd` in `<root>/attempt-header.json` record this invocation exactly.

### Sealed identity

| Field | Value |
| --- | --- |
| `q_counter_u64` | `11991974222275696420` |
| `q_pattern_index` | `0` |
| **Realized `q_by_cell`** | **`001110`** — `k7-early 0, k7-middle 0, k7-late 1, k13-early 1, k13-middle 1, k13-late 0` |
| Counter address | `["SCDMP-MF-RS-MK-ORDER-VALUE-B01", "RUN-01-REPLACEMENT-01", "PRE_EVENT_Q_PATTERN", 0]`, `draw_count: 1`, `redraw_allowed: false` |
| `pre_event_p` | `(1, 2, 3, 4)` (identity) on every prefix tick |
| HR post-event `(p, q)` | `((4, 2, 1, 3), 1)` |
| RH post-event `(p, q)` | `((1, 4, 2, 3), 0)` |
| Master commitment | `2c50adc54129b8e883b86b03b083eeb391aad359eed5e1b5ee69f17346e3993f` |
| Card revision bound | `SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901` |

Every statement below is conditional on the realized six-bit vector `001110`, as the card's claim
ceiling requires.

## 4. Foundation competence (card :201-211) — both foundations qualify

`<root>/foundation-competence-gate.json`: `passed: true`, `complete: true`.

| Seed | HR `k`=7 | HR `k`=13 | RH `k`=7 | RH `k`=13 | pooled | any one failure family |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1709 | 32/32 | 32/32 | 32/32 | 32/32 | **128/128** | 0 |
| 2903 | 32/32 | 32/32 | 32/32 | 32/32 | **128/128** | 0 |

Thresholds were ≥ 24/32 per cell, ≥ 109/128 pooled, ≤ 12/128 in any one physical-failure family,
every record terminal / finite / evaluator-valid. Observed failure counts across
`boundary_contact`, `cable_overload`, `swing_envelope_loss`, `formation_loss` were `0` for both
foundations. The run therefore did not stop at `FOUNDATION_COMPETENCE_NOT_ESTABLISHED`.

## 5. Nine-point fixed learning curves (32 missions per point, 8 per graph-by-`k` cell)

Mean endpoint `U = 1{safe dock} · (1 − dock_tick/364)`; these evaluations never select a
checkpoint.

**Seed 1709**

| Update | mean `U` | `k`=7 | `k`=13 | safe docks |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.000000 | 0.000000 | 0.000000 | 0/32 |
| 20 | 0.000000 | 0.000000 | 0.000000 | 0/32 |
| 40 | 0.018887 | 0.021120 | 0.016655 | 32/32 |
| 60 | 0.046446 | 0.047390 | 0.045501 | 32/32 |
| 80 | 0.023008 | 0.025069 | 0.020948 | 32/32 |
| 100 | 0.013221 | 0.016312 | 0.010130 | 26/32 |
| 120 | 0.036745 | 0.038977 | 0.034512 | 32/32 |
| 140 | 0.022579 | 0.023352 | 0.021806 | 32/32 |
| 160 | 0.026614 | 0.027988 | 0.025240 | 32/32 |

**Seed 2903**

| Update | mean `U` | `k`=7 | `k`=13 | safe docks |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.000000 | 0.000000 | 0.000000 | 0/32 |
| 20 | 0.046617 | 0.046188 | 0.047047 | 32/32 |
| 40 | 0.014166 | 0.019918 | 0.008413 | 22/32 |
| 60 | 0.047390 | 0.047734 | 0.047047 | 32/32 |
| 80 | 0.046961 | 0.047218 | 0.046703 | 32/32 |
| 100 | 0.047476 | 0.047905 | 0.047047 | 32/32 |
| 120 | 0.046703 | 0.046360 | 0.047047 | 32/32 |
| 140 | 0.047218 | 0.047905 | 0.046532 | 32/32 |
| 160 | 0.047562 | 0.048077 | 0.047047 | 32/32 |

Both curves are non-monotone; seed 1709 dips at update 100 (26/32 docks) and ends below seed 2903
(0.026614 versus 0.047562) while both pass the update-160 competence gate at 128/128. The card
forbids checkpoint selection and none occurred: the assay checkpoint is update 160 for both.

## 6. Six reachable public-state twins

All six were established; no `REACHABLE_STATE_PANEL_NOT_ESTABLISHED`.

| Cell | `k` | target tick | source seed | first legal boundary tick | nominal | candidate index used | `p_pre` | `q_pre` | persistent twin bytes equal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `k7-early` | 7 | 64 | 1709 | 70 | 70 | 0 | `(1,2,3,4)` | 0 | `true` |
| `k7-middle` | 7 | 160 | 2903 | 161 | 161 | 0 | `(1,2,3,4)` | 0 | `true` |
| `k7-late` | 7 | 256 | 1709 | 259 | 259 | 0 | `(1,2,3,4)` | 1 | `true` |
| `k13-early` | 13 | 64 | 2903 | 65 | 65 | 0 | `(1,2,3,4)` | 1 | `true` |
| `k13-middle` | 13 | 160 | 1709 | 169 | 169 | 0 | `(1,2,3,4)` | 1 | `true` |
| `k13-late` | 13 | 256 | 2903 | 260 | 260 | 0 | `(1,2,3,4)` | 0 | `true` |

Every cell retained its **first** legal boundary on its **first** source candidate (1 of the ≤ 8
permitted scans), and every observed boundary tick equals the card's nominal
`70/161/259` (`k`=7) and `65/169/260` (`k`=13). Post-`LEVEL_RELEASE` public/persistent twin bytes
were equal in all six cells.

## 7. Development-split action construction (18 actions × 8 development tapes × 2 graphs × 12 units)

Tie rule as frozen: `maximum_mean_then_smallest_native_action_index`. The map was frozen
atomically before any held-out tape namespace was opened.

| Seed | State | `k` | `A_HR` | `A_RH` | `C` | distinct | HR top-two margin | RH top-two margin | first/second-half winner agreement |
| ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1709 | `k7-early` | 7 | 10 | 12 | 1 | yes | 0.000343407 | 0.000686813 | HR yes / RH yes |
| 1709 | `k7-middle` | 7 | 10 | 12 | 1 | yes | 0.000343407 | 0.000343407 | yes / yes |
| 1709 | `k7-late` | 7 | 10 | 12 | 12 | yes | 0.000343407 | 0.001373626 | yes / yes |
| 1709 | `k13-early` | 13 | 10 | 12 | 12 | yes | 0.000686813 | 0.000686813 | yes / yes |
| 1709 | `k13-middle` | 13 | 10 | 12 | 10 | yes | 0.000686813 | 0.000000000 | yes / yes |
| 1709 | `k13-late` | 13 | 10 | 12 | 1 | yes | 0.000000000 | 0.000343407 | yes / yes |
| 2903 | `k7-early` | 7 | 10 | 12 | 1 | yes | 0.000686813 | 0.000000000 | yes / yes |
| 2903 | `k7-middle` | 7 | 10 | 12 | 1 | yes | 0.000343407 | 0.000000000 | yes / yes |
| 2903 | `k7-late` | 7 | 10 | 12 | 12 | yes | 0.000000000 | 0.000343407 | yes / yes |
| 2903 | `k13-early` | 13 | 10 | 12 | 1 | yes | 0.000343407 | 0.000343407 | yes / yes |
| 2903 | `k13-middle` | 13 | 10 | 12 | 10 | yes | 0.000686813 | 0.000686813 | yes / yes |
| 2903 | `k13-late` | 13 | 10 | 12 | 0 | yes | 0.000000000 | 0.000343407 | yes / yes |

`A_HR ≠ A_RH` in all twelve crossed units, so the run did not stop at
`ACTION_CONSTRUCTION_NONDISCRIMINATING`. **Direct observation, recorded without interpretation:**
the selected pair is the *same* pair in every unit — `A_HR = 10` and `A_RH = 12` for both seeds,
both `k` values and all six states. The common action varies (`1` in six units, `12` in three,
`10` in two, `0` in one). Several top-two margins are exactly `0.0`, i.e. the winner was fixed by
the smallest-index tie rule.

### FCEOV continuity diagnostics (actions 0, 10, 12) — output-disconnected

The card requires their development ranks, top-action gaps and whether the new mapping reproduces
the old triple. Across all 24 (unit × graph) development cells: action 10 ranked **1st under HR in
every cell** and 13th under RH in every cell; action 12 ranked **1st under RH in every cell** and
14th under HR in every cell; action 0 ranked between 3rd and 11th and never won. Its gap to the
top action ranged from `0.0177129` to `0.0398352`. So the new mapping reproduces two of the three
old FCEOV actions (10 and 12) as the graph-specific winners and does not reproduce action 0 as any
winner. These create no gate and activate no branch.

## 8. Held-out matched / swapped / common comparison (16 tapes × 12 units = 192 tape units, 1,152 raw cells)

Per the card: `M = ½[U(HR,A_HR)+U(RH,A_RH)]`, `X = ½[U(HR,A_RH)+U(RH,A_HR)]`,
`C = ½[U(HR,C)+U(RH,C)]`, `delta_swap = M − X`, `delta_common = M − C`.

**Arm-level raw cells (384 per arm):**

| Arm | mean `U` | safe docks | timeouts | cells with a failure family |
| --- | ---: | ---: | ---: | ---: |
| MATCHED | 0.062893 | 384/384 | 0 | 0 |
| SWAPPED | 0.000000 | 0/384 | 0 | 384 (all `cable_overload`) |
| COMMON | 0.036866 | 304/384 | 0 | 80 (all `cable_overload`) |

**Per foundation (96 tape units each):**

| Seed | `M` | `X` | `C` | `delta_swap` | `delta_common` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1709 | 0.06109776 | 0.00000000 | 0.03512763 | **0.06109776** | **0.02597012** |
| 2903 | 0.06468922 | 0.00000000 | 0.03860462 | **0.06468922** | **0.02608459** |
| mean | 0.06289349 | 0.00000000 | 0.03686613 | 0.06289349 | 0.02602736 |
| range | 0.00359146 | 0.00000000 | 0.00347699 | 0.00359146 | 0.00011447 |

**Per foundation × `k`:**

| Seed | `k` | `delta_swap` | `delta_common` |
| ---: | ---: | ---: | ---: |
| 1709 | 7 | 0.05108173 | 0.01883013 |
| 1709 | 13 | 0.07111378 | 0.03311012 |
| 2903 | 7 | 0.05471612 | 0.01860119 |
| 2903 | 13 | 0.07466232 | 0.03356799 |

**Per foundation × state (16 tapes each):**

| Seed | State | `M` | `C` | `delta_swap` | `delta_common` | tapes with `delta_swap` > 0 | tapes with `delta_common` > 0 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1709 | `k7-early` | 0.05099588 | 0.03202266 | 0.05099588 | 0.01897321 | 16/16 | 16/16 |
| 1709 | `k7-middle` | 0.06653503 | 0.04687500 | 0.06653503 | 0.01966003 | 16/16 | 16/16 |
| 1709 | `k7-late` | 0.03571429 | 0.01785714 | 0.03571429 | 0.01785714 | 16/16 | 16/16 |
| 1709 | `k13-early` | 0.07211538 | 0.03751717 | 0.07211538 | 0.03459821 | 16/16 | 16/16 |
| 1709 | `k13-middle` | 0.05906593 | 0.02979052 | 0.05906593 | 0.02927541 | 16/16 | 16/16 |
| 1709 | `k13-late` | 0.08216003 | 0.04670330 | 0.08216003 | 0.03545673 | 16/16 | 16/16 |
| 2903 | `k7-early` | 0.06129808 | 0.04223901 | 0.06129808 | 0.01905907 | 16/16 | 16/16 |
| 2903 | `k7-middle` | 0.06739354 | 0.04842033 | 0.06739354 | 0.01897321 | 16/16 | 16/16 |
| 2903 | `k7-late` | 0.03545673 | 0.01768544 | 0.03545673 | 0.01777129 | 16/16 | 16/16 |
| 2903 | `k13-early` | 0.08198832 | 0.04610234 | 0.08198832 | 0.03588599 | 16/16 | 16/16 |
| 2903 | `k13-middle` | 0.06001030 | 0.03030563 | 0.06001030 | 0.02970467 | 16/16 | 16/16 |
| 2903 | `k13-late` | 0.08198832 | 0.04687500 | 0.08198832 | 0.03511332 | 16/16 | 16/16 |

**Graphwise component differences (means over 96 tape units per seed × graph):**

| Seed | Graph | matched − swapped component | matched − common component |
| ---: | --- | ---: | ---: |
| 1709 | HR | 0.06009615 | 0.03007669 |
| 1709 | RH | 0.06209936 | 0.02186355 |
| 2903 | HR | 0.06519002 | 0.02432463 |
| 2903 | RH | 0.06418842 | 0.02784455 |

**Dispersion (card's required variance reporting):**

| Quantity | swap | common |
| --- | ---: | ---: |
| within-state tape variance | 3.7900777298098625e-06 | 8.883915992432554e-07 |
| between-state variance | 0.0002615932561993586 | 6.27026772877995e-05 |
| between-foundation dispersion | 6.4492947022405166e-06 | 6.551560466397173e-09 |
| tape-level covariance | 9.175288926368633e-05 | — |

**`q_pre` strata, descriptive only** (the card authorizes no `q` main effect or interaction, and
the artifact itself carries `q_inference_authorized: false`):

| `q_pre` | states | tape units | mean `delta_swap` | mean `delta_common` |
| ---: | --- | ---: | ---: | ---: |
| 0 | `k7-early`, `k7-middle`, `k13-late` | 96 | 0.06839515 | 0.02453926 |
| 1 | `k7-late`, `k13-early`, `k13-middle` | 96 | 0.05739183 | 0.02751545 |

### Branch determination, applied exactly as the card writes it

A foundation is `panel-positive` when its overall `delta_swap` and `delta_common` means are both
positive, both are separately positive at `k`=7 and `k`=13, and at least four of its six
state-level means are positive for each contrast. Observed: both means positive for both seeds;
both contrasts positive in both `k` strata for both seeds; **6 of 6** state-level means positive
for each contrast in each seed. Both foundations are panel-positive, so the ordered branch is
**`PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL`** (branch 5). The card states that branches 5–8 "are
exploratory B observations, never stable-performance or direction decisions."

**The one observation that most bounds this branch:** the SWAPPED arm returned `U = 0.0` in every
one of its 384 raw cells, always terminating with `cable_overload` after 6 transitions and 0 policy
queries. So `delta_swap` equals `M` identically, and the matched-versus-swapped separation is
entirely the swapped control's immediate absorption rather than a graded return difference. The
COMMON arm absorbed the same way in exactly the 80 cells whose common action was `10` or `12`
evaluated under the graph it is not matched to (5 units × 16 tapes × 1 graph). This is recorded as
a direct observation; the card defines no polarity for it beyond branch 5.

## 9. Work accounting and declared-versus-actual reconciliation

`<root>/work-ledger.json`:

| Stage | missions | allocated slots | transitions | policy queries | optimizer steps | evaluator calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| foundation_training | 3,840 | 1,397,760 | 1,092,330 | 120,436 | 3,840 | 0 |
| fixed_learning_curves | 576 | 209,664 | 196,906 | 21,821 | 0 | 18 |
| final_competence | 256 | 93,184 | 89,721 | 9,963 | 0 | 2 |
| reachable_state_source_scans | 6 | 17,472 | 984 | 108 | 0 | 0 |
| development | 3,456 | 1,257,984 | 398,483 | 42,020 | 0 | 1,728 |
| heldout | 1,152 | 419,328 | 127,960 | 13,722 | 0 | 576 |

Reconciliation: `declared_total_missions` 9,328; `actual_executed_missions` 9,286;
`declared_not_executed_missions` **42**; `allocated_primitive_slots` 3,395,392;
`actual_transitions` 1,906,384; `ppo_updates` 320; `optimizer_steps` 3,840;
`native_evaluator_calls` 2,324; `policy_queries` 208,070; `source_states_established` 6.

The 42 unexecuted missions are the source-scan ceiling the card sets at "at most eight source
candidates per cell": 6 of the 48 declared scans were needed because every cell's first candidate
yielded a legal boundary. This is the card's own ceiling, not a shortfall. Transition, optimizer-
step and evaluator counts are all nonzero, satisfying spec §5.2 and card :513-514.

## 10. Resource telemetry (measured; not `resources_unmeasured`)

`published-result.json → resource_telemetry`, verbatim:

```json
{"cpu_seconds":364.3125,"cpu_utilization_fraction":1.045409572798515,"durable_high_water_bytes":129513695,"end_available_memory_bytes":14737141760,"failure_reasons":[],"foreground_io_read_bytes":617277934,"foreground_io_write_bytes":129516632,"invocations":1,"max_process_count":5,"max_thread_count":67,"measurement_incidents":[{"disposition":"CHILD_EXITED_BEFORE_OPEN_PROCESS","errno":22,"exception_class":"OSError","path_summary":"process-child","phase":"windows_open_process","severity":"TOLERATED","winerror":87},{"disposition":"CHILD_EXITED_BEFORE_OPEN_PROCESS","errno":22,"exception_class":"OSError","path_summary":"process-child","phase":"windows_open_process","severity":"TOLERATED","winerror":87},{"disposition":"CHILD_EXITED_BEFORE_OPEN_PROCESS","errno":22,"exception_class":"OSError","path_summary":"process-child","phase":"windows_open_process","severity":"TOLERATED","winerror":87},{"disposition":"CHILD_EXITED_BEFORE_OPEN_PROCESS","errno":22,"exception_class":"OSError","path_summary":"process-child","phase":"windows_open_process","severity":"TOLERATED","winerror":87}],"native_internal_worker_threads":[0],"observed_os_cpu_count":[16],"observed_torch_interop_threads":[8],"observed_torch_intraop_threads":[1],"passed":true,"process_tree_io_read_bytes":645313894,"process_tree_io_write_bytes":129632302,"process_tree_peak_rss_bytes":399925248,"resources_unmeasured":false,"resources_unmeasured_reasons":[],"sample_count":2158,"scratch_high_water_bytes":459086,"start_available_memory_bytes":14285291520,"wall_seconds":348.48781710000185}
```

| Card ceiling | Observed | Headroom |
| --- | ---: | --- |
| process-tree peak RSS ≤ 2 GiB (2,147,483,648 B) | 399,925,248 B (0.372 GiB) | 81.4 % unused |
| scratch high water ≤ 256 MiB (268,435,456 B) | 459,086 B (0.44 MiB) | 99.8 % unused |
| durable output ≤ 256 MiB (268,435,456 B) | 129,513,695 B (123.5 MiB) | 51.7 % unused |
| wall ≤ 30 minutes (1,800 s) | **348.488 s** (5 min 48 s) | 80.6 % unused |

2,158 continuous samples, one foreground process, `passed: true`, `failure_reasons: []`,
`resources_unmeasured: false`. The four `measurement_incidents` are `TOLERATED`
`CHILD_EXITED_BEFORE_OPEN_PROCESS` records for short-lived `admit-memory` children and are not
failures. Process wall from the shell wrapper: start `2026-09-02T21:55:27Z`, end
`2026-09-02T22:01:19Z` = 352 s, which brackets the monitor's 348.488 s. The A-R2 projection was
350.119 s; the measured wall is 0.46 % below it.

**Nothing was quarantined.** No quarantine lock and no `terminal-no-polarity.json` exists under the
result root. `published-result.json` lists 383 artifact-inventory rows, each with direct byte size
and sha256, and the run cold-validated all 322 foundation checkpoints (parameters, Adam moments,
update frontier, training receipt) before publication.

## 11. Verbatim summary lines

The runner's launch line, unedited (`run.log` line 2):

```
{"argv": ["scripts/run_scdmp_mf_rs_mk_b01.py", "--run-01", "--receipt", "C:/Projects/HMASD/temp/directions/semigroup_consistent_duration_model_policy/exp/RUN-01-REPLACEMENT-01/admission.json", "--result-root", "C:/Projects/HMASD/temp/directions/semigroup_consistent_duration_model_policy/exp/RUN-01-REPLACEMENT-01/SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01", "--confirm-run-id", "SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01", "--performance-assessment", "C:/Projects/HMASD/temp/scdmp-b01/A-R2/assessment.json"], "attempt_id": "SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01", "cwd": "C:\\Projects\\HMASD", "mode": "SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01", "receipt": "C:\\Projects\\HMASD\\temp\\directions\\semigroup_consistent_duration_model_policy\\exp\\RUN-01-REPLACEMENT-01\\admission.json", "recorded_performance_assessment": {"assessment_id": "SCDMP-MF-RS-MK-ORDER-VALUE-B01-A-R2", "assessment_note": null, "assessment_path": "C:\\Projects\\HMASD\\temp\\scdmp-b01\\A-R2\\assessment.json", "assessment_performance_readiness": "REVIEW_REQUIRED", "assessment_projection": {"conservative_projected_total_seconds": 350.1191929995366, "fixed_overhead_seconds": 60.0, "formula": "sum(measured_stage_wall * fixed_full_missions / measured_missions * 2.0) + 60.0", "margin_to_1800_seconds": 1449.8808070004634, "projected_work_seconds": 290.1191929995366}, "assessment_status": "PERFORMANCE_OBSERVATION_COMPLETE", "gating": false, "ordered_branch": null, "readiness_receipt_note": "not_supplied", "readiness_receipt_path": null, "readiness_receipt_status": null, "recorded_only_reason": "evidence spec 11.4: a performance readiness capacity gate may not hold a B launch", "run_01_performance_disposition": "REPAIR_REQUIRED", "schema": "SCDMP_MF_RS_MK_B01_PERFORMANCE_ASSESSMENT_V1", "scientific_polarity": null, "section11_recast_record": "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md"}, "result_root": "C:\\Projects\\HMASD\\temp\\directions\\semigroup_consistent_duration_model_policy\\exp\\RUN-01-REPLACEMENT-01\\SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01", "resume": false, "study_id": "SCDMP-MF-RS-MK-ORDER-VALUE-B01"}
```

The runner's final stdout line, unedited (`run.log` line 3):

```
{"published_result": "C:\\Projects\\HMASD\\temp\\directions\\semigroup_consistent_duration_model_policy\\exp\\RUN-01-REPLACEMENT-01\\SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01\\published-result.json", "source_identity": "C:\\Projects\\HMASD\\temp\\directions\\semigroup_consistent_duration_model_policy\\exp\\RUN-01-REPLACEMENT-01\\SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01\\source-identity.json"}
```

Process exit status `0`; shell wrapper recorded `exit=0`, `start 2026-09-02T21:55:27Z`,
`end 2026-09-02T22:01:19Z`.

The published branch fields, unedited from `published-result.json`:

```
"ordered_branch": "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL"
"scientific_polarity": "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL"
"complete_full_chain": true
"resources_unmeasured": false
"resources_unmeasured_reasons": []
"performance_assessment_file": "performance-assessment.json"
"section11_recast_record": "docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md"
```

## 12. Deviations from the science card

| # | Deviation | Status |
| --- | --- | --- |
| D1 | No `PERFORMANCE_READY` receipt was supplied. The A/RECON assessment (`REVIEW_REQUIRED`) was recorded as a field and the run proceeded | **Authorized**: this is exactly owner decision 1 of `FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`, recorded under §11.6 in `SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md` and in the card's own 2026-09-02 addendum. The card's `:79-81` telemetry-arming precondition and the `:530-531` / `:96-99` / `:621` missing-measurement invalidators are demoted by the same decision. No demotion was exercised in this run beyond the receipt: telemetry was fully measured |
| D2 | `TMPDIR`/`TEMP`/`TMP` were redirected to `…/exp/RUN-01-REPLACEMENT-01/native-tmp` for the whole invocation | The default native build root `%LOCALAPPDATA%\Temp\hmasd_scdmp_mf_rs_mk_native\c0aeb83f…b44f1e` exists but is **unreadable and undeletable** — `Get-ChildItem`, `icacls` and `Remove-Item` all return access denied for the owning user — so `_read_build_receipt` raised `NativeBackendError("native cache receipt or DLL is unavailable")` and every native-touching test and the run failed before this redirect. The redirect made the cache root writable and the DLL was compiled fresh from the unchanged `mf_rs_native.cpp`. This changes only `compiled_native_library.resolved_path` / `build_receipt_resolved_path` recorded in `source-identity.json`; the source sha256, compile flags, ABI version 3, struct sizes and max batch width are unchanged, and no scientific factor of the card is affected. The redirected root is a sibling of the result root, so it does not enter the durable-byte measurement |
| D3 | `scripts/hmasd_run.py prepare/execute/reconcile/promote` was not used | The card's CM objective requires the isolated B runner to own its own manifest, header, ledger and publication, which it does. No workflow-layer manifest was written |
| D4 | Torch interop threads were left at the platform default, `8` | The card's `WORKER_TOPOLOGY` declares `torch_intraop_threads: 1`, and the runner sets `torch.set_num_threads(1)`; the observed intraop count is `1`. The executing instruction asked for "4 torch threads at most", and interop threads were not constrained: `observed_torch_interop_threads: [8]` is recorded in the telemetry. Named here because it exceeds that instruction, not the card |

No other deviation. Seeds `1709`/`2903`, 160 updates × 12 episodes, 1,920 AdamW steps per
foundation, the nine curve points, the 128-mission competence check, six state twins, the 18-action
sweep on eight development tapes, 16 held-out tapes, the four admissible `q_by_cell` vectors, the
RNG-domain separation, the zero-access quarantine of the old physical root and the create-once
publication were all executed exactly as frozen.

## 13. Could not verify

- **Nothing about why the swapped arm is uniformly zero.** Every swapped cell absorbed with
  `cable_overload` after 6 transitions. Whether that is a property of this six-state population, of
  the two selected actions (`10` and `12`), or of the host's cable dynamics at a forced first hold
  is untested here and would need a different object.
- **Whether the constant `A_HR = 10`, `A_RH = 12` mapping generalizes.** It held in all twelve
  units of this run, with several top-two margins of exactly `0.0` resolved by the tie rule. Two
  seeds and one eight-tape development selector cannot separate "the catalogue has two clearly
  graph-specific actions" from "the eight-tape selector is degenerate here".
- **Any `q` statement.** The card authorizes no `q` main effect or `q`-by-order interaction, and
  the artifact carries `q_inference_authorized: false`. The `q_pre` stratum means in §8 are
  descriptive only and every claim is conditional on the realized vector `001110`.
- **Any seed-superpopulation inference.** Two foundations. The card forbids manufacturing one; the
  per-seed mean and range in §8 are the whole permitted summary.
- **Promotion to C-BENCH.** That needs five valid competent foundations and the six conditions in
  the card's promotion section. `RUN-02A` (seed `4013`) and `RUN-02B` (seeds `5171`, `6361`) are
  now bindable to this valid base run and its realized `q_by_cell`, but neither was run.
- **The A-R2 assessment's `REVIEW_REQUIRED` disposition was not resolved.** It is recorded, not
  discharged. `RUN_01_PERFORMANCE_DISPOSITION` remains `REPAIR_REQUIRED` in the source and is
  recorded beside it.
- **The recast's telemetry demotion was not exercised.** Telemetry was fully measured, so the
  `resources_unmeasured: true` path is covered only by
  `tests/experiments/candidates/scdmp_variable_k/test_mf_rs_mk_section11_recast.py`, not by this
  run.
- **Resource-ceiling behaviour near the caps.** All four ceilings held with large margins; nothing
  here says what happens close to them.

## 14. Interpretation boundary

The strongest statement this run permits, in the card's own words and with the realized vector
named: across the two observed competent foundations, the six first-eligible treatment-common
reachable states generated under identity pre-event `p` and the realized constrained-balanced
`q_by_cell = 001110`, `k ∈ {7, 13}`, development-selected mappings and sixteen held-out tapes per
state, matched first actions showed a repeatable native full-mission return advantage over both the
swapped mapping and the strongest graph-blind common control.

It establishes no stable superiority, seed-superpopulation effect, complete support, pointwise
positivity, rescue or reinterpretation of FCEOV `.3`, learned graph recognition, chronology
mediation, duration-policy or semigroup value, arbitrary state/`k`/foundation generality, inherited
legacy polarity, coordinated-renewal value, variable lifetime or `N`, general MARL value, transfer
beyond the named simulator, safety, deployment, flight, convergence, closure, parking, fusion or
priority — and no invariance to `q_pre`, `q` main effect, `q`-by-order interaction, natural or
arbitrary `q` mixture, alternative pre-event `p`, or independence from `q`-conditioned survival and
first-eligible selection.

This is a valid, complete observation of the frozen B01 base run. Per the card, `B` evidence "does
not by itself retire a direction" and branch 5 "proceeds to `RUN-02A` and, absent invalidity, may
proceed to `RUN-02B`". Whether to spend that is a Portfolio decision, not one this document makes.
EM interpretation must use the persistent convergence node before any direction-local convergence
or lifecycle recommendation.
