# Proposed B15 confirmation: bounded N6-to-N8 package usefulness

Status, 2026-09-23: proposed for the required pre-confirmation scientific criticism;
no confirmation fit has started and the direction remains exploring. The DM will
record adoption or a pre-run amendment after reading the complete advice. This
document is not launch admission. Preserve this proposal when appending amendments
and the eventual fixed-plan result; do not rewrite a plan after seeing its results.

## Question, claim and scope

For the frozen native S1 task and a fixed, previously unread evaluation panel, does
the selected H6 complete learning package, trained only at N6 for 360k team steps,
yield higher final N8 native J and a practically useful increase in actual served
users than the selected ordinary SET package across new independent training blocks?

The proposed narrow claim is a positive training-block mean final N8 J difference
and a mean service increase exceeding one user per step (2 percentage points among
50 users), conditional on the fixed final-world panel. One user is the prospectively
chosen practical service difference for this claim, not an equivalence margin or
a threshold derived from final data. It is smaller than the development gains but
not chosen to classify an already observed confirmation result.

This is a comparison of the two specified packages and exposure, not skill causality,
superiority over the class of ordinary MARL, pure count causality, convergence speed,
world-population uncertainty, real deployment safety or every-world dominance.
N6 is a separately reported training-count consequence. It is not pooled with N8
and is not used to rescue a failed N8 result. No claim of tail harmlessness is made.

## Candidate and one primary comparator

Use the exact B14 algorithmic recipes from published source
`88b67e5e0110ae05c440588a2b19ab0b6c0f021c`: native H6 with constant low-level entropy
coefficient .05, and canonical fresh-N6 ordinary SET with coefficient .05. No old
trained weights, best-seed selection, reward or noise change, changed skill cadence,
target-N training, new communication, extra training or baseline swap is allowed.

Both use native S1 uniform/free-space, actual N6, 50 users, connection cap10, k10,
16 lanes, horizon500, 45 complete rollouts, and the same external task scalar R/6.
Raw Gaussian actions and their old log-probabilities are stored; an independent
clipped [-1,1] copy is executed. Store true terminal successors before reset.
Keep B14's actual learner/sampler, normalization, recurrent reset, termination,
PPO/update, evaluation isolation and native-unit contracts.

H6's skill-conditioned local actor and high-level state/joint-observation route,
and SET's held central snapshot/set representation plus current local feedback,
retain the same declared exogenous information sources and refresh opportunities.
Representations, bandwidth, intrinsic objectives, coordinator/discriminator learning
and actual computation differ. Matching does not mean identical actor tensors,
complete rewards, random-number consumption or optimization difficulty. SET's
single-category coordinator/decoder inference and snapshot work must be counted,
despite zero high-level/discriminator optimizer updates.

The selected SET recipe has real learning and stronger retained-control evidence
in B11/B12/B13/B14. That supports this bounded primary comparison, not a claim
that ordinary methods are fully tuned. The Pro question explicitly challenges
whether further ordinary-baseline development should precede this investment.

## Fixed prospective blocks and evaluation

Proposed batch: exactly three fresh independent training blocks, each containing
one fresh H6 fit and one fresh SET fit: six started fits if no technical failure.

| Block | Learning master seed for each arm | Actual training lane world seeds | Serial order |
| --- | --- | --- | --- |
| 1 | 994101 | 2994100 through 2994115 | H6, SET |
| 2 | 994102 | 2994200 through 2994215 | SET, H6 |
| 3 | 994103 | 2994300 through 2994315 | H6, SET |

Different blocks use separate actual model/learner and exogenous random streams.
Within a block, pairing is justified by the prospectively common exogenous world
design and verified actual reset scenes/RNG, not merely matching seed integers.
Architecture-specific initialization and subsequent endogenous visits stay intact.
Create training environments before seeding learning construction as in B14.
Record every actual reset and independently compare it within each block.

At initialization0 and the sole final checkpoint45, evaluate N8 then N6, with
32 worlds per N and 500 steps each, deterministic mean-then-clip deployment and
the actual stage's own weights, normalizers and closed-loop trajectory:

- N8 worlds: 1945800 through 1945831; evaluation RNG seed1945851.
- N6 worlds: 1945600 through 1945631; evaluation RNG seed1945651.

