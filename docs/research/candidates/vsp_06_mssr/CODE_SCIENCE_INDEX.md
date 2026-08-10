# VSP-06 MSSR Sequence 12 code-science evidence index

This index preserves the historical Sequence-12 predecessor for
`CAND-VSP-06-MSSR@adversarial-revision-v8` and records the current VSP06-A1
production binding below.  The predecessor treatment
`MSSR-D0-PREACT-CLOSURE-AND-REACHABILITY` bound a fixed rational synthetic
S/P/F unit and inspected three then-current production surfaces; its
`CONTRACT_NOT_CLOSED` terminal is historical revision-scoped evidence, not the
current A1 conclusion.

## Exact raw-output binding

- Binding: `vsp06_mssr.preaction_closure.sequence12.v1`
- Producer: `experiments/candidates/vsp_06_mssr/preaction_closure_certificate.py`
- Proof-sized checks: `tests/experiments/candidates/vsp_06_mssr/test_preaction_closure_certificate.py`
- Command: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B experiments/candidates/vsp_06_mssr/preaction_closure_certificate.py`
- Encoding: one compact JSON object on stdout with recursively sorted object keys and no nondeterministic fields.

The following unique block is the full exact one-line stdout from the bound producer.

<!-- FULL_RAW_JSON_BEGIN -->
```json
{"active_binding":{"inspection_base_revision":"c628683ae04e102620246e440b0e8193955f1e3c","inspection_scope":[{"fact":"ordinary_hidden_state","path":"ha_ctse_process/standalone_agent.py"},{"fact":"recurrence_precedes_action_distribution","path":"ha_ctse_process/standalone_models.py"},{"fact":"recurrence_precedes_action_distribution","path":"ha_ctse_process/variable_roster_event_models.py"}],"missing_objects":["registered_selective_S_P_F_partition","authenticated_support_native_P","action_before_recurrence_first_logits"],"no_direct_binding_in_inspected_surfaces":true,"output":"CONTRACT_NOT_CLOSED","scope_limit":"bounded active-surface probes, not exhaustive repository absence"},"assignment_id":"vsp06_mssr_sequence_12_20260803","candidate":"CAND-VSP-06-MSSR@adversarial-revision-v8","claim_boundary":"fixed rational unit possibility plus bounded active-binding evidence only; no value, semantic-memory, transport, training, return, or deployment claim","complexity":{"hypothetical_transitions":0,"legal_masks":4,"supported_arms":2,"training":false},"manifest":{"dag":[["S","P"],["S","F"],["P","F"]],"inventory":[{"category":"persistent_cells","depends_on":["S"],"may_carry_p":false,"name":"slow_task_context_cell","owner":"unit.slow_context"},{"category":"persistent_cells","depends_on":["P"],"may_carry_p":true,"name":"partner_interaction_cell","owner":"unit.partner_interaction"},{"category":"persistent_cells","depends_on":["S","P","F"],"may_carry_p":true,"name":"fast_control_cell","owner":"unit.fast_control"},{"category":"caches","depends_on":["S","P","F"],"may_carry_p":true,"name":"fast_feature_cache","owner":"unit.fast_control"},{"category":"routers","depends_on":["S"],"may_carry_p":false,"name":"renewal_router","owner":"unit.clock"},{"category":"normalizers","depends_on":[],"may_carry_p":false,"name":"input_normalizer","owner":"unit.input"},{"category":"external_memory","depends_on":[],"may_carry_p":false,"name":"external_memory","owner":"unit.none"},{"category":"optimizer","depends_on":[],"may_carry_p":false,"name":"optimizer_state","owner":"unit.none"},{"category":"ema","depends_on":[],"may_carry_p":false,"name":"ema_state","owner":"unit.none"},{"category":"rng","depends_on":[],"may_carry_p":false,"name":"rng_state","owner":"unit.fixed_rng"},{"category":"actor_visible_side_channels","depends_on":[],"may_carry_p":false,"name":"actor_visible_metadata","owner":"unit.none"}],"state_layouts":[{"byte_offset":0,"byte_width":16,"dimension":1,"dtype":"rational_i64_pair_le","name":"S","owner":"unit.slow_context"},{"byte_offset":16,"byte_width":16,"dimension":1,"dtype":"rational_i64_pair_le","name":"P","owner":"unit.partner_interaction"},{"byte_offset":32,"byte_width":16,"dimension":1,"dtype":"rational_i64_pair_le","name":"F","owner":"unit.fast_control"}],"state_order":["F","S","P"],"worlds":{"CHANGE_F":{"F":"0","P":"1","S":"7"},"CHANGE_P":{"F":"0","P":"0","S":"7"},"CHANGE_S":{"F":"0","P":"0","S":"2"},"SAME":{"F":"3","P":"1","S":"7"}}},"outputs":["P_PREACTION_RESIDUAL_PATH_EXISTS","GATE_EXACTLY_FACTORIZED","CONTRACT_NOT_CLOSED"],"raw_output_binding":"vsp06_mssr.preaction_closure.sequence12.v1","synthetic_unit":{"arms":[{"delta_kb":["1/2","-1/2"],"historical_p":"-1","keep_action1_probability":0.2689414213699951,"keep_logits":["7/8","-1/8"],"policy_equivalent":false,"rebuild_action1_probability":0.5,"rebuild_logits":["3/8","3/8"],"support_weight":"1/2"},{"delta_kb":["-1/2","1/2"],"historical_p":"1","keep_action1_probability":0.7310585786300049,"keep_logits":["-1/8","7/8"],"policy_equivalent":false,"rebuild_action1_probability":0.5,"rebuild_logits":["3/8","3/8"],"support_weight":"1/2"}],"current_rebuild_p":"0","gate":{"output":"GATE_EXACTLY_FACTORIZED","rows":{"CHANGE_F":{"g_fact":[0,1,1],"g_mssr":[0,1,1],"mask":[0,1,1]},"CHANGE_P":{"g_fact":[0,1,0],"g_mssr":[0,1,0],"mask":[0,1,0]},"CHANGE_S":{"g_fact":[0,0,0],"g_mssr":[0,0,0],"mask":[0,0,0]},"SAME":{"g_fact":[1,1,1],"g_mssr":[1,1,1],"mask":[1,1,1]}}},"no_state_model_optimizer_rng_update":true,"output":"P_PREACTION_RESIDUAL_PATH_EXISTS","registered_x0":{"provenance":"x0_unit_star","q_p":"-1/2","x0_partner":"-1","x0_public":"1/2","x0_self":"1"}},"terminal":"CONTRACT_NOT_CLOSED","treatment":"MSSR-D0-PREACT-CLOSURE-AND-REACHABILITY"}
```
<!-- FULL_RAW_JSON_END -->

## Fixed synthetic unit

The unit registers S/P/F as rational one-dimensional cells with explicit owners, dimensions, dtypes, byte offsets and widths. Its complete inventory names persistent cells, caches, routers, normalizers, external memory, optimizer, EMA, RNG and actor-visible side channels. The dependency graph is exactly `S->P`, `S->F`, `P->F`; every declared descendant closure must exactly equal the transitive DAG/inventory closure. Legal `(F,S,P)` masks are exactly SAME `111`, CHANGE_F `011`, CHANGE_P `010`, and CHANGE_S `000`. Initializers are current-free (`N_P=N_F=0`) and `N_S=2` reads only frozen schema/policy-generation constants. Historical `S=7`, so SAME/CHANGE_F/CHANGE_P retain 7 while only CHANGE_S resets S to 2.

The same registered `X0` and provenance supports historical `P=-1` and `P=+1`, each with weight `1/2`; environment, RNG and non-target state are exact matches. The deterministic full-current rebuild reads all four registered action-visible current fields and returns `B_P(x*)=0`. With beta=1, the exact centered residuals are `[1/2,-1/2]` and `[-1/2,1/2]`; KEEP action-1 probability is `sigmoid(beta*P)` and rebuild probability is `1/2`. This supports only the unit-fixture possibility label `P_PREACTION_RESIDUAL_PATH_EXISTS`.

The independently written `G_MSSR` and frozen factorized null agree on every legal mask, so the honest gate result is `GATE_EXACTLY_FACTORIZED`. No gate novelty is claimed.

## Historical predecessor active binding boundary

The commit-scoped probe is limited to these active surfaces at unchanged production base revision `c628683ae04e102620246e440b0e8193955f1e3c`:

- `ha_ctse_process/standalone_agent.py`: ordinary `low_actor_hxs` recurrent storage.
- `ha_ctse_process/standalone_models.py`: registered actor recurrence precedes action-distribution construction.
- `ha_ctse_process/variable_roster_event_models.py`: registered actor recurrence precedes action-distribution construction.

At that predecessor revision, those bounded active-surface probes found no
registered selective S/P/F partition, authenticated support-native P, or
action-before-recurrence first-logit expression.  Their historical terminal was
`CONTRACT_NOT_CLOSED`; it is neither a current-source conclusion nor an
exhaustive repository-absence claim.

## VSP06-A1 joint production binding (2026-08-09)

`experiments/candidates/vsp_06_mssr/joint_production_binding.py` registers the
zero-policy A1 production-factory probe for
`CAND-VSP-06-MSSR@adversarial-revision-v8`.  The production consumer is
`VariableRosterEventCore.apply_transaction -> _process_frontier` under the
explicit `mssr_joint_spf_pre_recurrence_v1` action-path identity.  That single
path validates the retained owner-private P ledger, constructs the typed
S/P/F partition owned by `unit.slow_context`, `unit.partner_interaction`, and
`unit.fast_control`, and makes `EventCommitmentPolicy.first_logits` consume all
three before the GRU recurrence.  Its post-action partner write remains the
only P writer.  The ordinary default continues to use the original
post-recurrence `logits` path.

The focused test constructs two legal transaction histories: source-specific
initial interactions write different authenticated P; temporary leave plus a
terminal old source and common replacement source removes the historical
current-source difference; rejoin retains P while selectively renewing F.
Both histories then reach byte-identical current non-P actor context, action
set, order, source and production path with different authenticated P.  Their
final action is the deterministic argmax of the complete production kernel;
no teacher action is supplied.  The registered CLI performs no dynamic policy
execution and reports zero environment,
policy, learner, trainer, optimizer, evaluation, environment-RNG and action-RNG
activity; deterministic production-factory construction is reported separately;
dynamic history execution is technical-test evidence only.

Public implementation/test locators:

- `ha_ctse_process/variable_roster_event.py`
- `ha_ctse_process/variable_roster_event_models.py`
- `experiments/candidates/vsp_06_mssr/joint_production_binding.py`
- `scripts/run_vsp06_a1_joint_production_binding.py`
- `tests/experiments/candidates/vsp_06_mssr/test_joint_production_binding.py`

Claim boundary: A-level production binding and legal-history matched-support
support only.  No learner, training, return, algorithm-effect, B/C, promotion,
retirement, sibling-direction, or deployment conclusion is licensed.

## Historical predecessor claim boundary

The predecessor's smallest conclusion was: a pre-action P residual path was
mechanically possible in its fixed rational unit and its gate was exactly
factorized, while the production surfaces inspected at that revision did not
close the MSSR contract.  It is retained only as predecessor provenance.

Technical acceptance is proof-sized: all manifest, closure, illegal-mask, initializer, current-rebuild, support, side-channel, action-order, no-update, residual-null, gate-equality, production-probe, stable-CLI, source-size and index-binding checks must pass.
