CONFORMANCE
CHANGES_REQUIRED — the V-K0C route conforms, but four realization bindings remain scientifically underdefined

The central design is correct and remains selected:

no training, policy update, checkpoint selection, or new evidence bank;

the six valid V-K0B rerun bundles are the authoritative checkpoint inputs;

2,688 matched V-K0B pre-decision anchors;

both autoregressive orders evaluated at every anchor;

exhaustive 16-outcome joint-distribution enumeration;

prescribed-assignment order-conjugacy controls;

fresh-versus-trained comparison;

exact finite-state occupancy propagation;

paired seed-first inference;

and the factorized A–E localization record.

Analytic occupancy propagation is the correct realization of the frozen “exact state-probability propagation, not Monte Carlo token sampling” requirement. The remaining problems concern the exact probability contract, source-artifact identity, the initial/no-incumbent transition, and result semantics across the two occupancy strata.

Ledger item	Disposition
VC-D1 — pure distribution API	Changes required: active and no-incumbent token masses are not fully specified; sharing only the roster-update helper is insufficient
VC-D2 — anchor restoration and positive control	Conforms conditionally: exact anchor inventory and duplicate-row consistency must be frozen
VC-D3 — finite-state propagation	Changes required: initial-check support, inter-check transition semantics, the four-sign descriptive panel, and required propagation outputs must be explicit
VC-D4 — orders and occupancy strata	Conforms, but the strata must remain separate in analysis
VC-D5 — fresh initialization	Conforms with a hash-scope clarification
VC-D6 — artifacts and analyzer	Changes required: 1e-9 raw-mass tolerance and “renormalized only for reporting” are rejected; input provenance and stratum-safe Factor D semantics must be added
VC-D1 — freeze the complete token-mass semantics

The ledger says token_distribution returns:

keep_prob
skill_probs

and describes the factorization as sigmoid times masked softmax. That is correct only for an active learned-KEEP decision.

The actual sampler has a distinct no-incumbent branch. When an agent is inactive:

KEEP is not legal;

the keep logit is not used;

SET occurs with probability one;

the replacement skill is drawn directly from the unmasked categorical distribution.

For an active learned-KEEP agent, by contrast:

P(KEEP)=p
K
	​

,
P(SET(z))=(1−p
K
	​

)p
Z
	​

(z),

with the incumbent skill excluded from p
Z
	​

. The existing sampler implements these branches separately.

This distinction is conclusion-bearing because exact full-episode propagation begins at check 0, where neither agent has an incumbent. A caller that always combines keep_prob and skill_probs through the active-agent formula will produce total legal mass 1−p
K
	​

, not one, at the initial assignment.

Required VC-D1 amendment

Freeze one pure API whose output is the unconditional legal token mass:

token_mass(
    joint_obs,
    compact,
    team_vector,
    working_skills,
    working_ages,
    working_active,
    agent_id,
    omega,
    agent_relevance
) -> {
    keep_mass,
    set_mass[n_skills],
    raw_keep_logit,
    raw_skill_logits
}

with:

Active learned-KEEP agent
m
K
	​

=σ(ℓ
K
	​

),
m
SET(z)
	​

=(1−σ(ℓ
K
	​

))softmax(ℓ
Z
	​

)
z
	​

.

The incumbent skill must have exactly zero SET mass.

No incumbent
m
K
	​

=0,
m
SET(z)
	​

=softmax(ℓ
Z
	​

)
z
	​

.
Out-of-contract controller modes

Native-categorical edit or forced full refresh must fail closed in V-K0C rather than be silently interpreted through learned-KEEP semantics.

The initial check therefore still has 4×4=16 legal joint outcomes, but all are SET/SET paths. Noninitial active checks have KEEP plus three legal SET outcomes per agent.

Anti-drift requirement

Sharing only advance_working_state prevents roster-update drift, but does not by itself prevent probability-factorization drift.

The sampling and enumeration paths must share both:

token_mass(...)
advance_working_state(...)

or Gate B must prove exact parity of token log-probabilities and resulting working states for every active/inactive legal token case.

