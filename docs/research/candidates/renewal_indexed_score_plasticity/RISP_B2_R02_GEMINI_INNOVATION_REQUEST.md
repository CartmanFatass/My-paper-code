# RISP-B2 revision-02 External Gemini innovation request

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B2
science_revision=RISP-B2-SCIENCE-20260814-02
request_kind=MUTUALLY_BLIND_DIVERGENT_INNOVATION
provider_role=External Gemini innovator
provider_contacted=false
conversation_relationship=CREATE_ONE_NEW_DIRECTION_CONVERSATION
owner=EM_renewal_indexed_score_plasticity
question_status=FROZEN_UNSENT
```

This is an independent innovation consultation, not mathematical closure,
implementation review, result acceptance, or portfolio selection. Do not infer
or reconstruct another reviewer's question or answer. Work only from the
scientific object below.

## Motivation and predecessor evidence

The predecessor used one shared policy at training `k={4,8}` and evaluation at
held-out `k=12` and the switches `4->12` and `12->4`. Its complete panel was
nonidentifying: both its selected-score recurrence and function-equivalent
generic recurrence lacked seen competence and failed the prospective target
update-induced policy-TV gate. Structural timing, support, information yokes,
and mechanism-read checks otherwise passed. Finite-budget optimization,
learned transition reachability, learned policy-port failure, global renewal-
rate sufficiency, and package-specific convergence remain live. No predecessor
target estimate is used to tune this successor.

## Frozen RISP-B2 object

There are two parameter-sharing, noncommunicating agents with independent
hidden processes. Each episode has 192 primitive ticks and three actions. At a
renewal the agent selects one action and holds it for the externally supplied
duration `k`. The hidden target matches the selected action with success
probability `3/4` and otherwise with probability `1/4`. After success the next
target is the selected action; after failure it is uniform over the other two
actions. The controller never observes the target or future `k`.

One slow controller and recurrent parameterization train jointly at `k={4,8}`.
The same frozen tensors evaluate at `k=12`, `4->12`, and `12->4`, without a
per-duration head, reset, gain, checkpoint, or evaluation optimizer. Each
agent's private bounded state persists across switches and changes only after a
completed nonterminal hold, before the next legal action.

The slow action distribution and private simplex state are mixed equally:

```text
pi(a|o,q) = 0.5*pi_slow(a|o) + 0.5*q(a).
```

Both heads use a bounded rational map. For finite rational `r in Q^3`,

```text
z_j(r)        = 6*r_j/(6+|r_j|)
omega_j(r)    = 16+(z_j(r)+6)^2
Affinity(r)_j = omega_j(r)/sum_l omega_l(r).
```

Every action remains above `1/21`. At action selection the controller stores
only `(q_n,a_n,k_n,tau_n)`. After the hold completes, the legal sign is the
realized outcome `s_n=Y_n`. The 13-vector is

```text
phi_n = [1,
         q_n(LEFT),q_n(HOLD),q_n(RIGHT),
         onehot(a_n)_LEFT,onehot(a_n)_HOLD,onehot(a_n)_RIGHT,
         s_n,
         s_n*onehot(a_n)_LEFT,
         s_n*onehot(a_n)_HOLD,
         s_n*onehot(a_n)_RIGHT,
         k_n/12,
         tau_n/192].
