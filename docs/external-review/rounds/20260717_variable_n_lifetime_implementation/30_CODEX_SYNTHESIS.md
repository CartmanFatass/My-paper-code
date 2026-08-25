# Codex Synthesis — Variable-N + Variable-Lifetime Implementation Plan

## Controller position before convergence

The evidence supports `MODIFY_PLAN`, not `RETURN_TO_ARCHITECTURE` and not
`STOP_AT_F0`. The probability/event decomposition remains coherent, but the
current plan does not yet define an executable boundary between the fixed-N
production stack and the new active-ragged event path.

This synthesis weights claims by repository evidence and causal relevance, not
by reviewer identity. It does not authorize code or training.

## Evidence boundary

- R49 remains interface-only evidence. It establishes permutation-compatible
  active-set encoding, applied-prefix replay and a structural prefix-gradient
  path in an isolated synthetic implementation. It does not establish a
  production event runtime, learnability, utility or a variable-N advantage.
- The current `StrictHMASDMAPPOLowLevelPolicy`, `StandaloneProcessAgent` and
  `train_loop` are fixed-N throughout construction, inference, recurrent replay
  and checkpoint loading.
- The two divergent reviewers independently returned `MODIFY_PLAN` and agreed
  that no forbidden latent, slot, graph, learned scheduler or F1-only module is
  needed to close the identified gaps.

## Agreement and disposition

| Claim | Gemini | Open Pro | Codex disposition |
|---|---|---|---|
| Exogenous gap/order ownership and K-way KEEP/SET probability are coherent | accept | accept | accept |
| Existing fixed-N low-policy surface cannot directly consume flat ragged rows | accept | accept | accept |
| Event mode needs one actor-only recurrent low interface and a separate active-set critic | accept | accept | accept with a narrower implementation below |
| Member-owned `gamma^Delta` and same-owner macro GAE are coherent | accept | accept | accept |
| Existing fixed-N paths must remain isolated | accept | accept | accept |
| Stop after focused engineering evidence, before a real environment or training | accept | accept | accept |
| F1 can collapse to F0 by ignoring or cancelling prefix information | accept | accept | accept |

## Disagreements and controller corrections

### 1. Event low policy is new and trainable, not a frozen legacy wrapper

Gemini proposed either wrapping a frozen
`StrictHMASDMAPPOLowLevelPolicy` or modifying its fixed-N sequence interface.
Neither is the preferred boundary.

The plan's intended meaning was to preserve the low actor *contract and
computation* `pi_low(a_i | o_i, z_i)`, not to force flat rows through the legacy
class. Clarify this by defining one trainable event-mode low policy in
`variable_roster_event.py`:

- one actor parameter set using the same observation base, skill FiLM,
  recurrent core and action distribution semantics;
- actor-only flat-step and lifecycle-chunk replay methods;
- one separate shared active-set critic;
- no legacy fixed critic, team-code input, adapter parameters or copied live
  actor instance;
- no schema-1/2 checkpoint migration.

F0 and F1 share this exact object and state-dict. The original strict class and
its checkpoints stay unchanged.

### 2. Lifecycle ownership must be singular

Open Pro correctly found a contract/plan contradiction: the architecture says
the collector owns the lifecycle table while the plan says the event core owns
one. There must be exactly one authoritative `LifecycleStore` per vectorized
environment.

The corrected boundary is:

- the environment worker owns physical membership facts;
- the collector emits a typed membership transaction;
- the event runtime owns the sole policy-runtime `LifecycleStore` and mutates
  it atomically after validating epochs and the collector snapshots;
- neither the worker nor `StandaloneProcessAgent` keeps a shadow copy of
  skill, hidden, age, gap or open-trace state.

The architecture contract's phrase `collector-owned table` must be replaced by
this exact single-store ownership rule. This preserves the intended routing
boundary without putting policy runtime inside subprocess workers.

### 3. Temporary leave requires a two-snapshot transaction

Accept Open Pro's correction. One collector result must distinguish:

```text
pre_membership_boundary_snapshot
  = post-transition, pre-removal active lifecycles and critic inputs

atomic_membership_delta
  = join / temporary leave / terminal leave / rejoin with epochs

post_membership_pre_policy_snapshot
  = active set used for the new frontier and initial commitment set
```

A temporary leaver's old-policy bootstrap comes only from the first snapshot.
The frontier and `C^(0)` come only from the third. Actual sampled replacement
gaps and frontier order are stored in the event ledger even though neither is a
policy likelihood factor.

### 4. Exact mid-episode resume also requires simulator/collector state

Both written plans list model, optimizer, lifecycle, RNG and open-trace state,
but that is insufficient to reproduce a live run if the simulator and
collector workers restart from different physical states. Schema 3 must add:

- current observation/state boundary;
- collector presentation and pending transaction state;
- environment/worker snapshot and environment RNG state;
- an explicit snapshot capability/version.

