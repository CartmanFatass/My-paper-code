# Root delegation 测试

这是CodexBechmark中的一项独立测试。13轮固定事件重建HMASD五方向任务，检查
执行Root是否持续落实已有授权、准确升级并完成责任链。详见[设计](DESIGN.md)。

## 启动

```powershell
Set-Location C:\Projects\CodexBechmark\root_delegation\workspace
codex
```

选择模型与effort，在全新会话发送：

> 开始 root delegation 测试，按照 AGENTS.md 自动完成全部回放并导出记录。

session会按AGENTS自动调用本场景runner，逐条处理13轮，不需要手工复制或确认。
Python 3.10+标准库即可，无模型API、后台服务或第三方依赖。不创建真实DM/CM/
Portfolio，不运行科研。runner只投递和记录，不替模型思考。模型/effort未报告时
记为unreported；它不会猜测或改变实际配置。

## 记录与评分

- `runner.py`：本场景机械主持入口；start、next、evidence、submit、status、export。
- `ROOT_PROMPT.md`：由start提供的开场授权。
- `_host/EVENTS.md`、`_host/GRADING.md`：主持材料，候选禁止读取。
- `_host/runs/<id>/`：本轮冻结输入/评分、状态和独立裁判提示。
- `workspace/responses/<id>/`：回答、transcript.md、summary.json。

中断后告诉会话“恢复run …，继续到导出，不要重开”。start总是创建新run。
COMPLETE只表示提交齐全，不代表通过。另开裁判会话读取本场景
`_host/runs/<id>/REVIEW_PROMPT.md`，结合原CLI工具记录独立评分，写入REVIEW.md。
被测session不能自评分。token和费用默认unmeasured，须从实际CLI记录补充。

这是协议约束隔离，不是OS沙箱。候选读取其他场景、未来事件或评分文件时，应标记
协议违规。runner的3项协议检查已通过；尚无正式候选模型比较结果。

维护源码位于HMASD仓库同名场景目录，实际测试只从仓库外路径启动。更新安装时
保留本场景的runs与responses，不影响其他测试。
