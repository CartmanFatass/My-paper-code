# S3 Agent-Local Controlled Predictive State Derivation

Date: 2026-07-24

```text
action_id=S3_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_DERIVATION
scientific_source=docs/research/cdc/EVIDENCE_NOTES/20260724_ALPSC_S2_RESULT_AND_ALCPS_S3_DIRECTION.md
code_executed=false
compute_executed=false
formal_run=false
```

## Result

`PASS_ALCPS_CONTROLLED_STATE_DERIVATION`

On the frozen finite anonymous-membership source, the full externally indexed primitive-action intervention vector identifies exactly two controlled decoder-equivalence classes. The C-ALCPS cue writer attains the controlled Bayes floor with two learned state installations per seven active rows. Every controlled-sufficient online model must change decoder-equivalence class on both post-join regime changes, so its learned-write rate is at least `2/7`; equality places writes exactly on the two cue rows, up to null events and latent relabeling. Merging decoder-equivalent subdivisions leaves exactly two states and removes the iid nuisance bit.

This establishes a canonical active-step controlled-state lifetime on this source. It does not establish that the state is a learned skill, that recurrence is insufficient, or that C-ALCPS improves optimization, utility, sample efficiency, robustness or held-out transport.

## 1. Exact source and online order

Each lifecycle independently samples `B∈{0,1}` and script `S∈{23,32}`, uniformly and independently. Its seven active rows are:

| Script | `R_0..R_6` | Cue rows | Complete lifetimes |
|---|---|---|---|
| `23` | `B,B,1-B,1-B,1-B,B,B` | `0,2,5` | `2,3` |
| `32` | `B,B,B,1-B,1-B,B,B` | `0,3,5` | `3,2` |

The three lifecycle epochs and membership rows are unchanged from S1/S2: 21 active rows total, one temporary leave/rejoin, one fresh genuine join and terminal leaves. Temporary absence emits no objective row, advances neither active index nor segment age, and freezes lifecycle state and RNG. Routing keys never enter the filtration.

Add `N_n∈{0,1}`, iid Bernoulli one-half and independent of `B,S,R`, membership, intervention query and target. At active index `n`, the writer observes `O_n=(C_n,X_n,N_n)`, where `X_n=R_n` on a cue and `⊥` otherwise.

The online order is:

1. establish active membership and current observation;
2. structurally initialize on genuine join or apply the existing-row writer;
3. expose the installed controlled state to the decoder;
4. evaluate both external intervention queries;
5. emit the controlled target;
6. record audit-only boundary and membership consequences.

Structural join sets `z=B` from the current cue without a learned installation. Terminal leave right-censors the final segment and deletes state after evidence is recorded.

## 2. Controlled potential-outcome table

At every legal active history, the external query has complete support `u∈{0,1}`. It is enumerated independently of `h,z`, history, identity and the natural policy; it is not persistent and is not visible to the writer.

The target law is `P(Y=1|R,u)=3/4` when `u=R` and `1/4` otherwise:

| Regime `R` | Query `u=0` | Query `u=1` | Controlled vector `(K^0(1),K^1(1))` |
|---:|---:|---:|---|
| 0 | `3/4` | `1/4` | `(3/4,1/4)` |
| 1 | `1/4` | `3/4` | `(1/4,3/4)` |

For either fixed query, total variation between the two Bernoulli regime kernels is `|3/4-1/4|=1/2`. Uniform query marginalization gives

`P(Y=1|R)=1/2*(3/4)+1/2*(1/4)=1/2`

for both regimes. Thus the action marginal has zero regime separation, while the complete controlled vector has exact separation. Query labels are current intervention indices, not temporal memory.

The conditional entropy at either correct regime/query pair is

`H=-(3/4)ln(3/4)-(1/4)ln(1/4)=ln 4-(3/4)ln 3`.

This is the exact controlled Bayes floor `L_star`.

## 3. Filtration and scientific state

Each lifecycle owns:

- unrestricted fast recurrent primitive-control state `h`, excluded from the controlled predictive channel;
- finite controlled predictive state `z`;
- learned state-installation indicator `w`;
- a segment, defined as a maximal active-step run in one decoder-equivalence class.

At an active existing row, the writer may use only current `O_n`, previous `z_n-` and fresh registered writer randomness. It receives no `h`, active age/index, local or global clock, `t mod k`, observation history outside `z`, natural action, query history, active-set or membership history, auxiliary persistence, identity/role, reward/task/goal/success/progress, future observation or oracle boundary.

The controlled decoder is `p_eta(Y_n|z_n+,u)` and receives exactly installed `z` and current external `u`. It receives no natural action, observation/cue, `h`, clock, history, nuisance or membership information.

For a legal history `f`, write `K_f^u(y)=P(Y=y|f,do(u))`. A state is controlled-sufficient iff its decoder reproduces this law for every legal history, both queries and both target values. Two latent values are decoder-equivalent iff their complete vectors `(K^0,K^1)` agree. State cardinality `K` is counted only after merging equivalent values.

## 4. Lexicographic criterion

Define

`L_ctrl(M)=mean_{active histories,u} E[-ln p_M(Y|z,u)]`,

