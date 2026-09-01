# VQFP VNPA r02 static-CM intake and complete r03 return — 2026-08-23

```text
document_kind=direction_cm_return_scientific_intake_and_complete_replacement_return
owner=direction:voronoi_quadrature_field_policy
assignment=VQFP-POST-ANALYTIC-VARIABLE-N-EMPIRICAL-DEFINITION-R01
object=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01
cm_input_revision=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-02
replacement_revision=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-03
cm_return_sha256=bc734bef9e234f699fd330e717116feca86214efb752556235715e072f4d1530
decision_marker=VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R02_CM_INTAKE_ACCEPT_PHILOX_AMBIGUITY_FREEZE_R03_RECLOSURE_RECOMMENDED_20260823
cm_static_constructability=accepted_subject_to_science_clarification
cm_science_bearing_ambiguity=PHILOX_NAMESPACES
em_ambiguity_disposition=ACCEPT_GENUINELY_SCIENCE_BEARING
replacement_scope=normative_Philox4x32_10_key_counter_lane_rejection_address_law_only
same_conversation_pro_reclosure_recommended=true
portfolio_decision_made=false
construction_authorized=false
empirical_activity_authorized=false
question_relevant_activity_begun=false
allocation_change=false
portfolio_cut_preserved=EMPIRICAL_4|ENABLING_CONSTRUCTION_0|DEFINITION_ONLY_1|UAV_EMPIRICAL_1
```

## Decision

Accept the CM's `PHILOX_NAMESPACES` ambiguity as genuinely science-bearing.
Freeze the complete replacement revision
`VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-03` (`r03`)
and recommend that Portfolio authorize exactly one same-conversation ChatGPT
Pro reclosure of r03. Do not select construction or empirical activity from
this intake.

The r02 Pro `CLOSED` disposition remains valid evidence about exact r02. It
does not close r03 because the accepted address law determines the actual
candidate vectors, geometries, Markov paths and resampling selections. R02 is
therefore superseded prospectively before activity, not retroactively declared
invalid.

## Exact CM facts accepted

The exact CM return has the assigned SHA-256 and matches the VQFP direction,
object and r02 revision. It reports no question-relevant output and performed
only static read-only inspection and paper feasibility/cost reasoning.

Accept the following technical evidence without converting it into scientific
or production authority:

- exact r02 is finite and native-first constructible on CPU once the RNG
  address law is fixed;
- no conforming r02 host, policy/control kernel, search, evaluation panel,
  resampler, runner, result schema or native registration exists today;
- the historical VQFP-B1 Python/PyTorch experiment is semantically different
  and cannot be adapted by changing constants;
- a batched C++ exact host, fused search/evaluation/resampling path, exact
  numeric predicates, atomic serialization/resume and result-blind
  measurement seams are required;
- the expected CM projection is central, with an exact-arithmetic/resampling
  tail reaching high; and
- no other science-bearing ambiguity was found in host, policies, controls,
  counts, estimands, finite resampling operations, terminal precedence,
  no-partial boundary or claim ceiling.

The CM prospective totals are retained as technical planning evidence:

| Case | Engineer-days | CPU core-hours | Wall | Peak RSS | Scratch | Durable | GPU |
|---|---:|---:|---:|---:|---:|---:|---|
| Low | 10 | 240 | 10 h | 8 GiB | 16 GiB | 4 GiB | none |
| Central | 16 | 820 | 32 h | 18 GiB | 56 GiB | 11 GiB | none |
| High | 20 | 1,750 | 70 h | 30 GiB | 112 GiB | 22 GiB | none |

The high case remains inside the frozen ceiling of 20 engineer-days, 1,800
CPU core-hours, 72 wall hours, 32 GiB RSS, 120 GiB scratch and 24 GiB durable,
but with little tail margin. This is not a guarantee, lease or construction
selection. A later result-blind measurement above any high limit returns to
Portfolio and Operational Root before expansion or compute.

## Why `PHILOX_NAMESPACES` is science-bearing

R02 named decimal root keys and said that purpose, block, roster, episode,
step, candidate and draw indices occupy disjoint counter tuples. It did not
define:

- how a decimal root key becomes the two Philox 32-bit key words;
- which semantic dimensions occupy the four counter words;
- which of four output lanes supplies a scalar draw;
- how modulo-rejection attempts advance without consuming another draw;
- how candidate coordinate addresses remain independent;
- how inner modulo rejection and outer whole-geometry rejection nest; or
- how source-block and state-stratified episode resampling addresses remain
  paired across arms.

