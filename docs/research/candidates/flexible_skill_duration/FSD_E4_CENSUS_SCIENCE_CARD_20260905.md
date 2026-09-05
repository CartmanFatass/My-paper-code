Claim: This finite renewal/reference census measures native timing opportunity on the stated K=2 host, without establishing a learned-algorithm effect.
Binding MARL structure: temporal abstraction or termination; fixed regional entities share public change information and native lease-renewal consequences.

# FSD E4 renewal/reference census — invocation card

Frozen 2026-09-05T16:17:16Z before implementation, calibration or result invocation.
Class **A/RECON**. DM `/root/dm_amx_fsd_e4_census`; local control worktree
`C:/Projects/HMASD-worktrees/dm-fsd-e4-census-20260905`, branch
`codex/dm-fsd-e4-census-20260905`; declared source baseline `411adffc3046947e28ccb8fe11d074276a95c759`.

## Authority and question

The complete archived Pro decision in
`pro_packets/20260905_e3_complete_convergence/archive/RESPONSE.md`, accepted by
`FSD_E3_COMPLETE_CONVERGENCE_INTAKE_20260905.md`, selected this sole next object.
The owner's current unattended-resume request explicitly confirms user and platform-side approval.
Historical restrictions remain historical evidence, not an invented active restriction. A fresh
actual tool refusal will be honored and reported. This card fills the invocation facts identified
in `FSD_E4_CENSUS_PREPARATION_20260905.md`; it selects no new family or successor.

Question: under the existing finite renewal model, how much native expected service return
separates public event-triggered renewal, the full fixed-clock grid, and all open-loop references?
Non-goals: E3 rerun or reinterpretation, E4/D2/D8 training, D3 recast, baseline tuning, Monte Carlo
replacement of DP, a variance-only causal effect, transfer, theorem or Portfolio disposition.
The valid E3 18/18 result and bounded `E3-H0-NO-ADVANTAGE` remain unchanged.

## Population, action path and comparators

Exactly `N=6, K=2, Z=4, regions=2, H=400, Delta=.4`, `event_process=renewal`, nominal
`renewal_mean=20`, `lognormal_shape=1`, `k={1,2,5,20,40}`, `rho=0`, `c_probe=0`,
`e5_coupling_enabled=False`, `role_decode=argmax`. Three law tokens are `deterministic`,
`geometric`, `lognormal` (rounded lognormal). Both regions use the same law. Configuration
defaults not active for renewal, including Bernoulli lambdas, remain recorded but inactive.

Membership and entity/zone/region assignment stay fixed; no join/leave/replacement or slot
identity question is introduced. Every law starts from age zero with a full initial dwell,
not a stationary residual-life phase. Regional events change latent and make regional leases
stale; public flags, lagged cues and identity determine the native role and RENEW/KEEP action.
A renewal costs one zero-service primitive step, and does not reset regional dwell age.
The estimand is undiscounted mean native service return over 400 scored steps and 399 transitions
of the reference DP. This is primitive time, not learner or semi-Markov update exposure.

Strongest competent same-information null: `GreedyOnPublicState`. At K2 the flag and lagged cue
identify the unique new latent, so the existing implementation reuses switching and gives
`J_greedy=J_switch`. It needs no learned gap, credit head or duration menu. FixedKOracle remains
a latent-aware numerical reference, not trained D0; open-loop maps and periods are not D8.
The null can completely explain reactive-over-clock gaps by scripted public event response.
Law differences match only nominal mean, not every property except variance.

## Observations, numerical reading and predictions

Per law publish exact configuration, source SHA, command/node, numerical law mean/variance,
DP age cap and complete hazard table. For rounded lognormal additionally report log location,
finite moment support cap, first/second moments, computed mass and `1-computed_mass`.
Reuse its private `_moments()` explicitly as disposable research code; no new core API.
The moment-support truncation differs from the finite-H DP age cap. Floating residual mass
of zero is not proof of zero infinite-support tail or exact infinite-support mean.

