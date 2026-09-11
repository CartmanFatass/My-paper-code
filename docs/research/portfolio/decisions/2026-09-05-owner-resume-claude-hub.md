# Owner resume through the Claude Code research hub

Provenance: `OWNER_DIRECT`, 2026-09-05 21:26 PDT, owner message "ok 我们开始推进科研流程 从handoff开始",
received by the Claude Code Fable session acting as research hub (`AGENTS.md` Appendix B,
`.claude/skills/hmasd-research-hub/SKILL.md`).

## What the instruction changes

- The execution pause recorded in `docs/research/portfolio/HANDOFF_20260905.md` (`OWNER_PAUSED`,
  owner instruction relayed by the Codex Root) is lifted for the Claude loop. New experiments and
  Pro requests may again be selected and dispatched under the existing decision ladder.
- Pro transport for the Claude loop runs through Agentify Desktop and the same scoped GitHub
  delivery, registry and bindings as the Codex Transport; its non-scientific smoke passed earlier
  today (`docs/Claude_docs/experiments/TRANSPORT_SMOKE_AGENTIFY_20260905.md`).
- The Codex research heartbeat stays `PAUSED`; nothing in this record restarts Codex agents. If the
  owner later resumes the Codex loop, the shared registry and the direction documents are the
  hand-back surface, exactly as they were the hand-off surface today.

## What it does not change

No lifecycle, priority, recast count, scientific meaning or evidence polarity of any direction.
Accepted Pro sends with `send_click_count=1` and terminal mismatch states are preserved and never
resent. Prepared-but-unsent work is reactivated only where a direction handoff explicitly reserved
that path for an owner resume.

## Working set selected by the hub (capacity: two directions, owner 2026-09-03 and 2026-09-05)

| Direction | Why now | First step |
| --- | --- | --- |
| `degraded_incumbent_shadow_handover` (N3) | Its direction-tier question is formed, the TASK is published and unchanged, and the DM handoff reserved an exact unsent recovery payload (`2026-09-05-dish-post-b02-convergence-recovery-01`) for reactivation on owner resume into the correct existing conversation. One Send unblocks the direction. | Fresh registry, GitHub and tab reconciliation, then one Send through `hmasd-pro-transport`; the direction parks until the response is archived. |
| `variable_n_fleet_churn` (N2/N7) | `PRO_FINAL` already selected a concrete, cheap successor: a fixed-checkpoint deployment-mode evaluation of the four saved round-64 policies (zero training, 576 episodes, 180 s cap). Nothing waits on Pro. | Freeze the successor card, dispatch `hmasd-cm`, launch detached on `wsl_4070`, intake. |

Queued behind them, in order, with the reason: `vsp_c1` (its Convergence request was misrouted into
the Portfolio conversation and must be re-authored with a new request id into a fresh
`em:vsp_c1:convergence` conversation; it takes the first free slot, typically when N3 parks on its
Send). `vsp_03` and `capability_bound_semantic_currentness` hold a `PRO_FINAL` family pause with no
selected successor; their pending work is integration only, which the hub performs regardless of
the working set. Other `ACTIVE` directions keep their recorded boundaries.

## Integration performed on resume

The five DM handoff chains (VSP03, CBSC, VNFC, VSPC1, N3) and the tracker handoff are cherry-picked
into `main` in the order each handoff lists, without replaying runs or re-integrating composition
commits the handoffs exclude. The resulting `main` commits are listed in the root handoff written
at the end of this session.
