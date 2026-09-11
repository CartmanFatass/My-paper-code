# RCLE post-B02 Innovator intake — 2026-09-06

Direction `roster_consistent_latent_exploration` (RCLE), node `em:roster_consistent_latent_exploration:innovator`.
Intake by the Claude research hub as DM. Provenance label **PRO_FINAL** (direction tier). Owner
instruction of 18:11 PDT ("finish this batch, then write the handoff, advance nothing further")
applies: this intake **records** the decision and freezes no card, implements nothing and launches
nothing; the resume procedure is in `docs/research/portfolio/HANDOFF_20260906_CLAUDE.md`.

## 1. Provenance

- Request `2026-09-06-rcle-post-b02-innovator-02` (packet `pro_packets/20260906_post_b02_innovator/`,
  TASK.md at `4eebef120`, evidence reference and delivery base `f6ba67cd7`). The first request (`-01`,
  TASK `5f9f62e1a`) pinned reference `5b58821af`, where the three packet aux files did not yet exist;
  Pro reported three 404s and formed no decision (kept as `TASK_r01.md` / `HANDOFF_r01.json`; its reply
  archived as the `-01` short receipt). Cause: hub error, corrected by rebuilding at `f6ba67cd7`.
- Response delivered by Pro at commit `6c0d1ca55` on `codex/pro-rcle-post-b02-20260906` (parent
  `f6ba67cd7`, "docs: deliver RCLE post-B02 Innovator frozen-state decision"), path `archive/RESPONSE.md`,
  29,964 bytes, sha256 `8339eef9da368cd76d0d…` (hub readback at the immutable commit; full hash in
  `archive/TRANSPORT_FACTS_CLAUDE.json`).
- Pro read the task at `4eebef120` and every listed path at `f6ba67cd7`; the two large arm summaries
  came back with `encoding=none` and were fetched through the blob interface but not independently
  decoded in full, so the aggregate numbers were taken from the intake and `EXPOSURE_AND_COST.json`
  and the smaller reference summary was read directly. Zero code executed, zero state created.

## 2. The decision (transcribed)

**Direction-tier decision:** the narrowed form of the DM's option 1 as the only next object,
**`RCLE-TBCFV-A02-FROZEN-SCORE-ALLOCATION`, class A/RECON**: on B02's common initialization and the
two update-200 states, measure the contributions of the manager score and the actor (claim) score
to the actual joint gradient, the per-tensor-group displacement, and the change of the claim
distribution on fixed inputs; no parameter update, no baseline change, no added training, no new
learner comparison. Two pre-specified training-domain probe blocks, 512 new episodes in total, at
most 32 derivative evaluations; **300 s** cap on the complete logical invocation. Not a proof of a
unique mechanism, not a "C1P1 must first learn" gate, not an upper reference, not a qualification
for an ordinary B; an undecided outcome does not forbid an independently valuable B. This round
authorizes only this A: no follow-on B, source change or launch, no C freeze, no Portfolio change,
no full five-arm twenty-block program.

Reason for changing last round's priority: the "buy a movement-amount intervention" ordering has
its counterexample (0.02/200 moved the parameters 0.47 without approaching the intended service
change); a frozen-state measurement with explicit branch readings decides whether the next change
should target gradient allocation, the baseline's finite-sample effect, or another still
unlocalized learning problem; the two cheap candidates (zero baseline, 0.2) each confuse a
mean-versus-information or a movement-versus-function distinction.

Object contract as fixed by the node (for the card to be written on resume):

- **States.** Host, observation, reward, decoder, both packages and FP64 unchanged. Only seed 18's
  three parameter sets: common θ0, C1P1 θ200, FLEX θ200, forming **four logical configurations**
  C1P1-init, FLEX-init, C1P1-final, FLEX-final (FLEX-init added so that identical forward policies
  are not mistaken for identical backward graphs; not a training arm). Final parameters loaded from
  the retained B02 files with provenance recorded; θ0 loaded from the retained initial tensors, or
  rebuilt by the same fixed law from the seed-18 key with the recorded identity/norm checked and
  marked "rebuilt"; no retraining to obtain a starting point or baseline, no seed change, no
  inference of a "better" start from final weights. Pro has not loaded these states; availability is
  confirmed on the executing node.