`E_ctrl(M)=L_ctrl(M)-L_star`,

`q(M)=mean_active E[w_n]`,

and `K(M)` as the number of decoder-distinct controlled kernels after quotienting.

Order models lexicographically by `(E_ctrl,q,K)`. Strict propriety of log score gives

`E_ctrl = mean KL(K_f^u || p_M(.|z(f),u)) >= 0`.

Therefore exact controlled sufficiency is the first non-negotiable coordinate. Positive predictive excess cannot be traded for fewer writes. Among sufficient models, minimize learned installations; only then minimize decoder-distinct cardinality.

## 5. Constructive C-ALCPS candidate

The candidate:

1. structurally installs `z=B` at genuine join;
2. on an existing-row cue, installs `z←X_n=R_n`;
3. otherwise preserves `z`;
4. ignores nuisance `N`;
5. decodes the table in Section 2 from `(z,u)`.

Before every decode, `z=R`. Hence

`E_ctrl=0`, `q=2/7`, `K=2`.

The learned writes are exactly the two post-join regime changes for either script. Boundary precision and recall are one. Script `23` has complete active-step lifetimes `2,3`; script `32` has `3,2`. The two controlled states are unique only up to `0↔1` with the matching kernel relabeling.

## 6. Minimum-write and quotient theorem

### Proposition

Every online model with `E_ctrl=0` has `q≥2/7`. Equality is possible only when learned installations occur exactly on the two post-join cue rows, up to null events and latent relabeling. After decoder-equivalent latent values are merged, every equality model has `K=2`.

### Proof

Because expected predictive excess is an average of nonnegative KL divergences, `E_ctrl=0` implies zero KL at every positive-probability legal history and query. The installed decoder class must therefore expose the exact controlled vector for the current regime.

The vectors `(3/4,1/4)` and `(1/4,3/4)` are distinct. Consequently every sufficient installed state distinguishes `R=0` from `R=1` almost surely.

At structural join, `z` is initialized to the class for `B`. In script `23`, the current regime first changes at active age 2; in script `32`, it first changes at age 3. Both scripts change back at age 5. Immediately before each change row, the installed class represents the old regime. The current cue is the first online information revealing the new regime. Exact prediction on that same row requires the post-update state to belong to the other decoder-equivalence class. Thus a learned installation is necessary at each of the two actual post-join changes.

There are seven active rows per lifecycle, so `q≥2/7`. The candidate attains equality. If an equality model installed at any other row with positive probability, it would exceed two expected installations because both change-row installations remain mandatory. Hence equality places its only learned installations on the two actual cue rows almost surely.

Every sufficient model contains at least the two distinct regime kernels. Any additional latent distinctions with the same controlled vector are decoder-equivalent and merge. Therefore the quotient of every equality model has exactly `K=2`. The nuisance `N` changes neither controlled vector and cannot survive this quotient. QED.

## 7. Complete registered null coverage

### 7.1 Never-write and always-write

`NEVER_WRITE_AFTER_JOIN` keeps `z=B`. Conditional on `z`, the current regime equals `z` on `9/14` source rows and differs on `5/14`. Its optimal controlled decoder therefore uses probabilities `4/7` and `3/7` across the two queries, giving

`L_NW=h(4/7)=ln 7-(4/7)ln 4-(3/7)ln 3 > H`.

Thus `E_ctrl>0`; zero writes cannot outrank a sufficient model lexicographically.

`ALWAYS_WRITE` can remain sufficient but installs on all six post-join rows, so `q=6/7>2/7`.

### 7.2 All 64 deterministic fixed-age masks

Each mask is a subset `A⊆{1,2,3,4,5,6}`. If age 2 is absent, script `23` cannot change class before decoding its first changed row. If age 3 is absent, script `32` cannot do so. If age 5 is absent, neither script can represent the final change. Hence every sufficient fixed-age mask must contain `{2,3,5}`.

Exactly the eight supersets of `{2,3,5}` can be made sufficient by using the current cue at scheduled rows, but every such mask has at least three scheduled installations and therefore `q≥3/7`. The other 56 masks have `E_ctrl>0`. This partitions all `2^6=64` masks and none matches `(0,2/7,2)`.

### 7.3 Periodic phases

Every deterministic finite-horizon period/phase schedule induces one of the 64 age subsets. It is therefore either insufficient or contains `{2,3,5}` and has `q≥3/7`. No periodic phase supplies a missing source-adaptive write.

### 7.4 Current-membership-event mappings

Current membership categories are ordinary, rejoin and terminal leave. They are independent of `B,S` and do not mark both internal regime changes for every lifecycle. The genuine join is structural. A rule writing only on membership events therefore misses at least one mandatory decoder-class transition and has positive `E_ctrl`; adding ordinary rows becomes a non-adaptive schedule and cannot beat the source-adaptive two-cue candidate.

### 7.5 Post-hoc segmentation

A segmenter using a future cue, later target or completed trajectory violates the online order and is inadmissible. If restricted to the registered online filtration, it is covered by the minimum-write theorem and must install on both current cue rows.

### 7.6 Stochastic writers and mixtures

