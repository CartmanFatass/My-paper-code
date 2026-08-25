# SGSP RSCF static full-cost assessment handoff

```text
direction_id=semantic_graphon_shared_policy
logical_identity=EM-semantic_graphon_shared_policy
generation=1
assignment_id=PortfolioLegacyCorrection-SGSP-20260825
artifact_role=local_reconciliation_and_static_full_cost_engineering_request
lifecycle_decision=Legacy-state correction and Portfolio expansion — 2026-08-25T11:50:42Z
original_activation_snapshot_sha256=9ebacd188f15e273111fc47d90389aec3e4a2988c8e51c51ed5769024bfada47
current_lifecycle_decision_ref_sha256=7d5353ab63a8ead4f90f6cb565df9620f68fb605d27150e2e8315c6ec49df86a
current_portfolio_sha256=7d5353ab63a8ead4f90f6cb565df9620f68fb605d27150e2e8315c6ec49df86a
registry_revision=9
registry_sha256=d02edd6b91c1fb103964f1f5b5a72c5f4d1fb0c0a651ba7b792bb2d1f2d685ee
frozen_question_sha256=70b2ed242ca4fcee5c54c00e814d336cbccc945a45252278093e4955f98d52cf
frozen_evidence_set_sha256=6b7c08b8b459e644467a4e6fe827f098717d8049acdea0da3b6dab064c21186e
external_review_performed=false
provider_operation_created=false
cm_dispatched=false
source_or_test_effect=false
scientific_activity_started=false
empirical_coordinates_bound=false
construction_selected=false
construction_authorized=false
compute_authorized=false
```

## Frozen authority and lifecycle reconciliation

| Reference | SHA-256 / revision |
| --- | --- |
| `docs/research/portfolio/PORTFOLIO.md` | `7d5353ab63a8ead4f90f6cb565df9620f68fb605d27150e2e8315c6ec49df86a` |
| `docs/research/portfolio/workflow/registry.json` | `d02edd6b91c1fb103964f1f5b5a72c5f4d1fb0c0a651ba7b792bb2d1f2d685ee` / revision 9 |
| `docs/research/candidates/semantic_graphon_shared_policy/DIRECTION.md` | `2fb5239b02eff2ca71421a44612ceac3539c3e0638c7fa9adeccb763e09fdb78` |
| `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_ROLE_SAMPLED_CF_R01_SCIENCE_CARD.md` | `1af5b6add80af436ab7c2ecc334673f15cbddae3d18e2ac6fe7b726e8b97eaa4` |
| `docs/research/candidates/semantic_graphon_shared_policy/workflow/research/state.json` assignment input | `5406ee2251642ba68f994e029d4e84ef209708856f65ed3e63adfba879445e73` / revision 1, schema 1 |
| `docs/research/candidates/semantic_graphon_shared_policy/workflow/research/state.json` after compatible routing migration and before this content transition | `ad0e4a74415e2f7425514e65578a358ab9ab33ec4856df915ffcc775da9006ec` / revision 2, schema 2 |
| `docs/research/candidates/semantic_graphon_shared_policy/workflow/research/state.json` after the first content transition and before current-registry reconciliation | `d480f164fb50bb8f7952d555c1ea805f365b888f456d9b7e06706ea6616b3c56` / revision 3, schema 2 |
| `docs/research/candidates/semantic_graphon_shared_policy/workflow/external-review/index.json` | `2574d62e5712580f4c6d625cb0eee5531cabd775374b27ba0e43d1f39f74fce2` / revision 1 |
| `docs/research/candidates/semantic_graphon_shared_policy/workflow/engineering/state.json` | `24fe82913c1c159b443a3a5ca1be28d049d36e582d82d9e05b759075c580229f` / revision 2, schema 2, unchanged by this EM |

