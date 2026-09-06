# B01 first independent training-seed result and scientific intake

On the new N7 same-distribution task, both real learners improved native recovery after training.
MAPR gained .204128 and DIRECT .188659 in aggregate R_fail_60, each above the card's descriptive
.10 MEI. MAPR's final advantage over DIRECT was only .015469; both learners remained below fixed
BCRH on recovery and the other native service metrics. This is a bounded B learning observation,
not MAPR-specific or stable superiority. Select one independent paired training-seed follow-up.

## E0 evidence, comparison and rule applied

Object: `VNFC-N7-DIRECT-RETURN-B01`, class B/EXPLORE. Frozen science is the B01 science card;
the formal02 execution supplement and formal01 intake select the fault-stack option and remaining
wall bound. Source `33e08f440c2117dcfd9457d825f42fef7b38ccd7`; training seed 2026090501,
evaluation seed 2026090502; namespace `VNFC-N7-DIRECT-RETURN-B01-20260905`. Formal01 and formal02
are attempts at the same training seed, not two independent samples.

Read the complete CM `VNFC_N7_DIRECT_RETURN_B01_FORMAL02_TECHNICAL_ACCEPTANCE_20260905.md`
at `9f4d8bd79` and its independent saved-output reconciliation at `c77783b31`. Read all saved
training/evaluation/curve arrays, summary/configuration/exposure and final log; read the external
time and memory evidence against the card. Raw evidence is `evidence/b01_formal_20260905_02/`.
CM and the independent reader reconstructed native endpoints/reward, pairing, all five contrasts,
zone summaries, recovery contexts and counts with no material discrepancy. The six checkpoints
were written/read by the actual runner; the independent reader checked metadata but did not
reopen remote checkpoint bytes. DM does not convert that boundary into an independent byte claim.

Evidence spec 11.8.3 applies verbatim: "When the question is learning performance, prefer a small
follow-up with one or two new independent training seeds using the same comparison and evaluation."
It further states: "Preserve every seed, failure, curve and exposure; do not run until all signs
are positive." And: "One training seed cannot estimate training-seed population uncertainty;
resampling units must respect shared data, folds and actual independence."

The card's applicable reading is: "If learners improve but remain below BCRH, or recovery trades
away other service, report the learning and losses separately." The .10 MEI is descriptive;
it is not a requirement that every contrast or zone pass. No result branch or checkpoint was
changed after observation. Evidence-spec 11.8.7 leaves formal01 incomplete and its fault unresolved;
the trustworthy complete formal02 output has its own bounded reading.

DM computed checkpoint/zone means and paired contrasts from the saved rows in
`evidence/b01_dm_intake_20260905/checkpoint_means.csv` and `paired_contrasts.csv`.
The scientific-tools `summarize_runs.py` was applied to `independent_run_scores.csv`, which has
one final score per actual training arm/seed, not episode or checkpoint pseudo-replicates.
Its `independent_run_summary.json` correctly reports n=1 and unavailable training-seed SD.
These were read-only calculations of existing output, with no new simulation, test or profiling.

## Complete actual exposure and receipts

One unannounced loss leaves seven survivors from eight pre-loss executors. Public observations,
entity/role identities and corrected physical masks/actions connect the event to each shared
learner's four-token decisions. Each trajectory retains six post-loss decisions and the complete
120-second post-loss process, with 240 native ticks including prehistory. Actual PPO updates use
the unshaped terminal J_ext = .5 R_fail_60 + .5 U_total; there is no BCRH imitation/oracle label.
MAPR and DIRECT share allowed information and paired exogenous worlds. BCRH is the fixed native
reference; its fieldwise information equality with learner tensors has not been established.