For any stochastic model, predictive excess is still an expectation of nonnegative KL terms. Zero expected excess forces exact controlled prediction almost surely at every positive-probability history/query. Each stochastic realization must therefore cross decoder class at both actual changes. Averaging cannot reduce `q` below `2/7`; equality leaves no positive-probability extra installation. A mixture containing an insufficient component has positive excess and loses at the first coordinate.

### 7.7 Nuisance-only tracking

A state that tracks only iid `N` has the same nuisance distribution under both regimes and cannot identify the distinct controlled vectors. A sufficient model may redundantly encode `N`, but its nuisance subdivisions have identical controlled kernels and merge, so they cannot increase `K` or define a lifetime.

## 8. Action-information counterexamples

### ACTION_MARGINAL_NULL

Omitting `u` after uniform marginalization yields `P(Y=1|R)=1/2` for both regimes. The coarsest predictive quotient has one kernel and no nontrivial controlled state. This valid negative control proves that action conditioning is load-bearing.

### NATURAL_ACTION_QUERY

If a policy with access to fast `h` selects the only observed action, the action label can reveal `R` to the decoder. Such a label is a temporal action-as-memory channel, lacks external complete support and is not admissible controlled evidence. It cannot substitute for the independently enumerated `u`.

### Identical-kernel negative source

If both regime controlled vectors are replaced by the same vector, the quotient has `K=1`, exact prediction requires no regime state and the correct result is no nontrivial lifetime. The criterion therefore does not manufacture a segment when controlled consequences are absent.

## 9. Constructive external-control check

Audit-only utility is `1[A=R]` and enters no writer input, loss, target, decoder or boundary decision.

- C-ALCPS chooses `A=z`; because `z=R`, `U_star_ALCPS=1`.
- G8 stores the current cue regime in lifecycle recurrence `h`, freezes it during absence and chooses `A=h`; `U_star_G8=1`.

G8 remains the complete external-policy comparator and strongest simpler explanation. The derivation establishes no recurrent representational impossibility or behavioral advantage.

## 10. Invariance audit

1. Lifecycle-key relabeling only renames iid product factors. Mismatch: 0.
2. Active-member permutation reorders independent per-lifecycle factors. Mismatch: 0.
3. Inactive padding contributes no active transition, query, target, write or objective row. Mismatch: 0.
4. Temporary-absence insertion freezes state, segment age and RNG and leaves the seven active rows unchanged. Mismatch: 0.
5. Swapping controlled query labels together with the corresponding kernel columns preserves the full vector and all conclusions. Mismatch: 0.
6. Swapping latent labels `0↔1` with their decoder kernels preserves predictions, writes, boundaries, lifetimes and utility. Mismatch: 0.

No reward, identity, role, goal, success, progress, future input, natural-action memory, clock, active-set history or auxiliary persistence enters the controlled state channel.

## 11. First-match terminal

1. `INVALID_ALCPS_DERIVATION_CONTRACT`: not triggered. Source arithmetic, online order, membership semantics, target law, null coverage and invariances are exact; no forbidden field enters.
2. `ACTION_QUERY_OR_TEMPORAL_SIDE_CHANNEL_LEAK`: not triggered. Both queries have complete external support, carry no memory and are absent from the writer; natural-action query is rejected as a counterexample.
3. `CONTROLLED_SOURCE_NON_IDENTIFIABLE`: not triggered. Each fixed-query regime separation is `1/2`, action-marginal separation is zero as required, and the candidate attains `L_star`.
4. `NO_UNIQUE_MINIMAL_CONTROLLED_LIFETIME`: not triggered. Every sufficient model has `q≥2/7`; equality writes only on the two actual cue rows, nuisance subdivisions merge and every registered null is worse.
5. `PASS_ALCPS_CONTROLLED_STATE_DERIVATION`: triggered.

```text
first_match_terminal=PASS_ALCPS_CONTROLLED_STATE_DERIVATION
source_contract_valid=true
query_support_complete=true
query_memory_leak=false
controlled_kernel_tv_each_query=1/2
action_marginal_tv=0
candidate_E_ctrl=0
candidate_q=2/7
candidate_K=2
minimum_sufficient_q=2/7
equality_schedule=two_post_join_cue_rows_only
nuisance_quotient_removed=true
boundary_precision=1
boundary_recall=1
complete_lifetimes={2,3}
U_star_ALCPS=1
U_star_G8=1
registered_mismatch=0
conclusion_bearing_iterations_consumed=3
iterations_remaining=7
```

## 12. Consequence boundary

Supported: the frozen finite source admits an exactly identifiable coarsest minimum-transition controlled predictive state with nontrivial active-step lifetimes `{2,3}`.

Not supported: learned-skill semantics, C-ALCPS necessity, recurrence insufficiency, optimization or sample-efficiency benefit, causal primitive-action mediation beyond the constructed audit, natural held-out value, robustness, transport or final-algorithm integration.

No code, implementation plan, prototype, compute, experiment or Monitor action occurred. Iteration 3 is consumed. This exact result must return to the same registered GPT-5.6 Pro conversation before iteration 4 is selected.
