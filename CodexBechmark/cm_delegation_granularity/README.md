# CM 委派说明颗粒度与复用

固定 Astra/medium CM、Terra/high implementer、Astra/high 独立 reviewer，
测试交接详细度和局部范例复用。L0 是当前项目五项交接；强制 Terra 委派是实验处理。

在 `C:/Projects/CodexBechmark/cm_delegation_granularity/workspace` 打开新 session，说：

> 开始测试，L2 reuse，seed=17

当前 session 本身就是 CM。它按档位真实编写交接、调用 implementer/reviewer、
处理修复并验收。每轮仅随机一题经典范例和一题非范例，默认预估难度不同。
结束后自动独立评分并提取完整团队与裁判成本。[完整入口说明](../_shared/cm_tasks/QUICKSTART.md)。

| 档位 | 交接增量 | fresh | reuse |
| --- | --- | --- | --- |
| L0 | 当前五项结构 | 逐题撰写 | 复用五项结构 |
| L1 | 接口、形状与本题代码约定 | 逐题撰写 | 引用对应档位 |
| L2 | 状态/数据流与具体逻辑 | 逐题撰写 | 引用并填差异 |
| L3 | 局部骨架与适用代码例子 | 本次生成并计费 | 引用冻结例子 |

只说“开始测试”默认 L0 fresh。一次只运行所选配置，两题的科学事实和验收完全相同。
[档位定义](../_shared/cm_tasks/HANDOFF_LEVELS.md)保持累积关系，材料按档截取，
L0 不会间接拿到 L3。不得把 CM 全部历史传给 implementer 来抵消交接差异。

目前实现和离线检查完成，所有候选模型配置仍未运行。难度是设计估计；
八个策略是可选择配置，并非一句话启动后必须全跑的任务清单。
同 seed、同题库的比较另开新 session；后续模型扩展也由用户选择。

费用包含 CM 编写、选择模板、解释、接管、审查与返工；库首次制作仍 unmeasured，
不能当免费。直接实现基线位于 [cm_direct_review](../cm_direct_review/README.md)。
