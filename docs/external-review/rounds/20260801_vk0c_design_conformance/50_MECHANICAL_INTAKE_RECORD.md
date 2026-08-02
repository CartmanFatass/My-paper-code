# Mechanical intake record — transport facts only

```text
round         = 20260801_vk0c_design_conformance
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = 060a86d9181be1f2721d693fd30a84a2f27affcb
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, agentify
operation_key = mypaper-open-divergent-untied-k-20260801-w7tp2-r1
receipt_sha256 = 51600a973ed827ce9a917da366c798a23abb502d9b3ba0bb20b4e30a1615e88b
touchpoint    = 2 of 3
```

## Preflight

Printed `ROUND_PREFLIGHT_READY` before fence dispatch; re-executed at intake
time with identical result:

```json
{
  "status": "ROUND_PREFLIGHT_READY",
  "round": "20260801_vk0c_design_conformance",
  "commit": "060a86d9181be1f2721d693fd30a84a2f27affcb",
  "branch": "untied-k",
  "question": "docs/external-review/rounds/20260801_vk0c_design_conformance/20_PRO_OPEN_QUESTION.md",
  "allow_list_count": 8,
  "fence_artifact": "docs/external-review/rounds/20260801_vk0c_design_conformance/10_FENCE.txt",
  "archive_build": "REVIEW_EVIDENCE_ARCHIVE_READY"
}
```

## Capture

Fence (r1), archived `21_PRO_OPEN_RAW.md`, digest bond OK:

```json
{
  "status": "ROUND_ARCHIVE_OK",
  "chars": 18280,
  "response_sha256": "51600a973ed827ce9a917da366c798a23abb502d9b3ba0bb20b4e30a1615e88b",
  "operation_key": "mypaper-open-divergent-untied-k-20260801-w7tp2-r1",
  "terminal_state": "NATURAL_COMPLETION_VERIFIED",
  "stage_commit_cited": false,
  "first_line": "CONFORMANCE",
  "last_line": "After the amendments are entered into VK0C_REALIZATION_DECISION_LEDGER.md, one convergence turn should return to this same touchpoint. This ruling authorizes neither implementation nor execution."
}
```

Convergence turn 1 (c1), archived `22_PRO_CONVERGENCE.md`, digest bond OK
(`chars=43`, sha `10a6e503fd193c87125e7b8fbfd5e85c32e96a8246703843cdd89a3832b1ee91`,
key `…-w7tp2-c1`) — **fragment; see Transport faults F1.**

Convergence turn 2 (c2), archived `22_PRO_CONVERGENCE_2.md`, digest bond OK
(`chars=22`, sha `954c8145aac113f23b84d03bb71afd30c7c73ed03bdad993f9141c072b2666a9`,
key `…-w7tp2-c2`) — **fragment; see Transport faults F2.**

## Transport faults

**F1 — c1 receipt certified a mid-stream fragment as complete.** Receipt
`…-w7tp2-c1` reached `NATURAL_COMPLETION_VERIFIED` 45 bytes into the reply
("CONFORMANCE / CONFORMS — the V-K0C design-con", cut at a token boundary).
Read-only CDP inspection of the reviewer conversation afterwards showed the
same assistant message (id `35c33da9…`) at 10,194 chars — the reply completed
on the page after capture. The archived raw is the receipt-certified fragment
and stands as received; the full page text is diagnostic only, never raw.

**F2 — c2 identical failure mode.** Receipt `…-w7tp2-c2` certified 22 bytes
("CONVERGENCE DECISION —") ~20 s after send, while the message (id
`483397a7…`) was still streaming on the page.

**Root cause (measured, not inferred):** Agentify's completion proof is
(assistant text SHA stable ≥3 s) AND (no stop/continue/retry control
detected). During a GPT-5.6 Pro async-reasoning turn ChatGPT shows **no stop
control anywhere in the document** (verified by read-only DOM enumeration
mid-generation), so any ≥3 s streaming stall after the first tokens satisfies
the proof. Both fragments end at token boundaries; both receipts completed
~17–20 s after send, far below a Pro reasoning turn's minutes-long duration.
The fence (r1) escaped only because its stream never paused ≥3 s.

**Repair (same round):** the in-progress marker that does exist during
generation is a `.streaming-animation` class on the assistant message's
markdown container (present exactly while streaming; verified absent on all
three finished messages and present on the live one).
`~/.agentify-desktop/selectors.override.json` `stopButton` was extended with
`[data-message-author-role="assistant"] .streaming-animation` (all default
branches retained), so `controls.stop` stays true until streaming actually
ends. Applied via app restart (selectors load at startup); recovery is one
further continuation turn (c3) asking Pro to restate the convergence
decision, captured under the repaired detector. The wrapper source is pinned
and untouched (`sourceDirty=false`).

**Also this round, pre-fence:** deterministic HTTP 409
`review_send_control_ambiguous` (count=2) from a "Run code" button in
conversation history matching the default `sendButton` selector; repaired by
the user-approved `selectors.override.json` `sendButton` narrowing plus app
restart. Two operation keys were burned with server-proven no-send before the
fence key `…-w7tp2-r1` succeeded.

`stage_commit_cited=false` on r1 is recorded, not a refusal (the response
addresses the design by content; the browser-era citation check was
downgraded to a recorded field 2026-08-01).

**Resolution (c3).** Convergence turn 3 (`…-w7tp2-c3`, operation
`87a9163c…`) was captured complete under the repaired detector: archived
`22_PRO_CONVERGENCE_3.md`, 6,711 chars, digest bond OK
(sha `14125d4ac53596c4b490fe08f08c190cf14b62aaed285319029886c500f18a48`),
`stage_commit_cited=true`, `NATURAL_COMPLETION_VERIFIED`, `sendCount=1`.
It is the operative convergence decision; the c1/c2 fragments stand as
received with their receipts and are superseded in content by c3. After the
repair restart, a fresh page load showed the c1 and c2 replies complete on
the server side (10,194 / 6,390 chars) — diagnostic confirmation of the
capture race, never raw evidence.

**F3 — pin advance during recovery.** The repair restart came up on
`e9f63674` because the other line had fast-forwarded the shared
agentify-desktop repo (3 commits past `6ed991f9`, Gemini-scoped; ChatGPT
review path verified unchanged by diff). The wrapper refused under the old
pin (`agentify_state_source_identity_mismatch`, watched red), and
`AGENTIFY_REQUIRED_COMMIT` was updated to
`e9f636740bf94d7db260c8817554904cdcb68870` with explicit user approval;
`review_round_contract_test` and the control-plane checker pass. The c3
send used `--allow-tab-creation` (first send for the key in the new server
lifetime, tab registry is in-memory).
