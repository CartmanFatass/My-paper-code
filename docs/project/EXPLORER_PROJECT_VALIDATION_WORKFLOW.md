# Explorer-Origin Project Validation Workflow

This contract defines the narrow semantic bridge from advisory Independent
Research Explorer output to Code Project Manager. It does not promote advisory
research into canonical science. Explorer's explicit instruction authorizes CPM
to execute the named treatment without giving Explorer direct code/runtime control.

## Authority and public interface

Explorer owns advisory research and writes only its outbound temporary handoffs.
Code Project Manager owns project coordination, code, runtime and technical
acceptance; it reads Explorer handoffs but never reads `local_research/`.
External Pro owns scientific choices inside each submitted review boundary.
Workflow Design Manager owns this stable interface, not its live handoff
content.

The tracked stable contract is `docs/project/handoffs/README.md`. Live exchange
files use the ignored shared root `temp/handoffs/`:

- `temp/handoffs/explorer_to_code_manager/`: Explorer writes and deletes its own files; CPM
  reads them.
- `temp/handoffs/code_manager_to_explorer/`: CPM writes and deletes its own files; Explorer
  reads them.

A handoff is a self-contained Markdown or JSON brief, with attachments only
when every receiver can read them. It should make the target, candidate and
version, intended outcome, concrete inputs, evidence, uncertainty, allowed and
excluded effects, authority boundary, completion evidence and return task easy
to understand. It also makes Explorer's selected treatment understandable:
experiment, instance binding, pause, abandon or one exact external-review need.
Explorer gives one clear instruction naming implementation, instance binding,
experiment, pause, abandon or exact review as applicable. That instruction
authorizes CPM to execute the named treatment without separate code or experiment
permission fields, and CPM does not infer omitted actions. If an object is
missing, the brief states what is known. CPM constructs or binds engineering
objects; Explorer answers any genuinely scientific choice CPM cannot determine.
These are semantic completeness cues, not a schema or admission check. No
`document_kind`, packet version, validator receipt, hash or byte count is required.

## Intelligent intake and ordering

The receiving model judges whether the brief is sufficient and may perform
bounded safe read-only reconnaissance before acting. It does not reject a
handoff because of formatting or a missing object. The two roles resolve the
gap through direct semantic exchange instead of creating a `BLOCKED` state.

One manifest may preserve an ordered group of public brief paths. That order is
work organization rather than queue state, ranking or scientific comparison.
CPM processes one isolated candidate at a time; one candidate's problem does
not block unrelated work or change another candidate's scientific status.

For an Explorer-origin candidate, CPM implements the selected treatment as an
engineering task and does not substitute External Pro for experiment, instance
binding, pause or abandon. It prepares an exact review only when the brief
explicitly requests one. An unclear treatment returns one precise question to
Explorer without blocking unrelated candidates. The instruction is not a
canonical scientific conclusion, but it is sufficient authority for CPM to
perform the named project-validation task. CPM resolves engineering gaps and
Explorer resolves scientific choices; neither treats a missing object as a
workflow terminal.

After work on one candidate, CPM returns an explanatory brief that begins with
the natural-language conclusion and then appends the necessary exact evidence.
A native task message carrying the same content is the single fallback.
Mechanical field-only callbacks are insufficient.

After technical acceptance, CPM pushes the result and returns its exact commit
and public GitHub repository/path locators. CPM does not initiate the final
acceptance review. Explorer may inspect project material read-only as needed,
then freezes one `CODE_SCIENCE_ALIGNMENT_AUDIT`, submits it through the dedicated
Agentify transport task, and archives and intakes the raw answer. External Pro
uses the GitHub connection to inspect the exact pushed revision and owns final
scientific-semantic acceptance. Explorer never substitutes its own acceptance.
The review starts only after CPM technical acceptance and push.

## Lifecycle and failure ownership

The sender deletes its outbound temporary file after intake. No live handoff
enters Git; canonical records remain in their existing owner locations. There
is no compatibility tree, registry, queue engine, retry state or duplicated
history directory.

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
