# DISH post-witness Convergence intake — 2026-09-06

Node `em:degraded_incumbent_shadow_handover:convergence`, request
`2026-09-06-dish-post-witness-convergence-01` (packet `pro_packets/20260906_post_witness_convergence/`,
evidence base `98d9defd8`, task `1a23df440`, handoff `29397d509`). Direction Manager: the Claude
research hub. Decision authority: `PRO_FINAL`.

## 1. Transport facts (observation)

One Send (click count 1, user message `adba5a87-7ac3-4a05-bbf7-553e36e9a864`, operation
`78df1edf-fd45-4abb-ba61-c4618b48917c`, 14:15 PDT), bound conversation
`6a9bec54-df00-83e8-9840-46440458f316` reused; the first `agentify_review_query` returned
`chatgpt_target_menu_open_unconfirmed` before any click and the identical call with
`verifyExisting=true` placed the one user turn. Delivery commit
`27730bf7547bc749c63930036837050120cffba0` (parent `98d9defd8`) on
`codex/pro-dish-witness-convergence-20260906` at 2026-09-06T21:26:53Z, file
`pro_packets/20260906_post_witness_convergence/archive/RESPONSE.md`, 207 lines, 35,335 bytes, sha256
`73da523f3ba181f2c4e7be5e99cdb0462a26e81b1cbcd9b63399de4c2bc3c2fe`; the hub read the file at the
immutable commit for this intake. The Issue 4 delivery comment and transport phase 2 (receipt,
registry, tab close) follow and do not change the decision.

## 2. The formed decision (read from the full response file)

**Continue the first-legal-application RETAIN/COPY/SHADOW agenda; the joint forecast-package branch
stays ended; this round selects exactly one new bounded B/EXPLORE, `DISH-CONTROL-LOW-LR-B04`: the
inherited CONTROL learner's AdamW learning rate 3e-4 versus 3e-5, one new paired training seed 89,
sixteen updates per arm.** Both arms keep the corrected boundary, the raw-logit service interface,
the original mean-MSE/PPO/auxiliary objectives and normal Welford updates. Not a reopening of the
NLL-plus-sigmoid package, not a frozen normalization, not a simultaneous epoch reduction, not a
PARK, not a RECAST.

Reason: the witness turned the previously unmeasured premise into a bounded fact (the seed-73
final CONTROL serves 245.75 fewer mean ticks than its own zero-update complete controller on the
same conditions), so it is now worth asking directly whether a smaller optimizer step improves
native service at the same interaction and update count. **The fact motivates the change but
does not diagnose an over-large learning rate; the selection is a performance hypothesis, not a
localized repair.** Nothing supports naming normalization, parameter movement or PPO as the sole
source of the loss.

What the response fixes:

- **What the witness establishes and what it does not.** The eight initial-to-final differences
  are a conditional change of the complete controller on one training seed, not the net effect
  of parameter updates alone and not an isolated PPO effect (the finals carry trained Welford
  statistics; the initial views run under the empty state). CONTROL's loss concentrates on the two
  TERRAIN rows; the heterogeneity is shown as is and TERRAIN is not selected as a "most promising"
  evaluation population. **The identical interface views do not prove that no prepare/commit was
  proposed or that the two views' internal action histories were identical**: the summary has no
  per-tick proposal counts; the intake's "no events, so the interface had nothing to act on" stays
  an inference, no reproduction is bought for it, and raw and sigmoid are not treated as
  interchangeable in later learning. B03's −272, its hard events, CONTROL's one training legal
  transfer, the finite gradient extremes and the staged training curves all remain as previously
  narrowed.
- **Why the low-learning-rate B rather than the DM's first choice (frozen Welford).** The LR
  change keeps sixteen updates, all minibatches, the original objectives and the normal
  normalization rule and changes only the optimizer's specified learning rate, so it directly
  tests whether weaker updates have native performance value. Freezing Welford from the start
  would change the effective inputs, saturation, actions, sampled data, gradients and recurrent
  co-adaptation; it intervenes on a component but does not identify the historical cause and is
  not a mandatory diagnostic; checkpoint surgery (final weights with initial Welford) is another
  unbought object. One epoch would also cut replay/backward/optimizer exposure (128 versus 512
  steps); not chosen so that the update count is preserved; existing clipping is not a new
  treatment. A standalone second CONTROL seed is not bought first because the new B's CONTROL arm
  plus its own zero-update reference already reports whether the before/after loss repeats, while
  producing the paired comparison. B02 witnesses, held-only, census, upper-bound search and a
  reproduction of the identical-views fact are not added. No PARK for lack of a unique cause or
  tuned headroom.
