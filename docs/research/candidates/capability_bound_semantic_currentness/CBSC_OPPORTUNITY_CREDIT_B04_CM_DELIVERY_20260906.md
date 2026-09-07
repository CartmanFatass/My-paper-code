# CBSC-OPPORTUNITY-CREDIT-B04 CM delivery and terminal evidence

Delivered: reviewed B04 implementation; the single engineering invocation passed;
formal RAW completed and was technically accepted; formal STRUCT failed before
model construction. **No paired result exists. No retry or extra diagnostic ran.**
DM owns scientific intake. The unknown-opcode cause is unresolved, not inferred.

Contract: [selected card](CBSC_OPPORTUNITY_CREDIT_B04_SCIENCE_CARD_20260906.md),
Selected learner / Host, information, RNG and evaluation / Exposure, cost and
execution / Single selected engineering check and scope. Relevant integrity rules:
evidence-spec sections4,11.4,11.8; engineering-scope sections4-5; runtime complete
invocation accounting. This record replaces encoding-damaged prose in its earlier
revisions with explicit UTF-8/ASCII text; it preserves the facts and prior Git history.

## Source, review and implementation

CM worktree `C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906`, branch
`codex/cm-cbsc-b04-20260906`, base pushed card
`bd8dff1f590c9f8f9dd630409b3275a18fa66321`; initial Git state was clean.
Implementation `3525f5e827ab69c564b8a05182623d05361ecb0a`; correction
`730906eed09ef5df1a493e63d794b44ecb7f81f2`. Root integrated these as833c28540
and a3c2a49bf, respectively. **Every actual call used detached source SHA
`a3c2a49bf7002639d43a94f460b688d50c6c42dd`**, committed/pushed and integrated
before execution. Only assigned new paths were changed; old B01/B02/B03 code and
scientific meaning remain untouched.

New code under `experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/`:
`learner.py`, `run.py`, `snapshot.py`, `__init__.py`; runner
`scripts/run_cbsc_opportunity_credit_b04.py`; mirrored `test_credit.py` under
`tests/experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/`.
Final549 non-test lines, including60 runner lines;55 test lines.
Engineering-scope section4 additions: **none**, as selected by the card. No old
B1 exception, resume machinery, registry, worker, service or profiler was added.

The existing DynamicHost builds action-independent TRAIN/EVAL tapes in B1_RUN.
Existing public RAW/STRUCT adapters project FP32[B,152,168]; the existing collector
records only sampled-action decision/settlement rewards in[8,152]. B04 builds
detached G=r[t]+r[t+1] and A=G-old_value[t] once per rollout, normalizes192 decisions
with population std plus1e-8 outside the square root, and fixes these for all four
PPO epochs. Critic MSE is on unnormalized G over48 minibatch decisions. Original
actor/entropy/global clipping/Adam order and152-token full BPTT are retained.
Nondecision values have no direct value loss; history gradients remain legal.
Original121349-parameter model, initialization, zero adapter columns and common
addressing are reused unchanged. The new config/snapshots truthfully name B04's
credit target; no old GAE metadata is falsified and no old trained state is loaded.

The trainer owns model/Adam/counters and detached target records. Snapshots save
actual state and compare complete tensor/metadata readback without another model
or replay. REQUEST_ONLY accepts public tokens and chooses before evaluator access.
The direct native evaluator receives chosen actions; publication retains their
24 decision/settlement contributions, native returns, credit/old-value/advantage
records, update losses, training action counts, parameter movement and endpoints.
Paired comparison checks matching random/data identities and reports both SHAs.
DM acceptance removed launch_sha equality gating only; no replacement guard was
added (AGENTS section6). Frozen execution binds source externally.

Independent reviewer `rv_ah_cbsc_b04` found no material scientific or scope issue.
Its AST comparison confirmed train_rollout changes only target construction and
retention, while _train_minibatch changes only the decision-value loss expression.
It inspected information/reward, original model/Adam/order/full BPTT, snapshots
and primary readback. No host/model/test execution occurred during review. DM
independently accepted the exact commit-equality removal. A trailing blank line
was removed; staged diff-check passed. Review establishes source conformance,
not runtime success or scientific performance.

