# UCOPE competence-first scout R01 B1 result evidence — 2026-09-01

## Question and evidence burden

Object `UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01` is a
`B/EXPLORE` study family. The valid B1 run asks, on one finite eight-context
UCOPE host and fresh paired data, whether target freezing or a low-dimensional
Bellman-complete learner package produces competence and, only after
competence, positive endogenous paid acquisition.

The claim ceiling is a preliminary finite-host, named-package observation.
This evidence cannot establish stable superiority, seed-population effects,
pure representation or optimization attribution, generic paid-information
value, COUNT-versus-RAW polarity, variable-`k`, variable-`N`, general MARL or
UAV performance, transfer, safety, deployment, flight, energy, or real-world
QoS. B1 is adaptive exploratory evidence, not a consumed confirmatory C object.

The strongest live alternative is that odd-to-even extrapolation, finite
optimizer exposure, fold-specific conditioning, and common root/tail
regression difficulty dominate all three learner packages. In particular, a
BC failure under finite-step FP32 AdamW is not evidence that its basis is
structurally incapable, and a FLEX/BC difference is not a pure representation
effect.

## Inputs and validity boundary

The valid result is the complete publication at:

```text
temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/
```

Only this complete tree was read for B1 scientific interpretation. Its retained
identities are:

```text
result.json SHA-256
  72deee383f2b0ff366e43ddcb43e17fe449c4f9616caf9a9e4f1ed3340bc16b6
resource-ledger.json SHA-256
  4406f7d8f54bbb47c5ba08b0f65d866a4d1bd673aba8aa6451c17eddeed21acb
terminal-receipt.json SHA-256
  798079a308d8a5fc83642f1fc34ac682cd54e26722bc78387eb6fb3419bf1d5c
source aggregate
  16ebd3bc30dc667bbc2e47037757290375f9ac7aa08309cef7e22d820644e9e6
manifest digest
  47405ebc4def488404b285d9fafb55e8d2b24b4342049ae08f608316684721a9
assessment digest
  cbae52fae338e0410935c50b9099ecab1d852b6d3ab647c5977d030b0ac74c31
```

Independent mechanical acceptance found `ARTIFACT_VALID/COMPLETE`: the
complete tree contains 72 bound checkpoints plus the result, resource ledger,
and terminal receipt; its journal/hash chain has 75 rows; fresh admissions,
process-tree telemetry, and all resource caps pass. The terminal receipt reports
combined peak RSS `455,200,768` bytes below the `603,979,776`-byte cap, wall
time `140.4895537 s` below `900 s`, and `combined_cap_pass=true`. These facts
establish a valid observation, not algorithm value.

The exact B1 comparison is:

- arms: `MT-XF-FLEX`, `FT-XF-FLEX`, and `FT-XF-BC`;
- three fresh seeds, two group-disjoint folds, eight contexts;
- `5,120` environment episodes per context and seed;
- `160` tail and `320` root optimizer updates per arm/seed/fold;
- checkpoint evaluations after root updates `40`, `80`, `160`, and `320`;
- exact finite-host evaluation plus 64 fresh paired sampled episodes per
  context/policy/checkpoint; and
- final checkpoint `320` alone controls the gates.

All arms share fresh data, BELIEF information, folds, example inventories,
batch size, update counts, checkpoint schedule, and evaluation. MT and FT FLEX
have `9,742` parameters each and paired initialization; BC has `12` parameters,
so FLEX-versus-BC is explicitly a learner-package comparison rather than
compute or parameter parity.

## Direct observation

### Work and support

The result retains:

```text
environment episodes/transitions       122,880 / 614,400
root/tail rows                          122,880 / 61,440
root/tail optimizer updates             5,760 / 2,880
root/tail example exposures             1,474,560 / 737,280
exact policy evaluations                576
sampled evaluation episodes/transitions 36,864 / 164,352
checkpoint writes / policies completed  72 / 18
nonfinite training events               0
```

