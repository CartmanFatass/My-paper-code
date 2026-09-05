# Direction flexible_skill_duration: policy-based interruption of fixed-duration skills

## Research organization — 2026-09-04

This source belongs to route **K1 — 中断时机**, in the **中断与续约** family
of **灵活 skill duration**. Sources in the same route share one agenda with named subdirections;
this does not establish scientific equivalence or pool result polarity.
See [owner-adopted map and resume](../../portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md).
Current lifecycle and sequencing are held only in `docs/research/portfolio/PORTFOLIO.md`;
older lifecycle/execution statements below are historical. Existing cards, technical quarantines,
second-recast counts and stopped object-family boundaries remain unchanged.

This authority preserves the direction's scientific question, evidence references, and provenance.

## Authority

- Stable direction ID: `flexible_skill_duration`
- Current lifecycle, priority, and owner are held only by `docs/research/portfolio/PORTFOLIO.md`; this file records only the direction's scientific authority and provenance.
- Registered 2026-09-02 at the owner's request ("我希望进入正式研究层") after the direction ran for one day under `docs/Claude_docs/`. Those documents remain the working record and are referenced below; nothing there is re-typed here.

## Scientific question

HMASD assigns skills on a fixed clock `k`. Can a policy-based interruption rule — re-decide agent `i`'s skill at any step when the coordinator's causal-prefix log-probability of the held skill trails its best alternative by at least a cost `c`, with a per-agent cap `k_max` and a separate team cap `k_Z` — untie the skill duration from the clock without a duration menu, without learned termination, and without a new network head, and does it pay where the environment's event hazard is heterogeneous or its event durations are random?

Untying the duration `k` is this direction. Untying the agent count `N` is a separate direction (`variable_n_fleet_churn`); no joint object exists (evidence spec §11.5).

## Position

- Scheme ladder D0 to D8 and the B-class experiment ladder E0 to E6 are fixed in
  `docs/Claude_docs/plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` (§3, §5, §11). The first object is D2 (policy-based interruption); D0 (fixed `k`) is the comparator; D1 (age-conditioned discriminator at fixed `k`) is the control arm; D8 (the `(z, k)` menu) is kept only as a comparator.
- Theory ceiling (evidence spec §11.2): a suboptimality bound for the implemented rule against the best fixed `k` on the corridor host, stated with its assumptions; no invariance proof, no semigroup claim.
- Claim ceiling now: B — EXPLORE. Promotion to C-BENCH only after E3 or E4 repeats across three to five seeds (plan §5).

## Accepted mechanism-level science (2026-09-05)

- E1 does not support carrying the age feature forward at fixed `k`.
- E2 is a valid two-seed B observation on the homogeneous corridor. Its frozen verdict is
  `NEITHER`: no finite `c` reaches the range-tolerant D0 bar in both seeds, event alignment is
  below `0.5` everywhere, and `c = 0.25` passes the return bar only in seed 1. D2's mean segment
  length nevertheless increases monotonically with `c` in both seeds, so the threshold is a
  duration control even though the event-driven explanation is not supported on this population.
- E3 is complete,18/18 valid B cells, with frozen verdict `E3-H0-NO-ADVANTAGE`. All three large-row
  D0 comparators are competent; paired gains are -0.071387329102,-0.108895874023,-0.086455281576.
  Only large seed2 has the implementation's cumulative event path, yet it also loses return.
  This closes only c=.25 on the declared large row/budget, not other thresholds or the direction.
- Strongest support for some policy-gap value: E2 monotone duration control and E3 small seed2's
  positive0.033291585 gain against competent D0. Small seed3 also gains but D0 is below the card's
  competence line and cannot support superiority. Strongest contradiction: all medium/large
  pairs lose; increasing structural margin does not deliver an increasing native gain.
- Surviving alternatives: noisy policy gaps, seed quality, unequal realized optimizer exposure
  under the preserved route and team-renewal interference. The experiment does not causally
  distinguish them. Cumulative versus final path windows differ and are both reported; neither
  changes this negative branch. No universal no-value or cross-host speed claim is supported.
- Existing-data A/RECON headroom: upper-minus-trained-D0 row means .098784120/.175543309/.336673587,
  versus exact structural margins .057037446/.144357787/.271218984. The difference includes
  baseline undertraining; a fully tuned generic baseline set remains absent.
- Convergence selected **CONTINUE** with one next A/RECON: existing deterministic/geometric/
  rounded-lognormal renewal/reference same-information native-action opportunity census,
  fixed members,K2,mean20,shape1,Delta.4,H400 and k={1,2,5,20,40}. Public greedy is the strongest
  legal null; a structural gap does not establish D2/D8 learning value. No E4 learning matrix,
  E3 rerun,c retune or D3 recast is selected. The selected census is now complete3/3 laws,
  with288 full open-loop candidate values and zero learner exposure. Decision provenance PRO_FINAL /
  OWNER_DELEGATED; no Portfolio change. Complete archive/intake:
  `FSD_E3_COMPLETE_CONVERGENCE_INTAKE_20260905.md`. E3 result and bounded H0 remain unchanged.
- E4 no-training A/RECON: deterministic D20 from age0 has best clock k20 and m_dur=0;
  geometric/rounded-lognormal have best clock k5 and m_dur=.097099500000/.098225136232.
  Public greedy equals switching for every law, so these finite structural gaps need no
  learned policy gap. Using k20 alone would add .045344868963/.045614655901 of clock-grid
  shortfall on the two random laws. Complete candidate coverage and law moments/hazards are
  preserved in `FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md`; numeric mass rounding is not
  infinite-support exactness and the law comparison changes more than variance. The current
  discriminator is answered; no successor or learner is selected by
  `FSD_E4_CENSUS_INTAKE_20260905.md`. Tuned generic renewal-host headroom remains absent.

