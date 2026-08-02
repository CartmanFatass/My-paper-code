CONFORMANCE
CHANGES_REQUIRED — the V-K0D scientific comparison is retained, but the current ledger does not yet isolate the two proposed corrections

The three-arm successor comparison remains the correct next route:

PRIMARY
    permutation-equivariant/order-symmetrized carrier

SIMPLER CONTROL
    current R30 with randomized training serialization

REFERENCE
    current R30 with canonical-only training serialization

The fixed clock, KEEP/SET support, supplied executor, training seeds, interaction and optimizer exposure, evaluation bank, and both evaluation serializations remain appropriate matched surfaces. The complete V-K0B access screen may also remain downstream of this competence-localization comparison. Those choices faithfully preserve the V-K0C successor ruling.

The remaining deviations are load-bearing:

Ledger item	Disposition	Required correction
VD-1 — relative-role PRIMARY	Changes required	The proposed populated self block adds duplicate focal information; freeze an identity-removal-only encoding or match that added feature in every arm
VD-2 — preserved token contract	Conforms conditionally	Must preserve identical module shapes, initialization, and optimizer membership across arms
VD-3/VD-4 — randomized order	Changes required	Freeze exactly when a draw occurs, who owns it, how it is reproduced, and how actual order exposure is audited
VD-5 — conjugacy gate	Changes required	Natural fresh-policy anchors are not an exact structural support; freeze the complete finite gate population and the swap operator
VD-6 — arm identities	Changes required	The PRIMARY arm’s training-order policy is omitted; it must be canonical for the proposed causal decomposition
VD-7 — matched exposure	Changes required	Equal counts alone do not establish matched model and optimizer opportunity
V-K0D result mapping	Missing protected binding	Distinguish invalid, support-insufficient, qualified, decisive failure, and unresolved outcomes before applying the four-way portfolio grid
REFERENCE role	Missing protected binding	Freeze the reference as a no-op reproduction control and define what happens if it does not reproduce V-K0B
1. VD-1 changes more than absolute-identity encoding

The current encode_working_roster deliberately skips the focal agent. It writes:

one permutation-invariant skill-count block;

the other agents’ skills into absolute physical-ID slots;

the other agents’ ages into absolute physical-ID slots.

The focal agent’s own current skill and age are already passed separately into _hidden.

VD-1 instead says the new roster encoder writes:

focal features into SELF
other-agent features into OTHER

That adds a second copy of focal skill and age that the reference and randomized-current-R30 arms do not receive. It therefore combines two interventions:

removal of absolute identity;

addition of duplicated focal features.

A performance improvement could not be attributed uniquely to order conjugacy.

Required PRIMARY encoding

For the cleanest matched intervention, freeze:

invariant skill-count block
    unchanged

relative OTHER skill block
    the sole other agent's current skill
    using the existing count scale

relative OTHER age block
    the sole other agent's current age
    using the existing age transform

relative SELF blocks
    zero, because focal skill and age already enter _hidden separately

absolute physical-ID information
    absent

ar_prefix_dim
    unchanged

input-layer shape and parameter count
    unchanged

The existing count scale and age transformation must carry forward exactly. No input dimension, initializer, hidden width, or optimizer parameter set changes.

A populated SELF block is still possible only if the same duplicate focal features are added to the randomized and canonical arms. That would alter the reference realization and require a different no-op baseline. The minimal selected correction is therefore the fixed anonymous-OTHER mapping.

Wording correction

The new encoder is not literally “information-lossless” relative to the current policy: it deliberately deletes the absolute physical-ID shortcut. The accurate statement is:

It preserves all anonymous task and roster information available in the current realization while removing absolute agent-label information.

That deletion is the intended treatment. All other information surfaces must remain matched.

2. Retaining the AR loop is acceptable

The prior ruling did not require replacing the autoregressive policy with a simultaneous joint head. It selected a permutation-equivariant or order-symmetrized carrier. A shared autoregressive policy with an anonymous relative roster representation is a valid PRIMARY candidate.

The correct structural identity is:

P
01
	​

(a
0
	​

,a
1
	​

∣x)=P
10
	​

(a
1
	​

,a
0
	​

∣swap(x)),

where swap(x) swaps every physical-agent-indexed component of the state and roster.

This is permutation conjugacy. It is not the stronger same-state serialization-invariance statement

P
01
	​

(a
0
	​

,a
1
	​

∣x)=P
10
	​

(a
0
	​

,a
1
	​

∣x).

The latter need not hold while the second mover conditions on the first mover’s realized edit. The existing policy advances the working roster token by token, so first- and second-mover conditional roles remain even after absolute identity is removed.

