# RCLE Innovator: evidence and options for a first bounded B on the TBCFV host (DM proposal, 2026-09-06)

Claim to be tested by the proposed object: at matched small training exposure on the frozen
rotating-perimeter host with within-episode membership events, a package that keeps one common
plan persistent across the event (`C1P1-COMMON-PERSISTENT`) recovers service after churn at least
as fast as the strictly containing package that may re-key or individualize the plan at the event
(`FLEX-REKEY`); the finite-budget direction of that difference is unknown. Binding structure:
other-agent partial observability under membership change, a broadcast common latent, and
identical low-level decoders; no partner co-adaptation beyond the shared plan.

Proposal only, for `em:roster_consistent_latent_exploration:innovator` (first binding of this
node), written by the Claude research hub as DM at the working-set refill after VSP-C1 and FRRIE
parked. Not a frozen card, not a launch, not a Portfolio action.

## What is recorded (observation)

- **Recast 2026-09-01** (`DIRECTION.md`, "Portfolio empirical-standard recast"): RCLE is `ACTIVE`
  for a B/EXPLORE finite-budget package question: "compares persistent-common and containing FLEX
  packages on churn recovery over three-to-five seeds with matched local information,
  communication, RNG access, parameters, interactions, updates, and model-selection exposure.
  Report full learning curves, post-churn recovery time, and integrated unserved demand." The
  earlier information-necessity claims are closed and transfer no polarity.
- **Frozen host definition** (`RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md`,
  `stage=definition_only`, `empirical_authorization=false`): circular perimeter of 120 sectors, six
  service beacons, `H = 64` ticks, one membership boundary at `t_c = 24`; training rosters
  `N ∈ {6, 10}` with static and within-episode `6→10` / `10→6` events; held-out rosters `{8, 12}`
  evaluated without retraining. Endpoints: learning return `Y = 1 − (1/64) Σ_t u_t` (unserved
  fraction), primary episode endpoint recovery time `τ = min{h : u_{24+h} = … = u_{24+h+3} = 0}`
  censored at 40, companion `U = (1/40) Σ_{t=24}^{63} u_t`. Treatment `C1P1-COMMON-PERSISTENT`;
  comparator `FLEX-REKEY`, which contains the treatment exactly (zero final update heads reproduce
  every treatment policy; trainable from update one); three further factorial arms and three
  scripted packages are defined but are the full program, not the first object. The card's
  prospective full program is 5 arms × 20 run blocks × 800 updates × 64 episodes of training plus
  held-out panels (7.74 M episodes in all); it is explicitly "not execution authority or a runtime
  forecast".
- **Executable state**: `experiments/candidates/roster_consistent_latent_exploration_tbcfv/`
  holds 23 tracked files (config, host oracle, models, packages, scripted packages, native backend
  with `native/tbcfv_backend.cpp`, process workers, empirical contract/runner/inference/artifacts,
  `__main__.py`) and seven preactivity certificate/preflight JSON records. **No result-bearing
  invocation of this host has ever run** (A1 census: tracked current-host result JSON = 0). The
  native backend has not been built on `wsl_4070`; per-episode cost is unmeasured.
- **A1 headroom census** (2026-09-04, `RCLE-HC-D / UPPER_REFERENCE_AND_GENERIC_BASELINE_MISSING`,
  `H_A1 = NOT_IDENTIFIED`): no numeric current-host result, no designated upper reference, no
  tuned same-information generic learner return exist. Per evidence-spec §11.7 a missing record
  sequences the measurement early and never stops investment; per §11.9 exploration needs neither
  complete headroom nor a unique explanation before real training.
- **Predecessor learning results** (different hosts, historical polarity does not transfer): B1
  (12 paired seeds, three comparators, all endpoints unresolved, `PRIMARY_POSITIVE=false`), B2
  (12 seeds, unresolved validity), CPC (16 seeds, `NO_COARSE_ADVANTAGE`, both deltas inside the
  ±0.03 no-material band). Declared budgets there were one CPU worker, ≤ 2 GiB, 45 wall minutes
  per object. No MEI in the §11.7 sense was declared on those cards (they predate it).
