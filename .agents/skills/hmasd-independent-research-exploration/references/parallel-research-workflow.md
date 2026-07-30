# Parallel independent research workflow

```text
scout_parallel_limit=4
innovator_parallel_limit=4
critic_parallel_limit=2
merge_barrier=required
completion_order_priority=forbidden
single_writer=independent_research_explorer
child_depth=0
automatic_formal_workflow_promotion=forbidden
campaign_authorization=one_user_confirmation_with_total_budgets
automatic_cohort_progression=allowed_within_frozen_campaign
per_cohort_user_confirmation=not_required
unbounded_cohort_loop=forbidden
initial_cohort_independence_shielding=required
later_cohort_collaboration_brief=required
```

## Shared intake and barrier

Freeze the question, one exact mode, mission link, named sources, exclusions,
completion condition and target-semantic traps before dispatch. A scientific-
innovation campaign also freezes exclusions, total Scout/Innovator/Critic
budgets, maximum cohort count, stop conditions, scope, common scientific
objects, exact source identities and boundary, and evidence baseline in one
fingerprinted user-confirmed campaign record. Operational failure may receive
one unchanged low-cost retry. A changed scope or larger budget needs a new user
authorization; a changed axis, family or mechanism inside the frozen campaign
is a new cohort assignment.

Every cohort has expected Scout/Innovator assignments and, after their return,
an exact expected Critic assignment set. The final merge barrier opens only
when every expected assignment has one terminal packet or terminal operational
failure. Reject packets with missing identity, locator or provenance, scope
expansion, authority claims or incomplete semantic-trap results. Never use
completion order as evidence priority. A terminal operational failure records
the exact `OPERATIONAL_FAILURE` kind, terminal status, assignment identity,
stable failure signature, whether its one unchanged low-cost retry was used,
and `scientific_output=false`. Its schema admits no scientific payload and it
cannot be cited as evidence.

## Evidence-review mode

1. **Integrity and recall.** Read live MyLib integrity when applicable. Build a
   bounded candidate list from registered indexes without treating excerpts as
   evidence.
2. **Evidence partition.** Split by disjoint evidence axes or paper IDs. Each
   candidate has one Sol-high Research Scout owner and one or more exact
   source-identity, JSON/PDF type and absolute-path bindings.
3. **Scout wave.** Launch 1-4 Scouts with exact axis, source set, semantic traps
   and `SCOUT_EVIDENCE_PACKET` contract.
4. **Merge.** Wait until every assignment has a terminal packet or terminal
   operational-failure record, deduplicate returned evidence by paper ID and
   claim, and map support, conflict, fidelity boundaries and uncovered evidence.
5. **Targeted criticism.** Select only central, surprising, conflicting or
   high-consequence claims. Launch 0-2 Sol-max Critics with exact packet and
   claim identities plus a target-specific checklist.
6. **Evidence synthesis and stop.** Write one advisory evidence report. This
   mode has no approach-family registry or additional research wave.

## Scientific-innovation campaign

1. **Campaign freeze.** Name the evidence baseline, exact source set, common
   definitions and scientific objects, scope, completion/stop conditions,
   maximum cohorts and total role budgets. Record what is established,
   contradicted and unresolved. Do not silently search project state.
2. **Conjecture portfolio.** The Explorer creates one versioned advisory row
   per mechanism-level family:

   ```text
   family_id | conjecture_id/version | parent_conjecture_ids |
   core_mechanism | exact_claim | evidence_baseline |
   strongest_support | strongest_counterexample | current_gap |
   status=live|blocked|parked|contradicted | reopen_condition |
   innovator_packet_ids |
   critic_status=not_selected|supported|weakened|contradicted|unresolved|conflicting|operational_failure|partial_operational_failure
   ```

3. **Independent first cohort.** Launch 1-4 read-only Sol-max Innovators on
   materially different mechanisms or formulations. Every assignment receives
   the same baseline and methodology but no peer packet. Do not reveal the
   favored family unless the assignment is an exact challenge. Group by
   mechanism, not wording.
4. **Concrete return gate.** Require one `RESEARCH_DIRECTION_PACKET` per
   assignment and at least one lemma, construction, equation, counterexample or
   falsifiable prediction. A reduction with a missing lemma of unchanged
   difficulty is `blocked`, not near-complete.
