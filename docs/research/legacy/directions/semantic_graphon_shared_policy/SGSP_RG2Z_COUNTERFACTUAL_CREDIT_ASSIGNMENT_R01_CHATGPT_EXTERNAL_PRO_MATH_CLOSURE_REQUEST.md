# SGSP RIDGEGATE-2Z counterfactual-credit revision-01 Pro closure request

You are continuing the existing dedicated SGSP scientific conversation. This
is one distinct, result-blind mathematical and causal closure request for the
complete prospective revision `SGSP-RG2Z-CCA-SCIENCE-20260820-01`. It follows
the complete r03 result-convergence finding of nonidentification but imports no
r03 value, seed, coordinate, policy or checkpoint.

Do not review code, runtime mechanics, hashes, receipts or implementation
correctness. Audit only whether the complete scientific object below is
mathematically and causally coherent. Return exactly `CLOSED`, or
`REVISION_REQUIRED` with every exact science-bearing defect and the resulting
claim boundary.

## Complete inherited object

The exact `RIDGEGATE-2Z` task is unchanged: twelve slots; balanced static public
roles; training `N={9,15}`; adaptation-free held-out `N={6,21}`; exact FIFO,
expiry, collision, detection, radio, base-link, waste, observation, message and
terminal-return laws; and no identity or future information in the policy.

The execution families are unchanged. `PHY-TRUST` and `EDGE-FLEX` have the
same 22-vector, message encoder, 32-vector role aggregation, exact 64-state GRU,
actor head, legal masks, `0.04` legal-uniform mixture, 18 count-dependent
residual coefficients, initialization and deployment work. PHY projects those
coefficients into `[-0.15,+0.15]`; EDGE uses `[-1.50,+1.50]` and literally
strictly contains every PHY policy.

The base budget remains 512 updates, 64 fresh factual episodes per update split
32/32 across the seen rosters, one full-batch backward per arm/update and the
sole evaluable checkpoint immediately after update 512. Projected Adam,
hyperparameters, float32 training, float64 inference and global clip `0.5` are
unchanged. The training-only team critic, its initialization, terminal-J loss,
Adam state, gradients and contribution to the joint global clip are retained
exactly, but its value is no longer used in the actor advantage.

Evaluation remains 24 independent fresh seed blocks, 256 episodes per roster
and seed, the exact intact/rotated/shadow/uniform cells, seed-level estimands,
18 two-sided paired-seed Bonferroni intervals, competence and answerability
gates, six margins, symmetric sender-column cut and four ordered branches. No
r03 stochastic object or result is reused, and there is no cross-trainer
estimand.

## Changed actor-credit rule

All 64 factual episodes and target continuations within update `u` use one
immutable pre-update parameter snapshot. At each factual agent-slot, retain the
complete state immediately after messages, role summaries, post-GRU hidden
states, legal distributions and factual joint actions exist, but before the
joint action changes the simulator.

For focal agent `i` and every currently legal action `a`, define one full-
horizon terminal-return sample by replacing only `i`'s current action, holding
teammates' current actions fixed, resolving the current slot, then allowing all
agents to follow their branch-specific closed-loop recurrent policies through
slot 11 under the same future environment and inverse-CDF action tape:

\[
\widehat Q_{i,t}(a)=
J(\operatorname{Continue}_{\theta_u}
[\operatorname{do}(a_{i,t}=a),a_{-i,t}=a^*_{-i,t};\Omega]).
\]

The factual action's Q entry equals and reuses the factual terminal return.
Every other legal action receives one continuation. Empty or ineffective legal
actions remain included; illegal actions are excluded. Current teammate actions
remain factual. From `t+1` onward, observations, messages, hidden states,
actions, buffers, acknowledgements and rewards are branch-specific. A branch
from slot `t` has `12-t` environment transitions and `11-t` future policy
rounds. Branches never recursively create training samples.

This is exhaustive current legal-action enumeration and an exact simulator
continuation on one tape, not exact expected `Q^pi`, a joint-action oracle or a
variance-free target.

With `pi` the factual floor-mixed legal distribution, define

\[
\widehat B_{i,t}=\sum_{a\in\mathcal A_i}
\operatorname{sg}[\pi_{i,t}(a)]\operatorname{sg}[\widehat Q_{i,t}(a)],
\qquad
\widehat A_{i,t}=\operatorname{sg}[J_{base}-\widehat B_{i,t}].
\]

The actor uses the unchanged sampled factual log probability and entropy:

\[
L_{actor}=-E_e\frac1{12N_e}\sum_{t,i}
\log\pi_{i,t}(a^*_{i,t})\widehat A_{i,t}
-0.01E_e\frac1{12N_e}\sum_{t,i}H(\pi_{i,t}).
\]

The complete loss adds the unchanged critic nuisance term
`0.5 mean_t(V(g_t)-J)^2`. All Q values, baseline weights, branch states,
future branch policy computations and terminal returns are stopped. Only the
factual 12-slot actor/entropy graph and unchanged factual critic graph receive
gradients. An all-action differentiable loss, branch BPTT, auxiliary loss,
replay or extra actor sample is forbidden.

## Coupling and leakage firewall

The successor uses 24 future independent seed blocks under a fresh semantic
namespace; numeric labels remain unmaterialized. Matching PHY/EDGE base worlds
share event, detection, channel, initialization and action-uniform coordinates.
Different rosters remain independent.

