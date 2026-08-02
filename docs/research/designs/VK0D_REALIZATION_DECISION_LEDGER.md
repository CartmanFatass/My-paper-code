# V-K0D realization — Project Manager decision ledger

Status: **complete code design for touchpoint 2 conformance** (workflow 8).
The scientific comparison is FROZEN by the ruling of round
`20260802_vk0c_order_transport_result` (§SUCCESSOR_DIRECTION): three arms —
permutation-equivariant/order-symmetrized carrier (PRIMARY),
order-randomized current R30 (mandatory simpler control), canonical-only
current R30 (reference) — matched on information, KEEP/SET support,
model/optimizer exposure, environment interactions, training seeds,
evaluation bank, and both serialization tests, with the ruled four-branch
interpretation grid and the exact order-conjugacy assertion gate before any
conclusion-bearing training. This ledger records only the realization
bindings. Nothing here moves a threshold, floor, seed or predicate.

## VD-1 — PRIMARY arm: relative-role (self/other) context, AR loop retained

The equivariant carrier is the existing `FixedClockAREditPolicy` with ONE
structural change: the decision context is re-encoded by **relative role
instead of absolute identity**. `encode_working_roster` currently writes
every other agent's skill/age at `identity_offset + agent_id*n_skills`
(absolute physical index, r30_fixed_clock.py:136-138) — the sole
identity-indexed surface (the scout's map; heads are already shared, no
positional feature exists). The conjugate encoding writes the focal
agent's own features in the self block and the other agent's features in
the other block, with no absolute index anywhere in the context. For
n_agents=2 this is information-lossless (every roster fact remains
readable), so "retains state information" holds exactly.

Consequence, by construction: the policy cannot read which physical agent
it is, so the joint token distribution under order [0,1] is the exact
agent-swap conjugate of the joint under [1,0] — P01(z0,z1|x) =
P10(z1,z0|swap(x)) — while the autoregressive conditional structure
(second mover sees the first mover's realized token through
`advance_working_state`) is retained, as is the fixed clock, the KEEP/SET
support, and the fixed executor, exactly per the ruling's retention
column. The inference-time both-orders averaging wrapper is NOT the
carrier (the ruling demotes it to a diagnostic) and is not built.

Scope note (disclosed): relative-role encoding is complete for n=2; the
variable-N generalization (pooled/attention aggregation of "others") is a
successor design question, not part of V-K0D.

## VD-2 — token_mass contract preserved verbatim

The change is context construction only. `token_mass`,
`advance_working_state`, `act_sequence`, `evaluate_sequence`,
`EditSequenceSample`, and the KEEP/SET factorization semantics (A-VC-1)
are unchanged in signature and meaning for all three arms. Therefore the
V-K0C conjugacy machinery (`enumerate_order`, `run_forced_window`, the
prescribed-assignment control) runs against the PRIMARY arm unchanged —
the coupled boundary A↔D in the scout's map is held fixed.

## VD-3 — dedicated RNG stream for the randomized-order arm

The per-check order draw consumes a dedicated
`numpy.random.Generator(Philox)` seeded from
`(training_seed, "vk0d-order-1")`, threaded from `train.py` into the
`maybe_assign_skills` call sites as an explicit `agent_order` tensor. The
global torch stream is never touched by order draws, so every model-init,
`Categorical.sample()` and `torch.rand_like` draw keeps its exact position
across arms: identical seeds ⇒ identical non-order randomness, only
serialization varies. (Today no stream owns an order draw — training order
is compile-time ascending; this creates the stream rather than reusing
one.)

## VD-4 — draw granularity: per check

The randomized arm draws uniformly over the two orders independently at
every renewal check (not per episode). The specialization mechanism
V-K0C identified operates per check token-factorization; per-check
randomization removes any persistent first/second position within and
across episodes. Recorded as a PM binding for conformance review.

## VD-5 — pre-training order-conjugacy assertion gate (new driver mode)

New `scripts/assert_vk0d_order_conjugacy.py`: constructs a FRESH agent of
the arm's resolved config (`build_fresh_agent`-style, seed-pinned, no
checkpoint), manufactures anchor states independently of any V-K0B
artifact by rolling natural from-reset episodes with the fresh policy
across all four sign pairs plus zero-action clock states, and asserts at
every panel state:

1. exact 16-outcome enumeration under both orders via `token_mass`
   (float64 joint accumulation, one canonical p̂ per A-VC-7 rules), with
   `P01(z0,z1|x) == P10(z1,z0|swap(x))` bit-exact in the policy dtype;
2. the executed prescribed-assignment control (`run_forced_window`
   semantics: force both agents, roll exactly 5 steps, compare
   physical-agent skills, primitive actions, reward and match vectors,
   post-window state) equal across orders.