| Completed quantity | MAPR | DIRECT | BCRH |
| --- | ---: | ---: | ---: |
| Independent training instances | 1 | 1 | 0 |
| Collect/update rounds | 64 | 64 | 0 |
| Complete training episodes | 2048 | 2048 | 0 |
| Joint training transitions | 12288 | 12288 | 0 |
| Optimizer steps / backward calls | 2048 / 2048 | 2048 / 2048 | 0 |
| Initial/midpoint/final evaluation episodes | 192 | 192 | 64 fixed |
| Final relative parameter displacement | .292124237 | .256308923 | n/a |

The parsed 4096 training rows, 448 evaluation rows and 128 curve rows total **4544 complete
episodes and 1,090,560 native ticks**. Each round has 192 transitions and 32 optimizer steps
(four epochs × eight minibatches of 24). Each learner checkpoint has 32 episodes per failed zone.
DIRECT's residual output parameter norm moved from 0 to .4019159714; evaluation residual logit
RMS moved from 0 to 4.2525973724 to 11.4421253281. It is an actually updated and learning generic
comparator, not an inactive control; these activity readings alone do not prove optimal competence.

Task `vnfc_b01_formal_33e08f440_20260905_02`, node `wsl_4070`, detached cwd
`/home/wu/hmasd-worktrees/vnfc_b01_formal_33e08f440_02`, completed exit 0. Fresh admission passed
with **15,294,115,840 bytes** physical/effective available memory. Complete external wall was
**388.75s**, aggregate user 387.89 + system .64 = **388.53 CPU-s**; runner through publication
388.165651326s. Maximum RSS 568,284 KiB is the observed maximum. The selected fault handler
reported no fatal event. Formal01+02 spent **476.61 wall / 468.78 CPU-s**, within the 2700 total.
Including the two measured non-target checks gives 502.22 wall / 494.57 CPU-s; earlier diagnostics
retain their separately incomplete timing. No cost is silently assigned zero.

The previous 282.611s planning estimate understated actual complete wall by 106.139s (about 37.6%).
This does not breach the selected 2612s remaining cap or establish a cause for the timing change.
For future identical work, final stdout's full cost law using this run's maximum observed units
projects **431.170369s**: MAPR 170.353471, DIRECT 201.228809, BCRH 46.377076, shared setup/worlds/
overhead/publication 13.211012s. It is a conditional estimate, not a guaranteed bound. Actual
phase and complete costs remain distinct. No engineering source budget was exceeded; the sole
scope addition was the selected built-in fatal-stack observation, with no new code or test.

## Results under the unchanged reading rule

| Aggregate checkpoint/reference | R_fail_60 | U_total | U_intact | J_ext |
| --- | ---: | ---: | ---: | ---: |
| Both learners initial | .059531250 | .154786287 | .093529717 | .107158768 |
| MAPR midpoint | .224127604 | .411992072 | .414746657 | .318059838 |
| DIRECT midpoint | .197148438 | .383747768 | .408452663 | .290448103 |
| MAPR final | .263658854 | .511674267 | .543194726 | .387666560 |
| DIRECT final | .248190104 | .508634901 | .541729516 | .378412503 |
| BCRH fixed | .305481771 | .559850706 | .593343649 | .432666238 |

| Frozen primary contrast | Aggregate | Zone 1 | Zone 2 | Aggregate descriptive episode SE |
| --- | ---: | ---: | ---: | ---: |
| MAPR final minus initial | +.204127604 | +.261197917 | +.147057292 | .017111614 |
| DIRECT final minus initial | +.188658854 | +.233125000 | +.144192708 | .013919579 |
| MAPR minus DIRECT final | +.015468750 | +.028072917 | +.002864583 | .013380398 |
| MAPR final minus BCRH | -.041822917 | -.040260417 | -.043385417 | .013597778 |
| DIRECT final minus BCRH | -.057291667 | -.068333333 | -.046250000 | .015687090 |

The paired SEs are descriptive spread-of-episode-contrast quantities conditional on this seed
and the fixed balanced panel, as reported by the runner. They are not training-seed uncertainty,
a population interval, an equivalence test or a new significance gate. The terminal checkpoint
remains primary even where an intermediate coordinate is larger (DIRECT zone-2 recovery).

