# DISH RBHR r03 opportunity, fork, endpoint, inference and branch manifest

```text
document_kind=direction_science_estimand_inference_branch_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-03
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

## 1. Indices and branch units

```text
b=0,...,23                                  independent replicate block
r=TARGET-VISUAL-MASK-PACKAGE |
  TERRAIN-RELAY-MASK-PACKAGE                physical package
s=K8 | K4_TO_K12 | K12_TO_K4               claim schedule
z=POSITIVE | NEAR_ZERO | NEGATIVE           advantage stratum
c=(r,s,z)                                   branch-authority cell, 16 tapes/block
u=(r,s)                                     atomic supercell, joint over three z
A=S|F|N|I|H                                 STRUCTURED|FLEX|NEVER|IMMEDIATE|HYSTERESIS
J=MEAN|TAIL|DEFICIT|DELAY                    direct endpoint
```

Renewal phase remains a prospectively balanced diagnostic interaction inside
the simultaneous family. It is never an additional branch cell or pass rule.
No pooled regime, schedule or stratum row can replace a required cell.

## 2. Exact windows and endpoint reducers

For a tick window `W` of length `L` and service bits `v[n]`:

```text
service_fraction(W)=(1/L) sum_{n in W}v[n]
service_deficit(W)=dt sum_{n in W}(1-v[n]).
```

For recovery delay, let `i` be the first invalid tick in `W`, and `j` the first
tick `j>=i` such that `j,...,j+9` all lie in `W` and are valid:

```text
delay(W)=0                 if no invalid tick exists
delay(W)=(j-i)*dt          if such j exists
delay(W)=L*dt              otherwise.
```

For ordered tape service fractions `x_(1)<=...<=x_(N)`, let `q=0.1N` and
`m=floor(q)`:

`CVaR_0.1=[sum_{i=1}^m x_(i)+(q-m)x_(m+1)]/q`,

where the fractional term is zero when `q` is integral.

Full-arm direct endpoints use exactly

`W20={n: tau_d<=n*dt<tau_d+20.0 s}` (`200` ticks)

on all sixteen tapes of a block/cell. MEAN is the arithmetic mean of tape
service fractions; TAIL is the fractional CVaR across those sixteen fractions;
DEFICIT and DELAY are arithmetic means of the tape reducers. No full-arm
endpoint conditions on a trigger.

## 3. Registered causal recovery witness

The opportunity assay follows, and never precedes, learned-arm competence. Its
script is a feasible recovery witness, not an optimizer or ceiling.

`SCRIPTED-RECOVERY-WITNESS` is arm-independent and uses only current evaluator
ground truth, packet/buffer state and deterministic mean physics. At every
ordinary renewal it considers the Cartesian product of five raw commands per
UAV

`U={(0,0),(3,0),(-3,0),(0,3),(0,-3)} m/s^2`

after the common norm/slew projection, and both legal owner choices if the
one-handover bit is unused. For each candidate it rolls the exact host forward
20 ticks using current target position/velocity extrapolation, zero future wind
and zero future measurement/radio/packet noise, the current buffers, and the
literal service recurrence. It selects lexicographically by: maximum predicted
valid-service ticks; minimum predicted propulsion energy; retain over transfer;
UAV-0 command index; UAV-1 command index. It applies only the first held
commands and any selected legal transfer, then repeats at the next renewal.
It never reads the realized future tape. Before the first renewal it uses the
same command enumeration at the first available renewal and holds zero command
before that. It permits at most one transfer.

`SCRIPTED-RETAIN` is the same receding-horizon script with the transfer choice
permanently masked false. Both scripts are run on the complete degraded and
mask-off tape; neither uses a learned state or action.

For accepted tape `i` in block/cell `(b,c)`, define:

```text
drop_bci = event service of paired mask-off NEVER
           - event service of degraded NEVER
maintain_bci = 1 iff SCRIPTED-RETAIN has valid service on each of the first
               five ticks beginning at tau_d and has no hard event there
witness_gain_bci = degraded SCRIPTED-RECOVERY-WITNESS event service
                   - degraded NEVER event service
witness_continuity_bci = 1 iff the witness has exactly one owner, no token gap,
                         dual payload, buffer clear, slew or separation breach
                         in W20
O_bci = 1{drop_bci>=0.10} * maintain_bci
        * 1{witness_gain_bci>=0.10} * witness_continuity_bci
