# RCLE TBCFV first-B Innovator intake — 2026-09-06

Node `em:roster_consistent_latent_exploration:innovator` (first binding), request
`2026-09-06-rcle-tbcfv-first-b-innovator-02` (packet `pro_packets/20260906_tbcfv_first_b_innovator_r02/`,
evidence base `9324b08d0`, task `727a2d70c`; the r01 request on the same inputs was never sent).
Direction Manager: the Claude research hub. Decision authority: `PRO_FINAL`.

## 1. Transport facts (observation)

One Send (click count 1) into a new conversation `6a9d9a3a-fd40-83e8-9e80-ad720582aaee`; the
tool's receipt stayed `SENT_UNCERTAIN` (message ids not observed) and was resolved by direct page
reading (one user turn with the prompt bytes, one assistant turn) and GitHub readback. Prompt
wording: the Codex-era renderer text, no connector wording. Delivery commit
`35e3b7b1470f372e09bc61b7e3a36f780040d327` (parent `9324b08d0`) on
`codex/pro-rcle-tbcfv-first-b-r02-20260906` at 2026-09-06T17:05:11Z, file
`pro_packets/20260906_tbcfv_first_b_innovator_r02/archive/RESPONSE.md` (32,108 bytes, sha256
`0e47b9105cae921d…`); Issue 8 comment 5560789984 at 17:06:00Z, `performed_via_github_app` =
`ChatGPT Codex Connector`. The hub read the file at the immutable commit for this intake.

## 2. The formed decision (read from the full response file)

**Open the first bounded B/EXPLORE pair `RCLE-TBCFV-B01-PERSIST-VS-FLEX` on the frozen TBCFV
host: `C1P1-COMMON-PERSISTENT` versus `FLEX-REKEY`, one paired training seed, 200 updates per arm
at 64 training episodes each, final checkpoint only, 256 evaluation episodes per held-out cell.**
The reason is not that persistent common plans are supported; it is that the containment
relation has never been asked at a finite learning budget, and one genuinely comparable learning
observation decides the next small investment more directly than an upper reference, a tuned
generic baseline or a mechanism explanation. The decision forms a cardable object and its
engineering boundary only: no source acceptance, no launch, no C freeze, no host, spec or
Portfolio change, no authorization of the definition card's five-arm twenty-block program.

What the response fixes, in its own terms:

- **Claim and binding structure.** Observe, on frozen TBCFV under the card's training law at a
  small budget, the recovery difference of the persistent common-plan package against the
  same-information strictly containing FLEX package on unseen-roster active-continuation
  changes, to judge whether an independent training replicate is worth buying. Binding MARL
  structure: **agent-count change and coordination recovery after a roster change**; the DM's
  "other-agent partial observability" is rejected as the identified cause (the card gives every
  arm the same public state summary and excludes private-cue aggregation).
- **Host and arms.** Host unchanged (120 sectors, six beacons, H=64, t_c=24, six always-legal
  claims, MOVE-TO-CLAIM decoder). Training per update: eight cells × eight episodes (6→6, 10→10,
  6→10, 10→6 crossed with ACTIVE_CONTINUATION and NEW_EPOCH); one parameter vector across all
  cells; held-out 8→8, 12→12, 8→12, 12→8 × both epoch conditions see no gradient, tuning,
  normalization re-estimate or model selection. Only two arms learn; treatment keeps a common z
  across active roster changes; FLEX may use common and individual update heads; both arms carry
  the card's 26,161 scalars, identical initial tensors per seed, paired exogenous randomness
  (positions, arrivals/departures, epoch) without forcing identical states after divergence.
- **Training law, unchanged.** Stopped-gradient Normal score term, actor log-probability term,
  joint 64-episode loss, one backward per block, plain SGD on the normalized full vector; eight
  stopped per-cell baselines per arm, parameters first, baselines 0.95/0.05 after. The DM's
  "separate optimizer/normalization state" is corrected to the state that actually exists: there
  is no Adam state and no return normalization, and none is added. FLEX's heads start at zero but
  train; the treatment's two heads are hard-masked. No entropy, auxiliary reward, pretraining or
  tuning.
- **Seed and scale.** One seed (to expose the new path's learning, measurement and cost problems
  with the smallest real pair), 200 updates and 256 episodes per cell as the chosen finite scale,
  not a sufficiency computed from cost or power data (none exists). Old "three to five seeds" and
  the card's twenty blocks are not entry requirements.
