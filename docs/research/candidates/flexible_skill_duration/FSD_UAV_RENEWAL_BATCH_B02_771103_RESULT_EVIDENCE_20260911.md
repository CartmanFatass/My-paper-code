# FSD UAV renewal batch B02 / 771103 — result evidence

## 1. Result and rule applied verbatim

**Valid complete B/EXPLORE; one new matched training pair; `opposite_sign`.**
The [card §8](FSD_UAV_RENEWAL_BATCH_B02_SCIENCE_CARD_20260911.md#8-new-rolling-allocation-771103--prospective-freeze-2026-09-11)
remains the prospective definition. Its applicable rule is quoted verbatim:

> - Mean difference < −.01: `opposite_sign`; an adverse new instance.

D0 mean native J is **0.4072901252402493** and I1280 is
**0.3948596946403985**. All 32 ordered I1280−D0 differences have mean
**−0.012430430599850807**, sample SD **0.10899371019760327** and conditional
episode SE **0.01926754789685166**. There are 16 positive and 16 negative
differences, no zeros; range −0.24384698682378197 to 0.1359835140131374.
The relative difference is −3.051984% of this D0 mean. The fixed branch uses
absolute .01 J.

The adverse mean lies only .0024304306 beyond the negative MEI boundary.
Conditional episode variation is substantial; the numeric branch is descriptive
and does not establish stable harm or population superiority of D0. This primary
contains one independent training pair, with 32 evaluations conditional on its
learned policies. [ORDERED_PRIMARY.csv](uav_renewal_batch_b02_771103_20260911/ORDERED_PRIMARY.csv)
retains every raw U, native J=6U/500 and ordered difference.
[PAIRED_ANALYSIS.json](uav_renewal_batch_b02_771103_20260911/PAIRED_ANALYSIS.json)
agrees with the runner's complete paired publication. The existing
[run summary](uav_renewal_batch_b02_771103_20260911/RUN_SUMMARY.json) uses one
selected endpoint per arm/training identity, correctly reports n=1 and leaves
training-run SD undefined. No older pair, checkpoint or episode is selected or
pooled into this primary.

## 2. Native components and separate training observations

The unchanged native objective is `.7*coverage + .3*quality - altitude_penalty`;
the source's existing `energy_penalty` field is its altitude term. All 32
component reconstructions agree with native J; reporting scale changes no reward.

| Final observable | D0 | I1280 | I1280−D0 |
| --- | ---: | ---: | ---: |
| Raw episode U | 33.940843770021 | 32.904974553367 | −1.035869216654 |
| Native J | 0.407290125240 | 0.394859694640 | −0.012430430600 |
| Coverage | 0.506087500000 | 0.491690000000 | −0.014397500000 |
| Quality | 0.178452068953 | 0.177971509140 | −0.000480559813 |
| Altitude penalty | 0.000506745446 | 0.002714758102 | +0.002208012656 |

Weighted coverage contributes −.01007825, quality −.00014416794378563914,
and the higher altitude penalty −.0022080126560651424. These sum to the native
loss. Lower coverage accounts for most of this observed contrast; the arithmetic
does not identify the causal origin of the learned motion.

| Rollout | D0 sampled training J | I1280 sampled training J | I1280−D0 |
| --- | ---: | ---: | ---: |
| 1 | 0.220379186061 | 0.228380652003 | +0.008001465942 |
| 2 | 0.174115188820 | 0.254337374936 | +0.080222186116 |
| 3 | 0.217501794080 | 0.255915583443 | +0.038413789363 |
| 4 | 0.327710210521 | 0.248947739101 | −0.078762471419 |
| 5 | 0.343742321454 | 0.305770066962 | −0.037972254493 |

I's first three sampled training means are higher and its last two are lower.
These observations remain separate from the final native endpoint and are not
extra evaluation panels or checkpoint-selection scores. The earlier two package
pairs had lower I means on their first two rollouts; those observations remain.

## 3. Mechanism exposure and bounded reading

Six UAVs observe partial service geometry and keep private recurrent state.
Own and partner motion affect later observations, while primitive velocity
remains reactive under held skills. I uses individual gap .25 and coordinator
batch 1280; authentic D0 uses infinity and batch 128. Team cap/clock 10,
reset/survivor behavior, primitive-time discount, segment credit, lower PPO,
private information and final evaluation are unchanged. The arms have separate
learners and RNG states; matching the evaluation law does not force identical
policy-induced trajectories.

I has **42413 individual training gap causes**, versus zero D0. Its valid joint
rows are 4729/4869/4951/5292/5050, totaling 24891 versus 4000, a 6.22275× ratio.
The actual coordinator law `15*sum ceil(M_r/batch)` gives 315 I calls
(60/60/60/75/60), versus 525 D0 calls (105 each rollout). Both have 11250 actor,
11250 critic, 75 team discriminator and 300 individual discriminator calls.
Every learner module moves and all five stages optimize. Fewer coordinator
calls do not equalize row/decoder work, gradient grouping or learned trajectories.

I training individual segments average 3.778/3.665/3.622/3.452/3.567 primitive
steps, versus 10 in D0. At final evaluation **both arms have zero individual
gap causes**, 32 reset events, 1568 team-cap events and 549 coordinator inference
calls. No extra individual renewal is observed in this final panel. That does
not isolate a batch effect: training data, credit and optimizer grouping also
differed. Evaluator segment storage is empty, so endpoint duration statistics
remain unmeasured; returns and decision counters are intact.

The prior I1280 gains **+.05697746721968016** and **+.206285904082309**
remain separately valid, with 24/32 and 32/32 positive episode contrasts.
The older batch128 losses **−.049670563167111874** and **−.035312725297886094**
retain their original meaning. The three allocated package pairs now have two
gains and one adverse observation under their own fixed rules. This new result
weakens recurrence of the local gain; it neither erases the earlier gains nor
closes the direction or mechanism family.

Strongest support for package benefit remains the two earlier native gains.
Strongest current contradiction is this complete unchanged-package loss,
together with **2.16911× D0 native wall**. Instance-dependent learning, spatial
behavior, data/credit exposure and gradient grouping remain alternatives. No
stable seed advantage, pure batching/online-renewal effect, longer-budget
advantage, transfer or safety claim follows. Tuned same-information UAV headroom
is absent; the old host baseline set has different exposure and does not replace
this fresh authentic comparator.

Actual exposure: **two real fits/four models; 80000 training team ticks/
160 episodes/ten update stages; 32000 final ticks/64 episodes; 112000 total
native team ticks/672000 agent observations/6000 batched controller calls;
zero checkpoint loads, extra panels or numerical replays.** The allocated
pair ends here. There is no fourth pair, C promotion or automatic successor.

## 4. Technical acceptance, resources and preservation

Both full commands used hmasd-wsl-node, CPU FP32/four Torch threads, at exact
source `5b15e536806d3b54dc693e7b4b911eba53ff643c`, training 771103 and evaluation
781103. The unchanged-source review and one nonnumerical binding/command check
are preserved. D0 acceptance is reused; I checks confirm source/object/card/
lanes, configurations differing only in the two allowed fields, full learning,
finite arrays, zero evaluator optimizer calls and all ordered paired statistics.
The primary was reduced only after integrity and admission/native-cap checks
passed. Technical acceptance and scientific interpretation are separate records.

| Arm | Complete wall seconds | Cap | User+system CPU seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| D0 | 471.82 | 900 | 1860.73 | 1632916 |
| I1280 | 1023.43 | 1800 | 4046.72 | 3510968 |
| Sum | 1495.25 | 2700 | 5907.45 | not additive |

Physical/effective available memory was 15628304384 bytes for D0 and
15637217280 for I, each above 4294967296. Both exits are 0 and both full arm
caps pass. Source delivery occurred exactly once in 7.438 s, within 45 s and
already charged inside support. Nested runner/supervisor clocks are not added
to complete invocation wall; study elapsed and aggregate CPU are distinct.

SUPPORT.json records invoked preparation, review, delivery, observation,
collection/reduction, publication/integration and cleanup once as available.
Root's already reported approximate 9.1 s, conservative at-most 6.8 s and
approximate 5.3 s contributions are included once each. Unmeasured Monitor,
relay-service and client/message attribution is not zero. Mark
`resources_unmeasured` for partial support telemetry: the 300 s support and
3000 s complete caps are not fully certified. No observed cap breach is found;
missing support measurements do not enter the primary, consistent with
evidence-spec §11.8.7. Section 4 machinery required/added: **none**. The
identity-only implementation adds no section 5 budget breach.

Both binary archives preserve all 22 unique current raw files: six native
outputs, four admission/time receipts and twelve supervisor files. Overlapping
D0 receipt copies agree. The cleanup inventory confirms all bytes match, both
supervisors are terminal without tmux sessions, and the execution checkout has
only six known ignored outputs. No local temporary extraction was created.
Final scoped cleanup and retention state is in the intake and CLEANUP_FACTS.json
when the authorized removal completes.
