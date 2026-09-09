Claim under test: the observed trained RESET advantage may recur in one further fresh RETAIN/RESET pair at the same finite exposure.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR-PUBLIC-LIFECYCLE-B03 — one further independent training pair

## 1. Question, authority and retained evidence

**B/EXPLORE; Root allocated one fresh pair on 2026-09-09 after accepting B02 through
main `71c781aec`.** This card and its prediction precede all B03 scientific execution.
The [intake §1](FOLR_PUBLIC_LIFECYCLE_B03_INTAKE_20260909.md#1-prospective-allocation-and-reading)
records the allocation and object-tier selection. It authorizes exactly two accepted
scientific submissions, one per arm, followed by collection and scientific intake.

Question: does the final native RESET preference recur in another independently initialized
and trained pair under the same complete package? B01 gave `d_01=-2.0021875`; B02 gave
`d_02=-1.9228125`, both RESET_ABOVE_MEI. These are two observed training pairs, with wide
conditional evaluation variation. Their mean is descriptive. B01's lower RESET training
return and missed WITHIN_MEI prediction remain visible; B02's leading RESET prediction
matched. The [B02 intake §§3–6](FOLR_PUBLIC_LIFECYCLE_B02_INTAKE_20260909.md) supplies their
bounded interpretation. This continuation is outcome-informed and uses no candidate-seed
search, minimum seed quota or confirmatory relabelling.

Same-information tuned baseline/upper headroom on this public-lifecycle host remains absent.
Reuse the existing generic actor/mixer baseline set because observations, actions,
information, host and exposure match; these fixed-configuration points are not tuned headroom.
The question concerns complete trained packages, including optimization/data paths and
partner co-adaptation. It does not isolate harmful memory contents or compare identical traffic.

## 2. Unchanged scientific recipe and fresh randomness

The preserved recipe is [B02 card §2](FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md#2-preserved-package-and-fresh-randomness),
with its explicit B01 scientific contract references. Reuse accepted source
`434f10cf95f16dd342cbf754382aa76155fcd2b7` and the existing
`scripts/run_folr_public_lifecycle_b01.py`; its unrestricted seed arguments need no edit.

Native CAMA easy Traffic Junction remains five slots/five actions, vision 1, 7×7 grid,
20 primitive steps and add rate 0.1. Keep native reward and side effects. Actual departures
D and births B, including same-step replacement, define true survivors
`C=A_before & A_after & ~D & ~B` and public event `E=any(D | B)`. These facts arrive after
the native transition and before the next actor update. Both actors receive the same local
attention input plus public E and own B; mixer information is unchanged. This is the
explicit public-lifecycle extension, not original-CAMA information.

New trips start fresh, inactive state is zero and only true survivors retain the legal
preceding action before attention. RETAIN carries true-survivor GRU state. RESET clears
that state on E before processing the next observation. Acting, online replay and target
replay preserve their respective rules. Slot reuse never establishes entity continuity;
full survivor history can contain teammate information. RESET retains current information
and history between events. Native events thus change entity-owned state available for
action, the replayed learning path and potentially native reward; no causal localization
within this chain is claimed.

Keep entity-attention GRU64/FlexQMixer, double Q, replay capacity 5,000, uniform 32-complete-
episode sampling without replacement, one RMSprop update per new episode from episode 32,
target copies every 200 episodes, lr 0.0005, source optimizer/clipping and epsilon 1→0.05
over 50,000 training ticks measured at episode start. Primitive gamma remains 0.99 with no
bootstrap at the true 20-step cooperative terminal; an individual departure is not terminal.
The final controller pass is not a native action or survivor-control opportunity. This
approximate discounted Q-learning does not guarantee exact optimization of the undiscounted
complete native return used for final evaluation.

**Training seed 7803; final evaluation seed 107803.** Fix the next unused pair in the
direction's public-lifecycle records once before B03 output. Each arm uses a new process,
resets Python/global NumPy/Torch to 7803 before identical actor/mixer construction order,
and creates new targets, optimizer, replay and environment. Reuse no earlier checkpoint,
trajectory, optimizer, replay or hidden/RNG state. Under the ordinary PRNG assumption this
fresh complete generation/training process supplies the independent fitting unit; seed
labels alone do not establish independence.

Keep native traffic and source-compatible replay on global NumPy, and preserve source
Torch epsilon draws including greedy/terminal passes. Before the sole final evaluation,
reset all three RNGs to 107803 and create a fresh evaluation environment. Within-pair
initialization is matched; actions can change traffic and RNG consumption, so equal seeds
do not imply an exogenous common-event tape or justify pairing same-index episode returns.

## 3. Endpoint, reading rule and prediction

Each arm trains **5,000 complete episodes / 100,000 native ticks / 4,969 RMSprop steps**,
then publishes one final checkpoint and evaluates it in **32 greedy episodes** under that
arm's trained rule. Use every final native episode return. No intermediate checkpoint
selection, periodic evaluation, extra evaluation or evaluation-only intervention is added.
Training return is reported separately. Define `d_03 = J_RETAIN,03 - J_RESET,03`.

**Absolute MEI = 1.0 native return unit per episode**, the existing scale of one target-
progress unit and one tenth of a single -10 collision penalty. This preserves direct
comparability without ratios around small or negative returns.

- `d_03 >= 1.0`: `RETAIN_ABOVE_MEI` for this new pair.
- `d_03 <= -1.0`: `RESET_ABOVE_MEI` for this new pair.
- `-1.0 < d_03 < 1.0`: `WITHIN_MEI` for this new pair, not equivalence.

How the result will be interpreted: another RESET-above-MEI point would strengthen the
bounded repeatability observation across these fitting instances and justify reassessing
the next useful performance question. An inside-MEI point weakens the immediate
repeatability case; a RETAIN-above-MEI point establishes opposing observed signs and favors
withholding a general winner claim. Every outcome is retained. None automatically selects
another invocation or changes a family, priority, lifecycle or C/UAV status.

The branch reads `d_03` alone. Display B01/B02/B03 separately; a descriptive aggregate must
not replace this branch. The independent unit is one final endpoint per fresh training run,
with declared matching across arms. Conditional evaluation episodes are not training seeds.
Three fitting instances still do not establish stable population superiority, transfer or
why clearing helps. No typed-state novelty, strictly-self ancestry, information necessity,
original-CAMA performance or UAV conclusion is sought. If a required counter fails or an
arm has zero survivor-control opportunities, limit its dependent memory-action reading
while preserving independently trustworthy returns under evidence-spec §11.8.7.

**DM prediction, outcome-informed but before B03 output: RESET_ABOVE_MEI.** Two intact
above-MEI final observations make this the leading branch. Confidence remains limited by
two prior pairs, large conditional rollout spread and finite optimization/partner effects;
WITHIN_MEI and reversal remain plausible. Owner prediction: **not taken (unattended)**.

## 4. Work, per-arm projection and finite allowance

The [machine-generated plan](evidence/2026-09-09-folr-public-lifecycle-b03-plan.json) checks
the unchanged runner/collector loop syntax and computes the following without importing
target code or running a simulator.

| Quantity | Per arm | New pair |
| --- | ---: | ---: |
| Training episodes / native ticks | 5,000 / 100,000 | 10,000 / 200,000 |
| RMSprop steps | 4,969 | 9,938 |
| Final episodes / native ticks | 32 / 640 | 64 / 1,280 |
| Total native ticks | 100,640 | 201,280 |
| Acting GRU row forwards, terminal included | 528,360 | 1,056,720 |
| Online-plus-target replay GRU row forwards | 33,391,680 | 66,783,360 |

Dominant algorithm work is `2 arms × 4969 updates × 32 replay episodes × 21 controller
positions × 5 slots × 2 actor passes`, plus backward and mixing. Acting is
`2 × 5032 × 21 × 5` rows. Replayed rows are not independent samples. No nested search,
solver or validation candidate is added. **Exposure per arm: 100,000 real training ticks;
4,969 trainable actor/mixer RMSprop steps at lr 0.0005; 32 final greedy evaluations.**
Nominal lr×steps=2.4845 is not parameter displacement.

| Complete invocation wall, seconds | RETAIN | RESET | Pair |
| --- | ---: | ---: | ---: |
| B01 observed | 770.69 | 746.89 | 1,517.58 |
| B02 observed | 767.84 | 753.11 | 1,520.95 |
| B03 point projection, mean at work ratio 1.0 | 769.265 | 750.000 | 1,519.265 |
| B03 hard limit | 1,800 | 1,800 | 3,600 |

These are same-workload CPU FP32/one-compute-and-interop-thread observations, not guaranteed
upper bounds or new cost. Different trajectories and contention may change wall. The caps
cover each complete logical invocation: imports/startup, training, final evaluation and
publication. **Total new-object supporting checks and artifact readbacks: 60 seconds.**
Added verification is distinct from algorithm work; record actual supporting costs.

Run RETAIN then RESET sequentially, one accepted scientific submission per arm. An intact
first arm's sign does not select whether RESET runs. No scientific retry/replacement,
third arm, tuning, diagnostic, smoke, additional evaluation, local fallback or automatic
successor is authorized. A failed scientific attempt ends its allowance; preserve its
facts and return the exact boundary. Reconcile uncertain acceptance through the same
handle. A failed admission, exhausted cap or primary-path defect supplies no scientific
polarity and adds no invocation.

## 5. Engineering acceptance and observation ownership

Engineering Scope Spec §4 needs exactly the already implemented telemetry quantities
**births, departures, true-survivor control opportunities and actual survivor resets**,
separately in training/final evaluation per arm. Reuse [B01 card §6](FOLR_PUBLIC_LIFECYCLE_B01_SCIENCE_CARD_20260909.md#6-required-counts-engineering-scope-and-acceptance):
birth/departure counts include terminal steps and exclude initial births; opportunity/reset
counts require a subsequent native action and exclude terminal passes, entrant/episode
clears and replay rows. No new §4 machinery is needed. Reuse the learner's final checkpoint,
existing detached supervisor and whole-process timing; add no research monitor framework.

No source change is needed. Reuse [B02 accepted two-case seed-routing evidence](FOLR_PUBLIC_LIFECYCLE_B02_ENGINEERING_RESULT_20260909.md)
and unchanged B01 semantic independent review; do not rerun tests without a concrete new
source change or risk. Acceptance checks the declared seeds, complete learner/evaluation
counts, native endpoint, counters and existing process/artifact receipts. Code success is
engineering evidence, not mechanism value. Evidence spec §§4, 5.2 and 11.4/11.8 control;
only §11.4's four items may hold an ordinary B launch.

Use shared authoring checkout `C:/Projects/HMASD-worktrees/codex-vap-folr` on
`codex/vap-folr`, serializing overlapping edits/index operations with the original CM.
The accepted source is already committed/pushed. Publish this card before launch, then
use a **new** detached remote execution worktree at source `434f10cf95f16dd342cbf754382aa76155fcd2b7`
and fresh B03 roots. Do not reuse the archived/reclaimed B01 or B02 execution worktrees.
Execution is `hmasd-wsl-node`, `/home/wu/.venvs/hmasd/bin/python`, CPU FP32, one Torch
compute and interop thread with native NumPy arithmetic. Host identity is not the estimand;
this allocation includes no node/device/dtype/topology substitution. Each arm has its own
fresh destination memory admission joined to its exact runner by `&&` under `agent-task`.

**Live control-plane policy:** CM reads `C:/Projects/HMASD/docs/project/EXPERIMENT_MONITOR.md`
and `C:/Projects/HMASD/.codex/hmasd-monitor.toml`, including Root's `4f216bc9e` address
calibration. Do not read the Monitor destination from frozen source434 or a stale direction
checkout. After each accepted launch CM sends MONITOR_ADD directly to shared task
`01a087e5-2044-7301-abb6-7a1709a98197`, naming node/handle/source/cwd/output/receipts and
original CM, DM and Root `01a07249-b095-7821-8ce2-e9c32ba85267`. The Monitor reads its goal,
continues an active set-scoped goal, or creates one for a nonempty assignment if none is
active, without an invented token budget. No duplicate goal or unsupported objective edit.
CM records accepted dispatch with adoption pending and returns pending collection; CM/DM/
Root do not run parallel routine status polls. Monitor adoption/terminal notices go directly
to Root, which confirms adoption and resumes the original CM/DM for collection/intake.
Dispatch is not adoption, and terminal exit is not technical or scientific acceptance.

The original CM owns complete terminal collection/technical acceptance and its later
verified preservation/closeout after Root's trigger. DM owns scientific intake, all outcomes,
prediction scoring and the Chinese valid-result brief. Root owns integration, tracking,
capacity and acceptance of reclamation. Neither a pending Monitor boundary nor a child's
return finishes the allocated B03 batch.
