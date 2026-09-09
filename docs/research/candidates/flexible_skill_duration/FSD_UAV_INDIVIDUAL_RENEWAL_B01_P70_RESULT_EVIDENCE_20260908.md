# FSD UAV individual-renewal B01 / P70 — result evidence

## 1. Observed result and original rule

**Complete B/EXPLORE; one matched training pair; opposite native performance.**
The original [card §§2–6,9](FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md)
and [P70 allocation](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_EXECUTION_HANDOFF_20260908.md)
are unchanged. Both original arms completed at source
`ca36e2f941d6c4d4e996a9bd919378af44ea0e93`, CPU4/FP32 on `hmasd-wsl-node`.

Card §5 rule applied verbatim:

> <−.01 | Opposite native performance on this pair; it weakens this exact .25 individual-gap configuration at this budget. It does not close every threshold or FSD.

D0 native mean J is **0.26946095234781076**; I is **0.21979038918069888**.
The 32 paired I−D0 differences have mean **−0.049670563167111874**,
sample SD **0.13442151634285882** and conditional SE **0.023762591435853447**.
The immutable branch is `opposite_sign`, below the .01 absolute MEI.
This is one training pair, not 32 independent training experiments. The endpoint
spread does not estimate training-seed uncertainty; no stable superiority,
equivalence, timing causality, transfer or whole-direction closure follows.

The [DM data-only analysis](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_DM_ANALYSIS_20260908.json)
retains every ordered U/J value and paired difference, all five original training
rows per arm, losses, counts, initial norms and displacement. The CM's
[complete collection record](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_COLLECTION_EVIDENCE_20260908.md)
also prints all 32 endpoints and contains exact technical acceptance evidence.
There are 12 positive and 20 negative endpoint differences; none was selected out.
Those counts describe this fixed pair's endpoint panel only.

## 2. Native primary and component tradeoff

The unchanged learner uses the original adapter reward. Reporting alone computes
`J = 6*U/500`, with native objective `.7*coverage + .3*quality - altitude_penalty`.
The field named `energy_penalty` in existing output is this altitude component.
No training reward, value target, normalizer or loss was rescaled.

| Observable | D0 | I | I−D0 |
| --- | ---: | ---: | ---: |
| Raw adapter episode U | 22.455079362317562 | 18.315865765058238 | −4.139213597259324 |
| Native mean J | .26946095234781076 | .21979038918069888 | −.049670563167111874 |
| Coverage | .3257012499999996 | .3498849999999997 | +.02418375000000006 |
| Quality | .1576304797918256 | .1290595785205807 | −.028570901271244925 |
| Altitude penalty | .005819066589736964 | .06384698437547542 | +.05802791778573846 |

The coverage gain contributes +.016928625 to the native contrast, quality
−.008571270381373477 and altitude −.05802791778573846. Their sum reproduces
the native loss. Coverage is a component gain, not an alternative winning primary.
This accounting identifies which recorded reward terms differ, not why the
learned policies produced those terms.

## 3. Exposure, training and actual renewal

Both arms use training base770503 and evaluation base780503, their specified
private lane seeds, six fixed UAVs/fifty users, H500, uniform/free-space,
latent6/6, common team k10/caps10 and the ordinary recurrent learning stack.
I individual cost .25/team Infinity and authentic D0 Infinity/Infinity are
present in both learner and evaluator. Pair initialization and exogenous reset
laws are shared; each arm owns its subsequent data, RNG consumption,
normalizers, weights and optimizer work. No membership changes occur.

Machine-computed exposure: **80000 collected/stored training transitions,
160 training episodes,10 update stages;32000 evaluation steps,64 endpoint
episodes;112000 environment steps,672000 agent-step observations,6000 batch
control calls;4 model constructions,2 training starts,0 checkpoint loads;
49620 actual optimizer.step calls over all five groups;1 independent training
pair.** There is no intermediate evaluation, tuning, selection, retry or resume.

| Actual optimizer calls | D0 | I |
| --- | ---: | ---: |
| Coordinator | 525 | 3345 |
| Discoverer actor | 11250 | 11250 |
| Discoverer critic | 11250 | 11250 |
| Team discriminator | 75 | 75 |
| Individual discriminator | 300 | 300 |
| Evaluator, all groups | 0 | 0 |

All five active parameter groups have finite nonzero displacement after update1
and update5. This establishes actual learner exposure, not competence. Their
initial norms and exact first/fifth values remain in the linked data and CM table.
The real per-rollout unscaled returns/losses and counts are retained without
relabeling update stages as optimizer calls.