Every seed has all displayed-count bins `0..6` in every context and fold. The
smallest retained bin count is `39`; all three `support_limited` flags are
false. Thus the result is not a support-refusal branch.

MT executes `1,920` root-target refreshes over `245,760` rows. The twelve
frozen-arm policies execute twelve target materializations over the same
`245,760` rows. This confirms that the two intended credit schedules were
actually exercised under equal optimizer and example exposure.

### Competence gate

For each final fold policy, competence requires all-finite scores, unique
choices, the exact eight-context oracle root vector, maximum expected regret
at most `0.02`, and minimum forced-PROBE tail agreement at least `0.95`. A seed
passes only when both folds pass; an arm is competent only when at least two of
three seeds pass.

All 18 final policies have finite scores and unique choices. None matches the
oracle root vector, none reaches the regret threshold, and none reaches the
tail-agreement threshold:

| arm | seed | fold | max regret | min tail agreement | oracle root | competence |
| --- | --- | ---: | ---: | ---: | --- | --- |
| MT-XF-FLEX | fresh-00 | 0 | 0.06943710125 | 0 | no | no |
| MT-XF-FLEX | fresh-00 | 1 | 0.15323855875 | 0 | no | no |
| MT-XF-FLEX | fresh-01 | 0 | 0.38090693125 | 0 | no | no |
| MT-XF-FLEX | fresh-01 | 1 | 0.1 | 0.52072671875 | no | no |
| MT-XF-FLEX | fresh-02 | 0 | 0.268 | 0 | no | no |
| MT-XF-FLEX | fresh-02 | 1 | 0.048 | 0.829299140625 | no | no |
| FT-XF-FLEX | fresh-00 | 0 | 0.37394275375 | 0 | no | no |
| FT-XF-FLEX | fresh-00 | 1 | 0.15323855875 | 0 | no | no |
| FT-XF-FLEX | fresh-01 | 0 | 0.38090693125 | 0 | no | no |
| FT-XF-FLEX | fresh-01 | 1 | 0.1 | 0.52072671875 | no | no |
| FT-XF-FLEX | fresh-02 | 0 | 0.268 | 0 | no | no |
| FT-XF-FLEX | fresh-02 | 1 | 0.048 | 0.829299140625 | no | no |
| FT-XF-BC | fresh-00 | 0 | 0.268 | 0 | no | no |
| FT-XF-BC | fresh-00 | 1 | 0.268 | 0 | no | no |
| FT-XF-BC | fresh-01 | 0 | 0.18943710125 | 0 | no | no |
| FT-XF-BC | fresh-01 | 1 | 0.38090693125 | 0 | no | no |
| FT-XF-BC | fresh-02 | 0 | 0.148 | 0 | no | no |
| FT-XF-BC | fresh-02 | 1 | 0.18943710125 | 0 | no | no |

Across all 72 checkpoint rows, not only the final rows, all scores remain
finite and unique, but there are zero oracle-root matches, zero policies with
regret at most `0.02`, zero policies with tail agreement at least `0.95`, and
zero competence passes. The closest observed regret is `0.02143710125`; the
largest observed minimum tail agreement is `0.829299140625`. No transient
checkpoint supplies competence evidence.

The final seed-level and arm-level result is therefore:

```text
MT-XF-FLEX competent seeds = 0/3; B_COMPETENT=false
FT-XF-FLEX competent seeds = 0/3; B_COMPETENT=false
FT-XF-BC   competent seeds = 0/3; B_COMPETENT=false
branch = NO_ARM_COMPETENT
```

### Adjacent arm observations

At checkpoint 320, MT-XF-FLEX and FT-XF-FLEX have exactly equal
result-serialized tail-score maps and tail choices in all six paired seed/fold
policies. Their complete root labels,
root actions, regret, and tail metric are also equal in five of six final
pairs. The sole final action-level difference is fresh-00/fold-0; neither
member is competent. Across all 24 paired checkpoint rows, the target schedules
do change some root actions, but neither schedule ever reaches competence.
This is no positive target-freezing signal and no equivalence claim.