q_bc=(1/16) sum_i O_bci.
```

For every `c` in supercell `u`, `WITNESS(u)` requires at least one `O=1` tape
in every block and simultaneous `L(mean_b q_bc)>=0.50`. Failure means only that
r03 did not establish recoverable headroom in that supercell. It never means no
feasible recovery policy exists and never deletes a physical package.

## 4. Competence, support, headroom and precision

### 4.1 Competence

`COMP(u)` passes iff simultaneous lower bounds satisfy:

- `L(mean_b C_ND[A,b,r,k,z])>=0.90` for every arm, both calibration schedules
  `k in {4,12}`, both regimes and all strata; and
- `L(mean_b C_PRE[A,b,c])>=0.85` for every arm and every `c` in `u`.

The block values are defined in the population manifest. Failure is learned-arm
competence not established, not physical impossibility.

### 4.2 Behavior-changing handover support

The primary trigger is the first valid STRUCTURED or FLEX commit intent with

```text
tau_d<=t_trigger<tau_d+20 s
t_trigger<=110 s.
```

For `A in {S,F}` and each opportunity tape, `T^A=1` iff such a trigger exists.
At its boundary define

```text
d_h^A=||h_shadow-h_incumbent||_2/sqrt(128)
d_a^A=||a_promoted-a_retained_incumbent||_2/6,
```

where both actions use the same deterministic evaluation rule and common
projection. Freeze `epsilon_h=epsilon_a=1e-3`. With a zero opportunity
denominator the gate fails. Otherwise per block/cell:

```text
R^A_bc=sum_i O_i*T_i^A / sum_i O_i
B^A_bc=sum_i O_i*T_i^A*1{d_h^A>=epsilon_h}*1{d_a^A>=epsilon_a}
       / sum_i O_i.
```

`SUPPORT(u)` requires, for both arms and every `c` in `u`, at least one primary
trigger in every block and simultaneous

`L(mean_b R^A_bc)>=0.10`, `U(mean_b R^A_bc)<=0.90`, and
`L(mean_b B^A_bc)>=0.10`.

This is the exact not-never/not-always definition. A failed support gate cannot
support adaptive timing; a simple rule survives only through its own value law.

### 4.3 Headroom and answerability

For every `c` in `u`, `HEADROOM(u)` requires simultaneous

```text
L(event MEAN-SERVICE of NEVER)>=0.25
U(event MEAN-SERVICE of NEVER)<=0.85
L(SCRIPTED-RECOVERY-WITNESS minus NEVER event MEAN-SERVICE)>=0.10.
```

`PRECISION(u)` requires every branch-changing direct-effect interval in the
supercell to have half-width at most its corresponding material margin:
`0.03` MEAN, `0.05` TAIL, `0.50` DEFICIT and `1.0 s` DELAY for full-arm
contrasts; `0.03`, `0.05`, `0.25`, `0.5 s` for the fork. Every branch-changing
energy-ratio interval must have half-width at most `0.03`. Phase diagnostics do
not enter this width predicate. Qualitative words such as saturated, censored
or too imprecise have no independent authority; a threshold-crossing interval
whose width passes goes to `UNRESOLVED`.

## 5. Complete fork population

For STRUCTURED, the primary fork trigger is its first valid intent satisfying
the two bounds in section 4.2. Clone immediately before applying that intent.
REAL and SHAM execute exactly ticks `n_trigger,...,n_trigger+99`; the bound
`t_trigger<=110 s` keeps all 100 ticks inside the episode. A terminal event
enters the registered absorbing state. No second transfer is allowed.

Fork endpoints are calculated within each block/cell over that cell's trigger
tapes only, using the same reducers and fractional CVaR. `SUPPORT` requires at
least one trigger in every block/cell before a fork effect has branch authority.
For a zero-trigger block, the stored fork block value is the literal numeric
zero plus `fork_supported=0`; this makes the panel total but is never interpreted
because support has already failed. No block or tape is silently removed.

## 6. Contrasts, margins and interval algebra

For treatment `A` and control `C`, orient benefit as

```text
theta_MEAN=A-C
theta_TAIL=A-C
theta_DEFICIT=C-A
theta_DELAY=C-A.
```

Full-arm material margins are `mF=(0.03,0.05,0.50,1.0)` and fork margins are
`mK=(0.03,0.05,0.25,0.5)`. Noninferiority margins are
`n=(0.01,0.02,0.25,0.5)` for both populations. For a supercell, POS denotes
its POSITIVE stratum and `z` ranges over all three strata:

```text
VALUE_m(A,C;u)
 = [at least one POS lower bound L_j>=m_j]
   AND [for every z,j, L_zj>=-n_j]

