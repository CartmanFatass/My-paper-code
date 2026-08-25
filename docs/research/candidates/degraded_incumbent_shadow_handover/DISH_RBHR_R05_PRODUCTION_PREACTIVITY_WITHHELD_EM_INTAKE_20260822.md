# DISH RBHR r05 production preactivity withheld EM intake

```text
document_kind=direction_production_preactivity_withheld_em_intake
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260821-05
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
root_return=docs/session/ROOT_TO_PORTFOLIO_DISH_R05_PRODUCTION_PREACTIVITY_WITHHELD_APPLIED_20260822.md
root_return_sha256=2ea85ff1dad1e03251224f024247b64708438eccd94bc3974ca4577edde84db8
cm_artifact=docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R05_PRODUCTION_PREACTIVITY_ACCEPTANCE_WITHHELD_CM_TECHNICAL_PACKET_20260822.md
cm_artifact_sha256=e21918cca49bbf645d28f1696461fb9da043a54c70511dc78ee339d1bac7faff
cm_technical_acceptance_reperformed=false
technical_disposition=PREACTIVITY_ACCEPTANCE_WITHHELD_NOT_ESTABLISHED
production_acceptance=false
lease_readiness=false
science_bearing_ambiguity=none
science_object_changed=false
empirical_allocation_changed=false
high_gates_changed=false
claim_ceiling_changed=false
portfolio_new_decision_required=false
```

## Conclusion

Accept the stricter Root/CM return as the controlling current engineering
status without redoing CM technical acceptance. Production preactivity is
withheld: all six resource gates are `NOT_ESTABLISHED`, not passed and not
failed. The return establishes no scientific ambiguity and changes no science,
allocation, resource ceiling or claim.

The existing Operational-Root-owned DISH CM should continue the same
unchanged-science repair. No new Portfolio decision is required now.

## Relationship to the preceding EM intake

This artifact supersedes and clarifies
`DISH_RBHR_R05_PREACTIVITY_REPAIR_CONTINUES_EM_INTAKE_20260822.md` for current
gate status, measurement interpretation and production-preactivity acceptance.
It does not erase that historical artifact or invalidate its direction-local
science conclusion.

The earlier intake remains evidence of an intermediate TEST-only engineering
milestone. It is expressly **not** gate acceptance. Its referenced benchmark
is source-stale after later coordinate/reflection edits, and the controlling CM
packet narrows the old figures as follows:

- `183.0503812064 CPUh` excludes rejected candidates and incomplete semantic
  work;
- `30.1571524884 wall-h` applies a training-only speedup rather than measuring
  the full chain;
- `2.5685653687 GiB` is not a concurrent process-group peak; and
- `34.0669612885 GiB` is a synthetic formula, not measured production I/O.

Accordingly, none of those values establishes any resource gate or lease
readiness. The earlier report of passing TEST seams remains an engineering
fact only; the latest source compiling, ABI-loading and smoking is likewise not
production acceptance.

## Accepted current engineering facts

The exact CM packet establishes that TEST-only component seams execute, while
the complete production runner is not technically accepted. The accepted-tape
generator/scanner and exact 20-tick/dual-50-tick scripts; full protocol,
lineage, CAS and certificate application; REAL/SHAM recurrent promotion and
telemetry; five-arm trainer with complete auxiliaries and replay; the complete
6,990-estimand mapper; failure-atomic lifecycle; concurrent RSS; full-chain
wall scaling; and actual production serialization/resume/I/O measurement all
remain unestablished. Shared registry binding properly waits for candidate
acceptance.

All six gates are therefore exactly:

```text
cpu_core_hours_le_560=NOT_ESTABLISHED
wall_hours_le_110=NOT_ESTABLISHED
aggregate_rss_gib_le_40=NOT_ESTABLISHED
scratch_gib_le_120=NOT_ESTABLISHED
durable_gib_le_16=NOT_ESTABLISHED
total_read_write_gib_le_400=NOT_ESTABLISHED
```

The future-master rejected-candidate count remains unknown. CM states that
preactivity can establish a compliant projection using TEST masters and the
exact generator/scanner; the present absence of that evidence is not an
intrinsic infeasibility result.

No scientific master, identity, coordinate, scientific model/checkpoint,
production training/evaluation, lease, provider action, result, empirical
activity or Git action occurred.

## Scientific intake and continuation

The missing surfaces are implementation-conformance, resource-measurement and
result-integrity requirements for the already byte-frozen composite. They do
not require choosing or changing any treatment, comparator, observable,
schedule, RNG law, endpoint, inference member, branch or claim. Therefore:

```text
science_revision=DISH-RBHR-SCIENCE-20260821-05 unchanged
pro_disposition=CLOSED unchanged
empirical_allocation=INVEST_FULL_EMPIRICAL_CONSTRUCTION_AND_COMPLETE_PANEL unchanged
panel_shrink_or_search=forbidden
partial_interpretation=forbidden
```

The high limits remain `560 CPU core-hours`, `110 wall-hours`, `40 GiB`
aggregate RSS, `120 GiB` scratch, `16 GiB` durable storage and `400 GiB` total
read/write I/O. Their status is unestablished; their values are not revised.

The claim ceiling remains finite-budget, host-specific evidence for the frozen
two-UAV first-handover package in passing registered fixed/held-out/switched-
`k` package/schedule/stratum cells. It does not support arbitrary `k`, variable
`N`, unique mediation, other physics, safety, certification, deployment or
flight claims.

Same-CM unchanged-science continuation is correct. The return boundary remains
a corrected complete preactivity acceptance within every existing gate, a
material gate expansion, an actual science-bearing ambiguity or a genuine
cross-scope conflict. No master, coordinate or lease precedes acceptance.

```text
applies_to=Current technical and scientific interpretation of DISH r05 production preactivity
does_not_imply=science revision|r06|allocation change|direction stop|new provider turn|new CM|master|coordinate|identity|model|checkpoint|lease|training|evaluation|empirical activity|result|panel shrink|search|partial interpretation|deployment|flight|Git
continuation_owner=Existing Operational-Root-owned DISH CM for unchanged-science repair; Portfolio-owned DISH EM only upon an exact relayed science ambiguity or accepted technical/result return
root_decision_class=none; current allocation, high limits, claim ceiling and same-CM continuation remain in force
```

This intake authorizes no action.