- **The object.** Question: on the corrected interface and the A03 host, does the inherited
  CONTROL learner at the same sixteen-update exposure with 3e-5 instead of 3e-4 raise final
  whole-episode native service, and is any improvement only a smaller loss against CONTROL or also
  a retention/gain relative to this seed's own initialization? Arms: CONTROL (inherited AdamW,
  constant 3e-4) and LOW_LR (the same AdamW with **all original parameter groups** at constant
  3e-5); identical objectives, raw-logit interface, no NLL/sigmoid; normalization and recurrent
  state updated by the original rule in both arms (no freezing, no borrowing, no refit); 16
  updates × 32 lanes × 128 ticks, 4 epochs × 8 minibatches; update-16 checkpoint only. All other
  optimizer coefficients, weight decay, clipping, loss weights, sampling, PPO/replay, label/mask
  laws and termination rules unchanged; AdamW's learning rate also scales its decoupled weight
  decay, so the object is the total effect of the learning-rate hyperparameter (no compensation of
  other coefficients; no promise that displacement becomes one tenth; not a pure actor-step
  effect). CONTROL is the direct same-information learned control; the zero-update reference
  prevents comparing only against a degraded final controller; neither is a tuned baseline or an
  oracle; 706.25 is neither an upper bound nor a transferable baseline.
- **Seed, initialization, pairing.** One new paired seed **89**: master = SHA256 of the ASCII
  string `DISH-CONTROL-LOW-LR-B04/seed/89`; a prospective new stream, not generated in the
  consultation; seeds 73 and 61 not reused. Both arms share the same master-addressed STRUCTURED
  initial parameters, the same initial empty Welford states and the same semantic-coordinate
  exogenous law; optimizer, recurrent and Welford states evolve independently; no copying between
  arms. A new seed avoids tuning for the seed already seen to drop and adds one training instance;
  the motivation stays outcome-inspired, not independently confirmed; one paired root is one
  training replicate; four rows are not four seeds; no per-row bootstrap as a seed interval.
- **Zero-update reference of the same seed** (inside the B, an ancillary measurement, not a
  prerequisite A and not an admission condition): the seed-89 initialization evaluated once per
  condition with the inherited raw CONTROL interface, four rows `J_0,r`; a normal zero-update
  policy with motion and protocol outputs (not held-only); no LOW_LR initial view is needed (the
  learning rate is not a second interface at inference); count-0 Welford, fresh recurrent state
  per row; the initializer's constructed objects and load counts recorded; the initial state may
  be saved to avoid later reconstruction (no resume, registry or identity guard for it). No
  skipping training, seed change, condition change or arm stop based on these rows; seed 73's
  706.25 is a historical reference only and enters no seed-89 arithmetic.