The registry identity, paths, and generation match this assignment. Registry
revision 9 keeps the direction `ACTIVE`; the lifecycle decision still names
the revision-6 legacy-state correction and now binds the exact current
Portfolio checkpoint containing that section. The current Portfolio also
retires `PARKED` as a current lifecycle and freezes deterministic cross-role
ownership. The `RESOURCE_WAIT`
label in `DIRECTION.md` and `RESEARCH_MAP.md` is historical provenance, not the
current lifecycle and not a resource veto. A missing cost estimate is queued
preparation work for an `ACTIVE` direction, not a reason to suppress it. The
direction authority remains unchanged and continues to point to the RSCF card
as its candidate evidence.

The assignment-input research state revision 1 is internally consistent but
predates the current lifecycle decision: it records `registry_revision_seen=1`,
`phase=IDLE`, and no engineering request. During this cycle Root applied the
compatible route-owner schema migration, producing revision 2/schema 2 with
those scientific and lifecycle fields unchanged and `next_action.owner=ROOT`.
The first content transition preserved that migration and produced revision 3
against registry revision 8. Concurrent current-reference normalization then
advanced the registry to revision 9 without changing the Portfolio bytes,
direction lifecycle, or request boundary; the final state transition reconciles
that exact checkpoint. The external-review index remains revision 1 with no workflow
rounds. The engineering state is revision 2/schema 2 and remains
`UNREQUESTED`; this EM does not mutate it. No provider operation or archive
exists to add to the external index in this cycle.

The RSCF card records
`mathematical_closure=complete_same_conversation_ChatGPT_External_Pro_CLOSED`
and `em_intake=accepted_closed`. It later states that the same-conversation Pro
disposition was `CLOSED` with zero science-bearing defects and that the EM
accepted it while the object remained preactivity. That is accepted
mathematical/scientific closure of the frozen definition. It is not acceptance
of a cost estimate, construction feasibility, a construction choice, a lease,
or empirical activity. The card and Portfolio record the closure as authority
facts; this cycle does not manufacture an external-review receipt absent from
the revision-1 external index.

The same card makes a named same-direction CM static full-cost assessment a
prerequisite to any later Portfolio construction decision. Portfolio therefore
opens one preparation boundary only: author this durable request for Root. The
current cross-role routing is preserved: this EM owns the reconciliation and
request; Root may later route the implementation/engineering assessment to the
CM authority. This EM does not dispatch that CM.

## Static comparison references

The frozen research question and evidence-set hashes above do not change. The
following existing documents are named only as static provenance and comparison
references; they are not new empirical evidence and do not expand the scientific
question:

| Reference | SHA-256 | Permitted use |
| --- | --- | --- |
| `docs/research/RESEARCH_MAP.md` | `8c2db819f73999775aaee740c0868790a8aef9b058154601f731db5e78829cbf` | Historical `RESOURCE_WAIT` row and current-position provenance only. |
| `docs/research/candidates/semantic_graphon_shared_policy/SGSP_RG2Z_COUNTERFACTUAL_CREDIT_ASSIGNMENT_R01_SCIENCE_CARD.md` | `1fd0a7446365f109b94ae2ec1761656b7b99c8127df3ea103388ff1ca7e38dcb` | Definition-only CCA logical-work comparator named by the RSCF card; no CCA execution, result, or empirical evidence. |

## Evidence separation

### Repository facts

1. The RSCF definition preserves the frozen scientific task and changes the
   actor-credit law to exactly one selected origin per public role and factual
   episode, with all legal unilateral current actions evaluated through the
   full remaining horizon on a common future tape.
2. The card freezes `15,728,640` all-legal Q entries, `11,010,048` new
   alternative continuations, `91,471,872` total base-plus-branch-plus-evaluation
   environment slots, `966,647,808` learned decisions, and `24,576` full-batch
   backward calls for the complete prospective RSCF object.
3. Relative to the complete unexecuted CCA definition, the card records exactly
   `48x` fewer Q entries and alternative continuations, approximately `37.77x`
   fewer total environment slots, and approximately `38.59x` fewer learned
   decisions. It explicitly says this adds no CCA empirical evidence and is not
   a cheaper execution of CCA.
