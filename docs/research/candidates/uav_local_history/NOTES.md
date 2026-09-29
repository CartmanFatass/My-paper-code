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

## 2026-09-29 - B01 Complete Reading

### Accepted Operation, Collection and Verification

Published input `9327837445025d756d823eeb6e39f50ac90293ad` was admitted on
`local_linux` at 14:36:14.825015 UTC. Original output is
`runs/uav_local_history/b01_censor_search_a01/`; the launch manifest binds claim
`4f31acfa31ba91c644027d45a2682ac72281df400b29ac0d8127c50f1c2ff1f1`,
supervisor3228232, runner3228234 and the exact interpreter/argv/source snapshot.
Fresh admission saw10,787,897,344 bytes available versus the4,294,967,296 floor;
published control revision was570fd45646ea62f4e28d86c74770e835b2e0a963.
The exit witness is valid and consistent: exit0 at14:36:45.215520 UTC, both native
processes absent. One constructor,64 explicit resets,64 complete episodes,
16,384 native team steps,0 fits and0 optimizer updates. No partial/retry/replacement
or added scientific episode occurred.

The deterministic observer used the same operation, state under
`temp/directions/uav_local_history/b01-wait`, generation1 and a1500s window.
READY event `b9a2e86cb7b64273fac2b4ec` was read natively while this DM remained
active. The automatic queue attempt returned the known unloaded-native-child
app-server rejection (`-32600`); no scientific operation was resent. Wake
`631f4a99-5c4d-4440-910e-9abc1debdf53` and the READY event were consumed by
same-handle rearm; generation2 was stopped with no worker restart. Final stopped,
consumed observer state is retained as `observer-terminal.json` in the run.

The64 compressed raw artifacts total2,150,358 bytes, all SHA256 identities match
the original summary. They remain the single necessary bulk copy in this durable
main checkout's run directory on local_linux; main is not being retired. The
summary records every file's canonical absolute path, byte count and hash.
Native manifests/config/summary/reading are compact Git evidence; logs and raw
remain outside Git. The post-result `b01/read_b01.py` is an offline reader, not an
additional admitted experiment: no environment, actor, training or evaluator
invocation. It verifies all32 distinct common initial user/UAV worlds, all4-step
command holds, exact native componentwise clipping/displacements and terminal
observation geometry. Independently reconstructing free-space power, cochannel
SINR,3dB eligibility, capacity10 and reward from stored true user/post-UAV geometry
reproduces all16,384 service counts exactly and native J to1.666e-16 maximum error
(quality5.274e-16). Maximum terminal coordinate roundoff is2.950e-5m. The evaluator
audit never enters an actor. Original scientific files/summary are unchanged.

### Native Effects and Decision Exposure

For the fixed32 paired worlds, mean J is C .335495108, H .339956525:
H-C +.004461417, descriptive paired t95[-.010567810,+.019490644]. Mean served
users are19.916015625 versus20.292968750: +.376953125
[-.777661820,+1.531568070]. J and service signs are both7positive,10negative,
15exactly equal. The15 equal pairs have byte-identical commands and physical
trajectories, not merely matching aggregates. The complete32-vector is preserved
in `summary.json`; `reading.json` adds paired first-divergence and exposure.
The observed mean benefit is retained, but its sign is not resolved over sampled
worlds. Neither interval crossing zero nor15 ties establishes equivalence.

Positive cases include29091005 (+.140601460 J,+10.44140625 users/step),29091026
(+.074523512,+5.38671875),29091011 (+.069269699,+6.44921875), and29091028
(+.061990331,+5.13281250). The strongest adverse case29091007 loses.081102573 J
and6.90625 users/step;29091003 loses.074926435/4.80468750 and29091004
loses.071837984/5.47656250. All other losses remain in the original vector. In
29091005 one equal-input shadow disagreement accompanies a large eventual gain;
in29091007 there are63 disagreements and a large loss. These are closed-loop
package outcomes, not proof of a specific beneficial/harmful intermediate action.

