# UCOPE UAV motion prefix B03 — P57 result evidence (E0)

**COMPLETE / DOWN**, one matched training pair7101. Complete native
T−G is **−0.010093085146628955**, conditional paired-episode SE
**0.008506138301283968**. The primary lies only0.0000930851466 below
the negative MEI boundary. Both learned arms beat hover on their sampled
means. This is a bounded fitted-pair observation, not stable harm or an
entropy-causal result.

## E0.1 Object, frozen inputs and actual invocation

- Object: `UCOPE-UAV-MOTION-PREFIX-B03`, B/EXPLORE, one independent matched
  training pair. [Card §§1–6](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md)
  frozen at`f5230ca30537e7baa7db71ee2ba437a17efe807b`; [P57](../../portfolio/handoffs/2026-09-08-p57-ucope-post-b02-selection.md)
  at`68c7dab578d4e64d201a34028b574469bf1c598f` supplies the one-pair limit.
- Source: `70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`, tree
  `13634a339b2d6e323238a46feac29f443d022b8e`. The frozen common change is
  explicit entropy coefficient0 in T/G, with agent-compound clipping and
  all native action/information/return paths preserved.
- Actual remote handle: `ucope-uav-motion-prefix-b03-7101-p57-20260908`,
  node`hmasd-wsl-node`, cwd
  `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b03-p57-check-20260908`.
  This reuses the exact committed checkout of the completed focused test;
  the scientific supervisor and output root are separate.
- Supervisor PID3007532; start`2026-09-08T20:46:06Z`, terminal
  `2026-09-08T20:50:50Z`, finished/exit0 and inactive according to Root/CM
  readback. Log timestamps are recorded in+08:00 and converted here to UTC.
  The stored runner matches the [bound command](UCOPE_UAV_MOTION_PREFIX_B03_P57_ROOT_HANDOFF_20260908.md).
- Technical collection commit`e904ceb5d9352a9eab28233890eaca28af8f8281`,
  integrated by Root as`27b0f7fe3`. [CM acceptance](UCOPE_UAV_MOTION_PREFIX_B03_7101_TECHNICAL_ACCEPTANCE_20260908.md)
  and [collection JSON](UCOPE_UAV_MOTION_PREFIX_B03_7101_COLLECTION_20260908.json)
  preserve the summary, all96 final J values, all paired differences,
  admission, counts, seven artifact hashes and six supervisor hashes.

No historical P21/P24/B02 endpoint is pooled into B03. No checkpoint,
seed, evaluation episode or metric was selected after observing7101.

## E0.2 Native estimand and rule applied verbatim

Five UAVs,50 users and256 primitive one-second steps per episode. Native
`J=sum_t sum(info['rewards_dict'].values())/256`; primary
`Delta=mean_e(J_T,e-J_G,e)` over the32 matched final reset episodes.
T/G actors each use their own108 local components; the common separate
critic uses the same predecision136 components. T selects a duration1/4
opening velocity and releases a four-step command at t4. G retains legal
velocity feedback every primitive step. H is untuned zero-velocity hover.

Card§5's applicable rule, verbatim:

> Delta<-.01: adverse native evidence for this task/prefix/learner budget; local movement or information changes do not compensate.

The unrounded−0.010093085146628955 satisfies this strict inequality:
**DOWN**. Rounding to−0.01 does not move the result into WITHIN. The
distance below the boundary is9.30851466289552e−05, about0.011 of the
conditional evaluation SE. This is a close threshold crossing in the
observed primary; it is not reliable separation from the MEI boundary.
There is no training-endpoint sample SD or training-population uncertainty
estimate from n=1. No interval, significance or stable-equivalence claim
is inferred from the fixed branch.

## E0.3 All-outcome native comparison

| Final arm | Mean J | Final episodes |
| --- | ---: | ---: |
| T: optional opening commitment | 0.1784473239057538 | 32 |
| G: primitive-step feedback | 0.18854040905238276 | 32 |
| H: untuned hover | 0.1409724467347594 | 32 |

| Paired contrast | Mean | Conditional episode SE | Positive / negative / zero episodes |
| --- | ---: | ---: | ---: |
| T−G | −0.010093085146628955 | 0.008506138301283968 | 17 /15 /0 |
| G−H | +0.04756796231762334 | 0.011545966671454506 | 24 /8 /0 |
| T−H | +0.03747487717099439 | 0.010037043349360902 | 25 /7 /0 |

The T−G episode range is−0.11007592829342794 to+0.08040545648681256;
the negative mean does not mean every episode or a majority has negative
difference. All96 outcomes and both signs remain in the collection JSON.
G's positive hover contrast supports the narrower fact that this fitted
ordinary-feedback controller beats this untuned reference on its sampled
mean. It is not a tuned generic ceiling or a headroom record.

