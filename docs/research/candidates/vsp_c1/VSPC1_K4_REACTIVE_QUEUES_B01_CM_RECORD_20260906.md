# Reactive queues B01 — CM technical acceptance, 2026-09-06

**Source accepted; no selected result invocation launched.** Source/test commit
`0652103f6d992a8c72ada7a45ca7b2384efdbe64` is pushed on
`cm/vspc1-reactive-queues-b01-20260906`, based on the frozen card commit
`503043ddaaeafd5985d26fe66f4c29303ae1a86e`.
Root integrates; DM retains scientific intake and subsequent execution selection.

Contract: [card §§2–7](VSPC1_K4_REACTIVE_QUEUES_B01_SCIENCE_CARD_20260906.md),
evidence-spec §§4, 5.2, 11.4, 11.8.6–11.9 and scope-spec §§3–5.
This record establishes implementation conformance, not an algorithm effect or remote runtime bound.

## Delivered paths and ownership

- `experiments/candidates/vsp_c1/k4_reactive_queues_b01/experiment.py`: 253 lines;
  NumPy batched host/tapes, PyTorch models, collection, detached actual-segment Double-Q,
  equal-period/equal-episode loss, Adam and target lifecycle, observed exposure and curves.
- `experiments/candidates/vsp_c1/k4_reactive_queues_b01/reporting.py`: 58 lines;
  JSON publication/readback, paired endpoint, conditional evaluation SE, AUC and branch reading.
- `scripts/run_vspc1_k4_reactive_queues_b01.py`: 79 lines; arm/configuration/technical-fixture
  entry points and offline paired-report entry point, launch facts and wall/RSS reporting.
- Mirrored `test_contract.py`: 164 lines of focused checks.

Scope §4 additions listed before writing: **none**, as requested by card §7.
390 non-test source lines, including the 79-line runner, are below the ordinary limits.
No source outside these new owned paths changed. No governance, Portfolio or old VSP-C1
source/evidence changed. No profiler, environment/baseline dependency, scheduler or recovery route added.
Ordinary per-update JSON publication retains partial primary facts if a process fails.

The caller owns a batch only through one update, then discards it. Collection sees the unchanged
online model; each period group contains eight complete episodes, yielding 192 and 64 rows.
Host state is `(q0,q1,h,t)`; only renewal states enter focal Q scoring. Tapes are private to
collection, not model inputs. Partner selection reads old `h` on every primitive tick before
service; the held action is reused through all ticks. Target state is a non-optimized copy,
initially equal and replaced after each multiple of 16. JSON has scalar/list copies, not live tensors.

## Frozen RNG mapping and prospective exposure

All random tapes use NumPy `Generator(PCG64(SeedSequence([root_seed, namespace_id, period, update])))`.
IDs: `init_FACTOR=11`, `init_GENERIC=12`, `train_arrivals=21`, `train_h=22`,
`explore_coin=23`, `explore_action=24`, `eval_arrivals=31`, `eval_h=32`.
Initialization takes the first uint64 SeedSequence word with period/update zero as the
arm's Torch seed, in a forked CPU RNG scope. Dense initialization and embeddings follow card §3.
Training update indices are 1–256. Evaluation update is always zero, with distinct period keys.
Arrivals are `[episode,primitive_tick,queue]`; exploration is `[episode,primitive_tick]`,
read only at actual renewal ticks. Initial `h` is `[episode]`. No draw depends on selected actions.
Arm names affect only initialization, so each arm reconstructs shared tapes without transfer.
Evaluation tapes are held once and reused at every checkpoint. No cross-host bit-identity claim.