## Selected check and cost accounting

Opening focused account132.15/300s. CM AST-only parsing0.6397762s; reviewer AST/count
check0.80s, included within its conservatively charged full39.85s of shell reads
and checks. Pre-engineering account172.6397762/300s. Selected engineering complete
wall5.86s; CM JSON-only contribution/pair collection check0.0019063s. Conservatively
recorded focused account179.50/300s, including a one-second collection allowance.
No repeated smoke, extra model/host call, seed, retry or runtime diagnosis occurred.

Per-arm prelaunch projections remained RAW159.38s / STRUCT181.56s (twice the
larger old same-arm complete wall), both below600s. These were planning scenarios,
not new B04 measurements. Cost law: admission/startup+host+48(project8/rollout8/
PPO4x4)+2(eval32/snapshot)+RAW fixed rules+publication/readback+STRUCT pair+grace.
The formal plan was768 Adam,58368 training and9728 evaluation transitions per arm;
136192 transitions/1536 Adam for a completed pair. The selected engineering call
was separate32 Adam/3040 transitions. The failed STRUCT does not fill its missing
exposure or result with plan values.

Post-learner coverage: engineering exercised all new snapshots, JSONL credit,
native returns, public rule context and paired-summary publication/readback.
No dependence on the old fifteen-table replay system. Formal RAW repeated its
actual selected full path successfully; STRUCT failed before this path existed.

## Exact execution and terminal handles

Node `wsl_4070`, SSH `hmasd-wsl-node`, interpreter `/home/wu/.venvs/hmasd/bin/python`.
CPU FP32, one scientific process, Torch intra-op1; OMP/MKL/OPENBLAS/NUMEXPR/VECLIB
thread limits1. No GPU, dtype, RNG, interpreter or parallelism change; no local
fallback. Detached cwd W=`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906`.
E=`W/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906`.
T=`W/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906`.

Each agent-task receives the exact shell command archived below: outer GNU time,
then timeout58s+2s grace (engineering) or598s+2s grace (formal), enclosing shell
startup, cd/env, actual-node admission joined with && to the runner, imports,
all learner/evaluation/snapshot/publication/readback and process completion.
Pair analysis belongs inside STRUCT. No phase received a new cap. Receipt floor
was4294967296bytes physical and effective. Source bytes were not copied uncommitted.

| Handle | PID | Start UTC 2026-09-07 | Terminal | Complete wall s | Peak RSS KiB | Physical/effective admission bytes |
|---|---:|---|---|---:|---:|---:|
| cbsc-b04-engineering-20260906 |2529595|04:19:08|exit0,04:19:14|5.86|530040|15277744128|
| cbsc-b04-raw-20260906 |2616329|04:21:51|exit0|53.46|589504|15271149568|
| cbsc-b04-struct-20260906 |2623556|04:24:24|exit1,04:24:31|6.38|404608|15671308288|

All receipts passed; assessment times were04:19:08.406466Z,
04:21:51.139416Z and04:24:25.003255Z, respectively. All calls ended within their
complete caps. Formal summed invocation wall59.84s; including engineering65.70s.
Supervisor timestamp elapsed span: formal160s, engineering-through-STRUCT323s
(one-second timestamp resolution, includes control-plane gaps). This is distinct
from summed machine wall; aggregate CPU is unmeasured. Wall and peak RSS are
measured; memory admission is not proof of exclusive resources or all descendants.

Bare remote Git networking initially hung before any admission or scientific call.
Only the identified B04 preparation process trees were stopped. The configured
`zsh -lic` network shell then fetched source and prepared the detached worktree;
its shell-theme warnings did not prevent exit0. No scientific call was duplicated.

All accepted handles were sent directly to the same global monitor task
`01a0791b-0d2d-7b43-85b6-cd5632e0b007`, Luna/low. Root returned adoption ACKs
confirming the existing heartbeat ACTIVE under procedure c0951c555. CM retained
observation until ACK, observed each short terminal before/around those ACKs,
and collected outputs. All terminal facts were sent back to the same monitor
for closing its rows; no per-experiment monitor or heartbeat was created.
Root receipt task is `01a07249-b095-7821-8ce2-e9c32ba85267`.

