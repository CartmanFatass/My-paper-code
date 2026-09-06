Claim: On the frozen TBCFV rotating-perimeter host, from identical initialization and identical small training exposure with a forty-fold larger fixed-norm joint update, the persistent common-plan package may leave less cumulative unserved demand after an unseen-roster active-continuation membership change than the same-information strictly containing FLEX package, and either package may or may not improve on its own initialization.
Binding MARL structure: agent-count change and coordination recovery after a roster change; one shared parameter vector across rosters, no per-N head, public state only.

# RCLE TBCFV B02 fixed-norm 0.02 — science card

Date 2026-09-06; object `RCLE-TBCFV-B02-NORM-0p02`; **B / EXPLORE**, outcome-informed after B01.
Selected by the complete post-B01 Innovator response
(`pro_packets/20260906_post_b01_innovator/archive/RESPONSE.md`, commit `b871d7a0d`), **PRO_FINAL**,
intake `RCLE_TBCFV_POST_B01_INNOVATOR_INTAKE_20260906.md`. The Claude research hub (Root and DM)
freezes this card under the owner's standing unattended delegation, after a read-only code map
of the B01 entry and the registered step function (§2 records what it found). No empirical
outcome has been observed for this object. B01 (`RCLE_TBCFV_B01_PERSIST_VS_FLEX_SCIENCE_CARD_20260906.md`)
stays valid in its mixed/undecided reading and is not repeated, continued or re-read by this
card; the definition card stays definition-only and keeps its 0.0005 law as historical meaning.

## 1. Question and ceiling

Under the definition card's host, from identical initialization and identical exposure, with the
sole learning-law change of a **0.02** fixed-norm full-vector step per nonzero joint update, does
`C1P1-COMMON-PERSISTENT` leave less mean normalised unserved demand after an active-continuation
roster change than `FLEX-REKEY`, and does either arm improve on the shared initialization's own
service on the same panel? Ceiling: an exploratory signal or counterexample on **one new seed, one
new step size, the fixed toy and the listed cells**. It is a minimal investment that observes
native service learning and the package difference at once; it is not a sufficiency guarantee for
0.02, not "a suitable learning rate was found", not a repair or repeat of B01, and not a proof
that the old step was the sole cause of B01's immobility. It establishes no commonality /
persistence single-factor contribution, headroom, stable superiority, arbitrary-roster
generalisation, competence against a tuned generic baseline, C-level inference, or deployment
conclusion. Predecessor-host polarity does not transfer; `H_A1` stays unidentified.

## 2. Host, arms and the sole learning-law change

Host exactly as the definition card and B01 card §2: 120 sectors, six beacons, H=64, t_c=24,
six always-legal claims, the original `MOVE-TO-CLAIM` decoder, demand/membership/epoch processes
and timing. Training cells per update `6→6, 10→10, 6→10, 10→6` × `ACTIVE_CONTINUATION, NEW_EPOCH`,
eight episodes each (64 per update); held-out cells `8→8, 12→12, 8→12, 12→8` × the two
conditions. One parameter vector across rosters; no 8/12 training, no N-specific head; low-level
control, information, communication, event order, loss and reward unchanged.

Arms: exactly `C1P1-COMMON-PERSISTENT` and `FLEX-REKEY`; both the 26,161-scalar maximum
structure, the same initial tensor and the original Xavier / zero-bias law; FLEX's two final
update-head layers start exactly at zero and train, C1P1 hard-masks them; old-epoch samples stop
gradient; FLEX's deterministic update head keeps the original actor gradient path; eight
per-cell baselines per arm, independent, updated 0.95/0.05 strictly after the joint parameter
update. No Adam, momentum, entropy, auxiliary reward, return normalisation, warm start, or
per-parameter-group learning rate.

**Sole change: for the complete parameter vector, if the raw gradient `g` is nonzero,
`θ ← θ − 0.02 · g / ‖g‖₂`; if `g = 0`, no update.** Exactly one backward and one joint update per
complete 64-episode block; a block is never split into several optimizer steps; both arms use the
same law with full-vector normalisation (no FLEX-head-only amplification). The B01 / definition
card law (`0.05 g/‖g‖` direction, `0.01` rate, norm 0.0005) keeps its historical meaning; this card
overrides only this B's update amount, inside this object's own namespace. Not "global constant
changed, B01 repeated".

