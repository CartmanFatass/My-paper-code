# Mechanical intake record -- transport facts only

No scientific classification; that is `30_PM_SCIENTIFIC_RECONCILIATION.md`.

```text
round         = 20260730_d7_s_manifest_replay_gate_result
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = a666b86caab06990d931ae346b637617ad6993c1
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
touchpoint    = 3 of 3
model_ui      = gpt-5-6-pro   (expected_model_ui = Pro)
message_id    = 8f021a73-d670-4e95-8637-c4143b52aa95
generation    = 13.5 minutes
```

## Preflight

```json
{
  "status": "ROUND_PREFLIGHT_READY",
  "round": "20260730_d7_s_manifest_replay_gate_result",
  "commit": "a666b86caab06990d931ae346b637617ad6993c1",
  "branch": "untied-k",
  "allow_list_count": 10,
  "fence_artifact": "docs/external-review/rounds/20260730_d7_s_manifest_replay_gate_result/10_FENCE.txt",
  "archive_build": "REVIEW_EVIDENCE_ARCHIVE_READY"
}
```

Fence absence proved from the conversation API, never from `find`:
`user_turns=39 exact_fence_hits=0 any_fence_turns=34`. Submission authorized on
`exact_fence_hits=0`.

## Send

Composed with `document.execCommand('insertText')` -- whole text in one operation,
zero Enter keypresses -- and read back against the committed artifact BEFORE
sending:

```text
paragraphs                     7
joined with '\n'               396 chars
byte-exact vs 10_FENCE.txt     True
```

**`innerText` reported 402, and that is a reader artifact, not a defect.** The
composer wraps each line in its own `<p>` and `innerText` emits a blank line
between paragraphs -- 6 extra newlines for 6 line breaks. Reading the paragraphs'
`textContent` and joining with a single `\n` reproduces the artifact exactly. A
length check against `innerText` alone would have failed a correct compose.

Sent once via the page's own send control. Verified mechanically:

```text
rendered      exactly one user turn carrying the stage_commit; composer empty
conversation  user_turns 39 -> 40, exact_fence_hits 0 -> 1
```

## Capture

```json
{
  "status": "ROUND_ARCHIVE_OK",
  "chars": 19708,
  "chars_reread": 19708,
  "exact_equal": true,
  "stage_commit": "a666b86caab06990d931ae346b637617ad6993c1",
  "first_line": "# Scientific ruling — D7.S manifest-replay gate result",
  "last_line": "**The current gate remains failed. The manifest must not yet be wired into a conclusion-bearing path. No confirmatory population or formal compute is authorized.**"
}
```

**Fidelity proof, stronger than the procedure requires.** The page computed
SHA-256 over its own emitted markdown; PowerShell computed SHA-256 over the
LF-normalized clipboard:

```text
page  len_chars=19708  len_bytes=19944  sha256=213e0fbd12755050c2872431f06310401257362f26cbe5ee1c7b10f30e027ea4
clip  raw_len=20172    lf_len=19708     sha256=213e0fbd12755050c2872431f06310401257362f26cbe5ee1c7b10f30e027ea4
```

A length match can be satisfied by a substitution; a digest match cannot. The 464
CR bytes are the clipboard's transport encoding and were normalized before
archiving; the LF round-trip through `Set-Clipboard` was then re-checked
(`19708 -> 19708`), because a silent CRLF reinsertion would have undone it.

No `22_PROVISIONAL_CAPTURE.txt` was written and none needs deleting. No heartbeat
was created, so there is none to delete -- pacing was one in-band background timer.

## Transport faults

Three, all recorded because they worked or because the next reader will hit them.

```text
FAULT 1  the composer STILL HELD THE DRAFT after the send fired
         Cleared immediately. This is how a duplicate fence gets sent. The
         previous round did not exhibit it, so an emptied composer must not be
         assumed from the send having succeeded.

FAULT 2  heavy `await fetch` to /backend-api/conversation/ timed out
         Runtime.evaluate at 45 s, repeatedly. Light DOM reads answered instantly
         throughout, so the page was alive. Firing the fetch unawaited and polling
         a window slot with light reads did NOT help -- the slot stayed 'pending'
         through 30 s. What DID work: reloading the tab. Every successful API read
         this round happened immediately after a `navigate` to the registered URL.

FAULT 3  the Skill's overlay-click gesture FAILED, twice
         __hmasd_copy_result stayed 'no_click_yet' on both clicks.
         document.elementFromPoint confirmed the overlay was topmost at the click
         point and document.hasFocus() was true, so this was not a coordinate
         error. The only observed difference from the previous round, where the
         same mechanism worked on its second click: screenshot space (1568x744)
         and viewport space (1912x907) differ this round where they were 1:1
         before. NOT established as the cause.
```

### The mechanism that did work, which is not in the Skill

Append a hidden `<textarea>` carrying the emitted markdown, focus it,
`setSelectionRange` over its whole value, then send a **real `ctrl+c` keypress**
via `computer`. A native keyboard copy needs neither the async-clipboard
permission nor transient activation, and it succeeded on the first attempt.

It preserves both constraints the Skill actually cares about -- the bytes are the
model's own emitted markdown rather than re-serialized DOM, and nothing is
transcribed by hand -- and it produced a stronger fidelity proof than the overlay
path can, because the same string is digestible on both sides of the boundary.

Both the overlay and the temporary textarea were removed and their absence
confirmed.

## Evidence access

No recovery required. The reviewer read the repository at `stage_commit` through
the connector and cited specific line ranges from the allow-listed paths,
including `envs/pettingzoo/scenario7_energy_aware.py`.

## Terminal order

```text
exact raw -> provenance intake -> (no heartbeat to delete) -> PM reconciliation
```