Both learners improved U_total, U_intact and J_ext relative to initialization in both zones.
This seed's recovery learning is not accompanied by a loss on those particular comparisons.
However, both final learners trail BCRH on all four metrics, aggregate and in each failed zone.
MAPR versus DIRECT also has tradeoffs: zone-1 U_intact is -.005180, while zone-2 U_total is
-.003992 and J_ext -.000564 despite a small positive recovery contrast. No safety/exclusivity
flags were recorded in these episodes; that supports no general safety or deployment claim.

Strongest support: real same-distribution N7 training yielded native learning gains in both
arms and zones, with substantial parameter movement and complete primary publication.
Strongest contradiction to MAPR-specific value: DIRECT also learned, the MAPR recovery advantage
is small relative to the declared .10 scale, and BCRH remains stronger. A generic shared-policy
learning effect is therefore a live explanation. The result does not identify which change from
historical R02 caused improvement: training roster, exposure and execution context were not
independently manipulated. No cross-N transfer, exact headroom, unique mechanism or stable
superiority claim follows. The headroom record remains incomplete and does not hold exploration.

DM prediction on the original card favored a positive learning gain in at least one arm over
MAPR exceeding BCRH by .10. This seed matches that qualitative prediction: both gains are positive
and MAPR is below BCRH. No probability calibration is inferred. Owner prediction: not taken
(unattended); current review instructions are empty. Historical negative/quarantined results,
the check01 HMAC error, formal01 SIGSEGV and preserved core remain unchanged and unexplained.

## Decisions this intake produces

| Option | Consequence | Recommendation |
| --- | --- | --- |
| A. One independent paired training-seed follow-up with the same comparison | Observe whether the learning gains and small relative differences persist in one new training/evaluation draw; retain all signs and losses | Recommended and selected |
| B. Run two new seed pairs immediately | Buys more variation now, but spends twice the work before the next informative reading; a second follow-up is not yet needed for this exploratory decision | Not selected |
| C. Retune, perform exact headroom/search or demand full mechanism diagnosis first | Changes the comparison or buys an unnecessary prerequisite before checking the observed learning signal across a new training draw | Not selected |

**Owner-delegated decision (unattended, 2026-09-03 instruction): A.** Tier: object;
kind: selection; provenance: OWNER_DELEGATED; reversible: yes; owner flag: none.
DM recommendation for the owner: 保持现有完整比较，只追加一个独立训练种子对；单次900秒，
并计入原2700秒累计预算，保留全部正负结果。
This follows the accepted learning mechanism and existing B ladder; it is not C promotion,
direction recast or a Portfolio investment/lifecycle decision. Only one additional seed pair is
selected, not unlimited positive-seed filling. Recasts remain 2 and sequencing remains Root's.

The selected card is `VNFC_N7_DIRECT_RETURN_B01_SEED02_CARD_20260905.md`: fresh training seed
2026090503 and evaluation seed 2026090504, the same namespace/actual source, unchanged 64×32
training and full fixed comparison, one new 900-second complete invocation bound. This bound
is newly selected inside the original cumulative 2700 total: 476.61 already spent, at most
1376.61 after the selected follow-up. It is not a new 2700 allocation. The actual 388.75s and
conditional 431.17s law motivate 900s headroom for observed cost variation without another timing
experiment. Unused budget authorizes no further seed or retry.

CM executes only after the new card/selection is committed and pushed, with fresh remote admission,
and returns every outcome, actual exposure, cost and any failure. No extra smoke, test or Pro round
is required for unchanged source and scientific computation. The Chinese brief is at
`docs/research/portfolio/owner/briefs/variable_n_fleet_churn/2026-09-05_B01-seed01.md`;
Root integrates the shared ledger, brief/decision/new-card items and the supplied owner packet.
The next discriminator is the same five primary contrasts on one new independent training draw.
