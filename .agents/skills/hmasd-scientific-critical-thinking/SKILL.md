---
name: hmasd-scientific-critical-thinking
description: Use when an HMASD EM explicitly selects scientific-critical-thinking to bound one frozen scientific claim against hash-bound evidence, alternatives, validity threats, and decisive missing observations.
---

# HMASD Scientific Critical Thinking

Produce one bounded, read-only claim audit for the spawning EM. This skill is an
instrument method, not scientific authority.

## Preconditions

Proceed only when the parent supplies a frozen operation containing:

- `direction_id`, `evidence_id`, and capability ID `scientific-critical-thinking`;
- one objective, hash-bound input refs, judgment criteria, and scope constraints;
- the claim or authority locator to be affected by the observation.

If the operation is incomplete, return `FAILED` with code
`INVALID_FROZEN_OPERATION`; do not invent missing criteria. Never delegate, create
tasks, install dependencies, use external providers, change lifecycle/state, or write
the durable evidence sidecar. The EM validates and writes that sidecar.

## Audit method

1. State the exact claim, its type (descriptive, mechanistic, comparative, causal,
   or readiness), and the strength of language being tested.
2. Separate source facts and direct observations from inference. Cite the supplied
   locator for each material fact; do not treat absence of evidence as falsification.
3. Test the prerequisites needed for this particular inference. When relevant, check
   for a finite registered algorithm, host dynamics/law and objective, operational
   thresholds or decision rules, a UAV/runtime bridge, a comparator, and evidence
   that discriminates the proposed mechanism from alternatives.
4. Classify each threat as `contrary_evidence`, `missing_evidence`, `scope_mismatch`,
   or `unsupported_assumption`, and explain exactly which inference it limits.
5. Give the strongest plausible alternative explanation. Name the smallest decisive
   observation that would change the judgment.
6. Classify the claim as `supported`, `refuted`, or `underdetermined`, then state the
   highest narrower claim the evidence supports. Never output `PASS` or equate tool
   success with scientific acceptance.

Use proportional criticism. Do not import clinical GRADE/Cochrane hierarchies,
systematic-review quotas, AI schematics, or generic paper-review ceremony.

## Typed final return

Return exactly one `instrument_observation` object with these fields:

```yaml
instrument_observation:
  schema_version: 1
  evidence_id: <frozen id>
  capability_id: scientific-critical-thinking
  outcome: OBSERVED | FAILED | UNAVAILABLE
  claim_classification: supported | refuted | underdetermined | null
  core_observations: [<bounded observation>]
  source_facts: [{locator: <input ref>, observation: <fact>}]
  inferences: [<explicit inference>]
  threats: [{kind: <class>, locator: <input ref>, impact: <bounded effect>}]
  strongest_alternative: <explanation or null>
  decisive_missing_evidence: [<observation that would change judgment>]
  supported_claim: <highest defensible statement or null>
  claim_ceiling: <forbidden stronger conclusion or null>
  assumptions: [<assumption>]
  limitations: [<limitation>]
  failure: {code: <code>, summary: <summary>} | null
```

For `FAILED` or `UNAVAILABLE`, keep every method-specific field in the object;
use empty arrays or null values where no audit observation exists and populate
`failure`. Do not add method, acceptance, lifecycle, or recommendation fields.

Keep the return concise enough for the EM to inspect and map into instrument evidence
v1. Do not add a lifecycle recommendation or edit instructions.
