# V-K0C realization — Project Manager decision ledger

Status: **complete code design for touchpoint 2 conformance** (workflow 7).
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

## Deliberately not done

No successor-route implementation (order randomization, equivariant
controller — the ruling's conditional table only); no V-K1 work; no new
seeds or banks; no change to V-K0B artifacts; no analytic shortcut where
the ruling requires executed replay (the positive control and factual-row
reproduction step real envs).
