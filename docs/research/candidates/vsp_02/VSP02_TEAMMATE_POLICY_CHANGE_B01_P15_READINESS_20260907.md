# VSP02 B01 — P15 scientific code/card readiness and Root execution handoff

**Decision: ready for the one P15-allocated pair.** This is source/record readiness, not a new
scientific result. No result-bearing process or resource admission was performed by this DM.

## 1. Authority, source and ownership

P15 VSP02, `docs/research/portfolio/handoffs/2026-09-07-p15-rolling-refill-after-transport-split.md`
at `25b1a88b162ae137b5071ca2d9acb87007fb3ea9`, allocates one complete B01 same-prefix pair under
the existing1800-second cap. It supersedes P14's zero-scientific-invocation limit only for that
pair. There is no extra comparator, seed, retry, resume, new branch or broader scientific claim.

The existing checkout `C:/Projects/HMASD-worktrees/dm-vsp02`, `codex/vsp02`, began clean at
`ef39e40706cb9656a81dfa1dd640bac419cd89a8`. It contains the accepted baseline implementation
`b0c957d9b9a23506dbd0ba8a1b8c729ea50d8cad` and complete common card/spec preparation
`a1b8c56f2a36e2027372bf578fc2646dfd57efe9`. All eight implementation/test files were checked
against the retained baseline-return bytes and their committed blobs: they agree exactly.
No source or test changes were made. Current AGENTS, ROOT_OPERATIONS and the P15 handoff were read
from the exact accepted main commit above. Root requested a VSP02-only publication; those input
copies add no control-plane file to this commit and no new governance decision was authored.

**Launch source:** the full committed/pushed revision returned with this readiness package.
Root uses that exact revision for the detached worktree. Its declared implementation surface is
the five research files under `experiments/candidates/vsp_02/teammate_policy_change_b01/` and
`scripts/run_vsp02_teammate_policy_change_b01.py`, identical to accepted `b0c957d9b9a23506dbd0ba8a1b8c729ea50d8cad`.
The full source SHA is returned after publication rather than pretending this document can embed
its own future commit. Doc-only publication does not change source acceptance.

CM route: reuse **`/root/vsp02_cm_baseline_b01`**, whose existing native identity was found
completed/resumable. After Root supplies the actual accepted handle and terminal receipts, CM
collects and accepts in this designated direction checkout, preserving its comparison worktree
and first-return evidence. DM is `/root/dm_vsp02_p13_convergence`. This is an existing implementation's
readiness/execution/collection continuation, **excluded from new CM comparison enrollment**;
there is no new coding assignment or replayed batch. A concrete same-module correction returns
to that same CM with its original comparison/correction history intact.

## 2. Scientific correspondence and original acceptance

Direct source review covered the complete626-line implementation, with32-line runner, against
CODE_SPEC §§2–5 and SCIENCE_CARD §§1–7:

- `host.py`: fixed entities/roles, simultaneous actions, endpoint-only RECEIVE/DELIVER reward,
  active old/new courier script,16 three-step rounds/H48,18-field local observation, visibility
  of past actions at the preceding pre-action positions, retained round history and terminal-only reset.
- `learner.py`: shared18→64→64 recurrent network, one joint Adam with the selected parameters,
  complete48-step gradients, GAE/loss/normalization rules, four epochs/four episode minibatches,
  cloned named streams, identical independent model forks, full CARRY state and RESET clearing
  only optimizer moments/steps while preserving parameter groups and global progress.
- `study.py` and runner: P4096/Q1024, master1103, CPU FP32/one intra-op and inter-op compute thread,
  alternating real descendant trajectories, sampled private evaluation RNG, shared q0 once,
  actual training-return primary, actual update/partial counts and all curves. The clock starts
  before torch import, is checked through collection/update/evaluation/publication, and retained
  complete native windows survive a later incomplete secondary phase with their narrower limit.

The earlier source review is retained in
`VSP02_TEAMMATE_POLICY_CHANGE_B01_IMPLEMENTATION_REVIEW_20260907.md`. Original baseline evidence
is under the **main checkout's**
`C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-01/outputs/baseline/turn-01/return/`:
`checks.json`, `FINAL_RESPONSE.md`, the eight returned files and `fixture/{summary.json,training_returns.csv,evaluation_returns.csv,updates.csv}`.
The independent verification is
`C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-01/independent_verify/results.json`,
baseline entry, and its `baseline/cmd1.stdout` / `cmd2.stdout`.

