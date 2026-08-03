# Explorer-Origin Project Validation Workflow

This contract defines the narrow semantic bridge from advisory Independent
Research Explorer output to Code Project Manager. It does not promote advisory
research into canonical science and grants no code or compute authority.

## Authority and public interface

Explorer owns advisory research and writes only its outbound public handoffs.
Code Project Manager owns project coordination, code, runtime and technical
acceptance; it reads Explorer handoffs but never reads `local_research/`.
External Pro owns scientific choices inside each submitted review boundary.
Workflow Design Manager owns this stable interface, not its live handoff
content.

The shared interface is `docs/project/handoffs/`:

- `explorer_to_code_manager/`: Explorer writes and deletes its own files; CPM
  reads them.
- `code_manager_to_explorer/`: CPM writes and deletes its own files; Explorer
  reads them.

A handoff is a self-contained Markdown or JSON brief, with attachments only
when every receiver can read them. It should make the target, candidate and
version, intended outcome, concrete inputs, evidence, uncertainty, allowed and
excluded effects, authority boundary, completion evidence and return task easy
to understand. These are semantic completeness cues, not a schema or admission
check. No `document_kind`, packet version, validator receipt, hash or byte count
is required.

## Intelligent intake and ordering

The receiving model judges whether the brief is sufficient and may perform
bounded safe read-only reconnaissance before acting. It does not reject a
handoff because of formatting. It stops only when an authority, External Pro
scientific choice or concrete input object is materially missing.

One manifest may preserve an ordered group of public brief paths. That order is
work organization rather than queue state, ranking or scientific comparison.
CPM processes one isolated candidate at a time; one candidate's problem does
not block unrelated work or change another candidate's scientific status.

For an Explorer-origin toy candidate, CPM may prepare the exact
`EXPLORER_TOY_DESIGN_ASSERTION_AUDIT` question after semantic intake. External
Pro decides the scoped scientific contract. CPM begins implementation only
after that science is frozen, and compute begins only under an applicable
explicit user grant. The handoff itself cannot supply either authority.

After work on one candidate, CPM returns an explanatory brief that begins with
the natural-language conclusion and then appends the necessary exact evidence.
A native task message carrying the same content is the single fallback.
Mechanical field-only callbacks are insufficient.

## Lifecycle and failure ownership

The sender owns its outbound file and removes it from the active tree after the
receiver has completed intake; Git is the archive. There is no compatibility
tree, registry, queue engine, retry state or duplicated history directory.

Explorer corrects missing advisory content. CPM owns implementation and
operational recovery. External Pro owns estimand, mechanism, sufficiency and
result meaning. WDM repairs only this interface. Missing formatting or a prior
mechanical BLOCKED receipt is not candidate evidence and does not support or
refute a proposition.

Candidate evidence, run roots, artifacts and results remain candidate-specific.
This lane consumes no formal iteration and does not update the CDC portfolio.

```text
formal=false
current_work_mutation=forbidden
```