H has legally absent remembered points in all32 worlds and5,685/10,240 local
decisions (55.52%). It changes the same-input current-only command and executed
four-step trajectory on543/10,240 decisions (5.30%); this diagnostic does not
identify a causal mediator or count the total C/H trajectory consequences.
Mean cache size5.30085 and absent size1.16711, maximum cache19, maximum absent
age255. Across both arms, maximum reconstructed-point error4.2253e-5m; zero
unmatched/duplicate/ambiguous associations. No cache eviction occurred. Thus
capacity/association failure is not an observed explanation for this panel.

There were no20-user observations, so native user loss here is threshold
censoring, not top20 truncation. Current visible-peer counts are overwhelmingly
zero: C35,290/40,960 UAV-steps, H35,968/40,960; none see3or4 peers. This limits
what the ordinary predictor can know about joint interference and peer response,
but does not empirically identify model error as the cause of a loss. Calibration
and censor discrepancy counters are0; the censor bound overrides the grid prior
on171 H point-decision cases. Current SINR agreement only checks consistency at
the observed state, not accuracy of future counterfactual actions.

### Components, Costs and Scope

Coverage reward increases .005277344 while quality reward decreases .000815927;
mean normalized SINR quality is .188902964 versus .186183208. Mean episode
minimum service is10.84375 versus10.875, while mean per-episode service-p10 is
18.875 versus18.75. Neither arm has any zero-service step in this panel; this
does not establish safety or coverage outside it. H mean path/UAV rises from
2587.85748m to3085.77974m (+497.92226m, descriptive t95[-108.66629,1104.51081]);
11worlds travel more,6less,15identical. Native S1 has no energy/return model here,
so travel is a measured cost, not a measured battery-risk consequence.
Boundary UAV-steps are4835 versus4765, and lower-altitude steps40764 versus39636.
Executed fallback decisions decrease510to191, while H's same-input shadow has549;
these are different closed-loop inputs from actual C, not a causal subtraction.
Two C and one H UAV-episodes never observe a user.

Actual main decisions20,480, trajectories552,960, model ticks/objective
reductions2,211,840; shadow decisions10,240 and reductions1,105,920. C/H link
evaluations4,536,611/6,661,387 (total11,197,998), including767,040 H grid links.
There are81,920 actor ingests,867 inserted H points and168,451 matches,0evictions.
One-thread scientific wall30.341465s, worker CPU29.774803s (.008271h), peakRSS
127,568KiB. Per-episode wall sums C12.673379s and H16.516042s; H includes the
diagnostic shadow overhead. Reading was below one wall second in the direct
invocation; support/engineering/review time was not fully metered. The conservative
5-30min scientific estimate was high. These measured costs supersede it for this
fixed package, not for a new learned policy or different host.

The constructive average-benefit prediction is not established on this panel.
The result does establish lawful retention, nontrivial decision exposure and
specific complete positive/adverse ordinary-control cases. It weakens treating
geometry history plus this short-horizon model as a default service improvement;
it does not establish GRU forgetting, sufficient state, optimal information value,
learnability or a learned increment. Historical cache/encoder failures and useful
B19451 assets remain intact, not overturned by this zero-fit package.

### Next Investment Under Independent Review

Current published background has been refreshed through5ba777812, including B05's
conditional continuation benefits and unresolved forecast increment. That result
is not a matched history control. Replicating C/H could cheaply narrow the mean
for this fixed ordinary pair, but would not answer what experience adds. A longer
ordinary horizon or richer hidden-peer model could target joint consequences, but
their causal benefit is not diagnosed by the retained trajectories; they are
substantive alternatives, not automatic repairs justified by cache activity.

A direct learned decision package can instead ask whether finite experience uses
the exact same current observation and bounded geometry/age/current-mask cache to
improve full J/service over H. One candidate is a full categorical27-command
policy with4-step commitments, not a forced small residual; no added recurrent
SINR/peer history, messages or privileged actor coordinates. A centralized training
critic is a declared training addition, not actor information. Three independent
512xH256 fits would cost393,216 training steps; three initialized/final pairs plus
C/H on32 new common worlds add65,536 evaluation steps, total458,752. This would
test a finite learned package, not isolate the causal contribution of retention to
learning or compare against the existing GRU's memory capacity.