| Training rollout | D0 mean native J | I mean native J |
| ---: | ---: | ---: |
| 1 | .2441620027058621 | .22203045145211742 |
| 2 | .2373040315790039 | .12171461438291079 |
| 3 | .2737892342931295 | .1409502642611887 |
| 4 | .3147706815508942 | .17168119065393064 |
| 5 | .32551798705140694 | .22073143238466128 |

These are stochastic collection returns on each arm's own trajectories before
that rollout's update. They are not an initial/final evaluation contrast.

Over training, both arms have4000 team decisions. Individual sampled positions
are24000 D0 versus78390 I; I has54390 individual gap causes. Joint decision rows
are4000/28351 and individual token switches19607/63763. D0 training segments
are all length10; I's mean individual segment length falls from3.53460972018
to2.76179516686 across the five rollouts, min1/max10. Team segment lengths
remain10. Gap causes count sampled (environment,agent) positions; team causes
count environment positions. Sampling, switching and optimizer work are distinct.

At the unique deterministic endpoint, both arms have1600 team decisions and
9600 individual sampled positions, with **zero individual gap causes** and zero
individual-cap causes. Token switches are612 D0/1421 I. Thus the configured
additional decision path was active in training but unused between team
boundaries in this endpoint panel. The native contrast remains a valid package
comparison, but is not evidence of benefit or harm from extra endpoint decisions.
Endpoint segment lengths/rows_M are **unmeasured by the empty storage/update
buffers**, not observed zero-duration skills. No extra activity requirement is
added; this reporting limit does not damage the independently measured primary.

## 4. Execution receipts, resources and engineering conformance

The [execution record](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_EXECUTION_EVIDENCE_20260908.md)
contains the committed literal commands, detached exact-source cwd, input digests
and acceptance receipts. Same CM observed and collected both terminal handles:
`fsd_uav_b01_p70_D0_ca36e2f94` then `fsd_uav_b01_p70_I_ca36e2f94`.
Exactly one accepted supervisor submission per arm; both have `finished`/exit0.
No live handle remains.

| Arm | Fresh physical/effective available bytes | Complete wall s | Peak RSS KiB | Aggregate CPU s |
| --- | ---: | ---: | ---: | ---: |
| D0 | 15615131648 / 15615131648 | 471.89 | 1610396 | 1859.66 |
| I | 15640535040 / 15640535040 | 1221.49 | 1623988 | 4862.61 |

Both admissions exceeded4294967296 bytes before model/scientific-root creation.
Complete outer clocks include admission, imports, initialization, all learning,
evaluator construction/sync, unique endpoint and closed-file publication. Caps
3600/18000s and summed21600s were respected. Sum of command walls is1693.38s;
aggregate CPU6722.27s; study critical path1817s at1s supervisor resolution,
including the between-arm collection/staging gap. These are different quantities.
Measured I/D0 wall ratio2.5885058 is this execution's cost fact, not a hardware
benchmark or algorithmic upper bound. Old cost scenarios remain historical.
Memory admission and measured peak RSS do not imply a continuous free-memory trace.

Technical collection commit: `5c0ba40754119cc1ba6a0f953c64ee9fb967ff81`.
Authoring control root: `temp/directions/flexible_skill_duration/exp/uav_b01_p70_control_20260908`.
It retains both evidence archives, adjacent admissions/process-time receipts,
launch stdout, supervisor files and original summaries under the preserved
`temp/directions/.../uav_individual_renewal_b01_770503/{D0,I}` layout.

| Bytes | SHA256 |
| --- | --- |
| D0 summary | `c7b8f32ddfa949147a29c4b3847bf3ac07d388d0258bfe8fc1ec0acfff979906` |
| I summary | `e60fddb3e99719e1a7e760f7e05791d39c48df3b94d1f3a8204de3c46a3b8b0f` |
| D0 archive | `4151ca1015db678fe1d8407f316360981ee5bbded941dfa5bb90d49760e54d47` |
| I archive | `ca1edf76e003f1ef4391b5cf80e909285ad00edcf6d1e5bc4723de4c5adb7289` |

CM verified remote/local bytes, configurations, counts, source and original
admission/terminal records. DM read the actual local summaries, terminal/time
receipts and technical report, recomputed U→J, all paired differences/SD/SE,
component accounting, exposure and work ratios with existing NumPy, and compared
them with in-cap publication. No runner import, remote observation, learner
execution, test rerun or new evaluator was performed by DM.
Engineering scope §4: none requested or added. The accepted424-line runner is
unchanged; no §5 budget breach or unrequested machinery was accepted. The old
blocked P69 scratch remains untouched. Scientific validity is not inferred from
source checks or exit status alone.
