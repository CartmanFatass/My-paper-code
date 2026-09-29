# Lawful Local Spatial History

## 2026-09-29 - Question Selection and B01 Prospective Design

Native DM `/root/dm_local_history`, assigned by Root `/root` on shared main.
Initial registration is published at `fed55fd0ef329f8fac55dfdf3faeac46158fc1d4`.
Question: can retained lawful local spatial history improve complete decentralized
UAV service/control under partial observations, and what can experience add beyond
a competent ordinary controller with the same history? This is a new direction,
not a restart of paused PPC/FSD or an old roster-memory operation. No inherited
operation, parameter asset, training exposure, or claim of novelty.

### Sources and Current Explanation

Current published background read at `fed55fd0e`: RESEARCH topics 2, 4 and 8,
and the completed [archive re-entry review](../../archive/2026-09-29/RESEARCH-archive-reentry-review.md).
Topic 2 separates lawful information recovery from native usefulness; its S7 BS
positive is an analogy, not a matched S1 baseline. Topic 4 retains adverse local
encoding/aggregation packages and does not equate added representation with finite
learning value. Topic 8 requires the decision and joint interference consequences
to connect information to service. These readings select a direct complete S1
controller comparison, with an explicit ordinary motion rule and measured native
tradeoffs. Prior FOLR/cache adverse evidence and original recurrent policies remain
constraints; neither establishes that the current actor forgets static users.

Source: `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py:make_real`,
`envs/pettingzoo/uav_env.py` and `envs/pettingzoo/env_adapter.py` at the above revision.
N=5, 50 static uniform users, H=256, map 1000m square, altitude 50-150m,
componentwise velocity action in [-1,1] times 30m/s, dt=1, free-space channel,
no shadowing/FDMA. Each actor sees own XYZ and up to 20 anonymous user rows with
relative XY and normalized SINR, plus up to 10 anonymous visible peer rows and
time. Users are thresholded at SINR >=3dB then sorted/truncated. World XY can be
approximately reconstructed from lawful float32 geometry; this is not exact entity
identity. There is no added sensor-noise model. Actor code must never receive
info, global state, private indices or environment handles. Native S1 reward in
this source is .7*(connected/50)+.3*mean clipped connected SINR quality; there is
no separate altitude/energy penalty in this source.

B19451 is a demonstrated conditional learned reference in the message-content
direction; it is not a causal control for a newly built ordinary controller.
The accepted B05 content/residual study is owned by another DM and is untouched.

### Proposed Smallest Complete Study

Intended contribution of B01: empirical understanding and a possible ordinary
task capability, not a learning-method claim. Compare one explicit decentralized
radio-aware receding-horizon motion rule using current user geometry (C) versus
the same rule retaining lawful observed geometry (H). The experience question
remains open at this boundary; a motivated direct learning comparison need not
wait for an ordinary positive. This complete zero-fit comparison is chosen because
no compatible current S1 local-motion controller exists and both its native value
and the history interaction are unresolved. It is not a sequence of preliminary
screens or a prerequisite for later learning.

Each UAV receives only its own observation row. Its cache stores up to 64 XY points
and last-seen times, resets each episode, matches nearest points within .01m, and
uses least-recently-seen eviction with insertion-order tie break. Fresh matches
replace coordinates. Capacity exceeds the true 50-user count but does not rely on
true IDs; association errors and evictions are reported, not silently corrected.
C reconstructs only current rows. H uses the union represented by its cache.
No cached peer track, cross-agent cache sharing or extra messages.