B05's843,776 steps cost.484397 CPUh on one local thread, giving a rough linear
analogy of.263 CPUh here, not a guarantee for a larger set-actor. A provisional
.5-2 CPUh and4-8 engineering-hour range explicitly leaves implementation overhead
unknown. This is not yet an accepted or frozen B02 design. Constructive prediction:
a learned full policy can value the longer closed-loop service consequences that
the4-step stationary-peer approximation omits, improving over both initialization
and H with the same lawful inputs. Failure would constrain that finite training
package, not prove history useless. The independent original ResearchCritic is
now reading the entire B01 outcome and evaluating this continuation against cheap
replication, targeted ordinary revision and justified stopping. No new episode,
fit, prediction gate or automatic follow-up has been purchased.

### Result Checks and Boundary Cleanup

The offline reader adds explicit one-transmitter capacity and co-located joint
interference checks. All20 direction tests pass in.82s;14 warnings are unchanged
third-party pyparsing deprecations. The admission-bound controller/collector/entry
hashes remain those reviewed before execution. No core, existing learner, B05
input or unrelated direction file was edited.

After verified collection and stopped observer/runner identities, snapshot GC
initially refused read access to protected own PID383's `/proc/.../cwd`. Its
supported read-only `--sudo-process-scan` then passed; preview and apply verified
the original claim, terminal witness, externally retained output and main source
reachability. The exact source snapshot
`.git/hmasd-launch-sources/143bdbfa00a04edd99316b47b5d29027` was removed and its Git
registration disappeared:1,639,256,064 allocated bytes reclaimed. Exact disposable
targets `temp/directions/uav_local_history/` (20,480 bytes), direction B01
`__pycache__/` (49,152) and mirrored-test B01 `__pycache__/` (45,056) were also
removed after retaining final observer facts. All four targets are absent;
net allocated release is1,639,370,752 bytes. No backup, relocation or duplicate
bulk copy was created. There is no remaining cleanup blocker for these targets.

The ordinary controller, collector, runner, offline reader and focused tests remain
useful small assets for a matched complete learning comparison/reproduction;
they are not an active operation or authorization to repeat B01. There are no
external executable consumers of the B01 package. Unique raw/logs/native records
remain under the canonical run path, while the historical source is reachable by
its published commit. Other writers' source snapshots, files and processes were
untouched.

### Independent Result Review and DM Disposition

The original separate-context ResearchCritic
`/root/dm_local_history/b01_scientific_review` read the original complete outputs,
raw/source and this prospective contract. Its complete substantive answer follows:

