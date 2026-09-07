# CBSC-OPPORTUNITY-CREDIT-B04 CM delivery and execution record

Contract: [selected card](CBSC_OPPORTUNITY_CREDIT_B04_SCIENCE_CARD_20260906.md),
Selected learner / Host, information, RNG and evaluation / Exposure, cost and
execution / Single selected engineering check and scope. DM owns scientific intake.

## Source and state ownership

Own branch `codex/cm-cbsc-b04-20260906`, worktree
`C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906`, from pushed card commit
`bd8dff1f590c9f8f9dd630409b3275a18fa66321`. Entry Git status was clean; no old
source is modified. Root integrates reviewed source before execution.

New source: `experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/`
(`learner.py`, `run.py`, `snapshot.py`, `__init__.py`),
`scripts/run_cbsc_opportunity_credit_b04.py`; mirrored `test_credit.py`.

Production chain: existing `DynamicHost(B1_RUN_NAME, seed)` creates immutable
TRAIN/EVAL tapes; existing RAW/STRUCT adapters project only public tokens to
FP32 `[B,152,168]`; existing collector samples common-uniform actions and puts
only the chosen decision/settlement ledger into `[8,152]` rewards. B04 computes
local detached G and old-value A once before four PPO epochs. It uses the
reference clipped actor and Adam/order, with value MSE over48 decisions per
minibatch. Full152-token recurrent forward/BPTT and episode-zero hidden state
remain. No extra host/model calls, future target or unchosen reward enters learning.

The model is the original121349-parameter model, including initialization and
zero adapter columns. The trainer owns Adam/counters and detached rollout targets;
new snapshots save actual model/optimizer/counters with truthful B04 metadata.
Snapshot readback checks all tensors and metadata directly, without a new model
or replay. The direct evaluator receives already chosen actions; REQUEST_ONLY
accepts only public tokens. Publication retains each action and local contribution,
returns, targets/old values/advantages, losses/action counts and endpoint pairs.
STRUCT uses RAW's fixed-rule records and checks matched source/random identities.

Engineering-scope Â§4 additions: **none**, as selected by the card's Single selected
engineering check and scope. No old B1 exception is used. Ordinary source/runner
budgets apply; mandatory publication/readback serves the primary measurement.
Independent scientific review is complete (below); runtime evidence remains pending.

## Focused coverage and cost

Opening focused account132.15/300s. First AST-only check of the six Python files
passed in0.6397762s (no imports, model or host). Constructed target/mask/public-rule
checks run only inside the selected engineering invocation, together with both
real learners, four evaluation executions, snapshots and pair readback. This
covers finalq23 settlement, detached/fixed targets, earlier raw G/A invariance,
shared normalization and48-decision MSE. It does not require zero gradients through
nondecision history. Source inspection checks fixed targets across all16 Adam steps.

Per-arm cost projection: RAW159.38s, STRUCT181.56s (card's twice-old-larger-wall
planning scenarios), both below600s. These are unmeasured B04 estimates. Cost law:
admission/startup+host+48(project8/rollout8/PPO4x4)+2(eval32/snapshot)+RAW fixed
rules+publication/readback+STRUCT pair+termination. Each formal arm58368 training
and9728 evaluation transitions,768 Adam steps; pair136192 transitions/1536 Adam.
Engineering32 Adam/3040 transitions is separate and charged to the same focused
account. No profiler or additional pilot. Complete study critical path and summed
invocation wall will be reported separately; aggregate CPU is unmeasured.

Post-learner path coverage: the single combined engineering invocation executes
all new snapshot, JSONL, native-return, rule-context and paired-summary publication
and readback. No dependence on the old fifteen-table replay system.

## Frozen execution plan

Execution node `wsl_4070`, SSH `hmasd-wsl-node`, interpreter
`/home/wu/.venvs/hmasd/bin/python`. One scientific process, CPU FP32, one Torch
thread; OMP/MKL/OPENBLAS/NUMEXPR/VECLIB thread limits1. Host portability follows
the card's CPU FP32 boundary; no GPU/dtype/RNG/interpreter change is selected.
Local fallback is not selected prospectively for this invocation plan.

