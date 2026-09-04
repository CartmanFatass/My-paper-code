# RISP-B2 External Gemini innovation request

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B2
science_revision=RISP-B2-SCIENCE-20260814-01
request_kind=MUTUALLY_BLIND_DIVERGENT_INNOVATION
provider_role=External Gemini innovator
provider_contacted=false
conversation_relationship=ROOT_MUST_SUPPLY_OR_ESTABLISH_ONE_CONCRETE_DIRECTION_CONVERSATION
conversation_id=none_available_at_freeze
owner=EM_renewal_indexed_score_plasticity
question_status=FROZEN_UNSENT
```

This is an independent innovation consultation, not mathematical closure,
implementation review, result acceptance, or portfolio selection. Do not infer
another reviewer's question or answer. Work only from the frozen scientific
state below.

The predecessor used one shared policy at training `k={4,8}` and evaluation
`k=12, 4->12, 12->4`. Its complete panel was nonidentifying: both its
selected-score recurrence and function-equivalent generic recurrence lacked
seen competence and failed the prospective target update-induced policy-TV
gate. Structural timing, support, information-yoke, and mechanism-read checks
otherwise passed. This leaves finite-budget end-to-end optimization, learned
transition reachability, learned policy-port failure, global-rate sufficiency,
and task/package-specific convergence live. No predecessor target estimate is
used to tune the successor.

The frozen successor keeps the same finite two-agent renewal toy. A hidden
three-action target generates completed-hold outcome `Y in {-1,+1}` with
success probability `3/4` on a target-matching action and `1/4` otherwise.
After success the next target is the selected action; after failure it is
uniform over the two alternatives. The policy observes only physical time and
current external `k`; it never sees the target or future `k`. One local state
persists across switches and changes only after a completed nonterminal hold.

The slow action distribution is mixed equally with a bounded local simplex
state:

```text
pi(a|o,q) = 0.5*pi_slow(a|o) + 0.5*q(a).
```

For selected action `a`, let `u` be uniform,
`b(+1,a)=onehot(a)`, `b(-1,a)=(1-onehot(a))/2`, and

```text
v(s,a)=0.75*b(s,a)+0.25*u.
```

Use the canonical two-logit chart of a positive three-simplex vector and the
packet

```text
phi=[1,q,onehot(a),s,s*onehot(a),k/12,tau/T].
```

A fixed matrix `G` maps every categorical `(s,a)` packet to `chart(v(s,a))`.
The treatment and containing control are

```text
ANCHOR:  q_next=Simplex((G+W_A)phi)
CONTAIN: q_next=Simplex(W_C phi).
```

Both `W` matrices are `2x13`, start at zero, and receive identical finite
training, information, optimization, and update opportunities. The classes are
exactly identical by `W_C=W_A+G`. The fixed anchor is not trained or decayed.
At a uniform slow policy/state and zero residual it raises exact expected
next-hold value over no update by `1/4` after success and `1/16` after failure;
the corresponding policy TVs are `1/4` and `1/8`. This is a prospective
structural calculation from the toy, not a fitted observation.

Training is intact-only and identical in both arms: 256 fixed AdamW updates on
seen `k={4,8}`, physical-reward policy loss plus a weight-`1/4` cross-entropy
alignment loss from the completed `(Y,a)` to `v(Y,a)`. Frozen checkpoints are
crossed at evaluation with actual completed outcomes and an independent
conditional-marginal twin sign. The twin matches
`P(Y=+1|controller-visible pre-outcome history,a)` while never reading the
recipient target, actual outcome, reward, next state, performance, or future
schedule. It alone drives the twin recurrence; actual outcomes still drive the
environment and physical reward.

Primary endpoints are mean primitive reward over fixed physical-time windows at
held-out `k=12` and both switches, averaged equally. Any positive result must
clear complete-panel, no-leakage, containment, common-support, seen competence,
headroom, update-induced TV, and positive expected-value-alignment gates in
both architectures. It must show an intact anchor advantage, a positive
architecture-by-feedback interaction, an intact-over-twin treatment benefit,
near-zero anchor/control difference under the twin, and schedule-wise nonharm.
The ceiling is only a finite-toy, finite-budget, realized-outcome-coupled
coordinate-prior claim.

Please provide one divergent but concrete scientific assessment:

1. Give the strongest counterexample in which the declared anchor passes its
   one-step value certificate and policy-TV identity yet reduces the registered
   physical-time endpoint after switching `k`.
2. Decide whether one global renewal rate, stationary action persistence, or
   the alignment auxiliary can still explain an apparent intact benefit despite
   the conditional-marginal twin. State the exact observable or control needed
   to separate the strongest such alternative without using future information.
3. If a strictly better bounded outcome-coupled recurrence exists under the
   same information, capacity-matched containing-control, shared-parameter,
   and next-legal-action constraints, give its exact state/update/policy
   equations and the algebraic containment map. Otherwise say why the frozen
   direct simplex anchor is the smallest high-information object.
4. Stress-test the four prospective later-probe meanings: old port reaches
   competence+TV; reaches TV but not competence; cannot reach TV; or reaches TV
   without expected-value gain. Name any branch that would incorrectly retain
   or delete the direct treatment, learned policy port, transition repair, or
   toy-to-UAV bridge.
5. Name the most important broken assumption in mapping the completed-outcome
   sign and action-semantic state to a UAV macro controller.

Return exactly one leading line:

```text
RETAIN_FROZEN_COMPOSITE
```

or

```text
SCIENCE_BEARING_REVISION_PROPOSED
```

Then give the counterexample, mechanism, exact proposed correction if any,
strongest alternative, and claim ceiling. Do not review code, files, tests,
random-number addresses, compute resources, or portfolio priority.