> B01 is a valid, mixed result with active history use. Retain C and H as ordinary
> references; do not adopt H as superior or replicate it separately. I recommend
> one bounded, full-control learning comparison using the same lawful spatial history.
>
> I checked all 64 raw-file hashes, all 32 paired initial worlds, every
> command/hold/clipped transition, and independently reconstructed service and reward
> using scalar greedy assignment. Every service count agrees; maximum reward
> discrepancy was 2.23e-16. Execution source/configuration and the pre-acceptance host
> fallback agree with the records. No new environment interaction occurred.
>
> Complete endpoints C/H/H-C are: mean native J .335495/.339957/+.004461;
> users served/step 19.9160/20.2930/+.3770; SINR quality
> .188903/.186183/-.002720; mean path/UAV metres 2587.86/3085.78/+497.92.
> The J interval is [-.010568,.019491]; service is [-.777662,1.531568]. Both
> comparisons have 7 positive, 10 negative and 15 identical worlds. This leaves
> average benefit unresolved, not equivalent. World29091005 gains .140601 J /
> 10.4414 users; world29091007 loses .081103 J /6.9063 users. H also worsens the
> lowest observed world-average service, from8.8242 to8.3203. Movement is an
> additional consequence, not an energy cost measured by this host.
>
> Several findings change the explanation. Opportunity and representation: all32 H
> worlds retain absent points. Association audits show no unmatched, duplicate or
> ambiguous points; maximum coordinate error is about4.23e-5m. Capacity never binds:
> maximum cache size is19. Crucially, no current observation fills20 user slots.
> This batch exercises SINR-threshold visibility loss, not observed top20 overflow.
> Decision use: absent points occur at5,685/10,240 H decisions, but change executed
> choices against shadow C at543 decisions. Of those,344 have current users and199
> have none. History use is real but selective; the15 unchanged trajectories are not
> cases without stored history. Ordinary capability: positive complete trajectories
> survive alongside substantial losses. This supports a capability worth retaining,
> but does not establish reliable replacement of C. The small positive mean is
> sensitive to world composition. Learning: nothing here measures learnability, a
> learning increment, GRU forgetting or failure of recurrent policies. The previously
> checked encoder and FOLR negatives remain relevant warnings about finite training
> packages, not vetoes on this new comparison.
>
> The strongest simpler explanation is ordinary model limitation: almost all
> observations expose zero or one peer, while all peers interfere; the controller
> predicts stationary peers and evaluates only known users. Its partial quality
> denominator and four-step decisions can misrank complete consequences. These are
> plausible explanations, not identified causes.
>
> The raw trajectories also resist a simple immediate-score story. At the first
> divergence in29091004, H improves the first four-step return by.094137 but loses
> .071838 in complete mean J. In29091026, the first four-step change is slightly
> negative, yet complete J improves.074524. These observations motivate learning
> from complete consequences without proving that horizon length caused the failures.
>
> For the next investment: separate replication is cheap, but mainly refines the
> fixed C/H population estimate. Neither current adoption nor the learning question
> requires it first. Evaluating both controls on the next fresh panel already supplies
> useful recurrence evidence. Targeted ordinary revision is potentially useful, but
> no specific correction is established. Cache coordinates are accurate and static;
> an age cutoff would be a new heuristic, not a diagnosed repair. Another interference
> or objective approximation should not become an automatic prerequisite. Direct
> learning answers the remaining substantive question: can experience produce better
> complete decentralized control than these ordinary programs under the same
> deployment information and action rights? Stopping is defensible on opportunity
> cost, but B01 does not supply an empirical reason to close that learning question.
> Given the measured inexpensive host, I prefer one bounded comparison.
>
> The proposed three independent full categorical-policy fits, each512 H256 episodes,
> is a reasonable complete next observation. Keep the27 commands and four-step
> cadence; retain current observations plus the declared coordinate/age/current-mask
> cache. Specify controller navigation state and any privileged critic inputs
> explicitly; do not silently add actor memory of past SINR or peer motion.
>
> Evaluate each initialization and final policy, plus fixed C and H, on the same32
> fresh worlds. This costs393,216 training +65,536 evaluation =458,752 native steps,
> three fits, with no checkpoint selection. H is the same-history reference; C
> prevents a claim of useful ordinary improvement based only on beating H. A
> learned-no-history arm is unnecessary for this package question, provided a
> positive result is not attributed specifically to retention.
>
> The constructive prediction is improved complete J/service through learned action
> choices despite the ordinary model's approximations. Improvement over initialization
> alone establishes own learning; improvement over H but not C does not establish
> useful advantage over the available ordinary alternatives. Losses or unstable
> training outcomes would constrain this finite recipe without automatically selecting
> more exposure or another encoder. Three training instances permit a meaningful
> recurrence check, not guaranteed precision.
>
> B01 cost30.34 seconds runner wall, about29.77 seconds worker CPU, and zero fits;
> engineering/support remain incompletely metered. B05's verified.484397 CPUh /
> 843,776 steps makes.263 CPUh a rate analogy only: it trained a smaller continuation
> package. The proposed.5-2 CPUh and4-8 engineering hours remain uncertain planning
> estimates. That implementation cost, rather than another30-second evaluation, is
> the material investment.
>
> MATERIAL_DISSENT:no. I support the bounded same-history learning comparison, with
> both ordinary controls and the stated attribution limits; I oppose treating B01 as
> established H superiority or as evidence to close the learning question.

