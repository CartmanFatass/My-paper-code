# Retired proposed B15 consultation plan — 2026-09-23

Source main: `4ffcc4779b7c3caf8ea93d7496664cdb990aee73`. Retired after complete advice delivery reconciliation and DM adoption.
Only the superseded DM1 proposal/wait is retired; this does not alter other directions or controls.
The full question, full answer and adopted plan remain in the append-only notebook and claim.

## Previous standing

| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。**B14两臂完整验收，0实验运行。** 固定source88b67e5e0、seed974201，实际共同训练场景/RNG及初末评价隔离通过，40文件、90更新、8面板完整收取重算；2fits/720k train/128k eval、137.854759 command min。N8最终H6−SET J +.071357215、服务+5.2826875人/步（各31正1负）；N6 +.049940952/+2.7015625（J31正1负、服务29正3负）。两臂各N自身J/服务均32/32改善，H6初始均值反而更低；保留N8 −1.102人与N6最差−2.488人的配对损失、N8质量/高度代价，以及B11/B12反号和B13损失。仍为每臂n=1开发观察，未认证技能因果或总体排名。下一判断是固定3新训练区组/6fits及未读面板的有限确认是否优于进一步普通学习；[实际草案](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/candidates/agent_count_generalization/CLAIM_bounded_count_transfer_20260923.md)及[聚焦问题](https://github.com/CartmanFatass/My-paper-code/blob/7df314e63a4b951fb6698e8be0c428f35e5fe273/docs/research/candidates/agent_count_generalization/NOTES.md#pro-question-2026-09-23-bounded-confirmation-after-fresh-b14)已提交，Pro同key一次Send成功并挂接观察，0确认fit启动，待读完整建议后作DM决定。[完整B14与全部反例](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-complete-fresh-learning-reproduces-a-bounded-package-benefit)；[退役运行计划](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/archive/2026-09-23/RESEARCH-agent-count-b14-complete.md)。 |

## Previous plan

| **DM1：泛化与训练条件** | B14新训练保留N8平均包用途，两臂均真实学习且初始均值排序反转；剩余关键不确定性是独立训练可靠性、未读世界和普通对照充分性。 | **B14完整结束；拟议B15确认正在科学审阅，未启动新fit。** B14 N8最终J/服务差+.071357215/+5.2826875，N6+.049940952/+2.7015625；四个J或服务不利世界和分量代价完整保留。确认草案每臂3新seed、共同外生训练块、N6/360k、未读32世界/N初末评价；拟议6fits/2.16M train/384k eval、2.544M总team交互。主比较为固定面板条件下N8训练区组平均差，拟议成对t下界J>0且服务>1人/步；小n假设、基线强度及普通mixed-N替代是本次审阅重点。草案不是已准入确认，不根据开发正结果自动追加；新入口尚未实现。[完整结果](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-complete-fresh-learning-reproduces-a-bounded-package-benefit)；[拟议claim](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/candidates/agent_count_generalization/CLAIM_bounded_count_transfer_20260923.md)；[本次问题](https://github.com/CartmanFatass/My-paper-code/blob/7df314e63a4b951fb6698e8be0c428f35e5fe273/docs/research/candidates/agent_count_generalization/NOTES.md#pro-question-2026-09-23-bounded-confirmation-after-fresh-b14)。 |

## Previous reading and recovery routing

**DM1 的关键读法。** B14初始H6−SET的N8/N6均值J为−.020434/−.016961，最终反转为
+.071357/+.049941；两包各自都有正学习，削弱本实例仅靠较好初始排序或对照退化的解释。
D0、D45、I_H、I_SET和Delta分别读取，恒等式不拆分初始化/技能/优化的因果份额。一个新
训练实例和32嵌套世界仍是开发证据；B13旧资产选择与B11/B12反号继续保留。平均收益、
各个不利世界、最低绝对服务和N6后果不互相替代。拟议新确认使用独立训练区组及未读
固定面板；不能把世界数当训练n，也不能在三个结果不清楚后自动增加到五个。
[完成B14计划已退役](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/archive/2026-09-23/RESEARCH-agent-count-b14-complete.md)。

**责任路由与实际状态。** DM1 复用“智能体数量泛化 DM”（task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`），
原 checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`；B11 两臂已完整准入、收取和独立判读，
B11/B12/B13/B14原生操作、完整收取及独立判读均结束；当前0实验运行。B14全部两臂验收后，generation119的SET READY已消费至120，未重启worker。拟议有限确认尚未实现/准入；聚焦问题source`7df314e63a4b951fb6698e8be0c428f35e5fe273`已在原私有咨询中一次Send成功，effort6 Pro与完整附件匹配。key `hmasd:577f4d6ba746d0bfffb66159eb0e364a826e986ca88e7cf5d685f6e1469687dc`由本任务generation121/1500秒观察接管；当前0新fit/1咨询等待，回来后仍须deliver核验及全文读取，再由DM处理实质意见。[完整结果](https://github.com/CartmanFatass/My-paper-code/blob/4ffcc4779b7c3caf8ea93d7496664cdb990aee73/docs/research/candidates/agent_count_generalization/NOTES.md#2026-09-23--b14-complete-fresh-learning-reproduces-a-bounded-package-benefit)；[新问题](https://github.com/CartmanFatass/My-paper-code/blob/7df314e63a4b951fb6698e8be0c428f35e5fe273/docs/research/candidates/agent_count_generalization/NOTES.md#pro-question-2026-09-23-bounded-confirmation-after-fresh-b14)。