Configuration-only CLI calls wrote `configuration.json` for each arm under the local
`temp/directions/vsp_c1/test/reactive_queues_configuration/` directory. They had zero host,
update, evaluation or selection exposure. Reviewer independently confirmed configuration counts.
Machine-generated per-arm line: FACTOR 300 / GENERIC 309 online float32 parameters;
4,096 train episodes, 196,608 train ticks, 65,536 rows, 61,440 nonterminal rows, 256 Adam steps;
2,304 evaluation episodes, 110,592 evaluation ticks, 36,864 evaluation decisions;
454,656 scalar Q predictions; 17 target copies; zero model-selection steps.
The configuration includes the nonzero Adam/TD can-move statement. Actual seed-401 initial
norms, final displacement and returns remain unmeasured.

## Focused acceptance and independent review

Local interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
Checkout: `C:/Projects/HMASD-worktrees/cm-vspc1-reactive-queues-b01-20260906`.
Commands used `-m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/<tag>`.

1. Whole changed directory: seven semantics/rule tests passed in 4.99 s; smoke setup failed
   because the new worktree's test parent directory did not exist. No smoke process started.
2. Created the test parent and ran only `test_contract.py::test_real_runner_publication_smoke`.
   FACTOR technical fixture completed 16 updates and wrote primary JSON, then failed on
   optional Windows RSS import: `ModuleNotFoundError: No module named 'psutil'`.
   The retained root is `temp/directions/vsp_c1/test/reactive_queues_smoke_20260906/`.
3. Repaired the known resource gap to publish `resources_unmeasured`; no dependency installed.
   Re-ran only the affected smoke in a new root: **1 passed in 10.31 s**. Both arm exit codes
   were zero, stderr empty, counts matched, parameter displacement was nonzero, target-copy
   updates were `[0,16]`, and all endpoint/consequence/TD entries were read back.
   Raw outputs live in `temp/directions/vsp_c1/test/reactive_queues_smoke_repair_20260906/`
   under `test_real_runner_publication_s0/`, including sibling arm stdout/stderr files.
4. Ran the offline `--compare FACTOR/summary.json GENERIC/summary.json` path over these
   saved fixture outputs; `paired_fixture.json` was published/read successfully, with no new exposure.
5. `git diff --cached --check` passed before the source commit.

The seven rule checks cover service conservation/overflow and old-h simultaneous ties;
holding/renewal-only scoring and actual final successor; feature order/parameters;
paired/separated RNG streams and primitive slots; detached Double-Q and no terminal scoring;
episode/period equal loss versus row-weighted loss; counts, MEI tradeoff boundaries and AUC.
The paired fixture exercises actual model/host/Adam/target/evaluation/publication dependencies.
One pre-existing pytest warning (`cache_dir` with cacheprovider disabled) is unrelated.
No repeat check merely for launch is needed.

Independent `hmasd-reviewer` task `review_ah_reactive_queues` read the complete source,
applicable specifications, tests and saved repaired fixture artifacts. It found **no material
finding**, including after the resource repair, and found no prohibited machinery/budget breach.
It independently executed configuration-only counts, did not repeat training or tests, and made no edits.
Its residual limits are the unobserved selected-run completion, remote resources and whole-arm runtime.
CM accepts that disposition; there are no unresolved source acceptance findings.

Technical exposure is separate from B01: three arm-fixture executions (failed post-primary
FACTOR, repaired FACTOR, repaired GENERIC), all seed 9401, each 64 training episodes / 3,072
training ticks / 16 updates and 8 evaluation episodes / 384 evaluation ticks. Total fixture
learning is 192 episodes / 9,216 ticks / 48 updates, plus 24 evaluation episodes / 1,152 ticks.
Host unit fixtures add 244 primitive episode-ticks; the loss unit fixture performs one synthetic
zero-lr SGD step. No selected seed-401 episode, update, evaluation or selection was executed.
Toy results are not interpreted as performance evidence or used to select settings.

## Cost and post-learner path coverage

**Per-arm planning projection:** complete logical work is initialization + 256 collections/Adam
steps + nine fixed evaluations + JSON publication/checking + exit. Cost law is recorded in each
configuration: training host ticks plus behavior/loss rows and nonterminal backups; evaluation
host ticks/action rows; optimizer/publication work. In-process groups retain batch16 overall;
no worker or device sweep was performed. Full selected runtime on wsl_4070 is unknown.