4. The full prospective cost categories named by the card are snapshot/restore
   and closed-loop branch construction; stopped-target/loss integration;
   selector, coupling, no-leakage, and atomic audits;
   runner/frontier/certificate work; streaming/batching and exact-cache
   engineering; CPU/GPU characterization; complete construction and test
   workdays; CPU/accelerator/host hours; elapsed time by safe concurrency; peak
   RAM/VRAM; scratch and retained storage; and opportunity cost.
5. The card labels `100--500` CPU core-hours and `18--30` CM workdays as
   advisory pre-CM planning only. It explicitly says those figures are not
   accepted estimates, a benchmark, a lease request, or empirical authority.
6. Static symbolic reasoning and CM read-only feasibility, observability, and
   cost analysis are preactivity. Scientific activity begins at the earliest
   materialization, generation, inspection, summary, or use of a new selector
   or master word, numeric seed, initialization, task event, detection, packet,
   action uniform, branch, Q entry, policy output, model, checkpoint, or
   endpoint.
7. Neither the card, its accepted closure, this handoff, nor a later complete
   static packet authorizes source, build, test, probe, benchmark, stochastic
   materialization, model activity, training, evaluation, compute, lease, CCA
   activity, another surface, or UAV activity.

### External evidence

No new external evidence was collected. The accepted Pro closure is preserved
only as a repository-held prior disposition recorded by the frozen RSCF card.
This cycle does not contact a provider, reconstruct a provider response, create
a round, reinterpret the prior disposition, or update the external-review
index.

### Local inference

1. Accepted same-conversation closure and the requirement for later static cost
   assessment are compatible: the former closes the definition's recorded
   mathematical/scientific defects, while the latter addresses construction
   feasibility, observability, and prospective resource cost without opening
   empirical activity.
2. Current `ACTIVE` lifecycle corrects legacy-state suppression and makes the
   preparation request actionable. It does not convert the historical
   `RESOURCE_WAIT` sentence or either advisory range into a current veto.
3. A legitimate static packet must derive each assessment independently from
   disclosed documentary facts and assumptions. When a quantity cannot be
   grounded without execution, it must be returned as
   `NOT_STATICALLY_ESTIMABLE`; copying an advisory range or manufacturing a
   point estimate would not close the gap.
4. The CCA comparison can be a report-only discriminator on a disclosed,
   like-for-like static accounting basis. Because this request freezes no
   metric or uncertainty rule for “materially below,” the CM cannot turn that
   phrase into a pass/fail benchmark, construction selection, or veto.

### Speculation retained as speculation

Whether snapshot/restore and full-suffix branching are construction-feasible on
a chosen implementation, the full person-workday and resource envelopes, safe
concurrency, whether an accelerator path is useful, whether RSCF total cost is
materially below CCA, and whether Portfolio will ever select construction all
remain unknown.

## Engineering request: CM static full-cost assessment

This is a request to Root for later routing through
`docs/research/candidates/semantic_graphon_shared_policy/workflow/engineering/state.json`
to the same-direction CM authority. Authorship is not dispatch. If Root later
dispatches this exact request, the CM may perform only symbolic, read-only
static analysis of the exact frozen documentary references above and return one
durable static packet. Cost-category names below describe prospective
assessment outputs; they authorize none of the named construction, integration,
test, measurement, or execution work.

### Exact static scope

The packet must provide all of the following without accessing source or
materializing any scientific or technical runtime object:

1. **Snapshot/restore feasibility and cost.** Inventory, from the frozen
   definition, the complete mutable state that a prospective branch origin must
   preserve; map the required pretransition boundary, immutable pre-update
   parameter identity, exact restore semantics, and factual-suffix identity to
   prospective components, risks, dependencies, and person-workday cost. This
   is a static state/interface analysis, not snapshot or restore implementation.