- **Sampling.** Two new fixed probe block labels `19001`, `19002` under a new purpose domain
  `post-b02-frozen-probe` derived from the seed-18 root key (not new training seeds). Each block is
  exactly 64 episodes, eight per training cell, roster {6, 10} with static and 6→10 / 10→6, both
  epoch conditions; the four configurations share the same exogenous scenarios and semantically
  paired randomness; arm names never select sub-streams; no forced identical visited state after
  policy divergence; both blocks bought in advance. Total **4 × 2 × 64 = 512 episodes, 32,768
  environment ticks**, recorded as measurement exposure (not "zero exposure" because there is no
  optimizer step). No new held-out panel, no thresholds from old held-out scenarios, no sweep of
  parameters, step or baseline; at most four model instances, graphs processed sequentially via
  the existing single-model constructor; all eight cells and both blocks reported.
- **Primary: path gradients of the actual loss and tensor displacement.** With the original stopped
  sampling and stopped advantage on each fixed 64-episode graph, `s_M,e` = mean used Normal score,
  `s_A,e` = mean used claim score (the card's separate means kept, no re-weighting by agent count):
  `L_M = −mean_e[(Y_e − b_cell(e)) s_M,e]`, `L_A = −mean_e[(Y_e − b_cell(e)) s_A,e]`, `g_M = ∇L_M`,
  `g_A = ∇L_A`, `g = ∇(original joint loss)` via `autograd.grad`, never `step`. Report the three full
  norms, cosine between `g_M` and `g_A`, the cancellation reading `‖g‖/(‖g_M‖+‖g_A‖)`, and the
  residual `g − g_M − g_A` against an explicit FP64 tolerance as a local identity check (no new guard
  framework); zero vectors reported as undefined/zero, no epsilon-made ratios. Project each gradient
  onto five exclusive tensor groups: the two set encoders; the four `manager_*` layers; the three
  `pointer_*` layers; `common_update_hidden/final`; `agent_update_hidden/final` (per-tensor norms
  within groups, group squares covering every registered parameter; no-graph/no-gradient and
  numerically zero distinguished). For the two final states also compute per-tensor and per-group
  `‖θ200 − θ0‖` and the real `‖θF,200 − θC,200‖` from loaded weights (not the difference of the two
  recorded displacement norms). This answers where the current gradient and the observed net
  displacement fall; it is not a historical decomposition of 200 updates.
- **Baseline handling.** Initialization uses b = 0; final states use each arm's actual eight-cell
  b200, frozen during the measurement: read from retained buffers, or rebuilt from that arm's
  full-precision per-update training-cell Y means by `b_(k+1) = 0.95 b_k + 0.05 mean(Y_k)`, b0 = 0,
  marked loaded/rebuilt with precision limits; never replaced by the probe blocks' return means. If
  neither buffers nor curves suffice, the baseline-sensitive part is reported undecided and the
  independent measurements (zero-baseline gradients, displacement, conditional distributions) are
  kept; B02 is not rerun. On each final state, on the **same trajectories and graph**, set b = 0 and
  compute `g_M^0`, `g_A^0` and their sum (weights only, no new trajectories or model change); report
  per-cell Y mean/std, original baseline, advantage mean/RMS/std, and the total-norm ratio and
  direction cosine between original and zero baseline. A larger norm alone does not mean better
  signal.
- **Backward cap.** At most **32 derivative evaluations**: 3 per initialization configuration-block
  graph (M, A, joint; 12) and 5 per final graph (M, A, joint, zero-baseline M, A; 20); `autograd.grad`
  counts as backward. No learning update of any parameter, baseline or random procedure.
- **Companion: fixed-input library.** From C1P1-init's two probe blocks, the first two episodes per
  cell by scenario index, claim moments at ticks {0, 24, 28, 60}, the first and last two active
  members by public ordering: **2 × 8 × 2 × 4 × 2 = 256 fixed input points** (raw public/individual/
  candidate features and the z in use), no new episodes. On the three parameter snapshots recompute
  the six-way probabilities through each snapshot's own encoder and pointer (no reuse of old encoded
  vectors), z fixed at the C1P1-init value; **768 probability vectors**. Report per-cell, per-block
  entropy means and the total-variation distance `TV = 0.5 Σ_a |p_a − q_a|` (final vs init; FLEX-final
  vs C1P1-final), mean and max; no argmax substitution, no checkpoint selection by the library. It
  identifies only the common encoder/pointer conditional change at fixed z and inputs, not the
  full-policy effect through manager or FLEX heads, not the visit distribution, not a causal service
  decomposition.
