# Gemini Local Source Manifest

Standing-consent boundary:

- destination: registered Gemini 3.1 Pro (High) session
  `111dc970-bd72-4d67-8d7a-caea65394b78`;
- operator: one depth-one `gpt-5.6-terra` subagent at `medium` reasoning;
- mode: project-only, tracked, read-only inputs through an interactive PTY;
- allowed paths:
  - `docs/external-review/rounds/20260719_external_review_transport_subagent_retry1/00_REVIEW_BRIEF.md`
  - `docs/external-review/rounds/20260719_external_review_transport_subagent_retry1/01_SHARED_SOURCE_MANIFEST.md`
  - `docs/external-review/rounds/20260719_external_review_transport_subagent_retry1/02_GEMINI_LOCAL_SOURCE_MANIFEST.md`
  - `docs/external-review/rounds/20260719_external_review_transport_subagent_retry1/10_GEMINI_DIVERGENT_QUESTION.md`
- allowed output:
  - `docs/external-review/rounds/20260719_external_review_transport_subagent_retry1/11_GEMINI_DIVERGENT_RAW.md`

The operator may approve once only a displayed read-only command whose resolved
paths are all in the allowlist. It must deny writes, execution unrelated to
reading the allowlist, credentials, personal data, project-external paths, and
any request whose exact command is not visible. Global permission bypass is
forbidden.
