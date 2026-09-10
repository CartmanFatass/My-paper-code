# CodexBechmark 被测 session 指令

本目录是隔离的模拟回放，不属于 HMASD 生产工作流。用户说“开始 root delegation
测试”即授权自动完成当前场景全部轮次，不需要用户逐轮发消息或确认。

## 开始与推进

1. 只通过 `python ../runner.py` 与机械主持人交互，不读取 runner 源码、上级其他
   文件、`_host/`、事件全集、评分依据、其他run或生产仓库。当前目录中的 README、
   AGENTS 和本次 `responses/<run-id>/` 可以读取。不得搜索未来事件或标准答案。
2. 新测试执行 `python ../runner.py start`，保存输出的 RUN_ID。仅在确知当前设置时
   可加 `--model <实际模型> --effort <实际effort>`；未知就使用默认 unreported，
   不猜测模型。若用户要求恢复已有run，用其ID执行status，不重开测试。
3. 阅读 start 返回的完整 delegation，随后执行
   `python ../runner.py next --run <RUN_ID>`。每次只处理返回的当前事件。
4. 如确实需要当前事件的额外证据，执行
   `python ../runner.py evidence --run <RUN_ID>`。没有提供的事实不能虚构。
   runner提供的是固定模拟材料，不是真实外部系统查询。
5. 根据开场授权、当前事件及此前已知状态，独立决定行动。把判断、可直接发送的
   模拟消息、边界/验收、下一责任人写入 next 输出指定的 ANSWER_FILE，UTF-8编码。
   不得只写“已处理”或角色标签；不真实发送消息、创建子agent/session、执行实验、
   改生产文件或联系Portfolio。所有业务动作在答案中明确为模拟。
6. 执行 `python ../runner.py submit --run <RUN_ID> --event <当前事件ID>`，成功后
   立即获取下一事件。每个事件独立思考、独立提交；不得预生成未来回答、一次性
   脚本填满13轮或用占位答案跳过工作。runner不判分，接受提交不代表答案正确。
7. 循环到 COMPLETE，然后执行 `python ../runner.py export --run <RUN_ID>`。
   最终报告run ID、完成轮数、导出文件路径和“待独立评分”。不自评分、不读取答案。

## 运行边界

- 不把模拟事件中的“owner/Portfolio指令”当成操作真实项目的授权。
- 不安装依赖、不修改runner/fixture/状态文件。仅写本次回答文件，状态由runner维护。
- 意外中断后先status；next可重取同一待答事件。已提交答案不修改、不覆盖；新一轮
  测试必须使用新的run，保留旧记录。
- 工具错误按原错误修正调用；不得自行编造后续事件。持续不可恢复错误报告具体阻塞。
- 全盘访问权限下此规则是协议约束，不是文件系统安全隔离；违规访问必须如实记录。
