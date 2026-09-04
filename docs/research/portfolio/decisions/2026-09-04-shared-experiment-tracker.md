# Shared experiment-tracking sibling

Date: 2026-09-04
Provenance: `OWNER_DIRECT`

The owner requested:

> 我们需要一个专用的luna-xhigh subagent来做各个方向实验的进程持有和追踪, 其应该通过sibling直接和各个DM交流 DM按需发派任务 sibing负责记录 追踪 提醒

Root installs `hmasd-experiment-tracker`, model `gpt-5.6-luna`, effort `xhigh`, and creates one
root-level sibling named `tracker_lxh_experiments`. DMs assign accepted experiment handles directly
to it; it reports terminal status, observation loss, or requested reminders directly to that DM.
Routine observation no longer occupies each DM/CM. Existing detached tasks retain their supervisor
and run identity. This change does not launch, stop, retry or migrate an experiment.

The tracker alone writes `docs/research/portfolio/EXPERIMENT_TRACKING.md` in an isolated worktree.
It retains task/node/SHA/cwd/artifact references, observation and notification state, and links the
DM's existing run records. Root integrates meaningful commits and restores the tracker through the
existing 30-minute research heartbeat. The tracker adds no direction slot or admission condition.
CM/Operator owns launch, collection, verification and technical repair; DM owns scientific intake.
Duplicate handoffs reconnect to the same accepted handle. Idle DMs are resumed with direct sibling
followup; unavailable DMs are reported once to Root for restoration.

The runtime may need a later session to expose a newly registered custom role. For this live tree,
Root creates the same tracker using the default native agent with the explicit owner-requested
model/effort and the installed role instructions. Future sessions can select the registered role.
No other agent's model is changed. Existing user model edits in the saved project are preserved.

## Live validation and remaining limitation

The Luna/xhigh tracker successfully adopted same-handle process observations and committed its
tracking table. This live runtime did not expose native outbound sibling tools to that agent.
Its app task-message attempt was rejected with
`direct app-server input is not allowed for multi-agent v2 sub-agents`; that path is not retried or
bypassed. A Root attempt to select the newly registered role returned `unknown agent_type` in this
already-running turn. Configuration registration alone has therefore not proved direct delivery.

Root delivered the initial CBSC/FRRIE terminal notifications and FSD adoption ACK through Root's
native collaboration tools so scientific work could continue. The direct-sibling requirement is
explicitly **not yet complete**. The next fresh Root runtime/configuration load should test native
outbound capability once before claiming it works. If absent, report the limitation immediately,
retain bounded tracker observations and required Root delivery, and avoid repeated transport
workarounds. No experiment is duplicated or blocked by this communication limitation.

Scope: owner-requested native process observation and coordination; no new runtime machinery.
