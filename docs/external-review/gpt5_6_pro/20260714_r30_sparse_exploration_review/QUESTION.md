# External Review: Rebuilding HMASD-Style Sparse Exploration Under R30

## Research Question

Original HMASD demonstrates sparse-reward exploration without adding a
task-distance potential to the environment. Its dense learning pressure comes
from the algorithm: team/individual discriminator-derived intrinsic rewards,
skill and action entropy, a skill-conditioned discoverer, and autoregressive
individual assignment.

HA-CTSE has now replaced HMASD's synchronized fixed skill interval with the R30
fixed-check `KEEP/SET(skill)` editor. The temporal controller works
mechanically and uses variable lifetime, but the internal sparse-exploration
loop has not been reconstructed. The current one-step transition residual is
active but does not establish persistent skill effects or state exploration.

Review the algorithm and concrete code and choose the single next causal route
for rebuilding that internal drive under a strictly sparse Alice--Bob external
reward.

## Status You Must Preserve

- Keep R30's fixed global check clock, all-agent autoregressive `KEEP/SET`
  decision, high-check PPO buffer, and variable realized lifetimes unless you
  identify a fatal interaction with the proposed intrinsic mechanism.
- The low actor remains `pi_l(a_i | o_i, z_i)`. OPT compact context and team
  context may not bypass the individual-skill bottleneck.
- R29 actor-density-ratio rewards and the forced-deterministic R28 scorer family
  are retired from online reward use.
- Communication/task-specific fields, button/target distances, contact flags,
  and environment potential may be diagnostics but may not define intrinsic
  reward.
- The active Alice--Bob external reward is sparse collection-only. Do not
  restore environment shaping or solve the task through a hand-crafted
  curriculum.
- The historical 64K pair is evidence about wiring and temporal use only. It is
  not evidence that sparse exploration succeeded or failed.
- Do not respond with “train longer,” a coefficient sweep, or several reward
  families to run in parallel.

## Proposed R31 Causal Boundary

The proposed next boundary is a fixed-window, task-generic process-effect
route rather than increasing the current one-step classifier coefficient:

```text
same on-policy context and teammate execution
+ counterfactual/forced individual z_i
+ policy-matched stochastic primitive execution
+ fixed observation window W = k0
-> persistent controllable effect of z_i beyond context/prior nulls
```

First, the target must pass reward-off causal intervention. Only after that
gate may a small detached, clipped, low-GAE-only intrinsic reward be compared
with a mechanism-matched inactive/sham control in the sparse environment.

This proposal intentionally leaves the precise effect representation and
variational objective for your review. Candidate information sources include
equal-length local trajectories and stop-gradient OPT compact interaction
changes, but OPT is descriptive context and must not become an executable team
skill or leak task labels.

## Required Decision

Return exactly one top-level verdict:

```text
ACCEPT R31
MODIFY R31
RETIRE R31
```

- `ACCEPT R31`: specify the single final reward-off target and its later
  reward-on form.
- `MODIFY R31`: identify one causal defect and provide one corrected route.
- `RETIRE R31`: state the reusable negative constraint and choose one different
  upstream causal edge. Do not replace it with a menu.

## Required Technical Review

### 1. What HMASD's intrinsic loop actually contributes

State which parts of the original team/individual discriminator, discoverer,
entropy, and autoregressive assignment are necessary for sparse exploration,
which can survive asynchronous skill lifetimes, and which cannot be copied
unchanged. Distinguish skill identifiability, behavioral state coverage,
cooperative composition, and delayed task credit.

### 2. Diagnose the current transition intrinsic

Review `TransitionSkillDiscriminator`,
`IntrinsicRewardComposer.transition_rewards`, and
`StandaloneProcessAgent._r30_transition_skill_update`. Decide whether the
current one-step residual is a valid component, should become diagnostic-only,
or must be replaced. Address the fact that it can reward easily classified but
task-irrelevant movement without rewarding new-state visitation.

### 3. Define one process-effect target

Give final equations for exactly one target. Specify:

- input trajectory/effect variables and the fixed horizon;
- conditioning variables and prior/context/shuffle nulls;
- whether the target is individual, team-conditioned, or joint;
- how it proves persistence and controllability rather than label recovery;
- how it remains support-native under stochastic execution;
- where gradients stop and which network each loss updates;
- whether and how OPT compact `c` is used without representation drift or
  skill-bottleneck bypass.

If generic episodic novelty/RND is superior to the proposed controllable-effect
route, you may select it only by retiring R31 and specifying one exact
replacement. Explain how it avoids stochastic-noise attraction and how it
supports cooperative rather than independent wandering.

### 4. Sparse-reward integration

If the reward-off gate passes, specify the single later intrinsic reward:

```text
r_low_i = r_task_sparse + beta * r_intrinsic_i
r_high  = discounted r_task_sparse over each fixed check block
```

Correct this split if necessary. State endpoint versus per-step placement,
credit horizon, detach boundaries, normalization/clipping, warmup or gating,
and why variable lifetimes do not earn more reward merely by surviving longer.
No task-specific shaping is allowed.

### 5. Exact code change map

Name the minimal changes by repository file and class/function. Cover data
collection, fixed-window ownership across PPO updates, recurrent-state capture,
null construction, discriminator/effect optimizer, low reward injection,
high-return isolation, metrics, and checkpoint compatibility. Identify current
code that becomes diagnostic-only or is removed.

### 6. Smallest evidence-bearing experiment

Specify one reward-off causal gate and, only conditionally, one small reward-on
matched comparison. Give no more than four decision metrics, explicit
PASS/FAIL/UNDERPOWERED branches, and the one action authorized by each branch.
The comparator must isolate the intrinsic mechanism; shared-`k` versus R30 is
not a substitute for intrinsic-on versus inactive/sham.

## Required Output Format

1. **Verdict**
2. **Causal diagnosis of the 64K result**
3. **Corrected intrinsic-exploration objective**
4. **Reward, gradient, window, and null contract**
5. **Exact code change map**
6. **Smallest reward-off gate and conditional reward-on comparison**
7. **Claims allowed and prohibited**

Do not restate the full history, propose a sweep, reintroduce environment
shaping, or recommend simultaneous semantic/novelty/team reward families.
