# CBSC-OMRC-B01 metrics-only and Convergence specification

Status: `PRO_BOUND / IMPLEMENTATION_READY_WITH_NULL_DERIVED_FIELDS`

This specification records the third decision of the persistent CBSC Innovator for the already
selected `CBSC-OMRC-B01 / CBSC-DYNAMIC-CACHE-2R-1C-v1` B/EXPLORE object. It is a responsibility and
evidence-publication clarification, not a new scientific object. The host, learner, arms, tokens,
adapters, RNG, PPO, motif tapes, seeds, budgets, claim ceiling, and literal laws in
`CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md` do not change.

- Decision: `FINAL_CLASSIFIER_DECISION=METRICS_ONLY_CONVERGENCE_CLASSIFIES`.
- Implementation readiness: `YES_WITH_NULL_DERIVED_AND_BRANCH_FIELDS`.
- Remaining ambiguity: none for implementation or lossless raw-evidence publication; derived
  scientific interpretation is intentionally deferred.
- Request: `cbsc-online-b-innovator-20260901-03`.
- Persistent conversation: `6a96a6c0-e918-83e8-a0c0-9dc9222dce1c`.
- Complete response:
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/capability_bound_semantic_currentness/cbsc-online-b-innovator-20260901-03/RESPONSE.md`.
- Response SHA-256:
  `7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7`.

## 1. Interpretation boundary

B1/B2 engineering owns implementation-unique observations, complete paired curves, support
indexes, exact RAW-competence inputs, and mechanical conformance. It owns no AUC reduction,
diagnostic rate/effect, scientific threshold, branch priority, B2 trigger, promotion decision, or
scientific polarity. Those interpretations belong only to the persistent
`em:capability_bound_semantic_currentness:convergence` node.

The seven names `PRELIMINARY_SEMANTIC_CURRENTNESS_SIGNAL`,
`GENERIC_FACTORIZATION_OR_CONDITIONING`, `PREDICTIVE_INDEX_SUFFICIENT_ON_HOST`,
`NULL_AT_THIS_BUDGET`, `INSTABILITY`, `ADVERSE_COUNTEREXAMPLE`, and
`INVALID_OR_NONIDENTIFYING` are non-executable interpretive vocabulary. They are not predicates and
have no engineering-owned priority or tie law. An implementation manifest's `scientific_branch`,
`scientific_polarity`, `promotion_eligible`, and `b2_extension_trigger` values are always literal
null. A later Convergence decision writes its principal interpretation to a separate decision
record and explains any overlap.

`normalized trapezoidal return AUC` is not currently bound. Checkpoints `[0,12,24,48]` remain raw
identities, but engineering chooses neither x/y normalization, split or panel pooling, observational
unit reduction, pairing, seed aggregation, nor missing/nonfinite handling. For every
`(run_name,attempt_id,seed,arm,checkpoint_update,evaluation_split,tape_id)`, publish the exact
undiscounted return. For fixed `(run,seed,arm,split,tape)`, the four observations form the paired raw
curve `[R(0),R(12),R(24),R(48)]`. Missing checkpoints/tapes, duplicate keys, or nonfinite returns make
the attempt mechanically unreadable; never impute, drop, carry forward, or zero-fill. Numeric zero
is an observation; null means unassigned.

Every named action/currentness diagnostic is likewise deferred. Engineering publishes exact truth,
policy action, potential ledger, motif/twin identity, event order, body age, and support, but no
numerator, denominator, eligible-support rule, panel scope, split pooling, per-seed aggregation,
checkpoint reduction, paired unit, minimum support, zero-denominator rule, effect, or interpretation.
Observed support zero is integer `0`; a zero-support rate remains null.

## 2. Canonical orders and raw records

Canonical categorical orders are:

- run: `0=CBSC-OMRC-B1-THREE-SEED-SCOUT`, `1=CBSC-OMRC-B2-TWO-SEED-STABILITY`;
- arm: `0=STRUCT-CURRENTNESS-GRU`, `1=RAW-GRU`, `2=PI-GRU`,
  `3=DERANGED-CURRENTNESS-GRU`;
- split: `0=TRAIN`, `1=EVAL_STOCHASTIC`, `2=EVAL_MOTIF`;
- checkpoints: `0,12,24,48`;
- scientific action: `0=SERVE`, `1=REFRESH`, `2=SAFE_FALLBACK`.

The actor's `WAIT` remains learner action index zero but is not a scientific decision action. Seeds,
tapes, opportunities, transitions, updates, PPO epochs, and minibatches sort numerically ascending.
Raw rows are authoritative; indexes and counts never replace them.

### 2.1 Shared tape transitions

Store each arm- and checkpoint-independent tape once, keyed by
`(run_order,seed,split_order,tape_id,transition_index)`. Required fields are `object_id`,
`literal_binding_spec_sha256`, `run_name`, `attempt_id`, `seed`, `split`, `episode_id`, `tape_id`,
`tape_sha256`, nullable `motif_family/motif_receiver/motif_slot`, `transition_index`,
`opportunity_id`, `event_order_position`, `event_kind`, exact 17-byte `primitive_token_bytes`, and
`primitive_token_sha256`. The complete 152-token sequence must be byte-recoverable. Compressed
storage also records byte offset, byte length, codec identity, and digest.

### 2.2 Evaluator decision truth

Store arm- and checkpoint-independent truth keyed by
`(run_order,seed,split_order,tape_id,opportunity_id)`. Each row contains:

```text
target_receiver presented_slot
current_owner_0 current_owner_1 current_epoch_0 current_epoch_1
current_need_0 current_need_1 carrier_0_receiver carrier_1_receiver