**What the code map established (engineering fact, binds the objective).** The registered step
`registered_plain_sgd_step(model)` (`roster_consistent_latent_exploration_tbcfv/models.py:374-398`)
takes no norm argument, reads the module constants `LEARNING_RATE` and `GRADIENT_DIRECTION_SCALE`
bound at import, and stamps the audit's `parameter_delta_norm` from the constant
`NONZERO_UPDATE_NORM`; `apply_registered_block_update` (`:408-425`) calls it, and B01's
`execute_b01_training_update` (`_tbcfv_b01/study.py:386-450`) publishes that constant into every
curve and into `configuration["nonzero_update_norm"]`. There is no legitimate call-time override.
The B02 entry therefore carries **its own copy of the step and block-update functions,
parameterised by the prescribed norm (0.02)**, reusing `exact_advantage_loss`, the validated
cell layout and `BASELINE_DECAY` unchanged; its audit records the prescribed norm **and the L2
norm of the delta it actually applied** (one norm over the parameter vector per update, no
framework). Calling the registered functions, or constructing a configuration value the step
never reads, would silently publish 0.0005; the focused check pins the new function on nonzero and
zero gradients and the published values.

## 3. Seed, pairing and exposure

One new paired training seed **18**; B01's seed 17 is neither continued nor selected. Root key =
SHA256 of the ASCII string `RCLE-TBCFV-B02-NORM-0p02/seed/18`, hex
`fd3cd5cf0f085e880a424f7a546017a62d300676e385e1174676b9f4c14e5093`; block digest by the existing
`_derive_block_digest(key, identity="RCLE-TBCFV-B02-NORM-0p02", index=0)`, hex
`82593ad701533212112f1e29d22f3d0b701fd8360b88d9bfcb61ac565f6b2210` (derived by the hub from the
existing functions; a new value, not an alias of B01's `a67b0144…`). Both arms share the
initialization (one common-initial-parameter draw with no arm field, copied onto both arms), the
exogenous membership and physical randomness, and the plan / actor draws pairable under the
original semantics; the arm name selects a draw substream only where the original law already
does (episode-execution draws carry `arm_only_variable`); no random numbers are decoupled to
manufacture a difference and no actions are forced equal after divergence. Training and
evaluation stay on the original coordinate domains. The physical / fixture / event
materialisation of a held-out cell depends only on the key, block, cell and index, so the same
seed-18 panel serves the shared initialization evaluation, both final evaluations and the
scripted reference, aligned by scenario. B01's seed-17 panel is not reused.

Each arm trains from the initialization to the **200th completed update × 64 episodes = 12,800
training episodes (819,200 ticks)**, at most 200 backward / joint-update calls, and evaluates the
update-200 parameters only on **256 episodes per held-out cell (2,048 per arm, 131,072 ticks)**.
Per-update training summaries (Y, U, τ per cell and overall) kept for all 200 blocks, display
points every 25; no mid-way checkpoint choice, early stop or best-of selection. The two arm runs
form one paired training replicate. Record: completed updates, zero-update incidence, nonzero
count, initial parameter norm, prescribed and measured per-update delta norms, final
displacement (the path bound 200 × 0.02 = 4 is an upper bound, never a displacement and never a
movement qualification), episode counts per cell, τ=40 fractions, failure codes; the
initialization helper's five allocated package models are recorded as allocations, separately
from the two training instances.

## 4. Shared initialization evaluation, final evaluation, reference and primary measurement

**Shared update-0 evaluation.** Before any update, the C1P1 initialization policy is evaluated
once on the new panel, eight held-out cells × 256 episodes (2,048 episodes, 131,072 ticks), paid
inside the C1P1 invocation and published with it; FLEX's initialization is the same distribution
by the retained zero-head correspondence and is not separately evaluated. It is the common
starting point of both arms for `G_U`; it is not used to decide whether to train, to tune the
step or to change the seed, and it is not a separate "pass first" object.

**Final evaluation.** Per episode exactly the definition card's endpoints: `u_t` normalised
unserved demand; `τ` = first offset `h ∈ 0..36` with four consecutive zero-unserved ticks from
`t = 24 + h`, else 40 (a bounded score with a failure code, not an uncensored mean);
`U = (1/40) Σ_{t=24}^{63} u_t`; `Y = 1 − (1/64) Σ u_t`; `F` descriptive. Intention-to-treat over
every assigned scenario; no episode, agent or interval excluded.

**Primary `ΔU` = mean over the two ACTIVE_CONTINUATION held-out paths `8→12` and `12→8` of
`(U_FLEX − U_C1P1)`**, paths equally weighted, the 256 scenarios of a cell equally weighted;
**positive favours C1P1, negative favours FLEX**; both arms' path means and the per-path
difference are published, never only the total. **Companion `G_U` per arm = mean over the same
two paths of `(U_init − U_final)`**, positive meaning less unserved demand than the
initialization. τ, τ=40 fraction, `40U` (cumulative normalised unserved demand, not raw service
units) on the same paths; τ / U / Y and F on all eight cells with the eight-cell mean as a
declared secondary description; NEW_EPOCH is not a pure "erase plan identity" contrast.
Naming U the primary is an outcome-informed measurement choice made openly after B01; it does
not repackage B01's zero as a U success, does not change the B01 card, and does not prove the
direction's full "faster recovery without demand harm" claim. Within-seed uncertainty:
cell-stratified paired-scenario Monte Carlo standard errors or descriptive intervals with
existing NumPy; ticks, agents, checkpoints and cells are not independent seeds; one paired seed
estimates no seed variance; no episode bootstrap or zero SE as stable superiority or equivalence.

**Reference `INDEPENDENT-NEAREST`** (every agent claims the nearest current beacon, ties to the
lower index, no plan latent): evaluated once on the **new seed-18 panel**, eight cells × 256
(2,048 episodes, 131,072 ticks); no training, search or rule change; scripted `Y` stays null with
its reason. It gives an achievable simple service level; it is not tuned-FLEX sufficiency, an
upper reference or headroom, and B01's seed-17 reference is not substituted for it.

## 5. Interpretation and predictions on record

**MEI: U absolute 0.05** (two normalised unserved ticks in the 40-tick window) for `ΔU` and for
each `G_U`; **τ companion MEI 4 physical ticks** (one claim period). Interest scales for this
object, not power guarantees, significance lines or launch gates. Reading (from the response):

| Observation | Current change and advice | Not inferred |
| --- | --- | --- |
| `ΔU` ≈ +0.05 or more, no τ reversal reaching its 4-tick scale | a preliminary cumulative-service signal for the persistent package under this learner; prefer one new independent paired seed of the same configuration; keep per-path trade-offs | with τ still all 40, only a cumulative signal: no recovery-time superiority, non-inferiority, mechanism attribution or stable advantage |
| `ΔU` ≈ −0.05 or less, or a substantial reverse service / recovery trade-off | less support for restricting FLEX at this budget; a credible adverse result may also merit an independent repeat | closing RCLE; extrapolating one seed's result to all persistent states or budgets |
| `ΔU` inside the MEI, at least one arm's `G_U` ≈ +0.05 | native service learning is now observable, no material package difference; a same-configuration repeat may be weighed from curves and cost | equivalence; "learned something" as superiority over a generic baseline or full recovery |
| `ΔU` inside the MEI, both arms barely improved on the start, τ still saturated | this 0.02 / 200 movement attempt gave no useful learning signal; end this spend and return to the next object selection with the complete counterexample | automatic 4,000 updates, step sweep or warm-started heads; that the normalisation principle is wrong or the host unlearnable |
| paths disagree, U and τ conflict, or evaluation error spans the interest scale | mixed / undecided; keep means and all details | a cherry-picked path, metric or checkpoint |
| execution or readout the primary depends on is damaged | direct exception / exit / missing-quantity / count facts; only independently trustworthy narrow facts kept | any algorithmic polarity; automatic arm completion, retry or seed replacement |

These rows are the new B's interpretive narrative and investment advice, not C's frozen
significance rules. Later learning-performance follow-ups prefer one or two new independent
training seeds with all outcomes kept, outside this pair's allowance; no second object is opened
by this card. Direct counter-evidence to the selection: FLEX serving as well or better, or a C1P1
recovery gain with substantial U harm. Counter-evidence to the working prediction: no material
native service improvement of either arm relative to the common initialization, which limits
only this magnitude and budget.

Predictions:

- **Node (Pro), prospective, recorded:** the change may lower at least one package's mean U on
  the same panel by about 0.05 relative to its own initialization; the package-difference
  direction is unknown. Strongest competing prediction: both arms still barely improve, or the
  larger random updates lower native service.
- **DM (hub), prospective.** `G_U` of at least one arm ≥ +0.05 (moderate confidence: at 0.02 per
  update the 200 updates can move the vector by up to 4 against an initial norm ≈ 21, and B01's
  raw gradient norms were finite and non-degenerate), and `ΔU` inside ±0.05 with τ still almost
  all 40 (row 3; low confidence), because FLEX's update heads start at zero and receive gradient
  from only the active-continuation half of the training cells, so the two arms are predicted to
  stay close over 200 updates even when both move. Competing prediction: row 2, FLEX below C1P1
  by ≥ 0.05, because the larger step lets FLEX's freshly trainable heads perturb survivors'
  claims after the boundary.
- **Owner:** not taken (unattended).

## 6. Whole cost, route and stop

Design counts (arithmetic, not exposure): per arm 12,800 training + 2,048 final evaluation
episodes; both arms 29,696 episodes / 1,900,544 ticks; shared initialization panel 2,048 /
131,072; reference panel 2,048 / 131,072; **object total 33,792 episodes, 2,162,688 ticks**; two
real training instances, one paired seed, at most 400 backward / joint-update calls, zero-gradient
count listed separately. The algorithmic work is a fixed number of real episodes, per-claim-clock
scoring of six beacon candidates, and one graph retention / backward and one full-vector update
per 64 episodes; no `6^N` joint-action enumeration, trajectory tree, beam search, controller
search or hyperparameter grid; existing single-process / single-thread and batching boundaries.

Measured references at their scope: B01 C1P1 ≈ 62.0 s and FLEX ≈ 69.8 s complete arm walls
(including final evaluation), reference ≈ 1.5 s, preparation ≈ 11 s, charged ≈ 144.3 s, cold
build 5.09 s. They are order-of-magnitude references for a similar scale, not the measured wall
of the new law plus the initialization panel and not a guarantee; the added initial evaluation,
the changed update's real cost, checks and output overhead are unmeasured and not filled with
zero; no calibration experiment, thread sweep or second first-executability probe.

**Spending limits, chosen deliberately: at most 600 s per arm and seed for the complete logical
invocation** (import, actually paid compilation / initialization, the shared initialization
panel inside the C1P1 invocation, that arm's whole training, final evaluation, necessary checks
and full publication), **and at most 1,500 s cumulative execution wall for the whole object**,
including the actually paid build, the one focused check, the reference and merged publication,
each charged once where it belongs; sub-items cannot each fill up and then append tail work;
600 s is a conservative hard bound for this object, not a balance granted by the runtime
specification's 2,700 s toy threshold; it limits the risk of an unmeasured change and does not
claim the time is needed. The study reports its elapsed critical path and the sum of logical
invocation walls; B01's 144.3 s is not an end-to-end figure. Existing wall / RSS / CPU witnesses
are kept; no new telemetry service; a missing resource figure degrades only what depends on it.

Route: remote-first on `wsl_4070` from exact committed and pushed source, the existing detached
`agent-task` supervision, a fresh physical and effective memory admission ≥ 4 GiB immediately
before each invocation (no receipt reuse), single CPU thread, existing float64 and RNG /
batching semantics; no GPU, low precision, parallelism or node change. The POSIX native build
branch established by B01 on the node is reused; a rebuild, if actually paid, is charged once.
Admission failure, an inexecutable existing dependency or an implementation beyond ordinary
budgets returns a concrete engineering gap; no retry budget.

Launch: only the four §11.4 conditions; the machine-generated exposure line states the
200 × 0.02 = 4 path bound and B01's ≈ 21.186 initialization-norm reference, with the actual new
initial norm recorded in the charged invocation; no requirement that U fall, τ leave 40, FLEX
heads reach a norm or headroom be filled.

Stop: once learning starts, no outcome-driven early stop or configuration change; poor C1P1
service does not stop the FLEX comparison; the initialization panel does not change the 200
updates. Only technical problems terminate: the 600 s invocation or 1,500 s object limit,
concrete non-finite values, wrong reward / information / event semantics, a broken learning
chain or a required output. A mid-way stop reports completed counts truthfully and is not
renamed a completed object; no seed, step or automatic continuation change; a first arm too
damaged to form the pair does not spend the second arm's allowance; a damaged second arm keeps the
first arm's facts. Missing only the shared initialization evaluation: no `G_U`, but `ΔU` keeps its
meaning if both finals and their exposure are complete; missing only the reference: not re-run,
the package comparison not erased; such degradation is not full completion. An actual NaN is an
execution problem to repair; finite values with worse service are an interpretable adverse
learning result.

## 7. Launch preparation and bounded engineering handoff

**Engineering-scope §4 declaration: none of its default-prohibited machinery is needed.** CM
owns a thin B02 entry only: `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/`
(own parameterised step and block update, seed / identity constants, arm entry with the
initialization panel, ΔU / `G_U` publication, reference entry, all reusing B01's and the TBCFV
tree's functions by import), `scripts/run_rcle_tbcfv_b02.py` (≤ 600 lines), focused tests, and
the CM record; no edit to `roster_consistent_latent_exploration_tbcfv/**`,
`roster_consistent_latent_exploration_tbcfv_b01/**`, `scripts/run_rcle_tbcfv_b01.py` or existing
tests. Objective: `RCLE_TBCFV_B02_NORM_0P02_CM_OBJECTIVE_20260906.md`. Implementation by Grok
Build under the CLAUDE.md Grok Build route with hub review. One focused check tied to the changed
behaviour and the primary output: the new full-vector update on nonzero and zero gradients
(prescribed 0.02, measured delta norm, no update at zero); FLEX's update heads still receive
gradient while C1P1 still masks them; reward / τ / U semantics unchanged; the new ΔU, `G_U`, the
shared-start source, counts and final outputs readable; existing oracle and package checks reused
(the Linux oracle tests on the node as in B01); no new first-build / full-smoke / history
reproduction; `parameter_delta_norm` must not print 0.0005; no full-parameter telemetry framework.
Budgets: ≤ 2,000 new non-test source lines, runner ≤ 600, five-minute research tests; the 30 %
ratio is a review signal.

Output root `temp/directions/roster_consistent_latent_exploration/exp/tbcfv_b02_20260906/` with
`c1p1/` (including the initialization panel), `flex/`, `reference/`, `receipts/`, `timings/`;
keep per-update curves, final parameters, per-scenario τ / U / Y for the initialization panel and
both finals, τ=40 counts, failure codes, actual counts, the selection history (0.0005 → 0.02 after
B01) and wall / RSS / CPU witnesses; no full trajectories. CM freezes argv / cwd / node / launch
sha before launch; the operator launches; DM interprets; Root integrates. The complete Pro
decision selects this comparison, not source acceptance; the four §11.4 conditions remain the
only launch gate.

## 8. Records

Card (this file); CM objective `RCLE_TBCFV_B02_NORM_0P02_CM_OBJECTIVE_20260906.md`; CM record
`RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md`; launch and result under
`docs/research/candidates/roster_consistent_latent_exploration/b02_tbcfv_norm0p02_20260906/`;
result intake `RCLE_TBCFV_B02_NORM_0P02_RESULT_INTAKE_20260906.md`, then the same Innovator node.

scope: none
