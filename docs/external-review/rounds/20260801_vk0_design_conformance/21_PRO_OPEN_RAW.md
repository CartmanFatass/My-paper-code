CONFORMANCE

CHANGES_REQUIRED — the design does not yet conform.

The overall scientific sequence is correct: exact V-K0A source qualification, followed conditionally by the unrestricted-R30 V-K0B screen. The real environment, fixed primitive table, six frozen training seeds, held-out order banks, split-sample counterfactuals, nested bootstrap, and no-constrained-mechanism boundary all preserve the prior ruling.

The deviations are in VK-D2, VK-D3, VK-D6, VK-D9, and VK-D10. VK-D8 also needs a fail-closed runtime binding before launch. These are not alternative scientific routes; they are corrections required to instantiate the frozen estimands and result branches.

Ledger item	Disposition	Required correction
VK-D1	Conforms	Retain the real environment and exact fixed action table.
VK-D2	Deviates	Replace the raw lexicographic incumbent tie-break with two explicit, permutation-equivariant oracle tracks.
VK-D3	Deviates	From-reset replay is acceptable, but its proposed equality test is incomplete and replay mismatches must invalidate rather than be dropped.
VK-D4	Conforms conditionally	Serial global-RNG branches are acceptable only after exact branch-local state/RNG restoration is enforced.
VK-D5	Conforms conditionally	Validate that agent_order is an exact permutation and apply it at every check in every replay branch.
VK-D6	Deviates	The “verbatim” schemas lack inferential keys and sufficient durable natural-execution evidence.
VK-D7	Conforms	Retain the frozen namespace, disjoint selection/evaluation streams, common evaluation bank, and bootstrap seed.
VK-D8	Incomplete binding	Add a resolved-runtime preflight, explicit backend, and checkpoint/config identities before training.
VK-D9	Deviates	Freeze executable predicates for decisive failure versus unresolved; “eight rows verbatim” is not an executable selector.
VK-D10	Deviates	Bind V-K0B to the exact V-K0A artifact and use the exhaustive oracle on each natural check’s actual incumbents.
VK-D2 — the lexicographic tie-break is not anonymous

The ruling fixes two anonymous slot-assignment permutations in the 112-row panel. VK-D2 instead starts from one joint optimum and resolves every tie by the lexicographically smallest raw pair. That rule does not commute with a slot permutation.

For example, when the target-serving skills are 0 and 2, the two optimal pairs are (0,2) and (2,0). Raw lexicographic selection returns (0,2). After swapping the agent labels, it still returns (0,2), rather than the required relabelled pair (2,0). Thus the two nominal permutation panels can collapse onto one identity-preferred path. That is incompatible with both the ruled panel and the invalidity condition that a permutation change only relabel the underlying source state. The environment itself is explicitly symmetric and scores the better of the two assignments.

Correct VK-D2 as follows:

assignment_permutation = 0:
    slot 0 carries the slow duty; slot 1 carries the fast duty

assignment_permutation = 1:
    slot 1 carries the slow duty; slot 0 carries the fast duty

At the initial check, instantiate the corresponding optimal pair. At each later check, choose the joint-return-maximizing legal edit that preserves that permutation. Equivalently, use a permutation-covariant tie-break expressed in permutation-canonical coordinates, not lexicographic raw agent IDs.

This preserves:

4 sign combinations
× 2 true permutation tracks
× 7 noninitial checks
× 2 focals
= 112 focal rows

Exhaustive enumeration of all incumbent pairs is not required. The ruled panel is a pair of permutation-related oracle-optimal histories, not an all-incumbent-state census.

VK-D3 — from-reset replay is admissible, but the proposed certificate is insufficient

The prior ruling requires equality at the focal boundary for environment state, observations, skills, ages, active mask, check clock, agent order, hidden state, RNG state, and policy/checkpoint identity.

The cited precedent does not verify that complete object:

_prefix_matches compares prefix action arrays and rewards.

check_incumbents stores only (skill, active).

_focal_state_matches compares those incumbent dictionaries, even though its docstring also claims to verify ages.

The recorded centralized states are not part of that equality predicate.

No focal-boundary RNG-state equality is tested.

Therefore the statement in VK-D3 that the precedent already verifies every listed snapshot component is false.

A new mid-episode snapshot subsystem is still unnecessary. From-reset replay conforms once every natural and counterfactual branch computes and compares one canonical pre-decision boundary fingerprint containing at least:

environment state and observation bytes
environment step
environment-owned RNG state
active skills
skill ages
active mask
steps_to_check
episode_steps
agent order
low actor and critic hidden arrays, even when identically zero
NumPy global RNG state
PyTorch CPU RNG state
PyTorch CUDA RNG state if applicable
checkpoint SHA-256
resolved-config hash
contract and trace-schema versions

