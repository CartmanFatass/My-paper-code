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

2026-09-20 owner parallel-work choice: an independent Codex Root coordinates three new FSD-adjacent
directions, each with its own Codex DM: termination-rule experience reuse, learning under joint
skill/teammate drift, and information-refresh timing. They may use fixed behaviourally explicit
skills or an independent host and do not wait for Claude's label-content study; such results do
not establish that the current HMASD learned skills are effective. Cross-duration/clock-perturbation
generalisation is retained only as an unstarted candidate from the owner's supplied proposal.

## Active

| Direction | Question | State | Lead runtime | Standing and next step |
| --- | --- | --- | --- | --- |
| `flexible_skill_duration` | Does an unfixed skill duration k help on the UAV host against a matched-information baseline? | confirming | Claude session (current lead; a Codex DM may take it, never both) | Frozen object [FSD_MATCHED_INFORMATION_BASELINE_B01](candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md): D1280 versus central-input flat, six selection plus ten confirmation fits, MEI .05 J, no established headroom. The card stands in for the claim note. It calibrates the baseline; it does not test an interruption benefit. Resumed 2026-09-18: CF comparator and B01 runner implemented, independently reviewed and accepted; stage 0 complete (six CF tuning fits, committed `SELECTION.json` selects multiplier 0.5); stage 1 complete 2026-09-19 (ten fits, all terminal, reduced): mean G = +0.290 J over five blocks, interval [+0.161, +0.418], five of five positive, read by card section 6 as `D_REFERENCE_ABOVE` with `INTERVAL_POSITIVE`; the selected flat learner declines over training (descriptive, no label change); the object is ended. Exploratory follow-up `FSD_COORDINATOR_BATCH_B02` (six fits, complete 2026-09-19): D1280 versus D128 coordinator batch on the same five blocks, mean M = -0.025 J, interval [-0.117, +0.067], no detectable difference, D128 rises in five of five blocks, the D1280 rerun reproduces B01 bit for bit; the batch law is dropped as an explanation of D1280's standing. Exploratory `FSD_FLAT_ENTROPY_B03` (six fits, complete 2026-09-19): the flat learner's evaluation decline was its entropy bonus inflating the action noise (`lambda_l` .05; std 1.0 to about 4.7); at .005 and .0005 the decline is gone and J45 rises from .105 to .28-.29 on three blocks, D1280 still above on all three (difference about .15, three blocks, values tried on the evaluation blocks, no size claim); but the flat actor barely moves from initialisation under any setting and does not learn over 45 rollouts, so the comparator is not yet competent. Zero-fit inspection 2026-09-19: the low-level sampler's minibatch is 32 sequences (320 agent-steps, 2,250 optimizer steps per rollout, advantages normalised per minibatch) and the flat learner's surrogate does not improve (mean policy loss about 0 against -0.026 for D). Exploratory `FSD_FLAT_UPDATE_B04` (six fits, package screen, complete 2026-09-19): the best flat setting with 1,200-sequence minibatches (60 steps per rollout) at rates 1e-4 and 5e-4 on three blocks changes nothing: surrogate still about zero, actor displacement still below .1, late-window J -.036 and -.007 against CF_E0005, D1280 above on three of three (about .17-.20, no size claim); all three predictions failed, the gradient-noise explanation is weakened, and the flat comparator is still not a learning baseline. Seen but not predicted: the flat critic does not fit (value loss .07-.30 against below .01 for D). A Pro critic pass (and a local comparison) then withdrew several of the DM's diagnostic inferences and found a construction defect: the CF actor reads the held global state in raw metres with no normalisation. Exploratory `FSD_FLAT_INPUT_SCALE_B05` (zero-fit probe plus three fits, complete 2026-09-19): unscaled, the state block is all of the first layer's input, GRU gates are 98 % saturated and the actor is insensitive to its own observation and identity from initialisation, and the trained CF_E0005 ends at its untrained level; with the coordinates scaled to the observations' convention (nothing else changed) the actor moves 7.5 times as far, the surrogate improves, J rises about .10 from the untrained level on three of three blocks, and D1280 stays above on three of three (about .10 in the late window, untuned flat learner, blocks reused, no size claim). B01's label stands as read but its meaning is narrowed: its CF was a defective comparator and +0.29 J is not a matched-information gap estimate; CF_S is the flat construction from here. D state probe B06 (zero fits, 2026-09-19): the untrained D1280 coordinator sees its observations and the raw state about as well as with the state pre-scaled (post-norm tokens; no consistent sensitivity difference on three blocks), so no scaled-state D; D1280 rises about +.23 J from its untrained level against CF_S's +.10. Exploratory `FSD_PERSISTENCE_B07` (closed 2026-09-20 at four started fits of six: two complete, two `D_K1` fits lost to the node's out-of-memory killer with no score, retries withdrawn, two fits unused): the D1280 rerun with a read-only behaviour capture is bit-identical; with every skill redrawn every training step (caps of 1, `config.k` held) the one block that has it attains the same late-window J as the recorded D1280 (.457 against .452), a higher training return, and the same paths, coverage and near-white executed actions although labels change ten times as often; the persistent-mode explanation of D's rise is weakened and the label may carry little behavioural content (its effect on the action mean at fixed input is unmeasured; no checkpoint). 2026-09-20 owner division: Claude owns the skill object and its learning, Codex the team-conditioned termination question (draft on `codex/team-conditioned-termination`). Next (Claude): label content at fixed weights — D1280 rerun with final weights saved, then zero-fit probes of the label's effect on the action mean and of J under frozen/random label rules — before any adaptive-termination comparison on this foundation; notebook [NOTES.md](candidates/flexible_skill_duration/NOTES.md), code map in [HANDOFF_2026-09-16_matched_information_baseline](candidates/flexible_skill_duration/HANDOFF_2026-09-16_matched_information_baseline.md). |
| `vap_folr_core` | After membership changes, can organising the history a continuing agent may legitimately access beat a competent generic recurrent baseline? | exploring | Codex DM | Idle after completed cache A01 and cumulative Pro synthesis; no live operation or selected successor. All three cache contrasts were adverse (mean -2.087265625); this does not establish history redundancy or UAV value. The owner now assigns the Codex session to UCOPE. Latest accepted [notebook at cd3b97ab](https://github.com/CartmanFatass/My-paper-code/blob/cd3b97ab7982ac5efec86eace09d33328be841fa/docs/research/candidates/vap_folr_core/NOTES.md) is preserved on the published FOLR branch. |
| `ucope` | Can feedback-conditioned KEEP/END of a UAV velocity commitment improve native return over ordinary feedback and fixed renewal? | exploring | Codex session (direct DM) | B02–B07 complete; 30 related development fits plus older T/L. B04 scalar B-G stayed mixed (mean -0.00506645); B05 mean-agreement C was not retained. B06 initial sigma .5 versus 1 improved final ordinary mean controllers on all three pairs (mean +0.07610407); retain this exploratory preparation at 2048 episodes, without an optimal-scale or population claim. B07's three new Bhalf fits against the exact retained Ghalf inputs all exited normally at source 088d0ca32, last exit 2026-09-20 11:03:17 UTC. Fixed sampled-B-minus-mean-G primary: -0.07869852 / -0.02032542 / -0.01943386 (mean -0.03948593). Mean-B-minus-mean-G is mixed: -0.06646396 / +0.01146420 / +0.01229523; the latter two contrary panels do not rescue the primary. Active copying and learner movement rule out nonactivation; favorable training blocks in 8942 and mixed differential extraction prevent uniform training-loss or temporal-noise explanations. Independent raw/tensor reconstruction and scientific criticism pass. Leave this scalar package idle; retain conditional uncertainty, Ghalf scale-selection provenance and the unidentified lawful-feedback opportunity. Post-result zero-fit analysis confirms randomized-gate identification in principle but finds that the saved arrays omit full lawful observations/recurrent states; a missing signal in the recorded projection cannot exclude history opportunity. Exact coupled and observational-equivalence models check that limit, without a native crossover or new predictor. No worthwhile native successor, rescue fit or further Pro is selected. All 15 owner-allocated fits are complete (B04 six, B06 six, B07 three); original deadline 2026-09-21 04:06:07 UTC unchanged, all native observers closed, both Pro answers complete. Direct DM owns [NOTES.md](candidates/ucope/NOTES.md) and PR #28; scheduler paused, Claude FSD independent. |

## Reserve

| Direction | State | Note |
| --- | --- | --- |
| `tail_return_distributional_learning` | reserve | B01 positive retained, B02 inside the MEI, Pro review of B02 never started ([DIRECTION.md](candidates/tail_return_distributional_learning/DIRECTION.md)). Codex Root may start a DM for it under the three-DM soft ceiling when a discriminating idea exists; no obligation. The reserve list changes only by an owner-triggered Portfolio review. |

## Archived (investment only, not scientifically disproved)

Each keeps its `DIRECTION.md` and evidence under `candidates/<direction>/`; code under
`experiments/candidates/` stops being maintained. `acvc` left the set on 2026-09-16 with its
[closing memo](candidates/acvc/ACVC_CLOSING_MEMO_20260916.md) queued for the next review.

2026-09-20 owner-directed feasibility review closed three formerly active directions instead
of retaining indefinite admission conditions. `termination_rule_experience_reuse` has no
independent identifiable object beyond ordinary history/belief off-policy learning in its fixed
scope; unsupported counterfactual branches remain unidentifiable ([notebook](candidates/termination_rule_experience_reuse/NOTES.md)).
`skill_teammate_drift_learning` reduced to bounded ordinary conditional regression, while its
relaxed-support native effect was unstable and no non-constructed successor remained
([notebook](candidates/skill_teammate_drift_learning/NOTES.md)). `skill_information_refresh`
was absorbed by a transparent value-of-information rule, with no concrete unknown interface
left for a learned scheduler ([notebook](candidates/skill_information_refresh/NOTES.md)). These
are current-scope investment closures, not universal impossibility claims.

`active_post_churn_population_flow_identification`, `actuator_conditioned_partial_sharing`,
`acvc`, `capability_bound_semantic_currentness`, `commitment_residual_triggered_options`,
`contention_aware_decentralized_communication`, `cross_play_compatible_population_learning`,
`degraded_incumbent_shadow_handover`, `ec4g_r1`, `eociv_lite`,
`expressibility_gated_renewal_credit_relay`, `finite_resource_relational_inductive_efficiency`,
`learned_counterfactual_agent_credit`, `metric_ground_transport_allocation`, `orbit_shadow_read`,
`recct_lite`, `roster_consistent_latent_exploration`, `scope_1s`,
`semigroup_consistent_duration_model_policy`, `skill_information_refresh`,
`skill_teammate_drift_learning`, `termination_rule_experience_reuse`,
`variable_n_fleet_churn`, `vsp_02`,
`vsp_03`, `vsp_c1`.

## Historical overhead reference

Retained from adoption; current constitution section 9 does not require monthly updates or owner-hour accounting.

| Month | Governance-only commits / unique result-bearing run summaries | Completed, read confirmation studies / owner-hour | Note |
| --- | --- | --- | --- |
| reference, 2026-09-02 to 09-16 | 33 docs-touching commits per run summary (older, broader definition; not re-audited) | N/A (no completed confirmation study) | transition reference only, not comparable with later rows |
