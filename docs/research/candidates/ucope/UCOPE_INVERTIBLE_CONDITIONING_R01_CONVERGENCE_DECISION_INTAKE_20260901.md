# UCOPE invertible-conditioning R01 convergence decision intake — 2026-09-01

## Pro decision and provenance

The complete persistent `em:ucope:convergence` response for request
`ucope-em-convergence-20260901-03` decides:

```text
FINAL_DIRECTION_DECISION=CONTINUE
DECISION_AUTHORITY=PRO_FINAL
DECISION_FORMED=true
BLOCKER=NONE

NEXT_DISCRIMINATOR_COUNT=1
NEXT_OBJECT_ID=UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01
NEXT_EVIDENCE_CLASS=B/EXPLORE
SINGLE_CHANGED_AXIS=BELLMAN_COMPLETE_COORDINATE_CONDITIONING_RAW_VS_INVERTIBLY_WHITENED
PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED
COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE
PORTFOLIO_EFFECTS=RESERVED
```

The canonical response is archived at
`temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-convergence-20260901-03/RESPONSE.md`,
SHA-256
`465b4db967dfa3eb36bce4fb8f6ff4591001219418df47277e6204ec4aebf0ba`.
It reports connected read-only GitHub access at pinned ref
`71b2bba2bb1a123a2ffc0a7269cf6a9a20c5b7a5`, all six listed paths read, and no
unlisted path read.

## Question and inputs

The decision question was the smallest direction-local consequence of the valid B1 competence
failure plus the retained odd-support A/RECON audit: continue, park, or recast, and, if continuing,
select exactly one non-B1, single-axis B discriminator without opening acquisition or COUNT/RAW.

Inputs were:

- the valid complete B1 evidence and its earlier convergence decision;
- the prospectively frozen odd-support audit definitions and route map;
- Root's retention of the one-shot audit despite its recorded launch-coordination violation; and
- the audit's already-recorded, independently recomputed measurements.

No old B1 or audit runtime was reopened for this intake, no audit was rerun, and no additional
checkpoint value was read.

## Direct observation

On the exact finite eight-context host and the B1 data/optimizer exposure:

- all 18 final B1 policies and all 72 checkpoint policies were finite and unique, but there were
  zero even-support oracle-root, regret, tail-agreement, or competence passes;
- all 72 retained policies were also finite and unique on odd training-period support, with zero
  odd-competent and zero odd-near policies and `0/3` qualifying final seeds in every arm;
- final paired `FT-XF-FLEX : FT-XF-BC` odd-support dominance counts at updates
  `40,80,160,320` were `2:3`, `2:2`, `4:1`, and `3:2`; only update 160 was clear, so no adjacent or
  final stable package separation exists;
- all six final paired MT/FT tail maps and root vectors were equal, so no target-schedule separation
  exists; and
- across-arm similarity held only at update 40, not at 80, 160, or 320, making
  `all_similar_odd_failure=false` and leaving the old route map uncovered.

The recorded audit route was `MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED`. Acquisition was never
evaluated; its false/null fields were downstream gate locks, not negative acquisition evidence.

## Smallest supported proposition and limitations

```text
ON_THE_EXACT_FINITE_EIGHT_CONTEXT_HOST_AT_THE_B1_DATA_AND_OPTIMIZER_EXPOSURE,
ALL_THREE_NAMED_PACKAGES_FAILED_COMPETENCE_ON_EVEN_HELDOUT_SUPPORT,
AND_ALL_72_RETAINED_POLICIES_ALSO_FAILED_ODD_SUPPORT_COMPETENCE_AND_NEAR_COMPETENCE;
THEREFORE_EVEN_ONLY_EXTRAPOLATION_IS_INSUFFICIENT,
WHILE_TARGET_SCHEDULE, CONDITIONING, OPTIMIZATION, OBJECTIVE, AND REPRESENTATION
REMAIN_UNRESOLVED.
```

This does not show that extrapolation is irrelevant; it shows only that failure begins before an
even-only transport explanation can suffice. It does not establish FLEX superiority: the sole clear
FLEX-over-BC observation was transient at update 160, absent at update 320, and not repeated at an
adjacent checkpoint. It also does not establish MT/FT equivalence, structural incapability of BC,
or paid-acquisition value.

