# ALPSW S1 Result and Exclusive Slow-Channel S2 Direction

Date accepted: 2026-07-24

## Provenance

- External scientific authority: GPT-5.6 Pro.
- Review round: `docs/external-review/rounds/20260724_alpsw_s1_result_review/`.
- Stage commit: `a373d6becd08067d866d9a64252d4a163bde4fdb`.
- Evidence commit: `b0a5c6b4c32121228c6449cd140b756ae9a17173`.
- Question body SHA-256: `f3f3f4becb248fef67ab935025b53de6990c2928208da2a087d8d271ffdd58a6`.
- Immutable raw SHA-256: `b4e9693092dd78c5292268465df07d12b48865855c67638e4963047fea69ba06`.
- Controller reconciliation: `30_EVIDENCE_RECONCILIATION.md`.

## Accepted S1 terminal

```text
action_id=S1_ALPSW_IDENTIFIABILITY_DERIVATION
contract_valid=true
accepted_terminal=NO_ONLINE_IDENTIFIABLE_SLOW_STATE
terminal_affecting_defects=none
algorithm_code_executed=false
compute_executed=false
conclusion_bearing_iterations_consumed=1
iterations_remaining=9
```

The exact C-ALPSW formulation is closed before implementation. Predictive NLL plus a cost only on slow-state writes cannot identify causal memory ownership when an unrestricted, unpenalized fast recurrence reads the same online history and is visible to the predictive decoder.

For the exact S1 source, a one-bit cue-updated recurrence achieves the entropy lower bound `H=ln 4-(3/4)ln 3` with zero learned writes. Across the full parameter class `Delta_ID(beta)=0` for nonnegative beta; for the intended two-write restriction it is `-(2/7)beta<0` for positive beta. At beta zero the owner is non-unique and negative beta favors always-write. The required open interval is empty.

The Pro audit accepts every terminal-bearing part of the finite source, filtration, NLL arithmetic, null optima, recurrent-absorption theorem, constructive ALPSW/G8 controls, invariances and iteration accounting. It notes only that the artifact's explicitly memoryless, non-gating `H+(5/28)ln 3` reference value must not be generalized to every unrestricted h-free decoder when direct current-cue use is allowed. The artifact already excludes that value from the registered optimum; no repair or branch change follows.

Smallest supported propositions:

- A finite legal-history recurrence or predictive sufficient statistic can absorb the registered slow state and attain no greater predictive NLL.
- A write-only complexity penalty cannot identify ownership while another unpenalized decoder-visible temporal channel carries the same information.

Smallest refuted proposition:

- The exact C-ALPSW objective uniquely identifies a sparse lifecycle-owned slow state despite the unrestricted alternative fast temporal channel.

Not refuted: predictive state, sparse online segmentation, continuous lifecycle state, variable individual lifetime, causal action mediation under a corrected contract, optimization/sample-efficiency benefit or held-out transport beyond G8.

All R42--R48 closure and quarantine scopes remain unchanged.

## New candidate C-ALPSC

C-ALPSC is an agent-local predictive slow channel with exclusive temporal ownership. It is a new scientific contract, not a repair or revival of C-ALPSW.

Each lifecycle owns:

- `h`: unrestricted fast recurrent primitive-control state;
- `z`: bounded slow predictive state and the sole cross-active-step memory of the slow self-supervised channel;
- `w`: learned slow-channel write indicator;
- evidence-only active-step age, which is not an S2 writer or decoder input.

The writer may use only current task-blind local observation, previous `z` and fresh writer randomness. It may not use `h`, age, active-step index, global time, `t mod k`, observation history except through `z`, current/past primitive actions, active-set or roster history, membership-event type as a predictive feature, auxiliary persistent writer state, identity, role, goal, reward, success, progress or oracle boundary.

Structural join initializes `z` separately. On an active existing row, the Bernoulli writer may install a candidate or preserve `z`. The slow decoder is exactly `p_eta(Y | z+)`; it receives no current observation/cue, `h`, age, clock, action, active-set summary, membership history or auxiliary memory. The current cue affects prediction only through an installed slow-state write.

The primitive-control path may still consume current observation, `h`, `stopgrad(z)`, active mask and G8 context. Primitive reward gradients never enter the S2 writer/decoder. S2 trains or evaluates no controller.

The claim ceiling is internal identifiability of a sparse predictive slow channel under an explicit exclusive information partition. S2 cannot establish utility, optimization, sample efficiency, natural policy use, causal action mediation, held-out transport, semantic skill, superiority over G8 or necessity of explicit slow state.

