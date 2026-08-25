# External Gemini innovation question — VQFP-FERL r01

Act as a divergent scientific innovator, not a code reviewer or final causal
authority. Review the following prospective variable-`N` MARL object without
seeing any other reviewer response. Seek overlooked physical regimes,
counterexamples, shortcut explanations, better controls and toy-to-UAV
interpretations that could materially change the design before activity.

The object is `VQFP-FERL-SCIENCE-20260821-01`. One shared permutation-
equivariant policy trains at `N={4,8}` and is evaluated without adaptation at
held-out `N={6,12}` on an open one-dimensional ridgeline. Two action-independent
plume-front urgency ridges move along the line. Each agent owns its physical
Voronoi cell and observes its current cell length, a deployable noise-free
cell-average plume-gradient reading, unrelayed data backlog, link quality,
previous allocation, time and immediate physical-neighbor records. The
simulator-truth high-gradient mask scores endpoints but is not an actor input.
The actor does not see future plume motion, front identity, evaluation cell or
arm label.

Every tick has one fixed roster-invariant physical budget `E=0.20` divided
over all agents' SENSE and RELAY modes. Sensing coverage in cell i is
`1-exp(-4*s_i/v_i)`; sensed plume-gradient data joins a backlog and relay
delivery is limited by link quality times relay effort. The direct lower-is-
better endpoints are integrated unserved high-gradient length, the 0.90 tail
of front-entry discovery delay and total relay-service gap.

The structured arm has action logits
`log(v_i)+q_(i,mode)`. The strict-containing comparator has
`log(v_i)+q_(i,mode)+residual_(i,mode)`. Both share information, recurrent
backbone, critic, actions, total effort, initialization, samples, optimizer work
and nominal parameters; the residual is zero-initialized, and setting it to
zero makes the comparator literally identical to the structured arm. Actions
are a fixed-concentration Dirichlet allocation over all `2N` slots. A frozen
reassociation intervention cyclically assigns the wrong length only at the
measure/residual port. A third matched learned `FREE-NO-MEASURE-PORT` arm
replaces every explicit length by `1/N` while preserving architecture and work.
Nonlearned EQUAL-MASS and a feasible exact current-state analytic allocator
qualify opportunity and headroom; the analytic rule is not a dynamic bound.

The result law first requires physical opportunity, nondegenerate policy-mean
allocation and both SENSE/RELAY modes, per-N competence of all learned arms,
endpoint interiority/event support and adequate precision. It then distinguishes
structured-arm harm, structured value over the containing controller, free-
controller superiority, explicit-measure-port value without hard-prior value,
generic allocation value without measure specificity, target-specific
no-materiality and unresolved evidence. No outcome automatically opens a 2-D
surface, new budget, UAV run or deployment.

Please answer:

1. What physical scenario or failure mode would make a fixed total effort and
   correct Voronoi measure genuinely decision-critical rather than a synthetic
   feature correlation?
2. What plausible shortcut could make the structured arm win even if correct
   physical measure is not the cause?
3. Is `FREE-MEASURE-CONTAIN` the strongest scientifically useful containing
   comparator, or is one additional control essential? Give only controls that
   would change retain/delete/modify decisions.
4. Does the reassociation intervention isolate useful measure association, and
   what should its result not be allowed to claim?
5. Which opportunity, support, competence or answerability failure is most
   likely, and can it be prevented prospectively without tuning to results?
6. Suggest at most one materially better one-dimensional physical DGP or endpoint
   change, only if it preserves the fixed-effort question and strict containment.
7. Map the strongest surviving positive result to a credible UAV sensing/relay
   use case, and state the decisive missing step before any 2-D or flight claim.

Conclude with a compact recommendation: keep the frozen object, make one exact
science-bearing revision, or abandon it as nonidentifiable. Do not use another
direction's result as evidence, choose portfolio priority, authorize activity,
or assess implementation/runtime.
