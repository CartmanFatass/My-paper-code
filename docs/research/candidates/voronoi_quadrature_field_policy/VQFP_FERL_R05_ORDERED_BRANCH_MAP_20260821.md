# VQFP-FERL r05 ordered prerequisite and branch map

```text
owner=direction:voronoi_quadrature_field_policy
object=VQFP-FIXED-EFFORT-RIDGELINE-SAMPLING-DEFINITION
revision=VQFP-FERL-SCIENCE-20260821-05
manifest=VQFP-FERL-R05-ORDERED-BRANCH-MAP-1
status=prospective_definition_only
```

This is a nonselectable restatement of the complete r05 science card. It adds
no predicate or interpretation. A contradiction returns to the EM before any
scientific activity.

## Global conventions

All interval endpoints come from the registered **nominal** 180-member
Bonferroni-adjusted Student working procedure. No exact finite-sample 0.95
familywise guarantee is asserted.

Every seed value is canonical binary64. Mean/variance are exact rational
reductions; the Student quantile at exact probability `7199/7200`, standard
deviation, interval endpoints and reverse intervals are correctly rounded
binary256 values with certificates. Margins are exact rationals promoted to
binary256, and every displayed strict/non-strict comparison is literal with no
epsilon. Spatial/effort/address/special-function certificates and the exact
finite-lattice ANALYTIC global/lexicographic certificate are part of validity.

For lower-is-better endpoint `X` and cell `c`, with nominal interval `[L,U]` for
`Delta_X(A,B,c)=X_B-X_A`, define

```text
MAT_X(A,B,c)  iff L>m_X,
HARM_X(A,B,c) iff U<-m_X,
NH_X(A,B,c)   iff L>-m_X/2,
EQ_X(A,B,c)   iff L>=-m_X and U<=m_X.
```

Margins remain `m_U=0.04`, `m_D90=0.05`, `m_R=0.04`. Failure of `NH` is not
harm unless `HARM` itself holds. Reverse contrasts negate and swap endpoints.

```text
EVENT_SUFFICIENT iff
for every seed b=0,...,23,
every N in {4,6,8,12},
and each layout in {IID,CLUSTER},
M_(b,N,layout)>=40.
```

Event count is action-independent. If `M=0`, `D90_seed=1` is a storage-only
sentinel and `event_sufficient_seed=false`. No `M<40` D90 value may enter an
interpreted predicate.

Every NO_PORT contrast means explicit actor-forward/actor-execution port value
conditional on the common measure-informed training critic. It never means
complete absence of true measure from training.

## Ordered prerequisites

1. `VALID`: the complete atomic panel, exact spatial/effort lattice,
   canonical address/raw-word/transform outputs, every correct-rounding and
   binary256S softmax and binary256 inference certificate, every exact
   finite-lattice ANALYTIC global/tie
   certificate, every working-score/backward/optimizer transition identity,
   and every arithmetic/containment/conservation/storage identity pass. Correct
   zero-event sentinels are valid storage; event insufficiency is not invalidity.
2. `EVENT_SUFFICIENT`: evaluate the global event gate before every D90 use.
3. `PHYSICAL_OPPORTUNITY`: in each held-out cell,
   `L_U(ANALYTIC,EQUAL)>0.08`, either
   `L_D90(ANALYTIC,EQUAL)>m_D90` or `L_R(ANALYTIC,EQUAL)>m_R`, and mean
   EQUAL `U_seed` lies in `[0.20,0.85]`.
4. `ALLOCATION_ACTION_SUPPORT`: every learned arm passes the exact held-out
   rounded-softmax target-share allocation/mode predicate.
5. `FERL_TARGET_HARM_CHECK`: apply decision 5 below before competence.
6. `PER_N_COMPETENCE`: for every learned arm, registered `N` and layout,
   `L(C_A)>0`, every endpoint versus EQUAL satisfies `NH`, and `L(Q_A)>0`.
7. `REMAINING_ANSWERABILITY`: each learned-arm held-out mean endpoint lies in
   `[0.08,0.92]`, and each FERL/FREE half-width is at most `m_X/2`.

## First-matching decision sequence

1. `INVALID_OR_INCOMPLETE`: `VALID` fails. Emit `NUMERIC_CONTRACT` for a
   lattice/address/transform/correct-rounding/binary256S-softmax/
   binary256-inference failure or
   `ANALYTIC_CERTIFICATE` for an uncertified global/tie result, with every exact
   address/state/certificate. No tolerance or approximate action is substituted.

2. `ENDPOINT_NONANSWERABLE`, `reason=EVENT_COUNT`: validity passes and
   `EVENT_SUFFICIENT` fails. Emit every failing seed/cell count and sentinel
   flag; evaluate no D90 predicate.

3. `NO_PHYSICAL_OPPORTUNITY`: event sufficiency passes and any held-out
   opportunity or EQUAL headroom condition fails.

