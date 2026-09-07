# VSP03 B02 transport observation intake — 2026-09-06

**No B02 direction decision is formed.** The current return is a transport observation mismatch,
not an experiment, a negative B result, or permission to select a successor locally. The fixed
N1 update-128 comparison remains paused and B02 remains a proposal.

## What was checked

This intake reads the actual current registry, the four raw mismatch artifacts, the accepted
B02 handoff, the immutable B01 archive/source, and current GitHub response/branch/Issue state.
Raw current artifacts are preserved under
`pro_packets/20260906_shared_service_convergence/archive/blocker_20260906/`; their observed bytes
and narrow comparisons are in `READBACK_CHECK.json`. The `MISMATCH_CHAT_CAPTURE.md` in that folder
is a short captured chat text, **not** the reserved full B02 `archive/RESPONSE.md`.

The controlling Transport rule says, verbatim: **“Never retry an uncertain or mismatched send,
never open a second conversation, and never silently alter whitespace, file selection,
reference order, or prompt text.”** Its identity rule additionally says to capture the assistant
paired with the request's recorded user message, rather than an unscoped first/last Copy control.
The question is therefore whether these observations belong to a new B02 Send at all.

| Surface read directly | Actual fact | Limit |
| --- | --- | --- |
| Current `registry.json` binding and `directions.vsp_03` mirror | Both still name archived B01 and conversation `6a9cbb9d-374c-83e8-b600-23d3a8033a69`. | The full current registry contains no `6a9cbb9d-3748` substring. A different old source was not supplied. |
| Immutable B01 `TRANSPORT_FACTS.json`, `ARCHIVE_CHECK.json`, and accepted B02 `HANDOFF.json` | They all contain the same exact `374c` conversation string. | No binding typo is established by these files. |
| New mismatch facts | User `fcd86924-8fcd-44b5-9b46-286cd45a2775` and assistant `b3da52fb-a05b-48db-b769-6bed3e6fe858` repeat the exact B01 IDs. `observed_user_task_url` is old TASK `4c2ec9a2...`. | Their presence proves an old user node was observed, not that B02 was sent. |
| New archived `__00_PROMPT.md` | Its body equals the old B01 prompt after removing only final line endings. It does not equal B02's expected TASK `e7a83daab...` prompt. | The file is 558 bytes; the manifest says 557 and hashes the old text plus LF. Actual bytes end with CRLF. Both representations are preserved, not silently repaired. |
| New captured reply | The text links CBSC response commit `d3222ccb53f4986320f0015960ea997dccd8e856` and Issue 7. | This is unrelated to B02. The cause of that capture/ID disagreement is unestablished. |
| New facts' Send fields | `provider_send_observed=true`, but `named_request_send_confirmed=false`. | The first field cannot establish a new Send when its recorded user ID/task is B01. It is not a new B02 accepted-send receipt. |
| GitHub B02 output read | Response path returns 404, output branch still points at science base `585fe948cdbde4fdb3c2fcf658cd02d848ba5c5f`, Issue 6 contains only B01 delivery and the DM B02 proposal. | No formed B02 file exists at the checked scope; absence of a file alone does not prove no Send attempt. |

The current archive's original classification `SENT_INPUT_MISMATCH` is retained unchanged as
Transport's report. My narrower reading is **new-request Send unestablished; observed old-input /
unrelated-capture mismatch**. No scientific polarity follows from either label.

## Historical evidence and receipt routing

The full historical B01 response at immutable commit
`8a02f09d2ed5693e9f150ba5d0243bdc0e6eee98` was fetched directly again for this concrete identity
question. It remains exactly the 24,870-byte archived file, SHA256
`8005eef870cca1928f9928b48a83ebe63cd08a14c1b9a82229018198431021b8`, Git blob
`6f254f2f524e7473f32e74a1d080f9d713e9f7d6`. The historical raw prompt, short VSP03 receipt,
transport facts and manifest also still equal their original local source bytes.
That complete scoped GitHub decision is not replaced by today's CBSC chat capture. Its accepted
pause and the original experimental observations remain in force. Current message association
needs reconciliation; this intake does not invent a cause or retroactively rewrite provenance.

The B02 author used native backing task `01a079ca-7587-7401-a419-06c482129f9a` as both source
and parent, incorrectly identifying it as Root. Root supplied the actual receipt destination,
`01a07249-b095-7821-8ce2-e9c32ba85267`, and sent a routing-only correction to the singleton.
Current Transport facts and the delivered terminal-blocker receipt use that correct Root.
The accepted handoff and TASK stay unchanged; this paragraph corrects the earlier `BOUNDARY.md`
interpretation without pretending the original metadata were right.

## Decisions this intake produces

No new object or direction selection is produced. Direction-tier options remain selecting the
proposed coupled B, maintaining the pause without a successor, or a concrete amended question;
only a complete conforming direction-node decision can select among them here. No recast count,
Portfolio action, implementation assignment or experimental result is inferred from this return.

The useful next technical action is one bounded read-only reconciliation by the same existing
Transport executor. The DM has sent that follow-up: establish its actual B02 provider Send-attempt
history; inspect the exact persisted URL and the old user's directly paired assistant content;
look for the exact B02 TASK in the history actually available; and identify any source behind the
claimed `3748` string. The instruction forbids paste, Send, repair prompts, binding mutation and
new conversations, and requires new evidence alongside the untouched original capture. It is a
technical follow-up, not a regenerated scientific request or another provider dispatch.

If actual action records establish that **no B02 Send was attempted**, normal serial admission of
the unchanged request on the already bound conversation can be reconsidered as a first Send;
absence of an output or the old node alone is insufficient. If an attempt remains uncertain,
preserve that uncertainty and do not resend. If a new exact user node is found, observe that same
request and its paired response without another Send. This intake does not yet select one of
these cases, because the requested action/DOM reconciliation is outstanding.

Automated context replacement is not currently available: the replacement reference requires an
immediately previous archived non-decision/blocker with exactly zero repository paths read and
acknowledged contamination traced to a named prompt defect. Those facts are not established;
the last accepted B01 decision was formed and read its declared evidence. A wrong chat capture,
an unconfirmed new Send or a copied UUID allegation does not satisfy that rule. No new provider
ID, owner reply or reset authority is invented.

Exposure remains zero: no new models, training seeds, environment episodes, optimizer steps or
evaluations. The proposed 120-second B budget remains unexecuted. This is documentary evidence
and request recovery only; it creates no runtime machinery or changed scientific contract.
