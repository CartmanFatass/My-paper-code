Claim: On the existing balanced allocation toy, equal-budget scalar learning-rate selection may absorb the small METRIC-versus-FREE learning-curve difference observed at one fixed rate.
Binding MARL structure: (c) multi-agent credit assignment; an agent's allocation consumes residual capacity for later agents, and their shared actor receives the joint allocation return.

# MGTAP B03 — same-information scalar-step-size control

Date: 2026-09-04. Direction: `metric_ground_transport_allocation`; route N5.
Class: **B/EXPLORE**, continuing the B02 finite-training geometry ladder.
Object: `mgtap_b03_stepsize`. DM: `/root/dm_amx_n5_continue`.
Selected before new learner output; explicitly outcome-informed by B02.

## Question, ceiling and non-goals

Does the observed METRIC-minus-FREE curve separation persist when each actor
gets the same four scalar SGD learning rates and selection exposure? B02 gave
+0.008396685564959483 at rate 0.1, inside its MEI 0.01. Generic effective step
size remains a live explanation. This is the next comparator/configuration
discriminator within the already accepted B mechanism, an object-tier choice.
The owner's 2026-09-04 explicit research resume supersedes the safe drain.

The ceiling is a preliminary, grid-restricted learning-geometry observation on
the trained centralized N=4/8 allocation toy. This study uses the same exploratory
panel to select and compare rates; the selected contrast is a development
statistic, not independent confirmation. Non-goals are stable superiority,
equivalence, a metric-specific causal effect, globally optimal tuning, held-out
N transfer, churn, decentralized execution, warehouse/UAV efficacy, convergence,
duration adaptation, safety, C promotion and lifecycle changes. The old C objects
remain terminal structural nonidentifications; neither their stationarity gates
nor their efficacy branches apply here. Evidence spec section 11 controls.

## Treatment, competent comparator and surviving explanations

Use the unchanged `Actor("METRIC", "INTACT")` and equal-class
`Actor("FREE", "INTACT")`. Each gets the common rate grid **0.1, 0.3, 1.0, 3.0**.
The treatment is the METRIC actor selected by mean curve AUC across the three
development seeds; the strongest comparator in this object is FREE selected by
exactly the same criterion and budget. In an exact AUC tie choose the smaller
rate. All four curves remain in the result, including the common 0.1 anchor.
There is no per-seed selection or additional search after observing this panel.
The logarithmic grid includes B02's anchor and covers thirty times that rate;
it tests a substantial scalar-rate alternative at the same update budget without
claiming that any grid winner is globally tuned.

Both arms keep 60 float64 output-connected scalars, zero initialization,
features `[1,d0/N,d1/N,d2/N,d3/N,epoch-1]`, dense invertible score maps, the same
legal autoregressive decoder, +/-6 logit clipping, 0.05 uniform exploration,
entropy coefficient 0.005, gradient-norm clip 5, no momentum and no weight decay.
The METRIC map is `I+0.5G`; FREE uses the orthogonal Walsh-Hadamard map. Both have
the same reachable score class and public observations, random priorities,
capacity accounting, action support and scalar team-return feedback. Neither
receives a utility table, oracle action/value, future load, opaque identities,
task row position or another direction's output.

The scalar-rate explanation predicts that selected FREE can catch the rate-0.1
METRIC curve and that symmetric selection leaves no gap of the declared size.
Anisotropic conditioning, implicit finite-SGD regularization, clipping interaction,
and grid-limited optimization remain live even if a residual gap survives. A
same-information rate sweep does not isolate metric binding; a later binding-cut
control would be a different named discriminator. No control is valuable merely
because a gradient statistic changes: the endpoint is native allocation return.

Trace: public role/task demand event -> ephemeral agents each own one service
quantum -> both allocators see identical public role/task/demand/epoch inputs ->
an assignment changes later legal capacities -> REINFORCE credits team return to
the shared actor -> native utility minus idle/unmet penalties changes. There is
no entity/slot identity, join/leave/rejoin, survivor state, replacement, censoring,
partial observation or partner co-adaptation. N is fixed and balanced inside an
episode. Two epochs are independent public allocation decisions, not a delayed
temporal-credit intervention; primitive duration stays fixed.

## Population, RNG, learner and measurements

Reuse the B02 numerical population and learner unchanged: N={4,8}, all 12
ordered distinct task pairs, SLACK/OVERLOAD, both epochs; each update contains
48 two-epoch episodes, 96 allocation transitions and 576 agent steps. The loss
is the existing sum over N of `-0.5*(R/N)*logp - 0.5*0.005*mean_entropy`, divided
by 48. The only numerical treatment changes are the named scalar rates.

