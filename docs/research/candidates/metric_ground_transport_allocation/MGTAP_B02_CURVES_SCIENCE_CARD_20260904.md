Claim: In the existing balanced allocation toy, METRIC coordinates may change finite-budget return learning curves relative to an equal-class FREE actor under matched information and work.
Binding MARL structure: (c) multi-agent credit assignment; each sampled assignment changes residual capacity for later agents, and the joint allocation return trains their shared policy.

# MGTAP B02 — finite-budget allocation learning curves

Date: 2026-09-04. Direction: `metric_ground_transport_allocation`; route N5.
Class: **B/EXPLORE**. Object: `mgtap_b02_curves`. DM: `/root/dm_amx_n5_allocation`.
Status: selected and prospectively specified before implementation or learner activity.

## Question and authority

At budgets 16, 64 and 256 SGD updates, and along the entire recorded curve, does
METRIC-INTACT learn a different normalized native return from FREE on the existing
N={4,8} population? The primary estimand integrates the curve through update 256.
This is a new B object under the owner-adopted N5 agenda in
`../../portfolio/decisions/2026-09-04-adopt-nine-routes-and-resume.md` and
`../../portfolio/decisions/2026-09-04-two-line-nine-route-proposal.md`.

Both old C objects remain terminal structural nonidentifications. Their selected
learning rate motivates this explicitly outcome-informed B choice; their calibration
values are not efficacy evidence, priors, pooled samples, or observations of B02.
This is no third support extension of either C object. The old stationarity gate,
conclusion-seed split, manifest/certificate machinery, and Pro/preactivity gates do
not apply. Evidence spec section 11.4 controls this B launch.

Claim ceiling: preliminary finite-training learning geometry on a centralized,
balanced two-role/four-task/two-epoch toy at the two trained sizes. Non-goals:
stable superiority, pure metric causality, general optimal transport, held-out-N
transfer, membership churn, decentralized execution, warehouse or UAV efficacy,
duration adaptation, convergence, safety, or lifecycle decisions. The two epochs
are independent public allocation decisions; no delayed temporal-credit claim.

## Mechanism, comparator and information

Reuse the existing `actor.py`, `environment.py`, `decoder.py`, `oracle.py`, and
`config.py` primitives without changing the old experiment. Both arms have 60
output-connected float64 scalars, zero initialization, features
`[1,d0/N,d1/N,d2/N,d3/N,epoch-1]`, the same legal autoregressive decoder,
logit clipping at +/-6, 0.05 uniform exploration mixture, entropy coefficient
0.005, and gradient-norm clip 5. The centralized public input, random priorities,
capacity accounting, action support and scalar team-return feedback are matched.
No actor receives the physical utility table, oracle action/value, future load,
opaque identities, task row position or another direction's output.

- Treatment: existing `Actor("METRIC", "INTACT")`, with the dense invertible
  ground-correlated map `I + 0.5 G`.
- Strongest equal-class comparison: existing `Actor("FREE", "INTACT")`, the
  dense orthogonal Walsh-Hadamard map, with exactly the same reachable score class.
  For any treatment W, FREE can represent it with `W_F=B_F.T B_M W_M`.
- Both receive the same observations; FREE may ignore the coordinates. Both use
  dense map arithmetic, the same two N batches, and equal learner/evaluation work.
  There is no weaker-information load-only baseline substituted for FREE.

The strongest live alternative is generic coordinate-dependent conditioning or
effective step size, followed by the implicit regularization of finite SGD; a
shared fixed learning rate need not optimize both coordinate systems. Explicit
weight decay is zero in both arms to remove that extra first-rung difference.
No CUT arm or tuned learning-rate grid is added at this first rung. Therefore even
a positive result identifies only the bundled coordinate/optimization contrast.
A curve signal would motivate a separately named conditioning-matched FREE or
binding-cut discriminator, not a metric-specific efficacy statement.

Trace: public role/task demand event -> ephemeral agents own one service quantum
each -> allocator sees identical public role, task, demand and epoch information ->
sampled assignment consumes task capacity and changes later legal choices ->
REINFORCE credits the normalized joint return to the shared actor -> native team
utility minus idle/unmet penalties changes. Entity and slot identity are absent;
there is no join/leave/rejoin, replacement, survivor state, censoring, partial
observation, partner learning or co-adaptation. N is balanced and constant within
each episode; duration is fixed at one allocation opportunity per epoch.

## Population, learner and full curves

Training uses the inherited complete factorial: N={4,8}, all 12 ordered distinct
task pairs, both SLACK/OVERLOAD load flags, and both epochs. Each update has
48 two-epoch episodes = 96 allocation transitions = 576 autoregressive agent
steps. Epoch reward and loss normalization remain the existing trainer's:
sum over the two N groups of `-0.5*(R/N)*logp - 0.5*0.005*mean_entropy`, divided
by 48. SGD has learning rate 0.1, momentum 0 and weight decay 0.