slot_0_body_owner slot_0_body_epoch slot_0_carrier
slot_0_addressed_receiver slot_0_payload_source_receiver slot_0_content
slot_0_native_neutral slot_0_issue_opportunity slot_0_issue_event_position
slot_1_body_owner slot_1_body_epoch slot_1_carrier
slot_1_addressed_receiver slot_1_payload_source_receiver slot_1_content
slot_1_native_neutral slot_1_issue_opportunity slot_1_issue_event_position

presented_body_owner presented_body_epoch presented_body_carrier
presented_body_addressed_receiver presented_body_payload_source_receiver
presented_body_content presented_body_native_neutral
presented_body_issue_opportunity presented_body_issue_event_position
request_active request_need access_gated presented_carrier_current_receiver

nonneutral_truth address_match_truth payload_source_match_truth content_match_truth
owner_match_truth epoch_match_truth capability_match_truth overall_valid_truth

serve_decision_reward serve_settlement_reward serve_total_value
refresh_decision_reward refresh_settlement_reward refresh_total_value
safe_fallback_decision_reward safe_fallback_settlement_reward safe_fallback_total_value
oracle_action oracle_value

owner_event_realized owner_event_subject owner_event_position
semantic_event_realized semantic_event_subject semantic_event_position
capability_event_realized capability_event_carrier capability_event_position
body_event_realized body_event_slot body_event_position
presented_body_age_opportunities
last_target_owner_change_opportunity last_target_semantic_change_opportunity
```

Oracle fields are evaluator facts, not scientific polarity.

### 2.3 Policy decisions and raw curves

Policy decisions use key
`(run_order,seed,checkpoint_update,split_order,tape_id,opportunity_id,arm_order)` and contain
the following exact fields:

```text
checkpoint_sha256 parameter_sha256
adapter_state_before_bytes adapter_state_after_bytes adapter_output_bytes
legal_action_mask actor_logits_fp32_bits legal_action_probabilities_fp32_bits
critic_value_fp32_bits selected_action selected_action_log_probability_fp32_bits
observed_decision_reward observed_settlement_reward observed_opportunity_return
hidden_state_before_sha256 hidden_state_after_sha256  # optional replay digests
```

Hidden-state digests may replace duplicated arrays only when checkpoint+tape+implementation permit
deterministic replay within the output cap.

Per-tape curves use key `(run_order,seed,split_order,tape_id,arm_order)` and contain exactly:

```text
episode_return_update_0 episode_return_update_12
episode_return_update_24 episode_return_update_48
episode_decision_reward_sum_update_0 episode_settlement_reward_sum_update_0
episode_decision_reward_sum_update_12 episode_settlement_reward_sum_update_12
episode_decision_reward_sum_update_24 episode_settlement_reward_sum_update_24
episode_decision_reward_sum_update_48 episode_settlement_reward_sum_update_48
```

They contain no mean, AUC, normalized curve, arm contrast, interval, or sign.

### 2.4 Motifs, supports, and training exposure

The motif/twin index is shared across arms/checkpoints. For families 0..6, pair
`(seed,tape_id,q)`, `q=0..11`, maps member A/B to opportunities `2q/2q+1`. For family 7, pair
`(seed,tape_id,block)`, `block=0..2`, maps GAP1/GAP6 to `base+1/base+6`. Record motif family,
receiver, slot, pair ID, member role/tape/opportunity, counterpart tape/opportunity, intervention
family/side, designated diagnostic member, and `pair_complete`; do not write action/oracle/return
differences or a correct-pair judgment.

Exact motif field names are `motif_family`, `motif_receiver`, `motif_slot`, `pair_id`, `member_role`,
`member_tape_id`, `member_opportunity_id`, `counterpart_tape_id`,
`counterpart_opportunity_id`, `intervention_family`, `intervention_side`,
`designated_diagnostic_member`, and `pair_complete`.

Publish mechanical support counts over the complete signature `(split,motif_family_or_null,
motif_side_or_null,request_active,access_gated,presented_body_native_neutral,address_match_truth,
payload_source_match_truth,content_match_truth,owner_match_truth,epoch_match_truth,
capability_match_truth,overall_valid_truth,oracle_action,presented_body_age_opportunities)`. A second
table adds `(arm,checkpoint_update,selected_action)`. By seed and motif family, separately publish
`expected_pair_count`, `complete_pair_count`, `missing_pair_count`, and `duplicate_member_count`.

For every training decision keyed by `(run,seed,arm,training_episode_id,opportunity_id)`, record
`rollout_update`, `policy_version`, `selected_action`, `legal_mask`, `selected_log_probability`,
`decision_reward`, `settlement_reward`, and `opportunity_return`. Each training episode records
`episode_return`, `action_count_serve`, `action_count_refresh`, and
`action_count_safe_fallback`. Every Adam step records `rollout_update`, `ppo_epoch`,
`minibatch_index`, `ordered_episode_ids`, `actor_loss_fp32_bits`, `value_loss_fp32_bits`,
`entropy_fp32_bits`, `total_loss_fp32_bits`, `preclip_gradient_norm_fp32_bits`,
`postclip_gradient_norm_fp32_bits`, `optimizer_step_count`, and `parameter_sha256_after_step`. Loss
magnitudes have no polarity.

### 2.5 Publication order

Sort tape transitions by `(run,seed,split,tape,transition)`; truth by
`(run,seed,split,tape,opportunity)`; policy evaluation by
`(run,seed,checkpoint,split,tape,opportunity,arm)`; curves by `(run,seed,split,tape,arm)`; motifs by
`(run,seed,tape,pair,member)`; training decisions by `(run,seed,arm,episode,opportunity)`; optimizer
steps by `(run,seed,arm,update,epoch,minibatch)`; and audits by
`(run,attempt,seed_or_minus_one,arm_or_minus_one,audit_code)`. Never omit adverse or inconvenient
rows.

## 3. Literal-null derived fields

Every B1/B2 manifest contains these literal-null fields:

```text
heldout_mean_return terminal_mean_return mean_oracle_regret normalized_return_auc
struct_minus_raw_auc struct_minus_deranged_auc struct_minus_pi_auc
oracle_action_accuracy invalid_serve_rate missed_serve_rate
unnecessary_refresh_rate missed_refresh_rate inactive_fallback_accuracy
owner_twin_flip_accuracy semantic_twin_flip_accuracy correct_swapped_sensitivity
capability_specificity retention_gap_effect owner_event_order_effect
semantic_event_order_effect clear_competent_null separation_from_deranged
separation_from_pi residual_concentrated_in_gated material_instability
adverse_seed catastrophic_seed promotion_eligible scientific_branch
scientific_polarity b2_extension_trigger
```

The AUC metadata fields `return_auc_x_divisor`, `return_auc_y_normalization`,
`return_auc_y_scale`, `return_auc_split_scope`, `return_auc_panel_pooling`,
`return_auc_episode_aggregation`, `return_auc_seed_aggregation`, `return_auc_pairing_rule`,
`return_auc_missing_rule`, `return_auc_nonfinite_rule`, and
`return_auc_scientific_interpretation` are also literal null. For each named diagnostic, its
numerator, denominator, eligible-support rule, panel scope, split pooling, per-seed aggregation,
checkpoint reduction, paired unit, minimum support, zero-denominator rule, effect, and
interpretation are literal null. Do not substitute zero, empty string, `UNKNOWN`, `UNRESOLVED`, or
a locally selected branch.

## 4. Mechanical conformance and RAW competence

Engineering must compute only the nonpolar fields `mechanical_attempt_complete`,
`mechanical_conformance_pass`, `scientific_packet_readable`, and `blocking_audit_codes`.
Conformance fails on: failed fresh 4-GiB physical/effective admission; resource/output cap breach;
missing or duplicate inventory; any literal token/mask/preamble/event/NOOP/motif/adapter/PRF/
initialization/GRU/PPO/sampling mismatch; cross-arm tape mismatch; train/evaluation overlap; unequal
work/evaluation exposure; non-FP32 or prohibited modes; any nonfinite value; recurrent-reset,
adaptation-free evaluation, or checkpoint-round-trip failure; learner leakage; illegal actions;
incomplete twins; or publication/digest failure. Publish a preserved diagnostic incident, never a B
branch.

The only allowed derived scientific-precondition Boolean is per-seed `raw_competence_pass`, computed
at RAW checkpoint 48 on `EVAL_STOCHASTIC` tapes 0..31 only:

1. In ascending tape order, exact mean RAW return strictly exceeds both `ALWAYS_REFRESH` and
   `ALWAYS_SAFE` evaluated on those same tapes; ties fail and missing/nonfinite inputs leave the
   gate unestablished.
2. Across eligible decisions—active request, OPEN access, nonneutral body, and true address,
   payload-source, content, OWNER, and epoch matches—`N_easy>0` and RAW chooses SERVE in at least
   `0.80` inclusive. Capability match is not required under OPEN.
3. Evaluator-oracle support includes at least one SERVE, REFRESH, and SAFE_FALLBACK, and RAW selects
   at least two distinct scientific actions across its 768 terminal stochastic decisions.
4. Mask violation, nonfinite, missing-record, and duplicate-record counts are all zero.

`raw_competence_pass` is the conjunction of those reference-return, easy-OPEN, oracle-support,
nonconstant-action, and mask/numerical components. It is mechanical and nonpolar. If any B1 RAW seed
is false or null, engineering cannot declare STRUCT supported or contradicted and B2 cannot launch.

## 5. B0 and Convergence routing

`B0_NONPOLARITY=ABSOLUTE`. Mark every B0 evaluator value `scientific_eligible=false`,
`classifier_eligible=false`, `threshold_tuning_eligible=false`, `b2_trigger_eligible=false`, and
`promotion_eligible=false`. B0 may audit arithmetic, replay, masks, checkpoints, publication, and
telemetry; it may not select a formula, denominator, scope, support law, threshold, branch, endpoint,
seed, budget, comparator, or B1/B2 trigger, and never enters a B1/B2 scientific estimate. Failure
permits only a preserved outcome-blind instrumentation repair under the unchanged object.

After three complete, valid B1 seeds, engineering sets `scientific_branch=null`,
`b2_extension_trigger=null`, `promotion_eligible=null`, and `convergence_required=true`. EM sends the
complete packet to `em:capability_bound_semantic_currentness:convergence`, which alone returns:

- `RUN_FIXED_B2_STABILITY`: run the already fixed seeds `21161,21179` for an outcome-informed B
  stability extension;
- `STOP_AFTER_B1`: stop for its recorded host-bounded interpretation; or
- `NO_B2_INTERPRETATION_BLOCKED`: B1 is incomplete/invalid or RAW competence is unestablished, and
  B2 is not a repair substitute.

If B2 is authorized, Convergence first records every AUC, diagnostic, support, threshold, and
classification formula that it will apply to B2, labeled
`outcome_informed_from_B1=true, confirmatory=false`; the formula is unchanged across both B2 seeds.
B1 is not retroactively prospective. After B2, EM must make a second Convergence call. Engineering
never populates a scientific branch.

The Convergence packet contains the complete create-only manifest; every raw table and audit above;
RAW and both fixed-reference per-tape returns; all RAW-competence components and inputs; every B0/B1/
B2 incident and invalid attempt separated from valid facts; digests; null fields; all individual
seeds/checkpoints/tapes/pairs/supports/outliers; `.01`, `.02`, and `.03`; and the exact B claim
ceiling. Nothing adverse or inconvenient may be deleted or replaced.

## 6. Claim ceiling and falsifier

The falsifier remains competent RAW matching or exceeding STRUCT without predicted OWNER/epoch
currentness corrections, or DERANGED producing the same native-return and twin-response pattern as
STRUCT. The necessary observation is a complete real recurrent-PPO run with same-information RAW,
held-out stochastic and motif tapes, work/information/exposure parity, every per-seed/checkpoint
return, raw action/currentness/twin facts, all support and adverse observations, and no
implementation-selected scientific reduction.

The maximum claim is one preliminary recurrent-PPO learning signal, competent null, instability
diagnosis, generic-conditioning explanation, predictive-index sufficiency observation, or adverse
counterexample on `CBSC-DYNAMIC-CACHE-2R-1C-v1` under the fixed three-to-five-seed B exposure. It is
not stable superiority, representation necessity, universal RAW inferiority, natural prevalence,
paid acquisition, authentication, receiver credit, variable-population/lifetime or general MARL
value, UAV transfer, safety, deployment, direction convergence/closure, or reinterpretation of the
exact factorial or `CBSC-LR01=UNRESOLVED`.

## Addendum — 2026-09-02 (section-11 recast)

The frozen body above is unchanged. Per evidence spec §11.6, this addendum records which of its
boundaries stopped gating on 2026-09-02 under owner decisions 3 and 7 of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4 and
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`. The full record is
`CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md`.