DM checked those actual records and read back the archived raw fixture rows:48 training episodes,
48 Adam steps,16 evaluation episodes,3072 joint steps, shared q0 four episodes once, three complete
rollout-update records, correct primary from raw training returns, nonzero movement, equal fork
weights and correct10-versus0 initial Adam state entries. These remain ENGINEERING_FIXTURE.
The recorded independent check passed15 tests and fixture/readback, with exit0; integrated
acceptance is reported in the committed implementation review. The transient authoring fixture
path is absent now, so this intake relies on the preserved return artifacts and independent record,
not an assertion that the missing transient path was read.

History is retained: the baseline's first pytest attempt had11 passes/four setup errors from a
missing scratch parent; the parent was created and checks passed. A later terminal-evaluation
publication correction caused a justified second fixture and third unit suite; both fixture
attempts remain recorded (96 training episodes/96 Adam steps/32 evaluation episodes/6144 joint
steps in participant fixtures). Independent and integrated verification are additional recorded
engineering checks, not scientific samples. DM did not rerun tests or a fixture at readiness.

No scientific correspondence defect was found. The research source and runner remain below the
2000/600-line limits. The398-line study includes the actual collector, evaluator, primary and
publication; its size relative to total source is a review signal, not a reason to demand new
machinery. Engineering-scope §4 additions needed by this object: none. No budget breach is
identified in the accepted source/check record; no price or scientific performance claim follows.

## 3. Counts, exposure and portable runtime

`VSP02_TEAMMATE_POLICY_CHANGE_B01_P15_READINESS_FACTS_20260907.json` was generated with stdlib
Python over source AST, retained fixture JSON and exact source files. It records unchanged
scientific constants and counts:6144 training episodes,294912 training joint steps,384 rollout
batches/6144 Adam.step calls;1152 evaluation episodes/55296 evaluation steps;350208 total joint
steps and1179648 PPO transition-passes. The independent unit is **one prefix and its whole pair**.
Dominant factors remain `(P+2Q)*H`, four PPO passes, and `(2+2*8)*E*H`; there is no nested search.

The machine-generated exposure line in that JSON records zero new readiness interaction/update,
zero scientific invocations so far, planned nonzero counts, and the existing same-path seed17
fixture displacement0.0021576136350631714 against initial parameter RMS0.07669830322265625
(ratio0.028131178193076693 after16 Adam steps). This establishes learner movement at fixture scale;
the real seed1103 movement is still measured in the same allocated B, without an extra probe.

Read-only SSH metadata on `wsl_4070` reports interpreter `/home/wu/.venvs/hmasd/bin/python`,
CPython3.10.21, torch2.7.0+cu118, NumPy1.26.3, Matplotlib3.10.0, Linux WSL2 x86_64. No workload
module was imported, package installed or native build performed. The code explicitly uses CPU
FP32; the CPU route was declared portable before question-relevant output. The Windows fixture
and Linux run are not claimed bitwise identical. The source's Agg plotting dependency is present.

New-host scientific competence, headroom, wall/CPU work and memory remain unmeasured. The
engineering fixture wall is not an affordability projection. The original complete1800-second
budget includes imports, setup, prefix, both descendants, every evaluation and publication;
it is not1800 seconds per arm. Root must run fresh physical/effective≥4GiB admission immediately
adjacent to the single runner on the actual node. This metadata check grants no admission.

## 4. Exact Root execution and collection route

Use `.codex/hmasd-compute.toml` remote_first and a detached worktree at the exact returned
publication SHA. Proposed task name was queried once and returned `not_found`; no process was
accepted. Reconcile actual acceptance before any dispatch retry; preserve every accepted attempt.

