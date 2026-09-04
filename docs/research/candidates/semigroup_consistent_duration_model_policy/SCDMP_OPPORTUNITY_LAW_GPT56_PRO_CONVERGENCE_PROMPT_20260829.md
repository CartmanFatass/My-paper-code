# Independent convergence review of the corrected pallet/gantry opportunity law

Please give a conclusion-blind scientific review of one frozen prospective correction to a
foundation-conditioned first-action opportunity assay. Do not review code or infer a preferred
answer from the way the evidence is presented. Decide independently whether exactly one coherent,
meaning-preserving opportunity law survives, or whether a measure, causal, estimator, or
one-correction defect is decisive. Check every displayed calculation and preserve any material
outlier.

The fixed simulator has four carriers transporting a rigid cable-suspended pallet. Two visible,
equal-duration, action-independent middle events act on the latent cable assignment. Starting from
`(1,2,3,4)`, hook handoff maps a tuple to `(p2,p1,p3,p4)` and formation rotation maps it to
`(p4,p1,p2,p3)`, so their two orders end at `(4,2,1,3)` and `(1,4,2,3)`. A common level-release
sentinel resets public cable tensions without changing the latent assignment. Both orders therefore
share the exact first-renewal public observation and differ only in latent support. This is a
simulator definition, not a real-aircraft claim.

The protected assay has eighteen legal first actions. At target hold period seven or thirteen, it
forces one first action for the full announced hold and then returns control to the same frozen,
deterministic, order-erased foundation for the complete mission. Its only value is
`U = 1[safe dock] * (1 - t_dock/36.4)`, with zero for failure or timeout. The intended opportunity
question is whether graph-specific first actions have higher expected direct full-mission value
than the best one action common to both graphs.

The order-erased foundation must independently pass first: every order-by-regime safe-docking lower
bound above 0.72, the pooled lower bound above 0.84, and all four worst-regime physical-failure
upper bounds below 0.10 across twenty-four independently trained replicates. A nonpass is
nonidentification and stops. Only after competence may an opportunity assay be considered; its
three simultaneous lower bounds must exceed `Q=0.20`, `D=0.025`, and `S=0.060`. A nonpass is a
bounded no-opportunity result. Passing both gates would merely make an adapter eligible for later
separate work; no adapter or empirical action is in scope here.

The historical opportunity definition had two result-blind defects. It named sixteen aliased
public states per replicate and target period without an exact draw law, and it used the same four
future-disturbance tapes to select action extrema and to evaluate them. The frozen candidate makes
the displayed mission-initial marginals for velocity, lateral offset, and pallet roll a mutually
independent product, pushes that common law to first renewal with the target period inserted
deterministically, draws sixteen states independently, and pairs every realized public state under
both latent support assignments. It also draws four complete disturbance tapes independently of
state and graph, while sharing each realization across graphs and actions inside a state.

Tapes one and two form one fold and tapes three and four the other. On one fold, lexicographic tie
breaking selects a maximizing and minimizing action separately for each graph and selects one
common action maximizing the graph-average sample value. Only the other fold evaluates those fixed
candidates. In that direction, `D` is the graph-average held-out selected-max value minus held-out
common-action value; `S` is the graph-average held-out selected-max minus selected-min value; and
`Q` is one only when the two graph-specific selected maxima differ and each strictly beats the
selected common action in its own graph on held-out tapes. The folds then swap and the two values
are averaged before state/period and replicate aggregation. No tape that selected an action reports
that selected action's held-out value.

Several result-blind observations now need convergence.

First, the antecedent target card states only the three uniform marginals. It does not state their
joint copula or mutual independence, although it explicitly uses independence language for later
disturbance coordinates. On unit-uniform coordinates, both the product density and
`1 + theta*(1-2*u_y)*(1-2*u_phi)` for any `0<|theta|<1` are positive full-support joint densities
with those same marginals, while their expected `u_y*u_phi` differs by `theta/36`. The candidate
product is internally single-valued and graph-invariant once adopted. Please decide whether it is
nevertheless derived from the named mission-initial law, or is a separate population choice that
cannot be bundled with the estimator repair under the one-correction boundary.

Second, the split fixes the supplied historical equal-value witness. If `K12` and `K34` are the two
independent two-tape Bernoulli counts, exact selection yields `Q=0`,
`D=(K12-1)*(K34-1)/4`, and `S=(K12-1)*(K34-1)/2`; all three expectations are zero. More generally,
when every action has equal true conditional mean at a public state within each graph, held-out
independence forces population `D=S=0`. This is the strongest supporting lemma for the proposed
repair. It is not enough by itself if the corrected quantities target a different opportunity.