Exact detached cwd: `/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906`.
It will be prepared at Root's integrated source SHA, recorded below before launch.
No uncommitted source is copied. Let `W` denote that exact cwd below, and
`E=W/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906`.
Receipts/timing/log collection directory:
`T=W/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906`.
These aliases in this record are literal path abbreviations, not a configuration layer.

Each configured `agent-task run` receives one shell-quoted command with outer
`/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o T/NAME-time.txt`
then `timeout -k 2s LIMITs bash -lc` enclosing the whole command below. LIMIT58
for engineering,598 for either formal arm; grace is inside60/600s. The shell
changes to W, exports the thread limits, and joins exactly:

```
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out T/NAME-admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_cbsc_opportunity_credit_b04.py ARGS
```

| NAME / accepted handle | LIMIT | Exact ARGS |
|---|---:|---|
| cbsc-b04-engineering-20260906 |58| `--engineering --seed 21211 --output E/engineering` |
| cbsc-b04-raw-20260906 |598| `--arm RAW-GRU --seed 21217 --output E/raw` |
| cbsc-b04-struct-20260906 |598| `--arm STRUCT-CURRENTNESS-GRU --seed 21217 --output E/struct --raw-result E/raw/summary.json` |

The engineering call precedes formal RAW, then STRUCT; no outcome-based choice
between the formal arms. Exactly these three calls, no retry. Stop on primary
integrity defect, unavailable necessary coverage/interface/scope, or full cap.
A failed attempt remains in place; missing pair is never filled with zero.
Fresh actual-node physical/effective memory>=4GiB immediately precedes each runner.
Timeout encloses shell/import/admission and every learning/evaluation/publication
phase. Supervisor start/status/exit and outer time retain complete process facts.

Accepted handles go directly to monitor task `01a0791b-0d2d-7b43-85b6-cd5632e0b007`,
Luna/low; Root receipt `01a07249-b095-7821-8ce2-e9c32ba85267`.
CM retains observation until adoption ACK and collection/technical acceptance after it.
No accepted process or runtime result exists yet.

## Independent source acceptance

Reviewer `rv_ah_cbsc_b04` completed read-only review of the exact new source and
reused boundaries. No material finding. Its AST comparison found train_rollout
changes only compute_gae to opportunity_targets plus target retention; the
minibatch changes only the decision-value-loss expression. Public projection,
sampled reward, original model/order/Adam, full BPTT, endpoint pairing and truthful
snapshot/readback boundaries were inspected. No model/host/test was executed.
The final non-test source is549 lines including60 runner lines; tests55 lines.
Staged diff shows only the seven assigned new paths; old objects are unchanged.
A trailing blank line reported by diff-check was removed (no semantic change).

Reviewer limits: launch must supply numeric-library thread limits, actual-node
admission and complete outer timing; no execution/resource/performance conclusion
follows from review. AST/count check0.80s; all reviewer shell reads/checks39.85s.
Conservatively charging its full shell time plus this CM's0.6397762s AST check
makes the pre-engineering focused account172.6397762/300s. Git/read-only control
plane operations are not host/model exposure. The selected60s engineering call
fits the remaining focused account and still runs only once.

DM acceptance correction: removed launch_sha from pair equality gating in run.py;
retained both launch SHAs as descriptive pair metadata. The frozen launch binds
actual source bytes externally; no replacement provenance guard was added.
This follows AGENTS section6 and the card no-new-section4-machinery boundary. No scientific
calculation, host/model invocation or test exposure changed.

## Integrated launch binding

Root integrated/pushed the accepted source as
`a3c2a49bf7002639d43a94f460b688d50c6c42dd` (implementation833c28540,
commit-equality removal a3c2a49bf). This exact SHA is bound for all three selected
calls at the cwd and argv above. Root returned the launch handoff directly to CM.

Current monitor procedure from c0951c555 applies on the local control plane:
use the same global monitor for all handles, with its existing heartbeat ACTIVE
and read back before adoption ACK. This workflow update changes no launch source
or scientific execution. No additional check is selected.
