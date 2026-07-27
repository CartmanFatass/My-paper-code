# Mechanical intake record — 20260726_d7_s_stage_b_shared_prefix_realization

Transport facts only. The scientific reading is `30_PM_SCIENTIFIC_RECONCILIATION.md`.

## Round identity

```text
round=20260726_d7_s_stage_b_shared_prefix_realization
reviewer_key=open_divergent
branch=untied-k
stage_commit=4d4a623f250decd9376afbb0b3f16e74aee813ee
conversation_id=6a63979e-35d8-83e8-8da7-10de59a5fdeb
question=docs/external-review/rounds/20260726_d7_s_stage_b_shared_prefix_realization/20_PRO_OPEN_QUESTION.md
raw=docs/external-review/rounds/20260726_d7_s_stage_b_shared_prefix_realization/21_PRO_OPEN_RAW.md
```

Preflight returned `ROUND_PREFLIGHT_READY` with a 10-path allow-list, all present
at `stage_commit`, and `REVIEW_EVIDENCE_ARCHIVE_READY`.

## Fence

Sent **exactly once**. Send-verified mechanically before any further action: the
composer was empty afterwards, and the count of visible user turns carrying this
round's identity went from **0 to exactly 1**, with all five fields matching
`10_FENCE.txt`. Never resubmitted. No convergence turn was sent.

## Response identity and completion evidence

```text
assistant_message_id=cdbe2842-e1ed-4db1-8aa0-c643b254f09b
model_slug=gpt-5-6-pro
finish_details={"type":"stop","stop_tokens":[200002]}
```

- Two inspections more than three seconds apart returned the same message id and
  the same rendered length (18,722 chars) with no change in tail text.
- No `Stop generating` / `Stop answering` / `Retry` / continue control was
  present in either inspection. While generation was still running earlier,
  `Stop answering` and `Answer now` were both observed active; **`Answer now`
  was never clicked**, and the round was left to finish on its own.
- `finish_details.type=stop` confirms normal termination rather than truncation.
- The response is attributable to this round's fence: its own header reads
  `Stage reviewed: 4d4a623f250decd9376afbb0b3f16e74aee813ee`.

## Capture path

`Copy response` was again unavailable: the extension's tab reports
`document.hasFocus()===false` intermittently, and a clipboard write from an
unfocused document is refused. Restoring OS foreground via
`scripts/ensure_review_browser.ps1` did not make the tab's document focused.

Capture therefore used the same message-source path as the previous round, which
is neither transcription nor rendered text:

```text
capture_method=react_message_source_extraction
chars=20099
utf8_bytes=20315
sha256=9CAC91680769F1B7B4A4604FB3B74CAA514A43911915CB418F263CBCE38BC9ED
```

The SHA-256 computed **in the page** over the UTF-8 encoding of the message
source equals the SHA-256 of the downloaded file and equals the SHA-256 of the
archived raw. Reread of the archived file returns 20,099 characters, head
`# Scientific ruling — D7.S Stage B shared-prefix realization`, tail
`...This review authorizes neither implementation nor compute.**`.

Rendered length (18,722) is shorter than source length (20,099) because the
source carries citation tokens in private-use codepoints that render as links.
None of the three prohibited capture methods was used.

As before, the byte-exactness claim scopes to the Git blob: `core.autocrlf=true`
and no attribute pins these paths, so a Windows checkout materializes CRLF.

## Terminal state

```text
exact_raw=written_and_hash_verified
provenance_intake=this_file
heartbeat=never_created_this_session_confirmed_absent
duplicate_submission_risk=none_fence_sent_once_never_resubmitted
evidence_access_recovery=not_required_reviewer_read_the_repository_successfully
verdict_recorded_without_alteration=MISMATCH
```