NO_MATERIAL_m(A,C;u)
 = for every z,j, [L_zj,U_zj] is contained in [-m_j,+m_j]

MATERIAL_HARM_m(A,C;u)
 = at least one z,j has U_zj<=-m_j

NONINFERIOR(A,C;u)
 = for every z,j, L_zj>=-n_j.
```

Exact equality satisfies the displayed predicate. Use `mK` only for
REAL-minus-SHAM and `mF` otherwise. Required effects are S-N, F-S, F-N, I-N,
I-S, H-N, H-S and REAL-SHAM.

For each block/cell and registered cost window,

`rho_E(A,C)=(E_A-E_C)/E_C`.

If both energies are zero set `rho_E=0`; if comparator energy is zero and
treatment energy is positive, energy nonharm fails deterministically. Otherwise
`NH(A,C;u)` requires simultaneous `U(rho_E)<=0.03` in every stratum, and every
treatment and comparator trajectory in the supercell has exactly zero invalid
commit, token gap, dual owner, dual payload, buffer clear, command-slew breach
and separation breach. Protocol bytes and minimum separation are reported but
not scalarized. Full contrasts use full-episode cost; fork uses 100 ticks.

## 7. One simultaneous max-t family

The 24 replicate blocks are the sole inferential clusters. For every frozen
estimand `h`, compute one block value `X_bh`,

```text
theta_hat_h=mean_b X_bh
se_hat_h=sample_sd_b(X_bh)/sqrt(24).
```

Use exactly 99,999 jointly paired nonparametric bootstrap resamples of the 24
blocks from the `INFERENCE` addresses in the host manifest. The same resampled
block vector is used for every `h`. Recompute every estimand and its block SE.
For resample `g`,

`T_g=max_h |(theta_hat*_gh-theta_hat_h)/se*_gh|`

over nondegenerate estimands. If all 24 observed block values are identical,
the interval is the point `[theta_hat,theta_hat]` and that estimand is excluded
from the maximum only. If an originally nondegenerate estimand has resampled
SE zero, its deviation is zero when its numerator is zero and `+infinity`
otherwise; no resample is discarded. The common critical value is ordered
`T_(95000)`. Every two-sided simultaneous interval is

`[theta_hat-c*se_hat, theta_hat+c*se_hat]`.

If a nondegenerate original estimand has nonfinite value or zero SE without all
24 block values being identical, inference is invalid. Two-sided intervals
supply every one-sided bound.

The frozen hypothesis vector contains:

1. every absolute no-degradation and pre-onset competence estimand;
2. every `q`, drop, maintainability fraction, witness gain, witness-continuity,
   trigger-rate and behavior-changing-support estimand;
3. every NEVER headroom mean;
4. every endpoint/cell effect for S-N, F-S, F-N, I-N, I-S, H-N, H-S and
   REAL-SHAM;
5. every corresponding energy ratio and absolute hard-event rate; and
6. for every claim effect, each exact initial-renewal-phase level minus its
   schedule-wide effect as a diagnostic.

The fork supplies paired potential outcomes, not a randomization law. No
unlisted pointwise or pooled interval can change a branch.

## 8. Atomic first-match predicates

Define

```text
V_SN=VALUE_mF(S,N;u)
V_K =VALUE_mK(REAL,SHAM;u)
CORE=V_SN AND V_K AND NH(S,N;u) AND NH(REAL,SHAM;u)
PACKAGE=V_SN AND NO_MATERIAL_mK(REAL,SHAM;u)
FORK_EXCLUDED=for every fork endpoint j, U_POSITIVE,j<mK_j

RULEQUAL_R=CORE
           AND VALUE_mF(R,N;u) AND NH(R,N;u)
           AND NONINFERIOR(R,S;u), R in {I,H}

FLEXQUAL=V_K
         AND VALUE_mF(F,N;u) AND VALUE_mF(F,S;u)
         AND NH(F,N;u) AND NH(F,S;u)

NM_ALL=NO_MATERIAL for REAL-SHAM, S-N, F-S, F-N,
       I-N, I-S, H-N and H-S with their registered margins.