For a coarse planning estimate only, reuse the whole repaired two-arm fixture pytest wall
(10.31 s) as a deliberately padded single-arm input. The largest ratio among total primitive
ticks, scalar Q predictions and optimizer steps is 88.8889 (307,200 / 3,456 ticks).
Linear-work projection is therefore **916.45 s per arm**, below the 2,700 s original per-arm cap;
sum is 1,832.89 s, and sequential study critical path is that sum plus remote preparation and
queue/control latency. This is an assumption-based planning estimate, not a proven bound:
different training/evaluation batch sizes, host, and per-phase costs may violate simple linear
scaling. No new profiling or calibration run was selected. Aggregate CPU is unmeasured;
neither summed wall nor study elapsed is relabelled CPU work. Each whole invocation retains
the hard cap; no borrowing, automatic retry or extension follows.

**Post-learner path coverage:** repaired real learner → all fixture evaluations → endpoint
arrays → summary write/read → paired report write/read → exit passed. The old six-tick
publication system is not imported. Local peak RSS is missing and explicitly labelled;
Linux uses `resource.getrusage` for main-process lifetime peak RSS. This is technical path
coverage, not completion of the selected learner/primary or resource measurements.

## Concrete launch plan — not executed

Root source integration must occur first. The following plan uses the exact pushed and reviewed
source SHA above, on the configured `wsl_4070` node (`ssh hmasd-wsl-node`), CPU float32,
one compute thread, batch16; source, interpreter and output all remain on that node.
The host is prospectively portable but execution is remote-first. Root/DM records the actual
accepted handles and launch SHA at execution. If integration changes source, this plan must
be bound to those changed bytes and the affected review/checks addressed.

Node-local preparation (ordinary Git only; no launch happened in this assignment):

```bash
cd /home/wu/projects/HMASD
git fetch origin cm/vspc1-reactive-queues-b01-20260906
git worktree add --detach /home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-0652103f6 0652103f6d992a8c72ada7a45ca7b2384efdbe64
```

The exact node-local command list below uses existing `agent-task`, whose `run/status/logs/stop`
interface was read with `--help`, and existing GNU timeout/time. FACTOR runs first; GENERIC
starts after FACTOR's terminal acceptance, so its one capped command also publishes the paired
report. These commands are a list, not a new queue implementation. Each contains its own fresh
node-local admission joined by `&&`, before its runner initializes any scientific state.

```bash
W=/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-0652103f6
P=/home/wu/.venvs/hmasd/bin/python
O=$W/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run01
/usr/local/bin/agent-task run vspc1-reactive-b01-factor-run01 bash -lc "cd $W && $P scripts/hmasd_resource_preflight.py admit-memory --out $O/FACTOR/resource_admission.json && /usr/bin/time -p -o $O/FACTOR/invocation.time timeout --signal=KILL 2700s $P scripts/run_vspc1_k4_reactive_queues_b01.py --arm FACTOR --seed 401 --out $O/FACTOR"
/usr/local/bin/agent-task run vspc1-reactive-b01-generic-run01 bash -lc "cd $W && $P scripts/hmasd_resource_preflight.py admit-memory --out $O/GENERIC/resource_admission.json && /usr/bin/time -p -o $O/GENERIC/invocation.time timeout --signal=KILL 2700s bash -c '$P scripts/run_vspc1_k4_reactive_queues_b01.py --arm GENERIC --seed 401 --out $O/GENERIC && $P scripts/run_vspc1_k4_reactive_queues_b01.py --compare $O/FACTOR/summary.json $O/GENERIC/summary.json --out $O/paired_summary.json'"
```