## Engineering acceptance

Constructed checks passed: sampled local G/A including native REFRESH -0.4+1.0
and finalq23; detached/fixed targets; earlier raw G/A unchanged by future rewards;
shared normalization can change;48-decision unnormalized MSE; nondecision output
loss masking; public REQUEST_ONLY. Source inspection covers fixed targets through
all16 Adam steps; no requirement of zero gradients through recurrent history.
Both real arms completed16 Adam/8 training episodes/1216 transitions/192 decisions,
plus two one-episode evaluations/304 transitions each: total32 Adam/3040 transitions.
Four snapshots and all primary JSON/JSONL/pair records were written/read back.

Initial parameter L2=29.92646598815918. RAW final29.927379608154297,
displacement0.4233545958995819; STRUCT final29.927444458007812,
displacement0.425073504447937. Actual sampled counts in each arm:
SAFE_FALLBACK60,SERVE66,REFRESH66. No performance conclusion is drawn from the check.

## Formal RAW narrower result

All48 rollout records retain TRAIN IDs0..383 once,16 losses each,768 actual Adam
steps,9216 sampled decisions and58368 training transitions. Evaluations only0/48,
32 episodes each,64 executions/9728 transitions. Both snapshots, actual counters,
credit records and complete native contributions were read back. CM checked the
retained24-action/contribution counts, exact ledger sums and episode coverage.
No new host/model call was used for collection. CPU FP32/Torch1/121349 parameters.

Initial/final mean native return: -1.68125 / **12.0375**. Same-tape context means:
ALWAYS_REFRESH11.025, ALWAYS_SAFE4.125, REQUEST_ONLY12.375. RAW minus REQUEST_ONLY
mean **-0.3375**; all32 signed differences follow. These are one trained RAW
instance's direct measurements, not the unavailable STRUCT-minus-RAW estimand.

Initial L2=29.883094787597656; final30.112651824951172; displacement
3.647372245788574 (relative0.12205470255719092),113459 parameter elements changed.
Training actions: SAFE_FALLBACK874,SERVE637,REFRESH7705. Endpoint actions:
SERVE108,REFRESH660,SAFE_FALLBACK0. Action records remain alongside native returns;
movement/action changes alone are not mechanism value.

| Episode | RAW return | REQUEST_ONLY return | RAW minus REQUEST_ONLY |
|---:|---:|---:|---:|
|0|12.3000|12.6000|-0.3000|
|1|10.9000|11.4000|-0.5000|
|2|10.9000|11.4000|-0.5000|
|3|10.9000|11.4000|-0.5000|
|4|10.9000|11.4000|-0.5000|
|5|9.5000|10.2000|-0.7000|
|6|12.3000|12.6000|-0.3000|
|7|12.3000|12.6000|-0.3000|
|8|13.0000|13.2000|-0.2000|
|9|12.3000|12.6000|-0.3000|
|10|13.0000|13.2000|-0.2000|
|11|12.3000|12.6000|-0.3000|
|12|10.9000|11.4000|-0.5000|
|13|13.0000|13.2000|-0.2000|
|14|8.8000|9.6000|-0.8000|
|15|13.0000|13.2000|-0.2000|
|16|12.3000|12.6000|-0.3000|
|17|11.6000|12.0000|-0.4000|
|18|12.3000|12.6000|-0.3000|
|19|13.7000|13.8000|-0.1000|
|20|10.9000|11.4000|-0.5000|
|21|13.7000|13.8000|-0.1000|
|22|11.6000|12.0000|-0.4000|
|23|13.0000|13.2000|-0.2000|
|24|13.0000|13.2000|-0.2000|
|25|12.3000|12.6000|-0.3000|
|26|14.4000|14.4000|+0.0000|
|27|10.2000|10.8000|-0.6000|
|28|13.0000|13.2000|-0.2000|
|29|10.2000|10.8000|-0.6000|
|30|13.7000|13.8000|-0.1000|
|31|13.0000|13.2000|-0.2000|