The existing _token_context is already a common deterministic source of the keep and skill logits, and the direct-state toy context is a deterministic function of the centralized state. The new pure mass layer should sit immediately above that common context rather than rederive the factorization independently in the V-K0C driver.

VC-D2 — anchor deduplication is accepted, but the anchor inventory must be immutable

One anchor per:

training seed
× evaluation episode
× noninitial check

is the correct interpretation:

6×64×7=2688.

Both physical agents’ quantities are then computed from that shared pre-decision state. The two focal-agent rows must not become two copies of the same anchor.

However, deduplication cannot mean “take the first of the two rows.”

Required anchor-consistency gate

For each candidate anchor, the two V-K0B focal rows must agree exactly on every shared field, including:

training seed
evaluation episode
check index
agent-order code
checkpoint hash
resolved-config hash
pre-check fingerprint
primitive step
active mask
current and previous targets
natural five-step reward vector
slow-match vector
fast-match vector

The two focal-specific fields must jointly reconstruct one ordered pair of:

current skills
skill ages
focal identities

Any missing row, third duplicate, or shared-field disagreement emits:

INVALID_VK0C_ORDER_TRANSPORT_AUDIT
reason = ANCHOR_INVENTORY_INCONSISTENT

It is not resolved by selecting one row.

Required source-artifact binding

The frozen evidence population is not merely “whatever rows are presently under logs/vk0b_r2_eval.” V-K0C must bind the exact valid V-K0B evidence bundle by SHA-256:

renewal_check_trace.jsonl
renewal_counterfactual_units.jsonl
train_and_checkpoint_manifest.json
summary.json
V-K0A panel and authorization sidecar

and freeze:

trace schema = vk0-trace-2
check-row count = 5,376
deduplicated anchor count = 2,688
training seeds = the six frozen seeds
evaluation episodes = 64 per seed
noninitial checks = 7

The V-K0C driver needs a durable vk0c_input_manifest.json, or equivalent control-row surface, containing these hashes together with the six valid checkpoint/exposure authorizations. Checkpoint hashes alone do not identify the anchor population.

The V-K0B fingerprint machinery already establishes the complete pre-decision reconstruction surface used by the paired replay. V-K0C should reuse that surface rather than define a narrower anchor identity.

VC-D3 — analytic propagation is accepted, with four amendments

The proposed memoized occupancy pushforward is the right implementation. Physically replaying all 16
8
 token paths is neither required nor desirable.

The toy permits an exact reduction because:

local observations are fixed;

the centralized decision context is determined by the target state;

the direct-state R30 path builds compact context deterministically;

the low-level executor is a fixed, stateless action table;

and the autoregressive policy reads the ordered physical-agent skills, ages, and active mask.

The canonical propagated state may therefore be:

initial slow sign
initial fast sign
check index
physical-agent joint skill pair
physical-agent skill ages
active mask

with checkpoint and token order held outside the state as kernel identities.

Amendment 1 — make check 0 explicit

Propagation must begin from:

check_index = 0
active_mask = [False, False]
no incumbent skills
ages = [0, 0]

and use the no-incumbent token semantics frozen under VC-D1.

The initial assignment cannot be simulated as an ordinary active KEEP/SET decision.

Amendment 2 — freeze the inter-check transition

For one five-step interval, the propagated roster transition must match the deployed agent:

KEEP:
    next skill = incumbent
    next age   = current age + 5

SET(z):
    next skill = z
    age immediately after edit = 0
    next-check age = 5

active after legal initial/renewal token = True
next check index = current + 1

Rather than relying only on a hand-coded version of this rule, Gate B must compare the pure transition with an executed one-window agent/environment transition over the complete set of canonical transition cases. The factual V-K0B-row reproduction remains the full assembled-path validity check; it is not the sole test of transitions that happen not to appear in those factual rows.

Amendment 3 — restore the complete-source descriptive panel

The frozen ruling required both:

the 64-episode registered evaluation bank for inference; and

all four initial slow/fast sign combinations as a descriptive complete-source view.

The ledger does not presently bind the second output.

Add a non-inferential propagation table covering:

slow sign ∈ {-1,+1}
fast sign ∈ {-1,+1}
both token orders
fresh and trained policy
all eight checks

