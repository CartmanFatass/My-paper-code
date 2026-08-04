# VSP-02 Sequence 09 code-science index

```text
candidate=CAND-VSP-02@adversarial-revision-v8
action=BIND_IMPLEMENT_AND_RUN
oracle=experiments/candidates/vsp_02/duration_escrow_oracle.py
tests=tests/experiments/candidates/vsp_02/test_duration_escrow_oracle.py
arithmetic=exact Fraction with gamma=1/2
coverage=W+/W0 x 32 valid x matched 32 stale = 128
registered_z0=(context,)
future_branch_law=uniform rational full support over world x close x cutoff x owner_departure (16 branches per Z0/action)
selector_tape=8 rational cells with LONG iff tape < p
comparator=REGISTERED_Z0_FINITE_COMPARATOR
terminal=REGISTERED_Z0_SELECTOR_VALUE_CONFORMANCE
disposition=NO_INCREMENT_OVER_REGISTERED_Z0_COMPARATOR
bookkeeping_scope=PER_REALIZATION_RECORD_SHAPE_ONLY
```

The deterministic audit preserves the literal eight-state total transducer,
exact absolute-time targets, separate policy/environment clocks, immutable
primitive and partner tapes, owner-departure escrow identity, simultaneous
event priorities, explicit independent two-step rewards, W+/W0 pathwise
arithmetic, and current/stale case coverage. Every independently constructed
accepted realization has one score, release, and tombstone record.

Legal initiation information is exactly `(context,)`. World, close mode,
cutoff, owner departure, action, and selector tape are excluded from Z0. The
future physical fields occur only in the immutable shared 16-branch
marginalization law. The candidate probability surface is F=1/4 and P=3/4; an
independent literal comparator table reproduces its selector on all 16
context/tape cells. Both selector surfaces exactly equal that finite domain.
Grouped candidate and canonical-physical comparator values also match exactly
on, and have exactly, the four context/action entries: F/SHORT=71/64,
F/LONG=63/64, P/SHORT=135/64, and P/LONG=139/64.

The terminal therefore supports only no increment over this registered finite
Z0 comparator in the fixed synthetic instance. It does not support learned
policy value, adaptive-duration retirement in general, production bookkeeping,
return, deployment, or new physical worlds.

## Byte-stable raw audit output

Command: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B experiments/candidates/vsp_02/duration_escrow_oracle.py`

```json
{"bookkeeping":{"scope":"PER_REALIZATION_RECORD_SHAPE_ONLY","stale_record_counts":{"events":1,"releases":0,"scores":0,"tombstones":1},"valid_record_counts":{"events":4,"releases":1,"scores":1,"tombstones":1}},"candidate":"CAND-VSP-02@adversarial-revision-v8","comparator":{"branch_law":{"branches_per_z0_action":16,"fields":["world","close_mode","cutoff","owner_departure"],"normalized_full_support":true,"uniform_weight":"1/16"},"branch_variables_marginalized_only":true,"candidate_z0_excluded_fields":["world","close_mode","cutoff","owner_departure","action","selector_tape"],"candidate_z0_fields":["context"],"comparator_z0_excluded_fields":["world","close_mode","cutoff","owner_departure","action","selector_tape"],"comparator_z0_fields":["context"],"name":"REGISTERED_Z0_FINITE_COMPARATOR","probabilities":{"F":"1/4","P":"3/4"},"same_information":true,"selector":{"candidate_domain_exact":true,"candidate_entries":16,"candidate_nested":true,"comparator_domain_exact":true,"comparator_entries":16,"equal_keys":true,"exact_reproduction":true,"tape_cells":8,"threshold":"LONG iff tape < p"},"terminal_gate":true,"values":{"candidate":{"F|LONG":"63/64","F|SHORT":"71/64","P|LONG":"139/64","P|SHORT":"135/64"},"candidate_domain_exact":true,"candidate_entries":4,"candidate_nested":true,"comparator":{"F|LONG":"63/64","F|SHORT":"71/64","P|LONG":"139/64","P|SHORT":"135/64"},"comparator_domain_exact":true,"comparator_entries":4,"equal_keys":true,"exact_reproduction":true,"key_fields":["context","action"]}},"coverage":{"axes":["world","context","action","close","cutoff","owner_departure","version"],"per_world_stale":32,"per_world_valid":32,"shape":[2,2,2,2,2,2,2],"stale":64,"total":128,"valid":64},"deltas":{"W+|F":"-1/4","W+|P":"1/8","W0|F":"0","W0|P":"0","psi":"3/8"},"disposition":"NO_INCREMENT_OVER_REGISTERED_Z0_COMPARATOR","invariants":{"absolute_target_conserved_before_gradient":true,"explicit_nonzero_second_reward_kernel":true,"frozen_deltas_exact":true,"frozen_stop_gradient_vbar":true,"interrupt_over_natural":true,"one_score_release_tombstone_per_realization":true,"owner_departure_identity_escrow":true,"raw_expected_score_matches_analytic":true,"registered_z0_selector_value_conformance":true,"separate_policy_environment_clocks":true,"slot_excluded_from_identity":true,"stale_has_no_score_or_release":true,"terminal_over_horizon":true,"w0_paired_physical_equality_zero_gradient":true},"raw_expected_scores":{"W+|F":{"settings":8,"value":"-3/160"},"W+|P":{"settings":8,"value":"9/640"},"W0|F":{"settings":8,"value":"0"},"W0|P":{"settings":8,"value":"0"}},"schemas":{"DecisionIdentity":["episode_id","source_owner_epoch","own_boundary_index","behavior_version"],"EventRecord":["event_id","identity","slot_index","event","before","after","policy_clock","environment_clock"],"ReleaseRecord":["identity","target","release_clock"],"TombstoneRecord":["identity","final_state","target","reason"]},"terminal":"REGISTERED_Z0_SELECTOR_VALUE_CONFORMANCE","timing_tensor":{"axes":["world","context","action","close","cutoff","owner_departure"],"entries":64,"frozen":true,"shape":[2,2,2,2,2,2],"tau_values":[100,104]}}
```
