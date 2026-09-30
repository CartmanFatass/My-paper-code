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
