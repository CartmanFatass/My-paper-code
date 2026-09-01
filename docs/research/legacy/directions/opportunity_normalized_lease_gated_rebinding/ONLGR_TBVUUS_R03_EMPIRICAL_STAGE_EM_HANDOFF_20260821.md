# ONLGR target-bound voluntary-update utility screen r03 empirical-stage EM handoff — 2026-08-21

```text
document_kind=portfolio_em_empirical_stage_handoff
direction_id=opportunity_normalized_lease_gated_rebinding
empirical_object=ONLGR-TBVUUS-R03-FULL-PANEL
science_object=ONLGR-TARGET-BOUND-VOLUNTARY-UPDATE-UTILITY-SCREEN-DEFINITION
science_revision=ONLGR-TBVUUS-SCIENCE-20260821-03
exact_object_revision=ONLGR-TBVUUS-R03-FULL-PANEL / ONLGR-TBVUUS-SCIENCE-20260821-03
em_owner=/root/em_onlgr_tbvuus_r03
portfolio_owner=Dedicated Portfolio Session 019ffc20-5001-7453-a08a-dac783cf4d80
portfolio_decision=CURRENT_EMPIRICAL_INVESTMENT
science_import=EXACT_UNCHANGED
scientific_activity_started=false
provider_contact_in_this_handoff=none
```

## Exact frozen sources

- Science card: `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_SCIENCE_CARD.md`
- Same-direction ChatGPT External Pro `CLOSED` intake: `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_EXTERNAL_PRO_CLOSURE_INTAKE.md`
- Definition, CM static acceptance and full-cost intake: `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_DEFINITION_COMPLETION_INTAKE.md`
- Portfolio empirical adjudication: `docs/research/workflow-runs/2026-08-11_five-round-research-team/ONLGR_TBVUUS_R03_EMPIRICAL_PORTFOLIO_ADJUDICATION_20260821.md`

The Portfolio adjudication imports the complete Pro-closed, EM-intaken and
CM-statically accepted revision 03 science object without a science-bearing
change. It preserves the fixed `t=0` action, four arms, public-road fit and
fallback, unchanged-waypoint host, fresh paired package, action and effective-
payload support, comparator competence, non-harm, estimands, thresholds,
inference statuses, first-match result map, strongest alternative and claim
ceiling. It changes only Portfolio allocation by authorizing unchanged-science
native construction and the one complete empirical panel. The existing Pro
`CLOSED` disposition and EM intake therefore remain the pre-production
mathematical/causal closure; no provider turn is required for this handoff.

## Frozen action and four arms

Every encounter has one scheduled voluntary decision at the first legal scored
tick `t=0`, after the common BOOT blackout and lockout have ended and after the
current tick's sensor fact is exposed. Every later decision is deterministic
KEEP and is neither an action shell nor payload support. No arm generates or
consumes an action uniform. All arms receive the same public eight-template
road registry and compute the counterfactual road fit from the two most recent
visible post-BOOT samples when exactly two samples with `t_1<t_2<=0` exist.
For every registry template `j`, the exact residual is

```text
R_j = ||z_1-x_base^j(t_1)||_2^2 + ||z_2-x_base^j(t_2)||_2^2.
```

The minimizing template uses the frozen tie order `SHORT` before `LONG`, then
`d=-1` before `d=+1`, then `ell=-8` before `ell=+8`.

When `ROAD_FIT_AVAILABLE=true`, the frozen ROAD payload is

```text
eta_raw   = (z_2-x_base^j*(t_2)) dot N^j*(t_2)
eta_patch = clip(eta_raw,-15 m,+15 m)
x_patch   = x_base^j*(0) + eta_patch*N^j*(0)
v_patch   = (4*pi m/s)*T^j*(0).
```

If the fit is unavailable, ROAD and RAW use the exact identity fallback and
preserve the incumbent estimate, while their scheduled shells still execute
and remain in the intention-to-treat panel. The four arms are frozen as:

- `NEVER-UPDATE`: select KEEP at `t=0`; preserve estimator, buffer and both
  waypoints; pay no charge and start no blackout or lockout; compute only the
  counterfactual ROAD-fit/effective-patch audit.
- `OVERHEAD-SHAM`: execute one `ACTION_SHELL`; debit 200 J from each UAV, start
  the one-second zero-service blackout and four-second lockout, clear the two-
  sample buffer, and preserve estimator and both waypoints exactly.
