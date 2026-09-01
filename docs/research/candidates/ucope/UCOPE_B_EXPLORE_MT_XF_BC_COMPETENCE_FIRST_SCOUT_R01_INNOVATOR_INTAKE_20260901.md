# UCOPE competence-first three-arm B scout innovator intake — 2026-09-01

## Pro decision

The complete persistent `em:ucope:innovator` response for request
`ucope-em-innovator-20260901-03` decides:

```text
FINAL_INNOVATOR_DECISION=SELECT_OBJECT
DECISION_AUTHORITY=PRO_FINAL
DECISION_FORMED=true
BLOCKER=NONE
SELECTED_OBJECT_ID=UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01
EVIDENCE_CLASS=B/EXPLORE
```

The selected object is a fresh, adaptive three-arm B study family. It is not a one-shot C object.
Every named run is frozen and reproducible, while later B runs may change declared settings after
the earlier observations when the change and reason are recorded and every earlier result remains
visible.

The archived response is
`temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-innovator-20260901-03/RESPONSE.md`,
SHA-256 `085fd946c6c7453929912864d192d026a85f6fd14588c37355c5d5c4e64512ed`.
Transport records natural completion through the persistent provider conversation
`6a963684-685c-83e8-a894-439bb35203d6`, with exactly one provider send and all ten manifest paths
read through the connected GitHub connector at
`f198cedf8b0bb2c06b6e79ed3415e08b6e197477`.

## Smallest proposition and ceiling

On a fresh paired population from the finite eight-context UCOPE host, with raw information, data,
folds, evaluation, and optimizer-update counts held fixed:

1. does replacing current moving root targets with final cross-fitted targets improve held-out
   competence at a fixed flexible learner class;
2. does replacing that flexible learner with a low-dimensional Bellman-complete learner change
   competence under the same fixed targets; and
3. only for learner seeds that first pass competence, does the endogenous greedy policy obtain
   positive paid-acquisition value over the strongest immediate-commitment null?

The maximum claim is a preliminary finite-host B/EXPLORE statement about competence and,
conditional on competence, endogenous paid acquisition for a named learner package on the observed
UCOPE setup. It supplies no stable superiority, lifecycle conclusion, consumed-object rescue, pure
representation-versus-optimization attribution, premature COUNT/RAW polarity, seed-superpopulation
inference, generic paid-information value, general variable-`k`, variable-`N`, MARL or UAV value,
safety, deployment, flight, energy, or real-world QoS claim.

## Common host and information

The finite contextual host is:

```text
link        in {LINKED, SEVERED}
reliability in {13/20, 17/20}
probe cost  in {9/100, 7/50}
K_train     = {1,3,5,7,9}
K_eval      = {2,4,6,8}
marks       = 6
horizon     = 12
```

Before training, every named run must verify that the direct probe contribution is negative in all
eight contexts; exactly `LINKED × 17/20 × 9/100` has positive oracle net acquisition value; the
other seven contexts favor IMMEDIATE; and all relevant oracle choices are unique. Failure is a
nondiscriminating-host observation, not learner evidence.

All learned arms receive the same BELIEF-level information. RAW mark sequences and COUNT-versus-RAW
inputs are absent. Candidate action scoring uses

```text
x = (1, phase_tail, a, k/9, b, C, L, p, L*p)
```

where `a=1` denotes root PROBE and `a=0` IMMEDIATE, `k=0` for root PROBE and otherwise the candidate
period, `b=1/2` at root and the posterior SHORT belief after six displayed marks at tail, `C` is
probe cost, `L` linkage, and `p` mark reliability. The explicit Bellman bases are

```text
z_T = (1, b, k/9, b*k/9, (k/9)^2)
z_R = (1, (1-a)*k/9, (1-a)*(k/9)^2,
       a, a*C, a*L, a*L*p)
```

No held-out even-`K` outcome or oracle action may enter fitting.

## Ordered three-arm ladder

### Arm 1 — MT-XF-FLEX

This is a moving-target, group-cross-fitted flexible learner. For root fold `f`, train the tail
scorer on complementary fold `1-f`; root examples come only from `f`. Recompute every PROBE root
minibatch target from the current complementary-fold tail scorer:

```text
y_PROBE     = realized_probe_primitive
              + max_{k in K_train} Q_tail_current(b,k)
y_IMMEDIATE = realized_tail_return
```

The nested Bellman-residual scorers are

