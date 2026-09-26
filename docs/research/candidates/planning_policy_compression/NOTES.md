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
