# UCOPE UAV motion prefix B04 — P61 result evidence (E0)

**COMPLETE / WITHIN**, one matched training pair 7201. Native T−G is
**−0.003948225944122139**, conditional paired-episode SE
**0.010191826216031805**. Both learned-arm means exceed untuned hover, while
the primary provides no demonstrated gain over ordinary feedback at MEI 0.01.
This is one fitted-pair observation, not stable equivalence or conditioning
causality. Every outcome ends the selected allocation at this intake.

## E0.1 Object, frozen inputs and actual invocation

- Object: `UCOPE-UAV-MOTION-PREFIX-B04`, B/EXPLORE. [Card §§1–6](UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md)
  frozen at `c54d8d9403d8613550b6b050f3df465d1b0e1424`, before implementation
  and output. [P61 Convergence](pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md)
  at immutable `475f4452177a98e20fb4c0aedf31a89aee4d8912` selects one pair,
  with the complete prior history and no automatic successor.
- Accepted execution source: `7693b7af6b7d89cdaa028659d606a37dee9eb68e`, tree
  `9b3221e69f3251ec030cfb0fb05b0d2a85126fa9`. The T-only conditional head
  and b+12 initialization are bound by the [CM specification](UCOPE_UAV_MOTION_PREFIX_B04_CODE_SPEC_20260908.md)
  and accepted [technical record](UCOPE_UAV_MOTION_PREFIX_B04_TECHNICAL_ACCEPTANCE_20260908.md).
- Actual handle: `ucope-uav-motion-prefix-b04-7201-p61-20260908`, node
  `hmasd-wsl-node`, cwd
  `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b04-p61-check-20260908`.
  Root executed the CM's exact LF wrapper; collected wrapper SHA-256
  `262ce2d711e1ded155abdf375aeb0e5a763f745e385772cfa2234e9506db796f` matches
  its prelaunch binding. No source, task horizon or primary changed at launch.
- Supervisor PID 3012256, start `2026-09-08T23:15:53Z`, terminal
  `2026-09-08T23:20:30Z`, finished/exit0 and inactive by Root/CM readback.
  UTC times here convert the actual log's +08:00 timestamps.
- Technical collection commit `2d8750b46da3cff99f3f632bb8a17b5a70a9ed91`,
  integrated by Root as `cc64a7b84`. [Collection JSON](UCOPE_UAV_MOTION_PREFIX_B04_7201_COLLECTION_20260908.json)
  preserves the full summary, all 96 J values and differences, seven artifact
  hashes, seven supervisor hashes, checkpoints' group counts/norms and memory
  receipt. [Terminal technical acceptance](UCOPE_UAV_MOTION_PREFIX_B04_7201_TECHNICAL_ACCEPTANCE_20260908.md)
  records complete publication and comparison checks.

