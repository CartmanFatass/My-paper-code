# DISH post-B04 Convergence intake — 2026-09-06

Direction `degraded_incumbent_shadow_handover` (DISH), node `em:degraded_incumbent_shadow_handover:convergence`.
Intake by the Claude research hub as DM. Provenance label **PRO_FINAL** (direction tier). Owner
instruction of 18:11 PDT ("finish this batch, then write the handoff, advance nothing further")
applies: this intake **records** the decision and freezes no card, implements nothing and launches
nothing; the resume procedure is in `docs/research/portfolio/HANDOFF_20260906_CLAUDE.md`.

## 1. Provenance

- Request `2026-09-06-dish-post-b04-convergence-02` (packet `pro_packets/20260906_post_b04_convergence/`,
  TASK.md at `4eebef120`, evidence reference and delivery base `f6ba67cd7`). The first request
  (`-01`, TASK `5f9f62e1a`) pinned reference `5b58821af`, where the three packet aux files did not yet
  exist; Pro reported three 404s and formed no decision (kept as `TASK_r01.md` / `HANDOFF_r01.json`;
  its reply archived as the `-01` short receipt). Cause: hub error (a failed first aux commit followed
  by a re-commit without rebuilding REQUEST.json); corrected by rebuilding at `f6ba67cd7`.
- Response delivered by Pro at commit `a9718a45e` on `codex/pro-dish-b04-convergence-20260906`
  (parent `f6ba67cd7`, "docs: deliver DISH post-B04 convergence decision", 2026-09-07T02:03:44Z),
  path `archive/RESPONSE.md`, 37,709 bytes, sha256 `042f100d5f8fe1f2dc222e73ef8eb7c23bc98855dac51bcc80b660bfc3d62511`
  (hub readback at the immutable commit). Transport facts in `archive/TRANSPORT_FACTS_CLAUDE.json`.
- Pro read all twenty listed paths at `f6ba67cd7` (its §八 table), executed no code, created no state,
  and reports the Issue snapshot time and its own pre-write Issue readback.

## 2. The decision (transcribed)

**Direction-tier decision:** continue the first-legal-application RETAIN/COPY/SHADOW agenda; the
joint forecast-package branch stays ended; this round selects **only option 2**: a second
independent paired training seed of the same CONTROL / LOW_LR comparison, **seed 101**, still
B/EXPLORE. Sixteen updates per arm, update-16 evaluation only, with this seed's own four-row
zero-update raw-interface reference inside the same object. Not chosen: retraining seed 89 to locate
when the loss appears (option 1), intermediate-checkpoint evaluation (option 3), any simultaneous
Welford freeze, epoch change, learning-rate change or scripted source trigger (option 4), PARK, CLOSE
or RECAST of DISH (option 5).

Object contract as fixed by the node (for the card to be written on resume):

- **Category and question.** B/EXPLORE, "seed-101 independent paired follow-up of the B04
  learning-rate comparison", its own card and outputs, seed 89 not overwritten. Question: under the
  same sixteen-update budget, what is the complete native service increment of 3e-5 against 3e-4 on
  a new random instance; how does each arm relate to their common zero-update reference; does the
  earlier result, concentrated in one terminated condition, still merit development. Not a
  conclusion on stable advantage, rare-event rate, calibration or the source effect.
- **Arms.** Identical to B04: inherited STRUCTURED CONTROL learner; AdamW constant 3e-4 (CONTROL)
  versus 3e-5 (LOW_LR) on every original parameter group; original objectives (mean-MSE,
  BCE-with-logits, PPO, link/missingness auxiliaries), raw logits, `forecast_package=False`; original
  Welford updates, recurrent replay, clipping, masks, sampling, termination and legality rules with
  independently evolving state; 16 updates × 32 lanes × 128 ticks, 4 epochs × 8 minibatches;
  update-16 checkpoint only. No compensation of the weight-decay effect, no Gaussian-NLL/sigmoid
  package, no frozen Welford, no new clipping or schedule.
