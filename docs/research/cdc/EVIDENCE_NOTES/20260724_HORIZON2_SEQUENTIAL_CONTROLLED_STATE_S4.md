# S4 Horizon-2 Sequential Controlled-State Derivation

Date: 2026-07-24

```text
action_id=S4_HORIZON2_SEQUENTIAL_CONTROLLED_STATE_DERIVATION
scientific_source=docs/research/cdc/EVIDENCE_NOTES/20260724_ALCPS_S3_RESULT_AND_ALSCPS_S4_DIRECTION.md
code_executed=false
compute_executed=false
formal_run=false
```

## Result

`PASS_ALSCPS_FUTURE_CLOSED_DERIVATION`

On the frozen finite anonymous-membership source, every immediate controlled branch observation is regime-uninformative, but every complete two-microstep open-loop plan produces regime-separated joint sequence kernels. The coarsest horizon-2 quotient has two decoder classes, is update-congruent under one online function and has minimum sufficient learned-installation rate `2/7`. Equality installs only at the two actual post-join regime changes, giving complete active-step lifetimes `{2,3}`.

This PASS establishes exact horizon-2 sequential controlled-state and active-lifetime identifiability on one finite source. It establishes neither arbitrary-horizon sufficiency nor learned recovery, skill semantics, recurrence insufficiency, optimization, mediation, natural value, robustness, transport or final integration.

## 1. Frozen lifecycle source

Each lifecycle independently samples uniform `B∈{0,1}` and uniform script `S∈{23,32}`. Its seven active rows are:

| Script | `R_0..R_6` | Cue rows | Complete lifetimes |
|---|---|---|---|
| `23` | `B,B,1-B,1-B,1-B,B,B` | `0,2,5` | `2,3` |
| `32` | `B,B,B,1-B,1-B,B,B` | `0,3,5` | `3,2` |

The exact three-lifecycle membership table remains 21 active rows with one temporary leave/rejoin, one fresh genuine join and terminal leaves. Absence emits no active transition, advances neither active age nor segment age, and freezes lifecycle state and RNG. Routing keys do not enter the scientific filtration.

The iid nuisance bit `N_n` is Bernoulli one-half and independent of `B,S,R`, membership, plans and branch outcomes. The writer sees `O_n=(C_n,X_n,N_n)`.

At an active existing row, the writer may use only current `O_n`, previous `z` and fresh registered writer randomness. It receives no `h`, clock/index, `t mod k`, observation history outside `z`, natural action, plan history, active-set/membership history, auxiliary persistence, identity/role, reward/task/goal/success/progress, branch outcome, future observation or oracle boundary.

Structural join sets `z=B` without a learned installation. Temporary absence freezes state. Terminal leave right-censors and deletes after evidence capture.

## 2. External plan and branch semantics

At every legal active history, enumerate all four open-loop plans

`a=(u_0,u_1)∈{00,01,10,11}`.

A plan is externally indexed, independent of `h,z`, history, identity and natural policy, absent from writer input, branch-local, visible only to the sequential decoder and supported completely at every history. The plan and branch do not mutate the natural lifecycle, membership, writer, segment age or natural RNG.

Emit

`Y^(1) ~ Bernoulli(1/2)`

independently of regime, plan, nuisance and membership. Conditional on regime and plan, emit

`P(Y^(2)=1|R,a)=3/4` if `u_0 XOR u_1=R`, and `1/4` otherwise.

The branch observations are conditionally independent given regime and plan.

## 3. Exact two-microstep potential-outcome table

Let `v=u_0 XOR u_1`. For plans `00,11`, `v=0`; for plans `01,10`, `v=1`.

| Plan | Parity `v` | `p_0=P(Y2=1|R=0,a)` | `p_1=P(Y2=1|R=1,a)` |
|---|---:|---:|---:|
| `00` | 0 | `3/4` | `1/4` |
| `01` | 1 | `1/4` | `3/4` |
| `10` | 1 | `1/4` | `3/4` |
| `11` | 0 | `3/4` | `1/4` |

For a matching regime/plan parity, the joint probabilities ordered as `(Y1,Y2)=(0,0),(0,1),(1,0),(1,1)` are

`(1/8,3/8,1/8,3/8)`.

For the other regime they are

`(3/8,1/8,3/8,1/8)`.

The one-step projection is always fair:

`P(Y1=1|R,a)=1/2`.

Thus `one_step_TV=0` for every plan and the coarsest immediate quotient has `K_1=1`.

For every full plan, total variation between the two joint distributions is

`1/2 * [4*(|3/8-1/8|)] = 1/2`.

Equivalently, the common fair first factor leaves the delayed Bernoulli TV `|3/4-1/4|=1/2` unchanged. Hence `horizon2_TV=1/2` for all four plans.

The exact sequence entropy at the correct regime is

`L_2_star=H(Y1)+H(Y2|R,a)=ln2+H`,

where `H=ln4-(3/4)ln3`.

