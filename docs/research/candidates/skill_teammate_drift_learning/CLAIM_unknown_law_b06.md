# B06: early adaptation with a learned joint law

Adopted without experimental changes on 2026-09-21 after reading the complete Pro
criticism preserved in NOTES.md. No B06 fit had started at adoption. This is a
finite-package claim, not novelty, universal model-based superiority, endogenous MARL
or UAV deployment.

## Hypothesis and comparison

On the four-context, two-version correlated terminal host defined in B05, all-history
conditional-response learning with a causal estimated joint law has higher expected
task value over the first 64 target decisions than the development-selected full-history
direct-value learner. The underlying collection is passive and common to all methods;
the estimand is the exact expected value of each sequentially trained greedy decision
under that collection history, not an action-induced learning trajectory.

Frozen response: `response_all__response__prior2`.
Primary reference: `fingerprint_full__hybrid__prior2`.
Secondary reference: `fingerprint_recent__hybrid__prior16__window256`.
No retuning or additional alternative after reading B06 outcomes.

The B05 selection is published at `1d311f8d5ef03b02886ebfedda881091d16b5526`,
`runs/skill_teammate_drift_learning/b05_unknown_law_development/selection.json`, SHA256
`ca32b21255d9bc60efb2c17fb1a7757d506d7fcaa49594db9a5ed9e3d3bd16e5`.
The exact B05 learner/host bytes are at `afe4f8ec74d48b2485db3d935de7871c86cc0e6c`.
The new entry will retain them and bind the selection bytes, fresh seeds and output
identity through native admission. A wrapper/reduction change requires proportionate
checks and independent executable review before launch.

## Selection exposure and rationale

B05 development used 95001–95003, 20 settings per block, 60 decision and three law fits.
Each family selected independently using the preregistered first64 feedback-only DR
score; whole-target observed reward Brier and lexical id resolved ties. The direct
bank included law-only, current-cell and hybrid models, two prior/precision strengths,
and two recent windows. These finite settings do not establish an optimal comparator.
Two earlier tiny correctness fixtures also touched development identity 95001; their
48 macros/six decision learners are recorded in NOTES. No proposed B06 seed was used.

B05 held-out exploration at 95101–95103 added nine decision and three law fits. Early
response-minus-full values were -.001796875, +.025781250, +.006718750. Full-target values
were all positive, but remain secondary. This motivates checking repeatability without
promoting that secondary endpoint or identifying a mechanism from the package ranking.
Full direct is primary because it is the stronger observed early reference; this is
an explicitly outcome-informed pre-confirmation choice. Recent remains secondary.

## Population, data and training

Five independent fresh block seeds: **95201, 95202, 95203, 95204, 95205**. One common
collector and one shared-law fit per block, plus three independent decision learners.
Each block uses 2,048 source + 256 target macros, three primitive ticks each, float64,
local_linux CPU and one BLAS thread. Context/version law generation, balanced cycling,
reward, uniform collector, lawful source-derived target prior, pre-outcome snapshots
and all parameter values remain B05's. No private true law or true response enters
learning or selection. No checkpoint choice; evaluate every pre-update decision by the
same exact-value evaluator, and retain all raw data and final states.

## Endpoint, uncertainty and decision rule

Primary block value is mean exact expected greedy reward over the first 64 target
decisions. The paired difference is response minus full direct, one value per fresh
block. Report every signed value, mean, paired sample SD and a two-sided 95% Student-t
interval for the mean (df4). This small-sample interval assumes an approximately normal
distribution of independent block differences; it is not distribution-free. Never use
the 64 nested decisions as 64 independent fits.

Operational support rule: mean difference at least **.005** and the primary
95% interval wholly above zero. The .005 scale is approximately one ninth of the full
reference's B05 early regret; it is selected before B06, not a global project threshold.
Passing means the point estimate reaches .005 and the parametric interval excludes
zero; it does not establish a true mean of at least .005. The expected reward scale
is .32 over 64 target decisions. Five blocks may leave a wide interval; no precision
guarantee follows from the seed count. Do not pool the outcome-exposed B05 blocks into
this confirmation. Report practical importance separately from uncertainty. If the rule fails, call the
planned confirmation inconclusive or adverse according to its actual signs/interval;
do not infer equivalence or no research value. Do not add seeds to this batch.

Retain full-256 mean/cumulative regret, late64, secondary recent contrasts, action
counts, context-specific mistake cost, response/law/SAFE errors and known-response
diagnostic. They qualify explanation and future investment but cannot replace a failed
primary. A positive early result with adverse full-target value supports only the early
claim. All outcome branches receive a cumulative NOTES update; no automatic direction
closure follows from the batch ending.

## Planned cost and next action

**20 fits**: 15 decision learners + five shared-law learners, no parameter search.
11,520 unique macros / **34,560 primitive ticks**; 34,560 decision-reading macros /
103,680 tick exposure. 34,560 exact decision panels +11,520 shared diagnostic panels;
zero new evaluation environment ticks/reward draws and zero gradient-optimizer calls.
Posterior/statistic update and ridge solve counts depend on the collector and will be
reported. B05's scientific-process time was 5.299 seconds for 75 settings/law fits;
this is context, not a promised B06 duration or project-end-to-end speed. Measure the
new complete process wall/RSS. One fixed batch, no score-dependent extension.

The full Pro answer supports this fixed recurrence observation with MATERIAL_DISSENT no.
The DM adopts it in NOTES, retaining selection sensitivity, finite representation and
shared-law estimation limits. No extra direction, current-law oracle, reward edit or
score-dependent rescue is part of this batch. All numerical rules and settings remain
the original pre-Pro proposal; these clarifications narrow interpretation only.
