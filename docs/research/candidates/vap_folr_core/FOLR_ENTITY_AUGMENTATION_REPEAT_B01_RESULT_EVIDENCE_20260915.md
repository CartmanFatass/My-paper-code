# FOLR prospective two-block A-G repetition: complete E0 evidence

Object FOLR_ENTITY_AUGMENTATION_REPEAT_B01_781901_782001, B/EXPLORE.
Card: [fixed question, programmes and reading](FOLR_ENTITY_AUGMENTATION_REPEAT_B01_SCIENCE_CARD_20260914.md).
Scientific source7975964542b83560cbc0e79f74a9212f8e3737af; author checkout
C:/Projects/HMASD-worktrees/codex-vap-folr, branch codex/vap-folr.
Four original learners are complete; no empirical invocation remains.

## Observation and rule applied verbatim

| Block; train/eval labels | G mean | Persistent A mean | A-G | Per-block rule |
|---|---:|---:|---:|---|
| 1; 781901/1781901 | 1.4009375 | -4.4296875 | -5.830625 | G_ABOVE_MEI |
| 2; 782001/1782001 | 0.208046875 | 0.098125 | -0.109921875 | WITHIN_MEI |

The frozen two-block rule is verbatim:

- both d1>1 and d2>1: BOTH_A_ABOVE_MEI;
- both d1<-1 and d2<-1: BOTH_G_ABOVE_MEI;
- both inclusive -1<=d1<=1 and -1<=d2<=1: BOTH_WITHIN_MEI, with both signs retained;
- every other complete pattern: MIXED_BLOCK_PATTERN, retaining actual signs and magnitudes.

The resulting primary is ordered(d1,d2)=(-5.830625,-0.109921875),
**MIXED_BLOCK_PATTERN**. Both signs are negative; mixed refers to their threshold
categories, not opposite signs. The descriptive mean difference is-2.9702734375;
it does not replace the ordered primary or relabel the result BOTH_G_ABOVE_MEI.
No A endpoint exceeds G by the card's1-point MEI in these two blocks. The raw
floating representations are retained in STUDY_READBACK.json.

## Exact exposure, programme and integrity

Every original fit has5000 native training episodes/100000 ticks/4969 RMSprop
actor/mixer updates, one final checkpoint and128 greedy nonlearning evaluation
episodes/2560 ticks. Totals are20000 train episodes/400000 ticks/19876 updates,
four checkpoints,512 evaluations/10240 ticks,410240 overall native ticks.
There are four separate fitted programmes, two per arm, and two contrast blocks.
All four outcomes are included in prospectively fixed G1,A1,G2,A2 order. There
is no screened label, extra initial evaluation, selected checkpoint, historical
endpoint substitution, fifth learner, scientific retry or post-result arm change.

A is the original AUGMENTED_PERSISTENT whole programme, with observer-subject
entity GRU16 plus Generic64/history/fusion; G is original GENERIC_RETAIN64 with
its original head. Both use entity_history_augmentation_b01.Learner, native easy
Traffic Junction/five slots/five actions/H20/vision1, legal local measurements
and truthful public lifetime interface, unchanged replay/optimizer/mixer/RNG.
Registered actor parameters G103173/A192741; complete state counts including
buffers G103199/A192768. A-G is unequal whole-program comparison, not an isolated
persistence manipulation. All measured execution is remote CPU FP32/Torch1/1,
Torch2.7.0+cu118/NumPy1.26.3, exact unchanged source and scientific argv.

All return arrays have finite complete lengths. All four checkpoints are finite,
CPU FP32, with expected arm/update/state counts and populated optimizer state.
G checkpoint176 tensors/41 optimizer slots; A230/54. Actor L2 changes are
G1=33.6245291054,A1=44.6570115429,G2=33.1718473357,A2=45.0062059672.
A1 and A2 read only their own block's G summary after their learning/evaluation;
both recorded paths and byte digests match the collected original G endpoints.

The working independent unit is the complete fresh A/G block. Distinct fixed
training/evaluation labels and no shared learned artifacts support that design
assumption; they do not prove representative independent population draws.
Common labels within a block align compatible initialization and nominal streams,
not episode-paired worlds or arm-independent stochastic draws. Each128-episode
panel is conditional on its fitted policy. Both labels vary across blocks, so
variation combines training and evaluation realizations. No population interval,
significance test, equivalence or stable ranking is inferred from n=2.

## Native handles, costs and observed deviation

