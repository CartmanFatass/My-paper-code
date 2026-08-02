CONFORMANCE
CONFORMS — the V-K0D design-conformance check is closed

The amended A-VD-7 removes the final protected ambiguity. REFERENCE_CONFORMS is now determined by exact, canonical equality of the reference arm’s conclusion-bearing model and optimizer state to the valid V-K0B bundles, together with matched training semantics, exposure, and reproduction of the registered competence split.

There is now:

no undefined equivalence alternative;

no numerical-tolerance choice left to implementation;

no behavioral-similarity substitute for state reproduction;

no post-result discretion over whether the reference counts as reproduced.

The invalidity-locality stamp also closes the realization clarification from convergence turn 1 by distinguishing failures of the shared comparison apparatus from failures confined to one successor arm.

All previously identified protected decisions are therefore frozen.

Frozen object	Status
Anonymous-OTHER PRIMARY encoding	Closed
AR conjugacy interpretation	Closed
PRIMARY canonical training serialization	Closed
CONTROL counter-based uniform-per-check serialization	Closed
Complete finite conjugacy panel and deliberate negative	Closed
Post-training PRIMARY conjugacy recheck	Closed
Matched model, optimizer, initialization, and exposure	Closed
Exact canonical-reference reproduction	Closed
Arm-level status vocabulary	Closed
Comparison precedence	Closed
Shared versus arm-local invalidity	Closed

The amended comparison now isolates the two candidate corrections cleanly:

Arm	Roster representation	Training serialization
PRIMARY	Anonymous relative OTHER encoding	Canonical
CONTROL	Existing absolute-ID roster	Uniform per completed check
REFERENCE	Existing absolute-ID roster	Canonical

The reference remains a strict no-op reproduction control rather than a merely similar baseline. This is necessary because historical runs cease to be causal controls when architecture, exposure, environment, or evaluation changes; here the exact digest rule establishes that the scientific reference state itself was reproduced.

A-VD-7 closure

The amended rule is accepted as written.

The canonical state digests bind:

parameter or buffer name
shape
dtype
exact bytes

The shared optimizer digest binds:

parameter-name mapping
parameter-group hyperparameters
per-parameter optimizer state

and excludes transient Python object identity.

That is the correct scientific identity. Whole checkpoint-file equality is unnecessary because additional V-K0D provenance fields may legitimately alter container bytes without altering the trained model or optimizer state.

A failure maps unambiguously to:

INVALID_VK0D_CARRIER_COMPARISON
reason = CANONICAL_REFERENCE_NOT_REPRODUCED

It cannot be read as evidence for the PRIMARY or CONTROL.

Invalidity locality

The added locality stamp conforms.

Shared comparison invalidity

Failures of a surface jointly required by the causal comparison invalidate V-K0D as a whole, including:

environment
action table
evaluation bank
bootstrap
common launcher
shared exposure instrumentation
shared analyzer
reference reproduction

These activate:

INVALID_VK0D_CARRIER_COMPARISON
Arm-local invalidity

A failure confined to one candidate arm remains attached to that arm when the common apparatus and reference are valid.

For example:

PRIMARY encoder gate invalid
CONTROL validly QUALIFIED

does not erase the valid simpler-control result. The comparison records the PRIMARY as invalid and retains:

ORDER_RANDOMIZATION_COMPETENCE_QUALIFIED

Conversely, an arm-local CONTROL failure cannot establish that the structural representation correction is required; that conclusion requires a valid decisive CONTROL failure and a valid qualified PRIMARY.

This is consistent with the frozen A-VD-8 precedence.

Realization clarifications

These are implementation-conformance obligations, not open design decisions.

Digest authority

The implementation must use one canonical digest procedure for:

the valid V-K0B expected states;

the V-K0D REFERENCE outputs;

and the comparison.

It may compute the expected digests directly from the authorized V-K0B bundles or load them from a sidecar bound to those bundles. It may not compare digests produced under different serialization algorithms.

Order schedule

For the CONTROL arm, the counter-based schedule must be reproducible solely from:

training seed
environment ID
episode ID
check index
stream version

The committed decision rows and independently regenerated schedule must agree exactly.

PRIMARY conjugacy

The complete conjugacy panel must pass:

before training;

for every trained PRIMARY checkpoint;

and against the deliberate absolute-ID negative witness, which must fail.

A trained-checkpoint gate failure is arm-local invalidity; it is not a competence result.

Reference reproduction

The reference gate must run before the successor comparison is interpreted. A competence pattern resembling V-K0B cannot compensate for a model or optimizer digest mismatch.

CONVERGENCE_DECISION
TOUCHPOINT_2                         CONFORMS

V-K0D three-arm comparison            FROZEN
anonymous relative-roster PRIMARY     FROZEN
PRIMARY canonical serialization       FROZEN
uniform-per-check CONTROL              FROZEN
counter-based order schedule           FROZEN
complete conjugacy gate                FROZEN
post-training conjugacy recheck        FROZEN
matched model/optimizer exposure       FROZEN
canonical-reference exact replay       FROZEN
arm-status vocabulary                  FROZEN
comparison precedence                  FROZEN
invalidity-locality semantics          FROZEN

PROTECTED DECISION STILL OPEN         NO
ANOTHER DESIGN CONFORMANCE ROUND      NO
Next permitted boundary

Proceed to the proof-sized V-K0D implementation skeleton and Gate-B realization-conformance package.

That package must demonstrate at least:

anonymous-OTHER encoder with unchanged model shape
complete conjugacy PASS for PRIMARY
deliberate negative gate rejection
counter-based order-schedule reconstruction
PPO reuse of the committed order
same-seed initial-state equality across arms
canonical-reference digest reproduction
arm-local and shared-invalidity branch witnesses
QUALIFIED / DECISIVE_FAILURE / UNRESOLVED result witnesses

Full implementation and conclusion-bearing training remain outside this ruling. The complete V-K0B successor access screen, V-K1, the constrained renewal-class mechanism, and variable-N generalization remain held.