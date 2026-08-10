# VSP-02 Sequence 09 code-science index

```text
candidate=CAND-VSP-02@adversarial-revision-v8
action=BIND_IMPLEMENT_AND_RUN
oracle=experiments/candidates/vsp_02/duration_escrow_oracle.py
tests=tests/experiments/candidates/vsp_02/test_duration_escrow_oracle.py
arithmetic=exact Fraction with gamma=1/2
coverage=W+/W0 x 32 valid x matched 32 stale = 128
registered_z0_full=(context,tau,remaining_horizon,focal_execution_phase,public_partner_phase,legal_duration_mask,behavior_version)
registered_z0_used=(context,) for candidate and comparator
future_branch_law=uniform rational full support over world x close x cutoff x owner_departure (16 branches per Z0/action)
registered_selector_tape=independent literal (0,1/8,1/4,3/8,1/2,5/8,3/4,7/8)
runtime_selector_tape=must equal the registered tape in order, length, uniqueness and all 16 Context x tape keys
comparator=REGISTERED_Z0_FINITE_COMPARATOR
integrated_value_scope=registered 16-branch synthetic mixture Q(context,action), not full-Z0 conditioning
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

The full legal initiation information is `Z0_full=(context, tau,
remaining_horizon, focal_execution_phase, public_partner_phase,
legal_duration_mask, behavior_version)`. Candidate and comparator both use
only `Z0_used=(context,)`, a strict subset, and ignore the same six additional
legal fields. `remaining_horizon` directly denotes `H-tau` and is registered
as the fixed legal-but-unused value `2`; it is not an alias for another
information object. Source cases mechanically report `tau_values=[100,104]`; tau is
neither absent nor constant. World, close mode, cutoff, owner departure and
the departure-associated tau are marginalized by the immutable registered
16-branch synthetic mixture rather than conditioned on as full Z0.

The candidate probability surface is F=1/4 and P=3/4. Its runtime tape must
equal the independent literal registered tape, in exact order with length and
uniqueness eight, yielding exactly 16 registered Context x tape keys. The
independent literal comparator probability table reproduces the candidate
selector on that exact finite domain. Grouped candidate and canonical-physical
comparator `Q(context,action)` values are scoped only to the registered
16-branch mixture and match exactly on the four entries: F/SHORT=71/64,
F/LONG=63/64, P/SHORT=135/64, and P/LONG=139/64.

The terminal therefore supports only no increment over this registered finite
used-information comparator in the fixed synthetic instance. It does not support learned
policy value, adaptive-duration retirement in general, production bookkeeping,
return, deployment, or new physical worlds.

## Owner-action-responsive lifecycle A1 source

Accepted registered result:
`A1_OWNER_ACTION_RESPONSIVE_LIFECYCLE_SUPPORTED`. The sole invocation was
`vsp02_a1_617290fb_r1` at source commit
`617290fb333d3dcd5ebf47525fcca04e05b0cce9`. The byte-exact public artifact is
`docs/research/candidates/vsp_02/VSP02_A1_OWNER_ACTION_RESPONSIVE_LIFECYCLE_RESULT.json`
(SHA-256
`68e91ead4d1cc2ab838de79f6fffcbf8665c266f11de95ea8ab9b083d25e9b4f`).
Its matched 2x2 separator is candidate `RELEASE=ENDED_RELEASE`, candidate
`HOLD=ACTIVE`, Z0 `RELEASE=ACTIVE`, and Z0 `HOLD=ACTIVE`. The artifact records
one registered deterministic A invocation and zero environment, policy,
learner, trainer, optimizer, return-evaluation, model-fit, stochastic, or
retry/rescue/sweep activity. This certifies only the frozen lifecycle action
edge and its matched-control boundary.

```text
treatment=VSP02-A1-OWNER-ACTION-RESPONSIVE-LIFECYCLE
candidate=CAND-VSP-02@adversarial-revision-v8
source=experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py
runner=scripts/run_vsp02_a1_owner_action_responsive_lifecycle.py
tests=tests/experiments/candidates/vsp_02/test_owner_action_responsive_lifecycle.py
evidence=A_READONLY_OR_ZERO_RUNTIME
registered_activity_cap=one deterministic invocation; all environment/policy/learner/trainer/optimizer/return/model-fit counts zero
scope=lifecycle actionability certificate only
```

This A1 package is independent of the earlier duration-escrow value
conformance above.  It binds an immutable owner epoch and behavior version,
separates authoritative membership from visible roster state, makes candidate
`RELEASE` an idempotent causal stopping edge, and keeps the matched Z0
post-claim `RELEASE` command log-only.  Its registered first observation is
the committed post-boundary phase on one matched positive-survival tape.

The package does not reuse the earlier synthetic return calculation as a
lifecycle certificate.  It makes no claim about learning, value, escrow
superiority, adaptive superiority, production deployment, promotion,
retirement, B/C readiness, or formal-compute readiness.

## Crossed physical-value support A2 source

This is the prospective source index for
`VSP02-A2-CROSSED-PHYSICAL-VALUE-SUPPORT`; no registered A2 audit or accepted
A2 result is recorded here.  The immutable manifest is built before its four
value cells and contains no `q_values`, `deltas`, branch, or result field.

```text
treatment=VSP02-A2-CROSSED-PHYSICAL-VALUE-SUPPORT
candidate=CAND-VSP-02@adversarial-revision-v8
source=experiments/candidates/vsp_02/crossed_physical_value_support.py
runner=scripts/run_vsp02_a2_crossed_physical_value_support.py
tests=tests/experiments/candidates/vsp_02/test_crossed_physical_value_support.py
evidence=A_READONLY_OR_ZERO_RUNTIME
arithmetic=exact Fraction
cells=(X_b=1,RELEASE)|(X_b=1,HOLD)|(X_b=0,RELEASE)|(X_b=0,HOLD)
contrasts=Delta_1=Q_1(RELEASE)-Q_1(HOLD)|Delta_0=Q_0(RELEASE)-Q_0(HOLD)
registered_activity_cap=one deterministic A invocation; all environment/policy/learner/trainer/optimizer/evaluation-episode/model-fit/stochastic activity zero
registered_audit_status=NOT_RUN
```

`frozen_contract()` owns the single reward, transition, discount, horizon,
continuation/partner/primitive-policy, owner/version, target/score, cue, and
matched-tape object.  The cue is prospectively and permanently mapped from the
public predecision cutoff-request bit: present is `X_b=1`, absent is `X_b=0`.
Its source-field allow-list excludes future termination, future reward, hidden
tape, realized end cause, treatment, branch, Q, and delta information.  Each
cue tape has exact weight `1/2`; RELEASE and HOLD each have exact registered
legal propensity `1/2` in both cue states.  The same cue tape is reused across
the two forced actions, so realized end cause is never selected.

`_evaluate_cell()` reuses the accepted A1 immutable-owner lifecycle edge.  A
legal RELEASE commits `ENDED_RELEASE`; a legal HOLD commits one frozen
primitive boundary and then `ENDED_NATURAL`.  It returns one exact physical
target/score witness per cell without policy, learner, optimizer, episode, or
model-fit execution.  `classify_a2()` recomputes both registered deltas from
the exact four-cell domain and applies, in order, invalid/leak, absent support,
registered strict crossing, reversed strict crossing, nonzero non-crossing,
and both-zero branches.  Reversed crossing is terminal as reversed and has no
cue-label or sign repair.

The runner separates prospective manifest creation, technical reconstruction,
the unique `registered-audit`, and validation.  The registered path creates an
exclusive claim before evaluation; an existing claim or result forbids retry,
and a post-claim failure consumes the invocation.  Before that claim, source
integrity covers both the four A2-owned claim paths and the immediate executed
runtime dependency
`experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py`.  An
absent, untracked, or dirty A1 dependency fails before claim creation, so the
result cannot claim the checkout HEAD while executing altered local lifecycle
semantics.  This package supports no B, C, Pro, formal, promotion, retirement,
rescue, sweep, or adjusted same-audit path.

## Byte-stable raw audit output

Command: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B experiments/candidates/vsp_02/duration_escrow_oracle.py`

