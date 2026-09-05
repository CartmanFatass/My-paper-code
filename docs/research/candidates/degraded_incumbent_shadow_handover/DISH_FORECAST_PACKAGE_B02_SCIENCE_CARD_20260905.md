Claim: At matched small training exposure on the A03 ground-terminal host, a joint forecast-supervision and service-interface package may improve ordinary whole-episode native service over the inherited learner/controller.
Binding MARL structure: other-agent partial observability and state ownership during handover; physical vehicles, current owner/standby roles and active/shadow recurrent copies remain distinct.

# DISH forecast package B02 — science card

Date 2026-09-05; object `DISH-FORECAST-PACKAGE-B02`; **B / EXPLORE**.
Selected by the complete post-A05 Convergence response, **PRO_FINAL CONTINUE, not RECAST**,
with intake `DISH_POST_A05_CONVERGENCE_INTAKE_20260905.md`. DM
`/root/dm_amx_n3_post_a05` records the seed and implementation-complete details below under
the owner's standing unattended delegation. No empirical outcome has yet been observed.

## 1. Question and ceiling

Does the selected joint learner/interface package improve native service after sixteen
updates on one paired training seed? The comparator is the actual inherited same-information
learner/controller at the same exposure, on the same new host. It is not an established
tuned optimum. No matched upper/tuned-generic headroom exists on this host; record that
absence without delaying the comparison.

The result is exploratory package performance on four development conditions from one
trained replicate. It is not calibrated uncertainty, stable superiority, generic transfer,
legal-handover competence, SHADOW-COPY value, component attribution or a variable-N claim.
Information restoration in A03 and synthetic A05 facts motivate this outcome-informed B;
they do not prove that the treatment will work. R02 stays closed and B01/A01-A05 retain
their meanings. A05's completed exact task and engineering exception do not carry forward.

## 2. Selected host, treatment and control

Both arms use **GROUND-TERMINAL-LINEAR-CLEARANCE-A03**, exactly the host law in section 2
of `DISH_GROUND_ENDPOINT_PATH_A03_SCIENCE_CARD_20260905.md`: terrain-referenced two-metre
ground emitter/visual target, linearly tapered ground-linked clearance, actual endpoint
distances, unchanged UAV/base heights and remaining native physics/protocol equations.
Bind ordinary training, passive labels and ordinary evaluation to that same host. The
literal-host comparison and A03's retained seed-11 checkpoint are not B02 inputs.

Output arm names are `CONTROL` and `FORECAST_PACKAGE`; both retain the underlying
`STRUCTURED` algorithm/RNG role. The treatment changes exactly two components:

1. Apply sigmoid to the raw service logits before the native probability input. Retain
   BCE-with-logits on raw logits for its training loss. The link is part of the policy
   interface, including training collection and evaluation, not only the evaluator.
2. Replace the prediction-mean coordinate MSE by the ordinary four-dimensional Gaussian
   negative log likelihood for the existing prediction mean and Cholesky output:
   `0.5 * ((y-mu)^T Sigma^-1 (y-mu) + logdet(Sigma) + 4*log(2*pi))`.
   Average across the same four recurrent copies and rows selected by existing `next_mask`.
   Keep its effective auxiliary coefficient **0.025**, with no coefficient search.

Use the existing lower-triangle order, diagonal `softplus(raw)+1e-3` and
`Sigma=L*L^T+1e-4*I` mathematical construction in the likelihood and native interface.
The training computation remains FP32; native physics/interface storage remains float64.
The new sigmoid is computed on the FP32 policy logits before native conversion. Stable
linear algebra implementing this same likelihood is appropriate; no explicit inverse,
cross-platform bit equality or extreme tolerance is required. Loss scaling differs from
coordinate-averaged MSE; this is a named treatment with no equal-gradient claim.

The control keeps its current mean-only MSE and raw-logit native interface. Both arms retain
PPO, AdamW, LR `3e-4`, clipping, link and missingness auxiliaries, service-label objective,
mask laws, recurrent replay and actor/snapshot/critic normalization rules. Cholesky training
is newly connected only by the selected likelihood; shared representations can change
covariance in the control. No threshold, action space, actor information, SOURCE/readiness
state or ordinary ownership transition is forced or altered.

The causal path is route/degradation event → role-specific causal observations and actual
messages → active/shadow recurrence → ordinary motion/prepare/commit and forecasts → native
action/certificate processing → native service reward and auxiliary labels → real recurrent
PPO/backward/AdamW → final-checkpoint ordinary native consequences. Covariance also enters
snapshots and can affect pre-transfer behavior. Certificate checks remain nondifferentiable.
Privileged next-state/passive-clone labels remain training labels, never actor observations.
The private service-label clone's forced promotion is not observed legal-handover support.

## 3. Seed, pairing and exposure

