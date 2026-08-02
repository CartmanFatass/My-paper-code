# Explorer-Origin Project Toy Validation Workflow

This contract defines the narrow bridge from advisory Independent Research
Explorer output to one project toy-validation candidate. It does not promote
advisory research into canonical science and does not grant compute.

## Authority and isolation

The Independent Research Explorer is advisory only. It emits typed packets and
may preserve multiple directions, but it cannot contact External Pro, select a
project direction, assign code, authorize compute, or make a result disposition.
Code Project Manager is the exclusive project coordinator: it validates packet
identity, freezes one exact review assignment, owns transport and grant checks,
routes runtime outcomes, and records candidate-local terminal receipts.
External Pro freezes the scientific contract and owns the scoped scientific
disposition. Code Project Manager owns code realization and technical
acceptance, but begins code only after External Pro freezes the science and
never reads `local_research/`. Workflow
Design Manager owns defects in this workflow contract.

Shared harness code may be reused. Candidate evidence, run roots, artifacts and
results must remain candidate-specific and isolated; harness reuse is never
evidence reuse.

This lane is also isolated from the active formal-research grant and CDC
portfolio. Its `nonformal_toy` results consume no formal iteration and cannot
support a formal project claim. A candidate's toy completion does not promote
it into canonical project science; any later promotion needs a separate
explicit project-science boundary.

```text
formal=false
current_work_mutation=forbidden
```

## Typed Explorer packets

The candidate packet is exactly one `EXPLORER_PROJECT_CANDIDATE_PACKET` with
`document_kind=explorer_project_candidate_packet_v1` and `packet_version=1`.
Its required top-level fields are:

```text
workflow_id
user_authorization_reference
evidence_tier=nonformal_toy
origin_campaign={campaign_id,campaign_workflow_commit,artifact:{path,bytes,sha256}}
cohort={ordered_candidate_ids,current_index}
candidate={id,artifact:{path,bytes,sha256}}
review_request={mode:EXPLORER_TOY_DESIGN_ASSERTION_AUDIT,candidate_count:1,cross_direction_competition:false,combined_toy:false}
authority={scientific_authority:none,code_authority:none,compute_authority:none,project_state_effect:none}
completion=OPS_IDENTITY_INTAKE_ONLY
```

`candidate_count` is always one. `cohort.ordered_candidate_ids` preserves the
whole multi-direction portfolio; it is not a ranking or a competition. The
Explorer packet is advisory evidence for CPM intake, not an authority to
mutate project state. CPM validates the packet and independently
checks the user-authorization fact; the packet cannot assert that fact.

An optional, separate `EXPLORER_ADVISORY_REFINEMENT_PACKET` may be emitted only
after CPM returns an exact External Pro advisory gap. It is
bound to the same `workflow_id`, campaign and candidate, names the exact gap,
and carries only an advisory refinement. It cannot alter the candidate identity,
grant authority, queue order, science ownership or compute gate, and it is never
sent directly from Explorer to Pro.

## CPM-centered sequence

1. CPM performs identity intake on one candidate packet and preserves all
   directions. It packages one candidate per Pro review.
2. CPM preserves `cohort.ordered_candidate_ids` as the scheduling queue.
   For `EXPLORER-TOY-VALIDATION-2026-07-31-P1`, the exact order is
   `CAND-VAP-FOLR-CORE`, then `CAND-VSP-02`, then `CAND-VSP-05`. This is
   scheduling only; it does not compare, retire or invalidate directions.
3. CPM sends the question directly with Agentify, waits for the response and
   archives it before intake. Exactly one candidate is included in each Pro
   turn; candidates are never combined and reviews are never concurrent.
4. External Pro receives `EXPLORER_TOY_DESIGN_ASSERTION_AUDIT`, judges the
   candidate's estimand, mechanism, controls and minimum toy validation, and
   returns exactly `TOY_CONTRACT_FROZEN`, `ADVISORY_REFINEMENT_REQUIRED` with
   one exact gap, or `PARK_CANDIDATE`. Only the first freezes science. For the
   second, CPM forwards the exact gap; Explorer independently decides any
   refinement inside its user-authorized research workflow.
   Explorer refinement is not a new candidate and cannot bypass Pro's explicit
   gap.
5. Only after the Pro freeze may CPM begin the complete code assignment. CPM
   accepts no partial, Explorer-only or unfrozen
   assignment and never reads `local_research/`.
6. No compute starts until the user grants it explicitly. Without that grant,
   the current flow terminates at `AWAITING_TOY_COMPUTE_GRANT`.
7. After an explicit grant, CPM routes every authorized step
   automatically inside the frozen grant. Mechanical outcomes remain isolated
   to the candidate and are classified before routing.
8. A mechanically valid toy result is sent through
   `EXPLORER_TOY_RESULT_SCIENTIFIC_DISPOSITION` on the dedicated conversation.
   External Pro owns the disposition, preserves all supported live or parked
   directions, and returns exactly `CONTINUE_CANDIDATE`, `PARK_CANDIDATE` or
   `COMPLETE_CANDIDATE`. CPM retains the current candidate only for
   `CONTINUE_CANDIDATE`; the other two advance the scheduling-only queue.

## Failure ownership and stop conditions

| Failure | Owner | Boundary |
| --- | --- | --- |
| transport, identity, grant, run routing, archival or other operational failure | Code Project Manager | recover within the frozen boundary or stop operationally |
| Explorer packet or candidate-artifact nonconformance | Independent Research Explorer after an exact CPM mechanical return | correct only the advisory packet or named source artifact |
| accepted implementation or frozen runtime-interface defect | Code Project Manager | diagnose and technically accept code only after the complete frozen assignment |
| estimand, controls, mechanism, sufficiency or result meaning | External Pro | freeze or dispose science; never accept code or authorize compute |
| contract, packet-validator or workflow-routing defect | Workflow Design Manager | revise workflow design only |

An absent compute grant is not an operational failure and is not a Pro choice:
the required stop is `AWAITING_TOY_COMPUTE_GRANT`. A later explicit grant starts
the frozen sequence; it does not broaden scope, reorder the queue or erase
candidate isolation.