```text
Q_T = beta_T · z_T + residual_T(x)
Q_R = beta_R · z_R + residual_R(x)
```

with separate two-hidden-layer `64→64` ReLU residual networks. This is a fresh mechanism test, not
a rerun of historical BELIEF v2.

### Arm 2 — FT-XF-FLEX

This is the target-frozen, group-cross-fitted flexible arm and the strongest learned
same-information null for the low-dimensional arm. Architecture, information, fresh data, folds,
parameter initialization, optimizer, batches, example counts, and final update counts match
MT-XF-FLEX. Train the complementary tail scorer first, freeze it, and materialize all root targets
once before root optimization:

```text
y_PROBE = realized_probe_primitive
          + max_{k in K_train} Q_tail_frozen(b,k)
```

`MT-XF-FLEX` versus `FT-XF-FLEX` tests the composite target-schedule/credit-construction package at
fixed flexible architecture. It does not isolate every historical difference.

### Arm 3 — FT-XF-BC

This is a target-frozen, group-cross-fitted, gradient-trained low-dimensional Bellman-complete
learner:

```text
Q_T = beta_T · z_T
Q_R = beta_R · z_R
```

It uses the same fresh data, folds, tail-first target materialization, batch size, update counts,
precision, optimizer family, and evaluator as FT-XF-FLEX and must have nonzero optimizer updates.
It is not the consumed exact least-squares structural certificate and cannot read that object's
coefficients, fits, tapes, slot outcomes, or policies.

`FT-XF-FLEX` versus `FT-XF-BC` tests a finite-budget learner-package difference jointly involving
inductive bias, conditioning, parameter count, and optimization geometry. It is not a pure
representation or optimizer effect.

### Evaluation controls and excluded factors

`IMMEDIATE-DP` is the strongest no-acquisition null: it chooses the best immediate held-out even
period in each context without probing. It is an evaluator, not a fourth trained arm. The exact
BELIEF oracle is an evaluation ceiling and supplies the expected target-only root vector; it cannot
produce training targets, select checkpoints, or guide optimization.

An `MT-XF-BC` factorial arm is excluded from B1. A later named B run may add it only if B1 shows a
plausible target-by-parameterization interaction and records that reason. All arms use separate
root and tail optimizer states and per-scorer clipping; shared global clipping is excluded so it
cannot contaminate the target-schedule contrast.

## Fresh population and consumed-artifact firewall

B1 uses three new seed identifiers in a namespace disjoint from every consumed
`cpa-r01-fresh-slot-*` slot. For every seed and each of the eight contexts, generate `5,120` fresh
environment episodes. The arm-independent schedule repeats ten-episode blocks containing exactly
one instance of each action-period training stratum:

```text
PROBE × each k in K_train
IMMEDIATE × each k in K_train
```

Each context therefore has `512` episodes per stratum. The observational group is
`(run_id, seed_id, episode_index)`. All eight context episodes with that group share the designated
RNG ancestry and remain in one fold:

```text
fold_id = floor(episode_index / 10) mod 2
```

Each context/fold has `256` groups per action-period stratum. Report displayed-count support
`0..6`. A completely absent count in any seed/context/fold makes that seed support-limited and bars
competence and acquisition interpretation for it; this is a valid B support observation rather
than a technical failure.

The new family may reuse only public host equations and action semantics, BELIEF posterior
construction, the context grid, accepted competence definitions, oracle and IMMEDIATE evaluation
semantics, and general implementation modules that CM confirms do not read consumed result state.

It must not reuse as data, initialization, targets, model selection, tuning evidence, or causal
controls:

- the 80 consumed BELIEF tapes or ten consumed BELIEF seed slots;
- BELIEF checkpoints or learned scores;
- structural fits, coefficient files, or certificate policies;
- the three failed structural slot/fold identities as sampling targets; or
- historical signs or metrics to choose favorable seeds, folds, thresholds, checkpoints, or count
  states.

The consumed BELIEF `0/10` and structural-prior `17/20` results appear only as immutable provenance.
They supply no paid-acquisition or COUNT/RAW polarity.

## Clocks, exposure, and B1 numerical contract

- **Event clock:** one root decision per episode; either IMMEDIATE commitment or paid PROBE; after
  PROBE, six marks and one tail commitment; external service, time, and energy are accounted through
  the fixed horizon.
- **Acquisition clock:** one endogenous acquisition opportunity at the root. Forced-PROBE
  evaluation is a tail-competence diagnostic only.
