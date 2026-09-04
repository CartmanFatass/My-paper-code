# E2 — D2 interruption-cost sweep against the fixed-k sweep on the homogeneous relay corridor

Design written by Claude Code (Fable 5.1) on 2026-09-03 after E1's intake (review Part XI).
Governing texts: `../plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` §3 (schemes D0, D2), §5 (E2
row), §11; `../plans/RESEARCH_ADVANCEMENT_PLAN_20260902.md` §1 (E2 row), §5, §6, §7;
`../plans/ADR_01_D2_POLICY_INTERRUPTION.md` (the D2 rule, `c`, `c_Z`, `k_max`, `k_Z`);
`../plans/ADR_02_RELAY_CORRIDOR_HOST.md` and `../plans/RELAY_CORRIDOR_MECHANICS_20260902.md`
(host, references, proposed grids); `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §4,
§5.2, §11.4. Claim ceiling: **B — EXPLORE.** Launch condition: refactor P4 reviewed and
integrated (review part recorded), and the owner's prediction on record in §1; the launch commit
sha is recorded in every manifest.

## 1. Question, claim ceiling, non-goals (spec §4.1)

Question: on the homogeneous relay corridor (both regions at the same event hazard), does
policy-based interruption (D2) at some finite cost `c` reach the return of the best fixed skill
duration `k`, and do its interruptions behave as an event-driven boundary (segment length
increasing in `c`, interruptions concentrated at event flags) rather than as noise in the
coordinator's log-probability gap?

Prediction on record (plan §11, 2026-09-03): owner — mechanism A, event-driven interruption, some
finite `c` reaches or exceeds the best fixed `k`; reviewer — mechanism A as well, with the best
`c` between 0.5 and 1.0 and the fraction of interruptions at event flags above one half at that
`c`. Both predictions agree on the mechanism; the reviewer's numerical clauses are the only
calibration contrast this study carries.

The two mechanisms the arms separate:

- **A, event-driven interruption.** The causal-prefix gap `g_i` rises sharply when the region's
  event flag flips because the held role becomes wrong for the observation; so at a `c` inside
  the gap's own scale, interruptions happen at events, segments last about as long as the
  inter-event time, and D2 matches or exceeds the best fixed `k` because it neither commits past
  events (large `k`) nor pays renewal outage every step (small `k`).
- **B, a noisy proxy.** The gap fluctuates with the coordinator's training noise independently of
  events; so a small `c` chatters (short segments not aligned with events, return below the best
  fixed `k`), a large `c` never fires (D2 equals D0 at `k_max`), and no `c` in between reaches the
  best fixed `k`. Under B the plan's stop condition (§6) sends the direction to D3.

Non-goals: no heterogeneous hazard (E3), no random event durations (E4), no age feature (E1
settled it), no team-level asynchrony study (E5), no claim about the UAV host (E2b), no
seed-count claim beyond direction and obvious instability (two seeds, plan §1).

## 2. Algorithm, environment, comparator (spec §4.2)

- Host: `envs/relay_corridor` at the mechanics page's first-object point except for the hazard:
  `n_agents = 6` (three per region), `n_roles = K = 2`, `n_zones = 4`, `horizon = H = 400`,
  `delta = 0.4`, `event_process = "bernoulli"`, **`lambda_regions = (0.02, 0.02)`** (homogeneous;
  the small row's second region rate for both), `rho = 0`, `c_probe = 0`, `role_decode = "argmax"`.
  The exact references for this point are computed by `enumerate_references` before the first
  run and recorded in the manifests: `J_switch` (the switching oracle) and `J_fixed_k` for every
  `k` in the sweep, hence the best fixed `k*` and the margins; they are references, not outcomes.
- Learner: the HMASD base route through `RelayCorridorHMASDDriver` at the launch commit,
  `policy_interruption_mode = "d2"` in every arm, `age_feature = "off"`, `num_envs = 16`,
  `episode_length = rollout_length = H = 400`, team code present with E5 coupling off (ADR 02),
  `torch` threads 4.
- Arms (nine; `c = ∞` is the D0 arm at `k = 40`):
  - **D0 `k` sweep:** `interruption_cost_c = interruption_cost_c_Z = inf`,
    `skill_cap_k_max = team_cap_k_Z = k` for `k ∈ {1, 2, 5, 20, 40}` (the mechanics page's grid;
    the fair D0 of ADR 01, boundaries identical to `off` at the same `k`).
  - **D2 `c` sweep:** `interruption_cost_c = interruption_cost_c_Z = c` for
    `c ∈ {0.25, 0.5, 1.0, 2.0}`, `skill_cap_k_max = team_cap_k_Z = 40`. The grid comes from E0's
    D0 gap histogram on scenario 1 (agent gap median 0.22, q90 0.64, max 1.66 in logit units;
    E0 result §7); the corridor's own gap distribution is recorded per rollout so the next
    contract can re-centre the grid if this one misses.
- Seeds: 1 and 2 for every arm (18 runs). Order: D0 `k = 40` and D2 `c = 1.0` first (seed 1,
  then seed 2), then the remaining `k` arms, then the remaining `c` arms, so that a stop after
  any pair leaves the central comparison matched.
- Comparator: D2 at each `c` versus the best fixed `k` from the D0 sweep at the same seed, and
  both versus the exact references. The D0 sweep is also its own sanity check: the learner's
  ordering of `k` is compared with the reference ordering of `J_fixed_k`.
- Matching: all arms at a seed share the host's master seed, so rollout 1's event tapes are
  identical across arms up to the first policy divergence (checked as in E0 for the `k = 40`
  and `c = 2.0` pair, whose first rollout must be bit-identical until the first interruption).

## 3. Measurements (spec §4.3, §4.4, §5.2)

Everything E0 records per rollout (transitions, episodes, optimizer steps per network, `M`,
returns, exposure lines, counts), plus:

1. **Evaluation every 5 rollouts** on **4,096 matched episodes** (ADR 02): the same 4,096 event
   tapes for every arm, seed and checkpoint, deterministic policy (`argmax` role, greedy
   coordinator), reporting mean return, its standard error over episodes, and the gap to
   `J_switch` and to `J_fixed_k*`.
2. **Interruption behaviour** (D2 arms), per rollout from the learner's `d2_metrics` and the
   host's event flags: interruption rate per agent-step; mean and distribution (deciles) of
   completed segment lengths per agent; the **event-alignment fraction**, the share of
   interruptions that fall within one step after the agent's region flag flipped; the team
   switch rate (`g_Z ≥ c_Z` firings); the fraction of segments closed by the cap `k_max`.
3. **Gap distribution**, per rollout, all arms: deciles of the agent gap `g_i` and the team gap
   `g_Z` at every step (not only at interruptions), so §1's grid can be judged against the
   corridor's own scale.
4. **Return by regime**: mean per-episode return split by whether the episode's event count is
   below or above its median across the 4,096 tapes (a cheap read on whether interruption pays
   where events are dense).
5. **D0 sanity**: the learner's `k` ordering by evaluation return at the last checkpoint against
   the reference ordering of `J_fixed_k`.

The evaluation uses a second agent instance synced from the learner (the E0 mechanism), so the
learner's RNG and per-lane state are untouched; the 4,096 tapes are generated once from a fixed
evaluation seed and their content digest is recorded.

## 4. Budget and stop rule

1. `R = 20` rollouts per run at 16 lanes; wall-clock estimate written before launch from the P4
   timing (the corridor rollout is update-bound; plan §4 assumed about 100 s per rollout at 16
   lanes before P4).
2. Resource preflight inside the runner before every run, as in E0.
3. Stop rule per run: `R` rollouts, or the first non-finite loss or return (recorded as an
   instability observation). Instrumentation failure quarantines the run (spec §6.2): no
   interpretation, no resume, no salvage; the run is re-run once from scratch under a new name;
   a second failure reports the arm-seed as not run.
4. Stop rule for the study: all 18 runs, or the 8-hour machine-time cap (advancement plan §7
   decision 3), or the owner's stop; a study that would exceed the cap drops seed 2 of the
   outer arms (`k ∈ {1, 2}`, `c ∈ {0.25, 2.0}`) first and records the deviation.

## 5. Reading the result (written before the data)

Let `R_best0` be the best D0 arm's evaluation return at the last checkpoint (per seed), `R_c` the
D2 arm's at cost `c`, and `s` the larger of the two arms' across-seed ranges.

- **Mechanism A is supported** if some `c` has `R_c ≥ R_best0 − s` in both seeds, and at that `c`
  the event-alignment fraction exceeds one half and the mean segment length is non-decreasing in
  `c` across the four `c` arms in both seeds.
- **Mechanism B is supported** if no `c` has `R_c ≥ R_best0 − s` in either seed, and the
  event-alignment fraction at every finite `c` is below one half.
- Anything else is **neither**, reported with the three quantities per seed and `c`; if the
  return condition holds but the alignment does not, that is recorded as "D2 pays for a reason
  other than event alignment" and becomes E3's first design question.
- The D0 sanity check is a §4 item: if the learner's `k` ordering disagrees with the reference
  ordering at the top (the learner's best `k` is not `k*` or its reference-adjacent neighbour) in
  either seed, the study is reported with that fact first and the comparison against `R_best0` is
  read against the learner's own best, not the oracle's.
- The reviewer's numerical prediction (§1) is scored separately: best `c` in `[0.5, 1.0]`, and
  alignment above one half there.
- Any pattern not anticipated here is recorded as an observation for E3's design, not as a result.

## 6. Outputs

- Runner `scripts/run_flexible_skill_duration_e2.py` (imports the E0 runner's manifest,
  preflight and summary conventions and the corridor driver; does not copy the E0 loop); run
  directories `temp/directions/flexible_skill_duration/exp/E2_<date>/<arm>_seed<S>/` with
  `manifest.json` (launch sha, host point, references, arm parameters), `preflight.json`,
  `metrics.jsonl`, `eval.jsonl`, `interruptions.jsonl`, `gaps.jsonl`, `summary.json`, the final
  checkpoint; a study-level `E2_summary.json` with the §5 quantities per seed and `c`.
- Result document `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_RESULT_<date>.md` in
  the E0 format: the §1 items, the launch commit, the references table, the timing basis,
  per-run tables, the §5 reading applied verbatim, verbatim summary lines, deviations,
  could-not-verify.

## 7. Interpretation boundary (spec §4.7)

Bounded to the homogeneous corridor at `(λ, Δ) = (0.02, 0.4)`, `N = 6`, `K = 2`, `H = 400`, the
grids above, two seeds, `R = 20`, 16 lanes, one machine, and the measurements above. It says
whether D2 at some finite `c` reaches the best fixed `k` on this host and whether its
interruptions are event-aligned; it says nothing about heterogeneous hazards, random durations,
the UAV host, or which `c` transfers.