The four-sign panel is descriptive and carries no additional bootstrap weight. It must not be substituted for, pooled with, or used to rebalance the 64-episode evidence bank.

Amendment 4 — freeze every ruled propagation output

For each order, policy state, training seed, and episode, the propagation artifact must retain enough row-level evidence to reconstruct:

occupancy probability of every reachable canonical state
expected slow match at every primitive step
expected fast match at every primitive step
expected external reward at every primitive step
expected episode return
expected KEEP/SET rate
expected per-agent renewal rate
expected realized lifetime distribution or sufficient run-length mass

VC-D3 currently names per-step match and return but does not explicitly bind renewal-rate and lifetime outputs, which are part of the frozen V-K0C evidence semantics.

The V-K0A evaluator remains an appropriate deterministic reward kernel for a final joint skill assignment over one five-step window.

VC-D4 — order and occupancy-stratum handling conforms

The following interpretation is correct:

the natural V-K0B row determines whether an anchor belongs to CANONICAL_OCCUPANCY or REVERSED_OCCUPANCY;

both orders are evaluated at every anchor;

occupancy stratum is a property of the state’s provenance, not the order being evaluated.

This yields the required same-x comparison:

P
01
	​

(⋅∣x)versusP
10
	​

(⋅∣x).

The order must remain a separate kernel argument; it must not be folded into the physical-agent state or used to relabel physical agent IDs.

Stratum reporting requirement

All matched-state quantities must be reported:

pooled
CANONICAL_OCCUPANCY
REVERSED_OCCUPANCY

including at least:

TV
D_R fresh
D_R trained
A_R
optimal-assignment mass
slow-coverage-failure mass
fast-coverage-failure mass

This is necessary to prevent pooled cancellation from being misread as absence of a direct order effect.

Factor D protection

SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_IDENTIFIED may not fire merely because the pooled matched-state D
R
(T)
	​

 is equivalent within ±0.5.

For the pure occupancy-mediation label, trained matched-state equivalence must hold:

pooled
and CANONICAL_OCCUPANCY
and REVERSED_OCCUPANCY

while the exact full-episode propagation reproduces the material competence split.

If pooled equivalence is produced by opposite material direct effects in the two occupancy strata, record the stratum-specific direct effects and leave pure occupancy mediation unresolved. Occupancy shift may still be present, but it has not been isolated from direct order sensitivity.

This is the one additional protected result-semantic decision not written in VC-D6.

VC-D5 — fresh initialization conforms

The same-seed double construction is the correct control, provided the hash covers every state-dict entry that can affect the high policy distribution, not merely an arbitrary subset of named parameters.

Freeze a canonical hash over:

high policy state_dict
all decision-context modules reachable under the resolved configuration
relevant buffers
resolved configuration identity

Two independent same-seed constructions must match exactly.

As previously ruled, this is called:

SAME_SEED_FRESH_INITIALIZATION_CONTROL

It is not described as the historical zero-step checkpoint unless independently bound to such an artifact.

VC-D6 — correct the normalization contract and durable analyzer inputs
The 1e-9 condition is rejected as written

The policy’s logits and categorical probabilities are produced in ordinary PyTorch floating-point tensors. The current sampler builds Categorical(logits=skill_logits) and combines sigmoid and skill probabilities on the learned-KEEP branch.

A hard absolute mass tolerance of 10
−9
 is not justified if the enumerated probabilities remain float32. A mathematically valid float32 distribution can differ from one by more than 10
−9
 solely through ordinary softmax, multiplication, and 16-term accumulation.

Frozen numerical rule

Use:

raw token masses produced in the policy probability dtype
joint products accumulated in float64
raw_joint_mass recorded
mass_tolerance = 32 × eps(policy_probability_dtype)

For each order and state:

all masses finite
all masses >= 0
same-label SET mass exactly 0
abs(raw_joint_mass - 1) <= mass_tolerance

A failure is invalidity.

If the raw mass passes, define exactly one canonical vector:

p
^
	​

j
	​

=
∑
k
	​

p
k
	​

p
j
	​

	​

.

Use 
p
^
	​

 consistently for:

TV;

marginals;

expected task consequences;

occupancy propagation;

and every factor calculation.

Record both the raw masses and normalization correction.