At a factual world, every legal action branch reuses the same future event,
detection, channel and inverse-CDF action coordinates. Branch origin and forced
action do not salt randomness. The same uniform may produce different future
actions because branch-specific distributions differ. Coordinates exist
independently of branch execution order or action use. The focal current action
uniform selects only the factual label and is independent of the complete Q
vector. The factual-action branch must reproduce the factual suffix and J by
construction.

Simulator-private state and future tapes are available only inside stopped
training target generation. The sole information path is terminal Q values to
the stopped scalar advantage to the factual log-probability gradient. Branch
state, IDs, future facts, Q vectors, actions, messages and hidden states never
enter execution inputs, critic input, normalization, checkpoints, evaluation,
thresholds or auxiliary losses. Branches do not mutate factual episodes, become
replay or train on held-out rosters.

## Equal opportunity and explicit compound work

Every factual decision in both arms receives one Q entry per legal action. No
arm-, probability-, state-, buffer-, action-effect- or outcome-dependent
pruning, extra continuation or resampling is allowed. Losses average over
agents/slots inside episodes and then equally over episodes. PHY and EDGE have
equal opportunity within each roster; total physical work may differ across
rosters and is not matched to r03.

For the complete 24-seed, two-arm object, the prospectively frozen logical work
is:

```text
factual base episodes                         1,572,864
all legal-action Q entries                    754,974,720
new alternative continuations                 528,482,304
counterfactual environment-slot transitions  3,435,134,976
base plus branch environment slots            3,454,009,344
future branch policy agent-decisions         37,059,821,568
base plus branch policy agent-decisions      37,286,313,984
full-batch backward calls                         24,576
```

The unchanged evaluation adds 86,016 complete rollouts, 1,032,192 environment
slots and 1,990,656 shadow-cut GRU/distribution evaluations. Total learned
policy agent-decision evaluations are 37,299,806,208. Vectorization or exact
caching may reduce wall time but cannot change the logical target set,
continuation length or stochastic dependence. Counterfactual objects are never
inferential replicates.

## Question, outcomes and claim ceiling

The package-level question is whether this simulator-backed unilateral credit
trainer makes EDGE competent and the held-out panel answerable at update 512,
allowing the unchanged physical-prior retention law to operate. It does not
estimate why r03 failed or whether this trainer is better than r03.

Structural invalidity now includes missing Q entries, parameter drift within an
update, factual-return mismatch, open-loop future replay, branch-salted
randomness, branch-order effects, target gradients, critic-nuisance deviation,
unequal opportunity, leakage or schedule deviation. After structural validity,
the r03 branch law remains literal:

1. failed answerability or EDGE competence gives `NONIDENTIFIED`;
2. every positive direct, interaction, worse-zone and cut gate gives
   `RETAIN_PHYSICAL_PRIOR_COLDSTART` under this exact trainer; and
3. every other valid, answerable panel with competent EDGE gives the unchanged
   `DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT` decision and ordered predicates.

No branch yields an r03 trainer-effect conclusion or automatic further stage.

The maximum positive claim is only:

> In the exact static `RIDGEGATE-2Z` toy, under the frozen exhaustive unilateral
> one-tape counterfactual-credit trainer, the narrow physical-prior policy
> achieved the complete registered action-sensitive held-out-roster advantage
> over a competent, equally initialized and strictly containing matched EDGE
> learner after exactly 512 matched updates.

The full r03 qualifications—larger held-out-than-seen advantage, worse-basin
preservation and greater attenuation under the symmetric cut—remain required.
No result establishes critic causation, trainer superiority to r03, exact
expected Q, joint-action credit, kernel truth, work efficiency, another budget,
arbitrary roster/topology value, churn, mobility, a second surface or UAV
benefit.

## Required audit

1. Is the post-GRU/pretransition unilateral intervention and closed-loop
   recurrent continuation mathematically well-defined under the task law?
2. Does the complete-Q stopped baseline remain action-independent for the
   factual draw and avoid gradient/future-information leakage?
3. Does retaining the critic strictly as an unchanged nuisance loss preserve
   the intended single actor-credit axis, or is another scientific correction
   required?
4. Are the arm/action common-random-number law, factual-return identity and
   legal-opportunity contract coherent without claiming exact expected Q?
5. Does the package ask an identifiable PHY-versus-EDGE question without
   falsely identifying the cause of r03 or importing an unregistered
   cross-trainer comparison?
6. Are the unchanged outcome map, strongest alternatives and narrowed claim
   ceiling complete?
7. Does any mathematical, causal or estimand defect require a revised complete
   composite before static feasibility work?

## Required response format

```text
MATH_CLOSURE_DECISION=CLOSED|REVISION_REQUIRED
EXACT_REVISION=SGSP-RG2Z-CCA-SCIENCE-20260820-01
RESULT_BLIND=true

ESTIMATOR_AND_GRADIENT
<audit>

RECURRENT_INTERVENTION_AND_COUPLING
<audit>

MATCHING_NO_LEAKAGE_AND_WORK
<audit>

IDENTIFIABILITY_AND_OUTCOMES
<audit>

STRONGEST_ALTERNATIVE
<audit>

CLAIM_CEILING
<audit>

DEFECT_LEDGER
SCIENCE_BEARING_DEFECT_COUNT=<integer>
<NONE or exact defects and required corrections>

FINAL_DISPOSITION=CLOSED|REVISION_REQUIRED
```