2. **Closed-loop branch-construction feasibility and cost.** Account for focal-
   only current-action replacement, factual teammate current actions, ordinary
   current transition, recomputed observations/messages/recurrent states/legal
   distributions from the next slot through slot 11, common future tape, and
   complete legal-action coverage. Report prospective component and work costs;
   construct or execute no branch.
3. **Stopped-target and loss-integration feasibility and cost.** Map the stopped
   Q vector and policy-weighted baseline, stopped factual-return difference,
   equal role weighting, retained all-agent/all-slot entropy, retained critic,
   one full-batch backward call, global clip, and projection lifecycle to
   prospective interfaces and work. No target, loss, autograd graph, optimizer,
   or policy output may be created or inspected.
4. **Selector, coupling, and audit feasibility and cost.** Provide a static
   bindability/observability matrix for one-origin-per-role selection,
   antithetic slot pairing, role-local selection, identical arm origin
   coordinates, common-tape and branch-order identity, immutable parameters,
   focal-only intervention, factual-return identity, closed-loop recurrence,
   no leakage, exact inherited optimizer opportunity, complete logical counts,
   and atomic completion before seed evaluability. Assess prospective audit,
   frontier, and certificate work only; generate no selector, coordinate,
   branch history, trace, digest, certificate, or partial value.
5. **Streaming, batching, and exact-cache feasibility and cost.** Identify only
   semantics-preserving prospective strategies and their cost sensitivities.
   Every strategy must preserve every logical Q entry, complete state,
   remaining-tape address, recurrence, horizon, factual identity, arm
   opportunity, and branch-order invariance. No strategy may prune or change the
   frozen logical schedule. Implement, execute, or benchmark none of them.
6. **Complete prospective labor.** Report person-workdays, separately from
   elapsed/calendar time, for every prospective component: snapshot/restore,
   branch host, stopped-target/loss integration, selectors/coupling,
   observability and atomic audits, runner/frontier/certificate surfaces,
   batching/cache, construction, tests, review, packaging, and integration.
   State staffing, sequencing, reuse assumptions, dependencies, risk allowance,
   and uncertainty. These are estimates of later work, not permission to do it.
7. **Complete prospective compute and host resources.** Keep CPU core-hours,
   accelerator-hours, and total host-hours separate. State the assumed hardware
   class, device count, process/thread/worker model, utilization assumptions,
   and uncertainty. Do not query hardware, import a runtime, characterize a
   device, execute a command, benchmark, request a lease, or consume compute.
8. **Elapsed time and safe concurrency.** Give elapsed-time ranges for every
   statically supportable concurrency case and disclose the CPU, RAM, VRAM,
   storage, I/O, process, and host constraints that make each case safe. A
   concurrency level unsupported by the frozen documents must be marked
   `NOT_STATICALLY_ESTIMABLE`, not tested. Unsafe memory plans must be reduced,
   batched, or sharded in the prospective analysis rather than sent for
   approval.
9. **Memory and storage.** Report peak RAM and peak VRAM separately, by
   prospective phase and both per worker and total when supportable. Report peak
   scratch/transient storage separately from retained storage, with retention,
   serialization, duplication, compression, cache, and frontier assumptions.
   These are static ranges, not telemetry; create no data or files to measure
   them.
10. **Opportunity cost and CCA comparison.** State the opportunity-cost basis
    and compare RSCF with the definition-only CCA reference on one disclosed,
    like-for-like static accounting basis. Keep exact logical-count ratios
    separate from estimated labor, elapsed, compute, memory, and storage costs.
    Report signed or ranged differences and all non-comparable dimensions. Do
    not execute, probe, benchmark, materialize, or import empirical evidence
    from RSCF or CCA, and do not emit a pass/fail construction label.

For every quantitative dimension, the packet must expose the source facts,
formula, units, assumptions, uncertainty method, and conservative range. A
single-point estimate without uncertainty is insufficient. If the documents do
not ground a value, the exact accepted output is `NOT_STATICALLY_ESTIMABLE`
plus the missing fact; the CM must not fill a gap with speculation or silently
open a successor assignment.

