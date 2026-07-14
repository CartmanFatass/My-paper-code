# GPT-5.6 Pro Fixed-Clock KEEP/SET Disposition

- Source: GPT-5.6 Pro / ChatGPT web, returned manually by the user.
- Received: 2026-07-14.
- Related claim: how to remove the discrete-lifetime action-space and sampling
  bias while retaining asynchronous skills and HMASD-style differentiation.
- Raw evidence: `RESPONSE_RAW.md` in this directory.

## Decision

**ACCEPT WITH MODIFICATIONS.** Retire discrete duration selection from the
active HA-CTSE core and replace it with fixed-clock, all-agent autoregressive
`KEEP/SET(skill)` editing.

Accepted:

- keep one global check clock `k0`; actual per-agent lifetime is the run length
  of consecutive `KEEP` decisions;
- include every agent in every high-level edit sequence, with later agents
  conditioned on the already-applied working roster;
- mask `SET(current_skill)`, so each active agent has exactly `K` effective
  edit choices rather than `K*D` skill-duration combinations;
- train the high level on fixed check blocks rather than completed variable
  segments, using `Gamma = gamma**k0` and check-sequence GAE;
- remove the duration head, duration entropy floor, duration candidates, and
  duration-dependent semantic targets from the active core;
- initialize the keep bias from the retired duration distribution rather than
  sweeping it. For the current `{1,2,3,4}`-block source this gives
  `p_keep=0.6`;
- keep the low-level bottleneck `pi_l(a_i | o_i, z_i)` and reserve a fixed,
  duration-blind `W=k0` effect window for the later semantic target.

Modified/qualified:

- this is **MAT-style autoregressive factorization**, not a claim that HA-CTSE
  inherits MAT's monotonic-improvement theorem. The SMDP clock, shared network,
  PPO clipping, partial observability, and HA-CTSE critic differ;
- pruning changes each agent's effective branch count from `K*D` to `K`; the
  realizable joint edit set is still `K**N`. Autoregressive generation makes
  sampling and conditional modeling linear in agent count but does not erase
  the combinatorial set of possible joint rosters;
- conditional switch-skill entropy must not create a gradient incentive to
  switch. Its switch-probability weight and shared feature input are detached
  for this regularizer so only the switch-skill branch receives the entropy
  gradient; no entropy bonus is applied to `KEEP/SWITCH` itself;
- the first causal implementation uses no explicit switch/edit penalty, no
  lifetime bonus, and no forced maximum age. Otherwise long lifetimes would be
  hard-coded rather than learned from task advantage;
- the semantic-effect objective is not added in the same change. R30 only
  preserves its clean fixed-window interface; the post-R29 realized-effect
  target remains a separate downstream causal edge.

Rejected/deferred:

- enlarging or retuning a discrete duration set;
- duration entropy floors, `+beta*T` rewards, or default switch penalties;
- claiming full MAT equivalence from token-wise PPO with a shared block
  advantage;
- restoring the failed actor-density-ratio family or old `q_d/q_D` rewards as
  the semantic term.

The accepted implementation contract is
`docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`.