Stop condition is update256 plus final evaluation/publication/exit, concrete failure, or 2,700 s
for the entire arm command. Generic's cap includes offline paired publication. No success is
inferred from child exit alone; inspect supervisor status, primary summary/readback and observed
counts. `agent-task status <name>` is the terminal witness and `agent-task logs <name> 40` reads
its existing log; `agent-task stop <name>` is the manual stop command. Uncertain acceptance is
resolved from the same name, never by relaunching. No accepted process currently exists.

Observation routing is operationally changing: DM conveyed Root's owner-authorized instruction
that Root will absorb Monitor/Transport after a routing-ready notice. At actual launch use that
current ready route, send accepted handles with the paths/node/SHA/bound, and retain observation
until adoption is confirmed. Do not create another monitoring task or heartbeat. This source
assignment stops here and creates no monitoring handoff. Root owns integration and routing;
DM owns subsequent launch assignment and scientific intake; CM retains technical collection.

## Command-transport repair after accepted run01 no-op — 2026-09-06

Root accepted FACTOR handle `vspc1-reactive-b01-factor-run01` at remote time
`2026-09-07T13:57:52+08:00`. Independent read-only collection confirmed status finished,
exit0, tmux inactive, and start/end at that same timestamp with duration0s. The log contains
only the two supervisor lines. Its stored runner's execution statement is exactly
`eval 'bash -lc  cd '`. Thus the accepted supervisor command ran only cd, not admission or
the scientific runner. The intended run01 output root does not exist. No GENERIC dispatch
is reported. These facts support zero experiment exposure from the accepted FACTOR handle,
not a scientific result. The upstream PowerShell interpolation mechanism is not uniquely
reconstructed from retained remote evidence; command truncation itself is directly verified.

The installed supervisor sets `COMMAND="$*"` and writes an eval command, losing argument
grouping unless the complete command is supplied correctly. The repaired
[launch assignment §4](VSPC1_K4_REACTIVE_QUEUES_B01_LAUNCH_ASSIGNMENT_20260906.md)
uses a literal single-quoted PowerShell here-string piped to remote Python stdin. Python
passes a single complete command-string argument to the existing agent-task. There is no
nested bash-c layer or shell-variable expansion in the scientific command. This is a
documentation/transport correction, not a new launcher or framework.

Readback confirmed the existing remote cwd
`/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835` at frozen source
`47674883572bbe078ede037cbb8f99b8cd54c159`. New planned handle is
`vspc1-reactive-b01-factor-run02`; new output root is
`temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/FACTOR/` beneath that cwd.
New handle and run02 root were absent. Old run01 handle/log/runner files remain untouched.

Bounded non-result transport check used the exact proposed command through PowerShell → SSH
stdin → remote Python. Bash syntax check exited0; assertions confirmed every token of
the cd/admission/timed-runner segments. Prospective agent-task argv was printed, not executed.
The chain includes fresh node-local memory admission immediately before the 2700s complete
FACTOR invocation, retaining seed401/256 updates/CPUfloat32/one thread/batch16. No admission,
model/RNG, experiment, source test, or new supervisor task ran during this repair.

Raw local evidence: `C:/Projects/HMASD-worktrees/cm-vspc1-reactive-transport-repair-20260906/temp/directions/vsp_c1/transport_repair_20260906/`,
files `accepted_runner.txt`, `status.json`, `task.log`, `paths.json`, `argv_check.json`.
Durable decision-relevant excerpts are above and in the corrected assignment. The repair
branch starts at main `956be39abc870dc2bd034fb51b7f450fc21b3b29`; unrelated Root changes
and prior evidence are preserved. Only the launch assignment and this record change.

DM selected this command-delivery correction and Root requested the exact bounded
FACTOR-only retry preparation. The original object/budget remain selected; no scientific
retry allowance or polarity is inferred from technical failure. Root must accept and dispatch
the exact payload once; CM does not launch. GENERIC remains undispatched pending its later
original-arm handoff. Integrated Root adoption/ACTIVE readback routing is unchanged, with
CM technical collection and DM science retained. Actual run02 acceptance/output remain unobserved.