Any other mutable runtime field read before or during the focal decision must be added. The fixed primitive executor is indeed stateless and zero-parameter, while the high actor is a per-check MLP, so this fingerprint remains small.

Most importantly:

any focal-boundary replay mismatch
    -> INVALID_VARIABLE_K_URGENCY_AUDIT

It must not be dropped and converted into ordinary support attrition. Selective dropping can alter the urgency and agent-order composition of the retained sample. In this deterministic toy, a replay mismatch is operational corruption of the registered paired estimand.

VK-D5 — accepted with one fail-closed guard

Threading an optional agent_order=None through maybe_assign_skills and _r30_maybe_assign_skills is the correct minimal change. The current call constructs ascending order once, passes it into the autoregressive sampler, stores it in the high-check row, and later associates tokens with agents through that order.

Add an assertion before sampling:

sorted(agent_order) == [0, 1]
len(agent_order) == 2
no duplicates

The selected order must be held for every check in an episode and for all natural, KEEP, named-SET, sampled-SET, and replay branches belonging to that episode. Default None must retain byte-identical ascending behavior.

VK-D6 — the ruled semantic payload was not a closed machine schema

“Transcribed verbatim” cannot mean “no additional identity fields.” The counterfactual field list in the ruling describes the semantic payload, but D9 requires resampling by training seed and episode, stratification by order, and joining every branch to a check-agent oracle label. Without durable parent keys, that analysis is not reproducible.

Both JSONL schemas therefore need at least:

contract_id
trace_schema_version
training_seed
evaluation_seed
episode_id
agent_order_code
check_index
focal_agent
check_unit_id
checkpoint_hash
resolved_config_hash

Each counterfactual row additionally needs:

branch_unit_id
estimand_family =
    KEEP_REFERENCE |
    OPP_NAMED_SET |
    SET_SAMPLED |
    NATURAL
parent_check_unit_id

The old audit precedent also cannot be copied for durable competence evidence: its CheckRow contains slow_match, fast_match, and team_reward, but _append_rows writes them as NaN; competence is computed from separate in-memory episode arrays and then placed directly in the result JSON. That violates the new ruling that conclusion-bearing statistics be reconstructible from durable row-level evidence.

Persist, either in the natural counterfactual row or in the check row:

five-step natural external-reward vector
five-step slow-match vector
five-step fast-match vector

Alternatively, source_oracle_panel.json may contain the exact action table and a complete deterministic recomputation contract, but directly persisting the three vectors is smaller and less fragile.

The corrected rule is:

The schemas contain all ruled semantic fields, plus the nonsemantic identity, provenance, and recomputation keys required by the registered analysis.

VK-D8 — add a resolved-runtime preflight

The scientific intent of VK-D8 conforms, but post-run exposure checking alone is too late. Before the first environment step, each training process must write and validate the resolved values for:

scenario
controller
k0
n_agents
n_skills
action-table hash
direct-state context mode
num_envs
rollout_length
total_timesteps
high PPO epochs
high learning rate
low optimizer absence
all intrinsic/shaping paths disabled
device/backend
training seed
output root

The existing configuration fixes the relevant model, reward, exposure, and optimizer choices and describes this as a CPU learned-KEEP lane. The existing audit also explicitly constructs the evaluation agent on CPU. The backend should therefore be pinned explicitly rather than inherited from a launcher default.

Do not bind scientific identity to the literal filename latest.pt. Bind it to:

final-checkpoint path
checkpoint SHA-256
training seed
resolved-config hash
recorded final exposure

The timing microbenchmark may remain only if it uses a non-scientific seed, discards its checkpoint, and reads no reward or capability metric. It may affect scheduling, never the contract, budget, or branch.

VK-D9 — freeze the actual first-match selector

The ledger says the eight result rows will be implemented “verbatim,” but the ruling supplies inequalities, not a complete Boolean selector for decisive failure versus unresolved. This is a protected branch decision and cannot be left to analyzer implementation.

For each required opportunity stratum

pooled
canonical order
reversed order

freeze:

opp_pass⟺LCB(U
urgent
opp
	​

)>0.5∧UCB(U
stable
opp
	​

)<0.5∧LCB(U
urgent
opp
	​

−U
stable
opp
	​

)>0.5.

A stratum is a decisive opportunity failure iff at least one holds:

UCB(U
urgent
opp
	​

)≤0.5,
LCB(U
stable
opp
	​

)≥0.5,
UCB(U
urgent
opp
	​

−U
stable
opp
	​

)≤0.5.

