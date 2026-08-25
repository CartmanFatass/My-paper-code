# Controller Synthesis — Stage C Skill-Bottleneck Portfolio

## 1. Evidence boundary and corrections

The two blind reviewers agree on the central result: Stage B proves that the
dynamic-roster carrier and anonymous recurrent control problem are learnable,
while Stage C proves that the current F0/F1 hierarchy does not produce naturally
executable skills. F1 changes the roster distribution and produces small forced
effects, so neither a dead selector nor total skill-token inertness is supported.
The result does not identify whether the missing cause is semantic pressure,
the low execution interface, high-level credit, or the usefulness of hierarchy
on this substrate.

Three reviewer claims require correction before convergence:

1. The positive forced `rho` contradicts the strong claim that the low policy
   simply ignores `z`. The defensible claim is that its `z` dependence is too
   weak or too context-dependent to form naturally useful semantics.
2. Original HMASD is a positive fixed-`N` source anchor, not an ablation proving
   that `q_d/q_D` alone caused the Alice--Bob success. A dynamic reformulation
   must therefore be compared causally rather than restored by assumption.
3. A membership change of another agent must not terminate a survivor's skill
   segment. Segment ownership follows the focal skill lifecycle and the
   registered leave/rejoin semantics, while survivor hidden state remains
   continuous.

The controller also rejects a direct promotion of continuous skill embeddings.
Replacing categorical `KEEP/SET` with an end-to-end continuous vector would
remove the current probability and lifetime contract, may collapse into a flat
network, and provides no demonstrated semantic pressure. It remains a recorded
idea, not a live implementation candidate.

## 2. Agreement and disagreement between the blind reviews

Both reviewers retain two high-level explanations:

- an environment-agnostic skill-semantic objective is absent or incompatible
  with mixed-age, variable-membership segments;
- the direct recurrent active-set policy is a strong null explanation, so the
  hierarchy must demonstrate transfer or long-horizon commitment value rather
  than merely solve this toy.

They also agree that effect maximization, task-shaped intrinsic reward, role
labels, scheduler-only changes and module stacking are excluded.

Their main disagreement is causal ordering. Gemini promotes a dynamic
`q_d/q_D` replacement and a continuous embedding route. Open Pro keeps
semantic pressure, execution interface and high-level credit as separate
explanations. The controller adopts the latter ordering: high-level credit is
not identifiable until reusable low-level semantics exist, and a continuous
embedding is not yet a coherent replacement for the discrete lifetime policy.

## 3. Controller portfolio

### C1 — Segment-owned environment-agnostic skill semantics

**Causal claim.** Stage C lacks a pressure that makes a discrete `z_i` denote a
reusable behavior process across anonymous agents, skill ages and roster
changes.

**Retain.** Schema-3 active-set runtime, discrete skills, decentralized low
execution, survivor recurrent continuity, event ledger and categorical
lifetime policy.

**Delete/replace.** Replace the absence of a semantic objective and the fixed-
cycle interpretation of original HMASD discriminators with an active-only,
focal-segment objective. `q_d` may be reformulated around local transition or
trajectory fragments. `q_D` is retained only if a roster-invariant team
semantic variable is explicitly justified; it is not restored as a decorative
team latent.

**Boundary.** No task state, roles, progress, contacts, success predicates or
external reward enter the intrinsic signal. Age, membership and duration may
be used only for sampling, conditioning audits or nuisance balancing, not as
shortcuts that make the label trivially predictable.

**Prediction.** With the same external task credit, skills become causally
distinguishable and their behavior signatures generalize across held-out agent,
age and active-`N` strata.

**Strongest objection.** Mutual-information pressure can create arbitrary
diversity that remains unrelated to cooperation, while a flat recurrent policy
already learns the task.

### C2 — Minimal event-context execution interface

**Causal claim.** A reusable skill exists only relative to its local temporal
execution context; strict `pi_low(a_i | o_i, z_i)` aliases newly started,
long-lived, interrupted and resumed execution.

**Retain.** Discrete `z`, categorical lifetime policy, decentralized execution,
semantic objective boundary and all active-set masks.

