# Planning policy compression

Lead: Codex DM (independent session), directly owned in the authoring checkout
`/home/fires/.codex/worktrees/fsd-a/hmasd-wsl`, branch
`codex/planning-policy-compression-sept25`. Task routing is maintained in RESEARCH.
This notebook is append-only and owned by this DM. No inherited worker or Send is resumed.

## 2026-09-25 — Adopt the planning-compression question and fixed B01 exploration

### Prior explanation and adopted advice

Owner delegated actual research execution of the adopted A plan to this new session.
Current published main was `d5261580dcf6d7a23da9473a4ad4f175c312e6db` when read:
[shared partial-observation background](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
[finite learning](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面),
[structural reasoning](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验),
and [current plan](../../RESEARCH.md#current-research-plan).
The current constitution supersedes historical four-DM wording: three is the concurrent
research-track ceiling, and each DM owns one result-bearing study at a time.
Owner pause is lifted for this direction; Claude FSD remains owner-paused and G33 frozen.

I read the complete [A question, saved Pro Answer and Decision](../../archive/2026-09-25/RESEARCH-decision-learning-adopted.md).
That consultation covers this question, comparator and first investment; no new premises
justify repeating it. Adopt its positive ordinary-loss term, stage-mean-one weights,
one shared roll-in augmentation, actual-history labeling, three simultaneous comparisons,
and full compute accounting. Ordinary BC can be a useful outcome without a WBC increment.
Do not identify zero Monte Carlo values with irrelevant decisions, small student-teacher
differences with noninferiority, or two training blocks with confirmation.

The retained [finite-model notebook](../finite_model_decision_value/NOTES.md#2026-09-25--b02-complete-precision-changed-native-budget-response-remains-small-and-uncertain)
and B01/B02 native evidence establish a bounded asset: ordinary P_k4_M32 completed
36/32 more jobs than AF on the two separate 256-context panels, including adverse worlds.
They do not establish an optimal teacher or general MARL/UAV advantage. The B02 initial
root had 114 exact-zero P32 means (109 all-zero particle sets); this is not the training
distribution. The filter omits state-dependent send/silence likelihood, and NEAR uses
AF continuation, at most 32 ticks and a receiver fixed at nominal .75. These approximations
remain unchanged. The old U/MC-budget repair investment and accepted operations stay closed.

The structural background changes the design concretely: we change finite history-policy
learning and deployment computation, not information rights or the receiver. Both agents
share student parameters but maintain private recurrent states. Joint replacement changes
state visitation and interaction, so local classification loss cannot substitute for H96
team completions. The simplest explanation is that ordinary BC is sufficient; another is
that neither finite RNN recovers the useful teacher behavior within this budget.

Primary-source passages checked: [VIPER/Q-DAGGER section 2](https://proceedings.neurips.cc/paper_files/paper/2018/file/e6d8545daa42d5ced125a4bf747b3688-Paper.pdf)
uses expert values to weight imitation; [DAgger](https://proceedings.mlr.press/v15/ross11a.html)
addresses policy-dependent observation distributions. Here a binary true advantage would
give local disagreement cost |Delta|, but our estimated NEAR advantage is neither optimal Q
nor a full-team causal effect. We borrow a weighting and data-coverage idea, not those
guarantees or novelty. One predetermined augmentation is not unlimited DAgger.

### Question, predictions and reading

Can a small recurrent student retain the observed ordinary planning use while removing
both online filtering and simulation? Read BC-AF, WBC-AF, each student-P_k4_M32 and
WBC-BC together. The candidate conjecture is that WBC reduces nonzero-advantage-weighted
disagreement on the same labeled data and loses fewer complete jobs than BC. A contrary
outcome, especially improved weighted imitation with worse complete utility, weakens
the usefulness of this approximate weighting under joint deployment. BC positive against
AF with no WBC increment strengthens ordinary amortization, not weighted novelty.

Primary outcome: completed jobs per H96 context; also retain service ratio, conflicts,
wait ticks, packets, forced sends and every loss world. Both training blocks are independent
realizations; the common 256 evaluation contexts are nested observations, not extra training n.
Report per-model and per-block effects and descriptive paired-context mean/normal-95%
intervals with sign counts. No pooled training-population interval, confirmation,
equivalence margin, best-checkpoint selection or result-dependent extra seeds.
If teacher-AF does not recur on this fresh panel, retain that failure rather than declaring
student compression successful solely from student-teacher similarity.

### B01 fixed scientific contract

- Host: unchanged finite_model_decision_value B01 CrossingHost, H96, two agents,
  theta drawn uniformly from {.35,.55,.75,.95} per context and persistent through calibration
  and deployment. Jobs/clocks/receiver/channel/reward and sign/AF tie fallback unchanged.
  Four legal observed calibration displacements are public to both students and teacher;
  hidden theta and unsampled futures are environment/evaluation fields only.
- Teacher: P_k4_M32; JointPhysicalBelief per agent with the same four-point prior and
  calibration posterior, POSTERIOR_MEAN planning with 32 particles, unchanged NEAR.
  Filter updates every consecutive tick from each actual local record, including under
  student roll-in. Query at most once per team tick, only available/unforced sender roots.
- Blocks: block0 seed 925941/model seed 926141; block1 seed 925942/model seed 926142.
  Calibration/environment/model phases 70/71/72. Context ids 0..255 are initial teacher
  trajectories; 256..383 are BC roll-in; 384..511 are WBC roll-in. This is 256+128+128
  complete trajectories per block. Separate context-indexed streams prevent action-dependent
  exogenous consumption. Both students receive the same complete merged labeled data.
- Evaluation: one fresh common 256-context panel, seed 925943/model seed 926143,
  calibration/environment/model phases 80/81/82, ids 0..255. Deploy four final students,
  P_k4_M32 and AF for 256 H96 episodes each. Teacher and AF are zero-new-policy-fit references.
  No teacher queries or shadow filter inside student evaluation; all optional imitation
  diagnostics use already purchased training/roll-in labels. Evaluation updates are zero.
- Student: shared linear input projection to 64 with tanh, one-layer GRU hidden64,
  one scalar send logit. Float32 CPU; private zero-reset memory for each agent/episode,
  advanced every tick, full-H96 training unroll, no truncated/detached within-episode replay.
  Fixed 35 inputs from LocalRecord: three payload encodings (own, last sent, received raw
  peer packet; each stage one-hot3 plus distance/7, crossing time/4, remaining commitment/16,
  route); last-sent and peer-packet valid flags and raw timestamps/96; availability;
  t/96, frame/8, own12-clock/12, peer16-clock/16 phases (both public clock phases for either
  identity); agent identity; four observed calibration displacements. Invalid packet payloads
  are zeroed with explicit validity. No projected/current peer truth, belief vector, teacher
  delta, world id, true theta, shared hidden state or future input. Fixed scales, no fitted normalizer.
  Execute logit >= 0 at optional roots; keep forced/unavailable behavior in the unchanged host.
- Each block creates two identical initial state_dict copies from its block torch seed.
  BC and WBC each start one Adam optimizer (lr .001, defaults otherwise, no weight decay)
  and continue that optimizer and those parameters through both stages. Stage1: 40 epochs
  on 256 trajectories. One augmentation follows both stage1 endpoints. Stage2: 40 epochs
  on all 512 trajectories. Batch64 agent sequences (both agents are separate private sequences),
  same block/epoch permutation for both arms, no dropped/padded sequences; clip gradient norm1.
  This yields 320+640=960 optimizer updates per fit, 3,840 total. No scheduler or early stop.
- Loss only on true optional sender opportunities (not forced, unavailable or other-agent
  ticks); all ticks remain in recurrent input. BC is ordinary BCE-with-logits. WBC uses
  g=min(|teacher delta|/.25,4), w=.5+.5*(.1+g)/(.1+mean_stage(g)), where mean_stage
  is over the stage's complete eligible training set only. This preserves a positive
  ordinary term, mean weight1 and w=1 for all-zero g. Normalize minibatch weighted sums by
  eligible count, not sum of weights; no class rebalance or result-dependent scale search.
  Retain optional-root counts, zero/fallback/nonzero diagnostics and weight min/mean/max.
- Fixed batch16 for host/teacher evaluation and data collection. CPU one torch intra/inter-op
  thread and one BLAS/OpenMP thread; no fit parallelism inside this one admitted study.
  Execute all four fits even if the first block is adverse. Engineering fixtures use separate
  seeds/tiny horizons and are not outcome selection or scientific replicates.

### Cost and endpoint

Four started policy fits at the above two-stage horizon, with 98,304 unique collection
team ticks (shared data are not charged twice as new environment interaction), 147,456
evaluation team ticks, total245,760. Optimization exposure is separately 11,796,480
agent-sequence time rows across four fits (40*(512+1024)*96*4), including non-loss history
ticks. There are 1,280 four-step context calibrations =5,120 single-robot moves and
1,280 closed-form posterior fits; these are separate from policy fits and team ticks.
The conditionally bounded model work is (98,304+24,576)*32*2*32=251,658,240 branch
transitions; record actual roots, samples, branches and random draws. It excludes
filtering, model initialization, optimization, storage, transfer and readback.

Record each fit's parameter movement versus initial state, epoch loss/eligible accuracy,
updates and processed rows; save initial, stage1 and final checkpoints. Count initialization
as fit start before its first update and preserve partial failures. No automatic retry,
reinitialization, replacement world or post-result extension. A technical failure is not
a negative result and does not create an extra fit entitlement.

Measure collection/filter/query/feature/network/environment/optimization/I/O time, fit and
batch wall/CPU, single-process peak RSS and artifacts' bytes/hashes. Deployment boundaries
include policy construction/checkpoint load or teacher initialization, memory resets, lawful
features, filtering/planning when applicable, environment and recorded outputs. Report
shared calibration generation/posterior costs separately and attach the needed calibration
cost to each method's conditional total; AF has no calibration requirement. Native manifest
to exit and entry import/startup measurements supplement internal timers. Offline batched
cost is not online deadline latency, and shared-node timing is not an intrinsic speed guarantee.
Only if teacher deployment exceeds student deployment may a same-unit conditional amortization
count be shown; it never overrides task losses. No full support-effort total is invented.

Primary node is configured wsl_4070. Inputs must be committed/pushed and actual-node admission
must pass on the new tag `b01_bc_wbc_s925941_20260925`; no result launch is accepted yet.
Full outputs stay in durable node run storage plus a verified local copy; compact
config/summary/episodes/curves/native status are Git evidence, bulk arrays/checkpoints under raw/.

### B01 L0 — one bounded implementation

Deliver the fixed complete protocol above in
`experiments/candidates/planning_policy_compression/b01/`, entry
`scripts/run_ppc_b01.py`, focused tests under
`tests/experiments/candidates/planning_policy_compression/b01/`.
Reuse immutable finite-model host, belief and paired planner imports; do not edit those
sources or shared control code. The new calibration collector generates exactly four
moves with the existing addressed stream and verifies the prefix against the old collector.
Source metadata names the inherited finite-model asset and actual launch SHA.

Checks cover lawful feature boundaries, offline/online recurrence identity and resets,
teacher equality on a shared fixture, actual student-history shadow updates, eligibility
and AF ties, positive mean-one weights, same-data/init/order/update accounting, parameter
movement, zero teacher calls in student deployment, deterministic world/phase separation,
native-entry refusal before science, and a tiny complete two-stage/artifact fixture.
The independent Reviewer inspects numerics/RNG/replay/information and result identity.
Implementer owns only these three code/test paths, no notebook/index/Git writes, research
launch, Pro Send or children. DM reviews and accepts the diff; no extra science or tuning.
Stop only dependent work on a real semantic conflict; return it with facts and finish
independent parts. All fixtures own and clean scratch through pytest under temp/.

Pre-implementation arithmetic correction: the formula for optimizer time-row exposure
above evaluates to **23,592,960**, not 11,796,480. It counts both private agent histories;
the fixed dataset sizes, epochs, updates and team-transition prices are unchanged.

## 2026-09-25 — Independent prospective critique and current routing

The bounded ResearchCritic read the complete contract, inherited evidence and adopted
consultation; MATERIAL_DISSENT: no. I accept its useful clarification: WBC-BC identifies
weighting under the joint shared-collection procedure, not two independently collected
imitation algorithms. Weighted disagreement on these purchased labels is an in-sample
intermediate; final native deployment is its distinct usefulness test. A conditional
amortization calculation must keep the common collection/query cost and both students'
contribution to augmentation visible; it may not divide away inconvenient research cost.
No added arm, fit, rollout, evaluation panel or changed comparator follows this review.
The full prior Pro consultation remains the scientific advice used, not replaced by Critic.

Fresh main `b815b2b6bbf5a5f5176c2062384306b0b6bd5fa6` only updates assignment/routing
for this question: this session is `01a0db8e-361c-7b13-a086-3fe1303fa4b7` / local.
Question, controls and plan are unchanged. A read-only wsl_4070 observation found about
15.6GB MemAvailable and no result runner at that instant; this is preparation evidence,
not admission or a reservation. Actual execution will repeat native memory/source/policy
and duplicate checks. Implementation and independent engineering review are still pending.

## 2026-09-25 — Pre-execution instrumentation clarification

DM draft review identified an output-directory check that would reject the native kernel's
own manifest/logs before science; it is being corrected before any result launch. The fixed
block seed, optional-root action masks and completed/partial counters are checked against
the contract rather than inferred from a successful process exit.

To measure the stated imitation prediction with one fixed endpoint model, read each stage's
already purchased common data once with that stage's final parameters, no gradients or
queries: eligible disagreement, zero/AF-fallback disagreement, nonzero disagreement and
mean |estimated delta| times disagreement. This adds 589,824 forward-only agent time rows
across the eight stage/model reads, separately timed and counted; it changes no training
epoch, optimizer update, fit, environment sample or evaluation panel. Epoch losses remain
mixed-parameter training diagnostics and do not substitute for this endpoint diagnostic.
The comparison is still in-sample and uses approximate labels, not observed optimal regret.

Preserve existing query MC SE in training raw data and executed evaluation actions, rewards
and cumulative native metrics under raw/ so the final summaries have reconstructible
evidence. Teacher/AF evaluation must not execute unused student feature work; student
evaluation must not create or update a shadow filter. Record each fit's initialization
and each optimization stage's wall/CPU separately; elapsed time crossing the other arm
and common augmentation is not summed as exclusive fit occupancy. These are implementation
and measurement corrections before results, not a comparator or investment change.

## 2026-09-25 — B01 implementation accepted for exact-source publication

DM read the complete new model/study/entry and focused tests, and accepts the Implementer
diff. The only executable additions are the owned planning-compression B01 modules,
`scripts/run_ppc_b01.py` and mirrored tests. No inherited host, belief, planner or shared
control source changed. Reuse of B02's existing exact four-move collector avoids duplication;
its positions/latent-law draw agree with the B01 first-four-move prefix. The student has
27,329 parameters. Block seeds initialize it; canonical tensor-state hashes verify both
arms' initialization, separately from checkpoint-file hashes.

The independent Reviewer found three actual output/cost defects, all repaired before any
result launch: purchased supervision now persists per batch even if later training/query
fails; returned and stored batch wall/CPU share a trace-inclusive boundary; global episode
index serialization is outside per-method deployment timers. Each method writes equivalent
per-batch outputs inside its timer. Trace/cost/JSON overhead is retained in the full process
measurement, not called zero. Failed observed/feature/executed prefixes remain distinct.
The reviewer found no remaining material issue in lawful features, teacher fidelity,
actual-history filtering, recurrence, RNG/data/order matching, optimizer continuity,
update arithmetic or admission-before-science, and accepted the focused repairs.

Validation: the complete six-test suite passed after repairs (6.34s); independent focused
recheck passed the three affected tests (6.25s, three deselected), following an earlier
independent six-test pass. Tests include a distinct tiny two-block/two-stage fixture,
teacher action/delta/MC-SE agreement at every eligible fixture root, recurrent sequence
versus online replay, weights and real parameter updates, paired initialization, failure
prefix recovery, artifact/timing consistency, and unadmitted entry refusal. Scratch is
pytest-owned. No full-size fixture, selected endpoint, result launch or replacement seed
has occurred. Fixtures are engineering checks, not evidence for the scientific predictions.

Publish these exact inputs before execution. Use a dedicated source/output checkout on
configured wsl_4070 and the native launcher snapshot; the desktop worktree tool addresses
only the local host, so the remote checkout follows the configured remote Git preparation.
The source snapshot is disposable after terminal collection; the remote run directory and
verified local copy are durable evidence. Admission and accepted-handle observation are
the next actions; no second scientific permission or new Pro consultation is required.

## 2026-09-25 — B01 accepted native operation and detached observation

The fixed four-fit B01 is accepted. Its authoritative command, published source, fresh
control observation, output location and native identities are in the
[launch manifest](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/launch-manifest.json).
The [admission preflight](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/admission-preflight.json)
passed on the actual node with 15,287,214,080 available physical bytes against the
4,294,967,296-byte floor. The launch checked current pause/lead, published inputs and
duplicate claims. The [initial native status](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/native-status.initial.json)
at 02:58:20 UTC on September 26 records accepted admission, consistent records and matching
live runner/supervisor identities. The outer preparation supervisor's successful exit is
not a scientific endpoint. The runner-written
[configuration](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/config.json)
agrees with the fixed two-block, two-stage, four-fit contract; no result has been read.

Remote checkout preparation reported that historical commit
`e0b4af9d04f8a4a53368e3ca0055007c82141449` exists in the commit-graph but not in the object
database. Preparation nevertheless resolved and checked out the exact published source,
and native admission passed. This is a retained repository warning, not a claim that all
historical objects are intact; no history repair or object deletion was attempted.

Observe this accepted operation through the native status handle using `hmasd_wait.py`.
Completion, error or the bounded checkpoint returns control to this same session.
Reconcile uncertain observations against this handle; do not repeat the accepted launch.

## 2026-09-25 — B01 complete: partial compression and a bounded weighting increment

### Observation and evidence integrity

The [native terminal status](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/native-status.final.json)
has a valid exit-0 witness and consistent accepted identities. The scientific
[summary](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/summary.json)
is COMPLETE. DM collected all 445 remote files (13,752,909 bytes) and checked every size and
SHA256 against the remote copy; the independent Reviewer separately checked all 438
runner-listed artifacts. All 1,536 evaluation episodes reconcile with raw actions, rewards,
packet quotas and cumulative native endpoints. These are artifact checks, not new rollouts.
The independent ResearchCritic reconstructed all 66 contrast means/sign counts from
[per-context results](../../../../runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/per_context.json)
and found no material dissent from the bounded interpretation below.

Every comparison uses the same 256 evaluation contexts. Job/other-count totals below are
sums over those contexts; service is the mean completion fraction. Positive wait/conflict
differences are adverse. All policies send 6,144 packets in total under the fixed quota.

| Method | Completed jobs | Service | Wait ticks | Conflicts | Forced sends | Conditional deployment seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AF | 2930 | .817522 | 1657 | 35 | 817 | .356000 |
| P_k4_M32 | 2964 | .827009 | 1617 | 29 | 854 | 24.410637 |
| BC0 | 2935 | .818917 | 1619 | 35 | 821 | 1.029312 |
| WBC0 | 2952 | .823661 | 1641 | 30 | 823 | 1.025045 |
| BC1 | 2939 | .820033 | 1615 | 35 | 820 | 1.010725 |
| WBC1 | 2949 | .822824 | 1620 | 32 | 832 | 1.017006 |

| Contrast | Job total difference | Mean per context | Descriptive paired-context normal 95% | Positive / tied / negative contexts |
| --- | ---: | ---: | --- | --- |
| P_k4_M32 − AF | +34 | +.1328125 | [.076710, .188915] | 29 / 224 / 3 |
| BC0 − AF | +5 | +.0195313 | [.002546, .036516] | 5 / 251 / 0 |
| BC1 − AF | +9 | +.0351563 | [.007836, .062477] | 9 / 246 / 1 |
| WBC0 − AF | +22 | +.0859375 | [.039840, .132035] | 18 / 236 / 2 |
| WBC1 − AF | +19 | +.0742188 | [.031103, .117335] | 18 / 235 / 3 |
| WBC0 − BC0 | +17 | +.0664063 | [.023099, .109714] | 13 / 241 / 2 |
| WBC1 − BC1 | +10 | +.0390625 | [.005092, .073033] | 9 / 245 / 2 |
| BC0 − P_k4_M32 | −29 | −.1132813 | [−.165149, −.061414] | 3 / 228 / 25 |
| BC1 − P_k4_M32 | −25 | −.0976563 | [−.145291, −.050021] | 2 / 233 / 21 |
| WBC0 − P_k4_M32 | −12 | −.0468750 | [−.089887, −.003863] | 3 / 239 / 14 |
| WBC1 − P_k4_M32 | −15 | −.0585938 | [−.102071, −.015117] | 5 / 235 / 16 |

The teacher opportunity recurs on this fresh panel, but neither student fully preserves it.
WBC retains descriptively 22/34 and 19/34 of the observed teacher-minus-AF total gain;
these ratios are panel-dependent descriptions, not population retention guarantees.
BC retains a smaller positive amount. No model is selected as a winner for confirmation.
The two training blocks share a single evaluation panel; the 256 contexts do not multiply
training n. Five common contexts contribute +8 jobs to each WBC−BC total, so the two positive
totals are not independent replication over deployment panels.

Adverse completed-job contexts are retained in full in per_context.json. In particular,
WBC0−AF and WBC0−BC0 lose at 82/146; WBC1−AF loses at 82/146/178 and WBC1−BC1 at 82/178.
The teacher loses to AF at 146/158/168. WBC0/WBC1 lose to the teacher in 14/16 contexts;
BC0/BC1 in 25/21. WBC−BC reduces total conflicts by 5/3 but increases wait by 22/5 ticks.
WBC−teacher adds 1/3 conflicts and 24/3 wait ticks; this is not general dominance or a
tail-safety conclusion. Service differences track completed jobs with 14 jobs per context.

### Learning and measured computation

All four fits started and finished. Each checkpoint optimizer advances 0 → 320 → 960 steps;
total 3,840 updates and 23,592,960 optimization agent time rows. Initial tensors match within
blocks, differ across blocks, and all final models move (L2 BC0/WBC0/BC1/WBC1 =
16.345/18.102/16.286/17.462). Evaluation performs zero optimizer updates.

The final model diagnostics on the already purchased merged training data are:

| Model | Ordinary disagreement | Weighted disagreement | Nonzero-root disagreement | AF-send-fallback disagreement | Mean absolute estimated delta × disagreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| BC0 | .062969 | .107478 | .312005 | .002466 | .004837 |
| WBC0 | .068216 | .086397 | .240106 | .033072 | .002696 |
| BC1 | .065521 | .102431 | .311701 | .002246 | .004224 |
| WBC1 | .070763 | .089651 | .237627 | .027628 | .002797 |

Stage1 has the same directional weighted/nonzero improvement; complete diagnostics and
curves remain in the summary and curves.json. Final eligible roots are 17,342/17,170,
of which 14,310/14,119 have exact-zero estimated delta. Final-stage weights have mean1,
minimum .797021/.797110 and maximum 12.677849/11.938744. The ordinary positive term prevents
zero-label removal, but does not keep ordinary/AF agreement unchanged. Ordinary disagreement
rises about .52 percentage points; AF-send-fallback disagreement rises from about .25% to
3.31% and .22% to 2.76%. This diagnostic tradeoff must remain visible. These labels define
training, so their better weighted fit is an in-sample intermediate, not independent
evidence that true consequential errors caused the native gain.

Realized counts equal the fixed contract: 98,304 collection and 147,456 evaluation team
ticks; 1,280 calibrations / closed-form fits and 5,120 calibration moves; 589,824 diagnostic
forward-only agent rows. There were 43,641 queried roots, 35,881 exact-zero estimates and
7,760 nonzero estimates across collection and teacher evaluation. Actual model work was
56,848,192 branch transitions, below the 251,658,240 conditional bound. The 1,396,512 root
particles initialized 2,793,024 branch worlds and generated 268,130,304 advance and the same
number of job draws; initialization/draw counts are not extra executed environment ticks.

Shared collection cost 96.9624s wall / 99.0808s CPU, including 56.6543s filtering and
35.3913s querying. It is retained in full, not divided away between arms. All fit occupancy
(initialization, optimization and checkpoints; excluding shared collection) sums to 78.9467s;
optimization alone is 78.1100s. Per-fit wall times BC0/WBC0/BC1/WBC1 are
20.7842/19.4673/19.0832/19.6120s. The first initialization includes the optimizer's one-time
startup cost and is not a clean algorithm-speed comparison.

Scientific-process wall/CPU are 205.9909/210.0445s through artifact hashing, excluding final
summary writing; peak single-process RSS is 570,728,448 bytes (544.29 MiB).
Native acceptance to exit is 211.8647s. Calibration generation/posterior cost is
.029070/.001030s, endpoint diagnostics are separately timed, and entry import/startup is
.896508s. Engineering, remote preparation/transfer and DM/Pro reading are additional support
work; no complete support-effort total is inferred.

The deployment table includes setup/checkpoint loading, necessary shared calibration,
lawful features, environment, policy work and equivalent per-method output. Teacher filtering
and query time are 14.2958s/9.5792s. All 64 student evaluation batches have empty filter/model
counters and zero filter/query time. Students take about 24 times less measured batched
deployment time than this teacher, but about three times AF's cost. This is an offline
shared-node measurement, not online deadline latency or an intrinsic speed guarantee.
No claimed compute saving erases the observed loss of teacher completions.

Bulk data and checkpoints remain at
`hmasd-wsl-node:/home/wu/hmasd-worktrees/ppc-b01-sept25/runs/planning_policy_compression/b01_bc_wbc_s925941_20260925`
and in this authoring checkout at the corresponding runs path. Exact paths, bytes and hashes
are in the existing summary.artifacts; compact results are published with this notebook.
After verified collection, source-snapshot GC initially refused a protected process scan;
the explicit read-only sudo process scan then passed. Preview and apply reclaimed only
the terminal operation's disposable snapshot. The durable authoring/output checkout,
published branch, accepted claim, manifests, exit witness and all outputs remain.

### Explanation update and next decision

Strengthened: partial amortization is feasible in this small host, and the fixed WBC
procedure allocates imitation errors differently while yielding more completions than BC
in both observed training blocks. Weakened: ordinary BC is sufficient to retain the same
use at this exact budget; full teacher preservation by either current student. Untouched:
teacher optimality, sufficient recovery of belief by the GRU, the cause of the residual gap,
generalization to a different host or UAV, and a causal consequential-error mechanism.
Optimization/decision-boundary changes under this shared data distribution remain a strong
alternative to genuine prioritization of true decision consequences.

I accept the Critic's recommendation to retain the assets and prefer an unchanged prospective
independent repetition over a larger network, extra roll-ins or an expensive label audit.
Its proposed two-block fresh-panel exploration can test recurrence; five new independent
blocks would additionally allow a narrowly specified confirmation with an exact sign rule.
The choice between those investments and their actual claim requires focused Pro advice;
the prior first-batch consultation does not cover a new confirmation plan. B01 stays complete
with no extra fit, selected checkpoint, reused test result or resumed worker. The current
main background at `b815b2b6bbf5a5f5176c2062384306b0b6bd5fa6`, especially sections 2/4/8,
supports keeping information rights fixed and distinguishing finite learning/computation
tradeoffs from representation guarantees. A bounded section-4 background update follows
with this result; the original finite-model route remains archived.

## Pro question 2026-09-25 recurrence-or-confirmation

Conversation: new (private Jev account; shared records retain only the question key).

Question: B01 now gives partial compression and a consistent exploratory WBC increment.
Should we buy the proposed five-block unchanged confirmation, use only two new blocks and
a fresh common panel for exploratory recurrence, or end this small-host recipe's investment?
Criticize the actual narrow claim/test below, and choose the smallest worthwhile next
observation. This is a focused direction decision, not a new programme/Portfolio review.

Standing: the complete B01 result/update immediately above is the new evidence. In its
common 256-context panel, teacher−AF is +34 jobs; BC−AF +5/+9; WBC−AF +22/+19; WBC−BC
+17/+10; WBC−teacher −12/−15. WBC improves weighted/nonzero training-label agreement but
worsens ordinary and AF fallback agreement. Both blocks share deployment contexts, with
five common contexts contributing +8 jobs to each increment. Full student deployment is
about 1.01–1.03s versus teacher24.41s and AF.356s; shared collection96.96s, four fits78.95s,
scientific process205.99s. The retained losses and complete component vectors matter.
The independent ResearchCritic had no material dissent and favored unchanged recurrence
over repairing capacity/coverage; it did not evaluate the exact new claim note below.

DM leaning: this promising unchanged procedure deserves one bounded independent reading,
not more hyperparameter or teacher-budget search. Five new paired blocks permit a simple
exact sign rule at .05 without using context count as training n; a two-block recurrence
costs less but remains exploratory. The proposed sign claim deliberately concerns the
probability of a strictly positive training/evaluation-block effect, not expected gain,
teacher noninferiority or the causal mechanism. Is that estimand useful and honestly framed,
or should the finite claim and next investment be changed? A negative/inconclusive final
reading is acceptable. A larger network, more roll-ins, permutation-weight control or
UAV migration is not owed; recommend one only if it answers the live question better.

Actual proposed plan: [CLAIM_weighted_partial_compression.md](CLAIM_weighted_partial_compression.md),
currently a draft for this criticism and not selected/started. It specifies five new
independent training pairs and five fresh block-specific 256-context panels, matched B01
procedure, all comparisons and costs. Primary rule: all five WBC−BC completed-job means
strictly positive, exact one-sided binomial p=1/32; ties count nonpositive, no B01 pooling,
no automatic extra seeds. Report an exact lower bound for positive-block probability and
all magnitudes/other native readings. The distinction between a narrow recurrence claim,
expected native benefit, and compute/completion tradeoff is the central concern for advice.

Alternative two-block plan would reuse the same fixed B01 recipe with fresh training seeds
925951/925952, query seeds926151/926152 and one common fresh eval seed925961/model926161;
four fits and the same exposure as B01. It is an alternative proposal, not an accepted second
batch or a post-score option. Neither proposal has new training, environment steps or queries.

Context (paths marked source_sha resolve at the published question revision supplied in the
send; other revisions remain as stated):

- Current governance at source_sha: `docs/project/OPERATING_CONSTITUTION.md` sections1–5
  and7–8. Owner has authorized this independent direction's research; no pause applies here,
  while Claude FSD remains paused and G33 frozen. Three concurrent tracks is a ceiling;
  only one result-bearing study per DM. Pro advises, DM decides without renewed owner approval.
- Current methods at source_sha: `.agents/skills/hmasd-scientific-tools/SKILL.md`, sections
  Update the working explanation, Confirm a claim, Comparators and MARL information,
  Statistics, Cost and exposure. Constitution sets 3–5 fresh seeds/arm for confirmation,
  with an actual frozen claim, independent criticism, adequate uncertainty and all outcomes.
- Shared background: `docs/research/RESEARCH.md` sections2/4/8 at main
  `b815b2b6bbf5a5f5176c2062384306b0b6bd5fa6`. Finite history learning is distinct from
  information rights or representational guarantees; joint closed-loop effects and complete
  cost matter. This is scientific background, not a required belief. The B01 update above
  supplies newer evidence than that index snapshot.
- Evidence at source_sha: this notebook's complete B01 contract/result/interpretation,
  `runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/{config,summary,per_context,curves}.json`
  and the actual proposed claim file. The summary reports measurements and artifact hashes;
  it is not the raw tensors. Bulk trajectories/checkpoints are at the recorded node/local
  locations and have been checked by DM and Reviewer; do not claim you personally read them.
- Frozen executable meaning: original B01 code/entry at
  `a576d6b6c830d712703ae069f91f74a57485e264` under
  `experiments/candidates/planning_policy_compression/b01/` and `scripts/run_ppc_b01.py`.
  Inspect only if comparison/cost semantics require it. No source or result changes follow
  merely from this consultation.
- Applicable prior advice: `docs/research/archive/2026-09-25/RESEARCH-decision-learning-adopted.md`
  at source_sha, complete Answer's A discussion and Decision. It covered the first four-fit
  batch, positive ordinary term, normalized weights, shared roll-in, three comparisons and
  full costs; it did not cover this actual confirmation claim. Original finite-model B01/B02
  remain archived with their bounded +36/+32 ordinary-teacher asset and contrary evidence.
  No new literature or novel-method claim is needed to decide this focused investment.

Prospective cost: five-block option =10 fits, 245,760 collection+491,520 evaluation team
ticks, 15,360 calibration moves/3,840 closed-form fits, 9,600 updates and58,982,400 optimizer
rows; branch upper754,974,720. B01 component rates imply about ten scientific minutes,
plus implementation/review and readback. The alternative is4fits/245,760 total team ticks
and approximately the B01 scientific price, plus support. Actual-node admission remains
mandatory; neither estimate authorizes a launch or claims a reserved resource.

Constraints: no experiment, no approval gate and no edits outside the empty Answer below.
Write only that subsection on branch `codex/planning-policy-compression-sept25` in
`docs/research/candidates/planning_policy_compression/NOTES.md`. Read the immutable question
but fetch the latest target blob before writing and use its actual blob SHA. Preserve every
other byte, including the question and result, and stop on overlapping edits. On successful
write return the actual commit. If writing is unavailable, return the complete answer in
chat, not just a receipt/SHA/link. Do not disclose the private account/conversation address.

Return: evidence-grounded strengthened/weakened/untouched judgments, strongest alternative
to the proposed mechanism/claim, whether the next investment changes a useful judgment,
and one recommended decision with actual prospective scope/price. For the proposed exact
claim, reconstruct population, estimand, independence, selection/stopping and uncertainty;
state MATERIAL_DISSENT yes/no and the smallest necessary revision. Cite sources actually
read; state decision-critical gaps without inventing verification or a compulsory new test.

### Answer

**MATERIAL_DISSENT: no。**

**建议选择拟议的五个全新独立训练／评估区组，一次完成、按原规则结束；不先购买两块探索再决定是否补成五块，也不在此时结束这份小宿主配方的投入。**我同意的是：对已经出现的 WBC 增量作一次有边界的独立检验。不同意把检验成功解释成平均净收益、可靠部署、完整教师保留或“真实决策代价机制”已经成立。

拟议 claim 已经主动区分这些对象，主比较、平局处理和停止规则也相容，所以这里没有要求改变核心假说、对照或批次的实质异议。最小修订是把有限面板估计对象写成明确的 `q_256`，补上五块全正时实际能得到的概率下界及检验功效，并在最终结果中把“符号主张的判读”和“完整用途的判断”分开写。无需新增训练臂、门槛、审批或机制诊断。[实际拟议 claim][claim]

#### 一、B01 改变了什么判断，尚未改变什么

B01 同时提供了三个不能互相替代的观察。第一，普通教师在这个新面板上仍比 AF 多完成 34 个任务，故当前不是一个已经失去教师用途的压缩问题。第二，普通 BC 也有真实的有限用途：两份终点分别比 AF 多完成 5、9 个任务。第三，WBC 分别多完成 22、19 个，因而相对配对 BC 的增量为 17、10 个；但是相对教师仍少完成 12、15 个。所有数字来自同一个 256-context 面板，不是四个独立部署总体的估计。[B01 完整结果与解释更新][notes]；[原生汇总的 arms/contrasts][summary]

| B01 比较 | block 0 任务总差 | block 1 任务总差 | 应保留的解释 |
| --- | ---: | ---: | --- |
| BC − AF | +5 | +9 | 普通部分压缩本身有用，不因 WBC 较高而抹去 |
| WBC − AF | +22 | +19 | 学生不是仅仅退回 AF；仍只是当前面板的正例 |
| WBC − BC | +17 | +10 | 固定共同采集程序内的加权增量值得独立检验 |
| WBC − teacher | −12 | −15 | 压缩丢失了部分教师完成量，不能称完整保留 |
| WBC − BC：等待 ticks | +22 | +5 | 完成量增益伴随更多等待 |
| WBC − BC：冲突数 | −5 | −3 | 冲突改善与等待恶化同时存在 |

WBC−BC 的每 context 平均增量分别只有 .06640625、.0390625 个任务；正／平／负 context 数为 13／241／2、9／245／2。均值为正不等于大多数世界改善，大量平局也不能变成跨训练的精度。[原生 contrasts][summary]

教师 − AF 的 +34 是共享参照，不应在表中重复后当成两次教师复现。WBC 保留了本面板教师 − AF 增量的约 64.7%／55.9%，但分子、分母都受面板影响；这不是总体保留率或非劣效结论。WBC 相对教师还增加 24／3 个等待 ticks、1／3 次冲突。所有方法均发送 6,144 个包，因此这里没有消息数量节省。[summary 的完整分量][summary]

**加强的判断**是：这个有限历史网络可以实现有用的部分计算压缩；固定加权干预在两份已观察训练实现中带来额外完成量；继续原样检验比立即修补容量或标签更有根据。**削弱的判断**是：在这个预算下，普通 BC 已经保留了与 WBC 同样多的用途，或者任一当前学生完整保留了教师收益。这里没有削弱“普通 BC 值得保留”这一更弱判断。

**未解决的判断**包括训练／部署程序总体的平均增益、教师最优性、GRU 是否恢复充分信念、残余教师缺口的来源，以及其他宿主或 UAV 上的收益。当前背景关于合法信息、有限学习与表示保证的区分，正好要求把这些问题留开；B01 没有改变 actor 的信息权限，改变的是有限历史策略的学习及其部署计算。[指定背景 §§2/4/8][background]；[B01 合同与更新][notes]

反例不是脚注。WBC0 相对 AF／BC0 在 82、146 失利；WBC1 相对 AF 在 82、146、178 失利，相对 BC1 在 82、178 失利。教师自身在 146、158、168 不如 AF；WBC0／WBC1 分别在 14／16 个 context 不如教师；BC0／BC1 相对教师总差为 −29／−25，也分别有 25／21 个失利 context。直接查看的 context 82 中，AF、BC0、BC1 均完成 10 个，教师 11 个，两份 WBC 均为 9 个；context 146 中，AF 和 BC0 完成 7 个，教师及两份 WBC 只有 6 个。不存在逐世界占优或尾部无损的结论。[B01 损失清单][notes]；[逐 context 原始读数][contexts]

#### 二、最强的竞争解释：改变了有限学习的误差分配，不等于识别了真实后果机制

这不是“网络根本没学”的结果。汇总记录四次 fit 全部完成，每次优化器累计 960 次更新，参数均发生明显位移；评价没有优化器更新。曲线中的 epoch loss 是训练过程中不同参数的汇总，不是一个固定模型的部署曲线，也不能跨 BC／WBC 的不同损失目标直接比较绝对大小。[config][config]；[fits/counts/endpoint_diagnostics][summary]；[已读训练曲线][curves]

固定终点在共同训练数据上的诊断支持一个更有限的中间预测：WBC 的加权 disagreement 从 BC 的 .107478／.102431 降至 .086397／.089651，非零根 disagreement 也下降；与此同时普通 disagreement 变差，AF-send-fallback disagreement 从约 .25%／.22% 升至 3.31%／2.76%。这些都是已用于训练的近似标签，不能作为独立证据再次证明“重要错误减少导致了完整服务增益”。正的普通项防止零标签被删除，但并不保证零／回退行为不受影响。[终点诊断][summary]

我保留的最强替代解释是：**加权改变了这个有限模型在共同数据分布上的分类边界、梯度分配及优化路径；这些改变碰巧或有规律地更适合当前一组稀疏的闭环机会。**阶段均值为 1 去掉了一个粗糙的全局损失尺度差异，却不会使梯度方向、裁剪事件或 Adam 的状态相同。两份学生共同参与一次 roll-in，后续数据又受各自早期行为影响；因此得到的是这份共同采集程序内的加权总效应，而不是两个独立采集算法之间的比较，也不是任意部署成本下 WBC 的优势。[冻结学习／采集源码][study]；[claim 的比较范围][claim]

教师的有限 MC、NEAR 截断、AF continuation 和过滤近似仍在。对固定历史、固定后续策略的真实二动作优势，`|Delta| × 错选指示` 可以表达局部错选代价；这里使用的估值不满足把该量直接换成全团队闭环 regret 的条件。联合学生替换还改变后续访问、接收信息及相互作用。五块复现能削弱“仅旧训练实现和旧共同面板有利”的解释，不能分离真实后果语义、优化效应和近似教师偏差。这个机制未识别，不构成必须增加 permutation-weight 对照、更多 roll-in 或高预算标签审计的理由。[原 A 建议与 Decision][prior]；[当前固定合同][notes]

#### 三、重建实际确认对象：是有限面板程序的正号概率

令 `T` 表示一整个配对训练随机实现：初始化、校准／教师数据、教师 MC、排列顺序及固定的一次双学生共同补充。令 `E=(X_1,...,X_256)` 是独立于训练的全新部署面板。每个 `X_i` 包含固定 CrossingHost、H96、四点持久物理律及其合法校准和外生随机实现。定义

$$
D_{256}(T,E)=\frac{1}{256}\sum_{i=1}^{256}\left[C_{W(T)}(X_i)-C_{B(T)}(X_i)\right],\qquad
q_{256}=\Pr_{T,E}\{D_{256}(T,E)>0\}.
$$

主检验是 `H0: q_256 <= 1/2`，候选主张是 `q_256 > 1/2`。这与 draft 一致；把 256 显式写进符号只是避免以后不知不觉更换估计对象。[claim 的 unit/scope 与 endpoint][claim]

尤其要区分另外两个量：

$$
g(T)=\mathbb E_X[C_{W(T)}(X)-C_{B(T)}(X)],\qquad
\mu=\mathbb E_T[g(T)].
$$

`q_256` 既不是 `Pr_T{g(T)>0}`，也不是平均效应 `mu`，更不是随机单个 context 的胜率。它包含了每次只取 256 个部署 context 所产生的抽样变化与平局概率；换成 32 或 2,560 个 context，一般会得到另一个正号概率。这个对象可以回答“重做这份完整有限程序，更常得到正的面板增量吗”，不能回答“一个新训练策略的真实期望收益以多大概率为正”。以上是对固定合同的数学展开，不是额外实证发现。

**区组独立性是检验的实质条件。**五个区组必须分别有新训练实现和自己的新评估面板；每块内部让 BC/WBC 共享初始化、训练数据、排列和实际外生评价世界，正是合理的配对。固定架构和固定教师是共同常量，并不因此破坏区组独立性；同一块的两个 actor、256 个 context 和多个 checkpoint 却都不是额外独立训练单位。声明不同 seed 不能单独证明独立，须由实际随机流和数据复用方式实现。已读 B01 源码的按 seed/phase/context 寻址及块内共同排列，与这种配对语义相容；本次没有读取／验证新的五块运行器，不能把旧检查说成已经验证了新运行。[冻结源码][study]；[方法的 Statistics][methods]

B01 的两个训练实现共用一个随机评估面板；即使给定这个面板时训练实现可以独立，也不能把两个符号当成两个独立的训练／面板联合抽样。五个共同 context 各自合计贡献了两个增量中的 +8，第二块总增量只有 +10，面板集中性尤其值得保留。这不证明这些世界“造成了假阳性”，更不是删掉它们重算主结果的许可；它解释了为什么五份真正独立的新面板，比又一次共享面板更贴近当前待判断对象。[B01 完整更新][notes]

五块同时改变训练和部署抽样，因而仍不能把变动分解成“初始化原因”或“面板原因”。这不是设计错误，而是联合程序估计对象的边界；当前不需要为分解它另买交叉面板。

#### 四、精确检验正确，但其信息量必须按实际大小解释

设 `S` 是五块中 `D_256>0` 的块数。在上述独立同分布模型下，零假设边界的精确上尾概率为

$$
p(S)=\sum_{k=S}^{5}\binom{5}{k}2^{-5}.
$$

`S=5` 时为 .03125；`S=4` 时已经是 .1875，不能以“四块大胜、一块微负”改称通过。平局留在五块分母中，作为本项检验的非正结果；不要删除平局后另做 sign test，也不需要对块效应分布假设对称或正态。完成任务总差是整数，可按总差严格大于 0 判号，避免不必要的浮点容差。精确二项检验及 Clopper–Pearson 区间的性质可见 [R stats 官方说明][binom]；以下数字由固定公式直接计算，不是对未来成功率的预测。

最重要的量不是“5/5=100%”，而是全正时的单侧 95% 精确下界：

$$
L(5)=0.05^{1/5}=0.54928027.
$$

因此全正支持的是一个仍很宽的单侧区间 `[0.54928,1]`，不是 95% 的下一块成功保证。一般 `S>0` 时按 `Beta^{-1}(0.05; S,6-S)` 给出下界，`S=0` 时为 0。单侧选择须保持预先声明，不能与双侧 95% 区间混用；全正的双侧 95% 下界反而约为 .47818。

本规则的功效是 `q_256^5`。例如，**假设**真实 `q_256` 为 .70、.80、.90，五块通过概率分别只有 .16807、.32768、.59049。这些是操作特性，不是根据 B01 给出的主观成功概率。故未通过通常只能写“主张未确认”，不能写“已证明增量不复现”、`q_256<=.5`、无效或等价。一个有实质负值的区组当然是反证，但其效应大小及条件须另外陈述。

反过来，符号成功也不能建立正平均收益。一个纯数学反例是：重复区组的任务总差以 .9 概率为 +1、以 .1 概率为 −10；正号概率为 .9，平均总差却为 −.1。此例不是 B01 的分布拟合，只展示符号估计对象为什么看不见稀少的大损失。即使五个观测均值都正，五块样本均值也只有描述意义；这个检验没有给总体平均完成量或等待加权净效用提供分布无关下界。

我仍接受这项窄检验，因为本次有用的问题包含程序复现，而 draft 没有把它冒称期望效应检验。三块／四块全正的同类单侧 p 值为 .125／.0625，五块是在拟议 3–5 块范围内能让这个预定精确规则过 .05 的最小数目；**这是该规则的算术，不是“所有有价值观察至少五块”的一般原则。**功效和区间宽度也说明，这一批应被看作有边界的读数，而不是取得精确可靠性估计的便宜办法。

#### 五、选择、停止和完整用途必须继续隔离

B01、旧教师资产及当前结果后的方案选择属于开发曝光。使用这些结果选择 WBC 并不禁止一次新的前瞻确认；关键是把现在的程序、五块种子、面板生成、终点和检验固定下来，不把已读结果重新包装成确认样本。此处不复用最佳 B01 权重，不按诊断选 epoch，也不将发现块拼进五块。[claim 的 Selection exposure][claim]

具体保留 draft 的五组训练／初始化种子 925951–925955、训练查询／排列种子 926151–926155、评价种子 925961–925965、评价查询种子 926161–926165，以及原始 40+40 epochs、960 更新、同一合法特征／网络／教师／权重常数和一次共同 augmentation。每块最终 BC、WBC、教师、AF 在该块自己的 256 个 H96 世界上完整部署。[固定种子表和成本合同][claim]

不要先读两块再决定是否增加三块；题面两块共用一个面板的替代方案本来就不是五块方案的合法“前两块”。也不要在四正一负后加第六块，或在五块后临时以 pooled contexts、t 区间、保留率、等待分量中的某个阳性替代主检验。其他完整对照与分量必须报告，但只要它们保持背景性描述，就不需要为了所有描述性输出另造一套多重主检验。该单项 .05 也不是全项目所有选择的家族错误率保证。

技术失败则按原规定保留所有已开始 fit 和部分产物，记为不完整确认尝试；不能填零、删除后补种子，或者把失败解释成策略有害。无科学提前停止、无自动重试和追加，这些边界不因先读到一个负块而改变。[claim 的 Completion][claim]；[现行方法][methods]

最终建议明确写两段结果，而不是一个成功标签：第一段只按原规则判断 `q_256` 主张；第二段同时判断 BC−AF、WBC−AF、学生−教师、教师−AF、等待／冲突／包数、所有损失世界和完整成本。如果五块 WBC−BC 全正，但 WBC−AF 或教师机会没有重现，仍可以通过窄符号检验，却不能宣称有用的规划压缩已经确认。若增量极小或等待／局部损失不合算，也可以不采用 WBC。反之，WBC 增量没有确认，不会抹去 BC 或教师各自观察到的用途。

这里没有新增一个事后非劣效界、任务价格或联合显著性门槛。确认结论与使用／继续投入判断本来就是不同结论；后者要公开依据，不能偷偷改写前者。

#### 六、为什么选择五块，而不是两块或现在停止

**两块探索不是无价值的。**新训练加一个新共同面板，可以检查旧正模式是否在另一组条件下出现；若结果严重反转，会降低这份程序的吸引力。它的价格更低，也不必为了“不够确认”而否定它。但是它仍只有一个新的共享面板，在这里再次留下同一种部署抽样依赖；两块全正不能获得拟议总体的确认，也不能与 B01 合并追认为前瞻四块结果。

我选择五块的理由是，当前没有需要先通过探索来选定的新权重、网络、训练长度或教师预算。下一次最能改变方向判断的观察，已经是**这份现成有限程序的增量在独立训练和独立部署抽样下能否保留，并付出怎样的任务／计算代价**。五块直接购买这项判断；即使未确认，也给出五组完整效应而不是又留下“再复制两块”的默认诱因。这是信息价值和机会成本判断，不是已经计算出五块在任何支持成本下都最优。

**现在停止也有可辩护之处**：平均增量稀疏、教师缺口存在、等待变差，加权模仿本身又不是方法创新。但这些限制已经界定了可问的有限问题，并未使该问题失去价值。当前有实际学习、正的学生−AF 读数、同向 WBC−BC 和显著减少教师过滤／模拟的实现，而不是只有一个代理指标；在已有实现基础上，一次范围不扩张的独立批次比立刻放弃更值得选择。研究用途不要求先虚构部署客户，也不要求机制证明或 UAV 阳性。[B01 结果][notes]；[原 A 选择及适用边界][prior]；[方法的探索与解释更新][methods]

所以，**我建议的最小值得选择的完整下一批是五块固定方案**，不是先两块、不是附带修复、不是无限确认。结束这次批次与是否日后对一个不同问题投入，应分别判断；没有自动追加权利，也不把本配方的结局扩展为全部规划压缩问题的结局。

#### 七、实际价格与不能省略的成本

保持指定 wsl_4070、CPU float32、单 Torch／BLAS 线程、batch16 和单科学进程，不把十个 fits 理解为十路并行。实际节点准入仍按现行制度执行；下面的建议没有预留资源。[拟议执行范围][claim]

| 下一批方案 | 两块共同新面板探索 | 五块独立面板确认（推荐） |
| --- | ---: | ---: |
| 新策略 fits | 4 | 10 |
| 采集团队 ticks | 98,304 | 245,760 |
| 评价团队 ticks | 147,456 | 491,520 |
| 团队 ticks 合计 | 245,760 | 737,280 |
| 校准／闭式 fits | 1,280 | 3,840 |
| 四步校准移动数 | 5,120 | 15,360 |
| 优化器更新 | 3,840 | 9,600 |
| 优化 agent time rows | 23,592,960 | 58,982,400 |
| 终点诊断 forward rows | 589,824 | 1,474,560 |
| 条件模型分支上界 | 251,658,240 | 754,974,720 |

这些数值来自 B01 固定曝光和拟议五块合同的算术，不是已执行工作。五块相对两块增加 6 fits、491,520 个团队 ticks。不能把两种价格仅按 fit 数乘 2.5：教师／AF 在五个面板分别评价，相对 B01 的一个共享面板，其参照评价次数不同。[B01 合同及算术更正][notes]；[五块成本][claim]

B01 实际科学进程墙钟约 205.99s、CPU 210.04s，采集 96.96s、四次 fit 独占范围合计 78.95s；实际模型分支是 56,848,192，不是条件上界 251,658,240。五块按这些分项速率约为采集 242s、fit 197s、部署 134s，总计约 573s，另有启动／输出工作；“约十个科学分钟”是同节点速率假设下的参考，**不是包含实施、审查、准备、转运、读回的全成本报价**。旧支持工作已经发生，不从记录中归零；新增支持成本尚未知。[B01 counts/resources/timing][summary]；[claim 的估价范围][claim]

尤其不能把“配方不变”写成“零工程”。冻结 B01 源码的校验要求恰好两块，`ARMS` 和部分工作计数固定为四个学生加两个参照；入口还拒绝不同于原 B01 的 seed。新方案需要有限的配置／组织／计数适配，才能真正实现每块独立面板。即便两块替代方案也不能直接把旧入口当成已接受的新运行。这里只指出已有源码的边界，没有实现、执行或宣称完成新运行器审查。[冻结 study.py][study]；[冻结入口][entry]

部署成本还要分清两个比较轴。学生约 1.01–1.03s，教师 24.41s，AF .356s，是既定离线批处理边界下的实测：压缩同时去掉了过滤和查询，而不只是把 planner 藏到别处；学生仍比 AF 慢约三倍。WBC 和 BC 是同样结构，B01 的毫秒级相对时间差不构成 WBC 更快的证据。**计算节省是学生对教师的比较，加权增量是 WBC 对 BC 的比较。**两者不能拼成“WBC 又更快又完整胜过所有参照”。[部署成本与零查询记录][summary]；[实际部署代码][study]

共同采集、教师打标签、两份 stage1 学生对 augmentation 的贡献都要留在账上；不能为了一个最终 WBC 实例，把 BC 的共同生产工作和离线教师工作删去。研究批次的十次训练成本与未来复用一个资产的边际成本也不能混成一个分母。当前没有部署次数、任务损失价格和完整支持报价，因此我不报数值摊销点或净经济收益。较少离线计算不会自动补偿少完成的任务、更多等待或单世界损失，也没有测出在线 deadline、能耗或真实部署安全。[原建议和固定成本边界][prior]；[B01 结果][notes]

#### 八、最小修订、来源边界与最终意见

我建议只在现有 claim／最终读法中补清三件事：明确 `q_256` 不是 `Pr_T{g(T)>0}`；写出全正下界 .54928 及低功效，使“不确认”的解释与检验能力相称；将固定符号结论和全向量用途判断分别陈述。draft 已含这些边界的大部分实质内容，因此这是落实其现有范围，不是要求换统计目标、设置新 MEI 或重做设计。原 seeds、十 fits、终点、严格正号、平局、无追加和技术失败规则全部保留。

本答复实际使用了固定问题／完整 B01 合同、结果和更新，实际拟议 claim，指定版本的 constitution、scientific-tools 和 RESEARCH 相关章节，以及归档 Answer 的完整 A 讨论和 Decision。数值核对使用了指定 config、summary 的科学计数／各臂对照／诊断／fit／成本段，curves 的训练记录和 per_context 的具体反例；为比较与工程成本语义，另读了指定执行 SHA 的 study.py 相关流程及完整入口。没有用移动 main 或聊天记忆替代这些输入。[治理 §§1–5、7–8][constitution]；[适用方法][methods]

**没有发现会阻断本次方向建议的关键文本访问缺口。**但我没有读取节点上的 bulk 轨迹／checkpoint 张量，没有重算全部 256 个世界或独立验证所有 438 项制品哈希；DM／Reviewer 的完整核验是已读 notebook 的报告，不是我的新核验。本次固定输入中没有新批次的已验证独立性实现、实测节点成本和最终结果，新增实施／支持工作的完整价格未知。这些限制不能被成功读取 summary 所替代；这里的建议不依赖假装已经完成这些工作。

**最终意见：五个全新独立训练／评估区组，原配方一次固定读完。**它能把当前有用但面板依赖的正例推进为一个诚实、有限的复现判断；无论符号是否通过，都保留普通 BC、教师、全部反例、教师缺口和等待／计算代价。此意见不授予预算或执行许可，也不创建新的审批；具体科学选择由 DM 按现行治理承担。

[notes]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/docs/research/candidates/planning_policy_compression/NOTES.md
[claim]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/docs/research/candidates/planning_policy_compression/CLAIM_weighted_partial_compression.md
[config]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/config.json
[summary]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/summary.json
[contexts]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/per_context.json
[curves]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/runs/planning_policy_compression/b01_bc_wbc_s925941_20260925/curves.json
[constitution]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/docs/project/OPERATING_CONSTITUTION.md
[methods]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/.agents/skills/hmasd-scientific-tools/SKILL.md
[background]: https://github.com/CartmanFatass/My-paper-code/blob/b815b2b6bbf5a5f5176c2062384306b0b6bd5fa6/docs/research/RESEARCH.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/ccad9a1b3cda9724288d098229c223d54a59d9f1/docs/research/archive/2026-09-25/RESEARCH-decision-learning-adopted.md
[study]: https://github.com/CartmanFatass/My-paper-code/blob/a576d6b6c830d712703ae069f91f74a57485e264/experiments/candidates/planning_policy_compression/b01/study.py
[entry]: https://github.com/CartmanFatass/My-paper-code/blob/a576d6b6c830d712703ae069f91f74a57485e264/scripts/run_ppc_b01.py
[binom]: https://www.stat.ethz.ch/R-manual/R-devel/library/stats/html/binom.test.html

## 2026-09-25 — Adopt the complete advice and freeze B02 independent confirmation

Question key `hmasd:d905518fb3a154e759f9740a4da1004c9804203457897d8cf0578bf458e12582`
was sent exactly once after a genuine pre-send missing-control check; the same-key read-only
page check found the control and the unchanged request was accepted at verified 6 Pro.
The observer collected a 263-character receipt, not the answer. Delivery verification found
`af90be1e9e2bd06816e63ec64ce38e6ad740031f`: one commit, only this file, only the originally
empty Answer, 164 added lines / 12,213 answer characters, question and all other bytes intact.
An initial delivery selector omitted the literal `##` prefix; correcting that read selector
verified the same operation/commit without another Send. I read the entire answer above.
The observer closed its owned tab; the terminal event is consumed and no Pro request remains.

MATERIAL_DISSENT: no. I adopt five completely new paired training/evaluation blocks, in one
fixed B02, over another two-block shared-panel exploration or ending this recipe now. The
reason is the already observed native/computation tradeoff, the absence of a remaining
hyperparameter choice, and the value of independent deployment panels after B01's common
panel. Ten new fits at the unchanged horizon are justified by this question, not by a fit
allowance or an obligation to confirm. B01 is development exposure and never enters the test.

Adopt the precise `q_256` interpretation and power caveat. Five positive integer job-total
differences give exact one-sided p=.03125 and a .54928027 lower95 bound, not reliable-deployment
certainty. Four positives do not pass; ties count nonpositive. I checked the published
[R exact-binomial documentation](https://www.stat.ethz.ch/R-manual/R-devel/library/stats/html/binom.test.html)
and the finite formulas. q_256 is neither probability of a positive true expected return for
a trained policy nor a mean-effect claim. Report one fixed sign verdict and a separate
complete-use judgment including magnitude, all other comparators, waiting, conflicts and
losses. Negative/incomplete/non-confirming outcomes remain useful and cause no automatic
replacement or extension. Advice is not new empirical evidence or execution acceptance.

The [claim note](CLAIM_weighted_partial_compression.md) now freezes this selected scope,
five seed tuples, 40+40 epochs, all comparisons, count/cost bounds and stopping rule.
Its only post-advice clarification is q_256's explicit definition, integer sign handling,
finite power/lower-bound examples and the separation of verdict from usefulness. No arm,
world, fit or scientific threshold was added. The original proposed section and complete
advice remain above, including the unselected two-block alternative.

Current main `ab628a57b` contains the B01 standing and relevant section-4 update; pause/lead
are unchanged. The shared background concretely keeps B02 on unchanged legal history and
finite learning/computation: it supplies no sufficiency, causal or UAV guarantee. Sections2/8
remain applicable without a new mechanism audit. I retain Pro's limitations on unseen raw
data and unimplemented B02 independence, rather than treating its source reading as runtime
verification. No further consultation is needed for implementation and this fixed execution.

### B02 L0 — adapt orchestration, preserve B01 science

Implement only `experiments/candidates/planning_policy_compression/b02/`,
`scripts/run_ppc_b02.py`, and mirrored B02 tests. Read the frozen claim and B01 scientific
functions first. Reuse B01 Student, features, episode/label semantics, calibration,
train_stage, diagnostics and state/artifact helpers directly where suitable. Leave B01,
finite-model assets and shared control code unchanged; no alternative architecture or
configurable scientific sweep. The new entry admits before scientific imports and fixes
seed925951 plus the exact launch SHA/output tag `b02_confirm_s925951_20260925`.

Replace the two-block/common-panel organization with five fresh block tuples and each
block's own evaluation panel. Preserve private recurrent resets, common within-block init,
same stage data/permutations, one optimizer per fit continued across stages, actual-history
shadow labels and zero shadow work in student evaluation. Store independent calibration
and checkpoint evidence with block-qualified paths so no block overwrites another. No
full-size result fixture before source publication/admission.

Maintain all B01 measurement/recovery guarantees: raw supervision per collected batch,
actual executed action/reward/cumulative trajectories, distinct partial observed/feature/
executed counts, initial/stage1/final checkpoints, per-fit timing and movement, curves,
endpoint diagnostics and equivalent full deployment boundaries. Collect 245,760 and evaluate
491,520 team ticks; 10 started/completed fits, 9,600 updates, 58,982,400 optimizer rows,
1,474,560 diagnostic forward rows, 3,840 calibrations / 15,360 moves. Upper model-branch
bound754,974,720; count actual work. Preserve partial failure with no automatic retry.

Summary exposes all five integer total differences, signed means, every comparator/native
component and loss world by block. Read q_256 using exact binomial upper-tail at .5 and
one-sided95 Clopper–Pearson lower bound; incomplete batches do not report a completed
confirmation decision. Report descriptive mean/range separately. Do not pool contexts or
quote a sign-test lower bound on mean native benefit. Report costs per block/method and
whole study without allocating away shared collection or BC roll-in work.

Focused tests: tiny distinct-data five-block fixture, real parameter updates and optimizer
continuity, distinct block calibration/eval streams plus within-block matching, complete
counts/output hashes, zero student queries, all sign/tie decision branches and exact known
probabilities, partial failure preservation and admission refusal. Existing B01 checks cover
unchanged teacher/feature semantics; do not redo full mechanism validation. Scientific
fixtures are tests and never confirmation observations. Independent engineering Reviewer
checks the new RNG/block/evaluation and inference accounting; DM accepts the full diff.
Implementer owns only those code/test paths, no NOTES/claim/index/Git, Pro, children or launch.

## 2026-09-25 — B02 engineering accepted for the frozen confirmation

I read and accept the complete B02 orchestration, admitted entry and focused tests, including
the final partial-cost repair. Independent Reviewer found one material recovery issue:
a later evaluation-arm failure could omit the completed BC/WBC full deployment boundaries
from the FAILED summary. The repaired live block timing preserves each completed method's
setup, deployment and attached calibration cost; the failed arm records measured attempted
cost and executed trace prefix without a completed-method claim or formal verdict.

Implementer reports five focused tests passed in 12.51s and py_compile passed. Reviewer
independently passed sign/admission checks (2) and the repaired later-arm failure regression
(1), and found no remaining material issue. Its independent finite binomial/CP arithmetic
agrees for all six positive-block counts. Checks cover five distinct training/evaluation
blocks, within-block pairing, optimizer continuation, fixed work accounting, zero student
queries and failure preservation. Fixtures are not research observations. B01 policy,
teacher, features and shared launch/admission source remain byte-identical to the accepted
B01 source; only the three scoped B02 code/test files and this notebook are added here.

Fresh origin/main is `1e6bb2b6cb379301edbbafd3632381becd3a04e6`: owner pause remains lifted,
this direction is confirming under the same independent Codex DM, and Claude FSD remains
paused. This scientific batch and ten-fit cost remain exactly as the claim above. Publish
this accepted implementation before requesting one native B02 launch; use the existing
remote author/output checkout and a new exact-SHA source snapshot, preserving B01 outputs.
Native admission and actual-node resource checks still precede result execution. No B02
result-bearing attempt has started at this acceptance boundary.

## 2026-09-25 — B02 accepted; fixed confirmation in progress

The [native manifest](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/launch-manifest.json)
binds the single accepted B02 request to the published implementation and retained source
snapshot. Its [initial native status](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/native-status-initial.json)
agrees on admission and live supervisor/runner identities; the
[actual-node preflight](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/admission-preflight.json)
passed. The copied [configuration](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/config.json)
matches all five frozen seed tuples, 40+40 epochs, CPU float32, batch16 and one-thread settings.
Training has begun; the initial status is a historical progress sample, not an endpoint.
The outer configured supervisor's exit zero acknowledges admission only. No scientific
acceptance or primary verdict is recorded while the batch is running.

Execution preparation synchronized only this direction's remote runtime state field from
exploring to the published confirming value; all other remote control text and its index
were preserved. The local canonical checkout/index was untouched. The first control-text
read stalled on a missing partial-clone object without the configured network environment.
Only its owned Git fetch was terminated; the helper then failed before writing or launching.
The configured network shell fetched the same published text and completed the narrow sync.
Existing remote auto-GC warnings about missing historical tree
`9e40125ee3e24973b69754649226d18847b45862` remain unrepaired; this is not a repository-wide
integrity claim. The requested source snapshot and published control were subsequently
accepted by the native kernel. This support episode started zero scientific fits and did
not repeat an accepted scientific request.

Observe the accepted operation with the task-local repository controller, keeping the same
handle through checkpoints or errors. Read every final native artifact, preserve and verify
the raw outputs, then apply the prewritten sign rule and separately judge complete utility
and cost. No early score-based change, replacement seed or automatic extension is permitted.

## 2026-09-25 — B02 complete: narrow recurrence confirmed with a persistent teacher gap

I accept the completed fixed batch after reading the config, summary, all comparison/component
vectors, per-context losses, all 800 curve rows, checkpoint/timing evidence and native terminal
records. The [prewritten claim](CLAIM_weighted_partial_compression.md) is unchanged above its
appended result. Source `443d392ec47a3e53652114d28084d48ce1e5d9e2`, same accepted operation;
no restart, replacement, early selection or extra seed. Native exit0 is supported by actual
complete scientific outputs, not used as their substitute.

**Recovery and engineering evidence.** All 1,342 remote files / 40,640,201 bytes were copied
and independently matched by size/SHA256. Reviewer separately verified all 1,335 runner-listed
artifacts and reconstructed all 5,120 deployment episodes from executed raw actions, rewards
and cumulative completions/wait/conflicts/packets. All contrasts and loss worlds reconcile.
Ten fit checkpoints show optimizer0→320→960, identical initial tensors within each pair,
distinct initializations across five blocks and nonzero movement. Each fit processed5,898,240
agent-time rows; all fixed seed tuples and calibration/step counts agree. All160 student
deployment batches have zero filter/model-query work; evaluation optimizer updates are zero.
Reviewer found no material inconsistency. This is stored-evidence verification, not new replay.
Native final status has a valid exit witness and consistent source/process identities; both
logs are empty. The terminal observation was consumed using its returned generation/wake/event.

**Fixed primary reading.** Blocks use training seeds925951–925955 and their own independent
fresh256-context evaluation panels925961–925965. Totals below are signed completed-job
differences over each whole panel; P is the same approximate P_k4_M32 teacher.

| Block | BC−AF | WBC−AF | WBC−BC | BC−P | WBC−P | P−AF | WBC−BC per context |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | +5 | +27 | +22 | −38 | −16 | +43 | +.08593750 |
| 1 | +6 | +17 | +11 | −31 | −20 | +37 | +.04296875 |
| 2 | +9 | +27 | +18 | −21 | −3 | +30 | +.07031250 |
| 3 | −1 | +15 | +16 | −28 | −12 | +27 | +.06250000 |
| 4 | +2 | +14 | +12 | −17 | −5 | +19 | +.04687500 |

All five integer WBC−BC signs are strictly positive, no ties. The prescribed exact one-sided
binomial test gives p=.03125 and one-sided95 CP lower bound .5492802716530589.
**CONFIRMED_NARROW_SIGN_CLAIM:** q_256>1/2 for the declared joint training-and-finite-panel
procedure. It is not the probability that a trained policy has a positive true expected return,
a lower bound on population mean gain, or a95% deployment reliability guarantee. The descriptive
mean is +15.8 jobs/panel (+.06171875/context), range +11..+22. B01 contributes no confirmation
unit; the1,280 contexts are nested observations, not n=1,280 independent training runs.

**Complete native use and contrary observations.** WBC−BC positive/zero/negative context
counts are18/237/1,15/234/7,16/238/2,12/242/2,14/237/5. Thus most contexts tie, and17 lose.
Loss contexts by block are0:{198};1:{91,128,149,150,153,191,205};2:{186,253};3:{48,139};
4:{18,55,69,119,188}. Block1/context128 loses2 jobs; all other WBC−BC losses are1.
WBC−AF loses3/7/2/3/6 contexts despite each positive panel total; its losses are
0:{13,198,226};1:{91,128,149,150,153,191,205};2:{186,253};3:{48,139,206};
4:{16,18,55,69,103,188}. The worst WBC−AF loss is2 jobs.
WBC−P loses14/19/6/16/14 contexts; block1/context147 loses3 jobs. BC−P also remains negative
in every block; BC−AF even totals−1 in block3. P−AF loses0/4/3/3/2 contexts. The full six
comparison loss lists, not just these selected examples, are retained in summary/per_context.

| Block | WBC−BC wait ticks | WBC−BC conflicts | WBC−P wait ticks | WBC−P conflicts | WBC−AF wait ticks |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | −56 | −4 | −38 | +7 | −126 |
| 1 | −56 | −2 | 0 | +7 | −89 |
| 2 | −95 | −4 | −57 | +1 | −114 |
| 3 | −78 | −5 | −26 | −2 | −92 |
| 4 | −30 | 0 | +10 | +3 | −51 |

All arms start3,584 jobs and send6,144 packets per panel. Service is the corresponding
completed-job fraction, not a separate success sample. WBC−BC forced packets are+28/+48/
+37/+60/+22 and delivered packets0/−2/+1/0/−1. Packet quantity is not reduced; delivery and
timing paths can differ under joint behavior. Full gate/disagreement/unknown/opportunity and
all other native components remain in the saved outputs. This does not diagnose a mediator.

**Intermediate learning prediction.** Every fit made960 actual updates and moved parameters;
the complete80-epoch curves are finite. Stage2 WBC weighted disagreement is.090434/.087987/
.080731/.084336/.097637, below paired BC .111067/.114744/.103529/.113449/.117487.
Nonzero-root disagreement is also lower in all five. Ordinary disagreement is higher in all
five by about.21–.70 percentage points, and AF-send-fallback disagreement rises from BC
.30–.68% to WBC3.09–4.18%. Stage1 has the same signs. These are in-sample approximate labels:
they support changed finite-learning error allocation, not independent validation of true
decision-consequence mediation. Mean1 weights do not match gradient direction or Adam history.

**Actual full cost.** Ten started/completed fits,245,760 collection+491,520 evaluation team
ticks;3,840 calibrations/closed-form fits,15,360 calibration moves;9,600 optimizer updates,
58,982,400 optimizer rows,1,474,560 endpoint-diagnostic forward rows. Actual model branches
172,410,112 remain below754,974,720 fixed upper bound. No new labels or environment queries
were purchased for endpoint diagnosis.

Scientific wall692.9198s, CPU709.7530s, single-process peak RSS608.625MiB; accepted-operation
elapsed712.7586s includes additional startup/terminal work. Entry import/startup is .9739s.
Shared collection batch wall291.3600s includes170.5404s filtering and105.6585s model queries.
Ten fit occupancy sums236.9011s, with236.2197s optimization; shared collection is excluded
from that fit subtotal and remains explicitly charged. Per-block BC/WBC fit walls are
24.5158/23.8803,23.7247/23.2480,23.6881/23.5189,23.6854/23.7238,23.3848/23.5312 seconds.

| Block | BC full deployment s | WBC full deployment s | P full deployment s | AF full deployment s |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1.195847 | 1.196081 | 29.036604 | .425690 |
| 1 | 1.222153 | 1.175882 | 28.846945 | .425352 |
| 2 | 1.240615 | 1.136311 | 28.841571 | .431386 |
| 3 | 1.178312 | 1.183091 | 29.428420 | .398086 |
| 4 | 1.137267 | 1.154972 | 29.486527 | .434741 |

These are the same full offline batched boundaries including checkpoint setup, deployment
and method-required calibration, not online latency. Costs nested in these totals are not
summed twice. Students remove filtering/querying; they remain more costly than AF. WBC and BC
share the architecture; these timings do not support WBC being intrinsically faster than BC.
Both students' joint data production remains part of obtaining WBC, including BC roll-in and
teacher labeling. No full engineering/transport/readback effort total, amortization point,
energy or deployment-safety price is inferred from this scientific process measurement.

**Working explanation and next investment.** Relative to the B01 update and current published
main `1e6bb2b6cb379301edbbafd3632381becd3a04e6` sections2/4/8, five genuinely separate
training/panel realizations strengthen useful partial compression and the fixed weighting
increment. They weaken the explanation that the B01 positive merely depended on its two
training instances and one shared panel. The complete native gain remains small and sparse;
the teacher gap is not removed, and ordinary BC's panel gain is not uniformly positive.
This leaves finite-history sufficiency, residual capacity/data/optimization limitations,
teacher bias, causal consequence semantics and UAV transfer unresolved.

B01's WBC−BC waiting increase (+22/+5) **did not recur**: all five B02 wait totals decrease.
Preserve both observations; an unavoidable completion–waiting tradeoff is unsupported.
The surviving learning explanation is changed optimization/classification and closed-loop
visitation under approximate labels. The study does not distinguish that from a genuine
benefit of prioritizing true decision consequences. No permutation-weight or oracle audit
is silently added to obtain a mechanism claim.

ResearchCritic reports MATERIAL_DISSENT:no after checking all330 contrast means/sign counts
against per-context outputs. I agree with its bounded update and stopping rationale. The
complete Pro answer above already considered stopping versus this exact independent batch,
its all-positive reading, remaining teacher gap and absence of automatic continuation. I reuse
that reasoning for this prewritten outcome and bounded recipe completion; no premise, primary
claim or comparator is broadened and no fresh consultation is needed just to bless the result.

I end **current CrossingHost planning-compression investment**, preserving WBC, BC and the
approximate teacher as reusable assets. B02 answers the unresolved recurrence question selected
after B01. More unchanged blocks chiefly buy precision; the residual gap does not select
capacity, extra roll-in, weight retuning or higher teacher budget over competing explanations.
Such sweeps have no presently chosen discriminating prediction that warrants another batch.
Mechanism identification or native UAV transfer would ask different questions with different
comparators and costs, not automatically follow from this sign result. Shared evidence keeps
those questions open; the independent partner-exposure study has its own lead, and unselected
critic/message reserves do not oblige this DM to fill a runtime slot. This is a completed useful
finite comparison, not a negative verdict on all planning compression, an assertion of scientific
exhaustion, or a request for new approval. There is no active producer, open Pro question,
unread result or selected successor after publication.

Recovery: bulk raw traces, supervision, all30 checkpoints and logs remain at both
`hmasd-wsl-node:/home/wu/hmasd-worktrees/ppc-b01-sept25/runs/planning_policy_compression/b02_confirm_s925951_20260925`
and this authoring checkout's matching run path. Compact config/status/summary/curves/
per-context and native records are versioned; the7.85MB episode file with detailed send-clock/
peer counters remains alongside the bulk evidence outside Git, with its runner-listed hash.
The remote complete-file inventory was verified
locally; its private scratch SHA256 is
`1d3fb38d8069b60871ccb70d2d1c2f0edbf2537ff1c06aebc38b2d4361e9fd37`.
[Full summary](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/summary.json),
[all per-context outcomes](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/per_context.json),
[curves](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/curves.json),
[native terminal evidence](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/native-status-final.json).

After verified recovery, the native snapshot collector previewed and reclaimed only
`bcfd81ab82b341919c4f569088ca4a97`, with its read-only sudo process scan. Both output copies,
published source/ref, claim and terminal records remain. The durable author/output checkout
was not removed, and cleanup does not authorize another execution.

### Completion storage and checkout disposition

The final publication refresh found main `913df36e8e59eb77e06a82224580509e252903ba`, including
the owner's new worktree/data separation method. I applied it without changing the scientific
result or restarting an operation. Complete B01/B02 output copies now also live outside all
worktrees at `/home/fires/hmasd-artifacts/planning_policy_compression/<tag>/`:
B01 `b01_bc_wbc_s925941_20260925` has447 files/13,758,268 bytes;
B02 `b02_confirm_s925951_20260925` has1,344 files/40,645,572 bytes. Every copied file matches
its source size/SHA256. A separate verification using only each external summary and retained
files matched all438 B01 and1,335 B02 runner-listed artifacts. Extra files relative to the
remote counts are the locally collected native status records. Keep each whole tag directory
with its config, summary and native records for recovery; original remote copies remain.

All accepted operations are terminal, all Pro text has been delivered/read, and observer
generation6 has no pending event or active job. Source and result commits remain on the
published direction branch. This chat's native artifact list contains only the temporary
`ppc-publication` checkout, which has no scientific dependency after the final main push
and is to be natively archived then. The reused `fsd-a` checkout is not attached to this chat;
the current archive tool cannot retire it. Preserve that directory for retirement through
its actual owning task/tool; do not bypass the limitation with shell deletion or an App message.
Its required data is now independently recoverable outside the checkout.

## 2026-09-26 — Draft only: conditional history–weight correspondence on archived data

### Scope, independent review and unresolved project decision

This is the bounded design preparation assigned by the acting Root in the owner's current
research/workflow review: **0 new fits, 0 scientific evaluation steps, no implementation,
no Pro Send and no new review/agent**. Current main and origin/main were both
`723392de5fc6edbc62ce1ed025238429bad66e90` when refreshed. I read the updated constitution
section 2, the complete DM responsibility body and the [portfolio Decision](../../RESEARCH.md#decision).
The two old local authoring/publication checkouts are now absent; new authoring is on main.
The preceding storage/checkout descriptions remain historical observations. B01/B02 and their
frozen verdicts remain complete. This entry is a candidate draft, **not an accepted new batch**.

Reuse the completed independent Scientific Reviewer's reconstruction and Root's disposition;
do not substitute this DM's feasibility checks for independent direction review. The material
dissent in that Decision is preserved verbatim:

> **MATERIAL_DISSENT: yes。** 异议针对把DM缺陷当已证实成因、把权重对应上升为真实后果机制，以及
> 没有不同科学决策价值的续项投资；不反对PPC冻结判据或伙伴的有限结论。Root已采纳上述限缩，
> 保留所提候选排序供后续咨询和前瞻设计，
> 但新的科学投入仍待所需咨询和前瞻设计，不能把本次角色修订当运行许可。

In particular, convenient significance and a narrow claim do not by themselves show that
B02 was a mistaken investment: its separate panels answered a real recurrence question.
The project-level Pro consultation is still incomplete after the recorded pre-send HTTP403,
with `send_attempted=false`; it is Root's existing operation, not a request for this DM to
retry or substitute a consultation. I have no new material direction objection to preparing
this limited comparison. The data choice and accounting below are explicit draft details,
not a self-clearance of that unresolved scientific investment.

### Question and fixed material actually available

Conditional on one archived dataset D, does retaining the estimated-advantage weight's
correspondence with its particular legal history improve complete native jobs over shuffling
those weights while preserving each training-stage/teacher-action-label weight distribution?
The alternative is that this fine correspondence contributes little beyond the remaining
label-level weighting and changed finite optimization. Neither outcome identifies true
decision consequences or repairs an identified cause of the teacher gap.

The minimal draft fixes **B02 block0 for both new paired starts**; it does not give each start
a newly collected dataset. Block0 is the first recorded block, not a selected old checkpoint.
All B02 results were already development-exposed; this choice is not described as blinded or
as a representative sample of datasets. Conclusions condition on this single D. Block1 is
also readable and matches its original artifact hash, but is not another candidate to select
after seeing new results.

- Local retained input:
  `/home/fires/hmasd-artifacts/planning_policy_compression/b02_confirm_s925951_20260925/raw/block0_training.npz`.
- Existing configured-node input, independently read through SSH in this preparation:
  `hmasd-wsl-node:/home/wu/hmasd-worktrees/ppc-b01-sept25/runs/planning_policy_compression/b02_confirm_s925951_20260925/raw/block0_training.npz`.
- Both files are **1,041,468 bytes**, SHA256
  `eba65c4c17b49a18c6376628913feabac79dd38ba497e8003808d79ebadb55a4`, matching the original
  [summary.artifacts](../../../../runs/planning_policy_compression/b02_confirm_s925951_20260925/summary.json).
  The retained summary matches main byte-for-byte; its SHA256 is
  `5cd70493b54809fcb9a7a7c361f59baa75d50f4f99aabb62915c83b7fa3d7ada`.
- Producing source: `443d392ec47a3e53652114d28084d48ce1e5d9e2`, frozen B01 learning source
  `a576d6b6c830d712703ae069f91f74a57485e264`; original block train/query seeds925951/926151.
  Current main's PPC model/B01/B02 study and inherited finite-model B01/B02 code have no diff
  from that producing source. This is source availability, not verification of a future runner.

Read with `allow_pickle=False`: x is float32[1024,96,35]; y is float32[1024,96]; mask is
bool[1024,96]; delta and mc_se are float64[1024,96]; context/agent are int64[1024]. All numeric
arrays are finite and eligible y is binary. Context equals repeat(0..511,2), agent alternates
0/1. Thus stage1 is the 512 sequences with context<256; stage2 is all1024 sequences. Each
sequence is one private agent history, not another independent training realization.

The archived collector concatenated 256 teacher contexts, 128 old BC roll-in contexts and
128 old WBC roll-in contexts; labels were computed on those actual histories. The old BC and
WBC jointly determined the later data distribution. Both new arms receive this identical D,
including its old WBC-generated histories. There is **no new roll-in, teacher query, calibration
for training or label acquisition**. This tests conditional retraining, not the value of
weighting through a complete adaptive collection procedure. Old data acquisition remains sunk
exposure/cost; its absence from the incremental price does not make the complete method free.
See the [original assembly](../../../../experiments/candidates/planning_policy_compression/b02/study.py)
at lines266–321 and the fixed B01 contract above.

### Candidate intervention, matching and randomization

Two arms: O uses original WBC weights; S uses the stratified permutation. Both are newly
initialized and trained, not a new S compared with a selected old WBC checkpoint. Preserve
Student's35 lawful inputs, GRU64/27,329 parameters, private episode-reset memory, full H96
unroll, CPU float32, one Torch/BLAS thread, Adam(lr=.001, original defaults), gradient clip1,
batch64 agent sequences, and40+40 epochs with the same optimizer continuing across stages.
Final stage2 is the only deployment endpoint; no checkpoint, seed or permutation search.

For each stage s, compute the original float32 weight array using the existing
`stage_weights`: g=min(abs(delta)/.25,4) on eligible roots, then
w=.5+.5*(.1+g)/(.1+mean_stage(g)); weights outside mask are zero. Do not reuse stage2's
normalizer for stage1. For S, enumerate eligible positions in C-order separately for y=0
and y=1 **within that stage**, then assign the same weight multiset in a uniformly permuted
order. Here y is the saved teacher action target, not the action executed by the old roll-in.
Leave x, y, mask, delta, mc_se, context, agent and sequence/time order unchanged. In particular,
do not shuffle labels or stored deltas to obtain permuted weights.

Permutations may cross contexts, agents, ticks and collection sources within a label stratum;
there is no extra agent/source/zero-delta/time stratification. Consequently, the intervention
also removes weight associations with those variables, and a gain cannot distinguish their
optimization/difficulty effects from true consequence semantics. Preserve exactly each
stage/label float32 weight multiset and count, hence its mathematical sum and stage mean.
Check floating reductions with stated roundoff tolerance; permutation need not preserve a
floating summation's last bit. Retain the original mean-one normalization. Match eligibility,
ordinary positive term and loss denominator (eligible count, not weight sum). Matching weight
distributions does not match gradients, clipping, minibatch weight sums or Adam history.

Array inspection establishes that the permutation is not forced to be trivial:

| Archived stage | Sequences | Eligible roots | y=0 roots / distinct weights | y=1 roots / distinct weights |
| --- | ---: | ---: | ---: | ---: |
| teacher-only stage1 | 512 | 8951 | 3581 / 15 | 5370 / 25 |
| merged stage2 | 1024 | 17825 | 7141 / 20 | 10684 / 28 |

Within each pair, copy one newly initialized state_dict to O/S and use identical epoch
sequence permutations. Different pairs use distinct initializations, sequence-order streams,
S-permutation streams and fresh evaluation panels. Draft seed choices, not executed:

| Pair | Torch initialization | Training sequence-order seed | S weight-permutation seed | Evaluation world seed | Evaluation model-address seed |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 926001 | 926101 | 926201 | 926301 | 926401 |
| 1 | 926002 | 926102 | 926202 | 926302 | 926402 |

Retain training order addresses `[order_seed,90,pair,stage,epoch]`. For S use
`SeedSequence([weight_seed,91,stage,label])` with the declared NumPy generator; sample each
stage/label mapping once and reuse it through that stage's40 epochs. Stage2 gets its own
mapping over the merged data. Save mapping indices and hashes in the eventual runner outputs;
do not redraw a mapping to increase the fraction changed or obtain a better outcome. Identical
weights can remain unchanged after a valid shuffle. No permutation has been generated here.
These two starts vary initialization/order, S assignment and evaluation together; their
differences do not isolate any one source of variability. D remains fixed for both.

### Native endpoint, diagnostics and outcome implications

Each pair deploys O/S, both agents jointly replaced, on its own new common256-context panel
under unchanged CrossingHost H96, four-point persistent physical law and legal four-move
calibration. Use evaluation phases80/81/82, ids0..255, batch16 and matched addressed exogenous
streams. The model-address seed is retained for interface identity; student deployment must
have zero teacher queries/filtering/model branches and zero optimizer updates. Calibration
generation is shared within a panel, not counted twice as physical collection. No new AF,
teacher or old-model deployment is included in this minimum candidate.

Primary reading is O−S integer completed-job total and mean/context for each of the two pairs,
with absolute arm outcomes, descriptive mean across pairs and full per-context differences.
Retain service, waiting, conflicts, packets/forced sends and every adverse context. Two starts
are exploratory, not a new sign confirmation or adequate evidence of equivalence. Contexts
are nested observations; old B02 WBC/BC/teacher results are background, not newly paired controls.

At both stage endpoints, use the same saved stage data and **original** weight definition
for both arms' ordinary/weighted/nonzero/zero-fallback disagreement and mean abs(delta) times
disagreement. Their own training losses use different assignments and are not interchangeable
native outcomes. These diagnostics are in-sample approximate-label readings, not fresh labels
or an independent mechanism validation. Read the following possible outcomes separately:

1. **Native/diagnostic decoupling:** better original-weight disagreement without better jobs
   weakens that proxy's use for selecting a method. Native improvement without the predicted
   diagnostic improvement retains conditional usefulness while weakening the proposed mediator;
   neither warrants repairing the diagnostic merely to make it agree.
2. **O has a positive native advantage in both pairs:** retain a limited reason to preserve
   history–weight correspondence in this D/learner. This may motivate a separately chosen
   complete-use or transfer comparison, but proves neither true-regret semantics nor a novel
   algorithm. Magnitudes, losses and other native costs still determine whether it matters.
3. **S is similar or better in the observed native totals:** lower preference for investing in
   fine correspondence here. Similar observed values are not statistical equivalence. The
   result does not establish that generic weighting beats ordinary BC, or that weighting never
   helps in another dataset/collection procedure; those would require different comparisons.
4. **Mixed, small or imprecise readings:** retain the unresolved conditional observation and
   the full vector; do not add seeds, change strata or select a checkpoint after seeing scores.
   Any subsequent investment needs a different prospective reason tied to an actual decision,
   not a rescue of this draft's expected sign. Technical incompleteness is not one of these
   scientific outcomes; preserve all started fits/partial evidence with no automatic retry.

These are exploratory implications, not four new acceptance thresholds. There is no mandatory
mechanism proof or toy-positive gate before a separately worthwhile native UAV experiment.

### Verified incremental price, optional BC and remaining material gaps

The Reviewer's four core counts are correct for the specified shape:

| Quantity | Two-arm, two-start candidate | Arithmetic |
| --- | ---: | --- |
| New policy fits | 4 | 2 arms × 2 starts, each40+40 epochs |
| Optimizer updates | 3840 | 4 × 40 × (512/64 + 1024/64) |
| Optimization agent-time rows | 23592960 | 4 × 40 × (512+1024) × 96 |
| New evaluation team ticks | 98304 | 2 pairs × 2 arms × 256 × 96;1024 episodes |
| New training-collection ticks / teacher queries / model branches | 0 | archived supervision only |
| Evaluation calibration | 512 contexts / 2048 single-agent moves | 2 panels × 256 × 4 |
| Endpoint-diagnostic forward rows | 589824 | 4 fits × (512+1024) × 96 |

Reusing the existing calibration helper also computes512 closed-form calibration posteriors;
these are not policy fits and the student does not consume the posterior. Count their work
separately, or explicitly record an implementation choice to omit that unused computation;
the draft reuse price includes it. Calibration moves are outside the98304 team-tick subtotal.
No environment rollout, policy forward/update or new permutation occurred in this preparation.

The old B02 fit subtotal236.9011s/10 ×4 gives **94.7604s**, consistent with the Reviewer's
rough95s estimate. It is a historical-rate estimate for fitting, not a measured new batch or
complete wall-time quotation. Loading/checking fixed inputs, constructing mappings, diagnostics,
evaluation/calibration, initialization/output, native occupancy, implementation, review,
publication and readback have real costs; the full future wall time remains **unknown**.
Keep original acquisition exposure and these incremental costs distinct, not erased or doubled.

Ordinary BC is **not in the current minimum**. A third arm would be useful if the actual
decision became whether to discard fine correspondence *and* choose ordinary imitation versus
label-marginal weighting: O−S alone cannot decide that, and old BC is not a fresh comparator.
Adding a newly trained BC per start at the same horizon costs2 fits,1920 updates,11796480
optimization rows,49152 evaluation team ticks and294912 diagnostic forward rows, with no extra
panels/calibration when shared. Totals would be6 fits,5760 updates,35389440 rows,147456 evaluation
ticks and884736 diagnostic rows. No such third-arm decision or execution is made here.

Required training material and source are available locally and on the configured node; no
missing-label reconstruction or data-copy operation is needed for this draft. A new runner is
**not implemented**: the old entrypoints collect new data and hard-code B01/B02 organizations,
and `train_stage` recomputes weights internally without an explicit external-weight input.
A future bounded implementation would need archived stage loading, an explicit weight-array
path, saved stratified mappings and the two-pair evaluator, while preserving original data and
frozen runners. Its implementation/source checks, actual new input SHA and native admission
have not happened. This note does not call the old runner, create a new CLAIM or launch handle,
reactivate the direction table, or resolve the outstanding project consultation. Root retains
the investment decision and any material scientific disagreement; this publication changes
only the owned NOTES design preparation.

## 2026-09-26 — B03 selected: O/S/BC retraining on the fixed archive

### Scientific choice and fixed prospective reading

The owner's instruction to proceed through the independent DM is now embodied in Root's
[adoption](../../archive/2026-09-26/RESEARCH.md#root-adoption-20260926), published at
`3767786829e869f7ff09baa10deeca5a8d13499a`. I read the complete Pro Answer saved at
`725a485baf1337e0b538b6224ae1e3f9979c1817`, the independent Scientific Reviewer's substantive
opinion/dissent and Root's resolution. The earlier draft's pending-consultation status is
historical: that same project consultation is complete, with no new question or Send here.
Reuse this completed advice/review for implementation and the stated outcome branches.
Pro disclosed incomplete large-summary/node access; its advice is not a new raw-data audit.

**Select six fresh fits**, two paired starts with O, S and ordinary BC at each. The complete
draft above supplies the unchanged D, stages, model, RNG addresses, training and evaluation
contracts. This selected B03 adds its priced BC option prospectively; the draft remains intact.
BC uses unit weight at eligible roots and zero elsewhere, with the same data, initial tensors,
sequence batches, 40+40 epochs and continuous Adam state as O/S. Old BC/O checkpoints are not
comparators. This is exploration conditional on a single exposed D, not more B02 confirmation.

The shared background at this main revision, especially RESEARCH sections3/4 and the current
plan, changes the actual comparison: a fine-correspondence gain over S does not establish a
reason to choose weighting over competent ordinary BC. For each pair and native metric read
O−S, O−BC and S−BC with the arithmetic identity O−BC=(O−S)+(S−BC); they are not independent
replications. Retain absolute outcomes and every adverse world. Complete native jobs, service,
waiting, conflicts and packet/forced-send consequences remain distinct from label diagnostics.

Working conjecture: preserving the original history–weight alignment lowers original-weight
endpoint disagreement and improves native completions over S, while offering enough benefit
over fresh BC to retain the weighting complexity. Strong alternatives are S damage without
O−BC benefit, ordinary BC absorbing the useful behavior, or a generic reweighting advantage
without a clear fine-correspondence increment. These are predictions to test, not required signs.

Read both pairs' integer completed-job differences and magnitudes, descriptive mean/range,
native component vectors and loss lists. No formal sign confirmation or equivalence claim:
the two new pairs share the archived D, and contexts do not create more training replicates.
Use original stage weights for the **same** endpoint diagnostics in all three arms. Retain:

- O has useful native advantages over both S and BC: keep the conditional correspondence
  rationale; a next worthwhile comparison would concern complete compression use or a named
  new condition, not another same-D positive-sign confirmation.
- O/S are useful over BC while O−S is unclear or favors S: lower fine-correspondence priority;
  a simpler reweighting question may be useful, but an untested label-constant scheme is not
  thereby accepted.
- BC is at least as good in the actual observations: use ordinary BC as the next working
  reference and end current fine-correspondence additions; O>S alone is not adoption evidence.
- Native/diagnostic disagreement lowers the proxy or mediator explanation as applicable.
  Mixed, tiny or imprecise readings remain unresolved; no extra seed, changed D/strata,
  re-drawn mapping or selected checkpoint is added after seeing results. A new investment
  needs a concrete different scientific reason. Technical incompleteness is reported separately.

These are qualitative investment implications, not post-hoc thresholds. B01/B02 and their
contrary evidence stand. No new teacher/AF deployment is bought here, so there is no new paired
teacher-retention, net deployment-speed, full adaptive-collection or UAV claim. The earlier
material scientific dissent and Root's disposition remain preserved, not self-cleared by DM.

### Inputs, cost and execution boundary

Use only the draft's B02 block0 NPZ with SHA256
`eba65c4c17b49a18c6376628913feabac79dd38ba497e8003808d79ebadb55a4` and 1,041,468 bytes.
Its local/node availability has already been verified; the new runner still verifies the
actual bytes it loads and stages before any fit. O/S/BC all receive the same fixed teacher
prefix512 sequences and merged1024 sequences. S maps stay within training stage and saved
teacher-action label, sampled once per stage/pair and reused over epochs; no input, label,
mask, delta, identity or time order is reassigned. Diagnostic weights remain the original ones.

Keep the draft seed table unchanged: initialization926001/926002, sequence-order926101/926102,
S mapping926201/926202, evaluation926301/926302 and evaluation model address926401/926402.
PCG64 via NumPy default_rng/SeedSequence supplies the declared permutations. Horizon96,
35 features/GRU64, batch64 learning and batch16 deployment, CPU float32 and one Torch/BLAS
thread remain fixed. Evaluate all three final stage2 models on the two new256-context panels.

Price: **6 fits, 5760 optimizer updates, 35389440 optimization agent-time rows, 147456
evaluation team ticks, 884736 diagnostic forward rows**, plus2048 calibration moves and512
closed-form posterior computations from the reused helper. New training collection, teacher
queries and model branches are all zero. Fits continue across both40-epoch stages; no optimizer
restart or hidden fit. Count every started fit and preserve partial outputs/costs on failure.
The old rate estimate142.14066s covers fitting only; full new scientific/native/support wall
time is unknown and will not be substituted by that estimate. Measure actual input/mapping,
fit/diagnostic/calibration/deployment/I/O work, process wall/CPU and single-process peak RSS.

Configured node is wsl_4070, interpreter/supervisor from `.codex/hmasd-compute.toml`; prospective
output tag `b03_osbc_archived_s926001_20260926`. Publish exact accepted code/inputs before one
native launch with fresh resource/pause/lead admission. Source comes from main through the
native immutable snapshot; no new authoring/publication worktree. Observe the same accepted
handle with hmasd_wait. No scientific run is accepted at this prospective-writing boundary.

### B03 L0 — bounded archived-data runner

Deliver one archived-data study and admitted CLI under
`experiments/candidates/planning_policy_compression/b03/` (entry `run.py`) and focused tests
under `tests/experiments/candidates/planning_policy_compression/b03/`. These are the only
Implementer write paths. Root AGENTS/constitution's newer direction-entry rule prevails over
the older experiments/AGENTS scripts convention. Keep B01/B02, finite-model host and archive
bytes unchanged. Reuse Student/features, stage_weights, endpoint_diagnostic, calibration and
episode_batch where applicable; add a small explicit-weight training path without changing
the frozen train_stage. Do not build a sweep or modify shared admission/control code.

CLI validates the fixed seed, launch SHA and external data digest, calls require_admission
before scientific imports/input loading/model/output effects, and binds SHA to that admission.
Validate/parse the same input bytes, strict shapes/IDs/stage masks, then train O/S/BC afresh
with common initial tensors and sequence orders. Preserve explicit weight arrays/mapping
indices and their hashes, per-stage/label multiset checks, original versus shuffled identity,
all checkpoints/curves/updates/movement, common diagnostics, per-context native results and raw
executed traces. Summaries are compact readings plus hashes, not duplicated bulk arrays.
Failure output retains every started fit, partial stage/trace count and completed deployment
boundary; no missing endpoint is filled in or called a completed comparison.

Focused checks cover archive SHA/shape/stage rejection, O/BC agreement with the frozen small
training path, explicit S-weight gradient/loss behavior, stage/label mapping/reuse and input
immutability, paired initialization/order and optimizer continuity, diagnostic comparability,
new panel matching/zero student queries, three-contrast arithmetic and adverse-world retention,
partial failure recovery and unadmitted entry refusal. Use small distinct engineering fixtures
with pytest-owned scratch; never train on the production D or evaluate production seeds as a
test. Existing unchanged teacher/feature evidence is reused. Independent engineering Review
targets these new data/numerical/execution paths; no duplicate scientific consultation.
Implementer returns diff/checks/risks, no Git/index/NOTES writes, result launch, Pro or children.
DM accepts and publishes; a real material scientific disagreement stops only its dependent new
effect and stays in this notebook for Root's decision. Other authors' edits must be preserved.

### 2026-09-26 — implementation accepted for the selected B03

The bounded Implementer returned the new direction-local `b03/study.py`, admitted `b03/run.py`
and mirrored focused tests. I read the implementation and checks. Independent engineering
Reviewer `/root/review_b01` reviewed these paths against the fixed draft/L0 and found **no
material engineering finding**. It independently ran the seven focused tests (7 passed in
5.61s; Implementer final pass5.28s), verified the production archive read-only against its
declared hash/size and stage counts, and confirmed the unchanged B01/B02 helpers. These were
small engineering fixtures, not production-data learning or production-seed deployment.

Accept the explicit O/S/BC training path, fixed saved stage/label permutations, paired initial
tensors and epoch order, full-sequence recurrence and continuous Adam. Original-weight
diagnostics are read at each **stage endpoint** on that stage's data; only final stage2 models
are deployed. Review also covered common worlds/three-contrast arithmetic, raw/checkpoint
identity and partial optimizer/later-deployment failure retention. The fixed six-fit counts
match the selected note. Native admission and result execution remain pending at this entry.

Remote preparation retains D at the existing node archive path and uses the configured
canonical `/home/wu/projects/HMASD` as author/output root. This leaves D external to the new
native snapshot and avoids remapping an untracked archive into source. Materialized only the
published maintained launcher and compute config in that canonical checkout, and aligned its
owned PPC state from confirming to the published exploring value; its owner pause/lead and
other rows/edits were preserved. No authoring worktree, data copy, new Pro request or App
message was created. The maintained launcher includes the published snapshot/admission lock
repair. After committing/pushing these accepted inputs, invoke the configured supervisor and
native immutable-snapshot launch once, then retain and observe that same operation reference.

### 2026-09-26 — B03 native operation accepted; result reading pending

Published input SHA `04d746dcc0e6feff11204a10c7f0aed87f0d7926` was admitted on wsl_4070 at
2026-09-26T09:04:30Z. The [native manifest](../../../../runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/launch-manifest.json)
retains the exact command, immutable source, operation reference and process identities;
the [actual-node memory admission](../../../../runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/admission-preflight.json)
passed its configured floor. `agent-task` completed the launcher with exit0; the native
scientific child was independently observed **running**, with consistent records, at09:05:34Z.
This is technical launch acceptance, not scientific completion or acceptance.

The single durable bulk output remains
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/`.
Only the compact manifest/preflight were collected here. Task-local hmasd_wait now observes
that same native operation, with no duplicate launch, new Pro question or cross-task message.
On its terminal wake, read all results and adverse outcomes, verify the changed numerical
path against saved outputs, apply the fixed prospective reading, publish the owned results,
and reclaim only the exact inactive native source snapshot after evidence verification.

## 2026-09-26 — B03 complete: original correspondence helps on this fixed archive

### Complete evidence and native reading

The selected batch completed all six fresh fits and both final256-context panels at input
SHA `04d746dcc0e6feff11204a10c7f0aed87f0d7926`. Native exit0 and identities agree with the
accepted manifest. I read the complete compact result, all contrasts/loss lists, diagnostics,
fit movement and costs. Independent engineering verification found no material inconsistency:
all319 runner-listed artifacts match size/SHA256; the seven collected compact files match
their node originals; all1536 deployment episodes,96 batches, contrasts and loss lists
reconcile. The reviewer independently reconstructed the four weight maps and label-wise
multisets, and checked initial tensors, optimizer steps0→320→960 and positive movement.
Twelve endpoint diagnostics match an independent reduction over saved checkpoints/D;
maximum weighted-reduction difference3.43e-9 is reduction roundoff. No retraining or
environment replay was used for verification.

The [complete summary](../../../../runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/summary.json)
is219292 bytes, SHA256`cb80a2c465b756aaeb2621ee1fb918a202e471e398a6bd5ee9431250a94bcd35`.
The [config](../../../../runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/config.json)
binds the unchanged external archive, seeds, CPU float32, one-thread settings and model.
Full raw checkpoints, maps, calibration, curves and trajectories remain at the single durable
node output linked above:326 files,11307400 payload bytes at collection, with319 artifact
entries/11081666 bytes covered by the runner inventory. No bulk copy or replacement dataset
was made. All six final models moved from their paired starts (L2: pair0 O/S/BC
19.3052/16.8143/17.2369; pair1 17.7060/16.6949/16.3374).

| Pair | O jobs total / mean | S jobs total / mean | BC jobs total / mean |
| --- | --- | --- | --- |
| 0 | 2855 / 11.15234375 | 2843 / 11.10546875 | 2841 / 11.09765625 |
| 1 | 3014 / 11.77343750 | 3000 / 11.71875000 | 2997 / 11.70703125 |

The following component differences are totals across each256-context panel except service,
which is the mean ratio difference. Signs retain metric meaning; more forced packets or
unknown-gate ticks is not called an improvement.

| Pair / contrast | Jobs total (mean) | Positive / negative / tied worlds | Service mean | Wait ticks | Conflicts | Forced packets | Unknown gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 O−S | +12 (+.046875) | 13 / 4 / 239 | +.003348214 | −60 | 0 | +13 | +61 |
| 0 O−BC | +14 (+.0546875) | 15 / 4 / 237 | +.003906250 | −55 | 0 | +15 | +61 |
| 0 S−BC | +2 (+.0078125) | 2 / 0 / 254 | +.000558036 | +5 | 0 | +2 | 0 |
| 1 O−S | +14 (+.0546875) | 12 / 4 / 240 | +.003906250 | −40 | −5 | +41 | +67 |
| 1 O−BC | +17 (+.06640625) | 11 / 2 / 243 | +.004743304 | −17 | −8 | +42 | +73 |
| 1 S−BC | +3 (+.01171875) | 4 / 3 / 249 | +.000837054 | +23 | −3 | +1 | +6 |

All arms start14 jobs and send24 packets/context. Delivered packets are identical within
each pair (23.34375 and23.3046875/context); there is no packet-count saving. Gate disagreement
totals for O−S/O−BC/S−BC are−46/−41/+5 in pair0 and−42/−26/+16 in pair1; corresponding gate
opportunity differences are−48/−41/+7 and−36/−16/+20. The summary retains all absolute native
components and per-contrast extrema/conditional panel intervals. Those intervals do not turn
contexts into independent training units or establish a population training effect.

All completed-job loss worlds (context: difference) are retained:

- Pair0 O−S and O−BC:13:−1,138:−2,169:−1,200:−1; S−BC has none.
- Pair1 O−S:147:−2,157:−1,166:−1,220:−1; O−BC:166:−1,220:−1.
- Pair1 S−BC:79:−1,125:−1,208:−1.

Descriptive means across the two pair totals are O−S13, O−BC15.5 and S−BC2.5; ranges12–14,
14–17 and2–3. The arithmetic identity holds per world and panel. These are three related
contrasts, not three independent empirical replications. The two starts share one exposed D;
do not pool them with B02's five independent data/learning/panel units as a new sign test.

### Common diagnostics, cost and explanation update

All rates below use the same **original** stage weights/labels for each arm, irrespective of
its training objective. These are in-sample stage-endpoint readings, not an independent test
of the teacher's true consequences. `AF0` is disagreement on zero-delta AF-send fallback roots.

| Pair / stage / arm | Ordinary disagreement | Original-weight disagreement | Nonzero disagreement | AF0 disagreement | Mean abs(delta) × disagreement |
| --- | --- | --- | --- | --- | --- |
| 0 / 1 / O | .085354 | .112687 | .303323 | .043823 | .00388225 |
| 0 / 1 / S | .074740 | .121112 | .389728 | .003744 | .00532762 |
| 0 / 1 / BC | .074070 | .119770 | .389124 | .003083 | .00525779 |
| 0 / 2 / O | .070912 | .087393 | .228383 | .035938 | .00267882 |
| 0 / 2 / S | .069285 | .119097 | .363095 | .001539 | .00550666 |
| 0 / 2 / BC | .067209 | .114877 | .345865 | .002857 | .00528576 |
| 1 / 1 / O | .078762 | .101379 | .267069 | .033913 | .00335856 |
| 1 / 1 / S | .072394 | .115113 | .358912 | .002863 | .00497151 |
| 1 / 1 / BC | .072171 | .115871 | .369184 | .003083 | .00505181 |
| 1 / 2 / O | .076129 | .087903 | .208333 | .047368 | .00236851 |
| 1 / 2 / S | .067546 | .111482 | .315789 | .008902 | .00497195 |
| 1 / 2 / BC | .065245 | .108270 | .314536 | .006155 | .00485273 |

Stage1/2 have8951/17825 eligible roots,1655/3192 nonzero roots and4541/9099 AF0 roots.
The saved permutations changed2875/5610 assignments in pair0 and2923/5588 in pair1;
unchanged repeated weights are legitimate. Stage/label multisets and means are preserved
within float32 reduction tolerance. Neither map was redrawn based on these counts or scores.

Actual scientific cost is **6 started/completed fits,5760 updates,35389440 optimization
agent-time rows,147456 evaluation team ticks,884736 diagnostic rows**, plus512 shared
calibrations/2048 single-agent moves and512 closed-form posterior computations. New training
collection, teacher queries, model branches and evaluation updates are all zero. Each fit
has960 updates/5898240 optimization rows. Native admission-to-exit occupied127.154178s;
the scientific body through artifact hashing used121.035783s wall/125.082884s process CPU,
excluding final summary write. Entry imports/startup were1.371833s separately. Single-process
peak RSS was591347712 bytes; this is not a host-wide or simultaneous multi-process peak.

Fit-scope wall sums to113.953019s (initialization, both stages and checkpoint I/O), of which
optimization was113.084352s; the old142.14066s estimate is superseded by this measurement.
Shared input read/hash/parse-validation cost.000513/.000699/.027420s; mapping.010178s,
diagnostics.819819s, calibration generation/posterior.012286/.000678s, output writing.319533s
and artifact hashing.013552s have their recorded scopes/overlaps. Complete conditional
batched deployment including reload and attached shared calibration is O/S/BC
1.049367/1.000977/.965876s for pair0 and.980450/.984513/.963083s for pair1. Shared calibration
is attached to each standalone method reading but incurred once per panel in the physical
batch total. This is not an online latency or new teacher speed comparison.

Independent numerical verification added884736 forward-only rows, about1.03s for those
forwards/reductions, with0 fits/updates/environment transitions/queries. Engineering final
test passes were5.28s and5.61s on tiny fixtures; earlier implementation/review/publication
support wall time was not comprehensively metered. Keep those support costs outside the
scientific batch and do not call them zero. Old acquisition cost remains historical and is
neither erased from complete-method accounting nor charged again as new B03 collection.

**Strengthened:** in this D/learner/training schedule, preserving the original weight
correspondence has a useful, modest native increment over this label-stratified shuffle and
over fresh ordinary BC. Both predicted original-weight/nonzero diagnostic improvements
accompany native gains. S itself is slightly above BC in both panel totals, so these observations
are not explained solely by S falling below ordinary BC. The six-fit comparator changed the
method choice that an O−S-only result could not make: retain original weighting as a live
candidate for a complete-method comparison.

**Weakened/untouched:** ordinary training-label accuracy is not a sufficient method selector
here; O's ordinary and AF0 disagreements are worse despite its native gains. This does not
identify true consequence semantics or causal mediation: shuffle changes correspondence with
difficulty, source, time and finite optimization, and mean-one weights do not match gradients,
clipping or Adam exposure. Modest gains, many ties, all loss worlds and higher forced/unknown
counts matter. There is no new teacher/AF pairing, independent adaptive acquisition, new-D
replication or UAV measurement. B01/B02 and the fixed q_256 claim keep their original meaning.

Apply the already-read Pro/Root positive branch: no same-D sign confirmation, added seed,
redrawn mapping, changed D or chosen checkpoint. The next investment must answer a distinct
complete-use or named-condition question with its own prospective comparison. A focused
independent scientific reading of that choice is underway; it does not authorize another run
or repeat the completed B03 design consultation.

### Independent scientific reading, disposition and B03 lifecycle

Scientific Reviewer `/root/b03_scientific_reading` received its dedicated role and a fresh
context, without the DM/Root conversation. It reconstructed the fixed protocol, exact source,
compact results and stored node episodes/context evidence before the proponents' explanation
and Pro advice. The protocol itself contains prior reasoning; this was evidence-first reading,
not a claim of being unframed. Its substantive recommendation is to **retain O conditionally
and compare complete standalone acquisition–training–deployment next**, rather than extend
the same-D positive signs. It found no material dissent with the bounded interpretation.

The reviewer emphasizes O−BC's mean+.060546875 jobs/context (about.53% of BC completions),
mostly tied worlds and all losses. Original-weight/nonzero training disagreement falls while
ordinary/zero-delta disagreement rises. A strong simpler account is finite optimization
allocating errors toward useful approximate-teacher distinctions under the fixed receiver
rules. The S intervention also changes time/source/difficulty correspondence; neither it nor
the observed native gain validates Monte Carlo delta as true joint-deployment regret. The
finite-MC, posterior-mean, AF-continuation teacher remains an approximation. Parameters,
inputs and update counts do not equalize gradients or Adam trajectories. Higher forced/unknown
counts are consequences to retain, not independently established harms; identical packet and
delivery counts provide no communication saving. S-damage-only with BC absorbing all benefit
is weakened, while representation insufficiency and a repair for the teacher gap remain
unidentified. B02's five blocks and their teacher shortfalls keep their original scope.

The review identifies a concrete remaining dependency: B02's shared augmentation requires
both student policies to generate its D, and B03 inherits that D. It recommends two fresh
paired blocks, four fits, a common256-context teacher prefix and **256 own labeled roll-ins
per student**, then the same second40 epochs on prefix plus own data. Evaluate final O/BC,
teacher and AF together. This tests complete standalone procedures; it does not identify the
causal effect of sharing data relative to old batches. The discriminating prediction is O>BC
and O>AF in both blocks. BC≥O lowers weighting preference; both students≤AF lowers investment
in this specific use; mixed results remain unresolved without automatic extra blocks.

Its price is4 fits/3840 updates/23592960 optimization rows,147456 collection and196608
evaluation team ticks,589824 diagnostic rows,1536 distinct calibrations/6144 moves and a
conservative402653184 model-branch upper bound. Historical fitting/collection/deployment
estimates are about95/175/64s, not measured new wall time. Each standalone method must carry
its full necessary prefix acquisition, even where the experiment physically shares it.
Engineering, realized query costs, full wall time and any UAV comparison remain unresolved.
The reviewer has no material objection to this next comparison or the qualitative outcome
branches; it would object to semantic-mechanism claims or automatic expansion. Earlier
scientific dissent and Root's bounded disposition remain intact.

DM disposition: adopt this uncontested recommendation under the standing question delegation
and the completed Pro positive branch. Constitution§2 authorizes ordinary prospective
successors; this event itself supplies no new authority. No Root acknowledgment or new Pro
Send is needed. B03 is complete before selecting the distinct B04 below. The decision buys a
change in deployable-method choice, not more signs on the exposed archive or a capacity rescue.

After complete evidence verification, the maintained native snapshot GC reclaimed only B03
source `4769d18a1e88433d8c830d359513fc51`. Its ordinary process scan first refused a protected
`/proc/660/cwd`; the supported read-only sudo scan established no live consumer. Preview and
apply succeeded with a durable Git reference, and both the exact directory and worktree
registration are absent. Net allocated source-tree bytes reclaimed:793542656; Git object
storage change was not measured. The326 output files remain at the same durable node path,
with unchanged summary SHA and12079104 allocated bytes. No backup, raw-data copy or other
checkout deletion was made. The consumed terminal observation has no remaining active job.

## 2026-09-26 — B04 selected: standalone own-roll-in compression

### Question, prediction and fixed prospective reading

Select **two fresh paired data/learning/evaluation blocks, O versus ordinary BC, four fits**.
Can O's useful weighting increment survive when each deployable student acquires its own
augmentation histories, while retaining useful native performance relative to AF? The current
RESEARCH learning/representation background and B01–B03 evidence motivate this complete-use
question. Single-D B03 supports retaining O but cannot answer it; B02's joint acquisition is
not a standalone O or BC procedure. No claim of representation insufficiency, teacher repair,
true consequence semantics or UAV transfer is assumed.

Keep the CrossingHost, lawful private35-feature history, Linear64/tanh/GRU64/scalar student
(27329 parameters), teacher posterior-mean law with32 paired particles and AF continuation,
and frozen O weights/BC unit weights from B01. Within each block generate a fresh256-context
teacher prefix shared by both arms. Start identical parameter tensors, train40 epochs, collect
256 own labeled roll-in contexts per arm on matched exogenous worlds, and train another40
epochs on **the shared256 prefix plus that arm's own256**. Neither arm receives the other
student's histories or needs its fitted model as an acquisition dependency. There are no S,
extra teacher interventions or additional fits. Matched episode/model budgets do not promise
equal realized eligible-root/query counts; record each method's actual costs.

Deploy only final stage2 O/BC plus the unchanged teacher P_k4_M32 and AF on a fresh common
256-context panel per block. Read integer completed-job differences, signed means/magnitudes,
absolute native service/wait/conflict/packet/forced/unknown components and every loss world.
Primary decision contrasts are O−BC and O−AF, with BC−AF, O−P, BC−P and P−AF preserving full
use and teacher gaps. These are related comparisons, not six independent replications.
Two blocks remain exploration; no new formal claim, sign test, equivalence, expected-policy
dominance, break-even demand, online latency or UAV assertion. Do not pool these blocks with
B02 or use their difference from B02/B03 to identify a causal acquisition-sharing effect.

Prediction and consequence, fixed before data generation:

- O−BC>0 and O−AF>0 in both blocks supports retaining weighting for standalone partial
  compression, subject to the actual magnitude, adverse outcomes and acquisition cost.
- BC≥O weakens a reason to prefer weighting; retain BC as a useful simpler reference only
  where its own AF/full-cost comparison warrants it. Do not call mixed signs equivalence.
- Both students≤AF lowers investment in this particular compression procedure even if
  O>BC. Persistent teacher gaps remain losses, not a mandate for capacity or MC rescue.
- Mixed, small or imprecise outcomes remain bounded; no automatic third block, changed
  collection mixture, horizon, weight scale, seed or checkpoint after results. Any next
  investment must address a concretely different use/condition or end this recipe's additions.

Endpoint diagnostics use original weights at each stage on that arm's actual data. Stage1
uses common prefix data; **stage2 data differ across arms**, so stage2 rates are descriptive
own-training readings, not a matched common-D mechanism comparison. No added diagnostic set
or production rehearsal is purchased. Preserve ordinary, original-weight, nonzero, zero-AF,
all-zero and abs(delta)-weighted disagreement and all eligibility counts.

### Exact inputs, resource price and execution

| RNG purpose | Block0 | Block1 |
| --- | --- | --- |
| Initial tensors | 926501 | 926502 |
| Epoch sequence order | 926601 | 926602 |
| Collection exogenous worlds/calibration | 926701 | 926702 |
| Collection teacher model address | 926801 | 926802 |
| Evaluation exogenous worlds/calibration | 926901 | 926902 |
| Evaluation teacher model address | 927001 | 927002 |

Prefix context IDs0..255 use phases100/101/102 for calibration/world/MC respectively. Both
own roll-ins use IDs256..511 with phases110/111/112 and the same within-block exogenous
addresses/calibration. Histories/labels follow each actor's policy. Evaluation IDs0..255 use
phases120/121/122. Training permutations use NumPy default_rng/PCG64 SeedSequence
`[order_seed,90,block,stage,epoch]`, identical sequence-position order across arms; no hidden
shared-data substitution. Save separate prefix, O-roll-in, BC-roll-in and each merged dataset,
with provenance/context IDs and hashes, and initial/stage1/final model+Adam checkpoints.

H96, float32 CPU, one Torch/BLAS thread, batch16 collection/evaluation and batch64 full-sequence
learning, Adam lr.001 with default remaining parameters, gradient clip1,40+40 epochs and
continuous optimizer remain fixed. Each fit has320+640 updates and5898240 optimization rows.
Four fits total3840 updates/23592960 rows. Collection uses2×(256+256+256)×96=147456 team
ticks; evaluation uses2×4×256×96=196608. Eight stage-endpoint diagnostics use589824 rows.
Distinct calibration contexts are2×(256prefix+256shared-roll-in+256eval)=1536,6144 lawful
single-agent moves and1536 closed-form posterior fits. The conservative model-branch bound
is402653184; measure actual roots/particles/transitions rather than substitute this bound.

Track physical batch cost separately from per-method acquisition/training/deployment cost.
Each student is charged the **full** required shared teacher prefix acquisition and calibration,
its own labeled roll-in acquisition/calibration, its single fit and its evaluation/reload.
Sharing inside this paired experiment does not halve a standalone method's required prefix.
Teacher/AF have no student fit; retain their actual deployment and appropriate calibration
cost. No online break-even or wall dominance follows from offline batching. Save batch/root
counts, wall/CPU, I/O, peak single-process RSS and failure-time costs; support work is separate
and may be only partially metered. Prior~95s fits/~175s acquisition/~64s deployment are rough
historical estimates; new complete wall time is unknown.

Use configured wsl_4070 and native supervisor/admission with output tag
`b04_standalone_rollin_s926501_20260926`. Commit/push exact accepted inputs first, then one
admitted immutable-snapshot launch. Continue the main authoring checkout; no new authoring
branch/worktree. Retain accepted handles and use hmasd_wait; no automatic retry/resume after
failure and no launch/Send from a wake alone. Count all started fits, including partial ones.

### B04 L0 — bounded standalone-acquisition runner

Implement only `experiments/candidates/planning_policy_compression/b04/study.py`, `b04/run.py`
and focused tests under `tests/experiments/candidates/planning_policy_compression/b04/`.
Use unchanged B01 helper behavior and B02/B03 patterns where suitable; do not modify frozen
B01/B02/B03, shared host/teacher/learner helpers, other directions, records or Git/index.
This is one direction-local disposable orchestration, not a generic runner refactor.

The runner must enforce two blocks/two students, exact production addresses/counts, fresh
output, four deployment arms and no formal claim. Admission must bind direction/source/tag
and reject unadmitted execution. Keep dataset ownership explicit: common teacher prefix,
matched but separate own-policy roll-ins, separate merged training sets. Save shared
calibration once physically and attach required full cost to each standalone reading. Preserve
paired initialization/order and continuous Adam0→320→960, training movement and partial
optimizer state/trace costs after failure. Complete per-world native readings and all losses
must reconcile with raw episodes. All students have zero deployment teacher queries/filter
updates; P/AF retain their frozen behaviors. Existing teacher/feature evidence is reused.

Use small distinct pytest-owned fixtures to test data separation/provenance, matched world
addresses and shared calibration, frozen training/optimizer invariants, full rather than
halved standalone acquisition charges, exact accounting/contrasts, failure retention and
admission refusal. No production-seed/data training or evaluation as a test. Independent
engineering review targets the new data/RNG/cost orchestration and saved-evidence path.
Implementer returns diff/checks/risks; no science, result launch, Pro, children, record or Git
writes. It is not alone in the checkout and must preserve concurrent edits. DM accepts the
diff and publishes the precise inputs before execution. No result-bearing B04 work has
started at this prospective-writing boundary.

### 2026-09-26 — owner stops new experiments; finish current engineering and hand off

Owner instruction in this task: “当前正在执行的任务完成后就写handoff吧 不要开新实验了”.
At that instruction B03 was complete and published at `940a06014278f2a4295d2086d6a97cc65ddf99fd`;
B04 had only its already-assigned implementation/tiny-fixture checks in progress. No B04
native launch, accepted handle, scientific data generation, fit or deployment exists.
Therefore **do not launch B04 or select another experiment**. Finish that bounded engineering
task and its review, preserve the unexecuted code/prospective design, write the handoff here,
then stop. This is an owner-imposed hold, not scientific rejection or exhaustion of the question.
No further Pro request, cross-task message, replacement worker or research continuation is
authorized by this handoff. Global pause/other directions/FSD/G33 are not changed. PPC's own
standing becomes paused; a future status question, handoff read or workflow edit cannot resume it.

## 2026-09-26 — Handoff: owner hold, B03 published and B04 unlaunched

**接手时先读：本任务已按owner要求收尾停止，不开新实验。** B03结果完整；B04只完成了
指令到达前已经在做的实现及工程检查，从未启动。交接不构成恢复、移交负责人或联系其他任务
的授权。保留当前DM地址`01a0db8e-361c-7b13-a086-3fe1303fa4b7`/local与共享main工作区
`/home/fires/hmasd-wsl`；未创建新任务、authoring worktree或新的Pro问题。

### 已完成结果与可恢复证据

B01/B02/B03累计20次科学fit已完成、读取并发布。B03执行输入为
`04d746dcc0e6feff11204a10c7f0aed87f0d7926`，完整结果与下一方案前瞻发布于
`940a06014278f2a4295d2086d6a97cc65ddf99fd`；owner停止及PPC暂停发布于
`b1d8bcb73af5de85d39ad4e2d41c98521975a6fb`。当前交接提交另保存未执行B04代码与检查结论。

B03两配对O−S为+12/+14、O−BC +14/+17、S−BC +2/+3完成任务；六fit科学墙钟121.035783s。
它支持单一已曝光D上的有限权重对应增量，未识别真实后果语义、教师缺口原因或UAV用途。
原生损失世界、普通/零delta分歧变差、更多强制发送/unknown-gate及全部成本已完整保留在上文。
旧B02五新区组q_256确认及所有教师缺口保持原义，不能与B03合并成新的训练重复。

- Git中的紧凑结果和原生操作记录：
  `runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/`。
- 唯一完整B03 raw位置：
  `hmasd-wsl-node:/home/wu/projects/HMASD/runs/planning_policy_compression/b03_osbc_archived_s926001_20260926/`。
  319项清单及326个文件已核验；summary SHA256
  `cb80a2c465b756aaeb2621ee1fb918a202e471e398a6bd5ee9431250a94bcd35`。
  该目录不是源码快照，不删除、不重复拷贝。
- 原生manifest保留准确operation reference；exit0已与完整科学输出分别核对。
  不需要恢复、重启或重跑B03。其闲置source snapshot已按维护工具回收，净释放793542656
  allocated bytes；输出与claim仍保留。
- B03的外部固定D仍在既有B02归档，SHA256
  `eba65c4c17b49a18c6376628913feabac79dd38ba497e8003808d79ebadb55a4`；B04本来需要新采集，
  不使用该D替代自己的未执行采集。

### 当前工程已完成，B04没有科学结果

DM读取并接受Implementer的限定差异；独立Engineering Reviewer`/root/review_b01`检查新增
数据流/RNG/成本/失败保全及CLI，报告**无实质工程问题**。冻结B01/B02/B03和共享helper未改。
两臂实际stage2输入各自拥有roll-in；匹配世界/校准、共同初始化/批序、Adam连续性、四臂部署、
学生零查询/过滤、来源哈希与部分失败保全已检查。单方法完整承担教师前缀；分项耗时明确不含
数据拼接/整理、部分I/O/hash与支持工作，不伪称完整端到端单方法墙钟。

已发布实现只包含以下三个新文件；以下SHA256绑定这次review的字节，不是原生执行凭证：

| File | SHA256 |
| --- | --- |
| `experiments/candidates/planning_policy_compression/b04/study.py` | `3b9fdaa83eb13cd73a7212febb1ef78d79883a9f451c8521d9b952314e5ca58f` |
| `experiments/candidates/planning_policy_compression/b04/run.py` | `5cd4c04d4fb5548a857c505831d9c099842685b5fc1d497206bd04020595c250` |
| `tests/experiments/candidates/planning_policy_compression/b04/test_study.py` | `152733d1504e4cd8ab88bb3341f46e71b1d69aacd90eb8bbf83c96accb56b759` |

工程检查命令：`/home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q
tests/experiments/candidates/planning_policy_compression/b04`。Implementer为4 passed/10.62s，
独立Reviewer为4 passed/8.00s；语法编译通过。测试使用单独小fixture及有意区分两臂的sentinel，
验证实际stage2数据传递、匹配roll-in地址、完整前缀费用，以及单tick后失败的轨迹/成本。
这些是工程检查，不是生产种子预演或新增科学fit；生产规模运行尚未验证，不能从绿测试宣称成功。

B04实际科学计数保持**0 fit、0采集、0评价、无accepted handle/source snapshot/输出目录**。
未执行方案仍是上文固定的两新区组/四fit独立采集比较；所有seed、40+40 epochs、前瞻判读和
拟议成本在那里，不因暂停重写。没有B05、额外区组、自动确认、迁移或备用科学操作。

### 停止状态与恢复边界

PPC在已发布RESEARCH中的状态为`paused`。节点canonical控制只修改本方向state格为paused，
其他方向、lead、全局owner pause及FSD/G33均保留。只读调用原生policy parser确认该状态
拒绝active launch；节点B04输出目录确实不存在。没有用一次真实launch来“测试”拒绝。

当前hmasd_wait state目录是
`/home/fires/.local/state/hmasd-wait/01a0db8e-361c-7b13-a086-3fe1303fa4b7`：generation8，
所有历史事件已消费，无pending wake/活动job；观察已显式stop，返回`work_unchanged:true`。
四个旧job均为终态（B01/B02/B03 ready，旧Pro collected且此前完整交付/读取完成）。
当前Implementer和Reviewer已交付停止，无未读Pro、等待工作或需要自动rearm的观察。

节点技术限制保留供未来人工恢复时检查：本次fetch origin/main成功；随后读取published
RESEARCH触发惰性对象获取，Git输出自动GC/repack警告
`fatal: bad tree object 9e40125ee3e24973b69754649226d18847b45862`及`failed to run repack`。
该次读取仍成功，published SHA与暂停格更新已验证。没有清理gc.log、修Git对象、改其他工作区
或借此启动新任务。不要把成功读取当作整个节点对象库已经验证健康。

只有owner明确恢复研究后，后续负责人才能重新确认当前lead/暂停/方案适用性及节点Git状态，
发布精确执行输入并走实际节点准入。当前完整Pro建议和独立科学审查已覆盖该方案的动机及
结果分支；读交接不要求重发。尚无责任转移或科学重启；当前任务至此停止。