Independent reviewer `review_ah_reactive_queues` inspected the exact transport payload,
preserved run01 facts and syntax/argv evidence and found no material concern. It performed
no launch, admission, learner probe, test rerun or edit. CM accepts this bounded transport
correction; it does not establish actual run02 admission or scientific completion.

## FACTOR run02 terminal technical acceptance — 2026-09-07 UTC

**FACTOR is technically accepted.** Root dispatched the corrected payload once; CM collected
the actual remote `summary.json`, `resource_admission.json`, `invocation.time`, supervisor
status/log and accepted runner from handle `vspc1-reactive-b01-factor-run02`, node wsl_4070.
Source readback in the summary is `47674883572bbe078ede037cbb8f99b8cd54c159`, cwd
`/home/wu/hmasd-worktrees/vspc1-reactive-queues-b01-476748835`, NumPy1.26.3/Torch2.7.0+cu118,
configured Python `/home/wu/.venvs/hmasd/bin/python`, CPU float32/one compute thread/batch16.
The observed argv is the frozen FACTOR/seed401 call at run02/FACTOR, without fixture flags.

The log starts `2026-09-07T14:09:30+08:00` and ends `14:09:35+08:00`, exit0, duration5s;
supervisor status is finished, tmux inactive. Node-local receipt assessed at
`2026-09-07T06:09:30.788337Z` passes physical/effective admission, both 15,668,547,584 bytes
against the 4,294,967,296-byte floor. Receipt precedes runner initialization in the accepted
command. Whole invocation `time` reports real4.84s/user3.73s/sys0.39s (CPU sum4.12s), below
the complete-arm 2700s cap. Main-process peak RSS is 478,375,936 bytes; summary wall through
primary readback4.422588917019311s and stdout through final readback4.425325764023s.
Whole invocation includes publication and exit; the log's rounded duration includes admission.

CM read/checks on the collected JSON passed: status complete, 300 online parameters, seed401,
256 completed updates, observed counts equal prospective counts; 4096 training episodes /
196608 joint ticks / 65536 renewal rows / 61440 nonterminal rows / 256 optimizer steps;
2304 evaluation episodes / 110592 ticks / 36864 decisions; 454656 scalar Q predictions;
17 target copies at [0,16,...,256], zero model selection. All nine fixed curve points,
256 per-update per-period finite nonnegative TD-loss records, and 128 indexed endpoint
episodes per period exist. Endpoint means recompute from those arrays; return bounds,
unused-service identity and backlog/overflow bounds hold. Initial parameter norm is
4.527723789215088 and final displacement1.4559444189071655. This inspection added no rollout,
learning, evaluation or replay exposure and did not rerun source tests.

All curves/adverse facts are retained in the exact summary. FACTOR initial/endpoint equal-period
means are 0.7252197265625 / 0.7248942057291665; endpoint d2=0.7266438802083333 and
d6=0.7231445312499999. These are direct arm measurements, not a comparison or scientific
selection. GENERIC remains required under the frozen two-arm object irrespective of FACTOR's
score/sign. No paired conclusion exists yet; DM owns scientific interpretation.

Collected local root:
`C:/Projects/HMASD-worktrees/cm-vspc1-reactive-transport-repair-20260906/temp/directions/vsp_c1/exp/k4_reactive_queues_b01_run02/FACTOR/`.
It contains exact copied primary/admission/timing artifacts, supervisor status/log/runner, and
`collection_check.json.txt` with the read-only checks and full curve means. Remote originals
remain in the same relative output path beneath the bound cwd. Prior failed run01 is unchanged.

FACTOR technical acceptance satisfies the preceding-arm dependency for preparing the original
GENERIC handoff. Root must accept and dispatch its exact corrected command; CM has not dispatched
GENERIC. The proposed `vspc1-reactive-b01-generic-run02` handle and run02/GENERIC root were absent
at read-only preparation. Root observation/adoption, CM technical collection and DM science remain.
