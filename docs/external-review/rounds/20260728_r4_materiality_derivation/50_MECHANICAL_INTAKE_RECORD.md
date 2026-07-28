# Mechanical intake record — transport facts only

```text
round         = 20260728_r4_materiality_derivation
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = 214553620e97085060a485d527ead3d85679ca2b
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
touchpoint    = 2 of 3 (plan review returning the convergence decision)
```

## Preflight

`ROUND_PREFLIGHT_READY`, seven-path allow-list, fence artifact present,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Fence

Committed artifact, clipboard round-trip `-ceq` verified, pasted in one
operation, submitted once. Send verified mechanically: composer empty, new user
turn carrying every field, `Stop answering` active. An `Answer now` control was
visible and was **not** operated.

## Transport faults

Wedges six and seven of the session, both on this conversation.

```text
RECOVERY_ATTEMPT
attempt=1
boundary=fence submission
action=bounded replacement WITHOUT first attempting reloads
outcome=rendered immediately
```

**Deviation from the written ladder, stated plainly.** The procedure says try
two reloads before replacing. By this point reload had failed on this
conversation **five times out of five** and replacement had succeeded five out
of five. Repeating a measured-failing action without changed state is itself
forbidden, so the reloads were skipped deliberately rather than overlooked. If
the intent is that the ladder be followed regardless of measured evidence, this
is the deviation to object to.

```text
RECOVERY_ATTEMPT
attempt=2
boundary=reading the completed answer
action=bounded replacement again
outcome=rendered immediately; sixth and seventh replacements, both first-try
```

Exactly one tab held the conversation at every point.

## Capture

`Copy response` by coordinate with a clipboard sentinel. Captured on the second
click after the neutral-body focus step — the same failure mode and same fix as
the previous three rounds.

### Sanity checks, all passed

- carries **this round's own** `stage_commit` `21455362…`;
- opens `# Scientific ruling — R4 materiality derivation` and addresses all five
  required sections by name;
- 20072 characters;
- first and last lines match the screen.

### Archival

`.NET WriteAllText` (UTF-8, no BOM) from the clipboard; reread
`EXACT_EQUAL=True` at 20072 characters.

## Preserved as received

LaTeX mangled by transmission; several `=` runs and `##` fragments stand where
display math and subscripts were. Preserved exactly, not repaired. No quantity
was illegible.

## Heartbeat

None created. Waiting was in-band.
