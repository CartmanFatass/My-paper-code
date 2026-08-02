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

## Deliberately not done

No inference-time order-ensemble arm (diagnostic only, per the ruling);
no variable-N aggregation design; no V-K1 work; no changes to V-K0B/V-K0C
artifacts or to the frozen evaluation bank; no new seeds; no touch of the
D7.S/B3-L line (HELD).
