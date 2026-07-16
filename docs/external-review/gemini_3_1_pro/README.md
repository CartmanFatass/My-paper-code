# Gemini 3.1 Pro External Reviewer

This directory owns the durable evidence for the persistent Gemini reviewer.
It does not own algorithm specifications, experiment results, papers, or source
code.

## Role

- **Gemini 3.1 Pro (High):** divergent architecture reviewer. It maintains
  competing causal explanations, looks for missing design families and tests
  whether a proposed experiment actually separates them.
- **GPT-5.6 Pro:** convergent adversarial reviewer. It audits evidence,
  implementation validity and promotion or retirement claims at sparse
  decision boundaries.
- **Codex:** controller. It owns the hypothesis portfolio, chooses at most one
  active experiment, interprets external responses and writes the repository.

Reviewer suggestions are evidence and criticism, not authorization to edit,
launch an experiment or replace the registered contract.

## Persistent conversation

Use one Antigravity CLI conversation rooted at `C:\project\HMASD`. The CLI's
own cache maps this working directory to the conversation ID; the ID is local
runtime state and is not committed. The invocation script always selects
`Gemini 3.1 Pro (High)`, plan mode and sandbox mode. Do not use
`--dangerously-skip-permissions`, and do not run an interactive and scripted
turn against the same conversation concurrently.

```powershell
pwsh -NoProfile -File `
  .\scripts\invoke_gemini_reviewer.ps1 `
  -QuestionPath .\docs\external-review\gemini_3_1_pro\YYYYMMDD_topic\GEMINI_3_1_PRO_QUESTION.md `
  -SourceManifestPath .\docs\external-review\gemini_3_1_pro\YYYYMMDD_topic\SOURCE_MANIFEST.md
```

Use `-DryRun` first when a manifest changes. The real call initializes the
project conversation if needed, reuses its exact ID thereafter and writes the
model output verbatim to `GEMINI_3_1_PRO_RESPONSE_RAW.md`. It refuses to
overwrite an existing raw response unless `-Force` is explicitly supplied.

## Round layout

```text
YYYYMMDD_topic/
  GEMINI_3_1_PRO_QUESTION.md
  SOURCE_MANIFEST.md
  GEMINI_3_1_PRO_RESPONSE_RAW.md
  DISPOSITION.md
```

The question states the decision needed. The manifest is the per-round local
file allowlist. The response is archived before interpretation. The disposition
records model, date, accepted/rejected/modified/deferred claims and their effect
on the live hypothesis portfolio.

## Source policy

- Keep papers, literature notes, code and experiment evidence at their
  canonical repository locations; do not copy them into every review round.
- List only files needed for the decision. Public papers may be supplied when
  locally available. Private HMASD material is supplied only through the
  explicit round manifest.
- A manifest is a reviewer instruction, not a filesystem security boundary.
  Plan and sandbox mode remain enabled, and the reviewer must not inspect files
  outside the list.
- When the question is self-contained, use `access_mode: prompt_only` and list
  no additional files.

Accepted algorithm synthesis moves to `docs/research/`. Current ownership and
the next active experiment remain in `memory/CURRENT_WORK.md`; experiment data
remain under `logs/`.
