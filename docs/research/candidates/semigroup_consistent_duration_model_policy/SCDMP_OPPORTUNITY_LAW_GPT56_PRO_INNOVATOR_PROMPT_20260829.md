# Independent scientific challenge: one corrected opportunity law for the pallet/gantry simulator

We need a result-blind mathematical and causal challenge to a prospective opportunity law for a
fixed-four-carrier planar pallet/gantry simulator. Please act as an innovator and adversary rather
than as a code reviewer. Look for a proof-sized construction that makes the law coherent, a minimal
counterexample that defeats it, or an unused alternative that changes the discriminator. Do not
assume that bundling two repairs under one name makes them one scientific correction.

The simulator begins with a rigid cable-suspended pallet and public initial coordinates
`v ~ Uniform[0,0.03]`, `y ~ Uniform[-0.01,0.01]`, and
`phi ~ Uniform[-0.01,0.01]`; every other public first-renewal coordinate is fixed. Four equal,
action-independent setup slots contain common `SYNC` and `LEVEL-RELEASE` sentinels around two
middle events. Starting from cable assignment `(1,2,3,4)`, `HOOK-HANDOFF` maps a tuple to
`(p2,p1,p3,p4)` and `FORMATION-ROTATE` maps it to `(p4,p1,p2,p3)`. The two orders therefore end in
different latent support assignments, `(4,2,1,3)` and `(1,4,2,3)`. `LEVEL-RELEASE` resets public
cable tensions and releases the pallet without changing the latent assignment. At the first
actionable renewal, both orders have exactly the same public observation and differ only in latent
support. This is an invented simulator event law, not a claim that the named operations have this
effect on a real aircraft.

There are eighteen legal first actions: common forward demand one or two, crossed with nine
zero-sum load-share patterns. For each target fixed hold period seven or thirteen, the opportunity
assay forces one first action for the announced hold and then returns control to the same frozen,
deterministic, order-erased foundation for the rest of the mission. The direct rollout value is
safe docking times remaining completion fraction,
`U = 1[safe dock] * (1 - t_dock/36.4)`, with zero for failure or timeout. No reward proxy or
one-interval score is allowed.

The stage order is protected. Twenty-four independently trained order-erased foundation
replicates must first pass a complete competence panel: every order-by-regime safe-docking lower
bound must exceed 0.72, the pooled lower bound must exceed 0.84, and all four worst-regime
physical-failure upper bounds must be below 0.10. A nonpass is nonidentification and ends before
opportunity. Only after a pass may the corrected opportunity assay run. Its three simultaneous
one-sided Bonferroni lower bounds must exceed `Q=0.20`, `D=0.025`, and `S=0.060`. An opportunity
nonpass is a bounded no-opportunity result. Passing both gates would only make a later order-aware
adapter eligible for separately authorized work; no adapter exists or may be built in the present
cycle.

The earlier opportunity definition had two result-blind defects. It said to draw sixteen aliased
first-renewal public states per replicate and target period but did not give a single-valued draw
law. It also drew four future-disturbance tapes for each state and used the same four-tape averages
both to choose graph-specific and common action extrema and to report the opportunity quantities.
That plug-in maximum can be positive even when every action has equal true expected value.

The proposed single correction treats population and estimator as one probability functional.
First, it completes the three displayed initial marginals as a mutually independent product law.
For each target period, the public-state measure is the pushforward of that product to the exact
first-renewal observation, with the period inserted deterministically. Sixteen states are drawn
independently from this common measure for every replicate and period. Each realized state is
instantiated under both latent support assignments; graph order never changes the public draw.

Second, for every state it draws four fresh complete future-disturbance tapes independently of the
state, graph, action, foundation and treatment. A realized tape is nevertheless shared across both
graphs and all actions within that state as a paired common random number. Tapes one and two form a
predeclared selection fold and tapes three and four form a predeclared evaluation fold, after which
the roles swap.