DM's [computed summary](UCOPE_UAV_MOTION_PREFIX_B03_P57_RESULT_SUMMARY_20260908.json)
matches the published mean-of-paired-differences. The existing scientific
tools summarizer was run once on only the two learned-arm final endpoint
means, paired by7101. It reports n=1 and null sample SD. Its subtraction
of already averaged arm means is−0.01009308514662896; the last-bit
arithmetic difference does not replace the card's primary. H and final
episodes were not entered as additional independent training runs.

## E0.4 Real exposure and retained action path

| Quantity | T | G | Complete invocation |
| --- | ---: | ---: | ---: |
| Training team steps | 131072 | 131072 | 262144 |
| Actual Adam calls | 1024 | 1024 | 2048 |
| Training episodes | 512 | 512 | 1024 |
| Two-episode rollouts | 256 | 256 | 512 |
| Final team steps | 8192 | 8192 (+8192 H) | 24576 |
| Complete episodes, train+final | 544 | 544 (+32 H) | 1120 |

Total286720 native team steps/scientific UAV calls;1600 existing
diagnostic frames,2 constructor resets and0 partial episode steps. All
training/final reset associations and every recorded J from its complete
reward sum were checked by CM over stored bytes, without resimulation.
Both saved actor/critic dictionaries contain finite FP32 tensors.

Machine-generated exposure line: **2 real fits; T/G each131072 train
steps/1024 Adam at lr0.0003 and entropy_coef0.0; T66441/G66311 parameters;
total relative displacement T0.558120601386/G0.538479842605; no new
exposure at intake.** T/G common actor relative movement is
0.174357544605/0.230575659931; critic movement is
0.898498263399/0.841313352589. T's zero-initialized duration head has
absolute displacement0.138774350286; its epsilon-denominator relative
number is not an effect-size interpretation.

During final evaluation, T sampled85 four-step openings and75 one-step
openings among160 owned choices, frequency0.53125. T has40705 actual
velocity decisions versus G40960; the255 difference equals three held
decisions for each of85 openings. Both learned arms retain40960 recurrent
observation updates. This records use of the opening/hold/feedback path,
not useful information acquisition or optimal duration selection.

Outcome-informed description of existing G training logs: entropy is
21.2840747833 at the first recorded objective and21.3598651886 at the
last recorded pre-update objective. The unchanged all-active latent-normal
formula implies effective geometric-mean std approximately1 initially
and1.0050653 at that last logging boundary. No checkpoint was rerun for
this calculation. This modest variance change is descriptive; native
policy credit still changes variance with zero explicit bonus. Different
masters and fitted policies prevent an entropy-causal contrast with B02.

## E0.5 Resources, integrity and deviations

Fresh actual-node admission at`2026-09-08T20:46:06.795821Z` records
physical/effective available bytes15645777920, both above4294967296.
The scientific command includes the accepted preflight/runner chain.
Whole invocation wall is **283.51s**, including publication/exit;
internal T143.6449221990s/G139.3128413130s and pair282.9577647990s.
The caps remain1800s per complete arm and3600s per invocation. No limit,
cap breach, nonfinite, partial result or primary-publication failure is
reported. One valid B03 result used283.51s of measured scientific
invocation wall; full historical direction usage is not aggregated here.

Peak RSS is554276KiB. `resources_unmeasured`: aggregate CPU work and
system-wide peak usage are unavailable; measured admission/wall/process
RSS are retained. The second-resolution supervisor start/end span284s;
283.51s is the external complete-process measurement. These facts are
distinct from implementation, staging, observation or collection elapsed
time. Missing CPU telemetry does not invalidate the native comparison.

Seven scientific artifact hashes matched CM's independent remote digest
readback. DM directly verified the raw summary digest
`87a81036eb623e25ae61f235a2ceea78f73e60d3af9077ecf1e4e6c7a6a07143`
and equality to the durable collection summary, read actual supervisor
runner/log/admission, and computed the primary/secondary descriptions.
Raw roots are retained on the exact remote checkout and locally at
`C:/Projects/HMASD/temp/directions/ucope/exp/uav-motion-prefix-b03-7101-p57-20260908/`.
CM's finite-checkpoint/hash/row checks are accepted without repeating its
commands. DM arithmetic files are under
`temp/directions/ucope/exp/uav-motion-prefix-b03-p57-dm-intake/`.

Engineering scope§4 remains none; B03's source/runner/test budgets were
met. The historical B02 smoke80.578s/60s breach, P48 disposition and
pre-admission wrong-cwd failure remain intact. No new learning, evaluation,
replay, profiling, smoke, aggregate or diagnostic invocation was added
by collection/intake. B02's valid negatives are not reclassified.

## E0.6 Bounded reading and exhausted route

This fitted zero-bonus opening-prefix package has a just-below-MEI native
loss to legal feedback, while both learned arms have positive hover
contrasts. The result supplies no current opening-commitment gain. It
does not establish stable harm, entropy causality, pure information value,
transfer, deployment, a family closure or C promotion. [Scientific intake](UCOPE_UAV_MOTION_PREFIX_B03_P57_INTAKE_20260908.md)
scores predictions and records the delegated choice. P57 is complete and
exhausted; no second pair, retry, extra evaluation or successor is selected.
