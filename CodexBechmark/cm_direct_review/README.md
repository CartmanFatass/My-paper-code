# CM 直接实现 + 独立 reviewer

状态：设计已建立；题包/新 runner 尚未制作，未运行模型比较。
与 [root_delegation](../root_delegation/README.md) 并列，不继承其文本答案协议。

CM 实际完成连续代码任务和杂务，独立 reviewer 实际检查改动；不设 implementer。
流程、代码起点与验收使用[共用设计](../_shared/cm_tasks/DESIGN.md)。
本项是 [spec 主研究](../_shared/cm_tasks/SPEC_DESIGN.md) 的直接实现基线与后续架构对照。
先执行 D-AM-AH 基线；其余模型/reviewer 组合放在 spec 筛选之后，不抢先展开。

| 候选配置 | CM | 团队 reviewer | 目的 |
| --- | --- | --- | --- |
| D-AM-AH | Astra / medium | Astra / high | 当前默认直接实现基线 |
| D-TH-AH | Terra / high | Astra / high | 固定 reviewer，比较 CM 配置 |
| D-LMX-AH | Luna / max | Astra / high | 固定 reviewer，比较 CM 配置 |

这是部署配置比较，模型与 effort 同时不同；不作纯模型因果结论。
Sol/high 保留为可选扩展，不默默加入首轮预算。

模型扩展阶段仅对选出的两个 CM，分别换 Terra/high、Luna/max reviewer，并与原
Astra/high reviewer 结果比较。实际重新执行团队流程；不能把对同一 patch 的离线 review
分数当成 CM+reviewer 的完整成本/质量。若需要便宜的 reviewer 诊断，可单列离线交叉审查。

同一 CM 连续经历全部工作，中途不为它人工重述约束。每个配置的最终结果由同一独立
裁判和隐藏检查评定；不能让正在比较的 reviewer 给自己团队打最终分。

模型扩展后需另外规划两个留出流程各两次独立重复；不计入 spec 主研究的 21 次范围。
报告整个流程的失败、成本和时间，同时给
语义修复、参数连接、集成/收尾等分层结果。按事先固定规则最多保留两个直接实现配置；
未达到同一验收的组不因便宜而被选为生产配置。

候选排序规则：先比较完整流程验收和严重失败，再比较总成本与时间；若互有优势则保留
两个作留出验证，不用小样本拼出一个任意综合分。筛选结果不直接修改 HMASD 生产角色。

后续启动目录：本场景各 run 的隔离 workspace，由 prepare 生成；目前无可用启动命令。
