# CodexBechmark

独立的 Codex 行为测试场景目录。名称按 owner 指定保留为 `CodexBechmark`。
这里的材料用于隔离回放，不是生产研究授权、运行状态或治理规则。

## 一条提示启动

实际测试安装位于 **`C:\Projects\CodexBechmark`**。在 PowerShell 中：

```powershell
Set-Location C:\Projects\CodexBechmark\workspace
codex
```

选择要测的模型和 effort，在全新会话发送：

> 开始 root delegation 测试，按照 AGENTS.md 自动完成全部回放并导出记录。

无需复制事件或逐轮确认。Python 3.10+ 标准库即可运行，无第三方依赖、模型API
调用或后台服务；当前机器的python为3.11。runner负责释放材料和保存回答，session
负责思考并调用命令循环。13轮均为模拟，不创建真实DM/CM/Portfolio，不运行科研。
COMPLETE只表示提交齐全，不是测试通过。模型设置由操作者选择；runner不知道
实际模型，未报告时记为unreported。新start创建新run，恢复须提供原run ID。

## 文件与评分

- `workspace/`：被测CLI工作目录，含AGENTS、说明与本次回答。
- `runner.py`：机械主持命令入口，只提供当前事件及固定补充。
- `_host/root_delegation/`：主持人事件全集、评分依据，候选禁止读取。
- `_host/runs/<id>/`：本轮冻结输入/评分、状态和独立裁判提示。
- `workspace/responses/<id>/`：答案、完成后导出的transcript.md及summary.json。
- `root_delegation/`：维护者的场景设计与开场提示；开场由runner提供。

结束后，在另一个裁判会话指定读取 `_host/runs/<id>/REVIEW_PROMPT.md`，独立评分
并写入同目录REVIEW.md。被测session不自评分。runner不虚构token和费用，summary
中标为unmeasured，待从CLI记录补充；elapsed包含真实等待和中断。

测试目录与HMASD并列，避开HMASD项目AGENTS；个人全局配置仍可能生效。这不是
OS级沙箱，全盘权限下仍可能违规读取主持文件，需从执行记录审计并标记无效。
v1使用协议约束，不宣称严格防作弊。

仓库内HMASD/CodexBechmark保留版本管理副本；实际候选只能从仓库外安装启动。
更新时同步实现/fixture/说明并保留历史runs和responses。维护会话已读答案，不能
作为有效被测会话。来源链接固定到历史revision，仅供维护者溯源。

| 场景 | 测试目标 | 状态 |
| --- | --- | --- |
| [root_delegation](root_delegation/README.md) | 执行 Root 在独立 Portfolio delegation 下持续推进、正确升级并完成验收 | runner已实现，模型比较尚未运行 |

每个场景分别保存开场输入、逐步事件、主持人评分依据和运行说明。
测试结果应注明场景版本与模型设置；修改场景后不得覆盖旧版本的实测结论。