Select one fresh seed **61**. Its 256-bit master is the SHA256 of ASCII
`DISH-FORECAST-PACKAGE-B02/seed/61`, hex
`ef9ec35ce27cf52e4c1d82292b22cfbe4926183ec1f29b19657280f6234814b1`.
This seed binding is prospective and differs from B01's seed/master namespace.

Start both arms with matched initial parameters from the existing master-addressed
STRUCTURED initializer, block 0. Keep the existing semantic-address train reset/sampling
and evaluation laws, with common exogenous randomness. The output arm name does not select
an RNG stream. Each arm has its own evolving native, optimizer, recurrent and normalization
state; trajectories and realized eligible-label counts may differ. Do not force them equal.
Record actual initialization/configuration and the pairing; matching here is within this
declared comparison, not a cross-platform exact-reproduction claim.

Each arm trains **16 complete updates**, **32 lanes ×128 ticks/update**, **4 epochs ×8
minibatches/update**. That is **65,536 ordinary training transitions and 512 optimizer steps
per arm**. Keep the existing recurrent fragment/replay structure. Use only update 16 for
evaluation; no earlier/best checkpoint selection or within-pair parameter search.
The two arm runs form **one paired training replicate**, not two independent seeds.

Record actual ordinary transitions, completed updates, optimizer steps, per-update native
service/learning curves and initial/final model norm plus total absolute/relative parameter
displacement. Nominal counts do not replace observations. Fresh next-mask and service-label
eligibility counts describe actual support and cost; they impose no support threshold.
No historical fragments, old checkpoint replay, exact upper or gradient census is required.

## 4. Ordinary evaluation and primary measurement

For each final checkpoint, evaluate the four combinations of both `TARGET_VISUAL_MASK`
and `TERRAIN_RELAY_MASK` with `K8` and `K4_TO_K12`, at **speed 4, slot 0, block 0**.
Use the existing coordinate geometry/reflection/initial-owner definitions and deterministic
policy evaluation with paired exogenous randomness. These are four development conditions,
not four independently trained samples. Continue ordinary execution after a legal transfer;
do not call B01's first-trigger fork evaluator or passive-label clones as evaluation.

Each episode has a fixed 1,200-tick return horizon. Stop actual stepping at native terminal,
assign zero service to its unstepped remainder in that fixed-horizon sum, and report the
actual completed ticks and terminal cause. Do not divide by surviving live ticks or replace
an unfavorable condition. Maximum ordinary evaluation exposure is 4,800 ticks per arm.

Let `J[a,r]` be the sum of actual native service indicators over that fixed horizon.
The primary difference is `Delta_package = mean_r(J[FORECAST_PACKAGE,r]-J[CONTROL,r])`
over all four paired rows, with no trigger-support filter. Publish both arm means and all
four paired differences. Report energy and the inherited hard-event categories
`invalid_commit`, `token_gap`, `dual_owner`, `dual_payload`, `buffer_clear`,
`command_slew_breach`, `separation_breach`, plus terminal outcomes.

Record ordinary legal transfer counts and service before/after any transfer. Temporal
post-transfer service is not automatically service carried by the promoted owner: old-owner
packets can still be in flight. Packet-source attribution may reuse available direct fields,
but is not necessary for the primary whole-episode sum and must not be invented from timing.

## 5. Interpretation and predictions on record

The MEI is **+24 mean service ticks**: +0.02 of the horizon, or 2.4 seconds of service.
This is a small tangible scale for buying independent seeds, not a universal MARL threshold
or a revision of B01's source-specific MEI. No significance test or per-row positive-sign
requirement is selected. The descriptive reading follows the Pro response:

- A trustworthy gain at or above 24 ticks without a dominating adverse tradeoff is a useful
  package-investment signal; consider one or two separately budgeted new independent seeds.
- An inside-margin or mixed result does not establish substantial gain at this exposure.
  Keep every row; do not claim equivalence or automatically extend training.
- Native-return loss, hard events or an adverse energy/service tradeoff remain visible even
  if a proxy improves. Do not scale the unchanged package for a proxy-only gain.
- No ordinary handover does not invalidate package performance. With no transfer, label
  any gain incumbent-only and leave source contrasts unestimated.
- A legal handover is observed opportunity, not SHADOW value. The source question still
  needs a separately selected matched RETAIN/COPY/SHADOW comparison.

One seed cannot estimate training-seed population uncertainty. Do not bootstrap the four
rows as if they supplied independent training seeds or run until signs agree. Report the
finite pattern and its limitations. Unresolved component attribution narrows the claim.

DM primary prediction: an inside-margin, mixed or adverse package result is more likely
than a useful >=24-tick gain at only sixteen updates. The known interface facts do not
demonstrate competent forecasts or useful legal proposals. The competing prediction is
that joint forecast training/interface consistency reduces disruptive auxiliary behavior
enough to produce an ordinary native-service gain, potentially entirely incumbent-driven.
Owner prediction: **not taken (unattended)**. This card records a new performance readout
within the continuing family and does not reinterpret the old diagnostic predictions.

