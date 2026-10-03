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
