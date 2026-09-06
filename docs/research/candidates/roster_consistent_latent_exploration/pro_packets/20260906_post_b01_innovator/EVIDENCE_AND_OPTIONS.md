# RCLE post-B01 Innovator: evidence and options (DM proposal, 2026-09-06)

Claim under test (direction, unchanged): on the frozen TBCFV rotating-perimeter host, a persistent
common plan package (C1P1-COMMON-PERSISTENT) recovers service after a roster boundary faster than
the strictly containing FLEX-REKEY package under matched information, communication, RNG,
parameters, interaction, update and model-selection exposure. Binding structure: variable roster
(6/10 training, 8/12 held-out) with in-episode membership events; a shared plan latent that
survives the boundary versus one re-keyed at the boundary.

Proposal only, for the existing `em:roster_consistent_latent_exploration:innovator` node, written
by the Claude research hub as DM after the intake of `RCLE-TBCFV-B01-PERSIST-VS-FLEX`, the first B
you opened. Not a card, not a launch, not a Portfolio action.

## What B01 observed (observation)

- Object as you fixed it: seed 17, one paired training replicate, 200 complete updates × 64
  episodes per arm (12,800 training episodes, 819,200 ticks), update-200 parameters evaluated on
  256 episodes per held-out cell (2,048 per arm), INDEPENDENT-NEAREST reference on the same
  2,048 scenarios, MEI τ 4 / U 0.05. Node `wsl_4070` at `4d40621e0`: first POSIX native build of
  TBCFV (`g++-13`, `/fp:strict`-equivalent flags), Linux oracle tests 23 passed, executability
  64 scripted episodes in 0.057 s; C1P1 62.0 s, FLEX 69.8 s, reference 1.5 s, all `COMPLETE`;
  whole pair 144 s of the 5,400 s budget; memory admission before every step; the FLEX arm
  validated the C1P1 summary's identity and exposure before training.
- **Primary `Δτ_B01 = 0.0` exactly (SE 0.0)**: τ = 40 (the censoring code) in every one of the
  2,048 held-out episodes of both arms; U 0.6929 (8→12) and 0.7181 (12→8) in both arms; every
  per-cell mean and every paired scenario identical across arms to all printed digits; training
  curves identical (episode Y 0.287 → 0.289 over 200 updates). Reference: τ=40 fractions
  0.95–1.0, U 0.233–0.336 (the nearest-beacon heuristic leaves far less unserved demand than
  either learned arm).
- Identical initial parameters (norm 21.186), `parameter_delta_norm` exactly 0.0005 on every
  update (the registered fixed-norm step), final displacement 0.0051249534 (C1P1) versus
  0.0051249677 (FLEX): the arms' trajectories differ at 1.4e-8, so the FLEX pathway executed.
- Engineering fact from a read-only code check (not a reproduction): the fixed-norm
  direction-normalized step (0.05 × 0.01 = 0.0005) bounds 200 updates to 0.1 total displacement
  from norm 21.19; FLEX's two zero-initialized update heads receive gradient only through the
  ACTIVE_CONTINUATION half of the training cells; and the discrete claims are drawn by
  inverse-CDF sampling against uniforms whose hashed address excludes the arm name (the card's
  "no RNG substream"), so a different claim requires the tiny probability perturbation to
  straddle the shared draw, which did not happen in roughly 10^5–10^6 decisions. Identical
  outcomes are expected by construction at this budget; not a wiring failure; not quarantined.
- Reading (card §5): rows 3 and 4 at their extreme (inside MEI; τ almost all 40 → mixed /
  undecided). DM primary prediction (inside-MEI, τ=40 fractions > 0.5, "the fixed step moves the
  policy little") confirmed at its extreme; the competing prediction wrong; your prospective
  judgement ("both arms may barely learn at 200 fixed-norm updates") held. Not inferred:
  equivalence, zero effect, closing RCLE, "persistent state has no value".
- The DM did not launch the card's default second seed: at this budget and step law it would
  reproduce the identity for the same mechanical reason.

## Unknowns the DM cannot resolve locally

- What exposure or update law lets either learned arm leave the near-initialization six-way
  claim distribution at all (the learned arms never reached the four-tick recovery condition;
  U 0.69–0.72 against the heuristic's 0.23–0.34). The card's full program (800 updates × 20
  blocks) is scale context, not a measured learning curve.
- Whether the fixed-norm step (a definition-card law) is itself the obstacle, or only its
  0.0005 magnitude at 200 updates; changing the step law is a change to the frozen learner and
  needs your authorization as a new outcome-informed object.
- Whether FLEX's zero-initialized heads, once training moves the policy, differ from C1P1 at
  all before the heads themselves have learned (the containment is policy-functional).

## Options (DM ordering; the node decides)

1. **A learning-amount ladder before any treatment comparison (A/RECON on one arm)**: C1P1 only,
   seed 17, the same fixed-norm learner, at 1,000 and 4,000 updates (or 800 as the card's block
   unit), evaluated at each checkpoint on the same 2,048 held-out scenarios, with the reference
   row; question: at what update count, if any, does τ leave 40 on the active paths and U fall
   toward the heuristic's level? Cost from the measured 62 s per 200 updates: ~310 s and
   ~1,240 s of training plus ~10 s evaluation per checkpoint; no treatment comparison, no
   polarity. The DM recommends this first: it decides whether the persist-versus-flex B can be
   asked at any budget under the frozen learner.
2. **A learner-law B at the same 200-update exposure**: C1P1 versus FLEX with a named change of
   the step law (plain gradient step with learning rate 0.01 and no direction normalization, or
   the same fixed-norm step with magnitude 0.02 instead of 0.0005), one paired seed, same
   evaluation; MEI τ 4 / U 0.05; ~150 s per pair from measured walls. Outcome-informed change
   of the frozen learner; the DM does not recommend choosing the magnitude by trial.
3. **B01 at a larger fixed-norm budget**: C1P1 versus FLEX at 4,000 updates each (the card's
   next rung), one paired seed, ~1,300 s per arm from measured walls; risks repeating the
   identity if 4,000 × 0.0005 = 2.0 still moves a norm-21 policy too little.
4. **Warm-started FLEX heads**: FLEX's final layers initialized non-zero from a named law so
   the arms differ from update 1; this changes the containment property the definition card
   proves and is a different object; the DM does not recommend it before option 1.
5. **Park RCLE** at this boundary (everything committed and pushed; both `parameters.pt`
   retained on the node). The DM's argument against: the host now runs end to end on the node
   in minutes and the learning-amount question is cheap.

Questions for the node: which of 1–5 (or another finite object) and why; if 1, the exact
update ladder, checkpoints, seed, what "leaves 40" means as a stop/continue rule, and the cost
cap; if 2 or 3, the named law or budget, seed count and reading; whether the identical-arms
fact changes how the TBCFV definition card's fixed-norm step should be read; any Portfolio-tier
consequence (the DM proposes none).

## Cost facts

B01 pair 144.3 s charged (preparation 11 s, arms 62.0 + 69.8 s, reference 1.5 s); native build
5.09 s cold on the node; per-update training wall ≈ 0.31–0.35 s at 64 episodes per update;
held-out evaluation 2,048 episodes ≈ within the arm walls (not separately timed). No
consultation exposure.