Publish `J_switch`, `J_greedy`, every `J_fixed_k`, `best_fixed_k`, `J_best_fixed_k`, all
96 `(zone-role-map, period, value)` open-loop rows, best open-loop candidate/value,
`m=J_switch-J_open_best`, `m_dur=J_switch-J_best_fixed_k`, and
`J_best_fixed_k-J_fixed_k[20]`. Preserve tie behavior of the existing enumerator.
DP uses the existing NumPy float64 arithmetic; no RNG is sampled. `--seed 0` records the
required CLI seed, which is inactive. No checkpoint/model/optimizer is created.

Learning MEI is **not applicable**: there is no learner or algorithm-effect comparison.
Report raw native-return gaps with an absolute reporting tolerance `tau=1e-10`; this is a
floating-arithmetic resolution convention, not a certified roundoff or tail-error enclosure.
Mean calibration consistency uses absolute `1e-8`; hazard values must be finite in [0,1],
variance nonnegative to `1e-10`, and computed mass in [0,1] to `1e-12`.
Numerical consistency observations include greedy minus switching, stored gap arithmetic,
maximum of the complete candidate list, and deterministic switching minus k20. Record exact
observed discrepancies; these checks are scientific observations, not schema machinery.

Apply this rule in order, independently to each law:

1. A cap/failed exit, nonfinite quantity, missing required output/candidate count, or unexplained
   calibration/reference inconsistency makes that law **INCOMPLETE**, with its exact missing
   fact; do not assign scientific polarity or salvage partial output.
2. Otherwise the law is **COMPLETE**. For each reported gap g, `g>tau` is positive at the
   declared numerical resolution, `abs(g)<=tau` is unresolved at that resolution, and
   `g<-tau` is an opposite ordering of these numerical references. No branch is a learning claim.
3. The object is complete only when all three law reports are complete. Stop after this census;
   no result branch selects a second object or changes parameters.

DM predictions on record: deterministic D20 from age zero aligns with k20, so their difference
should be unresolved; public greedy equals switching by K2 source semantics. These are expected
consistency observations, not independent new evidence. For geometric and rounded lognormal,
do not predict a gain magnitude or D2/D8 ordering. A positive structural gap would identify a
clock restriction already explainable by the public null; a resolved negative would demand a
bounded reference-ordering explanation; no resolved gap narrows only this law/grid opportunity.
Owner prediction: **not taken (unattended)**. No new ladder-level owner prediction is invented.
Tuned same-information generic headroom on this renewal host is absent. Existing E3 structural
and trained-D0 shortfall records are historical and are not this object's tuned headroom.

## Prospective cost measurement, budgets and stop rules

Execution is prospectively portable between configured CPU nodes with the existing float64
semantics and reporting tolerance; host identity is not the estimand. Use `wsl_4070` CPU through
the project `remote_first` route. Local control/edits remain local; no WSL configuration change
or restart. One Python process per law is fresh, including lognormal's lazy calibration caches.

Existing computation per full law: 2 switching + 10 fixed-k + 24 open-loop basis DPs = **36 DPs**;
K2 greedy reuses switching. Combining the basis yields **96 candidates**, no extra DP.

| Law | Age states | H * state cells * 36 | Calibration cap | Census cap |
| --- | ---: | ---: | ---: | ---: |
| deterministic D20 | 20 | 4,608,000 | 120 s | 300 s |
| geometric mean20 | 2 | 460,800 | 120 s | 300 s |
| rounded-lognormal mean20 shape1 | 400 | 92,160,000 | 120 s | 300 s |

These work proxies are not seconds, FLOPs or measured speed ratios. The caps are prospective
DM budget choices, not empirical predictions: at most 6 minutes calibration and 15 minutes
full census across three laws, excluding the one focused verification suite.

Before any full-law result invocation, run one bounded calibration for that law at H400 on the
actual node, at committed/pushed source bytes. Measure cold construction **including triggering
mean, variance and hazard computation** (not merely lazy object construction). Then time six
full-H calls to existing `dp_service_profile` in region 0: switching; oracle fixed k1 and k40;
open offset0 at periods k1, k40 and never-renew. The two regions share the law and K2 offsets
are symmetric; the samples still do not prove every DP path takes the same time.

