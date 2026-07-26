# G37 history-proxy coherence design assertion audit brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
code_acceptance_owner=project_manager
review_mode=DESIGN_ASSERTION_AUDIT
round=20260726_continuous_roster_history_proxy_coherence_g37_design_assertion_audit
selected_action=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT
formal_compute_authority=none_in_this_round
design_audit_compute=zero
conclusion_bearing_iteration_cost=0
```

## Purpose

External Pro accepted G36 as bounded actual-history-sensor substitution for the
exact formal G35 CS final checkpoints. The frozen G36 donor destroys connection
to the target episode's actual history but preserves joint time, age and action
coherence within source-valid donor snapshots. The remaining counterexample is
dependence on that joint coherence rather than on target history.

External Pro selected exactly one next action:

```text
CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT
```

This zero-compute round must freeze or reject a zero-training comparison between
the accepted G36 joint donor and an active-count-conditioned factorized donor.
It grants no implementation, evaluation or formal-run authority.

## Non-negotiable inherited boundary

```text
training=none
checkpoints=exact_formal_G35_CS_final_only
reference_execution=exact_formal_G36_joint_donor_read_only
H=48
capacities=6|8|12
sources=unchanged_G32_fixed_and_G34_P0_random
actor_actual_fields_0_to_6=unchanged
active_mask_and_prefix=unchanged
critic=unchanged
reward=unchanged
action_streams=paired
episode_ids=complete_inherited_support
g33_reactivation=forbidden
```

The intended factorized intervention preserves each of age, previous-action-0,
previous-action-1 and time's empirical donor marginal and legal support at the
current active count, while destroying within-row, cross-coordinate and
across-roster joint coherence. External Pro must freeze the exact independent
snapshot selection, column construction, row permutation, seed ownership and
reference binding rather than allow PM to choose them.

The positive claim ceiling is only that the exact checkpoints do not require
the G36 donor's joint coherence under the frozen factorized marginal law. A
negative result may establish checkpoint dependence on donor coherence or
distributional consistency, not task-level history necessity.

## Feasibility and evidence economy

```text
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
```

A later realization may read the exact G36 joint-donor baseline rather than
rerun it. The maximum admissible new formal inventory is three replicates,
three capacities, four factorized cells per capacity, 128 episodes per cell,
221,184 real transitions, zero optimizer steps and 10,000 bootstrap resamples.
The complete nonformal package must finish within 20 minutes and formal
evaluate/analyze within eight hours.