Actual raw files are in the **direction checkout**:
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/exp/uav-motion-prefix-b04-7201-p61-20260908/`.
This differs only from the handoff's proposed local collection destination;
remote identity, bytes and scientific meaning are unchanged. Root must preserve
these ignored raw files before reclaiming their containing checkout.

## E0.2 Native estimand and rule applied verbatim

Five UAVs, 50 users, 256 one-second primitive steps, unchanged local 108 actor
inputs and separate predecision 136 critic input. T chooses an opening velocity
and duration 1/4, conditional on its own actual sampled normalized command,
and returns to ordinary feedback by t4. G has every legal velocity available
at every primitive step under the same free local information. H is untuned
zero velocity on the matched reset seeds. Both real fits retain native full
RTG, agent-compound clipping and zero explicit entropy coefficient.

`J_a(e)=sum_t sum(info['rewards_dict'].values())/256`;
`Delta=mean_e(J_T(e)-J_G(e))` over 32 final matched-reset episodes. Card §5's
applicable rule, verbatim:

> -.01<=Delta<=.01: no demonstrated point gain at the selected scale/budget; prefer no unchanged continuation, not stable equivalence.

The unrounded primary satisfies this interval: **WITHIN**. It is
0.006051774055877862 above −0.01 and 0.01394822594412214 below +0.01.
The conditional SE 0.010191826216031805 does not estimate variation across
training pairs. There is one independent fitted pair; no training-population
SD, confidence interval, reliable equivalence or significance claim follows.

## E0.3 Complete native outcomes

| Final arm | Mean J | Final episodes |
| --- | ---: | ---: |
| T: command-conditioned opening duration | 0.18320920071658314 | 32 |
| G: ordinary stepwise recurrent feedback | 0.18715742666070528 | 32 |
| H: untuned hover | 0.16333870700710337 | 32 |

| Paired contrast | Mean | Conditional evaluation SE | Positive / negative / zero |
| --- | ---: | ---: | ---: |
| T−G | −0.003948225944122139 | 0.010191826216031805 | 18 / 14 / 0 |
| G−H | +0.0238187196536019 | 0.011454243503509544 | 20 / 12 / 0 |
| T−H | +0.019870493709479763 | 0.014677398371169156 | 21 / 11 / 0 |

T−G episode differences span −0.16125563298518442 to +0.09350894263405753.
The positive episode majority does not reverse the negative complete mean;
no negative tail, zero-hover episode or other outcome is excluded. T−H spans
−0.19468040105328094 to +0.20137099875325076. Positive sampled hover margins
support only performance relative to this untuned reference. They do not
establish tuned generic competence or compensate for the primary shortfall.

The [DM summary](UCOPE_UAV_MOTION_PREFIX_B04_P61_RESULT_SUMMARY_20260908.json)
records these calculations and points to the original all-outcome arrays.
No historical study is pooled, and no best seed/checkpoint/episode is selected.

## E0.4 Actual learner exposure and native path

Each fit completed 512 episodes, 131072 train team steps, 256 two-episode
rollouts and 1024 Adam calls at lr 0.0003. T/G parameter counts are 68553/66311.
Total relative displacement is T 0.5401094749093319/G 0.5930201245151642;
common-actor relative movement is 0.1815182643808623/ 0.15501710881425063,
critic 0.8856876376094958/ 0.9658026596983639. These show real updates, not
performance improvement.

T's 2242-parameter duration head has absolute movement 0.41481131315231323
and relative movement 0.12751004670944632 from initial norm 3.2531657218933105.
The 2176-parameter hidden layer moves 0.4102451503276825. The 66-parameter
final layer begins at norm 0 and moves 0.06137862801551819; its relative
displacement is correctly null. No epsilon-normalized effect is claimed.

T has 2560 owned duration samples during training, 1231 four-step choices.
Its final 160 openings contain 73 four-step and 87 one-step choices; sampled
d4 frequency 0.45625. Final T/G velocity decisions are 40741/40960, a difference
of 219=3×73 held decisions, while each arm still processes 40960 recurrent
observations. This is consistent with actual command ownership and continuing
observations during holds. It does not show that the learned conditioning
changes competent actions or information value usefully.

The causal route remains local history → own sampled command → conditional
duration → held/feedback physical motion → channels/service and later free
local observations → recurrence/actions → native rewards → PPO learning →
final sampled return. Direct geometry, persistence, added capacity, sparse
opening credit and partner co-adaptation remain unseparated explanations.
No new checkpoint inference, trajectory replay or mechanism diagnostic was run.

## E0.5 Counts, resources and conformance

Actual totals: 262144 train + 24576 evaluation = **286720 native team steps**,
2048 Adam calls, 512 rollouts, 1120 complete episodes/explicit resets,
2 constructor resets, 96 final episodes,1600 diagnostic rows and 0 partial
episode steps. All fits, final T/G evaluations and H evaluation are complete.
CM reconciled reward_sum/256, reset/stream/config associations, all artifact
hashes, finite FP32 checkpoints and supervisor publication. DM checked the
raw summary against collection, native arithmetic and actual terminal receipts.

Fresh physical/effective memory each measured 15640686592 bytes, above 4 GiB.
Complete invocation wall **277.51s**, process peak RSS **554964KiB**;
internal T 137.67042454401962s/G 139.29419632797362s, pair 276.9646218509879s.
The 1800s/arm and3600s complete caps were met; limits [] and cap_breach false.
`resources_unmeasured` marks aggregate CPU and system-wide peak memory only;
observed wall, process RSS and admission remain valid. The timing is an observed
complete B04 run, not a causal speed comparison with B03 or a measured new-head
increment. One valid B comparison used 277.51s of complete invocation wall.

Engineering scope §4 none; no new §5 breach. Earlier B04 test/setup/launcher
failures, B02's80.578s/60s smoke breach and all historical scientific outcomes
retain their original meanings. Collection/DM arithmetic add zero model,
environment, learner, evaluator, replay or scientific invocation. The
contradictory short Transport receipt and full immutable Pro answer remain
preserved in the Convergence intake, with no resend.

## E0.6 Prediction and fixed end boundary

Prospective WITHIN(.50) occurred; positive G−H(.60) occurred: **2/2**.
Binary Brier scores are 0.25 and 0.16, mean 0.205; two events do not establish
calibration. Owner prediction: **not taken (unattended)**.

The full card, implementation/review, one invocation, collection and all-outcome
intake are complete. P61's selected 7201 allocation is exhausted for this WITHIN
outcome. No unchanged continuation, retry, second pair, extra H/evaluation,
tuning or successor is allocated. No family closure/recast or Portfolio
lifecycle/priority change follows. See [DM intake](UCOPE_UAV_MOTION_PREFIX_B04_P61_INTAKE_20260908.md)
for the exact decisions and cleanup/integration route.