Cost law: `P_law = 2 * (T_cold_law + 36 * max(T_six_DP_samples))`. Record the six measured
times, cold time, H, age states and formula in a technical calibration summary. The factor 2
is a prospective safety allowance. P is an empirical heuristic, not a worst-case bound;
runtime/startup and output costs must be recorded with their measured timing window, not hidden
inside an invented coefficient. If the measured projection exceeds 300 s, or calibration is
incomplete, do not launch that law; report the cost gap at the unchanged card. Do not infer
scientific polarity or increase its cap in this slice. Record the three projections in
`FSD_E4_CENSUS_COST_PROJECTION_20260905.md` before full census launch.

Calibration may compute the six selected DP arrays for timing but does not publish them as
the final scientific census. It adds 18 DP calls; full census adds 108, for **126 DP calls**
excluding toy verification, **288 final candidate values**, and **zero learner exposure**.
No return-dependent calibration stopping, retuning, repeated sweep or automatic retry is selected.
Use existing external `timeout` and `agent-task` for the per-invocation cap; no new supervisor.
Stop each law on its cap, nonfinite output or unexplained inconsistency, leaving its log and
partial output in place. No learner-side failure can be reclassified as optional telemetry.

Immediately before every calibration, test probe or full law invocation, the actual execution
node runs `scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and both physical
and effective memory must be >=4 GiB. Preflight and exact invocation are one accepted
`agent-task` command joined by `&&`, with detached exact-SHA checkout and request-specific output.
Use a new receipt for every invocation. A passing receipt is not a scientific result.
Local fallback only if no remote process was accepted and a fresh local receipt passes, under
the portability already declared here; routing convenience changes no scientific parameter.

## Engineering boundary and technical success

This single logical research change prospectively uses the scope specification section 5
small-reuse exception: from baseline `411adffc3`, cumulatively <=100 new non-test source lines
across all files/commits, reusing the existing reference computation. Report A, D and O/(A+D);
tests/docs separately. No splitting, compression, relocation, padding or unchanged helper
denominator. **Adds no section 4 machinery.** Existing admission, detached task supervision,
external timeout and tracking are reused, not implemented inside the runner.

Owned source: `scripts/run_flexible_skill_duration_e4_census.py`; focused tests under
`tests/experiments/candidates/flexible_skill_duration/e4_census/`. Core `envs/relay_corridor/`
is read-only. One runner has argparse law/mode/output/seed/source/node fields and H override
for a clearly labeled toy test only; formal H remains400. It writes one `summary.json` per
calibration or law. The command shape is frozen here; the literal accepted SHA, cwd, paths,
task and launch command are recorded by CM before dispatch, never invented prospectively.

Run one end-to-end toy smoke and meaningful rule/arithmetic checks of publication, candidate
coverage and source-supported identities at committed bytes remotely; independent reviewer
checks all affected calculations, observations, consumers and publication, and unverified facts.
Successful tests/source review do not establish a scientific gap. No core change, learnability
claim or acceptance of unrelated preexisting source is implicit in this runner's acceptance.

After complete outputs, CM returns technical acceptance; DM writes E0-format result evidence,
applies this rule and writes intake plus a Chinese owner brief. Root owns shared Portfolio,
audit and item CLI surfaces. No new provider request, successor or lifecycle change occurs.

## Decisions this card records

Object tier, options: (a) freeze this bounded measurement then census using existing computation;
(b) keep waiting despite the resolved authorization and runnable finite path; (c) start learning.
Recommend/select (a): it fills the actual cost and output gap without making a new scientific
selection. **Owner-delegated decision (unattended, 2026-09-05 instruction): (a)**,
`OWNER_DELEGATED`; source object selection remains `PRO_FINAL`.
The result is reversible as research artifacts; historical evidence is not deleted.
The exact next discriminator is the three-law full reference census, not a next learner.
