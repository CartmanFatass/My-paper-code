# S2 Exclusive Slow-Channel Identifiability Derivation

Date: 2026-07-24

```text
action_id=S2_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_DERIVATION
scientific_source=docs/research/cdc/EVIDENCE_NOTES/20260724_ALPSW_S1_RESULT_AND_S2_DIRECTION.md
immutable_s1_source=docs/research/cdc/EVIDENCE_NOTES/20260723_ALPSW_IDENTIFIABILITY_DERIVATION_S1.md
code_executed=false
compute_executed=false
formal_run=false
```

## Result

`NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`

The exclusive information partition removes every S1 recurrent side channel and is internally valid. The cue writer is exact and remains the unique zero-predictive-excess two-write schedule. It nevertheless is not the unique global optimum throughout the frozen interval `0 < beta < (1/2)ln 3`.

The admissible `NEVER_WRITE_AFTER_JOIN` null keeps the structural join bit `z=B` and fits its optimal decoder to the aggregate target distribution. Its optimal prediction is not the deliberately restricted S1 reference decoder `p_z`; it is the exact softened probability `P(Y=z | z)=4/7`. This reduces its predictive penalty enough that it ties the cue writer at an interior `beta_star` and beats it above that value. Therefore the frozen complete-interval obligation fails without a side-channel leak.

## 1. Immutable finite source and information order

S2 content-binds the complete S1 source without modification.

Each lifecycle independently samples `B∈{0,1}` and script `S∈{23,32}`, each uniformly and mutually independently. Its seven active rows are:

| Script | Regime `R_0..R_6` | Cue rows | Complete lifetimes |
|---|---|---|---|
| `23` | `B,B,1-B,1-B,1-B,B,B` | `0,2,5` | `2,3` |
| `32` | `B,B,B,1-B,1-B,B,B` | `0,3,5` | `3,2` |

At an active row, `O_n=(C_n,X_n)`, where a cue has `C_n=1,X_n=R_n` and a non-cue has `C_n=0,X_n=⊥`. The generic target satisfies exact rational law

`P(Y_n=R_n | R_n)=3/4`, `P(Y_n=1-R_n | R_n)=1/4`.

The three-lifecycle global table is exactly the S1 table: 21 active rows, one temporary leave/rejoin, one fresh genuine join and terminal leaves. Temporary absence emits no objective row and freezes lifecycle state, age and RNG. Routing keys never enter the scientific filtration.

Structural join at `n=0` sets `z=B` from the current cue and has no Bernoulli write cost. On an active existing row, the admissible slow writer sees only current `O_n`, previous `z` and fresh writer randomness. The slow decoder receives only installed `z`. It does not receive `O_n`, the current cue, fast `h`, age, active index, time, action, active-set or membership history, auxiliary recurrence, identity, role, task, reward, goal, success, progress, future input or oracle boundary.

The objective is

`J_beta^SC(M) = mean_active E[-ln p_eta(Y_n | z_n+)] + beta * mean_active E[w_n]`.

Oracle changes appear only in the audit table. External source-control utility is absent from writer supervision.

## 2. Candidate cue writer

The cue writer initializes `z=B` structurally and, post-join, writes exactly when `C_n=1`, installing `X_n`; otherwise it preserves `z`.

For either script it writes twice per seven active rows, always has `z=R_n` before decoding and reaches

`H = -(3/4)ln(3/4) -(1/4)ln(1/4) = ln 4 -(3/4)ln 3`.

Thus

`J_beta^SC(CUE) = H +(2/7)beta`.

The learned writes coincide exactly with post-join regime changes, so boundary precision and recall equal one. Complete active-step lifetimes remain `{2,3}`.

Any zero-excess decoder must distinguish the two strict target laws `p_0` and `p_1` on every row. Because the decoder sees only binary `z`, this requires `z=R` up to the single invertible `0↔1` relabeling. Hence any zero-excess online model must install the changed bit on each actual cue row. A source-script-independent fixed schedule must contain the union `{2,3,5}` and therefore writes at least three times. The observation-dependent cue writer is the unique zero-excess two-write schedule up to latent relabeling.

This uniqueness at fixed predictive excess is insufficient for the frozen global objective, because a softened null may trade positive predictive excess for fewer writes.

## 3. Complete deterministic fixed-age enumeration

