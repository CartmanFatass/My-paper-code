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
