# ONLGR target-bound heterogeneity screen: frozen Pro closure question

Object: `ONLGR-TARGET-BOUND-HETEROGENEITY-SCREEN-DEFINITION`  
Revision: `ONLGR-TBH-SCREEN-DEF-20260815-02`  
Conversation: reuse the existing ONLGR ChatGPT External Pro conversation  
Question status: frozen before provider use  

Continue the existing ONLGR scientific conversation. This is a new prospective
definition-only target-bound screen prompted by the previously stated revisit
condition; it is not an ONLGR-B2 restart, a reanalysis, or an empirical claim.
No code, task outcome, calibration response, stochastic coordinate, or runtime
fact exists for this object.

Review the complete definition below as one indivisible conceptual scientific
object. Determine whether it meaningfully defines:

1. a physical two-UAV target-tracking and relay task;
2. two genuinely ex-ante, action-independent timing/tenure strata rather than
   post-hoc heterogeneity;
3. a physical reciprocal-response reason one pooled global rate may fail;
4. a genuinely calibration-best pooled constant comparator without held-out
   leakage;
5. a two-stratum controller whose sole additional rate input is the prospective
   class;
6. a flexible timing-rate comparator that exactly contains every two-stratum
   controller and has an explicit fallback protecting that containment from
   optimization failure;
7. physical mean and lower-tail endpoints, competence and headroom rules,
   reproducibility boundaries, nonidentification branches, strongest
   alternatives, and an appropriately bounded maximum claim; and
8. a clear boundary between this complete definition and a later, separately
   Pro-closed executable science card that alone may choose a simulator,
   coordinates, counts, search budget, or production conditions.

Return exactly one leading disposition:

```text
CLOSED
```

or

```text
REVISION_REQUIRED
```

If `CLOSED`, state that there is no science-bearing conceptual defect for this
definition-only stage and restate the maximum permissible future claim in one
bounded paragraph. If `REVISION_REQUIRED`, enumerate every exact mathematical
or causal defect, the smallest correction, and the claim boundary until
corrected. Do not review code, implementation feasibility, tests, runtime,
compute, repositories, files, hashes, receipts, or technical acceptance.

## Exact definition under review

The task has tracker UAV `T`, relay UAV `R`, and fixed ground station `B`. A
fixed common low-level flight/safety controller executes plans. At physical
time `t`, valid service is one exactly when tracker error is within a fixed
task tolerance, a target packet reaches `B` by a fixed deadline, and both air
links are valid. The event controller chooses `KEEP` or `JOINT-UPDATE`;
`JOINT-UPDATE` invokes one fixed deterministic joint planner and has common
nonzero energy, service-blackout, and lockout cost. Safety is common and
external to the voluntary event policy.

Before action, an exogenous route/contact plan labels every corridor and its
scheduled start/end time. `SHORT` is a transient handoff corridor of scheduled
tenure `2*tau_lock`; `LONG` is a sustained clear corridor of scheduled tenure
`8*tau_lock`. Both labels and remaining tenure are visible before every event
decision. They are fixed by route, terrain/occlusion, and contact plan and
cannot depend on actions, rewards, realized tracking/link success, learned
state, or later outcomes. Every future analysis block contains both classes
and orders, and the classes cannot be recut after outcomes.

The physical hypothesis is `lambda_SHORT > lambda_LONG`: prompt updates can
avoid missing a narrow transient handoff, whereas redundant updates in a
sustained corridor spend energy and blackout without comparable benefit. The
registered response must be reciprocal: the SHORT-selected rate improves
SHORT service relative to the LONG-selected rate, and vice versa.

Every arm uses

```text
p_event(e,lambda)=1-exp(-lambda*e)
Q={0,1/8,2/8,3/8,4/8,5/8,6/8,7/8}
lambda(q)=-log(1-q)/tau_lock.
```

`GLOBAL-BEST` evaluates every `q in Q` on the complete paired calibration
panel, pools classes by physical time, and selects by highest mean service,
then highest lower-tail service, then fewest updates, then lowest `q`. It is
frozen before held-out evaluation. `TWO-STRATUM` evaluates every pair in
`Q x Q` on the same calibration panel and uses the same selector plus fixed
rate-sum/rate tie breaks. It is one controller that reads only the current
exogenous class for rate selection.

For normalized remaining tenure `r`, normalized time since the later of
corridor entry or last voluntary update `a` (using corridor entry when no
voluntary update has occurred), and class `s`, the containing comparator is

```text
q_F(s,r,a)=clip_[0,7/8](alpha_s+beta_s*(r-1/2)+gamma_s*(a-1/2))
lambda_F=-log(1-q_F)/tau_lock.
```

Setting slopes to zero and the intercepts to `(q_S,q_L)` exactly recovers any
two-stratum member; equal intercepts recover any global member. Its calibration
selector explicitly includes the frozen selected two-stratum controller as a
fallback. A later executable card must freeze the finite coefficient domain
and search rule before activity.

For episode `i`, `Y_i` is the fraction of physical mission time with valid
end-to-end target service. Update blackout is included in failure time and a
common hard per-UAV battery budget is enforced. The endpoints are mean `Y_i`
and lower-CVaR at 10%, with raw tracking, packet, link, energy, update,
blackout, and safety facts reported. Hard battery, flight, separation, and
safety facts are non-harm gates.

A future package is identifying only if it is complete; the best global has
both voluntary actions in both strata, satisfies constraints, and retains at
least `0.05` service headroom; the selected pair is a complete `Q x Q`
calibration maximizer, its conditional stratum maximizer sets are disjoint and
half-split-stable within one grid step; `q_S>q_L`; each reciprocal
stratum-rate swap loses at least `0.02` service with a paired 95% lower bound
above zero; and two-stratum minus global improves held-out mean service by at
least `0.02` and held-out lower-CVaR by at least `0.05`, with each paired 95%
lower bound above zero. All hard non-harm gates must pass.

The flexible comparator is auxiliary. If the two-stratum screen qualifies but
flexible loses more than `0.01` on either endpoint, the local two-rate physical
result remains while flexible optimization is unresolved. If two-stratum does
not qualify but flexible independently clears both global gates, that is a new
continuous-timing question and cannot make this screen pass. Missing package,
competence, response identification, or headroom is nonidentification; valid
gate nonpassage does not prove global-rate sufficiency.

All future physical facts, fresh blinded coordinates, independent-replicate
counts, paired disturbance tapes, calibration/test split, coefficient search,
uncertainty rules, and complete-panel release must be prospectively frozen in
a distinct executable card. Nothing is chosen or run now.

At most, a future passing result could say that on this exact constructed
two-UAV task, two prospectively labeled route/contact packages observable
before action had reciprocally different calibration-best legal joint-update
rates, and one shared two-stratum controller improved both mean and worst-
decile held-out valid target-service time over the best pooled constant under
common physics, planner, action, energy, safety, event link, and paired
disturbances. It could not establish tenure causality apart from the corridor
package, ONLGR-B2 rescue, link/lease/rebinding/hazard causality, arbitrary or
continuous `k`, variable `N`, within-cap success, real-aircraft transfer,
other-task generalization, or general superiority.
