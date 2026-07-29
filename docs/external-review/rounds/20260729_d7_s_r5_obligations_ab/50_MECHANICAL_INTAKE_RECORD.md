# Mechanical intake — transport facts only

No scientific classification here.

```text
round         20260729_d7_s_r5_obligations_ab
stage_commit  59a221d80bd5d6af6c9459140c46e1cb64e57806
branch        untied-k
reviewer      open_divergent (registered), conversation 6a63979e-35d8-83e8-8da7-10de59a5fdeb
preflight     ROUND_PREFLIGHT_READY, allow_list_count=7, archive REVIEW_EVIDENCE_ARCHIVE_READY
fence_sent    YES (once)
status        REVIEW_PENDING
```

Fence absence proved before sending: the page carried neither `59a221d8` nor the
round id. Sent once. Verification: exactly one user turn carries `59a221d8`.

## Two learned procedures applied, and they worked

**The clipboard verify was given a settle before comparing.** 377 chars,
`exact=True` first time. The previous round's spurious `exact=False` was the
check racing its own write, not a corrupt artifact.

**The send used the paths that survive a hidden tab.** `document.visibilityState`
was `hidden` throughout — the window is not foregrounded — so `find`, `screenshot`
and any clipboard *read* by the page would have failed. OS-level `ctrl+v` and
`Return` do not care, and both worked. No reload was spent, and no wedge
diagnosis was attempted, because visibility was checked first.

**The composer again kept its text after a successful send** (382 chars, with
exactly one user turn carrying the commit). Same artifact as the previous round.
Cleared with `ctrl+a` + `Delete`, never a second `Return`, and re-read as empty.
This is now the expected behaviour on this page rather than a surprise.

## Capture plan for this round

The API path proven last round is the primary, not the fallback: from page
context, `/api/auth/session` for the token, then `/backend-api/conversation/<id>`,
then the last assistant message's `content.parts`. It returns the model's own
emitted markdown, needs neither focus nor visibility, and last round produced a
file byte-identical to the page's own source string.

A provisional capture is taken the moment generation stops, before anything else,
per the Skill's step zero.
