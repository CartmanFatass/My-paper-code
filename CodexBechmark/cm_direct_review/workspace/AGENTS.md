# 独立 CM 测试入口

用户在本目录打开的当前顶层 session 本身就是 CM。不要创建 CM 子代理，不要另启动一个 CM CLI。
默认建议 Astra/medium CM、Astra/high reviewer；用户可选择任意可用组合。
实际模型从运行元数据记录，不要求匹配默认值。用户指定组合时向start.py传入
`--cm MODEL EFFORT --reviewer MODEL EFFORT`，只传已明确的角色。
这些参数记录选择并生成子角色配置，不切换当前CM模型；当前CM使用用户在界面选择的模型。
这是独立 benchmark，不继承 HMASD 科研运行授权，不读取生产源或主持答案。

用户说“开始测试”时，直接运行 `python -B start.py`。用户指定 seed 时加 `--seed <整数>`；
委派场景指定档位/方式时加 `--level L0|L1|L2|L3 --delivery fresh|reuse`。
未指定时为 L0 fresh，抽题 seed 自动产生并保存。不要为了默认值再询问确认。
同一比较组应使用相同 seed。不要在已看过本轮答案的 session 重开新一轮；每轮使用新 session。

start.py 返回本轮独立 workspace 和 run 路径。立即读取该 workspace/AGENTS.md，
之后所有代码与 work/记录都写在该 workspace，执行它的 benchmark.py next/checkpoint 循环。
两题由当前 CM 连续完成；实际调用所需 implementer/reviewer，按运行说明保存交接/审查记录。
用户中途问状态时简短回答后继续；普通问题和杂务不结束本轮。
只能读取本轮分发的源码、任务说明、材料与公开检查；不得查看其它 run、_host、
共享维护文档、原项目历史正确 patch 或隐藏检查。只允许通过列明命令执行主持脚本。

最后一次 accepted checkpoint 自动安排收尾，等待当前 CM turn 真实结束，再导出实际会话、
运行独立裁判和既有成本工具。CM 给出交付并结束当前 turn，附返回的 REPORT.md 路径；
不要在本会话等待自身结束，不要读取隐藏反馈后修改答案，不要人工复制下一条题目。
成本或实际模型信息缺失时记录缺失，不能当作零或默认正确。此入口不启动完整配置矩阵。
