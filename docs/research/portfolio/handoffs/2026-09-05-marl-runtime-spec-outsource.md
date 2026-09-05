# MARL reference-library study dispatch

Task identity: `2026-09-05-marl-runtime-reference-spec`.
Root task: `01a07249-b095-7821-8ce2-e9c32ba85267`.
Status: dispatched; source study and navigation generation in progress, no accepted new spec.

Initial OUTSOURCE_DISPATCH v1: `/root/workflow_lxh_marl_runtime_spec`, native default,
`gpt-5.6-luna` / `xhigh`, fork none, INITIAL. User explicitly chose these settings,
overriding the workflow-outsource skill's Terra/high default. Its isolated worktree is
`C:/Projects/HMASD-worktrees/marl-runtime-spec-20260905`, branch
`codex/marl-runtime-spec-20260905`, baseline `90d6088e1681355014a7406196fd3632c41241be`.

The owner's later instruction explicitly changes the decomposition:

> 这次开源库学习会涉及大量代码输入 让多个Luna max subagent并行完成大部分工作 将涉及到性能的核心代码返回给你即可 你做好orchestrator和规范起草

This supersedes the skill's single-worker default for this task. Root now writes and
integrates the spec; the original worker remains the same agent, responsible only for
the ref-lib root index/AGENTS, manifest and archive aggregation. It no longer reads all
libraries or owns normative drafting. Six native default workers, each explicitly
`gpt-5.6-luna` / `max`, fork none, own distinct source study and navigation overlays:

| Agent under /root/ | Clone under C:/Projects/ref-lib/ | Pinned commit |
| --- | --- | --- |
| scout_lmx_benchmarl_performance | BenchMARL | 65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1 |
| scout_lmx_epymarl_performance | epymarl | cbc38c09588064eab978501d0f12c2cf58fa7fc2 |
| scout_lmx_jaxmarl_performance | JaxMARL | b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9 |
| scout_lmx_marl_lib_performance | MARLlib | 80e9973a430271a93c781d7422133acb1198f84b |
| scout_lmx_mava_performance | Mava | 83f7f0d19d6fdbe07264bb226a64baf8a0b17514 |
| scout_lmx_mappo_performance | on-policy | de66d7a4b23fac2513f56f96f73b3f5cb96695ac |

Each worker may add only local navigation AGENTS in its clone and its own
`ref-lib/reports/<library>/` evidence. Preserve existing upstream AGENTS and source.
Generate root and real relevant module navigation, an index, and recoverable overlay
copies. Return only performance-critical paths, short necessary excerpts, pinned
permalinks, dataflow and limitations to Root. Record licenses. No dependency installation,
training, benchmark execution, upstream commit/push, nested delegation or Pro transport.

The aggregator archives reports into
`docs/research/portfolio/pro_packets/20260905_marl_runtime_spec/` in its worktree,
commits explicit paths and pushes; Root integrates. Root drafts the engineering spec,
VNFC case analysis and implementation plan, submits them to the proper Pro node, and
iterates to a complete decision before activation for CM/implementer/reviewer. The owner's
standing Pro-directed-spec delegation applies; no repeated owner vote. The toy 45-minute
and UAV 12-hour thresholds are proposed investigation triggers, not scientific negatives
or permission to shorten frozen assignments. Pro must settle their exact budget semantics.
