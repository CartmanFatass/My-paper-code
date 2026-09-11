# CBSC direct-return B03 result evidence

Date: 2026-09-05. **Complete valid B/EXPLORE: another local zero difference.**
Source65bf2486594fc29b4813df2d1d79dec82f5756af; commandsb35d1ee78;
Root-integrated/pushed main323d5e343 before execution. CM complete evidence is
ce1b3d84a604b5c12f17541dec2b303a059d2022, after RAW617cbae92.

The frozen B03 card states:

> The primary quantity is the mean of all 32 native STRUCT-minus-RAW episode
> returns at update 48. Keep both absolute returns, all 32 differences and all
> four curves. No best-checkpoint, best-episode or metric selection is allowed.

The actual seed was21209. Both arms used the same new initialization, training
and procedural evaluation world addresses, public information, native reward,
CPU FP32 model, single Torch thread and PPO48-update budget. Compared with B02,
only the named seed and outer object binding changed. The source diff was
+23/-10 in two thin files, with independent review and five pure binding checks.
No new simulation smoke or forbidden engineering machinery was introduced.

## Primary observation and run-level context

| Update | RAW | STRUCT | STRUCT minus RAW |
| --- | ---: | ---: | ---: |
| 0 | 2.415625 | 2.415625 | 0 |
| 12 | 10.5875 | 10.5875 | 0 |
| 24 | 10.5875 | 10.5875 | 0 |
| 48, primary | 10.5875 | 10.5875 | 0 |

All32 endpoint differences are zero. At updates12,24,48 both arms choose
REFRESH on all768 evaluation opportunities. Same-tape ALWAYS_REFRESH is
10.5875 and ALWAYS_SAFE4.0375. The observed primary gap is inside MEI0.25;
no seed-population equivalence or optimality follows.

| Independent paired run | RAW endpoint | STRUCT endpoint | Paired difference |
| --- | ---: | ---: | ---: |
| B02 /21203 | 10.7125 | 10.7125 | 0 |
| B03 /21209 | 10.5875 | 10.5875 | 0 |

The descriptive mean across these two runs is10.65 for each arm, and the two
observed paired differences have mean0. The run-summary tool's observed sample
SD0 for those differences is not zero population uncertainty or a confidence
interval. There are two independent run seeds, not64 independent trained pairs.
Both initialization and procedural training/evaluation worlds vary across runs;
the records do not isolate initialization as a cause. All outcomes are retained.

## Actual learning and actions

Each arm completed384 fresh training episodes0..383,58368 training transitions,
9216 decisions,48 rollout updates and768 Adam steps/finite loss records.
Four checkpoints0/12/24/48 each evaluated32 episodes:128 evaluation executions,
19456 evaluation transitions per arm. Total B03 training plus evaluation is
155648 transitions and1536 Adam steps, exactly as scheduled. Two fixed context
policies score existing tapes and add no independent training or world sample.

Initial parameter L2 was29.90141106 for both. Displacement was6.07807636 RAW
(20.32705531%) and5.58644104 STRUCT (18.68286761%). All eight complete original
checkpoint payloads, optimizer states and counters are retained. Evaluation
model/optimizer state and paired random-address records are consistent.

| Sampled training decisions | RAW | STRUCT |
| --- | ---: | ---: |
| SERVE | 243 | 237 |
| REFRESH | 8515 | 8569 |
| SAFE_FALLBACK | 458 | 410 |
| Total | 9216 | 9216 |

Both first batches contain73 SERVE,54 REFRESH,65 SAFE decisions. The last batch
has RAW191 REFRESH/1 SAFE and STRUCT192 REFRESH. These are counts from existing
update logs, separate from greedy evaluation. They show sampled behavior became
concentrated on REFRESH; they do not uniquely establish the cause, absence of
all exploration, or that more training/changed entropy would improve the method.

## Complete costs, receipts and evidence

| Invocation | Exit | Outer wall s | Peak RSS KiB | Fresh physical/effective available B |
| --- | ---: | ---: | ---: | ---: |
| RAW | 0 | 59.53 | 576120 | 15679438848 |
| STRUCT, including pairing | 0 | 58.67 | 578280 | 15367352320 |

Both configured wsl_4070 invocations passed fresh4GiB admission immediately
before their runner, and each fits its complete600s cap. Task names were
cbsc-direct-b03-65bf24865-raw and cbsc-direct-b03-65bf24865-struct.
They ran detached at the exact source with /home/wu/.venvs/hmasd/bin/python.
Their complete invocation walls sum to118.20s, versus the qualified pre-run
reference170.47s from B02; this is not a matched acceleration study. B02+B03
formal invocation walls sum to288.67s, not elapsed study time including
preparation, Git, observer delays and collection. Aggregate CPU work was not
collected. The pure binding check charged0.69s; directory focused charge is
132.15/300s. No cap or source-scope breach occurred.

The tracker briefly ended a turn with a running snapshot; CM resumed that same
observer and obtained the already-existing terminal witness. No process or
experiment was restarted. Both task handles are terminal and no third pair exists.

CM and its independent artifact reviewer checked complete native output and
found no material inconsistency. DM separately recomputed all endpoint and
curve arithmetic,256 learned-evaluation native decision/settlement sums, all
finite loss counts, fresh episode sequence, pairing and sampled action counts.
CBSC_DIRECT_RETURN_B03_DM_ANALYSIS_20260905.json records the artifact-only method.
The four-row TWO_SEED_SCORES CSV and summarize_runs.py TWO_SEED_SUMMARY JSON
use one endpoint per training seed/arm, with no confidence interval or selection.

Original summaries,96 update rows, paired summary, training-action readback,
logs, exits, wrappers, receipts and external times are tracked under
direct_return_b03_20260905/. Full checkpoints and outputs are retained locally
at temp/directions/capability_bound_semantic_currentness/exp/cbsc_direct_return_b03_seed21209_65bf24865/
and remotely under that relative root in
/home/wu/hmasd-worktrees/cbsc-direct-return-b03-65bf24865-20260905/.
Historical B1/r05 evidence and unresolved SIGSEGV/TypeError causes remain unchanged.
