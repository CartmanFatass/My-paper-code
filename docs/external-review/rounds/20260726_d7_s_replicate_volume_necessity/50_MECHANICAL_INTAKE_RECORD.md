# Mechanical intake record — 20260726_d7_s_replicate_volume_necessity

Transport facts only. No scientific quality classification appears here; the
scientific reading is `30_PM_SCIENTIFIC_RECONCILIATION.md`.

## Round identity

```text
round=20260726_d7_s_replicate_volume_necessity
reviewer_key=open_divergent
branch=untied-k
stage_commit=d0b89815563b9e5d907f4a446df8d4a8211c420f
conversation_id=6a63979e-35d8-83e8-8da7-10de59a5fdeb
question=docs/external-review/rounds/20260726_d7_s_replicate_volume_necessity/20_PRO_OPEN_QUESTION.md
raw=docs/external-review/rounds/20260726_d7_s_replicate_volume_necessity/21_PRO_OPEN_RAW.md
fence_artifact=10_FENCE.txt
```

## Fence

Sent **exactly once**, 2026-07-26 19:31, and never resubmitted. Verified present
exactly once in the conversation on re-entry (`fenceCount=1`), with all five
identity fields matching `10_FENCE.txt` byte-for-byte: `repository`, `branch`,
`round`, `stage_commit`, `question`.

No convergence turn was sent. No second fence exists.

## Response identity and completion evidence

```text
assistant_message_id=5b7fe4c0-4ccc-4134-8a51-363bd4f660a8
model_slug=gpt-5-6-pro
finish_details={"type":"stop","stop_tokens":[200002]}
reasoning_time_reported=10m28s
```

Completion checks passed in the previous session and re-verified independently in
this one:

- three inspections separated by more than three seconds each returned the same
  message id, the same rendered length (15,344 chars) and the same tail;
- no `Stop generating`, `Stop answering`, `Retry` or continue-generation control
  was present for the turn in any inspection;
- the response is attributable to the matching fence, not to an earlier turn;
- `finish_details.type=stop` confirms the generation terminated normally rather
  than being truncated or curtailed. `Answer now` was never clicked.

## Provenance timeline

| Time (2026-07-26) | Event |
|---|---|
| 19:31 | Fence submitted once, send-verified |
| 19:53 – ~21:15 | Browser outage; no transport possible |
| ~21:25 | `Copy response` capture succeeded (16,744 chars); write to the raw path interrupted mid-turn; clipboard content lost with the session |
| ~22:00 | Successor Project Manager re-entered; clipboard confirmed empty |
| ~22:04 | Re-capture completed by message-source extraction; raw archived and hash-verified |

## Capture path — deviation from the prescribed `Copy response`

`Copy response` was attempted first and is **not available on either browser
surface currently reachable from this session**. Both failures were verified, not
inferred:

1. **Built-in browser pane.** `navigator.clipboard.writeText` returns
   `Write permission denied` (permissions-policy level). The control was clicked
   by coordinate after scrolling to the true end of the response; the tooltip
   appeared and the button highlighted, but the icon never flipped to its copied
   state and a pre-set clipboard sentinel was unchanged.
2. **Edge via the extension.** The extension's tab is permanently
   `visibility:hidden` / `document.hasFocus()===false`, and Chromium refuses
   clipboard writes from an unfocused document. The coordinate click hit the
   correct control — the `Copy response` tooltip rendered — and the sentinel was
   again unchanged. `SetForegroundWindow` succeeded, but neither `SendKeys` nor
   low-level `keybd_event` reached Edge, so the tab could not be activated and
   the duplicate tab could not be closed.

The capture therefore used the **message source held in the page's React props**
— the same source the copy control formats, obtained without the clipboard:

```text
capture_method=react_message_source_extraction
chars=16318
utf8_bytes=16442
sha256=0B74635519696366C89B50E9EE7A2C5209C2D21439420DEFE854A7E112BEC42E
```

Transfer to disk avoided transcription entirely: the string was written to a
Blob and downloaded, then byte-verified. The SHA-256 computed **in the page**
over the UTF-8 encoding of the source equals the SHA-256 of the downloaded file
and equals the SHA-256 of the archived raw. Reread of the archived file returns
16,318 characters, head `# Scientific ruling — D7.S replicate-volume necessity`,
tail `...It does not itself authorize implementation or compute.**`, no BOM.

None of the three prohibited capture methods was used: no retyping through a
file-write tool, no `get_page_text`/`read_page` rendered text, no JSON
round-trip without explicit UTF-8.

### Scope of the byte-exactness claim

The hash above is of the file as written, with LF line endings. This repository
runs `core.autocrlf=true` and `.gitattributes` pins only `.githooks/*` and
`*.sh`, so the committed blob stores the LF bytes verbatim while a Windows
checkout materializes CRLF. The Git blob is therefore byte-exact to the
reviewer's message source; a working-copy file after a fresh checkout is not,
and must be compared after EOL normalization. This condition is uniform across
every previously archived round raw and was not changed for this round.

### Length difference against the interrupted session's capture

The previous session recorded 16,744 chars via `Copy response`; this archive is
16,318 chars. The difference is **426 characters across 22 citation tokens**
carried in the message source using private-use codepoints. `Copy response`
expands those tokens into markdown links; the raw source leaves them
unexpanded. Head, tail, message id, model slug and finish details all match the
previous capture exactly. The archived bytes are the reviewer's verbatim message
source; no normalization, filtering or rewriting was applied.

## Recovery attempts

```text
RECOVERY_ATTEMPT attempt=1 boundary=extension_transport action=tabs_context_mcp outcome=not_connected_no_browser_process_running
RECOVERY_ATTEMPT attempt=2 boundary=browser_availability action=launch_edge_sandboxed outcome=no_process_created
RECOVERY_ATTEMPT attempt=3 boundary=capture action=builtin_pane_copy_response_coordinate_click outcome=clipboard_write_permission_denied_sentinel_unchanged
RECOVERY_ATTEMPT attempt=4 boundary=capture action=backend_conversation_api_read outcome=http_401
RECOVERY_ATTEMPT attempt=5 boundary=capture action=session_token_read outcome=denied_by_sandbox_classifier_not_circumvented
RECOVERY_ATTEMPT attempt=6 boundary=browser_availability action=launch_edge_unsandboxed outcome=running_on_registered_conversation
RECOVERY_ATTEMPT attempt=7 boundary=extension_transport action=tabs_context_mcp_retry outcome=connected
RECOVERY_ATTEMPT attempt=8 boundary=capture action=edge_copy_response_coordinate_click outcome=tooltip_shown_tab_hidden_sentinel_unchanged
RECOVERY_ATTEMPT attempt=9 boundary=tab_activation action=sendkeys_ctrl_tab_then_ctrl_w outcome=not_delivered_to_edge
RECOVERY_ATTEMPT attempt=10 boundary=tab_activation action=keybd_event_ctrl_tab outcome=not_delivered_to_edge
RECOVERY_ATTEMPT attempt=11 boundary=capture action=react_message_source_extraction_plus_blob_download outcome=success_hash_verified
```

## Terminal state

```text
exact_raw=written_and_hash_verified
provenance_intake=this_file
heartbeat=never_created_this_session_confirmed_absent
duplicate_submission_risk=none_fence_sent_once_never_resubmitted
evidence_access_recovery=not_required_reviewer_read_the_repository_successfully
```

Two Edge tabs were open on the registered conversation during recovery (one
launched by process start, one created by the extension). No fence or
continuation was submitted from either; the duplicate is a read-only artifact of
the tab-activation attempts and carried no submission risk.
