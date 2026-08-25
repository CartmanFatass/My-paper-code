# HA-CTSE Knowledge Base

HA-CTSE/process-core exploration uses HMASD and OPT as inspirations without
merging their conceptual roles or inheriting HMASD's discriminator objective.

HMASD is a hierarchical skill-discovery algorithm. It has a team skill `Z`,
individual skills `z_i`, a high-level coordinator, a low-level actor conditioned
on local observation and individual skill, and historical discriminator
machinery. In the new algorithm, these are reference structures, not a target to
preserve.

OPT is an interaction-pattern representation module. It builds sparse and
diverse interaction prototypes with sparsemax, contrastive disagreement, and
aggregation. Its compact output `c_tau` summarizes interaction structure. It is
not automatically a controllable team skill.

HA-CTSE therefore uses:

```text
c_tau = f_OPT(s_tau, joint_obs_tau)
g_tau = f_bridge(c_tau) or g_tau ~ pi_g(g | c_tau)
m_i   ~ pi_term(m | c_tau, g_tau, o_i, z_prev_i, age_i)
z_i   = z_prev_i if m_i = 0 else z_tilde_i
a_i   ~ pi_l(a_i | o_i, z_i)
```

The main inductive bias is that global interaction information can be refreshed
on a shared schedule, while individual executable skills can persist for
different horizons. After `k` and realized skill lifetime `T_i` are separated,
skills should be treated as behavior processes over their active lifetimes, not
only as single-step labels.

Current research direction: process/outcome-centric exploration is primary.
Single-step discriminator rewards are excluded from the standalone core because
they confound the target; they belong only to legacy HMASD baselines or explicit
controls.

The method is meaningful only if experiments show sparse and heterogeneous
editing:

```text
avg_executed_edits < num_agents
avg_switched_agents < num_agents
skill_persistence_cycles_mean > 1
lifetime_heterogeneity > 0
```

The low-level policy realizes `z_i -> behavior process over T_i`. Its reward,
entropy, and diagnostics should be reviewed under the process objective while
preserving the core actor invariant `pi_l(a_i | o_i, z_i)`.

A discrete lifetime set such as `D={1,2,3,5}` high-level intervals is a valid
simplifying hypothesis. It can make process segments easier to batch and reduce
termination noise, but it must be checked for duration-only shortcuts.

Not every old HA-CTSE/HMASD component needs a formal ablation after the
process-centric redesign. Keep ablations only when they answer a current
mechanism question; otherwise downgrade old structures to legacy diagnostics or
retire them.

Do not claim that HA-CTSE universally dominates OPT-MAPPO-K. The allowed claim
is that it is useful for tasks where temporal commitment differs across agents
and direct global conditioning can destabilize role persistence.
