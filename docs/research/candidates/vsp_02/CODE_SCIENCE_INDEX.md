# VSP-02 Sequence 09 code-science index

```text
candidate=CAND-VSP-02@adversarial-revision-v8
action=BIND_IMPLEMENT_AND_RUN
oracle=experiments/candidates/vsp_02/duration_escrow_oracle.py
tests=tests/experiments/candidates/vsp_02/test_duration_escrow_oracle.py
arithmetic=exact Fraction with gamma=1/2
coverage=W+/W0 x 32 valid x matched 32 stale = 128
null=HORIZON_FLUSH_TABULAR_DURATION_NULL
terminal=ADAPTIVE_DURATION_RETIRED
disposition=BOOKKEEPING_TRANSPORT_CONFORMANCE_ONLY
```

The deterministic audit covers the literal eight-state total transducer, exact
absolute-time targets, separate policy/environment clocks, immutable primitive
and partner tapes, timing tensor, owner-departure escrow identity, simultaneous
event priorities, stale-version rejection, and exactly-once persistence. The
physical kernel is independently assembled from explicit two-step reward
components; every second reward is nonzero, and targets are derived only by the
absolute-time oracle. Raw
expected scores are formed from the two action scores and their probabilities
before comparison with `mu*p*(1-p)*Delta`.

The independently enumerated same-information full-horizon tabular null has 32
finite predecision keys and 64 action entries. It exactly nests and reproduces
all 64 valid candidate action mappings. Therefore adaptive duration is retired;
only bookkeeping/transport conformance remains. This is a finite deterministic
oracle, not evidence of learned-policy performance, deployment scalability, or
behavior outside the enumerated physical kernels.

## Byte-stable raw audit output

Command: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B experiments/candidates/vsp_02/duration_escrow_oracle.py`

```json
{"candidate":"CAND-VSP-02@adversarial-revision-v8","coverage":{"axes":["world","context","action","close","cutoff","owner_departure","version"],"per_world_stale":32,"per_world_valid":32,"shape":[2,2,2,2,2,2,2],"stale":64,"total":128,"valid":64},"deltas":{"W+|F":"-1/4","W+|P":"1/8","W0|F":"0","W0|P":"0","psi":"3/8"},"disposition":"BOOKKEEPING_TRANSPORT_CONFORMANCE_ONLY","invariants":{"absolute_target_conserved_before_gradient":true,"explicit_nonzero_second_reward_kernel":true,"frozen_deltas_exact":true,"frozen_stop_gradient_vbar":true,"interrupt_over_natural":true,"owner_departure_identity_escrow":true,"raw_expected_score_matches_analytic":true,"separate_policy_environment_clocks":true,"slot_excluded_from_identity":true,"stale_has_no_score_or_release":true,"tabular_null_exact_reproduction":true,"terminal_over_horizon":true,"valid_score_release_tombstone_exactly_once":true,"w0_paired_physical_equality_zero_gradient":true},"null":{"action_entries":64,"candidate_entries":64,"candidate_nested":true,"exact_reproduction":true,"finite_predecision_keys":32,"full_horizon":true,"name":"HORIZON_FLUSH_TABULAR_DURATION_NULL","same_information":true},"raw_expected_scores":{"W+|F":{"settings":8,"value":"-3/160"},"W+|P":{"settings":8,"value":"9/640"},"W0|F":{"settings":8,"value":"0"},"W0|P":{"settings":8,"value":"0"}},"schemas":{"DecisionIdentity":["episode_id","source_owner_epoch","own_boundary_index","behavior_version"],"EventRecord":["event_id","identity","slot_index","event","before","after","policy_clock","environment_clock"],"ReleaseRecord":["identity","target","release_clock"],"TombstoneRecord":["identity","final_state","target","reason"],"VersionRecord":["behavior_version","record_count","released_count","invalid_count","can_advance"]},"terminal":"ADAPTIVE_DURATION_RETIRED","timing_tensor":{"axes":["world","context","action","close","cutoff","owner_departure"],"entries":64,"frozen":true,"shape":[2,2,2,2,2,2],"tau_values":[100,104]},"versions":{"current":{"behavior_version":9,"can_advance":true,"invalid_count":0,"record_count":64,"released_count":64},"stale":{"behavior_version":8,"can_advance":false,"invalid_count":64,"record_count":64,"released_count":0}}}
```