These addresses are prospectively fixed without running, screening or replacing
them. Do not execute old development panels during this batch. All blocks/stages
share the final panels for comparable conditional readings; worlds do not multiply
the independent training n. Initial evaluation must preserve the learner, modes,
buffer, optimizers, all learning RNG and actual training-environment state.

Keep all final checkpoints and all outcomes. No intermediate performance checkpoint
selection, seed replacement, early stopping by scores, additional worlds or expansion
to five seeds after seeing three is allowed. Owner pause and genuine technical
invalidity still take precedence. Technical failures remain counted and visible;
there is no automatic retry or substitution, and missing arms are never filled by
zero or old assets. An incomplete batch cannot confirm this claim.

## Endpoint and decision rule

For each block, compute H6 minus SET final45 N8 J and S, averaging its 32 fixed
worlds. J=.7C+.3Q-P uses actual test N to recover native units; S is actual served
users per step and equals50C. The three block differences are the inference units.

Proposed uncertainty: report each block, the across-block mean and a two-sided
95% paired Student-t interval (df2) for each of J and S, conditional on this fixed
world panel. The calculation assumes independent, approximately normal block
differences. Three blocks cannot diagnose that shape; the small-n limitation and
interval assumptions must accompany the result. Do not bootstrap worlds as if
they were independent trained policies or call the two marginal intervals a
simultaneous 95% confidence region.

Support the narrow fixed claim only if the lower J interval endpoint exceeds0
AND the lower S endpoint exceeds1 user per step. Otherwise report the signed
effects and intervals as not establishing this claim; intervals crossing the
threshold are inconclusive, not equivalence or proof of no effect. An interval
entirely below a threshold is reported as evidence against that component at the
stated exposure, without broadening to all variants or tasks. No post-result
threshold, uncertainty method or sample-size change is permitted.

Report each arm's own initial-to-final J/S and all other native components as
secondary learning evidence; a final advantage cannot conceal an arm's own
regression. Report D0, D45, I_H, I_SET and Delta separately without a causal
decomposition claim. At both N, preserve every paired J/service loss, component
tradeoff, world median/range and each policy's minimum absolute J/service. N6
and adverse worlds can limit an adoption judgment even when the narrow N8 mean
claim passes; no unplanned tail acceptance region is invented.

## Development exposure and cost

All B01–B14 observations remain development, including the action-law correction,
entropy-response reversals, target-N training reversals, retained-asset selection,
and B14's newly matched training. B14 has one instance per arm on previously read
worlds; its favorable result is not included among these three independent blocks.
The selected recipes, horizon, primary comparison and practical threshold are
development-informed. Do not relabel them as untouched original hypotheses.

Planned work: six fits, 2.16M training team steps/12.96M UAV rows, plus384k
evaluation team steps/2.688M UAV rows, 768 evaluation episodes/12,000 evaluation
policy calls. Total2.544M team interactions. Each arm has45 updates and101,250
actor and critic optimizer calls; six fits total607,500 of each. The three H6
fits add2,025 coordinator,2,025 team-discriminator and8,100 individual-discriminator
optimizer calls. Retain and count actual inference, sequential decoding and SET
snapshot work as in B14; no scientific replay or old-weight control is added.

B14 measured137.854759 summed command minutes per pair on the current CPU route.
Three such pairs suggest roughly6.9 scientific-command hours, not a guaranteed
schedule or isolated-node performance estimate. Preparation, implementation,
checks/review, collection and complete reading are extra. Trace/checkpoint output
is roughly3.3GB across the six fits before keeping a second collection copy;
actual wall, CPU, peak-process RSS and storage are recorded, not assumed.

The frozen B14 CLI admits only its own seed/world bindings. A separate bounded
entrypoint is needed; do not mutate or bypass that contract. It may parameterize
only these declared blocks/worlds and keep the algorithmic route unchanged.
The exact reviewed implementation and source SHA must be committed/pushed and
recorded before the first confirmation launch, with targeted seed-path,
initialization, isolation, actual-world and native-execution checks. No new fit
is used merely to decide whether to run the batch.

## Advice, pre-run amendments and result

Pending the focused pre-confirmation critique and DM decision. No confirmation
execution, acceptance or result is asserted here.