At t=0,4,...,252 each UAV scores the 27 componentwise velocity vectors in
{-1,0,1}^3 over four predicted primitive steps, then executes the chosen command
for four steps. It ingests observations every step, even during a commitment.
Predicted own position follows the native clipping rule. Currently visible peers
are held fixed. Known static-user geometry and the native free-space power law,
3dB threshold and per-UAV capacity 10 give a local predicted native J. Unknown
users are not invented. Unknown peer interference is an explicit approximation:
for current visible users infer its nonnegative residual from measured SINR
after subtracting visible-peer power and noise; for remembered absent users use
the expected contribution of the missing peers on a fixed 8x8 uniform XY grid
at 100m altitude. The latter is a public geometric prior, not current truth or a
calibrated posterior. No measured SINR is cached; the intervention is retained XY.
All arms share this same model, candidate set and cadence. Equal predicted scores
prefer smaller command norm then lexicographic action. With no known users the
rule holds position; this fallback is explicit and its frequency is reported.
Every candidate uses the full own/visible-peer SINR matrix. At threshold >0dB at
most one transmitter can qualify per user, so selecting the ten best eligible
users per transmitter implements greedy capacity assignment for this local model.
The model ignores future peer motion and never calls the live simulator to score
a hypothetical action. Its error can change the result; no optimal controller or
optimal information-value interpretation is intended.

Evaluation: 32 fresh common reset seeds 29091000-29091031, C and H each run the
complete H256 episode, fixed endpoint only. No tuning or checkpoint selection on
this panel. Primary comparison is paired full-episode J (mean native team reward)
and mean served users; retain total return, SINR-quality term, minimum/per-step
service, movement, boundary occupancy, all per-world signs and adverse tails.
Record cache size, absent remembered points, age, matched/inserted/evicted counts,
requested/executed actions, action disagreement at equal-input diagnostic calls,
model scores and actual decision counts. Evaluator-only truth may audit position
association error after action decisions, but must never feed the controller.
Per-world paired means and descriptive t95 intervals describe this fixed program
on sampled worlds; they are not training replicates, confirmation, safety or
component-mechanism identification.

Constructive prediction: cached points survive visibility loss and can alter
motion, with positive complete J/service on average. H>C supports this bounded
ordinary capability; it does not establish GRU forgetting or a learning increment.
Active cache and changed actions without native gain weakens practical value of
this specific geometry/model package. No action change limits the tested decision
use; it does not reject history generally. Gains with service/J conflicts or worse
tails remain conditional tradeoffs. Technical failure is missing evidence, not a
negative. No automatic repair, added worlds or new fit follows any branch.

### Prospective Cost and L0

0 fits and 0 optimizer updates. Two programs x32 worlds x256 = 16,384 native team
steps, 64 complete episodes, 20,480 UAV decision calls, 552,960 candidate trajectories
and 2,211,840 predicted primitive model ticks. Worst-case model link evaluations
with 5 modeled transmitters and 64 cached points are 707,788,800; actual visible
peers/cache lengths reduce this. Cache receives 81,920 scored-step actor observations
plus resets/terminal handling declared in actual counters. No branching live
simulator calls. Initial wall estimate is 5-30 minutes on one wsl_4070 CPU thread,
with contention and controller cost uncertain; within-batch measurement may revise
the wall estimate but not scientific exposure. Engineering estimate 1-2 hours;
support/review/publication actual time will be reported separately or unmeasured.

L0 deliverable: direction-owned `b01/controller.py` with observation-only parsing,
cache and vectorized local model; `b01/run.py` with admission before scientific
effects, complete episodes, compact summary/config and bulk trace separation;
focused tests mirroring that directory. Reuse the unchanged host constructor.
No core or another direction edits. Tests cover float32 reconstruction/dedup,
episode reset/eviction, anonymity/per-agent isolation, hold/clipping semantics,
model SINR/capacity versus independent scalar calculations, no-peers/no-users,
and runner count/primary-output consistency using fixture admission. Run real
source correctness checks only as bounded tests, not scored pilot episodes.
One writer per path, explicit-path commits under `.git/hmasd-main-writer.lock`.
Independent scientific qualification of this new model/comparator precedes
substantial implementation; high-risk executable engineering review precedes
result launch. No result execution until inputs are published and actual-node
admission accepts the currently active direction and lead.

