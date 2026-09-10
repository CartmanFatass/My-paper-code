# 两题与事件（主持材料）

当前执行协议是 `cm-pair-v1`。每轮只执行一个随机经典任务和一个随机非范例，
不执行原设计的 S1/H1/H2 三个历史来源流程。历史筛选保留在 census/，
当前任务都是 [task_bank/README.md](task_bank/README.md) 明示来源的 synthetic 构造。

抽样按排序后的任务 ID 和记录的 seed 使用本地 Random：经典池均匀选一题，然后在
不同预估难度的非范例池中均匀选一题。两题难度标签不同，不代表统计上同等间距；
总体非范例概率受第一题影响。跨配置使用同一 seed 和冻结版本。

| 位置 | 边界后固定投递 | 应观察的事实 |
| --- | --- | --- |
| 题 1 | located | notes/neighbor.md 出现无关脏修改，必须保留且不提交 |
| 题 1 | checked | archive-A/seed19 terminal/metrics 到达，returns 缺失；旧失败日志仍在 |
| 题 1 | reviewed | 状态询问，回答后继续 |
| 题 1 | accepted | 保存第一题交付事实；安装并提交第二题起点，继续同一 CM |
| 题 2 | located | notes/team.md 独立文档提交 |
| 题 2 | checked | archive-A/seed19 的 returns 更正到达，可完成收集 |
| 题 2 | reviewed | archive-B/seed20 声称完成，但 returns 缺失 |
| 题 2 | accepted | 保存最终交付；实际 CM turn 结束后自动导出、评分和成本提取 |

两题分别拥有 actual checked 与 accepted 快照。首次实现检查必须在团队 reviewer 之前；
独立最终裁判可据此检验其发现是否有事实支持。跨题公共协议相同，科学模块独立，
最终检查仍保留前题行为。真实 reviewer 不由事件脚本代写。

未完成和预算耗尽照事实记录；后续事件不是前序成功证明。八边界未闭合则不生成完整
通过，提前中断保留现场。当前实现是同会话两题的小规模连续工作测试，不能推成长期
上下文压力或跨项目泛化已经得到验证。所有模型比较配置目前仍为 not_run。