On a selection fold, let the two-tape mean for graph `q` and action `A` be `Ubar(q,A)`. With
lexicographic tie breaking, select a graph-specific maximizing action, a graph-specific minimizing
action, and one common maximizing action, where the common objective is the average of `Ubar` over
the two graphs. Use only the other fold to evaluate those already fixed actions. In one direction,
`D` is half the sum across graphs of held-out graph-specific-max value minus held-out common-action
value. `S` is half the sum of held-out selected-max minus held-out selected-min value. `Q` is one
only if the two selected graph-specific maxima are distinct and, on held-out tapes, each selected
graph-specific action strictly beats the selected common action in its own graph. Exact held-out
ties do not count. Swap folds and average the two `Q`, `D`, and `S` values. Average the thirty-two
period-by-state cells within replicate, then form the unchanged three lower bounds across the
twenty-four independent foundation replicates. No tape that selected an action contributes to that
action's reported held-out value.

A useful prior counterexample has two actions and one independent Bernoulli bit per tape. On graph
zero, action zero has value `0.5 Z` and action one has value `0.5(1-Z)`; on graph one the assignments
reverse. Every action has true expected value 0.25 in both graphs, hence true graph-conditioned
opportunity is zero. The old four-tape plug-in extrema nevertheless have expected
`Q=0.625`, `D=0.09375`, and `S=0.1875`, all above the registered thresholds. Please compute what
the exact proposed cross-fit reports for this witness, then search for a stronger joint
potential-outcome law on values in `[0,1]` that respects all declared independence and pairing yet
still creates population-level simultaneous positive `Q`, `D`, and `S` when all actions have equal
true expected value. Distinguish such a structural counterexample from ordinary finite-sample
Type-I risk under the frozen simultaneous family.

The central conceptual question is not merely whether sample splitting removes same-sample
maximization bias. Decide whether the held-out functional still estimates graph-conditioned direct
physical first-action opportunity, or instead changes the target to the performance of a noisy
two-tape action-selection algorithm. Give an explicit prediction that distinguishes those two
estimands. Also decide whether completing the state measure and cross-fitting its conditional value
functional are genuinely one atomic opportunity law, or two independent post-hoc repairs hidden
inside one correction. A treatment-dependent measure, unreachable state support, leakage,
non-single-valued tie behavior, causally meaningless `Q`, or changed physical estimand is terminal
for this bounded search.

Primary sources support only broad modeling primitives: rigid cable-suspended payload dynamics and
unilateral tension, disturbance rejection and formation control, failure-driven load reassignment,
and bounded sample-and-hold reasoning. They do not validate the exact event maps, latent incidence
vectors, action catalogue, coefficients or thresholds. Useful primary references are Sreenath and
Kumar, RSS 2013, `https://www.roboticsproceedings.org/rss09/p11.pdf`; Han et al., IEEE Access 2022,
`https://doi.org/10.1109/ACCESS.2022.3222031`; Liang et al., Aerospace Science and Technology 2021,
`https://doi.org/10.1016/j.ast.2021.107139`; and Omran et al., Automatica 2016,
`https://doi.org/10.1016/j.automatica.2016.02.013`.

If the GitHub connector is useful for scientific reference, the origin-reachable repository is
`https://github.com/CartmanFatass/My-paper-code.git` at commit
`118dd153d01eb0a41f005ce44746c7c7507699fd`. The complete prospective target definition is
`docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_TARGET_BOUND_COMPETENT_CONTROLLER_ORDER_VALUE_SCIENCE_CARD_REVISION_02_20260821.md`.
Source code and repository text are scientific reference only, not code-review scope. The current
local integrated Portfolio baseline is `86d699eb3dfdb09e79740783e407224a303a1750`; do not infer that
this local commit is available through the connector.

Conclude at the narrowest justified ceiling. A positive answer means only that this one prospective
simulator-only state-and-cross-fit law is coherent enough for a later separately authorized attempt
to run the foundation competence gate and, conditionally, the corrected opportunity gate. It does
not pass either gate or support an adapter, general chronology, semigroup composition, arbitrary
event length, arbitrary hold periods, variable populations, another simulator, real-aircraft
transfer, safety, deployment or flight. A negative answer should identify the smallest decisive
defect and the exact remaining alternative, without proposing training, implementation, a new
threshold, a new tape count, a new action catalogue, a second correction or a Portfolio action.
