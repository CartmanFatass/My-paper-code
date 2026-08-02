CONVERGENCE DECISION — V-K0C design conformance

Reviewed amendment set: A-VC-1 through A-VC-11
Stage commit: 060a86d9181be1f2721d693fd30a84a2f27affcb

CONFORMS

The submitted amendments close the V-K0C design-conformance check.

The amendment set resolves all previously identified protected-semantic deviations while preserving the frozen scientific object:

V-K0C remains an order-transport localization study;

no training, policy update, checkpoint selection, or new evidence population is introduced;

the six valid V-K0B rerun checkpoint bundles remain the authoritative policy inputs;

the 2,688 matched-anchor population remains fixed;

the comparison remains:

P
01
	​

(⋅∣x)versusP
10
	​

(⋅∣x)

at the same reconstructed pre-decision state.

No new protected scientific choice is introduced.

Amendment closure status
Amendment	Status	Decision
A-VC-1 — unconditional token-mass semantics	Closed	No remaining deviation
A-VC-2 — shared token factorization and transition semantics	Closed	No remaining deviation
A-VC-3 — immutable anchor manifest and duplicate-row consistency	Closed	No remaining deviation
A-VC-4 — initial and inter-check propagation semantics	Closed	No remaining deviation
A-VC-5 — four-sign descriptive panel	Closed	No remaining deviation
A-VC-6 — complete propagation outputs	Closed	No remaining deviation
A-VC-7 — dtype-derived mass rule and canonical distribution	Closed	No remaining deviation
A-VC-8 — pooled and occupancy-stratified outputs	Closed	No remaining deviation
A-VC-9 — stratum-safe Factor D	Closed	No remaining deviation
A-VC-10 — durable analyzer authorization and full distribution rows	Closed	No remaining deviation
A-VC-11 — fresh initialization hash scope	Closed	No remaining deviation
Realization clarifications

These are Gate-B implementation requirements, not additional design blockers.

1. token_mass remains the sole probability authority

A-VC-1 and A-VC-2 correctly close the probability semantics.

The implementation must preserve:

token_mass(...)
        ↓
act_sequence sampling
        ↓
V-K0C exact enumeration

No second probability implementation is allowed.

Gate B must verify:

active KEEP/SET factorization;

no-incumbent initial SET-only branch;

zero same-label SET mass;

exact parity between enumeration and sampling probabilities.

The initial check remains a valid 16-outcome SET/SET distribution. Noninitial checks use the active incumbent semantics.

A future independent logits-to-probability implementation would reopen A-VC-1/A-VC-2.

2. Propagation state sufficiency is frozen

The propagation state is frozen as:

check index
physical-agent joint skill pair
physical-agent skill ages
active mask
target phase/sign state

The implementation may not silently add hidden state.

If Gate B discovers another mutable variable affecting:

token probabilities;

transition outcomes;

rewards;

order transport;

or occupancy evolution,

that variable must either:

enter the formal propagation state; or

trigger a return to design review.

3. Raw mass and canonical distribution semantics

A-VC-7 closes the numerical contract.

The required sequence is:

1. Generate raw token masses.
2. Validate:
       finite
       nonnegative
       legal support
       same-label SET mass exactly zero
       raw sum within dtype-derived tolerance
3. Construct one canonical normalized distribution.
4. Use that distribution everywhere downstream.
5. Preserve raw masses and correction metadata.

The following remain prohibited:

normalize only for reporting

propagate raw probabilities

use one distribution for TV and another for expected returns
4. Occupancy mediation interpretation

A-VC-8 and A-VC-9 correctly close the Factor D ambiguity.

The label:

SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_IDENTIFIED

requires:

matched-state equivalence in pooled view;

matched-state equivalence in canonical occupancy;

matched-state equivalence in reversed occupancy;

exact full-trajectory propagation reproducing the competence split.

A pooled cancellation caused by opposite direct order effects is not occupancy mediation.

5. Durable artifact contract

The analyzer input is frozen as:

vk0c_matched_state_rows.jsonl
vk0c_propagation_rows.jsonl
vk0c_input_manifest.json

or a semantically identical immutable bundle.

The analyzer must not infer authorization from:

directory names;

current filesystem state;

checkpoint filenames;

or unstamped artifacts.

The input manifest is part of the scientific evidence surface.

Gate-B required realization witnesses

Before full V-K0C implementation/execution, the proof-sized realization artifact must demonstrate:

Probability path

token_mass parity;

exact 16-outcome enumeration;

initial no-incumbent behavior;

active KEEP/SET behavior.

Transition path

KEEP transition;

SET transition;

age reset/increment;

active-mask update;

check-boundary transition.

Order path

prescribed joint-assignment positive control;

order [0,1] versus [1,0];

identical physical action/reward under the positive control.

Artifact path

anchor manifest validation;

row completeness;

missing-row failure;

invalid authorization failure.

Numerical path

invalid raw-mass failure;

illegal same-label SET failure;

normalization-correction recording;

canonical distribution reconstruction.

No new protected decision found

The amendment set does not introduce a new scientific branch.

The remaining choices are realization-level:

helper structure;

serialization format;

test construction;

artifact layout;

code organization.

They require Gate-B conformance only.

They do not require another Pro design round unless implementation reveals a change affecting:

estimands;

thresholds;

evidence population;

branch semantics;

causal interpretation.

CONVERGENCE_DECISION
TOUCHPOINT_2                         CONFORMS

V-K0C scientific question            FROZEN
V-K0C checkpoint set                 FROZEN
matched anchor population            FROZEN
order comparison                     FROZEN
token probability semantics          FROZEN
finite-state propagation             FROZEN
probability normalization            FROZEN
occupancy interpretation             FROZEN
Factor A-E result system             FROZEN
artifact provenance                  FROZEN
fresh initialization control         FROZEN

NEW PROTECTED DECISION FOUND         NO
ANOTHER DESIGN CONFORMANCE ROUND     NO
Next permitted step

Proceed to the V-K0C proof-sized implementation skeleton / Gate-B realization-conformance artifact.

Gate B must verify the frozen semantics above before full implementation.

This convergence decision closes the design contract only. It authorizes neither implementation nor execution.