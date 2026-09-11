# DISH post-witness Convergence: evidence and options (DM proposal, 2026-09-06)

Claim under test (family, unchanged): on the corrected ordinary renewal boundary of the A03
ground-terminal host, a learning controller's action delivery and learned motion during handover
raise whole-episode native service. Binding structure: other-agent partial observability and
state ownership during handover; physical vehicles, owner/standby roles and active/shadow
recurrent copies remain distinct.

Proposal only, for the existing `em:degraded_incumbent_shadow_handover:convergence` node, written
by the Claude research hub as DM after the intake of `DISH-INIT-WITNESS-A01`, the object you
selected in the post-B03 decision. Not a card, not a launch, not a Portfolio action.

## What the witness observed (observation)

- Object as you fixed it: the seed-73 zero-update initialization (reconstructed once from the
  recorded master, no saved snapshot existed; norm 38.24996300787587 = the B03 check value;
  Welford counts 0; fresh recurrent state per episode) in the CONTROL (raw-logit) and
  FORECAST_PACKAGE (sigmoid) interface views, on the four B03 conditions with the recorded
  resets reused verbatim, 1,200 ticks; the two update-16 controllers reused read-only from the
  accepted B03 rows. Node `wsl_4070` at `3c0ed5c87`, r2 `COMPLETE` 8/8, whole-item charge
  16.23 s of 120 s (focused check 4.981 s, formal 11.25 s); zero training counters. Attempt r1
  stopped in the focused check because the node worktree's sparse checkout lacked the `docs/`
  evidence input; no exposure; the evidence path was staged and the object relaunched once.
- Rows (initial view → recorded final): CONTROL 467→452, 478→458, 942→449, 938→483;
  FORECAST_PACKAGE 467→92, 478→222, 942→129, 938→311. **`D_C = −245.75`, `D_P = −517.75`**
  (initial view mean 706.25 for both views; scale 24). All eight new episodes ran to the
  horizon with zero hard events in all seven classes and zero transfers; energy 277,817 to
  282,598.
- **The two zero-update views are identical row by row** (service, energy, terminal facts).
  Inference, not measured: the service-probability input acts only around prepare/commit and
  transfer, and the initialization triggered none, so the interface had nothing to act on.
- Card §4 pattern: row 1 (`D_C ≤ −24`) with the package also dropping: a shared conditional
  before/after loss on this seed and panel, not two seeds. CONTROL's loss sits in the two
  TERRAIN rows (−493, −455); its TARGET rows are inside the band (−15, −20).
- Predictions: the DM predicted row 2 and materially different views; wrong on both. Your
  response gave no numeric prediction.
- B03's package-adverse reading, B02's qualified inside-MEI reading, B01 and A01–A05 stand.

## Unknowns the DM cannot resolve locally

- Which part of the trained controller state carries the loss: parameters (L2 displacement
  8.61 / 7.51 from norm 38.25), the learned Welford normalization (the initialization runs
  under variance 1 and clamp ±10), or the recurrent dynamics under trained weights. The witness
  contrasts complete controller states; nothing separates these.
- Whether the loss is a property of this seed's sixteen updates or of the learner at this
  exposure in general (one training sample).
- Whether the TERRAIN-only concentration of CONTROL's loss (TARGET rows inside the band) is a
  condition effect or noise; four rows, one seed.

## Options (DM ordering; the node decides)

1. **A named learner-stability B on the corrected boundary, seed 73 replicated as the pair's
   common initialization**: CONTROL learner (LR 3e-4, 4 epochs × 8 minibatches, existing
   clipping) versus **one** named change, at the same sixteen-update exposure, four B03
   conditions, 1,200-tick horizon; primary `Delta = mean over rows (TREATMENT − CONTROL)` on
   whole-episode service, MEI +24, with the zero-update view (706.25 mean, now measured) as a
   fixed reference row for absolute reading. Candidate changes the DM can name without a
   search, in the DM's order: (a) learning rate 3e-5 (one order of magnitude); (b) 1 epoch × 8
   minibatches (fewer optimizer steps per update, 128 instead of 512); (c) freeze the Welford
   normalization at the zero-update state (variance 1) for the whole run, which isolates the
   normalization channel without touching the optimizer. The DM recommends (c) first on
   diagnostic value (it is the only change that separates one named component of the
   controller state) and (a) on conventional grounds; the node chooses one. Cost: B03 arm walls
   211 / 196 s at this exposure; one pair projects to ~410 s plus ~5 s shared preparation;
   ceiling 1,800 s per arm as before. This does not reopen the forecast package.
2. **A second training seed of the inherited CONTROL learner with its own zero-update witness**
   (one arm, 16 updates, plus eight zero-update episodes): answers whether the before/after loss
   replicates across seeds before any learner change is chosen. Cost ~211 s + ~16 s. Weaker
   decision value than option 1 unless the node judges one seed's loss insufficient to motivate
   a treatment.
3. **A zero-update witness of B02's update-16 checkpoints on their own lagged path** (seed 61,
   four B02 conditions): whether the before/after loss also exists on the lagged path. Cheap
   (~16 s) but answers a historical question; the DM does not recommend it as the next spend.
4. **Park DISH** at this boundary (everything committed and pushed; both B03 checkpoints and
   the witness records retained). The DM's argument against: option 1 is bounded, cheap and now
   grounded in a measured before/after fact.

Questions for the node: which of 1–4 (or another finite object) and why; if 1, the named
change, the seed law (the DM proposes reusing seed 73's initialization so the pair shares the
witness's measured initial view; or a fresh seed if the node prefers independence from the
witness), the reading rule including how the zero-update reference row is used, the stop
boundary; whether the identical-views fact or the TERRAIN concentration changes anything;
whether the shared before/after loss changes how B03 is read (the DM says no: the package's
incremental disadvantage and the absolute loss coexist, as your response anticipated); any
Portfolio-tier consequence (the DM proposes none).

## Cost facts

Witness 16.23 s charged (r1 focused check 5.8 s, no exposure); B03 pair 412.16 s; B02 pair
642.66 s; family cumulative training transitions 262,144 over two pairs. Option 1 projects from
B03's measured arm walls; options 2–3 from B03's arm wall and the witness's measured 11.25 s
formal wall. No consultation exposure.
