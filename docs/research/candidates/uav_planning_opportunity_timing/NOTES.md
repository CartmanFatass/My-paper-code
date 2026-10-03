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

<a id="b01-source-runtime-correction-20261003"></a>
### Concrete runtime correction before selection — 2026-10-03

After reading the full construction, Root relayed the independent critic's
support for the corrected68-mission comparison and corrected one prospective
runtime clause. **This paragraph supersedes the initial remote-first sentence
above:** this proposed study uses configured **local_linux first**, on host Jacob,
with `/home/fires/.venvs/hmasd-linux-cpu/bin/python`, the configured POSIX detached
supervisor and one numerical thread. Root explicitly selected this concrete
runtime because of the documented unresolved A03 remote-interpreter anomaly.
The old failure is not evidence that the remote node is generally unsafe.

The new operation would record actual interpreter/package/source versions,
user/system/child CPU without double counting, wall time, RSS, and any overlapping
local worker/reader conditions in its own records. The old local B04/B08 timings
remain price evidence, not a promise of equal new-clock recurrence, throughput,
isolation or latency. Local resource admission occurs only for an actual selected
effect launch. No health probe, standing reservation, automatic remote fallback,
duplicate launch or migration of an accepted operation is authorized by this
correction. The scientific/reader count and storage/support envelopes are
unchanged. Current work still has zero scientific effects and no implementation;
Root's whole-investment disposition remains the actual next dependency.

<a id="b01-selected-l0-20261003"></a>
### Whole study selected; independent response and bounded L0 — 2026-10-03

