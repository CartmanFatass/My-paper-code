# Mechanical intake record — transport facts only

No scientific quality classification appears here. The reconciliation is
`30_PM_SCIENTIFIC_RECONCILIATION.md`.

```text
round         = 20260727_d7_s_audit_2_result_disposition
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = 76c1ce328b57191f7a1c6f873684de041d12bbc3
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
model_ui      = Pro (verified in the composer's model selector before submission)
```

## Preflight

`preflight_review_round.ps1` returned `ROUND_PREFLIGHT_READY` at the commit
above, with an eight-path allow-list, the fence artifact present, and
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Fence

Composed as the committed artifact `10_FENCE.txt` and pasted in one clipboard
operation; `Set-Clipboard` round-trip verified `-ceq` before pasting, so no
`type` action delivered a newline. Submitted once.

Send verified mechanically rather than by inference: after the click the
composer was empty (placeholder `Follow up`), a new user turn appeared at the
tail carrying every fence field verbatim, and a `Stop answering` control was
active. Exactly one fence for this round exists in the conversation.

## Wait

Paced by the Project Manager. `hmasd-review-monitor` performed two bounded
inspections and reported page state only; it holds no tool that can wait and was
never asked for elapsed time.

- Inspection 1 — stop control present and active; content a progress trace
  (`Answer now`, `Clarifying file search`, `Pro thinking`).
- Inspection 2 — stop control absent; `Worked for 10m 54s` visible; response
  body not extractable, page reported an anomaly.

## Transport fault and recovery — a wedged tab

```text
RECOVERY_ATTEMPT
attempt=1
boundary=page read after generation stopped
action=script-injecting operations (screenshot, read_page) timed out at document_idle
outcome=tab unusable; `Script injection timed out after 5000ms`
```

```text
RECOVERY_ATTEMPT
attempt=2
boundary=same
action=one reload of the SAME tab, then an 8s wait
outcome=recovered; full transcript rendered. No tab was created and none closed,
        so exactly one tab held the conversation throughout.
```

The bounded replacement path (close and recreate) was **not** needed — the
ordinary hydration case cleared on the first reload.

## Capture

`Copy response` control, clicked by coordinate from a screenshot. The clipboard
was set to a sentinel first, so a click that wrote nothing was detectable.

```text
RECOVERY_ATTEMPT
attempt=3
boundary=clipboard capture
action=three coordinate clicks on Copy response
outcome=clipboard unchanged from sentinel on all three. Zoom confirmed the
        cursor was on the control and it was hovered, so the coordinates were
        right and the clipboard write was what failed. The copied-state icon
        never appeared.
```

```text
RECOVERY_ATTEMPT
attempt=4
boundary=clipboard capture
action=one click on neutral page body to take document focus, then one further
        coordinate click on the same control
outcome=captured, 16691 characters
```

No prohibited capture path was used: nothing was retyped, `get_page_text` /
`read_page` output was never treated as the archive, and no JSON round-trip
occurred.

### Capture sanity checks, all passed

- carries **this round's own** `stage_commit` `76c1ce32…` in its own body — the
  only check that catches a capture of the wrong round;
- opens `# D7.S audit run 2 — scientific disposition` and addresses the six
  required response sections by name, so it is not a progress trace;
- 16691 characters, plausible for a scoped scientific answer on this line;
- first and last lines match what was on screen.

### Archival

Written with `.NET WriteAllText` (UTF-8, no BOM) directly from the clipboard,
then reread: `EXACT_EQUAL=True` at 16691 characters both ways.

## Preserved as received

The response's LaTeX is mangled by transmission — display math renders as
`[ ... ]`, subscripts appear as `B*{\mathrm{stable}}`, and several `=` runs
appear where the source had an equation. Two headings were absorbed into a
blockquote in section 4. **This is preserved exactly as received and is not
repaired.** The numbers and the prose are unambiguous throughout; no quantity in
the ruling was illegible.

## Heartbeat

None was created for this round, so none required deletion. Waiting was done
in-band by the Project Manager, with the monitor dispatched for bounded
inspections.
