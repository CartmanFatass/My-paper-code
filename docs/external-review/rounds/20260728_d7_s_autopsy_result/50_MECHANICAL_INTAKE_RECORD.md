# Mechanical intake record — transport facts only

No scientific quality classification here. The reconciliation is
`30_PM_SCIENTIFIC_RECONCILIATION.md`.

```text
round         = 20260728_d7_s_autopsy_result
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = 6430ef968498bf8be0533cb27eb865cecba8a519
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, claude_in_chrome
touchpoint    = 3 of 3 -- the result submission, which opens the next workflow
```

## Preflight

`ROUND_PREFLIGHT_READY`, nine-path allow-list, fence artifact present,
`archive_build=REVIEW_EVIDENCE_ARCHIVE_READY`.

## Fence

Committed artifact `10_FENCE.txt`, clipboard round-trip verified `-ceq`, pasted
in one operation, submitted once. Send verified mechanically: composer empty, new
user turn carrying every fence field, `Stop answering` active. Exactly one fence.

An `Answer now` control was visible during generation and was **not** operated —
curtailing extended thinking is forbidden.

## Wait

Paced by the Project Manager. Two `hmasd-review-monitor` inspections: the first
reported the stop control active with a progress trace naming this round's own
subject matter ("Resolved aggregation semantics"); the second could not read the
page and said so plainly rather than inventing a state.

## Transport faults and recovery

The tab wedged **twice** during this round — the fourth and fifth wedges of the
session, all on this same conversation.

```text
RECOVERY_ATTEMPT
attempt=1
boundary=fence submission
action=two reloads of the same tab, each followed by a wait; second reload
       landed on the signed-in home page and a find timed out there
outcome=wedge survived both reloads
```

```text
RECOVERY_ATTEMPT
attempt=2
boundary=same
action=bounded replacement -- closed the wedged tab, created one, navigated
outcome=rendered immediately; fence submitted from the replacement
```

```text
RECOVERY_ATTEMPT
attempt=3
boundary=reading the completed answer
action=monitor read timed out at document_idle; bounded replacement again
outcome=rendered immediately, answer complete and readable
```

**The pattern is now consistent enough to state as a property rather than luck:**
this conversation holds five large reviewer answers, every wedge survived its
reloads, and every replacement tab rendered on the first try. That is the
documented accumulated-renderer-state signature. Exactly one tab held the
conversation at every point.

## Capture

`Copy response`, coordinate click from a screenshot, clipboard sentinel set
first. Captured on the second click, using the same neutral-body-click-for-focus
step that worked in the previous two rounds — the failure mode and its fix are
now stable across three rounds.

No prohibited capture path: nothing retyped, no `get_page_text`/`read_page`
output treated as the archive, no JSON round-trip.

### Sanity checks, all passed

- carries **this round's own** `stage_commit` `6430ef96…` in its body;
- opens `# Scientific ruling — D7.S normalizer autopsy result` and addresses all
  five required response sections by name;
- 22265 characters, plausible for a scoped scientific answer;
- first and last lines match the screen.

### Archival

`.NET WriteAllText` (UTF-8, no BOM) from the clipboard; reread `EXACT_EQUAL=True`
at 22265 characters both ways.

## Preserved as received

LaTeX is mangled by transmission — display math renders as `[ ... ]`, subscripts
appear as `B_{\mathrm{stable}}`, and `=` runs stand where equations were. One
heading in section 3 was absorbed into a code fence. Preserved exactly and not
repaired; no quantity was illegible.

## Heartbeat

None created, so none to delete. Waiting was in-band.