```json
{"bookkeeping":{"scope":"PER_REALIZATION_RECORD_SHAPE_ONLY","stale_record_counts":{"events":1,"releases":0,"scores":0,"tombstones":1},"valid_record_counts":{"events":4,"releases":1,"scores":1,"tombstones":1}},"candidate":"CAND-VSP-02@adversarial-revision-v8","comparator":{"branch_law":{"branches_per_z0_action":16,"fields":["world","close_mode","cutoff","owner_departure"],"normalized_full_support":true,"uniform_weight":"1/16"},"branch_variables_marginalized_only":true,"candidate_ignored_legal_fields":["tau","remaining_horizon","focal_execution_phase","public_partner_phase","legal_duration_mask","behavior_version"],"candidate_z0_used_fields":["context"],"comparator_ignored_legal_fields":["tau","remaining_horizon","focal_execution_phase","public_partner_phase","legal_duration_mask","behavior_version"],"comparator_z0_used_fields":["context"],"name":"REGISTERED_Z0_FINITE_COMPARATOR","probabilities":{"F":"1/4","P":"3/4"},"registered_remaining_horizon":2,"same_used_selector_information":true,"selector":{"candidate_domain_exact":true,"candidate_entries":16,"candidate_nested":true,"comparator_domain_exact":true,"comparator_entries":16,"equal_keys":true,"exact_reproduction":true,"registered_domain_exact":true,"registered_entries":16,"registered_tape_cells":8,"runtime_tape_cells":8,"runtime_tape_length_exact":true,"runtime_tape_ordered_exact":true,"runtime_tape_unique_exact":true,"threshold":"LONG iff tape < p"},"terminal_gate":true,"used_is_strict_subset_of_full":true,"values":{"candidate":{"F|LONG":"63/64","F|SHORT":"71/64","P|LONG":"139/64","P|SHORT":"135/64"},"candidate_domain_exact":true,"candidate_entries":4,"candidate_nested":true,"comparator":{"F|LONG":"63/64","F|SHORT":"71/64","P|LONG":"139/64","P|SHORT":"135/64"},"comparator_domain_exact":true,"comparator_entries":4,"conditions_on_full_z0":false,"equal_keys":true,"exact_reproduction":true,"key_fields":["context","action"],"marginalized_fields":["world","close_mode","cutoff","owner_departure","associated_tau"],"marginalized_owner_departure_tau_values":[100,104],"scope":"REGISTERED_16_BRANCH_SYNTHETIC_MIXTURE"},"z0_full_fields":["context","tau","remaining_horizon","focal_execution_phase","public_partner_phase","legal_duration_mask","behavior_version"]},"coverage":{"axes":["world","context","action","close","cutoff","owner_departure","version"],"per_world_stale":32,"per_world_valid":32,"shape":[2,2,2,2,2,2,2],"stale":64,"total":128,"valid":64},"deltas":{"W+|F":"-1/4","W+|P":"1/8","W0|F":"0","W0|P":"0","psi":"3/8"},"disposition":"NO_INCREMENT_OVER_REGISTERED_Z0_COMPARATOR","invariants":{"absolute_target_conserved_before_gradient":true,"explicit_nonzero_second_reward_kernel":true,"frozen_deltas_exact":true,"frozen_stop_gradient_vbar":true,"interrupt_over_natural":true,"one_score_release_tombstone_per_realization":true,"owner_departure_identity_escrow":true,"raw_expected_score_matches_analytic":true,"registered_z0_selector_value_conformance":true,"separate_policy_environment_clocks":true,"slot_excluded_from_identity":true,"stale_has_no_score_or_release":true,"terminal_over_horizon":true,"w0_paired_physical_equality_zero_gradient":true},"raw_expected_scores":{"W+|F":{"settings":8,"value":"-3/160"},"W+|P":{"settings":8,"value":"9/640"},"W0|F":{"settings":8,"value":"0"},"W0|P":{"settings":8,"value":"0"}},"schemas":{"DecisionIdentity":["episode_id","source_owner_epoch","own_boundary_index","behavior_version"],"EventRecord":["event_id","identity","slot_index","event","before","after","policy_clock","environment_clock"],"ReleaseRecord":["identity","target","release_clock"],"TombstoneRecord":["identity","final_state","target","reason"]},"terminal":"REGISTERED_Z0_SELECTOR_VALUE_CONFORMANCE","timing_tensor":{"axes":["world","context","action","close","cutoff","owner_departure"],"entries":64,"frozen":true,"shape":[2,2,2,2,2,2],"tau_values":[100,104]}}
```
