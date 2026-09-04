# ACVC uncertain/delayed veto R01 — science card

- Direction: `acvc`
- Object id: `ACVC-B-EXPLORE-UNCERTAIN-DELAYED-VETO-R01`
- Evidence class: **B/EXPLORE**
- Frozen: `2026-09-04T10:55:03Z`, before implementation, technical calibration, or result run
- Direction authority: the final Portfolio decision
  `docs/research/portfolio/decisions/2026-09-01-empirical-standard-full-direction-reaudit.md`
  opened uncertain/delayed veto learning against competent confidence/freshness,
  authenticated-probe, and same-information recurrent controls. This card chooses the first rung
  inside that already accepted family; it does not open, close, park, or recast the direction.

## 1. Question, claim ceiling, and prior observation

In a twelve-opportunity episode, can a return-trained structured counterevidence gate use revealed
outcome history to adapt to episode-local variation in how informative an authenticated, exactly
bound, delayed verdict stream is, and thereby improve native return over the strongest competent
memoryless confidence/freshness rule and an authenticated-probe rule, without being contained by a
generic same-information recurrent learner?

The maximum claim is a preliminary one-seed mechanism signal or counterexample on the constructed
sequential host below. A positive result may show that history-dependent calibration is actionable
under this finite training budget, and may distinguish an ACVC-specific compression from generic
recurrence. It cannot establish stable superiority, seed robustness, necessity of learning,
variable-`N` or variable-`k` value, UAV or simulator transfer, cryptographic security, sender truth,
safety, flight value, deployment readiness, or general MARL performance.

The complete valid B1 result remains attached to its old synchronous truthful-verdict host:
correct binding improved the tabular learner over randomized binding, but the learner was worse
than `DET-BOUND`. R01 neither repeats nor repairs B1. It implements the Portfolio-authorized
successor condition that the same visible current verdict fields can require different actions
after different observed histories.

## 2. Mechanism prediction and live alternatives

The mechanism prediction is **history-conditioned counterevidence calibration**. Exact binding
establishes which opportunity a frame concerns, but authentication does not establish that the
sender is informative. Across several opportunities, execute/probe outcomes reveal whether the
episode's sender stream is calibrated or uninformative. A compact signed consistency state should
let a learned gate stop paying for low-value probes in the uninformative regime while retaining
veto/probe behavior in the calibrated regime.

The strongest live explanations are:

1. **Memoryless sufficiency:** the population-marginal Bayes risk computed from current confidence
   and age already selects the competent action; history adds no return.
2. **Generic recurrence:** history matters, but a generic recurrent learner using the same raw
   observations matches or beats the structured gate. That is evidence for recurrence, not ACVC's
   compression.
3. **Authenticated probing:** probing every bound negative captures the useful value cheaply enough
   that learned calibration cannot improve the native return.
4. **Learner/exposure limitation:** either learner fails to move or fails to learn a competent
   policy at the declared budget. This is not evidence that the underlying history is valueless.

## 3. Host, roles, information, and native consequence

One episode has twelve serial service opportunities owned by one receiver. Every opportunity has a
fresh opaque target and one authenticated frame whose binding exactly matches that target. Opaque
identifiers and authentication bytes are not learner features. The sender regime is drawn once per
episode and remains fixed:

- `CALIBRATED` with probability `0.5`: at issuance, the verdict matches latent unsafe state with
  the displayed confidence `q`;
- `UNINFORMATIVE` with probability `0.5`: at issuance, the verdict matches latent unsafe state with
  probability `0.5`, irrespective of displayed confidence.

For each opportunity, issuance-time unsafe state is Bernoulli `0.12`, confidence is independently
uniform on `{0.70, 0.90}`, and integer age is independently uniform on `{0,1,2}`. After issuance
and before the receiver acts, latent unsafe state flips independently with probability `0.10` per
age tick. The frame exposes only its negative-verdict bit, displayed confidence, age, exact binding
match, and authentication acceptance. It never exposes sender regime, issuance truth, current
truth, transition flips, arm, Q/value/logit state, or another arm's history.

The receiver chooses exactly one compound action:

- `EXECUTE`: reward `+1.0` if currently safe and `-4.0` if currently unsafe; the outcome reveals
  current truth.
- `PROBE`: pay `0.60`, reveal current truth, then execute iff safe and veto iff unsafe; reward is
  `+0.40` when safe and `-0.60` when unsafe.
- `VETO`: reward `0.0`; current truth is not revealed.