DM adopts this reading and selects the substantive same-history full-control
comparison as the next within-question investment. Do not spend a separate panel
on C/H precision or insert a guessed ordinary-model repair before it. H is retained
as a conditional ordinary asset alongside C, not promoted to a new default.
Keep all prior encoder/FOLR adverse evidence, the present7 positive and10 adverse
worlds, and the possibility that ordinary or initialized control remains better.

The selected B02 envelope is three independent512-episode fits, full27-command
policy, shared4-step cadence, exactly the lawful bounded geometry history, and
fixed C/H plus three initialized/final endpoints on32 fresh common worlds. No
added peer/SINR recurrent history or message contract. Navigation-state availability
and centralized critic inputs will be explicitly bound before implementation is
accepted; optimizer/update counts, exact seeds and exposure, endpoint decoding,
resources and outcome branches will be published before admission. The existing
adequate scientific advice covers this package/comparator choice; ordinary exact
implementation binding does not add a scientific approval gate. A material change
would be separately reviewed. No B02 source freeze, fit, accepted operation or new
data yet exists, and B01 completion does not authorize a repeated B01.

This returns the assigned first substantive read-result boundary to Root, which
owns cross-question allocation. The recommendation is continuation for an explicit
remaining learning question, not because B01 ended or a slot is available. The DM
owns prospective exact design/implementation/admission if this selected investment
continues; no routine per-fit Root acknowledgment is required. The direction stays
exploring with this next investment, not idle with a fabricated outside dependency.

## 2026-09-29 - B02 Same-History Full-Control Prospective Binding

Root received the B01 boundary, accepted the explicit handoff of only this DM's
three disjoint RESEARCH hunks during its concurrent shared-file publication, and
requested continued concrete design/execution within the original question. B01
owned evidence was published at1ff778810. This is continuation of the selected
learning question under the completed independent review, not a new direction,
restarted B01, checkpoint rescue, or per-fit Root approval. B01 is closed; B02 is
the sole active result-bearing study. Current background/decision is the B01
reading above plus the published B05 result; no premise now diagnoses forgetting.

### Fixed Comparison and Information

Train three independently initialized full categorical policies L with masters
291021,291022,291023. Each fit has512 complete N5/S1 H256 episodes; block index
b=0,1,2 uses reset seeds29110000+1000*b+episode (episode0..511). Independent
parameter seed100000*master+11 and action-generator seed100000*master+29.
Evaluation uses32 fresh common worlds29102000..29102031, disjoint from B01 and
training. Evaluate the fixed B01 C/H programs once each, then for each master
evaluate its initialization L0, train all512 episodes, evaluate its sole final L1.
No panel-dependent checkpoint, training exposure, decoding, seed or arm selection.
Ordinary world order alternates C/H and H/C as B01. Deterministic learned argmax
deployment has the same ordered27 commands and4-primitive-step commitments; training
samples categorical commands at that cadence. This is a complete policy, not a
bounded residual around ordinary H or an inherited actor.

Each learned UAV ingests only its own104-feature observation on every primitive
step. It reuses B01's exact lawful .01m/64-point/LRU geometry association (no IDs),
including the same last-seen and current-mask state. Point input has seven fields:
absolute worldXY/1000, relativeXY/1000, age/256, current flag and current normalized
SINR (zero when absent). The SINR is rebuilt from current rows at every ingest,
never retained across absence. Padding has an explicit valid mask. Actor context
is the current104 features plus its own last executed command (3), including the
native time feature. No privileged state, team cache, peer track, past SINR, learned
recurrent state, message or action feedback from another UAV enters the actor.
Terminal observations are retained but not ingested after the last action.

Ordinary C/H remain byte-unchanged B01 control programs: their last-command and
fixed-waypoint navigation index are internal program state; H retains exactly the
same lawful geometry/age/current mask. L has no persistent navigation index or
recurrent navigation memory beyond its stated inputs. This explicitly favors
ordinary control's existing navigation knowledge rather than silently adding actor
history. Same history means the matched added geometry information, not identical
internal representations or algorithmic knowledge. Both C/H are reported; beating
H alone while trailing C is not useful superiority over the available alternatives.

