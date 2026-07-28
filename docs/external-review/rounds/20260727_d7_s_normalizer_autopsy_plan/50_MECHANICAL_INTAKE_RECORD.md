# Mechanical intake record — transport facts only

No scientific quality classification here. The reconciliation is
`30_PM_SCIENTIFIC_RECONCILIATION.md`.

```text
round         = 20260727_d7_s_normalizer_autopsy_plan
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = f1d79b17334e485708e4a457701c808605a08c7b
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
touchpoint    = 2 of 3 (plan review returning the convergence decision)
```

## Preflight

`ROUND_PREFLIGHT_READY` at the commit above; eight-path allow-list; fence
artifact present; `archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Fence

Composed as committed artifact `10_FENCE.txt`, clipboard round-trip verified
`-ceq`, pasted in one operation, submitted once. Send verified mechanically:
composer empty, new user turn carrying every fence field, `Stop answering`
active. Exactly one fence for this round exists.

## Wait

Paced by the Project Manager. One `hmasd-review-monitor` inspection reported the
stop control active and a progress trace naming this round's own subject matter.

## Transport faults and recovery

```text
RECOVERY_ATTEMPT
attempt=1
boundary=page read during generation
action=three screenshots across two 10s waits
outcome=all timed out at document_idle; not yet distinguishable from a busy
        renderer during heavy streaming, so no reload was issued yet
```

```text
RECOVERY_ATTEMPT
attempt=2
boundary=same
action=two reloads of the same tab, each followed by a wait
outcome=timeouts survived both -- this is the wedged signature, not busy-ness
```

```text
RECOVERY_ATTEMPT
attempt=3
boundary=same
action=bounded replacement -- closed the wedged tab, created one, navigated to
        the registered URL
outcome=redirected to the signed-in home page
```

```text
RECOVERY_ATTEMPT
attempt=4
boundary=conversation discovery
action=conversation discovery ladder -- located the sidebar link and confirmed
        its href contained the registered conversation id before selecting it
outcome=correct conversation opened. Selection was by ID, never by title
```

```text
RECOVERY_ATTEMPT
attempt=5
boundary=empty content pane
action=composer present, no message-role containers after two waits; one reload
outcome=full transcript rendered, answer complete
```

**Second wedge of the session.** Both occurred on this conversation, which now
holds three very large reviewer answers. The replacement tab rendered
immediately both times, which is the documented signature of accumulated
renderer state rather than a page or network fault. Exactly one tab held the
conversation at every point; no duplicate was ever open.

## Capture

`Copy response`, clicked by coordinate from a screenshot, clipboard set to a
sentinel first.

```text
RECOVERY_ATTEMPT
attempt=6
boundary=clipboard capture
action=two coordinate clicks, then one neutral-body click to take document focus
        followed by two further clicks on the control
outcome=captured on the fourth click of the control, 22040 characters. A zoom
        confirmed the Copy response tooltip was showing throughout, proving the
        coordinates were right and the clipboard write was what failed
```

Same failure mode and same fix as the previous round. No prohibited capture path
was used: nothing retyped, no `get_page_text`/`read_page` output treated as the
archive, no JSON round-trip.

### Sanity checks, all passed

- carries **this round's own** `stage_commit` `f1d79b17…` in its body — the check
  that catches a wrong-round capture;
- opens `# Scientific convergence ruling — D7.S normalizer autopsy plan` and
  addresses all six required response sections by name;
- 22040 characters, plausible for a scoped scientific answer;
- first and last lines match the screen.

### Archival

`.NET WriteAllText` (UTF-8, no BOM) from the clipboard; reread `EXACT_EQUAL=True`
at 22040 characters both ways.

## Preserved as received

LaTeX is mangled by transmission — display math renders as `[ ... ]`, subscripts
appear as `U^**{\mathrm{stable}}`, and `=` runs stand where equations were.
Preserved exactly and not repaired. No quantity in the ruling was illegible.

## Heartbeat

None created, so none to delete. Waiting was in-band.