A deterministic fixed-age null is identified by a six-bit mask `a_1...a_6`; bit `a_n=1` means a write at post-join active age `n`. The 64 masks are exhaustively partitioned below.

| Write count | Complete mask set |
|---:|---|
| 0 | `000000` |
| 1 | `100000 010000 001000 000100 000010 000001` |
| 2 | `110000 101000 100100 100010 100001 011000 010100 010010 010001 001100 001010 001001 000110 000101 000011` |
| 3 | `111000 110100 110010 110001 101100 101010 101001 100110 100101 100011 011100 011010 011001 010110 010101 010011 001110 001101 001011 000111` |
| 4 | `111100 111010 111001 110110 110101 110011 101110 101101 101011 100111 011110 011101 011011 010111 001111` |
| 5 | `111110 111101 111011 110111 101111 011111` |
| 6 | `111111` |

This list is the full power set of ages `{1,2,3,4,5,6}`: its row counts are `1+6+15+20+15+6+1=64`.

For each mask `A`, the strongest deterministic candidate installation is also enumerated, not assumed. At each scheduled age, a candidate map has domain

`{neutral,cue-0,cue-1} × {prior z=0, prior z=1}`

and binary output, so there are exactly `2^6=64` maps. Allowing a separate strongest map at every scheduled age gives the finite set `G(A)` of size `64^|A|`; this is an over-approximation of a shared candidate encoder and therefore cannot make a null look weaker.

For each `(A,g)`, propagate `z` through all 28 equally weighted `(B,S,n)` cases: two `B` values, two scripts and seven active rows. Define

`N_z(A,g) = number of cases decoded with state z`,

`K_z(A,g) = sum over those cases of [3 if R=1, 1 if R=0]`.

The second quantity is four times the expected count of target `Y=1`. The exact maximum-likelihood decoder is

`q_z(A,g) = K_z(A,g) / [4 N_z(A,g)]`

for nonempty state cells, and its exact expected NLL is

`L(A,g) = (1/28) sum_z N_z * h(q_z)`,

where `h(q)=-q ln q-(1-q)ln(1-q)`. Therefore the exact optimum of every fixed-age mask is the finite analytic quantity

`J_A(beta) = min_{g in G(A)} L(A,g) + (|A|/7)beta`.

This expression enumerates every candidate-state map and exact logarithmic objective for every one of the 64 masks; no sampled, asymptotic or implementation result is used. The decisive mask `000000` is resolved in closed form in Section 6. The branch does not require choosing a representative mask or assuming the restricted `p_z` decoder.

`ALWAYS_WRITE` is mask `111111`. `NEVER_WRITE_AFTER_JOIN` is mask `000000`.

## 4. Complete periodic and membership-only enumeration

Every deterministic period/phase schedule within post-join ages 1--6 is already one of the 64 masks. The complete mapping is:

| Period | Phase schedules as age subsets |
|---:|---|
| 1 | `{1,2,3,4,5,6}` |
| 2 | `{1,3,5}`, `{2,4,6}` |
| 3 | `{1,4}`, `{2,5}`, `{3,6}` |
| 4 | `{1,5}`, `{2,6}`, `{3}`, `{4}` |
| 5 | `{1,6}`, `{2}`, `{3}`, `{4}`, `{5}` |
| 6 | `{1}`, `{2}`, `{3}`, `{4}`, `{5}`, `{6}` |
| greater than 6 | empty post-join subset |

Duplicate singleton masks remain one deterministic extreme point. Thus periodic schedules add no unenumerated policy.

For membership-event-only writes, genuine join remains structural and temporary leave has no active row. The possible current active-row event categories are ordinary, rejoin and terminal-leave. The eight deterministic write mappings are exactly

`000 001 010 011 100 101 110 111`,

with bits ordered `(ordinary,rejoin,terminal)`. For each mapping, the exact three-lifecycle membership table determines its write rows; candidate maps and decoder optima use the same finite `N_z,K_z` construction above over all 21 active rows. No membership history is available. Any mapping that uses a routing key, counts inactive rows or retains prior event history is instead the forbidden ACTIVE_SET_TIME leak.

Post-hoc noncausal segmentation installs no online state and changes no prediction. Its online state and optimal decoder are exactly the never-write case.

## 5. Stochastic policies

