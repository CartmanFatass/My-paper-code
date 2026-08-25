# Shared source manifest

semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
repair_owner=project_manager

round=20260722_ehc_g1_source_contract_pm_owned
pm_authoring_source_commit=62369001ecc99ec77893ee8a5c39936585f94637
review_mode=focused_external_pro_clarification
formal_compute_status=unauthorized

## Scientific evidence

| Path | Authority and use |
| --- | --- |
| `docs/project/ALGORITHM_PRINCIPLES.md` | Durable scientific and result-semantics constraints. |
| `docs/external-review/OPEN_REVIEW_PRINCIPLES.md` | External Pro reasoning and response responsibilities. |
| `docs/external-review/rounds/20260722_ehc_formal_result_review/21_PRO_OPEN_RAW.md` | Sole scientific authority for G0's result meaning, four live explanations, and the selected independent G1 evidence direction. |

## Accepted provenance and active-boundary evidence

These files establish workflow state and adoption provenance. They do not
override or replace the external Pro raw as scientific authority.

| Path | Authority and use |
| --- | --- |
| `docs/external-review/rounds/20260722_ehc_formal_result_review/30_EVIDENCE_RECONCILIATION.md` | Accepted provenance record connecting the raw response to the active G1 label. |
| `docs/external-review/rounds/20260722_ehc_formal_result_review/50_DISPOSITION.md` | Accepted control boundary: four iterations remain and formal iteration-2 compute is unauthorized. |
| `docs/project/CURRENT_WORK.md` | Current active boundary, closed G0 status, CPU execution condition, and PM-owned replacement-package requirement. |

## Ownership and execution-boundary evidence

These files govern authorship, routing, and later realization. They are not
scientific evidence for selecting a task.

| Path | Authority and use |
| --- | --- |
| `AGENTS.md` | Controller/Project Manager semantic ownership and write-lease boundary. |
| `docs/project/AGENT_CONTEXT.md` | PM code-side ownership and registered CPU/one-thread execution constraints. |
| `.agents/skills/hmasd-dispatch-task/SKILL.md` | Live role resolution, source-boundary, terminal-delivery, and no-Controller-rewrite contract. |
| `.agents/skills/hmasd-review-round/SKILL.md` | PM-authored review package and external-Pro-only scientific disposition contract. |

## Reviewer-visible PM artifacts in this round

| Path | Purpose |
| --- | --- |
| `docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/00_REVIEW_BRIEF.md` | Accepted facts, frozen skeleton, exact gap, and prohibited scope. |
| `docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/01_SHARED_SOURCE_MANIFEST.md` | This evidence and authority manifest. |
| `docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/10_PM_CODE_SIDE_GAP.md` | Executable dependency map and non-selecting source-family option set. |
| `docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/20_PRO_OPEN_QUESTION.md` | Exact focused question for external Pro. |
| `docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/21_PRO_OPEN_RAW.md` | Transport destination; currently a non-scientific placeholder. |

## Excluded material

- No internal PM audit, callback, task transcript, scratch note, or work log is
  reviewer evidence.
- No file under
  `docs/external-review/rounds/20260722_ehc_g1_source_contract/` is an input.
- The G0 runtime log root is not needed to decide this prospective source
  contract; its accepted result meaning comes from the listed raw and
  provenance records.

The Controller must bind the eventual review to a pushed 40-character stage
commit and verify Git visibility before transport. That later mechanical action
does not change this manifest's semantics.
