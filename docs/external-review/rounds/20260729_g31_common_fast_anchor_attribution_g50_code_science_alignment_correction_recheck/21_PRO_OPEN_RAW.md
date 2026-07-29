FROZEN_ASSERTION

The frozen priority-2 outcome must be selected whenever the package is operationally valid and either:

source_valid=false

or:

reference_access_pass=false

A merely non-confident reference failure is still a reference-access failure. reference_access_confident_fail is not the branch predicate; confidence-qualified failure is used for the null as one route to the reference-advantage branch. The result contract states that any reference absolute-access failure has precedence over both conclusion-bearing comparison branches. The inherited G48 design likewise gives reference access failure precedence while reserving confident null failure for the advantage predicate.

CONFLICTING_PATH_AND_BEHAVIOR

The target’s select_g50_result_branch implements priority 2 as:

Python
Run
if not bool(metrics["source_valid"]) or bool(
    metrics["reference_access_confident_fail"]
):
    return SOURCE_FAILURE_BRANCH

It does not branch on not reference_access_pass. The later sufficiency and advantage predicates both require reference_access_pass=true; therefore an ordinary, non-confident reference-access failure bypasses priority 2 and falls through to:

MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50

instead of:

SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50

Concrete target-bound witness:

operational_valid=true
source_valid=true

reference_access_pass=false
reference_access_confident_fail=false

null_access_pass=true
null_access_confident_fail=false

fresh_single_immediate_noninferior=false
material_common_fast_anchor_advantage=false

Frozen result:

SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50

Target result:

MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50

The existing synthetic priority-2 witness changes only source_valid=false; it does not test reference_access_pass=false with reference_access_confident_fail=false, so the wrong mechanism can pass the focused branch tests.

SMALLEST_IN_CONTRACT_CORRECTION

Change only the priority-2 selector predicate to:

Python
Run
if (
    not bool(metrics["source_valid"])
    or not bool(metrics["reference_access_pass"])
):
    return SOURCE_FAILURE_BRANCH

Retain reference_access_confident_fail as a diagnostic consistency field. Do not use it as a substitute for reference_access_pass in priority 2.

Keep the null-side advantage predicate unchanged:

reference_access_pass
and (
    null_access_confident_fail
    or material_common_fast_anchor_advantage
)

Add one focused first-match witness with:

reference_access_pass=false
reference_access_confident_fail=false

and require SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50. Also require this branch to retain precedence even if a stored comparative Boolean is favorable.

No phase-A objective, baseline-shadow treatment, activation threshold, source, seed, optimizer exposure, evidence volume, confidence procedure, checkpoint schema, formal token or admission boundary needs modification.

AUDIT_DISPOSITION=MISMATCH