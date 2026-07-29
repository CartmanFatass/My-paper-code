# Mechanical intake — transport facts only

No scientific classification here. This round has **not** been delivered.

```text
round         20260729_d7_s_r4_formal_result
stage_commit  048483a9aa67357f98355715565bd0b4475c4469
branch        untied-k
reviewer      open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
preflight     ROUND_PREFLIGHT_READY, allow_list_count=8, archive REVIEW_EVIDENCE_ARCHIVE_READY
fence_sent    NO
status        REVIEW_TRANSPORT_BLOCKED
recovery_exhausted true
```

## Duplicate-submission risk: NONE

The fence was never composed and never submitted. The clipboard was loaded and
verified byte-exact against `10_FENCE.txt` (375 chars, `-ceq` True), but the
composer was never clicked, no paste was performed, and no send was clicked.
Every browser call in this pass was read-only — `get_page_text`, `screenshot`,
`wait`, `navigate`, `find`, `tabs_close_mcp`.

**A resuming pass must still prove the fence absent before submitting**, exactly
as on a first visit. This record is evidence about this pass, not a licence to
skip that check.

## Attempts

```text
RECOVERY_ATTEMPT attempt=1
boundary=get_page_text and screenshot on tab 507032375 both timed out
action=reload the registered URL in the same tab, wait 10s
outcome=PARTIAL -- screenshot succeeded once. Page showed the correct
  conversation selected, composer present, model "Pro", content pane still
  hydrating with no message-role containers. Wedged again on the next call.

RECOVERY_ATTEMPT attempt=2
boundary=screenshot after hydration wait
action=second reload-and-wait, then `find` for the fence identity
outcome=FAILED -- "Page still loading (executeScript waited 45000ms for
  document_idle)"

RECOVERY_ATTEMPT attempt=3
boundary=every script-injecting operation
action=close the wedged tab per the Skill's bounded replacement procedure
outcome=FAILED -- "The browser is shutting down."

RECOVERY_ATTEMPT attempt=4
boundary=extension not connected
action=restart the registered runtime -- locate and launch Chrome
outcome=FAILED -- `Get-Process chrome` returns nothing, and chrome.exe is
  absent from Program Files, Program Files (x86), LOCALAPPDATA, the
  HKLM App Paths registry entry, the Start Menu shortcuts, and a recursive
  search of every Google directory on the machine.

  Chrome was serving tabs earlier in THIS session, so it either exited and is
  installed somewhere non-standard, or was removed mid-session. Either way the
  runtime cannot be restarted from here, and re-probing is the behaviour the
  browser guidance names as a rabbit hole. Stopped at four attempts.

RECOVERY_ATTEMPT attempt=5
boundary=Chrome absent from this machine
action=`list_connected_browsers` -- the extension can pair with a browser on
  another device, so "no Chrome here" is not the same as "no browser at all"
outcome=FAILED -- returned `[]`. Zero browsers connected to the account.
  This is the definitive check and it closes every remaining avenue: there is
  no browser on this machine and none paired from anywhere else.

DIAGNOSIS
tabs_context_mcp then returned: "Browser extension is not connected."
The earlier timeouts were not the documented wedged-renderer state -- the
browser itself was going down. The two reloads spent on the wrong diagnosis
were correct procedure on the evidence available at the time; the shutdown was
only distinguishable once tab closure was attempted.
```

## Exact resume condition

1. Chrome running with the Claude browser extension connected, signed in to the
   same account as Claude Code.
2. `tabs_context_mcp` returns a tab whose URL contains
   `6a63979e-35d8-83e8-8da7-10de59a5fdeb`, and **exactly one** tab holds it.
3. Re-verify the fence for `stage_commit=048483a9...` is absent from the visible
   user turns.
4. Reload the clipboard from `10_FENCE.txt` with `-Encoding UTF8` and confirm
   `-ceq` before pasting — the clipboard is user-shared state and cannot be
   assumed to have survived.
5. Paste, verify the composer holds the whole fence exactly once, submit once,
   and confirm by the mechanical test: composer empty **and** user-turn count up
   by exactly one.
6. Dispatch `hmasd-review-monitor` only after send-verification passes.

Nothing upstream needs redoing. The question, the fence and the boundary are
pushed and the preflight gate is green at `048483a9`.