An episode ends after opportunity twelve; `gamma=1.0` and native return is the undiscounted sum.
Actions do not alter later latent draws. On the next opportunity, both learned arms observe the
same prior action and, when revealed, the same prior truth and prior verdict metadata. Divergent
actions may therefore create legitimately different revealed-history paths; no counterfactual
truth is supplied after `VETO`.

Trace: the environment event is a delayed noisy verdict about one target; the receiver owns the
execute/probe/veto action; available information is the authenticated bound current frame plus its
own prior actions and revealed outcomes; the credit path is the episode return; learner exposure is
the declared actor-critic update budget; the native consequences are return, unsafe execution,
probe cost, and lost safe service. There is no population membership change, slot reuse,
join/leave/rejoin, censoring, replacement, partner co-adaptation, or semi-Markov discounting in this
fixed-receiver host.

## 4. Treatment and comparators

All learned arms use FP32 on CPU, the same generated training/evaluation episode blueprints, the
same action set, reward, initialization law, actor-critic loss, optimizer settings, update count,
batch size, and evaluation tie order. No parameter, action sample, hidden state, gradient, or
checkpoint crosses arms.

### Treatment: `ACVC-HISTORY-GATE`

The treatment keeps a deterministic structured history summary from revealed opportunities. For
each revealed truth it adds

```text
+ strength(q, age)  when verdict_bit == current_unsafe
- strength(q, age)  otherwise

strength(q, age) = (2*q - 1) * 0.8**age
```

to a running consistency balance, clipped to `[-3,3]`, and records the revealed count clipped at
three. Its six normalized inputs are verdict bit, confidence, `age/2`, opportunity index divided by
eleven, consistency balance divided by three, and revealed count divided by three. They feed
`Linear(6,8) -> Tanh`, followed by separate policy and scalar-value linear heads. The summary is a
deterministic function of the raw history available to both learners; it introduces no extra
observation or oracle label. The action mapping is trained only through the common actor-critic
objective.

### Strongest same-information learned comparator: `RAW-GRU`

The comparator is a one-layer GRU with hidden width eight and policy/value heads. Its ten normalized
inputs are current verdict, confidence, `age/2`, opportunity index divided by eleven, previous
action as four-way one-hot (`NONE/EXECUTE/PROBE/VETO`), whether previous truth was revealed, and
that truth when revealed (zero when absent). This raw stream contains every quantity used to compute
the treatment's summary: the GRU saw the previous verdict/confidence/age before receiving its
revealed truth on the next step. The GRU is therefore the containing generic recurrent null; a
treatment advantage cannot be attributed to more information.

### Competent fixed comparators

`DET-CF` is the exact population-marginal memoryless confidence/freshness rule. It first marginalizes
the two equiprobable sender regimes, so issuance accuracy is `a_q=(q+0.5)/2`. With prior
`p0=0.12`, it computes issuance posterior `p_issue` by Bayes' rule from the displayed verdict and
then

```text
p_current = 0.5 + (p_issue - 0.5) * 0.8**age.
```

It chooses the action with maximum exact one-opportunity expected reward:

```text
EXECUTE: 1 - 5*p_current
PROBE:   0.4 - p_current
VETO:    0
```

Ties use `EXECUTE`, then `PROBE`, then `VETO`. This is the strongest policy that knows the frozen
population law and uses the current confidence/freshness fields but no episode history.

`AUTH-PROBE` executes on a positive verdict and probes on a negative verdict, irrespective of
confidence or age. `ALWAYS-EXECUTE`, `ALWAYS-PROBE`, and `ALWAYS-VETO` are reporting references,
not decision comparators.

## 5. Learner, RNG, and exposure contract

The learned arms use a batched advantage actor-critic objective with reward-to-go, `gamma=1.0`.
At every update, over all batch time steps, the loss is
`-mean(log_pi * stop_gradient(G-value)) + 0.5*mean((value-G)^2) - 0.01*mean(entropy)`.
Optimization is Adam with learning rate `0.02`, `eps=1e-8`, and global gradient-norm clipping at
`1.0`. Every linear/GRU weight is initialized from `Normal(0,0.05)` by the arm's initialization
namespace; biases and initial GRU state are zero. Each arm has one policy head over the three
actions and one scalar value head. Hidden/summary state resets at every episode. Evaluation is
greedy with tie order `EXECUTE`, `PROBE`, `VETO`. There is no validation selection, early stopping,
learning-rate schedule, checkpoint selection, or hyperparameter search.