## 4. Sequential quotient and update congruence

The decoder is `p_eta(Y1,Y2|z,a)` and receives exactly installed `z` plus the current external plan. It receives no current observation/cue, `h`, nuisance, clock, natural action, branch future, membership history or auxiliary state.

Two latent values are sequentially decoder-equivalent iff their complete joint sequence kernels agree for all four plans. `K_2` counts only distinct equivalence classes.

An admissible quotient must also be recursively updateable from its own class and the legal current writer observation. Define

`F(class(z_n-),O_n) -> class(z_n+)`.

The candidate uses:

- if `C_n=1`, `F(z,O_n)=X_n`;
- otherwise, `F(z,O_n)=z`.

For any two legal histories in the same regime class and the same current observation, this rule returns the same next regime class. It depends on no hidden representative or older history. Therefore update-congruence mismatch is zero.

## 5. Sequential lexicographic criterion

Define sequence risk averaged over active histories and all four plans:

`L_2(M)=E[-ln p_M(Y1,Y2|z,a)]`.

Let `E_2=L_2-L_2_star`, `q=mean_active E[w_n]`, and `K_2` be quotient cardinality. Order models lexicographically by `(E_2,q,K_2)`.

Strict propriety gives

`E_2 = mean KL(P_f^a(Y1,Y2) || p_M(.|z(f),a)) >= 0`.

Positive sequence excess cannot be exchanged for fewer writes. Only exactly horizon-2-sufficient models compete on installation rate; only equal-rate models compete on quotient size.

## 6. Constructive C-ALSCPS

The candidate structurally installs `z=B`, writes `z←X_n=R_n` on each post-join cue, preserves otherwise, ignores `N`, and decodes the exact table in Section 3 from `(z,a)`.

Before each branch decode, `z=R`, so

`E_2=0`, `q=2/7`, `K_2=2`.

Update-congruence mismatch is zero. Learned writes coincide with both actual post-join regime changes, so boundary precision/recall are one. Complete active-step lifetimes are `{2,3}`. Latent labels are unique only up to relabeling.

## 7. Minimum-transition future-closed theorem

### Proposition

Every online model with `E_2=0` has `q>=2/7`. Equality installs only at the two actual post-join cue rows, up to null events and latent relabeling. After quotienting sequence-equivalent values, every equality model has `K_2=2`.

### Proof

`E_2=0` is an average of nonnegative KL divergences and forces exact joint sequence prediction for every positive-probability history and plan, almost surely over writer randomness.

For each plan, the two regime sequence kernels have TV `1/2`. A sufficient installed class must therefore distinguish `R=0` and `R=1`. Structural join supplies the initial class for `B`. Script `23` changes regime at active ages 2 and 5; script `32` changes at ages 3 and 5. On each change row, the pre-update class is the old regime and the current cue is the first legal observation of the new one. Exact same-row sequence prediction requires transition to the new sequence-kernel class before decoding. Both changes therefore require learned installations.

Two required installations over seven active rows give `q>=2/7`; the candidate attains equality. Any additional positive-probability installation would raise `q`, so equality writes only at the actual changes.

Every sufficient model contains at least the two distinct regime sequence kernels. Any additional values with identical complete four-plan kernels merge. Therefore the quotient of an equality model has `K_2=2`. Since `N` changes no sequence kernel, nuisance subdivisions merge. QED.

## 8. Complete null coverage

### 8.1 One-step controlled quotient

Using only `Y1` gives one fair kernel, so `K_1=1`. A one-class decoder must average the delayed regime kernels and cannot reproduce both horizon-2 tables. Therefore `E_2>0`. This is the exact one-step-myopia counterexample.

### 8.2 Never-write and always-write

Never-write keeps structural `z=B`. Current regime equals `z` on `9/14` source rows. When plan parity equals `z`, its fitted delayed probability is

`(9/14)(3/4)+(5/14)(1/4)=4/7`;

for the opposite parity it is `3/7`. The fair first observation contributes `ln2`, so

`L_2_NW=ln2+h(4/7)`

and `E_2_NW=h(4/7)-H>0`.

Always-write may be sufficient but has `q=6/7`.

### 8.3 All 64 fixed-age masks and periodic phases

A deterministic age mask omitting age 2 fails script `23` on its first changed row; omitting age 3 fails script `32`; omitting age 5 fails both. Thus any sufficient mask contains `{2,3,5}`. Exactly eight masks are supersets of this set, each with `q>=3/7`; the other 56 have positive sequence excess.

Every finite-horizon period/phase schedule induces one of these age subsets and is covered by the same partition.

### 8.4 All current-membership mappings

The eight binary mappings over ordinary, rejoin and terminal-leave events are independent of `B,S`. If ordinary rows do not write, internal regime changes are missed. If ordinary rows write, the rate exceeds `2/7`. No membership-only mapping matches the source-adaptive two-cue schedule.

### 8.5 Post-hoc segmentation