## Objects and their state (2026-09-05)

| Object | State | Record |
| --- | --- | --- |
| ADR 01 — D2 on the HMASD base route | accepted revision 3; implemented; `off` byte-identical | `docs/Claude_docs/plans/ADR_01_D2_POLICY_INTERRUPTION.md`; review Parts I–III, VII, VIII |
| ADR 02 — relay corridor host family | accepted revision 4; implemented with exact references and both margins | `docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md`, `RELAY_CORRIDOR_MECHANICS_20260902.md`; review Parts IV–VI, VIII |
| E0 — exposure line and frozen probe set | complete, two seeds, four arms, no quarantine | `docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_RESULT_20260902.md`; review Part IX |
| E1 — age input at fixed `k` | complete; owner prediction stands unrefuted; age not carried forward | `docs/Claude_docs/experiments/E1_AGE_INPUT_RESULT_20260902.md` |
| E2 — D2 cost sweep on homogeneous corridor | complete; 15 valid runs; frozen verdict `NEITHER`; accepted B intake | `FSD_E2_INTERRUPTION_COST_SWEEP_RESULT_EVIDENCE_20260904.md`; `FSD_E2_INTERRUPTION_COST_SWEEP_INTAKE_20260904.md` |
| E3 — heterogeneous hazard | complete18/18 valid; original bounded E3-H0-NO-ADVANTAGE retained by complete Convergence | `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`; `FSD_E3_HETEROGENEOUS_HAZARD_INTAKE_20260905.md` |
| Post-E3 renewal/reference census | complete3/3 A/RECON,288 candidates, zero learner; public greedy explains switching opportunity; no successor selected | `FSD_E4_CENSUS_SCIENCE_CARD_20260905.md`; `FSD_E4_CENSUS_RESULT_EVIDENCE_20260905.md`; `FSD_E4_CENSUS_INTAKE_20260905.md` |
| Advancement plan | E1 → E2 → E2b/E3 → E4 → C-gate; E2b is not selected at this boundary | `docs/Claude_docs/plans/RESEARCH_ADVANCEMENT_PLAN_20260902.md` |

## Code

| Surface | Path |
| --- | --- |
| D2 on the base route | `config_1.py` (`policy_interruption_mode`, `interruption_cost_c`, `interruption_cost_c_Z`, `skill_cap_k_max`, `team_cap_k_Z`, `age_feature`), `hmasd/agent.py` (`_batched_assign_skills_d2`, `_d2_store_transition`, `update_coordinator_d2`), `hmasd/networks.py` (`evaluate_held_batch`, `assign_partial_batch`, `evaluate_training_batch_ordered`), `hmasd/utils.py` (D2 tables, `_compute_d2_high_level_advantages`, `get_d2_coordinator_sampler`) |
| Corridor host | `envs/relay_corridor/` (`host.py`, `references.py`, `adapter.py`, `hmasd_driver.py`) |
| Runners | `scripts/run_flexible_skill_duration_e0.py` (E0; E1 imports its loop), `scripts/run_flexible_skill_duration_e2.py` and its study aggregator; `scripts/run_flexible_skill_duration_e3.py` (accepted recorder/paired helpers); `scripts/run_flexible_skill_duration_e4_census.py` (no-training renewal references) |
| Tests | `tests/flexible_skill_duration_d2_test.py`, `tests/flexible_skill_duration_e2_test.py`, `tests/relay_corridor_host_test.py`, `tests/relay_corridor_hmasd_test.py`, `tests/uav_env_channel_equivalence_test.py` (throughput refactor) |
| Fixtures | `tests/fixtures/flexible_skill_duration_d2/fingerprint_off.json` (the `off` byte-identity guard) |
| Local evidence | `temp/directions/flexible_skill_duration/exp/`, `temp/directions/flexible_skill_duration/probes/` (gitignored; content digests recorded in the result documents) |

## Relations to other directions

- `semigroup_consistent_duration_model_policy` (SCDMP): recast toward scheme D6 (a duration model whose value is sharing `Q(s, z, k)` across `k`); its `(z, k)` menu is comparator D8 here (plan §11 F). SCDMP's own objects continue independently.
- `ucope`: independent; its paid-probe period is a candidate D2 special case, and its odd/even duration split is a candidate C-time transfer test for this direction (plan §11 G).
- `variable_n_fleet_churn` (VNFC): the untied-`N` direction; separate by evidence spec §11.5.
- The relay corridor host family reserves parameter points for FRRIE, VNFC, SCDMP, UCOPE and CBSC (ADR 02 "Decision"); the host is shared infrastructure, not a claim of this direction.

## Evidence standard

`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, with §11 (owner calibration, 2026-09-02) controlling. A B launch here is held only by the §4 integrity items, nonzero counts, resource admission, and one exposure line; every contract is written in the E0 format and records its deviations.

## Provenance

- Claude Code session `session_015hGLzLCuJLFFtZTboKg2bd` (Fable 5.1), 2026-09-01 to 2026-09-02; implementation by Codex (D2 Phases 0–2) and Opus sessions (D2 Phases 3–8, corridor host, integration, E0, throughput refactor); ADR drafts by GPT Pro through the GitHub connector.
- Index of all working documents: `docs/Claude_docs/README.md`.