- **Credit clock:** MT-XF-FLEX recomputes root targets at every root update from the current
  complementary tail scorer. The frozen arms finish tail training, seal the tail scorer, and
  materialize root targets exactly once.
- **Learner-exposure clock:** report environment data, example exposure, target refresh or
  materialization, optimizer updates, checkpoint selection, and evaluation separately.

The exact initial B1 run uses batch size `256` and, for each arm, fresh seed, and fold policy,
`160` tail updates and `320` root updates. MT-XF-FLEX executes 160 deterministic cycles of one tail
update followed by two root updates. Both frozen arms execute all 160 tail updates, seal and
materialize targets, then execute all 320 root updates. Across three arms, three seeds, and two
folds, this is exactly:

```text
tail optimizer updates = 2,880
root optimizer updates = 5,760
total optimizer updates = 8,640
```

The adaptive study-family envelope for later named B runs is:

```text
fresh seeds per named run       = 1 to 5
episodes per context per seed   = 2,560 to 10,240
tail updates per fold policy    = 80 to 320
root updates per fold policy    = 160 to 640
```

After observing B1, EM may change data volume, budget, width, optimizer details, measurements, or
add the excluded factorial arm only in a separately named run with the change and scientific reason
recorded. Earlier adverse, null, unstable, and support-limited observations remain visible and
cannot be overwritten or relabelled as prospective confirmation.

Use FP32, squared regression loss, AdamW learning rate `3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`,
zero weight decay, and per-scorer gradient-norm clipping at `1`. FLEX initial tensors are paired
between moving and frozen arms; BC coefficients have a separate deterministic namespace.

Evaluate every policy after root updates `40`, `80`, `160`, and `320`. Only checkpoint `320` gates
the branch; intermediate curves are descriptive. At every checkpoint run exact finite enumeration
for root vectors, uniqueness, regret, and probability-weighted tail agreement, plus `64` fresh
paired environment evaluation episodes per context/fold/seed/arm. B1 therefore has `36,864`
sampled evaluation episodes in addition to exact enumeration.

Fresh data, folds, example inventories, BELIEF information, candidates, FLEX initial tensors,
batch order, update counts, checkpoints, and evaluation episode roots require exact parity.
Parameter count, FLOPs, and wall time are not equal between FLEX and BC; measure them and interpret
their contrast only as a learner-package comparison.

## Competence, acquisition, and COUNT/RAW gates

For final fold policy `P`, define competence:

```text
C(P) = all root and tail scores finite
       AND all evaluated choices unique
       AND eight-context root vector equals the oracle vector
       AND maximum expected regret <= 1/50
       AND minimum forced-PROBE tail agreement >= 19/20
```

A seed passes an arm only if both fold policies pass. An arm is `B_COMPETENT` if at least two of
three fresh seeds pass both folds. All seeds remain visible; none may be removed or replaced. This
is a preliminary stability screen, not a seed-population inference. Competence failure gives no
acquisition or COUNT/RAW polarity, and competence alone gives no acquisition polarity.

For each competent seed/fold, compute in the sole target context:

```text
Delta_acq = exact expected external return of the endogenous greedy policy
            - exact expected external return of IMMEDIATE-DP
```

A competent seed is acquisition-positive only if both folds probe only the target context,
`Delta_acq > 0` there, choose IMMEDIATE in every nontarget context, and retain a negative direct
probe component. An arm is `B_ACQUISITION_POSITIVE` only if the same at-least-two-of-three seeds
that established competence also pass acquisition. Sampled returns and intervals are diagnostics;
the exact finite-host return gates the branch.

COUNT/RAW remains locked unless `MT-XF-FLEX` or `FT-XF-FLEX` satisfies both `B_COMPETENT` and
`B_ACQUISITION_POSITIVE` in the same named run and same qualifying seeds. BC-only success does not
unlock it. A valid unlock authorizes only design of a separate B study comparing COUNT,
unrestricted RAW, and a prospectively specified permutation-invariant RAW treatment; it creates no
COUNT/RAW polarity.

## Ordered interpretation

1. Wrong revision/configuration, consumed-artifact or held-out leakage, unequal data, missing
   telemetry, zero transitions/updates/evaluations, nonfinite training state, absent final
   checkpoints, resource failure, or incomplete publication is an incomplete attempt with no
   science. Repair under a separately named attempt.
