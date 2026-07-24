# S5 Predictive-Phase / Skill-Lifetime Confound Derivation

Date: 2026-07-24

```text
action_id=S5_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND_DERIVATION
scientific_source=docs/research/cdc/EVIDENCE_NOTES/20260724_ALSCPS_S4_RESULT_AND_PHASE_CONFOUND_S5_DIRECTION.md
code_executed=false
compute_executed=false
formal_run=false
```

## Result

`PASS_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND`

On the frozen finite anonymous-membership source, a legal current no-cue observation creates a positive-probability predictive-phase update inside a constant current-behavior segment. The decisive histories have identical complete current controlled behavior but next-active cue laws separated by total variation `1/2`. Any monolithic state sufficient for both objects must therefore change predictive class where the behavioral quotient does not change. A legal online projection updates predictive phase while preserving behavioral state, so a predictive-state class transition is not generally a behavioral skill-lifetime boundary on this source.

This PASS establishes only the exact phase/lifetime confound and the distinct scientific roles of current controlled behavior and next-active transition phase. It does not establish a learned factorization, optimal architecture, learned transition timing, policy benefit, recurrence insufficiency, arbitrary-horizon closure, value, robustness, transport or final integration.

## 1. Frozen lifecycle source and active clock

Each lifecycle independently samples uniform `B∈{0,1}` and uniform script `S∈{23,32}`. The seven active rows are:

| Script | `R_0..R_6` | Cue rows | Complete behavioral lifetimes |
|---|---|---|---|
| `23` | `B,B,1-B,1-B,1-B,B,B` | `0,2,5` | `2,3` |
| `32` | `B,B,B,1-B,1-B,B,B` | `0,3,5` | `3,2` |

The three lifecycle epochs contain exactly 21 active rows, one temporary leave/rejoin, one fresh genuine join and terminal leaves. `n` counts active rows only. Temporary absence emits no active row, advances neither active age nor segment age, and freezes lifecycle state and RNG. Genuine join structurally initializes from the current cue. Terminal leave right-censors after evidence capture and deletes lifecycle state.

The task-blind nuisance `N_n~Bernoulli(1/2)` is independent of `B,S,R`, membership and every target. Routing keys are provenance only. None enters a scientific decoder.

## 2. Current controlled-behavior object

Retain complete external support for query `u∈{0,1}` at every legal history and:

`P(Y=1|R,u)=3/4` if `u=R`, and `1/4` otherwise.

For legal history `f`, define `b(f)` as the equivalence class of the complete current controlled vector `(K_f^0,K_f^1)`. On this source, the two current controlled vectors are:

- `R=0`: `(P(Y=1|u=0),P(Y=1|u=1))=(3/4,1/4)`;
- `R=1`: `(P(Y=1|u=0),P(Y=1|u=1))=(1/4,3/4)`.

Thus `b=R` up to a global `0↔1` relabeling. A behavioral lifetime is the maximal active-step run between changes of `b`.

## 3. Next-active predictive-phase target

Define:

`D_n=C_{n+1}`,

where `C_{n+1}` is the cue indicator on the next active row of the same lifecycle. A temporary absence is skipped rather than treated as a zero cue. If the finite horizon or terminal leave occurs first, use an explicit terminal symbol. The decisive histories below occur before censoring, so terminal conventions cannot change them.

For legal history `f`, define:

`Q_f(d)=P(D_n=d|f)`.

A monolithic predictive state sufficient for both objects must reproduce the complete current controlled vector and `Q_f`. The phase decoder receives installed state only. It receives no current cue, active age, clock, script, membership history, future observation or terminal oracle as a bypass.

At an active existing row, a legal online update may use only current `O_n=(C_n,X_n,N_n)`, previous declared state and fresh registered writer randomness. It receives no fast recurrence `h`, age/index, wall or global time, `t mod k`, undeclared observation history, natural action, external query history, membership history, auxiliary persistence, lifecycle identity, script, reward, task, role, goal, success, progress, `D_n`, future cue or oracle boundary.

## 4. Exact decisive histories

### 4.1 Age-1 unresolved history

After active age 1, both scripts have produced exactly:

`C_0=1,C_1=0`.

The source priors are equal and the observed cue history has equal likelihood under both scripts. Therefore Bayes' rule gives:

`P(S=23|C_0=1,C_1=0)=P(S=32|C_0=1,C_1=0)=1/2`.

At the next active row:

- script 23 has `C_2=1`;
- script 32 has `C_2=0`.

Hence:

`Q_age1(D_1=1)=P(D_1=1|age-1 history)=1/2`.

### 4.2 Script-32 age-2 no-cue history

Consider the positive-probability branch `S=32`. At active age 2 the legal current observation has `C_2=0`. Script 23 would have emitted a cue at age 2, while script 32 emits no cue. The current no-cue therefore identifies script 32 under the finite source without using age, script oracle or future information: it resolves the uncertainty carried by the declared predictive phase from the prior history.

For script 32, the next active row is age 3 and has `C_3=1`. Therefore:

`Q_32,age2(D_2=1)=P(D_2=1|S=32 age-2 legal history)=1`.

The witness probability is `P(S=32)=1/2`; it is independent of `B` and nuisance `N` and remains positive under every registered lifecycle-key or member permutation.

## 5. Exact behavior/phase contrast

Under script 32:

`R_1=B` and `R_2=B`.

The complete current controlled behavior vectors at age 1 and age 2 are therefore identical. Thus:

`TV_behavior=0`.

Their phase laws are Bernoulli `1/2` and Bernoulli `1`, so:

`TV_phase=|1-1/2|=1/2`.

The conclusion-bearing exact signature is:

```text
TV_behavior=0
TV_phase=1/2
I_extra=1[TV_behavior=0 and TV_phase>0]=1
phase_only_boundary_count>=1
```

The contrast occurs inside the first script-32 behavioral segment:

`R=B` on active ages `0,1,2`, with complete length `3`.

It is not created by terminal censoring or temporary absence.

## 6. Monolithic-state consequence

Assume one quotient class is sufficient for both current controlled behavior and `Q`. If it assigned the age-1 and script-32 age-2 histories to the same class, one phase decoder would have to output both `Bernoulli(1/2)` and `Bernoulli(1)` from that class, which is impossible. Exact phase sufficiency therefore requires distinct monolithic classes.

Consequently, every behavior-plus-phase sufficient monolithic state has a class transition at the script-32 age-2 no-cue row. Yet `b_before=b_after=B`. The transition is predictive-information-only and lies strictly inside a constant behavioral segment. One positive-probability witness suffices to refute universal alignment between monolithic predictive-state changes and behavioral skill boundaries.

## 7. Legal online behavior/phase projection

Use two declared projections:

- `b`: current controlled-behavior class;
- `p`: next-active predictive phase required for `Q`.

Before the age-2 observation, `p` represents the legal posterior with scripts 23 and 32 equally likely, so its next-cue law is `Bernoulli(1/2)`. On the script-32 path, the current `C_2=0` observation updates `p` to the script-32-next-cue-certain class with law `Bernoulli(1)`.

The same observation does not change `b`: `b_before=b_after=B`. Therefore the online update is:

```text
p: script_uncertain -> script32_next_cue_certain
b: B -> B
```

This uses only previous declared phase plus legal current `C_2`; it uses no age, clock, script label or future cue. A `p`-only update does not reset the behavioral lifetime. The construction proves that the two causal roles can be separated online on the witness; it does not claim that this projection is a unique or optimal learned architecture.

## 8. Comparators, nulls and leaks

### 8.1 `BEHAVIOR_ONLY`

State `b=R` exactly reproduces the current controlled vector and preserves behavioral lifetimes. Because the decisive histories share `b` but require different `Q`, one phase decoder from `b` cannot reproduce both. It fails joint behavior-plus-phase sufficiency.

### 8.2 `MONOLITHIC_BEHAVIOR_PLUS_PHASE`

A monolithic exact quotient can reproduce both objects only by separating the decisive histories. It therefore adds at least one positive-probability class transition at the script-32 age-2 row while behavior is unchanged.

### 8.3 `PHASE_AS_SKILL`

Declaring every phase-class transition a skill boundary labels the script-32 age-2 information update as a new skill. That is a false additional behavioral boundary inside the length-three `R=B` segment.

### 8.4 Forbidden bypasses

- `DIRECT_CURRENT_C_PHASE_DECODER`: direct current cue bypasses declared state ownership and is inadmissible.
- `AGE_OR_CLOCK_PHASE`: active age, global time and `t mod k` are forbidden clock shortcuts.
- `SCRIPT_ORACLE`: direct `S` is a forbidden hidden-source label.
- `FUTURE_CUE_WRITER`: supplying `D_n` or `C_{n+1}` before installation is future-information leakage.
- `POST_HOC_BOUNDARY`: completed-trajectory or later-cue access is invalid online evidence.