Accordingly:

VD-1 may retain the AR conditional structure.

The pre-training gate certifies permutation conjugacy.

The frozen both-order competence screen determines whether this structural property is sufficient for order-robust execution.

The ledger must not state or imply that relative-role encoding guarantees same-state order invariance or guarantees that both-order competence will pass.

3. The PRIMARY training order must be frozen as canonical

VD-6 gives explicit values for:

CONTROL
    r30_training_order_policy = uniform_per_check

REFERENCE
    r30_training_order_policy = canonical

but does not state the PRIMARY value.

This is a protected causal choice.

The three-arm comparison isolates two proposed corrections only if it is:

Arm	Roster representation	Training serialization
PRIMARY	anonymous relative roster	canonical
CONTROL	current absolute-ID roster	uniform per check
REFERENCE	current absolute-ID roster	canonical

If PRIMARY also uses uniform-per-check training, it combines the structural and training-distribution interventions. Then:

CONTROL fails
PRIMARY passes

would not establish that the representation correction was required; it could establish an interaction between relative encoding and randomization.

Freeze:

PRIMARY:
    high_controller = r30_fixed_clock_ar_edit_conjugate
    r30_training_order_policy = canonical

CONTROL:
    high_controller = r30_fixed_clock_ar_edit
    r30_training_order_policy = uniform_per_check

REFERENCE:
    high_controller = r30_fixed_clock_ar_edit
    r30_training_order_policy = canonical

The launcher must reject every other controller/order-policy combination in a scientific V-K0D run.

4. VD-3/VD-4 need an exact order-assignment contract

Per-check randomization is an acceptable reading of “randomized training serialization.” It is preferable here to per-episode randomization because the identified specialization acts at each autoregressive renewal check.

But “thread a Philox generator from training into the call sites” does not yet define the treatment.

The current agent_order enters the R30 decision call, while whether a high decision is actually due is resolved inside the R30 assignment path. The current scientific exposure unit is a completed high-check autoregressive sequence, not every invocation of the outer method.

Required draw semantics

Freeze:

one order assignment
    per completed high-check autoregressive sequence

includes
    the initial assignment sequence

excludes
    non-due calls
    continuation-value calls
    aborted calls that emit no decision row

chosen order
    stored in the committed high-check row
    reused by PPO sequence evaluation

A draw must occur only after the due decision has been established and before token generation.

Required RNG ownership

The preferable realization is a counter-based assignment derived from the immutable decision identity:

training seed
environment id
episode id
check index
stream version = vk0d-order-1

This prevents unrelated batching or call-order changes from altering which episode/check receives which serialization.

A single sequential Philox generator is also admissible only if the ledger freezes:

exact environment/check traversal order;

its state at checkpoint and resume boundaries;

refusal of resumed training without that state;

and the rule that no non-due call consumes it.

Required durable exposure

For each seed and arm, record:

order stream identity/version
completed canonical-order sequences
completed reversed-order sequences
agent_0 first-position count
agent_1 first-position count
schedule digest over ordered high-check identities and assigned orders
completed-sequence total

The ordered schedule must be independently regenerated from the frozen identity and compared exactly with the committed high-check rows.

The structural identities include:

N
01
	​

+N
10
	​

=N
high check sequences
	​

.

For the canonical arms:

N_10 = 0
N_01 = N_high_check_sequences

For the randomized arm, validity means exact agreement with the preregistered generated schedule—not merely that both counters are nonzero.

Wording correction

A dedicated order stream ensures that the order assignment itself does not consume the global PyTorch stream. It does not make physical-agent stochastic outcomes or complete training trajectories identical across arms: reversing the autoregressive order deliberately maps later policy draws to a different conditional decision. The ledger should claim RNG-stream isolation, not full non-order trajectory identity.

5. VD-5 does not yet define an exact structural gate

The V-K0C machinery is an appropriate implementation basis:

token_mass is the sole probability authority;

order enumeration is in common physical-agent coordinates;

run_forced_window executes the real controller and environment;

and the prescribed-assignment control compares physical skills, primitive actions, rewards, match vectors, and post-window state.

The proposed gate population, however, is described as states reached by a fresh natural policy across four sign pairs plus zero-action clock states. That is not an exact structural support. It can omit:

joint incumbent skill pairs;

reachable age pairs;

active/no-incumbent states;

or checks that the fresh random policy does not naturally visit.

An encoder defect on an omitted roster would survive the gate.

Required gate population

Freeze the finite source support explicitly:

INITIAL CLASS
    check 0
    active = [False, False]
    no incumbents
    ages = [0,0]
    all four sign pairs

