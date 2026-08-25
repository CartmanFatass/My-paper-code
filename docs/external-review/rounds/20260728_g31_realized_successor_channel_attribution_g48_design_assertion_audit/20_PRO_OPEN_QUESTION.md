# External Pro: G48 realized-successor channel attribution design assertion audit

```text
semantic_author=research_operations_manager
artifact_scope=reviewer_visible_design_boundary
scientific_authority=external_pro
review_mode=DESIGN_ASSERTION_AUDIT
round=20260728_g31_realized_successor_channel_attribution_g48_design_assertion_audit
source_commit=9d5416d69051365e9da35e496949fabd8e9a1493
design_audit_compute=0
valid_iteration_cost=zero
```

You are External GPT-5.6 Pro, the exclusive scientific decision authority
inside this bounded design question. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from the pushed `source_commit`. Do not
implement code, run proof execution or formal compute, edit CDC, reactivate
G33, promote UAV, or select a different successor. Do not infer beyond the
stated G47 predecessor and the exact G48 boundary below.

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_CODE_SCIENCE_INDEX.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260728_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_FORMAL_RESULT.md`
- `docs/research/cdc/RESEARCH_DIRECTION_LEDGER.md`
- `docs/research/cdc/CONJECTURES.md`
- `docs/research/cdc/IDEA_PORTFOLIO.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_correction_recheck/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_code_science_alignment_correction_recheck/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/01_SHARED_SOURCE_MANIFEST.md`

No additional repository path is allowed.

## Exact G48 design assertion

Assess only whether a conclusion-bearing matched post-anchor comparison can be
frozen between:

- `NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR`: the accepted G47
  baseline-free route using immediate reward and realized-successor channels.
- `NATIVE6_G31_DUPLICATED_IMMEDIATE`: the identical baseline-free route with
  the successor channel replaced by a separately materialized duplicate of the
  immediate channel and no `G_(t+1)` value entering actor credit.

The only intended treatment is the complete realized-successor channel package.

Both arms retain exactly:

- accepted G40 common fast anchors, replicates 0, 1 and 2;
- accepted G41 no-slow projection;
- accepted G47 no-baseline-module projection;
- native-six no-carry actor and `log_std`;
- the same actor observations, active-set context, source ledgers, episode IDs,
  member-owned action noise, rewards and environment lifecycle;
- the same PPO clipping and likelihood semantics;
- the same actor parameter inventory, Adam hyperparameters, interaction and
  optimizer-step exposure;
- the same final-only actor checkpoint schema.

Training source is G32 capacity-8 fixed process. Evaluation source is G34-P0
fixed/random processes with capacities 6, 8 and 12 and `H=48`. Exclude
baseline/critic reintroduction, DB composition, recurrence change, actor
information change, source or reward change, G33 and UAV promotion.

## Exact target laws

Reference:
`x_t^I=r_t`, `x_t^S=G_{t+1}`, with the accepted realized-tail authority
`G_H=0` and `G_t=r_t+0.99G_{t+1}`.

Each channel is separately centered and independently RMS-scaled once from the
complete stored trajectory before both PPO passes. The reference actor
gradient is:

`d_REF = 0.5*(g_I + g_S) + g_E`

where the inherited common entropy gradient `g_E` is added once.

Null:

`x_t^{I1}=r_t`, `x_t^{I2}=r_t`

The two immediate rows are separately materialized and must be byte-identical
after the same centering and RMS rule. Its actor gradient is:

`d_NULL = 0.5*(g_I1 + g_I2) + g_E = g_I + g_E`.

The null must have all of these exact zero reads:

```text
realized_successor_read_into_actor_credit=0
realized_successor_read_into_actor_gradient_scale=0
realized_successor_read_into_checkpoint_selection=0
realized_successor_read_into_result_selection=0
successor_counterfactual_calls=0
```

The physical trajectory may contain rewards and terminals, but the null
actor-credit path may not construct or read `G_(t+1)`.

## Paired exposure and activation gates

Both complete paired trajectories are materialized before either update;
branch-start actor/log_std bytes are equal; actor Adam states are empty and
identically configured; both arms materialize two channel losses; both use two
PPO passes, one actor Adam step per pass, no clipping, no minibatches, no
optimizer reset, no baseline parameters and final-only checkpoints. The null
performs two immediate-channel backward constructions so loss-count and
channel-composition exposure match.

Using only the reference arm pre-update data, require:

- `RMS(z_S-z_I)>1e-6`;
- the reference credit direction
  `d_REF,credit=0.5*(g_I+g_S)` and null counterfactual direction
  `d_NULL,cf=0.5*(g_I+g_I)` are both nonzero when compared;
- their unit-direction distance is strictly `>1e-6`;
- immediate and successor gradients are finite and live;
- every registered actor group is finite in both channel rows and live in at
  least one reference channel.

Nonformal requires at least one active pass. Formal requires at least one
active pass in each accepted-anchor replicate 0, 1 and 2. The actual null
supplies no activation evidence. If normalized successor and immediate rows
are indistinguishable, or their counterfactual actor directions are collinear
throughout a required replicate, the package is operationally invalid rather
than evidence for channel removability.

The reference must pass the complete inherited access contract, including
delayed event-window and process-segment gates. A reference failure has
precedence over either successor-channel conclusion.

## Primary estimand, evidence and claim ceiling

For paired final random-deterministic episodes:

`Delta_succ = U_IMMEDIATE+SUCCESSOR - U_DUPLICATED_IMMEDIATE`.

Use materiality/noninferiority margin `0.05` and one confidence plan for all
absolute and comparative quantities. Register these component contrasts:
fixed deterministic utility per capacity; random deterministic utility per
capacity; fixed stochastic utility equal-capacity pooled; random stochastic
utility equal-capacity pooled; random event-window utility per capacity; random
process-segment utility per capacity; random-minus-fixed transport per capacity;
and minimum-replicate access.

Use one paired hierarchical whole-episode plan: formal bootstrap seed frozen
before implementation; 95-percentile intervals; no episode exclusions; equal
capacity weights; resample accepted-anchor replicate blocks then complete
episode IDs within replicate and capacity, retaining both arms and all mates.
Do not resample agents, primitive steps, events or channels independently.

Nonformal ceiling: replicates=1, branch_updates_per_arm=10,
environments_per_update=8, PPO_passes=2, evaluation_cells=24,
episodes_per_cell=6, training_transitions=7680,
evaluation_transitions=6912, total_real_transitions<=14592,
optimizer_steps<=40, wall_clock<=1200_seconds, bootstrap_resamples=250.

Formal ceiling: replicates=3, branch_updates_per_arm=100,
environments_per_update=8, PPO_passes=2, evaluation_cells=72,
episodes_per_cell=48, training_transitions=230400,
evaluation_transitions=165888, total_real_transitions<=396288,
optimizer_steps<=1200, wall_clock<=28800_seconds,
bootstrap_resamples=10000.

```text
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
```

A duplicated-immediate sufficiency result may support only removability of the
complete realized-successor channel package from this exact post-anchor G48-P0
route. A reference advantage may support only a source-local finite-budget
access or material-utility advantage over this exact null. Do not generalize
to future information universally or ordinary TEAM-GAE1 sufficiency.

## Frozen first-match outcomes

1. `INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48`
2. `SOURCE_OR_REFERENCE_ACCESS_FAILURE_G48`
3. `DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48`
4. `REALIZED_SUCCESSOR_CHANNEL_ADVANTAGE_G48`
5. `MIXED_UNDERPOWERED_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48`

Predicates: duplicated-immediate sufficiency requires both arms to pass the
complete access contract and every reference-minus-null primary/component UCB
to be <=0.05. Realized-successor advantage requires reference access and either
confident null access failure or `LCB95(Delta_succ)>0.05` with every
capacity-specific random-deterministic primary LCB strictly positive. Every
remaining operationally valid numerical pattern selects the mixed/underpowered
branch. No diagnostic may rescue or relabel an earlier branch. Equality at an
access or noninferiority boundary passes; material advantage remains strict.

## Required response sections

Return these sections in order:

1. `DESIGN_ASSERTION_CONFORMANCE`
2. `IDENTIFICATION_AND_DEPENDENCY_RESULT`
3. `COUNTEREXAMPLES_AND_CLAIM_CEILING`
4. `EVIDENCE_AND_COMPLEXITY_DISPOSITION`
5. `PORTFOLIO_AND_NEXT_ACTION`
6. `EXECUTABLE_BOUNDARY`
7. `中文简报`

Then return exactly one separate line:

`DESIGN_DISPOSITION=IDENTIFIABLE_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48`
or `DESIGN_DISPOSITION=DESIGN_MISMATCH`
or `DESIGN_DISPOSITION=SCIENTIFIC_AMBIGUITY`.

The response must contain all seven sections and exactly one disposition
line. Do not return only a generic audit token. The operator owns no scientific
interpretation, implementation, Git, browser transport or compute.