Those choices are not merely reproducibility metadata. Treatment and FREE
candidate coordinates are part of the selected interventions. Geometry and
Markov tapes are the finite host panel. Bootstrap selections determine the
registered decision bounds and terminal branch. Two encoders satisfying r02's
prose can therefore yield different selected policies, observations and
conclusions. CM may not choose among them.

The ambiguity also hides possible numeric collisions among the root-key
formulas. R03 preserves every root-key number but assigns purpose-specific
family codes in the counter so that equal numeric root keys still address
different streams. Concretely, development `(b=10,N=4)` and validation
`(b=0,N=4)` both evaluate to root key `202608232004`; r03 separates them with
family codes `0x10/0x11` and `0x20/0x21`. This is the smallest clean
clarification that makes the finite object single-valued.

Question-relevant activity has not begun, so a prospective complete
replacement and same-conversation reclosure are permitted. Retrofitting an
active panel is not involved.

## Complete r03 resolution

The complete normative replacement is:

`docs/research/candidates/voronoi_quadrature_field_policy/VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R03_SCIENCE_CARD_20260823.md`

R03 freezes:

1. the exact standard ten-round unsigned Philox4x32 transformation, constants,
   key bump and output-lane order;
2. unsigned 64-bit decimal root-key parsing with
   `k0=R mod 2^32`, `k1=floor(R/2^32)` and little-endian persistence;
3. a generic scalar rejection law using
   `counter=(floor(rho/4),c1,c2,c3)` and `lane=rho mod 4`, with no mutable
   stream advancement or wrap;
4. ten exhaustive draw-family rows: treatment coordinates, FREE coordinates,
   development geometry and Markov, validation geometry and Markov,
   evaluation geometry and Markov, bootstrap source blocks, and bootstrap
   state-stratified episode positions;
5. purpose-specific family codes in the high byte of `c3`, exact semantic
   counter fields and private rejection sequences;
6. whole-vector geometry-attempt semantics: draw every component at the same
   outer attempt, test heterogeneity only after the full vector, then advance
   the outer attempt;
7. ordered source-state strata, roster codes and canonical bootstrap
   resample-position semantics; and
8. `RNG_ADDRESS_EXHAUSTED` as a competence/no-partial failure if a finite
   counter domain is exhausted, never as treatment evidence.

No candidate, arm, worker, process, batch width, resume point or schedule can
silently alter a host or bootstrap address. There are no unregistered random
draw families.

## Preserved r02 science

R03 preserves unchanged:

```text
ONE_DIMENSIONAL_MARKOV_FIELD_HOST
N_TRAIN_4_8|N_HELDOUT_6_12
ONE_GLOBAL_TREATMENT_THETA
CONDITIONAL_4D_RESIDUAL_FREE_WITH_THETA_FIXED
EXACT_RATIONAL_GEOMETRY_FIELD_AND_ENDPOINT
LEGAL_LARGEST_REMAINDER
EQ|DENS|MASS|MARG0|ORACLE|FREE_EMBED
FULL_HALF_CYCLE_T_P_AND_F_P
12_TRAINING_AND_EVALUATION_BLOCKS
2048_CANDIDATES_PER_SEARCH|FORCED_ANCHORS|32_FINALISTS
512_EVALUATION_EPISODES_PER_BLOCK_ROSTER
20000_PAIRED_STATE_STRATIFIED_HIERARCHICAL_DRAWS
L_STAR_RANK_500|U_STAR_RANK_19500|NO_COVERAGE_CLAIM
EXACT_COMPETENCE_SUPPORT_ESTIMANDS_THRESHOLDS_AND_TERMINAL_PRECEDENCE
NO_PARTIAL_RELEASE
ONE_SELECTED_POLICY_CLAIM_CEILING
R05_AND_UAV_NONTRANSFER
LOW_CENTRAL_HIGH_COST_CEILING
```

The treatment/comparator relation, variable-`N` axis, scientific question,
activity boundary, maximum claim and strongest alternatives do not change.

## Claim ceiling and alternatives

The maximum claim supported now is only:

> The static CM found the frozen experiment constructible subject to an RNG
> clarification, and r03 supplies a complete prospective deterministic
> definition. R03 has not yet received Pro closure and no empirical value is
> known.