PASS is a hard precondition for launching conclusion-bearing training of
the PRIMARY arm; the gate also runs (and is expected to FAIL) against the
canonical-only reference as its paired negative — a conjugacy gate that
cannot go red is not a gate. Gate output is a JSON witness with the
config hash, seeds, panel inventory and per-state verdicts.

## VD-6 — arm identity in the frozen chain

Three resolved configs, three identities:

- PRIMARY: new config module `config_d7_2b_toy_conjugate_keep` with
  `high_controller = "r30_fixed_clock_ar_edit_conjugate"`; the
  controller string is added to `StandaloneProcessAgent`'s validation
  set and construction branch (scout region 4; class reuses
  `FixedClockAREditPolicy` with the conjugate context flag).
- CONTROL: existing controller with new config field
  `r30_training_order_policy = "uniform_per_check"`.
- REFERENCE: existing controller with
  `r30_training_order_policy = "canonical"` (explicit, so the field is
  present in all three resolved configs).

The field and the controller string enter `_config_only_fields` and
therefore `resolved_config_hash`; every row and checkpoint carries its
arm identity mechanically. The launcher grows one `--arm` selector that
maps to exactly these three config identities and nothing else.

## VD-7 — matched exposure kept exact-count

The PRIMARY arm changes context encoding only and the CONTROL arm changes
order only: neither changes the count structure (same AR loop, same
tokens per check, same env interactions). `validate_identical_contract_
identities` therefore keeps its exact-count definition, applied per arm
with identical numbers (640,000 interactions, 1,000 updates, the six
scientific seeds, token-count identities). Any arm whose realized counts
deviate fails the launcher preflight — matched exposure is enforced, not
assumed.

## Training and evaluation scale (informational)

Per arm: the six frozen seeds × 640k steps (the V-K0B contract), then the
frozen 64-episode/seed evaluation bank with the 32/32 canonical/reversed
order split and the V-K0B floors (support 192/192, competence LCB95 >
0.75 under BOTH order views). The V-K0D verdict applies the ruling's
four-branch grid to the CONTROL and PRIMARY competence outcomes;
"passes" for an arm = the V-K0B competence screen passed under both
orders. The full V-K0B access screen (opportunity access, sampled-SET
competence, alignment quantities) reruns for the surviving arm in a
LATER workflow before any V-K1 comparison — not part of V-K0D.

## Frozen amendments from the conformance ruling (round 20260802_vk0d_design_conformance, CHANGES_REQUIRED)