| Original learner handle suffix | Supervisor PID | Wall s | User+system CPU s | Peak RSS KiB |
|---|---:|---:|---:|---:|
| 781901-generic | 3707528 | 2251.18 | 2250.28 | 768528 |
| 781901-persistent-start2 | 3712032 | 3807.79 | 3807.34 | 860896 |
| 782001-generic | 3721180 | 2150.29 | 2150.95 | 770932 |
| 782001-persistent | 3722930 | 3009.11 | 3007.83 | 863732 |

Each suffix follows folr-augmentation-repeat-b01-. Every learner supervisor
finishes exit0/tmux false. Their Monitor terminal observations are respectively
05:26:59.6896005Z,06:50:30.9480767Z,07:39:19.7270166Z and08:33:11.0417155Z
on2026-09-15. These are observation times; supervisor uptime was not used as
completed-run wall. Terminal-only native-final delivery records actual leaf
capability, not a fabricated intermediate adoption. The Monitor active set is empty.

Each invocation passed a new destination-adjacent4GiB admission. Exact measured
physical/effective bytes are15606669312,14674436096,14543785984,15615676416.
Native wall sums11218.37s and CPU11216.40s; peak max863732 KiB. A1 was207.79s
above its ordinary3600s plan; the other arms and summed wall remain below the
ordinary references. Those plans were explicitly not caps or kill lines. This
is no hard-cap breach, controlled efficiency estimate or full-cost measurement.
Full support/provider/engineering/lifetime cost remains UNKNOWN.

There were five supervisor acceptances, including the first A1 supervisor
3711036 under suffix781901-persistent. It failed exit125 at05:30:46Z because DM
omitted output-directory preparation before GNU time opened its log. The full
six-member failed-supervisor archive remains preserved. A two-command nonlearning
marker check reproduced125 with no child execution and succeeded after directory
creation (0.002735s). Thus no child/admission/learner/tick/update occurred in that
failure. Manual preparation repair1 is reported; scientific retry0. The corrected
original A1 kept source/parameters/output and a new supervisor suffix preserved
the failed original. G2/A2 directory preparation prevents the same defect.

Independent source review found no material defect. The focused synthetic suite
had26 passes/one fixture TypeError, then two affected fixture cases passed after
repair:27 distinct final passing cases,3.692396s combined process time. The
original failure, exact repair and test scratch archive/absence are preserved.
No scientific programme/card/wrapper changed for that fixture repair. Support
collection helper revision only changed the A1 supervisor binding. New non-test
module/helper source493 lines is below the selected600-line bound; scope:none.

## Retained evidence and arithmetic

All40 selected result/supervisor archive members were verified remotely and after
local transfer; the extra failed-supervisor six members remain separate. Each
BLOCK{1,2}_{GENERIC,PERSISTENT}_{SUMMARY,COLLECTION}.json and RAW.tar.gz is under
[the object evidence directory](entity_augmentation_repeat_b01_781901_782001/).
Collections retain every source/count/array/checkpoint/admission/cost check and
digest. A2 summary SHA256a5a975eee15c004dc4e3337180bbb15bb59fc91f50b0c9f144bbb7a4cb9d3f23,
checkpoint7e8fc8d458a5129a15bc6b57182e35285078cf75360e110bf10040f412c85055.
A2 raw5289635 bytes/d23ac0af49d751e4dc6dbc23cee32448b5570dda5b67f6a0b6e7f25a413006ad.
Earlier per-arm intakes preserve the other digests.

The published study_result was invoked over all four selected summaries. The
previously published read_study helper independently recomputed each conditional
panel, both differences and the frozen pattern, checked both exact own-G inputs
and matched the publication modules to source797596454. STUDY_READBACK.json is
the primary machine record. RUN_SCORES.csv contains four selected endpoint rows;
scientific-tools summarize_runs produced descriptive RUN_SUMMARY with two runs
per arm, no paired flag/episode rows/interval. A run mean-2.16578125/SD3.2016469227,
G mean0.8044921875/SD0.8435010502 are descriptive only. ANALYSIS_METHOD retains
tool/helper/input hashes, independent-unit declaration and exact route.

Complete interpretation/prediction/decisions: [DM intake](FOLR_ENTITY_AUGMENTATION_REPEAT_B01_INTAKE_20260915.md).
This E0 preserves observed validity separately from the required object-only
independent result review, support retention and cleanup, which are pending at
initial publication. No further scientific invocation is selected or authorized;
the owner requires a safe operational pause after this object's closeout.