- **Host, conditions, path.** `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`, corrected boundary, native
  float64, policy FP32, single Torch thread; ABI, reward, service-label law, thresholds, causal
  information, action space, projection, entity/owner identity and protocol timing unchanged;
  inherited 32-lane training distribution (the four evaluation conditions are not made the training
  distribution). Final evaluation on TARGET_VISUAL_MASK / TERRAIN_RELAY_MASK × K8 / K4_TO_K12,
  speed 4, slot 0, block 0, with the four complete resets **derived for seed 89 by the inherited
  coordinate law and recorded** (not seed 73's phases 4/2/1/1), shared per row between the two arms
  and the initial reference; fresh native/recurrent state per row; no state borrowed across rows or
  arms. Passive-label promotion stays label generation, not a transfer; matched are the label /
  sampling rules and exposure, not realized labels; no source-fork estimates; the family is not
  written as having proved "learned motion raises service in handover".
- **Measurement and reading.** `J_a,r` = sum of native binary service over the fixed 1,200-tick
  range; early native termination stops stepping, unexecuted ticks count zero, completed ticks /
  reason / events reported; no early stop at first-valid; all four rows enter the primary.
  **Primary `Delta_LR = (1/4) Σ_r (J_LOW_LR,16,r − J_CONTROL,16,r)`**; ancillary absolute readings
  `D_CONTROL,new` and `D_LOW_LR,new` against the seed-89 initial rows; report initial and both
  final means and all per-row differences with sources separated from the seed-73 table.
  **Useful-effect scale +24 mean service ticks** (0.02 of the range), ±24 for the initial-to-final
  descriptions; not a tolerance, not per row, not a launch gate. Companions per row: energy, seven
  hard-event classes, completed/unexecuted ticks, termination reason, ordinary legal transfers with
  service before/after (time decomposition only); learning curves with per-update service,
  loss/gradient statistics with their scope and finiteness, eligible/next-mask counts, optimizer
  steps and parameter displacement; training events and transfers listed separately from
  evaluation; lower training loss or energy never counts as service gain. Reading table (seven
  rows): `Delta_LR ≥ +24` without an adverse companion trade-off → an incremental low-LR signal on
  this training instance and four conditions; one or two later independent seeds of the same
  comparison may be considered from the full record (not pre-bought, no per-row or per-seed sign
  requirement); relative signal with `D_LOW_LR,new ≤ −24` → only a smaller loss against CONTROL,
  not recovery of the initialization, the reference's advantage listed alongside; relative signal
  with LOW_LR's before/after inside the band or ≥ +24 → "near its initial performance" or "also a
  positive before/after change", neither equivalence nor general stability nor cause; primary
  inside the band or mixed rows → no useful LR advantage established at this exposure; keep the
  condition differences; no automatic further LR reduction, longer training, better checkpoint or
  seed-adding; no equivalence; LOW_LR with a clear service loss, more hard events or an adverse
  energy/service trade-off → the adverse fact prevails over any proxy, this LOW_LR configuration is
  not extended (one seed closes only this trial, not all CONTROL learning laws or source
  mechanisms); no evaluation legal transfer → the CONTROL comparison stands as incumbent-only, the
  source question stays unestimated; an input, training chain or primary measurement incomplete →
  keep trustworthy rows and counts, no complete paired conclusion, name the damaged dependency, no
  fabricated rows, B03 not quarantined. If the new CONTROL does not fall below its
  initialization, the old shared before/after loss simply did not repeat on this instance by the
  same description; the paired result stays readable and the witness is not overturned. **No
  outcome automatically authorizes another LR, a frozen Welford, reopening the package or a
  Portfolio change.**
- **Work and cost.** One paired seed 89 (two learner runs, one training replicate); 65,536
  ordinary transitions and 512 optimizer steps per arm (131,072 and 1,024 total), full recurrent
  replay/backward; one raw-interface initial view × 4 rows (≤ 4,800 native ticks, zero
  backward/optimizer/label calls); final evaluation 2 arms × 4 rows × ≤ 1,200 ticks (≤ 9,600); 12
  episodes / 14,400 ticks in total; update-16 only; no best checkpoint, LR grid, old seeds or old
  final controllers. Native training work law per arm `2N + 2E + H`, `0 ≤ H ≤ 20E`, at most
  1,572,864 native training step calls; E changes with the new seed and learning rate (B03's
  18,775 / 7,972 are not reused); H unmeasured if no direct reading, no ABI extension. **New cap:
  complete charge ≤ 1,800 s per arm and ≤ 3,600 s for both**, new limits not inherited from
  B02/B03/witness balances; the shared initialization, the four-row reference, the one focused
  check, actually paid build/load and the shared reduction/publication are part of the same item
  (no extra 120 s or "plus build"); shared work S charged once, S/2 allocated to each arm in
  advance, each arm's complete wall plus its share within 1,800 s, total including S within
  3,600 s, publication left room inside the cap; segments do not reset the cap; study elapsed,
  summed invocation wall and CPU kept separate; no new resource evaluation, CPU cap or profiler.
  B03's 211.04 / 196.18 s arms, 4.94 s shared check and 412.16 s chain are references for work
  types only; the witness's 11.25 s is one complete eight-episode run, not a unit price; the DM's
  ~410 s and 211+16 s are not adopted as projections; a tenfold LR cut is not a tenfold time cut;
  no calibration experiment; the CM lists the cost range from the chosen path and existing
  timings, and returns a specific range problem if the complete plan exceeds the cap rather than
  silently dropping labels, training or raising the limit. Stop after both arms' sixteen updates,
  the twelve rows or legal terminations, and publication; stop on budget exhaustion, an actual
  non-finite training state, or a failure threatening the primary measurement, keeping actual
  exposure; no efficacy early stop, ad-hoc early checkpoint, outcome-driven seed/row replacement,
  automatic continuation or scientific retry; pre-launch failures keep their records, spend and
  zero exposure. Remote-first `wsl_4070`, exact committed and pushed source, detached supervision,
  fresh ≥ 4 GiB physical/effective admission per invocation, full wall and scoped peak RSS;
  2,000 / 600-line budgets; no A05 exception, scheduler, registry, validator, extra guard or
  cross-platform bit contract.
- **Acceptance.** Targeted check that the selected LR actually acts on all original optimizer
  parameter groups at every update, and that checkpoint/state restore or trainer rebuild does not
  reset LOW_LR to 3e-4; that objectives, masks, clipping, normalization and interface carry no
  hidden change; the same new initialization / same raw reference, reset pairing, fixed-range
  primary reduction and the source of the before/after differences. One focused coverage of the
  change and the primary output; B03, the boundary correction and witness coverage of unchanged
  paths reused. The response does not claim to have verified that the current program has an LR
  switch without modification; the parameter passing is done in this bounded research
  implementation; a real dependency that prevents the comparison from running with its stated
  meaning is returned as that specific gap, not a history reconstruction. No retest of seed 61,
  A01/A02, the r06 suite, all schedules, historical fragments, all gradient connections or B03's
  eight final rows.
- **Unchanged.** Costs restated: witness r2 16.231 s (4.981 + 11.25) and r1 5.816 s, not summed as
  "total spend" and not zero; the two B03 pairs' readings coexist with the absolute losses; B02,
  B01, A01–A05 stand; R02 stays closed; the package branch stays ended (no rename, coefficient
  tweak or favourable seed); the source-selection question (COPY–RETAIN, SHADOW–COPY after an
  ordinary first application) remains the family's scientific question and an incumbent-only
  service gain does not substitute for it; no Portfolio lifecycle, priority, capacity, fusion,
  registration or recast action; `PORTFOLIO.md` not read; no RECAST.
- **Evidence access.** Everything read through the connected GitHub at `98d9defd8` (seventeen
  paths listed in §八 of the response; `DIRECTION.md` lines 210–310 and 350–end; the specs and
  `AGENTS.md` lines 1–370); Issue 4 body and four prior delivery comments read before 21:22:35 UTC;
  no code executed; the only external change is the response file and its Issue comment.

## 3. DM check of the decision (§2 of `AGENTS.md`)

- **Completeness.** The response decides the posed question (which of 1–4 or another object) at
  its declared class (B/EXPLORE), fixes arms, seed law, exposure, evaluation conditions, primary and
  ancillary measurements, scale, reading table, cap, stop boundary and acceptance scope, and
  states what it does not decide. Complete; final for the node.
- **Conflicts.** None with current owner instructions or specifications. The 1,800 s / 3,600 s
  caps are the B02/B03 ceilings restated as new limits; no default-prohibited machinery is added;
  the learning-rate plumbing is an ordinary bounded implementation. One implementation fact is
  open for the CM objective and is being mapped read-only: the r06 production modules construct
  AdamW with a literal `lr=3e-4` at three sites (initializer payload, engine construction, engine
  restore), so the thin entry must set the LOW_LR rate at every construction or restore site
  without editing the r06 sources; the response anticipates exactly this ("checkpoint/state
  restore or trainer rebuild must not reset LOW_LR to 3e-4") and the card's acceptance pins it.
- **Corrections accepted.** The intake's identical-views explanation is kept as inference only; the
  DM's preference for the frozen-Welford variant is withdrawn (the node's reasoning about
  component intervention versus cause identification is adopted).
- **Owner prediction slot.** Not taken (unattended). DM prediction for B04 recorded on the card.

## 4. Decisions this intake produces

1. **PRO_FINAL applied:** open `DISH-CONTROL-LOW-LR-B04` (B/EXPLORE) exactly as fixed in §2. Card
   `DISH_CONTROL_LOW_LR_B04_SCIENCE_CARD_20260906.md`; CM objective
   `DISH_CONTROL_LOW_LR_B04_CM_OBJECTIVE_20260906.md`; frozen after the read-only map of the
   learning-rate plumbing resolves the per-site mechanism.
2. **PRO_FINAL applied:** no frozen-Welford B, no one-epoch B, no standalone second CONTROL seed,
   no B02 witnesses, no held-only rows, no PARK, no RECAST, no Portfolio change; the package branch
   stays ended.
3. Records: ledger row (direction tier, `PRO_FINAL`), DIRECTION addendum, Portfolio row, owner brief
   `owner/briefs/degraded_incumbent_shadow_handover/2026-09-06_post-witness-convergence.md`, archive
   copies under the packet's `archive/` folder after transport phase 2.