- **Descriptive reading scale (no algorithm-effect MEI registered).** `r_A = ‖g_A‖/(‖g_M‖+‖g_A‖)`,
  `r_P = ‖P_pointer g‖/‖g‖`. Only when, under the original baseline, **both probe blocks satisfy
  r_A ≤ 0.01 and r_P ≤ 0.01** may a snapshot be described as "actor-score contribution and pointer
  update allocation very low in these two samples" (never "actor has no effect"); 1 % is a strict
  pre-chosen marker; for a hypothetical 0.02-normalised update r_P ≤ 0.01 means a pointer projection
  ≤ 0.0002, which is not applied and not turned into a return change. Also report the weaker
  manager-dominant reading r_A < 0.5 separately; direction cancellation, shared encoder and FLEX-head
  projections read together with the ratios; block or state disagreement is kept as
  heterogeneous/undecided. Fixed-input mean TV ≤ 0.01 per block may be called "small average
  conditional change on this library" with all cells and the max shown. Zero-baseline results report
  continuous changes only; no "must reach k×" gate for a next B.
- **Pro's working prediction.** At least one final snapshot shows r_A < 0.5 on both blocks with small
  conditional pointer change; not predicted to pass the 1 % marker. Refuted if no final snapshot
  meets both, or the actor path is not weak and TV is not small; the stronger competing explanation
  is that the actor receives substantial gradient and changes parameters and probabilities, but
  direction noise, mean-score credit assignment or coordination structure does not convert to
  service.
- **Result branches (each ends the A and returns to object selection; no conditional B hidden in the
  card).** (1) Low actor / low pointer allocation on both blocks and small TV: raise "joint gradient
  allocation or pointer conditional sensitivity" as the next named change's motivation; lower a blind
  global step increase (not a proof of no gradient over training, nor that re-weighting improves U).
  (2) Original vs zero baseline changes direction, cancellation or actor projection, not only scale:
  the baseline's finite-sample role merits a separate test; a reason for a future explicit baseline B
  (frozen zero-baseline gradients are not zero-baseline training; option 2 not auto-executed).
  (3) Actor allocation not low, or conditional probabilities clearly moved while service stays flat:
  rejects the simple "claim distribution unresponsive" reading; keeps credit assignment, noise and
  coordination-learning open (no unlearnability, no unbounded search). (4) Block conflict or no strong
  reading: publish undecided and end (no extra samples until a convenient reading; undecided is not
  a rule against an ordinary B). (5) File identity, numerical-graph or resource problems: stop only
  the dependent measurements, keep independent reads; no retroactive quarantine of B01/B02; no retry
  budget.
- **Cost.** Three parameter sets, four package-state graphs, two 64-episode blocks, 512 episodes,
  32 derivative evaluations, 768 six-way forward probabilities, tensor differences and statistics,
  plus loading, preparation and publication; 512 episodes are 2 % of a 200-update pair's 25,600
  training episodes but not a runtime ratio. Measured background only: B02 chain 152.6 s, B01 144.3 s,
  C1P1 arm 71.5 s (with the initialization panel), FLEX 71.2 s, reference 1.5 s; **no record times a
  2,048-episode learned panel on its own**, so the DM's "≈ 10 s per panel" and "≈ 30 s" were not
  measured and are withdrawn; 0.3 s per update is not the cost of repeated backward graphs. **300 s is
  the cap on the complete logical invocation, not a forecast**, not a balance from B02's 1,500 s or
  the 2,700 s threshold; loading/rebuilding, preparation, all measurements, summary and publication
  included; one invocation, no worker split, stop at the cap keeping partial records, no extension,
  probe replacement, retry or node change; unknown cost stays unknown, no calibration experiment.
  CM scope: a narrow measurement entry on the existing model and episode paths (sequential graphs,
  existing PyTorch derivatives and tensor ops, wall time and peak RSS only), within 2,000 / 600 lines,
  no registry, guard, validator or telemetry framework; result-bearing execution remote-first on
  `wsl_4070`, exact committed and pushed source, detached supervision, fresh ≥ 4 GiB admission.

