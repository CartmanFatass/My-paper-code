CONFORMANCE
CHANGES_REQUIRED — one protected choice remains open in A-VD-7

A-VD-1 through A-VD-6 and A-VD-8 close the corresponding deviations from the prior ruling. The amended design now cleanly separates:

anonymous roster representation with canonical training;

existing representation with randomized training order;

existing representation with canonical training as the no-op reference.

The order-assignment unit, finite conjugacy panel, matched model/optimizer exposure, and arm-status/result precedence are now sufficiently frozen.

A-VD-7, however, still contains an unresolved alternative:

final actor/value and optimizer-state digests reproduce the valid
V-K0B bundle

OR

a pre-frozen equivalence rule holds

No equivalence rule is actually defined. Because reference reproduction is a precedence-2 validity condition, choosing that rule after implementation or after seeing reference outputs could determine whether the entire V-K0D comparison is valid. It cannot remain an implementation-time option.

Amendment	Disposition
A-VD-1 — anonymous-OTHER encoding	Closed
A-VD-2 — conjugacy, not same-state invariance	Closed
A-VD-3 — PRIMARY canonical training	Closed
A-VD-4 — counter-based per-sequence order assignment	Closed
A-VD-5 — complete finite conjugacy panel	Closed
A-VD-6 — matched model and optimizer opportunity	Closed
A-VD-7 — canonical-reference reproduction	Still open
A-VD-8 — arm statuses and precedence	Closed
Required A-VD-7 correction

Freeze exact state reproduction and remove the unspecified alternative.

The preferred and smallest binding is:

REFERENCE_CONFORMS iff, for every scientific seed:

1. canonical SHA-256 of the final high-actor state_dict
       equals the corresponding valid V-K0B digest;

2. canonical SHA-256 of the final high-value state_dict
       equals the corresponding valid V-K0B digest;

3. canonical SHA-256 of the shared high-optimizer state
       equals the corresponding valid V-K0B digest;

4. resolved training semantics and actual exposure match;

5. the frozen evaluation reproduces:
       canonical competence above 0.75,
       reversed competence decisively below 0.75.

The state digests should bind, canonically:

parameter/buffer name
shape
dtype
exact bytes

The optimizer digest should bind its parameter-name mapping, parameter-group hyperparameters, and per-parameter optimizer state rather than transient Python object identities.

Only explicitly identified non-model provenance fields—for example, a new run path or the additional V-K0D manifest metadata—may differ. Those fields are excluded from the model/optimizer digests by construction.

There is:

no numerical tolerance;
no behavioral-only equivalence;
no later-selected equivalence rule;
no fallback based only on competence similarity.

Literal whole-checkpoint-file equality remains unnecessary because provenance metadata can legitimately change.

A mismatch produces exactly:

INVALID_VK0D_CARRIER_COMPARISON
reason = CANONICAL_REFERENCE_NOT_REPRODUCED

This correction closes the no-op reference without making file serialization itself the scientific object.

Accepted interpretations
1. Relative-role encoding with the AR loop retained

Accepted.

The PRIMARY remains an autoregressive editor. It is required to be permutation-conjugate under a complete physical-agent swap; it is not required to produce identical common-coordinate distributions under two different serializations at the same unswapped state.

A-VD-1 now isolates identity removal properly:

current focal skill/age inputs       retained once
anonymous OTHER roster information  retained
absolute physical-ID shortcut       deleted
model shape and parameter count      unchanged

No unmatched focal-feature duplication remains.

2. Per-check randomization

Accepted.

The correct unit is one completed high-check autoregressive sequence, including initial assignment. The counter-based identity and schedule digest remove dependence on batching and call order.

The dedicated order assignment isolates the schedule RNG. It does not imply identical policy trajectories across arms.

3. Competence-only V-K0D qualification

Accepted.

At this stage, QUALIFIED means only:

The arm satisfies the registered natural-task competence prerequisite under both evaluation serializations.

It does not establish renewal-opportunity access, sampled-SET competence, natural renewal value, or hazard alignment. The surviving carrier must subsequently rerun the complete V-K0B access screen before V-K1.

Realization clarifications

These do not create further design blockers.

Arm-local versus shared invalidity

The analyzer must stamp every invalid reason as either:

SHARED_COMPARISON_INVALIDITY

or:

ARM_LOCAL_INVALIDITY

Shared-shell failures—environment, evaluation bank, bootstrap, action table, common launcher, exposure measurement, or shared analyzer corruption—activate precedence 1 and invalidate V-K0D.

A PRIMARY-only encoder or checkpoint failure may remain arm-local. If CONTROL is validly qualified, that arm-local failure does not erase the simpler-control result.

Conjugacy gate

The complete gate must verify:

fresh PRIMARY
every trained PRIMARY checkpoint
deliberate absolute-ID negative witness

The negative witness, rather than a coincidental random reference failure, owns gate sensitivity.

Order exposure

For canonical arms:

N_reversed = 0
N_canonical = N_completed_sequences

For CONTROL, validity requires exact agreement with the regenerated counter-based schedule, not merely approximate balance.

CONVERGENCE_DECISION
TOUCHPOINT_2                         CHANGES_REQUIRED

V-K0D three-arm comparison            RETAINED
anonymous relative-roster PRIMARY     FROZEN
PRIMARY canonical serialization       FROZEN
uniform-per-check CONTROL              FROZEN
counter-based order schedule           FROZEN
complete conjugacy gate                FROZEN
matched model/optimizer exposure       FROZEN
arm-status vocabulary                  FROZEN
comparison precedence                  FROZEN

REMAINING BLOCKER
    A-VD-7 must remove the undefined
    "or a pre-frozen equivalence rule" alternative
    and freeze exact canonical model/optimizer-state
    digest equality to the valid V-K0B bundles

PROTECTED DECISION STILL OPEN         YES
ANOTHER CONVERGENCE TURN REQUIRED     YES

IMPLEMENTATION                         NOT AUTHORIZED
CONCLUSION-BEARING TRAINING            NOT AUTHORIZED
FULL SUCCESSOR ACCESS SCREEN           HELD
V-K1                                   HELD
CONSTRAINED RENEWAL-CLASS MECHANISM    HELD
VARIABLE-N GENERALIZATION              HELD

Once the exact A-VD-7 rule above is entered, the design has no remaining protected-semantic gap.