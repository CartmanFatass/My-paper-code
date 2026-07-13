# HMASD / HA-CTSE Algorithm Consultation: R29 Action Information

You are the algorithm-innovation and scientific-review partner for an active
cooperative MARL research project. Begin with `RESEARCH_BACKGROUND.md`, then
read the complete attached ZIP before
answering. Focus on algorithmic substance and the next discriminating
experiment. Do not propose additional workflow, audit, unit-test, packaging, or
review machinery.

## Research objective

HA-CTSE separates a global information/check clock from asynchronous
per-agent skill lifetimes. The immediate problem is to reconstruct an
HMASD-like intrinsic drive that makes individual skills differentiated and
useful while keeping the low-level actor invariant
`pi_l(a_i | o_i, z_i)`.

The active causal edge is:

```text
natural on-policy state visitation
-> support-compatible individual differentiation signal
-> useful low-level policy change
```

## Evidence that constrains the answer

1. R26 found weak/negative natural observational process differentiation.
2. R27-G2 proved that persistently forcing `z_i` causes distinct actions and
   local trajectory effects. This establishes conditional capacity, not
   natural use or reward usefulness.
3. R28's forced-deterministic process scorer failed transport to stochastic
   on-policy trajectories: deterministic OOD `0.068359`, stochastic OOD
   `0.823242`. That scorer family is retired and must not be widened or refit.
4. R29-G0 evaluates, on natural on-policy observations and stored pre-step
   recurrent states, the executed/source-skill action density relative to the
   uniform mixture of all four counterfactual skill policies:

   ```text
   r_AI(s,h,z,a) = log pi(a | s,h,z)
                   - log[(1/K) sum_z' pi(a | s,h,z')]
   ```

   The same squashed action is evaluated under every candidate, so the tanh
   Jacobian cancels. All three mature checkpoints passed: active means
   `0.017050`, `0.017990`, `0.019208` nats; every skill clears `0.005`; the
   inactive-FiLM control is numerical zero; cyclic-label sham separation is
   positive.
5. The lean R29-G1 implementation recomputes the four counterfactual policies
   from collection-time observations and pre-step hidden states, verifies the
   actual-skill likelihood against PPO's stored likelihood, detaches the score,
   clips `0.05 * r_AI` to `[-0.05, 0.05]`, and adds it only to low-level rollout
   rewards before GAE. It does not change high-level returns, collector
   semantics, environment dynamics, team intent, or skill lifetime.

## Questions

1. Is this uniform-prior same-action density ratio a sound intrinsic objective
   for the current recurrent on-policy setting? Derive what it optimizes and
   identify any mismatch caused by non-uniform learned skill usage,
   skill-dependent state visitation, policy-dependent rewards, or detachment.
2. Does the objective risk producing only instantaneous action separation,
   variance/mean pathologies, or task-irrelevant diversity instead of persistent
   skill effects? Identify the most likely failure mode from the supplied
   evidence and implementation.
3. Recommend **one** concrete version for the next run: accept R29 unchanged or
   give the smallest mathematically justified modification. Specify the exact
   reward formula, prior/marginal, temporal aggregation, detach boundaries, and
   where it enters PPO/GAE.
4. Design the smallest mechanism-matched `probe_only` versus `real_reward`
   experiment that can decide whether this signal changes learning. State the
   minimum exposure, seed strategy, primary metrics, falsification thresholds,
   and interpretation. Avoid a separate engineering-smoke stage.
5. If R29 is fundamentally too myopic, propose exactly one better next
   algorithmic target grounded in the existing R26/R27/R28 evidence. It must be
   support-native and task-generic, and it must not simply rename DADS or revive
   the retired forced scorer.

## Hard constraints

- Do not use communication-specific fields or environment reward as the
  intrinsic target.
- Do not add a team reward, `q_d/q_D`, q_A, kappa/hazard, DADS, or a new
  classifier family while this individual-differentiation edge is open.
- Keep `pi_l(a_i | o_i, z_i)`; do not feed team code or compact context into the
  low-level actor.
- Preserve asynchronous lifetimes and current collector/PPO semantics.
- Prefer one decisive change and one decisive experiment over a menu or sweep.

## Required answer structure

1. **Verdict:** ACCEPT / MODIFY / REJECT R29, with the decisive reason.
2. **Objective derivation and failure analysis.**
3. **Exact recommended algorithm**, including equations and implementation
   semantics.
4. **One next experiment**, with comparator, exposure, metrics, thresholds, and
   PASS/FAIL interpretation.
5. **What claim the result would and would not support.**