- `RAW-ESTIMATE-PATCH`: execute the same shell and, when the fit is available,
  set `x_hat=z_2` and
  `v_hat=clip_norm((z_2-z_1)/(t_2-t_1),20 m/s)`; otherwise use the identity
  fallback. It never invokes the planner or changes a waypoint.
- `ROAD-TRACK-ESTIMATE-PATCH` (`ROAD-PATCH`): execute the same shell and, when
  the fit is available, install `(x_patch,v_patch)`; otherwise use the identity
  fallback. It never invokes the planner or changes a waypoint.

Thus ROAD minus NEVER is the fixed-time net valid-service contrast, ROAD minus
SHAM isolates the target-state payload from the matched shell, and ROAD minus
RAW is nominal descriptive evidence only. The energy debit and lockout are
instantiated and logged, but terminal-energy utility is absent and no later
action is foregone.

## Frozen panel, support, comparator and non-harm

The production namespace is fresh and exact:

```text
ONLGR-TBVUUS-HEADLAND90-20260821-v1
HOLD only: 128 independent paired replicates b=0,...,127
4 arms * 128 replicates = 512 controller-replicates
20 paired SHORT/LONG blocks per controller-replicate
20,480 arm-encounters
3,840 ticks per controller-replicate
1,966,080 canonical physical ticks
```

All four arms consume complete shared controller-free disturbance tapes within
a replicate. There is no calibration, selection, rate grid, seed adaptation,
threshold search, early stopping, physical-alias deduplication or
coordinate/replicate replacement. All 512 assigned cells and every audit are
required in one indivisible package and one atomic release.

The exact action-support counts are:

```text
every arm SCHEDULED_T0_DECISION_COUNT = 5,120
ROAD-PATCH ACTION_SHELL_COUNT         = 5,120
RAW-PATCH ACTION_SHELL_COUNT          = 5,120
OVERHEAD-SHAM ACTION_SHELL_COUNT      = 5,120
NEVER-UPDATE ACTION_SHELL_COUNT       = 0.
```

An effective ROAD payload is prospectively defined, without selecting rows, by

```text
EFFECTIVE_ROAD_PATCH = ROAD_FIT_AVAILABLE
  AND (||x_patch-x_hat_pre||_2>=1 m
       OR ||v_patch-v_hat_pre||_2>=1 m/s).
```

`EFFECTIVE_ROAD_PATCH_SUPPORT_OK` requires at least 512 effective encounters
in HOLD and at least 96 of 128 replicates with one or more effective encounter.
SHORT/LONG counts are mandatory diagnostics only. They cannot gate or support
a timing or heterogeneity interpretation.

`TBVUUS_PACKAGE_VALID` and `SHAM_VALID` are exactly those in section 7 of the
frozen science card. They require the exact identities, complete four-arm
paired package, no action word, exact arm transitions and ledgers, exact
fallbacks, RAW conformance, no missing/substituted/imputed/deleted or
outcome-selected cell, atomic release, and exact SHAM equality except for the
registered shell effects. In particular, SHAM must satisfy paired tickwise
`q_SHAM<=q_NEVER` and, absent battery exhaustion, equality after blackout.

The NEVER comparator is competent only if

```text
TBVUUS_PACKAGE_VALID
HOLD_HARD_SAFE(NEVER)
MEAN_VALUE(NEVER)>=0.25
TAIL_VALUE(NEVER)>=0.10
1-MEAN_VALUE(NEVER)>=0.05.
```

`ROAD_NONHARM` requires zero ROAD terrain penetrations, geofence exits,
separation breaches, `NO_SAFE_CONTROL`, `NO_PLANNER_SOLUTION`, battery
exhaustions and numerical faults in every assigned cell, plus

```text
UCB95[override(ROAD)-override(NEVER)]<=0.01.
```

All support, route and template facts remain audit/diagnostic facts. Every
claim-bearing interval is an unconditional full-panel intention-to-treat
interval over all 128 assigned replicates.

## Frozen estimands, gate statuses and ordered result map

For replicate `b` and endpoint `e in {mean,tail}`, first form each arm's
20-block endpoint, then define

```text
VALUE_b,mean(C) = M_b(C)
VALUE_b,tail(C) = T_b(C)
d_AN,b,e = VALUE_b,e(ROAD-PATCH)-VALUE_b,e(NEVER)
d_AH,b,e = VALUE_b,e(ROAD-PATCH)-VALUE_b,e(OVERHEAD-SHAM)
d_AR,b,e = VALUE_b,e(ROAD-PATCH)-VALUE_b,e(RAW-PATCH).
```