If r03 later receives Pro `CLOSED`, Portfolio separately selects construction,
CM accepts conformance, a complete panel reaches a supported branch, this EM
intakes the result and the same Pro conversation validates it, the unchanged
prospective positive ceiling is:

> On the frozen 1-D Markov-field host and under the registered finite panel,
> margins and resampling decision law, one single roster-independent VQFP
> coefficient vector selected using only `N={4,8}` met the named held-out
> metric criteria at both `N=6` and `N=12` over every frozen nonoracle
> baseline, was noninferior to matched residual FREE, and lost value under
> full half-cycle measure reassociation. This is evidence for a useful
> physical-association inductive bias for that selected policy on this host.

The ceiling still excludes coverage, retraining repeatability, measure
necessity, jointly reoptimized eight-dimensional FREE noninferiority,
arbitrary geometry, dynamic-roster robustness, r05 evidence, 2-D/UAV value,
flight, safety and deployment.

The strongest remaining alternative is an unevaluated jointly reoptimized
eight-dimensional FREE policy. Within the tested panel, generic diminishing
returns (`MARG0`/ORACLE), DENS/MASS, finite-search regularization or selection
luck, LR quantization and inadequate host headroom remain the strongest causal
alternatives.

## Provider continuation and Portfolio question

The exact self-contained provider-visible reclosure question is:

`docs/research/candidates/voronoi_quadrature_field_policy/VQFP_VARIABLE_N_PHYSICAL_ASSOCIATION_VALUE_R03_CHATGPT_PRO_RECLOSURE_QUESTION_20260823.txt`

Portfolio should authorize exactly one continuation in the existing same-VQFP
ChatGPT Pro conversation for exact r03. This recommendation is not a send or a
Portfolio decision. `CLOSED` plus later same-direction EM intake would complete
only r03's mathematical/causal definition boundary. `REVISION_REQUIRED` would
return every defect for another complete replacement.

Do not request construction yet. If r03 is later closed and intaken, Portfolio
may separately decide whether to return exact r03 to the same CM for updated
static acceptance and then authorize native construction inside the unchanged
high ceiling. The r02 static evidence is informative but cannot technically
accept an implementation against a different revision.

## Cut, isolation and fences

This intake preserves the exact current cut:

```text
EMPIRICAL_4|ENABLING_CONSTRUCTION_0|DEFINITION_ONLY_1|UAV_EMPIRICAL_1
```

RISP, RCLE, SGSP and DISH retain all existing science, activity, lease,
recovery, result and production fences. This intake transfers no evidence,
threshold, provider conclusion, resource, authority or stage fact across
directions. VQFP-FERL r05 remains isolated and is neither resumed nor supplied
efficacy evidence.

```text
RISP_FENCE_CHANGE=false
RCLE_FENCE_CHANGE=false
SGSP_FENCE_CHANGE=false
DISH_FENCE_CHANGE=false
VQFP_R05_RESUME=false
CROSS_DIRECTION_EVIDENCE_TRANSFER=false
PORTFOLIO_CUT_CHANGE=false
```

## Owner translation

```text
observed_fact=The exact read-only CM return finds r02 finite and constructible within the frozen high ceiling but proves its Philox prose admits multiple key/counter/lane/rejection encoders that generate different candidates, host panels and resamples; r03 freezes one complete normative encoder and preserves all other science.
local_action_fence=This intake and replacement perform no provider, CM, source, build, test, runtime, compute, lease, identity, coordinate, panel, result, partial-value, Git, deployment or flight action; the exact r02 CM assessment remains read-only.
scientific_stage_continuation=Portfolio may decide whether to authorize exactly one same-conversation Pro reclosure of complete r03; construction and empirical selection remain separate later decisions.
root_decision_class=Portfolio r03 reclosure decision only; no Portfolio, allocation, construction, empirical or resource decision is made by this EM.
applies_to=VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01 r02 CM intake and exact r03 prospective replacement only.
does_not_imply=pro_closed_r03|construction_feasible_r03|construction_authorized|empirical_activity|efficacy|host_support|held_out_N_value|association_value|measure_necessity|full_FREE_noninferiority|r05_resume|UAV_value|allocation_change|lease|compute|Git|deployment|flight
continuation_owner=Dedicated Portfolio Root for the reclosure decision; same-direction VQFP EM for exact Pro intake/revision; Operational Root and same-direction CM only after a later exact bridge.
```
