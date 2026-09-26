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