“Renormalized only for reporting” is rejected. Using raw mass for propagation while normalized mass appears in reports would make the reported distribution and the propagated policy different objects, and small mass errors would compound over eight checks.

Full distribution rows

vk0c_matched_state_rows.jsonl must preserve all 16 common-coordinate outcomes per:

checkpoint/fresh policy
anchor
evaluated order

with:

physical-agent final skill pair
first token
second conditional token
raw token masses
raw joint mass
canonical joint probability
KEEP/SET marginals
five-step reward
slow-match vector
fast-match vector
task-optimal flag
slow-coverage-failure flag
fast-coverage-failure flag

This makes every ruled distributional and task-consequence statistic independently reconstructible.

Durable authorization

The analyzer cannot be “row-only” unless the rows themselves contain the complete input-authorization record. The simpler binding is:

three JSONL files
+ vk0c_input_manifest.json

where the manifest contains the exact V-K0B input hashes, valid checkpoint exposure blocks, resolved configurations, V-K0A authorization tuple, code/schema identities, and expected row inventories.

Missing or mismatched authorization fires precedence-1 invalidity.

INTERPRETATIONS
1. Analytic propagation versus executed replay
Accepted

VC-D3 correctly interprets the ruling.

“Exact propagation” means dynamic programming over the complete finite Markov state with exact policy probabilities, not physical enumeration of all path histories and not Monte Carlo token sampling.

Executed environment paths remain mandatory for:

prescribed-assignment order conjugacy;

transition-kernel parity;

anchor replay;

and reproduction of the stored factual V-K0B rows.

The analytic propagation is valid only after those conformance checks establish that its policy-input and transition reconstruction matches the deployed path.

2. Enumeration normalization
Corrected

The raw unnormalized sum is evidence and must be retained.

The hard 10
−9
 float32 test is withdrawn. Use the dtype-derived rule above, accumulate in float64, and form one canonical normalized vector after the raw sum passes.

That canonical vector—not a separate reporting-only normalization—must drive every probability-weighted result and propagation.

3. Anchor deduplication
Accepted with a consistency gate

One anchor per:

(seed, evaluation episode, noninitial check)

is correct and gives exactly 2,688 anchors.

Both agents’ focal quantities are computed at that shared anchor. The two source rows must agree on all shared state/provenance fields and jointly reconstruct the complete physical-agent roster. Any disagreement invalidates the anchor inventory; no row is selected preferentially.

CONVERGENCE_DECISION
TOUCHPOINT_2                         CHANGES_REQUIRED

V-K0C scientific route               RETAINED
no-training/no-update boundary        RETAINED
2,688 matched anchors                 RETAINED
both orders at every anchor           RETAINED
analytic exact propagation            ACCEPTED
fresh-versus-trained control           RETAINED
factorized A–E record                 RETAINED

BLOCKING AMENDMENTS
    1. unconditional token-mass semantics, including no-incumbent check 0
    2. shared probability-factorization helper, not only shared roster advance
    3. immutable V-K0B anchor-input manifest and duplicate-row consistency
    4. explicit initial/inter-check propagation semantics
    5. separate four-sign descriptive propagation panel
    6. complete renewal/lifetime propagation outputs
    7. dtype-derived probability-mass tolerance and one canonical distribution
    8. pooled plus occupancy-stratified matched-state outputs
    9. stratum-safe Factor D predicate
   10. durable analyzer authorization surface

NEW TRAINING OR POLICY UPDATE            NOT AUTHORIZED
V-K0C EXECUTION                          NOT AUTHORIZED
V-K1                                     HELD
ORDER-RANDOMIZED TRAINING                HELD
EQUIVARIANT CONTROLLER                   HELD
CONSTRAINED RENEWAL-CLASS MECHANISM      HELD

These amendments do not change the V-K0C scientific question, checkpoint set, evidence bank, materiality unit, competence floor, or conditional successor portfolio. They close the exact probability and propagation semantics needed for two reasonable implementations to instantiate the same localization experiment.

After the amendments are entered into VK0C_REALIZATION_DECISION_LEDGER.md, one convergence turn should return to this same touchpoint. This ruling authorizes neither implementation nor execution.