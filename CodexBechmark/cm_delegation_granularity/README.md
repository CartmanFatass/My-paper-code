# CM 委派说明颗粒度与复用

这是 CM 测试的主项：找到适合 RL 重复任务的 spec 内容、详细度与范例复用方式。
状态：设计、历史筛选、五类模式及三个微例子已建立；完整代码题包/runner 尚未制作，
未运行候选模型比较。先读 [SPEC_DESIGN.md](../_shared/cm_tasks/SPEC_DESIGN.md)。

固定 Astra/medium CM、Terra/high implementer、Astra/high reviewer，首先比较：

| 内容档位 | fresh：逐次完整撰写 | reuse：引用模式、补本次差异 |
| --- | --- | --- |
| L0 当前五项交接 | S-L0-FRESH | S-L0-REUSE |
| L1 +任务代码规范 | S-L1-FRESH | S-L1-REUSE |
| L2 +具体执行逻辑 | S-L2-FRESH | S-L2-REUSE |
| L3 +局部代码范例 | S-L3-FRESH | S-L3-REUSE |

8 个 spec 策略加一个当前 CM 直接实现基线，先在同一连续流程筛选，共 9 次计划流程。
最多两个 spec 策略加直接基线，在两个留出流程各重复两次；主研究最多 21 次流程，
不含协议校准及可选诊断。所有计划配置仍为未运行，未创建试跑会话。

同一 CM 保留代码问题、review、迟到回执、Git 杂务和状态询问形成的上下文；同模块修复
复用原 implementer。CM 真实编写交接、处理澄清并验收，检查后也要继续完成后续工作。
所有组获得同样的必要科学事实与验收；高档增量为实施指导，不能靠故意不给低档必要信息
制造优势。[各档定义](../_shared/cm_tasks/HANDOFF_LEVELS.md)和
[可复用模式](../_shared/cm_tasks/patterns/README.md)已分开，按档投递。

费用包括 CM 的规范编写、查阅与选择模板、填差异、沟通、接管、review 返工和验收。
模式/范例首次制作与维护单列，并报告实际复用次数下的摊销。判断详尽 spec 是否合算，
既看首用，也看跨任务复用；不只看 implementer 的 tokens。

只有 spec 策略筛选后，才增加 Astra/medium、Luna/max implementer 来验证适用范围；
Sol/high 为可选扩展。不同模型使用相同任务适用职责，不改科学规则。
CM/reviewer 的组合比较仍保存在并列的 [cm_direct_review](../cm_direct_review/README.md)。

最终交付包括每类任务适合的档位、可引用内容、必须逐次写的差异、范例适用边界，以及
可支持的模型范围。当前模式是候选，尚未验证为生产最佳默认。
后续 workspace 由 prepare 生成；目前没有完整 benchmark 的启动命令。
