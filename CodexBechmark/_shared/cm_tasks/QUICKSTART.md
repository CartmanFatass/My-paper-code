# 在独立 session 一句话启动

## 一轮五类经典题＋一道非典型题

在委派 workspace 的全新 session（界面选择 Sol medium）发送：

```text
开始测试，一轮5+1题，L1 fresh。CM：gpt-5.6-sol / medium；Implementer：gpt-5.6-luna / max；Reviewer：gpt-6-astra / medium。
运行 start.py 时使用 --suite five-plus-one --level L1 --delivery fresh --cm gpt-5.6-sol medium --implementer gpt-5.6-luna max --reviewer gpt-6-astra medium。
开局读取本轮 TASKS.md，全部六题说明和源码立即可访问。同一 CM 按清单逐题完成真实委派、独立审查和四个检查点，六题全部完成后统一交付 REPORT.md。不要拆成多个 run。
```

此模式为 `cm-six-v1`：五类经典题按类别顺序全部纳入，再从三道非典型题抽一道；
seed 可省略并自动记录，不需要逐轮替换。一次六题共24个检查点，首次实现与最终
回归均逐题评分。所有题提前可见，不能与旧两题顺序投递模式当作完全相同处理。
“非典型+1”不表示三道非典型题全覆盖。直接实现和委派入口现在都默认六题。
下文涉及两题顺序投递的旧流程仅在显式 `--suite pair` 时使用。

完整流程、数据字段、自动统计范围和异常处理见 [操作与统计文档](OPERATING_GUIDE.md)。

先选目录，在 Codex 中打开一个全新 session：

| 用途 | 目录 |
| --- | --- |
| 当前项目直接实现基线 | `C:/Projects/CodexBechmark/cm_direct_review/workspace` |
| 委派详细度与范例复用 | `C:/Projects/CodexBechmark/cm_delegation_granularity/workspace` |

当前打开的顶层 session 本身就是 CM。Astra/medium CM、Astra/high reviewer、
Terra/high implementer 只是默认建议，用户可以自选组合；按实际运行元数据记录。

发送一句：

> 开始测试

或明确配置：

> 开始测试，L2 reuse，seed=17

不指定时为 L0 fresh、自动随机 seed、六题模式。直接实现场景忽略 spec 档位的含义。
相同输入的配置比较使用同一 seed 和同一已冻结题库版本，各自在全新 session 执行。
不要让已读题库、隐藏答案或其他配置结果的 session 参测。

入口指令会执行 `python -B start.py`，绑定 `CODEX_THREAD_ID` 中的当前真实 CM，
建立本轮代码仓库、本地 bare origin、材料和私有主持记录。CM 随后自动读取本轮
AGENTS，按 located → checked → reviewed → accepted 的四个边界各完成两题。
implementer/reviewer 必须是真实独立子代理；子代理首次调用不继承 CM 全部历史。

最后一次 accepted 保存交付并启动一次性收尾进程。CM 正常结束当前 turn 后，
收尾进程才读取完整真实会话，做隐藏行为检查、独立 Astra/high 裁判和既有成本工具提取。
CM 最后返回本轮 REPORT.md 链接；文件会自动更新，无需用户粘贴题目、导出日志或手动评分。
收尾进程最多等待 CM 结束一小时；异常写入 finalization.json 和报告，不重复发起候选模型。
它不会回写候选答案，也不是定时任务或常驻服务。

每轮文件：

```text
<scene>/workspace/
  <run-id>/                 # 本轮候选源码、work/、真实 Git 仓库
  _host/runs/<run-id>/       # 主持记录；被测代理不得浏览
    REPORT.md               # 自动更新的人类可读入口
    state.json
    runtime/                # 本轮冻结的 runner、题库与规则
    snapshots/              # 八个提交边界及当时的 Git 事实
    origin.git/             # 仅本机的 bare remote
    export.json             # 实际 CM/子代理模型、effort 和公开原生交互证据
    judgement.json
    assessment/             # 独立裁判会话及报告
    cost/                   # 团队和独立裁判分别计量
```

所有运行写入均在打开的 workspace 下。`_host` 是协议访问边界，不是恶意代码防护。
评分报告存在也不代表通过：还需行为、流程、实际配置、原生工作流证据以及成功完成的独立裁判。
未计量、失败或缺失信息不能当成零费用或通过。

本机前提已用于离线检查：可用 Git、Codex CLI，Python 3.10.20 + NumPy 1.26.3 +
Torch 2.7.0+cpu（默认 `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`），以及已安装的
`codex-task-cost-analysis`。自动裁判会调用一个独立模型会话，成本单列。
定价为冻结的 API Standard 参考口径，不是订阅额度或实际账单。

先在界面选择CM模型。通过 `--cm MODEL EFFORT / --implementer MODEL EFFORT / --reviewer MODEL EFFORT`
记录本轮明确选择；未指定的模型字段不作为硬性约束。生成角色是便利入口，可使用等价真实子代理，
但必须记录ID/职责并接受独立工作流核验，不能从名字推断模型或实际工作。
参数不能切换已运行CM模型；显式指定与实际不符才算配置偏离，证据缺失标未核实。

维护者可对已关闭run使用 `runner.py export|judge|assess|cost --run <目录> --maintenance`
运行修复后的收尾工具，冻结runtime、题目和候选快照不变。补评额外传 `assess --retry`，
前次已结束裁判归档至assessment_attempts/，全部裁判费用单列保留；禁止覆盖仍运行的裁判。
裁判完整证据通过标准输入提供，保留assessment/input.txt；不依赖shell读取，权限不放宽。
`full_run_passed=null`表示尚不能确认，不把评估受阻或证据不足显示为代码失败。

## 维护者命令

正常候选只运行入口和本轮 benchmark.py 的 next/checkpoint/status。以下用于维护或外部主持：

```powershell
# 准备隔离输入，不调用模型
python -B C:/Projects/CodexBechmark/_shared/cm_tasks/runner.py prepare --mode direct --seed 17

# 从外部主持终端启动独立 CLI CM；不要在已有候选 CM 里调用
python -B C:/Projects/CodexBechmark/_shared/cm_tasks/runner.py launch --run ABS_RUN --with-assessment

# 关闭候选后可单独导出/核验；不要覆盖或重跑一个已尝试的裁判
python -B C:/Projects/CodexBechmark/_shared/cm_tasks/runner.py export --run ABS_RUN --session ACTUAL_ROOT_ID
python -B C:/Projects/CodexBechmark/_shared/cm_tasks/runner.py judge --run ABS_RUN
python -B C:/Projects/CodexBechmark/_shared/cm_tasks/runner.py cost --run ABS_RUN
```

外部 launch 是兼容的维护接口；用户的一句话入口使用 begin，直接绑定已打开的 session。
两条路径都使用每轮冻结 runtime；后续维护题库不能改变已准备运行的第二题或验收。
