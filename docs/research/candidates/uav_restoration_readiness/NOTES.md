# uav_restoration_readiness — append-only notebook (Claude DM, WSL session)

Direction opened 2026-09-28 as the owner-approved successor of `energy_relay_benchmark`
(owner: "确认A 准许"; selection record in
`docs/research/candidates/energy_relay_benchmark/NOTES.md`, entries "Successor selection, round 2 read"
and "Owner decision (direct, '确认A 准许')"; Pro §5 answer at 5004851c8; programme critic review
`energy_relay_benchmark/successor_selection_20260928/REVIEW_PROGRAMME.md`). Host: `envs/uav_service_restoration`
(T3), read-only; no shared-code edits in this direction.

## 2026-09-28 — b01 declaration: zero-fit readiness read on the Milan single-outage restoration host

**Question (Pro's contract, adopted verbatim in substance).** On the Milan single-outage, four-UAV
service-restoration host with real aggregated demand, lawful causal information and complete 1800 s
recovery trajectories, does a same-information qualified joint rolling ordinary planner deliver an
effect over same-information independent greedy redeployment and over the static deployment that
independent actions cannot explain, i.e. is there a joint-redeployment opportunity that can form the
next learning question, rather than only a static capacity gap or a weak-baseline gap? This is a
resource/host readiness read (RECORDED), not a MARL experiment and not a claim of a new question.
0 fits; no training permission is attached to any outcome.

**Host facts (verified in source).** Preset `configs/uav_service_restoration/milan_site_outage.json`:
4 UAVs prepositioned at 130 m, max speed 20 m/s, altitude 100–180 m, no battery, no collisions;
episode 1800 s at 10 s decisions (180 steps), physics 1 s, midpoint quadrature; three terrestrial
sites (400 Mbps egress each; sw (620,620), ne (1780,1880), se (1820,620)); one presampled
`full_site_failure` on site 1 or 2 starting uniformly in [300, 600] s, not repaired; recovery ρ .9
sustained 60 s; scheduler = fixed path-flow LP (`highs`, ε 1e−6), `max_backhaul_hops 2`,
`max_candidate_paths_per_demand 40`, `max_total_candidate_paths 4096`; information
`central_delayed_telemetry` with `telemetry_delay_s 0.0`, TTL 180 s, sensing radius 900 m,
site registration radius 1100 m, `on_entity_limit_exceeded: aggregate`, `max_demand_points 25`,
split `test` (dates 2013-11-20/21/22 in `preprocess_milan_reference.json`), demand_scale 30 Mbps.
The information condition is central shared telemetry (the channel "does not establish decentralised
execution under bandwidth limits", `observations.py:3–9`); TTL/sensing staleness is the only ageing.
No Dec-POMDP claim is made. Everything except the activity field is an engineering assumption
(`parameter_provenance`).

**Comparators (all forward-only, same `get_current_state()` view, same executor, same LP).**
- `static_uav`: never moves (existing controller).
- `backhaul_aware_greedy` (existing controller; "independent greedy redeployment"): per-UAV score
  `min(unmet_estimate, backhaul capacity at the slot)`, sequential slot assignment in agent order
  with a duplicate set (`baselines.py:100–114`); no joint evaluation.
- `joint_rolling_lp` (new, `experiments/candidates/uav_restoration_readiness/b01/joint_planner.py`;
  "qualified joint rolling ordinary planner"): every decision step it scores candidate joint
  placements (each UAV: "stay" or one of the top-K = 8 slots by the greedy score) by building the
  host's own `NetworkSnapshot` (telemetry-reported site capability, telemetry-observed offered
  demand with unknown slots = 0, UAVs at their hover targets at the common altitude) and solving the
  host's own LP (`solve_or_raise`); coordinate ascent from the greedy assignment, ≤ 2 sweeps,
  tie-break by travel distance; idle fallback: a UAV whose chosen target is "stay" with zero marginal
  LP value takes the greedy's slot unless that lowers the joint value; executor identical to the
  greedy's (unit velocity toward the target xy). No anticipation, no travel-time model, no future
  demand, no privileged diagnostics (tested). Model mismatches with the env's own solve are
  recorded in the implementer return (last released interval's demand vs instantaneous frame;
  end-of-interval site vector, so an in-interval failure is seen one step late; hover targets vs
  midpoint positions) and apply symmetrically to the read.
- Not run: `demand_greedy` (equals static on the fixture by construction), `random`, the
  `ideal_full_current_demand` bound (the flag exists in the config but `get_current_state()` ignores
  the mode and the final-step observation raises `DemandDataError` on both demand sources; a shared
  `envs/` change would be needed, not bought for a readiness read — recorded as a host defect).

**Scenarios and cost contract (Pro's caps).** 8 dev episode seeds `101–108` on the `test` split
(the seed draws the 30 min window and the failed site; the exact windows/sites are recorded per
episode) × 3 controllers = 24 complete trajectories, seed-major so a budget stop leaves complete
pairs. Engineering cap 8 h (implementer task ≈ 19 min of agent wall plus this DM's review;
tests 9 new + 255 host tests green at the implementer return). CPU cap 8 h on `local_linux`
(`--max-wall-s 25200`; the runner stops starting new episodes past it and records the stop). One
trajectory is priced first: the launch runs seed 101 for the three controllers as its own
operation (`b01_readiness_price_a01`) before the 8-seed operation; if the planner's wall exceeds
40 min per episode the 8-seed operation is not launched and the direction reports "not ready at
this cost". Fixture reference walls (3 UAVs/9 points): static 4.7–5.1 s, greedy 4.8–5.4 s, planner
7.8–8.0 s per episode (752 LP solves, ≈ 57 ms per planned step); Milan projection (not a
measurement): 30–60 ms per LP build+solve, ≤ 65 solves per step, ≈ 6–12 min per planner episode.

**Readers (declared before any real-data run).** Primary, paired per seed over the 8 seeds:
`controller_satisfaction` (delivered/offered over the episode) and
`fraction_of_lost_service_restored` for joint − greedy (D_J) and greedy − static (D_G), with mean,
SE over seeds and the count of positive/negative seeds; recovery time and censoring reason per
episode (never averaged over censored episodes); the per-step delivered/unmet series on the
affected set around the failure; planner diagnostics (LP solves, fallbacks, chosen targets).
Descriptive reading band: the SE of the paired mean over 8 seeds; nothing is called an effect
inside two SE. No S7 QoS threshold is transplanted.

**Outcome rows (what each result changes; none authorises a fit).**
- D_G clearly positive and D_J clearly positive beyond the band → a joint-placement opportunity
  exists on real data under the host's information condition: a learning question may be
  *formulated* under §5 with its own review, against the literature neighbour (Xu et al. MobiCom'24 /
  arXiv 2505.08448) and with a comparison that is new in itself; no fit is approved by this row.
- D_G positive, D_J inside the band or negative → the independent greedy already captures the
  redeployment value at this information condition and horizon; joint placement without
  anticipation adds nothing readable; T3 is "no ready learner question" unless a different decision
  object (anticipation, sensing, information) is argued separately.
- D_G inside the band (static ≈ greedy) → the scenario has no redeployment headroom at these
  parameters (capacity/geometry/TTL); the preset's engineering assumptions, not MARL, are the
  binding factor; T3 is dropped as next host without a MARL verdict.
- Unverifiable data/split/execution contract, `SchedulerSizeLimitError` on real layouts that the
  declared reconciliation cannot resolve, or the price run over budget → "not ready/unknown",
  never "opportunity = 0".

**Gates before launch (in order).** (1) Owner's Milan data decision (Dataverse guestbook requires an
e-mail; owner asked A/B on 2026-09-28); (2) `prepare_milan.py --real-data` on the 15 reference dates
+ `milano-grid.geojson`, `validate_dataset.py`, quality report read (observed fraction, cell count,
extent) and the preset reconciliation its README demands (region, `max_demand_points`, candidate path
limits — the implementer's synthetic probe tripped `max_candidate_paths_per_demand 40` at the
deployment positions with 3 sites × 4 UAVs × 2 hops, so a direction-owned copy of the preset with
reconciled limits is expected; any change is declared here before use); (3) code committed and
pushed; (4) price run; (5) 8-seed run through `scripts/hmasd_launch.py` on `local_linux`.

**Novelty note.** Store-relative only; the closest primary neighbour is Xu et al., MobiCom 2024 /
arXiv 2505.08448 (UAV relay-chain redeployment after base-station damage, MAPPO baseline). The DM
reads that paper first-hand before any question is formulated from this read. No claim of a new
question is made by this declaration.

**First-hand read of the neighbour (DM, 2026-09-28; arXiv 2505.08448v2 pp. 1–3, PDF fetched from arxiv.org).**
Xu et al. (Tsinghua SIGS; "MRLMN") formulate UAV-enabled multi-hop networking in disaster scenarios as a
stochastic game: UAVs form relay chains from operational base stations into a "communication dead zone"
around a damaged BS (Fig. 1), maximising coverage and communication quality under connectivity
constraints; contributions are task-oriented agent grouping with reward decomposition, behavioural
constraints on key UAVs, and LLM knowledge distillation into MARL agents via Hungarian matching of
decision outputs; evaluation is against a MAPPO baseline and other comparison methods at several
environment scales and swarm sizes. Related-work §II.A reviews optimisation-based UAV placement/routing
(TSP/VRP, block coordinate descent, K-means + interior point) and §II.B MARL methods (MADDPG, MASAC,
graph-based), noting that "many studies assume that the backhaul network interfacing with the core
network is fully configured, thereby neglecting the optimization of relay nodes". What the neighbour
does not have, on this read: real aggregated demand data, an exact fixed path-flow scheduler shared by
every controller, a matched central-telemetry information condition with TTL staleness, or an
ordinary joint planner as the comparator; its UE demand and mobility are simulated and its
comparators are learning or optimisation heuristics. Consequence for this direction: the *problem*
family (event-driven UAV relay redeployment after BS failure) is established; any question formulated
from b01 must be new in its comparison (learned vs a qualified exact-LP-aware joint planner under
matched telemetry, on real activity data), not in the problem. The MobiCom'24 predecessor ("Scalable
MARL for Effective UAV Scheduling in Multi-Hop Emergency Networks") was not read (paywalled; abstract
only via the critic's search).

### 2026-09-28 — b01 implementation accepted (implementer, Opus/high, two bounded tasks; DM read `plan()`, the snapshot/demand construction and the information boundary personally)
Files: `experiments/candidates/uav_restoration_readiness/b01/{joint_planner.py,run_readiness.py}`, tests
`tests/experiments/candidates/uav_restoration_readiness/b01/test_joint_planner.py` (10 tests: full fixture rollout
with `get_privileged_diagnostics` patched to raise inside `act()`; determinism; K=1 never below the greedy start
and start targets equal to the unmodified greedy's actions; end-to-end runner with paired fields and an aggregate
pinned to `evaluate_baselines._aggregate`; ideal mode refused without a rationale; `--no-admission` refused for a
Milan config; exactly one literal `require_admission(__file__, direction="uav_restoration_readiness")` and the
launcher's `_validate_guard_contract` accepting it; wall-budget stop leaves a well-formed summary; idle fallback
never lowers the LP value and occurs on the fixture). Host suite `tests/envs/uav_service_restoration/` 255 passed
after the first task; nothing under `envs/` changed in the second. Accepted deviations: LP demand = telemetry
offered demand on observed slots (not the residual, which would double-serve live sites); `solve_or_raise` with
failures scored −inf; `--out` refuses only an existing `summary.json`/`episodes/` because the launcher pre-creates
the root; seed-major episode order; positions taken from the permitted view per decision; `_aggregate`
duplicated and pinned. Fixture end-to-end (3 seeds × 4 controllers, 61 s): joint − greedy exactly 0 on
satisfaction and restored (0/0/3 after the idle fallback; −.0043 on 3/3 before it); greedy − static +.2348
(SE .0151) / +.9373; walls per episode static 4.3 s, greedy 4.3–4.4 s, planner 7.0 s (931 LP solves, 134
fallbacks, 47 planned steps). Fixture numbers characterise the code, not any algorithm. Host defect recorded:
`ideal_full_current_demand` is inert in `get_current_state()` and crashes the final observation on both demand
sources; not fixed here. Scratch: `temp/directions/uav_restoration_readiness/scratch/implementer-b01/` (fixture
output 1.7 MB, kept until closure).
