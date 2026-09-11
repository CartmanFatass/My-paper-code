Claim proposed for a later B: a fresh FLEX learner using separately normalized manager and claim score gradients can improve its own .99-nearest initialization and exceed attained INDEPENDENT-NEAREST service on this finite roster-change host.
Binding MARL structure: multi-agent credit assignment, expressed through shared team-return learning across manager-plan and agent-claim channels during physical roster change.

# RCLE: one Convergence question about score-channel normalization

## 1. Decision and present authority

Choose whether the fully specified candidate below is worth a later bounded B,
and at what claim/comparator ceiling, or hold this particular learning route.
The DM recommends the minimal one-fit performance question in section 4. This is
a proposal for the original Convergence node, not an adopted repair or frozen card.
Portfolio's post-program-vacancies response §5 commissions one original-node
question and complete conformance intake. Root's assignment supplies **zero
implementation and zero numerical allowance**. All future implementation, checks,
learning, evaluation and numerical caps are deferred. This question ends at one
complete original-node answer/intake or an exact blocker; no automatic consultation
ladder or numerical successor follows.

RCLE remains ACTIVE/MEDIUM. No Portfolio lifecycle, priority, registration, fusion,
recast count or capacity change is proposed. A direction-local hold of the named
learning route would not itself change the Portfolio lifecycle. There is no C freeze.
The existing .05 U MEI and absence of a tuned same-information headroom record are
retained. A close attained reference is neither an upper bound nor measured headroom.

## 2. Observation motivating the question, and contrary evidence

B06/master26 is one valid, complete .99-nearest-prior1000 fit. Primary
U(initial/final/reference) is .287371826172/.287479654948/.281722005208.
Delta_ref = U_reference − U_final = **−.00575764973958**;
G_U = U_initial − U_final = **−.000107828776042**. Negative G_U is not an
improvement. Its conditional 95% interval spans zero; this is no stable degradation
or equivalence claim. All eight reference U comparisons lose; four initialization
U cell means improve and the two active continuation paths oppose. The 504/512
initialization score ties do not establish identical actions, trajectories or policies.

The strongest support for trying a specific learning change is the earlier W100/W1
native service signal and the surviving local initialization gains. The strongest
contradiction is the recent aggregate absence of gain, eight reference deficits,
and adverse F/recovery consequences. B06's five positive initial F contrasts include
one +3.2526065174565133e−19 difference with equal displayed means; retain that raw
sign without calling it substantive harm. Its 2012/2048 tau40 outcomes are failure
codes, not observed forty-tick recoveries. Both active reference contrasts are
negative. Nonzero parameter movement establishes exposure, not competent action change.
The B06 reference-sign prediction matched; the positive-learning prediction missed.
The owner prediction was not taken. B04/B05 and B03 keep their own outcome histories.

The A02 frozen-gradient measurements concern saved seed18 states and different
learning conditions. They motivate considering allocation but do not measure B06's
channel norms, cancellation or gradient conflict. Even A02's small aggregate
manager/claim cosine did not identify inter-agent conflict or variance reduction.
No historical gradient census, replay or new diagnostic is needed before asking
whether this specified finite recipe is useful. No current defect is diagnosed.

## 3. Exact candidate, including shared tensors and degenerate cases

Keep the existing collected block of 64 episodes: eight episodes from each of the
eight 6/10 training cells, collected in two 32-episode native batches. All derivatives
below use that same block, same parameter state and same current stopped baselines.
Let A_e = stop(Y_e − b_cell(e)), where Y_e is the unchanged full 64-tick native
return. Let m_e and c_e be the existing episode means of used manager-plan log
densities and used claim log probabilities (`averaged_episode_score`). Their
existing score paths and stopped sampling semantics remain; no extra detach or
pathwise derivative is introduced.

    L_M = −mean_e(A_e m_e)
    L_C = −mean_e(A_e c_e)
    g_M = derivative of L_M with respect to the complete parameter vector
    g_C = derivative of L_C with respect to the same complete parameter vector

Take each derivative over all 26,161 FP64 scalars in the existing ordered parameter
inventory, each actual tensor identity once. A parameter unused by one channel has
zero contribution in that channel. A shared encoder or event-head tensor can receive
both contributions; add them at its same coordinates. Do not partition parameters
into manager-only and claim-only optimizers, duplicate shared tensors, normalize
each layer/agent/cell separately, or update one channel before differentiating the
other. Parameter sharing, physical state ownership and recurrent paths are unchanged.

