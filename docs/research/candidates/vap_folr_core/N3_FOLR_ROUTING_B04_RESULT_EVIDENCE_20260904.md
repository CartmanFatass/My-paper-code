# N3 FOLR B04 — result evidence

Date: 2026-09-04. Class: **B / EXPLORE**. Valid complete observation; no consumption state.
Card: `N3_FOLR_ROUTING_B04_SCIENCE_CARD_20260904.md`, frozen/pushed at `a5449da0d72094a7e1fbf3be3104f49fb6dd1a11`.
Launch source: `0f83132fb3484f8366eaaa5863559d203f0cb369`.
Result: **`B04_WITHIN_MEI`**. This is an exploratory finding on three fixed seeds and one host.

## 1. Observation and bounded reading

The TYPED minus GENERIC mean STALE_LOAD normalized native-return AUC is
**`0.0026041666666666665`**, inside the declared absolute MEI `0.05`.
Both learned arms attain mean final STALE_LOAD return `0.98828125`.
The continuing owner's legal information is useful: the RESET information-cut control
attains `0.5065104166666666`, while the simple same-information LATCH reaches
`0.9986979166666666`. RESET is not the same-information efficiency comparator.

| Seed | TYPED stale AUC | GENERIC stale AUC | Paired difference | TYPED / GENERIC final stale | RESET final stale | LATCH final stale |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 96041 | 0.87158203125 | 0.86962890625 | 0.001953125 | 0.9921875 / 0.9921875 | 0.5078125 | 1 |
| 96042 | 0.898681640625 | 0.89892578125 | -0.000244140625 | 0.9921875 / 0.9921875 | 0.50390625 | 0.99609375 |
| 96043 | 0.867431640625 | 0.861328125 | 0.006103515625 | 0.98046875 / 0.98046875 | 0.5078125 | 1 |

| Regime | TYPED mean AUC | GENERIC mean AUC | RESET mean AUC | TYPED / GENERIC final return |
| --- | ---: | ---: | ---: | ---: |
| CLEAN | 0.8720703125 | 0.8715006510416666 | 0.473388671875 | 0.9934895833333334 / 0.9921875 |
| STALE_LOAD | 0.8792317708333334 | 0.8766276041666666 | 0.4838053385416667 | 0.98828125 / 0.98828125 |

All three final writer sampled accuracies are one; expected rewarded-action probabilities
remain below one. `writer_weak=false`; `simple_control_headroom=false`: LATCH's mean final
advantage over the better learned routing arm is only `0.01041666666666663`, below `0.05`.
LATCH reused the paid writer and added zero receiver updates; it is an efficient simple
alternative, not a fourth matched training arm.

At the final checkpoint, GENERIC's mean STALE_LOAD action-kernel TV under an obsolete-bit
flip is `0.00023618467578974864`; TYPED and RESET are zero by their masks. This is a directly
observed low sensitivity to the stale input, consistent with the generic learner learning
to ignore it. TV alone does not establish value; the native-return comparison supplies it.

The unit physical upper minus the fixed-config generic terminal return is `0.01171875`
on STALE_LOAD and `0.0078125` on CLEAN. These are descriptive fixed-config gaps. No tuning
or model selection ran, so they are not relabelled as the tuned host headroom required by
the headroom convention. Historical B3 Phase R remains absent; B04 is a new B observation.

## 2. Rule applied verbatim

For a complete valid result, apply the first matching branch verbatim:

1. `B04_TYPED_SIGNAL`: `d >= 0.05` and at least two seed differences are positive.
2. `B04_GENERIC_SIGNAL`: `d <= -0.05` and at least two seed differences are negative.
3. `B04_WITHIN_MEI`: `abs(d) < 0.05`.
4. `B04_HETEROGENEOUS`: otherwise.

The first two predicates are false and the third is true. Thus the unique reading is
`B04_WITHIN_MEI`. Two positive seed signs do not override the MEI, and equal sampled terminal
returns do not imply exact policy equivalence. The rule is unchanged after the result.

## 3. Counts, curves and exposure

| Quantity | Actual | Card |
| --- | ---: | ---: |
| Seeds | 3 | 3 |
| Writer training episodes / updates | 24,576 / 384 | 24,576 / 384 |
| Routing training episodes / updates | 73,728 / 1,152 | 73,728 / 1,152 |
| Total training episodes / updates | 98,304 / 1,536 | 98,304 / 1,536 |
| Writer / routing / latch evaluation episodes | 6,912 / 41,472 / 1,536 | 6,912 / 41,472 / 1,536 |
| Total evaluated / complete episodes | 49,920 / 148,224 | 49,920 / 148,224 |
| Real primitive transitions | 444,672 | 444,672 |
| Final model+optimizer checkpoints | 12 | 12 |
| Final evaluation files / rows | 15 / 6,912 | 15 / 6,912 |
| Recorded evaluation points | 195 | 195 |
| Seed selections / parameter sweeps / model selections | 0 / 0 / 0 | 0 / 0 / 0 |

