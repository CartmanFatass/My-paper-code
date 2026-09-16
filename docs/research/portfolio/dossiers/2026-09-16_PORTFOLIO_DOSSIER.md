# Portfolio dossier — 2026-09-16 (first owner-triggered review)

Prepared by the Claude hub under `decisions/2026-09-15-portfolio-control-and-approved-set.md`
section 5. It decides nothing. Facts come from each direction's `DIRECTION.md`, `PARK.md`,
`PORTFOLIO.md`, `EXPERIMENT_TRACKING.md` and file counts (scout pass 2026-09-16 04:45Z); the
"hub proposal" column is the DM-equivalent recommendation for the owner to accept, change or
reject. Cost per valid result is approximated by objects run and Pro rounds spent, because
compute per result was never recorded consistently. "Signal" means a positive result above the
card's minimum effect that was not overturned by its own replication. Kill flags are inputs, not
actions.

## Questions for this review

1. ACVC lifecycle: PARK with assets retained (hub proposal) versus a second matched block.
2. Whether any parked direction enters the approved set beside FSD, and in what lane.
3. Whether the standing budgets of the lanes decision are the right size for the node (20 cores,
   about 15 GB, no GPU, four fits concurrently at 3 to 4 GB each).

## Current approved set (v1)

| Direction | Lane | Signal on record | Headroom record | Objects / Pro rounds | Hub proposal |
| --- | --- | --- | --- | --- | --- |
| flexible_skill_duration | CONFIRM, priority 1 | interruption vs no-interruption +.05 J at rollouts 5 and 10 over six blocks (accumulation interval touches zero); +.01 J at rollout 15 (four blocks, interval includes zero); the flat no-skill reduction scores .04 J above both at rollout 15 | none (FLAT is an untuned private-actor reduction, not a matched-information baseline) | 26 / 11 | keep; first CONFIRM object = headroom card (flat comparator, HMASD fixed k, D0 and I1280 at three times the current budget, five seeds per arm, decision rule from measured across-seed SD). Flag: the direction's whole record sits at 0.40 to 0.45 J against an achievable 0.67 J. |

## Queued from the closing lane

| Direction | Signal | Headroom | Objects / Pro rounds | Hub proposal | Alternative on record |
| --- | --- | --- | --- | --- | --- |
| acvc | wrapper lifts the C proposer by about .045 J on three blocks; complete packages F(C) vs F(M) within .04 J with sign flips; C trails M by .05 to .09 J on every block | none | 30 / 26 | PARK, assets retained, three reopening conditions (`ACVC_CLOSING_MEMO_20260916.md`); slot not refilled | option B of the result review: one more matched block, two fits, about 2,250 s native wall |

## Parked backups and other candidates

| Direction | State on record | Signal | Headroom | Objects / Pro rounds | Hub proposal | Flag |
| --- | --- | --- | --- | --- | --- | --- |
| tail_return_distributional_learning | ACTIVE/MEDIUM, paused (Codex) | B01 lower-tail +.035 J; independent B02 −.002 J (did not recur) | none | 3 / 2 | stay parked; if entered, EXPLORE with one pilot batch on the tail estimand, not CONFIRM | replication overturned the only positive |
| vap_folr_core | ACTIVE/MEDIUM, paused (Codex) | none (two fresh A−G blocks −5.83 / −.11; mixed pattern) | none, "unmeasured" | 23 / 19 | stay parked | 19 Pro rounds, no signal |
| roster_consistent_latent_exploration | ACTIVE/MEDIUM with a HOLD; listed PARKED in one table | none | none | 19 / 18 | stay parked | 18 Pro rounds, no signal |
| metric_ground_transport_allocation | PARKED/MEDIUM (2026-09-14) | COND_ABOVE_MEI +.015 J on one pair (2026-09-13) | none | 12 / 16 | stay parked; a pilot batch only if the owner wants the conditional effect replicated | single pair |
| degraded_incumbent_shadow_handover | PARKED reversible (2026-09-14) | none | none | 13 / 16 | stay parked | 16 Pro rounds, no signal |
| ucope | PARKED/MEDIUM (from ACTIVE/HIGH) | none | none | 46 / 8 | stay parked | 46 objects, no signal |
| finite_resource_relational_inductive_efficiency | ACTIVE/HIGH by a 2026-09-11 reaudit; not in the current table | none | partial local record | 30 / 0 | stay parked | 30 objects, no signal |
| capability_bound_semantic_currentness | historical | none | none | 24 / 3 | stay parked | none |
| commitment_residual_triggered_options | historical (ACTIVE/MEDIUM in its own text) | none | none | 24 / 2 | stay parked | none |
| vsp_c1 | ACTIVE at object-tier park | none | none | 18 / 9 | stay parked | none |
| vsp_03 | recasts 1, family pause | none | none | 11 / 10 | stay parked | none |
| semigroup_consistent_duration_model_policy | conflicting tokens (CLOSED, then ACTIVE/HIGH, then narrow PARK) | two small positives (+.007, +.004 J) | none | 8 / 4 | stay parked; resolve its lifecycle token at this review | inconsistent record |
| learned_counterfactual_agent_credit | PARKED/MEDIUM (2026-09-14) | none | none | 3 / 3 | stay parked | none |
| variable_n_fleet_churn | historical | none | none, explicitly | 5 / 5 | stay parked; the N-axis question is open but has no host (foundations review R2) | none |
| actuator_conditioned_partial_sharing | PARKED reversible (2026-09-13) | none | none | 2 / 1 | stay parked | none |
| contention_aware_decentralized_communication | PARKED/HIGH reversible | none (no result files) | none | 0 / 0 | stay parked | never ran |
| cross_play_compatible_population_learning | PARKED/MEDIUM | none (no result files) | none | 0 / 0 | stay parked | never ran |
| vsp_02 | ACTIVE/LOW by reaudit | none | record: matched greedy headroom 0 (census) | 5 / 2 | stay parked | headroom zero |
| eociv_lite | ACTIVE/MEDIUM in its own text | none | none | 3 / 0 | stay parked | none |
| active_post_churn_population_flow_identification, ec4g_r1, expressibility_gated_renewal_credit_relay, orbit_shadow_read, recct_lite, scope_1s | PARKED/LOW or research reserve | none | none | 0 to 1 each | stay parked | none |

Legacy (closed or absorbed, `docs/research/legacy/directions/`): fourteen further labels; not
candidates.

## Hub summary for the owner

- Only FSD carries an effect that survived a second block, and even there the sign is unstable
  across blocks and the flat reduction outscores the package at the longest budget run. The
  headroom card is the one object that can settle whether the host rewards the hierarchy at all.
- Twenty-six other directions have no surviving signal. Sixteen of them consumed between two and
  twenty-six Pro rounds each. The hub proposes none of them for the approved set now; the
  N-axis question (`variable_n_fleet_churn`) is the strongest reopening candidate once a host
  with a real hazard exists (foundations review R2).
- Lifecycle bookkeeping is inconsistent for about eighteen directions (their `DIRECTION.md`
  defers to a `PORTFOLIO.md` table that no longer lists them). The approved set makes this moot
  for execution; the owner may want a one-line "not approved" state recorded for each at this
  review so the files stop contradicting each other.
