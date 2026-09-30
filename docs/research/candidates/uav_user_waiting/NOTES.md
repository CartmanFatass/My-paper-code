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