Fresh main seeds are **307, 311, 313**, disjoint from B02 and its pilot.
Each of eight actor/rate configurations trains from zero through 256 updates
at each seed, giving **24 fits**. Reuse the inherited B02 PCG64 address law and
phase labels at these fresh seeds; do not silently change the sampler. Training
tapes and presentation permutations are common across all actor/rate choices
within a seed; evaluation tapes are common across arms/rates/checkpoints and
disjoint from training. Neither actor nor rate enters a tape address.

Evaluate at 0,16,...,256, with 16 tapes per pair/load episode/N, two epochs per
tape. Native endpoint is `(R1+R2)/(2N)`. Retain every loss, preclip gradient norm,
step displacement, cumulative path and distance from zero, plus parameter arrays
and episode returns at all 17 points. Report curves and AUC by seed, actor/rate,
N and load; report the existing oracle separately without exposing it to learners.

Per fit: 256 updates, 24,576 training transitions, 147,456 training agent steps,
13,056 evaluation episodes, 26,112 evaluation decisions and 156,672 evaluation
agent steps. Full panel: **6,144 updates; 589,824 training transitions;
3,538,944 training agent steps; 313,344 evaluation episodes; 626,688 evaluation
decisions; 3,760,128 evaluation agent steps**. Model-selection exposure is four
configurations times three seeds per actor, using this same panel; no hidden trials.

## Estimands, MEI and reading rule

Let `A[a,r,s]` be normalized trapezoid AUC over updates 0,16,...,256, divided
by 256. Choose `r_a=argmax_r mean_s A[a,r,s]`, ties to the smaller rate. Define
`d_s=A[METRIC,r_METRIC,s]-A[FREE,r_FREE,s]` and `D=mean_s d_s`.
Also report the common-rate-0.1 contrast, each actor's selection gain over 0.1,
and `H=mean_s(A[FREE,r_FREE,s]-A[METRIC,0.1,s])`, the direct scalar-rate bridge.
Use individual seed values, range and sample SD; no inferential confidence claim.

The absolute MEI is **0.01 normalized return AUC**. A one-percentage-point
curve advantage is the smallest useful signal for spending another small
mechanism-control object here; this keeps the B02 scientific scale while the
comparator becomes stronger. It is not a repository-wide investment threshold.

Reading rule, in order, on the complete 24-fit panel:

1. `B03_METRIC_RESIDUAL_SIGNAL` iff `D >= 0.01` and at least two d_s are positive.
2. `B03_FREE_SELECTED_SIGNAL` iff `D <= -0.01` and at least two d_s are negative.
3. `B03_SELECTED_INSIDE_MEI` iff `abs(D) < 0.01`.
4. `B03_MIXED_SEEDS` otherwise.

No aggregate branch is assigned to incomplete or budget-truncated panels.
Missing/nonfinite learner measurements quarantine the attempt after technical
reproduction; engineering failure has no scientific polarity. An edge-of-grid
winner is retained and flags limited search coverage; it is not a validity gate.

How the result will be interpreted: a positive residual above the MEI motivates
a targeted binding/anisotropy discriminator, with scalar tuning still bounded
to this grid. Inside the MEI, especially with H>=0, the result is consistent with
scalar-step-size absorption and I would stop treating the fixed-rate contrast
as a distinctive metric signal. It does not establish equivalence. An opposite
signal favors selected FREE here and motivates inspecting METRIC's conditioning
cost before another mechanism investment. Mixed seeds motivate a paired-dynamics
or variance discriminator. These narratives do not replace the ordered rule.

## Headroom and predictions

B02's trained-size oracle is 0.66875 and the untuned rate-0.1 FREE endpoint is
0.484165219907407, a gap of 0.184584780092593. A tuned headroom record at held-out
N=6/12 is absent. B03 will report the oracle minus the AUC-selected FREE endpoint
and its full curve at N=4/8 as an exploratory grid-tuned headroom diagnostic, with
the same-panel selection caveat. Existing baseline packages for `scenario_1`
and `relay_corridor` have different observations, actions, information and work;
they cannot substitute for this allocation comparator.

DM prediction: **B03_SELECTED_INSIDE_MEI**, with H>=0; increasing scalar rates
will help both actors more than METRIC's B02 fixed-rate separation. Competing
mechanisms are scalar-rate absorption, a residual bundled-coordinate advantage,
and METRIC conditioning cost favoring FREE. Owner slot: **not taken (unattended)**.
This continues B02's ladder, so its existing owner prediction item is retained;
score any owner reply at intake without inventing a reply.

## Exposure, per-configuration cost and stop rule