Every contrast uses all 128 paired replicate differences and the frozen
two-sided Student-t interval with `t_(0.975,127)=1.97882`. The four
claim-bearing gates are:

```text
mean(d_AN,mean)>=0.02 and LCB95(d_AN,mean)>0
mean(d_AN,tail)>=0.05 and LCB95(d_AN,tail)>0
mean(d_AH,mean)>=0.02 and LCB95(d_AH,mean)>0
mean(d_AH,tail)>=0.05 and LCB95(d_AH,tail)>0.
```

For each gate with registered margin `m_e`, record exactly one of `PASS`,
`MATERIALITY_RULE_NONPASS`, `SIGN_PRECISE_NONPASS`, or
`SIGN_POWER_NONIDENTIFYING` by:

```text
PASS                       = point estimate>=m_e AND LCB95>0
MATERIALITY_RULE_NONPASS   = point estimate<m_e
SIGN_PRECISE_NONPASS       = point estimate>=m_e AND LCB95<=0 AND sd<=s_e
SIGN_POWER_NONIDENTIFYING  = point estimate>=m_e AND LCB95<=0 AND sd>s_e,
```

where `s_e=0.080` for mean and `s_e=0.200` for tail. These SD limits apply only
to the positive-sign component and do not promise power for the complete joint
gate. ROAD minus RAW is always reported with its nominal interval but never
gates, selects, repairs or enlarges a claim.

Apply the first matching branch, without reordering:

1. Invalid `TBVUUS_PACKAGE_VALID`, `SHAM_VALID`, common host, pairing or
   endpoint audit: return the exact common-package nonidentification reason.
2. Incompetent NEVER: `NEVER_UPDATE_COMPARATOR_NONIDENTIFIED`.
3. Failed shell or effective-payload support:
   `ROAD_PATCH_ACTION_SUPPORT_NONIDENTIFIED`.
4. Failed ROAD non-harm: `ROAD_PATCH_EXACT_PACKAGE_NONHARM_FAILED` with the
   concrete physical fact.
5. Both net and both payload-isolation gates pass:
   `ROAD_PATCH_DIRECT_UTILITY_QUALIFIES`.
6. Any failed gate is `SIGN_POWER_NONIDENTIFYING`:
   `ROAD_PATCH_POWER_NONIDENTIFYING` with the complete four-gate vector.
7. Both ROAD-minus-NEVER gates pass but either ROAD-minus-SHAM gate is a
   materiality or sign-precise nonpass: `NET_VALUE_WITHOUT_PAYLOAD_ISOLATION`.
8. Both ROAD-minus-SHAM gates pass but either ROAD-minus-NEVER gate is a
   materiality or sign-precise nonpass:
   `PAYLOAD_BENEFIT_WITHOUT_MATERIAL_NET_UTILITY`.
9. Every other materiality/sign-precise nonpass pattern:
   `VALID_ROAD_PATCH_DIRECT_UTILITY_NONPASS` with the four-gate vector.

Only branch 5 may make a separately defined future
`ROAD-PATCH GLOBAL-TIME vs TWO-STRATUM-TIME` question eligible for Portfolio
consideration. It does not authorize that question. No other branch supports a
timing, fixed-rate, general no-update or action-uselessness claim.

## Scientific activity boundary

No source, build, test, probe, coordinate, random word, trajectory, evaluation,
result, lease or question-relevant activity had occurred for this object at the
Portfolio decision boundary. The adjudication now authorizes unchanged-science
construction and conformance. Those engineering acts remain preactivity only
while they create no word in the fresh production namespace and execute no
controller tick on a fresh production coordinate.

Scientific activity starts at the earlier of the first materialization of a
word in `ONLGR-TBVUUS-HEADLAND90-20260821-v1` or the first controller tick on a
new production coordinate. Technical and mandatory efficiency acceptance must
precede that boundary. No science-bearing field may change after it. Before
the boundary, a science-bearing ambiguity or proposed object change returns
through the two-root bridge to this EM. After it, science-neutral repair and
blinded, same-coordinate, atomic continuation remain CM work until the complete
question-relevant panel exists.

## Strongest alternative and claim ceiling

