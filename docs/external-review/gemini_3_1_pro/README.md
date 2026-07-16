# Gemini 3.1 Pro External Reviewer

This directory owns the operational contract and historical setup evidence for
the persistent Gemini reviewer. New multi-review evidence lives in the
round-centric directories under `docs/external-review/rounds/`.

## Role

- **Gemini 3.1 Pro (High):** independent divergent architecture reviewer. It
  may propose, replace or reject hypotheses and has equal standing with the
  independent GPT-5.6 Pro open reviewer. Its local CLI additionally reads
  allowlisted original papers.
- **GPT-5.6 Pro open reviewer:** an independent blind divergent review from a
  separate conversation.
- **GPT-5.6 Pro convergent reviewer:** evidence and validity adjudication after
  both divergent raw responses and the Codex synthesis exist.
- **Codex:** controller. It owns the hypothesis portfolio, chooses at most one
  active experiment, interprets external responses and writes the repository.

No reviewer receives a fixed evidentiary weight from model identity. Reviewer
suggestions are evidence and criticism, not authorization to edit, launch an
experiment or replace the registered contract.

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
  -QuestionPath .\docs\external-review\rounds\YYYYMMDD_topic\10_GEMINI_DIVERGENT_QUESTION.md `
  -SourceManifestPath .\docs\external-review\rounds\YYYYMMDD_topic\02_GEMINI_LOCAL_SOURCE_MANIFEST.md `
  -ResponsePath .\docs\external-review\rounds\YYYYMMDD_topic\11_GEMINI_DIVERGENT_RAW.md
```

Use `-DryRun` first when a manifest changes. The real call initializes the
project conversation if needed, reuses its exact ID thereafter and writes the
model output verbatim to `GEMINI_3_1_PRO_RESPONSE_RAW.md`. It refuses to
overwrite an existing raw response unless `-Force` is explicitly supplied.

For a multi-turn research phase, keep one process alive:

```powershell
pwsh -NoProfile -File `
  .\scripts\start_gemini_reviewer_live.ps1 `
  -QuestionPath .\docs\external-review\rounds\YYYYMMDD_topic\09_GEMINI_LIVE_RESEARCH_PROMPT.md `
  -SourceManifestPath .\docs\external-review\rounds\YYYYMMDD_topic\02_GEMINI_LOCAL_SOURCE_MANIFEST.md `
  -ResponsePath .\docs\external-review\rounds\YYYYMMDD_topic\11_GEMINI_DIVERGENT_RAW.md
```

Keep this process alive through source inspection, follow-up questions and the
final divergent answer. Once that answer is visible, press Ctrl+C twice. The
launcher exports the last completed Gemini response from the local full
transcript; it does not send an extra prompt or resume turn. To archive
manually, use:

```powershell
pwsh -NoProfile -File `
  .\scripts\export_gemini_live_response.ps1 `
  -ConversationId <UUID printed by the live launcher> `
  -ResponsePath .\docs\external-review\rounds\YYYYMMDD_topic\11_GEMINI_DIVERGENT_RAW.md
```

Use `invoke_gemini_reviewer.ps1` only for a single-turn non-interactive review
or recovery. Do not run the live and non-interactive clients concurrently on
the same conversation.

The shared round layout and blind-review ordering are defined by
`docs/external-review/README.md`.

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