**Delete/replace.** Replace only the low execution interface with
`pi_low(a_i | o_i, z_i, c_i^event)`, where `c_i^event` is the minimum public,
task-agnostic focal event state already owned by the runtime. It cannot contain
identity, roster slot, future membership, task phase or a second learned team
controller.

**Prediction.** Skill effects already present in Stage C become stable across
age and membership-event strata without requiring a new selector or task
shaping.

**Strongest objection.** The context is merely extra capacity; a matched flat
policy or a larger `pi_low(a|o,z)` should obtain the same benefit.

### C3 — Hierarchy-null active-set control

**Causal claim.** The current substrate does not require a skill hierarchy, and
the fixed skill bottleneck is an unnecessary source of optimization error.

**Retain.** Schema-3 event runtime, anonymous active-set representation,
survivor continuity and physical-time PPO.

**Delete/replace.** Remove high assignment, macro GAE and skill conditioning;
use the Stage B direct recurrent controller as the ordinary-MARL reference.

**Prediction.** It retains performance under unseen roster schedules and
lifetime variation without an explicit macro abstraction.

**Strongest objection.** A short toy cannot expose reusable macro-commitment,
skill transfer or sample-efficiency benefits required by the UAV target.

### Conditional branch — SMDP high-level credit

The H2-B credit explanation remains dormant rather than retired. It becomes a
live implementation candidate only if existing or newly learned skills show
stable cross-context behavior while natural assignment still fails. Its
replacement must use event/physical-time returns with `gamma^Delta`, stored
behavior likelihoods and explicit segment ownership. It cannot reuse effect
scores, role labels, external reward disguised as intrinsic reward, or the
retired R31--R33 estimators.

## 4. Next serialized evidence source

The next evidence should be a **diagnostic-only existing-checkpoint skill
semantics audit**, not another training gate. Reuse the Stage C checkpoints,
forced branches and natural ledger. Measure only three linked quantities:

1. causal action-likelihood and trajectory dependence on `z` under the same
   snapshot;
2. cross-agent, cross-age and cross-active-`N` stability of each skill signature;
3. overlap between stable forced signatures and naturally visited segments.

Use environment-agnostic action/process features and held-out strata. Task
reward, task phase, role names and success fields remain absent. R29/R31-style
statistics are diagnostic instruments only and do not become a reward or
gradient.

Outcome updates are portfolio-wide:

- **No material `z` dependence:** C1 gains weight; the conditional credit branch
  is closed; C2 loses weight unless the failure is specifically age/event
  conditioned; C3 gains weight.
- **Dependence exists but changes with age or membership events:** C2 gains
  weight; C1 remains possible; credit remains premature.
- **Stable cross-context skills exist but natural selection fails:** activate
  the SMDP credit branch and downweight C1; C2 survives only if instability is
  localized to event transitions.
- **Stable skills exist and add no transfer or commitment advantage over the
  Stage B controller:** C3 becomes the leading explanation and the hierarchical
  portfolio approaches its stop condition.

This audit must end with reweighted hypotheses, not a new numbered algorithm.
Only its result can justify the smallest one-variable implementation comparison.

## 5. Probability, clock and checkpoint invariants

Any later implementation must preserve distinct high/event and low/physical
policy factors, stored behavior likelihoods, active-only masks, focal segment
ownership, survivor recurrent continuity, physical duration in return discount,
and complete checkpoint state for skills, event clocks and recurrent state.
Intrinsic gradients may update the semantic low path but cannot leak task
labels or silently train the lifetime selector. High assignment receives task
credit only through its registered SMDP return.

## 6. Stop and integration boundaries

No candidate is integrated from a mechanism-only pass. A hierarchical route
requires reproducible skill semantics plus an advantage over a matched direct
active-set controller on unseen membership/lifetime conditions or genuine
long-horizon commitments. The portfolio stops if C1 and C2 cannot establish
stable executable skills and the direct controller covers the final capability
without a material scaling, transfer or commitment deficit.

This synthesis authorizes only the convergent review. It does not authorize
implementation, training, Stage C rescue or a unique successor.
