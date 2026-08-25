# Open-Pro question: UAV dynamic service roster source contract

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
repair_owner=project_manager
review_type=open_divergent_then_one_scheduled_action
```

## Authority and evidence

Use only the evidence listed in
`docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/01_SHARED_SOURCE_MANIFEST.md`
from the assigned stage commit. In particular, apply
`docs/project/ALGORITHM_PRINCIPLES.md` and
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md`.

You own the scientific answer to this exact question. The Project Manager owns
workflow, source-code realization, proof-sized tests, formal evidence contracts
and result acceptance. Your response is scientific input; it does not authorize
implementation or compute.

## Starting facts and user goal

The user wants multiple Scenario-7-like UAV tests for:

1. a localized temporary communication-demand surge requiring rapid coverage;
2. charging rotation that changes the number of service-capable UAVs; and
3. robustness to a small number of temporary detachments or failures.

Current S7-S1 fixes eight UAVs, thirty users, a 500-step episode and constant
per-user QoS demand. S7-S2/S3 enable batteries and charging; S7-S4 enables
temporary failures. The environment and adapter retain every physical UAV in a
fixed `possible_agents` tensor and expose charging/failure as state masks.

The previous synthetic result accepted `PREFIX_NORMALIZED_OPEN_ROSTER_G8` as a
usable runtime-variable-roster test version in its registered family. It is not
UAV evidence and it has not defeated a correctly information-matched
fixed-agent availability-mask reduction in Scenario 7.

## Central scientific question

What minimal causal benchmark ladder can determine whether a dynamic
service-roster algorithm is usable for these UAV disturbances, while keeping
the physical fleet fixed and resisting the simpler explanation that ordinary
fixed-agent recurrent MARL plus correct availability masks is sufficient?

## Required response

### 1. Competing benchmark framings

Give two to four genuinely distinct causal framings for the requested UAV
problem. For each, state what would count as service LEAVE/REJOIN rather than
mere temporary action masking, what algorithmic capability it probes, its
strongest simpler reduction, and its principal confound. Reject decorative
membership definitions.

### 2. Exact minimal source ladder

Freeze a minimal ordered ladder containing isolated burst-only,
charge-rotation-only and temporary-loss-only sources before any composed
source. You may reject or merge a source only with a scientific reason. Select
exactly one smallest first source for implementation after reconciliation.

For each retained source specify only the causal fields needed to make the
estimand unique:

- disturbance onset, duration, magnitude/support and dependencies;
- service-active membership predicate and temporary versus terminal lifecycle;
- physical state evolution while out of service and recurrent-state
  reset/freeze/restore behavior;
- actor and critic observability, including onset information and prohibited
  future schedule, failure, queue, target or outcome leakage; and
- train versus held-out shift that tests the intended capability.

For the demand burst, make temporary coverage load-bearing without directly
supplying the desired UAV assignment. For charging, preserve physical energy,
return and charger-capacity constraints. For temporary loss, preserve
anonymous membership and distinguish detachment, recoverable failure and
terminal loss if those distinctions change the claim.

### 3. Estimands and matched reductions

Define the smallest primary estimand set. It should cover, where scientifically
needed, shock-period QoS shortfall, recovery latency or recovery-area loss,
ordinary-service retention, energy safety/depletion and post-rejoin continuity.
Do not add metrics that cannot change a conclusion.

Specify the information-, parameter/exposure- and action-matched baselines. At
minimum address:

- a fixed-agent recurrent controller with correct availability masks;
- the accepted prefix-normalized open-roster treatment; and
- a constructive feasibility/oracle check that is not itself a learned
  comparator.

State what evidence would separate dynamic lifecycle ownership from masking,
and what result would instead support the ordinary fixed-agent reduction.

### 4. Access, gates and mutually exclusive outcomes

Define source feasibility/access before algorithm comparison. Then give a
first-match, mutually exclusive result system for the first source and a rule
for promotion to the next isolated source or composition. Include invalid,
non-identifiable, no-access, underpowered, usable-but-no-dynamic-advantage,
dynamic-roster-supported and mixed/anomalous outcomes as needed.

Every branch must state the smallest supported and refuted claim. A failed
source may not be rescued by threshold, budget, seed, reward, observation or
name changes.

### 5. Protected versus implementation-only choices

Return a compact table of unresolved choices. Mark a choice
`scientific_value` only when changing it can change the task distribution,
information set, external reward/utility, estimand, support/admission
predicate, confidence statement, result branch or held-out claim. Otherwise
mark it `implementation_only` and bound the PM freedom.

Do not demand exact file schemas, telemetry formatting, compatibility readers,
class layouts or seed integers unless their values alter the scientific
object. Conversely, do give an exact formula or distribution when ambiguity
would create two different scientific tasks.

### 6. One scheduled evidence action

Return exactly one bounded first evidence action with:

- source name and causal purpose;
- protected source and information contract;
- arms/comparators and primary estimands;
- access and first-match semantics;
- held-out claim boundary;
- minimum completion evidence; and
- explicit excluded conclusions.

This action is a recommendation for PM reconciliation. It consumes zero
conclusion-bearing iterations until a valid formal result exists.

### 7. Concise Chinese user brief

Explain the selected first source, why the other disturbances remain in the
ladder, how physical fleet differs from service-active roster, what ordinary
reduction must be defeated, and what the first iteration can and cannot prove.

## Frozen exclusions

- Do not relabel the synthetic G8--G16 evidence as UAV evidence.
- Do not assume that charging/failure masks alone prove dynamic membership.
- Do not insert demand targets, failures, future membership, desired coverage
  assignments, success or external reward into environment-agnostic intrinsic
  reward.
- Do not change Scenario-7 physics or safety reward merely to manufacture an
  algorithm advantage.
- Do not require backward compatibility or a broad production test suite.
- Do not authorize implementation, nonformal/formal compute, Git or a
  successor. The Project Manager acts only after exact raw reconciliation.
