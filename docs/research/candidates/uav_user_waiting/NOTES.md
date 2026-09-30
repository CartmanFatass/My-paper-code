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