Base seed is `11`. Independent deterministic namespaces derived from it own train worlds, train
actions, treatment initialization, GRU initialization, evaluation worlds, and fixed-policy
evaluation. Paired arms receive byte-identical environment blueprints at the same episode/update
coordinate; their action RNGs are independent. RNG ownership and every derived seed are published.

Training is exactly `128` optimizer updates of `64` complete episodes per update: `8,192` episodes,
`98,304` environment transitions, and `128` optimizer updates per learned arm. Evaluation is exactly
`4,096` fresh episodes and `49,152` transitions per arm. The fixed policies use the same evaluation
blueprints. Model-selection exposure is zero.

Before launch, the runner's non-result `project-cost` command must emit, for both learned arms:
parameter count, initialized parameter L2 and RMS scale, nominal clipped-gradient path
`128 * 0.02 * 1.0 = 2.56`, and the ratio of that path to initialized parameter L2. This is the
machine-generated exposure line required by evidence spec section 11.4. A zero/nonfinite scale or
ratio below `0.5` refuses launch. The result replaces the prospective line with actual initial/final
L2, displacement L2/RMS, displacement-to-initial ratios, nonzero-gradient update count, and action
entropy. Zero parameter displacement or zero gradient-bearing updates makes the attempt incomplete,
not a scientific branch.

## 6. Observables and estimand

The primary observable is episode return. For every arm report the mean, standard deviation, and
all `4,096` paired episode returns, plus regime-stratified means. Let `F` be the higher-return arm of
`DET-CF` and `AUTH-PROBE`, with ties resolved in favor of `DET-CF`. Primary paired effects are

```text
Delta_A = mean(return_ACVC-HISTORY-GATE - return_F)
Delta_G = mean(return_RAW-GRU - return_F)
Delta_AG = mean(return_ACVC-HISTORY-GATE - return_RAW-GRU).
```

Report ordinary paired 95% t intervals over evaluation episodes as environment-sampling
descriptions only; they do not represent independent training-seed uncertainty.

Also report per arm and regime:

- unsafe direct executions divided by unsafe opportunities;
- clean opportunity loss, `1 - opportunity_reward`, averaged over safe opportunities;
- direct execute, probe, and veto rates;
- revealed-history count and structured consistency balance distributions;
- return by confidence, age, verdict, opportunity index, and sender regime;
- nonzero train/evaluation transition and update counts, launch SHA, exact argv, elapsed wall time,
  and peak RSS when measured; and
- the exposure fields in section 5.

Missing resource telemetry leaves a valid result marked `resources_unmeasured`. Missing required
learner counts, per-arm returns, safety/clean observables, or exposure measurements quarantines the
attempt.

## 7. Frozen result rule

Define a learned arm as **harm-compatible** with `F` when its unsafe-execution rate is no more than
`0.02` above `F` and its mean clean opportunity loss is no more than `0.05` above `F`. Apply these
complete-result branches in order:

1. **`B2-A / STRUCTURED_GATE_SIGNAL`.** `Delta_A >= 0.25`, the treatment is harm-compatible, and
   `Delta_AG >= -0.10`. Reading: the structured history gate has preliminary finite-budget return
   headroom over both fixed controls and is not materially contained by the generic recurrent null.
2. **`B2-B / GENERIC_RECURRENCE_ONLY`.** `Delta_G >= 0.25`, `RAW-GRU` is harm-compatible, and branch
   A does not hold. Reading: revealed history is actionable, but this object does not identify value
   for ACVC's structured compression.
3. **`B2-C / FIXED_RULE_CONTAINS`.** Neither learned arm exceeds `F` by `0.10` while
   harm-compatible, or every learned improvement of at least `0.10` breaches a harm limit. Reading:
   the strongest fixed current-evidence control contains the learned policies on this host/budget.
4. **`B2-D / LEARNING_UNRESOLVED`.** Every other complete result. Reading: movement occurred, but
   the one-seed effects do not separate structured gating, generic recurrence, and fixed control.

No branch closes or parks the direction. A valid negative closes at most this host/budget rung.
Branch A may justify a three-seed B repeat with unchanged arms; branch B calls for an object-tier
recast of the ACVC representation before another run; branch C or D returns the bounded reading to
the direction's persistent Convergence node because selecting another object family is direction
tier.

## 8. Predictions on record

- **DM:** `B2-A / STRUCTURED_GATE_SIGNAL`. The current frame is informative in the population
  marginal, but revealed consistency should separate calibrated from uninformative episodes. The
  compact balance should learn that split faster than an eight-unit raw GRU at equal episode/update
  exposure while retaining the memoryless rule's safety behavior.
