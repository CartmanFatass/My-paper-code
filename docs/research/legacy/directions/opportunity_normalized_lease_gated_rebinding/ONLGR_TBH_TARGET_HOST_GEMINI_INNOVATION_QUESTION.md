# ONLGR-TBH target-host Gemini innovation question

Direction: `opportunity_normalized_lease_gated_rebinding`  
Object: `ONLGR-TBH-TARGET-HOST-EXECUTABLE-CARD-DEFINITION`  
Provider role: mutually blind divergent innovation, advisory and non-gating  
Question status: frozen before provider use  

Act as a divergent scientific innovator for one prospective definition-only
task. Do not review code, repositories, files, tests, implementation, runtime,
or empirical results. No task trajectory or result exists. Do not attempt
mathematical closure or portfolio selection.

We need to select and fully define one natural constructed two-UAV target host.
Tracker UAV `T` must track a moving target and emit timestamped state packets;
relay UAV `R` must preserve the `T-R-B` path to a fixed ground station `B`.
One event controller chooses only `KEEP` or `JOINT-UPDATE`; an update invokes a
common deterministic joint planner, costs energy, creates a service blackout,
and starts a common lockout. All rate families share physical dynamics, link
law, planner, action, safety, event law, and target-service endpoint.

Before action, an exogenous route/contact generator must assign immutable
packages:

```text
SHORT = transient handoff corridor with scheduled tenure 2*tau_lock
LONG  = sustained clear corridor with scheduled tenure 8*tau_lock.
```

The class and remaining scheduled tenure are visible before each event
decision, cannot depend on policy or outcomes, and may not be relabeled later.
The registered physical direction is a higher useful update rate in SHORT than
LONG. A stable opposite-sign result must also be interpretable.

Every future controller uses

```text
Q={0,1/8,...,7/8}
lambda(q)=-log(1-q)/tau_lock
p_event(e,lambda)=1-exp(-lambda*e).
```

`GLOBAL-BEST` is the calibration-best pooled constant. `TWO-STRATUM` selects
one rate per immutable class. A finite `FLEX-CONTAIN` family reads class,
remaining-tenure fraction, and time since corridor entry or last voluntary
update; its finite domain must contain every `Q x Q` lookup exactly and include
a genuinely nonconstant policy when selected. Confirmatory endpoints are mean
valid end-to-end target-service fraction and lower-CVaR at 0.10. A qualified
two-rate result requires both endpoints, positive paired lower bounds,
reciprocal held-out rate swaps, support, ceiling headroom, and non-harm.

Produce one advisory packet with four parts.

1. Propose three physically natural host mechanisms, not reward-table or
   label-engineered examples. For each, specify why the SHORT/LONG package is
   exogenous, why the rate response could plausibly differ, the strongest
   countermechanism, and the smallest physical facts needed to make tracking,
   packet delivery, energy, blackout, and safety auditable.
2. Recommend exactly one host for identifiability and cost. Give a compact
   candidate set of continuous/discrete physical laws: target and UAV motion,
   sensing, line-of-sight/link success, packet age/deadline, deterministic joint
   planner, update blackout/energy/lockout, safety override, clocks and service
   indicator. Use plausible dimensioned values or dimensionless ratios, but
   label every unsupported engineering number as a design constant rather than
   a real-aircraft fact.
3. Stress-test the recommended host. Seek routes by which the class becomes
   post-treatment, the planner or link law leaks an answer, the pooled
   comparator is handicapped, an apparent reciprocal response is a carryover
   artifact, the lower tail is underpowered, or FLEX is only a disguised lookup.
   Give prospective controls that preserve the same scientific question.
4. Suggest a finite, explicitly enumerable `FLEX-CONTAIN` coefficient family
   that contains all 64 lookup policies, adds real timing variation, and avoids
   a six-dimensional Cartesian explosion. Also give symbolic calibration and
   held-out cost/power considerations. Do not choose stochastic coordinates,
   run counts, or thresholds from outcomes and do not claim that your design is
   empirically adequate.

Return a bounded recommendation, strongest alternative, failure boundaries,
and the single most information-preserving host design. No continuous-surface,
ONLGR-B2 rescue, lease/rebinding/hazard, arbitrary-`k`, variable-`N`, UAV
deployment, or general-algorithm claim is in scope.
