# ALPSC S2 Result and ALCPS S3 Direction

Date accepted: 2026-07-24

```text
scientific_source=external_GPT_5_6_Pro
evidence_commit=60cd2d68a54e4c86f5bc0084ff627c779f1c7cb4
review_stage_commit=bcbf74d2598af034b728b586d641dfce67bcbc9d
review_round=docs/external-review/rounds/20260724_alpsc_s2_result_review
review_raw_sha256=065dcf47e8536bcb6fb20c54c7197e9df960506954249a53cb0d97aa7aaa87e5
accepted_s2_terminal=NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL
selected_action=S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION
code_authorized=false
compute_authorized=false
```

## S2 accepted terminal

External GPT-5.6 Pro accepted S2 as a valid conclusion-bearing negative with no terminal-affecting defect. The exact C-ALPSC contract is closed before implementation:

- exclusive `z`-only slow predictive channel;
- optimized predictive decoder;
- predictive-NLL/write-rate scalarization;
- complete interval `0<beta<(1/2)ln 3`.

The cue writer remains the unique zero-predictive-excess two-write schedule up to `0↔1`. It has `L=H=ln 4-(3/4)ln 3`, `q=2/7`, exact boundary precision/recall one and complete active-step lifetimes `{2,3}`.

The admissible `NEVER_WRITE_AFTER_JOIN` null preserves structural `z=B`, performs no learned write and fits the exact softened decoder

`P(Y=z|z)=4/7`,

so

`L_NW=ln 7-(4/7)ln 4-(3/7)ln 3`.

It ties the cue writer at

`beta_star=(7/2)ln 7-(11/2)ln 4+(9/8)ln 3`,

where `0<beta_star<(1/2)ln 3`, and is strictly better above the crossing. The null contains no alternative temporal channel. Complete deterministic-map, periodic, membership-only, post-hoc and stochastic-mixture coverage therefore establishes the first valid terminal `NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`.

Smallest supported proposition: excluding alternative temporal channels is necessary for ownership identification but does not remove the predictive-accuracy/write-rate tradeoff induced by an optimized coarser decoder.

Smallest refuted proposition: exclusive slow-channel ownership makes the cue writer globally unique throughout the complete frozen S2 interval.

The result does not reject controlled predictive states, exclusive channels, sparse segmentation, variable individual lifetime, optimization benefit, causal mediation or held-out transport generally. R42–R48 remain unchanged. Iteration 2 is consumed; eight remain.

## Selected S3 direction

The sole selected successor is:

```text
action_id=S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION
candidate=C_ALCPS
action_class=exact_derivation_and_counterexample
conclusion_bearing_iteration=3
code_required=false
compute_required=false
prototype_required=false
experiment_required=false
Monitor_required=false
```

C-ALCPS abandons fixed-beta scalarization. It asks whether a task-blind, action-interventional minimal-sufficiency criterion identifies one nontrivial agent-local active-step lifetime while rejecting action-marginal non-identification, temporal side channels, nuisance tracking and non-unique state-transition schedules.

## Frozen finite source

Reuse the S1/S2 lifecycle source without changing `B`, scripts `23/32`, regime sequences, cue rows, complete lifetimes `{2,3}`, 21 active rows, three lifecycle epochs, temporary leave/rejoin, genuine join, terminal leave, structural join initialization or registered invariances.

Add an iid nuisance bit `N_n∈{0,1}` with probability `1/2`, independent of `B,S,R`, membership, intervention query and target. The writer observation is `O_n=(C_n,X_n,N_n)`.

At every active legal history, enumerate an external query `u∈{0,1}`. It is not sampled by the natural policy, not chosen from `h,z`, history or identity, not persistent, not visible to the writer and supplied only to the current controlled decoder. The target law is

`P(Y=1|R,u)=3/4` if `u=R`, and `1/4` otherwise.

For each fixed `u`, the two regime kernels have total-variation distance `1/2`. Uniformly marginalizing and omitting `u` gives `P(Y=1|R)=1/2` for both regimes. The complete controlled vector contains regime information; the action marginal does not.

## State, lifetime and filtration

Each lifecycle owns unrestricted primitive-control recurrence `h`, controlled predictive state `z`, learned installation indicator `w`, and a segment defined as the maximal active-step run in one decoder-equivalence class.

Structural join initializes `z` from the current cue and is not a learned transition. Temporary absence freezes ownership and segment age. Terminal leave right-censors and deletes the state after evidence capture. Lifetime is the number of active primitive steps between decoder-equivalence-class changes, never wall time or global `k`.