- **Primary measurement.** τ per episode exactly as defined (first h in 0..36 with four
  consecutive zero-unserved ticks after the boundary, else 40; a bounded recovery score under a
  failure code, not an uncensored mean). **Primary comparison restricted to the two
  ACTIVE_CONTINUATION held-out paths 8→12 and 12→8, equal weight**: per path both arm means, the
  FLEX-minus-treatment difference and the τ=40 fraction; the primary summary is the arithmetic
  mean of the two path differences, positive favouring the treatment. Companion: U (mean unserved
  over t=24..63) and 40U (cumulative normalized unserved demand, not raw service units), τ/U/Y on
  all eight cells, the eight-cell mean as a declared secondary description; NEW_EPOCH results are
  not a pure "erase plan identity" causal contrast. No episode deletion.
- **MEI: τ 4 physical ticks (10 % of the post-boundary window, one claim period) and U absolute
  0.05** (two normalized unserved ticks in the 40-tick window); interpretive, not significance
  thresholds; not the original C's 0.02 non-inferiority margin or its 72-tail rule.
- **Curves and statistics.** Per-update Y summary over the training episodes, readable per cell
  and overall, display points every 25 updates with all 200 block summaries retained; no
  intermediate held-out evaluation, no selectable intermediate checkpoint. Within-seed
  cell-stratified paired-scenario Monte Carlo standard errors with existing NumPy are enough; no
  seed-level inference from one seed, no t-test or episode bootstrap as stable superiority.
  Minimum retained: scenario-aligned τ/U readings, per-cell completion counts, failure codes,
  training curves; no full trajectories.
- **Zero-learner reference: `INDEPENDENT-NEAREST`**, one row plus eight-cell detail on the same
  final held-out scenarios (256 per cell, 2,048 total), evaluated once, no training, no parameter
  search, no script edits after seeing learning results; nearest beacon per claim, ties to the
  smaller beacon id, no plan latent. Purpose: an interpretable non-coordinated level for τ and U
  to distinguish "both arms saturated" from "small relative difference". `C0P0-PRIVATE-REFRESH`
  is a learned arm, not a scripted reference; FLEX is not a tuned competent generic baseline;
  H_A1 stays unidentified. The DM's "seconds-level cost" for the reference is not adopted.
- **Cost and ceiling.** Design counts, not exposure: per arm 12,800 training episodes (819,200
  ticks) + 2,048 evaluation episodes (131,072 ticks); two arms 29,696 episodes; reference 2,048;
  total 31,744 episodes / 2,031,616 ticks; at most 400 backward/parameter-update calls in total;
  25,600 training episodes are 0.5 % of the full card's 5,120,000. **Hard cap 2,700 s per arm and
  per training seed for the complete logical invocation; the whole first-pair execution limited
  to 5,400 s cumulative execution wall including the shared native build, the executability
  measurement, required checks, the reference row and publication**, each charged once where it
  actually belongs; the arms cannot both spend 2,700 s and then add preparation. Per-arm timing
  covers import/initialization, training, final evaluation, checks and publication with no phase
  split or resume resetting the clock; the study reports the elapsed critical path and the sum of
  invocation walls. No credible numeric wall projection exists; A1's fifteen minutes and the
  predecessor's forty-five are declared bounds, not measurements; scripted-episode timing does not
  cover learned forward, graph retention, backward or model output and must not be multiplied
  into a per-arm cost law. If a credible projection exceeds the cap, the design is not launched;
  the DM may record one symmetric reduction of updates or evaluation episodes before any real
  learning, restating the question; 200/256 is the baseline, not a menu. The first real training
  block gives its own wall and is charged to the B; a run found infeasible mid-way stops as a
  technical stop, not a shortened "complete" object.
