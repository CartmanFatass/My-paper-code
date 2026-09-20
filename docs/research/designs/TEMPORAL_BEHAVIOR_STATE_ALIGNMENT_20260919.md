# Temporal behavior and state-aligned renewal

Owner-assigned independent FSD/UCOPE question, 2026-09-19 PDT.

## Scope and exposure

The owner assigned this session as the independent collaborator, then explicitly allowed an
independent worktree. This is a bounded design and prototype deliverable, not a third K-axis
direction or a takeover of either lead. The FSD and UCOPE sessions retain their notebooks,
scientific acceptance, code and operations. This document is the requested design artifact;
it is not a new standing research record type. No RESEARCH row or fit allowance is added.

Base checkout: `a41dbb31e5806d0b7c3e8958b6e74396406aa5cd`. Source inspection covered
FSD's current notebook and actual low-level actor, and UCOPE's unchanged reactive implementation.
During that inspection the UCOPE notebook had already recorded the B02 reading at
`2ea54c80e3327b8779af3e15b239f123c3b2718e`, then selected scalar-gate B03 at
`cec3ce8ba1978c9edfa018634e1da3f512fbb634`. This advice is exposed to those completed results
and that selected design. It is not a pre-B02 prediction. No live run output or checkpoint is
used by the prototype. Existing B02/B03 inputs, readings and operations are untouched.

## Working explanation

The shared question is whether useful temporal behavior requires alignment of renewals with
the agent's current trajectory. Training-time exploration and deployment-time feedback value
are different estimands: a gate may affect both, and its feedback acts through temporal behavior.
There is no general additive decomposition into independent "timing" and "coherence" effects.

| Construction | Persistent object | State dependence and unresolved differences |
| --- | --- | --- |
| UCOPE G | Recurrent controller; a new Gaussian innovation each tick | Actions are not IID: their means depend on history, observation and previous command. |
| UCOPE F | Actual velocity, for a precommitted 1 or 2 ticks with equal probability | Controls short, state-independent persistence already; not R's learned rate, timing, phase meaning or gradient path. |
| UCOPE R | Actual velocity on KEEP, at most 2 ticks | Gate uses fresh recurrent features and the actual previous command; both timing and the behavior distribution change. |
| FSD D | A skill label for fixed k=10, modulating actor features before the GRU | Low-level feedback and action sampling continue each tick. This is a persistent policy mode, not repeated velocity. |
| FSD CF | Recurrent state and a held central snapshot | Also temporally structured; wider input, representation, rewards and finite learning remain competing explanations. |

In particular, F's remaining-hold field and R's gate-eligibility field have different semantics.
F already makes another random 1/2-step hold baseline redundant. B03's learned global gate is a
reasonable simpler *learning package*; it still changes gate capacity and backbone gradients.
It is the existing UCOPE lead's selected comparison, not a new contribution of this document.

A scalar illustration, without boundaries, feedback or teammate coupling: two independent
zero-mean velocity draws with variance sigma^2 give displacement variance 2 sigma^2; repeating
one draw twice gives 4 sigma^2 with the same per-tick variance. This explains possible coverage
changes without clever timing. It predicts neither UAV return nor an FSD advantage.

## One minimal additional comparison: frozen controller, exchanged calendars

Target: the conditional native-return value of trajectory-aligned renewal for an already learned
R controller, relative to a calendar drawn from the same controller on an independent world.
This is a possible diagnostic, not a new training baseline or a commitment to execute it.

1. Fix both B02 final R checkpoints, never selecting the better score. For each checkpoint fix
   64 fresh, IID world seeds and independent policy random streams before any diagnostic result.
   Form 32 disjoint world pairs by the prespecified list order, not by observed trajectories.
2. Run normal frozen R once per world. Record the entire T-by-5 fresh/hold calendar. Each UAV
   is fresh at reset, and a hold must be followed by a fresh command; T=256.
3. Exchange each pair's entire joint calendar. Keep its original tick order and UAV columns.
   Rerun each recipient world with its own actor and its own innovations. At a fresh tick draw
   from that actor on its current observation/history; otherwise copy its own previous actual
   command. Never transplant donor velocities, hidden states, rewards or observations.
4. Advance the recipient GRU every primitive tick, including holds. The actor sees its own
   previous command and eligibility derived from the transplanted calendar. Reset both normally.
   No weight, normalizer or optimizer update occurs. No likelihood is fabricated for gate
   choices imposed by the intervention.