## 3. Corrections to the DM recorded by the node

- A falling raw gradient norm does not mean a falling normalised update: B02's entry applied 0.02
  at every one of 400 updates; normalisation removes the overall scale, so what can change is
  direction, noise and path allocation, which is what the A measures.
- A baseline approaching the cell mean does not destroy useful advantage information: for a
  state/cell-conditional, action-independent, stop-gradient baseline the subtraction leaves the
  expectation of the un-normalised score estimator unchanged and mainly changes finite-sample
  variance and cancellation; but under the non-linear `g/‖g‖` the expected normalised direction can
  differ between baselines, so zero baseline is a studyable change whose "keeps information longer"
  claim cannot be asserted a priori. The A measures the frozen-graph counterfactual only.
- Manager and actor paths cannot be split by parameter name into two exclusive piles: both scores
  can place gradient on the shared encoders, and FLEX's deterministic event-head map stays in the
  actor input; decompose by loss term first, then project onto actual tensor groups; a zero-valued
  head start does not imply zero gradient; identical forward policies do not imply identical
  backward graphs.
- τ leaving 40 is not a general "learning happened" gate: the reference lowers U a lot with τ=40
  fractions 1.0 and 0.973.
- B01 and B02 changed seed and law together, so they are neither two repeats of one law nor a paired
  causal estimate of the step size. B01 had no shared initialization panel; the two objects must not
  be narrated as both having one.
- The ≈ 0.425 gap between the scripted reference (two-path U ≈ 0.282) and the learned arms (≈ 0.707)
  on the B02 panel is a **diagnostic headroom record for Portfolio purposes** ("a specific improvement
  space left relative to these learned results"), not an identified H_A1: the reference is not an
  upper reference and neither package is a competent tuned generic baseline; τ's proximity to the
  failure-code cap should be recorded as a resolution limit.

## 4. Reasons for not choosing the other objects

The single-arm 1,000-update ladder is a legitimate B if it answers its own bounded learning
question (a single arm does not make it an A), but it needs up to 64,000 training episodes and
several panels under a law that has shown no service gain; not a priority now. Another magnitude
rung, warm-started heads or a baseline change are outcome-informed new objects that get no
automatic authorization from cheapness, unspent caps or old card defaults. Parking RCLE exceeds
what two small-budget, different-seed counterexamples support. Strongest objection to the choice:
the A cannot show a service improvement; two frozen states and two blocks may not represent
mid-training; gradient norms are parametrisation-dependent; the library fixes the latent. The node
chose the A anyway because the motivations of the two cheap changes cannot yet be told apart, and
a few concrete measurements narrow the next change's reason and can end cleanly without a
favourable reading.

## 5. Conflict check (AGENTS.md §2)

None found. The A is a bounded measurement object with named states, sampling law, exposure,
readings and a cap; it changes no training law, no frozen meaning, no Portfolio state; the
definition card's 0.0005 law stays the frozen law of the original object and B02 stays an independent
named change. The response is complete and final for this node. The DM's timing projections
(≈ 10 s per panel, ≈ 30 s for option 1) are withdrawn as unmeasured.

## 6. Decisions this intake produces

Direction tier: recorded as **PRO_FINAL**. Under the owner's 18:11 PDT instruction the hub takes
**no** executing step: no card `RCLE_TBCFV_A02_FROZEN_SCORE_ALLOCATION_...` is frozen, no CM objective,
no Grok Build task, no launch. On an owner-directed resume the ordinary sequence applies (card and
CM objective from §2 → Grok Build measurement entry → hub review → operator launch on `wsl_4070`
with fresh admission → tracker → result intake → this node again). Owner prediction slot: not taken
(unattended). DM prediction for the record (not binding): branch (3), the actor path receives a
non-negligible share (r_A between 0.1 and 0.5) and TV on the library is small but above 0.01 on at
least one block.

Records: brief `owner/briefs/roster_consistent_latent_exploration/2026-09-06_post-B02-innovator.md`;
ledger row; DIRECTION addendum and PORTFOLIO row (clerk pass); handoff
`docs/research/portfolio/HANDOFF_20260906_CLAUDE.md`.