The strongest alternative to a positive result is privileged package
alignment: the public registry exactly contains the true unperturbed road
family, the synchronized `t=0` action uses fresh post-BOOT samples that the
BOOT-only comparator does not assimilate, and the host's 15 m tracking-validity
boundary may specially favor this correction. The benefit may reflect a
privileged road prior or generic fresh-sample assimilation rather than road
regularization or general voluntary-update value. LONG receives four times
SHORT's physical-time weight; map error, computation latency, packet-size cost
and terminal-energy utility are absent, and unchanged waypoints exclude a
replanning or relay-portal claim.

The maximum positive claim is limited to fresh paired coordinates of the exact
analytic `HEADLAND-90-ROAD-TRACK-PATCH-UTILITY-v1` package: one shared fixed-
`t=0` intention-to-treat ROAD policy installed the frozen patch when the fit was
available and the identity fallback otherwise, met the registered effective-
support floor, and improved mean and lower-tail physical-time valid target
service over both BOOT-only NEVER and the action-shell-matched identity SHAM,
while retaining the frozen shell, energy, lockout, waypoint, physics, radio,
safety and pairing laws. No outcome establishes optimal/repeated timing,
event-rate value,
route-package heterogeneity, arbitrary/adaptive `k`, variable `N`, joint
replanning, relay-portal value, map-error robustness, real-aircraft transfer,
safety certification, deployment, terminal-energy utility or general
algorithm superiority. A nonpass is local to this exact one-shot package and
does not show that voluntary updating is generally useless.

## Exact result-intake and same-Pro convergence boundary

The ordinary result path is CM -> Operational Root -> Portfolio -> this EM.
Scientific intake begins only from the exact CM-authored artifact for a
technically accepted, complete and question-relevant r03 panel. This EM will
accept CM's technical facts rather than redo engineering acceptance, apply the
frozen first-match map, and author the direction-local conclusion, strongest
alternative, claim ceiling and next discriminator. A no-data or incomplete-
panel return has no partial scientific interpretation and remains CM work for
unchanged-science repair and completion.

After complete-result EM intake, this EM will freeze one result-convergence
science-only question and reuse the same ONLGR ChatGPT External Pro conversation
identified by the `CLOSED` intake above. It will ask whether the bounded
conclusion follows, what strongest alternative survives, what claim ceiling
applies and which next discriminator has the highest information value. Pro
will not be asked to accept code/runtime, select the portfolio or alter the
frozen observation. This EM will author the Pro convergence intake and return
one complete decision-level packet to Portfolio.

The stage returns early to Portfolio only for a science-bearing ambiguity or
proposed object change relayed from CM, a material cost-class expansion, a
genuine cross-scope conflict or an external-authority expansion. Runtime,
lease, PID, progress, coordinate, receipt and partial-result streams do not
cross the science/engineering interface.

## Protected exclusions

- No HEADLAND r03 rerun, rate repair, timing successor, second surface,
  selector/action-uniform/result/threshold/coordinate reuse or reinterpretation
  of the completed r03 timing object.
- No change to the fixed action instant, four arms, ROAD transform, availability
  or identity fallback, shell, estimator-only scope, waypoints, host physics,
  sensing, endpoint, pairing, support, comparator, non-harm, thresholds,
  inference statuses, branch precedence or claim ceiling.
- No partial-arm, replicate, block, route-class, endpoint, support, gate or
  branch interpretation; no cell replacement, row selection, imputation,
  retuning, threshold relaxation, early stop, result-dependent stop, payload or
  timing menu, or class-conditioned post-hoc claim.
- No Python per-tick or panel production fallback, training, backward work,
  GPU work, production deployment, real flight or safety-certification action.
  Python may be only a fixture/debug oracle for native conformance.
- No CM provider contact or scientific interpretation, no direct EM-CM contact,
  no Portfolio decision by this EM, and no shared-canonical write, user contact,
  lease allocation or Git action by this EM.

## Exact cross-root request body