## Selected S2 action

```text
action_id=S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION
action_class=accepted_evidence_reanalysis_plus_exact_derivation
conclusion_bearing_iteration=2
code_required=false
compute_required=false
prototype_required=false
formal_run_required=false
Monitor_required=false
evidence_artifact=docs/research/cdc/EVIDENCE_NOTES/20260724_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_S2.md
```

### Immutable source and objective

Reuse the exact S1 `B,S` laws, scripts, three-lifecycle membership table, 21 active rows, cue/target laws, structural join, utility, lifetimes and invariance transforms.

`J_beta^SC(M) = mean_active E[-ln p_eta(Y_n | z_n+)] + beta * mean_active E[w_n]`.

`Delta_SC(beta)` is the best admissible structural-null objective minus the best C-ALPSC objective.

The frozen interval is exactly `0 < beta < (1/2)ln 3`.

### Admissible nulls

Evaluate all of:

1. always-write;
2. never-write-after-join;
3. every one of the `2^6` deterministic post-join fixed-age subsets;
4. every deterministic periodic schedule and phase representable in the seven-active-row horizon;
5. every deterministic mapping from current membership event to write/no-write, with no membership history;
6. post-hoc noncausal segmentation, which cannot install online state;
7. every stochastic mixture of those deterministic policies, discharged by exact convexity/extreme-point proof or enumeration.

### Mandatory forbidden-leak counterexamples

- FAST_H_LEAK: one cue-updated recurrent bit gives zero writes and NLL `H`.
- AUXILIARY_RNN_LEAK: one undeclared persistent bit restores recurrence absorption.
- AGE_CLOCK_LEAK: age or equivalent time plus cue pattern reconstructs schedule with zero writes.
- ACTION_LEAK: an action chosen from fast memory transfers the bit into the decoder.
- DIRECT_CUE_DECODER_LEAK: direct cue access permits a delayed fixed-age writer at active ages 3 and 6 to match predictive NLL while breaking boundary ownership.
- ACTIVE_SET_TIME_LEAK: deterministic roster/membership history that reveals local/global time is a clock leak.

These are load-bearing counterexamples to exclusivity and are not admissible C-ALPSC models.

### PASS obligations

Across every beta in the frozen interval, the cue writer must uniquely write on the two post-join cue rows, achieve NLL `H`, write rate `2/7`, objective `H+(2/7)beta`, and have `Delta_SC(beta)>0` against every admissible null. Uniqueness is only up to latent `0↔1`.

The proof must exhaust fixed-age subsets, periodic phases, membership mappings and candidate-state maps; handle stochastic policies exactly; retain boundary precision/recall 1, complete lifetimes `{2,3}`, `U_star_ALPSC=U_star_G8=1`; prove zero lifecycle-key, active-order, padding, absence-insertion and latent-relabeling mismatch; reproduce every leak; and contain no forbidden information.

### First-match terminals

1. `INVALID_ALPSC_DERIVATION_CONTRACT`: incorrect arithmetic/order, forbidden information, incomplete enumeration, invalid membership semantics or failed invariance.
2. `SIDE_CHANNEL_OWNERSHIP_LEAK`: any supposedly admissible path carries temporal information outside `z`.
3. `NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`: contract valid but interval empty, cue writer not unique or any admissible null has `Delta_SC<=0` anywhere in the interval.
4. `PASS_ALPSC_IDENTIFIABILITY_DERIVATION`: every exact obligation passes.

Stop on the first valid terminal. A valid result consumes iteration 2; an invalid derivation permits only one transcription/arithmetic/proof correction under the identical contract. Iterations 3--10 remain unselected.

## Portfolio boundary

- C-ALPSW: closed exact formulation, no local rescue.
- C-ALPSC: live and selected for S2 derivation.
- C-JRDM: parked pending a representation-invariant joint codelength or information cost for `h,z`.
- C-ALH: parked; S1 does not rescue categorical hazards.
- C-ATS: parked; recurrence absorption strengthens its existing threshold-free-lifetime objection.
- C-SEPM: parked pending an identified complementary-allocation source.
- G8/C-OPEN-ROSTER-DIRECT: accepted base and complete external-policy comparator.
- C-REC: mandatory simpler explanation and exact S1 absorption witness, not an admission gate.

No experiment row belongs in `ExpRecord.md`. The accepted action authorizes no algorithm code, implementation plan, prototype, compute, Monitor, G8 modification, capacity change, complexity penalty, beta sweep, new source or successor beyond S2.
