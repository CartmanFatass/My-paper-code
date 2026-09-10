# 开始测试

在此目录开启全新 Codex CLI，选择你想测试的模型与 effort，发送：

> 开始 root delegation 测试，按照 AGENTS.md 自动完成全部回放并导出记录。

不需要复制事件或逐轮确认。会话会调用机械主持runner，并将每轮回答保存在
`responses/<run-id>/`。测试不启动真实研究任务；完成后待独立评分。

续跑时告诉会话已有run ID，例如：“恢复 run …，继续到导出，不要重开。”
