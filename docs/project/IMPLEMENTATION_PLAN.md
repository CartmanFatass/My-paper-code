# UAV dynamic-service-roster research plan

> **Current procedure:** external scientific review through
> `$hmasd-review-round`. Implementation later uses
> `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work and workflow hashes remain disabled.

```text
active_boundary=UAV_DYNAMIC_SERVICE_ROSTER_EXTERNAL_PRO_REVIEW
implementation_status=NOT_STARTED_REVIEW_PENDING
design=docs/research/designs/UAV_DYNAMIC_SERVICE_ROSTER_RESEARCH_BRIEF.md
backend=cpu
torch_threads=1
new_chain_iterations_remaining=10
iteration_report_range=ITERATION_18_to_ITERATION_27
```

## Goal

Turn the accepted synthetic runtime-variable-roster algorithm into an
algorithmically meaningful UAV test line based on Scenario 7. The line must
separate a fixed physical fleet from the service-active roster and test:

1. temporary coverage under a localized communication-demand burst;
2. service-roster contraction and re-entry caused by charging rotation; and
3. robustness to a small temporary UAV detachment or failure.

The initial goal is a usable algorithm in this task family, not a universal or
comparative-advantage claim.

## Repository facts that constrain the review

- `S7-S1` has eight UAVs, thirty users, a 500-step episode and a constant
  per-user QoS target. Batteries, charging and failures are disabled.
- S7-S2/S3 add battery and two single-capacity chargers. S7-S4 adds temporary
  failures while retaining at least six active UAVs.
- The environment and adapter expose a fixed `possible_agents` array. Charging
  and failure are currently physical availability masks, not registered
  dynamic service-membership events.
- The accepted G8 algorithm is supported only in its synthetic dynamic-roster
  family. UAV integration and UAV advantage remain untested.

## Review boundary

External Pro is asked to freeze only choices that change the scientific
object: service-membership semantics, disturbance/source laws, observability,
estimands, matched reductions, admission gates and held-out claims. Seeds,
serialization, class layout and other bounded realization choices remain PM
implementation authority unless they alter one of those objects.

No UAV source code is changed before exact raw intake and PM reconciliation.
The first post-review action will be the smallest one-source executable
definition that separates dynamic-service-roster behavior from a fixed-agent
masking reduction. Scenario composition follows only after isolated sources
are individually identifiable.

## Ten-iteration loop

For each valid conclusion-bearing iteration the Project Manager will:

1. freeze one bounded evidence contract inside the external scientific scope;
2. implement and run proof-sized nonformal acceptance;
3. commit the accepted source and launch the registered CPU-only formal run;
4. validate the first-match result without threshold or budget rescue;
5. write the Chinese `docs/report/ITERATION_<n>.md`; and
6. select the smallest supported successor without another authorization
   prompt while the ten-iteration grant remains active.

External review is requested again only for a new protected scientific choice
or a real anomaly, not as a routine review stack.