Generate full velocity-innovation and gate-uniform arrays independently per world, with fixed
(time, UAV, coordinate) slots. Unused innovations stay unused without shifting any future slot.
This preserves the same recipient innovations across both modes. It is a new evaluation RNG
coupling with the same sampling law, not bitwise replay of the old B02 Torch RNG streams.

For pair (i,j), the analysis unit conditional on one checkpoint is

    d_pair = ((J_online[i] - J_exchange[i]) +
              (J_online[j] - J_exchange[j])) / 2.

Report each checkpoint separately and all pair effects. World pairs are independent under IID
worlds/streams; worlds within a pair are coupled by the exchange. They are not new independent
training instances. No training-population confidence, equivalence or superiority claim follows.

The panel exactly preserves the calendar multiset, hence per-UAV update counts, observed hold
lengths, tick positions and within-calendar cross-UAV scheduling structure. It does not match
each recipient's own count, state visitation, velocity magnitudes or action autocorrelation.
The intervention removes adaptation to the recipient trajectory, including the previous sampled
command; a loss cannot uniquely identify the value of the newest environmental observation.
Recipient state becomes affected by its imposed calendar, so "independent" means an exogenous
calendar assignment, not statistical independence of all subsequent states and gate decisions.

Predictions: a positive online-minus-exchange effect supports dependence on trajectory alignment
at these frozen policies. A small effect weakens deployment-time necessity but neither proves
equivalence nor excludes exploration benefits during training. A negative effect makes the
learned online gate suspect for deployment. A loss can include co-adaptation/distribution-shift
cost and cannot prove that no simpler controller could learn equally well. Preserve all signs.

Candidate native budget, if a direction lead later selects this diagnostic: 2 checkpoints x
64 worlds x 2 modes = 256 evaluation episodes = 65,536 team steps, zero fits and zero optimizer
updates. Synthetic engineering tests are additional, not native evidence. Native integration/admission,
checkpoint identities, exact seeds and publication are not selected in this deliverable. No
new fit or native evaluation is executed here. Existing lead/runtime admission remains applicable.

## Likelihood and FSD limits

For each reactive agent-row, the existing likelihood is

    logp = eligible * log q(branch | history, previous_command)
           + fresh * log p_tanh_gaussian(command | history).

KEEP scores only the gate; END scores both gate and fresh velocity; forced fresh scores only
velocity. Recorded branches and previous commands are replayed, not resampled. The existing
primitive-return credit and denominator cannot silently change in a future training comparison.
The calendar intervention has no PPO update; it does not claim that imposed choices were drawn
from the online gate.

If G later uses residual AR(1) noise, with fixed rho, global sigma_theta and pre-tanh u,

    u[t] | H[t] ~ Normal(mu_theta[t] + rho*(u[t-1] - mu_theta[t-1]),
                         (1-rho^2) * diag(sigma_theta^2)).

The first draw after reset uses Normal(mu_theta[0], diag(sigma_theta^2)). PPO needs this
conditional density, the tanh Jacobian and consistent recurrent replay under each policy.
The historical residual must be reconstructed with the corresponding theta; using stored
old-policy residuals in the new-policy density is wrong. Keeping only a marginal Normal
likelihood after correlating samples confounds the learning algorithm with the proposed mechanism.
The prototype does not implement AR noise or change a learner.

For FSD, an analogous exchange would transplant entire *joint skill-label sequences* between
independent worlds of the same checkpoint while keeping the low-level feedback actor live.
Because the current skill clock is fixed, that would ask about state-aligned skill identity,
not learned renewal timing. It is not scheduled here. An actuator result cannot supply FSD
mechanism evidence; the two hosts, policies and scores are not pooled.

## L0: bounded implementation

Owned paths: this document, `tools/analysis/temporal_alignment.py` and
`tests/tools/analysis/test_temporal_alignment.py`. All edits stay in the independent
`codex/temporal-state-alignment` worktree. No edits to the two direction notebooks, shared
learners/runners/environments, source imports used by existing experiments, or RESEARCH.

Deliverable: an importable CPU FP32 prototype of the frozen UCOPE five-agent action loop,
validated calendars, prespecified adjacent-pair exchange and a pair-effect reducer. It exposes
no native-run CLI, training, checkpoint selection or output publisher. Reuse the existing actor
and synthetic adapter in tests only; source prototype depends on NumPy and Torch. It is a
one-off analysis tool, not a framework or an accepted production evaluator.