5. **Merge before cross-pollination.** Wait until every expected assignment has
   a terminal packet or terminal operational-failure record. Only returned
   packets may support comparison; failures remain exact gaps. The Explorer
   then writes a versioned collaboration brief with packet identities, retained
   lemmas, counterexamples, complete immutable corrections, gaps, transfer candidates and
   permitted parent identities.
6. **Targeted Critic wave.** Record and launch 0-2 Sol-max Critics only for central,
   conflicting, surprising or high-consequence claims. Each receives exact
   family, claim and packet identities plus an adversarial checklist tailored
   to the target semantics. Each expected Critic must return a terminal packet
   or operational-failure record; either consumes one frozen Critic slot.
   A family without a Critic assignment is `not_selected`. A selected Critic
   with only terminal failures is `operational_failure`; mixed packet/failure
   completion is `partial_operational_failure`. Other `critic_status` values
   derive from actual terminal packets, using `conflicting` when dispositions
   disagree.
7. **Cohort disposition.** Update every family to `live`, `blocked`, `parked` or
   `contradicted`. Preserve competing families; scheduling or emphasizing one
   does not make it the unique scientific direction.
8. **Adaptive next-cohort gate.** Continue automatically only within the
   confirmed campaign. Record prior/next cohort IDs, exact terminal assignment
   and packet sets, input collaboration brief, target/parent families, purpose
   `develop|refine|combine|challenge`, genuine novelty basis, expected
   disposition change, prior family-disposition snapshot, complete planned
   assignment semantics, role budgets and exact stop condition. A deterministic
   fingerprint binds the admission to the unchanged campaign authorization.
   Before dispatch, Scout plans bind to the explicit frozen source set and
   source paths; Innovator plans bind purpose, targets, parents, mechanism and
   claim to the admission, brief and registry. Prospective conjectures use the
   next canonical version, and all planned Innovators together cover the exact
   admitted parent set. Each refinement carries its own immediate predecessor;
   another assignment cannot satisfy that lineage obligation. An absent source set is not equivalent to an explicit empty set.
   `combine` creates a new family with at least two parents and a new interaction
   claim. A blocked route needs a new mechanism, invariant, construction or
   applicable exact Critic correction; rewording, generic search or one more
   citation is insufficient.
   A completed later cohort retains the originating admission and fingerprint
   and must match the admitted assignment semantics exactly. Its successor
   lineage is replayed against the registry visible before that cohort, never
   legalized by a current or future version. Every admitted and planned parent
   must already belong to that historical registry.
9. **Collaborative later cohort.** Later Scouts/Innovators see only their named
   collaboration brief and sources. They may transfer a lemma, counterexample,
   representation or identification design, refine one conjecture, combine
   parent families, or challenge a dependency. Every output records exact
   parent and input versions; originals remain immutable.
10. **Budget/stop check.** Derive cumulative role use from terminal cohort
    records. Stop before dispatch if the next cohort exceeds any total, exceeds
    maximum cohorts, leaves no disposition-changing target or meets a campaign
    stop/completion condition. Eligibility never authorizes compute or formal
    work.
11. **Synthesis and stop.** Return an audited result or the strongest rigorous
    derivation plus its exact gap and the ordered disposition snapshot for every
    cohort. Mark each exact Critic correction applied, unresolved or conflicting;
    an applied correction is a versioned conjecture successor whose target field
    contains the exact correction text and whose lineage includes the corrected
    conjecture. Never
   force an affirmative conclusion or automatically promote the result.

## Scientific-methodology contract

Every innovation campaign loads `research-methodology.md`. A conjecture and
direction packet instantiate the game/information objects, membership process,
identity ownership, clocks, strategic policy dependence, estimand, sampling
hierarchy, identification assumptions, strongest simple null, counterexample,
replacement ledger, partner-policy population, cross-pollination provenance,
unique discriminator, stop condition and lineage. Conditional fields use
explicit `unknown` or `not_applicable` records. Mechanical completeness never
means scientific truth.

## Concurrency and authority

With `max_threads=8`, normal maximum occupancy is one Explorer plus four Scouts
or Innovators, followed after the merge barrier by two Critics. Children cannot
spawn, write, use Git, contact persistent tasks or access active HMASD state.
There is no minimum-duration rule, fixed large-agent target or unbounded loop.
One user-confirmed campaign may use multiple bounded cohorts within its frozen
balances; only the user may expand that boundary or later initiate a separate
formal workflow submission.