ACTIVE CLASSES
    checks 1..7
    all four sign pairs
    all 16 physical joint-skill pairs
    every reachable age pair at that check
    active = [True,True]

ORDER VIEWS
    [0,1]
    [1,0]

For every state, define swap(x) explicitly over:

observations;

skill array;

age array;

active mask;

any agent-indexed auxiliary context.

The global target state remains unchanged where it is anonymous.

The PRIMARY must satisfy the registered conjugacy equality for the complete panel. The executed prescribed-assignment control must also pass.

Paired negative

Do not rely exclusively on one random initialization of the canonical reference to make the gate red. A random reference can accidentally suppress the identity slots on a finite panel.

Use a deliberate negative witness that restores the current absolute-ID encoder and deterministically makes the two absolute identity blocks consequential. The gate must reject it.

The canonical reference’s observed result may be recorded as an additional negative, but it is not the sole sensitivity proof.

Final-checkpoint gate

The same conjugacy gate must be rerun on every trained PRIMARY checkpoint before its competence result can be read. A pre-training PASS alone does not license a checkpoint whose configuration, encoder flag, or parameter wiring later drifted.

6. VD-7 matches counts but not yet model and optimizer opportunity

The frozen comparison requires matched model and optimizer exposure, not just:

640,000 interactions
1,000 updates
3,000 high optimizer steps

The current launcher already has a resolved configuration hash and exact training-exposure validation surface, which can be extended for V-K0D.

Before launch, freeze and verify per seed:

same high-policy state_dict keys and tensor shapes
same input dimension
same hidden widths
same parameter count
same high-value architecture
same fixed low executor
same optimizer class and hyperparameters
same optimizer parameter membership
same initial actor/value parameter bytes
same initial optimizer state

The PRIMARY context flag must create no parameter or initialization-order change. Under the same seed, the three arms’ initial trainable module hashes must therefore be identical.

The only pre-training differences may be:

PRIMARY
    anonymous roster encoding flag

CONTROL
    order schedule

REFERENCE
    neither

Actual interaction, update, sequence, token, order-exposure, optimizer-step, and parameter-coverage records must all pass independently for every arm.

7. The canonical reference needs a frozen no-op role

The reference is not decorative. It is the causal control showing that the V-K0D training and evaluation shell still reproduces the valid V-K0B failure when neither proposed correction is enabled.

Freeze:

REFERENCE_CONFORMS

only if, for every seed:

model and optimizer state digests at initialization match the valid V-K0B reference;

the canonical training path consumes no order-stream draw;

final actor/value and optimizer-state digests reproduce the valid V-K0B bundle, or a pre-frozen equivalence rule is satisfied;

exact training exposure matches;

the frozen evaluation reproduces canonical competence above 0.75 and reversed competence decisively below 0.75.

The strongest and cheapest binding is exact equality of the trainable model and optimizer-state digests to the valid V-K0B rerun bundles. Literal checkpoint-file equality is unnecessary if new provenance metadata changes serialized non-model fields.

If the reference does not reproduce, V-K0D cannot attribute differences among the successor arms. That is:

INVALID_VK0D_CARRIER_COMPARISON
reason = CANONICAL_REFERENCE_NOT_REPRODUCED

not evidence for or against either correction.

8. The four-way portfolio grid needs fail/unresolved semantics

The ledger defines only pass = V-K0B competence screen passes both orders.

That leaves every non-pass result called “fail,” contrary to the project’s required separation between decisive failure and unresolved evidence.

Freeze an arm-level status before applying the successor grid.

Arm status

For every arm and each required slow/fast × order quantity:

QUALIFIED
    every required LCB95 > 0.75

DECISIVE_COMPETENCE_FAILURE
    at least one required UCB95 <= 0.75

COMPETENCE_UNRESOLVED
    neither qualified nor decisively failed

SUPPORT_INSUFFICIENT
    any frozen support floor fails

INVALID
    provenance, exposure, replay, gate, reference,
    checkpoint, or schema validity fails

Equality at 0.75 is non-pass and decisive only under the frozen inclusive upper-bound rule.

Comparison precedence
1. Any shared comparison invalidity
       -> INVALID_VK0D_CARRIER_COMPARISON

2. Reference not reproduced
       -> INVALID_VK0D_CARRIER_COMPARISON

3. Any conclusion-bearing arm support insufficient
       -> VK0D_SUPPORT_INSUFFICIENT

4. CONTROL = QUALIFIED
       -> ORDER_RANDOMIZATION_COMPETENCE_QUALIFIED
          retain the simpler correction
          PRIMARY status still reported