## STRUCT failure and claim boundary

Terminal exit1, outer6.38s. The retained traceback says `XXX lineno: 285, opcode: 0`
and `SystemError: unknown opcode` in `omrc_b01/addressing.py:285`, the generator
inside PRF.records, called through host._potential/build_stochastic while
constructing B04 run.py:115 eval_tapes. That line precedes model/trainer creation.
Thus no STRUCT model training or policy evaluation was reached; its scientific
output directory is empty: no summary, updates, snapshot or paired_summary.
Host tape construction occurred, but no completed STRUCT learner exposure is
imputed from the planned counts. This is a Python runtime execution failure in
host construction. The exception alone does not identify its underlying cause.

The primary pair is incomplete. No zero/equality/adverse STRUCT gap is inferred;
RAW's independent native measurements remain reportable at their narrower ceiling.
No source repair, model/host diagnosis, retry or successor was selected after the
failure. The one permitted call per formal arm has ended. Existing historical
B1/r05 quarantine and causes remain unchanged. Next owner: DM
`/root/dm_amx_cbsc_next` for scientific intake and any separately selected next
question; Root owns integration and wakes the DM. CM collection is complete.

## Retained artifacts and exact commands

All artifacts remain in the remote E/T roots above and are copied to the CM
worktree. No evidence root was deleted. Complete RAW summary includes both curves,
all actions/local contributions, rule records, primary readbacks, source/RNG and
movement. Updates JSONL retains all48 loss/credit/action/counter records. PT files
contain actual B04 model/Adam/counter states, not a restorable old-GAE label.

- [Engineering summary](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/engineering/summary.json)
- [Engineering pair](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/engineering/struct/paired_summary.json)
- [RAW full summary](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/raw/summary.json)
- [RAW48 update records](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/raw/updates.jsonl)
- [RAW initial snapshot](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/raw/update-0.pt)
- [RAW final snapshot](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/raw/update-48.pt)

### cbsc-b04-engineering-20260906

- [Admission](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-engineering-20260906-admission.json)
- [Outer time](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-engineering-20260906-time.txt)
- [Supervisor terminal](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-engineering-20260906-status.txt)
- [Full log](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-engineering-20260906-logs.txt)
- [Exact command/argv](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-engineering-20260906-command.json)

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-engineering-20260906-time.txt timeout -k 2s 58s bash -lc 'cd /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906 && export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-engineering-20260906-admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_cbsc_opportunity_credit_b04.py --engineering --seed 21211 --output /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/engineering'
```

### cbsc-b04-raw-20260906

- [Admission](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-raw-20260906-admission.json)
- [Outer time](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-raw-20260906-time.txt)
- [Supervisor terminal](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-raw-20260906-status.txt)
- [Full log](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-raw-20260906-logs.txt)
- [Exact command/argv](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-raw-20260906-command.json)

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-raw-20260906-time.txt timeout -k 2s 598s bash -lc 'cd /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906 && export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-raw-20260906-admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_cbsc_opportunity_credit_b04.py --arm RAW-GRU --seed 21217 --output /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/raw'
```

### cbsc-b04-struct-20260906

- [Admission](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-struct-20260906-admission.json)
- [Outer time](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-struct-20260906-time.txt)
- [Supervisor terminal](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-struct-20260906-status.txt)
- [Full log](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-struct-20260906-logs.txt)
- [Exact command/argv](C:/Projects/HMASD-worktrees/cm-cbsc-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_control_20260906/cbsc-b04-struct-20260906-command.json)

```sh
/usr/bin/time -f 'process_wall_seconds=%e peak_rss_kib=%M' -o /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-struct-20260906-time.txt timeout -k 2s 598s bash -lc 'cd /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906 && export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/test/opportunity_credit_b04_20260906/cbsc-b04-struct-20260906-admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_cbsc_opportunity_credit_b04.py --arm STRUCT-CURRENTNESS-GRU --seed 21217 --output /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/struct --raw-result /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b04-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b04_20260906/raw/summary.json'
```
