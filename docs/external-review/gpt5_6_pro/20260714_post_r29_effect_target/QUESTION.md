# Post-R29 Algorithm Question: One Realized-Effect Target

You recommended retiring R29-T10 and the entire detached same-action
actor-density-ratio family as online intrinsic reward. We accept that decision.
R29 remains diagnostic-only and its online `real_reward` path is now fail-closed.

The accepted evidence chain is:

```text
R27: persistent forced z changes deterministic action trajectories and a local effect
R28: policy-matched stochastic execution breaks the forced deterministic support envelope
R29-G0: same-state on-policy actor differentiation exists
R29-T10: rewarding that actor-local differentiation weakens natural process evidence
         and violates task safety
```

The nearest unresolved causal edge is:

```text
natural on-policy prefix
-> persistent z intervention under policy-matched stochastic execution
-> task-generic realized environment-effect separation
```

Design **exactly one** replacement target for this edge. The answer must provide:

1. the mathematical target and the variables that are observed, predicted, or
   intervened on;
2. the explicit causal link from skill-conditioned action to realized
   environmental consequence;
3. one smallest reward-off diagnostic and one mechanism-matched null/comparator;
4. a falsification threshold or qualitative stop condition that would retire
   the target before reward injection;
5. how the target remains on-policy correct for a recurrent policy with
   variable skill lifetimes; and
6. why it is not merely another actor-density ratio, semantic label classifier,
   duration/agent/context shortcut, or forced-domain support transfer.

Hard constraints:

- no environment reward or communication-specific field may define the target;
- the low actor remains `pi_l(a_i | o_i, z_i)`;
- no coefficient, prior, terminal-window, normalization, or clipping sweep;
- do not revive the retired `q_d/q_D`, process-posterior, future-outcome,
  topology-role, R28 scorer, or R29 reward families under new names;
- do not propose team intent, cooperation reward, duration selection, or HMASD
  parity before this individual realized-effect edge is resolved;
- do not propose a large or multi-seed reward experiment. The next action must
  be the smallest evidence-bearing diagnostic.

If this edge is already fully answered by R27 despite the deterministic versus
stochastic execution difference, state that precisely and choose the single
nearest untested causal edge instead. Do not return a menu of methods.