Checks: self-calendar replay reproduces observations/actions/rewards exactly; current observation
and GRU still advance during holds; forced renewal and own-command copying agree with existing
UCOPE source semantics; paired exchange preserves full calendar multiset; invalid schedules and
nonfinite/malformed inputs fail; random inputs do not depend on gate consumption; pair effects
retain opposite-signed worlds and use the pair as unit; no model parameters or global RNG change.
Use pytest-managed scratch and the configured local_linux scientific interpreter. Obtain one
independent read-only engineering review for the new RNG/replay/evaluation semantics, then accept
or repair findings. Stop after publishing the tested prototype and this design; no native run.

## Verified prototype boundary — 2026-09-19 PDT

The focused suite passed **25 tests in 1.35 s** with the configured local_linux scientific
interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q tests/tools/analysis/test_temporal_alignment.py
```

Coverage includes exact self-calendar replay, original reactive sampler agreement at both
forced branches and log-std clamp boundaries, recipient-owned command/history, recurrent
advancement during holds, calendar preservation, prefix-stable world-specific random tables,
and pair-level signed outcomes. A manufactured switch example has a known pair effect 5/6;
a constant-reward null has effect zero. These are controlled engineering fixtures, not UAV
observations, training fits, or evidence that a learned gate uses state well.

An independent read-only engineering review found one completeness defect: a random table
shorter than the environment episode could be scored as a completed prefix. The prototype now
requires an explicit terminal/truncation witness on the final declared tick, in addition to
rejecting early termination. The regression exercises a three-tick table against a six-tick
environment. The reviewer inspected the repair and reported no remaining material findings,
reusing the focused test evidence; it did not run a native evaluator or assess scientific claims.
The author accepts this as a synthetic prototype. Direction adoption and native execution have
not occurred. No checkpoint was loaded, no native episode was run, and no fit was started.


## Sources

- FSD source and working explanation: [actor modulation](https://github.com/CartmanFatass/My-paper-code/blob/a41dbb31e5806d0b7c3e8958b6e74396406aa5cd/hmasd/networks.py#L1439),
  [notebook](https://github.com/CartmanFatass/My-paper-code/blob/a41dbb31e5806d0b7c3e8958b6e74396406aa5cd/docs/research/candidates/flexible_skill_duration/NOTES.md#L1341),
  [CF construction](https://github.com/CartmanFatass/My-paper-code/blob/a41dbb31e5806d0b7c3e8958b6e74396406aa5cd/scripts/run_fsd_matched_information_baseline_b01.py#L1).
- UCOPE [reactive implementation](https://github.com/CartmanFatass/My-paper-code/blob/21b7c9aeb8587a130402ec1d7c99c8fa9cfbb9cb/experiments/candidates/ucope/reactive_renewal_b01/reactive.py),
  [prospective interpretation](https://github.com/CartmanFatass/My-paper-code/blob/310d7c351c294ec2b1a4657a1b05862983dc1cbd/docs/research/candidates/ucope/NOTES.md#L232),
  [selected B03](https://github.com/CartmanFatass/My-paper-code/blob/cec3ce8ba1978c9edfa018634e1da3f512fbb634/docs/research/candidates/ucope/NOTES.md#L371).
- Korenkevych et al., [Autoregressive Policies for Continuous Control Deep Reinforcement Learning](https://www.ijcai.org/proceedings/2019/0382.pdf),
  section 5 equations 7-10: explicit history-dependent conditional density. This is a formulation
  bridge, not evidence of benefit on either HMASD host.
- Schulman et al., [Proximal Policy Optimization Algorithms](https://arxiv.org/pdf/1707.06347),
  section 3 equations 6-7: new/old policy probability ratio.


## 2026-09-19 PDT — owner continues the temporary question: identification scope

The owner explicitly continues this temporary research question. The earlier prototype stop
was the boundary of that completed task, not a continuing pause. This continuation develops an
exact finite-model argument and checks its arithmetic; it adds no native run or training fit,
and leaves the two direction sessions in charge of their own work. The next useful observation
is whether identical exchange gaps can arise with and without new environmental information.

New accepted context read in the [FSD lead correction](https://github.com/CartmanFatass/My-paper-code/blob/1b1b91400627ca2629181e372eb50170a369690d/docs/research/candidates/flexible_skill_duration/NOTES.md)
at commit `1b1b91400627ca2629181e372eb50170a369690d`: the lead has withdrawn the claim that
the coordinator had demonstrably learned to select skills; recorded choices remain near uniform,
and a confirmed CF input-scale hazard is the next targeted construction issue. Thus the table
above describes the architecture's *available* state dependence, not observed successful use.
A state-blind but persistent skill can still modulate a trained low-level policy. High entropy
alone does not prove exact state independence, and no new FSD result is inferred here.

L0 extension: add `tools/analysis/temporal_alignment_identification.py` and its mirrored test
`tests/tools/analysis/test_temporal_alignment_identification.py`; append the derivation and its
implications to this same requested design artifact. Use exact rational expectations over a
single eligible renewal decision and an analytic two-step Gaussian score counterexample.
No environment, training, checkpoint, action-noise tuning or simulation batch is involved.
The checks validate identities and known finite counterexamples, not an empirical fit/result
entry. Keep the existing frozen replay prototype unchanged. Review the mathematical semantics
and independent arithmetic checks before publishing the continuation.

The hypotheses to discriminate are: (a) the gate benefits from the new private observation;
(b) it only filters its previous command/retained history; (c) those contributions cancel in
an aggregate exchange contrast. Any distinction found in the finite model remains local to
its stated assumptions; no full-horizon MARL decomposition is presumed.


### Exact one-decision result: what an exchange gap contains

Let C be retained information immediately before the new observation: recurrent memory,
previous actual command, phase and clock, as relevant. Let S be the new private observation.
The velocity controller still receives its lawful full information in every comparison;
only the renewal gate's information dependence is varied. At one eligible decision in a
fixed predecision population, write p(C,S) for P(END) and A(C,S) for the frozen-controller
expected return of END minus KEEP. Any future continuation in this one-decision definition
is fixed identically; the return can include later native consequences.

Subtracting the common expected KEEP value, define

    V_online = E[p A]
    V_independent = E[p] E[A]
    V_retained = E[E[p | C] A].

The independent calendar is drawn from another IID episode's gate, with its marginal END
rate preserved. The ideal retained-only gate instead draws with probability E[p | C]; it
preserves each C-conditioned rate while dropping dependence on the recipient S. This is a
mathematical intervention, not an estimated native controller selected for training.

Direct expansion, requiring no independence between C and S, gives

    Delta_total = V_online - V_independent = Cov(p, A)
                = E[Cov(p, A | C)] + Cov(E[p | C], E[A | C])
                = Delta_new + Delta_retained,
    Delta_new = V_online - V_retained,
    Delta_retained = V_retained - V_independent.

Thus global calendar exchange measures total trajectory alignment in this model, not just
new-observation value. This is an exact local identity, not a decomposition of a 256-tick
calendar-exchange experiment: wholesale exchange changes later histories, eligibility and
joint-agent interactions. Summing this expression over logged baseline rows does not identify
the full-episode intervention. An independently observed donor calendar is exogenous to the
recipient initially, but its later state is naturally affected by the imposed choices.

Take C and S independently uniform on {-1,+1}, KEEP value zero, and terminal END value A.
The following expectations are exact fractions; no sampled score or learned fit is involved.

| Example | p(END) | A | END rate | Delta_total | Delta_new | Delta_retained |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Only new observation matters | (1+S)/2 | S | 1/2 | 1/2 | 1/2 | 0 |
| Only previous-command information matters | (1+C)/2 | C | 1/2 | 1/2 | 0 | 1/2 |
| Both contribute | 1/2+(C+S)/4 | C+S | 1/2 | 1/2 | 1/4 | 1/4 |
| Contributions cancel | 1/2+(C+S)/4 | S-C | 1/2 | 0 | 1/4 | -1/4 |

In the second row, C can be an internally generated good/bad previous command and S can be
irrelevant noise: no changing external task signal is needed. This still is a form of
state/history-dependent timing. It specifically refutes equating a positive exchange gap
with useful *new environmental information*, not all forms of adaptive renewal. The first
two rows have identical online return 1/2, independent-calendar return 0 and END rate 1/2.
In the fourth, online and independent returns both equal zero, while retained-only return
is -1/4. A zero net exchange gap therefore need not mean the new observation is useless.

Each gate can be embedded in a two-tick legal commitment episode: forced fresh first,
one eligible KEEP/END choice second, then termination. Donor swapping preserves the entire
calendar distribution. This tiny model removes learned features, recurrent optimization,
state-occupancy feedback after the choice, decentralized teammate coupling and training-time
exploration. It proves a non-identification possibility, not that either mechanism occurs
in a UAV checkpoint. F already supplies a state-independent short hold construction; these
examples introduce no random-hold baseline.

### A likelihood error can create credit for a parameter that cannot affect return

This second example addresses the owner's correlated-noise constraint quantitatively. For
fixed |rho|<1 and unit marginal variances, let

    a0 = mu0 + epsilon0,
    a1 = mu1 + rho*epsilon0 + sqrt(1-rho^2)*epsilon1,
    epsilon0, epsilon1 independent standard Normal.

The terminal reward, delivered after both actions, is a0. Hence J=mu0 and its true gradient
is (1,0). Use the valid zero baseline. With the correct joint/conditional Gaussian likelihood,
E[a0 * grad_mu log p(a0,a1)] = (1,0). With the product of the two independent *marginal*
Normal likelihoods, that expectation is (1,rho): it credits mu1 even though changing mu1
cannot affect the reward. At rho=3/5, the spurious second component is exactly 3/5.

At mu=(0,0), covariance is [[1,rho],[rho,1]], and the correct score is its inverse times
(a0,a1). Taking its product with reward a0 uses only E[a0^2]=1 and E[a0*a1]=rho, proving the
claim by second moments. The wrong marginal score uses the identity matrix instead. At the
start of a PPO update its ratio is one, so clipping cannot repair this already wrong score.
This does not assert the same bias size for UCOPE; it is a concrete counterexample to using
an independent likelihood merely because each correlated action has a Normal marginal.

The check separately differentiates the explicit conditional Normal log densities in Torch,
using two-node Gaussian quadrature per independent innovation. The reward-times-score terms
are degree-two polynomials, so those four integration points recover the Gaussian moments
exactly (up to Float64 arithmetic). They are not a discrete replacement behavior distribution,
Monte Carlo episodes or a training batch. No tanh is needed for this counterexample; an actual
tanh policy must additionally keep the correct transformation convention already stated above.

### Interpretation update and decision

Strengthened: calendar exchange is a narrowly defined deployment substitution test. Its
marginal scheduling match is useful, but a positive gap can reflect previous-command filtering
and a zero gap can hide offsetting information contributions. The earlier caution about
attribution now has an explicit pair of indistinguishable models and a cancellation example.
The frozen replay implementation remains valid for its original operational intervention.

Weakened: spending a native diagnostic solely to decide whether the newest environmental
observation is useful. The proposed global exchange does not identify that question. I retain
it as an optional answer to "can an external calendar replace this whole online gate?", and do
not select the previously costed native panel on the strength of this derivation. This is an
information-value decision within this temporary problem, not an owner permission requirement.

A genuine new-observation comparison would need a justified retained-information control or
an explicit one-decision counterfactual design. Exact matching on a continuous GRU/history is
not available for free: naïve binning, nearest-neighbor donor selection or fitting a control on
the final panel changes the estimand and exposure. No such uncosted native control is adopted.
B03 already asks a practical R-versus-scalar learning question; this temporary work does not
append arms to it. The new-observation/retained-history decomposition is not a third K claim.

For FSD, a skill sampled independently of the state can still produce coherent low-level
behavior. With a frozen mode mean m_z held for two ticks and independent residual noise e_t,
Var(a0+a1)=4 Var(m_z)+2 Var(e), against 2 Var(m_z)+2 Var(e) with independent mode resampling,
under independent zero-mean mode/noise draws. Per-tick variances agree. This bridge concerns
exploration/representation without learned skill selection; it neither diagnoses CF's input
hazard nor replaces FSD's own prospective repair. The FSD source update makes such separation
more relevant while reducing any basis to describe its current standing as learned timing.

Verification: the new exact-identification suite passed 22 tests in 1.14 s under the
configured scientific interpreter. Independent enumeration of world pairs and realized
KEEP/END choices checks the exchange expectations; unequal group masses check conditional
weighting; explicit conditional-density autograd checks the separate Gaussian moment formula.
The earlier 25-check replay suite concerns unchanged code and is not recast as new research.

Independent read-only review found no material issue in the covariance decomposition, four
examples, conditional weighting, Gaussian scores or the stated identification limits. It
recognized the pair/branch enumeration and conditional-density autograd as independent
arithmetic checks and reused the recorded test evidence; it did not reverify FSD history or
run native evaluation. I accept this continuation within its fixed-decision mathematical
scope. No new fit, checkpoint evaluation or native experiment is selected or executed.
