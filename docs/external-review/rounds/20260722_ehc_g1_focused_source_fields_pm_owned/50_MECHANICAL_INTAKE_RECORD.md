# Controller mechanical intake record

semantic_author=controller
artifact_scope=mechanical_transport_only
scientific_authority=external_pro
repair_owner=controller

round=20260722_ehc_g1_focused_source_fields_pm_owned
repository=CartmanFatass/My-paper-code
branch=aggressive
stage_commit=50f95da37496b092128c2136d50503ac3e18a5c1
conversation_id=6a5a7735-ab30-83e8-bb88-d0cfb3cea56c
question=docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/20_PRO_OPEN_QUESTION.md
question_sha256=9e87fadafe8e2f090c7385e97c6e247c42578bcdbb1b69f6b90a2b8ab73198d8
raw=docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/21_PRO_OPEN_RAW.md
raw_sha256=db95309db3fc04d5c754fff3001e66b93d8b185d34c26ec9a21867b6182efce5
raw_bytes=11810

## Transport observations

- The exact registered URL initially redirected to the signed-in ChatGPT home
  page. The registered conversation was recovered from the visible sidebar by
  exact `conversation_id`.
- The recovered conversation initially exposed a composer but no message-role
  containers. One reload of the same tab restored the existing conversation.
- The full focused freshness fence was absent before submission. It was
  submitted once and the visible user turn matched `round`, `stage_commit` and
  `question` exactly.
- The first assistant response explicitly reported unavailable listed evidence.
  It was classified only as an operational transport diagnostic and was not
  written to the raw file.
- The 12 evidence paths listed by the question were materialized directly from
  `stage_commit` into one repository-relative archive. The archive contained
  exactly the allow-listed file members and no additional file.
- evidence_archive_sha256=6c2d41c760552513a12f3631bc0f4dd98b7f68db853771375d055d5e34eeac45
- evidence_archive_bytes=68615
- The archive was attached in the same registered conversation. The mechanical
  continuation did not submit another freshness fence and added no scientific
  content.
- The candidate assistant message after that continuation had
  `data-message-id=91220a55-8a25-47c1-bbd3-0f7ef8fd11c5`. Two snapshots at
  least 3.5 seconds apart had the same identity and 11,406-character text.
  Both exposed no active `Stop generating`, `Stop answering`, retry or
  continue-generation control.
- The archived UTF-8 raw plus its final newline matched the captured response
  SHA-256 exactly.
- heartbeat_id=hmasd-focused-g1-source-fields-pro-review-heartbeat
- heartbeat_terminal_status=absent_confirmed_by_delete_not_found

transport_status=COMPLETE
transport_eligibility=eligible_for_project_manager_reconciliation
scientific_quality=not_classified_by_controller
implementation_authority=none
compute_authority=none