## 6. Whole cost, route and stop

Tool-computed configuration/counts are in `DISH_FORECAST_PACKAGE_B02_PLANNED_COUNTS_20260905.json`.
For each arm let `N=32*128*16=65,536`, E be label-eligible transitions and H their actual
consequence-step sum. The retained training work is
`N ordinary + N next-label +2E delay +H consequence`, with `H<=20E`, hence at most
**1,572,864 native training calls**, plus at most **4,800 ordinary evaluation steps**.
Recurrent/critic forwards, replay/backward, physics readouts, initialization, compilation
and publication are additional work. This bound is not a measured wall multiplier.

The spending ceiling is **1,800 seconds per complete arm**, **3,600 seconds in summed
pair allowance**, including charged preparation, required checking, learning, evaluation
and publication. Account genuinely shared preparation once: allocate half its measured
compute wall to each arm, leaving `1800 - shared_preparation_wall/2` for that arm's own
complete invocation. Do not add an unbounded preparation allowance. CM records the exact
command/time scope and this allocation before question-relevant execution. Agent editing,
Git, queue delay and SSH control latency are not relabelled experimental compute.

Use current **single-thread CPU** numerical configuration and existing tensor/native
batches; no new compute team, worker pool, device sweep or extra pilot is selected.
The new host's eligible clone work and whole-invocation wall/CPU are unmeasured. Historical
B01 wall scaling, core-count division or the 24N upper cannot stand in for a matched
projection. Unknown completion feasibility is explicit; no generic extra calibration or
validation round is required. If direct implementation facts establish an over-cap or
source-scope conflict, return the concrete gap rather than remove labels or alter the pair.

Route portable execution to `wsl_4070` per `.codex/hmasd-compute.toml`: exact committed/pushed
source in a detached worktree, configured Python and existing `agent-task`. No OS/device
comparison is claimed; local fallback only follows the already declared project routing
rule with no accepted remote process and fresh destination admission. Immediately before
each arm's native/master/model/result construction, join the actual-node memory preflight
and runner by `&&`; physical and effective available memory must each be at least 4 GiB.

Each arm stops after the fixed training/evaluation/publication work, at its remaining full
wall allowance, or at an actual failure threatening learning/primary measurements. Preserve
actual counts, partial evidence and observed exception; incomplete work cannot be called the
complete sixteen-update pair. Do not substitute an earlier checkpoint, replace a failed
seed, resume in place, automatically retry, enlarge the cap or adapt an arm after its output.
Return such evidence to DM. Optional resource gaps retain their narrower consequence under
§11.8; no new performance or launch gate is introduced.

## 7. Bounded engineering handoff and output

**Engineering-scope section 4 declaration: none of its default-prohibited machinery is
needed.** Ordinary in-process batching and minimal whole-invocation CPU accounting use the
current runtime specification. No historical census/reconstruction, generic trace service,
schema/provenance guard, retry/lease machinery, extra approval or GitHub Issue/PR gate.

CM owns the minimal B02 code under
`experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/`,
`scripts/run_dish_forecast_package_b02.py`, its focused tests under
`tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/`,
and B02 technical/evidence documents. Minimal explicit variant hooks may touch the R06
`production_training_engine.py`, `production_recurrent_trainer.py`, `production_training.py`
and `production_backend.py` to instantiate the selected loss/interface and per-instance
ground-host library. Reuse the existing A03 native variant; no native physics/protocol
rewrite or global loader swapping is selected. Preserve unchanged default routes and old
checkpoint/RNG behavior outside the explicit new study. Return an actual additional owned
dependency if needed; do not silently modify unrelated sources.

Use a semantic implementer and independent reviewer for changed gradient/native-interface
semantics, coordinated by the existing CM. Reuse trustworthy unchanged checks. One focused
changed-path profile should cover sigmoid with raw-logit BCE, the joint NLL/Cholesky graph and
masks, same ground-host binding in ordinary/passive paths, and native service reduction into
the actual publication path. It is conformance evidence, not a second learning replicate.
Do not repeat smoke at a new launch boundary. Ordinary 2,000 new source lines, 600 runner
lines and five-minute research-test budget apply; the 30% ratio is a review signal.

Use `temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/`
with separate `control` and `forecast_package` output roots and adjacent arm-specific
admission receipts. Preserve compact curves, final checkpoint, configuration, per-row
native outcomes, event/owner summaries, actual exposure and process wall/RSS/CPU witnesses.
Full per-tick arrays are unnecessary. CM freezes exact argv/cwd/node/launch SHA before
launch, observes technical completion, and hands accepted handles to DM/the shared tracker.
DM interprets science; Root integrates and owns shared Portfolio/audit/owner surfaces.

The complete Pro decision selects this comparison, not source acceptance. It authorizes
implementation and its bounded execution once the ordinary applicable conditions are met;
no additional Pro round, owner vote or exact-main-commit identity is a prerequisite.