Let a stochastic structural null mix deterministic policies `d` with weights `alpha_d`, with no mixture identity supplied to the writer or decoder. Its joint distribution of `(Y,z)` is the convex combination of the deterministic joint distributions. Conditional entropy `H(Y|Z)` is concave in that joint distribution, while expected write count is linear. Therefore

`J_beta(mixture) >= sum_d alpha_d J_beta(d) >= min_d J_beta(d)`.

If the mixture identity is exposed to the decoder, it is an auxiliary persistent side channel and is rejected earlier as `SIDE_CHANNEL_OWNERSHIP_LEAK`; even then its weighted objective cannot be below its best deterministic component. Thus no stochastic mixture beats the best enumerated deterministic extreme point.

## 6. Exact never-write optimum and interior crossover

Under `NEVER_WRITE_AFTER_JOIN`, structural initialization leaves `z=B` for all seven rows.

For script `23`, `R=B` on four rows and `R=1-B` on three. For script `32`, the counts are five and two. Averaging scripts gives

`P(R=z)=9/14`, `P(R=1-z)=5/14`.

After the exact `3/4` target channel,

`P(Y=z | z) = (9/14)(3/4) +(5/14)(1/4) = 32/56 = 4/7`.

The optimal decoder therefore predicts `4/7` for `Y=z` and has exact NLL

`L_NW = h(4/7)
      = ln 7 -(4/7)ln 4 -(3/7)ln 3`.

It makes zero learned writes, so `J_beta^SC(NW)=L_NW` for every beta. Strict concavity of binary entropy, or strict loss of the regime information under the many-to-one map to structural `z`, gives `L_NW>H`.

Let `G=L_NW-H`. Exact simplification gives

`G = ln 7 -(11/7)ln 4 +(9/28)ln 3 > 0`.

The cue writer ties never-write at

`beta_star = (7/2)G
           = (7/2)ln 7 -(11/2)ln 4 +(9/8)ln 3`.

This crossover lies strictly inside the frozen interval. Positivity follows from `G>0`. For the upper bound,

`beta_star < (1/2)ln 3`

is equivalent to

`7^28 * 3^5 < 4^44 = 2^88`.

The inequality is exact because `7^7=823543 < 2^20=1048576`, hence `7^28<2^80`, and `3^5=243<2^8=256`; multiplying gives the required strict bound.

Therefore:

- for `0<beta<beta_star`, this particular null is worse than the cue writer;
- at `beta=beta_star`, never-write ties the cue writer, destroying uniqueness and strict `Delta_SC>0`;
- for `beta_star<beta<(1/2)ln 3`, never-write strictly beats the cue writer.

Because never-write is an admissible registered null and uses no temporal side channel, this single exact crossover is sufficient to refute the complete-interval C-ALPSC obligation. Over the unrestricted C-ALPSC parameter class, the never-write model is itself available, so `Delta_SC=0` at and above the crossover; if C-ALPSC is restricted to the cue writer, `Delta_SC=L_NW-[H+(2/7)beta]` is zero at the crossover and negative above it.

## 7. Mandatory forbidden leak counterexamples

These constructions are outside admissible C-ALPSC and confirm that every exclusion is load-bearing.

### FAST_H_LEAK

Give the decoder the cue-updated recurrent bit from S1. It preserves the current regime, achieves NLL `H` on every row and requires zero learned `z` writes.

### AUXILIARY_RNN_LEAK

Give the writer or decoder one auxiliary persistent bit. Update it to `X` on cue rows and preserve it otherwise. It is the fast-state absorption construction under another name: NLL `H`, zero `z` writes.

### AGE_CLOCK_LEAK

Keep structural `z=B` and give the decoder active age plus the current cue pattern. At ages 0,1 the regime is `B`; at age 2 a cue identifies script `23` and no cue identifies script `32`; at age 3 the complementary cue/no-cue pattern identifies the script; age 4 is `1-B` for both; ages 5,6 are `B` after the common cue. Thus the decoder reconstructs every regime with zero learned writes and NLL `H`.

### ACTION_LEAK

Let the constructive recurrent controller choose current action `A=R` and give that action to the slow decoder. Predicting from `A` yields NLL `H` with zero learned `z` writes. The action has transferred fast memory into the predictive channel.