- SSH node: `hmasd-wsl-node` (`wsl_4070`).
- Existing repository: `/home/wu/projects/HMASD`; configured supervisor: `/usr/local/bin/agent-task`.
- Detached worktree/cwd: `/home/wu/hmasd-worktrees/vsp02-tpc-b01-p15-s1103-a1`.
- Supervisor handle: `vsp02-tpc-b01-p15-s1103-a1`.
- Scientific output: `temp/directions/vsp_02/exp/teammate_policy_change_b01_p15_s1103_a1` within that worktree.
- Admission receipt: `temp/directions/vsp_02/exp/admission/tpc_b01_p15_s1103_a1.json` within that worktree.
- Supervisor log: `/home/wu/.agent-tasks/vsp02-tpc-b01-p15-s1103-a1/task.log`, with its existing status/exit files.

After preparing the detached exact-SHA worktree, this is the **one on-node supervisor command**.
The existing supervisor accepts the quoted chain as one command; no new launcher is needed:

```bash
/usr/local/bin/agent-task run vsp02-tpc-b01-p15-s1103-a1 "cd /home/wu/hmasd-worktrees/vsp02-tpc-b01-p15-s1103-a1 && env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vsp_02/exp/admission/tpc_b01_p15_s1103_a1.json && env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /home/wu/.venvs/hmasd/bin/python -u scripts/run_vsp02_teammate_policy_change_b01.py --seed 1103 --out temp/directions/vsp_02/exp/teammate_policy_change_b01_p15_s1103_a1"
```

This is not the shortened engineering mode. The runner itself owns the complete1800-second cap;
do not add an independent1800-second budget to either descendant. Prepare only the source checkout
before admission; the runner creates its scientific output after admission passes. If admission
refuses or dispatch acceptance is uncertain, retain exact facts and return the gap without a
scientific negative or blind repeat. No fallback or accepted-process migration is silently used.

Root owns actual dispatch and observation under EXPERIMENT_MONITOR. It records the accepted node,
handle, full launch SHA, cwd, paths and bound in existing tracking. At terminal state it sends the
actual status/exit/log and paths to the same CM, using followup_task if idle. No relaunch occurs.
CM collects the complete run directory and admission/supervisor receipts to the corresponding
local `temp/directions/vsp_02/exp/` surface, checks raw counts/returns/fork/movement/runtime and
publishes technical acceptance/E0 evidence in the direction directory. Collection must preserve
all partial failures and current actual exposure, with no training/evaluation replay.

CM's five concise assignment items are: (1) collect/technically accept this exact P15 invocation;
(2) own its local runtime-artifact copy and B01 result/acceptance evidence in the existing direction
checkout; (3) preserve this card's treatment, RNG, native raw returns and every outcome;
(4) check actual output against card §§1–8/code spec §§2–5 and evidence-spec §§4,5.2,11.8.7, with
independent windows retained when secondary work fails; (5) zero additional result-bearing calls,
no retry/resume/cap increase, return the accepted result or concrete defect through Root to this DM.
No scientific choice is delegated to CM. DM then writes full intake, audit and the Chinese brief.

## 5. Decisions this readiness intake produces

**Object tier, technical readiness:** options (a) accept scientific correspondence of the existing
baseline and return the exact P15 command; (b) return a concrete source defect to the same CM;
(c) return a frozen-meaning conflict explicitly. Recommendation/executed choice: **(a)**. No
concrete defect or scope conflict was found, and P15 already selected/allocated the observation.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** The execution allocation
itself is OWNER_DIRECT P15, not a new DM budget decision. Ledger:2026-09-07.md#L91 in this checkout.

Current main and direction owner-console reviews returned no unapplied instruction or prediction;
there is none to mark answered. Existing P2 card item20260907-vsp02-003 receives the P15 allocation
trace; no redundant ordinary-readiness item is created. Prediction remains not taken (unattended),
with Pro's Delta-in-[-0.5,+0.5] working expectation retained. No result exists to score or brief yet.

Direction verdict remains PRO_FINAL, recasts:1; lifecycle/priority and old negative evidence remain
unchanged. The strongest support is the concrete courier-action/native-service comparison with
matched learned start and information. Generic optimizer transience is the strongest attribution
alternative. Next scientific discriminator is the allocated full native adaptation-service pair;
its ceiling is one-host/one-prefix initial signal or counterexample, without stable superiority,
member recovery, event-specific Adam attribution, transfer or UAV entry.
