# DISH A1 current-host baseline and upper-reference inventory

- Direction: `degraded_incumbent_shadow_handover`
- Portfolio lifecycle: unchanged `ACTIVE / MEDIUM`
- Host inspected: `RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3`
- Inspection time: `2026-09-04T07:05:24-07:00`
- Activity: read-only repository and Git-tree inspection; no test, model, native process, resource
  admission, result root, or scientific run
- Guidance applied: A1 only, by Root instruction; no MEI, fusion, PARK, lifecycle, or B authority

## 1. Question

Does the current repository already contain both:

1. an accepted, result-bearing, tuned generic baseline that uses no more information than the
   deployed DISH controller on the current host; and
2. an accepted upper reference against which its raw finite-host gap can be read?

Declarations, TEST fixtures, engineering checks, unlaunched cards, and technically incomplete
attempts do not count as result-bearing assets.

## 2. Direct inventory

| Candidate asset | Direct fact | Disposition for A1 |
| --- | --- | --- |
| R06 five-arm definition | `DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md` is `stage=definition_only`; it declares STRUCTURED, FLEX, NEVER, IMMEDIATE, and HYSTERESIS, while `DIRECTION.md` records that no scientific result exists. | Comparator definitions exist, but no tuned generic baseline result exists. |
| Registered recovery witness | `DISH_RBHR_R05_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md` says the script is a feasible recovery witness, **not an optimizer or ceiling**. It also uses current evaluator ground truth and deterministic mean physics. | Useful common carrier/reference component, but neither a same-information tuned baseline nor an upper bound. |
| FLEX and simple-rule arms | They are learner-dependent declared arms of the closed R05/R06 programme. No accepted current-host checkpoints or complete evaluation results exist. | Cannot be relabelled as a baseline result. |
| B01 `TRANSFER_COPY` | The frozen B01 names COPY as its strongest live same-information source comparator, but B01 remains unconsumed and its isolated conformance chain was quarantined before launch. | A comparator definition at a learned first trigger, not a current-host tuned-baseline asset. |
| R02 certificates and TEST forks | Direction records state that R02 had no result activity and that TEST transaction/oracle evidence supplies no COPY/SHADOW polarity. | Historical definition/conformance evidence only. |
| Shared baseline/result locations | Neither `docs/research/baselines/` nor `experiments/baselines/` exists at the inspected Git tree; no tracked DISH result root exists under `temp/directions/`. | No shared current-host baseline set or upper-reference result is present. |

## 3. Inventory conclusion

**Absent.** The current host has useful definitions and a no-learner recovery script, but it has
neither an accepted same-information tuned generic baseline result nor an accepted upper
reference. This is a missing A1 measurement, not a negative scientific result and not permission
to resume B01.

Historical declarations are preserved as provenance. No file is rewritten, and the quarantined
C01/C02 implementation is neither reused nor repaired.

## 4. Decisions this intake produces

### Decision 1 — A1 object disposition (object tier)

Options:

- **(a)** freeze a separate, minimal, no-learner A/RECON object that tunes a generic
  same-information binary transfer rule on calibration rows and measures its raw gap to a
  per-row finite-family upper reference on held-out current-host rows;
- **(b)** count the definition-only R06 arms, evaluator-ground-truth witness, TEST forks, or
  unlaunched B01 comparator as if they were accepted baseline/upper results; or
- **(c)** resume B01, change its frozen causal cut, apply an unapproved MEI, fuse DISH, or mutate
  lifecycle state.

Recommendation: **(a)**. It fills exactly the observed asset gap without learner activity or
mechanism testing. Option (b) confuses definitions and engineering conformance with empirical
assets. Option (c) exceeds A1 and crosses Direction/Portfolio authority.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. The frozen object is
`DISH-SAME-INFORMATION-GENERIC-HEADROOM-A01`; this decision authorizes its card only. It does not
authorize implementation, project-cost execution, resource admission, or a result invocation.

## 5. Boundary

The inventory produces no direction- or Portfolio-tier decision. DISH remains `ACTIVE / MEDIUM`;
B01 remains frozen and unconsumed. The next permissible step is the separately admitted
A/RECON object in the accompanying science card.
