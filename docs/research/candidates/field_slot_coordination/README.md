# Field-Slot Coordination — Inactive Backup Concept

Status: preliminary backup idea only. This directory does not authorize an
implementation, experiment, route change, or claim. The active project remains
the R52 failure review recorded in `docs/project/CURRENT_WORK.md`.

## 1. Motivation

The intended long-term setting combines:

- a variable active team size `N`;
- potentially different decision intervals `k`;
- anonymous or exchangeable team members;
- cooperation that may depend on local topology and a few critical members;
- a requirement that parameter count and coordination depth not grow with N.

R49 showed that permutation-safe, padded, active-only open-roster interfaces
can be implemented without N-dependent parameters. R52 then showed a more
subtle optimization result: fixed-N specialists received positive stochastic
training utility but collapsed under deterministic evaluation, while the
shared cross-N policy learned the task. Therefore a new representation alone
must not be assumed to solve credit or optimization transport.

This candidate treats population fields as a policy representation, not as an
intrinsic reward, task-specific feature, role label, or renamed skill system.

## 2. Core hypothesis

Replace an agent-length autoregressive coordinator with a fixed number of
learned population slots, while preserving a small exact residual for critical
members:

```text
anonymous active roster
-> multi-resolution field slots with slot mass
-> sparse critical-member residual
-> fixed-length slot coordinator
-> parallel focal-agent action decoder
```

The proposed claim is narrower than "mean-field MARL":

> A fixed-size structured population field plus a bounded exact residual can
> preserve the information needed for anonymous allocation and coordination,
> while removing N-dependent coordinator depth.

Variable decision intervals are a later extension, not part of the first test.

## 3. Preliminary architecture

For each active member, form a generic token

```text
xi_i = [local observation, generic capability, current control state,
        elapsed control time]
```

Persistent identity, human-assigned role, task reward, success predicates and
environment-specific intrinsic fields are excluded.

### 3.1 Global multi-slot field

With a fixed slot count `M`, compute soft anonymous membership:

```text
alpha_im = softmax_m(g(xi_i))
F_m      = sum_i alpha_im * phi(xi_i) / (epsilon + sum_i alpha_im)
mass_m   = sum_i alpha_im / N
```

The coordinator also receives `log(1+N)`. Slot mass is required because a
normalized average alone cannot distinguish teams with the same empirical
distribution but different absolute size.

Learned slot queries provide a fixed slot order. Slot collapse, unused slots
and unstable slot semantics remain diagnostics; they must not be repaired by
adding an environment-specific reward.

### 3.2 Local interaction field

For focal member `i`, aggregate only a generic sparse neighborhood:

```text
F_local_i = weighted_pool({xi_j : j in neighbors(i)})
```

Weights may use general relative position, relative motion, communication
reachability or capability compatibility. They may not consume a task success
label or external reward.

The claimed near-linear complexity is valid only when the candidate
neighborhood already comes from a sparse physical/communication graph, spatial
index or bounded sampler. Scoring every ordered pair before selecting Top-L
would still cost `O(N^2)` and is not an acceptable implementation shortcut.

### 3.3 Critical-member exact residual

Retain at most `L` high-impact neighbors per focal member:

```text
C_i = bounded_exact_set({xi_j : j in critical_neighbors(i)}, size <= L)
```

This protects rare relays, low-energy members, cut vertices and conflicting
allocations from disappearing into a population average. Selection must use a
generic sparse candidate source; it is not a learned task oracle.

### 3.4 Fixed-length slot coordinator

Run coordination over the fixed M slots rather than N members:

```text
u_1, ..., u_M = SlotCoordinator(F_1, ..., F_M, mass, log(1+N))
d_i            = sum_m alpha_im * u_m
```

Each focal action decoder then uses:

```text
pi(a_i | local observation, d_i, F_local_i, C_i, recurrent state)
```

This may reduce coordinator depth from `O(N)` to `O(M)`, with M fixed.

## 4. Unresolved probability contract