Machine-generated arithmetic before learner activity:
`parameters=60; init_l2=0; grad_clip=5; updates=256; lr=[0.1,0.3,1,3];
max_path_l2=[128,384,1280,3840]; unit_logit_reference=1`.
Ratio to initialization scale is undefined at zero, so the listed finite SGD
path budgets use a unit-logit reference. They are upper bounds, not forecasts;
the actual first step and full displacement traces are mandatory observations.

The reused runner cost law is `P[a,r]=2*3*(256*u_a+17*e_a)` seconds per
actor/rate across three seeds, including factor-two allowance. Its existing
B02 pilot measured `u_METRIC=0.007148870814`, `e_METRIC=0.004888009498`,
`u_FREE=0.003733942001`, `e_FREE=0.004117850498` on the configured remote CPU.
Only the scalar SGD rate changes the reused numerical path, so no extra cost
pilot is needed. The new runner reports the same units from its actual runs.

| Configuration | Projection seconds | Per-configuration cap seconds |
| --- | ---: | ---: |
| METRIC 0.1 | 11.4792425391 | 60 |
| METRIC 0.3 | 11.4792425391 | 60 |
| METRIC 1.0 | 11.4792425391 | 60 |
| METRIC 3.0 | 11.4792425391 | 60 |
| FREE 0.1 | 6.1553556643 | 60 |
| FREE 0.3 | 6.1553556643 | 60 |
| FREE 1.0 | 6.1553556643 | 60 |
| FREE 3.0 | 6.1553556643 | 60 |

Apply the cap per configuration, not to an average across configurations.
Use ordinary elapsed checks between updates/evaluations at **20 seconds per
fit**, 60 seconds per configuration over the three seeds; allow 20 seconds
shared setup per seed, 60 total. Maximum new result work is **540 seconds**.
Stop a capped fit and retain its outputs; do not drop it post hoc or compute a
complete-panel branch. No automatic retries, resume or widening of the grid.
Missing wall/RSS leaves valid non-resource evidence `resources_unmeasured`.

## Host, scope and meaning-complete CM objective

Prospectively portable between configured Windows/Linux CPU nodes, float64
PyTorch CPU, NumPy PCG64, one thread. Route remote-first to `wsl_4070`; no GPU,
dtype or RNG change, and no cross-host bit-identity claim. Run each seed as an
invocation at exact committed/pushed bytes in a detached remote worktree through
the existing `agent-task`; immediately precede each runner with destination-local
`admit-memory --out <receipt> && runner`. A local fallback is allowed only under
the configured portable/no-accepted-remote-process/fresh-admission rule.

Engineering scope section 4 needs **none**. Reuse the existing external detached
facility and memory preflight; add no scheduler, guard, registry, retry, resume,
manifest or resource telemetry beyond wall and peak RSS. Required learner traces
are scientific measurements. Scope budgets: <=2,000 new research lines, <=600
runner lines, orchestration <30%. Return a diff that exceeds them rather than
accepting excess machinery as a result cost.

CM owns `scripts/run_mgtap_b03_stepsize.py`, any small helper in
`experiments/candidates/metric_ground_transport_allocation/mgtap_b03_stepsize/`,
mirrored tests, B03 technical/result evidence, and raw artifacts under
`temp/directions/metric_ground_transport_allocation/exp/mgtap_b03_*`.
Preserve the old actor/environment/decoder/oracle/config and B02 source bytes;
reuse their numerical functions without invoking old C orchestration. The DM
owns this card, intake and owner items. Work in an independent worktree; Root
integrates by explicit pathspec. One toy end-to-end smoke through summary
publication and meaningful selection/rule tests suffice; no added launch gates.

CM must return every configuration's curves, counts, selection exposure,
launch SHA, argv, execution node/cwd, accepted task and admission, plus budget
accounting and technical conformance. Passing tests or exit 0 establishes no
mechanism value. DM interprets the direct native returns. Hand accepted tasks
to `/root/tracker_tl_experiments`, responsible DM `/root/dm_amx_n5_continue`;
the tracker observes and reminds, CM collects and repairs.

## Decisions this card produces

Options: (a) run this symmetric rate-control panel; (b) add a binding-cut control
first; (c) extend the rate-0.1 update budget. Recommendation and selection: **(a)**.
The fixed optimizer is the clearest live simpler explanation from B02; (b)
leaves it unresolved and (c) changes work without directly testing it.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Tier object, kind selection, provenance `OWNER_DELEGATED`, reversible, owner
flag none. No Pro round is needed to select this rung of the accepted B ladder.
No family closure, recast, C promotion or Portfolio action is taken.
