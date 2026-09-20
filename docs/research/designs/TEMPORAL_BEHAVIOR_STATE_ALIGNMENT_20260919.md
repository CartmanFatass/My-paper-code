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