- §1 and §3 (lines 48-52 and 192-217), the metrics-only delegation and the literal-null derived
  field list — superseded for **descriptive** quantities. The runner computes from its own
  materialized tables and publishes a `descriptive_curves` block (schema
  `cbsc_omrc_b01_b1_descriptive_curves_v1`): per `(seed, arm, split)` mean/min/max held-out episode
  return at each checkpoint; per `(seed, arm, split, checkpoint)` SERVE/REFRESH/SAFE_FALLBACK counts
  and serve rate; per `(seed, arm)` training action counts; per `(seed, arm)` an exposure line
  (Adam step count, whether the parameter digest moved, post-clip gradient-norm magnitudes); and the
  mechanical RAW-competence flags. §11.6 demotes the consumer-recompute boundary as a gate that
  "does not change a B decision"; a descriptive mean of 64 held-out returns is not an
  interpretation.
- Everything the section reserves for Convergence is still reserved. No AUC normalization, panel
  pooling, seed aggregation, pairing rule, missing/nonfinite rule, arm contrast, threshold, sign,
  branch, polarity, promotion flag or B2 trigger is computed by engineering. The manifest fields
  listed at lines 196-217 remain literal null and their validator is unchanged. The lossless
  15-table raw publication of §2 is unchanged.
- §4 (lines 219-247), mechanical conformance and RAW competence — **unchanged and still in force**,
  including the exact four-component `raw_competence_pass` predicate at its stated thresholds. Its
  resource-cap clause is read under the recast: a measured cap exceedance is recorded, only the wall
  cap stops a run, and missing resource telemetry downgrades to `resources_unmeasured` rather than
  failing conformance. Learner-side instrumentation failure still fails conformance and quarantines.
- §5 (lines 248-271), Convergence routing — `convergence_required` stays `true` in every B1 manifest
  as a recorded routing fact, and B1 still writes no branch. It no longer blocks
  `CBSC-OMRC-B2-TWO-SEED-STABILITY`, which the direction now sequences itself with the same
  `outcome_informed_from_B1=true, confirmatory=false` labelling. `B0_NONPOLARITY=ABSOLUTE` is
  unchanged.
- §6, the claim ceiling and falsifier — unchanged in every respect.
