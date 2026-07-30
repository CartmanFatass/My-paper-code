# External Pro: UAV G0 source-identifiability design assertion audit

semantic_author=research_operations_manager
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260729_uav_source_identifiability_g0_design_assertion_audit
source_commit=0b27630
compute_budget=zero
scientific_iteration_cost=zero

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded design review. Read only the allow-listed paths in
`01_SHARED_SOURCE_MANIFEST.md` from the pushed stage commit. The user has
explicitly authorized one transport of this independent UAV review. Do not
start experiments, formal execution, code changes, or paper acceptance.

Exact evidence allow-list (read only these repository-relative paths at the
stage commit):

- `docs/research/designs/UAV_DYNAMIC_SERVICE_ROSTER_RESEARCH_BRIEF.md`
- `docs/research/designs/UAV_TEMPORARY_SERVICE_LOSS_G1.md`
- `docs/external-review/independent/20260729_dynamic_roster_uav_paper_readiness_external_review_v1/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/30_PM_SCIENTIFIC_RECONCILIATION.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`

The project-manager summary supplied to this review is: the toy chain has a
compact candidate mechanism, but whether the paper can stand depends first on
G0, not on further toy ablations. Treat that summary as a proposal to audit,
not as an accepted scientific conclusion.

Decide whether the next correct boundary is a minimal UAV
`SOURCE_IDENTIFIABILITY_G0` design audit. If it is, freeze the smallest
executable contract that tests both (a) physical/service-task feasibility and
(b) causal necessity of roster-triggered reallocation. The contract must
separate physical fleet slots from service-active roster membership and must
specify fair information for an oracle/constructive controller, a
same-information constructive controller when applicable, and a
ledger-blind/no-reallocation control. Preserve paired physical and disturbance
randomness, source feasibility, access/utility, ownership/permutation
certificates, and result-sensitive gates. Explain what must be held out and
what claims remain excluded.

Required response sections and exact disposition token:

1. `G0_DESIGN_CONFORMANCE`
2. `G0_SCIENTIFIC_BOUNDARY`
3. `G0_MINIMUM_EXECUTABLE_CONTRACT`
4. `G0_COUNTEREXAMPLES_AND_CLAIM_LIMITS`
5. `G0_EVIDENCE_AND_FIRST_MATCH_GATES`
6. `G0_NEXT_BOUNDARY`
7. `G0_DESIGN_DISPOSITION`

Return exactly one final token in section 7:

- `G0_DESIGN_DISPOSITION=PROCEED_TO_UAV_G0_SOURCE_IDENTIFIABILITY`
- `G0_DESIGN_DISPOSITION=REVISE_G0_CONTRACT`
- `G0_DESIGN_DISPOSITION=CLOSE_UAV_SOURCE`

If the disposition is `REVISE_G0_CONTRACT`, name only the concrete missing or
conflicting scientific field; do not propose code. If it is
`PROCEED_TO_UAV_G0_SOURCE_IDENTIFIABILITY`, state the smallest next design or
implementation question without authorizing compute. Do not select G33 and do
not consume an iteration.
