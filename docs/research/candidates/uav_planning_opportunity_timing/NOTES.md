# Completion-based planning opportunities on the retained N8 host

<a id="b01-source-contract-20261003"></a>
## 2026-10-03 — B01 source construction: commanded completion plus one report cadence

**State: source/contract preparation, not an effect purchase.** Root assigned this
new question to the existing, nonarchived `/root/dm_message_budget` native DM at
01:57 UTC. The former `uav_message_content` B07 and finite-channel source decision
are closed in reserve with all assets/adverse findings unchanged. This notebook
owns the new `uav_planning_opportunity_timing` paths. No world construction,
controller/model/native/physics query, saved-outcome re-reduction, fit, prototype,
implementation or node health check is authorized by this source assignment.
Current construction uses source, original published readings, primary literature
and arithmetic only. Root owns the subsequent whole-investment selection, using
its one separately contextualized `/root/four_dm_selection_critic`; no additional
selection critic or Pro round is commissioned here.

### Question, evidence and changed investment basis

The substantive question is whether a useful sequential cooperative-control
capability can be developed by changing when its second physical planning
opportunity occurs. The intended contribution is an executable ordinary-control
capability and empirical understanding of complete timing programs, not a new
learning method. Exactly two selection opportunities remain available per mission;
the intervention is their timing policy, not more opportunities, more sensing or
more training. An initiated selection is not necessarily a nonzero relocation.