- **Seed law.** The only new paired seed is 101 (not 89, 73 or 61); master = SHA256 of the ASCII
  `DISH-CONTROL-LOW-LR-B04/seed/101`, bound in the response before any result; no master generated
  and no initialization executed by Pro. Both arms and the reference use one new master-addressed
  STRUCTURED initial parameter set and empty Welford state. Four complete resets derived and
  recorded for seed 101 by the inherited `_reset_row` coordinate law; the three controllers use the
  same reset and exogenous randomness per row. Seed-89 phases (6/0/6/0), the 393.75 reference and
  the seed-73 706.25 are not carried over. If the thin entry hard-codes 89, the follow-up
  implementation binds 101 explicitly and checks its propagation (a CLI label change is not a
  random-source change); Pro has not verified that the entry accepts a new seed unmodified.
- **Reference.** One four-row evaluation of the same new initialization on the raw interface,
  `J_0,101,r`, count-0 Welford and fresh recurrent state per row; a companion measurement inside this
  B, not a prior A or a launch gate (its level cannot skip training, change seed or conditions).
- **Host and evaluation.** GROUND-TERMINAL-LINEAR-CLEARANCE-A03 on the corrected ordinary renewal
  boundary, native float64, policy FP32, single thread; two physical UAVs with owner/standby and
  active/shadow copies distinct; training distribution unchanged. Final four conditions unchanged
  (TARGET_VISUAL_MASK / TERRAIN_RELAY_MASK × K8 / K4_TO_K12, speed 4, slot 0, block 0), fixed
  1,200-tick range, deterministic. **Terminated-row treatment unchanged**: native termination stops
  stepping, the remaining range counts zero, actual ticks/causes/events listed; no division by
  survival time, no row removal, no matching to shorter survival, no stop at first-valid. A legal
  transfer, if any, continues ordinary evaluation without claiming a RETAIN/COPY/SHADOW fork.
- **Primary and companions.** `Delta_101 = (1/4) Σ_r [J_LOW_LR,16,101,r − J_CONTROL,16,101,r]`;
  `D_CONTROL,101` and `D_LOW_LR,101` against the new common zero-update rows; all twelve rows, three
  means, per-row paired and before/after differences kept. MEI +24 mean service ticks (±24 for the
  before/after description), a scale, not a tolerance, per-row threshold or launch condition. On
  completion seed 89's +182.75 and `Delta_101` are listed separately; an equal-weight two-seed mean
  may be appended as description but never replaces the full record; no per-row bootstrap over the
  training-seed population; B03's package pair is not a third learning-rate pair. Companion fields as
  in B04 (energy, seven hard-event classes, executed/unexecuted ticks, terminal causes, legal
  transfers with pre/post-transfer service decomposition, training curves, LR read-back per
  parameter group, finiteness, parameter displacement, eligible/next-mask, training events and
  training transfers). Reference-row bad behaviour is kept.
- **Reading table (verbatim in substance).** (1) `Delta_101 ≥ +24` with an acceptable
  service/event/energy trade-off: another instance of a useful mean increment; consider, on both
  pairs' complete rows, whether LOW_LR stays a development candidate; mixed rows do not cancel the
  mean signal; no claim of stability, per-condition advantage or safety. (2) That signal together
  with `D_LOW_LR,101 ≤ −24`: still a smaller loss against CONTROL, not recovery of the
  initialization. (3) LOW_LR before/after inside the band or ≥ +24: report near-initial service or a
  positive change respectively; neither equivalence nor general stable learning. (4) `Delta_101`
  inside the band, clearly negative, or a gain with a severe native trade-off: the earlier signal's
  repeatability/usability is qualified; no automatic third seed, lower rate or longer training;
  listed beside seed 89 without denying +182.75; continuing, stopping this configuration or a new
  named question is a separate decision on the complete result. (5) New CONTROL no longer below its
  initialization, or the separation termination not repeated: the earlier loss/termination did not
  repeat in this instance; the original record stands; no zero-rate inference; the LR pair reads
  independently. (6) Still no legal transfer in final evaluation: incumbent-only; the source
  difference stays unestimated; not a proof of no source value. (7) Input, training or primary
  measurement incomplete or damaged: keep real exposure and independently trustworthy rows; no
  fabricated pair; report the specific gap by dependency; no collateral quarantine of B04/B03.