### Independent Selection Review: Adopted Corrections Before Implementation

Reviewer `/root/dm_local_history/b01_scientific_review`, registered
`hmasd-research-critic`, separate context (`fork_turns=none`), read-only; original
host sources were reconstructed before the proposal. Two source/design findings
change the draft above, with no result exposure:

1. A cached point absent from the current rows is censored evidence. If fewer than
   20 users are current, ego SINR is below 3dB; if 20 are current, it cannot outrank
   the last current row. The unconditional prior could contradict this information
   and invent attractive currently eligible targets. H must condition its unknown
   interference residual on this bound before predicting motion. Current-row
   measured-SINR calibration is source-consistent. DM adopts this correction.
2. Holding when no users are known can make an avoidably blind ordinary controller.
   Both arms instead use the same fixed deterministic sweep whenever every candidate
   predicts zero service, including empty geometry. No extra arm, demand model,
   pilot or learner is added. C retains its own navigation/issued-command state,
   but no prior user geometry. DM adopts this correction.

Exact shared sweep: ten waypoints (100,100),(900,100),(900,300),(100,300),
(100,500),(900,500),(900,700),(100,700),(100,900),(900,900), cycling in this order,
all at altitude 50m. Initialize the navigation index to the nearest XY waypoint
from the actor's own first observation, with listed-order ties. On a fallback
decision, advance one waypoint if within 60m horizontally, then select the common
27-action command minimizing squared distance of its clipped four-step endpoint
to that waypoint. Score ties retain the declared norm/lexicographic order. The
navigation index changes only on an executed fallback, not in shadow diagnostics.
Different agents get no privileged IDs or allocations. Search is a bounded ordinary
fallback, not an optimal coverage rule; its executions and first acquisition are
reported separately from model-selected service actions.

The same-input H-versus-shadow-C diagnostic reuses H's candidate power/SINR tensor
restricted to current rows, so adds no links or live simulator calls. Its objective
reductions are still work: at most 10,240 diagnostic calls and 1,105,920 additional
candidate-step score reductions, plus up to 10,240 cheap sweep selections. These
never change H's action or navigation/cache state. The original 707,788,800 link
upper bound remains unchanged. All such counters will report actual work.

#### Complete Substantive Scientific Answer

Recommend retain the question and use the revised C/H comparison for the first
complete observation. The original unconditional interference prior and blind-hold
fallback were consequential weaknesses; the DM has adopted corrections to both.
No extra arm, pilot, fit or positive-result prerequisite is needed.

This review received no parent conversation history. The assignment identified C/H,
so it was not blinded. I reconstructed the host and recorded a provisional reading
before opening the proposal and previous archive recommendation.

I checked make_real, observation filtering, radio interference, actions, reward and
adapter semantics at fed55fd0e; those files match the proposed source. Users are
static, but visibility depends on all UAVs' interference. Retained coordinates
therefore have a plausible use without establishing GRU forgetting. The adapter
scalar is team reward divided by five; evaluation must use the declared team reward.

The inherited adverse evidence is real. I recomputed the original summary arrays:
LOE DENSE-ORIGINAL is -.256172 J; aggregation P-O/E-O are -.349276/-.326121,
each adverse in all 32 evaluation worlds. All five fits report complete exposure
and optimizer movement. FOLR's four native summaries reproduce A-G
-5.830625/-.109922 across its two blocks. These constrain those trained packages,
not this controller or history generally. The earlier S1 studies also differ in
N, horizon and reward, so their scores are not matched benchmarks for B01.

The coherent revised comparison should retain these specifications:

