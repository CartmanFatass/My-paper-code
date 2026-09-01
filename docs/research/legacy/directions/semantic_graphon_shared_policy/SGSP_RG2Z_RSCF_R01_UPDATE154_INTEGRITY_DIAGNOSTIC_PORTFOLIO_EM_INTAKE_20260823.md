# SGSP RSCF-r01 update-154 integrity diagnostic — Portfolio EM intake

```text
artifact_kind=SAME_DIRECTION_PORTFOLIO_EM_TECHNICAL_INTAKE
direction_id=semantic_graphon_shared_policy
exact_object_revision=SGSP-RG2Z-RSCF-SCIENCE-20260821-01|SGSP-RG2Z-RSCF-R01-RUNNER-AND-GATE-B-CONFORMANCE
source_cm=temp/handoffs/code_manager_to_root/SGSP_RG2Z_RSCF_R01_UPDATE154_INTEGRITY_DIAGNOSTIC_AND_REPAIR_COST_CM_RETURN_20260823.md
source_cm_sha256=7071e310e42c7ae23e24dbbeef75991d72ada1b881da2f5846321c982f78fef1
scientific_result=NONE
question_relevant_output=NONE
partial_value_exposed=false
```

## Intake

The exact terminal cause is a shared in-memory Torch/native conformance audit,
not a torn update, retained-state corruption, serialization failure or
durability failure. Both arms raised the composite
`AUTOGRAD_OR_NATIVE_REPLAY` family at attempted update index 154. Blinded
generation 154—representing successful updates 0 through 153—remains an
integrity-valid forensic/rollback boundary; generation 155, the sole update-512
checkpoint and a complete result do not exist.

The same-direction science inherits the r03 numeric training contract and
changes only the two RSCF scientific replacements named in the r01 card. The
technical diagnostic finds a cross-precision implementation seam: Torch FP32
actor parameters enter NumPy FP64, while the native host performs logits,
softmax, recurrence and sampling in C++ `double`. The surviving failing leaf is
action replay identity and/or probability error at the `2e-5` conformance
tolerance. This is an engineering-conformance candidate, not evidence for or
against PHY-TRUST, EDGE-FLEX, variable-N value or the registered claim.

Repairing or merely instrumenting the accepted production package changes its
source-binding digest. The active `ProductionIdentity` and resume state bind
the old digest and current restore law rejects repaired bytes. The current
Portfolio objective separately requires every frozen identity, coordinate and
frontier to remain unchanged. Therefore neither a source-binding alias,
identity migration, fresh empirical identity nor restart is admissible now.

## Portfolio direction boundary

```text
current_object=EMPIRICALLY_ALLOCATED|FORMAL_ACTIVITY_CROSSED|NO_COMPLETE_RESULT
latest_valid_frontier=BLINDED_GENERATION154|PRESERVE_UNOPENED
current_engineering=NO_CURRENT
current_empirical_activity=NONE
repair_release=NONE
resume_or_rerun=NONE
lease=ONE_DISPATCH_EXERCISED_AND_CONSUMED|NO_REUSE
heartbeat=PAUSED_NO_ACTIVE_LONG_OPERATOR
reason=REPAIRED_BYTES_CANNOT_BIND_CURRENT_PRODUCTION_IDENTITY_UNDER_CURRENT_CONTRACT|FROZEN_IDENTITY_CHANGE_FORBIDDEN
science_disposition=NO_POSITIVE_OR_NEGATIVE_RESULT|DIRECTION_NOT_REJECTED_OR_RETIRED
current_cut=EMPIRICAL_4|ENABLING_CONSTRUCTION_0|DEFINITION_ONLY_0|UAV_EMPIRICAL_1|UNCHANGED
```

A future revisit requires an explicit owner decision that permits either a
meaning-preserving source-binding compatibility mechanism or a fresh empirical
identity. Before any future production-capable revision is accepted, it must
use `HMASD-MARL-SANCHECK-V1`: current-file C++/batch/parallel evidence, FP32
hot-path conformance, no proof-grade numerical lane, and—for a toy
classification—a complete-plan projection no greater than 1800 seconds. Any
science-bearing numeric or identity revision additionally requires a complete
same-direction revision and same-Pro closure. None is opened by this intake.

RISP, RCLE and DISH are unchanged. No source, build, test, benchmark, runtime,
CM, Implementer, Reviewer, Operator, lease, identity, coordinate, frontier,
result, partial-value, provider or Git action is authorized.