- **Stop boundary.** Only this new paired instance is bought: two arms × sixteen updates, four
  reference rows, eight final episodes (or their legal early terminations) and full publication,
  then stop. Budget exhaustion, non-finite training state or a failure threatening the primary
  measurement: keep what happened and stop; a finite large gradient is not a non-finite fault. No
  effect-based checkpoint choice, seed/reset change, re-run of bad rows, automatic continuation or
  another learning rate; a native separation termination is a result, not a scientific retry;
  technical failures create no budget or polarity.
- **Cost.** Per arm 16×32×128 = 65,536 ordinary transitions and 512 optimizer steps (131,072 /
  1,024 total); one raw-interface reference of four episodes (≤ 4,800 native ticks, zero learning or
  label calls); final evaluation 2 × 4 rows (≤ 9,600 ticks; 12 episodes and ≤ 14,400 ticks with the
  reference); update-16 only; no intermediate checkpoints, grid, search, old-seed retraining or
  source fork. Label-algorithm work per arm `2N + 2E + H` with `N = 65,536`, `0 ≤ H ≤ 20E`, upper
  bound 1,572,864 native training step calls per arm; B04's E (22,044 / 15,616) is a record, not a
  value for the new seed. **Caps re-selected: 1,800 s per arm charged in full, 3,600 s for both, no
  inherited balance**; the shared work S (focused check, common initialization, four reference rows,
  build/load, shared reduction/publication) charged once and allotted S/2 to each arm in advance; no
  extra 120 s reference allowance, no "build untimed", no cap reset across phases or scripts. B04's
  432.40 s chain (S 15.84, CONTROL 210.07, LOW_LR 206.49; charged 217.99 / 214.41 per arm) is a
  conditional planning reference of the same comparison type and scale, not a promised completion
  time; prepublication walls (≈ 209.8 / 206.2) are not the full outer wall; the shared summary's
  6.5486 s is not a unit price for four episodes; no calibration experiment. Execution on `wsl_4070`,
  exact committed and pushed source, detached supervision, single-thread FP32/float64 path, fresh
  ≥ 4 GiB physical and effective admission per actual invocation; ordinary 2,000 / 600 line and test
  budgets; no scheduler, registry, validator, guard or profiler; the 2,700 s investigation threshold
  does not widen the stricter cap.
- **Checks.** Only the actual binding of the new seed/master, the common initialization and per-row
  resets for both arms, result provenance and the existing primary reduction; one focused pass over
  whatever changes in the thin entry and its primary output; LR persistence across updates, the
  corrected boundary, the reference and native termination reuse their existing trustworthy
  coverage, no full smoke rerun. Pro claims no independent code audit or seed-101 acceptance; a
  dependency that threatens reward, information, training or the primary is resolved in the thin
  implementation or returned as a specific gap, not expanded into a full historical replay.

## 3. Reasons recorded by the node

- **Why not option 1 (seed-89 evaluation across updates).** It is a new real training B, not a free
  A over saved early checkpoints (only the final checkpoint was saved): one 65,536-transition /
  512-step learner plus five checkpoints × four rows, up to 24,000 evaluation ticks; it locates the
  loss in time for that retraining instance but adds no independent LR pair and does not identify a
  normalization cause from a time curve; an exact same-seed update-16 reproduction is not an entry
  condition for repeating an existing performance comparison. Not bought, so "early versus
  accrued" stays unanswered this round.
- **Why not option 3 (new seed with five-checkpoint evaluation on both learners).** Same training,
  but 2×5×4 = 40 checkpoint episodes plus four initialization rows = 44 episodes, up to 52,800
  evaluation ticks (32 episodes / 38,400 ticks more than the selection); "most information per
  charge" is not established by timing or by a decision that would change with checkpoint results;
  it needs evaluation state and random streams isolated from continued training and no
  best-checkpoint selection; the round decides whether the LR comparison merits continuation, not
  training-time selection.