- **CM preparation and the implementation gap.** `__main__.py` run/repair-resume calls
  `execute_full_panel`; the old path demands a twenty-block binding, all packages, training to
  800, per-arm per-cell 2,048-episode evaluation and the full prerequisite/value/mechanism
  reducers; it is not this B. CM implements a minimal B adapter in ordinary research scope:
  reuse host, model, package, loss and update computation; create only the two arms and one
  paired seed; pass the chosen budgets; keep training curves and final τ/U/Y; publish a readable
  result. No fake lease/certificate, no TEST identity through the twenty-block checks, no
  deletion of the full C's quantities while calling it the same object; the new B does not
  inherit the 72-tail publisher's mechanism and recovery guarantees. Launch preparation: first
  native build on `wsl_4070` from exact committed and pushed source, and **one zero-learner
  scripted executability/cost measurement of at most 300 s, at most eight cells × one
  eight-episode batch (≤ 64 episodes, 4,096 ticks) on preparation samples separate from the final
  held-out evaluation**; it asks only whether native lifecycle, events and outputs execute and
  what wall/RSS they cost; any host interaction is recorded as actual non-learning exposure. The
  old preflight (`full_runner_chain`, `_synthetic_empirical_frontier_chain`, `_new_block_runtime`)
  is not reused for it. One moderate focused check: real return, t_c event/claim/motion order, τ's
  four-tick and 40 failure coding, both arms' initial correspondence and FLEX's actual gradient
  path through the update heads, the joint 64-episode update, readable final output. Budgets:
  ≤ 2,000 new source lines, ≤ 600 runner lines, five-minute research tests; no registry,
  validator, guard, worker pool, lease, retry or telemetry beyond wall/RSS. CM may derive the
  200 × 0.0005 = 0.1 path-length upper bound mechanically with no learner; actual nonzero updates,
  initialization norm and final displacement are recorded inside the charged B.
- **Stop boundaries.** Native build failure, executability error or overrun, admission failure,
  or adaptation exceeding ordinary budgets stop the launch attempt with logs and counts and a
  concrete gap; no claim that either package fails to learn, no automatic second A, host change,
  dtype change, retry or seed replacement. Once the real B runs: hard cap reached, non-finite
  primary, wrong reward/information/event order, missing arm, asymmetric training exposure or
  held-out adaptation forbid the complete comparison; a damaged first arm does not spend the
  remainder on the second; a damaged second arm keeps the first arm's facts; technical stops are
  not adverse polarity; a missing reference row or telemetry degrades descriptively only.
- **Reading rule (five rows):** treatment-favourable Δτ ≈ +4 without a U loss at its MEI →
  candidate worth an independent replicate; adverse Δτ ≈ −4 or a material U loss → less support
  for restricting FLEX at this budget, a clear adverse result may also merit one replicate; inside
  τ ±4 / U ±0.05 → no material difference claimed, learning amount, censoring and seed
  uncertainty first; paths disagree, τ/U trade, errors span the MEI or τ almost all 40 → mixed,
  no post-hoc path choice; primary damaged → narrower facts only. Default follow-up for a credible
  pair: one new independent paired seed as a separately recorded investment; no "run until
  positive"; a changed budget or algorithm is a new outcome-informed B.
- **Not chosen:** upper/generic first, a standalone cost A, the full five-arm program, parking,
  the predecessor host. Ceiling: a preliminary performance signal or counterexample on this frozen
  toy, budget, training instance and held-out cells; no component attribution, fragmentation
  mediation, stable superiority or extrapolation.

## 3. Check against current instructions and specifications

The response decides the posed direction-tier question at its declared class (first B/EXPLORE),
inside evidence-spec §§5.2, 11.1, 11.4, 11.7, 11.8, 11.9, the engineering scope spec §§3–5 and the
runtime spec §§1–7; it requests no exception, no Portfolio action and no launch. No conflict
found; nothing returned to the node. `PRO_FINAL` for this node. The DM's three corrected
formulations (binding structure, optimizer/normalization state, seconds-level reference cost) are
adopted as corrected.

## 4. Decisions this intake produces

- Direction tier (`PRO_FINAL`, executed): the first B `RCLE-TBCFV-B01-PERSIST-VS-FLEX` is opened
  as specified; the DM freezes `RCLE_TBCFV_B01_PERSIST_VS_FLEX_SCIENCE_CARD_20260906.md` from the
  node's contract and a bounded CM objective (thin two-arm adapter, first native build,
  ≤ 300 s executability measurement, INDEPENDENT-NEAREST reference, focused check). RCLE stays
  `ACTIVE`/MEDIUM and in the Claude working set (with DISH).
- Object tier: none new. Predictions: the node's reading that both arms may barely learn
  (path-length bound 0.1) is recorded on the card; DM prediction to be written on the card
  before launch; owner slot not taken (unattended) unless filled.

Owner brief (Chinese): `docs/research/portfolio/owner/briefs/roster_consistent_latent_exploration/2026-09-06_TBCFV-first-B-innovator.md`.

scope: none
