# CodexBechmark

多个独立 Codex 测试场景的集合，实际安装在 `C:\Projects\CodexBechmark`。
顶层仅提供目录索引和通用约定，不默认启动任何一项测试。

| 场景 | 测试目标 | 状态/入口 |
| --- | --- | --- |
| [root_delegation](root_delegation/README.md) | 持续执行 delegation、正确升级、完成验收 | runner 可用；`root_delegation/workspace/` |
| [cm_delegation_granularity](cm_delegation_granularity/README.md) | spec 颗粒度、交接详细度、RL 任务模板/范例复用 | 设计/筛选/微例子；完整题包待制作 |
| [cm_direct_review](cm_direct_review/README.md) | CM 直接实现与独立 reviewer 的组合 | 基线/架构对照设计；未试跑 |

CM 测试先读 [spec 主设计](_shared/cm_tasks/SPEC_DESIGN.md)。同一个 CM 连续处理代码问题和
杂务；先比较 spec 策略，再扩展模型，不把每个问题都变成干净上下文的新会话。

```text
CodexBechmark/
  README.md
  AGENTS.md
  root_delegation/
    README.md             # 本项测试的启动与评分说明
    DESIGN.md             # 场景设计
    AGENTS.md             # 本项测试入口
    ROOT_PROMPT.md
    runner.py
    _host/                # 本项事件、评分依据与私有运行记录
    workspace/            # 本项被测CLI目录
      AGENTS.md
      responses/          # 本项逐次回答与导出记录
  cm_delegation_granularity/ # spec 主测试的独立入口
  cm_direct_review/         # 并列的直接实现对照
  _shared/cm_tasks/         # 两项共用的模式、材料与主持筛选
  <future_scenario>/        # 后续测试各自独立
```

每项测试拥有自己的入口指令、材料、运行记录和评分方式；不共享隐含的当前run。
先选择场景，再在该场景的workspace启动全新CLI。不要遍历所有测试材料。
运行记录保留场景版本、模型与effort；完成回放和通过评分分别报告。

HMASD仓库内同名目录是版本管理副本，仓库外目录用于实际测试，避免加载HMASD
项目AGENTS。个人全局配置仍可能生效；目录分离不是OS级读取隔离。更新安装时
只同步维护文件，保留各场景的`_host/runs/`及`workspace/responses/`。
