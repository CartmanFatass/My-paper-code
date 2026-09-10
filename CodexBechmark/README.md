# CodexBechmark

多个独立 Codex 测试场景的集合，实际安装在 `C:\Projects\CodexBechmark`。
顶层仅提供目录索引和通用约定，不默认启动任何一项测试。

| 场景 | 测试目标 | 启动目录 |
| --- | --- | --- |
| [root_delegation](root_delegation/README.md) | 持续执行 delegation、正确升级、完成验收 | `root_delegation/workspace/` |

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
  <future_scenario>/      # 后续测试各自独立
```

每项测试拥有自己的入口指令、材料、运行记录和评分方式；不共享隐含的当前run。
先选择场景，再在该场景的workspace启动全新CLI。不要遍历所有测试材料。
运行记录保留场景版本、模型与effort；完成回放和通过评分分别报告。

HMASD仓库内同名目录是版本管理副本，仓库外目录用于实际测试，避免加载HMASD
项目AGENTS。个人全局配置仍可能生效；目录分离不是OS级读取隔离。更新安装时
只同步维护文件，保留各场景的`_host/runs/`及`workspace/responses/`。