None is used by the decisive derivation or two-projection update.

### 8.5 Independent non-solutions

- `MEMBERSHIP_PHASE`: membership is independent of `S`; using its history is forbidden and cannot supply the registered script distinction.
- `NUISANCE_PHASE`: `N` is independent of both current controlled kernels and `Q`; nuisance subdivisions are decoder-equivalent and merge.
- G8: lifecycle recurrence may store behavior and phase together and remains the complete external-policy comparator. S5 makes no recurrence-insufficiency or representational-necessity claim.

## 9. Invariances

Every registered mismatch is zero:

1. Lifecycle-key relabeling changes only provenance labels.
2. Active-member permutation reorders independent lifecycle rows without changing either decisive law.
3. Inactive padding emits no active row and supplies no model input.
4. Temporary-absence insertion is skipped by the next-active target and freezes state, preserving both histories and probabilities.
5. `B` relabeling with the corresponding controlled-kernel relabeling swaps behavior labels but leaves `TV_behavior=0` and `TV_phase=1/2` unchanged.
6. Nuisance-bit relabeling changes no target law.
7. Equivalent phase-class renaming changes no decoder law or update event.

The witness depends on neither physical wall time, padding position, identity nor role.

## 10. Proof-obligation audit

All 24 registered obligations pass:

1. The S1–S4 source and membership contract are unchanged.
2. `D` indexes the next active row, not global time.
3. Temporary absence cannot create or erase the witness.
4. Age-1 writer histories are identical across scripts.
5. Their posterior is exactly one-half/one-half.
6. The age-1 next-cue probability is `1/2`.
7. Script-32 age-2 no-cue is legal current information.
8. It identifies script 32 under the finite source.
9. Its next-cue probability is `1`.
10. Current regime remains `B` across the decisive transition.
11. `TV_behavior=0`.
12. `TV_phase=1/2`.
13. Every jointly sufficient quotient changes class on the witness.
14. The behavioral quotient does not change there.
15. The witness has positive probability `1/2` over scripts.
16. It lies inside a complete length-three behavioral segment.
17. `BEHAVIOR_ONLY` fails phase sufficiency.
18. `PHASE_AS_SKILL` creates an extra nonbehavioral boundary.
19. The legal two-projection update changes `p` without resetting `b`.
20. Direct-cue, clock, script, future-cue, membership-history and post-hoc shortcuts are rejected.
21. Nuisance subdivisions merge.
22. G8 remains a complete recurrent comparator.
23. All registered invariance mismatches are zero.
24. No reward, task, identity, role, goal, success, progress, natural-action memory or future information enters the admissible update.

There is no statistical, mixed or underpowered branch.

## 11. Smallest supported and refuted propositions

### Supported

`P_PHASE_WITHIN_BEHAVIOR`: On the exact source, a legal current no-cue resolves next-active transition phase with `TV_phase=1/2` while the complete current controlled behavior vector is unchanged.

`P_BEHAVIOR_PHASE_ROLE_SEPARATION`: An online declared projection can update predictive phase without changing behavioral state on the witness.

### Refuted

`P_MONOLITHIC_PREDICTIVE_CHANGE_EQUALS_SKILL_BOUNDARY`: Every exact predictive-state class change is a current behavioral skill-lifetime boundary.

S5 does not refute use of monolithic recurrence for control or prediction. It refutes only the universal semantic identification of all such predictive transitions with behavioral skill boundaries.

## 12. First-match terminal

1. `INVALID_PHASE_LIFETIME_DERIVATION_CONTRACT`: not selected. Source, conditional probabilities, next-active semantics, nulls, membership and invariances are exact.
2. `FUTURE_CLOCK_OR_SCRIPT_INFORMATION_LEAK`: not selected. The witness uses only prior declared phase and legal current cue absence; it receives no future cue, script label, age, time or membership history.
3. `NO_PREDICTIVE_PHASE_WITHIN_BEHAVIOR_SEGMENT`: not selected. The positive-probability exact signature is `0` versus `1/2` inside constant `R=B`.
4. `NO_VALID_BEHAVIOR_PHASE_PROJECTION`: not selected. The online update changes `p` on current no-cue while preserving `b`.
5. `PASS_PREDICTIVE_PHASE_SKILL_LIFETIME_CONFOUND`: selected.

## 13. Iteration accounting and stop

No code, implementation plan, prototype, compute, experiment or Monitor action occurred. Iteration 5 is consumed; five remain. This result must return to the same registered Pro conversation before iteration 6 is selected.