Actor: shared point encoder7->64 tanh->64 tanh, masked mean and max pooling
(empty set gives zeros), concatenated with107 current/last-command features;
MLP235->128 tanh->64 tanh->27 logits. No shared gradient with the critic. Native
central state116 normalized by the existing `critic_features` helper plus five
last-command/zero-remaining rows gives136 critic inputs; reuse the existing
136->128 tanh->128 tanh->1 Critic. True current users/UAVs are CTDE-only training
information, never actor inputs or synthetic future labels. The critic need not
observe actor-cache history for the complete-return baseline to remain lawful;
it is a function approximation, not a sufficient-state claim.

### Training, Endpoints and Outcome Branches

Collect two complete episodes per rollout:128 macro clocks/640 actor decisions.
Gamma1 full Monte Carlo return with no terminal bootstrap; critic predicts returns
divided by256 as a fixed numerical parameterization, while raw native rewards and
all reported objectives remain unchanged. Advantages use these normalized returns
minus collected critic values, standardized across rollout episode/time with
population SD+1e-8 and shared across the five actors. Four full-rollout PPO epochs,
per-agent categorical likelihood ratios clipped[.8,1.2], summed-agent surrogate
averaged over episode/time; entropy coefficient.01 on summed categorical entropy.
Separate Adam actor/critic at3e-4, betas(.9,.999), eps1e-8, zero decay, separate
global gradient clipping.5; critic objective .5*MSE. Use the existing project
`returns_to_go` and `clipped_policy_loss` functions. CPU FP32 Torch, one intra-op,
inter-op and BLAS thread. No early stopping, imitation pretraining or online
evaluation updates. Initial and final actor/critic checkpoints retained.

Primary reading: full native J and mean service, each L1-L0, L1-H and L1-C on the
same world panel, then three independent training-instance means (not96 independent
training replicates). Preserve component quality/coverage, every world and seed,
minimum/low service, zero-service ticks, actual motion/boundaries and all adverse
tails. Three training instances permit a recurrence check with very wide df2
intervals; no guarantee of confirmation precision. Record cache/legal exposure,
action distributions, entropy, held/clipped actions, gradient norms, approximate
KL/clipping, parameter displacement and actual training/update counts. Evaluation
also computes a nonmutating current-only cache-input shadow on the learned
trajectory; report changed logits/argmax and clipped4-step motion only as input
sensitivity, not retention causality or another policy evaluation.

Constructive prediction: experience learns useful complete consequences despite
ordinary local-model approximations, improving L1 over its initialization and both
competent ordinary controls on native J/service. L1>L0 alone is learning in the
tested instances, not useful ordinary advantage. Any H/C advantage or mixed seed
signs remain real alternatives; active updates/input sensitivity without complete
gain constrain this finite recipe. A positive L1 does not attribute improvement to
retention because no learned-no-history arm is present. No GRU-forgetting, optimal
information value or pure coordination-mechanism claim. Preserve valid evidence
on technical failure, mark incomplete and stop the fixed operation; no automatic
retry, fourth fit, encoder/optimizer/horizon repair or more worlds follows closure.

### Dominant Cost and L0

3fits x512 x256 =393,216 training steps. Eight programs/endpoints x32 x256 =65,536
evaluation steps, total458,752;1,536 training plus256 evaluation episodes. There
are768 two-episode rollouts,3,072 actor and3,072 critic optimizer calls (6,144total),
491,520 training agent decisions and1,966,080 replayed actor rows. Learned evaluation
has61,440 actor rows plus61,440 diagnostic shadow rows; ordinary evaluation has
20,480 search decisions/552,960 trajectories/2,211,840 model ticks and1,105,920 H
shadow reductions. Count actual link/cache/forward work and process wall/CPU/RSS.
There are no live counterfactual environment calls. B01.008271CPUh and all support
remain cumulative; B05 cost is an analogy, not this direction's exposure.

