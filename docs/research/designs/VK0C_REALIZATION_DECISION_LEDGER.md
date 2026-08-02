# V-K0C realization — Project Manager decision ledger

Status: **CONVERGED — CONFORMS** (round `20260801_vk0c_design_conformance`,
`22_PRO_CONVERGENCE_3.md`): all amendments A-VC-1..11 closed, every
scientific surface frozen, no further design round. Five Gate-B realization
clarifications bind the implementation (verbatim in the raw): (C-1)
`token_mass` is the sole probability authority — a second
logits-to-probability path reopens A-VC-1/2; (C-2) the propagation state
(check index, joint skill pair, ages, active mask, target phase/sign) is
frozen — a hidden variable affecting outcomes enters the state or returns
the design to review; (C-3) raw masses → validation → ONE canonical
distribution everywhere downstream; (C-4) the Factor-D label is
`SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_IDENTIFIED` under pooled + both
stratum equivalences plus propagation reproducing the split; (C-5) analyzer
authorization only from the input manifest and stamped rows, never
directory or file names. The Gate-B witness lists (probability, transition,
order, artifact, numerical paths) precede full implementation; execution is
not authorized by the convergence.
The evidence semantics are FROZEN by the ruling of round
`20260801_vk0b_valid_rerun_result` (V-K0C sections 1–9); this ledger records
only the realization bindings. Zero training, zero policy updates, zero
checkpoint selection; nothing here moves a threshold, estimand, floor, seed
or result predicate beyond what the ruling froze.

## VC-D1 — pure distribution API with explicit working state

`FixedClockAREditPolicy` gains one public method,
`token_distribution(...)`: same inputs as one agent-iteration of
`act_sequence` but with EXPLICIT `working_skills/working_ages/
working_active`, returning `(keep_prob, skill_probs)` — `sigmoid(keep_logit)`
and the softmax of `_masked_skill_logits` (the `finfo.min` mask underflows
to exactly zero mass on the incumbent). Pure: no sampling, no RNG
consumption, no buffer writes. The joint distribution under an order is
enumerated by the caller: first agent's distribution from the initial
roster; for each of its 4 outcomes, advance the working state and read the
second agent's conditional — P(joint) = P(first) × P(second | first).

**Anti-drift binding:** the working-state advance (`act_sequence`
:432-438) is refactored into a shared pure helper
`advance_working_state(working_*, agent_id, kind, skill)`;
`act_sequence` itself calls the helper, so the enumeration path and the
sampling path cannot diverge. The three pinned forced-token tests must
stay green (behavioral no-op refactor).

## VC-D2 — anchors by natural from-reset replay; no replay generalization

The 2,688 matched anchors are the natural (unforced) pre-decision states
of the valid V-K0B evaluation; each is restored with the existing
importable `replay_branch`-style natural prefix (from-reset, byte-verified
`build_fingerprint` against the stored V-K0B `pre_check_fingerprint` —
any mismatch is `INVALID_VK0C_ORDER_TRANSPORT_AUDIT`, never a dropped
anchor). At the anchor: both orders' joint distributions are enumerated
purely (VC-D1, no stepping, no RNG); the deterministic positive control
forces BOTH agents via the existing multi-agent `forced_tokens` dict under
each order and rolls exactly 5 steps, comparing final skills by physical
agent, primitive actions, five-step reward and match vectors, and
post-window state. The prescribed-assignment control runs for every legal
final joint assignment at every anchor, as ruled.

## VC-D3 — exact propagation by finite-state occupancy, not tree replay