FT-XF-BC has minimum tail agreement `0` in every final fold policy and at every
checkpoint. Both FLEX arms show two final folds with nonzero tail agreement
(`0.52072671875` and `0.829299140625`) but retain four final folds at zero and
never reach the `0.95` gate. BC therefore supplies no competence advantage;
the FLEX pattern is heterogeneous and remains below competence. Because the
packages differ in inductive bias, conditioning, parameter count, and
optimization geometry, this observation cannot isolate representation.

Final endogenous root patterns range from zero to eight PROBE choices across
the eight contexts; no final policy selects PROBE only in the sole oracle
target context `LINKED-p17_20-c9_100`. This agrees with the zero oracle-root
matches and does not independently establish acquisition value.

### Paid acquisition and COUNT/RAW

The protocol permits paid-acquisition evaluation only for a seed whose two
final fold policies first pass competence. No seed qualifies. Consequently all
`target_delta_acquisition` and `direct_probe_component` result fields remain
`null`, and `acquisition_pass=false` is a locked downstream gate rather than a
negative acquisition observation.

The retained gate output is:

```text
arm_acquisition_positive = false for all arms because competence admitted none
count_raw_status = LOCKED
```

B1 therefore provides no paid-acquisition polarity and no COUNT-versus-RAW
polarity. It does not authorize a separate COUNT/RAW design.

## Inference and limitations

The smallest supported proposition is that, on this exact fresh finite-host
B1 configuration and optimizer exposure, none of the three named learner
packages established the prerequisite competence needed to interpret paid
acquisition. The result localizes the immediate failure to this
host/package/budget discriminator; it does not close the UCOPE question.

The result does not support the conjecture that target freezing is sufficient
for competence: FT-XF-FLEX is no more competent than paired MT-XF-FLEX. It also
does not support the conjecture that the gradient-trained low-dimensional BC
package is sufficient: FT-XF-BC is no more competent than FT-XF-FLEX. The
prospective contradiction rules are not triggered either, because neither
adjacent arm reaches competence. Thus both mechanism explanations remain
unresolved rather than positively accepted or structurally refuted.

The most decision-relevant unresolved alternative is common learnability:
finite-step optimization and odd-to-even extrapolation may dominate both
target-schedule and architecture contrasts. The heterogeneous FLEX tail
agreement and the BC all-zero tail agreement make an optimization/conditioning
diagnostic potentially informative, but this is an inference from the observed
patterns, not a demonstrated cause.

## Judgment impact pending persistent convergence

This evidence is ready for the persistent `em:ucope:convergence` node. No local
CONTINUE, PARK, CLOSE, or RECAST decision is formed in this note. The Pro node
must decide whether one adaptive, explicitly named competence-focused B run is
still the cheapest valuable discriminator, whether this particular host/budget
realization should be retired and UCOPE parked, or whether a recast is justified.

Any continuation must preserve B1, name the changed budget/optimizer/measurement
and its outcome-informed reason, keep acquisition and COUNT/RAW locked until a
FLEX seed passes both folds, and remain within the B/EXPLORE ceiling. Direction
closure would require evidence beyond this one valid exploratory
non-competence result.

## Exact evidence and contract paths

- `temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/result.json`
- `temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/resource-ledger.json`
- `temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete/terminal-receipt.json`
- `docs/research/candidates/ucope/UCOPE_B_EXPLORE_MT_XF_BC_COMPETENCE_FIRST_SCOUT_R01_INNOVATOR_INTAKE_20260901.md`
- `experiments/candidates/ucope/competence_first_scout_r01/contract.py`
- `experiments/candidates/ucope/competence_first_scout_r01/evaluation.py`
- `experiments/candidates/ucope/competence_first_scout_r01/gates.py`
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`
