---
name: hmasd-explorer-project-validation
description: Use for the Explorer-to-project toy-validation bridge: build or check one advisory candidate packet, then keep CPM-owned Pro and compute routing inside the frozen grant.
---

# Explorer project validation

This Skill is the mechanical boundary for the Explorer-to-project toy lane and
its CPM-centered lane and routing.
It creates no project state and grants no compute, code, scientific, or current-
work authority. CPM submits one ordered manifest of currently frozen questions
to the dedicated Agentify task, continues unrelated work, and later accepts one
batch result; transport details do not enter CPM context.

The packet is an `EXPLORER_PROJECT_CANDIDATE_PACKET` with
`document_kind=explorer_project_candidate_packet_v1`. It is advisory input only:
one candidate is selected for each Pro package, and a package never selects
multiple directions. The design request is
`EXPLORER_TOY_DESIGN_ASSERTION_AUDIT`; after an authorized toy run, the
scientific disposition label is `EXPLORER_TOY_RESULT_SCIENTIFIC_DISPOSITION`.
The intake completion marker remains `OPS_IDENTITY_INTAKE_ONLY`. If CPM lacks
a separate toy-compute grant, its workflow state stops at
`AWAITING_TOY_COMPUTE_GRANT`; that state is not stored in the Explorer packet.

The packet's canonical v1 fields are `workflow_id`,
`user_authorization_reference`, `evidence_tier=nonformal_toy`, `origin_campaign`,
`cohort`, `candidate`, `review_request`, `authority`, and `completion`.
`origin_campaign` binds `campaign_id`, `campaign_workflow_commit`, and one
repository-relative artifact path. `cohort.ordered_candidate_ids` is unique and
`cohort.current_index` identifies the one `candidate.id` under review.
For `EXPLORER-TOY-VALIDATION-2026-07-31-P1`, the script accepts only the frozen
ordered queue `CAND-VAP-FOLR-CORE|CAND-VSP-02|CAND-VSP-05`.
`review_request.candidate_count` is `1`, `cross_direction_competition` and
`combined_toy` are false, and every authority value is the exact string
`none` (`scientific_authority`, `code_authority`, `compute_authority`, and
`project_state_effect`).

Use the adjacent `scripts/explorer_project_packet.py` only with its `build` and
`check` commands. It reads packet/artifact files and emits JSON to stdout; it
never writes files, messages, Git state, browser state, runtime state, or
project state. All referenced files are repository-relative regular files under
`local_research`, outside `local_research/pro_reviews`, with no traversal or
symlink/reparse escape. Build and check directly re-read each referenced regular
file. Artifact identity is its safe path, not content metadata.

`EXPLORER_ADVISORY_REFINEMENT_PACKET` is an optional Skill-level packet used
only when Pro explicitly requests a gap; v1's mechanical script does not
broaden into a refinement dispatcher or transition engine.

## CPM coordination

CPM checks one candidate packet, independently verifies its live user
authorization reference, and packages only that candidate for the dedicated
Explorer-validation Pro conversation. The same conversation is reused
sequentially with one candidate per turn; candidate turns are neither combined
nor concurrent. The packet is an identity envelope, so
the Pro package also includes the CPM-authored question, allow-list and
named candidate evidence. `TOY_CONTRACT_FROZEN` permits one complete CPM code
assignment; `ADVISORY_REFINEMENT_REQUIRED` permits one exact Explorer
refinement request; `PARK_CANDIDATE` advances the scheduling-only queue.

After `CODE_ACCEPTED` and code-science alignment, CPM stops at
`AWAITING_TOY_COMPUTE_GRANT` unless the user has frozen a toy-compute grant.
Inside that grant, CPM owns runtime dispatch and recovery. It routes a
mechanically valid isolated result to
`EXPLORER_TOY_RESULT_SCIENTIFIC_DISPOSITION`: `CONTINUE_CANDIDATE` retains the
current candidate, while `PARK_CANDIDATE` or `COMPLETE_CANDIDATE` advances the
queue. Explorer packet or candidate-artifact nonconformance returns to Explorer
through CPM. Accepted implementation or frozen runtime-interface defects
go to CPM, scientific questions go to the dedicated Pro conversation, and
contract, packet-validator or routing defects go to Workflow Design Manager. Shared
harness code may be reused; candidate roots, artifacts and result evidence may
not.

All evidence and dispositions in this lane are scoped to the frozen
`nonformal_toy` estimand. They consume no formal-project iteration and do not update the CDC portfolio.
They cannot establish a formal project claim or authorize promotion. Promotion,
if later requested, is a separate explicit project-science boundary.

```text
formal=false
current_work_mutation=forbidden
```