- **No Pro node for RCLE exists yet** (registry has no `em:roster_consistent_latent_exploration:*`
  key; no archive; no GitHub Issue before this packet's Issue). VSP-06 partner-memory code is
  absorbed as a branch (`experiments/candidates/vsp_06_mssr/`), not part of the first object.

## What is not known

- The TBCFV cost law: wall per episode, per update, native build time, peak RSS. Unmeasured.
- Whether the treatment/comparator packages train at all at small exposure on this host (no run).
- The direction of the finite-budget effect; the containing comparator can only match or exceed
  the treatment's policy class, not its optimizer trajectory.

## Options weighed by the DM

1. **First bounded B/EXPLORE pair on TBCFV (recommended).** Object `RCLE-TBCFV-B01-PERSIST-VS-FLEX`:
   arms `C1P1-COMMON-PERSISTENT` versus `FLEX-REKEY` only (no factorial arms); one paired training
   seed (matched initialization, common exogenous randomness, separate optimizer/normalization
   state), training cells as the card defines on rosters `{6, 10}` with the within-episode events;
   a reduced budget of **200 updates per arm** (a quarter of the card's 800; 64 episodes per update)
   with learning curves at every 25 updates; held-out evaluation on the 8 cells with **256 episodes
   per cell** (2,048 per arm, an eighth of the card's panel), using only the final checkpoint;
   endpoints as the card: primary mean recovery time `τ` (censored at 40) over the 8 held-out cells,
   companion `U` and the learning return curve, energy-free; **MEI proposed by the DM: 4 ticks of
   `τ`** (10% of the 40-tick post-boundary window, the smallest recovery difference an operator
   would schedule around) and 0.05 absolute in `U`, offered for challenge. Complete-invocation
   ceiling 2,700 s per arm (the runtime spec's toy threshold), 5,400 s summed, on `wsl_4070`, fresh
   admissions, no retry, no substitution. The CM assignment includes, as engineering not science,
   the first native build on the node and a bounded scripted-package executability and cost
   measurement (≤ 300 s, zero learner) from which the per-arm projection is composed before
   launch; if the projection exceeds the ceiling, the DM reduces updates or evaluation episodes
   before launch and records it, rather than launching over the cap. Result branches follow the
   B02-style pattern: favourable / adverse / inside-MEI / damaged, with all curves and seeds
   retained; one or two further independent seeds are the default follow-up under §11.8.3 if the
   first pair is trustworthy and comparable.
2. **Construct the tuned generic baseline and upper reference first** (the A1 gap). Rejected as a
   prerequisite: FLEX-REKEY is the containing same-information null and is trained in option 1;
   an upper reference on this host has no known construction; §11.9 does not require it.
3. **A separate zero-learner executability/cost object (A) before any B.** Not selected as a
   science object: the measurement is needed but belongs inside the CM's launch preparation for
   option 1 (§11.4 admits no extra launch gate); it becomes a separate object only if the host
   fails to build or run, which would be a technical failure, not evidence.
4. **Run the full card program (5 arms × 20 blocks × 800 updates).** Rejected: two to three orders
   of magnitude beyond an exploration budget and beyond the toy threshold per arm; not a B.
5. **Park RCLE or move to a predecessor host.** Rejected: the recast selected this host and question
   and the predecessor hosts' questions are closed.

Questions the DM puts to the node with option 1: the update budget (200 versus another finite
number) and evaluation episodes per cell; one paired seed versus two; the MEI values and reason;
whether `τ` or `U` is primary; whether a scripted no-plan reference (`C0P0`-style) evaluation on
the held-out cells should accompany the pair as a non-learning reference row (the DM proposes yes,
evaluation only, since it costs seconds and gives the first current-host numeric reference the A1
census lacked); and the stop boundary if the native build or the executability run fails.