"Slot-level MAT" is not yet a complete policy definition. One of these
contracts must be chosen before PPO implementation:

1. **Deterministic slot messages.** The coordinator is a deterministic
   representation and only per-agent actions contribute policy likelihood.
   This is simplest but cannot claim MAT-style stochastic joint actions.
2. **Stochastic slot directives.** Directives are explicit latent actions;
   their sampled values, behavior probabilities and credit must be stored and
   replayed exactly alongside agent actions.
3. **Autoregressive deterministic transform.** Slots are processed
   sequentially but no random directive is sampled. This provides ordered
   computation, not an additional policy factor.

The first representation gate should use deterministic slot messages. A later
RL design must not silently mix these contracts.

## 5. Main failure risks

- **Multimodal aliasing:** different spatial or capability modes compress to
  the same field.
- **Rare-member loss:** a single critical member is diluted by the population.
- **Anti-coordination failure:** soft broadcast causes all members to choose
  the same target.
- **Slot collapse:** multiple learned slots represent the same population
  mode.
- **No stable actionability:** slot directives change internally but do not
  change focal action distributions.
- **Hidden quadratic cost:** critical-member selection first constructs a full
  pairwise score matrix.
- **Credit remains unsolved:** a valid field representation does not guarantee
  PPO can learn persistent complementary behavior.

## 6. First possible gate: representation sufficiency only

The first gate should not be a 320K PPO experiment. It should ask one question:

> Does the compressed hybrid representation retain the information needed to
> reproduce a constructive anonymous allocation policy across N?

### Data

Use deterministic constructive-oracle trajectories from a small anonymous toy
task containing all three stressors:

1. two or more simultaneous population modes;
2. one-member-per-target anti-coordination;
3. a rare critical member whose omission makes the assignment infeasible.

The oracle exists only to produce supervised actions and prove realizability.
Its task labels and future information are not policy inputs.

### Arms

- `full_set_reference`: permutation-safe full active-set encoder and decoder;
- `hybrid_field_slot`: fixed M slots plus sparse bounded critical residual.

Pure averaging can be retained as a diagnostic null later; it is not required
for the first minimal gate.

### Evidence

- exact held-out action or roster reconstruction by N;
- rare-critical-member cases;
- anti-coordination collision rate;
- permutation and padding equivalence;
- behavior under N outside the training minibatch composition;
- measured runtime/memory slope as N grows;
- slot usage, slot mass and directive actionability diagnostics.

### Interpretation

- Failure retires this compression before PPO.
- Success supports representation sufficiency only.
- It does not support task performance, cooperation, skill semantics,
  variable-k control, dynamic membership, or UAV transfer.

Numerical thresholds, exact N values, budgets and the toy transition contract
remain intentionally unregistered until the active R52 review is complete.

## 7. Staged research order if reconsidered later

```text
1. oracle behavior-cloning representation gate across N
2. fixed-N external-return access with full-set and field-slot models
3. shared-N learning with a mechanism-matched fixed-N reference
4. externally supplied variable decision intervals with time-aware recurrence
5. episode-internal exogenous join/leave with survivor-hidden continuity
6. only then reconsider macro skills, KEEP/SET or learned timing
```

The N and k questions must not be activated together in the first experiment.

## 8. Later variable-k extension

If the N stages pass, expose actual event duration `Delta t` and use an SMDP
contract:

```text
R_e     = sum_{r=0}^{Delta t-1} gamma^r * reward_{t+r}
delta_e = R_e + gamma^Delta_t * V(s_{e+1}) - V(s_e)
```

The first clock test uses exogenous intervals. It tests clock-conditioned
robustness, not learned duration, hazard quality or skill lifetime semantics.

## 9. Relationship to the active project

- This candidate does not reopen R49, R51 or R52.
- It does not authorize a new intrinsic reward or shaping term.
- It does not use the quarantined R52 shared arm as evidence of variable-N
  success.
- It is not yet the official successor route.
- No code, test, experiment registration or compute task belongs in this
  directory until a later explicit decision activates it.