The strongest contradiction is complete even-support competence failure plus zero odd competence
or near-competence. The strongest surviving alternatives are finite-step optimization, raw-feature
conditioning, target/objective misspecification, insufficient five/seven-term span, fold coupling,
fresh-seed instability, common regression difficulty, and an additional odd-to-even penalty.

## Judgment impact

`RECAST` is not supported because no arm reached odd competence or near-competence. `PARK` is
premature because the prospectively defined all-arm-similar predicate is false and one clean,
function-class-preserving conditioning question remains. `CONTINUE` is therefore bounded to one
object, not an open-ended tuning family:

```text
OBJECT_ID=UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01
ARMS=FT-XF-BC-RAW,FT-XF-BC-WHITENED
CHANGED_AXIS=BELLMAN_COMPLETE_COORDINATE_CONDITIONING
```

The treatment uses, separately for each seed/fold/stage, the deterministic positive-diagonal
Cholesky transform

```text
G = X^T X / n
G = L L^T
z_w = L^-1 z
beta_tilde_0 = L^T beta_0
```

using training feature coordinates only. It preserves the same five-term tail and seven-term root
function spans, information, data, folds, target-frozen credit construction, FP32 AdamW exposure,
checkpoint schedule, and evaluator. A non-positive-definite `G` stops the object rather than adding
ridge, truncation, or another repair.

The exact science and implementation contract is
`UCOPE_B_EXPLORE_FT_XF_BC_INVERTIBLE_CONDITIONING_DISCRIMINATOR_R01_PROSPECTIVE_CONTRACT_20260901.md`.
It freezes the three new seeds, paired ancestry, work counts, update-320 competence gate, stable
clear advantage at updates 160 and 320, exact falsifier, historical-artifact firewall,
performance/readiness requirements, and command/effect boundary.

The result falsifies the intervention's sufficiency if the whitened arm is not competent and lacks
a clear paired advantage at both updates 160 and 320. The contrary observation that would support
a later PARK decision is both arms noncompetent in all seeds, neither arm with an odd-competent or
odd-near seed, and no stable clear whitened advantage at 160 and 320. Every valid result still
returns to `em:ucope:convergence`; no lifecycle or successor effect is automatic.

## Claim ceiling and protected non-effects

The ceiling is one preliminary, finite-host, three-seed/two-fold B/EXPLORE conditioning-package
observation. It cannot isolate pure conditioning, optimization, or representation causality or
establish stable superiority, equivalence, seed-population effects, generic UCOPE or paid-information
value, variable-`k`, variable-`N`, MARL/UAV efficacy, transfer, safety, deployment, flight, energy,
or real-world QoS.

```text
UNCHANGED_B1_REPEAT=false
AUDIT_RERUN=false
AUDIT_RETRY=false
ADDITIONAL_B1_OR_AUDIT_SCORE_READ=false
OLD_B1_ATTEMPT_ACCESS=false
CHECKPOINT_SELECTION=false
AUTOMATIC_BUDGET_ENLARGEMENT=false
ACQUISITION_EVALUATION=false
COUNT_RAW_WORK=false
RESULT_EXECUTION_AUTHORITY=NO
PORTFOLIO_PRIORITY_OR_CAPACITY_EFFECT=false
```

## Evidence paths

- `temp/sessions/hmasd-chatgpt-pro-transport/archive/ucope/ucope-em-convergence-20260901-03/RESPONSE.md`
- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_RESULT_EVIDENCE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_CONVERGENCE_DECISION_INTAKE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_A_RECON_B1_ODD_SUPPORT_VS_EVEN_HELDOUT_COMPETENCE_AUDIT_R01_PROSPECTIVE_CONTRACT_20260901.md`
- `docs/research/candidates/ucope/UCOPE_A_RECON_B1_ODD_SUPPORT_VS_EVEN_HELDOUT_COMPETENCE_AUDIT_R01_RESULT_EVIDENCE_20260901.md`
- `docs/research/candidates/ucope/UCOPE_B_EXPLORE_FT_XF_BC_INVERTIBLE_CONDITIONING_DISCRIMINATOR_R01_PROSPECTIVE_CONTRACT_20260901.md`
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`
