# V-K0D realization design conformance check

Touchpoint 2 of workflow 8. One question: **does the completed code design
in `docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md` conform to
the successor comparison you froze in round
`20260802_vk0c_order_transport_result` (§SUCCESSOR_DIRECTION)?** Zero
experiments have run in this workflow. Discarding this question's structure
is a legitimate answer.

## Variable-k relevance

V-K0D builds and gates the order-robust carrier that your ruling made the
precondition for every further variable-k step: without an
order-conjugate carrier passing the V-K0B competence screen under both
serializations, V-K1 and all downstream variable-k comparisons stay
blocked.

## Frozen inputs (not review surface)

Your three-arm table (equivariant/order-symmetrized PRIMARY;
order-randomized R30 mandatory control; canonical-only R30 reference),
the matching requirements (information, KEEP/SET support, model/optimizer
exposure, environment interactions, seeds, evaluation bank, both
serialization tests), the four-branch interpretation grid, the
pre-training exact order-conjugacy assertion requirement, the V-K0B
floors and bank, and the rule that the full access screen reruns before
V-K1.

## Code facts (scout-mapped, PM spot-checked at this stage_commit)

The high policy's only identity-indexed surface is the roster context:
`encode_working_roster` writes other agents' skill/age at
`identity_offset + agent_id*n_skills` (r30_fixed_clock.py:136-138) while
also already accumulating a permutation-invariant count term; the
skill/keep heads and input MLP are single shared modules called per agent
— there is no per-agent parameter bank and no explicit position feature.
Order reaches the network only through the autoregressive working-state
mutation (the second mover reads the first mover's realized token).
Training-time order is compile-time ascending: `maybe_assign_skills`'s
`agent_order` defaults to `None` = arange, and no training path passes it;
no RNG stream currently owns an order draw. The V-K0C conjugacy machinery
(`enumerate_order`, `run_forced_window`) binds by name to
`agent.high.token_mass(...)` and to the `forced_tokens`/`agent_order`
contract; `build_fresh_agent` constructs a checkpoint-free agent from a
config module and seed. The launcher pins exact-count exposure identities
per run and derives `resolved_config_hash` from `high_controller` among
other fields.

## The design, in one paragraph (full detail in the ledger)

VD-1 realizes the PRIMARY arm as the existing AR policy with the context
re-encoded by relative role (self/other) instead of absolute identity —
information-lossless at n=2, giving exact order conjugacy by construction
(P01(z0,z1|x) = P10(z1,z0|swap(x))) while retaining the fixed clock,
KEEP/SET support, autoregressive conditional structure and fixed
executor; the inference-time both-orders averaging wrapper is not built
(your ruling demotes it to a diagnostic). VD-2 preserves the `token_mass`
contract verbatim for all arms, so the V-K0C conjugacy machinery runs
unchanged. VD-3/VD-4 realize the randomized arm with a dedicated
Philox stream keyed (training_seed, "vk0d-order-1") drawing uniformly
per check — the torch stream is untouched, so identical seeds give
identical non-order randomness across arms. VD-5 adds a pre-training
conjugacy gate driver: fresh agent, anchors manufactured from-reset
independent of V-K0B artifacts across all four sign pairs, bit-exact
16-outcome conjugacy plus the executed prescribed-assignment control;
PASS gates conclusion-bearing training of the PRIMARY arm, and the gate
must go red on the canonical-only reference (its paired negative). VD-6
gives the three arms three resolved-config identities (new controller
string for PRIMARY; explicit `r30_training_order_policy` field for
control/reference) entering `resolved_config_hash`. VD-7 keeps matched
exposure as the existing exact-count identities applied per arm
(neither arm changes count structure).

## Points where the design interprets the ruling (flagged)

1. **"Permutation-equivariant or order-symmetrized"** is realized as
   relative-role context encoding with the AR loop retained — structural
   conjugacy rather than a non-autoregressive joint head or an averaging
   wrapper. If your ruling instead requires deleting the autoregressive
   conditional structure itself, the design needs your correction.
2. **Per-check draw granularity** for the randomized arm (VD-4) — your
   ruling says "randomized training serialization" without granularity;
   per-check was bound as the strongest removal of persistent position.
3. **"Passes both orders"** in the interpretation grid is realized as the
   V-K0B competence screen (support 192/192, LCB95 > 0.75 under both
   order views on the frozen bank); the full access screen is deferred to
   a later workflow per your gate. If "passes" means more than competence
   at this stage, the design needs your correction.

## Required response sections

1. `CONFORMANCE` — CONFORMS, or the exact ledger items that deviate.
2. `INTERPRETATIONS` — accept/correct the three flagged readings.
3. `CONVERGENCE_DECISION` — your closing decision for this touchpoint.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md`
- `docs/external-review/rounds/20260802_vk0c_order_transport_result/21_PRO_OPEN_RAW.md`
- `ha_ctse_process/r30_fixed_clock.py`
- `ha_ctse_process/standalone_agent.py`
- `scripts/audit_vk0c_order_transport.py`
- `scripts/run_vk0b_training.py`
