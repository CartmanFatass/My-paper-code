# Draft claim for Pro critique: ordered ordinary roster training

Prepared 2026-09-24 by the current agent_count_generalization DM after B19.
**Draft for the actual confirmation decision; no confirmation operation is admitted.**
The DM will append its response to criticism and finalize the selected plan before execution.
This draft does not extend B19 or change the frozen B15 contract.

## Claim and scope

For the native S1 uniform/free-space host with 50 users, capacity 10, fixed within-episode
rosters and the specified LOCAL1 learner, the exact ordered mixed training program
M=[4,6,8]×15 has positive expected final45 native J and served-users-per-step differences
relative to F=45×N6, at **each of N5 and N7**, conditional on the fixed new evaluation
panel below and averaging over fresh independent training blocks.

The claim concerns the complete ordered program at equal team/UAV training exposure, not a
pure count-support mechanism. Native reward/N, per-N optimizer weighting, order, last-N8
recency and finite optimization remain treatment components. N5/N7 are untrained exact
counts for both arms and interpolation inside M's trained [4,8] range. No N4/N8 deployment,
outside-range, skill-causality, arbitrary-world, universal-MARL or no-local-loss claim.
No practical minimum improvement is claimed; this draft uses zero directional margins,
not B15's unrelated service margin. N6 cost is fully reported but not added post hoc to
rescue or overturn the four fixed primary tests; no N6 noninferiority claim is made.

## Exposure and comparator

B19 is one exposed development pair with positive mean M−F J/S at N5,N7,N6, and 2/2/1 paired
adverse worlds. It and all B01–B18 exposure, the incomplete B18 attempt and B15 inconclusive
confirmation remain in the notebook. None is included in the new confirmation estimates.

F is the competent LOCAL1 fixed-N6 control, not SET or an untrained actor. Use the identical
B19 native environment/learner path: local104 actor, central133 critic/MAX8, trainable single
category FiLM, task-only native J/N, entropy .05, raw Gaussian PPO/logprobs with clipped
execution, k10, hidden256/8 heads/2 layers, 15 epochs, seqbatch32, coordbatch1280,
obs/state normalization off and unchanged scalar value normalization. No learning-rate,
entropy, architecture, schedule, checkpoint or family search. Commit exact B20 implementation
and prospective source identity before any new execution, preserving the B19 science.

## Fixed new batch proposed for critique

Three fresh independent paired blocks, six new fits total; within each block F then M, each
from the same actual new initialization and matched initial optimizer/normalizer/runtime/RNG.
Learning and sampler states persist throughout each arm. F has 45 N6 rollouts, M [4,6,8]×15;
16 lanes × H500 ×45, 360,000 team/2,160,000 UAV training steps per arm and 45 updates.
Expected actor and critic optimizer calls are 101,250 each per arm; measure them.

| Block | Learner seed | Training-world base |
| --- | --- | --- |
| 1 | 1016101 | 3246100 |
| 2 | 1017101 | 3346100 |
| 3 | 1018101 | 3446100 |

Training world = block base +100×rollout +lane, rollout1..45, lane0..15; reset/construction
preserves learner RNG. Common N6 scenes between arms match; record completed reset scenes
before collection. Seeded world construction preserves the ongoing learner RNG; private sampler state persists as in B19.

A new fixed evaluation panel is shared across all three blocks and both arms: N5 seeds
2446500..2446531, N7 2446700..2446731, N6 2446600..2446631; 32 worlds each, H500, this order.
Runtime evaluation seed is that N's base +51. Evaluate one genuine common initialization
per block after full identity checks, then F45 and M45, with no updates during evaluation.
Nine actual panels/144,000 evaluation team steps per block; 27 panels/432,000 total. The
common initial is actually evaluated, not generated algebraically or inherited from B19.

Total: **six new fits**, 2,160,000 training +432,000 evaluation =2,592,000 team steps;
15,552,000 UAV steps. Use the independent local_linux CPU path already exercised in B19,
with the same configured interpreter and threads; its 131.964485min per pair gives about
6.6h of runner time for three sequential pairs, an estimate rather than a stopping rule.
Actual node admission still applies. Bulk retention is about 3.3GB before replication of
outputs, plus artifact reading/storage and implementation/review cost. No extra sweep or
interim evaluation/endpoint selection is included.

## Estimand and fixed proposed reading

For training block b and N in {5,7}, compute D_b,N,J and D_b,N,S as the arithmetic mean of
32 paired final45 world differences M−F. The independent unit is the training block, n=3.
For each of the four co-primary quantities report all three D_b values, their mean and
Student t two-sided 95% interval with df2: mean ±t(.975,2)×s/√3. These are model-based
intervals over training blocks conditional on this fixed panel, assuming approximately
normal block effects; n3 cannot validate that approximation or establish precision.
Worlds/time steps do not increase n; no world bootstrap stands in for training variability.

The **single conjunctive claim** is supported only if all four lower limits are strictly
above zero. This is an intersection-union reading of a joint all-positive claim; do not
advertise the four individual intervals as simultaneous 95% coverage. Any failed lower
limit yields inconclusive for this claim, preserving positive/negative means and intervals;
no equivalence/ineffectiveness conclusion. A clear adverse estimate is reported as such.
There is no pooled N statistic, post hoc threshold, rounding pass, or added fourth block.

Also report all raw per-world initial/final J,C,Q,P,E,S,U,height, both own-learning changes,
all adverse worlds, and N6 tradeoffs per block. Common initialization makes differences in
own-learning changes equal endpoint differences algebraically, not independent evidence.
Retain actual optimizer counts, source/config/identity, motion/clip diagnostics and costs;
diagnostics are not additional efficacy gates or causal mechanisms.

## Stopping and interpretation

Execute the fixed three-pair batch once only if the DM adopts this plan after critique.
No early score stop, interim checkpoint, seed replacement, horizon extension or automatic
retry. An incomplete arm is a technical failure; preserve completed/partial outputs and
started-fit cost, and mark the fixed confirmation incomplete. Any repair/new attempt is a
separate decision rather than a hidden completion of this batch.

A supported result is limited repeatable utility of this exact ordered ordinary program
on the fixed new panel and host. It does not resolve order versus support or the omitted
claims. An inconclusive result ends this batch without relabeling exposed instances as
fresh evidence. The DM separately assesses whether an additional different question is
worth its cost; success does not require an architecture or another confirmation.