Main paired seeds: **203, 211, 223**. No hyperparameter or checkpoint selection:
one declared configuration per arm, zero search exposure. Each arm/seed trains
once through **256 updates**, retaining every update's loss, pre-clip gradient
norm and displacement from the zero initializer. Evaluate at **0,16,32,...,256**,
including the named budgets 16/64/256; never retain only the best checkpoint.

Every evaluation point uses all 24 pair/load episodes at each N, with **16 tapes
per episode**, two epochs per tape. Native endpoint is `(R1+R2)/(2N)`.
Use the same evaluation tapes across arms and checkpoints within a seed, disjoint
from training. Training tapes and presentation permutations are shared across
arms for the same seed/update/N. New B02-specific phase tags or an explicit new
SeedSequence namespace keep both phases separate from the old C RNG addresses.
Arms must not draw from a single mutable RNG stream in arm-execution order.

Report each seed and each N curve, their equal-weight aggregate, return by load,
native evaluation count, and the primary AUC contrast. Retain all evaluation
episode returns (or a compact array with equivalent per-episode records), and
parameters at the evaluation checkpoints to make the reported curve inspectable;
these are measurement outputs, not resume orchestration. Compute the existing
nonanticipating immediate-allocation oracle on this same population once, outside
policy inputs/labels, and report its gap to each curve as a diagnostic.

## Estimand, MEI and result branches

For seed s, `J_A,s(t)` is the equal-weight average of N=4 and N=8 native
evaluation return. `A_A,s = trapz(J_A,s(t), t)/256` on the complete 17-point
grid. Let `d_s=A_METRIC,s-A_FREE,s` and `D=mean_s(d_s)`. Report individual d_s,
range, mean, sample standard deviation and every terminal/named-budget contrast;
three seeds do not justify a stable-performance confidence claim. Tapes are not
independent training replicates.

**MEI = 0.01 absolute normalized native return in curve AUC.** A relative-only
MEI is unsuitable because early returns can be small. One percentage point per
agent/epoch, sustained over the curve rather than at one selected endpoint, is
enough to justify a small conditioning discriminator but not broad investment.
It is chosen for this B object, not inherited from the old C margins.

Reading rule, in this order, on the complete main panel:

1. `B02_METRIC_CURVE_SIGNAL` iff `D >= 0.01` and at least two d_s are positive.
2. `B02_FREE_CURVE_SIGNAL` iff `D <= -0.01` and at least two d_s are negative.
3. `B02_INSIDE_MEI` iff `abs(D) < 0.01`.
4. `B02_MIXED_SEEDS` otherwise.

An incomplete implementation/panel has no aggregate scientific branch; retain
its partial outputs and reproduce a failing step before classifying the cause.
No stationarity or competence threshold hides a valid learning curve. A stopped
budget arm is reported as budget-truncated and cannot supply the full-panel AUC.

How the result will be interpreted: above the positive MEI, the bundled METRIC
coordinates show a preliminary curve benefit and I would recommend a small
same-information conditioning control. Inside the MEI, the first rung gives no
effect of the declared size and I would inspect curve motion/headroom before
recommending a targeted budget or step-size change. An opposite-sign signal
favors FREE on this setup and I would first test whether METRIC's conditioning is
the cost. Mixed seeds call for a variance or paired-dynamics discriminator.
These are descriptions; the ordered branches above control the reported result.

## Headroom and predictions on record

Current-host normative headroom is **absent**: the A1 census
`MGTAP_GUIDANCE_A1_HEADROOM_CENSUS_RESULT_EVIDENCE_20260904.md` found no valid
final tuned same-information FREE result at N=6/12. The historical oracle-load
gap uses a weaker-information comparator. B02 reports the matched finite-budget
FREE and oracle curves at N=4/8 early, but its untuned baseline does not complete
that historical held-out-size headroom record. No reusable tuned host baseline
package matching these observations/actions/information/budgets was identified.

DM prediction: `B02_INSIDE_MEI` is most likely; both arms should improve from
zero initialization, with small early separation explainable by conditioning.
Competing mechanisms: (a) shared learnability/generic conditioning dominates;
(b) METRIC coordinates yield a positive AUC signal; (c) conditioning disadvantages
METRIC and FREE yields the signal. The owner's slot is **not taken (unattended)**.
Score an owner prediction reply at intake if one exists; do not infer a reply.

## Exposure, cost and stopping