Root selected the complete corrected study at
`fdf68804ec2533d9b6020f5d9b4a393940f6d2c7`,
[whole-purchase disposition](../../RESEARCH.md#four-dm-c-selected-20261003).
I read the **entire original C recommendation** from the same separately
contextualized ResearchCritic, preserved without edits in
[its canonical original section](../../archive/2026-10-03/RESEARCH-four-dm-selection.md#four-dm-c-independent-review-20261003)
at that commit:8,677 characters/8,699 UTF-8 bytes, SHA256
`3aaeff42b91e38d7f4ef15cdc86c1d5bfeb7c86838cf2a1a8fca6faf5f465a1f`
(body excluding the enclosing details tag and leading/trailing newlines).
The complete original lives there once; this is my separate scientific response.

I accept the recommendation and its retained objection. This is a narrow
known-model renewal-law comparison, with no newly demonstrated defect in120.
Retained ordinary reuse and the usefulness of an earlier complete control answer
justify this one investment; they do not establish a new timing principle or a
learning surplus. The first mover's guaranteed early ineligibility, including
the lost old29497014 possibility, is a predicted tradeoff to test rather than
repair away. I retain the G_E−A2 simpler-use contrast, exact candidate-specific
clocks, all aliases/adverse outcomes, and the uncompressed reader bill. There is
no material dissent, no second selection review or Pro dependency, and no need
to wait for A/D. No outcome has yet been acquired.

The selected purchase is the declared68H500 missions/34,000 native transitions,
all four audits, zero fits/updates and complete uncompressed reconstruction.
Root fixes termination at **20 aggregate metered preparation/worker/reader CPU
hours**, **48 operation wall hours** or **10GiB normal operation allocation**
including source, unique evidence and transient scratch. These are operation
ceilings, not a fit allowance, runtime forecast or permission to add work.
Unmetered support and the finalization tail stay unknown. Use local_linux first,
one numerical thread and real memory/overlap admission; no health probe or
automatic fallback. **The first real formal-request/admission/worker/reader
failure closes this purchase**, retaining its completed prefix and concrete
failure facts without automatic retry or missing-cell completion. Reconcile
uncertain acceptance only for the same request. Pure source/mock corrections
before formal submission are permitted, metered where feasible, and retain their
failures. Root selected implementation through execution, reading, publication
and cleanup, not a prototype or another per-run approval stage.

**L0 deliverable and ownership.** Implement B01 under
`experiments/candidates/uav_planning_opportunity_timing/b01/`, matching tests,
the existing owned notebook, one `runs/uav_planning_opportunity_timing/` attempt
and owned temporary paths on shared main. The complete operation performs the
four fixed audits and their full reading before the sixty-four result missions
and their full reading; this is one prospectively bought chain, not an audit
outcome screen. Exact operation identities and paths will be fixed in committed
inputs before the single formal launch. No frozen fleet/parent path is edited.

One bounded registered Implementer owns the **early-clock selector and segment
behavior**, specifically new `b01/controller.py`, `b01/option.py`,
`b01/segment.py`, `b01/__init__.py` and their focused
`tests/.../b01/test_timing.py`. Required interface is
`TimingProgram(arm, horizon=500, branch_sink=None, candidate_sink=None,
reuse=True, segment_sink=None)` for G_E/A_E, exposing controller, plan,
plans/selections/banks and the selected second_t; `select(t, report, old_mask)`
returns command/mask/decision. Callback payloads cannot mutate scientific state.
Branch outputs retain arrays/summary/decisions; segment callbacks additionally
carry the B08-compatible entry/terminal/reuse certificate. All identifiers encode
their actual start time and candidate context. The new ordinary menu must price
every original site at500−start, not merely reprice an old chosen champion.

The DM owns world/config bindings, collector, complete reader, runner/admission,
resource accounting, publication and separate pipeline tests. The Implementer
has no index/commit/NOTES/shared-file ownership, performs no result launch,
scientific world/controller/model/native/physics probe or fixture run, and spawns
no children. Its checks use fully stubbed scorer/host dependencies and synthetic
arrays; any real query belongs to the declared whole audits. Return exact checks,
metered self/child CPU and wall, owned scratch cleanup, diff and open risks. We
are not alone in the checkout: preserve all other edits and use disjoint paths.

The implementation preserves the complete contract above: pre-E t2 dispatch,
expiry even on decline, unchanged absolute ordinary phase and FP32/FP64 order,
fresh actual history/reports, independent nested copies, inner decoded/outer
unrounded distinction, strict stay ties, empty menus/zero-path aliases, no third
opportunity and no cross-segment reuse. Focused independent engineering review
will cover these semantics plus RNG/source/launch identity, evidence completeness,
full-reader independence and the actual resource-stop path. The DM reads the
diff/checks and accepts the implementation. Inputs are committed/published before
native admission; accepted observation stays on the same operation handle.


<a id="b01-implementation-accepted-20261003"></a>
### Complete implementation accepted before the single formal request — 2026-10-03

The bounded Implementer returned the four owned timing modules and focused tests;
I read and accept the code and checks. G_E retains the frozen complete first
selector; A_E prices every first candidate with its own second clock. Early
menus enumerate all original sites with remaining horizon500−start. The new
segment loop is needed because the frozen entry validator admits only40/120;
it imports the original primitives and B08 keys/certificates without changing
frozen files or shared globals. The DM implemented fixed worlds/input binding,
streamed collector, uncompressed reader, finite-operation entry, resource guards
and separate pipeline tests. The full source is in the owned `b01/` directory.

The full reader uses the frozen uncompressed B03/B04 reference for G2/A2 and the
new explicit nonreuse path for G_E/A_E. Every model array and ordered decision,
stationary row, selection, actual private history and reuse certificate is
checked. Native reconstruction uses the original exact-array checks and original
1e−14 scalar/N8 reward-scaling check; there is no new tolerance chosen from a
result. Chosen forecasts remain empirical comparisons with actual native suffixes.
The operation first runs all four audit missions and their full readings, then
runs and reads each four-arm result-world group in the fixed cyclic order.
This changes neither the bought population nor the comparison or failure rule.

The collector saves a native prefix and all completed branches/banks/segments
when an exception closes a cell. Full branch/segment payloads with identical
scientific arrays/decisions share one artifact reference. After a mission passes
its full reader, prefix/suffix copies are checked bitwise against the retained
outer branch before deletion; their summary, certificate, digest and slice
reference remain. Partial deletion facts and new catalog hashes survive a delete
failure. These are evidence-layout operations, not an additional model replay.

The separate-context engineering Reviewer inspected all timing/menu/precision,
cache, source/RNG/admission, full-reader and retention paths. It found three
material issues, all repaired before submission: (1) negative differences had
been called adverse even for cost quantities; they now retain neutral signed
counts/extrema, with explicit adverse fields only for J; (2) repeated SIGXCPU
could interrupt failure retention; signal/cooperative stops now disarm before
unwinding and latch a permanent stop; (3) an unlink failure after catalog
publication could leave the summary's old hash; a `finally` path now refreshes
catalog bindings and retains a mutable planned/actual-deletion ledger. Synthetic
regressions cover resource-stop retention and a FAILED_CLOSED summary that still
resolves every retained branch/segment after unlink failure. Reviewer final:
**no material engineering finding remains**. DM acceptance is separate and made
here. Real native execution and actual admission remain untested until this one
purchased operation; these mock checks are not a scientific pilot.

Checks and measured preparation (one numerical thread, configured scientific
Python3.10, `-B`, pytest-managed scratch):

| Work | Outcome | Metered self CPU s | Metered child CPU s | Wall s |
| --- | --- | ---: | ---: | ---: |
| Implementer check1 |11 passed |.071434|.940302|1.090912360|
| Implementer check2 |12 passed,1 failed synthetic scorer geometry ledger |.070605|.956785|.957547601|
| Implementer check3 |13 passed after stub-only repair |.068773|.918932|.902150824|
| Fixed17-world input generation |88,298B JSON; no host/controller/scorer |.205673|0|.178365705|
| DM complete focused suite |27 passed |.084954|4.363473|4.793970992|
| Independent Reviewer suite |27 passed |.000333|3.630421|3.641693|

The failed stub test reported zero geometry rows while the independent certificate
checker reconstructed unique/reused rows from the arrays; only that synthetic
bookkeeping was corrected, without a production or tolerance change. Both full
suites had14 third-party Matplotlib/Pyparsing deprecation warnings and no scratch
cleanup warning. AST/source checks passed. These instrumented preparation tasks
sum to**11.311685 CPU seconds**; wrapper interpreter startup before the Reviewer's
sample and uninstrumented source/support tools remain unknown, not zero. Largest
pytest-child lifetime peakRSS was323,440KiB; wrapper high-water maxima were inherited
process-lifetime facts and are neither incremental nor additive. Every check used
stubs/synthetic arrays:0 real native steps,0 real model/scorer queries,0 fits/updates.
The input constructor generated exactly the17 declared initial arrays and no
rollout. Initial arrays and preparation accounting are committed source inputs.

The exact selected attempt tag is `b01_complete_timing_a01`, output
`runs/uav_planning_opportunity_timing/b01_complete_timing_a01/`. Its sole entry is
`experiments/candidates/uav_planning_opportunity_timing/b01/run.py`, identity seed
29523000, full published source SHA supplied to both kernel and runner. Submit
through the configured local_linux native launcher with a retained source
snapshot, exact lead `Codex DM (native child)`, and one numerical thread. No input
checkpoint, remote staging, health probe, alternative node, duplicate, missing-cell
completion or automatic retry is added. The20h aggregate metered CPU limit reserves
300CPU seconds for launcher/finalization; the48h wall limit reserves600seconds;
normal source/output allocation reserves64MiB before10GiB. Runtime signals cover
long branches and cooperative checks cover cells/callbacks; the final measured
bill, possible tail and any reserve overrun must be reported, not assumed away.
A real formal-request/admission/worker/reader failure still closes this purchase.

Root moved the completed original selection advice unchanged to the dated archive;
the canonical link above now points there. Its8,699-byte original/hash and my
scientific response are unchanged. No second scientific selection round or owner
approval was added. The selected whole comparison is now ready for its single
formal submission; there is still no accepted operation or scientific result at
this entry's publication boundary.


<a id="b01-a01-formal-refusal-20261003"></a>
### A01 first formal request refused; zero-effect purchase closure — 2026-10-03

The single formal local_linux request at published source
`4736b91c62b4a1e0072fa6ea37c1300ebafee9c8` exited4 before execution:

> hmasd launch refused: direction 'uav_planning_opportunity_timing' has unrecognized active state 'active'

[Exact request, stderr/stdout, exit, source diagnosis, cost and reconciliation](../../../../runs/uav_planning_opportunity_timing/b01_complete_timing_a01/launch-refusal.json)
retains the command as an argv array and the empty stdout digest. No native
manifest, output directory, worker, process-exit witness or result existed; the
compact run directory was created only afterward to retain this refusal. The
same-output read-only status request also exited4 because the reference did not
exist. No accepted handle was invented and no observer was armed.

The defect is specific and ours to preserve: the direction table had literal
state `active`. Current `scripts/hmasd_launch.py` accepts `exploring` and
`confirming` in its Active table, and `parse_research_state` rejected that local
value. `_prepare_paths_and_config` calls this policy check before snapshot
preparation. Read-only reconciliation found no matching record in the actual
`.git/hmasd-admission` store, no non-author worktree at the scientific SHA, no
exact runner process, and no native output. The refusal preceded published-control
verification, source snapshot construction, memory admission, claim and spawn.
This is not a runtime-health failure, resource shortage or test of the timing law.

The first-formal-failure stopping rule closes A01: **0 native missions/steps,
0 model/scorer/full-reader queries,0 fits/updates**, and no automatic correction,
retry, fallback, missing-cell completion or pilot. GNU time reported.24s launcher
wall,.12s user+.07s system CPU (each at.01s precision); known metered preparation
plus launcher is approximately11.50CPU seconds, with uninstrumented support and
Reviewer's wrapper startup still unknown. There was no scientific worker or reader
bill. Technical source completion and synthetic checks remain useful; no native
comparison was acquired and no timing hypothesis is strengthened or weakened.

Root received the concrete failure and requested complete closure/reconciliation
before it reads the exact record and makes any explicit corrected-purchase choice.
The existing complete comparator and independent scientific/engineering reviews
still apply to the unchanged design, but this does not itself authorize another
formal request. The direction is placed in reserve for that concrete Root choice;
the question remains open, with old B04/B08 evidence and the first-mover opportunity
loss unchanged. No shared scientific-background edit is warranted by zero new
scientific evidence.

After confirming no consumer, the two exact scratch captures and their attempt
and empty direction directories were deleted. Their unique contents live once
in the compact refusal record. **Net allocated space reclaimed:8,192bytes**, after
charging the compact record's final growth; exact deleted paths and before/after
allocation are in that record. No source snapshot was created or deleted, no
required evidence was removed, and no cleanup tool blocker or own scratch remains.
The already published useful implementation/tests/fixed initial arrays remain for
Root's concrete corrected-purchase review; no new code change or scientific
repair was performed after the formal refusal.


<a id="b01-a02-selected-20261003"></a>
### Root selects one corrected whole A02 purchase; costs carried forward — 2026-10-03

Root read the complete A01 refusal, reconciliation, cost and closure, and explicitly
selected `b01_complete_timing_a02` at
`1ca29126a9899d52ddd42d6c2a396dd5c460f71e`,
[corrected whole purchase](../../RESEARCH.md#four-dm-c-a02-selected-20261003).
A01 remains closed. No accepted operation exists to resume. This is one newly
selected formal request with a specific, source-supported reason: replacing the
mistaken local/published direction state `active` with the authorized `exploring`
value should remove exactly the parser refusal identified in the A01 record.
It does not establish that later admission or native execution will succeed.

Only the owned RESEARCH row/state and task routing, this prospective note and
preparation/provenance metadata change. Lead remains `Codex DM (native child)`;
owner pause remains lifted and all other rows/controls are preserved. All
scientific Python, tests,17 committed initial arrays, controller/comparator/world
laws, tolerances, tie/order/precision rules and reader contracts remain byte-for-
byte those accepted at `4736b91c62b4a1e0072fa6ea37c1300ebafee9c8`. A pure Git
comparison confirmed the only implementation-tree change is preparation.json;
the unchanged worlds.json Git blob is`cf9e82f2f819acbf15ebc46d8fcdd82e1286780d`.
No launcher-rule change, redesign, validation mission, health test, new Oracle or
independent scientific/engineering round is added. Existing completed advice and
checks cover this unchanged study and remain applicable.

A pure source parser/metadata check verified `parse_research_state` returns
pause`lifted`, state`exploring`, lead`Codex DM (native child)` for the corrected
local index, without invoking launch, snapshot, actual-node admission or any
scientific callable. It consumed.122822self+.074350child=.197172CPU seconds,
1.704124wall seconds, including its fetch/hash subprocesses. Those costs add to
11.501685known A01 preparation+refused-launcher CPU seconds, so committed
preparation now carries**11.698857metered CPU seconds**. Source/publication support,
Reviewer's pre-sample wrapper startup and the final metadata-write tail remain
unmeasured, not zero. Paid costs are not reset by the fresh attempt name.

The full fixed68H500 missions/34,000 native transitions/0fit and complete
uncompressed reading remain selected. Local_linux first, one numerical thread,
20 cumulative measured preparation/worker/reader CPUh,48 operation wallh and
10GiB normal source/evidence/scratch allocation remain binding. The first actual
formal/admission/worker/reader failure of A02 still closes it; uncertain acceptance
is reconciled only for that request. Healthy adverse/no-change outcomes complete
all planned cells. No alternative node, repeated audit, missing-cell completion
or automatic retry follows. The new sole formal output is
`runs/uav_planning_opportunity_timing/b01_complete_timing_a02/`; runner identity
seed29523000 and all science argv remain unchanged except the newly published
source/attempt bindings. Submission follows publication of these exact corrected
inputs. A01's record and8,192byte cleanup remain intact and independently readable.


<a id="b01-a02-accepted-20261003"></a>
### A02 native acceptance and deterministic observation — 2026-10-03

The one corrected request was accepted at2026-10-03T03:28:23.305107Z from
published source`4481c6240dc8266c2a6f13070cc1e8762328e614`, node`local_linux`
(Jacob), with the unchanged fixed seed29523000 and complete operation argv.
[Native manifest](../../../../runs/uav_planning_opportunity_timing/b01_complete_timing_a02/launch-manifest.json)
and[actual-node preflight](../../../../runs/uav_planning_opportunity_timing/b01_complete_timing_a02/admission-preflight.json)
are the accepted identities. The immutable source is
`/home/fires/hmasd-wsl/.git/hmasd-launch-sources/3461f799792c4200ae6f20e13d45c4c8`;
output remains the original author checkout's A02 run directory. The operation
reference is
`/home/fires/hmasd-wsl/.git/hmasd-admission/1d91acf5dbdac0424e47368754ded110b19e347d5c68265843a18297406127e1.json`,
command SHA256`224de292b02186289666f922b36cc6e0167fa90b1ca1ddce44ac1b488ed97c2f`.
SupervisorPID1070061 and runnerPID1070062 share session1070061 with native start
ticks12536133/12536137 and boot id in the manifest. These are process facts,
not scientific completion.

Fresh actual-node effective available memory9,731,661,824B passed the4GiB floor
at03:28:23.269329Z. Actual runtime reports Python3.10.20,
`/home/fires/.venvs/hmasd-linux-cpu/bin/python`, NumPy1.26.3 and Torch2.7.0+cpu,
Torch intra/inter-op1/1 and the declared numerical environment threads1.
The runtime's overlap inventory includes the independent decision-generalization
worker/supervisor at source49b9b182f78c472ebd5f8227396e92b5 (PIDs883772/883773)
and its own supervisor; this is not an isolated-host throughput claim. Initial
recorded source/output allocation was about1.849GB; actual operation accounting,
RSS and later overlap remain in summary.json.

GNU time for this formal launcher reports20.36wall seconds,4.63user+6.69system
=11.32CPU seconds at.01s precision. Add that separately to the committed
11.698857preparation CPU seconds (about23.02known pre-worker CPU seconds total);
do not double count the detached runner. It fits within the prospectively
reserved300CPU-second allowance for launcher/finalization. The final complete
bill still includes actual worker/reader CPU and unknown uninstrumented support.

The session's existing stopped observer had no pending events or live jobs;
it was rearmed and the new A02 status job registered. Observer generation4
then independently observed matching running supervisor/runner identities and
consistent native records on this **same** operation handle. Its30second probes
and1,500second checkpoint window never restart the worker. The DM remains active
through assigned reading and will drain/rearm that handle as needed; registration
alone was not used as wake or completion evidence. All four audit worker missions
had finished when the first full audit reader began; no result claim or fit-law
change follows from that progress. Correct adverse/no-change outcomes retain the
entire fixed purchase.

At the first observer checkpoint (generation4, event
`4790e5d9b9b99d5eebb3d346`, wake`9fa3dccc-c270-425d-a693-317f0f58e924`),
the03:54:17UTC native observation still had the same running process identities,
consistent records, no exit witness and no probe errors. The controller's queue
delivery returned the explicit native-child rejection (`direct app-server input
is not allowed for multi-agent v2 sub-agents`); the already active DM read its
saved event locally, so no launch or observation identity changed. A rearm call
with3600seconds was rejected by the observer's1500second limit without mutating
the operation; rearm at1500seconds consumed that checkpoint and established
generation5 (observerPID1091589). The passive local wait only watches saved
events, while the existing deterministic job alone probes the native handle.
The contemporaneous summary contained12 completed worker episodes and11 reader
entries, with the reader on G2/world29523001. Its last resource sample was
1,572.665900runner CPU seconds plus11.698857preparation,1,573.284084operation
wall seconds,381,772KiB peak RSS and1,910,870,016peak observed allocated bytes;
the exact resource JSON remains authoritative. No scientific interpretation follows from
this checkpoint and all planned healthy cells remain selected.


<a id="b01-complete-reading"></a>
### A02 complete execution and fixed-design reading — 2026-10-03

The sole A02 worker exited0 at2026-10-03T06:44:45.667871Z. The same native
operation's06:45:10.766533Z terminal observation found both recorded processes
absent, a valid process-exit witness and consistent source/manifest records.
All68 H500 missions and all68 complete uncompressed readers finished:34,000
native transitions,34,068 native snapshot reconstructions,34,000 motion/reward
checks,0 fits and0 updates. Both output logs are empty. The fixed audit world
remains outside the16-world estimand; no failed or missing cell was replaced.

Observer generations4–10 were drained at their saved checkpoints and rearmed
on the original handle only. Generation11 delivered terminal READY event
`889b76912fcc74b5505eba94`, wake`cfb1a4fe-f472-4a5f-acae-9ff27fb109a1`.
The same native-child queue rejection persisted, while deterministic local
observation remained healthy. After reading the terminal facts, generation12
consumed that event and the observer was stopped; saved state has no pending
event or wake. No operation was rebound, resent or migrated.

Complete reading now reduces only the already acquired summaries, choices,
native arrays and catalogs. The scope is the predeclared six contrasts, all
worlds and individual-service losses, actual choices/clock/remuting identities,
forecast correspondence and the complete worker/reader bill. It adds no
physics/controller/model query, native transition, bootstrap plan, fit or
changed numerical tolerance. A compact result retains the readable aggregate
and per-world outcomes, with verified hash/size locators for the unchanged
canonical bulk. After checking terminal and live-consumer facts, cleanup will
remove only this operation's released source snapshot and redundant scratch.

#### Complete ordinary-program value

**Retain A_E as a useful anticipatory timing capability on this host.** It improves
the complete primary A_E−A2 panel mean in J and service, with lower mean path and
a quality loss. The simpler G_E does not absorb that gain: it loses mean J and
service to A2, while A_E−G_E improves both in all seven worlds whose first physical
commitment changes. The other nine A_E/G_E native programs are byte-identical in
every stored native array. This is an acquired ordinary-control result, not just
an untested suggestion about timing or an intermediate predictor improvement.

The [compact complete result](../../../../runs/uav_planning_opportunity_timing/b01_complete_timing_a02/result.json)
retains all64 scientific world/arm outcomes and four audits, all six predeclared
contrasts, choices, forecasts, individual-service comparisons, costs and canonical
bulk locators. Intervals below are the frozen10,000 paired-world percentile
bootstrap (seed29523991, the same16 sampled world indices for every arm/metric).
They describe these fixed deterministic programs and the sampled world law;
there are no training replications, confirmation or equivalence claims. Exact
positive/zero/negative counts include very small differences; no practical margin
was selected after seeing them.

| Complete contrast | Mean J difference [95% interval] | J +/0/− worlds | Mean served users/tick [95% interval] | Mean quality difference | Mean path difference, m/UAV |
| --- | --- | --- | --- | --- | --- |
| A_E−A2, primary | +.004137129 [.000260501,.009437566] |11/3/2| +.376750 [.068625,.824128] |−.003892798|−441.436129|
| G_E−A2, simpler use | −.004305155 [−.007940417,−.001030237] |6/4/6| −.335125 [−.658638,−.055875] |+.001957401|−109.425313|
| G_E−G2 | −.000213750 [−.001175236,.000598995] |8/4/4| −.025625 [−.115375,.037750] |+.000466146|−49.852614|
| A_E−G_E | +.008442284 [.003034965,.014523678] |7/9/0| +.711875 [.258109,1.230753] |−.005850199|−332.010817|
| A2−G2 | +.004091405 [.001310957,.007290872] |6/10/0| +.309500 [.067997,.581884] |−.001491255|+59.572699|
| A_E−G2 | +.008228534 [.003081355,.014080948] |12/3/1| +.686250 [.258375,1.175650] |−.005384053|−381.863431|

The primary J median is+.000966575. Its two adverse worlds are29523005
(−.003121738J/−.064service) and29523012 (−.007264407J/−.214service).
World29523010 contributes55.80% of the signed total J improvement; its gain is
+.036933412J/+3.198service. This concentration limits precision and breadth without
erasing the observed capability. Mean quality falls with interval
[−.008077742,−.000101068]. The path interval is[−1183.352776,−31.823056]m/UAV;
world29523009 contributes82.00% of that signed total saving. Paths increase in
two worlds, by at most92.729708m/UAV. Path is not charged by native J, so a travel
or deployment utility has not been optimized by this result.

| World suffix (295230xx) | A_E−A2 J | Served users/tick | Path m/UAV | Users losing served ticks | Users with longer longest gap |
| --- | ---: | ---: | ---: | ---: | ---: |
|00|+.003146564|+.240|0|2|2|
|01|+.014706482|+1.310|0|2|2|
|02|0|0|0|0|0|
|03|+.004974539|+.492|+92.729708|9|7|
|04|+.000650280|−.002|+6.856602|4|4|
|05|−.003121738|−.064|−442.699569|8|7|
|06|+.000100914|0|0|0|0|
|07|0|0|0|0|0|
|08|+.004847198|+.086|−372.925716|9|6|
|09|+.006604120|+.490|−5791.679381|4|4|
|10|+.036933412|+3.198|−9.577230|8|6|
|11|+.000004545|0|0|0|0|
|12|−.007264407|−.214|−140.125383|9|10|
|13|+.003329288|+.230|−188.639290|5|5|
|14|0|0|0|0|0|
|15|+.001282870|+.262|−216.917809|8|8|

Fresh A2−G2 again has six changed first commitments with six J gains and ten
byte-identical complete native programs. Thus the fixed120 anticipation capability
is independently retained on new worlds; it was not a failed comparator that
needed rescue. Its service-loss world29523015 and quality/path costs also remain.
G_E has a lower measured compute/path cost than A2 but no demonstrated mean
J/service preservation here. That is a conditional frontier, not an equivalence
finding or an unconditional reason to discard cheap control.

#### Choices, anticipation and what the mechanism reading establishes

All programs made exactly two scheduled selections. On the16 scientific worlds,
G2/A2/G_E/A_E initiated15/15/15/14 first commitments and12/12/10/13 second
commitments. The new second clocks actually span50,60,70,80; no selected first
duration requires90 on this panel. A_E/G_E share a timing law, not necessarily a
realized timestamp: two of their seven changed-first worlds also change t2.
The remaining five retain the same realized t2 while changing the first physical
commitment. Across all68 missions, the actual menus retain128 nonpositive
champions; none is stay-only, and no selected zero-path or champion physical/
execution alias occurs. Their source semantics were preserved despite that
nonactivation.

World29523010 is a concrete new anticipatory capability. G_E first moves member4
to site75, then member1 to site40; A_E first moves member2 to site35, then member4
to site6. Both use the actual early second clock60. A_E's selected outer model
J is309.001610, versus290.549622 for its modeled member4-first alternative;
the complete native A_E−G_E gain is+.036903974J/+3.198service. These paid modeled
alternatives are not additional native counterfactual missions. World29523009
shows a different useful program: A_E declines at40 and moves member0 at50,
while G_E/A2 keep the member2-first program. Its complete mean path falls from
6061.625732 to269.946351m/UAV, with J/service gains. The useful object is the
evolving program, including a valuable initial stay, rather than a count of
permanently added transmitters.

The source-predicted early first-mover exclusion is respected in every actual
initiated-first case. However, every actual initiated first mover in this fresh
G2/A2 panel is also still active at its fixed120 selection, and no arm actually
relocates the same member twice. Therefore the old29497014 remuting opportunity
remains a real structural constraint, but loss of that realized action does not
diagnose this panel's two A_E−A2 adverse programs. Counterfactual menu/phase,
ordinary motion and endogenous first/second choices remain coupled. No remuting
exception or new clock was added after observing this fact.

All136 selected forecast/native comparisons, including audits, agree exactly in
commands, masks and per-tick service. The largest coordinate discrepancy is
5.6707223e−5m; the largest absolute cumulative J discrepancy is2.8904488e−6.
The original FP32-report/FP64-native distinction remains, without changed tolerance.
This validates the stated selected-forecast correspondence for both favorable and
adverse programs, including fresh actual second replanning. It does not provide
native labels for every unexecuted branch or prove accuracy under another task.
In particular, world12's A_E loss is a correctly executed different timing program,
not an observed model/native prediction failure.

The primary full-program comparison establishes a conditional empirical benefit
of this complete anticipatory early rule. A_E−G_E further establishes the value
of its anticipatory selection package under that rule. Neither statement requires
isolating each contribution of clock, absolute phase, menu and ensuing motion.
The G_E result rules out the simple claim that early access alone reproduces the
gain; it does not refute timing usefulness. No learner ran, so representation or
finite learnability is not adjudicated, and no general MARL or optimal-clock
claim follows. Mechanism limits do not cancel the native gains.

#### Individual continuity and adoption scope

A_E adds3014 served-user-ticks over A2 across the16 complete missions. Among the
800 matched user/world records,104 gain served ticks,628 tie and68 lose; longest
observed gaps shorten for92, tie for647 and lengthen for61. These are descriptive
dependent records, not800 independent inferential units. Never-served counts are
G2=35, A2=26, G_E=35 and A_E=23. A_E rescues five A2-never-served users but creates
two new never-served users, both in29523012 (users17/48; rescued users2/4/7/42).
World29523010 also rescues user6 while user16 loses445 served ticks (500→55),
acquiring a445-tick right-censored terminal gap. A positive team gain and a net
reduction in never-served users therefore coexist with substantial individual
losses. In world04, just one net lost team user-tick includes user24's499→93
served ticks; total throughput is not an individual continuity guarantee.

Whole-episode service minima and p05 match in every paired world, and every arm
has zero whole-team-zero ticks. Their common early prefix and different per-user
outcomes prevent interpreting these equal team tails as safety or equivalence.
All individual gaps retain left/right censoring at post-transition ticks0…499;
they do not extrapolate waiting beyond the mission. The complete records, including
these adverse outcomes, remain in the canonical reading.

For research use, A_E is now a competent ordinary capability to retain beside
A2, not merely another baseline that a future learner must beat. Under the
observed mean J/service/path criteria it is attractive at nearly the same worker
CPU cost. There is no new universal deployment default: the original study did
not price an individual's loss, quality, travel or a deadline, and its two primary
J losses cannot be removed by changing that rule afterward. Continued capability
development need not wait for a complete mechanism account or a universal
adoption criterion.

#### Full acquisition and reading cost

All1260 worker model branches and296 stationary banks were fully reconstructed.
Worker logical model work is530,330 ticks, of which90,606 were computed and439,724
reused. The independent uncompressed reader computes530,330 model ticks again;
its reconstruction checks the reuse keys/barriers and original ordered payloads.
Worker logical state/mask requests are143,000,722, actual worker requests36,666,869,
and uncompressed reader requests143,000,722:179,667,591 actual worker-plus-reader
requests, with the separately stated native snapshot/physics checks. Worker and
reader each price96,400 stationary rows and1,846,490 candidate transit ticks.
Actual menus were substantially below the prospective ceilings; the lower than
forecast wall/CPU bill cannot be attributed entirely to reuse or a host speedup.

| Arm,17 missions including audit | Worker episode CPU s | Uncompressed reader episode CPU s | Actual worker requests | Computed / reused model ticks |
| --- | ---: | ---: | ---: | ---: |
|G2|382.589842|1052.006193|5,146,429|9,645 /52,235|
|A2|1008.897921|3124.027760|13,396,664|36,628 /153,312|
|G_E|380.814163|1134.691286|5,210,067|9,846 /55,554|
|A_E|1019.642450|3428.178320|12,913,709|34,487 /178,623|

A_E/A2 worker episode CPU is1.010650; their reader-inclusive episode CPU ratio
is1.076192. These are this panel's measured price, including recording, under
the shared local runtime, not a portable deployment latency or speedup estimate.
Worker episodes sum2791.944376CPU seconds and readers8738.903559; the encompassing
runner sample is11,709.959133CPU seconds and11,777.474865wall seconds, with
179.111198CPU seconds outside those episode subscopes. Runner peak RSS is
382,900KiB and final sampled source/output allocation2,271,563,776B. Concurrent
jobs differed between the start and terminal overlap inventories; this was not
an isolated-host benchmark.

Preparation11.698857CPU seconds includes A01's paid refusal and subsequent
preparation; the A02 formal launcher adds11.32CPU seconds. Saved-data publication
reduction and complete current-artifact hashing add4.762020measured CPU seconds
(4.612027wall, process-lifetime RSS high-water669,536KiB, separate from runner RSS).
The currently measured total is11,737.740010CPU seconds, about3.26048hours.
Uninstrumented source/review/manual-reading/observer/publication support and
final-write tails remain unknown, not zero. Prior B04/B08 acquisition and their
earlier costs remain in their records; this new bill does not erase them.

The retained current artifact graph verifies3,022 files /420,373,462 logical bytes,
including native arrays/decisions, bank rows, model branches, current catalogs,
reading and config. Original summary.json is5,519,917B; its exact SHA256 and
the full reading digest/size are stored in result.json. These bulk JSONs and raw files stay unmodified in the
one canonical local_linux output. During accepted execution, the reviewed
projection compactor deleted640 redundant segment files after publishing and
verifying their retained model-derived references, reclaiming48,902,144net
allocated bytes. Exact targets and episode-level allocation changes remain in
summary.json:cleanup; all replacement catalogs and current references verified.

#### Resolved reading and next investment boundary

I reread the complete original C selection review in
[the dated Root review](../../archive/2026-10-03/RESEARCH-four-dm-selection.md#four-dm-c-independent-review-20261003).
Its explicit positive branch—retain A_E if it improves on A2 and G_E—covers this
unchanged design and the present disposition. The scope, clocks, comparators,
outcome rule and uncertainty interpretation did not change, so no second
confirmation, pilot, mechanism gate or review ceremony is added. Its objection
to the limited marginal knowledge of another renewal law in a small known-model
host is still retained, along with MATERIAL_DISSENT:no for the accepted purchase.

Current published main399cdcde1c8d71f816960410673fd3712cc3203f was consulted at
this boundary. Topics3/5's complete evolving-program and opportunity/commitment
distinctions now gain direct timing evidence; topic8's nonnested-policy-set caution
still applies. The new request-scheduling B05 evidence separately retains a useful
ordinary tail-control package despite adverse finite learning, reinforcing why
capability, adoption and investment must be kept separate. It is a different
task, not another replication of A_E or a reason to pool the two studies.

The main judgment changes from an untested timing opportunity to a retained
anticipatory timing capability with measured primary gains, nearly unchanged
worker CPU and explicit individual/quality costs. **The fixed purchase is
complete; the temporal-cooperation question and responsibility remain open.**
I recommend carrying A_E forward in Root's next capability-development allocation,
beside A2 and the cheaper greedy programs, rather than treating mechanism limits
as a rejection or automatically buying a clock grid.

One concrete, unselected continuation is a lawful initial full-program choice
between the existing A2 and A_E clocks, preserving exactly two physical
opportunities and fresh actual second replanning. It would test whether added
planning can preserve the early gains while retaining useful fixed120 programs;
it would not prove optimal timing or require a learner. A complete A2/A_E/chooser
comparison on16 fresh worlds plus one audit per arm would cost51H500 missions /
25,500native steps /0fits. Charging both planning programs to the chooser gives
conservative worker-plus-full-reader ceilings of1,209,632,416state/mask requests
and4,526,080model ticks; the observed A2/A_E episode-cost scale is about4.77CPUh
before additional implementation, audit overhead and unknown new-world demand.
This is a proposal, not execution authority or a hidden post-hoc chooser result.
Its strongest alternative is simply reusing A_E: the two laws differ favorably
for A2 in only two of these16 worlds, while a chooser could approximately double
its own planning search. That additional marginal knowledge/cost should compete
with Root's other substantive questions before purchase. An unchanged replication
would instead estimate breadth/concentration; it is not a prerequisite to using
or developing the observed capability. No new effect is selected here, and the
current result changes neither A's frozen40/120 study nor another lead's work.


<a id="b01-final-cleanup"></a>
### Final publication and measured cleanup — 2026-10-03

The complete scientific reading and compact result/config/terminal records were
published first at 24b7a97064a6b28656a7b486c1cee417ac670434. The canonical output
remains `/home/fires/hmasd-wsl/runs/uav_planning_opportunity_timing/b01_complete_timing_a02`
on configured `local_linux`, outside the accepted source snapshot. Its current
3,022-file artifact graph had already been verified by size/SHA256; native arrays,
full original summary/reading, source bindings, all adverse outcomes and the
terminal claim/manifest/exit evidence are retained. No raw-data copy was created.
The published policy, exact reuse, independent reader, tests and bound inputs
remain useful ordinary capability and verification code; there is no unused
new direction code or cache to remove. Live accepted operations in other
directions and their source trees were left alone.

After worker/supervisor exit, full reading and consumption of every observer
event, the exact-target native snapshot collector rechecked terminal witnesses,
consistent records, durable source reachability and live process references.
The initial unprivileged preview could not inspect own process 454's `/proc/454/cwd`
(`Permission denied`). The supported `--sudo-process-scan` read-only scan resolved
that inspection limitation; preview and apply both admitted the exact snapshot.
The final apply exited 0, reported `eligible:true`/`removed:true`, and found source
4481c6240dc8266c2a6f13070cc1e8762328e614 reachable from `refs/heads/main`.
There is **no remaining cleanup tool blocker**.

Actual deleted targets and allocated bytes were:

- `.git/hmasd-launch-sources/3461f799792c4200ae6f20e13d45c4c8`:
  1,831,297,024 B, removed by `scripts/hmasd_snapshot_gc.py`.
- Its linked Git administration directory
  `.git/worktrees/3461f799792c4200ae6f20e13d45c4c8`: 3,776,512 B, removed by that tool.
- `temp/directions/uav_planning_opportunity_timing/b01_complete_timing_a02/launch-response.json`,
  `launch-timing.txt`, and `wait-request.json`, followed by the empty attempt and
  direction scratch directories: 20,480 B combined. These were duplicate launch/wait
  request material and the already-recorded launcher timing, not unique evidence.

All listed targets are actually absent. Deletion reclaimed 1,835,094,016 allocated
bytes before the final record edits. The measured scope includes these targets,
the retained canonical run, this NOTES and the shared RESEARCH file; it fell
from 2,276,843,520 to 441,757,696 allocated bytes after the closure prose,
for **1,835,085,824 net allocated bytes reclaimed**. This is the scoped
working-tree/linked-metadata reduction, not a Git-object repack or a claim about
host-wide free capacity while other studies run. The canonical run remains
441,053,184 allocated bytes. The separately recorded in-run removal of 640 redundant
segments reclaimed 48,902,144 B; A01's earlier 8,192 B cleanup is also separate and is
not counted twice here. No unneeded target remains in this closure scope.

Fresh published main 24b7a97064a6b28656a7b486c1cee417ac670434 was fetched before the
shared update. The direction standing is now reserve, retaining A_E's gain and
an open temporal-cooperation question with no selected further purchase. Directly
affected background topics 3/5 now state the complete-package timing positive,
the greedy adverse comparison, individual limitations and the observed boundary
of the first-mover exclusion explanation. Routing keeps the same lead. The next
choice remains Root's capability-development allocation described above; there
is no running producer, pending result/advice, automatic retry or invented owner
approval dependency. This closes the assigned complete-read/publication boundary.


<a id="b02-source-assignment-20261003"></a>
## 2026-10-03 — B02 source-only construction: repeated two-opportunity anticipation

Root accepted B01's full reading/publication/cleanup and assigned this same DM a
new **source-only** construction boundary. The current task may read literature,
source and existing results, do contract arithmetic and publish this notebook /
owned standing. It does not authorize production implementation, world generation,
controller/scorer/model/RF/native/branch execution, fits, real or synthetic launch
smokes, or a new accepted operation. B01 and A/D's accepted work remain unchanged.
One actual completed contract will go to Root's existing independent selection
critic before Root selects any complete effect purchase; no second sketch review
or DM selection-review pass is added. Question ownership continues across this
boundary. The proposal below is coauthorship, not independent scientific review.

Current published main `be641b1c0b2d5c79d015dfbf424bc41ed471974f` was freshly fetched
and relevant topics3/5/8 read. Its positive complete A_E capability motivates a
reusable rolling program; its individual/quality adverses remain mandatory outputs;
the opportunity/commitment/eligibility distinctions fix event ordering; and its
nonnested-policy-set caution prevents turning optional future opportunities into
a native monotonic-improvement theorem. The detailed source-checked contract and
DM response follow below after construction.

<a id="b02-oracle-original-20261003"></a>
### Complete original Oracle proposal, received by native message

Author: `/root/four_dm_allocation_oracle`, the original proposal coauthor, **not
an independent Reviewer**. Delivered once at Root's request. The following body
is retained verbatim, including its root-relative Markdown links and estimates;
those links/estimates are part of the original advice, not newly verified claims.
No assent or empirical evidence is inferred from the advice.

<!-- B02_ORACLE_ORIGINAL_BEGIN -->
我会选择 **“将 A_E 发展为四次机会、两步预见的滚动合作规划”**，由同一 C DM 完成一次完整比较。暂不选择 A2/A_E 双程序 chooser。

这是构造建议，不是独立科学审查，也不构成启动授权。本次只读了合同、结果、源码和文献，并核算成本；没有生成世界、调用模型或环境、训练、编辑文件或改变 A/D 的已接受操作。

**1. 新结果支持什么，以及为什么继续。**

我核对了 source `4481c624…` 对应的 [完整结果](runs/uav_planning_opportunity_timing/b01_complete_timing_a02/result.json) 和 [完整合同、判读](docs/research/candidates/uav_planning_opportunity_timing/NOTES.md#b01-complete-reading)。

值得发展的对象已经很具体：A_E 能为后续伙伴的移动改变首个物理承诺；七个改变首个承诺的世界全部提高 J 和服务，另九个完整程序字节相同。它在新面板上又优于有用的 A2，worker 成本几乎不变。世界 29523010 的两成员组合、29523009 的“先停留、再移动”表明，可复用资产包括行动顺序和有价值的等待。

这不消除质量损失、两例任务 J 损失和严重个体服务损失。尤其不能用旧面板的“第一成员不能再次移动”解释本面板的不利结果：此次 A2 实际也没有同成员二次移动。继续投入的理由是已示范的能力可以构成更长的控制程序，不需要先完成这一归因。

我建议把 C 的问题扩展为：**已经有效的“两次机会间的预见”，能否在实际状态不断变化时反复使用，形成有用的多阶段合作程序？其增量是否值得相对于同机会数贪心控制的计算成本？**

**2. 选择的完整程序。**

保留 N8、50 个静态用户、H500、原生奖励、133 维 FP32 报告及全部原有物理控制规则。改变的是实际规划机会数，明确从二次增至四次；这不是“仅改时钟”的后续归因实验。

| 程序 | 实际机会 | 每次选择 |
|---|---:|---|
| A2 | 2 | 原始固定 40/120 预见程序 |
| A_E | 2 | 已得到正面结果的完成后第二机会程序 |
| G_E4 | 4 | 每次只评价当前承诺及此后完整 C/E 延续 |
| A_E4 | 4 | 前三次各预见当前和下一次机会；第四次做普通完整延续选择 |

A_E4 的“四次”指实际机会数，**搜索深度仍为两次机会**，不做四层穷举。

共同规则：

- 首次在 t40。每次停留后，下一次在 `t+10`；每次启动承诺后，下一次在 `arrival_t+10`。
- 第四次之后恢复普通 C/E，直到完整任务结束。四次机会均被消费，停留也不补发机会。
- 每次重新从自身合法报告、实际私有历史和进入 mask 构造原菜单。保持全部候选、严格 stay 比较、原始 ties 和浮点次序。
- A_E4 每次模型只保留“当前候选→其完成对应的下一次普通选择→完整 C/E 尾部”；实际只执行当前选择，下次再算。
- 到达、过期替换、普通 C/E 与选择的先后次序保持 C 原合同。不得插入 remuting 例外。

第四次机会最早 t70、最晚 t190，最后一次承诺最晚 t230 到达，因此无需引入临近 H500 的截断规则。四次是这次购买的有限范围，不声称最优次数，也不以结果决定是否追加第五次。

这个设计有一个有用的源级身份：**A_E4 第一次搜索就是原 A_E 的第一次搜索，二者必须在实际第二机会之前完全一致。** 后继真正改变的是此后能否继续利用预见，而非重新修饰已经成功的第一次选择。

**3. 为什么优先于 chooser，以及最强替代。**

A2/A_E chooser 合法，也可能有用。但它的新增能力主要是为同一状态计算两个已知完整程序，再挑预测较好的一个。当前只有 2/16 世界 A2 的 J 更高，chooser 自身搜索约翻倍；其完整三臂购买约 4.77 CPUh。它主要回答这两个程序之间的条件选择值多少钱。

四机会方案多买约 1.8 CPUh 的中心估算，却回答更大的使用问题：**两步合作能否成为反复执行的控制单元，以及重复机会能否让更便宜的贪心程序充分发挥作用。** G_E4 是关键控制：如果它已经达到或超过 A_E4，就应优先保留这个简单能力，不能把“四次比两次好”写成预见胜利。

最强“不新增”替代是直接保留并使用 A_E，等 A/D 完整结果。这是合理选择，尤其当支持工程时间紧张时。我的购买倾向来自这次明确的能力扩展，并非四个 DM 的数量要求。A 的固定时钟学习、D 的 S7 选择和 B 的请求排程后继均不成为本研究的前置依赖；也不能把 A 学到的排序器直接移植到新时间分布而不另行验证。

还有一项应保留的实质限制：在理想的精确状态模型下，增加可拒绝的规划机会具有普通 rollout 改进的理由。因此，这不是发现一种新的规划原理。实际增益有多少、需要多少额外工作、是否转移服务损失，仍需完整运行；当前 FP32 报告、分支解码和重新选择也不允许直接宣称原生逐世界单调改善。

**4. 一次完整购买，以及会改变选择的结果。**

使用同一生成律的 **16 个未曝光共同世界**，四臂完整 H500；另一个预先冻结的工程世界各臂一次完整 audit：

- **68 missions，34,000 native transitions，0 fits、0 updates、0 新训练标签。**
- 合计 204 次实际计划机会，至多 204 次启动承诺。
- 全部未压缩独立 reader；34,068 个 native snapshot 重构、34,000 个运动/奖励检查。
- 新 RNG 地址在 C 的合同中冻结。本次没有生成或筛选世界。

主比较为 **A_E4−A_E 的完整任务 J**；决定性同权控制为 **A_E4−G_E4**。同时保留 G_E4−A_E、两种四机会程序对 A2 的完整比较，以及 A_E−A2 的新面板结果。按世界报告服务、质量、路径、个体 served ticks、最长间隙及删失、never-served 的新增与救回，不能用共同前缀造成的相同 team p05 代替个体读取。

预先采用完整配对世界均值、分布、全部 adverse worlds、贡献集中度和固定的配对 bootstrap。16 世界仍是有限探索，不以某个显著性结果决定加样本。

实际分支：

- **A_E4 优于 A_E，也优于 G_E4：** 保留可反复使用的预见能力，报告完整增量成本。
- **G_E4 已达到或超过 A_E4，并改善 A_E：** 保留较便宜的多机会控制；不声称额外预见必要。
- **A_E4 优于 G_E4，但没有改善 A_E/A2：** 预见在四机会合同内有条件价值，却没有证明扩展值得采用。
- **额外机会基本停留、程序同一，或总体不利：** 结束这一固定四机会配方，保留原 A_E 的正面能力；不能据此关闭整个时序合作问题。
- **团队增益伴随更严重个体损失：** 保留条件能力与代价，不升级为普遍服务默认，也不在结果后悄改奖励。

A_E4 前两次的模型尾部没有预见全部未来四次选择，因此 forecast/native 比较应止于下一次实际重新选择。第三次两步模型与第四次单步模型才覆盖真实剩余机会结构。把每个早期 forecast 都要求匹配完整实际尾部，会错误地把滚动规划本身判成缺陷。

**5. 源码可行性及真正的工程工作。**

现有实现已具备关键构件：

- [TimingProgram](experiments/candidates/uav_planning_opportunity_timing/b01/controller.py) 的 `_ordinary_selection`、`_anticipated_selection`、`_install`。
- [segment](experiments/candidates/uav_planning_opportunity_timing/b01/segment.py) 的显式 `start_t/end_t`、实际历史副本及复用屏障。
- [OptionProgram / validate_plan](experiments/candidates/uav_fleet_transmission/b04/surrogate.py) 已支持相对于显式起点执行承诺，并不限于 t40 的命令索引。

但它**不是改一个机会数配置**即可完成：

- B01 的 `STARTS`、`second_clock` 和 anticipated selector 写死初始 t40，需在 C 自有后继中参数化。
- 需要实际机会序列、机会编号和分支级身份；旧 plan 即使选择 stay 也必须过期。
- [reader](experiments/candidates/uav_planning_opportunity_timing/b01/reader.py) 写死两个时刻及完整尾部比较；必须随上述 forecast 边界修改。
- 成本、目录投影和 segment certificates 要覆盖重复的两步搜索，避免证据身份碰撞或漏计。

采用 C 自有的有限适配即可。必要的内部数值循环提取应保留 B01 外部合同和冻结来源，不修改 fleet/parent 的原始接口，也不靠全局 monkeypatch 或移时间戳复用固定 40/120 程序。工程审核重点是历史隔离、绝对 phase、机会过期、复用屏障和完整计费。真实物理检查只放在已计入的四个 audit 中。

**6. 全价。**

以下是从现有菜单和 scorer 算式推导的保守上限，不是新增测量。每次最多 stay 加七个成员 champion；全 reader 再完整计算一次。

| 每个完整 mission 的 worker 上限 | state/mask 请求 | logical model ticks | stationary banks |
|---|---:|---:|---:|
| A2 | 8,351,156 | 31,040 | 10 |
| A_E | 9,437,556 | 35,520 | 10 |
| G_E4 | 3,855,642 | 14,240 | 4 |
| A_E4 | 25,621,722 | 97,040 | 28 |

68 missions 的 worker 总上限为：

- **803,523,292 请求；3,023,280 model ticks。**
- **884 banks、618,800 candidate rows、24,752,000 candidate transit ticks。**
- **7,072 个完整 model branch artifacts。**

worker 加完整 reader 合计 **1,607,046,584 请求、6,046,560 model ticks、1,768 banks、1,237,600 rows、49,504,000 candidate transit ticks**；另加前述 native reconstruction、序列化、哈希和归约。候选 transit ticks 与 model ticks 分列，不能把前者漏掉。实际复用可以降低实际计算，不能抹掉 reader 或逻辑工作。

用 C 已测各臂成本按新搜索负担外推，中心估算约 **6.54 CPUh**；我会按 **6–12 CPUh** 看待当前不确定价格。沿用旧未压缩请求成本尺度则约 **17.79 CPUh**，这是保守规划尺度，不是机器无关的耗时上限。菜单大小、重复状态比例和并发负载均未知，尤其不能把 B01 的复用比例直接承诺给新增机会。

另价 **8–14 小时主动支持工作**，覆盖构造、实现、检查、工程审核、完整科学读取、发表及清理；它不计为零。预计单份 canonical evidence **1–2.5 GiB**，launcher snapshot 约 **1.6–2 GiB**，另留 **1–2 GiB** 临时空间，进程 RSS 估 **1–2 GiB**。这些只是价格估计，实际节点仍须按配置正式准入，不插入健康探针，也不移动 A/D 操作。

具体文献桥只需已有的 **VS-0005**：其 PDF 第 2–3 页区分 initiation、intra-option policy 和 termination，支持把这里的机会、承诺执行和后续选择分开定义；不支持四次一定优于两次或任何 N8 学习结论。来源为 `/home/fires/projects/Inst-sci/papers/MyLib/json/VS-0005.json` 与相应 `pdf/VS-0005.pdf`。三库已查；没有新颖性声明，也不把额外阅读设成投入门。

我的实质保留意见是：这仍是在静态、已知模型、路径未计入奖励的 N8 宿主中发展普通规划能力。若 Root 当前真正优先的是未知动力学、学习迁移或有物理预算的应用，应直接选择那个更大的合同，不能把本研究包装成替代品。但在“把已经有效的时序合作继续发展为可执行能力”这个目标下，我会优先购买上述完整四臂研究，而不是双程序 chooser。
<!-- B02_ORACLE_ORIGINAL_END -->


<a id="b02-source-contract-20261003"></a>
### B02 executable source contract and DM construction response — 2026-10-03

**Boundary: source-only, complete contract for Root's single new-investment review;
no effect or production implementation selected.** The original Oracle body above
is11,649 UTF-8 bytes (without delimiters/final newline), SHA256
`45aef6db27c7a8ffa4ba2a25d65c708651d402dc24d24d38165ea8d10a71869e`.
I read it completely. It proposes the study; it does not discharge independent
review. This entry is my source-checked construction and response, not an adviser
consensus or a newly observed benefit.

#### Scientific object, prediction and strongest alternatives

The intended contribution is a useful finite ordinary-control program and
empirical understanding of repeated temporal cooperation on this N8 host. The
question is whether the demonstrated A_E two-opportunity anticipation can be
reapplied to changing actual histories, improving complete service/J enough to
retain the additional decision work, and whether anticipation adds value over
competent greedy control with the same four opportunities. There is no learning
method, new fit, optimizer update, training target or acquired skill in this study.

B01's complete A_E−A2 J+.004137129 / service+.37675 at1.01065 times worker CPU
supports developing A_E itself. A_E−G_E changed the first commitment in seven
worlds, all seven gained J/service, and nine native programs were identical.
Useful waiting and member sequencing are therefore concrete existing capabilities,
not only baselines to defeat. Their original source/reading is pinned at
`4481c6240dc8266c2a6f13070cc1e8762328e614` /
`24b7a97064a6b28656a7b486c1cee417ac670434`; all55 bound source files still match the
published A02 config byte digests at this construction boundary. The original
compact result has SHA256
`d42c2c46fc6d8a6be4bd98be02fb6bfd3bbd27fd72fc05503e4dc04b7d3f6e0d`.

The constructive prediction is that actual third/fourth choices, with fresh
history and repeated two-opportunity anticipation, can assemble further useful
member/wait sequences and raise complete J/service relative to A_E. The matched
G_E4 comparison tests whether the extra physical access already gives a cheaper
ordinary program the same usefulness. Changes in choices, arrivals, transmission,
remuting, user service and end-to-end cost are the proposed intermediate/native
observations; changed choices alone do not validate the prediction.

The strongest no-new-study alternative is to use the retained A_E. A2 remains
another demonstrated ordinary capability and wins J in two of B01's16 worlds.
The previously priced lawful A2/A_E chooser would instead test selecting between
two complete clocks (about4.77CPUh before engineering/unknown demand); it remains
unselected. The rolling proposal asks a larger capability question at about6.54
heuristic CPUh plus8–14 support hours. That extra knowledge, not an available DM
slot or a remaining old budget, is the reason to consider it. Waiting for A/D is
not a scientific prerequisite; their fixed40/120 learning and accepted S7 work
remain unchanged and are not sources of scorer weights or new labels here.

My substantive qualification to the proposal is its scope: four early selections
are a finite multi-stage program, not indefinite sustained cooperation. The
fourth arrives by230, leaving ordinary C/E for the rest of H500. This is still a
static, known-model, centrally coordinated team with shared interference and
capacity consequences. It does not answer unknown-dynamics adaptation,
decentralized partner learning or physical deployment with a travel budget.
B01's quality decline, concentrated mean gain, two primary J losses and severe
individual losses remain reasons to read those outcomes prospectively, not to
reject the existing gain or require another mechanism screen.

The Oracle's ideal-model rollout intuition is useful but conditional. For a
complete exact state/model and faithful remaining-time semantics, ordinary
selection can choose its C-only stay continuation; anticipating such a future
selection can improve the modeled current value. This is not a new planning
principle. The implemented actor sees FP32 reports, keeps a separate estimated
history, and decodes an inner report before applying its chosen plan to unrounded
outer coordinates. Those distinctions, changed visited states and repeated
replanning prevent asserting native per-world improvement. Neither repeated
anticipation nor four opportunities is guaranteed to dominate G_E4 or A_E here.
Service for each individual and quality would not be monotone even from a J
improvement argument. No proof or positive toy is made an admission gate.

Relevant published background is main `be641b1c0b2d5c79d015dfbf424bc41ed471974f`,
[topic3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构),
[topic5](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据) and
[topic8](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验).
They respectively require retaining the demonstrated complete ordinary capability,
separating selection/commitment/eligibility, and avoiding an optimal-policy-set
claim about these implemented programs. The directly read VS-0005 PDFpp2–3 /
printed13392–13393 bridge from B01 remains applicable: initiation, intra-option
policy and termination clarify the objects being composed. Original sources are
`/home/fires/projects/Inst-sci/papers/MyLib/json/VS-0005.json` and
`/home/fires/projects/Inst-sci/papers/MyLib/pdf/VS-0005.pdf`. Its single-agent learned
extension does not supply the fleet's shared-mask coupling or evidence that four
is better. No novelty claim or additional literature prerequisite is added.

#### Fixed host, information, menu and numerical law

All four arms use the unchanged B01 native law: N8,50 static uniform users,H500,
free-space radio,0dB service threshold,capacity10 per active UAV, nonempty mask,
and silent members remaining physical. Native J is
`.7*(served/50)+.3*quality−height_penalty`; scalar reward keeps its existing
`J/8` scaling. There is no battery, travel price, collision law, latency penalty,
new observation or time spent waiting for model computation in the simulated task.
CPU/wall price is recorded separately from these native outcomes.

The actor begins with mask255, a fresh private OrdinaryController, zero FP32
issued commands and next_t0. It receives only its actual entering mask, lawful
actual controller history and the133-vector FP32 CountAdapter report every10
ticks; other ticks receiveNone. Reports contain the original normalized fleet
positions/validity, static public users and absolute t/500. The selector cannot
read world ID, unrounded native coordinates, native local-observation internals,
future trajectories, another arm's history or old result labels. Model-generated
physical states are internal forecasts, never privileged native observations.

Keep the source's FP32 command multiplication before addition to FP64 positions:
`positions + (commands * 30) * 1.0`, then componentwise clipping to
x/y[0,1000],z[50,150]. Do not cast commands to FP64 before multiplying. C makes
one rotating coordinate pass, member order `(t+j)%8`, evaluating all27
lexicographically ordered ternary commands/member. Its rank is immediate J,
served, less whole-team movement, retain entering command, lower command index.
At a report boundary ordinary E follows that motion choice, scores all255 masks
at its predicted moved geometry, and ranks J,served,retain entering mask,lower
mask integer. Issued command bits survive clipping. No phase reset or controller
reinitialization occurs at any actual or modeled opportunity.

At every actual and hypothetical selection construct the original full stationary
bank from that context's report and entering mask. Enumerate ascending muted
members and all100 sites/member:50 original user rows followed by50 anchor-plus-
nine-nearest centroids, retaining duplicate rows and stable distance/row ties.
Projection searches k=−34…34 with the original distance, clipped coordinate,
absolute-k,k tie order. Descent and horizontal counts yield
`L=10*max(1,ceil(unrounded_duration/10))`, L∈{10,20,30,40}. This is the commanded
movement budget, including zero-path commitments, not detected geometric arrival.

Each candidate freezes every other member's commands at zero and moves only its
currently muted member for L ticks under the entering mask. Its stationary price
is its per-tick transit J/service plus `(500−t−L)` times its best destination-mask
J/service. Destination masks are all128 containing that member, in ascending
integer order; rank J,served,lower mask without an old-mask preference. The
per-member champion rank is total J,total served,less committed physical path,
shorter duration,lower member,lower site. Retain each champion even when its
stationary prediction is nonpositive relative to stay. There is no additional
shortlist, top-k approximation, learned scorer or four-layer sequence search.

The planning menu is stay followed by these zero-to-seven champions in member
order. Ordinary complete-continuation ranking uses total J,total served,less
current commitment path,shorter L,lower member/site. For stay, path/duration/member/
site tie coordinates are all0 exactly as in the frozen rank. After ranking, choose
stay whenever the best total J is **≤** that context's stay branch J, even if
served/ties otherwise prefer an option. No epsilon or outcome-fitted tolerance
is introduced. Stationary aliases, relative-command aliases and complete modeled
execution aliases remain distinct recorded notions; none is deduplicated out of
the charged menu. A stay-only/all-alias/unhelpful world remains in the panel.

These laws were checked in current source, not executed:
`uav_fleet_transmission/control.py` (C/E,scorer,report,motion),
`b02/option.py` (sites,projection,transit,128-mask arrival),
`b02/controller.py` (`_forced`/ordinary ordering),
`b03/controller.py` (`continuation_rank`), `b03/option.py` (champion/identity),
`b04/surrogate.py` (`OptionProgram`/plan validation/ordered concatenation), and
this direction's `b01/{option,controller,segment,study,reader,evidence,inputs,meter}.py`.
B01's55-file config binds the transitive native/scoring implementation; future B02
inputs must bind those inherited identities plus every actual B02 source/input,
without importing a changed A/D algorithm or substituting current filenames for
frozen contents.

#### Actual opportunity sequence and exact event order

| Arm | Actual choices | Selector law |
| --- | ---: | --- |
| A2 |40,120|Unchanged B01 A2, including its fixed120 anticipated first program and fresh ordinary second choice.|
| A_E |40,then50 after stay or first arrival+10|Unchanged complete B01 A_E.|
| G_E4 |Four, starting40|Ordinary complete C/E-continuation selection at each actual opportunity.|
| A_E4 |Four, starting40|Anticipate current plus one ordinary future choice at opportunities1–3; ordinary selection at4.|

For either four-opportunity arm, let actual ordinal k start at1, t1=40. Selection
occurs once, before that tick's ordinary C/E action. Install the selected plan
with `start_t=tk`, even when it declines, replacing any old plan while preserving
the same live OrdinaryController. Consume the opportunity unconditionally. If
k<4, set `t{k+1}=tk+10` after stay, otherwise `tk+L+10`; after k4 there is no fifth
schedule. There is no retry on stay, arrival failure, poor score, empty menu or
unused opportunity. All four opportunities fit this host: t2∈[50,90],t3∈[60,140],
t4∈[70,190], all multiples of10; final commanded arrival is at most230.

An initiated plan at tk executes commands indexed0…L−1 on ticks tk…tk+L−1, with
old mask held. At `arrival_t=tk+L`, consume that actual fresh report, force all
commands to zero, select a fresh128-mask member-containing arrival mask, and
execute that tick. Ordinary C resumes at arrival+1. Through arrival+9 it retains
that mask because no intervening E boundary exists. At arrival+10 the next
selection sees the actual report/history and entering mask **before** C/E can
remute anyone. Consequently the immediately preceding mover is excluded from
that next menu. Do not insert remuting, early geometric arrival, cancellation,
a new timeout rule or a plan-completion call that advances the actual controller.

If the previous choice was stay, ordinary C/E executes on that selection tick;
its E can change the entering mask for the next opportunity10 ticks later.
A nonadjacent earlier mover may therefore become eligible again. Another member's
later arrival mask may also remute it. The rule excludes the immediately previous
initiated mover at the following opportunity; it does **not** ban repeated members
through the complete four-stage program. Preserve zero displacement with L10:
freezing teammates and changing the arrival mask can differ from ordinary stay.

The last ordinary/initiated plan executes under these same rules, then C/E runs
through499. Terminal is exactly after tick499. No horizon shortening or suffix
reset is introduced to accommodate the extra opportunities. Menus/segments need
start support40…190 by10; the old B01 allow-list40…90 and hardcoded `second_clock`
are not reused at unsupported clocks by modifying module globals or translating
absolute timestamps.

#### Two-layer forecast and its lawful history boundary

Write D(t,h,r,m) for the ordinary selector defined above: build one bank and
simulate every stay/champion from t through499 under OptionProgram(C), with that
one forced commitment followed only by C/E. It returns the strict-stay-selected
plan plus every ordered branch and bank. It does not call another planner.

For A_E4 at actual k≤3,t=tk, the two-layer operation is:

1. Build the same actual-context bank. For each current candidate a, calculate
   u=t+10 for stay or u=t+L(a)+10 for an initiated commitment.
2. Copy the actual history and model a over `[t,u)`. Its physical state starts
   from the decoded lawful FP32 report, with the original issued commands/users
   and absolute next_t; the copied controller consumes that report at t.
3. Preserve unrounded FP64 outer terminal positions x_u. Encode the original
   CountAdapter FP32 report at absolute u/500 with static public user bits intact.
   Call **ordinary D**, not A_E4, on a separate copy of the terminal controller,
   the decoded inner report and entering terminal mask. This inner simulation
   starts at report-decoded physical positions as in B01.
4. Execute the inner selected plan on the saved unrounded x_u, with the original
   outer terminal history and the same inner report, over `[u,500)` under C/E
   after that plan. Never replace x_u with an inner branch's decoded positions or
   let inner selection/sinks mutate the outer branch or actual history.
5. Concatenate prefix and selected suffix and accumulate J/service/path in the
   original tick order. Annotate the modeled future selection at index u−t.
   Rank complete outer programs by the same continuation rank and strict J stay
   rule. The stay-first outer branch includes its own future ordinary opportunity.
6. Install and execute **only the current** selected plan on the actual controller.
   At the actual next opportunity rebuild everything from actual history. A
   previously modeled inner plan is evidence, never a cached actual action.

Thus search depth is always two selections, even when three or four actual
opportunities remain. Each prefix, inner branch and selected outer suffix owns
its history copy, report, physical state and fresh local segment cache. All
reports retain absolute phase and denominator500. A2/A_E keep their original
scientific laws. A_E4's first search must equal A_E's first search at the same
lawful state; borrowing that already-bound first selector is preferable to
recreating it. Their actual first plan, t2 and native arrays through the input
snapshot at t2 must be bitwise equal; actions/history outputs stop at t2−1.
All four arms share native snapshots0…40 and actions/history outputs0…39.
These identities can be checked from the four already paid missions/forecasts;
they authorize no extra reference-world, model or controller call.

Different evidence namespace prefixes may distinguish arm/opportunity IDs. For
first-search identity compare the same scientific payloads, ordered plans, bank
rows and branches after only the documented arm/ordinal ID-prefix mapping; do not
strip scientific fields, times, score bytes or divergent decisions. G_E4 uses
ordinary first ranking, but absent G_E/G2 arms receive no unbought native replay.
Equal first choices in A_E4/G_E4 no longer imply complete-program equality because
the later selector laws differ. Any whole-program equality must be read from saved
arrays rather than inherited from B01's two-opportunity implication.

#### Reuse, source and evidence identity

Worker transition reuse remains exact and private to a single modeled segment.
Its little-endian key is phase t%40,entering mask,N8,FP64 physical positions,
estimated controller positions/users,FP32 issued commands and original public user
bits. Phase40 is lcm(8,10), preserving rotating C and report/E cadence. The model
segment runs OptionProgram(C), not a four-opportunity actor with hidden future
scheduler state. Its only commitment is explicit in that segment's entry; reuse
starts strictly after its start/arrival barrier, never inside movement or arrival.
The cache is fresh for each prefix, inner branch, selected suffix and actual
replan. Do not reuse across arms/worlds/opportunities or treat a prior modeled
future branch as an actual-history continuation.

Absolute time/reports and history.next_t advance every tick, including a reused
tick, and the original ordered reductions and issued command bits remain intact.
The early prefix has only9 eligible post-barrier ticks, too short to repeat a
phase40 key; no early-prefix saving is forecast. Long hypothetical C/E tails may
recur even across the timestamp where a real rolling controller would have made
another decision: that later decision is absent from this explicitly labeled
model law. This does not allow cache reuse across a real selector boundary.
B08's old zero-query reader cannot certify these new worlds.

Use a canonical identity containing phase/audit-or-result,world,arm,actual ordinal,
actual start clock,outer candidate's relative identity and hypothetical next
clock,inner candidate,segment kind/start/end. Physical identity keeps the original
member/duration/command-byte definition; temporal/execution identity separately
retains timestamps, positions,masks and full scientific hashes. Raw branch IDs
cannot collide when different ordinals happen to contain the same relative plan.
Keep all full branch arrays/ordered decisions, complete stationary rows, source
and config bindings, entry/terminal history envelopes and every recurrence source/
barrier certificate, including unselected and adverse model alternatives.

The existing evidence store may share an ordinary segment's payload with its
identical branch. After the **full** reader verifies prefix/suffix projection,
replace redundant segment payload references with their retained outer-branch
slices, publish that replacement catalog atomically, verify digest/bit identity,
then delete only those redundant files. Retain the deletion/allocated-byte ledger.
Changing ordinal ID paths must preserve this parent/slice mapping, the prediction
annotation at u−t, ordered endpoint arrays and report rows. Duplicate IDs, changed
bytes, partial catalogs or incomplete model/native traces are technical failure,
not an opportunity to rerun the same worker.

Publish exact new source, configuration and17 bound initial arrays/hashes on main
before any selected result execution. The actor receives no old A02 outputs;
source/data identity is verification, not policy information. Preserve a single
canonical output on the admitted node, compact Git reading/config/terminal facts,
and the original accepted status/manifest/exit identity. No accepted source tree
or output from A/D is touched. Native-child observation uses the same accepted
handle and deterministic observer, with active native waits through the complete
reading; no replacement launch or App wake assumption.

#### Fixed fresh population and complete reading

Freeze result IDs **29524000…29524015**, audit ID **29524900**, and bootstrap seed
**29524991**. The new stream address is
`SeedSequence([261003,74,world_id,stream,*suffix]).generate_state(1,uint32)[0]`:
stream1 supplies the user RandomState seed, stream2 the UAV seed, and stream3 with
suffix8 the runtime seed. Preserve member-major draws:50 successive pairs of
uniform x/y∈[0,1000], then a separate RNG's8 successive x/y/z triples with
z∈[50,150]. The address is complete; no seed state or initial world has been
materialized in this source task. A targeted search of current generator/NOTES/
config paths found no use of these addresses; that is a scoped collision check,
not a claim about unrecorded work or a new-world result.

Proposed arm order is `(A2,A_E,G_E4,A_E4)`. First run the separate audit world once
per arm in that order; then result worlds ascending, rotating the arm order left
by result-world index modulo4. For each four-arm world group retain all worker
missions, read all four fully, verify cross-arm prefixes and lossless references,
then proceed. A positive audit outcome or an interesting alias cannot change
this order, panel or arm set. No cross-arm world/controller/bank cache is shared.
All16 result worlds enter every paired contrast; the audit is excluded from all
scientific means/bootstrap and is not a seventeenth inference unit.

The full uncompressed reader reconstructs all actual policy calls/private
histories, all stationary rows, every model branch and every segment/reuse source
against freshly computed no-reuse arrays. Require bitwise scientific model/worker
and ordered-decision equality under the frozen numerical law. Native saved-array
reconstruction independently verifies all501 snapshots/mission, all500 motions/
rewards, FP32 public reports, user and peer radio, greedy assignments, local views,
visibility counts, capacity identity and J/8 reward scaling. Actual clocks,
consumption of all opportunities, plan expiry, report cadence, source hashes,
strict stay, branch completeness and the immediate-mover exclusion are checked
for every mission, not only favorable or activated cases.

Forecast/native correspondence is a separate empirical comparison with these
prospectively fixed valid horizons:

| Arm / actual opportunity | Forecast comparison interval |
| --- | --- |
| A2 and A_E, both choices |Their unchanged complete remaining program, from that choice through499, including fresh ordinary second replanning.|
| G_E4, opportunities1–3 |From tk through `t{k+1}−1`; its current C-only forecast omits the next actual choice.|
| G_E4, opportunity4 |From t4 through499.|
| A_E4, opportunities1–2 |From tk through `t{k+1}−1`; the modeled next **ordinary** choice does not describe the actual next anticipatory choice or later rolling decisions.|
| A_E4, opportunity3 |From t3 through499: its modeled ordinary fourth choice has the remaining actual selector structure; retain fresh-replan/quantization differences.|
| A_E4, opportunity4 |From t4 through499.|

Also retain the immediate next-choice prefix comparison for opportunity3 to locate
a discrepancy. First/second outer model tails remain legitimate ranking evidence,
but receive no label as full native forecasts and no new native counterfactuals.
For each valid comparison report commands,masks,per-tick service, ordered summed
J,coordinate errors and the modeled/actual next choice when modeled. A lawful
FP32/FP64 forecast discrepancy is recorded and interpreted; it is not repaired
by relaxing tolerance or automatically treated as an implementation mismatch.
Full-reader law/identity failure remains a technical stop. Actual adverse outcomes
with faithful forecasts remain scientific adverse results.

Primary contrast is **A_E4−A_E complete native mean J**. The decisive matched-rights
contrast is **A_E4−G_E4**; also report G_E4−A_E,A_E4−A2,G_E4−A2 and fresh A_E−A2.
For every contrast retain all16 world values for J,served users/tick,quality,
height term,mean path/UAV,eligible/ineligible unserved,active mean,whole-team
p05/minimum,zero steps and longest zero-service run. Report means,medians,
positive/equal/adverse counts,worst losses and contribution concentration; a
signed contribution share is undefined when its total is zero, not silently0.
Use exactly10,000 paired world bootstrap samples from default_rng(29524991),
each16 indices with replacement, shared across all arms/metrics, with2.5/97.5
percentile bounds. No score-dependent sample extension, equivalence claim,
post-hoc threshold or pooling with B01 is selected.

All four arms use the same exogenous world, but endogenous clocks and later
states may differ. A_E4−G_E4 estimates the complete selector rule under the same
four-opportunity rights, including its induced timing. A_E4−A_E changes opportunity
count and later selector use, not an isolated timing or mechanism coefficient.
There are no independent training seeds:16 worlds support conditional exploratory
uncertainty for fixed deterministic programs;68 missions and800 user-world records
are not68 or800 independent replicates of a learning effect.

Read every actual opportunity's mask/menu size,requested/initiated/stay decision,
commanded/physical duration,path,arrival mask,activation/remuting,nonadjacent member
revisits and future modeled choices. Individual continuity uses saved post-transition
connections at ticks0…499: per-user served ticks, all unserved intervals with
left/right censoring,longest gaps, never-served additions/rescues and paired losses
within team-positive worlds. These reductions cost reading CPU but no extra native
mission. Preserve all losses and quality/path tradeoffs; path remains unpriced
in native J. Whole-team tails constrained by a shared prefix do not imply individual
continuity. Activation-conditioned groups are descriptive, not substitute estimands.

The fixed result branches change the following judgments:

- A_E4 improves on A_E and G_E4 with a useful complete tradeoff: retain the rolling
  anticipatory capability and its measured price, without calling it universally
  best or attributing all gains to a specific member interaction.
- G_E4 improves on A_E and is as useful or better than the more expensive A_E4:
  retain the simpler four-opportunity capability; additional anticipation has not
  earned its premium on this panel. Near equality/interval overlap alone does not
  prove equivalence.
- A_E4 improves on G_E4 but not A_E/A2: retain within-contract anticipation
  witnesses, but the four-opportunity expansion has not established a complete
  use advantage over the existing capability. A2 winning also remains useful.
- Means trade off service,quality,path or concentrated/individual losses, or the
  intervals are broad: retain the observed conditional capabilities and explicit
  uncertainty; no universal default, weighted utility or fairness rule is invented.
- Additional choices stay, physical programs coincide, or complete results are
  adverse: close this fixed four-opportunity purchase and preserve A_E/A2. No
  automatic fifth opportunity, depth increase, learned gate, clock grid or repair
  follows. This does not close the broader temporal-cooperation question.
- A formal/worker/reader/resource failure leaves a missing comparison: preserve
  the paid partial evidence and technical cause. Do not impute missing arms,
  choose replacement worlds, restart an audit or call the incomplete result an
  adverse planning effect. Investment can end without an empirical refutation.

#### Source-derived complete work and cost

The full proposed purchase is **64 result+4 audit missions=68H500/34,000 native
transitions**, **204 actual opportunities**, at most204 initiated commitments,
**0 new fits/updates/training labels**. World preparation/reset/imports/native
initial radio and serialization are still paid. The reader adds34,068 saved-native
snapshot reconstructions and34,000 motion/reward checks, not extra env.step calls.
Its saved-native loop calls each user-path-loss,user-SINR,greedy-assignment,
peer-path-loss and peer-SINR reconstruction34,068 times, plus272,544 native
observation reconstructions and corresponding local visibility readings. Native
constructor/reset work and internal routines remain separately timed/counted;
the planner request ceiling below does not pretend to include native radio work.

The Oracle's request/tick/bank ceilings reproduce exactly from the actual loops:

- Per bank B=`1+7*100*128=89,601` public state/mask requests, at most700 stationary
  rows and28,000 candidate transit ticks. Transit uses a muted member under fixed
  transmitters: the source propagates motion/height/path for each tick while using
  invariant radio service; those ticks are not extra calls to `_Scores.score`.
- A C/E model suffix at a multiple-of10 start t has
  S(t)=`217*(500−t)+255*(500−t)/10=242.5*(500−t)` requests, including one model reward
  query per tick. Native C/E alone has C=`500*216+50*255=120,750` planner requests.
  Conservatively add128 for each actual possible arrival; this deliberately does
  not credit the native C/E work that an option replaces.
- A forced L10 candidate saves at least `11*216+255+127=2,758` requests relative
  to a stay model suffix. Thus F(t)=`8*S(t)−7*2758` bounds one complete menu's model
  branches, and D(t)=B+F(t) bounds one ordinary selection.
- A stay-first early prefix costs2,425; an initiated L prefix costsL+2,082. For one
  anticipatory root at t, each first candidate pays a prefix, a new inner bank
  and all its branches, and execution of the inner selected suffix. Therefore
  A(t)=`B+[2425+B+F(t+10)+S(t+10)]`
  `+7*[2092+B+F(t+20)+S(t+20)] =72*S(t)+341655`.
  L10 maximizes this bound among initiated candidates. In particular A40=8,373,255,
  A50=8,198,655,A60=8,024,055; D40=962,695,D50=943,295,D60=923,895,D70=904,495,
  D120=807,495. Later actual clocks only reduce these remaining-horizon ceilings.
- A2's fixed first search costs at most7,422,655 by the same decomposition with
  an80-tick prefix and u120. Two-opportunity totals add C+256; four-opportunity
  totals add C+512. G_E4 uses D40+D50+D60+D70; A_E4 uses A40+A50+A60+D70.
- An anticipatory root's logical model ticks are
  `8*(500−t)+8*(500−t−10)+56*(500−t−20)=72*(500−t)−1200`.
  The eight outer branches count each concatenated prefix/suffix once; inner
  branches are additional. This is not eight branches all reaching t+10, nor
  a double charge for an outer array plus its retained segment projections.

| Arm, one mission | Worker requests ceiling | Logical model ticks | Banks | Rows | Candidate transit ticks | Complete model branches | Segment certificates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
|A2|8,351,156|31,040|10|7,000|280,000|80|88|
|A_E|9,437,556|35,520|10|7,000|280,000|80|88|
|G_E4|3,855,642|14,240|4|2,800|112,000|32|32|
|A_E4|25,621,722|97,040|28|19,600|784,000|224|248|

For17 missions/arm, worker ceilings are **803,523,292 requests;3,023,280 logical
model ticks;884 banks;618,800 rows;24,752,000 candidate transit ticks;7,072 complete
model branch artifacts;7,752 segment certificates**. An anticipatory root has
one outer bank+eight inner banks; A_E4 has3*9+1=28. The extra segment certificates
record prefix/suffix boundaries, not extra full model returns.

The **full uncompressed reader separately incurs the same complete search**:
combined ceilings are **1,607,046,584 requests;6,046,560 logical model ticks;
1,768 bank constructions;1,237,600 rows;49,504,000 candidate transit ticks;14,144
branch evaluations**, plus the native reconstructions above. Actual worker reuse
reduces computed transitions/requests only; the reader repeats all logical model
transitions. Count requested/scored/cached candidates,geometry rows computed/reused,
ordinary candidate-position predictions,native controller work,banks,model control/
reward and candidate transit separately. A scored request is not necessarily a
new geometry computation. Prefix/outer duplication is not another opportunity to
hide or double-count work. These are deliberately conservative, not necessarily
jointly achievable envelopes or forecasts of the actual menus.

All artifact serialization/compression,catalog replacement,per-file and payload
hashing,certificate comparisons,saved-array bootstrap/individual reductions and
final compact publication are additional real support/reader work. Their byte/
CPU demand depends on actual histories and is not derivable from request count
alone. Required first-search identity comparisons use already paid evidence; no
extra scorer calls are authorized to implement them. Record enclosing process
CPU/wall as well as nested stage counts/times so residual hashing/I/O/reduction
cost is not dropped or added twice. On a stop retain actual completed/partial
counts, even if the planned envelope is not reached.

The CPU center is explicitly a heuristic: B01's17-mission worker+reader episode
costs are4,132.925681s for A2,4,447.820770s for A_E and1,515.505449s for G_E. Keep
the first two; scale G_E by3,855,642/2,026,996 and A_E by25,621,722/9,437,556 for
new G_E4/A_E4. That gives2,882.712379s and12,075.247795s, totaling
**6.538530 CPUh** before additional enclosing/engineering/support costs. Scaling
B01's original conservative8.171633h no-reuse request price by
803,523,292/369,017,368 gives **17.793465CPUh**, not a runtime upper bound. The
Oracle's6–12CPUh is a plausible planning range with this alternative17.79h
sensitivity; I cannot turn it into a confidence interval. Smaller/larger actual
menus,new recurrence behavior,recording cost and shared-node load remain unknown.
B01's observed reuse fraction and resource margin are not transferred as facts.

Budget **8–14 active support hours** as an uncertain estimate for source design,
implementation,pure mock checks,focused engineering review,full scientific reading,
publication and deletion, plus queue/network elapsed. This is not a measured CPU
bill or a guaranteed completion time. Existing B01/B04/B08 costs remain separate
historical investment; B01's unused20CPUh boundary is not a B02 entitlement.

Forecast one canonical evidence copy1–2.5GiB,source snapshot1.6–2GiB,transient
output/scratch1–2GiB and process RSS1–2GiB. Compression/trace size and the current
source tree are uncertain; there is no duplicate-retention allowance. Propose
configured **local_linux** on Jacob, interpreter
`/home/fires/.venvs/hmasd-linux-cpu/bin/python`, POSIX detached supervision and one
numerical thread, using the same concrete reason as B01's published runtime
correction (unresolved A03 remote anomaly, not a blanket diagnosis of that node).
Do not probe or reserve a node in this source phase. Actual pause/lead/source,
free memory and duplicate checks apply only to a selected formal launch.

My proposed **new B02 stop envelope** is24 aggregate metered CPUh,48 operation
wallh and12GiB normal allocated source/output/scratch bytes. The CPU bound includes
all measured new B02 source/preparation,mock checks,input binding,formal launcher,
worker,full reader and closure CPU, charging preparation once to the runner's
remaining limit. Unmetered adviser/manual support remains explicitly unknown;
this is not a claimed bound on human/model reasoning cost. Operation wall starts
with the formal process/import scope, not the earlier source/engineering calendar.
The12GiB measure uses allocated blocks/inodes, no symlink-following or count of
other directions, including partial files and any owned external scratch.

Within this envelope, propose a separate **pure engineering mock sublimit of
.5CPUh and2wallh of automated checks**, not an extra free allowance and not current
permission to run them. Reserve **600CPU-s,1,200wall-s and128MiB** inside the main
limits for failure/terminal evidence and orderly closure. Stop scientific work
before those reserves; use the same non-restarting signal/cooperative guards and
bounded allocation checks, with actual detection overshoot reported. The reserve
cannot purchase another mission, omitted reading or a retry. These are proposed
protective stops for this exact finite purchase, not fits to spend or entitlement
to continue until a ceiling is reached.

The first formal-request/admission/worker/full-reader/resource failure closes
that purchase and preserves its error,accepted-or-refused status,partial unique
evidence and consumed costs. Lost observation is reconciled against the same
handle, never treated as a new request. No automatic resume,retry,local/remote
fallback,seed replacement,audit repetition or repair is included. Pure mock
failure may be corrected inside the bounded pre-effect engineering task; it does
not allow a real scientific probe. A later distinct purchase would need a new
reasoned prospective choice, preserving this one as technical missingness.

#### Bounded future engineering and current disposition

If Root later selects the complete study, implementation belongs only to this
direction's new `b02/` entrypoints/mirrored tests and matching run/scratch paths
(proposed first tag `b02_rolling_timing_a01`). Keep fleet/parent/A/D and B01's
published external contracts frozen. Reuse original primitives for reporting,
C/E,sites,transit,mask scoring,relative option execution,ordered summaries,recurrence
keys and certificates. A small direction-owned parameterized menu/segment/rolling
adapter is needed; do not copy the whole planner/environment/scorer stack, patch
module-global starts or fake a relative clock. Any necessary internal factoring
must retain B01 behavior/source provenance and be independently reviewed before
result execution; this contract grants no such implementation now.

The one verifiable behavior change is four actual opportunities with fresh history,
using the fixed two-layer selector at1–3 and ordinary selector at4, together with
the correctly scoped complete reader. The future L0 must include the exact phase,
expiry and copied-history invariants above. Pure fixtures cover all duration
classes,stay-only menus,nonpositive champions,ties,zero-path and site/command
aliases,changing masks,old-plan replacement,maximum clock190/arrival230,source/
certificate tampering,ordinal-ID collisions,mutating sinks and resource-stop
retention. Inject stub scores/transitions rather than secretly generating a host
or querying native/public RF. The real four full audits and their full readers
are already paid within68 missions; they check correctness, not a beneficial score
or a chosen activation threshold. Independent engineering review has a different
purpose from Root's coming scientific investment review.

I support taking this complete four-arm construction to that one independent
selection review. I found no contradicted source premise or arithmetic error in
the Oracle's main ceilings. I retain the substantive investment qualification:
this buys finite ordinary capability on a small known-model host and significant
engineering/reading time; reuse of A_E or a different task contract can still be
better portfolio choices. The new source-defined opportunities and model scopes
are feasible, not observed successes. No mechanism-proof gate,confirmation batch,
parallel miniature pilot or second preliminary review is proposed.

Current actual work remains **0 new worlds,0 native/model/candidate-transit/RF/
scorer/branch calls,0 fits/updates/labels,0 production code changes and0 formal
requests**. The only modified file so far is this notebook. Measured source-only
subsections so far total0.117889CPU-s: fresh Git read/fetch0.086772s, existing JSON/
55-source hashing0.017959s, integer/Fraction count reconstruction0.007686s and
cost arithmetic0.005472s. Their measured walls total1.858182s. Other read/search,
CodeGraph,advice capture,reasoning and final publication support were not fully
instrumented and remain unknown, not zero; no new scientific execution is hidden
in those figures. The following write/publication tails are reported separately
when measured. The next assigned boundary is Root's review/whole-investment
choice on this actual contract; question ownership continues and no owner-permission
wait is invented.


Source-contract self-check: original B01 notebook prefix remains byte-equivalent
to published HEAD; the Oracle body digest above is unchanged; no B02 code/test/run
or direction scratch path exists, and the retained A02 result digest is unchanged.
The contract write added0.002103 measured CPU-s /0.002337 wall-s; this source/path
validation added0.006969 CPU-s /0.006709 wall-s. These are support-only costs,
additional to0.117889s above; this append and later publication tails remain outside
those samples. `git diff --check` passed for the owned notebook. No scientific
query or test execution was used to certify the prospective science.


Before source publication I refreshed and read the changes through published
main `f8c2ab328f1f5670cfcea6ff5d096b0cac1b14d7`. Root's new timing disposition
accepts the B01 capability and records this same four-opportunity source assignment;
its updated B learning-data construction is separate. Background topics3/5/8 and
the source premises used here are unchanged. This ordinary publication refresh
changes no comparison,permission,accepted operation or source-only boundary.


<a id="b02-purchase-l0-20261003"></a>
### B02 selected whole purchase and L0 — 2026-10-03

Root has selected the complete four-arm B02 purchase on the published actual
source contract `1d0124bb96cdcf1c2c9c9918487f009aa8dff95a`, after reading that contract,
the full coauthor proposal and one new independent Root-hosted selection review.
The fixed contract above now authorizes implementation, exact-input publication,
one formal admission/execution, all paid reading, interpretation/publication and
necessary cleanup. Source-only language above remains the historical boundary,
not a current restriction. The original independent review will be retained below
verbatim with its identity; no repeat science review or per-run Root ACK is added.

Adopt Root's review clarification: third/fourth stay is not evidence that the
complete program did not change, because the second actual selector already
changes in A_E4. Retain complete native usefulness even when its attribution stays
unresolved; use only the paid choice sequences/arrays to inspect this distinction.
Never use absent late activation to reject an otherwise useful package, or use
local modeled improvement to rescue actual loss. The purchase remains finite
ordinary planning, not sustained throughout H500, learning or optimal opportunity
count. Existing B01 positive/adverse results, A01 failure/cost and A/D work stand.

**L0 deliverable:** implement exactly four actual completion-based opportunities
and the fixed two-layer/ordinary selector schedule, with complete uncompressed
reconstruction, scoped forecasts, published17 initial arrays and bounded runtime.
Author only on shared main in this direction's new `b02/`, its matching tests,
`runs/uav_planning_opportunity_timing/b02_rolling_timing_a01/` and owned scratch.
B01 and all55 original source/input bindings remain byte-frozen; no fleet/parent/
shared edits, global-start mutation, synthetic shifted clocks or complete planner/
environment copy. A narrow menu/segment adapter may repeat only the necessary
clock-validating loop while importing the original sites/transit/scorer/C/E/
OptionProgram/reduction/key/certificate primitives. Any broader factoring needs
an explicit narrow exception before editing frozen paths.

The bounded Implementer owns only `b02/{__init__,controller,option,segment}.py`
and matching `b02/test_rolling.py`; DM owns all other B02 runner/input/reader/test
integration and this notebook. No simultaneous edits to those helper paths;
Implementer makes no Git/index mutations, launch, real world/model/RF/scorer/
native calls or scientific choice, and spawns nothing. It returns its diff and
metered pure-fixture checks for DM acceptance. Existing B01 implementation and
checks are read-only evidence. Independent Engineering Reviewer then checks the
whole final diff and targeted fixtures; DM accepts the result and owns the launch.

Interface: `RollingProgram(arm,horizon=500,branch_sink=None,candidate_sink=None,
reuse=True,segment_sink=None)` for G_E4/A_E4, retaining frozen `controller`,
`plans`, `selections`, `banks` and `select(t,report,old_mask)` shapes. Expose ordered
actual opportunity times. A_E4 first search should call the inherited B01
anticipated selector with identical scientific IDs/payloads; its `ae/first`
namespace already identifies opportunity1. Subsequent scopes include ordinal,
actual clock and candidate/hypothetical clocks, preserving prefix/suffix/outer
parent mapping. No model or actual-history cache crosses a selector boundary.

Semantics: t1=40, stay advances10, commitment advances commanded arrival+10;
stay consumes one of four, old plan replaced without history reset, fourth has
no successor. First three A_E4 searches foresee only one ordinary next choice;
G_E4 and fourth A_E4 use the ordinary complete C/E tail. Preserve every candidate,
strict-J stay/ties, zero-path commitments, absolute phase/report denominator500,
FP32 command arithmetic and inner decode, unrounded FP64 outer state, separate
history copies and mutating-sink isolation. Entry starts40..190 by10 are explicit.
Use frozen A2/A_E constructors without changing their external law. Native prefix
and first-search identity use already-paid evidence; no extra scientific call.

Checks are synthetic only: duration10/20/30/40, all-stay and maximum190/230 clocks,
nonpositive champions/ties/aliases, changing masks/immediate-mover exclusion,
old-plan expiry, no fifth/deeper search, absolute phase/history/precision, copied
sink payloads, segment-local recurrence plus fresh uncompressed certificate,
ordinal evidence identity, compaction/source tampering and stop/failure retention.
Real audits are exactly the four paid29524900 missions, not an extra gate/pilot.

Fixed new limits adopted from Root:24 aggregate metered CPUh,48 operation wallh,
12GiB normal allocated owned source/output/scratch. Science stops before internal
600CPU-s/1200wall-s/128MiB closure reserves; retain actual overshoot. Pure automated
mock checks total at most.5CPUh/2wallh within the same24CPUh. For coordination the
Implementer may use at most.15CPUh/.5wallh of that mock subtotal before returning;
DM/Reviewer keep the remaining subtotal. All metered preparation/support/import/
launcher/worker/full-reader/closure costs count once. Previously measured source
subsections0.126961CPU-s plus Root-reported review support approximately.016CPU-s
are retained with their actual scope; other support is unknown, never0. Formal
process/import start defines operation wall, not previous authoring calendar.
First real formal request (including refusal), admission, worker, complete reader
or resource failure ends this purchase with partial evidence/original error. No
retry/resume/fallback/reseed/re-audit. Lost acceptance reconciles the same request.
Pure fixture/source defects can be repaired within the declared pre-effect scope.


<a id="b02-independent-selection-review-20261003"></a>
### B02 independent selection review — Root-hosted, 2026-10-03

Original complete advice delivered once by `/root/four_dm_selection_critic` at
Root’s request. This is Root-hosted independent ResearchCritic advice, not the
Oracle coauthor’s self-review. Verbatim body follows; DM read it completely.

<!-- B02_INDEPENDENT_SELECTION_REVIEW_ORIGINAL_BEGIN -->
**建议保留 B02 已发布的四臂设计，购买一次完整研究。** 理由是检验已获得的两步合作能力能否在后续实际状态中反复使用，并检验同样四次机会下，廉价贪心程序能否取得相当或更好的用途。无需先购买 chooser、正面试跑或机制证明。

我沿用原独立上下文，没有继承 Root 对 B02 的判词。本次先读 B01 原始配置、结果、完整 reader、正负世界及源码，再读 DM 判读、B02 合同和 Oracle 原答。审阅的是发布于 `1d0124bb96cdcf1c2c9c9918487f009aa8dff95a` 的[完整合同](/home/fires/hmasd-wsl/docs/research/candidates/uav_planning_opportunity_timing/NOTES.md:1288)，未重评 A/D/B，也未执行新实验或修改记录。

B01 的证据足以支持这次有限延伸。原始 [result.json](/home/fires/hmasd-wsl/runs/uav_planning_opportunity_timing/b01_complete_timing_a02/result.json) 中，AE−A2 的平均 J 为 **+.004137129**，配对世界区间 **[+.000260501,+.009437566]**；服务为 **+.37675**，J 正/零/负世界为 **11/3/2**。更有建设性的证据是 AE−GE：七个改变首个承诺的世界全部提高 J 和服务，其余九个完整原生程序逐字节相同。GE−A2 的平均 J 和服务均下降，单纯提前提供第二次机会没有吸收 AE 的收益。

这仍是带有明显代价的能力。世界 29523010 提供约 **55.8%** 的主比较净 J 增益；世界 29523009 提供约 **82.0%** 的净路径节省。质量平均下降，两个主比较 J 负例保留。800 个匹配用户—世界记录中，68 个损失服务时长、61 个最长观察间隙变长；五个 never-served 被救回，同时新增两个。它们不是 800 个独立实验单位。

我直接核对了这些结论的具体支撑：

- 世界 29523010 中，AE 改变两成员序列，取得 +.036933412 J、+3.198 服务；保存的原生连接数组同时确认用户 6 从 0→410 个服务 tick，用户 16 从 500→55，并产生 445 tick 的右删失末端间隙。
- 世界 29523009 的“先 stay、后移动”保留了有用等待能力；大幅路径下降没有进入原生 J 的成本项。
- 世界 29523005、29523012 的 J/服务损失是真实执行后的不同程序结果。世界 12 的已选模型、实际选择及个体救回/损失记录一致。
- 此面板 A2 的首个 mover 在第二机会也仍然活跃，没有同成员再次移动。因此旧面板的再次移动机会不能解释本次两个负例。

B01 全部已选 forecast 在有效比较范围内保持命令、mask、逐 tick 服务一致；这支持其原有两步程序的可信执行，但不能外推为 B02 滚动程序的完整预测准确性。55 个绑定源码文件，以及 canonical config、summary、reading 的字节数和散列均匹配；我还核对了上述关键世界的原始数组、决策流和证据目录绑定。没有重新运行物理或模型重建。

**B02 的科学对象定义成立，但其价值应从完整闭环结果判断。** AE4 第一次搜索就是 AE 的第一次搜索，两者应在实际第二次选择前保持相同首选、时钟和原生前缀。这是一个有用的比较结构：新增问题从第二次重规划开始，检验后续继续使用两层选择是否值得。

我核对了原 `TimingProgram`、菜单、segment 和 `OptionProgram/validate_plan` 的相关路径。合同正确保留了：

- 绝对时钟、报告相位和实际 controller history；每次选择消费一次机会，stay 也替换旧 plan。
- 到达时强制零命令及 member-containing mask，然后到 arrival+10 才再次选择；直接前一个 mover 被排除，更早的非相邻 mover 仍可能重新进入菜单。
- 完整 champions、非正预测候选、严格 stay、原始 ties 和 aliases。
- 内层 FP32 报告解码与外层未舍入 FP64 物理状态的分离。
- 每个模型 segment 独立的复用缓存；完整 reader 另行计算全部逻辑工作。

四次机会在 t40…190 内发生，最后承诺最迟 t230 到达，其后仍是普通 C/E。它检验的是**四个有限早期机会中的滚动两步选择**；没有覆盖贯穿 H500 的持续合作、无限次组合或四层完整规划。

最重要的限定是模型与实际后继策略的差异。AE4 前两次估值假定“下一次普通选择，然后 C/E”，实际下一次还会进行两步预见。因此这些模型尾部是合法的排序依据，却不是实际四阶段程序的完整价值预测；严格优于模型 stay 也不保证原生逐世界改善。合同将前两次 forecast/native 核验限定到下一次实际重选前，并保留第三、四次对应的完整剩余结构，处理正确。不能把后续策略有意不同造成的尾部差异判成实现错误，也不能因此免除完整原生结果比较。

这项差异没有使研究失去价值。它恰好暴露一个实际选择：这个有限估值器作为滚动控制单元，能否在额外计算和新的访问状态下继续产生用途？若完整效果有益，代理尾部不等于实际策略价值不自动否定用途；若完整效果不利，也不能靠每次局部预测正面来保住方案。

**最强替代仍是直接复用 AE，保留 A2；实验内的关键替代是 GE4。** 更多机会本身是增加控制权，可能让普通贪心充分发挥，也可能只是改变普通 C/E 的后续运动。AE4−GE4 才检验这项共同新增权利下的预见增量。两者匹配机会数量和更新规则，实际时间戳仍由各自选择决定，因此比较的是完整 selector 规则。

我倾向于本次滚动研究优先于 A2/AE chooser：它同时回答能力延伸与廉价替代两个问题，chooser 主要回答两个已有时钟间的条件选择。这个优先级是投资判断，不是数据证明“知识量更大”。也不能把“中心估计只多约 1.8 CPUh”当作可靠差价——两者都有未测菜单、工程与支持成本。若支持工作已成为主要瓶颈，直接保留 AE 而不买 B02，仍是合理的投资停止。

本次值得购买的完整观察是合同中的 **16 个新共同世界×四臂，加四个独立工程 audit，共 68 个 H500 mission**；不要拆成先看有无正面效果再决定是否补完。A2/AE 保留现有用途参照，GE4 保留同权的廉价解释。无需再增加 G2/GE、时钟网格或 attribution 分支。

不同结果应改变不同判断：

- **AE4 同时改善 AE 和 GE4：** 保留滚动预见能力及完整增量成本；个人服务、质量和路径损失仍单列。
- **GE4 改善 AE，且用途/成本更有利：** 保留简单的四机会能力；额外预见尚未证明值得其价格。区间重叠本身不证明等价。
- **AE4 胜 GE4，却未改善 AE/A2：** 保留同权合同内的预见价值，但四机会扩展未建立相对已有能力的用途优势。
- **完整结果不利或不确定：** 结束这次固定购买，保留 AE/A2；不自动购买第五次机会、加深搜索或修补。
- **技术或资源失败：** 比较缺失，保存已付证据与成本，不能当作规划负面结果。

判读时还应区分“后两次没有启动承诺”和“完整程序没有改变”。AE4 第二次选择的规则已经改变，后两次 stay 不能单独替代主结果判断；只有实际序列和保存数组才能确定新增干预是否发生。现有合同字段足以完成这个区分，无需额外调用。

**完整价格核算一致。** 我用独立整数/有理数算术复核了每臂及总量：

| 项目 | Worker | 完整 reader 另付 |
|---|---:|---:|
| state/mask 请求上限 | 803,523,292 | 同量 |
| logical model ticks | 3,023,280 | 同量 |
| stationary banks | 884 | 同量 |
| candidate rows | 618,800 | 同量 |
| candidate transit ticks | 24,752,000 | 同量 |
| complete model branches | 7,072 | 同量 |

另有 **34,000 native transitions、204 次实际机会、34,068 个保存原生快照重建、34,000 次运动/奖励检查**，以及原生无线、观察、序列化、散列和归约工作。零 fits 不代表便宜。

B01 已测的完整相关成本约 **3.26048 CPUh**，另有未完整计量的支持成本。B02 的 **6.538530 CPUh** 算式能够复现，但只是按旧各臂成本及新请求负担缩放的中心估计；**6–12 CPUh** 是规划范围，**17.793465 CPUh** 是无复用价格敏感性，均非性能保证。新状态下的菜单大小、复用比例和记录成本仍未知。

合同的 **24 累计 CPUh、48 operation-wall h、12 GiB** 是这次新购买的停止范围，不是旧 20 小时余额。`.5 CPUh/2 wallh` 纯 mock 子界限和 `600 CPU-s/1200 wall-s/128 MiB` 收尾预留均包含在主范围内。首次正式请求、worker、reader 或资源失败即关闭本次购买；没有额外健康查询或自动重试。预计 **8–14 支持小时**、**1–2.5 GiB 唯一证据**以及 source/scratch/RSS 价格仍需保留为估计，实际节点准入和新实现正确性尚未验证。

本次审查没有生成世界、真实 scorer/model/native/RF/optimizer 调用、生产实现或记录改动。可单独计量的保存数据读取、散列和算术片段约 **0.143 CPU-s**；其他检索、阅读和推理支持没有完整计量，不计为零。

**MATERIAL_DISSENT: no — 支持按已发布 B02 的完整比较与新全价购买一次研究；不支持将其解释为四阶段完整预测、普遍部署升级或原生单调改进保证。**
<!-- B02_INDEPENDENT_SELECTION_REVIEW_ORIGINAL_END -->

DM disposition: adopt the complete four-arm purchase and all scope/cost qualifications; MATERIAL_DISSENT:no. The paid program sequences and native arrays, including second-choice changes, determine whether the intervention changed the complete program. No late-activation proxy gate or additional scientific call is added. The independent original body is 9451 UTF-8 bytes, SHA256 `398192e50c69a5ced53391480fef2396b7c41b9aa7e6fb3326c40317e8eb8acf` (excluding delimiters/final newline).

Meter correction to the preceding provisional L0: the complete original reviewer report measures approximately0.143CPU-s for its own saved-data/hash/arithmetic fragments, not an inferred0.016s. Charge that separately from DM’s0.126961s source fragments and0.000154968s L0 append; other support stays unknown. This corrects the provisional estimate without changing the24CPUh total.


<a id="b02-engineering-acceptance-20261003"></a>
### B02 implementation accepted; one formal request remains — 2026-10-03

DM read and accepts the bounded registered Implementer diff and its checks:
new rolling controller/menu/segment/init plus `test_rolling.py`. No frozen/shared
file was edited. The adapters repeat only the short menu/segment loops needed for
the larger start domain while importing the original C/E, sites, transit, scores,
OptionProgram, reductions, keys and certificates. A_E4 opportunity1 calls the
inherited B01 anticipated selector with identical `ae/first` scientific payloads.
Later IDs are `ae/op{k}/{first}/t{actual}/t{future}/...`: candidate identity remains
at index2 for the unchanged B08 certificate reader; ordinal/current/future clocks
and prefix/suffix/outer relationships are all explicit. This narrow correction
was covered by fresh synthetic prefix/suffix certificate checks, not a frozen edit.

DM's integration uses frozen EvidenceStore/compaction and saved-native reduction
helpers, with new four-opportunity collector, source/input manifest, complete
uncompressed reader and scoped forecast comparisons. The first-search comparison
reads all paid model/bank/segment payloads and certificates; the native comparison
ends at input t2, while complete-program comparisons retain later differences.
A regression specifically keeps a changed program when its last two choices stay.
Every paired world and individual loss remains; zero signed totals leave net
contribution shares undefined. Complete logical counts now include7752 maximum
segment certificates in addition to all originally charged work.

All17 selected initial arrays were generated once for publication from stream74,
with per-array little-endian FP64 hashes and no host/controller/scorer/RF/model
execution. The original55 source/input files matched the B01 A02 config exactly;
`frozen-bindings.json` keeps that original source SHA and byte bindings. B02
`fixed_config` verifies them before science as well as binding every new source/input.

The original Implementer return reported39 passing synthetic tests. Five
invocations cost21.720959CPU-s/22.027672wall-s, including the first fixture-only
`KeyError: barrier_t` (15failed/19passed): its assertion was corrected to the
frozen certificate field `eligibility_after_t`, without production or tolerance
change. DM's integrated52 tests passed, then two added program/individual-loss
regressions and one formal-wall-origin regression passed. No real audit was used.

The same registered independent Engineering Reviewer read the full fixed contract,
planner, callers and final integration, including precision/history, scopes,
full replay, paired reductions, evidence/compaction, failure retention and budgets.
Its final finding is **no material engineering finding remains**. It independently
ran the full existing B02 suite: **55passed**,14 dependency deprecation warnings,
5.37s pytest/6.291180s enclosing wall. Full-lifetime wrapper.107124CPU-s plus
children6.205285CPU-s gives6.312409CPU-s; separate peaks669536/332004KiB are neither
incremental nor additive. No new scratch leftovers, code edits, scientific query
or launch. Runtime numerical identity and resource sufficiency remain unverified;
the four paid audits and complete readers are the selected observation, not a
positive activation gate. DM accepts this engineering result.

B02's Meter preserves the B01 permanent-stop/signal-unwind behavior. It additionally
counts authored B02 code/tests and direction scratch alongside the accepted
snapshot/canonical output, and reads one atomically written formal-launch resource
record. Launcher CPU is charged once. When that same-host record becomes available,
its monotonic request start replaces the later runner-import origin, so overlapping
launcher/runner wall is not summed. The narrower initial sample is explicitly
labeled until then. This conservatively includes snapshot/admission in48operation
wallh; it changes no exposure, limit or first-failure rule. Detection/reserve and
hard-envelope overshoot are explicitly recorded. Post-final-sample closure and
unmetered support remain separately reportable, not zero.

Before submission the owned RESEARCH row will use the launcher's actual admitted
state **exploring**, consistent with Root's published complete selection at
`e926c4418`; literal `active` is not an accepted parser state. This carries forward
the exact B01 A01 failure lesson. Lead stays `Codex DM (native child)` and pause
must remain lifted. Pure CLI/state parsing is a pre-effect source check, not a
formal launch, memory probe or extra audit. The single new selected output is
`runs/uav_planning_opportunity_timing/b02_rolling_timing_a01/`, identityseed29524000,
configuredlocal_linux/one numerical thread, with no retry/resume/fallback.

Preparation before the final publication/parser tails is **41.884765120CPU-s**; automated mock subtotal is41.396104000CPU-s/41.903658897wall-s, inside1800CPU-s/7200wall-s. The bound preparation JSON retains individual measured scopes and unknown support. This final append/write tail is measured separately below.

Final pre-effect source check refreshed published main`e926c44188833f6cd127ad062e721ec48b8bad66`, preserved Root’s complete selection/routing and other writers, and changed only this direction’s stale reserve row to parser-supported exploring. Pure parse_research_state and CLI parsing verified lifted/exploring/Codex DM (native child), local_linux, one fresh B02 output and no retry argument. All55 inherited byte bindings and new Python ASTs passed. This check incurred0.249730000CPU-s/1.486982732wall-s; with the preceding.000617334CPU-s acceptance append, published preparation now totals42.135112454CPU-s. No actual-node admission or scientific call occurred. This metadata/publication tail remains outside that sample and is not reported as zero.


<a id="b02-accepted-operation-20261003"></a>
## 2026-10-03 — B02 single formal request accepted; complete reading pending

The exact inputs were published on main as `9b763be8a45dad875166efcfba8efbf9c3db54b2` before the **one** new formal request. Current canonical and published policy both read owner pause lifted, direction exploring, lead `Codex DM (native child)`. The ordinary local_linux launcher accepted at 09:23:09 UTC. Its [native manifest](../../../../runs/uav_planning_opportunity_timing/b02_rolling_timing_a01/launch-manifest.json) and [preflight](../../../../runs/uav_planning_opportunity_timing/b02_rolling_timing_a01/admission-preflight.json) retain the exact command, source snapshot, node, process identities and stable operation reference; no new cell, fallback, audit, reseed or retry was introduced. The worker and complete independent reconstruction are in the same accepted operation. Acceptance is **not** a scientific result or this assignment's return boundary.

The formal-request wrapper measured 9.945715 CPU-s (0.077823 wrapper + 9.867892 reaped launcher subtree), 20.130138383 monotonic wall-s and separate lifetime peak RSS 669536/673112 KiB. These peaks are not additive or simultaneous. The atomic `formal-launch-resources.json` supplies that extra CPU and the same-host monotonic request start to the worker meter, in addition to published preparation's 42.135112454 CPU-s. Its final JSON-write tail remains unmetered, not zero. UTC and monotonic durations are reported in their own clocks.

The first observer arm returned `ValueError: drain and rearm the existing state before adding observations`: this session's prior completed jobs had consumed events and observation was stopped. The DM inspected and drained generation12 with no pending events or live prior job, rearmed that state, then armed only the new B02 operation. No old scientific worker, launch or blocked observation was resumed. The first actual drain, generation14, read matching live runner/supervisor identities and consistent accepted records at 09:25:14 UTC. Arm refusal, same-session reconciliation and first drain consumed a further measured 0.612463 CPU-s; their exact small records are retained in this run. The detached observer uses 30-s read-only status probes and a 1500-s checkpoint window. Its future support cost is not included in those initial samples. The native child remains active; later checkpoints drain/rearm this same operation, never relaunch it. Registration alone is not assumed to provide a future native-child wake.

The first real formal/admission/worker/full-reader/resource failure still closes this purchase. The four prescribed audits and full finite panel are now pending; no interpretation is inferred from admission or early activity.


<a id="b02-complete-reading"></a>
## 2026-10-03 — B02 complete/read: retain finite rolling anticipation with its full price and adverse service outcomes

**The selected complete comparison is positive for A_E4 against both A_E and G_E4.**
Retain this four-opportunity ordinary planning capability alongside the two-opportunity
A_E/A2 and cheaper G_E4 comparators. The fixed purchase ends here; it does not select
another opportunity count, clock, deeper search, chooser, learning gate or fit. This
is the positive-with-tradeoffs branch of the [original independent selection
review](#b02-independent-selection-review-20261003), read before implementation;
that review is not misrepresented as an independent inspection of these new results.
The main judgment changes from an untested extension to an observed useful finite
closed-loop capability on this panel. Its deployable value depends on compute and
service-distribution costs. The broader cooperation question remains open.

The accepted source is `9b763be8a45dad875166efcfba8efbf9c3db54b2` and the unchanged
[fixed scientific contract](#b02-source-contract-20261003) defines all four arms.
The one accepted operation completed at **2026-10-03 15:58:22.598810 UTC**, exit0.
All **68 H500 missions**, **34,000 native transitions**, **204 actual planning
opportunities**, and the complete uncompressed numerical reader finished. The
reader reconstructed **34,068 saved native snapshots**, every motion/reward check,
all model branches, stationary banks, segment certificates and actual decisions.
There were **0 fits, 0 optimizer updates and 0 new teacher labels**. No exposure,
stopping rule, candidate set, seed, scope or metric changed after launch. No formal,
admission, worker, full-reader or resource failure occurred and there was no retry.

The compact [result](../../../../runs/uav_planning_opportunity_timing/b02_rolling_timing_a01/result.json)
contains all six comparisons and all world vectors, complete opportunity readings,
all scoped executed forecast checks, individual adverse records, program identity
checks, source identity and costs. Tables below are mechanically projected from
its `core_reading.comparisons`, `individual_continuity_comparisons` and
`by_arm_costs_including_audit`, which preserve the original reader outputs. The
source config and native launch/status/exit records are beside it. The DM read all
world/arm choices, all metric contrasts, forecast scopes, individual losses and the
complete resource accounting; exit0 alone is not this disposition.

The estimand is the **16 fresh common worlds 29524000…29524015**. The four missions
at engineering world29524900 are excluded. Intervals use the fixed10,000 common
paired-world bootstrap draws with seed29524991. These are exploratory world-sample
intervals, not confirmation, training-seed uncertainty or68/800 independent
replicates; the six displayed comparisons are not a multiplicity-corrected family.

| Contrast | Mean J [paired-world 95% interval] | J + / 0 / − | Mean served [interval] |
|---|---:|---:|---:|
| A_E4-A_E | +0.003381696 [+0.001431760, +0.005597273] | 11 / 5 / 0 | +0.269875 [+0.090250, +0.484756] |
| A_E4-G_E4 | +0.005336419 [+0.001650346, +0.009669445] | 12 / 4 / 0 | +0.463125 [+0.130747, +0.841506] |
| A_E4-A2 | +0.004566894 [+0.002073338, +0.007325428] | 15 / 1 / 0 | +0.349125 [+0.138247, +0.588503] |
| A_E-A2 | +0.001185197 [+0.000142142, +0.002285706] | 14 / 1 / 1 | +0.079250 [-0.050253, +0.196003] |
| G_E4-A_E | -0.001954723 [-0.005266627, +0.000988033] | 5 / 4 / 7 | -0.193250 [-0.529259, +0.103262] |
| G_E4-A2 | -0.000769526 [-0.003405011, +0.001844771] | 8 / 2 / 6 | -0.114000 [-0.395250, +0.164031] |

| Contrast | Mean quality [interval] | Mean path m/UAV [interval] |
|---|---:|---:|
| A_E4-A_E | -0.000687470 [-0.004102562, +0.002886155] | +67.375228 [+16.020910, +122.419048] |
| A_E4-G_E4 | -0.003150998 [-0.007614071, +0.000774010] | -4.638593 [-46.617787, +35.513425] |
| A_E4-A2 | -0.001114833 [-0.004190136, +0.001828368] | +25.259314 [-33.537579, +84.010705] |
| A_E-A2 | -0.000427363 [-0.001972297, +0.001323250] | -42.115914 [-90.356097, -3.966274] |
| G_E4-A_E | +0.002463528 [-0.002019495, +0.007603730] | +72.013821 [+12.902804, +134.466801] |
| G_E4-A2 | +0.002036164 [-0.002135209, +0.006331345] | +29.897907 [-38.706586, +102.848288] |

The primary median J difference is **+.001202918**; its five exact J ties are
worlds00/03/09/13/15, and the saved **complete native arrays** are bitwise identical
there. The eleven other worlds improve J; none lose J on this finite panel. The
largest share of signed primary net J gain is world04's26.0825%, followed by
world02's18.9560%; this result is less concentrated than B01's55.8% single-world
share, without establishing population monotonicity. Mean service gains coexist
with losses of .016 and .006 in worlds07 and11. Mean path rises67.375m/UAV and
mean quality falls slightly with an interval spanning zero. The primary mean
active-count change is−.00625, eligible-unserved+.0025, ineligible−.272375 and
height penalty+.0001903125; world12 contributes a+.00306 height-penalty change.
A positive J result is not shorthand for every native outcome improving.

The matched-rights A_E4−G_E4 J median is+.000458391; its four full-native identity
worlds are09/10/13/15. The largest net J share is world11's27.4596%. Service is
lower by .04 in world06 despite positive J. This supports anticipation's increment
within the common four-opportunity rule and actual lawful input contract. It
compares complete selectors, including the clocks their own choices induce; it
does not identify a pure timing coefficient at fixed native trajectories.

Fresh A_E−A2 remains J-positive on average, with a smaller effect than B01 and one
adverse world12 (J−.003347934, service−.638). Its service interval crosses zero and
its mean path saving is42.116m/UAV. B01 remains separate positive/adverse evidence;
we do not pool the two panels or revise the old outcomes. G_E4's mean J and
service fall against A_E and A2, with intervals spanning zero. Its positive local
outcomes, especially worlds06/10, and cheaper compute remain real alternatives;
an uncertain adverse average does not prove every greedy program useless or
statistical equivalence. Equal whole-team served p05/minimum/zero counts/longest
zero-run in all these comparisons do not establish individual continuity.

| Contrast | Served ticks + / equal / − | Longest gap shorter / equal / longer | Never-served rescued / new | Worst served-tick loss / longest-gap increase |
|---|---:|---:|---:|---:|
| A_E4-A_E | 24 / 750 / 26 | 23 / 756 / 21 | 4 / 0 | -397 / +397 |
| A_E4-G_E4 | 69 / 654 / 77 | 66 / 664 / 70 | 6 / 2 | -439 / +440 |
| A_E4-A2 | 65 / 702 / 33 | 61 / 708 / 31 | 5 / 0 | -430 / +415 |
| A_E-A2 | 50 / 727 / 23 | 46 / 730 / 24 | 1 / 0 | -431 / +434 |
| G_E4-A_E | 68 / 670 / 62 | 62 / 681 / 57 | 4 / 4 | -438 / +439 |
| G_E4-A2 | 74 / 671 / 55 | 65 / 683 / 52 | 4 / 3 | -438 / +439 |

Each row covers the same800 matched **user-within-world records**, not800
independent draws. The complete reader retains every observed gap and both
mission-edge censoring flags; a terminal observed gap is not an observed future
return-to-service time. A_E4−A_E has24 users gain served ticks,26 lose and750
unchanged, despite all26 losses lying in J-positive team worlds. In world29524002,
user7 falls492→95 served ticks and its longest observed gap grows8→405 while team
J and service improve. There are four never-served rescues and no new never-served
users against A_E. Against G_E4, however, six rescues coexist with **two newly
never-served** users (world02/user20 and world11/user42). The latter falls439→0
served ticks and its gap grows60→500 in a team-positive world. Result-panel
never-served totals are A2=37, A_E=36, G_E4=36, A_E4=32. These outcomes constrain
fairness/default-adoption claims without erasing the measured team capability.
Travel is absent from the fixed native J; no post-result weighted utility or new
adoption threshold is invented to collapse these different costs.

**What the actual programs establish.** All17 A_E4/A_E first scientific searches
have identical payloads under the declared `ae/first` identity mapping. Their
saved native prefixes agree until the actual second input (t60/70/80), and all
arms agree beforet40. A_E4's actual second choice nevertheless differs from A_E
in worlds05/07/08/12/14; worlds08/12 choose stay there and initiate a later third
commitment. Thus the added package already changes at the second selector. Five
A_E4 worlds with both late choices stay happen here to have full-native identity
with A_E, established by the actual arrays, not by using late stay as a proxy gate.

On the16 result worlds, A2 initiates30/32 opportunities, A_E31/32, G_E4 42/64 and
A_E4 46/64. The A_E4 ordinal commitment counts are16/13/10/7 and G_E4's16/12/8/6.
All menus retain their actual2…5 candidates including nonpositive champions;
every initiated actual plan has nonzero path. No fifth opportunity, hidden deeper
search, phase reset, forced remuting or candidate pruning appears. Actual A_E4
commanded durations are10…30 with2…27 physical moving ticks; G_E4 includes40-tick
commands and up to31 moving ticks. Planning eligibility still excludes the
immediately preceding mover, while lawful nonadjacent revisits occur at A_E4
world05/op4/member6 and world06/op4/member5, and G_E4 world00/op4/member5. Ordinary
subsequent C/E can remute initiated movers:11 A_E4 plans and7 G_E4 plans do so,
versus2 in each two-opportunity arm. A commitment is not permanent activation.
All actual fourth opportunities occur by t140; latest commanded arrival is160
for A_E4 and180 for G_E4. The configured maximum remains t190/t230. These are
four finite **early** opportunities followed by ordinary C/E, not sustained
throughout-H500 cooperation or an optimal opportunity count.

**Forecast scope and numerical reading.** Complete same-source, uncompressed
reconstruction and identity checks pass. Across all221 declared executed forecast
scopes, commands, masks and per-tick service agree with native execution. Largest
coordinate discrepancy is0.0000535236493988m and largest absolute ordered J-total
discrepancy is0.00000209734395185; these are lawful model/native FP32/FP64 readings,
not a bitwise claim about those distinct paths. The early scopes end before the
next actual selection as declared (G_E4 first3, A_E4 first2). In A_E4 the first
model's assumed ordinary next choice differs from the actual anticipatory second
choice in worlds05/07/08/12/14; the second model's next choice differs from the
actual third in04/06/07/11. Those full early model tails are **not** predictions
of the complete rolling controller. A_E4 ordinal3 retains both its prefix check
and complete remaining-program check; ordinal4 retains the full remaining check.
Successful ranking usefulness therefore coexists with an intentionally different
future policy; neither local positive model differences nor forecast agreement
replace the complete native comparison. Unexecuted branches remain model values,
not additional native counterfactual outcomes.

**Full measured price.** Every arm's audit mission is included in this table;
reader work is additional to worker work.

| Arm, 17 missions including audit | Worker episode CPU-s | Full uncompressed reader CPU-s | Actual worker state/mask requests | Logical requests in each complete pass |
|---|---:|---:|---:|---:|
| A2 | 1139.638566 | 3407.621381 | 14,267,269 | 54,439,585 |
| A_E | 1124.744185 | 3750.476844 | 13,615,630 | 60,078,256 |
| G_E4 | 658.113353 | 2156.604621 | 8,356,942 | 34,017,852 |
| A_E4 | 2542.875040 | 8362.016482 | 30,024,152 | 135,935,079 |

A_E4 worker CPU is **2.260847× A_E** and **3.863886× G_E4**. Including their full
uncompressed readers gives2.236799× and3.874239× respectively. A_E worker CPU is
.986931× A2 on this new panel (1.072123× including reader); B01's historical
1.01065× observation is unchanged. These are measured CPU scopes on the selected
host and implementation, not portable response latency. Other accepted direction
workers overlapped parts of this operation and are recorded in its resources.

Worker episode computation costs5465.371144CPU-s; full reader episodes cost
17676.719328CPU-s, total23142.090472CPU-s. The broader runner meter, including
imports/common work/reaped children, is23674.032120CPU-s. Adding bound preparation
42.135112454CPU-s and the one formal-launch scope9.945715CPU-s once gives
**23726.112947454CPU-s =6.590587CPUh** through its final sample. Separately logged
support fragments so far total12.340501CPU-s in `support-waits.jsonl`, plus initial
observer.612463, initial support-record.082149 and terminal-observer closure
.218684CPU-s. The final saved-data hash/result extraction3.669233CPU-s is already
inside that12.340501, not an extra charge. Later publication/cleanup scopes are
reported below where measured. Source/control inspection, tool overhead, manual
reading/reasoning, observer/status lifetime and final-write tails are not fully
metered and remain **unknown, not zero**. Therefore6.590587 is not an exact
all-inclusive project/support total. Earlier A01 failure and B01's approximately
3.26048CPUh and unknown support remain cumulative investment, not a balance
available for B02.

The last runner sample records23400.151221 monotonic operation-wall seconds
(6.500042h) from the formal request, not a sum of overlapping subprocess walls;
UTC request-to-exit duration is a separate clock measurement. Observed owned
allocated-byte peak is2693521408 (2.509GiB), and runner peak RSS399020KiB. No
science-reserve or hard-envelope excess was detected, and stop_reason is null.
The24CPUh/48operation-wallh/12GiB new purchase, included mock subtotal and terminal
reserves were not exhausted. The prior6–12CPUh range,6.538530 center and17.793465
no-reuse sensitivity remain forecasts, not fitted retrospective guarantees.

Actual worker logical counts are284470772 state/mask requests,1085480 model
physical ticks,594 stationary banks,203400 candidate rows,4094440 candidate-transit
ticks,2628 complete model branches and3018 segment certificates. Exact reuse
reduces worker requests to66263993 and computed model ticks to183128, with902352
reused. The complete independent reader separately computes all284470772 logical
requests and1085480 ticks; combined worker-actual plus reader requests are350734765.
The other listed logical objects are also separately paid in each pass. These
counts do not subsume the34000 native transitions and their RF/observation work,
snapshot reconstruction, hashing, serialization or reduction overhead. Zero fits
never meant zero or negligible research cost.

**Evidence, operations and interpretation.** All68 source-binding checks and all
6122 retained raw/catalog/cell-status artifact hashes and byte lengths were checked
after completion:804162344 logical bytes, canonical tree SHA256
`7c12c6ff11307d5c06f4bde6e7b6a673af2d64a4bc0b86307ff28283f82d54f4`.
The one durable evidence location remains local_linux at
`/home/fires/hmasd-wsl/runs/uav_planning_opportunity_timing/b02_rolling_timing_a01/`.
Original `summary.json` is10448432bytes/SHA256
`81391ce7afabcf9c524d2d65d94bca5e4f1d88b08c212a1c5ad8a7115562de9f`;
original `reading.json` is11702306bytes/SHA256
`fdcdcad5f508b16278a3ac8124f9640a4f6952c45e0a7c21d7e49fc4799e1b69`;
`config.json` is30486bytes/SHA256
`44e01f34e4453eb9cbb2553152a7a789ef8c6bfb5df8c941b9f6cab5fd087e67`.
Raw arrays and large original readings stay unchanged in that one location; the
compact result and source/native recovery records are published in Git.

The native child stayed active through deterministic waits on the same accepted
handle. Observer checkpoints were drained/rearmed through generation29; native
child queue deliveries returned−32600, without invalidating process observation.
At completion both recorded native processes were absent with valid exit0 evidence.
The terminal event was consumed, generation30 was stopped and drained with no wake
or pending events. These records distinguish the actual terminal read from an
assumed queue return. There is no live producer or future experiment dependency.
Two manual saved-JSON helpers needed corrections (optional `zero_path` on a stay;
including68 cell-status metadata files in the artifact union); neither reran
science nor failed the required numerical reader. Their original unmetered
support is retained as unknown, not recast as zero or as an experimental failure.

Runtime compaction independently verified then removed1560 redundant prefix/suffix
files; all exact targets are in `summary.cleanup` and compact `runtime_compaction`.
All are absent. It removed111906816 allocated file bytes and reclaimed
**111951872 net allocated bytes** including directories. These were reproducible
duplicates; all unique required positive/adverse/failed evidence remains. Final
snapshot/scratch reclamation is reported in the subsequent closure entry.

This reading strengthens **task opportunity**: additional early closed-loop use
of the existing two-layer ordinary selector produces useful native consequences,
and same-rights greedy control does not absorb its mean gain on this panel.
**Representation** remains the same lawful133-FP32 report, actual mask and private
C history; this study does not compare encoders or grant additional information.
**Learnability** is untouched because nothing was trained. **Complete-package
value** is conditional: the native gains are real under the fixed objective, at
higher compute and with serious individual-service losses. Useful capability,
universal adoption and further investment are separate decisions.

Current published background was refreshed at main`0a621fd228f84d99f87e6acc4a43a630d430ca16`
before this interpretation's publication. The ordinary planning capability topic
and event-order topic are directly affected: extend their finite-use judgment,
preserve B01's contrary worlds, and distinguish early forecast scope from actual
rolling control. No wider background rewrite or new explanation is needed.

**Disposition and recommendation to Root:** keep A_E4 as a demonstrated conditional
ordinary reference, preserve A_E/A2 and cheaper G_E4 with the full comparison, and
close this purchase with no queued scientific work. The positive result permits
future development; the cost ratio is a concrete reason to consider reducing the
whole useful controller's cost if Root selects another purchase. It does not
establish an amortizer, a useful-world selector, a fairness remedy or a learning
advantage, and none is launched here. Root owns the next cross-question allocation;
this is a recommendation at the assigned boundary, not an owner permission blocker
or a claim that the parent question is exhausted.
