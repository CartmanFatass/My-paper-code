Claim under test: B01's final trained RESET advantage may recur in a fresh RETAIN/RESET training pair at the same finite exposure.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR-PUBLIC-LIFECYCLE-B02 — independent training-pair follow-up

## 1. Status, question and retained evidence

**B/EXPLORE; exactly one RETAIN/RESET training pair is now allocated.** Root's subsequent
execution assignment is recorded in §6 and the [execution intake](FOLR_PUBLIC_LIFECYCLE_B02_INTAKE_20260909.md).
The original preparation and implementation assignments each had zero scientific execution;
this new allocation does not reopen B01's completed batch. The
[preparation intake](FOLR_PUBLIC_LIFECYCLE_B02_PREPARATION_INTAKE_20260909.md) records that
authority and the relevant special-review reading; the review itself allocated no training.

Question: does another independently initialized and trained pair reproduce a RESET-favoring
final native-return gap at the same exposure? This compares the complete trained packages,
including their optimization/data paths and partner co-adaptation. It is not causal isolation
of memory contents or a same-traffic counterfactual.

B01 remains one matched training pair: RETAIN `2.104375`, RESET `4.1065625`,
`d_01=-2.0021875`, hence `RESET_ABOVE_MEI` under MEI 1.0. Preserve its all-64 final returns,
wide conditional episode spread and lower RESET training mean (-5.225858 versus -5.044872).
Its DM prediction of WITHIN_MEI missed. B02 is selected after this outcome; its configuration
is unchanged apart from fresh training/evaluation randomness, and no candidate seed was tried.
The [B01 intake §§2–5](FOLR_PUBLIC_LIFECYCLE_B01_INTAKE_20260909.md) supplies the retained limits.

There is no tuned same-information baseline/upper headroom record on this public-lifecycle
host. Reuse B01's generic actor/mixer comparator and prior observations because host,
observations, actions, information and exposure match. B01 is a fixed-configuration result,
not tuned headroom. The old B04 scalar host does not supply a matching baseline.

## 2. Preserved package and fresh randomness