- **Owner:** `not taken (unattended)`.

## 9. Cost projection, caps, and stop rule

This is a paired seven-arm evaluation: two learned arms, two decision comparators, and three
reporting references. Per learned arm, the runner's operation law is `98,304` train decisions plus
`49,152` evaluation decisions. Per fixed arm it is `49,152` evaluation decisions. The non-result
`project-cost` command must benchmark two discarded updates of 64 episodes and 512 discarded
evaluation episodes under a separate technical seed, then emit

```text
projected_learned_arm_seconds = 3 * (
    measured_train_seconds_per_decision * 98,304
  + measured_eval_seconds_per_decision  * 49,152)

projected_fixed_arm_seconds = 3
  * measured_eval_seconds_per_decision * 49,152.
```

The factor three is the fixed host-load allowance. The cap is `600 s` per learned arm and `120 s`
per fixed arm. No arm launches if its own projection exceeds its cap. The result records actual
per-arm seconds and the formula inputs. `project-cost` discards all parameters and outcomes and
cannot select, tune, prune, or stop a scientific arm.

There is one result-bearing invocation in one CPU process and one computational thread. It stops
after all arms publish one complete `summary.json`, or immediately on a common-integrity breach,
failed fresh 4 GiB physical/effective memory admission, nonfinite learner quantity, zero learner
count, required-measurement loss, or per-arm cap. There is no result-informed rerun, extra seed,
arm drop, budget extension, resume, or checkpoint recovery. A reproduced implementation defect may
be repaired outcome-blind at a new SHA and launched as a fresh attempt; it has no scientific
polarity and does not consume this B object.

## 10. Protected semantics, side effects, and CM objective

CM must implement the smallest isolated research path that exactly preserves the host law,
information boundary, action/reward order, treatment summary, generic comparator, fixed
comparators, FP32 initialization/optimizer/update order, RNG ownership, counts, exposure line,
result rule, and side effects in this card. Expected owned paths are:

- `experiments/candidates/acvc/uncertain_delayed_veto_r01/`;
- `scripts/run_acvc_uncertain_delayed_veto_r01.py` (single runner, at most 600 lines);
- `tests/experiments/candidates/acvc/uncertain_delayed_veto_r01/`;
- scratch output under
  `temp/directions/acvc/exp/uncertain_delayed_veto_r01_20260904/`; and
- this object's result evidence and intake after DM interpretation.

Technical success means only that the declared learner/environment/evaluator ran and the required
measurements are complete. It cannot establish mechanism value or choose a scientific branch.
Historical B1 code/results are read-only. Core code, provider conversations, network actions, and
files outside the named source/test/scratch/doc surfaces are non-goals.

**Engineering-scope section 4 line: this object needs none of the default-prohibited machinery.**
It adds no multi-process execution, queue/scheduler, checkpoint/resume/retry, lease/heartbeat,
tamper evidence, provenance/currentness guard, incident tree, schema framework, registry,
compatibility shim, telemetry beyond wall time/peak RSS, or repeated smoke loop. New non-test
research code stays below 2,000 lines, the runner below 600 lines, orchestration below 30 percent,
and tests are one under-60-second end-to-end toy smoke plus result-rule/host-semantics tests. Any
budget breach is returned and recorded, never accepted as the price of a result.

## 11. Object-tier unattended decision

Options considered before implementation:

- **(a)** tune or repeat the old B1 truthful deterministic-verdict host;
- **(b)** run this one-seed uncertain/delayed, episode-calibration R01 with the competent
  confidence/freshness, authenticated-probe, and same-information recurrent controls;
- **(c)** jump directly to a three-to-five-seed transfer or C-BENCH-style object.

Recommendation: **(b)**. It is the smallest direct implementation of the already accepted B2
family, creates the missing same-visible-fields/opposite-history discriminator, and can reject
ACVC-specific value without paying for seed-level promotion. Option (a) cannot change the B1
reading; option (c) spends conclusion-bearing exposure before a one-seed mechanism signal exists.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** The choice is reversible,
changes no frozen prior object, and carries provenance label `OWNER_DELEGATED`.

## 12. Non-goals

Do not repair or rerun B1, claim binding necessity, weaken the deterministic or recurrent
comparators, add a hidden oracle feature, tune the host after a result, add variable population or
skill duration, introduce delayed credit beyond this twelve-opportunity episode, change core MARL
code, build production certificate machinery, or infer a direction/Portfolio lifecycle decision.