I read the complete original four-DM Oracle recommendation in
[RESEARCH](../../RESEARCH.md#four-dm-oracle-proposal-20261003), published at
`54b36da4e476c4b861aa536904a87d97e66de61e`: original body 23,598 UTF-8 bytes,
SHA256 `78e165c12e222314f367472dc1658e7966d2ad3bbc191e893c1a1c1882828058`.
That recommendation is not the independent scientific review. Its C construction
revisits the [previously unbought timing proposal](../uav_fleet_transmission/NOTES.md#post-b04-source-only-design).
The earlier no-buy was an investment deferral, not an adverse timing experiment.
The new proposed basis is retained temporal benefit plus subsequently demonstrated
ordinary exact-reuse economy and the opportunity cost of completed competing
development purchases. Neither fixed120's suboptimality nor a positive early-clock
outcome follows. The owner's four-DM allocation is not scientific evidence.

The load-bearing positive is [fleet B04](../uav_fleet_transmission/NOTES.md#b04-complete-reading),
accepted source `239360b03f5d7acf788bd9ae5d4dccbde4f9237e`. On its sixteen fresh
N8/H500 worlds, A2−G2 mean J was +.001706076836 and service +.243875 users/tick.
Six changed first physical commitments all improved J despite sacrificing earlier
J and their complete one-opportunity modeled value; ten complete native programs
were identical. This supports conditional sequential complementarity under the
fixed40/120 rule. It does not prove that shortening the interval helps.

The same result retains substantial competing evidence. World29497012 supplied
about59% of mean J gain; 29497007 gained only .000491523 J with +613.328109m/UAV;
29497014 gained J but lost two user-ticks. Mean quality fell .005651723048 and
path rose42.946589m/UAV. Native J does not charge travel. The first selected member
was sometimes remuted and selected again later; usefulness was not permanent
extra activation. Whole-episode service minima/p05 did not measure individual
continuity. These are constraints on the new prediction, not defects to remove
from the inherited record.

[Parent B08](../uav_parent_adaptation/NOTES.md#b08-complete-reading), source
`ba18513feec96ed4de8d7cf111f6587e99df8271`, preserved the original scientific
payloads while reducing measured worker-plus-reader CPU to46.1146% for G2 and
45.6542% for A2. Optimized A2 still cost2.888276 times optimized G2. The retained
[result](../../../../runs/uav_parent_adaptation/b08_exact_planning_reuse_a01/result.json)
and full original reading were consulted, without recomputing old outcomes.
This was64 controller histories/32,000 calls, zero new native worlds/transitions;
its zero-query reader compared against existing immutable B04 outputs. It does
not establish early-clock reuse, new-world savings, native throughput or a
deployment deadline. Earlier B06/B07 approximation/ranking adverses remain their
original results; no learned approximation is added to this timing purchase.

The relevant shared background was read from published main
`54b36da4e476c4b861aa536904a87d97e66de61e`: [topic3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构)
distinguishes the full evolving program from permanent extra activation and makes
optimized ordinary planning a competent comparator; [topic5](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据)
distinguishes selection, commitment and effective cooperation lifetime; topic8's
mathematical/information discussion requires matching actual policy sets before
making improvement claims. Those judgments cause three design choices here:
include fresh G_E as well as A2, preserve actual private history/absolute phase,
and claim only this complete timing rule rather than a nested-set or generic
adaptive-timing advantage. No shared-background change is inferred from source
construction alone.

One primary-source bridge is **VS-0005, Learning Uncertainty-Aware
Temporally-Extended Actions (AAAI2024)**, personally read at PDFpp2–3
(printed13392–13393), with structured source
`/home/fires/projects/Inst-sci/papers/MyLib/json/VS-0005.json` and PDF
`/home/fires/projects/Inst-sci/papers/MyLib/pdf/VS-0005.pdf`. Its initiation,
intra-option policy and termination distinction, and separate choice of action
and commitment length, clarify why changing an opportunity clock is not merely
renaming an action. Its learned uncertainty/extension results are not evidence
for this deterministic fleet or for earlier timing. Here the missing single-agent
coupling is the shared interference mask, member eligibility and later team
motion. No novelty or theorem-transfer claim is made.

### Exact host, lawful state and unchanged ordinary program

The native law is the existing `uav_fleet_transmission.b02.host.RepositionS1` /
`make_env` composition: eight physical UAVs, fifty fixed uniform users, H500,
free-space channel, 0dB service threshold, capacity10 per transmitting UAV,
nonempty transmitter mask, and the original componentwise clipped motion.
Silent UAVs remain physical, including in the mean-height penalty. The returned
team objective is J=.7(served/50)+.3quality−height_penalty; retain scalar reward's
existing division by8 separately. No finite battery, collision-avoidance law,
link-delay model, travel penalty or new information channel is introduced.

At reset each arm starts a fresh private OrdinaryController, zero FP32 issued
commands, next_t=0 and mask255. The actor receives only the entering nonempty mask,
its actual command/position/user history and the lawful CountAdapter FP32 state
at t divisible by10; all other ticks receive None. That133-vector contains
normalized UAV positions, validity bits, static users and normalized time. Decode
positions/users exactly as the frozen source does into FP64. It cannot read world
identity, unrounded native coordinates, local-observation internals, future native
arrays or another arm's private state. World IDs are for construction/evidence,
never selector features. Reports retain absolute t/500, including inside models.

Unchanged C runs one rotating coordinate pass each ordinary tick, member order
`(t+j)%8`, all27 FP32 ternary commands per member. It ranks immediate modeled J,
served count, less team movement, retaining the entering command, then lower
lexicographic command index. E at a legal report boundary follows that motion
choice, scores all255 nonempty masks at predicted moved positions and ranks J,
served, retaining entering mask, then lower mask integer. The chosen mask applies
to the actual step and is held between boundaries. C's issued command bits survive
position clipping. All arms retain absolute phase; no phase restart, zeroing of
history or parallel shadow controller occurs at a planning decision.

Motion remains `positions + (commands * 30) * 1.0` in the original FP32-command /
FP64-position order, clipped per component to x,y∈[0,1000], z∈[50,150]. Casting
commands to FP64 before multiplication changes the contract. Unchanged public
encoding, ties, mask ordering and every ordered floating-point reduction remain
part of the reference; there is no tolerance chosen from the new outcome.

### Menu, commanded completion and second-opportunity dispatch

Every selection constructs the original stationary shortlist from its own lawful
report and entering mask: stay plus one stationary champion per currently muted
member. A nonempty mask permits zero through seven muted members. The complete
stationary enumeration retains all100 sites/member: fifty user rows and fifty
anchor-plus-nine-nearest-user centroids, including duplicates, with the original
stable row ties. Horizontal projection considers k=−34…34 on clipped30m component
increments and the original distance/coordinate/absolute-k/k order. Descent and
horizontal component counts produce L=10max(1,ceil(unrounded_duration/10)), so
L∈{10,20,30,40}. This is a **command budget**, not measured geometric arrival.

Only that muted member receives its fixed ternary movement commands; all other
commands are zero during the L ticks. The old mask remains fixed. Each site's
stationary score uses its transit return plus `(500−start−L)` times its best
member-containing destination-mask return. There are128 such masks, ranked by J,
served then lowest integer, with no old-mask preference. Per-member champions
rank predicted total J, served, lower physical path, shorter L, lower member,
then lower site. Keep nonpositive champions as hypothetical commitments; do not
filter them merely because the stationary score loses to stay.

For an initiated first option beginning at40, commands execute at40…40+L−1.
At **t_arr=40+L**, the actual fresh report is decoded; all commands are forced to
zero, the best currently evaluated member-containing mask is installed, and that
tick executes. Native position may have reached/clipped to its destination earlier.
There is no position-based arrival detector, timeout repair or cancellation.
The new second opportunity is **t2=t_arr+10** (60/70/80/90); if the first selection
declines, t2=50. It is not rescheduled after later motion or after the second
commitment. All four arms still have exactly two scheduled selection opportunities
and at most two initiated commitments. An empty muted set yields a stay-only
menu and still consumes its scheduled opportunity.

Between arrival and t2, C runs at t_arr+1…t_arr+9 under the arrival mask.
There is **no intervening E report boundary**. At t2, perform the new search from
the actual report/history/entering arrival mask **before** executing that tick's
ordinary C/E action or replacement option. Thus an initiated first member is
still transmitting and cannot be relocated by the second selection under this
early rule. Ordinary E is not inserted ahead of selection to remute it. This
differs consequentially from fixed120, where C/E may already have remuted it.
In particular, it removes the same-member second relocation used by old
world29497014. This is a source-derived adverse prediction about the new action
opportunities, not a measured new score or a reason to insert a remuting exception.

Replace the expired first plan at t2 even when the second choice is stay; preserve
the same live OrdinaryController history. Never allow the old first-plan metadata
to reexecute or force another arrival. An initiated second plan uses indices
relative to t2, holds its entering mask during its own L2 command ticks, installs
the member-containing mask at t2+L2, then resumes actual C/E on the following tick.
There is no third selection. The forecast and actual program use identical expiry,
replacement and report ordering.

Zero-path commands and site aliases are retained. Minimum L is10 even if projected
displacement/descent is zero; freezing the team and changing the arrival mask can
still differ from stay. Record site labels, member/L/command physical identities,
actual displacement and complete modeled execution identities separately. An
all-alias menu, all-stay world, zero native difference or no changed first choice
is a complete legitimate result, not a reason to drop a world or acquire another.

### Four fixed programs, nested model semantics and contrasts

| Program | First choice at40 | Second choice |
| --- | --- | --- |
| G2 | Complete C-only continuation ranking of the unchanged shortlist | Fresh complete continuation search at120 |
| A2 | Rank each first candidate through its modeled ordinary120 search and selected suffix | Fresh actual120 search |
| G_E | Exactly G2's first selector, including C-only tails | Fresh search at that selected first plan's t2 |
| A_E | Rank every first candidate through its own modeled t2 search and selected suffix | Fresh search at its actual selected first plan's t2 |

For every ordinary second search, simulate stay and every forced per-member
champion from that actual/inner context through499 under the unchanged complete
C/E continuation. Choose by cumulative J, cumulative served, lower committed
first path, shorter commitment, lower member/site. Exactly equal or lower total
J than that context's stay branch **declines**, regardless of service tie-break.
This is exact comparison, not a fitted epsilon. The fixed G2/A2 controls directly
use retained parent B08 with exact reuse; its scientific law stays the B04 law.

A_E's t40 outer simulation for each first candidate proceeds from40 through its
own t2−1. Stay-first therefore models the later50 opportunity too. Copy the full
terminal controller and mask, preserve unrounded FP64 outer physical coordinates,
and encode an FP32 inner report for this absolute t2. The inner search starts
from the report-decoded physical coordinates and a private copy of terminal
history; it cannot alter the outer branch. The selected inner plan is then
executed on the unrounded outer physical state with the terminal history and
same report, through499. Ordered prefix/suffix accumulation yields the full
460-tick outer value. The trace annotation is at t2−40, never hardcoded80.
Branch/bank/segment identities include the first branch and its actual second
clock, and cannot collide across candidate-specific times. The actual second
selection replans from new lawful history even when a modeled second plan exists.

First selection uses the same strict comparison against its full stay-first
program and the original continuation ties. The actor never consumes stored
native counterfactuals. G_E/G2 must share all native arrays and first commitment
up to G_E's second opportunity; all four share their native0…39 prefix. Equal
complete first commitment under G_E/A_E means equal t2 and complete future law,
so the resulting native programs should agree. These are implementation/evidence
identities, not outcome screening rules.

Predeclare complete paired native **A_E−A2** as the primary use contrast.
Also retain **G_E−A2** as the decisive simpler-use contrast, **G_E−G2** for the
greedy timing package and **A_E−G_E** for anticipation under the same timing
policy. A2−G2 is the fresh fixed-clock reference; A_E−G2 completes the four-arm
description. G_E−A2 costs no extra trajectories and prevents overlooking a
cheaper useful program. A_E and G_E share a rule, not necessarily realized t2:
anticipation can change the first commitment and consequently its next clock.
Their contrast therefore includes those endogenous timing consequences. It is
not the original fixed-clock attribution with the same realized second timestamp.

The positive prediction is that using completion-aligned access can improve
complete J/service for some worlds, and that anticipating the resulting later
choice can alter useful first commitments. The competing explanations are
strong: ordinary early G_E may capture all useful benefit; early access can deny
remuting/repositioning opportunities available at120; the longer ordinary interval
can establish a better route; or all programs may coincide. Source alone does not
choose among them. This tests a fixed ordinary package, so no claim that timing
mediates every score change or that learning is needed is planned.

### Fixed prospective population, complete reading and finite outcome branches

Propose sixteen fresh common worlds29523000…29523015, independent from A's panel,
using SeedSequence address `[261003,73,world_id,stream,*suffix]`: stream1 user
seed, stream2 UAV seed and stream3/suffix8 runtime seed. Each stream uses the
same original member-major RandomState uniform generation (fifty x/y user draws;
eight x/y/z UAV draws). The world constructor is **not called during this source
task**. Generated initial arrays/hashes would be committed before result work.
Run worlds ascending and rotate `(G2,A2,G_E,A_E)` left by world index modulo4.
There is no shared controller, bank or branch cache across arms/worlds.

The four whole-mission engineering audits use one separate fixed world29523900
from the same declared address, once per arm in the listed order:4H500/2,000 steps.
These are included in the purchase below, not a free pilot or native labels for
all hypothetical branches. Their engineering acceptance concerns fixed-law
reconstruction, prefix/report/clock/reuse identity and artifact/count integrity,
not positive outcomes or useful activation. The actual result estimand excludes
this audit world and includes all sixteen fresh result worlds. Audit score signs
do not tune the rule, choose a seed or change the fixed panel. A consequential
correctness mismatch preserves evidence and ends dependent execution; repairing
it does not silently authorize a repeated audit or a larger scientific purchase.

Keep every complete native trajectory, masks, reports, component rewards,
commands, actual private terminal history, both selection records and all charged
stationary rows, model branches and segment reuse certificates. Immutable source,
configuration, RNG addresses, dtypes, ordered identifiers and artifact hashes bind
the one canonical evidence copy. Each first candidate's hypothetical t2, inner
eligible members, strict-stay decision and the selected outer program remain
readable, including unselected adverse alternatives as model forecasts.

The **full independent reader is uncompressed**: replay every paid controller
history, bank and model branch using the same declared laws without transition
reuse, reconstruct every reused transition key/source/barrier against those
freshly computed arrays, and require bitwise agreement of scientific model
arrays/ordered decisions with the worker. G2/A2 use the frozen B04 uncompressed
reference; the new adapter has an explicit no-reuse path. Independently reconstruct
all501 native snapshots/mission, motion/FP32 public encoding, user and peer radio,
assignment, observed views, reward arithmetic and capacity identities from saved
arrays. This adds no `env.step` missions but is real native-physics/model/scorer
work. B08's old zero-query certification is not available for these new outputs.

Selected forecast/native correspondence is an empirical reading, not equality
by fiat: report commands, masks, per-tick service, cumulative J and coordinate
errors under the original FP32-report versus FP64-native distinction. A2/A_E
t40 outer predictions are compared to their full actual suffix including fresh
second replanning. G2/G_E t40 C-only forecasts are compared only through t2−1,
before their unmodeled additional decision; their actual second forecasts compare
through499. Unexecuted model branches receive no new native label. A discrepancy
caused by lawful model/native quantization is not repaired by tolerance relaxation
or silently labeled a code defect; document it and its effect on the claim.

Report all16 paired J/service/quality/height/path outcomes, means, median,
positive/zero/adverse counts and worst losses, with a fixed10,000-replicate paired
world percentile bootstrap, seed29523991. Each sample resamples the sixteen world
indices jointly across all arms. Intervals are descriptive uncertainty for fixed
deterministic programs, not learning replication, confirmation or equivalence.
Keep complete service p05/minima/zero-service runs, activation and remuting
durations, first/second physical choices and zero-path/alias counts. For individual
continuity, reduce the already saved per-user connection stream into complete
served-user-ticks, longest unserved gaps and left/right censoring; do not rename
team minima as individual safety. These saved-array reductions add support CPU,
not new host/model queries, and are included in reading time.

No practical adoption threshold, travel exchange rate, deadline or universal
superiority criterion is invented. Conditional task usefulness and continued
investment are separate from deployment adoption. A_E improvement with tolerable
observed tradeoffs retains this specific capability; G_E−A2 improvement at lower
complete cost supports the simpler capability; early harm in both preserves120;
isolated gains/wide uncertainty preserve their witnesses without automatically
buying a timing grid. A_E−G_E alone cannot substitute for complete A_E−A2 use.
All aliases/no changes is informative about this fixed program only. None of
these branches restarts a frozen recipe or reserves all temporal-control questions.

### Complete prospective computation, storage and support price

The proposed comparison has **zero new fits/updates/training targets**,
64 result missions+4 audits=**68H500 missions/34,000 native transitions**,
136 scheduled selections and at most136 initiated commitments. Native reset,
initial radio state, data generation, imports and serialization are paid even
though they are not extra `env.step` transitions. The full reader adds34,068
saved-native snapshot reconstructions and34,000 motion/reward checks, not another
34,000 native environment steps. Any additional real-controller/physics check
outside these audits would require an explicit prospective count; no hidden
smoke/profile/pilot result is included.

The inherited conservative integer ceiling is reproduced by source/algebra:
`B=1+7*100*128=89,601` stationary requests/bank, at most700rows and28,000 candidate
transit ticks/bank; `C500=500*216+50*255=120,750` native ordinary requests.
For a complete all-ordinary model suffix, `S(t)=242.5*(500−t)` includes its reward
requests. An initiated candidate saves at least2,758 requests versus stay in
this bound, so `F(t)=8*S(t)−19,306` bounds one full stay-plus-seven-champion bank
of continuations. Early prefixes cost2,425 requests for stay and `L+2,082` for an
initiated first option. The early nested stay context costs1,054,845; an initiated
context has maximum1,032,687 atL10. These are query ceilings, not measured demand.

| Arm | Worker requests/mission ceiling | Worker logical model ticks/mission | Requests for17 missions | Model ticks for17 missions |
| --- | ---: | ---: | ---: | ---: |
| G2 |1,891,196|6,720|32,150,332|114,240|
| A2 |8,351,156|31,040|141,969,652|527,680|
| G_E |2,026,996|7,280|34,458,932|123,760|
| A_E |9,437,556|35,520|160,438,452|603,840|

Worker totals are **369,017,368 state/mask requests**, **1,369,520 logical model
physical transitions**, at most**408 stationary banks/285,600 rows/11,424,000
candidate-transit ticks**, and3,264 complete modeled branch artifacts. These
include every actual second replan and every candidate-specific inner search;
prefix+outer suffix totals460ticks, not two full missions. Counts distinguish
native controller requests, banks, model control/reward, candidate-transit work
and geometry caching. A request is not necessarily a new scored geometry.

The uncompressed full reader incurs the **same additional** search ceilings.
Thus worker+reader maxima are738,034,736 requests,2,739,040 logical model ticks,
816 bank constructions,571,200 rows and22,848,000 candidate-transit ticks, plus
the separately stated native-physics reconstruction and reductions. Verification
is not presented as free algorithmic work. The worker will report actual scored
requests, computed/reused transitions and logical work separately. Exact reuse
can reduce actual work, not change these prospective logical bounds.

Reuse is private to one branch segment, with a fresh cache at each decision,
prefix/inner/outer boundary and actual second selection. Use the retained B08
little-endian key: phase t%40, entering mask, fleet size; all FP64 physical
positions, controller estimates/users; FP32 issued commands and original public
user bits. Reuse is eligible strictly **after** that segment's start or arrival
event, never across an active commitment/arrival or later selection barrier.
Reports and absolute clock advance every tick, cached issued commands survive
clipping, and each floating addition/trace serialization retains original order.
The nine cache-eligible ticks in each early prefix cannot repeat a phase40 key;
there is no early-prefix recurrence saving to assume. Long tails may recur;
no new-clock saving is spent before measurement. No deadlines or compute-induced
physical waiting are imposed: CPU/wall are complete execution costs, not simulated
real-time performance. Adding such a resource contract would be another question.

Scaling B04's original worker and full-reader cost per request to this conservative
bill gives4.063508 worker+4.107914 reader hours, approximately**8.171633 enclosing
CPU-hours** before any demonstrated new reuse saving. It is an estimate from a
different execution/runtime, not an enforced allowance, timeout or benchmark.
The Oracle's broad **4–10 combined CPU-hour** forecast remains uncertain; its low
end must not be inferred by transferring B08's worker-only saving to this full
reader. Price **6–10 active support hours** for source/design, implementation,
synthetic checks, focused engineering review, complete scientific reading,
publication and cleanup, plus queue/network elapsed time. Actual support CPU and
overlapping review are not comprehensively metered and will not be called zero.
An expensive or slower implementation remains a possible result.

Forecast1–2GiB unique canonical raw/trace/certificate evidence, small committed
world/config/summary/reading metadata, about1.6–2.0GiB launcher source snapshot,
2–3GiB transient output/scratch headroom, and roughly.5–1GiB streamed process RSS.
These are existing-record estimates, not actual-node admission or a second backup
allowance. Retain one necessary evidence copy and compact adverse/failed records;
after live-consumer release remove unused scratch, snapshots and duplicate output,
measuring net allocated bytes. The future fresh launch would use the configured
remote-first `wsl_4070` interpreter for this CPU workload, one numerical thread,
no GPU work and fresh resource admission. No node is reserved now. A known
platform defect would require concrete same-operation reconciliation before
fallback, not a local-first health/probe round or silent duplicate.

### Bounded future implementation and present decision

Root accepted the proposed owned-adapter boundary by native message: new timing
selector and segment driver import the unchanged B02 transit/arrival primitives,
B03 ranking/identity/report helpers, B04 OptionProgram/summary and B08 recurrence
key/certificate primitives. G2/A2 directly import retained B08. Frozen fleet and
parent implementation, tests, notebooks and run records remain read-only inputs.
B04/B08 explicitly reject non40/120 starts; shifting timestamps cannot work
because it changes C's absolute phase. The new driver is therefore substantive
executable behavior, not a launch configuration change. No shared generic-driver
extraction is selected: A keeps its fixed clocks, so there is no second consumer
requiring one. There will be no shared-global monkeypatching or copied whole
planner/core to avoid ownership.

If selected after the actual whole-investment review, implementation belongs in
`experiments/candidates/uav_planning_opportunity_timing/b01/`, mirrored tests,
`runs/uav_planning_opportunity_timing/<tag>/` and matching direction scratch.
The DM owns this notebook/shared publication and accepts any bounded helper work.
The behavior change is candidate-specific command-completion scheduling while
preserving the primitive/state/score contract, with a complete uncompressed reader
and exact reuse accounting. Focused independent engineering review must cover
clock/expiry, report precision, history isolation, phase/reuse barriers and count
completeness. Pure tests may use stub scorers/hosts to exercise ties, empty menus,
aliases and sink mutation; real scientific queries are charged in the declared
whole audits, not hidden in a correctness label. This is a scope note, not current
permission to implement or run.

My source-level recommendation is the complete four-arm purchase rather than a
pilot timing grid or a learned-clock fit: it preserves the consequential ordinary
alternative and can distinguish a useful simpler program, extra anticipation,
harm or no change. The important correction to the Oracle is commanded completion
with **selection before any next-boundary remuting**, together with the full reader
price. This recommendation does not self-clear Root's independent selection review
or claim positive timing evidence. The current deliverable remains source-only;
the next actual dependency is Root's whole-investment choice after the single
ResearchCritic reads this construction. Source construction has acquired zero
new scientific effects, and no result producer or accepted launch exists.