Future branch outcomes cannot alter an already installed state or earlier sequence prediction. Providing either branch outcome before the current installation violates the online order. Restricting to the legal filtration returns to the minimum-transition theorem.

### 8.6 Stochastic writers and mixtures

Zero expected sequence excess forces zero KL almost surely at every positive-probability history/plan. Each realization must distinguish regimes and install at both actual changes. Mixtures cannot average away mandatory class transitions; equality permits no extra positive-probability write.

### 8.7 Nuisance-only state

The iid nuisance changes no horizon-2 kernel. Nuisance-only state cannot distinguish regimes, while redundant nuisance subdivisions of a sufficient state are sequence-equivalent and merge.

### 8.8 Identical-sequence-kernel negative source

If both regimes receive identical complete horizon-2 kernels, the coarsest quotient has `K_2=1`, exact prediction needs `q=0`, and no nontrivial lifetime appears. The criterion does not manufacture persistence without delayed controlled consequences.

## 9. Leak and adaptive-plan audits

A length-two plan selected by a policy with fast recurrent memory can encode hidden regime information and lacks external complete support. It is an invalid natural-plan-as-memory channel.

Giving `Y1` or `Y2` to the writer before current installation is a future-outcome leak and invalidates online lifetime evidence.

The four open-loop plans are the conclusion-bearing support. For the adaptive audit, let the second action be any deterministic function of first action and `Y1`. Because `Y1` is fair and independent of regime, the induced plan-selection weights are regime-independent. Conditional on each realized `Y1`, the chosen parity still gives delayed probabilities `3/4` versus `1/4` across regimes. The joint adaptive branch therefore retains TV `1/2`; it neither makes the immediate projection informative nor eliminates the registered horizon-2 distinction.

## 10. Constructive control and invariances

Audit utility is `1[A=R]` and enters no sequential-state supervision.

- C-ALSCPS chooses `A=z` and attains `U_star_ALSCPS=1`.
- G8 stores `R` in lifecycle recurrence `h`, freezes it during absence, chooses `A=h` and attains `U_star_G8=1`.

G8 remains the strongest simpler explanation and complete external-policy comparator.

Mismatch is zero under lifecycle-key relabeling, active-member permutation, inactive padding, temporary-absence insertion, arbitrary permutation of the four plan labels with corresponding kernel columns, latent-state relabeling and nuisance-bit relabeling. No reward, task field, identity, role, goal, success, progress, natural-action memory, clock, branch future or auxiliary persistence enters the admissible channel.

## 11. First-match terminal

1. `INVALID_ALSCPS_DERIVATION_CONTRACT`: not triggered. Source, target table, entropy, online order, null coverage, membership and invariances are exact.
2. `ACTION_PLAN_OR_FUTURE_INFORMATION_LEAK`: not triggered. Plans have complete external memory-free support and are absent from the writer; natural-plan and future-outcome paths are rejected.
3. `NO_HORIZON_SEPARATING_CONTROLLED_SOURCE`: not triggered. The immediate projection has `TV=0,K_1=1`; every full plan has horizon-2 TV `1/2`; the candidate reaches `ln2+H`.
4. `NO_UNIQUE_MINIMAL_FUTURE_CLOSED_LIFETIME`: not triggered. The quotient is update-congruent, every sufficient model has `q>=2/7`, equality writes only at actual cues, nuisance merges and every registered null is worse.
5. `PASS_ALSCPS_FUTURE_CLOSED_DERIVATION`: triggered.

```text
first_match_terminal=PASS_ALSCPS_FUTURE_CLOSED_DERIVATION
source_contract_valid=true
plan_support_complete=true
plan_memory_leak=false
future_outcome_leak=false
one_step_tv=0
one_step_K=1
horizon2_tv_each_plan=1/2
L_2_star=ln2+H
candidate_E_2=0
candidate_q=2/7
candidate_K_2=2
minimum_sufficient_q=2/7
equality_schedule=two_post_join_cue_rows_only
update_congruence_mismatch=0
nuisance_quotient_removed=true
boundary_precision=1
boundary_recall=1
complete_lifetimes={2,3}
U_star_ALSCPS=1
U_star_G8=1
registered_mismatch=0
conclusion_bearing_iterations_consumed=4
iterations_remaining=6
```

## 12. Consequence boundary

Supported: the frozen source admits an exactly identifiable, update-congruent horizon-2 controlled predictive quotient with one unique minimum-transition active-step lifetime.

Refuted: equality of immediate controlled observations is sufficient to identify all delayed controlled regimes; and a predictive partition without update congruence is automatically a lifecycle state.

Not supported: arbitrary-horizon closure, learned-state recovery, skill semantics, recurrence insufficiency, optimization/sample-efficiency benefit, primitive-policy mediation, natural value, robustness, transfer or final integration.

No code, implementation plan, prototype, compute, experiment or Monitor action occurred. Iteration 4 is consumed; six remain. This result must return to the same registered Pro conversation before iteration 5 is selected.
