# S1 ALPSW Identifiability Derivation

Date: 2026-07-24

```text
action_id=S1_ALPSW_IDENTIFIABILITY_DERIVATION
registered_question_stage=7ff4d216e2ce23415c2b3b9ca671c7a76dde7801
registered_evidence_commit=f073d8e77a006515c7800f04e616d5b62a5e4e26
scientific_contract=docs/research/cdc/EVIDENCE_NOTES/20260723_DECOUPLED_SKILL_LIFETIME_DIRECTION.md
code_executed=false
compute_executed=false
formal_run=false
```

## Result

`NO_ONLINE_IDENTIFIABLE_SLOW_STATE`

The C-ALPSW contract makes the predictive decoder conditional on the fast
lifecycle recurrent state `h` and gives no cost, bottleneck or information
restriction that distinguishes memory stored in `h` from memory stored in the
slow state `z`. On every finite source, a no-write model can absorb the finite
slow-state transition into its recurrent state, reproduce the same online
predictive distribution, and pay zero learned-write cost. Therefore no
nonempty write-cost interval can make a nondegenerate sparse writer uniquely
optimal under the registered objective.

The exact finite construction below demonstrates the collision while satisfying
the anonymous runtime-membership, independent-change-point, variable-lifetime
and constructive-policy controls. The following absorption theorem shows that
the collision is not peculiar to this construction.

## 1. Finite anonymous process

### 1.1 Exact source variables

Each lifecycle independently draws at genuine join:

| Variable | Support | Exact law | Meaning |
|---|---:|---:|---|
| `B` | `{0,1}` | `P(B=0)=P(B=1)=1/2` | initial generic binary regime |
| `S` | `{23,32}` | `P(S=23)=P(S=32)=1/2` | independent active-step duration script |

`B` and `S` are independent within and across lifecycles. Routing keys never
enter an observation, model input, action or objective. The script determines
only active-step regime changes:

| Script | Active indices carrying a regime-start cue | Regime on `n=0..6` | Complete segment lengths |
|---|---|---|---|
| `23` | `{0,2,5}` | `(B,B,1-B,1-B,1-B,B,B)` | `2,3` |
| `32` | `{0,3,5}` | `(B,B,B,1-B,1-B,B,B)` | `3,2` |

Index `n=0` is structural join initialization. The later two cue indices are
endogenous-boundary audit rows. The last segment is right-censored at the finite
horizon and is not counted as a complete lifetime.

At each active index `n`, the local online observation is

`O_n = (C_n, X_n)`,

where `C_n=1` exactly on a cue row, `X_n=R_n` on a cue row, and `X_n=⊥` otherwise.
`R_n` is the regime shown in the table. After the online state update, the
generic predictive target `Y_n` is emitted with exact rational law

`P(Y_n=R_n | R_n)=3/4`,  `P(Y_n=1-R_n | R_n)=1/4`.

The prediction is scored before any later observation is available. Emissions
are conditionally independent given the finite regime script. The predictor
never receives external reward, oracle script `S`, oracle regime `R`, routing
key, role, success, progress, future observation or global-cycle phase.

For the constructive external source control only, a primitive action
`A_n ∈ {0,1}` earns utility one exactly when `A_n=R_n`. This utility never enters
the writer objective or writer context.

### 1.2 Complete membership table

Three anonymous lifecycle epochs `ℓ0,ℓ1,ℓ2` are used only as ledger routing
names in this table. Every listed row is exact; `n` is the lifecycle active-step
index before that row.

| Global row `t` | Active lifecycle rows `(ledger key:n)` | Membership operation after the row |
|---:|---|---|
| 0 | `ℓ0:0, ℓ1:0` | none |
| 1 | `ℓ0:1, ℓ1:1` | temporary leave of `ℓ1` |
| 2 | `ℓ0:2` | none |
| 3 | `ℓ0:3, ℓ2:0` | genuine join of fresh `ℓ2` before its row |
| 4 | `ℓ0:4, ℓ1:2, ℓ2:1` | rejoin of `ℓ1` before its row |
| 5 | `ℓ0:5, ℓ1:3, ℓ2:2` | none |
| 6 | `ℓ0:6, ℓ1:4, ℓ2:3` | terminal leave of `ℓ0` after its row |
| 7 | `ℓ1:5, ℓ2:4` | none |
| 8 | `ℓ1:6, ℓ2:5` | terminal leave of `ℓ1` after its row |
| 9 | `ℓ2:6` | terminal leave of `ℓ2` after its row |

