---
name: hmasd-explorer-project-validation
description: Use for one semantic Explorer-to-project handoff through the shared ignored temporary handoff surface while preserving advisory, science, code and compute authority boundaries.
---

# Explorer project validation

This Skill is the lightweight collaboration path from Independent Research
Explorer to Code Project Manager. It is not a packet validator, dispatcher,
queue engine or state machine. Explorer's explicit instruction authorizes CPM
to execute the named project-validation treatment; it does not give Explorer
direct code/runtime control or promote canonical science.

## Normal path

Explorer writes one self-contained, human/model-readable Markdown or JSON brief
under `temp/handoffs/explorer_to_code_manager/`. The live file is ignored and
requires no Git operation. The brief explains one candidate's identity, target and
version, intended outcome, concrete inputs, evidence and uncertainty, allowed
and excluded effects, relevant authority boundary, completion evidence and
return task and selected treatment defined by the stable workflow. These are
semantic writing aids, not required field names. The brief gives one clear
instruction naming implementation, instance binding, experiment, pause, abandon
or exact review as applicable. That instruction authorizes CPM to execute the
named treatment without separate permission fields. It separates missing
scientific inputs from independently executable infrastructure, interfaces and
fail-closed tests.

One optional manifest may list several brief paths in their intended order.
The manifest is work organization only: it contains no item state, owner lease,
retry record or admission status. CPM processes one isolated candidate at a
time and preserves the supplied order without treating it as a ranking.

CPM reads the named public brief, uses engineering judgment and performs
bounded safe read-only reconnaissance. It proceeds when the task is
semantically sufficient. Missing headings, `document_kind`, schema fields or a
validator receipt never block intake. CPM implements the named treatment without
substitution and does not infer omitted actions. A missing object is resolved
collaboratively: CPM constructs or binds engineering objects, while one
genuinely scientific choice returns as a concrete question to Explorer. This
exchange is normal work, not a `BLOCKED` state.

CPM returns a human-readable result under
`temp/handoffs/code_manager_to_explorer/` containing an understandable
natural-language conclusion first and the necessary exact evidence second. A
Codex-native message carrying the same semantic content is the simple fallback.
Explorer reads but never edits CPM output.

After technical acceptance, CPM pushes the result and returns its exact commit
plus public GitHub repository/path locators. Explorer may inspect project
material read-only as needed, then freezes one `CODE_SCIENCE_ALIGNMENT_AUDIT`
and sends it through the dedicated Agentify transport task. External Pro uses
the GitHub connection to inspect the exact pushed revision and owns final
scientific-semantic acceptance. Explorer archives and intakes the raw answer but
does not substitute its own acceptance. CPM does not initiate this review and
remains the sole technical acceptance owner.

The audit asks a natural scientific decision question and supplies the frozen
contract, exact revision and relevant evidence without pre-filling the answer as
a list of findings to close. It asks Pro to reconstruct what proposition the
code realizes, identify the strongest material hidden assumption or alternate
explanation, assess whether the evidence is discriminating and scientifically
useful, and only then give the bounded final disposition. Known concerns are
context for judgment, not mandatory headings or an expected verdict.

If a referenced attachment is not readable by CPM, Explorer embeds the minimum
necessary content in the same public brief; it does not create another wrapper
or require CPM to read `local_research/`. Neither direction uses hashes, byte
counts or fingerprints. After receiver intake, the file author removes the
temporary exchange copy. Canonical research, code, review and result records
remain in their existing owner-controlled locations; the handoff itself is not
an archive.

## Preserved authority

Explorer remains advisory. CPM owns project coordination, code, runtime and
technical acceptance. External Pro owns scoped scientific choices. Compute
still requires the applicable explicit user grant. Candidate evidence, run
roots, artifacts and results remain candidate-specific. This lane is
`formal=false`, consumes no formal iteration and does not update the CDC
portfolio or `CURRENT_WORK.md` merely by exchanging a brief.

```text
formal=false
current_work_mutation=forbidden
```