Prefer wsl_4070 if its source/control fetch and real-node admission are healthy;
otherwise the local_linux configured CPU interpreter is the prospective fallback
before acceptance. Exactly one worker runs all three fits serially; no GPU,
parallel fits or remote control mutation. Existing workers/claims remain intact.
Planning.5-2CPUh plus4-8 engineering hours remains uncertain (.263CPUh naive B05
rate analogy). Reuse current components instead of cloning another learner.
Per-episode/update diagnostics and six checkpoints are durable bulk; full raw
evaluation trajectories retain actor inputs, commands and native consequences.
Compact config/per-world/fit summaries and source/native operation identities go
to Git. No scientific pilot or learner fit occurs during code checks.

L0: direction-owned `b02/inputs.py` observation-only cache wrapper, `model.py`
set actor/reused critic, `update.py` fixed categorical PPO, `study.py` complete
collection/training/final evaluation, `run.py` admission-first entry, mirrored
tests and offline reader. DM owns inputs/collector/entry/records; bounded
Implementer owns only model/update and its focused test. Existing B01 and shared
code stay unchanged. Independent engineering review covers likelihood, temporal
alignment, initialization/action/evaluation RNG, actor/critic information boundary,
update counts and complete result/admission contract before source acceptance.

### B02 Implementation Acceptance and Host Binding

DM read and accepts the Implementer's model/update diff and tests, then the
integrated inputs/collector/entry. The registered independent engineering Reviewer
`/root/dm_local_history/b01_engineering_review` found one P2: reused ordinary
collection counted partial successful steps globally but not in the evaluation
phase if it then raised. The DM fixed only the B02 wrapper: actual step delta is
accounted in `finally`, while completed episodes stay success-only; frozen B01 was
not edited. Injected-failure regression now establishes3successful evaluation
steps/4attempted calls,0training and no retry. No material finding remains.

Reviewed: actor/critic information separation, no retained SINR, cache mapping,
four-step macro alignment, categorical density and summed-agent PPO, normalized
complete-return targets, separate gradients/optimizers, independent initialization
and action RNG, initial/final identities, exact panel indexing, nonmutating shadow,
admission ordering, collision refusal and exposure accounting. The complete B02
suite has11passing tests (DM6.32s, independent5.45s); the4affected collector tests
pass5.12s after repair and the Reviewer reran the failure test successfully.
These include synthetic fixture collection/update, not a scored native pilot or
admission handshake. The later offline reader is not part of that engineering
acceptance; it will independently check hashes, all native outcomes/holds, exact
lawful input reconstruction and six checkpoint decisions after completion, with
native J tolerance1e-12 and same-host logits/logp tolerance2e-6, reporting exact
argmax agreement separately. It adds no environment or optimizer call.

Accepted executable SHA256 values:

- inputs.py:8a1e4eb7cb989d1fa65f9827b8a51168d86b6109f6b8494f12ad7a266f08947e
- model.py:8b72f22bfbc122e215fa44c34344cf584f051bbbc5f01138410a939e4c56c228
- update.py:efb16726ee1bd6e85c8384d86b32048b9ffd807e79506d2957a26598ca381856
- study.py:cc3aecdfdca50588c650e7342219fdfae6e7ac8df62fbf3241d2eb40aea2f01c
- run.py:d07e6edaeaf155570257bc2dbcb42cb82da1a233f3a16524e8e5164e4becb567

At15:12UTC the actual preferred wsl_4070 node was idle with14,898MiB available
and20logical CPUs, but a bounded fresh `curl -I https://github.com` again failed
SSL connection after5s. No remote result request, claim, worker, configuration or
canonical-control mutation was made. Bind the already declared local_linux
fallback before acceptance:16logical CPUs,8,770MiB available, load5.00 at15:13UTC,
configured `/home/fires/.venvs/hmasd-linux-cpu/bin/python`, one CPU worker/thread.
The kernel's fresh actual-node memory/source/pause/lead/duplicate checks still
determine admission. Exact output tag `b02_same_history_a01`, first CLI seed291021;
no change to the fixed exposure or scientific program. Root has the concrete host
facts; no additional approval gate is introduced.
