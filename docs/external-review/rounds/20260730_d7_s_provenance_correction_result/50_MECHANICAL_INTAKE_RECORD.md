# Mechanical intake -- 20260730_d7_s_provenance_correction_result

Transport facts only. No scientific classification; that is
`30_PM_SCIENTIFIC_RECONCILIATION.md`.

## Identity

```text
round          20260730_d7_s_provenance_correction_result
repository     CartmanFatass/My-paper-code
branch         untied-k
stage_commit   b8652fd97cc7f29b123a343eab7aaa3df3a2bbf2
question       docs/external-review/rounds/20260730_d7_s_provenance_correction_result/20_PRO_OPEN_QUESTION.md
reviewer       open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
transport      project_manager_direct
model_ui       gpt-5-6-pro  (expected_model_ui = Pro)
message_id     2f236234-31c7-47bf-a58b-75c95b0664c7
```

## Send

Verified mechanically at the time of sending, not by inference: `user_turns`
38 -> 39, exactly one turn carrying the `stage_commit`, composer empty,
generation active. Recorded in `docs/project/CURRENT_WORK.md` at `fe58f714`.

## Wait, and a transport interruption worth recording

Generation took **11.2 minutes** (fence `create_time` 1785403932.48, ruling
1785404606.39). No `hmasd-review-monitor` was dispatched and no Monitor was
created; the Project Manager paced in-band. **No heartbeat exists, so there is
none to delete.**

**Between send and capture the browser process disappeared entirely.**
`tabs_context_mcp` returned `Browser extension is not connected`, and
`list_connected_browsers` returned `[]`. This was NOT a dead round: the ruling
had already been generated server-side and was waiting in the conversation.

```text
RECOVERY_ATTEMPT
attempt=1
boundary=browser extension not connected
action=Get-Process chrome -> 0
outcome=MISLEADING. This repository's transport browser is Edge, not Chrome, and
        Chrome has never been installed on this machine. The Skill already names
        this exact false negative ("Verify a search before concluding absence").
        Re-ran against msedge: also 0, so the browser really was gone -- but the
        first search proved nothing and must not be cited as if it had.

RECOVERY_ATTEMPT
attempt=2
boundary=same
action=scripts/ensure_review_browser.ps1 -ReviewerKey open_divergent
outcome=BROWSER_READY, launched_by_this_script=True, main_window_pid=17988,
        os_foreground=False. The MCP tab group had not survived, so the
        registered URL was opened once by `navigate`, per RESOLVE_REGISTERED_
        CONVERSATION. Extension reconnected on its own, as the Skill predicts.
```

The purpose-built bring-up script did in one call what a previous session
re-derived by hand. Its documented sandbox caveat did not fire.

## Completion evidence

Judged before capture, from a light DOM read (the reliable signal on a hidden
tab) and then confirmed against the API:

```text
stop_button        false
last_assistant_len 20534 (rendered innerText)
composer_empty     true
api last_len       22115 (emitted markdown)
```

The rendered transcript is virtualized -- only 3 assistant and 4 user nodes were
in the DOM against 102 and 39 in the conversation. The API is the authority for
identity; the DOM is only a liveness signal.

## Fence verification, from the API rather than `find`

```text
api_user_turns=39   api_assistant_turns=102   exact_fence_hits=1
```

Exactly one user turn carries `b8652fd97cc7f29b123a343eab7aaa3df3a2bbf2` -- the
fence this round sent, not a second accidental submission.

## Capture

Primary path -- the conversation API, returning the model's own emitted markdown
rather than re-serialized DOM. Text stashed on `window`, never returned through
the tool channel.

The tab was `visibilityState=hidden` and `hasFocus()=false`, and the Edge window
could not be given OS foreground (`SetForegroundWindow` returned, but
`GetForegroundWindow()` never matched). The Skill's prescribed mechanism was used
anyway: a full-viewport transparent overlay carrying the copy handler, clicked by
`computer`, then removed immediately.

```text
click 1 at (640, 400)   __hmasd_copy_result = 'no_click_yet'   -- handler never fired
click 2 at (461, 460)   __hmasd_copy_result = 'exec=true'      -- viewport centre
```

The first click reported success and did nothing, which is the recurring failure
this procedure exists for; `document.elementFromPoint` had already confirmed the
overlay was the topmost element at the centre, so the fix was the same place
again at the centre, not different coordinates. Overlay removed and confirmed
absent.

`document.execCommand('copy')` succeeded where `navigator.clipboard.writeText`
would have been refused for lack of transient activation on a hidden tab.

**Fidelity proof, which the clipboard path alone cannot produce.** The page
reported its own emitted source as **22115** characters. The clipboard held
**22546** raw with 431 CR bytes; normalized to LF that is exactly **22115**. Two
independent measurements of the same text agreeing to the character.

The LF round-trip through the Windows clipboard was checked before archiving
(`set_len=22115 readback_len=22115`), because `Set-Clipboard` re-inserting CRLF
would have silently undone the normalization.

`archive_pro_response.ps1`:

```json
{
  "status": "ROUND_ARCHIVE_OK",
  "chars": 22115,
  "chars_reread": 22115,
  "exact_equal": true,
  "stage_commit": "b8652fd97cc7f29b123a343eab7aaa3df3a2bbf2",
  "first_line": "# Scientific ruling — D7.S provenance-correction result",
  "last_line": "**This review selects the scientific repair route. It authorizes neither implementation nor conclusion-bearing compute.**"
}
```

The capture carries THIS round's `stage_commit`, opens with its own heading, and
is 22115 characters -- not the 382-character fence, and not a progress trace.

No `22_PROVISIONAL_CAPTURE.txt` was written: the byte-exact capture succeeded, so
no provisional artifact was created and none needs deleting.

No evidence-access recovery was required. The reviewer read the repository at
`stage_commit` through the connector and cited specific line ranges from the
allow-listed paths.

## Terminal order

```text
exact raw -> provenance intake -> (no heartbeat to delete) -> PM reconciliation
```
