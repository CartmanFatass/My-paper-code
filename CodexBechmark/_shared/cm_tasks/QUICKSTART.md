# 在独立 session 一句话启动

先选目录，在 Codex 中打开一个全新 session：

| 用途 | 目录 |
| --- | --- |
| 当前项目直接实现基线 | `C:/Projects/CodexBechmark/cm_direct_review/workspace` |
| 委派详细度与范例复用 | `C:/Projects/CodexBechmark/cm_delegation_granularity/workspace` |

当前打开的顶层 session 本身就是 CM。入口使用 Astra/medium；
reviewer 使用 Astra/high；委派场景另用 Terra/high implementer。

发送一句：

> 开始测试

或明确配置：

> 开始测试，L2 reuse，seed=17

不指定时为 L0 fresh、自动随机 seed、不同预估难度的两题。直接实现场景忽略 spec 档位的含义。
相同输入的配置比较使用同一 seed 和同一已冻结题库版本，各自在全新 session 执行。
不要让已读题库、隐藏答案或其他配置结果的 session 参测。

入口指令会执行 `python -B start.py`，绑定 `CODEX_THREAD_ID` 中的当前真实 CM，
建立本轮代码仓库、当地 bare origin、材料和私有主持记录。CM 随后自动读取本轮
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

模型配置在新 session 启动前生效。当前入口预设基线模型；若改 CM/子代理模型，
先修改入口 `.codex` 对应配置，再开新 session，并用匹配的
`--cm MODEL EFFORT / --implementer MODEL EFFORT / --reviewer MODEL EFFORT` 记录请求。
在运行中传参数只改变请求记录，不能改变一个已运行 session 的实际模型。
模型/effort 由真实日志核验，设置不符时不会算作该组通过。

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