Machine-generated static exposure (generated with Python before any learner):
`parameters=60; init_l2=0; lr=0.1; grad_clip=5; updates=256;
max_path_l2=128; unit_logit_reference=1; max_path/reference=128`.
The initializer is exactly zero, so division by its scale is undefined; the
nonzero SGD path budget is reported against a unit-logit reference instead.
This is a budget, not predicted displacement. The real first step and cumulative
displacements are required learner measurements; a numerically motionless learner
would be an observed B diagnostic, not an excuse to erase a completed result.

Main counts per arm/seed: 256 updates, 24,576 training allocation transitions,
147,456 training agent steps; 13,056 evaluation episodes, 26,112 evaluation
allocation decisions and 156,672 evaluation agent steps. Complete main panel:
1,536 updates, 147,456 training transitions and 156,672 evaluation decisions.

One named **B02 cost pilot**, seed **1907**, precedes the main panel: 16 updates
per arm, evaluations at 0 and 16, the same batches/dtype/threads/configuration.
Its 32 total updates and all learner observations are preserved separately as B
development data and excluded from the main estimand. It changes no arm choice,
learning rate, seed, MEI or result rule. This is not an efficacy screen.

The runner measures each arm's update time `u_A` (seconds/update), evaluation
time `e_A` (seconds/full requested panel), and separately shared setup/oracle time.
Before the main panel, record the runner's per-arm projection
`P_A=2*3*(256*u_A+17*e_A)` seconds, using a factor-two timing allowance.
The cap is **300 seconds per arm over all three main seeds**, plus **60 seconds
for the pilot** and **60 seconds total shared setup**: at most **720 seconds**
of new result work for this object. No main arm with projected P_A>300 is
launched; that resource/budget finding returns to the DM for a recorded object-tier
adjustment, with no scientific polarity. This is one small comparison, no sweep.

Use ordinary elapsed-time checks between updates/evaluations to stop an arm at
100 seconds per main seed (300 across three seeds), and each pilot arm at 30
seconds. These implement only the stated machine-time cap. A technical failure
or learner-instrumentation failure ends the invocation; no retry/resume loop.
Missing wall/RSS telemetry leaves a valid non-resource result marked
`resources_unmeasured`; missing required learner outputs triggers quarantine.

## Host/device, engineering scope and CM objective

Prospectively **portable across configured Windows/Linux CPU nodes** with float64
PyTorch CPU, NumPy PCG64 and one CPU thread. Use remote-first `wsl_4070`; no GPU,
dtype or RNG change. Cross-host bit identity is not claimed. Before every pilot,
main seed or fresh attempt, node-local `admit-memory` must pass immediately before
the runner in one detached `agent-task` command joined by `&&`. Execute only
committed and pushed source in an exact-SHA remote worktree. Local fallback is
permitted only under the configured no-accepted-remote-process rule and a fresh
local admission. The source launch SHA, exact argv, node, cwd, output root and
accepted handle are recorded in the result/resume evidence.

Engineering scope section 4 needs **none**: use the existing detached agent-task
facility and preflight, not new distributed/resume/guard/registry/telemetry
machinery. Required return, gradient and parameter traces are scientific
measurements. Wall time and peak RSS are enough resource telemetry. Reuse the
existing numerical primitives without calling the old `run.py`, certificate,
artifact tree or stationarity selection orchestration.

CM owns new attempt code under
`experiments/candidates/metric_ground_transport_allocation/mgtap_b02_curves/`,
one `scripts/run_mgtap_b02_curves.py`, mirrored tests under
`tests/experiments/candidates/metric_ground_transport_allocation/mgtap_b02_curves/`,
and result/technical evidence for B02 in this direction directory. The DM owns
this card, owner items and intake. Preserve others' work. CM uses its own worktree;
Root integrates. Keep <=2,000 new research lines, <=600 runner lines and <30%
orchestration; return any unrequested machinery. One end-to-end toy smoke reaching
summary publication and rule tests suffice; independent focused verification
checks parity, real learner counts, exposure, cost law and publication.

Technical success cannot establish mechanism value. CM returns the card-matched
result document with raw counts/curves and measured per-arm cost; DM applies this
rule and interprets it. Send accepted long-running handles directly to
`/root/tracker_lxh_experiments` with this DM's canonical name; Root's temporary
outbound recovery arrangement remains in force. Tracker does not launch or repair.

## Decisions this card produces

Object-tier options: (a) this two-arm curve object and short cost pilot;
(b) first run a multi-rate/binding sweep; (c) repeat the historical support gate.
Recommendation: **(a)**, the smallest direct learner discriminator of the adopted
question. (b) spends unpriced work; (c) reopens a stopped question and does not
answer finite-budget learning.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Provenance: `OWNER_DELEGATED`; reversible. No direction/Portfolio decision or new
Pro launch gate. Read owner reviews at every clean boundary. Record the measured
projection before main execution and take the completed result in under its B ceiling.