If any required stratum decisively fails, emit row 5:

SOURCE_IDENTIFIED_R30_OPPORTUNITY_NOT_ACCESSED

If no stratum decisively fails but at least one does not pass, emit row 7, the generic unresolved branch.

After opportunity passes, natural alignment is decisively wrong iff any of the following holds:

UCB(U
urgent
nat
	​

)≤0.5,
LCB(U
stable
nat
	​

)≥0.5,
UCB(U
stable
nat
	​

)≤−0.5,
UCB(Δ
λ
	​

)≤0.

The realized SET-rate contrast remains a positive-point-estimate pass requirement. It independently triggers wrong direction only if its upper bound is at or below zero; otherwise a nonpositive point estimate is unresolved.

This realizes the earlier rule that decisive opposite evidence requires an upper or lower bound beyond the relevant boundary, whereas merely missing a lower-bound pass gate is unresolved.

VK-D10 — bind the gate and oracle implementation

Two additional bindings are required.

First, V-K0B may not accept an arbitrary artifact containing the word IDENTIFIED. The V-K0A authorization artifact must bind:

contract ID
stage commit
environment blob SHA
fixed action-table hash
oracle-script hash
panel-schema version
112-row count
all validity predicates
verdict
artifact SHA-256

V-K0B must verify that tuple before loading a checkpoint. A stale or differently constituted source artifact is an invalid audit, not a failed source gate.

Second, every V-K0B natural check must compute U_src by invoking the same exhaustive V-K0A oracle on that check’s actual pre-decision incumbent pair. It must not assign urgency from:

physical phase
skill axis
fast/stable labels
the V-K0A oracle-optimal track

The cited older audit classifies “flex” or “stable” directly from whether the incumbent skill belongs to the fast or slow axis. That script is an acceptable replay-surface precedent but is not an admissible implementation of the newly ruled source estimand.

Finally, the final branch selector must consume the exposure/provenance manifest as well as the two JSONL files and oracle panel. Statistical quantities remain row-recomputable; manifest mismatch, replay mismatch, checkpoint mismatch, or nonzero prohibited optimizer exposure feeds the precedence-1 invalid branch.

INTERPRETATIONS
1. VK-D2 panel incumbents

Corrected, not rejected.

Using oracle-optimal incumbents is the smallest acceptable reading. Exhaustive enumeration over every incumbent pair is not required and would change the ruled 112-row panel.

The correction is that the oracle must maintain two explicit permutation-related optimal histories. Raw lexicographic tie-breaking over physical slot IDs is rejected because it is not permutation-equivariant.

2. VK-D3 from-reset replay

Accepted in principle; the current certificate and drop semantics are rejected.

A new snapshot subsystem is unnecessary. Verified from-reset reconstruction is equivalent to restore on this deterministic, stateless-low-level toy, provided the complete pre-decision fingerprint is identical.

Prefix action/reward equality plus incumbent equality is insufficient. Any mismatch in the complete fingerprint emits the invalid branch; it is never silently dropped.

3. VK-D4 serial branches and global RNG

Accepted conditionally.

Serial execution is appropriate because the existing policy uses process-global PyTorch randomness, and parallel branch execution would race it. The six training seeds may remain separate processes. The forced-token implementation already samples the focal KEEP variate and skill variate before applying the force and lets later agents observe the modified working roster, which is the ruled autoregressive continuation.

No per-branch generator refactor is required if:

every branch seed derives solely from its immutable unit identity;

every relevant RNG state is reset or reconstructed before the branch;

branch enumeration order cannot change a derived seed;

the complete pre-decision fingerprint passes;

any future introduction of another reachable RNG source reopens VK-D4.

CONVERGENCE_DECISION
TOUCHPOINT_2 = CHANGES_REQUIRED

V-K0 scientific direction       RETAINED
V-K0A -> conditional V-K0B      RETAINED
alternative experiment          NOT SELECTED
implementation authorization    NOT GRANTED
compute authorization           NOT GRANTED

Revise the ledger before constructing the proof-sized executable skeleton. The minimum closure set is:

1. permutation-equivariant two-track V-K0A incumbent construction;
2. complete from-reset boundary fingerprint with fail-closed replay;
3. durable row identity/recomputation fields and natural match vectors;
4. resolved-runtime/checkpoint/source-artifact provenance;
5. actual-incumbent exhaustive U_src in V-K0B;
6. executable decisive-failure versus unresolved branch predicates.

Because VK-D2 changes the source-panel realization and VK-D9 freezes result-branch semantics, the amended ledger should return to this same conformance touchpoint. No experiment should run before that review closes. Review output itself does not authorize code or compute.