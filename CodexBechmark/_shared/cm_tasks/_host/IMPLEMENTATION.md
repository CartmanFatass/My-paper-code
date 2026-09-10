# cm-pair-v1 实现与核验

2026-09-09 PDT。版本管理源为 HMASD/CodexBechmark；实际使用目录为
C:/Projects/CodexBechmark。未修改 root_delegation 的 runner、历史回答或运行记录。

## 已实现

- 场景 workspace 的 start.py 绑定当前新打开的顶层 session 为 CM；不再创建 CM。
- 每轮五个经典候选抽一题，三个非范例抽一题；默认难度标签不同，可复现 seed。
- 两题顺序分发、八个边界、真实 Git/local bare origin 和固定背景事件。
- L0–L3 × fresh/reuse 按档材料；真实 implementer/reviewer 由当前 CM 调用。
- 每轮冻结 runner、题库、oracle、材料与输入哈希；后续维护不能改变已准备的第二题。
- 首次实现和最终行为检查；每题单独检查提交/push，保留未提交邻接改动。
- 真实会话配置及公开原生子代理调用/返回导出；不导出私有推理。
- 最后边界后一次性后台收尾：等实际 CM turn 结束，再独立评分与调用原成本 skill。
- 独立裁判失败、没有 session ID 或使用 CM 的 ID 时不产生完整通过。
- REPORT.md、原始成本输出和失败状态留档；价格是冻结 Standard 参考口径。

正常入口与维护接口见 [QUICKSTART.md](../QUICKSTART.md)。
角色来源见 [BASELINE.json](BASELINE.json)，题库语义和来源见
[task_bank/README.md](task_bank/README.md)。

## 已完成的证据

题库作者提供八题 baseline/reference/典型错误、公开检查及隔离安装校准：
原 baseline 和错误解被拒绝，参考解通过。publication helper 契约已补足，
masked_credit 在候选试跑前改为当前 UCOPE 的 agent-sum / all-row-mean，
其针对性校准接受参考解、拒绝两个错误分母。原记录和修订边界保留于
[task_bank/CALIBRATION.json](task_bank/CALIBRATION.json)。

最终离线协议检查命令：

```powershell
python -B CodexBechmark/_shared/cm_tasks/_host/test_runner.py --scientific-python C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe --scratch-parent C:/Projects/HMASD/temp/tests -v
```

七项通过，20.070 秒。包含：

- 80 个 seed 的两类/不同预估难度抽样与全部题目可达；八种材料隔离。
- 完整参考实现两题、八边界、真 Git 操作与冻结输入；维护副本改变后本轮题目/oracle 不漂移。
- 缺产物、丢失邻接修改、漏掉第一题 push、实际模型不符、缺会话证据的负例。
- 当前 session 绑定，无第二个 CM；两种运行目录都包含于打开的 workspace。
- 真终止事件必须晚于最后边界；子代理不能冒充顶层 CM。
- 裁判非零退出/缺 ID/CM 同 ID 拒绝；独立成功完成才具备完整评分条件。
- 收尾调用次序、CM abort 不发起裁判、一次性 detach；这些部分使用明确的替身依赖，没有模型调用。

测试只创建其独有的 temp/tests/cm-runner-* scratch，运行后已清理。
独立 Astra/high native reviewer 检查题库/材料和 runner 边界：
隐藏 publication 条件、冻结 oracle、逐题 push、workspace 写入范围及裁判完成判定的问题
均已修复；最终 focused review 无未解决 material finding。审查未启动候选模型。

CLI help 确认 exec 的配置/JSON/output-schema 接口；debug prompt-input 可生成提示，
但该命令不支持 strict-config，也不展示子代理工具定义，因此不作为角色加载成功证据。

## 尚未测量

没有真实候选 CM 流程、spec 策略比较或模型优劣结论。
真实候选会话的自定义角色加载、后台进程在该运行权限下存活以及在线裁判完整启动，
仍需首个实际运行确认；离线测试替身不是这些事实的证明。
题库难度仅为设计估计；小型 synthetic 修复不等同完整生产任务。
首次模式/题库制作成本没有可独立归属的完整边界，仍为 unmeasured。
API 参考费率未计未知 service tier/超长请求倍率；不能报告为实际账单。

任何失败都有独立诊断，不自动重启候选、额外抽题或批量展开矩阵。

## 2026-09-10 首次在线故障修复

Owner确认模型组合由用户选择。默认模型不再当硬性比较组；仅显式参数进入expected_models，
实际turn配置独立保留。缺失role标签不从模型或名称猜测，职责与工作目录交独立工作流审查。
裁判收到完整闭合证据的UTF-8标准输入，不依赖其被策略拒绝的shell读取；没有放宽sandbox。
后台成本输出写UTF-8文件，只打印ASCII路径状态，收尾进程启用UTF-8；已结束的旧裁判费用保留。
评估受阻/证据不足为full_run_passed=null；确认缺陷或偏离才为false。
维护者--maintenance使用新收尾代码处理旧快照；--retry仅允许已结束裁判并归档前次输出，
不修改冻结runtime、题目、候选代码、八边界快照或原始模型元数据。

修复后9项离线检查通过（19.461s），包含显式模型约束与自选组合、证据缺失、完整内联材料、
中文成本在cp1252输出下不中断、三态评分及原有两题八边界/Git检查。无候选重跑。
