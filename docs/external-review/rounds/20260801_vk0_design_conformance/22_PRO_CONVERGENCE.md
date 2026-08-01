CONFORMANCE
CONFORMS — the amendments close the V-K0 design-conformance check

All six previously required closure items are now resolved at the protected scientific-semantics level:

Required closure item	Disposition
Permutation-equivariant two-track V-K0A incumbents	Closed by A-VK-D2
Complete from-reset boundary identity with fail-closed replay	Closed by A-VK-D3 and A-VK-D4
Durable row identity, recomputation keys, and natural match evidence	Closed by A-VK-D6
Runtime, checkpoint, configuration, and V-K0A authorization provenance	Closed by A-VK-D8 and A-VK-D10
Exhaustive U
src
	​

 on each V-K0B row’s actual incumbent pair	Closed by A-VK-D10
Executable decisive-failure versus unresolved predicates	Closed by A-VK-D9

The amendments retain the ruled V-K0 sequence and do not introduce a competing experiment, constrained renewal-class mechanism, fixed-period arm, UAV execution, or delayed-credit detour. The source qualification remains V-K0A; unrestricted R30 natural access remains the conditional V-K0B stage.

Closure details
A-VK-D2

The replacement of raw-agent-ID lexicographic selection by two explicit permutation-related optimal histories fixes the anonymity defect without expanding the 112-row panel. The two histories now commute under slot relabelling and preserve the intended slow-duty/fast-duty assignment relation.

This is the correct middle ground:

no identity-preferred collapse;

no all-incumbent combinatorial expansion;

no change to the registered row count or source estimand.

A-VK-D3 and A-VK-D4

From-reset replay is now a valid realization of immutable-snapshot semantics because equality is defined over the complete pre-decision state rather than only prefix actions, rewards, skills, and masks. Replay mismatch now enters the precedence-1 invalid branch rather than changing sample composition.

Serial branch execution remains acceptable because the current R30 intervention consumes process-global PyTorch randomness, draws both focal random variables before forcing, and allows later agents to respond to the modified autoregressive prefix.

The exact canonical encoding of the fingerprint is a Gate-B realization matter. It is no longer an open scientific choice.

A-VK-D5

The order guard closes the possibility that malformed or partially propagated order inputs define an unintended controller. Keeping one order fixed across the entire episode and all of its factual and counterfactual reconstructions is the correct evaluation contract.

Training remains byte-identical because agent_order=None preserves the existing ascending path. The current implementation hardcodes ascending order and records token identities through that order, so this is the minimum necessary extension.

A-VK-D6

The augmented schemas now support all registered joins and resampling levels:

training seed
evaluation episode
agent order
check
focal agent
estimand family
candidate/branch unit
checkpoint/config identity

Persisting the natural five-step reward, slow-match, and fast-match vectors also closes the previous durability gap: competence can be recomputed from the row artifacts rather than trusted from a summary-only in-memory calculation.

The amendment correctly treats the earlier field lists as semantic minima, not as a prohibition on nonsemantic provenance keys.

A-VK-D8 and A-VK-D10

The resolved-runtime preflight and checkpoint identity now make nominal and actual exposure distinguishable before and after execution. The V-K0A-to-V-K0B authorization chain also binds the actual source definition rather than accepting a verdict string alone.

Most importantly, V-K0B now applies the exhaustive oracle to the policy’s actual incumbent pair. It therefore cannot substitute:

target phase;

skill-axis labels;

the canonical V-K0A history;

or an inherited “slow/fast” classification

for the ruled source-level estimand.

This prevents the older diagnostic shortcut—classifying incumbents by skill axis—from becoming the new conclusion-bearing urgency label. The earlier toy audit used that shortcut, so the explicit prohibition is load-bearing.

A-VK-D9

The amendments now provide a complete first-match implementation rule:

every opportunity stratum can be PASS, decisively failed, or unresolved;

material urgency failure is separated from confidence-bound non-resolution;

stable natural behavior can be wrong in either direction;

hazard direction and realized SET direction are separately handled;

a nonpositive point estimate is not automatically converted into a decisive negative.

That closes the previously underdetermined branch selector.

Two realization clarifications

These do not reopen the design or require another Pro round.

1. Artifact hashing must be non-self-referential

“Artifact SHA-256” should be realized as one of:

a launch/authorization manifest containing the completed artifact hash;
a sidecar digest file;
or a bundle index hashing the separately serialized V-K0A files.

The JSON artifact should not be required to contain the hash of its own final bytes. V-K0B must receive or locate an independently frozen expected digest and compare the completed artifact against it.

This is a serialization binding, not a new scientific choice.

2. The complete fingerprint field set must become explicit in Gate B

The phrase:

plus any other mutable runtime field read before or during the focal decision

is scientifically correct but cannot remain an implicit implementation promise. The proof-sized skeleton must enumerate the concrete fields or recursively cover the relevant object state, and Gate B must verify that coverage.

A newly discovered omitted mutable field is an implementation-conformance defect. It does not require a new design ruling unless deciding whether to include it would change the registered estimand or branch.

CONVERGENCE_DECISION
TOUCHPOINT_2                         CONFORMS
V-K0 scientific sequence             FROZEN
V-K0A source estimand                 FROZEN
V-K0B policy-side estimands           FROZEN
panel construction                    FROZEN
paired replay semantics               FROZEN
trace and provenance semantics        FROZEN
branch predicates                     FROZEN
new protected decision found          NO
another Pro design round required     NO

The next permitted artifact is the proof-sized executable skeleton covering:

the two-track source panel;

exhaustive actual-incumbent oracle;

complete replay fingerprint;

row serialization and joins;

authorization verification;

bootstrap inputs;

and branch-selector witnesses.

That skeleton then receives the realization-conformance grill. Full implementation and any experiment remain outside this ruling.