```

For selected action `a`, the fixed semantic raw vectors are

```text
g(+1,a)_j = +30 if j=a, else -30
g(-1,a)_j = -30 if j=a, else   0.
```

A unique fixed binary64 matrix `G in R^(3x13)` is zero outside the two action-
categorical blocks and satisfies `G*phi=g(s,a)` for all six categorical pairs.
Its entries are only `-30,-15,0,+30`.

Both arms deploy the identical effective-matrix function class:

```text
DIRECT-ANCHOR:  q_(n+1) = Affinity(E_A*phi_n)
DIRECT-CONTAIN: q_(n+1) = Affinity(E_C*phi_n).
```

Each `E` contains 39 learned binary64 scalars and may be any finite binary64
`3x13` matrix. The arms have identical packet information, forward map, action
support, loss, batch order, AdamW work, update count, update opportunities, and
reset law. Their sole prospective difference is finite optimization geometry:
`E_A` initializes at `G` and decays about `G`; `E_C` initializes at zero and
decays about zero. The treatment tests a value-aligned initialization and
centered-decay coordinate prior, not capacity or expressivity.

With a uniform slow policy and old state, the fixed center has an exact local
certificate. After success its next-policy value gain and TV are both `40/171`.
After failure its value gain is `35/726` and its policy TV is `35/363`.
Separate value gates prevent high-TV but value-negative motion from qualifying.

Training uses 256 fixed AdamW updates on intact outcomes at seen `k={4,8}`.
Both arms receive the same physical-reward policy loss and a weight-`1/4`
alignment loss toward `Affinity(g(Y,a))`. This target uses only the selected
action and its completed outcome; it never reads the hidden target, future
duration, future reward, or evaluation statistic.

Frozen checkpoints are crossed at evaluation with `INTACT` and
`MARGINAL-TWIN`. The twin sign independently samples the exact conditional law
of the recipient outcome given the controller-visible pre-outcome history and
selected action, while never reading the recipient target, actual outcome,
reward, next state, performance, or future schedule. It alone updates the twin
recurrence. Actual outcomes still drive the environment and offline value
labels. The twin preserves the one-step conditional sign law but intentionally
does not preserve every serial dependence of the realized hidden lineage.

Primary endpoints are mean primitive reward over fixed physical-time windows
at `k=12` and both switches, averaged equally within each seed and then analyzed
over 16 independent seed strata. Any positive result must clear the complete
panel, no leakage, common support, seen competence, oracle headroom, target
policy-TV, positive expected-value alignment, both-architecture qualifications,
family-controlled nonharm, intact anchor advantage, architecture-by-feedback
interaction, intact-over-twin anchor benefit, and anchor/control equivalence
under the twin. A failed qualification panel is nonidentifying.

The strongest live alternative after a favorable result is that nonzero
initialization and centered-decay geometry lie closer to the shared alignment-
loss optimum, improve conditioning, or merely converge faster than the zero-
centered arm, rather than encoding useful win-stay/lose-suppress semantics.
A prospectively separate sign-reversed center `g_REV(s,a)=g(-s,a)` would
preserve magnitudes, sparsity, norm, work, function domain, support, and shifted-
center geometry while reversing completed-outcome meaning, but it is not part
of this object.

## Frozen later-probe map and UAV bridge

A possible later `BEST-REACHABLE-X` probe is not authorized here. Its four
prospective meanings are:

1. If an old frozen checkpoint can reach both competence and target TV, retain
   the old port and treat the direct bypass as optional; focus repair on
   transition reachability, dose, or optimizer geometry.
2. If it can reach TV but not competence, retain actuation capability but
   delete TV-alone success; require expected-value and physical-value evidence.
3. If no admissible old fast state reaches target TV, delete the old learned
   low-rank port branch for this bounded host and retain the direct mixture as
   the decisive actuation bypass, still conditional on competence and value.
4. If target TV clears without improved expected next-hold value, delete
   actuation-only explanations and retain only a prospectively value-bearing
   semantic treatment; if its structural certificate also fails, delete that
   treatment and its UAV bridge.

The narrow UAV bridge maps external `k` to commanded macro-action or
communication/skill-hold duration. Each UAV would keep a private bounded action-
affinity state across duration changes and update it from a deployable outcome
or advantage sign only after a macro completes. Toy success would not establish
transfer: UAV macro semantics, masks, credit, delayed effects, wind/link
dynamics, coordination, safety overrides, matched controls, and physical-time
mission value would require a new science object. In particular, real UAV
transitions need not make the next useful macro equal the successful previous
macro or one of the other macros after failure.

## Requested divergent assessment

1. Construct the strongest counterexample in which the exact one-step value
   certificate and policy-TV identity hold locally, yet the declared anchor
   reduces the registered physical-time endpoint after an external `k` switch.
2. Decide whether global renewal rate, stationary action persistence, temporal
   correlation, or the common alignment auxiliary can still explain an
   apparent intact benefit despite the conditional-marginal twin. Give the
   exact observable or matched control that best separates the strongest such
   alternative without using future information.
3. Stress-test whether the sign-reversed center is the highest-information
   discriminator of semantic meaning versus generic shifted-center geometry.
   If not, give a better capacity-, norm-, work-, support-, and information-
   matched discriminator and explain its distinct possible outcomes.
4. If a strictly better bounded outcome-coupled recurrence exists under the
   same causal information, shared-parameter, equal-function-class containing
   control, and next-legal-action constraints, give its exact state, update,
   policy equations, and algebraic containment map. Otherwise explain why this
   direct affinity anchor is the smallest high-information object.
5. Audit the four `BEST-REACHABLE-X` meanings. Name any outcome that would
   incorrectly retain, modify, or delete the treatment, toy-to-UAV bridge, old
   policy port, or transition-repair branch.
6. Name the most important broken assumption in mapping this completed-outcome
   action-semantic state to a UAV macro controller, and the smallest toy change
   that would make that assumption identifiable.

Return exactly one leading line:

```text
RETAIN_FROZEN_COMPOSITE
```

or

```text
SCIENCE_BEARING_REVISION_PROPOSED
```

Then give the counterexample, mechanism, exact proposed correction if any,
strongest alternative, next discriminator, and claim ceiling. Do not review
code, files, tests, random-number addresses, compute resources, or portfolio
priority.