At an active existing row, the writer may use only current `O_n`, previous `z` and fresh registered writer randomness. It may not use `h`, any clock/index, observation history outside `z`, natural actions, query history, membership history, auxiliary persistence, identity/role, reward/task/goal/success/progress, future input or oracle boundaries.

The decoder is `p_eta(Y_n|z_n+,u)` and receives only installed `z` plus current external query `u`. Both query actions are evaluated at every legal history. A natural-policy action stream is insufficient controlled evidence.

## Estimand and candidate

For each legal history `f`, define `K_f^u(y)=P(Y=y|f,do(u))`. Sufficiency requires the decoder conditioned on `z(f)` to match this law for every history, query and target. Decoder-equivalent latent subdivisions are merged according to the complete vector `(K^0,K^1)`.

Order models lexicographically by:

1. controlled predictive excess `E_ctrl=L_ctrl-L_star`, where `L_star=H=ln 4-(3/4)ln 3`;
2. learned-write rate `q=mean_active E[w_n]`;
3. number `K` of distinct controlled decoder kernels after merging equivalent latent values.

Exact controlled sufficiency is non-negotiable. Only then minimize writes and decoder-state cardinality.

The candidate structurally installs `z=B`, writes `z←X_n` on each post-join cue, preserves otherwise, ignores `N` and decodes from `(z,u)`. Required values are `E_ctrl=0`, `q=2/7`, `K=2`, boundary precision/recall one and lifetimes `{2,3}`. The two states are unique only up to relabeling.

## Mandatory nulls and controls

Cover never-write, always-write, all 64 deterministic fixed-age masks, all finite-horizon periodic phases, all current-membership-event maps, post-hoc segmentation, stochastic mixtures and nuisance-only state tracking.

`ACTION_MARGINAL_NULL` omits `u` and must produce no nontrivial identified controlled state. `NATURAL_ACTION_QUERY` uses only a policy action selected with access to `h` and must be classified as an invalid action-as-memory channel. A negative source with identical controlled regime kernels must also reject a false lifetime PASS.

G8 remains the complete constructive external-policy comparator. Audit utility is `1[A=R]` and is absent from state supervision. Constructive C-ALCPS chooses `A=z`; constructive G8 stores `R` in `h` and chooses `A=h`; both must attain utility one. This forbids a representational-necessity claim.

Registered invariances require zero mismatch under lifecycle-key relabeling, active-member permutation, inactive padding, temporary-absence insertion, controlled-action label swap with corresponding kernel relabeling and latent `0↔1` relabeling.

## Exact proof obligations and terminals

A valid derivation must establish exact source/query arithmetic, full action-query support, memory-free query indexing, controlled separation `1/2`, action-marginal separation zero, candidate tuple `(0,2/7,2)`, the lower bound `q≥2/7` for every sufficient model, uniqueness of equality writes at the two post-join cues, `K=2` after quotienting, nuisance removal, complete null inferiority, exact boundary/lifetime audit, utility-one constructive policies and all registered invariances. No statistical, mixed or underpowered branch exists.

Apply first-match terminals in this order:

1. `INVALID_ALCPS_DERIVATION_CONTRACT`;
2. `ACTION_QUERY_OR_TEMPORAL_SIDE_CHANNEL_LEAK`;
3. `CONTROLLED_SOURCE_NON_IDENTIFIABLE`;
4. `NO_UNIQUE_MINIMAL_CONTROLLED_LIFETIME`;
5. `PASS_ALCPS_CONTROLLED_STATE_DERIVATION`.

The sole conclusion-bearing artifact is `docs/research/cdc/EVIDENCE_NOTES/20260724_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_S3.md`. A valid PASS or negative consumes iteration 3. One invalid realization permits at most one transcription/arithmetic/proof correction without changing source, intervention table, filtration, nulls, estimand, obligations or terminal order; a second invalid realization blocks.

## Authority ceiling

S3 authorizes no algorithm code, implementation plan, prototype, CPU/GPU action, formal analysis run, experiment, Monitor, G8 modification, reward-based supervision, natural-action query, R42–R48 revival, iteration 4–10 selection or final-algorithm integration. A future PASS would establish only exact controlled-state and active-lifetime identifiability on this frozen finite source. The result must return to the same registered Pro conversation before any implementation or iteration-4 action is selected.
