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
| `flexible_skill_duration` | Does an unfixed skill duration k help on the UAV host against a matched-information baseline? | confirming | Claude session (current lead; a Codex DM may take it, never both) | Frozen object [FSD_MATCHED_INFORMATION_BASELINE_B01](candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md): D1280 versus central-input flat, six selection plus ten confirmation fits, MEI .05 J, no established headroom. The card stands in for the claim note. It calibrates the baseline; it does not test an interruption benefit. Resumed 2026-09-18: CF comparator and B01 runner implemented, independently reviewed and accepted; stage 0 complete (six CF tuning fits, committed `SELECTION.json` selects multiplier 0.5); stage 1 complete 2026-09-19 (ten fits, all terminal, reduced): mean G = +0.290 J over five blocks, interval [+0.161, +0.418], five of five positive, read by card section 6 as `D_REFERENCE_ABOVE` with `INTERVAL_POSITIVE`; the selected flat learner declines over training (descriptive, no label change); the object is ended. Exploratory follow-up `FSD_COORDINATOR_BATCH_B02` (six fits, complete 2026-09-19): D1280 versus D128 coordinator batch on the same five blocks, mean M = -0.025 J, interval [-0.117, +0.067], no detectable difference, D128 rises in five of five blocks, the D1280 rerun reproduces B01 bit for bit; the batch law is dropped as an explanation of D1280's standing. Exploratory `FSD_FLAT_ENTROPY_B03` (six fits, complete 2026-09-19): the flat learner's evaluation decline was its entropy bonus inflating the action noise (`lambda_l` .05; std 1.0 to about 4.7); at .005 and .0005 the decline is gone and J45 rises from .105 to .28-.29 on three blocks, D1280 still above on all three (difference about .15, three blocks, values tried on the evaluation blocks, no size claim); but the flat actor barely moves from initialisation under any setting and does not learn over 45 rollouts, so the comparator is not yet competent. Zero-fit inspection 2026-09-19: the low-level sampler's minibatch is 32 sequences (320 agent-steps, 2,250 optimizer steps per rollout, advantages normalised per minibatch) and the flat learner's surrogate does not improve (mean policy loss about 0 against -0.026 for D). Exploratory `FSD_FLAT_UPDATE_B04` (six fits, package screen, complete 2026-09-19): the best flat setting with 1,200-sequence minibatches (60 steps per rollout) at rates 1e-4 and 5e-4 on three blocks changes nothing: surrogate still about zero, actor displacement still below .1, late-window J -.036 and -.007 against CF_E0005, D1280 above on three of three (about .17-.20, no size claim); all three predictions failed, the gradient-noise explanation is weakened, and the flat comparator is still not a learning baseline. Seen but not predicted: the flat critic does not fit (value loss .07-.30 against below .01 for D). A Pro critic pass (and a local comparison) then withdrew several of the DM's diagnostic inferences and found a construction defect: the CF actor reads the held global state in raw metres with no normalisation. Exploratory `FSD_FLAT_INPUT_SCALE_B05` (zero-fit probe plus three fits, complete 2026-09-19): unscaled, the state block is all of the first layer's input, GRU gates are 98 % saturated and the actor is insensitive to its own observation and identity from initialisation, and the trained CF_E0005 ends at its untrained level; with the coordinates scaled to the observations' convention (nothing else changed) the actor moves 7.5 times as far, the surrogate improves, J rises about .10 from the untrained level on three of three blocks, and D1280 stays above on three of three (about .10 in the late window, untuned flat learner, blocks reused, no size claim). B01's label stands as read but its meaning is narrowed: its CF was a defective comparator and +0.29 J is not a matched-information gap estimate; CF_S is the flat construction from here. D state probe B06 (zero fits, 2026-09-19): the untrained D1280 coordinator sees its observations and the raw state about as well as with the state pre-scaled (post-norm tokens; no consistent sensitivity difference on three blocks), so no scaled-state D; D1280 rises about +.23 J from its untrained level against CF_S's +.10. Exploratory `FSD_PERSISTENCE_B07` (closed 2026-09-20 at four started fits of six: two complete, two `D_K1` fits lost to the node's out-of-memory killer with no score, retries withdrawn, two fits unused): the D1280 rerun with a read-only behaviour capture is bit-identical; with every skill redrawn every training step (caps of 1, `config.k` held) the one block that has it attains the same late-window J as the recorded D1280 (.457 against .452), a higher training return, and the same paths, coverage and near-white executed actions although labels change ten times as often; the persistent-mode explanation of D's rise is weakened and the label may carry little behavioural content (its effect on the action mean at fixed input is unmeasured; no checkpoint). 2026-09-20 owner division: Claude owns the skill object and its learning, Codex the team-conditioned termination question (draft on `codex/team-conditioned-termination`). Exploratory `FSD_LABEL_CONTENT_B08` (three fits plus zero-fit probes, complete 2026-09-20): the D1280 reruns with final weights saved are bit-identical on three of three; a fixed-weight panel reproduces exactly only on the host that trained it, so the probes ran on the node. The label is not inert (it moves the deterministic action by about .2 of the action std, roughly 18 m per step RMS, and replacing labels moves J by .02-.07 on every block), but uniform random labels score +.002 J on average against the coordinator's argmax and beat it by .065 on the weakest block, random every step equals random every 10, frozen equals as-trained, and a deterministic mid-cycle END re-selects the held label 63-89 % of the time: persistence is not where D's score comes from and the coordinator's selection has no demonstrated value (three blocks, one checkpoint each, no size claim). Claude's recommendation to Codex: no J/I/F termination comparison on this foundation yet; `uniform_every_10` becomes a required comparator for any later termination arm. Zero-fit `FSD_LABEL_MAP_B09` (2026-09-20, same checkpoints, node host): one label held by every agent for the whole episode gives J spanning .13-.22 across the six labels on the same worlds, so the labels are six distinct policies; on 772903 one label is best in 32 of 32 worlds (+.167 J over as-trained, lifting the weakest block to .521) and the coordinator executes it on 0.09 % of agent-steps; on the other two blocks the coordinator matches the best constant label; per-world best label adds at most .025 over the best single label; random mixtures score about the mean of the constants and team heterogeneity does not correlate with score. The defect is the high level's selection among six arms, not persistence, termination or role diversity; any later termination arm on this learner needs as-trained, random-every-10 and best-constant comparators (three blocks, one checkpoint each, no size claim). Zero-fit `FSD_LABEL_MAP_SAMPLED_B10` (2026-09-20): with low-level actions sampled as in training the constant-label spread is .080 / .133 / .073 J against .129 / .216 / .127 with mean actions, 12-25 times the sampled panels' replicate noise, rankings preserved (rank correlation about .79); action noise costs every label .05-.16 J but does not hide the label gap, so 'invisible under training noise' is rejected as stated. Open: whether the coordinator's own per-decision signal contains the ranking (one agent's label in a mixed team over a ten-step window) or is diluted below its advantage noise. Zero-fit `FSD_COORDINATOR_SIGNAL_B11` (2026-09-20): in four training-law rollouts per block at the saved weights, with the advantages computed exactly as the update computes them, the mean advantage by chosen agent label spreads .019-.024 against .058-.068 for the team label, which cannot affect behaviour (placebo, a sixth of the rows), eta-squared .0003-.0004 and a different best label in almost every rollout: the coordinator's own signal carries no usable ranking at the end of training; even a perfect-credit regression of ten-step segment reward on label counts finds only 4-12 % effects (R-squared at most .013) although the same labels held for an episode differ by 25-40 % of J. Working explanation: the labels are long-horizon policies valued through ten-step commitments redrawn for six agents from a near-flat law with a shared reward and a label-free baseline, so selection cannot be learned and the deployed argmax is arbitrary (the DM's declared E2a criterion was met by the letter and is withdrawn as miscalibrated; the placebo is the calibration). Next (Claude): zero-fit B12, the same collection at caps 10, 50, 100 and 500 with permutation and placebo calibration, to see at what commitment length a label becomes visible in its own credit; strongest alternative is a non-additive joint map (team assignment, Codex's question); notebook [NOTES.md](candidates/flexible_skill_duration/NOTES.md), code map in [HANDOFF_2026-09-16_matched_information_baseline](candidates/flexible_skill_duration/HANDOFF_2026-09-16_matched_information_baseline.md). |
| `vap_folr_core` | After membership changes, can organising the history a continuing agent may legitimately access beat a competent generic recurrent baseline? | exploring | Codex DM | Idle after completed cache A01 and cumulative Pro synthesis; no live operation or selected successor. All three cache contrasts were adverse (mean -2.087265625); this does not establish history redundancy or UAV value. The owner now assigns the Codex session to UCOPE. Latest accepted [notebook at cd3b97ab](https://github.com/CartmanFatass/My-paper-code/blob/cd3b97ab7982ac5efec86eace09d33328be841fa/docs/research/candidates/vap_folr_core/NOTES.md) is preserved on the published FOLR branch. |
| `ucope` | Can feedback-conditioned KEEP/END of a UAV velocity commitment improve native return over ordinary feedback and fixed renewal? | exploring | Codex session (direct DM) | B02–B07 complete; 30 related development fits plus older T/L. B04 scalar B-G stayed mixed (mean -0.00506645); B05 mean-agreement C was not retained. B06 initial sigma .5 versus 1 improved final ordinary mean controllers on all three pairs (mean +0.07610407); retain this exploratory preparation at 2048 episodes, without an optimal-scale or population claim. B07's three new Bhalf fits against the exact retained Ghalf inputs all exited normally at source 088d0ca32, last exit 2026-09-20 11:03:17 UTC. Fixed sampled-B-minus-mean-G primary: -0.07869852 / -0.02032542 / -0.01943386 (mean -0.03948593). Mean-B-minus-mean-G is mixed: -0.06646396 / +0.01146420 / +0.01229523; the latter two contrary panels do not rescue the primary. Active copying and learner movement rule out nonactivation; favorable training blocks in 8942 and mixed differential extraction prevent uniform training-loss or temporal-noise explanations. Independent raw/tensor reconstruction and scientific criticism pass. Leave this scalar package idle; retain conditional uncertainty, Ghalf scale-selection provenance and the unidentified lawful-feedback opportunity. Post-result zero-fit analysis confirms randomized-gate identification in principle but finds that the saved arrays omit full lawful observations/recurrent states; a missing signal in the recorded projection cannot exclude history opportunity. Exact coupled and observational-equivalence models check that limit, without a native crossover or new predictor. No worthwhile native successor, rescue fit or further Pro is selected. All 15 owner-allocated fits are complete (B04 six, B06 six, B07 three); original deadline 2026-09-21 04:06:07 UTC unchanged, all native observers closed, both Pro answers complete. Direct DM owns [NOTES.md](candidates/ucope/NOTES.md) and PR #28; scheduler paused, Claude FSD independent. |

## Reserve

| Direction | State | Note |
| --- | --- | --- |
| `tail_return_distributional_learning` | reserve | B01 positive retained, B02 inside the MEI, Pro review of B02 never started ([DIRECTION.md](candidates/tail_return_distributional_learning/DIRECTION.md)). Codex Root may start a DM for it under the three-DM soft ceiling when a discriminating idea exists; no obligation. The reserve list changes only by an owner-triggered Portfolio review. |

## Archived (investment only, not scientifically disproved)

Each keeps its notebook and recoverable code/run evidence; legacy directions also retain
their `DIRECTION.md`. Code under `experiments/candidates/` stops being maintained.
`acvc` left the set on 2026-09-16 with its
[closing memo](candidates/acvc/ACVC_CLOSING_MEMO_20260916.md) queued for the next review.

2026-09-20 owner-requested closure review: **UPHOLD_CLOSE for A, B and C**. This entry
supersedes the shared closure summary at
[`fe15893e9`](https://github.com/CartmanFatass/My-paper-code/blob/fe15893e99a1b3f5265c5d25f808749b6f0eb759/docs/research/RESEARCH.md).
Their ongoing research investment and maintenance are closed, with no selected successor,
waiting producer or open-ended re-entry task. The present lack of a worthwhile next
experiment does not establish that these research categories have no remaining scientific
questions. Positive findings and contrary evidence remain part of the archived knowledge.

- **A — `termination_rule_experience_reuse`: archived.** A01 supports ordinary multistep
  reuse over one-step; the selected extra trace correction showed no clear additional
  benefit. A02's long-commitment collector did not improve its prewritten primary endpoint;
  its favorable early panel is retained. The concrete incremental mechanisms examined
  currently supply no selected next comparison. Their ordinary-method reductions do not
  prove finite-sample optimality or exhaust termination-rule reuse. The zero-support
  identification limit does not cover finite missing coverage of a positive-support branch.
  [Final notebook, `6c1a38833`](https://github.com/CartmanFatass/My-paper-code/blob/6c1a38833a85a55574a0fba8714b51b38a4b988a/docs/research/candidates/termination_rule_experience_reuse/NOTES.md).
- **B — `skill_teammate_drift_learning`: archived.** B03's bounded early conditional-transfer
  benefit is retained. B04 also retains positive joint-response minus fixed full-fingerprint
  gains under relaxed support on all three blocks: +.001097060 / +.081054324 / +.085450278.
  It is the prewritten intervention contrast, `G_product - G_permuted`, that has mixed signs
  (+.025759620 / 0 / -.009575933): support repair did not reliably shrink that gain.
  Thus B04 weakens the support-repair explanation, not B03's positive observation.
  Full rank does not remove the ridge/prior-geometry confound, and B04 did not rerun recent
  fingerprint or additive comparators. Closure rests on the absence of a concrete next
  target beyond the constructed known-joint-law, stationary-response setup; ordinary
  conditional regression can itself be a useful scientific finding.
  [Final notebook, `efd26695a`](https://github.com/CartmanFatass/My-paper-code/blob/efd26695a9a223f953f614afdaafe87db9c8f92a/docs/research/candidates/skill_teammate_drift_learning/NOTES.md).
- **C — `skill_information_refresh`: archived.** Lawful timing value is retained. C03's
  original conditional gains survive, although its chosen freshness repair lost tasks;
  C04's stage rule beat the three frozen learned policies by 12 / 1 / 1 tasks on its panel.
  This supports ending that learning package, not global stage-rule optimality. In C05's
  fixed protocol the transparent VoI rule solves the timing decision; one learned history
  matched its exact return 479/90, versus 5 for the restricted stage/age/change family.
  No extra learned-scheduler value or multi-seed reliability was established. No concrete
  target interface and lawful feedback stream justify a selected successor now.
  [Final notebook, `089e21f36`](https://github.com/CartmanFatass/My-paper-code/blob/089e21f36fd51716bf15efde1abb3e4aca0100c5/docs/research/candidates/skill_information_refresh/NOTES.md).

These are current-scope investment closures, not general impossibility, equivalence or
UAV claims. Recorded training cost remains A: 15 fits, B: 57 fits, C: 4 fits; C03/C04 were
frozen-policy evaluations. This records correction adds no training or result execution,
and does not independently certify every underlying artifact. Closure is not attributed
to a fit allowance. The pinned notebooks and their code/run evidence remain on the
published direction branches and the integrated Root branch; only the shared index is
synchronized here.

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