4. `NO_ALLOCATION_ACTION_SUPPORT`: opportunity passes and any learned arm fails
   support in any held-out cell.

5. `FERL_TARGET_HARM`: support passes and either:

   - one common held-out `N` has `HARM_U(FERL,EQUAL)` in both layouts;
   - any held-out cell has `HARM_R(FERL,EQUAL)`; or
   - any held-out cell has `HARM_D90(FERL,EQUAL)`.

   Report harm only for exact qualifying endpoints/cells.

6. `LEARNED_OR_CONTAINING_COMPETENCE_FAILURE`: decision 5 does not match and
   any of the three learned arms fails competence. For every failed
   `NH_X(A,EQUAL,c)`, if `HARM_X(A,EQUAL,c)` is true, report established harm
   for exactly `(A,X,c)` while retaining this disposition. Otherwise report
   non-harm unresolved and make no harm statement.

7. `ENDPOINT_NONANSWERABLE`,
   `reason=INTERIORITY_OR_FERL_FREE_PRECISION`: competence passes and any
   remaining held-out interiority or FERL/FREE precision condition fails.

8. `HETEROGENEOUS_FERL_FREE_EFFECTS`: decisions 1-7 pass and there are held-out
   cells `c,c'` with both `MAT_U(FERL,FREE,c)` and
   `MAT_U(FREE,FERL,c')`. Report exact opposing cells and make no target-wide
   retain/delete decision.

9. `FERL_TREATMENT_SPECIFIC_VALUE`: decision 8 does not match; one common
   `N* in {6,12}` has both layouts satisfying `MAT_U(FERL,FREE)`,
   `MAT_U(FERL,EQUAL)` and `MAT_U(FERL-intact,FERL-reassociated)`; every
   held-out cell satisfies `NH_U(FERL,FREE)` and, for `X in {D90,R}`,
   `NH_X(FERL,FREE)` and `NH_X(FERL,EQUAL)`. Retain only the exact cell-specific
   hard-factor claim.

10. `FREE_MEASURE_SUPERIORITY`: decision 8 does not match; one common `N*` has
    both layouts satisfying `MAT_U(FREE,FERL)`; every held-out cell satisfies
    `NH_U(FREE,FERL)` and, for `X in {D90,R}`, `NH_X(FREE,FERL)` and
    `NH_X(FREE,EQUAL)`. Retain only exact qualifying cells.

11. `EXPLICIT_MEASURE_PORT_ONLY_VALUE`: every FERL/FREE endpoint is `EQ` in
    every held-out cell; one common `N*` has both layouts satisfying
    `MAT_U(FERL,EQUAL)`, `MAT_U(FREE,EQUAL)`,
    `MAT_U(FREE,FREE-NO-MEASURE-PORT)`,
    `MAT_U(FERL-intact,FERL-reassociated)` and
    `MAT_U(FREE-intact,FREE-reassociated)`; every held-out cell has secondary
    `NH` for FERL/EQUAL and FREE/EQUAL. Retain only explicit actor-port/correct-
    binding value conditional on the common critic.

12. `GENERIC_ALLOCATION_VALUE_WITHOUT_MEASURE_SPECIFICITY`: one arm
    `A in {FERL,FREE}` and one common `N*` have both layouts satisfying
    `MAT_U(A,EQUAL)`; all held-out cells satisfy `NH_D90(A,EQUAL)` and
    `NH_R(A,EQUAL)`; and all held-out endpoint intervals are `EQ` for FERL/FREE,
    both intact/reassociated contrasts and FREE/NO_PORT. Only then may the exact
    family move toward generic scarcity allocation. NO_PORT remains conditional
    on the common critic.

13. `ALLOCATION_VALUE_WITH_MEASURE_SPECIFICITY_UNRESOLVED`: the common-arm/
    common-`N*` value condition from decision 12 holds with global secondary
    non-harm, but decisions 8-12 do not match. Retain correct association,
    generic allocation, optimization geometry and insufficient control
    precision as live explanations; make no automatic deletion/modification.

14. `TARGET_SPECIFIC_NO_MATERIALITY`: every held-out endpoint is `EQ` for
    FERL/FREE, FERL/EQUAL, FREE/EQUAL, both intact/reassociated contrasts and
    FREE/NO_PORT. Close only this exact target without a positive, negative-
    general or arbitrary-`N` claim.

15. `UNRESOLVED_VALID_EVIDENCE`: all prerequisites pass and no earlier decision
    matches. Report every interval and launch no automatic successor.

## Required output

Emit the top-level disposition and reason code, every prerequisite Boolean with
its underlying count/interval, every competence-branch harm annotation, common
qualifying `N*` where applicable, all raw seed vectors, and which later
contrasts are descriptive. No branch launches a successor, deletes a family,
changes a threshold or authorizes activity.