Third, consider three distinguished actions `a0,a1,a2`, with every other catalogue action fixed at
value 0.5. Each complete future tape is type `R` with probability one fifth or type `C` with
probability four fifths. In graph zero the `(a0,a1,a2)` values are `(0,0.9,1)` on `R` and
`(0.8,0.3,0.1)` on `C`. In graph one they are `(0.3,0.9,0.6)` on `R` and `(1,0,0.6)` on `C`.
The true means are therefore `(0.64,0.42,0.28)` and `(0.86,0.18,0.60)`. Action `a0` is uniquely
optimal in both graphs and uniquely maximizes the graph-average mean, so the intended oracle
graph-specific opportunity is zero.

For a mixed two-tape selection fold, which occurs with probability `8/25`, the graph-specific
selectors choose `a1` in graph zero and `a0` in graph one, while the pooled selector chooses `a2`.
The held-out strict comparisons both pass unless the evaluation fold is `R/R`, giving
`Q=(8/25)*(24/25)=192/625=0.3072`. The mixed selection fold has true held-out `D=0.20`; `R/R`
selection has `D=-0.07`; `C/C` has zero, so
`D=(8/25)*0.20+(1/25)*(-0.07)=153/2500=0.0612`. The selected-max-minus-min contrasts are `-0.52`,
`0.23`, and `0.52` for `R/R`, mixed, and `C/C`, hence
`S=(1/25)*(-0.52)+(8/25)*0.23+(16/25)*0.52=241/625=0.3856`. Thus all three population quantities
clear their point thresholds although one common action is uniquely optimal. Check whether this is
a valid structural counterexample in the admitted bounded full-mission potential-outcome class, or
whether some frozen simulator-law restriction proves it irrelevant. Do not assume an unstated
restriction.

The algebraic distinction is that, after averaging out the held-out fold, the candidate estimates
the expected true value of actions returned by graph-specific and pooled sample-size-two selectors.
The intended oracle quantity instead takes true expected-value maxima before comparing the two
graphs with the best common action. Cross-fitting removes evaluation optimism but not selector
regret, and the two sides use different selectors. Decide whether that is merely a finite-sample
estimation detail or a changed physical estimand. Bonferroni inference protects intervals about the
chosen population functional; it cannot by itself establish equality between two different
functionals.

A counterexample in the other direction also matters. With deterministic values `(1,0)` across
graphs for `a0` and `(0,1)` for `a1`, the graph-specific oracle optima are disjoint and the oracle
advantage is one half. But the selected common action must equal one graph-specific action, making
the candidate's bilateral-strict held-out `Q` zero. Decide whether this confirms that `Q` no longer
means prevalence of disjoint optimal-action sets.

Primary literature supports only broad host ingredients: rigid multi-quadrotor cable-suspended-load
dynamics and unilateral tension; formation and disturbance control; suspension-failure load
reassignment; and bounded sampled-data reasoning. It does not validate the exact event maps,
incidence vectors, action catalogue, numerical plant, state copula, thresholds, or statistical
functional. The exact object must remain simulator-only. Relevant sources are Sreenath and Kumar,
RSS 2013, `https://www.roboticsproceedings.org/rss09/p11.pdf`; Han et al., IEEE Access 2022,
`https://doi.org/10.1109/ACCESS.2022.3222031`; Liang et al., Aerospace Science and Technology 2021,
`https://doi.org/10.1016/j.ast.2021.107139`; and Omran et al., Automatica 2016,
`https://doi.org/10.1016/j.automatica.2016.02.013`.

For repository scientific reference only, not code-review scope, the origin-reachable repository is
`https://github.com/CartmanFatass/My-paper-code.git` at commit
`118dd153d01eb0a41f005ce44746c7c7507699fd`. The prospective target card is
`docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_TARGET_BOUND_COMPETENT_CONTROLLER_ORDER_VALUE_SCIENCE_CARD_REVISION_02_20260821.md`.

Return one narrow scientific disposition. If the proposal survives, state the exact equality or
causal argument that makes its state law derived, its selector functional the intended direct
opportunity, and the combination one correction. If it does not survive, identify the smallest
decisive defect, preserve the useful cross-fit lemma, state the remaining alternative, and explain
what the result does not imply. Do not recommend implementation, foundation execution, new tape
counts, revised thresholds, a second correction, adapter work, deployment, or a Portfolio lifecycle
action. The maximum possible positive ceiling is only coherence of this one simulator-specific
prerequisite law; neither empirical gate has run, and no claim reaches an adapter, general
chronology, semigroup composition, arbitrary hold periods, variable populations, real-aircraft
transfer, safety, deployment or flight.
