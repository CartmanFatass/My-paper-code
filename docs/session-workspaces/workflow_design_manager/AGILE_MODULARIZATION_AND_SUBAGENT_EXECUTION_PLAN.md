# HMASD 敏捷模块化与按风险委派计划

```text
document_kind=wdm_execution_plan
workflow_assignment_id=AGILE_MODULAR_RESEARCH_SUBAGENT_ROUTING_V2
status=ACCEPTED_LIGHTWEIGHT_PLAN
default_research_stage=EXPLORATION
```

## 目标与架构

先用最小机制和便宜判别实验回答“是否值得继续”，仅在价值已显现时建设正式证据。默认核心为 `source -> controller -> episode -> metrics -> analysis`。可选正式层为 `serialization -> independent validation -> artifacts -> runtime binding`，只能消费冻结核心输出，不能反向改变核心语义。

进入 FORMALIZATION 必须同时满足：最小判别支持继续、工程可行、正式证据回答明确主张、没有更便宜的等价证据。否则保持 EXPLORATION；若正式化要求改变核心含义，删除 workaround 并退回探索。

## 简单任务预算

```text
active_engineering_budget_minutes=20
failed_probe_budget=2
allowed_paths=one_normal_plus_one_simple_fallback
success=user_visible_requested_result
passive_external_generation_wait=excluded_and_never_interrupted
```

预算耗尽后停止新增机制并返回最小事实。一次事故只修根因并记入 incident log；同一根因独立复发至少两次，才可提出永久规则。失败仅意味着可安全重试时，不建设 lease、sentinel、身份账本或恢复状态机。

## 子任务与模型路由

- 单文件、格式、引用、局部测试：Luna 或主任务直接完成。
- 调用关系/所有权未知：可选只读 Scout。
- 单模块且合同冻结：Luna 实现并以聚焦检查结束。
- 跨模块且保护 RNG、梯度、时钟或结果含义：Sol 实现或主任务集成。
- production entry、序列化、artifact lifecycle、phase connection：按需 Verifier。
- 已观察语义异常或聚焦检查失败：最多一次 Reviewer。

不组成固定流水线，不因文件数、时长或理论风险自动升级。并行度等于可分离文件族数量，同一文件不得并发写，主任务负责集成和接受。

## Reviewer 比例性

finding 必须同时具备正常路径复现或明确保护语义影响、对当前项目的实质影响、以及成本低于风险的最小修复。理论攻击、敌对输入、一次性工具故障和安全可重试失败只记 residual risk。Reviewer 只审一次，不审查审查本身；投入更多推理预算不等于项目价值。

## 外审与控制面

CPM 与 Explorer 各自在自己的会话直接调用 Agentify：复用稳定页面、一次插入完整科学问题、发送、等待自然完成、归档原文。不设置传输子代理、monitor、heartbeat、hash admission、跨会话中转或模型编写的恢复状态机。

WDM 对用户发起的设计变更先给精简计划，确认后连续实施、聚焦验证、提交和推送。其他会话的缺陷按时间写入 incident log；日志不是调度器、审批队列或全局 blocker。每项新机制必须写明删除什么，并满足 `lines<=100`、`terminal_states<=3`、默认净行数不增长。修改权限自动包含相同路径的 Git 权限。

## 迁移与完成

1. 删除重复角色、阻塞式队列语义和传输包装层。
2. 运行直接相关合同、结构 harness、stale-term 和 diff 检查。
3. 提交并推送精简 workflow commit。
4. 再创建或重载新 CPM/Explorer；旧会话不再接收任务。
5. 后续代码模块化由 CPM 逐模块执行，不阻塞本次控制面恢复。

完成条件：WDM 核心低于总行数预算；Cost Reviewer、阻塞式 FIFO 和外审传输子代理不再是合同要求；Reviewer 检查净项目价值；简单任务预算可测试；Git 无无关路径和未解释旧术语。