### DIRECT_CUE_DECODER_LEAK

Give the current cue directly to the decoder and use fixed writes at active ages 3 and 6. At script-23 age 2, the direct cue predicts the changed regime; at age 3 the delayed writer flips `z`. Under script 32, age 3 is itself the cue and the same write installs the changed state. At common cue age 5, direct cue predicts `B`; age 6 flips `z` back to `B`. This delayed schedule has NLL `H` and write rate `2/7`, exactly matching the cue writer while its writes are not the true boundary schedule.

### ACTIVE_SET_TIME_LEAK

Expose a deterministic active-set or membership-history sequence from which global row or lifecycle active count is recovered. Combining that clock with structural `z=B` and the registered cue pattern reproduces the age-clock construction. Such a sequence is temporal information, not anonymous ownership context, and is classified as a forbidden clock leak.

## 8. Constructive controls and invariances

The constructive C-ALPSC policy installs `z=R` on cue rows and chooses primitive action `A=z`; the G8-class policy stores the cue in lifecycle recurrent `h` and chooses `A=h`. Both achieve exact `U*=1`. S2 does not train or compare them.

The immutable S1 proofs carry forward exactly:

- lifecycle-key relabeling permutes ledger ownership but no feature;
- active-member permutation reorders independent lifecycle factors;
- inactive padding contributes no transition, prediction or write;
- temporary-absence insertion freezes state/RNG and leaves active sequences unchanged;
- latent `0↔1` relabeling preserves state, decoder, action and objective.

Every registered mismatch is zero. Boundary precision and recall for the candidate remain one; distinct complete lifetimes remain exactly `{2,3}`.

## 9. First-match terminal

1. `INVALID_ALPSC_DERIVATION_CONTRACT`: no. The source is immutable, the exclusive filtration is explicit, all 64 fixed-age masks, all candidate maps, periodic phases, membership mappings, post-hoc null and stochastic mixtures are exhaustively represented by finite exact formulas, and membership/invariance semantics remain valid.
2. `SIDE_CHANNEL_OWNERSHIP_LEAK`: no. The decisive never-write null uses only structural `z=B` and its fitted memoryless decoder `p(Y|z)=4/7`; it receives no `h`, cue, age, clock, action, active-set history or auxiliary state. All deliberate leaks are separately classified as forbidden counterexamples.
3. `NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL`: yes. The exact admissible never-write null ties at interior `beta_star` and beats the cue writer on the nonempty upper part of the frozen interval, so uniqueness and `Delta_SC(beta)>0` fail.
4. `PASS_ALPSC_IDENTIFIABILITY_DERIVATION`: not reached.

```text
valid_terminal=NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL
frozen_beta_interval=0_LT_BETA_LT_HALF_LN3
beta_star=(7/2)ln7-(11/2)ln4+(9/8)ln3
beta_star_inside_frozen_interval=true
decisive_null=NEVER_WRITE_AFTER_JOIN
never_write_decoder_probability=4/7
never_write_nll=ln7-(4/7)ln4-(3/7)ln3
cue_writer_nll=ln4-(3/4)ln3
cue_writer_write_rate=2/7
boundary_precision=1
boundary_recall=1
distinct_complete_lifetimes={2,3}
U_star_ALPSC=1
U_star_G8=1
contract_mismatch=0
smallest_refuted=C_ALPSC_CUE_WRITER_UNIQUE_OVER_COMPLETE_FROZEN_BETA_INTERVAL
smallest_retained=EXCLUSIVE_FILTRATION_REMOVES_S1_SIDE_CHANNEL_BUT_DOES_NOT_FORCE_GLOBAL_RATE_DISTORTION_TRADEOFF
```

## 10. Consequence boundary

This result rejects the exact C-ALPSC frozen interval and objective before implementation. It does not reopen C-ALPSW and does not show that exclusive predictive channels, sparse segmentation or variable lifetime are generally impossible. It establishes that exclusion of temporal side channels is necessary but not sufficient: the optimized predictive decoder creates a rate-distortion tradeoff in which a coarser zero-write state can become globally preferable.

No local beta narrowing, forced `p_z` decoder, extra null restriction, source change, code, prototype or compute is a legal rescue. Changing the interval, decoder family, objective or source requires a new external-Pro scientific decision after this valid S2 terminal.
