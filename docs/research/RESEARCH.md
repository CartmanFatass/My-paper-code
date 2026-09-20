# HMASD research index

The only current view of the research programme (constitution section 4). States:
`exploring`, `confirming`, `reserve`, `archived`. One line of standing per active direction,
with evidence links; nothing here is retranscribed from older records.

**Owner pause: lifted** 2026-09-18 about 17:55 PDT by the owner in the Claude session on the WSL
host ("我们继续研究"). It had been in force since 2026-09-15 22:23 PDT ("Prepare to pause"). The
first execution batch is FSD B01 exactly as frozen; no other DM slot is filled by this resumption.

2026-09-19 owner parallel-work choice: Claude continues FSD; the current Codex session directly
owns the reopened UCOPE feedback-renewal K branch. FOLR stays idle. Each lead owns its notebook,
code and experiments; UCOPE does not wait for FSD's scientific result. See
[UCOPE scope and prospective batch](candidates/ucope/NOTES.md).

## Active

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `flexible_skill_duration` | Does an unfixed skill duration k help on the UAV host against a matched-information baseline? | confirming | Claude session (current lead; a Codex DM may take it, never both) | Frozen object [FSD_MATCHED_INFORMATION_BASELINE_B01](candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md): D1280 versus central-input flat, six selection plus ten confirmation fits, MEI .05 J, no established headroom. The card stands in for the claim note. It calibrates the baseline; it does not test an interruption benefit. Resumed 2026-09-18: CF comparator and B01 runner implemented, independently reviewed and accepted; stage 0 complete (six CF tuning fits, committed `SELECTION.json` selects multiplier 0.5); stage 1 complete 2026-09-19 (ten fits, all terminal, reduced): mean G = +0.290 J over five blocks, interval [+0.161, +0.418], five of five positive, read by card section 6 as `D_REFERENCE_ABOVE` with `INTERVAL_POSITIVE`; the selected flat learner declines over training (descriptive, no label change); the object is ended. Exploratory follow-up `FSD_COORDINATOR_BATCH_B02` (six fits, complete 2026-09-19): D1280 versus D128 coordinator batch on the same five blocks, mean M = -0.025 J, interval [-0.117, +0.067], no detectable difference, D128 rises in five of five blocks, the D1280 rerun reproduces B01 bit for bit; the batch law is dropped as an explanation of D1280's standing. Exploratory `FSD_FLAT_ENTROPY_B03` (six fits, complete 2026-09-19): the flat learner's evaluation decline was its entropy bonus inflating the action noise (`lambda_l` .05; std 1.0 to about 4.7); at .005 and .0005 the decline is gone and J45 rises from .105 to .28-.29 on three blocks, D1280 still above on all three (difference about .15, three blocks, values tried on the evaluation blocks, no size claim); but the flat actor barely moves from initialisation under any setting and does not learn over 45 rollouts, so the comparator is not yet competent. Zero-fit inspection 2026-09-19: the low-level sampler's minibatch is 32 sequences (320 agent-steps, 2,250 optimizer steps per rollout, advantages normalised per minibatch) and the flat learner's surrogate does not improve (mean policy loss about 0 against -0.026 for D). Exploratory `FSD_FLAT_UPDATE_B04` (six fits, package screen, complete 2026-09-19): the best flat setting with 1,200-sequence minibatches (60 steps per rollout) at rates 1e-4 and 5e-4 on three blocks changes nothing: surrogate still about zero, actor displacement still below .1, late-window J -.036 and -.007 against CF_E0005, D1280 above on three of three (about .17-.20, no size claim); all three predictions failed, the gradient-noise explanation is weakened, and the flat comparator is still not a learning baseline. Seen but not predicted: the flat critic does not fit (value loss .07-.30 against below .01 for D). Next, zero fits: inspect what the two low-level critics are asked to fit (return horizon, skill-boundary bootstrap, reward scale); notebook [NOTES.md](candidates/flexible_skill_duration/NOTES.md), code map in [HANDOFF_2026-09-16_matched_information_baseline](candidates/flexible_skill_duration/HANDOFF_2026-09-16_matched_information_baseline.md). |
| `vap_folr_core` | After membership changes, can organising the history a continuing agent may legitimately access beat a competent generic recurrent baseline? | exploring | Codex DM | Idle after completed cache A01 and cumulative Pro synthesis; no live operation or selected successor. All three cache contrasts were adverse (mean -2.087265625); this does not establish history redundancy or UAV value. The owner now assigns the Codex session to UCOPE. Latest accepted [notebook at cd3b97ab](https://github.com/CartmanFatass/My-paper-code/blob/cd3b97ab7982ac5efec86eace09d33328be841fa/docs/research/candidates/vap_folr_core/NOTES.md) is preserved on the published FOLR branch. |
| `ucope` | Can feedback-conditioned KEEP/END of a UAV velocity commitment improve native return over ordinary feedback and fixed renewal? | exploring | Codex session (direct DM) | B02–B06 complete; 27 related development fits plus older T/L. B03 provisionally favored simpler B over R; B04 B-G stayed mixed (mean -0.00506645), with no established advantage or equivalence. B05 frozen mean-agreement C did not meet retention and is not carried into threshold tuning or learning; its conditional mean-deployment gains never established universal de-noising benefit. B06, authorized by the owner as the third batch, completed six ordinary-G fits at 2048 episodes each plus 768 final evaluations: initial sigma .5 versus 1 gave primary mean-deployment gains +0.09028229 / +0.05237898 / +0.08565095 (mean +0.07610407), and sampled-deployment gains in all three pairs (mean +0.05794360). Lower scale persisted; all models learned and evaluation weights stayed fixed. Retain .5 as exploratory ordinary-controller preparation at this exposure, with no optimal-scale or population-ranking claim. In 8942 its on-policy training J was lower in all eight blocks; G1 mean-minus-sampled signs were mixed. Independent raw/tensor reconstruction and scientific critique pass. Exact simple models distinguish gradient-variance and sampled-objective effects without diagnosing B06. Next, prepare B07 as a conditional practical screen: three new Bhalf fits against the three retained Ghalf checkpoints, with fresh paired evaluation and Bhalf_sampled minus Ghalf_mean primary. Selection of sigma on these Ghalf instances remains explicit. Exact temporal models distinguish smoother command increments from lower marginal noise. B07 preparation is implemented and independently reviewed: 17 synthetic tests pass, all three actual retained input sets validate without native work. Its concrete request is three additional fits (12 to 15 total), pending owner allocation; the original deadline remains. All 12 authorized fits are consumed, all native handles terminal by 2026-09-20 10:01:17 UTC, both Pro answers complete; no further native batch under the window ending 2026-09-21 04:06:07 UTC. Direct DM owns [NOTES.md](candidates/ucope/NOTES.md) and PR #28; scheduler paused, Claude FSD independent. |

## Reserve

| Direction | State | Note |
| --- | --- | --- |
| `tail_return_distributional_learning` | reserve | B01 positive retained, B02 inside the MEI, Pro review of B02 never started ([DIRECTION.md](candidates/tail_return_distributional_learning/DIRECTION.md)). Codex Root may start a DM for it under the three-DM soft ceiling when a discriminating idea exists; no obligation. The reserve list changes only by an owner-triggered Portfolio review. |

## Archived (investment only, not scientifically disproved)

Each keeps its `DIRECTION.md` and evidence under `candidates/<direction>/`; code under
`experiments/candidates/` stops being maintained. `acvc` left the set on 2026-09-16 with its
[closing memo](candidates/acvc/ACVC_CLOSING_MEMO_20260916.md) queued for the next review.

`active_post_churn_population_flow_identification`, `actuator_conditioned_partial_sharing`,
`acvc`, `capability_bound_semantic_currentness`, `commitment_residual_triggered_options`,
`contention_aware_decentralized_communication`, `cross_play_compatible_population_learning`,
`degraded_incumbent_shadow_handover`, `ec4g_r1`, `eociv_lite`,
`expressibility_gated_renewal_credit_relay`, `finite_resource_relational_inductive_efficiency`,
`learned_counterfactual_agent_credit`, `metric_ground_transport_allocation`, `orbit_shadow_read`,
`recct_lite`, `roster_consistent_latent_exploration`, `scope_1s`,
`semigroup_consistent_duration_model_policy`, `variable_n_fleet_churn`, `vsp_02`,
`vsp_03`, `vsp_c1`.

## Historical overhead reference

Retained from adoption; current constitution section 9 does not require monthly updates or owner-hour accounting.

| Month | Governance-only commits / unique result-bearing run summaries | Completed, read confirmation studies / owner-hour | Note |
| --- | --- | --- | --- |
| reference, 2026-09-02 to 09-16 | 33 docs-touching commits per run summary (older, broader definition; not re-audited) | N/A (no completed confirmation study) | transition reference only, not comparable with later rows |