Every trained phase has updates 1–128 and evaluation points 0–128 every 16. The CSV
`N3_FOLR_ROUTING_B04_EVALUATION_CURVES_20260904.csv` retains all sampled and expected-return
evaluation curves, including individual seeds. Full training reward/loss curves remain in the
collected raw summary. All complete episodes execute the real three-transition B3 host.
Policy calls count actual batched role forwards, not WAIT transitions: each routing seed/arm
has 128 training and 18 evaluation calls for each of its five roles, plus two diagnostic calls
for each of four roles. The 4,608 final obsolete-flip kernel rows are diagnostic forwards only.

Actual final/initial parameter displacement ratios (float64 norm arithmetic):

| Seed | Writer | TYPED | GENERIC | RESET |
| --- | ---: | ---: | ---: | ---: |
| 96041 | 1.5876368623002 | 1.6078326353697274 | 1.6421824140559267 | 0.9006334750618166 |
| 96042 | 1.4471760019151876 | 1.8342035554031277 | 1.8452982092390346 | 1.1644816301931704 |
| 96043 | 0.8988417325015212 | 1.918138240566288 | 1.9800923557662662 | 1.162631470191767 |

The prospective nominal coordinate path was `3.2`; it was not a realized displacement bound.
Writer tensors are frozen and identical across each seed's three routing arms. CPU float32,
Adam settings, legal cue support, paired initialization/data/action tapes and separate fixed
evaluation tapes match the card. The standalone runner sets one CPU thread, recorded in its
configuration; cross-OS bit equality was never claimed. No treatment or budget changed in-run.

## 4. Receipts, machine cost and artifact locations

- Node: `wsl_4070`, SSH `hmasd-wsl-node`; detached cwd
  `/home/wu/hmasd-worktrees/cm-n3-folr-b04-20260904-a1`.
- Supervisor: `n3-folr-b04-full-20260904-a1`, PID `97387`, exit 0, terminal at
  `2026-09-04T22:09:13Z`; tracker observed it later at `22:09:55Z`.
- Exact command and technical acceptance: `N3_FOLR_ROUTING_B04_CM_RETURN_20260904.md`,
  final report commit `6f9e3716f1b8f0c3219320e57c68eafb92b31d0c`.
- Fresh node admission: `2026-09-04T22:08:30.583381Z`; physical and effective available
  memory both `12,932,308,992` bytes, above the `4,294,967,296`-byte floor.
- Relative output root: `temp/directions/vap_folr_core/exp/n3_routing_b04_full_20260904_a1/`.
  Original remote artifacts remain. The full collected copy is under the same relative root
  in `C:/Projects/HMASD-worktrees/cm-n3-folr-b04-20260904`.
- Full learner wall `40.371824955997` seconds; supervisor duration 43 seconds; peak RSS
  `484,229,120` bytes. Resources are measured. Actual phase train+evaluation wall: writer
  `8.5029`, typed `10.4839`, generic `10.1866`, reset `10.0354`, latch `0.3504` seconds.
- The prelaunch smoke projected `47.8191` seconds total and a maximum charged arm
  `27.3193` seconds, below 2,400/600-second caps. Actual full cost also fits; no arm dropped.
- One technical smoke used 6,400 complete episodes, 19,200 transitions and eight updates;
  its learner wall was `2.382219321` seconds and suite wall 4.69 seconds. These development
  counts are separate from the valid full result. One valid result was bought; total observed
  learner wall for smoke plus full is `42.754044276997` seconds. Agent token/USD use is not
  measured here. No hypothetical cross-direction reuse saving is booked.

`N3_FOLR_ROUTING_B04_RESULT_SUMMARY_20260904.json` preserves the rule inputs, seed metrics,
counts, actual exposure, cost coefficients and admission values. Root integrates source and
science commits; remote worktree commit identity remains the exact launch source.

## 5. Reconstruction, deviations and limits

CM's independent review found no material issue: 506 research-code lines, 178 runner lines,
23–26% orchestration, no engineering-scope section 4 addition or section 5 breach. The seven
smoke/rule/count/cost checks passed. CM verified final checkpoints including Adam step 128,
writer equality and all publication artifacts; full-endpoint publication coverage is now closed.

DM read the implementation against the card, the collected full summary and resource receipt,
recomputed all 6,912 final-row native rewards and regime means, and recomputed all recorded
writer/routing AUCs from the full curves. The reconstruction created no new learner run.
Tracker terminal event was acknowledged; CM collected without a second launch.

No scientific deviation, missing required learner measurement or quarantine occurred. A
pre-learner remote fetch was corrected to use the configured login/interactive network shell;
it created no result attempt or polarity. The historical B3 calibration gate and formal
validator machinery were not used as B launch conditions.

Strongest support for a narrow null is that all paired AUC differences are small with
near-unit generic terminal return and low stale-input sensitivity. Strongest contrary
observation is a positive early sampled mean gap at update 16 (`0.0221354167`) and two
positive seed AUC signs; this preserves small/transient effects below this card's MEI.
Three seeds, one scalar host and one update budget cannot establish exact equivalence or
close the broader state-retention/reconstruction agenda. Information retention matters here;
special typed masking has little measured incremental value at this exposure.