- **Why not option 4 (source study on the zero-update controller now).** The source question still
  needs an ordinary legal first-application opportunity and matched RETAIN/COPY/SHADOW
  interventions; no such object is selected; it cannot be built by forcing a trigger or picking a
  favourable controller. Corrections to the DM: "zero-update serves best on both seeds on average" is
  not "best on every condition" (seed-89 TARGET/K8: LOW_LR 760 above the initial 617); and "no
  controller ever transferred legally on the corrected path" exceeds the record (B03 CONTROL had
  one training transfer). The DM's "twenty evaluation rows" are B03's eight, B04's eight and B04's
  four reference rows, not twenty training replicates; the earlier zero-update witness's eight rows
  are recorded separately.
- **Why not option 5 (park DISH).** A finite performance signal from a real treatment exists together
  with a concrete comparison that tests whether it holds on another random instance, so continuation
  has a positive decision reason; not an indefinite extension because the source value is
  unanswered; the forecast-package branch stays ended; no third LR seed and no automatic next
  stabilization variant are authorized; without a further concrete, bounded, choice-changing object
  the direction should stop at the smallest relevant branch rather than infer mechanism failure from
  an unestimated source effect.
- **B04 reading kept.** The complete four rows, the terminated row and the before/after losses stay
  together; the companion result is not "LOW_LR harmless"; the treatment and learning were real
  (rate read-back and displacement), not a configuration label. Strongest support: a positive mean
  comparison from a real learner, real treatment and complete native endings without checkpoint
  swapping or row filtering. Strongest contradiction: its concentration, two non-positive rows,
  LOW_LR's −57 before/after loss, and no legal transfer in evaluation; insufficient for a general
  low-rate recommendation or a source-mechanism claim; the difference may be seed/condition-specific
  motion and termination differences; normalization, parameters, recurrent dynamics, auxiliaries and
  training-data shift remain jointly unlocalized.
- **Boundaries of history.** The two CONTROL before/after losses do not change B03's package
  disadvantage, the seed-73 witness's conditional measurement, B02's qualified inside-MEI reading
  under the executed lag interface, B01's insufficient triggers, A03–A05's bounded facts, or
  A01/A02's local boundary measurements; B02/B03 are not to be merged as independent repeats of one
  algorithm. The source quantity was unestimated before and remains unestimated. No Portfolio
  lifecycle, priority, capacity, fusion, registration or recast-count change; no polarity to other N3
  components; R02 not reopened; `PORTFOLIO.md` was not in the reading list and was not read.

## 4. Conflict check (AGENTS.md §2)

None found. The decision selects one bounded object inside the family's existing B/EXPLORE
practice, keeps §11 burdens (one seed is one training instance; two seeds are two instances, not a
seed-level claim), and fixes caps, seed law, primary, reading table and stop boundary sufficient for a
card. The response is complete and final for this node. DM corrections accepted: the "no legal
transfer on the corrected path" sentence in the packet's option 4 overstated the record (B03's one
training transfer was in fact stated elsewhere in the same document; the intake will not repeat the
overstatement); the "6.5 s for four reference episodes" projection was a shared-item wall, not a unit
price.

## 5. Decisions this intake produces

Direction tier: the node's decision above is recorded as **PRO_FINAL**. Under the owner's 18:11 PDT
instruction the hub takes **no** executing step: no card `DISH_CONTROL_LOW_LR_B05_...` is frozen, no
CM objective is written, nothing is dispatched to Grok Build, nothing is launched. On an owner-directed
resume the ordinary sequence applies (card and CM objective from §2 of this intake → Grok Build thin
entry binding seed 101 → hub review → operator launch on `wsl_4070` with fresh admission → tracker →
result intake → this node again). Owner prediction slot for the follow-up: not taken (unattended).
DM prediction for the record (not binding): `D_CONTROL,101 ≤ −24` again; `Delta_101` positive but
inside or near the band with mixed rows (rows 1 and 4 of the table competing).

Records: brief `owner/briefs/degraded_incumbent_shadow_handover/2026-09-06_post-B04-convergence.md`;
ledger row; DIRECTION addendum and PORTFOLIO row (queued for the next clerk pass or the resuming
session); handoff `docs/research/portfolio/HANDOFF_20260906_CLAUDE.md`.