**A-VD-1 (anonymous-OTHER encoding; no populated SELF block).** The
PRIMARY encoder change is identity-removal ONLY. Frozen encoding:
invariant skill-count block unchanged; a relative OTHER skill block (the
sole other agent's current skill, existing count scale) and a relative
OTHER age block (existing age transform); SELF blocks zero — focal skill
and age already enter `_hidden` separately, and duplicating them would be
an unmatched second intervention; absolute physical-ID information
absent; `ar_prefix_dim`, input-layer shape and parameter count unchanged.
Wording corrected: the encoder is NOT "information-lossless" — it
deliberately deletes the absolute agent-label shortcut while preserving
all anonymous task and roster information; that deletion is the
treatment.

**A-VD-2 (structural identity and its limits).** The PRIMARY retains the
AR conditional structure. Its gate certifies permutation conjugacy —
P01(a0,a1|x) = P10(a1,a0|swap(x)) with swap over every physical-agent-
indexed component — NOT same-state serialization invariance
P01(a0,a1|x) = P10(a0,a1|x), which need not hold while the second mover
conditions on the first mover's realized edit. The ledger claims neither
same-state invariance nor a preordained both-order competence pass.

**A-VD-3 (PRIMARY trains canonical).** The causal decomposition requires:
PRIMARY = anonymous relative roster + canonical serialization; CONTROL =
current absolute-ID roster + uniform per check; REFERENCE = current
roster + canonical. Frozen identities:
PRIMARY `high_controller=r30_fixed_clock_ar_edit_conjugate`,
`r30_training_order_policy=canonical`; CONTROL
`r30_fixed_clock_ar_edit` + `uniform_per_check`; REFERENCE
`r30_fixed_clock_ar_edit` + `canonical`. The launcher rejects every other
combination in a scientific V-K0D run.

**A-VD-4 (order-draw contract and durable exposure).** One order
assignment per COMPLETED high-check autoregressive sequence (including
the initial assignment sequence; excluding non-due calls,
continuation-value calls, and aborted calls emitting no decision row);
the draw occurs only after the due decision is established and before
token generation; the chosen order is stored in the committed high-check
row and reused by PPO sequence evaluation. Assignment is counter-based
from the immutable decision identity (training seed, environment id,
episode id, check index, stream version `vk0d-order-1`) so batching or
call-order changes cannot move assignments. Durable per-seed/arm
exposure: stream identity/version, completed canonical and reversed
sequence counts, each agent's first-position count, a schedule digest
over ordered high-check identities and assigned orders, and the
completed-sequence total; the ordered schedule is independently
regenerated from the frozen identity and compared exactly with the
committed rows. Identities: N01+N10 = N_sequences; canonical arms have
N10=0. Wording corrected: the dedicated stream gives RNG-stream
isolation only — reversing the order deliberately maps later draws to
different conditional decisions; no cross-arm trajectory identity is
claimed.

**A-VD-5 (complete finite conjugacy panel; deliberate negative;
post-training recheck).** The gate population is the complete finite
support, not natural fresh-policy states: INITIAL class (check 0, active
[False,False], no incumbents, ages [0,0], all four sign pairs) plus
ACTIVE classes (checks 1..7 × all four sign pairs × all 16 physical
joint-skill pairs × every reachable age pair at that check, active
[True,True]), both order views. swap(x) is defined explicitly over
observations, skill array, age array, active mask, and any agent-indexed
auxiliary context; anonymous global target state unchanged. The PRIMARY
must satisfy the registered conjugacy equality on the complete panel AND
pass the executed prescribed-assignment control. Paired negative: a
deliberate witness restoring the absolute-ID encoder with the identity
blocks made deterministically consequential — the gate must reject it;
the canonical reference's observed red is supplementary, never the sole
sensitivity proof. The same conjugacy gate reruns on EVERY trained
PRIMARY checkpoint before its competence result is read.

**A-VD-6 (matched model and optimizer opportunity).** Before launch,
freeze and verify per seed across all three arms: identical high-policy
state_dict keys and tensor shapes, input dimension, hidden widths,
parameter count, high-value architecture, fixed low executor, optimizer
class/hyperparameters, optimizer parameter membership, initial
actor/value parameter bytes, and initial optimizer state — the PRIMARY
context flag must create no parameter or initialization-order change, so
same-seed initial trainable module hashes are identical across arms. The
only pre-training differences: PRIMARY's anonymous-encoding flag,
CONTROL's order schedule, REFERENCE neither. All actual exposure records
(interaction, update, sequence, token, order-exposure, optimizer-step,
parameter-coverage) pass independently per arm.

**A-VD-7 (reference no-op reproduction gate).** REFERENCE_CONFORMS only
if, per seed: initialization model+optimizer digests match the valid
V-K0B reference; the canonical path consumes no order-stream draw; final
actor/value and optimizer-state digests reproduce the valid V-K0B bundle
(or a pre-frozen equivalence rule holds — file-level equality not
required when only non-model provenance fields change); exact training
exposure matches; and the frozen evaluation reproduces canonical
competence above 0.75 and reversed decisively below. Otherwise
`INVALID_VK0D_CARRIER_COMPARISON / CANONICAL_REFERENCE_NOT_REPRODUCED` —
not evidence for or against either correction.

**A-VD-8 (arm status vocabulary and comparison precedence).** Per arm,
over each required slow/fast × order quantity: QUALIFIED (every required
LCB95 > 0.75); DECISIVE_COMPETENCE_FAILURE (any required UCB95 ≤ 0.75,
equality decisive under the frozen inclusive upper-bound rule);
COMPETENCE_UNRESOLVED (neither); SUPPORT_INSUFFICIENT (any frozen
support floor fails); INVALID (provenance, exposure, replay, gate,
reference, checkpoint, or schema validity fails). Comparison precedence:
(1) shared invalidity → `INVALID_VK0D_CARRIER_COMPARISON`; (2) reference
not reproduced → same; (3) any conclusion-bearing arm support
insufficient → `VK0D_SUPPORT_INSUFFICIENT`; (4) CONTROL QUALIFIED →
`ORDER_RANDOMIZATION_COMPETENCE_QUALIFIED` (retain the simpler
correction; PRIMARY still reported); (5) CONTROL DECISIVE_FAILURE and
PRIMARY QUALIFIED → `STRUCTURAL_REPRESENTATION_CORRECTION_REQUIRED`;
(6) both DECISIVE_FAILURE → `AUTOREGRESSIVE_CARRIER_REOPENED`; (7) every
other valid combination → `VK0D_SUCCESSOR_COMPARISON_UNRESOLVED`.
CONTROL-unresolved + PRIMARY-qualified does NOT establish the structural
correction; CONTROL-qualified with PRIMARY unresolved/failed retains the
simpler correction provided the PRIMARY defect does not contaminate the
shared shell. If both qualify, the portfolio rule selects the simpler
order-randomized R30 (VD-1 supplies no independently identified
variable-N benefit).

## Deliberately not done

No inference-time order-ensemble arm (diagnostic only, per the ruling);
no variable-N aggregation design; no V-K1 work; no changes to V-K0B/V-K0C
artifacts or to the frozen evaluation bank; no new seeds; no touch of the
D7.S/B3-L line (HELD). V-K0D uses only the competence and support screen;
the full V-K0B access screen reruns for the selected candidate in a later
workflow before V-K1.