- Condition absent-point interference on current censoring. For a correctly
  associated cached point, fewer than 20 current rows implies current ego SINR
  below 3dB; 20 rows implies it cannot outrank the weakest current row. In linear
  units use `I_hidden=max(I_grid,P_ego/gamma_upper-P_visible_peers-noise,0)`.
  A fixed 1e-4dB conservative margin below the cutoff is a reasonable numerical
  model convention, not sensor noise or a calibrated confidence bound. With 20
  rows, an absent point may still be service-eligible: truncation differs from
  falling below 3dB. When all four peers are visible, do not invent hidden
  interference to resolve a substantial inconsistency; retain zero hidden-peer
  interference and expose association/numerical discrepancies.
- Use the adopted shared sweep when every candidate predicts zero service. The
  ten-waypoint rule is adequate for this bounded comparison. Otherwise initially
  blind C can remain blind when peers settle, allowing H to beat an avoidable
  fallback weakness. C may retain navigation without retaining user geometry.
- Freeze the approximate objective explicitly. Score known users with the native
  denominator 50, capacity and quality formula across all four predicted steps.
  Static peers, omitted unknown users and grid approximation remain restrictions.
  Expected interference is not expected native reward. These restrictions are
  acceptable for this package observation but do not establish optimal ordinary
  control.

The strongest ordinary alternative is therefore the same lawful receding-horizon
controller with censoring-aware inference and basic search. A richer demand model
or peer tracker is not required before this observation. The constructive prediction
is that persistent coordinates permit useful motion after visibility loss. The
competing prediction is that current geometry plus search already supplies
comparable service, or that partial-objective error and simultaneous peer motion
outweigh cache benefit.

The fixed 32 paired worlds, 64 complete H256 episodes can distinguish those package
outcomes. H improving complete J and service supports ordinary history capability.
Active history-induced motion with losses weakens this recipe's practical value.
Little executed action change shows limited decision exposure, not a general
history negative. Conflicting service/J and adverse tails remain tradeoffs.
Shadow-C disagreement measures choice exposure, including whether clipping makes
commands equivalent; it does not identify a causal mediator.

This result cannot establish what learning adds. Experience could improve prediction
of hidden interference or peer responses, but a later learned comparison must give
the competent ordinary comparator the same information and account for training
and deployment cost. Neither B01 positivity nor complete failure diagnosis is
required before a separately motivated learning study.

Cost remains 0 fits, 16,384 native team steps, 20,480 main decisions and 2,211,840
candidate-step scores. Count the additional 1,105,920 shadow reductions separately.
Also count grid-prior work: recomputing 64 quadrature points for every possible
cached point at each H decision adds up to 41,943,040 power evaluations. The draft
link bound is conservative; actual timings remain unknown. The 5-30 minute
execution and 1-2 hour engineering figures are estimates, and no direct-learning
alternative has yet been fully priced.

I did not verify new implementation, checkpoint bytes, every historical trajectory
or old failure archives. No B01 result exists; I performed no edits or experiments.
MATERIAL_DISSENT: no. The source-grounded objections have been adopted; no unresolved
direction disagreement remains.

#### DM Disposition and Final B01 Binding

Adopt the review in full for this first complete comparison. `b01_censor_search_a01`
will keep the declared C/H programs, 32 seeds, H256, no fit or optimizer. In addition
to the prior corrections, when all four peers are visible the predictor fixes hidden
interference to zero and reports current/censor inconsistencies beyond 1e-4dB;
it never fabricates another hidden peer. The 1e-4dB censor margin is fixed. Count
quadrature separately, and measure both shadow command disagreement and clipped
four-step trajectory disagreement. Evaluator truth uses native copied `state_info`
coordinates after action decisions for association and motion audits only; it is
never passed to the controller. Terminal observations are retained as endpoint
geometry but are not ingested into an actor with no remaining decision.

This ordinary result can inform useful control and representation without learning
attribution. The cheap complete comparison is preferred now to engineering a new
learner and buying hundreds of thousands of interactions before a matched ordinary
motion interface exists. That is an investment judgment, not a requirement for an
ordinary positive. At the read-result boundary compare constructive learning,
ordinary-model revision, replication and stopping by what they would change; return
the evidence and proposed next investment to Root within the assigned question.
No claim note is required because this is exploratory fixed-program evaluation.