Temporary absence emits no active transition, does not advance `n`, does not
advance age, and freezes all lifecycle state and RNG position. Thus `ℓ1`
receives exactly the same seven-row local process as the other lifecycles. The
membership schedule is independent of every `B,S` draw.

### 1.3 Online filtration

For lifecycle `i` at active index `n`, every admissible online model is
measurable with respect to

`F_i,n = σ(O_i,0:n, A_i,0:n-1, anonymous active masks/events through n,
           its own prior recurrent and slow states, past realized writer RNG)`.

`Y_i,n`, future observations, `B_i`, `S_i`, oracle boundaries not yet observed,
external reward and other lifecycles' routing keys are outside `F_i,n` at the
prediction decision. The current cue is inside the filtration; it is a generic
observation, not an oracle training label. The audit table compares cue rows to
oracle changes only after the complete finite process is defined.

## 2. Registered predictive objective

Let

`p_1(y) = 3/4` for `y=1` and `1/4` for `y=0`,

`p_0(y) = 3/4` for `y=0` and `1/4` for `y=1`.

The decoder prediction indexed by a remembered bit `r` is `p_r`. For a model
`M`, normalized description length is exactly

`J_beta(M) = (1/N) Σ_active E[-ln p_M(Y_n | F_n)]
             + beta * (1/N) Σ_active E[w_n]`,

with `N=21` active rows in the membership table. Structural join initialization
at `n=0` has its own `q_join` factor and is not a learned Bernoulli write, so it
contributes no `w_n` cost.

The conditional entropy attained by a correct remembered regime is

`H = -(3/4) ln(3/4) -(1/4) ln(1/4)
   = ln 4 - (3/4) ln 3`.

Predicting the opposite regime has cross entropy

`H_wrong = -(3/4) ln(1/4) -(1/4) ln(3/4)
         = ln 4 - (1/4) ln 3`,

so one wrong-regime row costs exactly

`H_wrong - H = (1/2) ln 3 > 0`.

All source probabilities and transition/observation quantities are rational;
only the exact logarithmic score of those rational probabilities appears in the
objective.

## 3. Constructive sparse writer and complete lifetimes

The intended causal sparse writer uses bounded state `z∈{0,1}⊂[0,1]`:

1. at structural join, set `z=X_0` through `q_join`;
2. on an active existing row, write `z←X_n` iff `C_n=1`;
3. otherwise preserve `z` exactly;
4. decode `Y_n` with `p_z`.

It is online because `(C_n,X_n)` is in `F_n`. It makes two learned writes on
each seven-row lifecycle and achieves the entropy lower bound on every row:

`J_beta(SPARSE) = H + (2/7) beta`.

The learned write rows equal the two post-join regime changes for either script,
so audit-only boundary precision and recall are exactly one. Script `23` has
complete lifetimes `2,3`; script `32` has `3,2`. Therefore the number of
distinct complete active-step lifetimes is exactly two. Neither lifetime is
created by identity, global time, membership events or inactive gaps.

The representation is unique only as a remembered regime bit up to its
invertible relabeling `0↔1`; the writer itself will fail uniqueness because the
same bit can be carried by `h`.

## 4. Analytic registered-null optima

The C-ALPSW predictive decoder is explicitly allowed to condition on the fast
recurrent state `h`. Let a one-bit recurrence update on a cue and persist
otherwise:

`h_n = X_n` if `C_n=1`, and `h_n = h_n-1` otherwise,

with temporary absence freezing `h`. Decoding with `p_h` attains `H` on every
active row. This recurrence is online, task-blind, anonymous and uses no
forbidden information.

For `beta≥0`, the exact optima of the registered structural nulls on this source
are:

| Registered null | Online realization | Learned-write rate | Minimum `J_beta` |
|---|---|---:|---:|
| `ALWAYS_WRITE` | Decode from `h`; write on all six post-join active rows. | `6/7` | `H + (6/7) beta` |
| `NEVER_WRITE_AFTER_JOIN` | Decode entirely from `h`; keep `z` at structural initialization. | `0` | `H` |
| `FIXED_AGE_OR_PERIODIC_WRITE` | Decode from `h`; among required periods `1..6`, period six minimizes nonnegative write cost. | `1/7` | `H + (1/7) beta` |
| `MEMBERSHIP_EVENT_ONLY_WRITE` | Decode from frozen/restored `h`; if the sole rejoin must write, only `ℓ1` writes once. | `1/21` | `H + (1/21) beta` |
| `POST_HOC_NONCAUSAL_SEGMENTATION` | Retrospective boundaries install no online state; the legal online predictor decodes from `h`. | `0` | `H` |

If fixed-period or membership-event-only nulls permit skipping an eligible
write, their minima reduce further to `H`; this does not alter the result.
Allowing a post-hoc model to inspect future data at decision time would violate
`F_n` and produce `INVALID_ALPSW_DERIVATION_CONTRACT`, so its admissible online
optimum above uses no retrospective state installation.

For reference, a deliberately memoryless never-write decoder that ignores `h`
would be wrong on three of seven rows under script `23` and two of seven under
script `32`. Its expected objective would be

`H + ((3+2)/(2*7)) * (1/2 ln 3)
 = H + (5/28) ln 3`.

This worse value cannot be used as the registered null because the frozen
C-ALPSW factorization itself supplies `h` to the decoder.

## 5. General recurrent-absorption theorem

### Proposition

For any finite discrete source and any online C-ALPSW model under the
registered factorization, there is an online never-write-after-join recurrent
model whose expected predictive NLL is no greater. If the C-ALPSW model has a
positive expected learned-write rate, the never-write model has strictly lower
`J_beta` for every `beta>0`.

### Proof

At a finite horizon with finite observations, actions and membership events,
the set of legal online histories is finite. Define the never-write model's
recurrent state `h'` as an injective code of the current legal history, or
equivalently of the predictive sufficient statistic induced by that history.
Its deterministic recurrence appends the current legal observation, executed
action and anonymous membership event. Temporary absence freezes this code.
The separate slow state is structurally initialized and never written.

For any history `f`, let the absorbed decoder output the original C-ALPSW
model's predictive distribution marginalized over any internal writer and
candidate randomness:

`p_abs(y | f) = E[p_original(y | f,h,z) | f]`.

This distribution is online because it depends only on `f`. The log-sum
inequality gives expected predictive NLL no greater than that of first sampling
the original internal state and then scoring its conditional decoder. If the
original state is deterministic given history, the distributions and NLL are
exactly equal. Lifecycle relabeling and active-member permutation only relabel
the product of per-lifecycle history states; neither becomes a feature.

The S1 contract registers no dimension bound, information bottleneck or
complexity cost on `h`, and explicitly supplies `h` to the predictive decoder.
The finite history recurrence is therefore inside the unrestricted recurrent
simpler explanation frozen by the contract. On the explicit source above, it
reduces to one regime bit and has exactly the same state cardinality as `z`.

Let the original expected predictive NLL be `L` and its expected learned-write
rate be `q>0`. The absorbed model has zero learned writes and satisfies

`J_beta(absorbed) <= L`,

`J_beta(original) = L + beta*q`.

Thus the absorbed model is strictly better for every `beta>0`. At `beta=0` it
is either better or tied, so the nondegenerate sparse writer is not a unique
optimum. For `beta<0`, an always-write realization with the same predictive
distribution is strictly preferred to any genuinely sparse writer because
each extra write lowers the stated objective. No open beta interval anywhere on
the real line makes a nondegenerate sparse writer uniquely optimal. QED.

### Exact `Delta_ID` consequence

For every `beta≥0`, the full C-ALPSW parameter class contains the absorbed
zero-write recurrence, so its minimum is `H`; the registered null minimum is
also `H`. Therefore `Delta_ID(beta)=0`. If “C-ALPSW” is restricted to the
intended nondegenerate two-write construction instead, then for `beta>0`

`Delta_ID(beta) = H - (H + (2/7) beta) = -(2/7) beta < 0`.

