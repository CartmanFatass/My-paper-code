# FSD UAV renewal batch B02 / 771003 — result evidence

## 1. Result and rule applied verbatim

**Valid complete B/EXPLORE; one new matched training pair; `above_mei`.**
The [card §§4,7](FSD_UAV_RENEWAL_BATCH_B02_SCIENCE_CARD_20260911.md#7-new-allocation771003--prospective-freeze2026-09-11)
remains the prospective definition. Its applicable rule is quoted verbatim:

> - Mean difference **>+.01**: `above_mei`; a second local same-package gain.

Both full commands ran on hmasd-wsl-node, CPU FP32/four Torch threads,
at source `5250c43536d8520d4005eed3f613226ec4bc6e73`. D0 mean native J is
**0.26171018760764769** and I1280 is **0.46799609168995665**.
All 32 ordered I1280−D0 differences have mean **+0.20628590408230901**,
sample SD **0.069599759511641879** and conditional SE
**0.012303615479908721**. All 32 are positive; none are negative
or zero. Range: 0.07188282716047284 to 0.32612075939924712. The relative
difference is 78.822267% of this D0 mean; the
frozen rule uses absolute .01 J.

This is one new independent training pair. Evaluation episodes describe its
learned policies and cannot estimate training-seed uncertainty. Every raw U,
native J=6U/500 and ordered difference is in
[ORDERED_PRIMARY.csv](uav_renewal_batch_b02_771003_20260911/ORDERED_PRIMARY.csv).
[PAIRED_ANALYSIS.json](uav_renewal_batch_b02_771003_20260911/PAIRED_ANALYSIS.json)
agrees with the runner's complete ordered publication. The existing run-summary
tool received one selected endpoint per arm/training identity;
[RUN_SUMMARY.json](uav_renewal_batch_b02_771003_20260911/RUN_SUMMARY.json)
correctly reports n=1 and no training-run sample SD. No older result is pooled.

## 2. Native components and separate training observations

The unchanged native objective is `.7*coverage + .3*quality - altitude_penalty`;
its existing `energy_penalty` field stores the altitude term. J scaling is
reporting only; neither the learner reward nor selected endpoint changed.

| Final observable | D0 | I1280 | I1280−D0 |
| --- | ---: | ---: | ---: |
| Raw episode U | 21.809182300637 | 38.999674307496 | +17.190492006859 |
| Native J | 0.261710187608 | 0.467996091690 | +0.206285904082 |
| Coverage | 0.441377500000 | 0.592561250000 | +0.151183750000 |
| Quality | 0.118979603884 | 0.182923326493 | +0.063943722609 |
| Altitude penalty | 0.082947943557 | 0.001673781258 | -0.081274162299 |

Weighted coverage contributes +.105828625, quality +.01918311678282103, and the
lower altitude penalty +.08127416229948815. Their sum equals the native gain.
This is observed reward accounting, not causal identification of learned motion.

| Rollout | D0 sampled training J | I1280 sampled training J |
| --- | ---: | ---: |
| 1 | 0.248537859607 | 0.244752767424 |
| 2 | 0.204182790841 | 0.196784839325 |
| 3 | 0.225222632561 | 0.239608053614 |
| 4 | 0.240645338991 | 0.258870032278 |
| 5 | 0.249432260818 | 0.303318226347 |

The first two I training means are lower and the final three are higher. These
are retained training data, not extra evaluations or checkpoint selection.

## 3. Mechanism exposure and claim ceiling

Six UAVs observe partial service geometry and retain private recurrent state.
Own and partner motion affect subsequent observations; primitive velocity stays
reactive under held skills. I renews an individual skill at gap .25, while D0
uses infinity. Both retain team clock/caps10, reset/survivor rules, primitive
discount, segment credit and ordinary PPO. Only individual threshold and
coordinator batch1280 versus128 differ. Each arm has its own learner and RNG;
matching evaluation law does not imply identical policy-induced trajectories.

I has 44697 individual training gap causes versus zero D0. Its valid joint rows
are 4957/4838/5605/5568/5524, totaling 26492 versus 4000 D0, a 6.623× ratio.
The actual coordinator law `15*sum ceil(M_r/batch)` yields 345 versus 525 calls:
60/60/75/75/75 versus 105 in each D0 rollout. Fewer optimizer calls do not remove
row/decoder work or preserve identical gradient grouping. Each arm also has
11250 actor,11250 critic,75 team-discriminator and 300 individual-discriminator
calls. Every stage has finite nonzero module movement and optimizer exposure.
Final coordinator displacement from initialization is .04356839281466031 I
versus .04470412879200881 D0. I individual training segments average
3.729/3.803/3.421/3.301/3.282 primitive steps versus 10 D0.

At final evaluation there are nine I individual gap causes versus zero D0,
with 32 resets and 1568 team-cap events each. This is sparse online renewal;
its causal return contribution is unresolved. Evaluator segment storage is
empty, so endpoint duration statistics are unmeasured. Returns, components and
decision counters remain intact, with zero evaluator optimizer calls.

The earlier I1280 pair remains separately +.05697746721968016 with 24 positive
and 8 adverse episode contrasts. The older batch128 I losses
−.049670563167111874 and−.035312725297886094 retain their original meaning.
This second package gain strengthens the local observed history, not stable
superiority, pure batching causality, online-renewal causality, transfer or
safety. The new D0 mean .2617101876 is lower than the earlier .4162744505, while
I means .4679960917 and .4732519178 are close descriptively. Different training
and evaluation identities prevent assigning that variation a cause. Tuned
same-information UAV headroom remains absent; the older host baseline set has
different exposure and does not replace the actual fresh comparator.

Machine-generated actual exposure: **two fits/four models;80000 training team
steps/160 episodes/ten update stages;32000 evaluation steps/64 episodes;
112000 total native team steps/672000 agent observations/6000 batched controller
calls; zero checkpoint loads or extra validation episodes.** Collection and
intake calculations use existing bytes with zero learner/environment work.

## 4. Technical acceptance and complete-cost limitations

The source-delivery receipt and existing independent review cover frozen source
and binding. D0 acceptance is reused; I checks cover complete identity/config,
five training rows, nonzero optimization/movement,32 endpoint rows, finite data,
raw/native/component accounting and the dependent ordered pair publication.
Both exits are 0 and both adjacent admissions pass. I physical/effective memory
was 15628656640 bytes and D0 was 15641456640, each above 4294967296. Complete
original outputs and receipt bytes are preserved in the two collection archives;
CLEANUP_INVENTORY.json verifies all 22 current raw files match collected bytes.

| Arm | Complete wall seconds | Cap | User+system CPU seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| D0 | 538.66 | 900 | 2119.87 | 1667448 |
| I1280 | 1069.26 | 1800 | 4241.77 | 3444284 |
| Sum | 1607.92 | 2700 | 6361.64 | not additive |

I costs 1.98504× D0 wall. First supervisor start through final exit is 3000s of
study elapsed, including idle handover time, distinct from summed invocation
wall and aggregate CPU work. Nested runner/supervisor clocks are not added again.
Exactly one source-delivery transaction took 7.359s, within its 45s cap and already
inside support accounting. The separate support 300s and complete 3000s caps are
**not fully certified**: I terminal observation and relay-service attribution
remain unknown. Root's measured 28.5s enclosing FSD integration commands are
charged once; the earlier shared 1.0s query stays unallocated and adoption costs
are not added again. SUPPORT.json retains the known subtotal and pending
publication/cleanup charges.

Mark `resources_unmeasured` for partial support telemetry. No observed cap breach
or engineering-scope addition is found; section4 machinery required/added:none.
Unknown observation costs do not enter the native primary. Evidence-spec
§11.8.7 therefore limits complete-cost certification while preserving the valid
bounded scientific result. No retry, new invocation, C consumption or
retrospective change to an ended instance follows. The execution record and
intake retain terminal receipts, decisions and final cleanup state.

Final preservation: all22 raw files are retained in published commit522b7ba2b;
all four remote execution/input/supervisor paths are absent and the detached
worktree is unregistered. The190929-byte local collection duplicate remains
after tool policy rejected its removal. See the intake and CLEANUP_FACTS.json;
this cleanup limitation changes no scientific observation.