5. CONTROL = DECISIVE_COMPETENCE_FAILURE
   AND PRIMARY = QUALIFIED
       -> STRUCTURAL_REPRESENTATION_CORRECTION_REQUIRED

6. CONTROL = DECISIVE_COMPETENCE_FAILURE
   AND PRIMARY = DECISIVE_COMPETENCE_FAILURE
       -> AUTOREGRESSIVE_CARRIER_REOPENED

7. Every other valid combination
       -> VK0D_SUCCESSOR_COMPARISON_UNRESOLVED

In particular:

CONTROL unresolved
PRIMARY qualified

does not establish that the structural correction is required.

If CONTROL qualifies while PRIMARY is unresolved or fails, the valid CONTROL result is sufficient to retain the simpler correction. A primary implementation invalidity may remain a separate unresolved arm, provided it does not contaminate shared training/evaluation infrastructure; shared-shell invalidity invalidates the comparison.

INTERPRETATIONS
1. Relative-role encoding with the AR loop retained
ACCEPTED WITH CORRECTIONS

The prior ruling did not require deleting the autoregressive conditional structure.

The selected PRIMARY may be:

shared AR policy
+
anonymous relative roster context
+
canonical training serialization

Its structural gate proves permutation conjugacy under simultaneous state/agent swap. It does not prove same-state order invariance, and it does not preordain the both-order competence result.

The populated SELF block is rejected as an unmatched second intervention. Preserve the current focal-information multiplicity and anonymize only the other-agent roster slot.

2. Per-check randomized serialization
ACCEPTED WITH THE DRAW AND PROVENANCE CONTRACT ABOVE

Per-check randomization is the appropriate strongest test of whether permanent first/second training position caused the specialization.

The binding unit is one completed high-check sequence, not one outer call or one primitive step.

The randomized schedule must be deterministic from its frozen unit identities and auditable after training.

3. “Passes both orders” means competence at V-K0D
ACCEPTED

V-K0D may use only the frozen competence and support screen to choose which order-robust carrier candidate proceeds.

A V-K0D qualification means:

The arm satisfies the registered natural-task competence prerequisite under both evaluation serializations.

It does not mean that the arm has passed the complete unrestricted-carrier access claim.

After V-K0D selects a candidate, that candidate must still rerun the full V-K0B screen:

opportunity access;

sampled-SET competence;

natural renewal value;

KEEP/SET hazard alignment;

and the complete invalidity/support chain.

Only that later full-access result can unblock V-K1.

Because VD-1 explicitly supplies no independently identified variable-N benefit, if both PRIMARY and CONTROL qualify, the frozen portfolio rule selects the simpler order-randomized current R30.

CONVERGENCE_DECISION
TOUCHPOINT_2                         CHANGES_REQUIRED

V-K0D three-arm comparison            RETAINED
relative-role AR candidate            RETAINED WITH CORRECTION
uniform-per-check control             RETAINED
canonical reference                   RETAINED
same seeds and evaluation bank        RETAINED
competence-only V-K0D gate            ACCEPTED
full V-K0B access screen later        RETAINED

BLOCKING AMENDMENTS
    1. remove the unmatched populated SELF roster block;
       freeze the exact anonymous-OTHER encoding

    2. freeze PRIMARY training serialization as canonical

    3. freeze completed-check order-draw ownership,
       deterministic schedule identity, and actual order exposure

    4. replace natural fresh-policy gate states with the complete
       finite conjugacy panel; define swap(x), a deliberate negative,
       and a post-training conjugacy recheck

    5. freeze identical model shape, initialization, optimizer membership,
       and actual exposure across all arms

    6. freeze the canonical reference no-op/reproduction gate

    7. freeze arm-level INVALID / SUPPORT_INSUFFICIENT /
       QUALIFIED / DECISIVE_FAILURE / UNRESOLVED semantics
       and the resulting comparison precedence

NEW PROTECTED DECISIONS FOUND         YES
ANOTHER CONVERGENCE TURN REQUIRED     YES

IMPLEMENTATION                         NOT AUTHORIZED
CONCLUSION-BEARING TRAINING            NOT AUTHORIZED
V-K1                                   HELD
FULL V-K0B SUCCESSOR ACCESS SCREEN     HELD
CONSTRAINED RENEWAL-CLASS MECHANISM    HELD
VARIABLE-N GENERALIZATION              HELD

These corrections do not replace the selected V-K0D direction. They make the two candidate interventions causally separable and prevent a competence non-pass, an unmatched feature addition, or an unaudited order schedule from deciding the successor portfolio.