The toy's complete high-level state is finite and sufficient (constant-zero
local obs; centralized state = targets from (steps, signs); stateless
executor; feedforward low level): `(initial signs, check index, joint
skill pair, skill ages, active mask)`. The propagation driver enumerates
reachable states check-by-check as an occupancy map: at each state × order,
policy inputs are rebuilt exactly the way the natural driver builds them
(env reconstructed at `(steps, signs)` by zero-action stepping — the
documented action-independence of the env clock — plus the roster given by
the state), the 16-outcome distribution is read from VC-D1, and occupancy
pushes forward; per-step expected slow/fast match and returns come from the
deterministic executor via the V-K0A window evaluator. Memoization on the
canonical state tuple bounds the work (thousands of states, not 16^8
paths). The propagation must reproduce the stored factual V-K0B rows
(replaying each episode's factual token sequence through the same
machinery and comparing the row's five-step vectors) — failure is
invalidity, not evidence.

## VC-D4 — orders and strata

`[0,1]` and `[1,0]` are caller-selected per evaluation (the existing
`agent_order` hook); anchors carry their natural occupancy stratum
(CANONICAL_OCCUPANCY / REVERSED_OCCUPANCY per the episode's bank parity);
both orders are evaluated at every anchor regardless of stratum, giving
the ruled P01-vs-P10-at-same-x comparison.

## VC-D5 — fresh-initialization control

For each training seed: `torch.manual_seed(seed)` immediately before each
of two independent `StandaloneProcessAgent` constructions from the
resolved config (construction consumes the global stream in fixed order;
no internal reseeding — scout-verified); require identical parameter
hashes across the two constructions (else invalidity: nondeterministic
construction); then run the same matched-state and propagation panels on
the fresh policy. Quantities D_R^(0), D_R^(T), A_R per the ruling.

## VC-D6 — drivers, artifacts, analyzer

New `scripts/audit_vk0c_order_transport.py`: authorization (the six
`VK0B_R2_VALID_EXPOSURE_CHECKPOINTS` bundles — checkpoint SHA,
vk0b-exposure-1 block, source-manifest hash, resolved-config hash, V-K0A
tuple; historical bundles never enter the chain), anchor restoration,
positive control, exact enumeration (validity: all 16 outcomes exactly
once, finite nonnegative, sum 1 within 1e-9 then renormalized for
reporting with the raw sum recorded, same-label SET absent by mask —
asserted exactly zero mass), TV and task-consequence quantities,
propagation, factual-row reproduction, fresh-init control; rows to
`vk0c_matched_state_rows.jsonl` / `vk0c_propagation_rows.jsonl` /
`vk0c_control_rows.jsonl` with the identity keys of the vk0 family
(contract_id "VK0_TOY_RENEWAL_URGENCY", vk0c_schema_version "vk0c-1",
seeds, anchors, checkpoint hashes). New
`scripts/analyze_vk0c_result.py`: the ruled factorized record — precedence-1
invalidity conditions; Factor A (fresh distributions differ at ≥1 matched
state; promotion to materially-task-relevant only outside ±0.5); Factor B
(LEARNED_CANONICAL_ORDER_SPECIALIZATION_IDENTIFIED per the three ruled
conditions); Factor C (amplification LCB95(A_R) > 0.5); Factor D
(occupancy mediation); Factor E / unresolved; existing bootstrap
hierarchy, 10,000 iterations, the existing frozen VK0 bootstrap seed,
paired-within-state comparisons, δ=0.5 and the 0.75 bridge floor.
`summary` recomputable solely from rows.

## Cost (informational)

Anchor restorations ≈ 2,688 from-reset replays (≤40 steps each) ≈ minutes.
Positive control ≈ 2,688 × 16 × 2 windows of 5 steps ≈ 4.3×10^5 window
rolls — comparable to the V-K0B evaluation (~30–60 min). Enumeration and
propagation are pure forward passes over a memoized finite state space —
minutes. Fresh-init panels double the pure parts only. No training.

## Frozen amendments from the conformance ruling (round 20260801_vk0c_design_conformance, CHANGES_REQUIRED)

**A-VC-1 (unconditional token-mass semantics).** The pure API is
`token_mass(joint_obs, compact, team_vector, working_skills, working_ages,
working_active, agent_id, omega, agent_relevance) → {keep_mass,
set_mass[n_skills], raw_keep_logit, raw_skill_logits}` with branch
semantics: active learned-KEEP agent — `m_K = σ(ℓ_K)`,
`m_SET(z) = (1−σ(ℓ_K))·softmax(ℓ_Z)_z`, incumbent SET mass exactly zero;
NO incumbent — `m_K = 0`, `m_SET(z) = softmax(ℓ_Z)_z` (unmasked). The
initial check has 16 SET/SET outcomes; noninitial active checks have
KEEP + 3 SETs per agent. Native-categorical edit or forced full refresh
fail closed in V-K0C.

**A-VC-2 (shared factorization, not only shared roster advance).** The
sampling and enumeration paths share BOTH `token_mass(...)` and
`advance_working_state(...)` — the mass layer sits immediately above the
common `_token_context`, and `act_sequence` consumes it (or Gate B proves
exact log-probability and working-state parity for every active/inactive
legal token case; the shared-helper realization is chosen).

**A-VC-3 (immutable anchor-input manifest and duplicate-row consistency).**
`vk0c_input_manifest.json` binds by SHA-256: the V-K0B
`renewal_check_trace.jsonl`, `renewal_counterfactual_units.jsonl`,
`train_and_checkpoint_manifest.json`, `summary.json`, the V-K0A panel and
sidecar; plus trace schema vk0-trace-2, check-row count 5,376,
deduplicated anchor count 2,688, the six seeds, 64 episodes per seed, 7
noninitial checks, the six checkpoint/exposure authorizations, resolved
configs, and code/schema identities. Anchor gate: the two focal rows of
one (seed, episode, check) must agree exactly on every shared field
(training seed, episode, check index, order code, checkpoint hash,
config hash, pre-check fingerprint, primitive step, active mask,
current/previous targets, natural five-step reward and both match
vectors) and jointly reconstruct one ordered roster (skills, ages,
focals); any missing row, third duplicate, or disagreement →
`INVALID_VK0C_ORDER_TRANSPORT_AUDIT / ANCHOR_INVENTORY_INCONSISTENT`,
never row selection.

**A-VC-4 (explicit initial and inter-check propagation semantics).**
Propagation begins at `check_index=0, active_mask=[False,False], no
incumbents, ages=[0,0]` under the no-incumbent semantics. Inter-check
transition frozen: KEEP → same skill, age+5; SET(z) → skill z, age 0 at
the edit, 5 at the next check; active True after a legal token; check+1.
Gate B compares the pure transition against an executed one-window
agent/env transition over the complete set of canonical transition cases
(the factual-row reproduction remains the assembled-path check, not the
sole transition test).

**A-VC-5 (four-sign descriptive panel).** A separate non-inferential
propagation table over slow×fast signs ∈ {−1,+1}², both orders, fresh and
trained, all eight checks — never pooled with, substituted for, or used
to rebalance the 64-episode bank.

**A-VC-6 (complete propagation outputs).** Per order × policy state ×
seed × episode, row-level evidence sufficient to reconstruct: occupancy of
every reachable canonical state; expected slow match, fast match and
external reward at every primitive step; expected episode return;
expected KEEP/SET rate; expected per-agent renewal rate; expected realized
lifetime distribution (or sufficient run-length mass). The V-K0A window
evaluator is the deterministic reward kernel.

**A-VC-7 (dtype-derived mass rule; one canonical distribution).** Raw
token masses in the policy probability dtype; joint products accumulated
in float64; `raw_joint_mass` recorded; `mass_tolerance = 32 ×
eps(policy_probability_dtype)`; validity requires all masses finite,
nonnegative, same-label SET mass exactly 0, |raw_joint_mass − 1| ≤
tolerance (failure = invalidity). After passing, exactly one canonical
normalized vector p̂ drives TV, marginals, task consequences, occupancy
propagation and every factor calculation; raw masses and the
normalization correction are both recorded. The 1e-9 rule and
"renormalized only for reporting" are withdrawn.

**A-VC-8 (pooled plus stratified outputs).** Every matched-state quantity
(at least TV, D_R fresh, D_R trained, A_R, optimal-assignment mass,
slow/fast coverage-failure masses) is reported pooled AND per occupancy
stratum (CANONICAL_OCCUPANCY / REVERSED_OCCUPANCY). Order stays a kernel
argument, never folded into the physical state.

**A-VC-9 (stratum-safe Factor D).** The pure occupancy-mediation label
requires trained matched-state equivalence within ±0.5 in the pooled AND
both stratum views while the exact propagation reproduces the material
competence split; pooled equivalence produced by opposite material
stratum-level direct effects records the stratum effects and leaves pure
occupancy mediation unresolved.

**A-VC-10 (durable analyzer authorization; full distribution rows).**
`vk0c_matched_state_rows.jsonl` preserves all 16 common-coordinate
outcomes per (policy, anchor, order) with: physical-agent final skill
pair, first token, second conditional token, raw token masses, raw joint
mass, canonical joint probability, KEEP/SET marginals, five-step reward,
slow/fast match vectors, task-optimal and coverage-failure flags. The
analyzer consumes the three JSONL row files plus
`vk0c_input_manifest.json`; missing or mismatched authorization fires
precedence-1 invalidity.

**A-VC-11 (fresh-init hash scope, from VC-D5's clarification).** The
construction hash covers the high policy state_dict, every
decision-context module reachable under the resolved configuration,
relevant buffers, and the resolved configuration identity.

## Deliberately not done

No successor-route implementation (order randomization, equivariant
controller — the ruling's conditional table only); no V-K1 work; no new
seeds or banks; no change to V-K0B artifacts; no analytic shortcut where
the ruling requires executed replay (the positive control and factual-row
reproduction step real envs).