```

Before these predicates, `PROTOCOL_OK` requires exact host recurrence, causal
mask, one-owner transaction, payload lineage, FLEX algebraic containment,
fork clone, scoring, RNG address uniqueness and complete-panel integrity.

Apply this first matching label independently to every atomic supercell `u`:

1. `INVALID_PROTOCOL_OR_MEASUREMENT` if `PROTOCOL_OK` fails.
2. `LEARNED_ARM_COMPETENCE_NOT_ESTABLISHED` if `COMP(u)` fails.
3. `NO_REGISTERED_RECOVERY_WITNESS` if `WITNESS(u)` fails.
4. `EFFECTIVE_HANDOVER_SUPPORT_NOT_ESTABLISHED` if `SUPPORT(u)` fails.
5. `NONANSWERABLE_OR_NO_HEADROOM` if `HEADROOM(u)` or `PRECISION(u)` fails.
6. `TARGET_SPECIFIC_HARM` iff S-N or REAL-SHAM has MATERIAL_HARM, or either
   fails its absolute continuity/energy `NH`. FLEX and simple-rule comparisons
   cannot trigger this label.
7. `NONACTUATION_PACKAGE_EFFECT` iff `PACKAGE` holds.
8. `SHADOW_ACTUATION_NONPASS` iff `FORK_EXCLUDED AND NOT NM_ALL`.
9. `SIMPLE_RULE_SUFFICIENT[IMMEDIATE]` iff `RULEQUAL_I`; if both rules qualify,
   record both and select IMMEDIATE as the prospectively lower-memory rule.
10. `SIMPLE_RULE_SUFFICIENT[HYSTERESIS]` iff only `RULEQUAL_H` holds.
11. `FLEXIBLE_CONTAINER_SUPERIOR` iff `FLEXQUAL` holds.
12. `STRUCTURED_ATOMIC_VALUE` iff `CORE` holds.
13. `TARGET_SPECIFIC_NO_MATERIAL` iff `NM_ALL` holds.
14. `UNRESOLVED` otherwise.

This order makes the nonactuation package predicate precede actuation nonpass;
restricts harm to S-N, REAL-SHAM and absolute nonharm; leaves FLEX and simple
comparisons reachable; gives tight global no-materiality its own reachable
label; and sends all remaining mixed/crossing patterns to one catch-all.

## 9. Schedule then regime aggregation

Return all six atomic labels before aggregation. No cell preempts another.

Within each physical regime, apply:

1. If the same simple rule qualifies in all three schedules, return
   `SIMPLE_RULE_SUFFICIENT[rule]`; IMMEDIATE wins a two-rule tie and both are
   recorded.
2. Else if FLEX qualifies in all three schedules, return
   `FLEXIBLE_CONTAINER_SUPERIOR`.
3. Else if all three atomic labels are `STRUCTURED_ATOMIC_VALUE`, return
   `STRUCTURED_REGIME_SPECIFIC_VALUE`.
4. Else if fixed `k=8` has any retained positive class from steps 1-3 at its
   atomic level but either switched schedule lacks that same class, return
   `FIXED_ONLY_NO_SWITCH_K_VALUE`, naming the fixed class and both switched
   labels. It supports no variable-switch claim.
5. Else return `NO_COMMON_THREE_SCHEDULE_RETAINED_VALUE` with the ordered
   three-cell tuple.

`STRUCTURED_CROSS_REGIME_VALUE` is returned only when both regimes independently
return `STRUCTURED_REGIME_SPECIFIC_VALUE`. A cross-regime simple-rule or FLEX
family conclusion likewise requires the identical retained class in both
regimes; otherwise conclusions remain package-specific. A failing package
cannot erase a passing package. A retained simple rule must therefore pass its
own RULE-versus-NEVER value and nonharm and its RULE-versus-STRUCTURED
noninferiority in every required atomic supercell.

## 10. Interpretive boundary

`NO_REGISTERED_RECOVERY_WITNESS`, incompetence, nonanswerability, support
failure, no-materiality and unresolved intervals are bounded nonidentification
or exact-package results, never proof that handover is impossible in general.
FLEX superiority supports only the broader finite-budget family. A structured
advantage over FLEX supports finite-budget restriction/learnability, not a
strictly larger function class. No branch supports arbitrary `k`, variable
`N`, unique mediation, safety, deployment or flight.