At `beta=0` the constructions tie. For `beta<0`, both the full class and the
registered null family contain always-write, whose `H+(6/7)beta` is strictly
below the intended sparse value `H+(2/7)beta`. Hence no interpretation of the
registered minima supplies a beta with `Delta_ID(beta)>0`, much less a nonempty
open interval.

## 6. Constructive external-policy controls

The source-control action is `A_n=R_n`.

- Constructive ALPSW policy: structural initialization and cue writes set `z` to
  the current regime; choose `A_n=z`. It is correct on all active rows, so
  `U_star_ALPSW=1`.
- Constructive G8-class recurrent policy: update the lifecycle recurrent bit
  `h` on a cue, preserve it otherwise, freeze it during temporary absence and
  choose `A_n=h`. It is correct on all active rows, so `U_star_G8=1`.

This establishes that the finite source does not manufacture a claim that
ordinary recurrence lacks representational capability. It also exposes why the
predictive objective alone cannot identify which state object owns the memory.

## 7. Exact invariance proofs

1. **Lifecycle-key relabeling.** `B,S` are iid and routing keys are absent from
   the filtration. Any bijection on ledger keys maps the transition table,
   state ownership, predictions, writes and utilities bijectively. Mismatch: 0.
2. **Active-member permutation.** Every update and prediction is per lifecycle;
   the joint transition is a product over the active set. Reordering rows does
   not change a factor. Mismatch: 0.
3. **Inactive padding.** Padded rows are outside the active set and contribute no
   transition, prediction, write or objective term. Mismatch: 0.
4. **Temporary-absence insertion.** Inactive rows do not advance `n`; `h,z`, age
   and RNG freeze. Inserting or deleting any finite inactive gap leaves the
   seven active rows identical. Mismatch: 0.
5. **Latent relabeling.** Swapping `0` and `1` in state and decoder leaves every
   probability, boundary, action and objective unchanged. Raw coordinate
   accuracy is therefore not used.

## 8. First-match decision

- `INVALID_ALPSW_DERIVATION_CONTRACT`: no. The construction is finite, online,
  anonymous, exact, membership-complete and invariant; no forbidden field
  enters the writer or predictor.
- `NO_ONLINE_IDENTIFIABLE_SLOW_STATE`: yes. The general absorption theorem and
  the exact source both prove that no nonempty write-cost interval gives a
  uniquely nondegenerate sparse optimum.
- Lower-precedence `NULL_EQUIVALENT_PREDICTIVE_WRITE`: not selected. Never-write
  equality is the witness for the earlier no-identifiability terminal.
- `PASS_ALPSW_IDENTIFIABILITY_DERIVATION`: not reached.

```text
valid_terminal=NO_ONLINE_IDENTIFIABLE_SLOW_STATE
beta_interval=empty
minimum_registered_null=NEVER_WRITE_AFTER_JOIN
Delta_ID_beta=0_at_beta_0_and_nonpositive_for_beta_positive_under_nonzero_writes
boundary_precision_audit=1
boundary_recall_audit=1
distinct_complete_lifetime_count=2
U_star_ALPSW=1
U_star_G8=1
contract_mismatch=0
smallest_refuted_proposition=C_ALPSW_PREDICTIVE_OBJECTIVE_IDENTIFIES_SLOW_STATE_WITHOUT_A_FAST_STATE_BOTTLENECK
smallest_retained_proposition=FINITE_LIFECYCLE_RECURRENCE_CAN_ABSORB_THE_REGISTERED_SLOW_STATE_AND_MATCH_PREDICTION
```

## 9. Consequence boundary

This terminal rejects the exact C-ALPSW formulation before implementation. It
does not show that predictive state, sparse segmentation, individual lifetime
or task-blind latent dynamics are useless. It shows only that the registered
objective cannot identify the slow state while an unrestricted, unpenalized
fast recurrent state is given the same online history and supplied to the
predictive decoder.

No empirical rescue, beta change, latent-width change, source-difficulty change,
code implementation or compute follows from this result. Any correction that
adds a fast-state information bottleneck, fast-state complexity penalty,
different decoder filtration or new causal objective changes the frozen
scientific contract and must return to the registered GPT-5.6 Pro conversation.