2. An invalid opportunity map is a nondiscriminating host. A wholly absent displayed count makes
   the affected seed support-limited. Neither permits learner interpretation.
3. Apply competence to all arms and report every seed/fold and learning curve. No arm competent
   means no acquisition interpretation and COUNT/RAW remains locked.
4. Adjacent arm separations are preliminary target-package or learner-package signals only.
5. Evaluate acquisition only for competent arm-seeds. Competent non-acquisition is bounded to that
   package and setup.
6. FLEX competence plus acquisition produces only a preliminary finite-host acquisition signal and
   unlocks design of the separate COUNT/RAW B study.

The narrow target-freezing conjecture is contradicted on this setup if paired MT-XF-FLEX reaches
competence in at least two seeds no later than FT-XF-FLEX. The need for low-dimensional restriction
is contradicted if FT-XF-FLEX is competent and at least as stable as FT-XF-BC. If all three arms
show materially similar tail-agreement failures without learning-curve separation, retire this
host/budget realization as a discriminator rather than scaling it automatically. None of these B
observations closes UCOPE.

The strongest alternative is that fresh finite-sample exposure, odd-to-even extrapolation, fold
coupling, and tail-action conditioning dominate all three packages. A BC advantage may reflect
only easier optimization and fewer parameters; a frozen-target advantage may reflect sample-use
order and preprocessing rather than moving targets. Neither pattern diagnoses either consumed
object.

## Required CM and run tickets

Before the first full B run:

1. **CM implementation ticket:** implement the three arms, fresh data path, group-cross-fitted
   folds, target schedules, common evaluator, immutable consumed-artifact exclusion, and exact
   activity counters.
2. **A/RECON resource sizing:** use one fresh seed and reduced data/update counts solely to measure
   wall and CPU time, peak RSS/VRAM, worker/thread/process count, scratch, durable bytes, and
   aggregate I/O. It has no algorithm-effect authority.
3. **Per-run resource ticket:** freeze a small cap from sizing and, immediately before every named
   B invocation, require fresh physical and effective available memory of at least 4 GiB. Resource
   refusal or telemetry failure is an incomplete attempt.
4. **Telemetry ticket:** by arm/seed/fold/checkpoint record environment episodes/transitions, root
   and tail rows, target refresh/materialization counts, optimizer updates and example exposure,
   clipping and gradient norms, nonfinite events, exact and sampled evaluations, root vectors,
   regret, tail agreement, acquisition return and probe rates, parameters, FLOPs or auditable
   proxy, wall/CPU/GPU, RSS/VRAM, disk, scratch, and I/O.
5. **Publication ticket:** create-once run identity binding revision, configuration, seeds, data
   manifest, arms, telemetry, checkpoints, final result, and completion. Incomplete attempts remain
   outside completed-result namespace. Later named runs record every change and its scientific
   reason.

No additional formal certificate or C-level inference object is required before implementation of
this B family.

## Exact CM objective

Implement and observe `UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01` using the B1 contract
above. Generate one fresh paired population per new seed; instantiate the three arms without
reading consumed data or learned artifacts; preserve common information, folds, data, update
counts, and evaluation; publish complete curves and every seed/fold outcome; apply competence
before acquisition; keep COUNT/RAW locked until a FLEX arm passes both exact gates; perform the
non-scientific sizing ticket before the first full run; and freeze and record every named run and
every later adaptive change.

## Evidence paths

- `temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-innovator-20260901-03/RESPONSE.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-innovator-20260901-03/TRANSPORT_FACTS.json`
- `docs/research/portfolio/PORTFOLIO.md`
- `docs/research/portfolio/decisions/2026-09-01-empirical-standard-full-direction-reaudit.md`
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/candidates/ucope/DIRECTION.md`
- `docs/research/candidates/ucope/UCOPE_CONTEXTUAL_PAID_ACQUISITION_R01_BELIEF_RESULT_INTAKE_20260831.md`
- `docs/research/candidates/ucope/UCOPE_STRUCTURAL_COMPETENCE_VALID_RESULT_INTAKE_20260831.md`
- `docs/research/candidates/ucope/UCOPE_EM_CONVERGENCE_DECISION_INTAKE_20260831.md`
- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SUCCESSOR_PRO_INTAKE_20260831.md`
- `docs/research/candidates/ucope/UCOPE_STRUCTURAL_COMPETENCE_INNOVATOR_PRO_DECISION_INTAKE_20260831.md`