### Acceptance criteria

The returned packet is acceptable as a **complete static assessment packet**
only if all of the following hold. Packet completeness is not acceptance of any
numeric estimate and is not construction acceptance.

1. It binds the exact direction, RSCF revision, question hash, evidence-set
   hash, current Portfolio SHA, registry revision/SHA, direction SHA, RSCF-card
   SHA, and definition-only CCA-card SHA listed above.
2. It addresses every item in the exact static scope with either an auditable,
   assumption- and uncertainty-bearing static range or an explicit
   `NOT_STATICALLY_ESTIMABLE` finding. It identifies every unresolved
   bindability, observability, comparator-preservation, resource, and cost gap.
3. It reports labor person-workdays separately from elapsed time; CPU core-hours,
   accelerator-hours, and host-hours separately; elapsed ranges by stated safe
   concurrency; peak RAM separately from peak VRAM; and peak scratch separately
   from retained storage.
4. It preserves every RSCF logical entry, continuation, state, recurrence,
   coupling, loss, optimizer, checkpoint opportunity, and audit requirement.
   Static cost-reduction options may not change science or logical work.
5. It treats `100--500` CPU core-hours and `18--30` CM workdays as
   provenance-only pre-CM planning figures. It does not accept, reject,
   validate, calibrate to, target, benchmark against, repeat as a substitute
   estimate, or use either range as a lease, request, threshold, decision rule,
   or veto. The assessment is independently derived or explicitly ungrounded.
6. Its CCA section uses one disclosed common static accounting basis and keeps
   exact logical ratios distinct from estimated total costs. Because this
   request contains no frozen materiality metric or uncertainty rule, it reports
   comparison ranges without a `MATERIALLY_BELOW`, pass/fail, investment, or
   construction-selection label.
7. It contains no reward, return, loss, gradient, policy, Q-entry, branch,
   selector, coordinate, seed, initialization, model, checkpoint, endpoint,
   result, partial value, measured timing, telemetry, or benchmark value. It
   creates no scientific, inferential, or runtime artifact.
8. It records that its only return is feasibility, observability, risk,
   uncertainty, and prospective full-cost information for Root/Portfolio. It
   does not select, reject, recommend, authorize, or veto construction and does
   not alter the direction's scientific status.
9. It returns one terminal packet to Root. A dimension marked
   `NOT_STATICALLY_ESTIMABLE` remains a visible preparation gap; it is not a
   failure of the direction and does not silently trigger measurement,
   construction, compute, external review, or another engineering assignment.

### Explicit forbidden boundary

This EM does not dispatch the CM. Neither this handoff nor a later complete
static packet authorizes any provider activity; access to or effect on source,
runtime, results, or partial values; source mutation; build; test; validation;
probe; benchmark; hardware or environment characterization run; command
execution; scientific activity; construction selection; construction; snapshot
or restore implementation; branch construction; stopped-target or loss
integration; selector, coupling, audit, runner, frontier, certificate, batching,
or cache implementation; generation, inspection, summary, or use of a selector
or master word, numeric seed, coordinate, initialization, task event, detection,
packet, action uniform, branch, Q entry, policy output, model, checkpoint,
endpoint, trace, digest, certificate, or partial value; rollout; training;
evaluation; r03, CCA, second-surface, UAV, or empirical-successor activity;
lease; compute; worktree; commit; push; or other Git effect.

Cost-category and feasibility language describes static assessment outputs only.
All unlisted acts remain unauthorized.

## Durable next boundary

Root may later route the exact request above through the direction's engineering
state to the same-direction CM. The only acceptable return from that assignment
is one static packet satisfying the acceptance criteria or an exact account of
the remaining static evidence gap. Root/Portfolio may then make a separate
decision about whether any construction proposal should even be authored. No
construction, measurement, source, test, compute, scientific, provider, result,
or Git action follows automatically from this handoff or from the packet's
completion.
