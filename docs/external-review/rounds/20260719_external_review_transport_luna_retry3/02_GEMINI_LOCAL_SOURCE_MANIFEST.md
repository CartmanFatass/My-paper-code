# Gemini Local Source Manifest

Standing-consent boundary:

- destination: registered Gemini 3.1 Pro (High) conversation
  `111dc970-bd72-4d67-8d7a-caea65394b78`;
- operator: one depth-one `gpt-5.6-terra` subagent at medium reasoning;
- mode: project-only, tracked, read-only inputs through an interactive PTY;
- allowed paths:
  - `docs/external-review/rounds/20260719_external_review_transport_luna_retry3/00_REVIEW_BRIEF.md`
  - `docs/external-review/rounds/20260719_external_review_transport_luna_retry3/01_SHARED_SOURCE_MANIFEST.md`
  - `docs/external-review/rounds/20260719_external_review_transport_luna_retry3/02_GEMINI_LOCAL_SOURCE_MANIFEST.md`
  - `docs/external-review/rounds/20260719_external_review_transport_luna_retry3/10_GEMINI_DIVERGENT_QUESTION.md`
- allowed output:
  - `docs/external-review/rounds/20260719_external_review_transport_luna_retry3/11_GEMINI_DIVERGENT_RAW.md`

The operator may approve once only a displayed read-only command whose resolved
paths are all in this allowlist. Writes other than the registered raw,
credentials, project-external paths, execution, and global permission bypass
are forbidden.