```text
PORTFOLIO_EM_TO_ROOT_CM_REQUEST
marker=PORTFOLIO_EM_TO_ROOT_CM_ONLGR_TBVUUS_R03_FULL_PANEL_20260821
direction_id=opportunity_normalized_lease_gated_rebinding
exact_object_revision=ONLGR-TBVUUS-R03-FULL-PANEL / ONLGR-TBVUUS-SCIENCE-20260821-03
em_owner=/root/em_onlgr_tbvuus_r03
science_artifacts=docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TBVUUS_R03_EMPIRICAL_STAGE_EM_HANDOFF_20260821.md|docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_SCIENCE_CARD.md|docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_DEFINITION_COMPLETION_INTAKE.md
pro_disposition_and_em_intake=docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_TARGET_BOUND_VOLUNTARY_UPDATE_UTILITY_SCREEN_EXTERNAL_PRO_CLOSURE_INTAKE.md
portfolio_decision_artifact=docs/research/workflow-runs/2026-08-11_five-round-research-team/ONLGR_TBVUUS_R03_EMPIRICAL_PORTFOLIO_ADJUDICATION_20260821.md
observed_fact=The Portfolio adjudication exactly imports the Pro-closed, EM-intaken, CM-static-accepted ONLGR-TBVUUS-SCIENCE-20260821-03 object without science revision, records no prior question-relevant activity, and authorizes the immutable full panel.
technical_question=Construct and technically conform a separate exact-stage native C++ reset-to-terminal component for the frozen four-arm ROAD utility screen, complete every audit/endpoint/inference/ordered-map field, pass the mandatory result-blind full-chain efficiency and equivalence review, then materialize fresh coordinates only after technical acceptance and, under a later Operational-Root lease, execute the indivisible panel and return one technically accepted complete atomic result artifact.
protected_semantics=Preserve the single scheduled t=0 action and later KEEP law; exact NEVER/SHAM/RAW/ROAD arms, public-road fit and fallback, unchanged waypoints, common shell, no action word, 128 fresh paired replicates/512 controller-replicates/20480 encounters/1966080 ticks, exact shell and effective-support floors, NEVER competence, ROAD non-harm, unconditional full-panel paired estimands, four thresholds/statuses, descriptive-only RAW contrast, first-match branch order, strongest alternative and claim ceiling.
allowed_engineering=Same-direction native source/runner/schema/test construction; a separate exact-stage C++ reset-to-terminal component with four-arm paired batching; Python fixture/debug oracle only; conformance and technical acceptance; result-blind process-cold/warm B=1/8/32 baseline/optimized full-chain review covering environment, loader/cache, rollout, zero forward/backward work, evaluation/inference, I/O, resume and atomic release with CPU/RSS/I/O/wall measurements, semantic equivalence and rollback nodes; fresh namespace/coordinates after acceptance; blinded same-coordinate atomic continuation and full execution under a later Root lease; complete reduction and CM-authored result installation.
prospective_cost=7-10 focused engineer-days; 3-7 total construction/conformance/benchmark-plus-panel CPU-hours; 1-2 post-readiness one-worker panel wall-hours; <=4 GiB RSS; <=1 GiB expected durable storage and 4 GiB hard storage; no GPU/training/backward work.
compute_class=later Operational-Root direction-scoped one-worker CPU-only lease required before production-coordinate materialization and the complete empirical panel; frozen limits are <=4 GiB RSS, <=1 GiB expected durable storage and 4 GiB hard storage
local_fence=No HEADLAND r03 rerun/rate repair, timing successor, second surface, old coordinate/selector/action-uniform/result/threshold reuse, Python production fallback, partial interpretation, search/retuning/replacement, production deployment or flight.
scientific_stage_continuation=Unchanged-science native construction, conformance, mandatory efficiency acceptance, fresh-coordinate full-panel execution and technically accepted complete result remain live; the exact result returns through Operational Root and Portfolio to this EM for frozen-map intake and same-conversation ONLGR Pro convergence.
root_decision_class=Portfolio empirical-investment decision already made; Operational Root applies the CM construction stage and later lease/resource authority without changing science, while CM owns engineering, coordinates, execution and technical acceptance.
return_boundary=Return the exact CM-authored technically accepted complete-result artifact through Operational Root; before activity return an exact science-bearing ambiguity/proposed object change, projected total above 10 focused engineer-days/10 CPU-hours/16 GiB RSS/4 GiB storage, changed physics/sensing/endpoint law or genuine cross-scope conflict, and after activity preserve frozen science while returning only required lease/resource expansion or cross-scope conflict at its owner boundary; exclude runtime/status and partial-result streams.
post_cm_science_boundary=Portfolio returns the exact CM artifact to /root/em_onlgr_tbvuus_r03; EM applies the complete first-match result map, authors scientific intake, reuses the same ONLGR ChatGPT External Pro conversation for result convergence, intakes that response and returns one decision-level packet to Portfolio.
does_not_authorize=No direct EM-CM contact, science revision, partial-result interpretation, CM provider contact/scientific conclusion, timing/rate successor, Portfolio re-adjudication by EM, shared-canonical write, user contact, lease allocation or Git action by EM, production deployment or flight.
```
