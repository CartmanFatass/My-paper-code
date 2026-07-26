# External Pro open question: G38 code-science alignment

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=3b13ce0c6936fc5209e9ff7928aaaae61ec7200b
implementation_code_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
index=docs/research/designs/CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_INDEX.md
frozen_contract=docs/external-review/rounds/20260726_continuous_roster_six_coordinate_cs_g38_design_assertion_audit/21_PRO_OPEN_RAW.md
nonformal_compute_started=false
formal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`. Inspect
the exact pushed audit target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. The index is navigation, not a substitute for
reading the named implementation.

Question: does PM's accepted implementation instantiate the exact common
ten-coordinate FULL10/FOLD6 no-carry training graph, active-only constant-input
treatment, genuinely six-wide FOLD6 source boundary, byte-identical paired
initialization, live removable-column gradients, exact two-bias fold into a
true six-coordinate actor, evidence-bearing one-trajectory fold equivalence,
paired G32/G34 exposure, access and FULL10-minus-FOLD6 estimands, whole-episode
confidence plan and first-match semantics frozen in the G38 design audit,
without another route to either conclusion-bearing branch?

Check only these conformance points:

1. Before folding, both arms use one serialized ten-coordinate graph and equal
   key set, shapes, trainable mask, parameter count and initial bytes. The only
   raw actor-observation consumers are `member_input: Linear(10,32)` and
   `current_readout: Linear(10,2)`. No normalization, gate, residual, context,
   action head, critic, baseline, routing, prefix or credit path independently
   reads the raw observation. Both arms carry zero learned hidden state.
2. FULL10 receives the exact registered active ten coordinates. Every FOLD6
   training, replay, gradient, PPO and evaluation actor boundary constructs,
   passes and stores only source coordinates `0:6`; its model rejects ten-wide
   input. The constant `(1/2,1/2,1/2,24/47)` is written only into active rows
   after that boundary and inactive rows remain zero. Real age, previous action
   and actor time cannot be materialized, stored or inspected by FOLD6; the
   critic retains its unchanged true state.
3. Both ten-coordinate matrices remain fully trainable. On the forced first
   paired batch, every inherited trainable group and each removable column
   `6:10` of both affines has finite live fast or RTG gradient strictly above
   `1e-12` before an optimizer step. Paired initialization on the same clamped
   tensor and noise closes the frozen `1e-7` gate.
4. Folding uses the pre-fold removable weights for both bias additions, retains
   both affine column ranges `0:6`, copies all other actor, critic, credit,
   buffer and log-standard-deviation tensors unchanged, deletes exactly 136
   actor weights and performs no optimizer step afterward. The deployment
   checkpoint accepts only six coordinates and retains no filler or proxy path.
5. Every conclusion-bearing FOLD6 zero/final cell compares pre-fold and folded
   actors on the same states/noise while advancing exactly one environment
   trajectory. The gate actually measures both immediate rewards, full reward
   traces and recomputed utility/event-window/segment summaries, validates each
   membership edit against the registered schedule, and applies the exact
   bitwise/tolerance rules to values, means, actions, prefixes, likelihoods,
   inactive zeros, roster and lifecycle. No constant telemetry field may stand
   in for a measured predicate.
6. Fresh FULL10/FOLD6 training uses exact G32 capacity-8 fixed ledgers, shared
   episode/action streams, separate empty Adam state, collection of both mates
   before either update, 100 fast plus 100 RTG updates, eight environments,
   two PPO passes and final-only checkpoints per arm/replicate. The exact seed
   bases, nonformal offset and paired exposure/optimizer inventories bind.
7. Evaluation retains the exact G34-P0 fixed/random capacity-6/8/12 source and
   exactly five registered cells per arm/replicate/capacity. Only the folded
   six-coordinate checkpoints are deployed for FOLD6; the pre-fold path exists
   solely inside the one-trajectory audit. Source, reward, action distribution,
   lifecycle, 48-step traces and zero evaluation optimizer steps fail closed.
8. One bootstrap plan with the frozen seed resamples paired replicate blocks
   and whole episode IDs, retains every arm/checkpoint/process/action-mode mate,
   weights capacities equally and is reused for absolute and paired estimands.
   Access, confident failure, component noninferiority, primary
   `FULL10-FOLD6`, strict/inclusive `0.05` semantics and branch order are exact.
9. Invalid, source/common-access failure, six-coordinate architectural
   reduction sufficient, full-information finite-budget advantage and mixed/
   underpowered branches stop in exact priority. A positive reduction claim is
   limited to the exact freshly trained folded actor; a negative branch is only
   finite-budget advantage for the four-field bundle. Diagnostics cannot rescue
   or relabel either result.
10. Complexity is `H=48`, `K_search=0`, zero hypothetical transitions,
    26,880/1,013,760 nonformal/formal real transitions, 120/3,600 optimizer
    steps, 30/90 cells, 250/10,000 bootstrap resamples and no nested rollout or
    replanning. Formal admission requires the exact G38 token, same-source
    `ALIGNED` audit and all three bounded-preflight artifact digests plus the
    frozen wall-clock projection.

A positive result can support only the exact freshly trained folded
six-coordinate deployment actor under G38-P0. It cannot support native-six-input
training equivalence, task-level or global history redundancy, individual-field
redundancy, critic-time redundancy, recurrence necessity, another constant or
transport outside the registered source. A negative result can support only a
finite-budget capability or material utility advantage for varying access to
the four-field bundle; it cannot establish task-level history necessity or
separate semantic information from optimization conditioning.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the exact target instantiates the frozen
  contract and no indexed test/probe can pass through a result-changing wrong
  mechanism.
- `AUDIT_DISPOSITION=MISMATCH` only with the exact frozen assertion and exact
  conflicting code path or behavior, plus the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one previously unstated
  result-changing scientific choice that prevents conformance judgment.

Do not introduce or request a new algorithm, controller, solver, source,
threshold, evidence volume, experiment or formal run. Do not accept or redesign
PM's code. Stop after the single scoped disposition.
