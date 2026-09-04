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

For this live tree, Root created a temporary tracker using the default native agent with the
explicit owner-requested model/effort and the role instructions. This is not evidence that a
custom-role instance was loaded. The configured custom role must be selected by its file's name
when the runtime exposes it; current discovery failures do not establish a reload mechanism.
No other agent's model is changed. Existing user model edits in the saved project are preserved.

## Live validation and remaining limitation

The temporary default Luna/xhigh tracker successfully adopted same-handle process observations and
committed its tracking table. That agent's top-level tool context did not expose native outbound
sibling tools; this is not a finding about all custom agents or all Luna runtimes.
Its app task-message attempt was rejected with
`direct app-server input is not allowed for multi-agent v2 sub-agents`; that path is not retried or
bypassed. A Root attempt to select the newly registered role returned `unknown agent_type` in this
already-running turn. Configuration registration alone has therefore not proved direct delivery.

Root delivered the initial CBSC/FRRIE terminal notifications and FSD adoption ACK through Root's
native collaboration tools so scientific work could continue. The direct-sibling requirement is
explicitly **not yet complete for the Luna tracker**. Select the custom role when exposed and test
native outbound capability once before claiming it works. If absent, report the limitation immediately,
retain bounded tracker observations and required Root delivery, and avoid repeated transport
workarounds. No experiment is duplicated or blocked by this communication limitation.

## Owner follow-up: installed role and verified sibling guide

The owner explicitly requested the custom role, both local and remote instructions, and a docs
guide after confirming sibling use. The role now separates remote agent-task supervision from
local detached process identity and private tool-session access. It explicitly enables the
documented agents.enabled setting and points at the native guide; this is configuration, not a
claim that a missing tool has become available.

Root verified two peer roundtrips between the existing FSD and CRTO custom DMs: direct
send_message with an actual returned ACK, then followup_task waking the idle FSD DM with an ACK
received by CRTO. Root forwarded neither test message. The independently reported calls and the
default tracker limitation are recorded in
[SIBLING_COMMUNICATION.md](../../../project/SIBLING_COMMUNICATION.md), together with official
configuration references and the exact native invocation boundaries. No research process changed
because of these communication probes.

Scope: owner-requested native process observation and coordination; no new runtime machinery.
