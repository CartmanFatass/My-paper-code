# UAV per-user accumulated waiting

## 2026-09-30 — B01 prospective ordinary fairness comparison and L0

**Question:** Can lawful accumulated per-user burden improve complete worst-user
waiting beyond oldest-first O while retaining a useful aggregate service/age
tradeoff against W/M? This is ordinary task-performance/empirical-understanding
work, zero fits; it neither repairs nor reopens the old learned selector.
Root selected this independent question under the native-DM trial. The completed
selection review is being preserved in
[the parallel-allocation review](../../archive/2026-09-30/RESEARCH-parallel-allocation.md);
its actual full response will be read before accepting implementation.

### Inherited explanation and decision exposure

Current published main `b45d15745de100eb9209141ec8a81c8c82a5d148`,
[shared background topic 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练)
and [topic 8](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验)
distinguish aggregate age, worst-user waiting and periodic coverage. Their concrete
effect here is to retain O as the primary fairness comparator, W/M as useful
aggregate-age/service alternatives, and full trajectories rather than treating
accurate short predictions as complete benefit. The source
[age reading](../uav_service_age/NOTES.md#b01-complete-reading), input
`d4430e6198f95d599b79f23575445a18e6566c26`, compact result `0b358981a`, records
W−O aggregate age −1.086826/service +5.809448/J +.073966 but worst-user mean age
+2.822327 and maximum gap +6.859375. O/W/M worst-user means are
10.829956/13.652283/13.001892. L1's own-initialization gain remains real but L1 lost
to W/M; its 189/183/181-tick closed waits had correct lawful model ages at every
anchor. Missing age or missing ACK is not the diagnosed cause. The original
[O/P](../uav_registered_service/NOTES.md#b01-complete-reading),
[G/O](../uav_registered_service/NOTES.md#b02-complete-reading) and
[two-tick radio](../uav_radio_activation/NOTES.md#b03-complete-reading) contracts
retain their coverage/service/travel/quality and immediate-positive/complete-negative
counterexamples.

The conjecture is that repeated burden matters beyond current age: R remembers
which user accumulated waiting earlier, affecting meaningful motion/mask ranking
now and reducing the worst individual complete mean. Competing explanations are
historical overcompensation, unreachable users under the current action support,
or O already providing the better fairness/service compromise. This changes the
objective and history summary, not information rights or action support. Joint
interference and whole-team commitment remain coupled; no single-server AoI
optimality theorem is assumed, and no novelty claim is made.

### Fixed comparison, numerical contract and cost

- R/O/W/M, 64 common fresh worlds with seeds **29321000..29321063**, fixed before
  exposure; 256 complete H256 episodes, 65,536 native steps, zero fits or optimizer
  updates. Eight cyclic arm orders (R,O,W,M and its reverse, all four rotations),
  assigned by world index modulo eight. All worlds/users remain; users and slots
  are not independent world n. No pilot or extra result-bearing test.
- N5/U50 native host; immutable 400-byte registered integer-XY map decoded float64,
  quantized five-UAV anchors and current five C proposals every four ticks. Replace
  only the rotating member's proposal, leave other four proposals fixed. Entire
  commands/mask arrive in two ticks and hold four; preserve initial two committed
  ticks, final two-tick truncation, current nonempty mask and all fallback behavior.
  Communication .544s and charged computation allowance 1.456s retain the original
  host meaning. No live user coordinates, service identities, ACK, private truth,
  extra refresh or new future-C policy enters any actor.
- `S_u(t)=sum_{s<t} a_hat_u(s)` is accumulated only from settled executed command/mask
  history and decoded anchors. Native age resets to zero on service, increments
  otherwise. Private copies propagate the known two-tick prefix then candidate
  block. R ranks by `(-max_u S_u(endpoint), -sum_u S_u(endpoint), native/tie keys)`
  at every inner and final selection of the retained two-order search. Native/tie
  keys are `(J, served, q==proposal_q, mask.bit_count(), -mask, -q)`. Integers use
  int64; physics is existing float64. Missing initial history remains censored:
  no missing transition is invented, reconstructed burden carries an incomplete
  prefix flag which does not clear after later service. Forecasts never settle.
- R/O/W use 27+31+31+27=116 candidate requests total per report, not per order;
  M generates O/W with 232 before cache. No 837-plan grid. Dominant prospective
  work: 2,375,680 requests and at most 9,502,720 post-prefix candidate-state
  reductions, plus settled history/prefix/native/reader work. Prior O/W/M scheduler
  cost is 3.371/3.692/4.666 CPU seconds/episode; if R resembles W the whole panel
  is about 987 scheduler CPU seconds, not a total estimate or upper bound. R's
  actual cost is unknown. Record full worker/reader and storage costs; single
  process with one BLAS/OpenMP/PyTorch thread, configured provisional wsl_4070
  interpreter, fresh actual-node admission at launch. No runtime stress study
  absent a recurrence.
- Primary actual endpoint `F_user = max_u sum_{t=0}^{255} age_u(t)/256`, with
  post-transition actual ages. Primary paired R−O (negative favorable); R−W and
  R−M, aggregate A/service/J/quality, per-user max/closed/censored gaps, never-served,
  four-window coverage F, zero-service, travel, transmitter-on exposure and all
  runtime/request/deadline measurements are retained. Report per-world levels and
  paired differences, mean/SD/range and descriptive paired t95 intervals. No
  invented equivalence margin or scalar exchange rate among fairness and costs.
- Record whether accumulated settled burden changes choices within R's actually
  visited candidate sets, compared with the same forecast costs after subtracting
  the settled per-user burden; also compare same-set O ranking. These are ranking
  sensitivity diagnostics, not a complete counterfactual O/no-memory trajectory.
  Native R/O/W/M differences remain the complete-package comparison.
- Full reader reconstructs every actual trajectory/age/periodic endpoint and lawful
  settled history, R integer burdens and candidate ranking arithmetic independently
  of R's implementation. Reuse frozen O/W/M reader contracts. Verify every selected
  candidate's physics plus all evaluated pairs at reports 0/60/124/252, using the
  shared radio kernels. No new native episodes in the reader.

If R improves worst-user waiting beyond O with useful aggregate cost, retain the
new ordinary reference conditionally. If fairness improves while aggregate
age/service worsen, retain the explicit frontier rather than a loss-free default.
If dominated, inactive or worse on the primary, end this fixed-burden recipe;
no threshold/ACK/horizon/exponent scan or selector fit follows automatically.
Interpretation and the next worthwhile comparison receive an independent scientific
reading; Root chooses any cross-question pivot. The broader fairness question need
not be empirically refuted by declining further investment.

### L0 implementation scope

Direction-owned `experiments/candidates/uav_user_waiting/b01/`, mirrored tests,
this notebook, run directory and scratch only. Reuse frozen radio/history/search,
C and O/W/M implementations without editing their modules. Implementer receives
one bounded behavior: R's causal accumulated-burden history/ranking scheduler and
focused correctness tests (`scheduler.py`, `history.py`, `test_scheduler.py`). DM
owns collector, complete reader, metrics, runner, acceptance, notebook and Git index.
Both author shared main; no other writer's edits are reverted. Independent engineering
review covers high-risk behavior before publication/execution.

Checks must include exact small integer recurrence and independent ranking oracle,
both search orders/request count, private forecast isolation, late-anchor censoring,
atomic deadline settlement and complete fallback, final block truncation and
saved-record replay. Native correctness fixtures are bounded tests, not scientific
pilots, and their counts/cost remain separate. Stop for a material contract mismatch
or undeclared cost expansion; ordinary implementation choices remain in scope.

### Selection review read and adopted

The complete independent Astra Max response and Root disposition were read at
published `97927817dfc4b8c15e2e07f4284b6ec2a8df8a15`,
[full review](../../archive/2026-09-30/RESEARCH-parallel-allocation.md#full-independent-response).
`MATERIAL_DISSENT: no`. I adopt its substantive prescription: O is primary,
W/M remain essential aggregate alternatives, exact accumulated individual burden
is the sole intervention, and complete outcomes may expose overcompensation or
limited reachable support. The review directly checked the original source and
age contrasts and covers this unchanged selection; no duplicate selection review
or Pro round is needed. The richer fleet comparison is a different owner's work,
not a dependency or a control here. RESEARCH now lists this direction exploring
with the assigned native lead; no owner pause applies to this selected comparison.

The input/source identity set inherits frozen host/O/W/M dependencies and adds only
this direction's code. Full raw records keep R per-user settled, prefix and
candidate-endpoint burdens as int64; their incomplete-prefix flag is permanent
after a late initial anchor. Diagnostic comparisons are explicitly limited to
R's actually visited stage sets and final two/visited union. They cannot assert
what a no-memory or O search with a different path would have executed.

### Implementation accepted; fixed launch preparation

DM read and accepted the Implementer's three-file diff. `ServiceHistory` extends
the frozen summary and preserves its subclass on copy; frozen `ExecutionHistory`
still controls atomic settled transitions and anchors. R uses the same physical
kernels and two-order search, with eight exact lexicographic key components.
The direction collector preserves the old event order and records actual service
before arriving masks mutate radio state. O/W/M modules remain unchanged.

The 19 scheduler tests cover scalar integer recurrence, permanent prefix
censoring, memory-sensitive rankings, private copied forecasts, full saved-record
candidate physics/key replay, both search orders and all deadline phases. They
passed in the Implementer's scoped 18-test/1.79s and added-test/.52s invocations,
with zero native environment steps. Seven DM collector/metric/reader checks passed
first in3.82s, then in3.29s after adding serialization coverage:40 native fixture
steps each,80 total. External measurements were4.70/4.19s wall,
6.65/6.15s user+system CPU and304528/305824KiB process peak RSS. These are
correctness work, not fits or result-panel exposure.

Independent registered Engineering Reviewer `engineering_review` received the
contract and source in a separate context. It reproduced a direct-reader CLI
relative-import defect; I repaired it to absolute imports and direct `--help`
then passed. The reviewer found no remaining material engineering problem after
26 checks/3.77s plus two affected checks/2.23s (56 additional native fixture
steps, zero fits). It checked history/censoring/private forecast semantics,
search/counts, delivery/fallback, endpoints, reader arithmetic and admission order.
It did not run the destination runtime or full panel. Thus total native
correctness exposure to this boundary is136 steps; other review/source-reading
CPU is incompletely measured, not zero.

All new code and prospective records are ready for exact-input publication.
Selected tag **b01_burden_a01**; run entry `b01/run.py --seed 29321000`, fixed
four-program/64-world contract above. Reader is direct `b01/read.py --out` on the
same accepted source snapshot and canonical output. No test/bypass production
flag exists. The node's maintained launcher and provisional compute configuration
match published bytes; its older canonical index needs narrow synchronization
before current direction/lead and actual-memory admission. Preserve all unrelated
dirty files and existing operations. Neither a launch acceptance nor exit0 will
be reported as a scientific result before full verification and diagnosis.

### B01 original operation accepted

Exact input `86ae782cab3946a14062d3e0825c8597ea4513a7` was published before
execution. The original `b01_burden_a01` was admitted on wsl_4070 at
2026-09-30T11:20:41Z; see the
[native manifest](../../../../runs/uav_user_waiting/b01_burden_a01/launch-manifest.json)
and [actual-node preflight](../../../../runs/uav_user_waiting/b01_burden_a01/admission-preflight.json).
It passed the4GiB memory floor with14,682,673,152 bytes available. The manifest
binds source, command, snapshot, interpreter, operation and native process
identities; this remains one invocation and one fixed panel.

Prelaunch control preparation required the configured `zsh -lic` for Git network
operations, including lazy blob retrieval by `git show` in the partial clone.
Two plain-shell support requests stalled and only those owned prelaunch process
trees were stopped; no scientific operation existed then. Published controls were
synchronized under the node writer lock, preserving foreign edits. Fetch completed
despite the node's pre-existing commit-graph/repack warnings; no Git repair,
sparse-selection change or extra runtime stress work was performed.

Deterministic observation uses the same original claim handle. An initial request
was rejected for a relative `ssh` executable and then an incorrect `launch-status`
reference: the status command requires a manifest or operation claim. These were
observation errors, not worker failures. The blocked event was consumed in
generation2 and the corrected same-operation probe registered in generation3.
Native child queue delivery was explicitly rejected (`-32600`); this DM remains
active and drains/rearms locally instead of ending the turn or moving its handle.
The original worker remained running with consistent native identities throughout.

At the generation3 checkpoint (2026-09-30T11:37Z), the original process remained
consistent/running and summary counts were224 complete episodes/57,344 native
steps, zero fits/updates, no technical error. No outcomes were selected or batch
conditions changed. The checkpoint was consumed and observation rearmed in
generation4 against the same claim for a300-second window; this does not restart
the worker. Full readback and independent scientific diagnosis remain outstanding.

Reader-observation L0: the pure saved-data reader will run under one named
`agent-task` from the accepted snapshot, with external time accounting. A disposable
read-only adapter in this direction's scratch will bind its supervisor name,
PID/start ticks/boot ID/start time and wrapper digest, and normalize genuine native
status into the existing wait controller's launch-probe shape. It does not launch,
retry or validate scientific results. Bounded mocked identity/classification tests
and focused independent engineering review cover this observation-only code; the
accepted worker, reader and scientific inputs remain unchanged.

### Original worker terminal; complete reader accepted

The original worker exited0 at2026-09-30T11:40:10Z; generation4 READY was
drained and consumed into generation5. Native exit witness, absent recorded
runner/supervisor and accepted consistent operation agree. Counts are exactly
256 complete episodes/65,536 native steps, zero fits/updates. Full scientific
verification remains outstanding; collector summaries alone are not the read result.

The original saved-data reader was accepted once under native `agent-task`
`uav-user-waiting-b01-reader` at11:43:17Z (task start epoch1790768597). It uses
the unchanged86ae782cab3946a14062d3e0825c8597ea4513a7 snapshot and canonical
output, one BLAS thread and `/usr/bin/time -v` accounting.
[Bound supervisor identity](../../../../runs/uav_user_waiting/b01_burden_a01/reader-supervisor.json)
preserves its PID/start ticks/boot/task start and wrapper digest. The disposable
observation adapter does not create an official launch operation or assert
scientific validity. Independent engineering review has checked its status/exit
semantics against the actual native wrapper and one stable running observation;
mocked checks and final review disposition will be recorded before observation
acceptance. Independent scientific diagnosis has begun in a separate context with
the original supporting/adverse evidence and complete, explicitly unverified
collector summaries; its interpretation is conditional on full readback.

DM read and accepted the observer implementation and mocked identity/consumer
checks. Implementer65 checks/.09s and independent Reviewer65 checks/.07s
passed; zero native steps/fits, no retries or launches. The Reviewer found no
material remaining issue after the actual remote wrapper/source inspection and
one permitted stable running observation. Races, stale identities or conflicting
exit files remain unknown; same-handle observation can be rearmed. This narrow
adapter establishes no launch-kernel guarantee or scientific validity.

<a id="b01-complete-reading"></a>
## 2026-09-30 — B01 complete reading: retain a worst-user-mean capability and its temporal-tail costs

The original saved-data reader exited0 and the generation6 READY event was
consumed into generation7; the observer was then stopped without changing either
completed operation. Native wrapper status, immutable binding and absent process
agree. **All256 fixed trajectories are VERIFIED_COMPLETE**, source
`86ae782cab3946a14062d3e0825c8597ea4513a7`:65,536 native steps, zero fits/updates.
The [compact result](../../../../runs/uav_user_waiting/b01_burden_a01/result.json)
retains all64 world levels/paired differences, all per-user means/gap summaries,
exposure, source/native identities, ranking diagnostics and raw artifact hashes.

The full reader checked every native/C/age/periodic/history record, independently
reconstructed R's integer burdens and candidate keys, and verified125,931 candidate
physics pairs within the declared subset. All65,536 lawful model transitions were
reconstructed. Maximum native-J discrepancy was5.55e-17; native SINR and observation
discrepancies were zero. The radio kernel is shared, not an independent physical
model. Quantized-anchor reconstruction is not exact service truth: R has470 false
positive/438 false negative model user-service flags, and all64 R worlds have some
settled-burden discrepancy (largest absolute user burden error1036). The primary
outcomes below use actual native service, not those predictions. No history prefix
was unavailable or censored and no deadline was missed in any arm.

| Mean over64 common H256 worlds | R | O | W | M |
| --- | ---: | ---: | ---: | ---: |
| Worst-user complete mean age, primary `F_user` | 9.200317 | 11.089661 | 12.947205 | 11.948669 |
| Aggregate mean age `A` | 4.433879 | 4.500314 | 3.256572 | 3.205242 |
| Served users/tick | 21.576599 | 18.702637 | 24.455017 | 24.316101 |
| Native mean J | .360902 | .322828 | .396148 | .393546 |
| Within-episode pooled age p95 | 19.422656 | 16.923437 | 15.265625 | 14.860156 |
| Mean per-user maximum unserved gap | 27.491875 | 24.104375 | 20.475000 | 20.189687 |
| Episode maximum gap | 54.171875 | 52.734375 | 56.453125 | 53.937500 |
| Four-window coverage F, maximum200 | 199.984375 | 199.984375 | 199.890625 | 199.921875 |

The fixed primary **R−O F_user is−1.889343**, descriptive paired-world t95
**[−3.013856,−.764831]**:45 improving/19 adverse worlds, median−1.634766.
R−O service is+2.873962[+2.594064,+3.153861] users/tick and J is
+.038074[+.034459,+.041689], both positive in all64 worlds. Aggregate age is
−.066434[−.243032,+.110163],33 improving/31 adverse; this does not establish
equivalence or loss-free preservation. Quality decreases−.007206
[−.012447,−.001965]. Mean path decreases478.944m/UAV, while transmitter exposure
increases82.9375 team-transmitter ticks/episode in every world (mean active
transmitters+ .323975). No energy outcome was modeled.

The temporal-tail costs are consequential even versus O. R−O pooled age p95 is
**+2.499219[+1.616429,+3.382008]**,46 worse/10 better/8 same worlds. Mean
per-user maximum gap is **+3.387500[+2.394902,+4.380098]**,50 worse/14 better.
Episode maximum gap is+1.437500[−2.442717,+5.317717], and maximum closed gap
+2.687500[−1.168649,+6.543649]. Therefore lower worst-user time-average burden
is an observed capability with measured temporal-tail costs, not general waiting
protection. Pooled user/tick quantiles are episode endpoints; inference n remains64
independent worlds, never users or slots.

Against W/M, R improves worst-user mean age by3.746887/2.748352, with descriptive
intervals[−4.853055,−2.640719]/[−3.785615,−1.711089] for the R contrasts;
52/47 worlds improve and12/17 lose. R increases aggregate age by1.177307/1.228638
and reduces service by2.878418/2.739502 users/tick. R−W/R−M J is
−.035246/−.032645. R retains higher quality and lower transmitter exposure than
both, but pooled age p95 and mean per-user maximum gaps also increase. Maximum
right-censored gap increases4.640625[+.434961,+8.846289] versus M. These are
different useful tradeoffs; no scalar exchange rate, adoption margin or general
dominance rule was invented. All arms eventually serve every user; F<200 occurs in
1/1/6/5 worlds and zero-service steps total1/16/0/0 for R/O/W/M. Near-complete
periodic coverage does not imply favorable continuous waiting.

### Ranking use and complete adverse witnesses

Every R report was timely and its selected commitment executed;2037 reports changed
the rotating member's C proposal, with no clipped aliases. Across4096 R reports,
removing settled burden within the same visited stage sets changes at least one
stage's winner in2280 slots (4886 stage differences), the final-two choice in199,
and the visited-union best in2126. Same-set O ranking changes those respective
counts to3598 slots/8392 stages/444 final-two/3208 visited-union choices. These
checks show active ranking dependence, but changed search paths and complete
no-memory/O counterfactual outcomes are unmeasured. Complete R/O/W/M contrasts
support package value; they do not isolate historical memory as the causal source.

Independent Scientific Reviewer reconstructed actual ages from the canonical raws
for all four arms in the strongest R−O gain and loss worlds, checked the hashes and
common initial world inputs, and inspected the original adverse L1 raw. These are
post-result saved-data readings, zero new native steps/fits; their support cost is
incompletely metered. The review preserves both consequential examples:

- **29321040:** R F_user10.570313 versus O32.160156. O's worst user44 has
  closed83/91-tick gaps despite correct reconstructed last-service times at all64
  anchors. O does not exhaust the opportunity under this lawful interface.
- **29321048:** R F_user17.203125 versus O8.5, the largest primary loss
  (+8.703125). R user13 has a **closed90-tick gap[71,161)**. Its reconstructed
  last-service time and accumulated burden equal actual values at all64 anchors.
  At report72, selected(q6,mask7) and four visited alternatives predicting service
  to user13 share maximum predicted burden1465, attained by user28. R selects total
  burden15790 over the alternatives16011/16057/16031/16038. Thus the secondary
  sum criterion decides while the primary maximum is flat. At reports76..152 no
  visited candidate predicts service to13; service is selected again at156/160.
  This is a finite-forecast/search and closed-loop redistribution witness, not
  proof of full-support unreachability or a diagnosed historical-overcompensation
  mechanism. It does not identify which earlier counterfactual prevents the gap.

The old L1 users49/26/40 in29312024 retain their189/183/181-tick closed waits
with correct model last-service times at every anchor. Missing age/ACK is not the
explanation for these specific failures; ACKs are not thereby proven universally
useless. Actual adverse evidence is preserved without an automatic plumbing repair.

### Complete cost and durable evidence

Result work is256 episodes/65,536 native steps/zero fits or updates. Actual search
cost is2,375,680 requests,1,676,660 unique completed candidate plans,
6,654,556 candidate-state reductions,1,755,648 geometry snapshots,65,536 settled
history transitions including terminal drain and32,768 private prefix ticks.
Inherited C adds81,920 decisions,2,211,840 trajectories/8,847,360 model ticks
and48,473,529 link evaluations, all counted separately rather than hidden by0fit.
Scheduler CPU totals1038.500s; R/O/W/M mean3.749983/3.618255/3.905659/4.952667s
per episode. R is.131727s above O and1.202684s below M. Largest charged report
wall is.162977s in M (R.115017s), below1.456s; no deadline crisis was observed.

Worker records1120.773s entry wall,1167.922s measured CPU and1169.178s lifetime
user+system CPU, peak647372KiB. Full reader records625.704s internal wall/
652.925s CPU; external `/usr/bin/time` includes imports and serialization:
**655.82s wall/654.89s CPU/534684KiB peak**, exit0. Combined worker lifetime plus
external reader CPU is**1824.068s (.506686 CPU-hours)**. Nested scheduler/C/
history/candidate/storage CPU must not be added again to this total. Correctness
exposure was136 native fixture steps; preparatory engineering, independent review,
observation and collection cost is additional and incompletely measured. This is
not a fit-only or total-wall upper-bound quote.

Sole canonical full evidence remains on **wsl_4070** under
`/home/wu/projects/HMASD/runs/uav_user_waiting/b01_burden_a01/`:256 NPZ files,
**296,862,326 logical bytes**, with individual paths/hashes in the compact result.
`summary.json` is4,688,407bytes, SHA256
`e2aa75d971fb1d84aaf2e2d64def80a361843acc6060cb3fc275521ec4fcb886`;
`reading.json` is5,156,449bytes, SHA256
`150eae3bb986e0e57d197b138dbbc30287f18c737e134215a21e420ad5b02389`.
Remote and collected summary/reading/config/native-exit/time digests were compared
after completion and match. The compact result is a field selection, not a rewrite
of either original full file. The useful scheduler/history/metrics/collector/
reader and their correctness tests remain published for conditional reuse.

<a id="b01-independent-review-and-disposition"></a>
### Independent scientific diagnosis and DM disposition

Registered ResearchCritic `scientific_reading` worked in a separate context with no
DM/Root conversation history. It reconstructed the new numerical result before
reading allocation advice, then compared it with the DM's proposed retention.
It checked53 source identities against both current bytes and86ae782, the fixed
config/order/seeds/all256 rows and paired statistics, scheduler/history/reader
semantics, eight new raw trajectories in the two extreme worlds and the inherited
L1 adverse raw. It did not repeat the full physical reader. Its completed advice
was explicitly conditional on that original reader passing; the condition is now
satisfied with the unchanged summary and no consequential verification mismatch.

**Reviewer recommendation: retain R as an ordinary reference for worst-user mean
age alongside O/W/M; select no additional experiment now. MATERIAL_DISSENT: no.**
Its consequential correction was to state measured p95/per-user-max-gap costs,
not merely the absence of a longest-gap guarantee. The report72 adverse choice
follows the secondary sum criterion on a flat primary, so historical
overcompensation is not an established failure mechanism. Same-set sensitivity
does not identify complete memory-mediated benefit. I adopt these corrections.

The explanation changes at the useful task level: objective-aligned ordinary
control can improve complete accumulated waiting for the worst user beyond this O
implementation under the same information/control rights. The available lawful
history representation is sufficient for this capability; its approximate model
errors and finite search still constrain what it establishes. No extra ACK or
future-C rights were used. Zero fits establishes nothing about learnability.
The package has a favorable worst-user-mean/service comparison to O with quality,
transmitter and temporal-tail costs, and a fairness/aggregate-service tradeoff to
W/M. It is a **conditional additional reference, not a universal default**.

I compared further investment with retention rather than turning a positive panel
into an automatic confirmation. An unchanged replication could sharpen world
precision but would not currently change reference retention or erase the observed
tail cost. A complete no-settled-burden control could identify mechanism, but that
attribution presently changes neither package usefulness nor a selected action.
ACK, horizon, penalty or learner changes have no diagnosed repair prediction here.
No extra run, confirmation, fit or sweep is selected. Pro adds no distinct unresolved
expertise/disagreement value to this decision beyond the adequate independent review.

The constructive re-entry question is a separately selected temporal-continuity
use case: a competent ordinary policy that anticipates loss of service continuity,
compared completely with R and O under equal information/resources, predicting
shorter temporal gaps while retaining a useful complete burden/service tradeoff.
No concrete policy, operational gap requirement or credible full cost is selected,
so this is a candidate question in the notebook, not a queued experiment or external
dependency. Longer horizons or different information/action rights likewise require
their own consequential question and prediction. Root receives the completed study
and chooses any cross-question allocation. This direction becomes reserve after
publication/cleanup; no owner decision, other DM result or recurring check blocks it.

### Publication and final cleanup started

Complete reading, independent disposition and compact evidence were published in
`0b9e2fee44edaf4183ae25aa8269136280f4826c`. The wait controller is stopped
in generation7, no unconsumed event remains and both original native operations
are terminal. The earlier incorrect status-reference probe remains a historical
blocked observer; it never restarted or replaced the successful operation.

Exact-target snapshot GC preview with the supported read-only sudo process scan
initially refused `b0c39dd04cef4a898b18c8095dd94a56`: “snapshot has changed,
untracked, or ignored files”. Inspect the named contents and current consumers
before removing only disposable runtime material; preserve this refusal. No claim,
manifest, scientific output or foreign snapshot was removed to make the tool pass.

<a id="b01-final-cleanup"></a>
### Final cleanup complete

The refusal was exactly45 ignored Python bytecode files in the completed source
snapshot; no tracked source had changed. Both native processes were terminal,
the observer was stopped, all bounded helpers had returned, and no remaining
source/test consumer required the disposable observer. Removing only those45
bytecode files and their empty cache directories reduced snapshot allocation from
808,284,160 to807,718,912 bytes. A second exact-target GC preview passed source,
durable Git reachability, terminal identities and the privileged read-only process
reference scan. Supported `--apply --snapshot b0c39dd04cef4a898b18c8095dd94a56`
then removed the snapshot; its path is absent. Claim, manifest and canonical
scientific outputs remain present. The initial refusal is resolved, not suppressed.

Deleted targets and measured allocated bytes (each target now absent):

| Deleted target | Net allocated bytes reclaimed |
| --- | ---: |
| wsl_4070 `/home/wu/projects/HMASD/.git/hmasd-launch-sources/b0c39dd04cef4a898b18c8095dd94a56`, including its runtime caches | 808,284,160 |
| Local `temp/directions/uav_user_waiting/` (observer, requests, extraction script/cache) | 53,248 |
| Local `experiments/candidates/uav_user_waiting/b01/__pycache__/` | 147,456 |
| Local `tests/experiments/candidates/uav_user_waiting/b01/__pycache__/` | 102,400 |
| Local disposable `tests/experiments/candidates/uav_user_waiting/b01/test_reader_observer.py` | 12,288 |
| Local run-directory duplicate `summary.json` | 4,689,920 |
| Local run-directory duplicate `reading.json` | 5,156,864 |
| Local run-directory duplicate `stdout.log` / empty `stderr.log` | 28,672 / 0 |
| Local temporary `reader-terminal.json`, preserved inside published result | 4,096 |
| **Total across the two nodes** | **818,479,104** |

The local subtotal is10,194,944 bytes. These are before/after allocated bytes for
the exact deleted targets, not Git-object pruning or a claim about whole-host free
capacity while other studies write concurrently. No backup, archive chain or
second raw copy was created. Useful source/tests, compact evidence and the one
necessary canonical copy of all256 trajectories/full readings remain. There is
no active worker/reader/observer, unread result/advice, selected successor or
concrete cleanup blocker. The direction is reserve with the conditional R/O/W/M
comparison and the re-entry reasoning above available to Root.

<a id="b02-continuity-design"></a>
## 2026-09-30 — Recommended ordinary continuity comparison; design only

Root selected this bounded design task after the complete B01 return: determine
whether anticipating service loss offers useful temporal control beyond the
accumulated-user fairness result. The intended contribution is an ordinary-control
capability and empirical understanding on the coupled host, not a learning or
novelty claim. **Recommend one fresh A/S/M/R comparison below for scientific
selection. No implementation, new native step, fit or result-bearing prototype has
been performed or selected by this design return.** Root's existing independent
allocation reviewer covers this decision; Root will take the concrete proposal to
Pro. These are assigned scientific producers, not a new owner-permission gate.

### Evidence, sources and choice

Published-main [topic 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
including the B01 update in `8e8ca5391` and Root's continuity plan in `04cf609a6`,
changes the comparison in two ways. Retain R's worst-user-mean capability and its
measured temporal costs; do not relabel its correct-history90-tick witness as an
ACK failure or a global reachability limit. Also, **M is the stronger existing
reference for the proposed typical-user temporal endpoint**, not O. In B01,
R/O/W/M mean per-user maximum gaps were27.491875/24.104375/20.475/20.189688;
pooled age p95 was19.422656/16.923437/15.265625/14.860156; service/step was
21.576599/18.702637/24.455017/24.316101. R retains the best worst-user mean9.200317,
versus M11.948669. These are common-panel observations, not universal rankings.
M already includes O/W alternatives; O and W therefore remain inherited evidence
without buying two more complete arms. This corrects my initial O/R-only framing
of the temporal-use comparator, following Root's independent review.

Primary passages read for this choice:

- Bin Li, Ruogu Li and Atilla Eryilmaz, *Throughput-Optimal Scheduling Design with
  Regular Service Guarantees in Wireless Networks*, [author PDF](https://www.ele.uri.edu/faculty/binli/papers/TON14_RegularService.pdf),
  §II, Eq.(4)–(6), Lemma1: a counter resetting to0 after service connects mean
  time-since-service to inter-service second moments under its steady-state
  assumptions. This supports reading regularity separately from throughput.
  Their queue arrivals, link-conflict schedules and stationary-channel assumptions
  are not this finite moving-UAV task; their guarantees do not transfer.
- Kadota et al., *Scheduling Policies for Minimizing Age of Information in
  Broadcast Wireless Networks*, TNET2018, [author PDF](https://www.mit.edu/~modiano/papers/CV_J_104.pdf),
  §IV-D, Eq.(32)–(36), pp.6–7 of the PDF: quadratic-potential drift motivates an
  ordinary age-weighted scheduler. Their age resets to1, yielding `h(h+2)`;
  equal weights/reliabilities reduce their rule to oldest-first. Here age resets
  to0 and multiple users can be served through coupled motion/interference, so
  neither that expression nor their optimality guarantee is imported.
- Asghar, Smith and Sundaram, *Multi-Robot Routing for Persistent Monitoring
  with Latency Constraints*, ACC2019, [author PDF](https://ece.uwaterloo.ca/~sl2smith/papers/2019ACC-Multi-Robot_Routing_w_Latency_Constraints.pdf),
  §III, DefinitionIII.1 and Fig.1: the spacing of future revisits matters for
  temporal latency, and adding evenly spaced robots to a repeated walk need not
  improve every location's latency. Radio service here is not a graph visit;
  this is a structural analogy for anticipating future opportunities, not a
  graph-routing reduction or an asserted latency guarantee.

The three local library entry/index searches for age-of-information, peak age,
service regularity and persistent monitoring did not locate a directly usable
indexed bridge in that search. This is a coverage-limited retrieval result, not
a claim that the stores or literature contain no related work. Root also
identified the already-used *Remembering to Be Fair* source; this design makes
no new-memory or novelty claim. The load-bearing evidence above is the primary
passage itself, not a title/hint. No additional toy run is needed: the following
finite identities already resolve the criterion and its limits.

For pre-transition age `a_u` and service bit `s_u`, native age obeys
`a'_u=(1-s_u)(a_u+1)`. Consequently
`sum(a'^2-a^2)=sum(2a+1)-sum(s*(a+1)^2)`. A one-native-tick minimizer of
quadratic age therefore uses `(a+1)^2` service weight, not `h(h+2)`. For a
completed unserved streak of length `g` starting just after service, linear age
cost is `g(g+1)/2`; squared-age cost is `g(g+1)(2g+1)/6`. The latter places
greater weight on long interruptions without an invented operational cutoff.
It is still a surrogate: at equal twelve-tick exposure, one length6 gap costs91
in squared age, while two length5 gaps cost110, although the latter has the
smaller maximum. Thus neither a smaller predicted squared-age cost nor a smaller
actual one establishes a maximum-gap improvement. The complete temporal endpoint
below must be measured. In a one-service symmetric static system a monotone age
weight would not create a different oldest-first ranking; the essential proposed
opportunity is this host's coupled service sets, spatial consequences and delayed
next decision, retained in the complete comparison.

### Actual information and control contract

Retain N5/U50, static native users, H256, the400-byte registered rounded-XY map,
27 motion commands, all31 nonempty transmitter masks and rotating-member
replacement. At report `t`, current actual commands execute ticks `t,t+1`; the
new joint command/mask, if timely, executes `t+2..t+5`. Reports occur every4ticks.
The other four current C proposals are fixed within a candidate. Initial commands,
position clipping, terminal truncation, reward, actual service semantics and
hold-old-command/mask fallback remain those of B01. No service ACK, live hidden
user coordinate, native future observation, future action or future environment
state is provided to a controller.

There is one explicit **common richer-information contract**. Source
`LocalController(history=False)` still retains `_nav_index` for its sweep
fallback (`controller.py:_sweep_choice,act`). A fresh C instance would falsely
reset it; reading another actor's live C object centrally would silently cross
the old report boundary. Each local sender instead appends its current
**post-C-call waypoint index0..9 as one byte**. All four arms receive the same
five25-byte reports and16-byte command at2kbit/s:136→141 recurring bytes,
.544→.564 seconds wire time and **1.436 seconds** charged computation allowance.
Use a new codec version with range checks; current map acquisition is unchanged.
C with history=False overwrites its current user rows on every call, so the
waypoint index is the only retained C state affecting the next decision; its
counters and old score arrays are not information inputs. The local sender may
read its own index to serialize it; the receiver only sees decoded bytes.

All actual C computation, encoding, history reconstruction, candidate search,
virtual observations/C calls and final serialization count within that one
current deadline. A virtual decision does not receive a second wall-time budget.
Any overrun or unavailable causal history uses the common physical fallback;
there is no late partial acceptance. M/R retain their mathematical rankings and
search semantics under this same codec/deadline. The fixed B01 source/results are
not rewritten. The study answers use **within this extension**; it does not
attribute the added byte's value or claim a gain under B01's original rights.

### Fixed policies and the modeled continuation

Define `Q4` as the sum of squared post-transition model ages over the candidate's
four delivered ticks, shortened to two at report252. There is no tunable exponent,
discount, terminal weight or gap threshold. All ages are integer int64; predictions
use existing float64 motion/radio and native greedy service assignment. Settled
executed history supplies the lawful starting ages; hypothetical updates are
private and never settle into that history.

**S**, the competent short-block temporal controller, uses the existing two
search orders, with `(-Q4,J,served,q==proposal_q,popcount(mask),-mask,-q)` at every
inner and final choice. Motion-first is27 current-mask motions then31 masks;
mask-first is31 proposal-motion masks then27 motions:116 requests before cache.
Keep both completed order finalists; S chooses the better one by that same key.
This is a four-native-tick commitment controller, not literally a one-tick action
policy. It preserves an ordinary objective-aligned comparator for anticipation.

**A** first makes exactly the same116-request S search on its own current input.
Its only first-action candidates are the two order finalists, deduplicated by
identical `(q,mask)`. **S's selected first action is always included.** If only
one remains or there is no next report before the episode ends, A selects S
without buying a useless continuation. Otherwise, for each of the two candidates:

1. From the decoded current anchor, propagate the actual two-tick prefix and
   that candidate's first two delivered ticks to the synthetic report at `t+4`.
   Build the predicted104-value local observations using the known map, native
   user/peer SINR thresholds/order/truncation, mask and float32 observation format.
   Clone each C from its **reported** waypoint byte, call it once at `t+4` on
   that synthetic observation, then form/decode a synthetic quantized report.
   These are model-generated proposals, never the real C call from `t+4`.
2. The first candidate is still active during `t+4,t+5`. Its remaining prefix
   must execute in the model before the next action is applied. From the private
   history at `t+4`, run S for the next rotating member with the predicted C
   proposals, current candidate mask and that two-tick committed prefix.
   This base-S continuation would start at `t+6` and last through `t+9`.
3. Score `Q8=Q4(first block)+Q4(base-S next block)` over `t+2..t+9`, clipped
   at256. At report248 it contains six delivered ticks; at252 there is no
   continuation and A=S. Rank by `(-Q8, S's current Q4/native/tie key)` and send
   **only the first action**. At the actual next report A replans as A; the
   hypothetical base-S continuation is never queued or committed.

This is restricted rollout selection between S's two search-order finalists,
not exhaustive two-stage MPC, optimal prospective control or a future-policy
oracle. At most `116+2*116=348` candidate requests occur per A report before
cache, rather than `116+116^2=13,572`. A/S share objective, first-stage search,
candidate support, information and deadline; A spends extra model computation on
one next decision. Their complete contrast tests the value/cost of that bounded
continuation package, not a computation-free pure mechanism. **M** is the primary
complete-use reference because of its existing typical-user temporal and service
capability. **R** preserves the separate worst-user-mean frontier. They receive
the same extra field/budget even though they do not consume it in ranking.

### Predictions, complete endpoints and disposition

Constructive prediction: some reports have two physically different finalists,
and the modeled next C/S response reverses their short-block ranking. A then
occasionally gives up immediate squared-age improvement to retain later service,
and reduces **mean per-user episode-maximum unserved gap** relative to both S and
M. The full task prediction is `A−M < 0` on that endpoint; a model score gain or
changed-action count cannot substitute for it. Some service/quality cost relative
to M is plausible; R may still have the better worst-user mean because neither
A nor S compensates accumulated historical burden. No loss-free default is
predicted or required to recognize a conditional capability.

Adverse alternatives remain concrete: the two finalists may often coincide;
longer-useful motion plans may be absent from their small support; quantized
geometry may change future C/assignment choices; or assuming one future S plan
may be a poor guide once A actually replans. Convex current age alone may explain
any S/A gain over M. Correct model reports and active rollout can also coexist
with worse complete gaps or service. None of these outcomes proves global
unreachability or exhausts prospective control, and none automatically buys a
new horizon, beam width, penalty, ACK or learner.

Proposed fixed exposure after scientific selection: **64 fresh common worlds,
seeds29322000..29322063, A/S/M/R**, eight cyclic orders from that sequence and
its reverse, world index modulo8. This is256 H256 episodes/**65,536 native
steps/0fits/0updates**, no pilot, extra old-world replay or adaptive panel.
Sixty-four worlds preserve the prior panel's useful paired world-variation
resolution at modest complete-run cost; this is exploration, not a power or
confirmation claim for the unobserved A effect.
Every world, user, timeout and adverse trajectory remains in the reading.
Primary world statistic is `G=(1/50)*sum_u max_gap_u[0:256]`, using maximal
contiguous actually unserved runs, with episode-boundary lengths included as
observed finite-window gaps and separately marked left/right censored. Primary
contrast is **A−M:G**; planned A−S:G tests the continuation investment, and
S−M:G tests the shorter ordinary capability. Report all pairwise contrasts,
per-world levels/differences, means/SD/ranges, win/loss/tie counts and descriptive
paired t95 intervals over64 independent worlds, not over users or ticks.

Retain actual squared-age mean, pooled age p95, all per-user gap maxima and
closed/censored counts, global maximum gap, never-served users, worst-user mean
age versus R, aggregate age, service/J/quality, service p10/minimum/zero-service,
four-window coverage, path length and transmitter exposure. Retain all request,
unique-plan/cache, physics/history/geometry/C-call, wall/CPU/RSS/storage/deadline
counts. No maximum-gap guarantee, steady-state claim, equivalence threshold,
battery claim or empirical learning claim is implied.

The activation record includes unique first finalists, A-versus-S requested
changes, executed command/mask differences and physically distinct delivered
blocks. Duplicate finalists mean sparse opportunity for this restricted rollout,
not a general null for anticipation. For A's selected first branch, compare its
predicted `t+4` geometry and C proposals with the actual report **before the next
new command takes effect**. Record model/actual age/service errors separately.
The hypothetical next S action and actual replanned A action can disagree by
construction; that disagreement alone is not prediction error. Saved-data
ranking/forecast observations describe the realized policy, not complete native
counterfactuals for unselected finalists.

If S improves the temporal endpoint against M but A does not improve S enough
to justify its measured cost, retain S conditionally and decline this rollout
extension. If A improves S but loses to M on the intended complete tradeoff,
retain M for that use rather than calling a weak-reference gain useful. A clear
A/M temporal gain with explicit service/fairness costs could retain a new
conditional reference beside M/R. A result with intervals spanning both useful
gain and meaningful loss remains unresolved; no automatic replication follows.
Full independent reading will separate tested approach, open question and next
investment without moving a completed rule or requiring an invented hard SLA.

### Full cost, engineering work and scope of this recommendation

All4 arms make64 current report decisions/world. If searches complete, the
first-stage pre-cache request count is
`64 worlds *64 reports *(116 A+116 S+232 M+116 R)=2,375,680`. A has at most
two continuations at each of63 reports with a future report: **935,424** more
requests, total **3,311,104 before cache**. Terminal lengths give at most
`64*(254*580 +250*232)=13,140,480` candidate-state radio reductions. These
are conservative pre-cache counts, not promises that every finalist differs.
They exclude65,536 actual transitions,65,536 settled-history transitions with
terminal drain,32,768 current private prefix ticks and at most16,128 additional
continuation prefix ticks; reusable duplicate prefix arithmetic must be counted
honestly rather than charged as new physical work twice.

Inherited actual C adds81,920 decisions/2,211,840 trajectories/8,847,360 model
ticks. A adds at most40,320 virtual C decisions/1,088,640 trajectories/4,354,560
model ticks plus8,064 five-UAV synthetic observation/report constructions. With
at most20 visible user rows per C, the virtual C candidate-link upper count is
87,091,200, plus setup/peer-observation links; actual counts depend on visibility.
All model-C work is intrinsic algorithm cost, not free verification. Full saved
data verification is additional, with no new native exposure.

B01's worker plus external reader cost1,824.068 CPU seconds(.506686CPUh), excluding
engineering/support. This proposal adds at most39.375% first/continuation requests
over that panel and at most49.219% C decisions, with different caching and
serialization. A rough planning estimate is **.7–.9 CPU-hours for worker+reader**,
roughly40–60 minutes in a serial single-thread path; it is neither measured nor
an upper bound. Construction/review/publication/observation remain additional,
currently unmetered work. Raw retention is roughly .45–.75GB rather than B01's
.297GB, likewise an estimate. Actual C/encoding is included in report timing;
B01's largest M report was.162977s, but a scaled average/max is not evidence that
the new1.436s deadline will hold. All fallback costs remain task outcomes.

Implementation would stay under this direction's `b02/` source/tests, with a
versioned codec, synthetic-observation/C-state predictor, private two-finalist
continuation scheduler and collector/reader adaptation. Reuse the frozen native
radio kernels and existing actual metrics; do not change environment physics or
old evidence. High-risk obligations are byte/state sufficiency, synthetic
observation ordering, the `t+4`/`t+6` commitment distinction, private history,
int64 arithmetic, R/M semantic preservation, single deadline and independent
reader/source identities. Plan one16-tick four-arm correctness fixture(64native
steps, distinct from result exposure), plus non-native codec/recurrence/deadline
checks and independent engineering review; any extra reviewer reproduction cost
is recorded separately. No substantial implementation starts before the current
scientific selection is resolved. A selected run would publish exact inputs,
admit on configured wsl_4070, execute once, collect and fully read the same
accepted operation. This paragraph is a design cost/scope estimate, not a launch.

Compared with another unchanged R replication, an attribution-only burden
ablation, a short-cost-only study or a no-investment choice, this four-arm
comparison can change two useful decisions in one complete panel: whether an
ordinary temporal criterion beats the established M reference, and whether one
affordable next-decision forecast adds enough beyond it. It also exposes the
richer-information and runtime costs instead of obtaining hidden future-C state.
That information value justifies recommending the bounded comparison; the actual
selection remains Root's current allocation-review/Pro task. Broader horizons,
larger candidate sets and learning are unselected alternatives, not a queue.

<a id="b02-selected-implementation"></a>
### B02 selected; full advice adopted and implementation scope

Root selected the fixed comparison at `e82a361eac44f88a81b62fb84e0ed7dfe47e83e5`;
the [complete independent and 6 Pro answers and decision](../../archive/2026-09-30/RESEARCH-temporal-service-continuity.md#decision)
have now been read in full. I adopt their no-dissent recommendation and precise
shared-trajectory construction: the private state/history at t+4 comes from the
first candidate, the next S prefix reproduces its last two transitions, and Q8
counts every delivered tick once. Synthetic observations contain native eligible
top20 users, not only capacity-assigned users. Current post-C waypoint state is
serialized before any hypothetical C call. All work shares one deadline; a late
A holds the old whole-team command/mask rather than falling back to its new S.
The already computed c0/c1 branches will record predicted current sacrifice and
continuation benefit, without new native counterfactuals. M's O/W candidates and
A's S candidate do not imply complete-trajectory dominance. Pro's limited compact
result retrieval remains disclosed; adviser agreement supplies no new empirical
evidence. There is no dependency on the other directions' progress.

**L0, one bounded behavior change:** implement the selected lawful A/S/M/R
decision API in `experiments/candidates/uav_user_waiting/b02/`, with tests under
the matching test directory; preserve all B01 files and existing native physics.
The kernel owns the25-byte codec, native-format synthetic observations from
decoded model geometry/map, decoded-state C clone, private current/continuation
search and common1.436s whole-plan fallback. Reuse the existing settled execution
history and radio kernels. Keep an independently reconstructible record of every
request, completed candidate/key/contact/cost, two finalists, continuation state,
synthetic packet/C result, timing phase and actual returned command. Empty/partial
records must describe timeout progress without pretending that an uncomputed
candidate completed. Integer age/burden/cost arithmetic uses int64.

The bounded Implementer owns only `b02/{protocol,predictor,scheduler}.py` and
`tests/.../b02/test_scheduler.py`; it has no notebook, shared-source or Git-index
ownership and launches no result or native fixture. The DM owns `__init__`,
collector/metrics/reader/entrypoint and their tests, accepts the helper's diff and
checks, then commissions independent engineering review of the complete path.
All authors share main; preserve other writers. The stable integration API is
`Scheduler(arm,map_packet,clock,cpu_clock,horizon=...)`, `executed(...)`, and
`decide(own_position_rows,actual,proposals,tick,current_mask,nav_indices,
started=...,cpu_started=...)`. Return actual command/mask/timeliness, packets,
timings/counters and a self-contained numeric/string record tree; the collector
stores its leaves losslessly in the episode NPZ without pickle. The scheduler's
`execution` supports the unchanged terminal history drain.

Checks cover source-equivalent R/M ranking, reset-zero squared costs, codec/state
boundaries, eligible synthetic observations, independent cloned C state,
two-finalist support, integer-grid report/prefix continuity, terminal248/252
semantics and every deadline/fallback phase. Use mocked or algebraic fixtures for
these. The DM will run the declared four-arm16-tick native fixture once(64steps),
collect/save/read it completely; additional checks use those saved data or
non-native construction unless a concrete correctness defect requires an honestly
recorded reproduction. Result exposure remains exactly the selected256episodes,
65,536steps,0fits; source publication, independent engineering acceptance and
actual-node admission precede its one detached launch.

**Implementation and declared correctness check (2026-09-30 UTC).** I read and
accepted the bounded four-file kernel/test implementation. It preserves the
frozen R ranking and M's deterministic W-key selection between O/W plans under
the new common codec. M is not a randomized mixture. All new result files are
under `b02/`; B01 source remains unchanged. The independent reader reconstructs
actual C/movement/radio/observations, age/gaps, causal settled history, all completed
candidate keys/costs, both request orders and each continuation. It checks all
selected plans/two A finalists physically and all evaluated candidates at reports
0/60/124/248. Saved partial prefix/candidate work is also reconstructible. The
reader's radio/observation references share frozen native kernels; this is not a
second independently implemented physical law.

The kernel's25 non-native checks passed in3.93s, then three strengthened A
selection/truncation checks passed in1.20s. My complete30-check suite passed
in3.18s, including the pickle-free record storage and its corruption rejection.
The final test strengthening changed only the synthetic oracle. Both direct CLI
help paths load correctly. The source review exposed C's nonfinite absent-user
diagnostic scalar; explicit lossless NaN/Inf tags were added before the fixture,
and their roundtrip is tested. No native call was used to discover that issue.

Exactly the declared **four16-tick episodes/64 native steps/0fits** were then
collected once on configured local scientific Python, seed92731, and saved in
`temp/directions/uav_user_waiting/correctness_b02/`. All four passed the complete
reader without repair or recollection. Counts are one constructor, four resets,
64 calls/transitions, four complete episodes, zero optimizer updates. All64
native and all64 model transitions were checked; candidate physical pairs were
346/118/117/115 for A/S/M/R. No deadline was missed; A's largest fixture round
was.241496s against1.436s. A exercised three two-finalist continuation rounds and
30 virtual C calls. The four raw files total513708bytes. These are correctness
observations, not the selected world-panel evidence or a performance estimate.
Their saved arrays remain available for the independent engineering Reviewer;
reviewer checks may reuse them without new native exposure.

The selected result tag is `b02_continuity_a01`, still64 fresh worlds
29322000..29322063 and256H256 episodes/65,536steps/0fits. Independent engineering
review of the full implementation/reader is in progress. Its acceptance and
published exact inputs precede the one detached result launch.

**Engineering acceptance.** The independent Reviewer found no material issue in
the stable B02 source after checking the common wire/deadline contract, lawful
post-C clones, native observation eligibility, shared t+4 trajectory, Q8 timing,
terminal clipping, frozen M/R ranking, whole-team fallback, partial evidence,
collector/reader and source/admission bindings. Its30 non-native checks passed
in3.25s. It re-read the four saved fixture episodes with **zero additional native
steps**, verified all62 fixture source identities, independently recomputed the
primary gap endpoint and demonstrated rejection of corrupt Q8, S keys and
virtual navigation state. I accept this review and the implementation. Shared
radio kernels and the declared candidate-physics subset remain explicit limits;
no full-panel result or destination admission is asserted by these checks.

Exact B02 scientific inputs were committed and published at
`16500b6f85c8cd20a7765801ed413608c36cf9f0`. Current main still records the lifted
owner pause and this runtime's active `uav_user_waiting` lead. On `wsl_4070`, the
maintained launcher and compute configuration exactly match published main; the
RESEARCH backstop was refreshed with an exact-old-hash guard to the published
control snapshot. Existing native-clone Git repack warnings did not prevent the
verified fetch/control read and were not repaired as part of this study.

The single detached launcher was submitted as native agent-task
`uav-user-waiting-b02-continuity-a01`; supervisor acceptance alone is not yet
runner admission or a read result. Reconcile this same request/manifest; never
repeat it on uncertain observation. Collection/reading responsibility continues.

**Reader-observation L0 (support only):** restore the previously reviewed B01
read-only agent-task identity adapter under this direction's disposable scratch,
with mocked tests under the B02 test directory. The existing pure reader remains
a direct accepted-source program, not another result-launch admission. Adapter
inputs are the actual immutable task/PID/boot/start/wrapper binding; it only
observes the same native task and translates unambiguous facts for `hmasd_wait`.
It cannot launch, retry or accept science. No native/model experiment is added.
The Implementer owns only that adapter and its test while the result executes;
all other paths and Git remain with their writers.


<a id="b02-technical-failure-continuation"></a>
### B02 technical failure and selected bounded continuation — 2026-09-30 UTC

The accepted first attempt `b02_continuity_a01`, input
`16500b6f85c8cd20a7765801ed413608c36cf9f0`, exited1 after six complete
H256 episodes and112 steps of R/29322001:1,648 actual steps, seven resets,
one constructor,0fits/updates. The unchanged native radio assignment raised
`TypeError: only integer scalar arrays can be converted to a scalar index`
during the R report112 candidate search. The original failing frame operands
were not saved. Its operation, source snapshot, six complete raw records and
partial raw record are retained. This is an incomplete technical collection,
not evidence that the A hypothesis failed.

All1,648 saved transitions have now been read, including the six complete
native/C/history/key/continuation records and the partial112-transition record,
113 observations,28 returned decisions and their delayed deliveries. The reader
verified zero observation error and added zero native steps/fits. The independent
engineering Reviewer inspected the partial-reader treatment, original hashes and
coverage and found no material issue. A bounded pure replay of only the failed
report was run once locally and once from the original accepted source on the
same configured node, without constructing an environment or stepping it. Both
completed116 requests/83 candidates/332 candidate states, selected(q10,mask15),
and produced identical assignment/contact digests; the original TypeError did
not reproduce. R-key byte digests differed across hosts, so no cross-host
bitwise-parity claim follows. Zero-clock replay, added diagnostic allocations
and a fresh process also mean this does not establish a cure or corruption.
The after-failure host sample is not a measurement of conditions at failure.

Root selected one bounded continuation on the same configured `wsl_4070`,
subject to fresh actual-node admission: preserve/reuse the six independently
validated complete records, restart only partial R/29322001, then finish the
frozen order. This is250 new H256 episodes/**64,000 new native steps/0fits**.
The complete panel will contain65,536 valid transitions; the112 failed-prefix
steps remain additional exposure, making65,648 result-exposure steps across
both attempts. The earlier64 correctness steps remain separate. Same host avoids
adding cross-host numerical/deadline scope; this does not assert runtime repair.
No policy, seed, search, horizon or deadline changes and no automatic further
retry are selected. No additional native correctness fixture is needed for the
continuation bookkeeping; tests use mocks and the already-saved evidence.

**Continuation L0.** New code belongs under
`experiments/candidates/uav_user_waiting/b02_continuation/` and its matching
tests. All original62 scientific source files, including the original B02
collector/scheduler/reader, stay byte-identical. A distinct continuation entry
binds the original accepted operation/source/output, terminal summary/exit and
all seven raw identities, proves the exact six-row reusable prefix and resumes
only the fixed250-row suffix into a new output. It never writes the original
attempt. The final composite reader checks both source groups and all256 raw
records with the unchanged B02 reconstruction functions, with the original
partial raw retained as adverse technical evidence and excluded from endpoints.
Counts distinguish new exposure, prior exposure, valid panel and failed prefix.

The existing launcher's `--retry-of` deliberately accepts only an identical
source SHA and normalized runner command. It cannot represent this selected
partial continuation plus new failure instrumentation. Use supported standard
fresh admission for the explicitly published new scientific object/source/entry,
with the parent linkage enforced in its own config and records; do not change or
bypass shared launcher admission. A failure-only helper reads selected traceback
frame operands/shapes/dtypes after an exception is already raised. It neither
patches shared radio code nor installs tracing, and does no work on the normal
policy/search/RNG path. If a second attempt fails, preserve its complete and
partial evidence and return; no third launch is authorized here.

The existing Implementer owns only `b02_continuation/failure_capture.py` and its
non-native tests; the DM owns entry/config/composite reader and integration. All
work uses shared main with disjoint paths; helpers have no Git-index, notebook,
shared-code, launcher or native-execution ownership. The existing engineering
Reviewer will independently check binding/accounting and failure instrumentation
before publication/admission. Collection and scientific reading/diagnosis remain
with this DM. The current Root Pro-answer subsection is outside this edit scope.


**Continuation implementation accepted.** The new entry and composite reader are
separate from the frozen B02 package. The fixed-parent validation checks all four
metadata digests, the published reading proof, all seven complete/partial raw
identities and exact equality of the original62 source/frozen-config bindings.
It selects the exact suffix after six rows, guards the original output, requires
the original operation to be definitely stopped, distinguishes all exposure
counts and allows no implicit resume or further retry. Only already-raised
exceptions trigger bounded create-only JSON/NPZ operand capture; best-effort
capture errors remain explicit and do not replace the original failure.

The Implementer's eight synthetic traceback checks passed in.21s; I read and
accepted both owned files. My five mocked continuation checks passed in2.29s
(and2.10s after the integration edit); the combined13-check suite passed. Direct
runner/reader help paths load, and the original62 scientific inputs match byte
for byte. The independent engineering Reviewer ran13 checks in2.15s, separately
matched actual parent metadata/proof/seven raw identities and reviewed admission,
6+250 ordering, source protection, exposure arithmetic, complete composite
reading and failure-only capture. It found no material issue. I accept this
implementation. Tests/review added **zero native steps, fits or optimizer updates**.
Native admission and the actual complete composite read remain execution checks;
the original runtime exception remains unexplained.

The retained failure support scripts are copied verbatim into the original run
record for provenance. The partial-reader script's historical raw locator names
the hash-verified temporary collection; its unique durable inputs are the seven
canonical `wsl_4070` raw paths in the original summary. These support scripts are
saved-data reconstructions, not new result entrypoints. Their scratch copies will
be removed after the accepted continuation and reading have no live consumer.


**A02 support-input failure and one corrected continuation selection.** Exact
continuation inputs were published at `d19ea9daece1f68c4b9278ce08bccb7706ab95a7`.
The first supervisor submission hit an implicit Git commit-fetch timeout before
claim/output/admission; exact reconciliation found none. An explicit fetch made
the published source available, and the same scientific request was admitted
once at2026-09-30T14:31:52.099075Z as `b02_continuity_a02`. Fresh physical/effective
memory was14,663,192,576bytes, exceeding the4GiB floor. It exited1 at
14:31:54.332493Z:2.233418s acceptance-to-exit; worker CPU/RSS are unmeasured.

A02 failed before writing config, constructing the environment or collecting any
transition. Its proof-path guard found the Git-published reading under `runs/`
absent from the sparse snapshot. Direct inspection establishes **skip-worktree S,
not a filesystem symlink**: the existing node sparse selection includes
`experiments/` but omits this direction's Git run records. The launcher routes
output arguments to canonical runs; that does not populate source-side Git run
inputs. My initial mapping shorthand was corrected after this inspection. A02
adds **zero constructors, resets, native steps, fits or optimizer updates** and
has not reproduced the original radio TypeError. All native terminal/error/input
facts are retained in the A02 run record. The original six complete records and
112-step failed prefix remain unchanged.

Root explicitly selected one corrected continuation after this located binding
failure, keeping the exact250H256 episodes/64,000new steps/0fits and original
node/runtime/policy/seed/search/deadline. **Minimal correction L0:** relocate the
exact published reading proof, unchanged bytes and SHA256
`e971cf194942ecc99278e63e8ba64f397242c44a638a5a1acf88fbd5636bbd18`, into the owned
candidate `b02_continuation/inputs/` and read only that source-bound input. Keep
one working proof copy; its original published run-record identity remains at
the A02 source commit. Add a zero-native check importing the actual continuation
module from a source-layout fixture whose Git runs input is absent and whose
canonical output is separate. Do not change node sparse selection or the shared
launcher. Existing independent engineering review covers this narrow correction;
exact publication and fresh admission precede the one new object at a fresh tag.
A further failure must be preserved and returned without another automatic retry.


**Sparse-layout correction accepted.** The one-line input-path change and
77,875-byte proof relocation preserve the exact published proof hash. My14
non-native checks passed in2.37s. The existing independent Reviewer separately
compared the relocated bytes with the original at `d19ea9da`, ran14 checks in
2.14s, checked the actual module import under omitted-runs/separate-output layout
and reverified the original frozen configuration. It found no remaining material
issue and acknowledged the previously missed sparse-layout dependency. I accept
the correction. It changes neither scientific inputs nor native exposure. The
new selected tag is `b02_continuity_a03`; all prior operations remain terminal and
unchanged, the observer is stopped, and source publication/fresh admission come
before this one newly selected execution.


**Corrected continuation accepted (2026-09-30T14:39:39.857793Z).** The corrected
source `db13ccf307e9cf467450fdad8318721fb8db603a` was published, fetched to the
actual node, and its candidate proof blob independently hash-checked before the
single new submission `uav-user-waiting-b02-continuity-a03`. Fresh actual-node
physical/effective available memory was14,649,356,288bytes;4GiB floor passed.
The admitted snapshot is `97402e6dc42c44dfbac06b78f3c7f145`; supervisor/runner
PIDs1127510/1127511 are bound by the native manifest. Stable operation:
`/home/wu/projects/HMASD/.git/hmasd-admission/b54101d5db3d63adf599cba4ee5d1cf64de30e8382a59eb72671c64f82e446a8.json`.

The generation13 stopped observer was explicitly rearmed14, then the new bound
job registered generation15 for a900s window. First drain at14:40:20Z observed
consistent accepted/running identities, present summary and zero probe errors.
No acceptance is inferred from supervisor submission alone. Native child remains
active through deterministic observation, collection and complete reading;
checkpoint rearming will never restart the worker. Prior failed attempts are
unchanged, and this acceptance is not a scientific-result boundary.


**First A03 checkpoint.** Generation15's900s checkpoint was drained with the
same accepted operation still consistent/running and zero probe errors. The
last saved summary held156 new complete episodes/39,936 steps, plus the retained
six:162 valid panel rows. This is saved progress, not the instantaneous count
inside the running next episode or a read result. The event
`5c6a33a4e9628d91c11b5b89` and wake
`6cce1154-309a-4278-b5e0-8fd17ea1bd92` were consumed into generation16 with a600s
window; no worker was restarted. Native child queue delivery again returned
code−32600, so the turn remains active with deterministic local event waiting.


**A03 worker terminal and complete-panel reader.** The protected continuation
exited0 at2026-09-30T15:04:36.758678Z with250 new complete H256 episodes/64,000
native transitions/0fits and the original six rows unchanged. The final fixed
panel is256episodes/65,536valid transitions; total result exposure is65,648
including the original112-step failed prefix. A02 contributed no native exposure.
The generation16 READY event `1c953ba04ce1f03d25e63d94` and wake
`ab49ec55-8fad-421f-99af-31bedbf4bf1d` were consumed into generation17; native
operation facts show consistent exit0 and absent runner/supervisor identities.
The full composite summary SHA256 is
`620cad3f8da694615ef4883b8e225c94b54f1a86bb4333c5b64c1fbd5a875df3`.

The unchanged accepted-source composite reader was submitted once at15:06:41Z
as `uav-user-waiting-b02-reader-a03` using the configured GCC Python, one thread
and external `/usr/bin/time -v`. Its immutable task binding is preserved in
`runs/uav_user_waiting/b02_continuity_a03/reader-supervisor.json`: wrapper
PID1129756/start112418663, task-start1790780801, wrapper SHA256
`481f035b449b6cb4712de59ce2c48a93d78f0423936b814da893acf3b95ebbdb`.
Generation18 observes that same pure-reader handle through the previously
accepted read-only adapter; the first drain was consistent/running with zero
probe errors. It does not launch a second result operation or add native steps.
The DM remains active through the complete reader and independent scientific
diagnosis. Worker exit alone is not yet a verified scientific conclusion.


**Pure-reader checkpoint.** Generation18 reached its900s checkpoint with the
same bound reader consistent/running and zero probe errors. At this checkpoint
the native log had verified217/256 trajectories. Event
`a80041fd9b4cd5782575b02d` and wake
`3a67528d-0a07-457e-be45-9e7ef29a6a84` were consumed into generation19 with a600s
window; no reader or worker restart. This remains verification progress.


<a id="b02-complete-reading"></a>
### B02 complete reading — 2026-09-30 UTC

**The fixed anticipation package does not establish the intended typical-user
continuity gain. Retain M for that use, and preserve S as a useful additional
extreme-tail/fairness tradeoff.** The scientific panel is now complete, not a
technical-failure verdict:256 valid H256 episodes on the64 fixed common worlds,
0fits. The protected six original rows plus250 new rows give65,536 valid steps;
the original112-step failed prefix makes65,648 total result-exposure steps.
The64 native correctness steps are separate. A02 contributed zero native steps.
Original scientific inputs remain `16500b6f85c8cd20a7765801ed413608c36cf9f0`;
the accepted protected-continuation/reader source is
`db13ccf307e9cf467450fdad8318721fb8db603a`.

The pure composite reader completed once, exit0. Generation19 READY event
`4ae13e2a0c770a995b35d9e8` and wake
`19f6f964-dba5-4a47-a0f3-e1af79937c58` were consumed into generation20; observation
was then stopped. No worker, reader or Send was restarted. Native reader binding
and terminal facts are in the compact [result](../../../../runs/uav_user_waiting/b02_continuity_a03/result.json).

**Verification and retained evidence.** All256 raw files/408,643,897 logical
bytes passed their exact identities, paired-world geometry, native transitions,
actual observations/C/private waypoint states, age/gap endpoints, lawful report
and delayed-delivery contracts, model-history reconstruction, completed key/cost
arithmetic and continuation-clock checks. The reader verified65,536 native and
65,536 executed-model transitions, with177,158 candidate physics pairs under the
frozen subset:all selected plans and both A finalists, plus all evaluated
candidates at reports0/60/124/248. Native radio is a shared kernel; history,
cost/ranking/trajectory reconstruction and the frozen observation reader are
separate. This is not an independently implemented full physics audit. Maximum
native J discrepancy was5.55e-17; SINR and actual-observation errors were0.
The original112-step failed prefix was fully read earlier and is excluded from
endpoints. Independent review also found its saved native prefix identical to
the completed R/29322001 prefix, without diagnosing or curing the original error.

The canonical full summary is5,027,091bytes, SHA256
`620cad3f8da694615ef4883b8e225c94b54f1a86bb4333c5b64c1fbd5a875df3`;
full reading4,532,651bytes, SHA256
`353c14a1c03e4440e90f0718c52bcab5dfaaaf36b0b129c5b33ce9e5e604d065`.
Both remain at `wsl_4070:/home/wu/projects/HMASD/runs/uav_user_waiting/b02_continuity_a03/`.
The six reused complete raw files remain in canonical `b02_continuity_a01/raw/`,
along with the original553,351-byte partial R file. All250 new raw files remain
in canonical `b02_continuity_a03/raw/`. The compact result records every raw
identity, all paired per-world values, all per-user gap/mean-age summaries,
per-world verification/model diagnostics, work/cost and native terminal bindings.
No new result is inferred from a log or a successful exit alone.

The fixed primary is the mean over50 users of each user's maximum observed
contiguous unserved gap, including observed left/right-censored lengths. Worlds,
not users or reports, are the independent paired units. The intervals below are
prespecified descriptive paired t95 on64 worlds, not confirmation or equivalence.

| Mean over64 worlds | A | S | M | R |
|---|---:|---:|---:|---:|
| Mean per-user maximum gap |20.455625|20.964063|19.826875|28.743125|
| Worst-user mean age |9.725708|9.835510|12.914001|10.935425|
| Episode maximum gap |49.921875|46.968750|55.921875|59.046875|
| Aggregate mean age |3.378014|3.497772|3.175093|4.682748|
| Pooled age p95 |13.954688|14.438281|14.970313|20.892188|
| Mean squared age |42.330797|43.477169|46.206426|84.572096|
| Served users/tick |21.247375|20.933899|24.596436|21.640076|
| Native J/tick |.353128|.350250|.398139|.362645|
| Scheduler CPU seconds/episode |9.258024|3.902444|5.059534|3.883219|

Primary **A−M = +.628750 [−.215564,+1.473064]**,29 improving/35 adverse worlds.
Planned A−S = −.508438 [−1.366416,+.349541],36 improving/28 adverse;
S−M = +1.137188 [+.335121,+1.939254],25 improving/39 adverse. A's point increment
over S is favorable but uncertain, and neither superiority nor equivalence is
established. S's different tail gains do not retrospectively pass this primary.

**Positive capability and its cost.** Against M, S reduces episode maximum gap
by8.953125 [−12.816345,−5.089905] and worst-user mean age by3.078491
[−4.271702,−1.885281], with1.157089 fewer scheduler CPU seconds per episode.
A also reduces these respective endpoints by6.000000 and3.188293, and lowers
age p95 by1.015625. But S/A serve3.662537/3.349060 fewer users per tick than M
and lose J in **all64 worlds**. Their aggregate ages increase.322679/.202921,
paths increase602.538/659.409m per UAV, while transmitter-on ticks fall105.938/
97.813 and quality improves. Neither energy savings nor physical safety follows
from this host's transmitter/path measures. Actual mean-squared-age contrasts
with M have intervals crossing0; optimizing its local forecast does not certify
improvement in its complete actual value either.

A has a real observed secondary increment over S:service+.313477
[+.099148,+.527805],44 improving/20 adverse worlds. J+.002878 has a narrow
interval crossing0. Quality falls.005037, transmitter-on ticks rise8.125, and
scheduler CPU rises5.355580 seconds/episode (2.37 times S). The episode-maximum
gap point contrast A−S is+2.953125 with interval[−.629981,+6.536231]. Preserve
this non-inert mixed result; it does not justify the extra rollout for the named
continuity use. Against R, A/S reduce typical-user maximum gaps by8.287500/
7.779063 and have lower worst-user mean-age point estimates, but their service,
quality and travel costs remain. A−R worst-user mean age is−1.209717
[−2.405703,−.013731]; S−R is−1.099915 [−2.287524,+.087694]. This is neither
loss-free preservation by an equivalence rule nor general dominance of R.

**Intervention, lawful model and limits.** All16,384 delivered rounds were
timely; no unknown history prefix was used. The common141-byte round and1.436s
compute allowance include the reported post-C waypoint byte for every arm.
This evidence does not identify the byte's separate value or retroactively
establish B01-contract performance. Maximum charged round was.267830s for A
(.112368/.147476/.116074 for S/M/R), on this observed node/load.

A had2,881 reports with two distinct finalists;40 horizon-terminal reports do
not extend them, leaving2,841 complete timely two-branch comparisons. It selected
a different pair from same-state S in644/4,096 reports:289 paid positive current
squared-age cost and355 tied that cost; all644 lowered computed total cost.
Across the2,841 comparisons, current sacrifice sums65,909, modeled continuation
gain684,966 and total gain619,057. These inequalities are constructed by A's
selection rule, not independent evidence of actual future benefit. The644 count
is a command/mask-pair difference, not a claim that all induce physically distinct
motion after clipping or distinct service.

For the selected first branch, the modeled next C command differed on103/14,205
UAV proposals (101 report slots), and its waypoint index on7. Maximum next-report
position error was.499130m and maximum synthetic/native observation component
difference.780659. The virtual future S pair differs from actually replanned A
on456/2,841 slots **by design**, and cannot be counted as model error. These
measurements reject total failure to activate or predict the next local policy;
they do not isolate the cause of the primary result. Quantized-history service
false-positive/false-negative counts were A454/416, S441/361, M481/463 and
R431/379. Every episode has some terminal burden discrepancy; maximum absolute
burden errors are672/1054/2028/1032. No truthful ACK was substituted for model
history. Broadly calling that model exact would therefore be wrong.

**Positive and adverse raw witnesses.** Independent contact-to-age and gap-run
reconstruction on12 source-bound trajectories reproduced every inspected gap
and endpoint. A−M positive29322058 has mean-user maximum gaps20.90/27.26 and
maxima45/84; M's84 is closed. In adverse29322021, A/M are28.06/18.92 and40/50
users have worse maxima under A. A−S positive29322027 is15.94/26.54, including
S's66/63/62 observed terminal gaps; adverse29322001 is30.66/21.18 with37 users
worse under A and56/55/55 closed gaps. In29322048, A user20 has a98-tick closed
gap[110,208), worst-user mean21.253906 versus S/M/R10.085938/9.003906/8.074219.

The first checked A/S divergence in positive29322027 pays86 current Q4 for339
modeled continuation gain; adverse29322001 has a current tie and290 modeled
continuation gain. Both execute and all five selected-branch next C proposals
match actual C. They establish active model-supported interventions before both
complete signs, not single-decision attribution of either trajectory. For the
98-tick adverse user, age **and accumulated burden are correct at all64 anchors**.
Some visited candidates predict service at reports108/112/116/124 but are not
chosen; later visited sets contain none at128..200, with service selected204.
This does not diagnose missing ACK/history, full-support unreachability, or a
successful horizon/search repair.

**Cost and cumulative investment.** The valid panel used3,034,792 requests,
2,219,628 candidate plans,8,808,440 candidate-state reductions and28,410 virtual
C calls; original C contributed81,920 decisions. Current/future requests are
2,375,680/659,112. These panel counters exclude failed-prefix/aborted-request
work and correctness/support. The new worker used1,495.087732 lifetime CPU
seconds; the original failed worker42.228441. External full-reader time is
1,113.99 CPU seconds/1,114.27 wall seconds, peak534,556KiB. Known worker plus
full-reader CPU is **2,651.306173 seconds (.736474h)**, within the prospective
.7–.9h estimate but not the whole research bill. A02 CPU/RSS is unmeasured;
its2.233418s acceptance-to-exit, fixtures, engineering/review, two saved-failure
replays, partial readers and collection are additional. New worker perf-counter
wall1,431.421581s and reader internal wall1,055.765772s have different scopes
from native UTC/external wall; no runtime explanation is inferred from them.
Across this direction's B01+B02, result exposure is131,184 steps plus200 fixture
steps,0fits, and4,475.374087 known worker/full-reader CPU seconds, with support
additional. Completed continuation is not evidence that the unexplained original
radio exception is cured.


<a id="b02-independent-review-and-disposition"></a>
### B02 independent scientific diagnosis and disposition

The existing registered ResearchCritic worked in its separate, originally
non-inherited context. It received the actual question, frozen design/source,
original selection/Pro advice, B01 adverse evidence and both failed/completed
outputs, not only the DM's explanation. It formed its numerical reading before
consulting selection advice. It independently checked all62 original scientific
bindings, continuation config/order/accounting, protected parent metadata/seven
raw hashes, exact reuse of six rows, paired statistics and the matching failed/
completed112-step prefix. Its bounded12-trajectory raw reconstruction and
positive/adverse decision inspections are reported above. It did not duplicate
the complete physical reader. After the full reader completed it independently
verified both full-file hashes, source binding, terminal exit0,256 unique rows,
aggregate verification counts and continuation diagnostic sums.

**Substantive recommendation:** retain M for the intended typical-user
continuity/service use; retain S as a conditional extreme-tail/worst-user-mean
ordinary reference; end investment in this fixed A rollout extension; select no
new native experiment. The initial recommendation was conditional on the full
reader, and the final addendum explicitly says that condition is now satisfied
within the reader's declared scope. **MATERIAL_DISSENT: no.** It would object to
promoting A as a demonstrated typical-user improvement or treating S's extreme
benefits as a retrospective primary success.

Its explanation is that convex short-block control already supplies much of the
observed extreme-tail capability, while neither the surrogate nor one modeled
continuation establishes improvement in mean per-user maximum gap. The
criteria differ:worst-user time mean, typical-user episode maximum and largest
single interruption are not interchangeable. It preserves A's+.313477 service
increment over S, active interventions and mixed continuity outcomes; it does
not label A inert or universally useless. Same-state modeled gains are forecasts,
not realized primary gains. Restricted finalists, finite forecasting,
quantization and subsequent replanning remain possible limitations; none has
been identified as the cause or shown to be repairable by more investment.
Zero fits says nothing about learnability. The byte extension was common and
lawful, but its separate value and original-contract transfer were not isolated.

The Reviewer considered unchanged replication, model repair, wider search,
longer horizon, ACK access and learning. Replication could narrow A−S uncertainty,
but no present adoption decision depends on that precision. The other routes
lack a selected discriminating complete-controller prediction. It recommends a
constructive re-entry only for a consequential actual choice among typical-user
continuity, extreme tails, service and compute, offering more decision value
than retaining the measured M/S/R alternatives; it does not require a mechanism
proof or a positive toy as an admission condition. Its final addendum confirms
that the103 next-C mismatches and456 declared replanning differences do not
justify an automatic repair or a general rejection of anticipation. No live
Reviewer scratch consumer remains.

**DM response and working explanation.** I accept this recommendation without
a new Pro round:the completed independent diagnosis addresses the actual fixed
claim, all supporting/adverse evidence and the continuation choice; no distinct
unresolved expertise or material disagreement remains. The task opportunity is
real but plural:M remains strong for typical-user interruption and aggregate
service; S adds a measured extreme/fairness tradeoff. B01's R benefit remains
valid on its own panel, and B02 shows R is not the only ordinary way to obtain
lower worst-user time means. Representation/history were active and lawful;
the correctly tracked98-tick witness specifically weakens a missing-age/ACK
story, without showing the whole representation or support sufficient. No
learning method was tested. For the complete package, A's added forecast cost
has not earned investment for the selected primary use, even while its secondary
service increment is retained as a real observed capability.

I therefore **end this fixed A extension's additional investment**, retain M
and conditional S alongside R and all adverse results, and place the direction
in reserve after publication/cleanup. This is a choice about the tested package
and current investment, not an empirical refutation of the still-open broader
question of prospective service-continuity control. No automatic horizon,
penalty, beam, ACK, decoder, fit or seed-panel repair follows. There is no
producer, unread result, selected successor or approval dependency. Re-entry
would need a selected complete controller/comparison with a consequential
continuity-versus-tail/service/compute purpose; no such object is currently
specified. A cross-question successor remains Root's allocation decision, not
an outstanding task for this finished batch.


<a id="b02-final-cleanup"></a>
### B02 final publication and measured cleanup

Useful frozen policy/protocol/predictor/readers, continuation provenance and
failure-only instrumentation remain published because they support this exact
retained comparison and its reconstruction. The compact reading and independent
disposition were published at `87a66f083`. No new policy execution is selected.
Before deletion, all three worker identities and the bound pure reader were
terminal, the deterministic observer was stopped with every event consumed, and
the independent Reviewer confirmed no live scratch consumers. Reference checks
found only the disposable test using the private reader adapter; both are removed.
No other direction's files or controls were deleted.

Local full summary/reading hashes match their one canonical remote copies; native
terminal JSONs are preserved inside the published compact result. The seven
failure raw copies match retained canonical inputs, and the remote diagnosis
script matches its published run-record copy. Disposable64-step correctness
raws/scripts and caches are retired after the complete fixed-panel verification;
their check outcome and exposure remain above. They are not result endpoints.
The sole complete native trajectories, original partial failure, full readings,
all operations/manifests and native exits remain in the canonical run directories.
After deletion, all256 complete raw files and the original553,351-byte partial
were present with their expected sizes; the partial hash and full summary/reading
hashes were rechecked. These257 unique raw files total409,197,248 logical bytes.

Allocated-byte measurements below are `du -B1` on the exact disposable targets
before deletion and zero after; they concern reclaimed working files, not Git
object storage or whole-host free-space changes during other sessions' work.

| Deleted target | Net allocated bytes reclaimed |
|---|---:|
| Local `temp/directions/uav_user_waiting/` |10,387,456|
| Local disposable `tests/experiments/candidates/uav_user_waiting/b02/test_reader_observer.py` |12,288|
| Local owned source `b01/b02/b02_continuation/__pycache__/` |339,968|
| Local owned test `b02/b02_continuation/__pycache__/` |139,264|
| Local `b02_continuity_a03/{summary.json,reading.json,reader-terminal.json,terminal-status.json,stdout.log,stderr.log}` duplicates |9,605,120|
| Node snapshot `.git/hmasd-launch-sources/659e9fd1fe8a48eaba8dd80b40409443` |809,299,968|
| Node snapshot `.git/hmasd-launch-sources/074beee0d94642b98af7b8e0db31e0ba` |809,230,336|
| Node snapshot `.git/hmasd-launch-sources/97402e6dc42c44dfbac06b78f3c7f145` |809,340,928|
| Node `temp/directions/uav_user_waiting/` diagnosis scratch |16,384|

Local total **20,484,096**; node total **2,427,887,616**; combined measured net
reclamation **2,448,371,712 allocated bytes**. Initial supported snapshot-GC
preview refused A01/A03 because23/2 ignored `.pyc` files remained. Only those
25 cache files and now-empty cache directories were removed (already included
in the snapshot totals). A fresh exact-target preview with the read-only
`--sudo-process-scan` then found all three eligible, and supported `--apply`
removed each. Actual absence was checked. No snapshot, tar, backup chain or
extra retention copy was created as a deletion condition. **No cleanup target
or concrete tool blocker remains.** The scientific runtime TypeError remains
unexplained in its preserved adverse record; that is not a live cleanup block.


<a id="b03-design-only"></a>
## 2026-09-30 — B03 design only: experience about remaining interruption cost

**State and authorized scope.** Root assigned one scientific design task to the
existing lead after B02's completed boundary. This is new question preparation,
not unfinished B02 collection or permission to restart A. The assignment permits
source/literature reading and this prospective note: **0 fits, 0 new native
steps, 0 model or actor queries, 0 current-data rescoring, and no result-code
implementation.** Those are the actual counts for this design task. No operation
was launched. B02's original runtime-fault uncertainty, stopped fixed-A investment,
retained M/S/R evidence and measured cleanup remain closed.

I used the current published RESEARCH background at
[a76af735f5eae2bcb82371eaf5a470845f50529b](https://github.com/CartmanFatass/My-paper-code/blob/a76af735f5eae2bcb82371eaf5a470845f50529b/docs/research/RESEARCH.md):
topic 2's B02 continuity/tail/service distinction, topic 3's newly positive N8
relocation capability, and topic 8's separation of lawful information, policy
class and finite learning. Their concrete effects are to retain M and S as
complete ordinary references, avoid an ACK/horizon repair diagnosis, make
counterfactual continuation validity an uncertainty, and compare this investment
with developing N8's demonstrated capability. No shared-background claim changes
merely because a new design is feasible.

The question is whether native experience can improve **mean per-user maximum
observed service interruption**, using a learned M-continuation value inside
lawful joint command/mask search. Its first intended contribution is empirical
understanding and possible task capability, not an asserted new architecture,
duration-learning result or necessity theorem. It changes actual candidate
ranking rather than choosing between unchanged O/W assets. Interference,
capacity-limited assignment, joint transmitter masks and future responses of the
five fixed C controllers couple the choices. There are no co-adapting learners.
The lawful coordinator still does not observe exact radio geometry or truthful
service ACKs.

The prior learning result is adverse evidence, not a clean slate. I read the
[published service-age compact result](../../../../runs/uav_service_age/b01_age_selector_a01/result.json)
and its [complete interpretation](../uav_service_age/NOTES.md#b01-complete-reading):
one active PPO selector fit, 512 training plus 448 evaluation episodes and
245,760 native steps; L1 improved its own initialization but had mean age
3.542917 versus M's 3.273864 and mean per-user maximum gap 21.614063 versus
20.202500. It differed from M on 738 evaluation choices. Its known lifetime
worker plus external-reader CPU was 6,687.213851 seconds, with support additional.
The present proposal changes the objective, supervised native suffix target and
action-level use of experience; it does not reinterpret that negative as an
optimizer, missing-history or nonactivation failure. This direction has already
paid 131,184 result steps, 200 correctness steps and 4,475.374087 known worker/
full-reader CPU seconds across B01/B02. Both investments lower the case for an
unfocused repair, without refuting a different complete learning comparison.

### Source binding and actual interface

The following source was read on the published main revision above and had no
working-tree diff. B02's full 62-file scientific binding remains in its original
config and compact continuation evidence; the independent Oracle checked all
62. These are the directly load-bearing interfaces, not a replacement manifest:

| Source | Consequence for this design |
|---|---|
| experiments/candidates/uav_user_waiting/b02/protocol.py; imported uav_radio_activation/b01/protocol.py | N5/U50/H256; map 400 bytes, five 25-byte reports and 16-byte command; report period 4, delivery 2, recurring 141 bytes and 1.436-second charged computation. Bounds are (0,0,50) to (1000,1000,150); masks are nonempty. |
| experiments/candidates/uav_user_waiting/b02/scheduler.py, _Stage.prepare/score/search | Two old-command prefix ticks; four delivered candidate ticks except the final truncated stage; saved midpoint after the first two delivered ticks. The two search orders use 27+31+31+27=116 pre-cache requests. M retains its existing O/W generation and cumulative-age selection. |
| experiments/candidates/uav_user_waiting/b02/study.py, collect_episode/allocate_raw/record_round | C acts only at reports; the pending command arrives after two native steps. Actual radio arrays are copied before mask-arrival mutation. Raw records retain commands, masks, packets, post-C navigation, model contacts and causal stage histories. |
| experiments/candidates/uav_registered_service/b01/history.py and uav_user_waiting/b01/history.py | Executed actions settle atomically from decoded anchors. Only executed settlement changes persistent memory. A late initial anchor leaves the missing prefix censored permanently; numerical reconstructed ages are not truthful past service. |
| experiments/candidates/uav_local_history/b01/controller.py and uav_user_waiting/b02/predictor.py | For history=False, current local points overwrite prior points at each call; navigation is persistent. A pre-next-C value must carry previous post-C navigation, but exact future native observation remains unavailable. No future C call is required by the proposed value method. |
| experiments/candidates/uav_user_waiting/b01/metrics.py and b02/metrics.py | The native mean of 50 per-user maxima is the primary quantity; extreme episode maximum, worst-user mean age, aggregate age and native J/service remain distinct endpoints. |
| experiments/candidates/uav_service_age/b01/features.py and learner.py | Existing causal availability/scaling conventions can guide a new feature pack. The learner is a two-action PPO actor/critic and is not a supervised suffix-value fit. No direct reuse of that learning rule is claimed. |

For a compact byte check, the inspected B02 scheduler SHA256 is
b752521080a9fa12c24a05e696880a2f94e74734fe273d77fee5e20a0df85b41,
its study is e69ccca9d8213a07de56a13b1110365b74545a5312be53e23e84604c4d51753d,
the inherited waiting history is
a839438052c6c57337eade4a1b066802830a5fbd0af78e49f45564160f57a7f4,
and the inspected service-age learner is
9ad461b2a64d3439cf7004ad656758b02d3579c7c5b57ec127cbfc9db60f7ac8.

At a boundary k before native transition k, define actual age a-minus(k) as the
post-transition age after k-1, with a-minus(0)=0. Let actual b(k) be the vector
of maximum ages over transitions 0 through k-1, with b(0)=0. Each native
transition first records actual service, updates age, then updates b by a
coordinatewise maximum. Thus
G = mean(b(256)) = sum from k=0 to 255 of mean(b(k+1)-b(k)).
This is exactly the existing observed-gap convention, including observed
left/right-censored endpoints; it is not the unobserved length of a gap outside
the episode.

The actor instead maintains modeled ages and maxima from lawful executed
settlement. At report t, score the modeled record increment over t..t+3:
old action/mask at t,t+1 and candidate at t+2,t+3. Add the value at the
**pre-current-C boundary t+4**. The value input carries the candidate commands/
mask that still execute at t+4,t+5 and the current report's post-C nav as the
next boundary's previous nav. No actual future C proposal or post-current-C nav
is an input. At t=252, the four elapsed ticks reach terminal 256 and V=0.
The existing delivered-four-tick M/native score still costs t+2..t+5, clipped
at the native horizon; it is not silently shortened to two delivered ticks.

For old M data, pre-C navigation at report t>=4 is the previous report's saved
post-C nav. Decode the current anchor from saved packets, exclude that current
packet's newly chosen C proposal/nav from value features, and use only model
contacts strictly before t whose causal settlement is already complete in the
stored stage record. The terminal log by itself is not proof that a past actor
could see the information. This permits later extraction without new physics
queries, but **no extraction or rescoring has been performed in this design
task**. Original true positions/maps/observations and actual contacts may only
supply offline targets/verification, never deployment features.

### Proposed fixed representation, target and comparison

Use the same 805-component float32 input for ridge and MLP, with fixed scaling
and no fitted normalizer or learned encoder:

| Field | Width and fixed meaning |
|---|---|
| Decoded map | 100, xy/1000 in registered user order |
| Decoded boundary anchors | 15, (xyz-LOW)/(HIGH-LOW) |
| Effective commands and mask | 15 command components in {-1,0,1}; 5 mask bits |
| Previous post-C nav | 50, five separate 10-way one-hot vectors |
| Modeled age and running maximum | 50+50, divided by 256; omit redundant last-service tick |
| Modeled window contacts | 200, the existing four-by-50 bits |
| Known-unserved and availability | 50 indicators last<0 under a complete history; 3 indicators for decoded map, anchor and complete origin-to-boundary history |
| Clock and rotating member | 2, t/256 and (256-t)/256; 5-way one-hot (t/4) mod 5 |
| Per-user fixed relations | 250: d, d², slack=(b-age)/256, d·age/256 and d·slack |
| Pooled fixed relations | 10: means and second moments of age/256, b/256, slack and d; means of the two interaction terms |

Here d is distance from the decoded user at z=0 to the nearest UAV active under
the effective boundary mask, divided by sqrt(1000²+1000²+150²). The nonempty mask
makes it defined. Quantize a synthetic candidate endpoint with the same position
codec before packing it. These features use geometry arithmetic, not additional
radio/model queries. The pooled terms do not make the entire network permutation
invariant. This basis was added prospectively to both estimators because a ridge
on separate raw geometry and ages could not express even their simple interaction.
A neural win would still not prove that every ordinary basis or linear alternative
fails.

A usable feature row requires an anchor at tick 0, all executed transitions
settled causally to the boundary, and known modeled maximum history. Incomplete
rows are retained as missing evidence and excluded from regression, not filled
with invented b/age. For deployment, if M has completed lawfully but maximum
history is unavailable, the new planner may use that completed M candidate;
there is no value query on fabricated features. Any whole-round deadline or
incomplete M/search computation instead retains the old commands/mask, as in
the original contract. No partial result or late M rescue is delivered. Count
these cases separately. Expected label counts below assume eligible histories;
fewer labels never reduce reported episode exposure.

The supervised target at a real M-suffix boundary t is
y_t = mean(actual b(256)-actual b(t)).
Normalize y by 256. This is **not** actual G_final minus modeled G_t. Predicting
native remaining increase from modeled b does not reveal the hidden actual past;
adding a modeled prefix increment remains approximate. The suffix after every
training row must actually follow M, including its outstanding two-tick
commitment. No fictional branch, relabeled physical suffix or value bootstrap
supplies a target.

The complete proposed arms are M, S, G0, LR and LN. Each new planner generates
the full M candidate (232 requests), runs the same two-order coordinate search
with its own new key (116), then explicitly includes M (at most1 additional
request): **349 pre-cache requests/report**, within the legal 27x31 space.
It is not exhaustive search. The key minimizes modeled elapsed record increment
plus its terminal value, then elapsed four-tick cumulative age, then the existing
delivered-four-tick native tie key. Values affect the inner searches as well as
the final choice. Candidate physics is cached across all these rankings.

G0 uses terminal0. LR uses weighted ridge with lambda=0.001 and an unregularized
intercept. LN uses two 128-ReLU hidden layers and an unclipped scalar output,
Adam learning rate0.001, 4,096 minibatches of 256, one fixed initialization/data
sampling realization and the final checkpoint only. Hidden layers receive
ordinary seeded nonzero initialization; only the last scalar weights/bias start
at zero. Therefore G0 is LN's exact **pre-fit decision rule when computation
completes**; extra inference time can still change a deadline outcome and must
be charged. Both models deploy 256 times the scalar output, clipped to
[0,256-t], with terminal256 exactly0. Both train the same weighted MSE objective:
each eligible episode has equal total weight, and its eligible reports share
that weight equally. LN samples episode then eligible report uniformly. Ridge
uses those same weights. No validation-score search, checkpoint selection,
online update, feature revision or repeated acquisition is part of this recipe.

M/S remain full-use references. R's retained evidence remains in B01/B02; this
proposal does not buy a fresh R arm or claim improvement over every fairness
reference. G0 controls direct objective/search development, and LR tests whether
a modest fitted relational basis captures the benefit. Neither retaining M
among scored candidates nor any prediction metric gives a policy-improvement
guarantee.

### Proposed exposure, full cost and reading

Reuse all 64 already-paid B02 M trajectories with their recorded canonical raw
hashes. Acquire192 fresh H256 episodes:96 pure M and 96 with one uniformly
sampled legal command/mask pair at a prebound report, then M for the remainder.
For perturbation j=0..95 use report index floor(63*j/96), hence0..62, and train
only at later reports. Uniform means uniform over encoded27x31 pairs; it does
not mean uniform over physically non-aliased behaviors. Pure M contributes
reports 4..252. The resulting maximum is 160*63+3,102=**13,182 suffix labels from
256 distinct training episodes**, not13,182 independent worlds. Old training
worlds have already been exposed and are not holdout data.

Evaluate64 untouched common worlds with all five frozen programs:320 episodes.
This is **512 new H256 episodes /131,072 native steps**, plus 64 reused episodes/
16,384 previously paid steps. There are **2 initial scientific regression fits
on one acquisition realization**, one analytic ridge solve and one neural fit;
they are not independent training replications. The acquisition/evaluation
worlds, intervention tapes, initialization and minibatch seed must be bound
before any execution if Root selects the proposal. There is no data-dependent
arm or seed selection.

| Prospective work | Count or explicit uncertainty |
|---|---|
| Candidate requests | 192*64*232 +64*64*(232+116+3*349) =8,564,736 upper bound before cache reuse |
| Candidate-state reductions | (192*232+64*(232+116+3*349))*(63*4+2) =33,991,296 upper bound;4-per-request loose bound34,258,944 |
| Prefix and history model work | 65,536 committed-prefix reductions; up to 131,072 executed-history/terminal settlements for the new full episodes, separately counted |
| Actual C decisions | 512*64*5 =163,840; no virtual future-C call |
| Deployment value queries | At most2*64*63*117 =943,488; terminal zeros require no network call |
| Value/fit verification | Up to 943,488 saved-choice value re-evaluations,8,064 held-out M-suffix predictions, and 26,364 final training-row predictions; all separately metered |
| Learning arithmetic | Original ridge weighted solve and 4,096 Adam steps /1,048,576 minibatch presentations. A deterministic full fit replay in the reader adds one weighted solve and another4,096 Adam steps; no new acquisition or independent statistical replication. |
| Communication | New full episodes:4,620,288 recurring bytes and 204,800 map bytes; fixed141-byte report rounds |
| Necessary native correctness if selected | One H8 common fixture world across the five interfaces,40 native steps/0 scientific fits, using fixed stub values where appropriate; synthetic history/target/feature/deadline checks separately metered. No such fixture has run now. |

The 805-wide input matrix at 13,182 rows has 42,446,040 float32 bytes; LN has 119,809
parameters (479,236 float32 bytes). These are analytic payload sizes, not peak
RSS or total artifact sizes. Preserve one canonical copy of new native evidence,
training inputs/checkpoint and full reader output; publish compact per-world
results, provenance and counters. Avoid retaining a fully materialized feature
matrix for every candidate when a saved trace and prediction are enough to
reconstruct it. B02 averaged about1.6MB compressed/raw episode, suggesting an
order-of-1GB new trajectory bill, but changed traces/compression make the actual
serialized size unverified. Preserve the old64 M raws by reference, not by a
second retention package.

For the proposed configured wsl_4070 CPU path, old M/S scheduler rates give
about3,006 CPU seconds (0.835h) for new acquisition/evaluation scheduling
before new feature/value overhead. Scaling the external B02 reader's1,113.99
CPU seconds by the upper candidate-reduction ratio gives about4,299 seconds
(1.194h), versus the Oracle's lower episode-based nominal estimate. These are
different planning extrapolations, not measured bounds. **Approximately2–3 CPU
hours** is a useful provisional worker/reader/fit expectation, with changed
feature arithmetic, full fit replay, imports, I/O, engineering and support
unmeasured. Record actual component and lifetime CPU/wall, peak RSS and disk;
there is no admitted budget or guarantee of timing. The current compute table
names the gcc3.10.21 interpreter as a provisional mitigation, not a cure for
B02's unexplained radio exception. Actual-node admission is needed only if a
result launch is selected.

Read every native trajectory and the causal feature/target/selection pipeline,
including reused training-source hashes. Check native contacts/ages/maxima and
the telescoping identity; every fit update/counter/parameter change; causal
input provenance; request/cache/choice arithmetic and deadline fallback. The
proposed physical reader keeps B02's bounded scope: every actual native/C and
executed-model transition, each selected candidate, and every visited candidate
at reports 0/60/124/248. Rebuild age/max/value/key arithmetic from saved contacts
for all remaining evaluated candidates; this is not an exhaustive radio replay
or an optimality claim. For old64 M trajectories, reuse the source-bound B02
physical verification and recheck raw hashes plus the newly derived causal
features/targets, without repurchasing all old candidate radio calls. Report paired
world levels and all prespecified contrasts for G, extreme/censored gaps,
worst-user mean age, mean age, J/service/quality, travel, transmitters and total
compute. The primary complete-use contrast is LN-M on G; LN-G0 is the main
experience-use comparison; LN-LR, LR-G0, G0-M and comparisons with S preserve
ordinary and tail alternatives. World-paired intervals describe one fitted
acquisition instance; reports/users/epochs are not independent replicates.

Log chosen-pair differences from the already computed M candidate, value
dispersion/clipping, and zero-terminal rankings within the same visited set.
That last calculation is not the full G0 controller at the same state: its own
coordinate search could visit different pairs. Low fresh-M suffix error does
not validate counterfactual M continuation on states selected by LN, and a
realized LN suffix follows LN rather than M. Do not score its observed suffix
as an M-value prediction error. No extra shadow physical branches or native
suffix bank is authorized by this design.

Constructive prediction: learned continuation changes executed pairs and lowers
G beyond both M and G0. The strongest ordinary competing outcomes are that G0
captures the benefit, or LR captures it without a demonstrated neural increment.
Retain either as a useful capability; absence of a significant LN-LR difference
is not equivalence. A G benefit with worse service or extreme tails is a
conditional frontier point, not default adoption. An active native negative
ends this finite recipe; sparse changed choices limit the learning/exposure
reading; missing targets, failed fits or deadline-dominated deployment are
technical or exposure limitations rather than evidence against learning in
general. None automatically purchases a repair, another fit or confirmation.

### Independent recommendation and DM investment judgment

Root's separate-context Astra Max Oracle reconstructed the original evidence,
read the primary bridges and returned the complete recommendation preserved
below. It checked five original native trajectories, not a second full-panel
reader; its agreement is advice, not new independent empirical replication.
I directly read the cited load-bearing pages in B01, Remembering to Be Fair,
Diminishing Return of Value Expansion and Inst-sci VS-0005, plus Bertsekas
sections1–2/Proposition2.1. The exact-value/Markov assumptions do not hold here.
Running-max memory gives the algebraic objective decomposition without making
the public state Markov. None of these sources identifies the cause of B02's
negative primary result or establishes novelty.

I accept the recommendation with the explicit timing, eligibility, feature and
cost refinements above; **no material scientific disagreement remains**.
Selected-state extrapolation is the strongest objection. One perturbation per
world broadens observed support but neither covers the planner's future
selected distribution nor recovers hidden exact radio state. A good fit could
still supply the wrong action ranking. That objection limits the claim and
lowers expected success; it is not a mandatory preliminary model-accuracy,
toy-pass or counterfactual-headroom gate.

My preference is the complete five-program comparison over first buying only
M/S/G0: it directly answers whether experience adds useful continuation value
and can return a useful ordinary or linear positive in one bounded study.
The cheaper alternative is 64 worlds times M/S/G0,192 episodes/49,152 steps,
0 fits and no training acquisition; it answers the narrower ordinary-objective
question and remains a legitimate allocation, not a required positive precursor.
N8's newly positive relocation/activation/C-reoptimization capability is a
stronger demonstrated starting point. A comparably concrete, inexpensive
continuation-development question under that lead could take priority. The
existence of four DM slots alone does not justify this investment, and I do not
take over N8 or claim it needs learning.

**Return boundary:** this is a feasible, costed design recommendation, with no
selected result execution. Root owns whether to invest in this complete design,
the cheaper ordinary-only alternative, an N8 development or neither. If
selected, new code belongs in this direction's B03 paths with a bounded L0,
fixed data/RNG/fit inputs, engineering review and published source before launch;
the frozen B02 files and evidence are not rewritten. No new shared host/control
change is indicated. Exact runtime/deadline margin, serialization size, support
coverage and native benefit remain unresolved. B02 remains completed and no
accepted operation is waiting to be resumed.

<a id="b03-original-oracle-advice"></a>
### Original independent Oracle recommendation, received 2026-09-30

The following is the complete substantive recommendation, with spacing and
paragraph formatting normalized. Its nominal reader estimate is retained as
advice; the more conservative DM calculation above is the current planning
estimate. The zero-initialization statement refers to the decision rule, with
the deployment-time caveat already made explicit above.

I recommend a bounded successor question in uav_user_waiting: can native
experience improve average per-user worst interruption by learning the remaining
M-continuation cost and using it inside the joint command/mask search, beyond both
competent M and a direct-objective ordinary planner? Revise the next approach,
retain the published B02 disposition and M/S capabilities, and make no claim
that a horizon, ACK, representation or learning bottleneck has been identified.
This develops the controller's action choices rather than ranking unchanged
assets. The decision clock remains fixed; a learned option duration is not part
of this proposal.

I reconstructed the waiting evidence before forming this proposal, then used the
waiting DM's source check to resolve boundary, feature and cost details. I
checked all 62 scientific source hashes in B02's frozen configuration against
current files; all matched. I read the compact positive/adverse/failure records
and independently reduced five retained native trajectories, including A/S/M on
seed 29322048 and S/M on29322000. I did not repeat the complete256-episode reader,
audit every candidate replay or independently reproduce all current portfolio
results. Those remain explicit limits.

The strongest empirical premise is the existing tradeoff, not a failed-predictor
narrative. In the 64-world B02 panel, M's mean per-user maximum gap was 19.826875,
extreme maximum gap55.921875 and mean service24.596436. S gave20.964063,46.968750
and 20.933899 respectively; A gave20.455625,49.921875 and 21.247375. S's extreme-tail
improvement cost service in all 64 worlds and worsened the average per-user worst
gap versus M by 1.137188 [0.335121,1.939254]. A-M on that average gap was+0.628750
[-0.215564,1.473064], despite644 executed pair changes,289 with positive modeled
current sacrifice. A was an active intervention, not nonactivation. On
A/29322048, user 20's98-tick gap occurred with modeled contacts exactly equal to
actual contacts for that user throughout the episode; S and M on the same world
had extreme gaps47 and 50. This removes an ACK error explanation for that witness,
but does not prove generally correct histories or that longer prediction is the
remedy. Source: runs/uav_user_waiting/b02_continuity_a03/result.json; frozen
scientific source 16500b6f85c8cd20a7765801ed413608c36cf9f0, protected continuation/
reader db13ccf307e9cf467450fdad8318721fb8db603a. The complete reader covered 256
trajectories/65,536 valid steps; the 112 failed original native steps remain
charged. Known worker plus full-reader cost was 2,651.306 CPU seconds, with some
support/A02 cost unmetered.

The prior learned service-age selector is a serious negative. One fit consumed512
training episodes plus 448 evaluation episodes,245,760 native steps, and both
actor/critic moved. L1 improved its own mean-age result from 3.816882 to 3.542917
but remained worse than M's3.273864; its mean per-user maximum gap was 21.614
versus M 20.2025. It made738 evaluation choices differing from M, so this was not
merely inactive learning. Worker and external reader cost approximately4,564.268
and 2,121.840 CPU seconds. Source:
runs/uav_service_age/b01_age_selector_a01/result.json. The proposed change is
substantive—native suffix regression and action-level ranking under a different
existing objective—but a negative would still be a finite-package result, not
evidence that learning or temporal reasoning is impossible.

Literature supports the construction's form, not its success. DIRECT: B01,
docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf, physical p60/printed31,
Eqs2.38–2.42, gives policy improvement with the appropriate exact value function.
Bertsekas arXiv1910.00120v3, https://arxiv.org/html/1910.00120 sections1–2/
Proposition2.1, gives base-policy rollout and componentwise search under its
state/action-ordering assumptions. INFERENCE: retain M's candidate and
approximate its remaining cost, but our partial lawful state, learned value and
finite search inherit no no-worsening theorem. DIRECT: Remembering to Be Fair,
paper icml-2024-pmlr-v235-alamdari24a,
/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-alamdari24a/arxiv-2312.04772.pdf
pp5–7, distinguishes temporal and stakeholder aggregation and uses explicit
reward memory under declared conditions. INFERENCE: our maximum-gap state makes
the objective telescoping; it does not establish a Markov public state or license
counterfactual physical suffixes. DIRECT counterweight: Diminishing Return of
Value Expansion Methods in Model-Based RL, iclr-2023-virtual-11586,
/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2023/iclr-2023-virtual-11586/arxiv-2303.03955.pdf
pp2–5, shows that oracle accuracy/longer model rollouts did not automatically
establish superior sample efficiency in its studied SAC tasks. It is not a UAV
impossibility result. I also checked the formal Inst-sci store: VS-0005,
/home/fires/projects/Inst-sci/papers/MyLib/json/VS-0005.json pp3–4, studies
action-repeat options and prefix reuse under a different commitment contract.
Together with July's R30 fixed-clock design and external-review record, these
checks rule out a novelty claim or an automatic case for reopening duration
selection. All three libraries were searched; index hints were locators, not
evidence.

Define actual service age a_u(t), running maximum b_u(t)=max_{s<=t}a_u(s), and
G=mean_u b_u(H), H=256. Per-tick increments mean_u[b_u(t+1)-b_u(t)] telescope to G
from the initial state. The deployed controller maintains MODEL ages/maxima/
windows from settled executed history only. Native contacts and actual b are
offline regression labels and reader evidence, never new deployment ACKs. Train
y_t=mean_u[actual_b_u(H)-actual_b_u(t)] on suffixes genuinely followed by M. This
is not actual G_H minus modeled G_t. A modeled immediate increment plus expected
native suffix remains an approximation when history/geometry are imperfect.

Keep the actual N5/U50 native S1 host, static 400-byte registered map,27 commands
and 31 nonempty masks. Reports remain every4 ticks; the rotating member is
(t/4) mod 5 and the other four use current C proposals. Five 25-byte reports plus
a 16-byte command packet cost 141 bytes/report; at 2 kbit/s, wire time is 0.564
seconds, leaving1.436 seconds of charged computation before two-tick delivery.
At report t, old commands/mask execute t,t+1; the candidate executes t+2,t+3
and remains committed at t+4,t+5. Score the four elapsed ticks t..t+3 plus V_M at
the pre-current-C boundary t+4. The value state MUST include that still-committed
candidate action/mask and the prior report's post-C navigation memory. Do not use
actual future C outputs. At t252, score the final four elapsed ticks and use
terminal value 0. Hypothetical histories are private copies; only executed
history updates persistent memory. Whole-round lateness retains old commands/
mask, with no partial or late rescue.

The code supports this boundary:
experiments/candidates/uav_user_waiting/b02/scheduler.py already retains the
midpoint after two delivered ticks; study.py retains model_contacts and
navigation records for causal reconstruction. The service_age feature path
supplies lawful missingness conventions, but its learner is a two-action PPO
implementation, not a reusable supervised value learner. A new bounded history
maximum/feature pack, acquisition collector, ridge/MLP fit, ranking path and full
reader are required. No shared host rewrite is indicated.

Both estimators receive the same fixed-scaled decoded map/anchors, effective
commands/mask, previous post-C nav(one-hot), modeled ages/maxima/windows,
known-unserved/availability flags and time/phase. Add the same fixed relational
features to both: per-user nearest-active3-D distance d normalized by
sqrt(1000²+1000²+150²), d², slack=(b-age)/H, d·age/H and d·slack; plus the ten
pooled means/second moments and interaction means agreed in the DM source note.
These require geometry arithmetic, not new radio queries or a learned encoder.
Quantize synthetic endpoint anchors through the same codec. History unavailable
from tick 0 must not be converted into fabricated b/age; freeze row eligibility
and the lawful completed-M fallback prospectively. Deadline fallback remains the
original hold rule.

Evaluate five complete programs: M; S; G0, the direct four-tick record-gap planner
with terminal value 0; LR, that planner with fitted ridge continuation value; LN,
that planner with fitted neural continuation value. Each new planner first
generates M's full candidate(232 pre-cache requests), retains it, conducts the
ordinary two-order coordinate search using its own key(116 requests), then
compares M explicitly(up to one additional pair): at most349 requests/report.
Value changes inner and final ranking. Secondary key is modeled cumulative age
over the four elapsed ticks, followed by the existing delivered-four-tick native
tie key, with native-horizon truncation. G0 is a consequential ordinary
comparator; M and S remain full-use references. Candidate retention is not a
policy-improvement guarantee.

Smallest complete learning comparison I recommend: reuse all 64 already-paid B02
M trajectories, collect192 fresh full episodes(96 pure M;96 with one legal
uniform(q,mask) intervention followed permanently by M), and evaluate64 untouched
common worlds times 5 programs=320 episodes. Prebind acquisition worlds, evaluation
worlds and separate intervention tapes. For intervention j=0..95, freeze report
r_j=floor(63j/96); train only at later report states whose future really is M.
Pure episodes contribute reports 4..252. If histories are eligible throughout,
160*63+sum_j(63-r_j)=13,182 labels. Retain every native episode, including adverse/
censored failures; any unavailable label reduces usable rows, not reported
exposure. This is 512 NEW complete H256 episodes/131,072 native steps, plus 64
reused/16,384 already-paid steps. It is a recommended bounded exposure, not a
sample-complexity lower bound or guarantee of learnability.

Fit weighted ridge(lambda=10^-3, intercept unregularized) and a
two-hidden-layer 128-ReLU MLP on the identical data/features. Give episodes equal
aggregate weight; sample episode then eligible report uniformly for the MLP.
Normalize target by H; use Adam 10^-3 for 4,096 minibatches of 256, one fixed seed,
final checkpoint only. Zero-initialize only the final scalar layer, with seeded
nonzero hidden initialization, so G0 is exactly LN's pre-fit deployment. Train an
unclipped scalar MSE output; deploy H times output clipped to[0,H-t]. Ridge uses
the same clipping. These are two started regression fits on ONE acquisition
realization, not two independent learning replications. No score-driven
checkpoint, feature or hyperparameter search is proposed.

Complete cost:8,564,736 pre-cache candidate requests;33,991,296 candidate
reductions after terminal truncation, plus 65,536 committed-prefix reductions and
settlement;943,488 nonterminal terminal-value queries in deployment. Rechecking
all learned values in the reader incurs up to the same query count again; fresh
M evaluation supplies 8,064 held-out suffix predictions for the two models
without extra episodes. Count training prediction diagnostics separately. The
neural fit has 1,048,576 minibatch sample presentations/gradient participation;
ridge has one weighted solve. All512 new plus 64 reused trajectories require
physical/history/target/choice/deadline reading. Nominal new-episode communication
is 4,620,288 recurring bytes plus 204,800 map bytes. Old measured M scheduling was
323.810 CPU seconds/64 episodes; the old complete reader used 1,112.707 seconds/
256 trajectories. Crude scaling suggests around 0.8 scheduler CPU hours plus 0.7
reader CPU hours, BEFORE changed features, fitting, imports, storage and
engineering/support. These are planning extrapolations, not measured new costs
or node admission. Exact peak memory, serialized bulk size and actual deadline
margin remain unverified; avoid retaining redundant fully materialized candidate
feature matrices when traces and outputs suffice.

Constructive prediction: LN reduces G against both M and its exact pre-fit G0
through executed command/mask changes, with complete native service/reward,
extreme-gap/worst-user-age, quality, travel and transmitter cost reported.
Opposing ordinary prediction: G0 absorbs the gain because direct objective
arithmetic is sufficient. Another useful outcome is that LR supplies the effect
and no additional neural benefit is established; prefer the simpler fitted
capability without claiming statistical equivalence. If mean-gap benefit
purchases service or extreme-tail deterioration, retain it only as an explicit
conditional frontier point, not a default controller or universal improvement.
There is no invented mission threshold to make a method win.

The strongest consequential objection is selected-state extrapolation. Observed
M and singly perturbed M suffixes need not support the synthetic states selected
by a new planner. Navigation memory and relational features do not make the
observation Markov, and low held-out M prediction error does not validate
counterfactual M continuation on LN trajectories. The one-intervention acquisition
addresses some support, not this guarantee. Separate: valid choices rarely
differing(nonactivation/sparse exposure); genuinely different executed choices
that worsen native outcomes(active adverse intervention); and outcomes obscured
by censoring/deadlines. An active negative stops this finite recipe without
demanding a repair; a sparse-choice result does not refute value-based control
generally. A narrow positive warrants replication only if another independent
data/fit realization would change a practical or scientific decision. More worlds
for one fit are not that replication.

This deserves a bounded place because it targets an already-declared native
continuity quantity, reuses demonstrated ordinary control and paid experience,
and permits a useful ordinary positive while changing actual action development.
It does not duplicate N5 policy reward-development, parent joint sampling or
anonymous-peer forecasting. The newer N8 relocation result also merits
constructive attention under its owner: R-J reward/service gains
(+0.01765/+1.55225) coexist with quality/travel/adverse-world costs, and
after-arrival C reoptimization remains part of the useful closed loop. I read
its compact output and original independent review, not an independent full N8
raw audit. A well-posed inexpensive N8 continuation-development comparison could
take priority over this still-conjectural acquisition/two-fit investment. Four
active DMs are not themselves a reason to run it.

A useful lower-cost alternative is M/S/G0 only:64 worlds times 3 programs=192
episodes/49,152 native steps,0 fits and 0 new training acquisition. That answers
whether directly targeting accumulated worst gaps improves ordinary control; it
does not answer whether learning remaining cost helps. It is an alternative
allocation, not a mandatory positive precursor or another unbounded gate.

MATERIAL_DISSENT: no, for Root's current design-only continuity assignment and the
bounded comparison as a proposal. No run is authorized by this review; the
retained source limits, complete costs and competing N8 investment remain part
of Root's decision.

### Pre-publication background refresh

Current published main advanced to
c0a9ddc5a856e83c01583cd17afed3652cb16ef4 while this note was prepared. I read the
affected topic2/topic4 B04 additions and current direction standing. Parent
adaptation's fixed joint-sampling primary failed, while the distinct fixed
S_I-Q_I comparison retained J+0.024075, service+1.767029, service-p10+3.546875 and
path-1232.241m/UAV, with serious adverse worlds. This strengthens the competing
investment in an already demonstrated inherited asset. It does not measure this
proposal's individual-user maximum-gap objective or change the lawful M/S
comparison, and it is not evidence that all learning is adverse. Root's final
allocation should include that positive alongside N8; neither the new value
design nor the older failed selector owns the project-wide learning question.
This refresh adds no run, rescore or changed result to the present design-only
scope.

<a id="b03-selected-l0"></a>
## 2026-09-30 — B03 selected implementation and fixed exposure

Root selected the complete design above at published
`1ab42997a5a805764d5c54e3fdd810fcc2fdf514`
([decision](../../RESEARCH.md#waiting-value-root-decision-20260930)). The accepted
exposure is 192 new acquisition plus 320 evaluation episodes (131,072 native
steps), two scientific fits on one acquisition realization, and all 64 paid B02
M traces by canonical hash/path reference. The separate necessary correctness
fixture is five interfaces on one H8 world (40 native steps, zero scientific
fits). No automatic repair fit, enlarged acquisition or confirmation is bought.

**Fixed identities, before code or execution.** Pure-M acquisition worlds are
`29423000..29423095`; single-perturbation worlds are `29423100..29423195`;
evaluation worlds are `29424000..29424063`. The perturbation for index j remains
report `floor(63*j/96)`; a local NumPy PCG64 stream seeded `29425002` draws each
encoded q uniformly from 0..26 and mask uniformly from 1..31, in that order for
j=0..95. Initialization uses `29425000`; episode-then-row PCG64 minibatches use
`29425001`. The H8 correctness world is `29425999`, never an acquisition or
evaluation world. Reused B02 M seeds remain `29322000..29322063`. No global RNG
stream is repurposed. Common evaluation arms rotate the forward and reversed
M/S/G0/LR/LN orders by world index. Descriptive paired bootstrap, if used, has
seed `29425991` and 10,000 world resamples shared across contrasts. A source and
notebook search found no prior assigned worlds in these new ranges; numerical
substrings in unrelated tables are not world identities.

**L0 deliverable and ownership.** Add direction-owned B03 implementation and
mirrored tests, without modifying frozen B01/B02 or the shared host. The entry
will acquire the fixed data, fit the fixed ridge and MLP, evaluate all five
frozen programs, and retain compact results plus one canonical raw copy. A
separate reader checks the causal feature/target pipeline, native and bounded
physical replay, every value/key calculation, and full deterministic fit replay.
Only this DM edits this notebook, collection/integration/history/scheduler/data/
reader and run records. The registered Implementer owns only new
`b03/features.py`, `b03/learner.py` and mirrored `test_values.py`, on shared main,
with no Git/index mutation, launch, notebook or other-file edit. The independent
engineering Reviewer receives the completed diff and contract before execution.

The fixed feature interface accepts decoded sites/anchors, effective commands/
mask, previous report post-C nav, modeled last-service/max/window arrays, tick,
history start and causal settled boundary. It returns exactly 805 float32
components or rejects an incomplete history; the formula and H256 scales above
are unchanged. The learner accepts those rows, native-tick suffix targets and
episode IDs. Both fits use equal episode weight and equal row weight within
episode. Ridge is a float64 weighted solve, lambda .001 on weights only; the MLP
is CPU float32 805–128–128–1 with two ReLUs, seeded ordinary hidden initialization,
zero final affine, Adam(lr=.001, betas=(.9,.999), eps=1e-8, weight_decay=0), exactly
4096 updates of 256 rows and final checkpoint only. Saved initial/final movement,
update losses and sampled row identities allow independent exposure accounting
and exact same-node numerical replay. Models expose raw tick predictions and
the prescribed [0,256-t] deployment clipping; no training target is clipped.
Checkpoint files are pickle-free named numerical arrays. No new fitted scaler,
validation selection, feature search or hidden hyperparameter is introduced.

**Invariants and checks.** Preserve delayed native commitment, actual pre-mask-
arrival radio capture, current-only C calls, the M/S laws and four-delivered-tick
native ties. A new running-maximum history extends atomic executed settlement;
private candidate copies never settle persistent history. The new key uses the
two old-prefix plus first two delivered ticks, and pre-next-C features at t+4;
terminal V is exactly zero. Missing complete-origin history uses a completed M
only; a late/incomplete whole round holds the old command/mask with no late M
rescue. M generation has no value calls. G search calls the estimator only for
its queried pairs, cached per pair, with the explicit M inclusion and maximum
117 values/report. Record unfinished work, chosen/M pair, visited-set G0 rank,
clipping and true elapsed/CPU costs. Tests target these causal, numerical,
RNG/checkpoint and fallback risks, plus the fixed 40-step native fixture after
source publication and actual-node admission; no outcome-bearing pilot is added.
Engineering estimates retain the earlier provisional 2–3 CPU-hour calculation
with new feature/fit/I/O overhead unmeasured and will be updated from actual
support measurements. Stop on incomplete scientific execution, preserve its
evidence, and diagnose without silently spending another fit or episode.

### B03 engineering acceptance, before native exposure

The bounded Implementer returned the three assigned feature/learner/test files;
I inspected their full source and accepted the implementation. The complete
synthetic suite is **40 passed in 4.09 seconds** on the configured local scientific
interpreter with one BLAS/OpenMP thread. Independent engineering review reran
the same suite (**40 passed in 4.17 seconds**) and found no remaining material
issue. It caught a real reader caller defect: a history-loop temporary overwrote
the value-model argument. That was corrected before native exposure, with full
LR/LN decision-reader regressions. The reviewer verified all 62 inherited
scientific source files remain byte-identical and all 64 reused M references
match the published B02 artifacts and verification. No scientific/native result
has been generated during this acceptance. The helper's separate value suite
passed 30 tests in 2.00 seconds. Per value-suite invocation the synthetic
arithmetic includes three 805-feature ridge solves, one two-dimensional
reference solve, nine learner Adam updates plus one manual Adam reference
update (40 total minibatch presentations); these are toy correctness work,
not the two selected scientific fits. Geometry tests and reader regressions
make additional synthetic model calls, with no native environment transition.
No complete scientific fit or outcome-bearing pilot was added.

Source-only checks cover exact 805-component arithmetic, active-mask geometry,
complete-origin eligibility, maximum-history copies/atomic settlement, actual
remaining-increment targets, previous-nav/current-C separation, same-law M/S
rankings, initial G0 equivalence when computation completes, terminal zeros,
117-query limit, and late-value fallback after completed M. They also cover
equal-episode weights, the unregularized ridge intercept, fixed local sampling,
global RNG isolation, reduced-update deterministic neural replay, checkpoint
identities and pickle-free storage. Actual-node layout, the 40-step native
fixture and full-sized deterministic fit replay remain execution evidence.

The worker verifies every required old M raw hash before acquiring a new
episode. Old raw data remain in their canonical B02 paths; only a compact
source-bound proof/reference manifest is new. Initial fit predictions are known
zero algebraically, so no hidden full-row initialization pass is made. Each
fit retains its already-computed final normalized predictions in the trace;
the reader uses the replay fit's existing final predictions for its independent
weighted-error calculation, without another training-row model pass. The
visited-set zero-value diagnostic covers all physically evaluated M/G pairs;
it still does not equal a full G0 policy control at that state.

Use the admitted native launch/observation path for three ordered operations:
the selected correctness fixture, the worker, then its full reader. The reader
has a separate output directory and binds the canonical worker summary SHA256,
its original source SHA and every model/data identity before verification
optimization. This is the already-priced one ridge/4096-Adam replay, not another
independent scientific fit. Worker outputs are not rewritten. The inherited
native and navigation readers each reconstruct current C, so reader C calls
are separately **327,680** on a complete panel, in addition to the worker's
163,840; no virtual future-C call enters the actor. Fresh-M calibration uses
at most 8,064 predictions and fit replay's final training predictions at most
26,364, as designed. The earlier 2–3 CPU-hour planning estimate remains
provisional; no full-size feature/fit timing has been measured. A read-only
node process inspection found no active research worker before publication;
fresh admission and node contention are checked again at launch.

### B03 accepted operations and first observation

Inputs were published at `a045bc9b4e3ba9ef211474293c4bc43ad8b16b08` before
native exposure. Root assigned this direction the next exclusive heavy window on
`wsl_4070` for fixture, producer and complete reader. The canonical remote tree's
unrelated dirty controls and older HEAD were preserved; configured login-shell
fetch made the published source available to the native snapshot launcher. The
actual admission projection agreed on the lifted pause and this direction's
active `Codex DM (native child)` ownership. Remote Git's pre-existing automatic
GC warning did not prevent fetch, source verification or acceptance; no unrelated
Git repair or checkout reset was made.

The selected correctness operation `b03_correctness_a01` was accepted at
2026-09-30 18:49:33.936646 UTC and exited zero. Canonical output is
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_user_waiting/b03_correctness_a01/`;
operation claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/3a7152c6b44765365b45049e8a10604c05766e5fd0c9f658082487829cd4972e.json`.
The five H8 interfaces completed exactly 40 native/team steps, zero scientific
fits and zero optimizer steps. Native reward/radio/observation reconstruction,
all 40 modeled transitions and bounded candidate/history/key checks passed;
LR/LN each replayed 113 value calls. All arms had zero deadline misses. These
checks validate the defined model arithmetic, not equality between decoded
model history and the native service process: the fixture retains its observed
model-versus-native history differences. Measured wall time was 4.67145s,
process user/system 4.12979/0.33974s and peak RSS 422,552KiB. The collected summary
SHA256 is `7bfeea92fb797fdc6fc1f584be014d83d42c3ad1a6806e3ae472bdda4a8c4a10`;
compact local copies match canonical hashes, while the five raw files remain
only at their recorded canonical paths. This is correctness evidence, not an
outcome-bearing estimate.

The full selected producer `b03_value_a01` was then accepted at
2026-09-30 18:52:09.873791 UTC, with canonical output
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_user_waiting/b03_value_a01/`
and operation claim
`/home/wu/projects/HMASD/.git/hmasd-admission/d6a66f057cc5d6e340ac9ee5e1812ede7c01cb08005cfcda34f3779fb6a70003.json`.
Its accepted source snapshot is
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/d913f7219d8b43c6baa5dd66a0f8d5c4`;
supervisor/runner are PID 1147328/1147329 with start ticks 113705555/113705558
on boot `bb732fcb-1a33-4659-a786-331110ae41d3`. Published control observation was
`4e05c7d60894f145ec4572ee8706c364a70c4023`. Generation 24 of the same-session
deterministic observer adopted the matching live identities and consistent
accepted claim at 18:54:55 UTC. Registration's initial missing `jobs` wrapper
was corrected locally before observation; it never resubmitted a launch.
The native child remains active because App queue input is rejected for this
runtime. Fixture observation was drained and acknowledged; checkpoint rearming
continues on the producer's existing claim. The full reader remains selected
but unlaunched until a terminal producer summary can be bound by SHA256.

Root's N8 admission-schema warning was checked against this source: B03 retains
the actual admission dictionary and validates its `sha`; it has no guessed
`operation_id` access. No source change or extra exposure followed that check.

### Producer terminal and reader artifact-path adaptation

The producer exited zero at 2026-09-30 19:47:14.838393 UTC. Its complete
10,610,736-byte summary has SHA256
`f7b8a56a94c6c07a97071527ae43df6b0c1324f93e90c02815eb9a0ea100b525`.
Reported exposure is exactly 512 complete episodes/131,072 native steps, two
scientific fits, 13,182 labels from 256 eligible training episodes, and 4,096
Adam updates/1,048,576 presentations. These are collected producer facts;
complete independent reading remains outstanding. Worker lifetime user/system
CPU is 3293.497397/6.886158 seconds and peak RSS 939,196KiB.
Observer checkpoints 24/25 were drained and rearmed on the same claim; generation
26 READY `aa3c864502ea7f0cf7a845a1`, wake
`a8698e32-8a88-4b38-8c49-472d41f09b64`, supplied matching terminal identities and
was acknowledged into generation 27. No producer was restarted.

The first reader request, outer task `uav-user-waiting-b03-value-read-a01`,
exited 4 at 19:49:12 UTC **before admission or reader execution**:
`absolute author input is absent from published snapshot` for the canonical
worker directory supplied as `--worker-out`. Same-request reconciliation found
no reader output directory and no matching admission claim. There are zero
reader optimization, model or native calls from that refused request. Its source
snapshot input-rewrite rule recognizes `--generic-summary` for canonical bulk
artifacts, whereas the frozen reader's own flag is not recognized.

**Bounded L0:** add a sibling `b03_reader/run.py` admission/argument adapter,
outside the frozen B03 source-identity glob. It accepts the supported canonical
`--generic-summary` plus its exact digest, validates its own admitted published
SHA, and calls unchanged `b03.read.read_result` with the summary's parent and
the fixed original producer SHA `a045bc9b4e3ba9ef211474293c4bc43ad8b16b08`.
The original 75 scientific source identities, configuration comparison,
physical/history/value checks and deterministic fit replay remain intact. The
adapter does not acquire, fit a new scientific model, change a model or rerun
the producer. Its only optimization is the already-selected reader replay.
Output remains a separate canonical run directory. This DM owns the adapter,
focused admission/binding tests and notebook; no shared launch controls or
frozen B03 files are edited. Independent engineering assessment identified this
as the smallest supported solution; it rejected routing data through aliases
or placing reader outputs inside a disposable source snapshot. Review the small
diff and its checks before corrected first admission. The actual scientific
comparison and exposure are unchanged, so this is not a new investment decision.

The adapter's four mock-only admission/artifact-binding tests passed in 0.04s;
independent engineering review reran them (four passed, 0.04s), checked all 75
original source identities against the producer configuration and found no
material issue. CLI help and diff checks passed. No test invoked a model, fit,
reader replay or native transition. I accepted the bounded adapter; the current
adapter admission identity and original producer/scientific identity remain
separate. The refused request record is retained in the reader run directory.

The corrected first reader admission was accepted at 2026-09-30
19:57:08.864276 UTC from published adapter source
`737a50333e794fbca02bce45f335e9e92b1e0b56`. Its output is
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_user_waiting/b03_value_read_a01/`;
operation claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/e07b3bcb24d3579339183f140cdc8104eb21ec183413b69f02c511e8208e8e82.json`.
Snapshot `548aeb29c8a14a93b942c992862cdd31` carries the unchanged original
scientific sources plus the adapter. Native supervisor/runner are
1152868/1152869, start ticks 114090275/114090278 on the same recorded boot.
Observer generation 28 adopted those consistent live identities at 19:57:27 UTC.
The adapter's source identity is distinct from original worker/scientific SHA
`a045bc9b4e3ba9ef211474293c4bc43ad8b16b08`; the worker summary digest above is
bound before the selected verification replay. The existing independent
Scientific Reviewer is reading the original evidence and bounded raw witnesses
in parallel, with any conclusion explicitly conditional on the full reader.

<a id="b04-conditional-selection"></a>
## 2026-09-30 — Conditional ordinary service–extreme-continuity question

Root's native assignment at 20:38 UTC selects one M/S/U/K comparison **only if
the already accepted B03 full reader completes without material discrepancy**.
B03 collection, interpretation, publication and cleanup remain required first.
Until that boundary this entry is source-only reasoning; it adds no successor
code, model query, fit or native transition. The same DM owns the selected
successor after the condition is satisfied, without another acknowledgment.
Root subsequently retained the configured remote `wsl_4070` real-deadline
window for this chain; exact published inputs and fresh actual-node admission
are still required. No accepted operation is moved.

The substantive question changes openly: can a competent ordinary controller
retain square-age S's recurring extreme-wait improvement without its native
service loss? Here S is the ordinary square-age scheduler, never the inherited
neural motion policy. This develops a demonstrated ordinary capability; it
does not repair or rename the adverse G0/LR/LN recipe. Root assigns 64 fresh
matched worlds × M/S/U/K, H256 (256 episodes/65,536 steps/0 fits), plus at most
one necessary H8×4 correctness panel (32 separately charged steps, no final
worlds or complete quality pilot). Estimated full worker/bounded-reader cost
is 0.9–1.3 CPU-hours and implementation 3–6 engineering hours, with scientific
reading/publication additional. No sweep or adaptive extension is selected.

The source bridge and decision use current published background at
`239360b03f5d7acf788bd9ae5d4dccbde4f9237e`, especially RESEARCH topics 2 and 8:
native mean age, typical-user maximum gap and extreme continuity are distinct
uses; low regression error or locally favorable ranking does not certify the
whole dynamic policy. The earlier B02 S tradeoff and the still-provisional B03
replication supply the constructive premise. U and K must use the identical
union of all pairs visited by **unmodified** full M and S generators at the
same history. Only after generation does K filter on modeled mean delivered-
block service at least that of the same-state M winner, then use exactly U's
S key. M is in the pool and feasible. Changing the inner search path would
confound the filter with generation and is excluded. Entire-pool completion
must meet the existing deadline; otherwise retain old-action hold, without a
new M rescue. Precise terminal convention, service arithmetic/ties, fresh
addresses, bounded physics subset and source identities will be fixed in the
prospective L0 before implementation and execution.

<a id="b04-original-oracle-advice"></a>
### Original independent successor advice (complete)

The following is the complete unchanged recommendation returned by Root's
independent `oracle_next_capability` scientific reviewer. It reused its prior
separate-context review and original result critics; it is not an outcome-blind
review or a second raw-data audit. Root selected its bounded M/S/U/K question.

> **I recommend the ordinary M/S/U/K comparison as the next native investment, conditional on B03’s pending full reader finding no material discrepancy.** Its question is whether a service constraint can retain the ordinary square-age controller’s improvement in extreme waiting. End purchases for the unchanged B05 composition and B03 learned-value recipes. The saved B05 continuity reduction is feasible, but I would not make it a prerequisite for this distinct question.
>
> This follow-up reuses my earlier independent analysis and the original result critics. It is not outcome-blind. I checked source compatibility and consequential summaries; I did not repeat their raw/model audits or execute the proposed reduction.
>
> The evidence changes the opportunity:
>
> - **B05 weakens generic motion–radio complementarity.** S+S2 loses `.004497 J` against C+S2, with an interval crossing zero, and `.010311 J` against C+T2, with a negative interval. Its narrow positive against Q+S2 survives, as does substantially shorter travel. Ordinary management absorbs much of the earlier all-on S advantage. This supports retaining useful packages and tradeoffs, without selecting further composition training. [Complete B05 reading](/home/fires/hmasd-wsl/docs/research/candidates/uav_parent_adaptation/NOTES.md:4030)
> - **B03’s producer result actively contradicts the learned continuation-value prediction.** LN−M increases mean user maximum gap by `11.9028` ticks in all 64 worlds; LN−G0 is adverse in 59. LR is also strongly adverse. Both fits updated, so nonactivation does not explain this. The full reader remains pending; no feature, ACK or horizon repair is selected by these results.
> - **The constructive positive is ordinary extreme-continuity control.** M versus square-age S has mean maximum gap `57.77 → 48.33` ticks and worst-user mean age `13.32 → 10.29`, while service falls `24.59 → 21.08` users/tick in all 64 worlds. Typical-user G remains approximately unchanged, `20.19 → 20.63`. Thus the proposed successor changes the scientific question openly; it does not rescue B03’s failed G prediction.
> - **A missing-comparator claim needed correction.** The earlier service-age B01 already compared S2 and M on the same worlds: S2 delivered about `30.10` users/tick versus M’s `24.56`, but G was `69.78` versus `20.20`, and maximum gap `250.59` versus `55.66`. The basic service/continuity tradeoff does not require rediscovery. [Verified B01 result](/home/fires/hmasd-wsl/runs/uav_service_age/b01_age_selector_a01/result.json)
>
> For M/S/U/K, **S means the ordinary square-age scheduler, not the inherited neural motion policy**:
>
> | Arm | Decision rule |
> |---|---|
> | M | Existing ordinary M search and selection. |
> | S | Existing square-age search and selection. |
> | U | Generate the union of every pair visited by unmodified M and S searches; select globally using the existing S key. |
> | K | Generate that identical union; retain pairs whose modeled delivered service is at least the same-state M winner’s, then use the same S key. |
>
> The constraint must not alter search generation. The M winner is already in the pool, ensuring modeled feasibility. U separates the service constraint from the benefit of additional ordinary search. These are identical construction rules at any given history; deployed trajectories will diverge.
>
> All arms retain C motion proposals, existing lawful information, action rights, two-tick delivery, the 141-byte report contract and the 1.436-second computation deadline. A missed deadline retains the existing hold behavior. No additional ACK, future truth, actor state or fitted predictor enters.
>
> The proposed service floor is **a local model constraint, not a native or episode-level guarantee**. Quantization can cause prediction error; even an exact local comparison evaluates M at K’s current history, not along M’s counterfactual trajectory. Age/throughput scheduling already has ordinary antecedents, while stronger competitive guarantees require assumptions and deviation accounting absent here. [Age/throughput primary source](https://www.mit.edu/~modiano/papers/CV_C_204.pdf), [Anytime-Competitive RL](https://papers.neurips.cc/paper_files/paper/2023/hash/f53437debdd397c42929d929614bc705-Abstract-Conference.html)
>
> The smallest worthwhile complete observation is **64 fresh matched worlds × four arms: 256 H256 episodes, 65,536 native steps and zero fits**. Read native service jointly with maximum gap and worst-user mean age; retain original G, native J, path, all adverse worlds and complete cost. This is a fixed-program frontier comparison, without a training-generalization claim or assertion of overall controller optimality.
>
> The outcomes change the decision:
>
> - K improves extreme continuity while preserving native service relative to M: retain a useful conditional ordinary capability.
> - U matches or exceeds K: additional search explains the useful result; prefer the simpler unconstrained program where its service tradeoff permits.
> - K mostly reproduces M: the local floor seldom exposes consequential alternatives. That does not establish a learning limitation or an impossible frontier.
> - K changes actions but loses service or continuity: weaken this local-floor approach. Another weight, horizon or learned repair is not automatic.
> - A mean gain with meaningful service, J or tail losses remains a tradeoff, not a service-preserving upgrade.
>
> The complete cost estimates are:
>
> | Option | Scientific work | Planning cost |
> |---|---|---|
> | **M/S/U/K** | 256 episodes; 0 fits; 4,276,224 pre-cache candidate requests; up to 16,971,264 delivered-state reductions | Approximately **0.9–1.3 CPU-hours** including bounded reading; **3–6 engineering hours**, with scientific publication additional |
> | Saved B05 continuity reduction | All 512 existing traces; 0 native/model/actor calls; 0 fits | Expected seconds to under **1 CPU-minute**, with a **5 CPU-minute incomplete-stop envelope**; approximately **1–2 engineering hours**, plus interpretation |
> | Stop unchanged composition/value recipes | Preserve completed evidence and assets | No new scientific exposure |
>
> The native estimate includes approximately 29.4 scheduler CPU-minutes plus 0.35–0.7 reader CPU-hours. It is a scaling estimate, not profiling or resource admission. The reader must check all executed endpoints/history, selection arithmetic and a prospectively bounded physics subset. Any required native correctness exposure needs separate accounting.
>
> The saved B05 reduction is **compatible as endpoint measurement**:
>
> - B05 and waiting B03 share the frozen native factory, static uniform population, five UAVs, 50 users, H256 horizon, channel law and capacity-constrained connection assignment.
> - Both record connections after physical movement and before an arriving mask refresh can mutate the current connection arrays. Contact means actual assignment, not merely SINR eligibility.
> - Reuse the exact waiting definitions: reset contacts are unscored; the first unserved transition has age one; initial and terminal gaps remain censored; never-served users have a 256-tick gap counted in both boundary groups. Include two-tick startup and the final executed transitions.
> - B05 has **32 world units**, with Q/S tapes averaged within world. B03 has **64 different worlds**. Users, ticks and tapes do not become independent replicates, and the panels cannot establish matched M/S trajectory dominance.
>
> A full reduction would hash the existing 231.3 MB archive once and decompress about 1.25 MB of required members, covering 25,600 user histories. It needs neither the source snapshot nor staged S. No such reduction has been performed.
>
> Its decision value is narrower than K/U’s. It could reveal whether C_T2 or S motion changes the **matched B05** service/path/individual-continuity frontier, informing which existing package deserves a later continuity comparison. It cannot establish M/S dominance, test K’s service preservation, diagnose B03’s learning failure, or revise B05’s failed primary prediction. Given the existing matched S2/M evidence, I would buy it only when Root is actually choosing among those B05 packages for individual continuity—not as another gate before the native frontier study.
>
> I would defer motion×M/S composition and fixed-S2 learning. Both remain plausible questions, but the former has lost its generic managed-S premise, and the latter lacks a complete costed training comparison. CAL/CONT already supplies a selected, distinct learning investment.
>
> The three-library, July and external-review checks support ordinary scheduling/control antecedents, not a novelty verdict. Current measured expenditure also remains visible: B05 cost approximately **1,902 worker/reader CPU-seconds** with zero new fits; B03 has already cost approximately **3,300 worker CPU-seconds**, two fits and additional pending reader work.
>
> **MATERIAL_DISSENT: no.** No conflicting successor purchase is committed. I recommend the bounded M/S/U/K question above, preserving B03’s pending-reader condition and selecting no automatic repair or composition expansion.

### DM response and primary-source boundary

I accept this conditional change of question. The recurring S result supplies a
constructive capability worth developing; B03 does not supply a rationale for
another learned-value repair. The intended native pattern is K−M lower episode
maximum gap and lower worst-user mean age, jointly with nonnegative *sample*
mean service. This is a directional exploratory prediction, not a confirmed
noninferiority margin, adoption tolerance or required changed-choice count.
K−U asks what the floor adds at matched search; U−S asks what expanded ordinary
search adds. A successful model floor is an intermediate prediction only. Its
native service and continuity consequence must be read even if they contradict
it. Sparse intervention and active adverse intervention lead to distinct
interpretations; neither forces a new repair.

I directly read the following load-bearing passages, using the reviewer's
source locators. Searches of the three stores, July and earlier review are
antecedent checks, not novelty certificates. These are source identities and
scope, not new experimental evidence:

- Foundations **B01**, Albrecht/Schaefer/Christianos (2024),
  `docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf`, physical p60 /
  printed p31, Eqs.2.38–2.42; metadata
  `docs/new-libs/corpus/papers/B01/metadata.json`. PDF SHA256
  `4eec7be5bcabaf912846ddd295925c35d46502d92fcd9f7ba3311656fd2e9091`.
  The exact-value all-state improvement premise is stronger than keeping M
  feasible under a local service floor; it supplies no K performance theorem.
- Inst-sci **MARL-0558**, Zhao et al., *Multi-Agent First Order Constrained
  Optimization in Policy Space* (NeurIPS 2023),
  `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0558.json` and
  `/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0558.pdf`, §3 pp3–4 and
  §4/§§4.1–4.2 pp4–5. PDF SHA256
  `821c8ffad73bec4dfe73841047ea877076b2bce518239ff0dd3b6dee2103eb87`.
  Its expected discounted cost constraints, nonparametric update and parametric
  approximation are distinct from this finite deterministic local filter.
- My-lib **neurips-2023-f53437debdd397c42929d929614bc705**, Yang et al.,
  *Anytime-Competitive Reinforcement Learning with Policy Prior*, arXiv
  2311.01568v3 (2024-02-02),
  `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/neurips-2023/f53437debdd397c42929d929614bc705/arxiv-2311.01568.pdf`,
  §3.1 pp3–4 and §4.1 pp5–6, especially Definition3.1, Assumptions3.2/3.4,
  Proposition4.1 and Corollary4.2. PDF SHA256
  `b277315650f1ed867406601bb344e6cbbdfd1a092e32bde4602708a5ab92ccc2`.
  Its comparator cost follows the prior's own unobserved trajectory; known
  Lipschitz and telescoping bounds support future-deviation accounting. We
  establish none of those premises by testing K at its current history.
- Kadota/Sinha/Modiano (INFOCOM 2018), *Optimizing Age of Information in
  Wireless Networks with Throughput Constraints*,
  [original primary PDF](https://www.mit.edu/~modiano/papers/CV_C_204.pdf),
  §II physical pp2–3 and §III-C physical p6 (printed1849), Eqs.35–40 and
  Theorem6. The reviewer's p5 locator was off by one physical PDF page. Its
  single-hop one-transmission/slot model, fixed independent link probabilities,
  feasible per-node targets, observed throughput debt and age reset to one
  differ from moving UAVs, delayed commands, modeled history without ACK,
  finite maximum-gap outcomes and our aggregate same-state service floor.
  This is an ordinary age/throughput antecedent; neither its theorem nor its
  debt mechanism is implemented here. No verified local-library id is claimed.
- July `docs/research/designs/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`,
  lines9–23,66–89,202–224; SHA256
  `502ea67df79a0f37991a7d95d712da297ef7e7648e6a5cf25d6f90c972bb04b6`;
  and `docs/external-review/rounds/20260718_stage_c_skill_bottleneck_portfolio/41_PRO_CONVERGENT_RAW.md`,
  §1, §6 (lines163–177, “Ordinary-MARL objection”) and final boundaries; SHA256
  `467dd9ec85c0cb2358df7c90c3f18cca35bf24204646db717ec9e4b6e3cbc6cd`.
  These preserve active-adverse versus nonactivation distinctions and competent
  ordinary comparators, but do not derive this particular filter or add gates.

The independent recommendation has no material dissent. I retain its adverse
alternatives and local-constraint caveat. B05 saved-data continuity reduction,
motion×M/S composition and fixed-S2 learning remain unselected; this assignment
does not spend on any of them.

<a id="b03-complete-reading"></a>
## 2026-09-30 — B03 complete reading: fitted values actively worsen interruption control

The accepted reader exited zero at 20:50:07.476823 UTC. Observer generation29
exposed checkpoint `044af9f83013473e6eecbe46` and READY
`d060b0ddf2c70794642be49b`, wake `0a1516f4-6a98-44c1-8e2b-ac7518da671b`;
both were drained and acknowledged into generation30 on the same claim.
The complete canonical reader output is
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/uav_user_waiting/b03_value_read_a01/reading.json`,
7,320,501 bytes, SHA256
`448ecaf87e604642c19cdcbe70dc989757f5e74eedf65abc1d73c26bb2281722`.
Its local temporary collection matches the canonical hash. It reports
`VERIFIED_COMPLETE`, reproduces both fits bitwise, verifies all 512 new
episodes/131,072 native transitions and all 517 worker artifacts, and binds
the original producer SHA and summary independently of the adapter's admission
SHA. No material discrepancy is present. B04's verification condition is met;
B03's final publication/cleanup still precedes successor implementation.

**Compact-reading L0:** publish one standard-library extractor outside the
frozen B03 source glob, plus its compact run result. It reads the two pinned
complete JSON records and accepted terminal bindings only: no native/model/
optimizer calls, new hypothesis or scientific exposure. Preserve all paired
world vectors and adverse endpoints, per-user mean age/gap categories, every
raw/source identity, fit/calibration provenance, verification coverage and
measured cost; full large summaries and raw remain at their existing canonical
node paths. Verify source hashes, exact paired-value equality and complete arm/
world coverage before publication. This small deterministic postprocessing is
disposable research support, not a change to the accepted scientific worker or
reader. Existing independent scientific review receives the final reading.

The published compact endpoint record is
[`runs/uav_user_waiting/b03_value_a01/result.json`](../../../../runs/uav_user_waiting/b03_value_a01/result.json),
4,125,068 bytes, SHA256
`224d232fa40b165e7d4ba5e9f0ea611a9ab18cd789585bfdacd45eafa30ce3a7`.
It retains all 512 episode scalar records, all 320 evaluation per-user endpoint
vectors, all paired world vectors, 512 verification rows, training/source/fit
identities and all 517 artifact identities. Exact round-trip checks against the
two complete inputs passed for every retained row, per-user field, paired
statistic and artifact, as did diff checks. Extraction took0.164813 CPU seconds,
0.165264 wall seconds, peak57,296KiB, with zero scientific calls. The extractor
`experiments/candidates/uav_user_waiting/b03_result.py` preserves the pinned
input hashes; the accepted 75 scientific sources remain unchanged.

### Complete native comparison and active exposure

All values below are means over the same64 evaluation worlds. G is mean
per-user episode maximum unserved gap; F_user is the worst user's complete
episode mean age. Lower G/age/gaps are favorable; service and native J retain
their original meanings. The original141-byte recurring contract and1.436s
computation deadline are common to all arms.

| Arm | G ticks | Episode maximum gap | F_user | Served users/tick | Native J | Scheduler CPU s/episode |
|---|---:|---:|---:|---:|---:|---:|
| M | 20.194375 | 57.765625 | 13.316406 | 24.586731 | .397487 | 5.188154 |
| S | 20.632813 | 48.328125 | 10.289795 | 21.075317 | .351806 | 4.005727 |
| G0 | 23.780000 | 86.312500 | 23.950378 | 22.819336 | .379510 | 5.860538 |
| LR | 30.759063 | 104.078125 | 28.354187 | 21.191040 | .354718 | 7.569228 |
| LN | 32.097188 | 96.109375 | 27.816040 | 20.319458 | .348096 | 8.550679 |

The primary **LN−M G difference is +11.902813**, descriptive paired t95
[+10.414273,+13.391352], with **all64 worlds adverse**. The declared bootstrap95
is [+10.474984,+13.396898]. Experience use LN−G0 is +8.317188
[+6.743167,+9.891208],59 adverse/5 improving. LR−G0 is likewise adverse,
+6.979063[+5.481500,+8.476625],58 adverse/6 improving; LR−M is +10.564688,
63 adverse/1 improving. Even direct G0−M is +3.585625
[+2.542372,+4.628878],48 adverse/15 improving/1 tie. LN−LR is
+1.338125[−.171901,+2.848151]; this establishes neither neural advantage nor
equivalence. These intervals describe paired-world variation conditional on
one acquisition/initialization realization, not independent training repeats.

The native costs are not hidden by the primary mean: LN−M loses4.267273
served users/tick and .049390 J, both in all64 worlds, raises overall age by
3.241183 in all64, and adds943.171m/UAV travel in all64. Episode maximum gap
rises38.34375 ticks (60 adverse/4 improving); worst-user mean age rises14.499634
(59 adverse/5 improving). LN does raise measured quality by.034505 and reduces
transmitter-on exposure by59ticks on average; those are retained tradeoffs,
not success on waiting or an energy claim.

All G0/LR/LN eligible4,096 evaluation rounds executed. Their same-history
departures from M are2,855/3,472/3,845; no missing-maximum fallback or deadline
miss occurred. Maximum observed scheduler round wall times are
.200192/.204620/.224446s, below1.436s on this node only. LR/LN made
427,018/443,089 value calls, with132,488/30,357 clipped outputs. The
`value_pair_changes_from_visited_zero` diagnostic is266/2,713/3,641: it reranks
the cached all-visited pool, including M-generation candidates, and **is not a
complete same-state G0-policy counterfactual**. G0's nonzero diagnostic count
therefore does not imply a broken zero-value control. This is active adverse
intervention, not an untrained model, inactive choice channel or missed deadline.

S retains the constructive ordinary result. S−M reduces episode maximum gap
by9.4375[−13.755527,−5.119473] and worst-user mean age by3.026611
[−4.232096,−1.821127], with47 and52 improving worlds respectively. It loses
3.511414 served users/tick and .045680 J in **every** world, raises overall age
by.211328, adds505.268m/UAV travel, and uses less scheduler CPU. Its G contrast,
+.438438[−.404622,+1.281497], is unresolved rather than equivalent. S's extreme-
continuity/service tradeoff recurs from B02; M remains the stronger typical-user
and service reference. Neither controller is a universal replacement.

### Fitting, factual calibration and what remains unidentified

Both estimators fitted13,182 eligible causal M-suffix labels across256 training
episodes, including64 old M episodes by canonical reference. Equal-episode
weighted training RMSE is1.221189 ticks for LR and.653347 for LN. Every one of
LN's4,096 Adam updates moved parameters; the saved sampling trace covers all
rows and episodes. The complete numerical reader reproduced both final
parameter states bitwise, with one ridge solve and4,096 deterministic Adam
updates explicitly counted as verification, not scientific replication.

Fresh factual M-suffix calibration has4,032 queries/model over64 fresh worlds:

| Clipped calibration in native ticks | LR | LN |
|---|---:|---:|
| RMSE | 2.329478 | 2.254624 |
| MAE | 1.811133 | 1.700276 |
| Mean signed bias | +.232525 | +.233862 |

The actual target mean is4.757520. Both improve on zero initialization's RMSE
6.6293. The independent reviewer computed paired-world LN−LR MSE
−.3431[−1.1086,+.4223],33 improving/31 adverse; the small aggregate difference
does not establish neural forecasting superiority. More fundamentally, factual
M-suffix prediction improved while deploying the values worsened the complete
native objective. This weakens wholly absent predictive signal as an account,
but does not validate ranking synthetic selected states or identify why that
ranking failed. The lawfully available partial state, modeled history, acquired
coverage and repeatedly replanned state distribution all remain possible gaps.
An observed LN suffix is not a measured M-counterfactual target.

The declared complete checks verify131,072 native/model transitions,333,656
candidate physical pairs in the prospective selected/anchor subset,
870,107 value calculations, all training feature/target rows and all worker
artifacts. Native J maximum reconstruction error is5.55e−17; native SINR and
actor-observation maximum errors are0. The shared native radio kernel remains
part of verification, and candidate physics remains the declared bounded
subset; this is not an independent reimplementation of every physical law or
all candidate physics. Actual and modeled burden/history discrepancies remain
recorded per episode; correctness does not make model history native truth.

<a id="b03-independent-review-and-disposition"></a>
### Independent scientific reading and DM disposition

The separate-context ResearchCritic reconstructed endpoints **before** reading
the proposed B03 explanation and original Oracle advice. It checked all75
scientific source identities; independently recomputed all contrasts;
reconstructed every saved age/gap in15 hash-verified evaluation trajectories;
checked190 causal805-feature/target rows from four old, pure-M and early/late-
perturbed M sources; and inspected saved fit traces without new model queries,
fits or native trajectories. It retained these positive/adverse witnesses:

- Largest LN−M G loss, world29424010:48.02 versus23.26,46/50 users worse.
  Its87/83/81tick closed gaps have exactly correct recorded age **and running
  maximum** for those three users at every report anchor. All59 same-state
  departures from M change forecast motion/mask.
- Largest LN−G0 loss,29424047:42.70 versus17.68,42 users worse. Its111tick
  closed and94/94tick terminal gaps coexist with exact checked histories.
  At the initial common state LN accepts immediate modeled increment2.64
  versus M's2.44 because continuation predictions are18.33059 versus19.49810;
  the changed program executes. This demonstrates the mechanism, not causal
  attribution of the full later loss or an M-counterfactual suffix observation.
- Strongest LN−G0 gain,29424005:30.78 versus40.26, yet M/S achieve23.28/17.58.
  Nineteen users improve versus G0 and29 worsen; a few long-gap reductions
  drive the favorable mean. LR's sole M improvement is29424027,24.80 versus
  28.16. G0 improves on M at29424046,18.02 versus25.48, while S reaches17.40.
  These exceptions remain evidence, without a prospectively known selector.

After receiving the full reading, the reviewer independently verified local
and canonical hashes, accepted identities/exit, the unchanged75 scientific
sources, all512 episode and517 artifact identities, bitwise fit replay and
calibration arithmetic. Its final recommendation is: **retain M and conditional
S; end investment in unchanged G0/LR/LN. No further B03 observation is needed.
MATERIAL_DISSENT: no.** It explicitly distinguishes useful factual prediction
from useful state-dependent action ranking and preserves selected-state
extrapolation as uncertainty, not established cause. The final addendum made
no new model queries, optimizer replay or raw-witness checks.

I accept that diagnosis. Task opportunity persists in S's recurring extreme
continuity capability and tradeoff. This finite representation/training/search
package supplies no G improvement; fitting and factual predictive signal are
real but did not translate into useful deployment. No general unlearnability,
information ceiling, missing-ACK diagnosis or isolated optimizer/feature cause
follows. Keeping M among candidates is not a policy-improvement guarantee under
approximate ranking. Stop this fixed recipe and retain all adverse evidence;
do not purchase another fit, horizon, feature or acquisition repair. The parent
learning question remains open. Root's **explicitly changed**, independently
reviewed M/S/U/K question above is the selected next investment, after this
batch's publication and cleanup, not a renamed G-value rescue.

### Complete cost and retained evidence

Scientific exposure is512 new H256 episodes/131,072 steps and2 fits, plus the
40-step correctness fixture. Of512 episodes,192 acquire data and320 evaluate
fixed policies with zero evaluation parameter updates. Reused16,384 old steps
are not new exposure. The producer performs one ridge solve and4,096 Adam
updates/1,048,576 presentations; the reader repeats those operations for
numerical verification, adds327,680 C calls,870,107 value replays,8,064 factual
calibration queries and26,364 final-training predictions, with zero new native
steps or independent scientific fits. Producer requests total8,564,736 and
delivered state reductions17,137,344.

Producer lifetime CPU is3,300.383555s, reader lifetime CPU3,174.845006s:
**6,475.228561s /1.798675 CPU-hours** together. Wall times are3,251.435954s and
3,175.478258s; peak RSS939,196KiB and807,980KiB. The separately paid fixture
used4.469529 CPU seconds and4.67145 wall seconds. The provisional critic's
bounded remote inspection used6.55 CPU seconds, with local support, engineering
and review not comprehensively metered; they are not zero. The complete compact
extraction cost above is additional. Across B01–B03 this direction has262,256
new result steps,240 correctness steps and2 scientific fits; previously known
B01/B02 CPU4,475.374087s plus this worker/reader is10,950.602648s before the
separately recorded fixture/support costs. No failed or refused work is erased.

The worker's517 unique retained artifacts occupy916,234,958 logical bytes,
besides the full summary/reader/config/native receipts. Native trajectories,
training data, both fitted models and fit traces remain at the canonical node
paths in the compact manifest; the64 old M trajectories remain at their original
canonical paths. Full large JSON copies used for local interpretation will be
deleted only after compact publication and final live-consumer checks. Useful
frozen source, tests and the small argument adapter stay published. Managed
source snapshots, redundant progress data and unused direction scratch are
the cleanup targets; no archive or duplicate backup is a prerequisite.

<a id="b03-final-cleanup"></a>
### B03 publication and cleanup

Complete evidence, independent interpretation and the conditional successor's
full original advice were published to main at
`fd20615f79a09648220fc2bcc27aa5eee09f76b7`. The accepted operations, complete
reader and independent addendum were terminal before cleanup; generation30
observation was stopped with work unchanged. There is no unread B03 result,
pending model query, review, Pro request or selected B03 continuation. Root's
retained `wsl_4070` deadline window is for the separately selected B04 study.

The exact-target collector first refused normal process inspection because
PID660's `/proc/660/cwd` returned permission denied. Its supported
`--sudo-process-scan` performed the read-only scan; fresh preview then verified
terminal accepted identities, no live source consumers, clean source and
durable Git reachability. The refused first-reader source was identified as the
clean unclaimed snapshot made at19:49 with original SHAa045bc9b4, matching the
recorded outer refusal time/source; explicit `--unclaimed-source` was used for
that target. No claim, manifest or evidence directory was removed to obtain
eligibility. Subsequent exact-target apply deleted all four snapshots:

| Deleted path under `/home/wu/projects/HMASD/.git/hmasd-launch-sources/` | Allocated bytes reclaimed |
|---|---:|
| `44a238c7a07d45b1b72f03493a2d26a5` | 811,012,096 |
| `d913f7219d8b43c6baa5dd66a0f8d5c4` | 811,024,384 |
| `f572dbb398bd45f1acb9ef999e1f9531` | 811,024,384 |
| `548aeb29c8a14a93b942c992862cdd31` | 811,745,280 |

Also deleted canonical-node redundant
`runs/uav_user_waiting/b03_value_read_a01/reading-progress.json` (4,341,760
allocated bytes), after rechecking the complete reading's pinned hash and
zero process exit. Local `temp/directions/uav_user_waiting/b03/` contained only
`worker-summary.json`, `full-reading.json`, `correctness-wait.json`,
`worker-wait.json`, and `reader-wait.json`; those five files and the empty
directory were deleted (17,952,768 allocated bytes). All exact targets are
absent. **Net target disk reduction is3,267,100,672 allocated bytes**:
3,249,147,904 on the execution node and17,952,768 locally. This measures actual
working-tree/scratch deletion, not hypothetical Git-object or filesystem-wide
reclamation. No backup, tarball or replacement evidence tree was created.

No cleanup target or tool blocker remains. Canonical raw, models/training/fit
traces, full summary and complete reading remain the one necessary evidence
copy; original64 M traces remain by reference. Useful frozen implementation,
tests, argument adapter and compact extractor stay published. B03 is fully
read, diagnosed, published and cleaned; the changed ordinary M/S/U/K question
may now proceed under Root's existing allocation.

<a id="b04-selected-l0"></a>
## 2026-09-30 — B04 fixed ordinary service-floor comparison and L0

B03 closure is published at `5861a1b1936115c875120ad8c9bf66b1cb099394`.
The completed result critic and original Root-assigned selection advice above
cover the present question; there is no unresolved material objection or need
for another routine selection round. Current published RESEARCH topic2 carries
B03's predictive-signal/control distinction and recurring S tradeoff; topic8's
information/action/finite-controller distinction limits the interpretation of
a local constraint. Those premises guide this fixed comparison. No new claim
of learning, novelty or native service preservation is being assumed.

**Actual host and decision exposure.** Reuse the complete N5/U50/H256 native
factory, static uniform worlds, original C motion proposals, componentwise
clipped motion, 400-byte map and B02 post-C navigation protocol. At report
ticks0,4,…,252 the five C calls, lawful report encoding/decoding, history
settlement, two-tick old-command prefix, candidate generation/ranking and
command encoding are inside the existing1.436s computation allowance;141
recurring bytes account for the .564s transmission component. C proposals at
tick0 supply the original startup. Delivery is at t+2. Only member
(t/4 mod5)'s27 command alternatives and the31 nonempty team masks are searched;
other members keep their C proposals. No additional ACK, truth, actor input,
future C, fitted value, global action enumeration or native counterfactual is
introduced. Cached predictions are legal modeled history, not actual contacts.

The candidate block contains min(4,256−t−2) delivered transitions. At the last
report t252 it therefore contains the **two** scored transitions254/255;
the252/253 old-command prefix is shared and is excluded from both candidate
service and S ranking. No beyond-terminal reward/contact padding is allowed.
The ordinary S key is the existing lexicographic tuple
(-sum delivered squared per-user ages, mean native modeled J, mean served,
proposal-command retention, active-mask count, -mask id, -command id).
Initial/reset contacts are unscored; native age starts0 and becomes1 on the
first unserved transition. Initial/terminal gaps retain censoring, and an
always-unserved user has a256tick gap counted in both boundary groups.

**Four fixed programs and matched construction.** M and S retain their exact
B02 programs. Full M runs the unchanged O and W two-order searches (232
pre-cache requests), choosing the O/W winners by W's existing key. S runs its
unchanged116-request two-order search. U and K both run O, W, then S without
modifying any generator, with one common stage/cache/history. The union is all
distinct pairs actually visited by those348 requests, in first-visit order;
it includes intermediate pairs and the final M and S winners. U chooses the
maximum existing S key over this entire union. K uses the **same completed
union** and same S key, but admits only candidates with modeled delivered-block
mean served users >= the same-state M winner's. Mean service is the total
number of assigned user-ticks divided by that common block length; comparing
integer totals is exactly equivalent (no epsilon, relaxed floor or fitted
threshold). This is contact assignment, not mere SINR eligibility. M is always
feasible. Full tuple ties preserve first-visit order, though mask/command IDs
already provide a total order. The floor never affects search generation.

The whole program must finish on time. A partial union, missing history or
whole-round timeout holds the old command and mask under the original fallback;
neither M nor a partial winner is a new rescue. The same source construction
does not require different deployed trajectories to visit identical pools.
Record every requested/evaluated pair, O/W/S search result, M/S/U/K same-state
pair, integer service total/floor, feasible mask, chosen/returned program,
deadline and meaningful command/mask/forecast changes. Separately count complete
calculation, timely delivery and actual changed execution. There is no changed-
choice minimum, pilot-based gate or post-result exposure threshold.

**Fixed addresses and stopping.** Evaluation uses exactly64 fresh world seeds
29426000…29426063, all four programs in eight alternating cyclic/reverse arm
orders (eight worlds per order), H256. There are256 complete new episodes,
65,536 new result steps,0 fits and0 optimizer updates. Bootstrap diagnostic
seed29426998 with10,000 paired resamples is fixed; paired-world t95 and all
individual world vectors remain primary descriptive summaries, with no claim
of multiplicity-adjusted confirmation. One necessary native correctness fixture
uses seed29426999, H8×M/S/U/K (four episodes/32 steps) and no final world. No
complete quality pilot, sweep, adaptive extension or duplicate retry is
selected. Preserve partial/failure evidence if interrupted; do not quietly
restart the scientific batch.

The primary joint reading is K−M actual mean service (constructive sign >=0),
episode maximum gap (<0) and worst-user mean age (<0). These signs express the
conjecture, not confirmed noninferiority or a chosen adoption tolerance. Retain
G/J/overall age/quality/path, complete censored gap/age tails, transmitter use,
all adverse worlds, actual selection exposure and full cost. K−U isolates the
local filter at matched generation; U−S measures expanded ordinary search.
K's intermediate prediction is modeled service floor satisfaction on every
complete selected decision; its native consequence is the joint pattern above.
Exact intermediate satisfaction with native losses weakens this local-floor
package. Sparse changes do not refute the wider frontier, and successful U is a
useful ordinary contribution even if K adds no value. Declining another repair
is not an empirical rejection of broader learning or control.

**Complete cost and reader.** The worker has4,276,224 pre-cache candidate
requests, at most16,971,264 delivered-state reductions,32,768 prefix transitions
and81,920 current-C calls, before cache savings; there are no future-C or
learned-value calls. Expected worker+bounded-reader0.9–1.3 CPU-hours and3–6
engineering hours remain estimates, not profiled guarantees. The reader checks
all256 raw/source hashes, all65,536 native endpoints, C observations/proposals,
lawful executed histories, native age/gap metrics, all saved candidate costs/
keys, exact O/W/S request paths and U/K pool/filter/selection arithmetic. It
recomputes physical radio for every selected program and completed search
winner plus all visited pairs at report ticks0/60/124/248, using the same native
radio kernel. All other stored contact-to-score arithmetic is checked without
repurchasing all candidate physics. Two existing independent C passes imply
163,840 reader C calls; actual physical/history work and reader CPU/RSS are
reported separately. Bounded fixture runs the same checks at H8. All actual
model/native history discrepancies remain adverse evidence, not verifier errors
or reasons to supply truth to a policy. Output/native-status bindings remain
distinct for the worker and separately admitted reader.

**Implementation scope and ownership.** New code and tests live only in this
direction's `b04/` directories. Reuse the B02 protocol, finite-search stage,
history and pickle-free record storage; keep frozen prior files unchanged.
Retain byte identities of the ordinary dependency set in the B04 config along
with all new modules and the exact published launch SHA. The DM owns this
notebook, worker/reader/config/publication and fixtures. A bounded Implementer
may own only `b04/scheduler.py` and its corresponding scheduler tests: add the
whole-union U/K behavior and record fields while M/S delegate unchanged to
the frozen scheduler. No Git index, shared files, notebook, science choice,
native launch or new child belongs to that helper. DM review/acceptance and an
independent engineering review cover control, delayed delivery, immutable
generator paths, failure records, numerical comparisons, reader and admission.
Mock/analytical correctness tests add no native panel; the32-step fixture is
separately admitted only after exact inputs are published. Required outputs
remain one canonical node copy plus compact Git evidence. Source publication,
fresh actual-node admission, detached observation, full reading, independent
result diagnosis and cleanup complete this one selected chain.


<a id="b04-implementation-review"></a>
## 2026-09-30 — B04 implementation accepted; exact native fixture next

The bounded Implementer authored only the new scheduler and scheduler tests.
DM inspection accepted unchanged M/S delegation, common unmodified O/W/S paths,
integer assigned-user-tick filtering after generation, the final two-tick block,
and retained partial/late records with old-action fallback. The DM authored the
collector, metrics, fixed configuration, reader and admitted entries. The B04
collector and storage functions are verbatim B02, with the new scheduler/arm and
metric bindings; all 62 inherited scientific dependency files remain unchanged.
The complete focused analytical/mock suite passed42 checks in3.84s, including
reader rejection of altered floors, feasibility, union order, winners, request
paths and costs. These tests use no native result world, native step or fit.
CLI/AST checks also passed.

A separate registered Engineering Reviewer inspected all eight new modules,
both test modules and their actual frozen stage/storage/reader/launcher consumers.
It found no material open failure and independently reran42 tests in3.80s. The
reviewed ten-file aggregate SHA256 (sorted path, NUL, binary per-file SHA256) is
`03bfadebce9a83413456398874e15564222136fe7dee4de6524059119f605e8b`.
The DM accepts this implementation within the published L0. This covers
engineering semantics, not a scientific outcome. Actual native integration,
source-layout binding and deadline evidence remain for the fixed32-step fixture.

The separately admitted reader uses the canonical `--generic-summary` artifact
path with worker-summary digest and worker source SHA, while retaining its own
admission SHA. This preserves the supported external-input contract established
by the completed B03 reader. It reconstructs every saved native/C/history record,
all contact-to-cost/key arithmetic, complete and interrupted search paths, and
U/K pool/filter/selection. Physical recomputation covers all selected same-state
M/S/U/K programs and search winners, plus all visited pairs at0/60/124/248.
Current-C reconstruction, candidate physics, prefix and executed-history counts
are reported separately from the producer's new native exposure. No additional
pilot, fit, threshold, arm or scientific stopping change was introduced.

Source publication below precedes the single selected native fixture at
seed29426999,H8×M/S/U/K=32 steps on the retained `wsl_4070` window. A successful
fixture is followed by the fixed64 fresh worlds and complete saved-data reading;
there is no per-run Root acknowledgment or adaptive quality gate.


<a id="b04-native-start"></a>
### B04 native fixture read; fixed producer accepted

The exact scientific inputs were committed and published at
`dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4`. Native fixture
[`b04_correctness_a01`](../../../../runs/uav_user_waiting/b04_correctness_a01/launch-manifest.json)
was accepted at21:27:50.784093UTC and exited zero at21:27:55.083957UTC.
Its complete summary SHA256 is
`74d34501f613201f8fa2c973e1f168c823debc64b46c076b5a46e379c3e0d186`;
the collected summary and four admission/exit files match canonical node hashes.
Exactly four H8 episodes/32 native steps completed, with zero fits/optimizer
updates, eight complete and timely calculations and zero deadline misses.
The reader verified all32 native and modeled transitions, all observations,
terminal clipping, candidate cost/path/pool/floor arithmetic and the declared
physical subset. Maximum reward reconstruction error was5.55e−17; radio and
observation error were zero. Process user/system time2.997491/.302938s,
wall3.970811s and lifetime peak RSS412,524KiB. This is integration evidence;
it does not estimate treatment quality. Raw fixture arrays remain once at the
manifest's canonical node output.

The unchanged-source full producer
[`b04_service_floor_a01`](../../../../runs/uav_user_waiting/b04_service_floor_a01/launch-manifest.json)
was accepted at21:30:06.167218UTC under fresh actual-node admission.
Its operation claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/1686d37b2d92e283bc678ede5bca7d429e10461288381dab32dec778615df6cb.json`.
Generation34 of this session's deterministic observer adopted matching live
supervisor/runner identities and a consistent accepted claim at21:30:20UTC.
The prior stopped observer was drained/rearmed before adding B04; the initial
refusal to add to stopped state caused no repeat or change to either launch.
Fixture terminal events were drained and consumed. Queue delivery again returned
native-child rejection−32600, so the child remains active through deterministic
observation, same-handle checkpoints and the separately admitted final reader.
Root's reserved timed-node window continues through that reading. The fixed
256 episodes/65,536 steps/zero fits and complete/adverse reading remain in force.


### Compact B04 evidence extraction prepared without changing accepted inputs

A JSON-only publication extractor, `experiments/candidates/uav_user_waiting/b04_result.py`,
lives outside the frozen B04 dependency glob. It binds the complete worker and
reader JSON by digest, retains all256 world scalars, all six paired contrasts,
per-user age/gap vectors and raw artifact identities, and summarizes per-slot
verification into per-world counts/extrema with the complete slots retained at
the canonical node. It performs no policy/radio/native/optimizer query.
An independent engineering pass found a P2 risk: equal worker/reader source SHAs
alone would allow the wrong same-source terminal status to name the reader's
canonical path. Before publication, each status was bound to its own pinned
record's admission source/direction and parent/child PIDs, plus the configured
node. Five focused regression checks accept the matched record and reject
same-source worker, supervisor, node or direction substitutions. The DM and
Reviewer independently observed five passes; the Reviewer resolved P2 with no
material remaining finding. Actual extraction awaits the complete producer and
reader. No accepted B04 input, scientific endpoint or live process changed.


### B04 producer complete; final reconstruction in progress

The fixed producer exited zero at21:52:42.074888UTC. Its canonical full summary
is5,139,433 bytes with SHA256
`49754e61f38009681d5a842d320a1878bdd260518300a5391cc3c8678db47c47`.
Collection verified this digest plus the configuration and exit witness. It
reports exactly256 complete episodes/65,536 native steps/zero fits/zero optimizer
updates and zero deadline misses. Worker wall1355.281210s, lifetime process CPU
1354.406528s and peak RSS569,076KiB. The observer's consistent terminal fact is
retained as `b04_service_floor_a01/native-status.json`; generation34's READY
was consumed before the next observation was armed.

The separately admitted unchanged-source reader
[`b04_service_floor_read_a01`](../../../../runs/uav_user_waiting/b04_service_floor_read_a01/launch-manifest.json)
was accepted at21:55:08.240108UTC, binding that exact canonical summary digest
and worker source. Its operation claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/f6c6cd4a5ab546ae9b7f4785d655248358f5b6ae05e72215955b797b90451bfa.json`.
Generation36 adopted the same consistent live native identities at21:56:12UTC.
The child remains active through this selected reading; no duplicate or retry
has been launched. The named ResearchCritic is independently reconstructing the
complete producer and original supporting/adverse advice while the verifier
runs. Producer completion is not yet a fully verified scientific conclusion.


<a id="b04-complete-reading"></a>
## 2026-09-30 — B04 complete: useful expanded search, local floor does not establish trajectory preservation

**Disposition.** Retain M's service/typical-interruption reference, U's measured
S-relative capability, and S's cheaper operating point. K misses the frozen joint
sign on native service; its near-zero mixed contrast and favourable tail point
estimates remain evidence, not equivalence or a demonstrated service-preserving
upgrade. Close this fixed comparison without an automatic K extension, repair,
new fit or confirmation. The broader service/continuity and learning questions
remain open. No new out-of-question study is selected here.

The exact worker and reader source is
`dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4`. The separately admitted reader
exited zero at22:11:37.370681UTC with **VERIFIED_COMPLETE**. Its complete
11,309,402-byte reading has SHA256
`69787803a4de84555c534d9b7f21a23c290c7d4446bc874a2da6e49237289513`.
It binds the worker's full summary digest
`49754e61f38009681d5a842d320a1878bdd260518300a5391cc3c8678db47c47`.
Both terminal statuses have consistent accepted claims and distinct matched
supervisor/runner identities. Generation36's READY event was consumed; generation37
was then stopped with no pending event. Native-child queue rejection caused no
repeat launch. Root received the actual timed-node release after both processes
and the full verification finished; no further heavy or native work is selected.

[`result.json`](../../../../runs/uav_user_waiting/b04_service_floor_a01/result.json)
is the compact Git reading:2,509,981 bytes, SHA256
`ccd52d06fe48c7e3f5315b834cb702e1b22b826df25af68a6e2eeb7e3a09707a`.
The published, independently reviewed extractor binds both complete JSONs and
their own native terminal identities. All256 scalar rows, six paired contrasts
with every signed world, declared bootstrap, per-user age/gap/censoring vectors,
raw hashes, source identities and verification summaries agree with the pinned
inputs. The512 omitted aggregate all/closed-gap summaries reconstruct exactly
from retained per-user counts/totals/maxima; complete slot records and satisfied-
window histograms remain in the canonical full JSONs. No outcome was dropped
because of its sign. Extraction used0.138204 CPU seconds and0.138204 wall seconds,
with zero policy/radio/native/optimizer queries; local support is not included.

### Native outcomes under the fixed rule

All64 new common worlds29426000…29426063 completed all four H256 programs in
the fixed balanced orders:256 episodes,65,536 steps,0 fits/optimizer updates.
G is mean per-user maximum gap; F_user is the worst user's whole-episode mean
age. These are different from the episode maximum over every user's gap.

| Arm | Served users/tick | Episode maximum gap | F_user | G | Native J | Overall age A | Scheduler CPU s/episode |
|---|---:|---:|---:|---:|---:|---:|---:|
| M |24.736206|55.078125|12.982300|19.534375|.399790|3.130050|5.031795|
| S |21.180481|51.406250|10.962158|20.901563|.353223|3.517103|3.870323|
| U |21.666870|46.828125|9.362488|19.797188|.358628|3.273011|5.223771|
| K |24.699707|52.515625|11.963806|19.786875|.399501|3.183102|5.330757|

The declared paired-world t95 intervals describe these fixed policies over64
worlds; they are not training replication, simultaneous confirmation or an
adoption tolerance.

| Contrast | Service difference [t95] | Episode maximum-gap difference [t95] | F_user difference [t95] |
|---|---|---|---|
| K−M |−.036499 [−.243719,+.170721]|−2.562500 [−6.365632,+1.240632]|−1.018494 [−2.052410,+.015423]|
| U−S |+.486389 [+.271307,+.701471]|−4.578125 [−9.381291,+.225041]|−1.599670 [−2.788147,−.411194]|
| K−U |+3.032837 [+2.792975,+3.272698]|+5.687500 [+1.648206,+9.726794]|+2.601318 [+1.630085,+3.572552]|
| U−M |−3.069336 [−3.331439,−2.807233]|−8.250000 [−12.437878,−4.062122]|−3.619812 [−4.640074,−2.599550]|
| S−M |−3.555725 [−3.818581,−3.292869]|−3.671875 [−8.565182,+1.221432]|−2.020142 [−3.287653,−.752630]|

**K primary.** The mean service sign is negative, while both extreme-continuity
point estimates are favourable; all three t95 intervals cross zero. Service
falls in36 worlds and rises in28. Maximum gap falls in31, rises in21 and ties
in12; F_user falls in37 and rises in27. Eight worlds meet all three constructive
signs. K−M G+.252500, J−.000289, A+.053052, quality+.000740 and
travel+2.023m/UAV all have intervals crossing zero. K adds.298963 scheduler
CPU seconds/episode. The predeclared10,000 paired bootstraps at29426998 give
F_user percentile95[−2.014221,−.034966], unlike its t95 interval; this diagnostic
does not replace the frozen reading or rescue the failed joint mean sign.
This is not B03's uniformly adverse learned-value result. Neither no effect,
noninferiority nor a small positive population benefit is established.

**Useful U result with explicit costs.** U−S improves service in47 worlds and
loses in17; F_user improves in39 and worsens in25. It also reduces G1.104375
[−1.945315,−.263435], A.244092 and age-p95 1.031250, and increases
J.005405[+.002425,+.008385]. Its episode maximum-gap contrast remains uncertain.
The added search costs1.353448 scheduler CPU seconds/episode in every world;
quality falls.004682[−.007604,−.001759] and transmitter exposure rises16.8125
UAV-ticks/episode. Travel+11.705m/UAV has an interval crossing zero. U therefore
does not dominate the full benefit/cost vector. Against M, U loses service and
J in all64 worlds, adds544.900m/UAV travel and increases A.142961, despite its
clearer extreme-tail gains. Retain a useful operating option, not a service-
preserving upgrade or global optimum. S retains its lower compute/stronger
quality operating point, and its recurring service/F_user tradeoff; the
maximum-gap contrast versus M is less precise on this fresh panel.

K−U restores3.032837 served users/tick and J.040874 in all64 worlds, but gives
back5.6875 maximum-gap ticks and2.601318 F_user ticks on average. It shortens
travel542.877m/UAV, lowers quality.005287 and adds82 transmitter UAV-ticks.
This measures this floor's complete deployed consequence at matched generation;
it does not prove an unavoidable service/continuity frontier.

### Intermediate prediction, lawful history and adverse trajectories

All16,384 rounds were complete and timely with zero deadline misses. Executed
command/mask/forecast changes total16,282/16,142/16,384. Each arm completes4,096
rounds. U/K use the same source construction at a given history; their deployed
trajectories need not share literal pools. Along K histories the completed floor
changes U's selected pair2,211 times, yet K differs from same-state M only289
times(7.06%;1–10 per world). U differs from same-state S521 times along U histories.
Sparse K exposure is real, not a new minimum gate or a nonactivation claim.

K's exact modeled floor holds at all4,096 decisions, satisfying the intermediate
prediction. Its modeled selected service exceeds same-state modeled M by1,034
assigned user-ticks; actual selected-block service minus its model totals−88.
Thus K delivers946 user-ticks above its accumulated local modeled references,
while those references total1,544 fewer user-ticks than M's actual trajectory:
full K−M service is−598 user-ticks, with common startup. **This is an accounting
identity, not a causal decomposition.** M's unexecuted references at K states
are different objects from M's deployed trajectory. Prediction error on selected
blocks alone does not explain the episode loss; errors in unexecuted references
and future state/opportunity consequences remain unresolved.181 K blocks fall
below their modeled M floor, not an executed counterfactual M block. Local
modeled feasibility supplies no native trajectory guarantee.

The independent critic hash-checked12 complete raw traces, reconstructing
contacts, ages and censored gaps. These retain both the joint-positive case and
strong adverse cases. Filenames are exact under the canonical worker's `raw/`;
full hashes are in `result.json`. Each native outcome pair lists the first arm
then its comparator. First-difference comparisons use actual delivered blocks.

| Exact raw pair | First report→execution; block service | Full service | Maximum gap | F_user |
|---|---|---|---|---|
| K_29426061.npz / M_29426061.npz |28→30;94/94|23.65625/22.97656|33/87|7.27734/22.06250|
| K_29426006.npz / M_29426006.npz |88→90;80/77|23.34375/24.98438|50/49|9.63281/11.43750|
| K_29426034.npz / M_29426034.npz |8→10;110/109|25.08984/25.24609|75/45|12.68750/13.67188|
| K_29426030.npz / M_29426030.npz |108→110;116/102|28.00781/28.26172|57/45|17.13281/11.23047|
| U_29426030.npz / S_29426030.npz |28→30;105/79|22.01953/24.28906|70/33|10.78516/8.52734|
| U_29426001.npz / S_29426001.npz |4→6;93/100|20.42578/19.46484|65/117|10.34375/31.14453|

K06/K34 first-difference modeled service and squared-age costs equal the actual
first-block values, yet the episodes have adverse service or maximum-gap effects.
K34 also has total modeled surplus+53 and net selected-model residual0, while
losing episode service and adding30 maximum-gap ticks. Conversely U01 initially
sacrifices service and later improves episode service and tails. These witnesses
refute a simple attribution to initial comparison error without identifying a
unique later mediator. K61 preserves genuine joint-positive evidence. M61 user47's
87-tick gap[62,149), K34's75/74/70-tick gaps and S01 user4's117-tick gap[96,213)
are closed gaps; these adverse tails do not disappear under boundary censoring.

The full reader checks all256 raw files/358,763,054 logical bytes,65,536 native
and modeled transitions, all C/observation/history/age metrics, every saved
contact-to-cost/key calculation, exact O/W/S paths and U/K pool/filter/choice
arithmetic. Physical reconstruction covers every selected same-state program
and search winner plus every visited pair at0/60/124/248:154,478 candidate pairs,
617,014 candidate transitions and32,768 prefix transitions. It uses the shared
native radio kernel and the existing independent observation reader. Native
SINR/observation errors are0; maximum J error is5.55e−17. This is the declared
bounded physical reconstruction, not exhaustive independent physics replay.

Legal model history need not equal truth: M/S/U/K respectively have3,745/3,651/
3,572/3,711 of4,096 report anchors with some cumulative-burden discrepancy;
maximum absolute discrepancies are943/870/616/532. They are retained model
limitations, not reconstruction failures, an identified cause of K's loss or
permission for an ACK/truth repair. Full anchor/slot details remain canonical.

<a id="b04-independent-review-and-disposition"></a>
### Independent scientific diagnosis and DM response

The registered ResearchCritic worked in its original separate context without
inherited DM/Root conversation. It reconstructed the actual design and complete
outcomes before reading the original Oracle answer and DM response; it checked
all70 source identities and12 positive/adverse raw traces. It initially conditioned
its recommendation on the accepted full reader. After reading the entire pinned
reading and terminal bindings, it removed that condition: all256 identities and
the full paired object agree, with no consequential reconstruction discrepancy.
Engineering review remains a separate, already completed judgment.

The critic's substantive recommendation is retained: **retain M and the costed U
option, preserve S's cheaper operating point and K's near-M evidence, and close
the fixed experiment without automatic K extension or repair.** It rejects a
native-preservation claim, not the possibility of a small service-preserving
population improvement. More unchanged worlds would principally improve
population precision, not identify the local-floor failure mechanism; a future
prospectively specified service/tail valuation could make that investment useful.
No such tolerance or confirmation claim was selected here. **MATERIAL_DISSENT:no.**

The DM accepts that diagnosis and investment disposition. Task opportunity is
supported by U's improvement over ordinary S and its service/continuity tradeoff
against M. Representation supports a lawful local model but not equality to
native trajectories or their counterfactual opportunity. Learnability is untouched
by this zero-fit study. Complete-package value is conditional on service, quality,
travel and compute preferences; neither K nor U is adopted as a universal M
replacement. The changed explanation is specific: satisfying this modeled floor
and increasing modeled local service is insufficient to establish complete native
service preservation. Initial prediction error alone is not a sufficient account.
K's small mixed service contrast leaves precision unresolved, unlike the active
uniform losses in B03; this distinction survives the stop decision.

No automatic new debt, weight, horizon, ACK, fit or expanded panel is selected.
Retain the useful ordinary source/tests and complete positive/adverse evidence.
The wider parent question is open; a re-entry requires a newly selected substantive
prediction or declared service/tail valuation with competent same-resource
comparators and a prospective complete cost. Root owns any new cross-question
allocation. There is no missing adviser, owner ACK or fabricated producer on which
this completed reading depends.

### Complete cost and evidence retention

The worker used4,276,224 pre-cache requests,1,975,375 distinct evaluated plans,
7,841,314 delivered-state reductions,1,755,648 geometry snapshots,32,768 prefix
transitions and81,920 current-C calls. It made no future-C/value query or fit.
Scheduler CPU totals1,245.225374s, nested within worker lifetime CPU1,354.406528s;
reader lifetime CPU988.464463s makes **2,342.870991s/.650797CPUh** in total,
below the .9–1.3h planning estimate. Wall1355.281210/987.461429s and peak
RSS569,076/552,760KiB are worker/reader separately, not summed peaks. Reader
163,840 C reconstructions and the physical counts above add zero new native
steps/fits. The separate four-episode/32-step fixture cost3.300429 CPU seconds.
The critic's bounded remote raw/source inspection cost.72user+.05system CPU
seconds,.79wall,peak82,828KiB; its other saved-JSON/source/SSH work, implementation,
review, observation and collection remain incompletely metered, not zero.

Across B01–B04 this direction has327,792 new result steps,272 correctness steps
and2 scientific fits, preserving B02's failed-prefix exposure. Known worker/full-
reader CPU is13,293.473639s/3.692632h, before separately recorded fixture/support
costs. Result-level reconstruction calls are not independent training replicates.
The B04 worker's256 raw artifacts occupy358,763,054 logical bytes and remain once
at their canonical node paths, alongside complete summaries/readings and receipts.
The32-step fixture raw evidence also remains canonical. Useful source/tests and
compact readings are published; no full-tree copy, tar or duplicate backup is a
cleanup condition. Terminal snapshots, redundant progress data and local copies
are the final cleanup targets after publication and fresh live-consumer checks.


<a id="b04-final-cleanup"></a>
### B04 publication, cleanup and reserve standing

Complete compact evidence, native terminal records and independent scientific
interpretation were committed and published on main at
`5d6353ff59da4b2b5c796629cacb4820ab0bb986` before deleting any final retained-input
copy. Worker/reader/fixture processes and independent review were terminal;
observer generation37 was stopped with no pending event. No B04 native/model
query, result reader, Pro request or selected continuation remains. The actual
`wsl_4070` timed window was released to Root after complete verification.

The exact-target snapshot collector previewed and then freshly rechecked all
three accepted snapshots: terminal identities, no live source consumers, clean
source and durable Git reachability passed. It used the supported read-only
`--sudo-process-scan` for the already known node `/proc` permission restriction.
No claim, manifest or unique result was removed to create eligibility. Apply
removed, and subsequent inspection confirmed absent, these exact paths under
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/`:

- `b01a6dda2cfe44159ab182d37d48213f` — correctness fixture source.
- `be056e4355fc4310bf8e7746ec3b002c` — fixed worker source.
- `fb6ae62573bd4141b21580b90e26f058` — complete reader source.

Their allocated sizes were **not captured before deletion**, and this version
of the collector reports removal/eligibility without byte counts. Therefore
no fabricated byte credit is assigned to these three snapshots; their exact
reclaimed-byte total is unmetered. This is a measurement-record limitation,
not a cleanup tool blocker or remaining directory.

The full worker summary and complete reader digests were rechecked at the
canonical node. The redundant reader progress contained the same256 rows and
worker binding as the final reading. `fuser` found no live consumer before
deleting that progress file and the local temporary inputs/requests. Exact
allocated-byte measurements (`st_blocks×512`, including the local directory)
before deletion and verified zero after deletion are:

| Deleted target | Before bytes | After bytes | Measured net reduction |
|---|---:|---:|---:|
| node `runs/uav_user_waiting/b04_service_floor_read_a01/reading-progress.json` |10,403,840|0|10,403,840|
| local `temp/directions/uav_user_waiting/b04/` |16,470,016|0|16,470,016|
| ten local compiled-bytecode directories listed below |602,112|0|602,112|

The local directory held exactly `worker-summary.json`, `reader-reading.json`,
`fixture-observer-request.json`, `worker-observer-request.json`, and
`reader-observer-request.json`; all five files and the directory are gone.
The44 untracked `.pyc` files and their ten `__pycache__` directories were also
checked for live consumers, deleted and verified absent. Exact directories are
`experiments/candidates/uav_user_waiting/{,b01/,b02/,b03/,b03_reader/,b04/}__pycache__`
and `tests/experiments/candidates/uav_user_waiting/{,b03/,b03_reader/,b04/}__pycache__`;
no tracked source or test file was removed.
**Measured target reclamation is27,475,968 allocated bytes; total actual
reclamation is at least that amount**, with the three deleted source snapshots'
portion unmetered. No cleanup target or tool blocker remains. One canonical
copy of complete raw/summary/reader/fixture evidence and all accepted-operation
receipts is retained; compact Git data, useful source/tests and all adverse
outcomes remain published. No full-tree backup, tar or retention chain was made.

The direction moves to reserve with the bounded result and re-entry condition
in the preceding disposition. The directly affected shared background records
U's useful conditional capability and the local-floor/trajectory distinction;
it does not turn them into adoption, learning or a general impossibility claim.
The substantive prospective B04 selection is retained in the dated research
archive. No new study, automatic retry or owner/adviser dependency is created.

<a id="post-b04-source-assessment"></a>
## 2026-09-30 — source-only next-use assessment after B04

Root assigned a bounded source-only next-allocation assessment after reading
the complete B04 result and original independent diagnosis. The question is
whether a substantive remaining service/continuity capability or materially
different use merits development, compared with stopping. Root assigned the
existing independent Oracle `/root/oracle_next_capability` to innovation and
challenge; this DM owns interface feasibility and the complete prospective
bill. Parent/N8 design and fleet-count development are separately owned and
excluded. **The direction remains reserve; no next result study, code,
prototype, model/controller/native query, pilot, acquisition or fit is
selected.** B04 operations and cleanup remain closed.

The relevant published background is
[RESEARCH topic2](../../RESEARCH.md) at
`d02e5029f4c9687e12a5d03746527aee2d979ae5`, including B01–B04 and the prior
service-age result. Its concrete effect here is to retain M's service/typical
continuity, U's useful costed expansion, cheaper S and all contrary outcomes;
to reject an automatic local-floor, horizon, ACK or learned-value repair; and
to examine a different decision right only with a competent ordinary rule
under the same added information. Prior fitted factual predictions do not
justify another fitted selector. A new objective weight chosen after these
outcomes would not establish preservation or complete-package value.

### Source facts and the remaining decision right

The inspected source is unchanged from B04's frozen
`dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4`. Load-bearing locations are
`envs/pettingzoo/uav_radio.py:33–118`,
`envs/pettingzoo/uav_env.py:23–159,288–456,598–604,979–997,1441–1490`,
`envs/pettingzoo/env_adapter.py:201–318`,
`experiments/candidates/ucope/uav_motion_prefix_b01/environment.py:8–24`,
`experiments/candidates/uav_radio_activation/b01/study.py:52–55`,
`experiments/candidates/uav_registered_service/b01/history.py:39–108`,
and the waiting B01 history, B02 scheduler and B04 scheduler/collector.
CodeGraph was used first; omitted source ranges were then read directly.

1. The actual factory fixes five UAVs,50 users, cochannel interference,
   free-space radio, no shadowing, native non-paper reward and H256. The
   native threshold is3dB and each UAV's capacity is10.
   Write an active signal as P_i and gamma=10^(3/10)>1. Eligibility requires
   P_i >= gamma(noise + sum_{j!=i}P_j). Two eligible UAVs for the same user
   would require both P_i>P_j and P_j>P_i. Therefore the eligible user sets
   are disjoint. This is a source-conditioned mathematical consequence,
   not a measured frequency or a claim for FDMA, another threshold or S7.

2. Highest-SINR native allocation already attains the largest number of
   contacts for fixed geometry/mask: sum_i min(10,|E_i|). Its remaining
   freedom is which eligible users receive a saturated UAV's slots, not a
   general cross-UAV matching problem. Any work-conserving alternative with
   the same eligible sets preserves that tick's contact count. Native
   quality is monotone clipped SINR, so highest-SINR allocation also
   maximizes quality at that count. An alternate allocation cannot raise
   mathematical native J on the same path; quality ties can preserve it,
   and strict quality loss lowers J. This is a substantive valuation
   constraint, not a new reward success criterion.

3. Connections affect actual contacts, native reward and evaluator histories,
   but not the selected physical transition or policy observations. Native
   observations expose the top20 eligible users' geometry/SINR, peers,
   position and time. They do not expose assigned connections. The adapter
   packages rewards separately without feeding them into observations.
   B04 C receives only observation/tick. The scheduler receives own
   positions, actual/proposed commands, tick, mask and post-C navigation
   indices. Its executed log receives commands/mask only; it reconstructs
   contacts from rounded anchors and the original greedy model. Actual
   connections/reward are copied only afterward to evaluator raw.

4. Consequently a new local allocation layer can preserve each saved
   complete physical path **provided** it leaves the original C, commands,
   masks, observations, reports, modeled-greedy histories and delivery/
   timeliness unchanged. Feeding new actual contacts into the manager or
   changing its forecast law invalidates that statement. Source invariance
   does not establish integrated runtime deadlines, hardware link behavior
   or the absence of contention from added local work.

5. The new local layer would need current eligible registered IDs/SINR,
   its own grant memory, and the right to choose the capacity subset.
   The native radio layer already computes eligibility, but exposing it
   to a new decision rule is an explicit richer local information/action
   contract. It is not part of the old104-feature C or141-byte BS message.
   Grant equals service in this simulator, so remembering one's own
   grants needs no new global ACK. Local grant age is not actual global
   user age after handover. No claim of zero real implementation or
   protocol cost follows.

Existing B04 rows contain `mean_visible_users`, `mean_visible_peers` and
`empty_discovery_uav_steps`, derived from pre-step capped observation lists.
There is no saved capacity-exclusion/saturation aggregate in this reading,
and those fields have no arm aggregate in B04's paired summaries. The raw
schema retains full postmove `sinr[T,5,50]`, `connections[T,5,50]`, masks,
positions and commands. No new saturation, opportunity or outcome panel
was computed during this assessment. In particular, mean service below50
does not identify capacity denial, and the source proof does not establish
that fair allocation will reduce complete-episode tails.

### Prospective complete comparison and cost; not selected

Oracle requested a price for immutable B04 M/U/S paths on all64 worlds,
with original allocation and ordinary causal work-conserving fair rules.
The minimal useful comparison proposed to the Oracle is:

- **Highest SINR:** the frozen native allocation and its existing path.
- **Cyclic round-robin:** scan at most50 registered IDs cyclically per UAV,
  grant min(10,|E_i|) eligible users, then advance past the last grant.
- **Local least-recently-served:** choose oldest own grant first, ties by
  higher current SINR then registered ID; own last-grant times start at−1.

The two fair rules receive the same current eligible IDs/SINR and own-grant
history, with no future eligibility, cross-UAV ACK or global actual age.
Round-robin tests a simple ordinary service opportunity; local recency is
the competent history-based comparator and can differ under changing
eligibility/handover. Neither is a learned method or new optimality claim.
The existing motion/radio manager deliberately retains its modeled-greedy
history. No K extension, objective-weight sweep, learned rule or new
physical acquisition is included.

All192 proposed source members are available at the canonical node under
`/home/wu/projects/HMASD/runs/uav_user_waiting/b04_service_floor_a01/raw/`:
M/S/U × seeds29426000–29426063. A read-only existence/size check found192
members, zero missing and zero size mismatches; it did not open raw arrays
or recompute outcomes. Their compressed sizes are91,404,329 /78,207,842 /
93,129,012 bytes, total262,741,183. Every individual SHA256 is already in
the published compact result's `rows`/`raw_artifacts`. Bindings are:

- compact `result.json` SHA256
  `ccd52d06fe48c7e3f5315b834cb702e1b22b826df25af68a6e2eeb7e3a09707a`;
- complete worker summary SHA256
  `49754e61f38009681d5a842d320a1878bdd260518300a5391cc3c8678db47c47`;
- complete reader SHA256
  `69787803a4de84555c534d9b7f21a23c290c7d4446bc874a2da6e49237289513`.

The prior complete reader verified all256 raw identities. A selected replay
would verify its192 required raw files anew; this metadata check does not
replace that verification. It would be **new result-bearing allocation
replay**, despite zero new native or radio-model calls.

| Prospective work | Producer | Independent complete reader | Combined |
|---|---:|---:|---:|
| Existing physical trace ticks consumed |49,152|49,152|98,304 reads of49,152 unique ticks|
| New fair-allocation complete outcomes |384|384 reconstructions|384 distinct new outcomes|
| Original-law complete reconstructions |192|192|192 distinct original paths|
| Fleet allocation calls, all three laws |147,456|147,456|294,912|
| Corresponding per-UAV allocation decisions |737,280|737,280|1,474,560|
| Service/quality/age transition reductions |147,456|147,456|294,912|
| User-tick age updates |7,372,800|7,372,800|14,745,600|
| Eligibility threshold entries, conservative two scans/tick |24,576,000|24,576,000|49,152,000|
| New native steps/resets, physics/geometry/model predictions, C/search calls |0|0|0|
| Fits, optimizer updates, new physical acquisition episodes |0|0|0|

The two fair rules themselves account for98,304 fleet calls /491,520
per-UAV decisions per pass. The conservative eligibility bill permits the
frozen greedy kernel's separate threshold scan plus one shared scan for
the two fair laws; sharing all three would halve threshold entries, not
allocation or outcome counts. The eventual implementation must expose its
actual scans. Correctness fixtures, all allocation/reduction work, source
and input hashing, reading and support are still costs, not fits. The576
law/path rows contain only64 independent world clusters; users, ticks,
physical programs and allocation variants are nested.

Without executing a pilot, the source-based planning estimate is0.05–0.20
CPUh for producer plus complete reader, including two raw SHA scans of
262.7MB, selective NPZ decompression, all allocations, metrics, paired
summaries and serialization. This is **uncalibrated**, not a measured cost
or execution allowance. A streaming pure-NumPy/stdlib implementation is
expected to stay within0.25GiB RSS and needs no GPU; unnecessary native
environment/learner imports would invalidate that memory estimate. Rough
active engineering work is4–6 hours: approximately2–3 for rules, producer
and causal/edge-case tests;1–2 for a separate reader and independent replay
review;0.5–1 for scientific reading, publication and retention. These
overlapping planning ranges are not observed labor or runtime. Separate
review/support CPU and unmetered time would be reported honestly. No
current code or test was written to estimate them.

A complete reading would retain every world and rule, changed-grant
exposure, no-link versus eligible-but-capacity-excluded interruption,
service counts, maximum gap, worst-user mean age, typical-user gaps,
mean/quantile ages, quality and J. It must preserve adverse users and
boundary censoring, and show whether continuity improvement merely trades
quality. Source guarantees count equality on fixed paths, not lower
tails. Reused B04 worlds are development evidence, not fresh confirmation;
post hoc best-rule selection would not establish a new default.

Retention can reference original raw in place and keep one canonical new
50-user contact stream per fair law/path:4,915,200 uncompressed Boolean
bytes total, or688,128 bytes if each50-bit row is packed into7 bytes,
before metadata/compression. New compact records would retain all world/
per-user outcomes, exposure, cost and source/input identities. No second
SINR/path tree or duplicate original evidence is needed. Full live native
integration, grant latency, manager-deadline interference, hardware channel
and ACK realism, or a manager that consumes the new assignments remain
unverified and would require a separately justified complete study.

The present DM recommendation is to consider this only as a bounded
empirical-understanding/use purchase: can a real local capacity-allocation
right improve individual continuity on retained competent motion/radio
paths, at what quality cost? It can locate an assignment bottleneck but
cannot rescue K, demonstrate learning or improve J on those paths. A
new fitted or live-control program is not warranted by source feasibility
alone. Stopping remains reasonable if that limited information is not
worth the engineering cost relative to other project questions. The
independent Oracle's completed recommendation and Root's subsequent
allocation remain distinct from this source price.

Actual assessment cost so far is source/document/JSON-metadata reading,
one remote metadata-only availability check and reasoning; shell/support
CPU is not fully metered. There are zero new scientific fits, native
steps, model/controller queries, allocation replays, outcome reductions
or code/test changes. Cumulative completed B01–B04 cost remains two fits,
327,792 result steps,272 correctness steps and13,293.473639 measured
worker/reader CPU seconds, plus separately described support/fixtures.

<a id="b05-original-oracle-advice"></a>
## 2026-09-30 — complete allocation Oracle question, advice and DM response

Root requested preservation and full reading of the original source-assessment
question and recommendation. The complete original texts follow; their
source-only status is historical. Root subsequently selected the bounded
allocation replay described below. No result calculation preceded that choice.

### Root's original question to the independent Oracle

> New source-only next-allocation assignment, reusing your independent Astra Max context and the original M/S/U/K recommendation. Waiting B04 is now fully verified, independently diagnosed, published5d6353ff59da4b2b5c796629cacb4820ab0bb986 and closed/reserve atd02e5029f. Root read the complete DM result and the ORIGINAL result critic plus final addendum (agent/root/dm_user_waiting/scientific_reading, window01a0f458-766c-74c0-836d-83f7117e6bcd, items811039568 and678354406). Evidence: NOTES#b04-complete-reading/#b04-independent-review-and-disposition and runs/uav_user_waiting/b04_service_floor_a01/result.json (SHA ccd52d06fe48c7e3f5315b834cb702e1b22b826df25af68a6e2eeb7e3a09707a); full reader SHA69787803…89513, source dd3b2577d. Read original outcomes/adverses before proponents' reasoning; reuse that critic's complete reconstruction, no duplicate result audit.
> 64worlds/256H256/65,536steps/0fits: K−M service−.036499[t95−.243719,+.170721], max-gap−2.5625[−6.365632,+1.240632], worst-user mean age−1.018494[−2.052410,+.015423]. Joint mean sign fails on service, but mixed near-M evidence is NOT B03's uniform learned loss, equivalence or impossibility. U−S gives service+.486389 and worst-user age−1.599670 (both intervals exclude0), G−1.104375, J+.005405; extra1.353448schedulerCPU-s/episode and lowerquality. U still loses3.069336service vsM in ALL64worlds while improving extreme tails. All4096 K floorshold,289same-stateMphysicaldepartures; +1034modeledservice margin−88 selected prediction residual but full−598 user-ticks because K-state reference sum is1544belowMtrajectory. This is accounting, not an identified cause; first divergenceK06/K34 predictedexact yetlateradverse. Everyroundtimely. Readercomplete154478candidatepairs617014physicaltransitions plusallmetrics/history/choice, sharedradiokernel. Completeworker+reader2342.870991CPU-s; fixture32steps/3.300429CPU-s separate. Retain M, costedU, cheaperS, K'smixedfacts; stop automaticKextension/repair.
> Question for Root allocation: given this cumulative service/continuity frontier and the active negative finite-learning results, what substantive knowledge/use question is worth this DM's next effort, if any? Give demonstrated ordinary capability genuine development/use consideration, but do not default to another floor/debt/horizon/ACK repair, a parameter sweep or precision-only extension without a real prospective decision. You may recommend a materially independent research question or a reasoned stop; no fixed idea count or manufactured promise. New acquisition/learning is allowed as a proposal only if a complete matched comparison would answer a useful question beyond asset ranking; explain its physical information/action rights and strongest simpler alternative. Owner wants4substantiveDMs, but source preparation is not a selected result study.
> Use cumulative records, all3local libraries, July/external rounds and load-bearing primary passages/web as needed; no novelty from a library miss. Work with SAME /root/dm_user_waiting for bounded source/interface/full-cost facts; I am rearming it for this source-only question. N8 temporal and planner-amortization results are being considered together by /root/deep_report_review, so coordinate concrete overlap rather than purchase duplicate designs. Fleet B06 count-diverse imitation is already selected/implementing4fits/679936steps+40fixture at2687e773, not available to duplicate. Claude's paused questions remain owned. Return original reasoned recommendation, outcome-dependent decisions, full training/native/model/reader/engineering/support/retention costs and material dissent. No code edits, probes, controller/actor/model/native queries, fits, prototype execution or launch; Root will choose the next cross-question allocation.

### Complete original Oracle recommendation

> **Recommend a bounded pivot: test ordinary local service allocation on the saved M/S/U trajectories.** Buy the complete replay comparison below; do not buy another K extension, learned-value repair or fresh acquisition now.
>
> The question is: **How much of the observed continuity cost comes from always assigning capacity to the highest-SINR users, and can ordinary local allocation improve it without changing UAV motion, transmitter use or served counts?** This develops the demonstrated controllers through a materially different control right. It makes no novelty claim for round-robin or recency scheduling.
>
> I reviewed B04’s compact outcomes and consequential positive/adverse rows, then read the complete original critic and verifier addendum. I reuse their full reconstruction. K61 preserves a genuine joint-positive example; K34 loses episode service and adds 30 maximum-gap ticks despite exact prediction at its first departure. U’s service/F_user improvement over S remains useful, with additional computation and lower quality. Those results justify retaining the ordinary capability, but identify neither a K repair nor a learning bottleneck. Root supplied result headlines, so this successor review is not blinded to B04.
>
> The new comparison has a source-backed separation:
>
> - With the frozen non-FDMA interference law and 3 dB threshold, a user cannot be eligible for two UAVs simultaneously. Two eligible transmitters would each need received power greater than the other.
> - Consequently, any allocator filling each UAV’s eligible set to `min(10, eligible users)` preserves the original per-tick served count.
> - Associations do not determine interference, physical movement or native observations. C and the manager receive geometry, commands and modeled history; actual connections and reward remain evaluator outputs.
> - Keeping the manager’s original modeled-greedy history unchanged therefore preserves the recorded physical trajectory. Feeding the new grants back into that history, or changing its forecast law, would invalidate this replay claim.
>
> I directly inspected these dependencies and matched seven consequential current source files to B04’s frozen identities, including the [radio law](/home/fires/hmasd-wsl/envs/pettingzoo/uav_radio.py:33), [observation construction](/home/fires/hmasd-wsl/envs/pettingzoo/uav_env.py:405), [collector](/home/fires/hmasd-wsl/experiments/candidates/uav_user_waiting/b04/study.py:119) and [history settlement](/home/fires/hmasd-wsl/experiments/candidates/uav_registered_service/b01/history.py:85). This narrowly satisfies the July review’s warning against replaying action tapes when counterfactual observations would change.
>
> **The strongest consequential limitation is mathematical: highest-SINR allocation already maximizes native quality at fixed positions, mask and served count.** An alternative can retain quality through ties or sacrifice it; it cannot improve mathematical native J on that same path. The proposed benefit is service continuity with a measured quality/J price—not an unrestricted improvement of the original reward.
>
> The smallest worthwhile complete comparison is all 64 B04 worlds, each of the three immutable physical programs M/S/U, under these three allocation laws:
>
> | Law | Causal selection rule |
> |---|---|
> | Original | Frozen descending-SINR assignment, capacity 10 |
> | Cyclic RR | Scan persistent registered IDs cyclically, fill capacity from currently eligible users, advance after the last grant |
> | Local LRS | Serve users least recently granted service **by this UAV**; break ties by higher current SINR, then ID |
>
> Freeze the RR initial cursor and empty-set behavior prospectively; a simple choice is cursor zero and no advancement without a grant. Initialize each LRS timestamp to −1. Reset contacts are unscored and do not initialize grant history.
>
> Both new laws receive the same explicitly richer **local** interface: current eligible user identities/SINRs, persistent identity across the mission, and their own previous grants. They receive no future eligibility, other UAV’s grant history, global true age or cross-UAV ACK. At handoff, an arriving user may look locally unserved despite having just received service elsewhere. LRS must preserve that limitation.
>
> Grant implies service in this simulator, so recording an own grant needs no additional acknowledgment. Exposing the full eligible-ID list and choosing the capacity subset is nevertheless a new observation/action contract. It is not already an action available to the frozen motion actor. Central reports remain unchanged; hardware discovery, addressing and timing costs are not thereby established as zero.
>
> RR is the simpler fairness comparator. LRS tests whether retaining local recency adds useful value under changing eligibility. These can resemble the same cycling discipline with a fixed eligible set; their names alone do not establish different mechanisms. The frozen highest-SINR law remains the competent quality comparator.
>
> The declared reading should retain:
>
> - Full-episode maximum gap, worst-user mean age, original typical-gap G, overall age, and all censoring boundaries.
> - Served-count equality at every tick, quality/J, and inherited path/transmitter/manager costs.
> - Every world, per-user outcomes, changed-grant exposure, capacity exclusions and intervals without any eligible link.
> - Within-program allocator contrasts, LRS−RR, and the resulting M/S/U operating choices. Use 64 paired world clusters; users, ticks and the 576 resulting rows are not independent replications.
>
> These are reused development worlds. No fresh confirmation or population-optimal frontier follows. K’s mixed evidence remains intact outside this proposed intervention; neither K nor other physical controllers are declared inferior under the revised allocation law.
>
> The outcomes would change real choices:
>
> - **RR improves continuity at an acceptable observed quality price, and LRS adds little:** retain simple RR as the ordinary allocation option. Stop local-history elaboration.
> - **LRS adds useful continuity beyond RR:** retain that ordinary memory capability and its costs. This establishes no need for learning.
> - **M with fair allocation reaches the useful tail range of U while retaining M’s service count:** revise the practical comparison toward that combined operating option. The original M/U tradeoff was partly contingent on allocation law.
> - **U retains a tail advantage after both receive the same allocation right:** retain a distinct contribution from U’s physical program.
> - **Few grants change:** report sparse capacity-choice exposure and stop this purchase without claiming scheduling is generally ineffective.
> - **Grants change substantially but continuity remains poor or worsens:** stop these allocation rules. Do not automatically escalate to global ACK, new weights or another learner.
> - **Source invariance or baseline reconstruction fails:** the affected replay is invalid; no automatic native replacement run follows.
>
> A favorable replay would establish complete conditional episode outcomes for this add-on. It would not establish live deadline compliance or authorize adoption. A later integration purchase would require valuing the measured continuity/quality tradeoff.
>
> The same DM supplied this complete feasibility response, without calculating new outcomes:
>
> | Cost or exposure | Proposed complete study |
> |---|---|
> | Inputs | 192 existing H256 traces; 262,741,183 bytes; stat check found no missing files or size mismatches |
> | New allocation outcomes | 384 H256 outcomes, 98,304 fleet allocation steps |
> | Original-law reconstruction | 192 outcomes, 49,152 fleet steps |
> | Producer plus full reader | 294,912 fleet allocator calls; 1,474,560 UAV subdecisions; 294,912 service/quality/age reductions |
> | Eligibility accounting | Budget up to 49,152,000 threshold entries across both passes |
> | New fits, native steps/resets, C calls, radio predictions, candidate search | **Zero** |
> | Worker plus reader estimate | **0.05–0.20 CPU hours**, including input hashing, reads, metrics and serialization |
> | Memory | Expected ≤0.25 GiB; no GPU |
> | Engineering and support | **4–6 active hours**, covering rules, causality tests, independent reader/review, interpretation, publication and retention |
> | New retained bulk | One contact stream per new law/trace: 4,915,200 Boolean bytes, or 688,128 row-packed bytes, plus compact outcomes and bindings |
>
> These are source estimates, not profiling measurements. Input hashes must be checked during execution. Reuse original SINR/path files in place. B04’s 65,536 native steps and 2,342.871 worker-plus-reader CPU seconds are already paid evidence; this replay is additional result-bearing work despite zero new native calls. Current review/support time is incompletely metered.
>
> Live allocator latency, interference with the manager deadline, integration into the native interface and hardware channel/ACK realism remain unverified and unpriced. The proposed study does not silently include those purchases.
>
> I searched all three local library catalogs and the available My-lib hints, and revisited the relevant July/external-review constraints. A search miss supplies no novelty verdict. Primary antecedents already support ordinary fairness/age scheduling: [Han et al., arXiv:2010.07139, §III-A](https://arxiv.org/pdf/2010.07139) analyzes clustered round-robin under specific homogeneous-channel assumptions; [Talak et al., arXiv:1803.06471, §§II/V](https://arxiv.org/pdf/1803.06471) uses centrally available channel state and ages. Neither guarantee transfers to these changing eligibility sets and strictly local grant histories.
>
> I prefer this purchase to another motion/value intervention because it tests a distinct causal lever using complete existing trajectories at bounded cost. If Root does not value studying the richer allocation interface, retain waiting in reserve; the present evidence supplies no comparably justified automatic continuation within the old interface.
>
> **MATERIAL_DISSENT: no** — Root has selected no new run and requested this assessment. My recommendation is the bounded allocation replay, with explicit new rights, quality/J consequences and live-timing limits.

### DM scientific response and selected scope

I read the complete original question and answer. I accept the bounded
allocation-rights question and its three-law comparison. The source proof
removes an unnecessary new physical acquisition; it does not make this a
free result or establish a favorable tail tradeoff. Root has now explicitly
selected this purchase because distinguishing allocation loss from physical
path limitations and developing M/S/U is worth the estimated4–6 support
hours. The earlier source-only entry and the Oracle's historical unselected
wording remain intact. B05 is the one active result-bearing study; B01–B04
and K's positive/adverse evidence remain closed and preserved.

The response to the material premises is:

- **Rights and invariant:** full current local eligible IDs/SINRs and own
  grants are an explicit new local observation/action contract, common to
  RR and LRS. No actual global age, other UAV's grant, future eligibility,
  new BS packet or new C input is supplied. The original manager's
  modeled-greedy history is an invariant, not an estimate we may update
  using the new outcomes. Preserve complete original physical programs,
  delivery/timeliness and all source bindings.
- **What the intervention identifies:** alternate complete contacts on a
  fixed eligible-link sequence identify the effect of those allocation
  rules conditional on each retained physical program. A gap may contain
  both capacity-denied and no-link ticks; their counts are not a unique
  additive causal decomposition of its length. Report the actual changed
  grants and full gaps, plus the eligibility/exclusion exposure, without
  claiming that all residual waiting is an immutable physical limit.
- **The ordinary comparison:** original greedy is the quality comparator;
  cyclic RR is the simpler fairness option; LRS is a competent alternative
  using own recency under changing eligibility. RR also carries state in
  its cursor. LRS−RR therefore compares complete scheduling disciplines
  and their tie rules, not an isolated causal effect of memory. At fixed
  eligible sets they may agree; naming alone establishes no mechanism.
- **Native value:** service-count equality and the quality/J ceiling are
  structural checks, not successful empirical discoveries. No alternative
  can improve J on its own fixed path. Cross-program combinations may
  still change useful service/continuity/quality choices; keep their full
  measured costs. No post hoc acceptable-quality threshold, scalar weight,
  tolerance or population-optimal frontier will be invented.
- **Cost and decision:** I accept the4–6 active support-hour purchase as
  engineering, independent reading, interpretation and publication work,
  not as zero cost because no native steps are needed. The0.05–0.20 CPUh
  and≤0.25GiB streaming figures remain uncalibrated planning estimates.
  Actual allocator/reduction/hash/I/O counts and process resources will
  be recorded. Sparse exposure or adverse tails can justify a stop with
  no automatic additional rule, ACK, learner, native fallback or pilot.

I directly read the two cited primary passages. Han et al.
[arXiv:2010.07139v4, §III-A, PDF p4](https://arxiv.org/pdf/2010.07139)
assumes homogeneous independent time-varying error probabilities for its
clustered-RR guarantee and defines clustered RR through longest transmission
intervals. Talak et al.
[arXiv:1803.06471v1, §§II/V, PDF pp2/6](https://arxiv.org/pdf/1803.06471)
uses current link channel states and link ages in its age-weighted activation
rule, under temporally independent channel states. These are ordinary-model
antecedents, not guarantees for finite H256 trajectories, changing local
eligibility or own-UAV grant memory. The waiting metric here resets to0
after service; the cited packet-age recurrences use a one-slot convention.
No theorem, novelty verdict or empirical support is transferred. The exact
arXiv PDFs are the source locations; no matching paper ID was found in the
three catalog searches made for this direct passage check.

Root's selected closure conditions are adopted: a baseline/source-invariance
failure stops the affected replay for diagnosis; no automatic native
replacement follows. Favorable replay remains conditional development
evidence, with live latency, scheduling interference, hardware discovery/
addressing and native integration unverified and outside this purchase.
Reset contacts and unscored mask-refresh associations do not initialize
or update new grant histories. Only the256 scored postmove transitions do.
There is no material scientific dissent; the causal and memory-attribution
limits above narrow the interpretation without changing the selected laws.

<a id="b05-local-allocation-prospective"></a>
## B05 — selected complete local-allocation replay; prospective contract and L0

Root selects the complete comparison above. The published shared background
and selection at `d976f4ef8` and the current
[Root decision](../../RESEARCH.md#waiting-local-allocation-root-decision-20260930)
are reused: this purchase tests a distinct allocation right while preserving
the retained physical capabilities, the quality ceiling and all old adverse
outcomes. It is exploratory development on already exposed worlds, not
confirmation, a native integration trial or a learning study. No acquisition,
fit, C/radio-model query or parameter search is included. Code preparation
starts after this entry; no production allocation outcome has been computed.

**Frozen object and inputs.** Name `UAV-USER-WAITING-B05`; use exactly
B04 source `dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4`, its complete summary
and reader at the hashes recorded above, and M/S/U × seeds29426000–29426063.
Each source trace has256 scored postmove ticks, five UAVs and50 registered
users. Use canonical remote files in place. Source metadata and every raw
file are hash-checked before their allocations are consumed; retain their
identities in the new config/results. The radio, native step/observation,
adapter, real factory, C, collector and modeled-history/scheduler source
bindings supporting the separation must match the frozen B04 identities.
Do not instantiate any old environment, C, scheduler, learner or predictor.
There is no new native reset or step. A violated binding, non-disjoint
eligible set, original-allocation mismatch, count violation or quality
ceiling violation stops the affected replay with its paid prefix/error;
there is no automatic replacement or native fallback.

**Policies and causal interface.** Programs are M/S/U; allocation laws are
`ORIGINAL`, `RR`, `LRS`. At every scored tick, each fair allocator sees
only its own current eligible registered IDs and their actual SINRs, the
tick and its own state. Eligibility is SINR>=3dB; disabled rows remain
ineligible. It grants exactly min(10,eligible count) users. Each law/path
has separate state, reset at the mission boundary. RR starts each UAV at
cursor0, scans ascending IDs modulo50 from its cursor, stops after the
last needed grant and advances to the following ID. If no grant is made,
the cursor is unchanged. LRS starts each own-UAV/user timestamp at−1,
sorts by earlier own grant, then higher current SINR, then smaller ID,
and sets selected timestamps to the current scored tick. No reset or
unscored mask-refresh contacts initialize/update either history. No other
UAV history, global age, future eligible set, reward or original selected
connections enter a fair rule. The original manager's modeled-greedy
history, physical path, observations, reports, masks and delivery remain
unchanged; only the evaluator's new actual contact streams differ.

**Complete reading.** Produce all576 law/path rows:192 complete original
reconstructions and384 new complete fair outcomes. Baseline reconstruction
means all original assigned-user bits and all256 native served/quality/J
values, plus the original episode age/gap endpoints; it does not rerun the
already verified old C/search/model histories. Keep full post-transition
age accounting (initial0, service resets0, otherwise+1), every unserved
interval `[start,end)`, its left/right mission-boundary censoring, and
per-user service counts, mean ages and longest gaps. Record F_user,
episode maximum gap, G=mean per-user maximum gap, A, age_p95, terminal age,
never-served users, closed and censored gap maxima, mean service, quality
and J. Preserve inherited physical path, transmitter and manager costs
separately from new allocation/replay costs.

For each law retain changed-grant user/tick exposure against ORIGINAL,
per-user capacity-denied versus no-link ticks, and no-link intervals.
Distinguish an eligible set of size10 from a genuine choice of size>10.
Every unserved tick must be classified; a mixed gap retains both counts.
The three-law within-program contrasts and LRS−RR are primary interpretive
comparisons; preserve all36 unordered comparisons of the nine program/law
packages to read the complete operating choices without selecting a new
contrast after seeing results. Report each64-world paired vector, mean,
sample SD and descriptive t95 interval; the t63 critical value is fixed
at1.998340542520741 (the inherited SciPy definition checked as arithmetic,
not a data query). No bootstrap, fitted test, acceptance weight or new
equivalence/adoption tolerance is added. Numerical array/reduction checks
use exact integer/contact equality and at most1e−12 absolute floating
error; report actual maximum discrepancies. This tolerance is numerical,
not a service/quality noninferiority margin.

**Cost and output contract.** The full prospective cost table above applies:
producer147,456 fleet allocations/737,280 corresponding UAV decisions and
147,456 service/quality/age reductions; the independent complete reader
repeats all. Original-kernel calls and RR/LRS row selections are exposed
separately from these conceptual UAV allocation components. Count actual
threshold scans, input hashing/bytes, original/new complete outcomes,
partial work, all zero native/model/C/fit/update counters and correctness
fixtures. Up to49,152,000 threshold entries for both passes is the declared
conservative bill, not a requirement to add redundant scans. The0.05–0.20
CPUh total estimate and0.25GiB streaming target remain estimates, not a
fit allowance or outcome-based stop. Instrument complete process user/sys
CPU, wall and peak RSS, plus allocator-only timing as replay computation,
not live deadline compliance. The4–6 active support-hour estimate includes
implementation, independent review/reader, reading, publication and cleanup;
unmetered support is not reported as zero.

Retain one new Boolean50-user contact stream for each fair law/path, with
source/member identities; no duplicate original SINR/path/history tree.
Keep compact complete rows, paired vectors, per-user age/gap/censoring and
exposure, source bindings and native operation records in
`runs/uav_user_waiting/b05_local_allocation_a01/`. A separately admitted
full reader uses `b05_local_allocation_read_a01/`, verifies all192 inputs
and all576 outcomes independently, and retains its complete reading.
Durable bulk stays on the canonical node; no whole-tree backup is needed.

**L0 implementation and ownership.** Shared main checkout is
`/home/fires/hmasd-wsl`. One bounded Implementer owns only new
`experiments/candidates/uav_user_waiting/b05/{__init__,protocol,allocation,study,run}.py`
and matching `tests/experiments/candidates/uav_user_waiting/b05/test_allocation.py`
and `test_study.py`: implement the causal allocation producer with the
fixed bindings, counts, streaming outputs and admitted CLI. The DM owns
the numerical reader (`b05/reader.py`, `b05/read.py`, `test_reader.py`),
NOTES, RESEARCH and run publication. Sharing protocol constants or
hash/JSON utilities is allowed; the reader must not use producer
allocators or outcome/paired reducers as numerical proof. Helpers cannot
write notebooks, old B01–B04 code/evidence, shared core or the Git index,
commit, launch or read/reduce production raw arrays. Preserve other
writers; no checkout, branch or source-tree copy is created.

Checks cover capacity/exclusivity, empty/off rows, ties, cyclic wrap,
changing eligibility, handoff-local history, mission reset, no future/
other-UAV input, original reconstruction, quality ceiling, exact ages and
gap censoring, malformed/truncated/hash-mismatched input and complete
output identity/counts. Use small synthetic correctness fixtures under
pytest-managed scratch; no saturation pilot or production-data test run.
The DM reads and accepts the diff/checks. A registered independent
engineering Reviewer checks the high-risk causal replay and numerical/
input boundaries before exact input publication and launch. The existing
ResearchCritic independently diagnoses the complete result afterward.
The current Oracle review covers this selected scientific decision; no
additional Pro/review round is needed absent a material change.

After source publication and active direction/lead verification, use the
configured remote interpreter, native admission and detached worker/reader
observation. Root reports fleet B06 producer/reader released the node at
23:07:11UTC; fresh actual occupancy/memory admission still applies. The
native DM remains active through complete reading and publishes its own
disposition/background/standing. New live integration, rule elaboration,
fresh-world confirmation or learning requires a substantive new choice;
finishing this replay grants none of them.

<a id="b05-engineering-acceptance"></a>
### B05 implementation, independent engineering review and launch input contract — 2026-10-01 UTC

The bounded Implementer delivered only its five producer modules and two
test files; the DM read and accepts that implementation and owns the
independent reader/CLI/test file. All ten new executable/test files remain
inside the declared B05 paths. The final combined synthetic suite passed
**60 tests in1.70s**; the independent engineering Reviewer reran all60 in
1.42s. These include the complete producer/reader assembly on one synthetic
H8 world, all nine packages/36 comparisons, contact/gap/source tampering,
mission reset, handoff-local memory, input truncation, partial-law failure,
and admission before scientific effects. The test-only reduced assembly
uses pytest dependency injection; the production CLI exposes only the
fixed64-world/H256 contract. Synthetic allocator arithmetic and repeated
test/support work are additional incompletely metered support, not part of
the result exposure. All new native, environment, C/model and fit/update
counts are still zero; no production raw arrays have been consumed by B05.

The reviewed implementation makes these equivalent mechanical choices:

- RR sorts current eligible IDs by cyclic distance from its own cursor.
  This yields the same ordered grants and next cursor as the prescribed
  ascending modulo50 scan; there is no new policy or data access.
- The producer calls the frozen original greedy kernel49,152 times and
  each fair local selector245,760 times. The independent reader uses
 245,760 separate per-UAV original sorts after checking disjoint eligibility,
  rather than importing that kernel as its proof; it also repeats both fair
  laws. The conceptual294,912 fleet/1,474,560 UAV decisions and14,745,600
  user-tick age updates across both passes are unchanged. The producer
  makes two full threshold scans per tick; the reader shares one across its
  three independently reconstructed laws. Thus the implemented complete
  bill is36,864,000 threshold entries, within the declared49,152,000 bound.
- Fourteen frozen source files are checked, including the originally
  identified causal paths plus B02 protocol/predictor/collector dependencies.
  None of the old environment, controller, scheduler or predictor is
  instantiated. Full gap/censor/exclusion records are streamed to192
  per-trace JSON files; the summary keeps scalar endpoints and per-user
  vectors. Each trace has one NPZ containing its two fair contact streams,
  with source and completed-prefix identities. Original raw data stay in
  their existing canonical location.

The Reviewer found one material failure-accounting defect: a rejected
trace's independently measured allocation time was dropped because only
successfully returned trace timings were summed. The DM accepted and
fixed it with an accumulator updated during every measured selector.
The full assembly regression now rehashes a corrupted gap record and
checks that the failed first trace retains24 paid fleet allocations and
all three nonzero selector CPU readings in `reading.json`, while reporting
zero verified traces. Original/fair outcome counts and measured work are
separate. The Reviewer's focused return found no remaining material issue;
the reviewed ten-file aggregate SHA256 (sorted relative path, NUL, binary
file digest) is`eb71831c60ea0f561a7ae8461bece84196518062f0c02589523aa529006ba7a3`.
Full192-input verification, actual node resources and any scientific
outcomes remain unexecuted, so synthetic checks supply none of those claims.

**External inputs under immutable launcher snapshots.** Inspection of
`scripts/hmasd_launch.py` shows that the maintained `--generic-summary`
argument preserves a canonical data path while ordinary absolute
author-root arguments are rewritten into the source snapshot. B05 adopts
that supported route with its own declared hash contract, without changing
the shared launcher, creating filesystem aliases or copying bulk data:

- Producer `b05/run.py` receives the canonical B04 `summary.json` through
  `--generic-summary` and its fixed49754e61…c47 digest through
  `--generic-summary-sha256`. After admission it checks that digest, derives
  the already-declared sibling `b04_service_floor_read_a01/reading.json`,
  verifies its fixed69787803…9513 digest, and checks frozen code in its own
  immutable source `ROOT`.
- Reader `b05/read.py` receives the new canonical B05 `summary.json` through
  the same path/hash arguments plus the producer's exact launch SHA. After
  admission and worker digest validation, the original B04 summary/reader
  paths come from that bound worker config; its own immutable `ROOT` must
  still match the frozen code identities. No source or data path is inferred
  from a lost observer, alternate task or unbound filename.

The planned actual-node operations retain the declared producer and reader
tags, lead `Codex DM (native child)`, configured remote interpreter, published
source SHA, `--snapshot`, and canonical author-root outputs. Source
publication and fresh pause/ownership/memory/duplicate admission precede
execution. The current index still says owner pause lifted and this lead's
direction exploring. No retry, pilot, live integration or science revision
has been added by these implementation corrections. Runtime resource
fields are measured at final record assembly; final JSON serialization,
Python teardown and external support are not claimed as zero cost.

<a id="b05-a01-runtime-failure"></a>
### B05 A01 — accepted replay interrupted by SIGSEGV; evidence preserved (2026-10-01 UTC)

The reviewed inputs were published as `de238594dc9d64d7be246e7b9628a63f6a53b272`.
The fixed replay was admitted once on the configured `wsl_4070` node with
the configured GCC CPython3.10.21 interpreter. Its
[manifest](../../../../runs/uav_user_waiting/b05_local_allocation_a01/launch-manifest.json),
[native terminal status](../../../../runs/uav_user_waiting/b05_local_allocation_a01/native-status.json)
and [compact failure reading](../../../../runs/uav_user_waiting/b05_local_allocation_a01/result.json)
bind the exact command, source snapshot, native identities and preserved
artifacts. Admission was accepted at00:27:26.275399Z; the runner exited by
signal11 at00:27:41.182344Z,14.906945s later. Runner and supervisor were
both absent at observation. That elapsed interval is not process CPU time.

The last atomic `summary.json` is still `RUNNING`, with89 source traces,
267 outcomes (89 original,178 fair),22,784 source ticks and68,352 fleet
allocations. Its1,479,367 bytes hash to
`6e646a0ff9ef278cb15fd86a96e8471f4fd09f047182e8d2cbd696c182db72b8`.
It reports341,760 UAV decisions,3,417,600 age updates,11,392,000 threshold
entries and4.45502627 inner-allocator CPU seconds. These are checkpoint
lower bounds, not the completed bill. The disk also contains the complete
`U_29426029` contact/outcome pair: its outcome self-reports256 steps for
each of the three laws, yielding90 trace files/270 self-reported outcomes
in total. A1,120,784-byte `summary.json.tmp` is truncated JSON. This is
artifact context; it does not establish the faulting stack or cause.
Whole-process CPU, peak RSS and final accounting were not finalized.
New fits, native steps, model and C calls remain zero. The producer's
recorded invariance discrepancies through its saved prefix were within
the fixed thresholds, but no independent B05 reader has run and no partial
allocation benefit, package ranking or population conclusion is adopted.

All189 original output files,18,724,648 bytes, remain in their sole
canonical directory
`wsl_4070:/home/wu/projects/HMASD/runs/uav_user_waiting/b05_local_allocation_a01/`.
The compact record contains every file's path, size and SHA256, including
the extra trace and incomplete temporary summary. Eight collected metadata
copies were checked against those remote identities. Original B04 input
data and all old adverse outcomes remain intact. The new core remains in
place at
`/mnt/c/Users/wu/AppData/Local/Temp/wsl-crashes/wsl-crash-1790814460-1179774-_home_wu_.local_opt_hmasd-cpython-3.10.21-gcc_bin_python3.10-11.dmp`:
35,643,392 bytes, SHA256
`a06e26819a28ca65630bccadcdc72205d8cacb541f0eba460e31ac2365ec9cec`.
The source snapshot is retained while Root's read-only recurrence diagnosis
may consume it; it has not been removed merely because the native process
ended. The remote stderr is empty. At00:29:50.990256Z the guest reported
load averages0.12/0.35/0.21,15,249,348KiB available memory and2995.199MHz
for all20 visible CPUs. These post-failure observations neither measure
fault-time conditions nor establish load/throttling as the cause.

The deterministic observer registered this same operation, exposed the
consistent terminal fact in generation39, and could not queue a native
child wake (`-32600`). The DM stayed active, drained and consumed that
event, rearmed generation40 and stopped observation after collection.
There was no replacement worker or duplicate replay. A prior source-only
Git fetch stalled without the configured network login shell; its exact
owned transport process was terminated and the read-only fetch completed
through `zsh -lic` before scientific admission. This did not restart a run.

**Disposition and dependency.** This is technical incompleteness, not a
negative result for RR/LRS or a changed explanation of waiting. The
all64-world comparison, full independent reader and result interpretation
remain outstanding. Root has taken the bounded read-only shared runtime
recurrence investigation and node/runtime reassessment, under the owner's
earlier instruction to investigate if the provisional replacement crashes.
The DM supplied the exact operation/core identity through native child
communication and is preserving the accepted collection. No retry,
resumption, different-node replay, allocator repair, new scientific
comparison or confirmation is selected by this failure. Any selected
recovery must retain A01's exposure and cost rather than silently replace it.

**Local collection cleanup (00:35 UTC).** After publication at`54fd01aca88`
and identity verification, the DM checked visible same-user open file
descriptors for the six exact targets below and found no live consumer.
Deleted the redundant local
`runs/uav_user_waiting/b05_local_allocation_a01/{summary.json,stdout.log,stderr.log,failure-observation.json,failure-inventory.json}`
and the consumed
`temp/directions/uav_user_waiting/b05/worker-observer-request.json`.
Measured allocated file bytes fell from1,568,768 to0; all six targets are
absent, so net allocated disk reclaimed is1,568,768 bytes. Compact committed
metadata and the complete original canonical output/core remain. The
remote source snapshot is deliberately retained for Root's live forensic
consumer; no deletion tool was blocked and no backup chain was created.

<a id="b05-local-recovery-prospective"></a>
### B05 — selected local recovery, exact staging and narrow L0 (2026-10-01 UTC)

Root selected one complete recovery on `local_linux` after the bounded
core check found an invalid CPython iterator operand during apparent JSON
publication; its antecedent cause remains unresolved. This selection does
not declare the remote interpreter or hardware repaired. A01's failed
operation, unique partial outputs, core and source snapshot remain intact
for the separate read-only diagnosis. There is no remote retry or prefix
resume. The same DM owns recovery through the full independent reading,
scientific interpretation/review, publication and measured cleanup.

**Exact scope and additional bill.** Use new tags
`b05_local_allocation_a02` and `b05_local_allocation_read_a02` for all192
original M/S/U source trajectories,64 original worlds×3 paths×3 laws,
576 outcomes including384 fair outcomes, followed by the original full
independent reader. No new worlds, policies, fits, native resets/steps,
model or C calls are added. All tie/reset/history/precision/metric semantics
and the36 paired comparisons stay fixed. Charge the full294,912 fleet
decisions,1,474,560 UAV allocation decisions,14,745,600 user-tick age updates
and36,864,000 threshold entries again, in addition to A01's separately
preserved partial bill. The earlier0.05–0.20CPUh complete replay/reader
estimate remains a prospective conservative estimate, not a measured local
price or hard allowance. New allocation CPU/wall measurements belong to
the local node. Inherited B04 real-time execution, geometry/controller
costs and deadline evidence still belong to their original remote node.

**Input staging.** Copy byte-identical B04 metadata and only the192 M/S/U
NPZ members to
`/home/fires/hmasd-wsl/temp/directions/uav_user_waiting/b05/local-inputs/`,
preserving sibling directories`b04_service_floor_a01/{summary.json,raw/}`
and`b04_service_floor_read_a01/reading.json`. The two metadata files retain
their fixed49754e61…c47 and69787803…9513 hashes; the192 raw members retain
the summary's per-file hashes and total262,741,183 bytes. No K data, new
trajectory or changed summary is staged. Mechanical transfer verification
hashes every staged byte before execution; producer and independent reader
each hash their actual input again. Staging is a temporary additional copy
of the existing durable remote inputs, removable after its last consumer.

**L0 owned correction.** Direct DM implementation is limited to B05's
`protocol.py`, `study.py`, `reader.py` and their focused tests. The frozen
summary/reading still describe their original canonical remote paths;
local path equality cannot truthfully be satisfied by rewriting those
hash-bound bytes. Add the fixed canonical B04 run root to the protocol,
independently check each original member against that root and its exact
program/seed basename, then bind only its read location to the staged
summary's sibling`raw/` directory. Preserve the original path beside the
effective input path and require the same bytes/hash on read. The original
B04 reader's summary identity is compared using its canonical path and
unchanged bytes/hash; B05 records its actual staged metadata location.
The independent reader repeats the location/provenance check without
using producer allocator or outcome code. No launcher change, filesystem
alias, input mutation, numerical policy change, environment construction
or unrestricted source override is needed. Synthetic checks cover relocated
metadata, canonical-member mismatch and changed staged bytes, alongside
the existing complete producer/reader assembly. An independent engineering
Reviewer checks this source-binding correction before publication and
execution. Existing scientific advice still covers the unchanged question;
the technical recovery alone adds no new scientific review decision.

Exact code and this scope are published before result execution. The local
configured interpreter is`/home/fires/.venvs/hmasd-linux-cpu/bin/python`.
Fresh actual-node pause/lead/publication/memory/duplicate admission applies;
another accepted local operation is neither restarted nor presumed absent.
The ongoing remote cause investigation is not a prerequisite for this
separately selected local path. Source/baseline/invariance failure still
preserves the affected output and stops; this selection authorizes one
complete local recovery, not an automatic chain of replacements.

**Recovery implementation accepted.** The194 staged files were verified
byte for byte by SHA256:192 raw members total262,741,183 bytes and the two
metadata files total16,448,835 bytes. Transfer verification did not load
NPZ arrays or run an allocator. The narrow correction changes three
production files and two test files; allocator, outcome, pair reducers and
CLI are unchanged. The DM ran62 synthetic checks in1.52s and the independent
engineering Reviewer ran the same62 in1.50s, including relocated metadata
with the origin absent, rehashed synthetic wrong-member rejection, staged
byte corruption and the complete producer/reader assembly. The Reviewer
returned no material finding. The accepted five-file aggregate SHA256
(sorted relative path, NUL, binary digest) is
`4632d680d87635c7f08b9122c10c348eb034295250be0af64618e2a7ba650f59`.
This accepts the location/provenance correction, not production arithmetic
or local-node admission; those are still pending their actual operations.

**Local A02 acceptance.** Source/scope publication is
`4de05b0da41827cf945587003a2476584dac480e`. The new local producer was admitted
once at00:53:04.261137Z; its
[manifest](../../../../runs/uav_user_waiting/b05_local_allocation_a02/launch-manifest.json)
binds the configured interpreter, canonical outputs, immutable snapshot,
staged metadata argument and actual native identities. The standard
observer registered generation42 and adopted a consistent running status
at00:53:21.576376Z. The same DM keeps its turn active through collection and
the planned full reader. This is execution acceptance, not a scientific
result; A01's separate failure evidence remains preserved.

<a id="b05-complete-reading"></a>
### B05 — complete local recovery and independent reading (2026-10-01 UTC)

**Evidence and completeness.** The local producer finished with native
exit0 at00:53:46.526686Z; the separately admitted full reader finished with
native exit0 at00:55:34.728416Z. Both native records have consistent
identities and absent runner/supervisor processes. Source is
`4de05b0da41827cf945587003a2476584dac480e`. The
[compact complete result](../../../../runs/uav_user_waiting/b05_local_allocation_a02/result.json)
retains all576 producer rows, their complete per-user summary vectors,
all36 paired-world comparisons, all source/artifact identities, native
status and both passes' measured work. Repeated per-path source/artifact/
inherited-cost descriptors are factored into192`path_records`; each row
merged with its shared record was checked to equal the full producer row,
including a second check after writing and rereading the compact JSON.
No endpoint or adverse world was removed in this factorization.

The unique full files remain on`local_linux`:

- `runs/uav_user_waiting/b05_local_allocation_a02/summary.json`:
  4,780,839 bytes, SHA256
  `29829b9026d73992a2bf188373ed6ba24c7061d2a55dc57e74c91b39940f6508`.
- `runs/uav_user_waiting/b05_local_allocation_read_a02/reading.json`:
  4,551,440 bytes, SHA256
  `1fbd3ec9c3a85a74e9006171c89033d0f4705c21e9caf1fdb1b9494bd64d9a07`.
- Producer`contacts/` and`outcomes/` hold192 pairs. The former retain all
  two-law contact streams; the latter retain all576 complete per-user gap,
  censoring, no-link and denial interval records. Their hashes are in the
  bound summary and compact record; their combined bytes are34,159,038.

The reader verified every original/fair grant, service/quality/J tick,
actual age, gap, exclusion record, inherited field and the complete paired
comparison. It checked263,430 floating and9,231,493 exact fields; maximum
absolute floating discrepancy was2.842171e−14, within the fixed1e−12
threshold. Original quality/reward reconstruction errors were at most
2.220446e−16/1.665335e−16. There were192 verified source traces,192 original
reconstructions and384 fair outcomes; no failure or truncated trace.
The same observer drained producer generation42 and reader generation44,
consumed their terminal events, then stopped after generation45. Native
child queue delivery remained unsupported; neither operation was relaunched.

**Levels and same-path allocation.** All units below are simulator ticks
except service (users/tick) and the native quality/J scales. F_user is the
largest per-user mean age; gap is the episode maximum unserved gap; G is
the mean per-user maximum gap. These are means over the same64 reused
world clusters, not independent user/tick replicates or new confirmation.

| Physical program / law | F_user | gap | G | A | service | quality | J |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M / ORIGINAL | 12.982300 | 55.078125 | 19.534375 | 3.130050 | 24.736206 | .178278 | .399790 |
| M / RR | 9.368286 | 43.859375 | 15.605000 | 2.311390 | 24.736206 | .158520 | .393863 |
| M / LRS | 9.125000 | 43.375000 | 15.362188 | 2.288806 | 24.736206 | .166544 | .396270 |
| S / ORIGINAL | 10.962158 | 51.406250 | 20.901563 | 3.517103 | 21.180481 | .188986 | .353223 |
| S / RR | 6.460388 | 36.703125 | 15.158750 | 2.334149 | 21.180481 | .153867 | .342687 |
| S / LRS | 6.285339 | 35.093750 | 14.911250 | 2.298601 | 21.180481 | .161247 | .344901 |
| U / ORIGINAL | 9.362488 | 46.828125 | 19.797187 | 3.273011 | 21.666870 | .184305 | .358628 |
| U / RR | 6.170105 | 35.312500 | 15.239062 | 2.303875 | 21.666870 | .152620 | .349122 |
| U / LRS | 5.807617 | 33.171875 | 14.878125 | 2.259182 | 21.666870 | .159392 | .351154 |

Every law preserves **each tick's contact count** on its same physical
path. This both realizes the source-conditioned construction and fixes the
total eligible-but-denied user-ticks; the change redistributes grants and
denials over users/time. It is not a newly learned service improvement.
Both fair laws reduce G, A and age-p95 in all64 worlds for every path.
LRS reduces F_user in all64 worlds for each path. LRS−ORIGINAL F_user is
M−3.857300 (descriptive paired t95[−4.599530,−3.115070]),
S−4.676819[−5.576029,−3.777608], and
U−3.554871[−4.106393,−3.003348]. Corresponding episode-gap mean changes
are−11.703125/−16.312500/−13.656250, with53/62/62 improved worlds,
11/2/1 ties and0/0/1 losses. G changes are−4.172188/−5.990313/−4.919063.

These benefits have a measured price: LRS quality and native J fall in
every world against original greedy on all three paths. Mean quality
changes are−.011733/−.027739/−.024913 and J changes
−.003520/−.008322/−.007474 for M/S/U. RR also loses quality and J in every
world, by larger means. There was no declared utility weight, quality
noninferiority margin or global dominance rule that makes this cost zero.
All packages serve every user at least once within H256; never-served
counts are already zero under the originals and cannot explain the gain.

**Competent ordinary comparator.** RR supplies most of the waiting gain.
Its F_user changes against original greedy are−3.614014/−4.501770/
−3.192383 for M/S/U. LRS−RR adds smaller F_user changes of
−.243286[−.399993,−.086580],−.175049[−.307962,−.042135], and
−.362488[−.546644,−.178331]. It has24/26/22 adverse F_user worlds;
these means do not give per-world protection. LRS−RR episode-gap changes
are−.484375[−1.200630,+.231880],−1.609375[−2.433188,−.785562], and
−2.140625[−3.407982,−.873268]; M's interval crosses zero. LRS's quality
advantages over RR are+.008024/+.007380/+.006773 and its J advantages
+.002407/+.002214/+.002032, positive in every world. This is a useful
whole-rule comparison; RR is also stateful, and the comparison does not
isolate memory, SINR tie-breaking or any one mediator.

**Adverse worlds and censoring.** The sole LRS−ORIGINAL episode-gap loss
is U/29426039:34→35. Users48 and49 have the closed interval[218,253),
containing3 capacity-denied and32 no-link ticks. It is not a reset/terminal
censor artifact or proof that all its length is caused by denial. RR's
episode-gap losses occur in M/29426030(+1),M/29426058(+5),
S/29426021(+3),S/29426038(+2),S/29426059(+2),
U/29426039(+1),U/29426049(+7),U/29426059(+1).
RR's F_user losses are M/29426058(+.417969) and
U/29426030(+.441406); S has none. All per-user counterexamples remain in
the bound outputs, including LRS's adverse comparisons to RR.

The same-path gain is present in closed gaps as well as censored ones.
For M, mean maximum closed/left/right gaps change under LRS from
51.609375/36.515625/25.640625 to41.796875/26.359375/18.265625;
for S,48.828125/30.265625/23.781250 to32.625000/21.578125/16.171875;
for U,45.828125/27.234375/19.921875 to32.125000/21.125000/13.734375.
Longest observed gaps have a censored tie in15/14/10 LRS worlds, so those
observed intervals do not establish waiting lengths beyond the horizon.
The initial age is zero and only scored postmove grants update histories;
reset and unscored mask-refresh contacts are not extra service observations.

**Opportunity and a fixed-path bound.** Mean capacity-choice exposure
(`|E_i|>10`) is283.171875/301.828125/290.703125 UAV-ticks per H256 episode
for M/S/U, out of1280. Exactly-at-capacity exposure is111.5625/70.6875/79
and provides no subset choice. Mean no-link user-ticks are5435.921875/
5669.843750/5690.703125; mean capacity-denied user-ticks are1031.609375/
1707.953125/1562.578125. Both totals are unchanged across laws on a path.
LRS changes1110.875/1616.03125/1504.1875 user-grant bits per episode;
XOR counts include both recipients and displaced grants, not additional
served users. Thus real subset-choice exposure existed in this full panel;
the source proof alone had not established that opportunity.

For each world/path let L be the longest saved contiguous no-link interval
over all users. Every allocator restricted to that eligibility trace must
leave that interval unserved, so its episode maximum gap is at least L.
This is a finite-path bound, not an additional simulated policy. Across all
192 outcome files, mean L is42.75/34.21875/31.890625 for M/S/U. Mean
LRS episode gap minus L is only.625/.875/1.28125, with42/37/39 worlds at
the bound. Consequently those means also bound any further mean reduction
of episode maximum gap achievable by another allocator on these exact
paths, even one with privileged information. This does **not** bound
F_user, G or mean age, guarantee the bound is jointly attainable elsewhere,
or decompose a mixed gap into additive causal effects. The full per-world
arithmetic and all longest-gap intervals are retained in`gap_reading` of
the compact result; the scientific Reviewer independently reconstructed it.

**Cross-path reading.** M+LRS versus U+ORIGINAL increases service by
3.069336 and J by.037643 in every world, reduces A by.984205 in every
world, and reduces G by4.435 (61 improvements/3 losses). F_user changes
−.237488[−1.191972,+.716996] and episode maximum gap
−3.453125[−7.741012,+.834762] remain unresolved; this is not tail
equivalence or universal dominance. Quality is lower by.017760 on average.
The inherited M path is shorter on average but has83.1875 more transmitter
ticks than U; neither fact alone establishes energy value.

Giving both paths LRS retains the physical-program tradeoff: U+LRS minus
M+LRS reduces F_user by3.317383[−4.117548,−2.517218] and maximum gap by
10.203125[−13.749208,−6.657042], but loses3.069336 service/tick and
.045116 J, both in all64 worlds. Its mean-age change−.029624 has an
interval crossing zero. U+LRS versus cheaper S+LRS retains service
+.486389[+.271307,+.701471] and J+.006253[+.003039,+.009467], but
F_user−.477722, maximum gap−1.921875 and G−.033125 now all have
descriptive intervals crossing zero. U still pays1.353448 additional
inherited scheduler CPU seconds per episode versus S. Thus improved local
allocation changes the useful ordinary reference without erasing the
remaining extreme-tail/service tradeoff or proving S/U equivalence.

**Costs, exposure and failure retained.** Complete local producer/reader
process CPU is41.849593+23.628504=65.478097s (0.018188CPUh); recorded
wall is42.141184+23.755721=65.896905s. Worker peak RSS is75,800KiB and
reader peak79,581,184 bytes, each below the prospective.25GiB streaming
target. Producer inner-allocator CPU is9.969120s; the independent reader's
original/RR/LRS selector CPU is.384220/.362227/.459433s. These timings are
local replay computation, not remote or integrated live-deadline evidence.
Final record assembly/serialization and support have their stated limits;
the JSON publication extraction is separately metered in the result.

The full pair paid294,912 fleet allocations,1,474,560 conceptual UAV
decisions,14,745,600 user-age updates and36,864,000 threshold entries.
Each pass read all262,741,183 raw source bytes; transfer verification
additionally hashed279,190,018 staged bytes. Both passes had zero native
steps/resets/constructions, fits, optimizer updates, C/model/SINR queries or
geometry predictions. The64 reused world clusters remain the scientific
replicates: repeated reconstruction and A01's partial execution do not add
independent worlds. A01's incomplete bill is separate, not replaced by
these successful measurements. All90 preserved A01 fair-contact NPZ
hashes match the fully verified A02 artifacts. That confirms those bytes;
it does not complete A01's missing panel or its missing final accounting.

Root's [bounded recurrence diagnosis](../../../../runs/runtime_repair/cpython_20261001_recurrence/diagnosis.json),
published at`011e074cf2c021a59f38c6c32131ec37ba2ab15a`, recovers
`protocol.py:84 → study.py:420 → json/encoder.py:296` during progress
publication and an invalid CPython FOR_ITER operand with a null iterator
slot. The antecedent cause remains unknown. Mapped build identities match
the rebuilt GCC interpreter/NumPy/libc, but executable text pages are absent
from the core; disk-fallback disassembly is not evidence of resident code
corruption. Post-fault load observations and A02 success do not diagnose or
cure the remote recurrence. The original core and A01 source snapshot
remain required forensic evidence under Root's disposition.

The relevant published shared background at`011e074cf2c` (topic2) remains
the comparison context: accumulated burden, learned factual continuation,
expanded search and local floors answer different questions and retain
their adverse evidence. B05 directly tests the source-identified local
subset-choice right. Its ordinary allocation capability can revise future
comparators under these richer rights; it does not retrospectively change
the old information/action contracts, claim novelty, establish learnability
or supply new-world confirmation. Independent scientific disposition is
recorded below before choosing any continuation.

<a id="b05-independent-review-and-disposition"></a>
### B05 — independent scientific review and disposition (2026-10-01 UTC)

The registered ResearchCritic received the actual question, original
supporting/adverse B01–B04 records, the complete original Oracle question
and answer, fixed B05 contracts, frozen source, full producer/reader and
canonical data. It reconstructed the main result before reading the
Oracle recommendation and DM explanation. It checked all21 source
bindings, all192 outcome hashes/gap records and seven consequential
original/contact archives; it did not rerun native dynamics or perform a
new fit. Its saved-data inspection used3.86 metered CPU seconds, separate
from worker/reader and other unmetered support. The DM's condensed record
of its substantive diagnosis and recommendation follows:

> Retain LRS as a useful ordinary allocation capability and revise the
> baseline toward M:LRS. Close B05 without an automatic learner, allocator
> extension or native rerun. S:LRS remains the cheaper option; U:LRS
> retains an extreme-tail advantage with lower service. The new result
> changes the practical comparison without establishing learning necessity
> or a free fairness improvement.
>
> Count preservation and the original greedy quality ceiling follow from
> disjoint eligibility sets and work conservation. The empirical finding
> is the substantial improvement in complete waiting outcomes. LRS lowers
> worst-user mean age by3.857300/4.676819/3.554871 ticks and episode maximum
> gap by11.703125/16.312500/13.656250 on M/S/U; quality and J fall in every
> world. Round-robin supplies most of that improvement. LRS's smaller
> F_user increments and its quality gain over RR in every world deserve
> retention, but24/26/22 adverse F_user worlds preclude uniform protection.
> RR is also stateful, and LRS changes discipline and tie-breaking: this
> supports the whole rule, not an isolated effect of memory.
>
> M:LRS retains M's service while reaching approximately the original U
> tail range; the F_user and maximum-gap differences versus U:ORIGINAL
> remain uncertain, and quality falls. Giving both paths LRS preserves
> U's distinct extreme-continuity contribution at a loss of3.069336 served
> users/tick in every world. Under LRS, U's extreme-tail increment over S
> becomes unresolved while its1.353448 extra inherited scheduler CPU
> seconds/episode remains. The stronger B04 U−S tail result should not be
> carried unchanged into this richer allocation contract.
>
> The cases preserve both opportunity and adverse consequences.
> M/29426061's original user47 has a closed87-tick gap[62,149), containing
> 18 denied and69 no-link ticks. LRS reduces that user's longest gap to25;
> episode F_user falls22.0625→6.078125, while RR already achieves6.164063.
> Serving selected eligible opportunities splits mixed intervals;
> subtracting denial counts from gap length misdescribes the effect.
> S/29426036 shows LRS worsening RR's F_user8.570313→9.582031 and maximum
> gap50→55: at tick62 RR grants user26 while LRS declines it among13
> eligible users competing for ten slots. LRS's closed[58,113) interval
> has one denied tick and54 no-link ticks. U/29426030 provides the positive
> RR comparison: F_user11.226563→8.160156 and gap55→34; LRS grants user28
> at its first eligible tick34 and retains the initial censored[0,34)
> interval. U/29426039's sole LRS−original maximum-gap loss34→35 is real,
> with three denied and32 no-link ticks in closed[218,253) intervals.
> M/29426022 retains user40's unavoidable88-tick no-link interval[71,159)
> under both fair laws; U's different path substantially reduces that
> user's waiting. Allocation and physical-path opportunities are distinct.
>
> The no-link bound was independently reconstructed from all192 outcome
> files. Any uninterrupted interval without an eligible link lies inside
> an unserved gap. Further allocation changes on these paths can therefore
> reduce LRS's mean episode maximum gap by at most.625/.875/1.28125 ticks
> for M/S/U, with42/37/39 worlds already at the bound. This finite-panel
> endpoint bound neither establishes allocator optimality nor bounds
> improvement in F_user or typical age.
>
> Direct reading of the frozen radio, observation, collector and history
> dependencies confirms that actual grants/rewards do not feed C or the
> manager's modeled-greedy history. A faithful port preserving that history
> has no demonstrated new grant-feedback path into motion. Remaining port
> uncertainty concerns implementation, added work and timeliness; feeding
> actual grants back or changing the forecast law is a different comparison.
>
> The old service–waiting tradeoff was partly contingent on greedy
> allocation, and ordinary local rules exploit substantial opportunity
> under the added rights. This supports a representable, causal local
> capability, leaves finite learnability untouched and does not explain
> earlier learned-policy failures. Eligible IDs/SINRs and subset control
> are explicit additions; there is no result for unchanged old actor rights,
> global-age access, hardware channels or another host.
>
> The65.478097 successful process CPU seconds do not replace A01's paid
> incomplete prefix. Matching90 contact hashes supports unchanged outputs
> without diagnosing the crash or adding replication. Local replay timing
> does not establish integrated deadlines. No additional observation is
> needed for this bounded result. Retain M:LRS as a main ordinary reference
> under the richer contract and the measured S/U alternatives; end further
> allocation-only investment aimed merely at reducing maximum gap on these
> paths. Materially larger maximum-gap gains require changed eligible-link
> sequences and comparison with fair baselines, including service, quality
> and cost. Buy fresh-world confirmation or a native port only for a
> corresponding population or practical-use decision, not because B05
> happened to be a replay. MATERIAL_DISSENT: no.

**DM response and changed explanation.** I accept this recommendation.
B05 establishes useful ordinary task capability under a specifically
richer local action/information contract. It changes the practical
baseline to include M:LRS, with RR as its competent simpler comparison,
and retains S:LRS/U:LRS as measured cost/service/extreme-tail choices.
The former physical-program tradeoff was partly contingent on original
greedy allocation; it was not wholly a lack of useful link opportunity.
The positive full-panel result now supplies that opportunity evidence,
which the earlier source proof alone could not provide.

Representation is not wholly untested: the causal local LRS rule is an
implemented representable capability with verified outcomes. The limits of
the old actor representation, finite learning and training-population
reliability remain untested by B05. The prior B03 learned failures, B04 K
adverses and their incurred costs remain unchanged. No individual memory
mechanism, missing ACK, neural limitation or learning necessity has been
identified. Complete-package value is conditional: contact count is
preserved, but quality/J fall, policies have adverse worlds, allocation
rights are richer, and integrated runtime has not been measured. Without
a supplied utility for these outcomes there is no universal adoption rule.

The selected B05 purchase is complete and ends here. Another fixed-path
allocator may still improve F_user or typical age, but this study supplies
no selected use case or conjecture worth buying it merely to chase the
already near-floor episode maximum. Nor does it select a native rerun,
fresh-world confirmation, changed forecast, new learning objective or
retuning. For the parent maximum-gap/service question, a consequential
future comparison would have to change physical eligibility and give
ordinary alternatives the same fair-allocation rights. That is a
recommendation to Root for a separately justified question, not execution
authority or an admission gate. Root owns that next cross-question
allocation; there is currently no dependent producer or required owner
decision. The direction returns to reserve after publication/cleanup,
with this conditional capability and its adverse evidence retained.

**Cleanup boundary.** The Critic closed all read handles and released the
two A02 source snapshots and temporary input staging. After completing
the core diagnosis, Root also released the A01 source snapshot from its
temporary forensic requirement. All21 A01 code identities were checked
against published`de238594dc9d64d7be246e7b9628a63f6a53b272`; the exact
config/native failure records also match published Git. All21 A02 code
identities match published`4de05b0da41827cf945587003a2476584dac480e`.
Exact-target collector previews accept all three terminal snapshots.
The core, mapped runtime files, canonical failed/partial A01 records,
original B04 evidence and complete unique A02 outputs remain required;
only source copies, staging and redundant scratch are selected for
deletion. Measured removal is recorded below after it actually occurs.

<a id="b05-final-cleanup"></a>
### B05 — publication and measured closure (2026-10-01 UTC)

The complete result, native records, independent diagnosis/disposition and
revised shared background/own standing were published at
`5715b7469b052f5380d51efa8b846f1d7d4850a5`. Useful allocation and independent
reader code/tests remain published for the retained capability and its
verification. No additional result execution or interpretation is pending.

After source/config recoverability checks and the explicit consumer
releases above, the supported exact-target collector removed these
terminal source trees **and their Git worktree registrations**:

| Node | Snapshot | Source tree allocated bytes | Registration allocated bytes |
| --- | --- | ---: | ---: |
| local_linux | `f558b8cd2a9c4b29a199f298bb7af1ff` (A02 producer) | 1,745,420,288 | 3,584,000 |
| local_linux | `754b66a479994bbfb898f76066019ea5` (A02 reader) | 1,745,412,096 | 3,584,000 |
| wsl_4070 | `9b680a5b7dee471e865759e84a49a043` (failed A01) | 813,965,312 | 3,612,672 |

It then removed these exact redundant local targets after a read-only
privileged process scan found no file/map/cwd consumer and no inspection
denial:

- `temp/directions/uav_user_waiting/b05/`:279,908,352 allocated bytes,
  including194 byte-identical staged B04 inputs, source-membership list,
  consumed observer requests and gap-reading scratch already in the result.
- `experiments/candidates/uav_user_waiting/b05/__pycache__/`:53,248 bytes.
- `tests/experiments/candidates/uav_user_waiting/b05/__pycache__/`:69,632 bytes.
- `runs/uav_user_waiting/b05_local_allocation_read_a02/progress.json`:
  4,096 bytes; the complete bound reader is retained.

All selected targets are now absent, including the three Git registrations.
The measured target allocation fell from4,595,613,696 bytes to zero:
3,778,035,712 local and817,577,984 remote. The newly retained
[cleanup record](../../../../runs/uav_user_waiting/b05_local_allocation_a02/cleanup.json)
uses12,288 allocated bytes, giving **4,595,601,408 net allocated bytes
reclaimed** for this cleanup scope. No relocation, archive or replacement
copy was made. This is an exact-target working-tree/registration measure,
not whole-host free space under concurrent activity or Git object-store
reclamation. The earlier1,568,768-byte A01 duplicate cleanup remains a
separate completed deletion and is not counted again here.

Post-deletion checks confirm unchanged hashes for the full A02 summary,
full reader and published compact result, with all192 contact/outcome
pairs present. The remote B04 full summary/reader and original crash core
retain their hashes; all256 B04 raw files,90 failed A01 contact/outcome
pairs and A01's unchanged atomic summary remain. Required mapped runtime
files and native claims/manifest/exit witnesses were not deletion targets.
These are intentional unique evidence, not cleanup blockers. There is no
concrete tool refusal or leftover selected deletion. B05 is closed/read/
published/cleaned, with no live producer, unread advice or selected next
batch; the retained question remains in reserve under the disposition above.