For a finite vector v, define u(v) as its unit L2 direction, or zero when all its
coordinates are zero. The proposed FP64 realization is scale-safe: let a be the
largest absolute coordinate; when a>0 use (v/a)/sqrt(sum((v/a)^2)); when a=0 use
zero. This specifies normalization without a tunable epsilon or a small-gradient
discard threshold. It is an algorithm definition here, not implemented or tested code.
Reject a nonfinite derivative/vector as a technical failure before mutating parameters
or baselines; do not replace it with a convenient zero.

    d = u(g_M) + u(g_C)
    if d is zero: parameter change = zero
    otherwise: parameter change = −0.02 u(d)

This combines the two unit channel directions with equal weight, then retains the
existing full-vector .02 norm for a nonzero update. **There is no remaining factor
100**, before or after combination. A positive constant multiplying a channel would
cancel in its unit normalization. The existing joint100 control instead normalizes
g_M + 100 g_C once. The candidate therefore changes the finite learning geometry;
it is not an unbiased rewrite of the original weighted objective or a new native reward.

If one channel is zero, the other determines the .02 step. If both are zero, or
their unit directions cancel exactly, parameters do not move. The ordinary baseline
update still follows this zero parameter step using the same block. Near cancellation
that leaves a nonzero represented d still receives a .02 step. That may magnify a
noisy direction and is a substantive weakness to assess, not a conflict-removal
guarantee. No cosine gate, projection, tie-breaking random direction, clipping,
adaptive mixture, channel schedule or retry is hidden in the definition.

After the single combined parameter step, retain b_j ← .95 b_j + .05 mean(Y | cell j).
Start every later fresh fit with the unchanged zero baselines. The candidate uses
two derivative traversals of the same collected graph, not two rollout batches per
channel, two optimizer steps, a second return, or higher-order differentiation.
Gradient vectors and the retained graph live only within that block and are released
after its two derivatives and update. Normalization is not differentiated through.
Actual attempted/completed derivatives, zero/nonzero steps and displacement would be
reported under a later funded card; none is observed here. A zero-only learner could
not establish a positive native learning claim merely by completing a loop.

The .99 nearest/.002 each other prior remains legal and overridable: six candidate
actions, 81 pointer inputs, field76 nearest-distance tie resolved by first index,
zero initial pointer output, additive log495 offset, and the same probability tensor
for sampled actions and their selected log score. No teacher trajectory, privileged
state, deterministic override, probability grid, changed reward or F penalty is added.

Environment event → ownership → information → action → learning → consequence:
public tick24 changes roster, positions and demand; physical survivors retain their
entity-owned FLEX state, departures remove it and newcomers get fresh state/noise;
the same partial local/public observations and plans feed four-tick claims/movement;
joint coverage supplies full64-tick Y and post-event U/F/failure-coded recovery;
only allocation of the two native-return gradient channels changes; changed future
claims could improve or impair actual joint service. This does not add a membership
sensor, change entity/slot identity, reset survivors or shorten the native horizon.

## 4. Minimal useful comparison and the conditional stronger alternative

**DM recommendation:** if this route is worth a later investment, start with one new
unscreened training instance of the changed recipe at the existing final1000 endpoint,
its own initialization, and attained INDEPENDENT-NEAREST. Keep the three eight-cell
8/12 evaluation panels with 256 scenarios per cell. No intermediate checkpoint or
best-of-many selection is proposed. Fresh seed/object identity and every actual cap
would be fixed only in the later funded card; no B06 state, root or partial run is reused.
The scientific ceiling is native service of that complete changed recipe relative
to its initialization and the attained reference, conditional on one fit. It is not
superiority to joint100 or evidence that normalization caused a gain.

Keep Delta_ref and G_U signs as defined above, with equal weight on
ACTIVE_CONTINUATION8→12 and12→8. Retain the .05 absolute U MEI because it represents
two normalized unmet-demand ticks over the forty post-event ticks. Preserve both
paths, all eight U/F/tau levels and contrasts, 40U, failure-coded tau40 counts,
initial/final Y and actual movement. Reference Y remains null. Scenario uncertainty
is conditional on the fit, not training-population uncertainty. Do not treat small
inside-MEI gains as stable superiority, G_U≤0 as learning, or opposed paths/F harm
as unqualified nonharm. The six B06 descriptive reading rows remain the proposed
language limits; this does not alter that completed card or its result.

Initial/final evaluation shares the existing semantic exogenous/action-uniform
addresses, while the deterministic reference shares exogenous addresses without
actor-uniform consumption. Training and evaluation domains remain separate. Nearest
uses the same available information and needs no training; this is an attained
service comparison, not equal compute or a tuned-baseline win. Its old same-information
definition is reused because observation, actions, information and endpoint match.

