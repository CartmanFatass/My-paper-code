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

## Accepted mechanism-level science (2026-09-04)

- E1 does not support carrying the age feature forward at fixed `k`.
- E2 is a valid two-seed B observation on the homogeneous corridor. Its frozen verdict is
  `NEITHER`: no finite `c` reaches the range-tolerant D0 bar in both seeds, event alignment is
  below `0.5` everywhere, and `c = 0.25` passes the return bar only in seed 1. D2's mean segment
  length nevertheless increases monotonically with `c` in both seeds, so the threshold is a
  duration control even though the event-driven explanation is not supported on this population.
- Strongest support: monotone segment duration and the seed-1 `c = 0.25` return pass. Strongest
  contradiction: every raw D2 return is below the learned best D0 return, alignment peaks at only
  `0.124684`, and the best D2 cost differs by seed.
- Surviving alternative: homogeneous hazards let one tuned fixed clock fit both regions; E3 tests
  whether the registered heterogeneous rows make regional renewal actionable. The competing
  explanation is that the policy gap remains optimizer noise.
- Next discriminator: E3 at the three registered hazard rows, D2 `c = 0.25` versus the exact best
  fixed-`k` D0 learner, with paired return and region-specific event-to-renewal measurements.

## Objects and their state (2026-09-04)

| Object | State | Record |
| --- | --- | --- |
| ADR 01 — D2 on the HMASD base route | accepted revision 3; implemented; `off` byte-identical | `docs/Claude_docs/plans/ADR_01_D2_POLICY_INTERRUPTION.md`; review Parts I–III, VII, VIII |
| ADR 02 — relay corridor host family | accepted revision 4; implemented with exact references and both margins | `docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md`, `RELAY_CORRIDOR_MECHANICS_20260902.md`; review Parts IV–VI, VIII |
| E0 — exposure line and frozen probe set | complete, two seeds, four arms, no quarantine | `docs/Claude_docs/experiments/E0_EXPOSURE_PROBE_SET_RESULT_20260902.md`; review Part IX |
| E1 — age input at fixed `k` | complete; owner prediction stands unrefuted; age not carried forward | `docs/Claude_docs/experiments/E1_AGE_INPUT_RESULT_20260902.md` |
| E2 — D2 cost sweep on homogeneous corridor | complete; 15 valid runs; frozen verdict `NEITHER`; accepted B intake | `FSD_E2_INTERRUPTION_COST_SWEEP_RESULT_EVIDENCE_20260904.md`; `FSD_E2_INTERRUPTION_COST_SWEEP_INTAKE_20260904.md` |
| E3 — heterogeneous hazard | selected over E2b by object-tier unattended decision; card frozen, not launched | `FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md` |
| Advancement plan | E1 → E2 → E2b/E3 → E4 → C-gate; E2b is not selected at this boundary | `docs/Claude_docs/plans/RESEARCH_ADVANCEMENT_PLAN_20260902.md` |

## Code

| Surface | Path |
| --- | --- |
| D2 on the base route | `config_1.py` (`policy_interruption_mode`, `interruption_cost_c`, `interruption_cost_c_Z`, `skill_cap_k_max`, `team_cap_k_Z`, `age_feature`), `hmasd/agent.py` (`_batched_assign_skills_d2`, `_d2_store_transition`, `update_coordinator_d2`), `hmasd/networks.py` (`evaluate_held_batch`, `assign_partial_batch`, `evaluate_training_batch_ordered`), `hmasd/utils.py` (D2 tables, `_compute_d2_high_level_advantages`, `get_d2_coordinator_sampler`) |
| Corridor host | `envs/relay_corridor/` (`host.py`, `references.py`, `adapter.py`, `hmasd_driver.py`) |
| Runners | `scripts/run_flexible_skill_duration_e0.py` (E0; E1 imports its loop), `scripts/run_flexible_skill_duration_e2.py` and its study aggregator; E3 runner pending CM |
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
