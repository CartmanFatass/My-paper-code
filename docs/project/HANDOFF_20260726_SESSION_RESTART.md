# Handoff — 2026-07-26 session restart (replicate-volume round answered, capture pending)

Successor PM: read this, then `docs/project/CURRENT_WORK.md`. This file is
the restart seam only; delete it once its content is archived and the round
is closed.

## Where things stand

Round `20260726_d7_s_replicate_volume_necessity` is **answered and verified
complete, but not yet archived to the repo**.

- Fence was sent **exactly once** (2026-07-26 19:31, conversation
  `6a63979e-35d8-83e8-8da7-10de59a5fdeb`) and verified. **Never resubmit it.**
- Pro's answer (reasoned 10m28s) passed the full completion protocol: fence
  identity match on all fields, two stable snapshots >3s apart, response
  actions row present, no stop/retry control, composer empty.
- The answer was captured via `Copy response`: **16,744 chars of markdown**,
  head `# Scientific ruling — D7.S replicate-volume necessity` /
  `Stage reviewed: d0b89815563b9e5d907f4a446df8d4a8211c420f`, tail ends
  `**This review amends the scientific contract. It does not itself authorize
  implementation or compute.**`
- It sits on the **Windows clipboard** (volatile) and authoritatively in the
  ChatGPT conversation. The write to
  `docs/external-review/rounds/20260726_d7_s_replicate_volume_necessity/21_PRO_OPEN_RAW.md`
  was interrupted by the user mid-turn; it has **not** been written.

## The ruling (from the verified capture; re-verify against the raw when archived)

Disposition: **MODIFY THE REPLICATE VOLUME; ACCEPT SHARED-PREFIX FORKING; DO
NOT LAUNCH UNTIL THE REVISED DESIGN PASSES THE EIGHT-HOUR COST GATE.**

1. Reject `n_select=1, n_eval=2` for the frozen max-over-z inference.
2. **Freeze the scientific minimum at `n_select=2, n_eval=2`.**
3. Accept one canonical prefix replay + independent full-state continuation
   forks (shared-prefix realization; stream_seed semantics unchanged).
4. The original 4/8 volume is **not** scientifically indispensable; the
   source-necessity predicate itself **is** indispensable — no downscope.
5. Cost evidence does not yet establish that 2/2 fits 8h. Scheduled next
   boundary: refreeze at 2/2 with shared-prefix semantics → Stage-B
   realization-conformance check on the diff → produce the policy-required
   prelaunch cost upper bound → **launch only if that bound ≤ 8h**. If it
   exceeds 8h: stop with `NON_EXECUTABLE_EVIDENCE_DESIGN`, do not substitute
   1/2, do not reinterpret existing evidence, do not advance D7.3 or D8.
6. Smallest refuted unit: only the frozen 4/8 replay-every-prefix realization
   as an executable design on this CPU — not the D7.S predicate, event-aligned
   auditing, topology inference, or the R30 line.
7. Q2 confirmed: the amendment is ruled in this round; the contract refreezes
   on this answer — no separate freeze round.

## Immediate next actions, in order

1. **Archive**: if the clipboard still starts with
   `# Scientific ruling — D7.S replicate-volume necessity`, write it byte-exact
   to `21_PRO_OPEN_RAW.md` and byte-verify by reread. If the clipboard is
   lost, re-capture from the conversation (gotchas below) — the answer is safe
   server-side.
2. Write `50_MECHANICAL_INTAKE_RECORD.md` (provenance: sent 19:31, captured
   ~21:25 after Chrome outage 19:53–~21:15, Copy-response path, sentinel
   check) and `30_PM_SCIENTIFIC_RECONCILIATION.md`. Commit + push.
3. Amend `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md` Section 8
   constants to n_select=2/n_eval=2 and add the shared-prefix realization
   note; record the refreeze (per Q2, no new round needed).
4. Dispatch `hmasd-implementer` for the shared-prefix realization in
   `scripts/audit_d7_s_event_aligned.py`; PM diff-read + tests; **Stage B
   diff is mandatory here** (Pro ruling names it).
5. Produce the prelaunch cost upper bound (zero-compute, from the measured
   0.10–0.30 s/step model at 2/2 + shared prefix). ≤8h → compute-gate check,
   launch by-topology shards under `logs/`, pool with
   `scripts/pool_d7_s_event_aligned_shards.py`. >8h →
   `NON_EXECUTABLE_EVIDENCE_DESIGN`, report to user.
6. Update `CURRENT_WORK.md` and write the iteration report (zh-CN) with the
   mandatory time-distribution table.

## Transport gotchas learned this session (browser work)

- The browser is **Edge** (`msedge`, pid was 20276), not Chrome, despite the
  tool names.
- Clipboard writes from the page **fail silently unless the browser window has
  OS foreground focus**. Fix: `SetForegroundWindow` on the Edge main window
  via P/Invoke, then click.
- `find` for "Copy response" matched the **previous** assistant turn's button
  (and its description claimed otherwise). Verify by screenshot that the
  actions row you click belongs to the tail of the current answer (scroll End
  first).
- The tab wedges intermittently on this large conversation (screenshot CDP
  timeouts); one reload + ~8s wait recovers it. Ladder: reload ×2, then
  replace the tab (exactly one tab on the conversation afterwards).
- `get_page_text` truncates at 50KB of ~65KB — the newest turns are cut off;
  never conclude absence from it. Never click `Answer now`.

## Process defect acknowledged this session

After the fence landed, the PM held the wait itself instead of dispatching
`hmasd-review-monitor`; the user called this out. The rule going forward: the
moment send-verification passes, the monitor owns the wait (memory:
`dispatch-review-monitor-immediately-after-fence`). During a browser outage
the monitor cannot run either — say so explicitly instead of silently
heartbeating.

## Session mechanics

The /loop driver died with the old session. The overnight grant
(`iterations_remaining=17`) and all authority live in `CURRENT_WORK.md`, not
in the driver. Support work on this round consumes no iteration.