Remote canonical controls were synchronized by Root to fed55fd0e under writer and
admission locks, preserving five dirty run statuses and sparse selection. Ownership
check passed on wsl_4070. This is not result admission; exact inputs, fresh actual-node
memory and the launcher still apply. No scientific effect or operation existed at
this design boundary.

### Implementation Acceptance and Frozen Input Publication

DM accepts the bounded Implementer's controller and mirrored tests after reading
the diff and its scalar, capacity, censoring and cache checks. DM authored the
admitted entry, collector, compact reader and runner tests. No core or other
direction source changed. Final code uses broadcast reuse for visible-peer powers:
the precise worst-case power-call count is 92,897,280 moving links +4,300,800
setup links +41,943,040 grid links =139,141,120, below the earlier conservative
707,788,800 fully recomputed bound. Main and shadow objective reductions remain
2,211,840 and1,105,920. Worst-case H association computes 52,428,800 point distances.
Actual counters and process time, not these upper bounds, will be read.

Independent engineering Reviewer `/root/dm_local_history/b01_engineering_review`
checked actor leakage, independent caches, mapping/eviction, 19/20-row censoring,
all-four-peer semantics, clipping/holds/search/shadow nonmutation, independent
scalar SINR/capacity, link accounting, native team reward, exact seeds/counts,
incomplete status, admission ordering, artifact identity and thread controls.
One P2 output-contract issue was repaired before publication: retain the terminal
observation in raw without another actor ingest. No material finding remains.
All18 focused tests passed in .70s; the5 affected runner tests passed again in
.47s after repair. Fourteen warnings are third-party matplotlib/pyparsing
deprecations. Tests used fixtures and one real reset-row reconstruction, no scored
native episode or result pilot. Mid-episode failure persistence was inspected
statically, not tested by injected failure; no real admission handshake occurred
during review.

Final reviewed SHA256 values:

- controller.py: b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2
- study.py: 5fb3a1538a29bc5dd613a49fdd469d351876e8b070794171956a290651cdb8ec
- run.py: 0d1ff97debe0dbfbd6b9908186afe5e22915ae9c5f5283804710eb8408e7e2f6

At the read-only prelaunch resource look, wsl_4070 had20 logical CPUs, load3.83,
one scientific process using about4 CPU cores, and 11,953MiB physical memory
available on the earlier memory reading. These are planning observations, not the
fresh admission receipt. B01 uses one NumPy/BLAS thread and no GPU. Other accepted
workers, claims, dirty run statuses and sparse paths are preserved.

### Prospective Host Fallback Before Any Launch

Exact inputs were first published at `ae184f74175b59f6036a06b510be2b70a7205a69`.
The wsl_4070 source fetch then stalled for over two minutes in git-remote-https;
a separate bounded curl probe returned `curl: (28) SSL connection timeout` after
5s. At 2026-09-29 14:32 UTC I terminated only this fetch's known git/remote-HTTP
processes (1001103-1001105), and its command returned143. No result launcher,
admission claim, environment or scientific step had started. The shared writer
lock was released; no accepted worker, control or network configuration changed.

Choose the authorized local_linux fallback prospectively: 16 logical CPUs,
10,070MiB MemAvailable and load4.82 in the planning observation. The same reviewed
float64 NumPy controller and unchanged native source run with the configured
`/home/fires/.venvs/hmasd-linux-cpu/bin/python`, NumPy1.26.3, SciPy1.15.2, one BLAS
thread, no GPU or fitting. The focused checks already ran on this host. Keep the
full C/H panel and all counters; this is a new launch location before acceptance,
not migration/retry of an accepted experiment. Execution time is still estimated
5-30min and will be measured. Local launcher fresh memory/publication/pause/lead
admission remains required. Root was informed natively of the concrete dependency
and fallback; this introduces no approval or scientific review round.
