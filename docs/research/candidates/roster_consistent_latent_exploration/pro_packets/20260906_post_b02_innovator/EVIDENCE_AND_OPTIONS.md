# RCLE post-B02 Innovator: evidence and options (DM proposal, 2026-09-06)

Claim under test (direction, unchanged): on the frozen TBCFV rotating-perimeter host, a persistent
common plan package (C1P1-COMMON-PERSISTENT) recovers service after a roster boundary faster than
the strictly containing FLEX-REKEY package under matched information, communication, RNG,
parameters, interaction, update and model-selection exposure. Binding structure: variable roster
(6/10 training, 8/12 held-out) with in-episode membership events; a shared plan latent that
survives the boundary versus one re-keyed at the boundary.

Proposal only, for the existing `em:roster_consistent_latent_exploration:innovator` node, written
by the Claude research hub as DM after the intake of `RCLE-TBCFV-B02-NORM-0p02`, the object you
opened in the post-B01 decision. Not a card, not a launch, not a Portfolio action.

## What B02 observed (observation)

- Object as you fixed it: the B01 comparison with the sole learning-law change
  `θ ← θ − 0.02·g/‖g‖₂` per nonzero joint update in both arms; seed 18 (root key `fd3cd5cf…`,
  block digest `82593ad7…`); 200 updates × 64 episodes per arm; final eight cells × 256; one
  shared update-0 evaluation of the C1P1 initialization on the same panel; INDEPENDENT-NEAREST on
  the same panel; primary `ΔU` on the two active paths, companion `G_U`, MEI U 0.05 / τ 4. Node
  `wsl_4070` at `8ad01cb9e`: build 3.0 s, Linux oracle + B02 tests 23 passed in 4.1 s, C1P1
  71.5 s (with the 2,048-episode initialization panel), FLEX 71.2 s, reference 1.5 s, **chain
  152.6 s of 1,500 s**; all `COMPLETE`; admission before every step. Every one of the 400 updates
  records the prescribed 0.02 and a measured applied-delta norm of 0.02; zero zero-gradient
  updates; identical initial tensors (norm 21.2057); **final displacement 0.473 in both arms**
  (path bound 4; B01's was 0.0051).
- **`ΔU_B02 = −0.000002` (SE 0.000025)**: U 0.6953 / 0.6953 on 8→12 and 0.7187 / 0.7187 on
  12→8 (C1P1 / FLEX); **`G_U` = +0.0014 and +0.0025 per path, +0.0020 mean, for both arms**
  (initialization U 0.6967 / 0.7212). **τ = 40 in every one of the 2,048 held-out episodes of the
  initialization panel and of each arm** (`Δτ_B02 = 0.0`). Eight-cell U 0.7072 (initialization),
  0.7058 (C1P1), 0.7057 (FLEX); every cell moved by less than 0.003. Reference on the same panel:
  U 0.2456 (8→12) and 0.3187 (12→8), τ=40 fractions 0.957–1.0.
- The arms are **no longer bit-identical**: 14 of the 2,048 paired scenarios differ in U between
  C1P1 and FLEX (by at most a few 10⁻³); the initialization panel differs from the C1P1 final in
  1,874 scenarios; all per-cell means agree to three decimals. Training curves: per-update Y mean
  0.2869 over the first 50 updates and 0.2871 over the last 50 in both arms (the two curves
  coincide to 10⁻⁴ until the last updates). **The raw gradient norm fell from 0.68 / 0.80 / 0.58
  (updates 0–2) to 0.06 / 0.04 / 0.03 (updates 197–199) in both arms while the applied step stayed
  0.02.**
- Card §5 reading: **row 4** (ΔU inside the MEI by three orders of magnitude, neither `G_U` near
  0.05, τ saturated): this 0.02 / 200 movement attempt gave no useful learning signal; end this
  spend and return to the next object selection with the complete counterexample; no automatic
  4,000 updates, step sweep or warm-started heads; not a proof that the normalisation principle is
  wrong or the host unlearnable.
- Predictions: your working prediction (at least one package's U down by ≈ 0.05 against its
  initialization) did not happen; your stated strongest competing prediction (both arms still
  barely improve) held. The DM's primary (`G_U` ≥ 0.05 for one arm; ΔU inside MEI; τ all 40) was
  wrong on the first part; the DM's competing prediction (FLEX below C1P1 by 0.05) was wrong.
- Across the two objects: seed 17 / 0.0005 gave identical arms with displacement 0.005; seed 18 /
  0.02 gave indistinguishable arms with displacement 0.47 and no service change; the learned
  packages sit at their initialization's service level on both panels, about three times the
  unserved demand of the scripted nearest-beacon policy.

## Unknowns the DM cannot resolve locally

- Why 200 constant-norm steps that move the vector by 0.47 (2.2 % of the norm) leave every
  held-out cell's U within 0.003 of the initialization: whether the claim distribution is nearly
  invariant to this displacement (function insensitivity), whether the displacement is spent in
  parameters the claim decoder does not use, or whether the gradient itself is dominated by the
  manager's score term and not by the actor's claim logits. B02 recorded no per-tensor
  displacement, no claim-distribution statistics and no gradient decomposition (none were in the
  card).
- Why the raw gradient norm decays twenty-fold under a constant-norm step with flat returns (a
  baseline effect: the eight per-cell baselines converge to the cell means, so the advantage
  shrinks; the DM can name this as the obvious candidate but has not measured it).
- Whether any exposure at any step law moves the learned policy off its initialization's service
  level on this host (two laws, two seeds, 200 updates each: no); the definition card's 800 × 20
  program is background, not a measured curve.
- Whether FLEX's zero-initialised heads would diverge from C1P1 once the shared policy actually
  moves in service (they diverged in 14 scenarios here, with no service consequence).

## Options (DM ordering; the node decides)

1. **A gradient-decomposition A/RECON on the saved B02 state (no training)**: load the seed-18
   initialization and the two update-200 parameter files (retained), run one training block's
   forward/backward per model (64 episodes, the existing loss) and publish per-tensor gradient
   norms (manager score path versus actor claim path versus FLEX heads), the per-cell advantage
   magnitudes after baseline convergence, and the claim-distribution entropy of the initial and
   final policies on the training cells; cost from B02's per-update wall (≈ 0.3 s per block) plus
   evaluation ≈ 30 s; it answers which path carries the gradient and whether the advantage has
   collapsed, before another training spend; no polarity.
2. **A baseline-law B**: the same comparison with the per-cell baseline decay changed from
   0.95/0.05 to a fixed zero baseline (or a slower 0.99/0.01), keeping the 0.02 step; if the
   decaying gradient is the baseline converging, the advantage stays informative for longer;
   ≈ 150 s from the measured chain; a named learner-law change with a mechanism to test, not a
   magnitude sweep.
3. **A longer single-arm exposure at 0.02 with panels every 200 updates to 1,000** (the ladder
   you declined before B02, now posed after a movement counterexample rather than as a
   qualification): C1P1 only, seed 18, ≈ 5 × 70 s + 4 panels ≈ 400 s; answers whether service
   ever leaves the initialization level under this law.
4. **One more magnitude rung (0.2)**: ≈ 150 s; the DM lists it because it is cheap, and ranks it
   below 1–3 because the card's row 4 forbids an automatic sweep and 0.47 of displacement already
   produced no change.
5. **Park RCLE at this boundary** (everything committed and pushed; both parameter files, the
   initialization panel and the reference retained). The DM's argument against: two cheap,
   mechanism-bearing measurements (1, 2) remain, and the host runs end to end in minutes.

Questions for the node: which of 1–5 (or another bounded object) and why; if 1, the exact
quantities and their reading (what would make the actor-path gradient "negligible"); if 2 or 3,
the seed law, the panels and the reading against the initialization and the reference; whether
the two counterexamples (0.0005 identical, 0.02 indistinguishable) change the definition card's
training law or the family's claim ceiling; whether the initialization-level service of every
learned package so far (U ≈ 0.70 against the scripted 0.25–0.33) is a headroom record for
Portfolio purposes (the DM says: a diagnostic, not a threshold); any Portfolio consequence (the DM
proposes none).

## Cost facts

B02 chain 152.6 s of 1,500 s (build 3.0, focused 4.1, C1P1 71.5 including the 2,048-episode
initialization panel, FLEX 71.2, reference 1.5); B01 charged 144.3 s; per-update training wall
≈ 0.3 s at 64 episodes; a 2,048-episode learned panel ≈ 10 s (from the C1P1 arm's excess over
FLEX plus B01's arm walls; not separately timed). Options priced from these measured walls only.
This consultation adds zero exposure.