Event-mode live resume fails closed when the chosen collector/environment
cannot round-trip these fields. Fresh-reset evaluation remains a separately
declared model-only load. This adds a default-off snapshot interface to
`collectors.py`; a later real testbed must implement it before any training can
be authorized.

### 5. Freeze the critic snapshot for concurrent tokens

Accept Open Pro's proposed rule: every token's stored old value uses that
token's exact pre-token working centralized context. The same critic rule is
used by F0 and F1. Only the actor summary selector differs:

```text
F0 actor summary = initial active commitment set
F1 actor summary = current applied-prefix commitment set
```

Collection and replay must use the same stored source context; no current
roster reconstruction is allowed.

### 6. Equal state dicts do not imply identical realized data

Gemini's claim that the comparison is already fully data-matched is too strong.
Equal graph, initialization, collector contract, reset distribution, exogenous
RNG contract, update budget and replay code are required. Once F0 and F1 sample
different actions, on-policy state visitation may legitimately diverge; forcing
identical realized trajectories would change the estimand.

The plan must replace `same data exposure` with `same data-generation contract
and exposure budget`. At the deterministic engineering trace, both modes use
the same authored source transaction. A later training comparison may pair
external randomness but must treat treatment-induced trajectory divergence as
part of the causal effect, not as an infrastructure confound.

### 7. Structural F1 evidence must be distributional

The current derivative-only check is insufficient. On a concurrent frontier
with common legal support, force an earlier `SET` and compare the later token's
relative logits or normalized probabilities:

- F0 must remain tied to the initial summary;
- F1 must change at least one common-support relative score through the applied
  summary;
- a mask-only change or common additive logit shift is a reduction to F0.

This remains wiring evidence, not usefulness evidence.

### 8. Do not create a second evidence source merely for Git visibility

Open Pro proposed a tracked acceptance-result JSON because the ignored R49 raw
JSON was unavailable through GitHub. The underlying reproducibility concern is
valid, but a second result store conflicts with this repository's ownership
rule: runtime evidence belongs in `logs/`, and tracked tests/contracts own
engineering assertions.

The corrected implementation should keep one focused test file as the durable
executable contract and write any run output under `logs/` with a pointer in
`CURRENT_WORK.md`. Do not commit a duplicate generated acceptance JSON unless
the convergent reviewer identifies a scientific claim that cannot be audited
from the test, code and owning log pointer.

## Exact file and interface consequences

### Design corrections before code

- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`
  - replace ambiguous collector/core dual ownership with one authoritative
    event-runtime lifecycle store and typed collector transactions;
  - add the two-snapshot leave boundary;
  - distinguish shared data-generation contract from realized on-policy data.
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`
  - freeze actor-only event low policy and active-set critic interfaces;
  - freeze normative high-event and ragged-low row/chunk schemas;
  - freeze exact pre-token critic context;
  - add early schema-3 dispatch plus simulator/collector snapshot state;
  - replace the derivative-only F1 check with common-support relative-score
    evidence.

### Production boundary after separate implementation approval

- new `ha_ctse_process/variable_roster_event.py`
  - lifecycle store and typed transactions;
  - F0/F1 shared commitment model and critic;
  - trainable actor-only event low policy and active-set low critic;
  - high-event/ragged-low ledgers, owner returns and strict schema-3 payload.
- `ha_ctse_process/train.py`
  - inspect the checkpoint/mode header before constructing any fixed-N agent;
  - instantiate the event runtime directly for event mode while retaining the
    same outer training entry;
  - use an independent strict schema-3 loader with no legacy fallback.
- `ha_ctse_process/collectors.py`
  - default-off typed two-snapshot membership transaction;
  - snapshot/restore capability used only by event mode.
- `ha_ctse_process/standalone_agent.py`
  - no required event dispatch and no legacy state-dict change; event code may
    import its reusable actor building blocks but may not instantiate the fixed
    policy stack.
- one focused test under `tests/`
  - one deterministic transaction trace covering join, concurrent KEEP/SET,
    temporary leave, rejoin, terminal leave, update truncation, ragged replay,
    strict resume and common-support F0/F1 reduction.

## Proposed implementation order and stop

1. Correct the two design documents.
2. Implement pure lifecycle/probability/ledger/model core with synthetic data.
3. Add early event runtime dispatch and actor-only ragged low path.
4. Add typed collector transactions and strict snapshot-aware schema-3
   round-trip using a synthetic collector snapshot.
5. Run the single focused deterministic transaction test.
6. Stop after engineering evidence. Do not reset a real environment, train,
   benchmark or infer F1 usefulness.

If correctness passes but F1 changes only masks or common additive logits, the
structural hypothesis reduces to F0 and the next disposition is `STOP_AT_F0`.
If correctness requires identity, slots, an F1-only module, learned ordering or
learned event time, stop at F0 rather than stacking mechanisms.