The complete unchanged scientific recipe is [B01 card §§2–3](FOLR_PUBLIC_LIFECYCLE_B01_SCIENCE_CARD_20260909.md#2-native-host-information-and-state-intervention),
frozen at `97eb1683ee2a19d56918b80e2e92ff939328aa7a` and implemented at
`387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358`. Its information/state/native-reward and learning
semantics remain binding. The accepted B02 seed-routing source is
`434f10cf95f16dd342cbf754382aa76155fcd2b7`; the original preparation invented no launch SHA.

- Keep CAMA `1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58` easy Traffic Junction: five slots,
  five actions, vision 1, 7×7 grid, 20 native steps, add rate 0.1 under ordinary reset, native
  reward, waiting/removal side effects and global NumPy draw order.
- Actual departures D and activations B, including same-step refill, define
  `C=A_before & A_after & ~D & ~B` and `E=any(D | B)`. Emit them after the native step and
  before the next actor update. Both actors receive the same local attention input plus
  public E and own B before fc2; the centralized mixer retains the same source information.
  This is the declared public-lifecycle extension, not unchanged original-CAMA information.
- Both arms start new trips fresh, zero inactive state and retain preceding actions only
  for true C before attention. RETAIN carries true-survivor GRU state; RESET clears it on
  E **before** processing the next observation. Acting, online replay and target replay use
  the same respective rule. Full survivor history can contain teammate observations.
  RESET still uses current input, the legal preceding action and history between events.
- Keep the source entity-attention GRU64/FlexQMixer, double Q, replay capacity 5,000,
  uniformly sampled 32 complete episodes without replacement, one RMSprop update per new
  episode from episode 32, and target copies every 200 complete episodes. Preserve all
  B01 architecture, lr 0.0005/optimizer, clipping and epsilon settings: 1→0.05 over 50,000
  training ticks, measured at episode start. No curriculum, tuning or alternate baseline.
- Keep primitive gamma 0.99 and no bootstrap at the true 20-step cooperative terminal.
  A car's departure does not terminate that episode. The terminal controller pass is not
  a native action or survivor-control opportunity. The discounted Q-learning procedure is
  a shared finite training method; it does not guarantee exact optimization of the
  **undiscounted complete native reward sum** used for final evaluation.

**Training seed 7802; final evaluation seed 107802.** These are fixed once, before new
implementation or output, as the next unused pair after 7801/107801; no seed search is
performed. Each arm starts a new process and resets Python, global NumPy and Torch to 7802
before the identical actor/mixer construction order. Within B02, RETAIN and RESET therefore
have matched initial parameter generation. Across B01/B02, create fresh actor/mixer/targets,
optimizer, replay and environment state: no checkpoint, trajectory, replay, optimizer or
hidden-state warm start is reused.

Native traffic and source-compatible replay retain their global NumPy plumbing; the source
Torch epsilon selector retains its draws, including greedy and terminal passes. Before the
single final evaluation, reset all three RNGs to 107802 and start a fresh evaluation
environment. A different seed label alone is not the independence argument: the fresh
complete generation/training process with no reused state/data is the intended independent
unit, under the ordinary PRNG assumption. Equal within-pair seeds do not force equal traffic:
different actions can change collision, departure, activation and RNG consumption.

## 3. Endpoint, reading rule and predictions

Each arm trains for exactly 5,000 complete episodes/4,969 optimizer steps, then receives
**one frozen final checkpoint and 32 greedy episodes (epsilon zero)** under its trained rule.
No periodic evaluation, checkpoint selection, extra final evaluation or evaluation-only
intervention is added. Let `d_02 = J_RETAIN,02 - J_RESET,02`, using every final native episode
return. Training returns remain separately reported training exposure.

**Absolute MEI = 1.0 native return unit per episode.** Preserve B01's concrete scale: one
native target-progress unit and one tenth of a single -10 collision penalty. This makes the
new measurement directly comparable without dividing by a small or negative return.

- `d_02 >= 1.0`: `RETAIN_ABOVE_MEI` for this new pair.
- `d_02 <= -1.0`: `RESET_ABOVE_MEI` for this new pair.
- `-1.0 < d_02 < 1.0`: `WITHIN_MEI` for this new pair, not equivalence.

How the result will be interpreted: another RESET-above-MEI point would support repeatability
at these two training instances and motivate considering further bounded performance work;
an inside-MEI point would weaken the immediate repeatability case; a RETAIN-above-MEI point
would establish opposing observed signs and favor withholding a general winner claim.
None automatically launches a successor or closes a family. A new negative is preserved on
the same terms as a new positive; no requirement that every seed improve is introduced.

Primary classification uses `d_02` alone. Always display `d_01` and `d_02` separately; their
two-pair mean may be descriptive, but it cannot replace the new-pair branch or rewrite B01.
Use one endpoint row per training run in the paired run analysis. The 32 episodes per arm
are conditional rollouts; even two training pairs cannot establish stable population
superiority, mechanism localization or transfer. No same-index episode pairing is treated
as a common exogenous event tape.

**DM prediction, outcome-informed but before B02 output:** `RESET_ABOVE_MEI` is now the
leading prediction because B01 supplies a trustworthy above-MEI native point. Confidence is
limited by one prior pair, its broad rollout spread and the adverse training-return comparison;
WITHIN_MEI and a RETAIN reversal remain plausible. Owner prediction: **not taken (unattended)**.

If either arm has zero actual survivor-control opportunities, the corresponding memory-action
interpretation is limited; trustworthy full returns remain reportable under §11.8.7. Do not
filter evaluation episodes by events or divide returns by reset counts to claim pure erasure
value. No typed-state novelty, strictly-self ancestry, information necessity, original-CAMA
performance, stable superiority, UAV or Portfolio claim is sought.

## 4. Runner-derived work and prospective limits

The [machine-generated plan](evidence/2026-09-09-folr-public-lifecycle-b02-plan.json) reads the
existing runner/collector as syntax, without importing or running target code.

| Work quantity | Per arm | Whole new pair |
| --- | ---: | ---: |
| Training episodes / native ticks | 5,000 / 100,000 | 10,000 / 200,000 |
| RMSprop steps | 4,969 | 9,938 |
| Final evaluation episodes / native ticks | 32 / 640 | 64 / 1,280 |
| Total native ticks | 100,640 | 201,280 |
| Acting GRU row forwards, terminal pass included | 528,360 | 1,056,720 |
| Online-plus-target replay GRU row forwards | 33,391,680 | 66,783,360 |

Dominant work is `2 arms × 4969 updates × 32 replay episodes × 21 positions × 5 slots ×
2 actor passes`, plus online backward and mixing; acting is `2 × 5032 × 21 × 5` rows.
These reused rows are not independent samples. There is no nested search, solver,
counterfactual rollout or selected-checkpoint sweep. Prospective exposure per arm is
**100,000 real training ticks; 4,969 trainable actor/mixer RMSprop steps at lr 0.0005;
32 final greedy evaluations**. Nominal lr×steps=2.4845 is not parameter displacement.

| Complete wall planning | RETAIN | RESET | Pair |
| --- | ---: | ---: | ---: |
| B01 same-workload point reference, seconds | 770.69 | 746.89 | 1,517.58 |
| B02 prospective hard limit, seconds | 1,800 | 1,800 | 3,600 |
| B02 actual elapsed | unmeasured | unmeasured | unmeasured |

The dominant loop work ratio to B01 is 1.0 on the same CPU FP32/thread topology. The point
reference is not a guaranteed upper bound or new consumed cost; fresh trajectories and
contention can change wall. No cost-only run is needed. The cap covers the complete logical
invocation, including startup/imports, learning, final evaluation and publication.
Prospective supporting seed-plumbing checks and artifact readbacks have a **60s total** cap,
including necessary correction reruns; this is added verification, not algorithmic exposure.

Under the §6 allocation, run exactly RETAIN then RESET, regardless of an intact first-arm sign.
No pilot, retry, tuning, extra evaluation, local fallback or automatic successor is included.
Admission failure, a cap, damaged primary path or exhausted scoped engineering/check budget
returns the exact boundary without another scientific invocation. The original preparation had
zero target imports/calls, simulator steps, learning/evaluation, resource admissions and runs.

## 5. Engineering scope, acceptance and execution boundary

Reuse the four B01 §4 telemetry quantities because this claim still needs their actual
exposure: **births, departures, true-survivor control opportunities and actual survivor
resets**, separately for training and final evaluation in each arm. Their counting rules
are exactly [B01 card §6](FOLR_PUBLIC_LIFECYCLE_B01_SCIENCE_CARD_20260909.md#6-required-counts-engineering-scope-and-acceptance):
birth/departure counts include terminal native steps and exclude initial births; opportunity
and reset counts require a subsequent native action, excluding terminal passes, entrant/episode
clears and replayed rows. No new counter or other §4 machinery is needed. Reuse the one final
learner checkpoint/publication and existing supervisor; add no resume, registry, guard,
validation framework, compatibility shim, profiling or repeated semantic smoke.

The [five-item CM assignment](FOLR_PUBLIC_LIFECYCLE_B02_CM_ASSIGNMENT_20260909.md) names the
small change: allow training seed 7802 and explicit final-evaluation seed 107802 through the
existing runner, with all actual seed uses and reported values agreeing. Reuse the accepted
environment/model/learner/collection modules and their semantic evidence. Preserve original
7801/107801 defaults; B01's immutable launch and artifacts remain untouched. A focused seed
routing/publication check is required for this changed boundary; the unchanged full scientific
suite is not repeated merely for a new object. CM retains engineering acceptance. If a
concrete semantic discrepancy appears, return it to DM without changing the question.
Ordinary 2,000 new non-test-source/600 runner line limits remain; no new framework is needed.

Use the shared `C:/Projects/HMASD-worktrees/codex-vap-folr` / `codex/vap-folr` checkout.
The original preparation dispatched no CM and edited no source. Under the later §6 allocation,
portable execution uses configured `hmasd-wsl-node` and `/home/wu/.venvs/hmasd/bin/python`,
CPU FP32, one Torch compute and interop thread, native NumPy arithmetic. Host identity is
not the estimand; no device/dtype/topology substitution follows. Commit/push exact new source,
create a new detached exact-SHA execution worktree, and use fresh B02 output roots. The B01
execution worktree/handles have been archived and reclaimed and must not be resumed.

Immediately before each arm, join destination `admit-memory` and its exact runner
with `&&`, requiring physical/effective available memory at least 4 GiB before scientific
roots, RNG or model creation. CM records actual SHA/command/node/cwd/root, receipt and
accepted supervisor handle and owns observation through collection. Execution facts and
complete results are recorded by CM and taken in by DM; Root integrates the accepted return.

## 6. Execution allocation and prediction before output — 2026-09-09T20:05:36Z

Root accepted the narrow source, technical evidence and DM intake, integrated them on main,
then allocated exactly two accepted arm submissions: one RETAIN and one RESET at training
seed 7802/final evaluation seed 107802. The original CM executes them sequentially from
the committed/pushed source `434f10cf95f16dd342cbf754382aa76155fcd2b7`, on fresh detached
remote execution state, and observes each accepted handle through terminal publication and
verified collection. The shared authoring checkout remains `codex/vap-folr`; no new
authoring branch or B01 recovery is involved.

**Object-tier execution selection:** (a) execute the frozen independent training pair;
(b) defer it and retain only B01's observation. Recommend/select (a), because the next
observation must test the complete trained effect on a new independent fitting process.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a), under Root's new finite
execution allocation.** This is not a priority, lifecycle, comparator or direction change.

The §3 prediction remains **RESET_ABOVE_MEI**, outcome-informed from B01 and recorded before
any B02 output; confidence remains limited. Owner prediction: **not taken (unattended)**.
The inclusive ±1 branches apply to `d_02` alone, with B01 displayed separately. All §2–5
science, exposure, host/device and result interpretation stay fixed.

Complete limits remain 1,800s per arm and 3,600s per pair. The 60s supporting-check/readback
budget includes CM's already spent 3.0730197s and DM's 0.0661974s: **3.1392171s spent,
56.8607829s remaining at this allocation**. Reuse the two controlled cases and unchanged
semantic acceptance; no native smoke or repeated scientific check is allocated.
Pre-acceptance technical failures may be repaired within the existing rules/budget;
uncertain acceptance is reconciled against the same handle. A failed scientific attempt
retains evidence and returns without a replacement. No missing arm is silently paired.
There is no pilot, tuning, additional seed/arm, diagnostic, retry or automatic successor.

CM records per-arm and complete study timing, keeping summed invocation wall, aggregate CPU
work and elapsed critical path separate. The completed return includes all outcomes,
resource receipts, exact commands/handles, collected artifacts and cleanup inventory. DM
performs scientific intake, prediction scoring, the Chinese brief and audit; Root handles
integration and any later successor allocation. Previously blocked scratch stays with CM.
