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
automatic_additional_wave=forbidden
additional_wave_user_confirmation=required_per_wave
```

## Shared intake and barrier

Freeze the question, one exact mode, mission link, named sources, exclusions,
completion condition and target-semantic traps before dispatch. Operational
failure may receive one unchanged low-cost retry. A changed axis, family,
mechanism or source boundary is a new assignment.

Every wave has an expected assignment set. The merge barrier opens only when
each expected assignment has one terminal packet or a terminal operational
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

## Scientific-innovation mode

1. **Evidence-baseline freeze.** Name the accepted evidence report or exact
   source set. Record what is established, contradicted and unresolved. Do not
   silently search project state.
2. **Portfolio freeze.** The Explorer creates one advisory registry row per
   mechanism-level family:

   ```text
   family_id | core_mechanism | exact_claim | evidence_baseline |
   strongest_support | strongest_counterexample | current_gap |
   status=live|blocked|parked|contradicted | reopen_condition |
   innovator_packet_ids |
   critic_status=not_selected|supported|weakened|contradicted|unresolved|conflicting
   ```

3. **Independent Innovator wave.** Launch 1-4 read-only Sol-max Research
   Innovators on materially different mechanisms or formulations. Shared
   sources are allowed. Do not reveal the favored family unless the exact
   assignment is to challenge it. Group by mechanism, not wording.
4. **Concrete return gate.** Require one `RESEARCH_DIRECTION_PACKET` per
   assignment and at least one lemma, construction, equation, counterexample or
   falsifiable prediction. A reduction with a missing lemma of unchanged
   difficulty is `blocked`, not near-complete.
5. **Merge before cross-pollination.** Wait until every Innovator assignment has
   a terminal packet or terminal operational-failure record. Only returned
   packets may support comparison; failures remain exact gaps. The Explorer may
   then compare, combine or redirect families.
6. **Targeted Critic wave.** Launch 0-2 Sol-max Critics only for central,
   conflicting, surprising or high-consequence claims. Each receives exact
   family, claim and packet identities plus an adversarial checklist tailored
   to the target semantics.
   A family without a Critic is `not_selected`; any other `critic_status` is
   derived from its actual terminal Critic packet set, using `conflicting` when
   terminal dispositions disagree.
7. **Round disposition.** Update every family to `live`, `blocked`, `parked` or
   `contradicted`. Preserve competing families; scheduling or emphasizing one
   does not make it the unique scientific direction.
8. **Additional-wave gate.** Default to stop. A proposed extra wave records:
   prior and next wave IDs; exact terminal assignment and packet sets; target
   family; new mechanism, invariant or construction; expected disposition
   change; Innovator and Critic budgets; exact stop condition; and separate user
   confirmation. A deterministic admission fingerprint binds the confirmation
   to those frozen fields; it is an internal consistency check, not proof that
   a model supplied user authority. A blocked family does not reopen for
   rewording, another generic search or a new citation alone.
9. **Synthesis and stop.** Return an audited result or the strongest rigorous
   derivation plus its exact gap. Propagate exact Critic corrections. Never
   force an affirmative conclusion or automatically promote the result.

## Concurrency and authority

With `max_threads=8`, normal maximum occupancy is one Explorer plus four Scouts
or Innovators, followed after the merge barrier by two Critics. Children cannot
spawn, write, use Git, contact persistent tasks or access active HMASD state.
There is no minimum-duration rule, fixed large-agent target or autonomous
multi-wave loop. The user alone confirms each additional innovation wave and
may later initiate a separate formal workflow submission.
