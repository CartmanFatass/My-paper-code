---
name: hmasd-explorer-project-validation
description: Use for one semantic Explorer-to-project handoff through the shared ignored temporary handoff surface while preserving advisory, science, code and compute authority boundaries.
---

# Explorer project validation

This Skill is the lightweight collaboration path from Independent Research
Explorer to Code Project Manager. It is not a packet validator, dispatcher,
queue engine or state machine. It grants no code, compute, scientific,
current-work or project-state authority.

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

Explorer may then inspect project code, tests, configuration, design documents
and runtime evidence as needed. Result-named paths are useful entry points, not
an allow-list. It accepts or rejects
scientific-semantic conformance to the selected treatment and explains any
mismatch. CPM remains the sole technical acceptance owner and performs any
authorized correction; Explorer does not modify code or run compute.

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