**Conditional stronger alternative:** if the chosen claim is that the new update
outperforms joint100, add one newly trained, matched joint100 control at the same
endpoint. Use the same fresh initialization and semantic address law, but each fit's
own evolving policy/trajectories/baselines. One common initialization panel can serve
the identical initial policies and is charged once. Historical B06 is context, not
this control. This gives one paired training root, not two independent replications.
Compare U_joint100 − U_changed plus each arm's initialization/reference results and
all F/recovery consequences. It still would not uniquely diagnose gradient conflict,
variance reduction or shared-tensor causality. Do not require this extra fit for the
narrower service-only question merely because a stronger claim could be imagined.

The strongest objection to the minimal proposal is its inability to identify an
update advantage over joint100; a supplied prior and stochastic training could
produce a favorable single instance. Its value is instead whether the changed
complete recipe acquires useful native competence at all. The strongest objection
to either numerical option is that equal unit norms can amplify a noisy weak channel
and a near-cancelled direction, while .99 initialization already leaves little
observed improvement in B06. Holding the named route is a valid outcome. Neither
low headroom nor gradient conflict has been established. Pro should weigh these
alternatives and may decline or specify one conforming revision; it must not fund
an unbounded normalization search or a preliminary diagnostic programme.

## 5. Work, future limits and knowledge used

[EXPOSURE_AND_COST.json](EXPOSURE_AND_COST.json) is documentary arithmetic over the
published loop, not numerical scientific work. The recommended future comparison
has 64,000 training + 6,144 endpoint episodes = 70,144 episodes / 4,489,216 native
ticks; 1,000 combined parameter-update attempts, 2,000 rollout batches and 2,000
channel derivative traversals. It makes 8,847,360 neural agent-claims × six scores.
Seven current-style model allocations include six helpers, not seven fits. The
conditional two-fit comparison has 136,192 episodes / 8,716,288 ticks, 3,000
derivative traversals, 2,000 parameter-update attempts and four evaluation panels;
its common initialization is counted once. There is no candidate trajectory search.

Per-arm work includes startup/admission, constructors, all native collection and
derivatives, parameter/baseline updates, final panels, checkpoint/primary publication
and exit. Two traversals can add graph lifetime, memory and compute. Changed-method
rates and complete supporting work are unknown. B06's complete native335.86s
(learned333.40/reference2.45) and known support86.7963743s are a historical window,
not a forecast or renewed 750-second allowance. No calibration, numerical fixture,
profile, implementation or validation run is released. Future source/check/support
and native caps must be selected separately; unknown work is not presumed free.
Engineering-scope §4: this consultation needs none of the listed machinery.

Scientific reading changes the interpretation as follows. Foundations §§3–6 and
04_EMPIRICAL distinguish shared team credit from learned coordination, finite
optimization from policy expressibility, whole-recipe performance from component
attribution, and evaluation scenarios from independent training roots. Thus the
minimum comparison can answer a recipe question but not a joint100-effect claim.
Current My-lib coverage reports only two synthetic-core fixtures, excluded from
scientific evidence. Inst-sci's actual 190-row catalog search returns GradPS,
HyperMARL and M3W for the bounded gradient terms. Metadata matches alone are not
support. Re-reading HyperMARL's pp.4–7 confirms that its agent/observation-conditioned
factorization and measured interference/variance concern a different decomposition.
The earlier A02 intake supplies the verified baseline-control-variate caveat.
Neither reading validates this channel normalizer or diagnoses B06; it instead
requires preserving the untested-allocation and no-conflict-attribution wording.
The service-design intake's legal overridable-prior reading is reused without an
optimal-.99 claim. [LITERATURE_SCOPE.json](LITERATURE_SCOPE.json) records actual
coverage, pages and limits; no general literature/novelty conclusion is made.

## 6. Requested original-node answer

Return one clear direction-local choice: consider one specifically defined future B
at the narrow service ceiling; choose the fresh joint100 comparison because the
intended claim warrants its added work; or hold this named learning route. If
revising the candidate within scope, specify the complete combination, zero,
cancellation and shared-tensor behavior and its changed meaning. State the strongest
counterargument, why the next observation matters, the independent unit, necessary
comparators, uncertainty ceiling, outcome language and dominant work. No positive
pilot, exhaustive gradient diagnosis, exact upper or stronger evidence class is a
prerequisite. No-useful-candidate is a valid complete answer.

Preserve the protected native law and the zero implementation/numerical boundary.
Give prospective expectations separately from observations. The DM will read the
entire immutable response, check scientific/specification conformance and record
only its conforming direction disposition. Any conflict or access blocker returns
as that exact fact; it is not scientific polarity or permission to send another
question or run a fit. Future investment remains separately unselected.
