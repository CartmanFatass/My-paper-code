# HMASD 工作流设计目标与验收标准

状态：用户确认的工作流重设计目标与验收基准  
Decision owner: User  
确认日期：2026-08-26

本文档定义工作流实现必须达到的目标和可观察验收结果。实现细节、历史协议、
skill、测试夹具或运行记录不得改变这些目标。若当前实现与本文档冲突，冲突表示
尚未完成的迁移工作，不得通过重解释本文档来消除。

## 已撤销的错误标准

此前提出的“删除 Work Packet、reconcile、native adapter、Clerk”验收项已经
作废。它会摧毁需要保留的自动化内核，不得作为简化、清理或重构的依据。

## 当前确认的设计目标

- Clerk 持有全局工作面：拓扑、任务创建/复用、路由、消息、等待、恢复和结果
  回收。
- Root 保持最高权限和用户入口，可直接介入任何角色，但不常驻普通自动流程。
- Portfolio、EM、CM、Operator 只接收自己的工作切面，完成局部工作并返回；
  不协调其他 session。
- 机械动作由 scripts 和统一协议完成，LLM 不自行解释状态机、不发明 gate。
- 研究→代码→实验→结果能够无人值守连续运行；故障按
  project/direction/feature/Effect 精确限定，有限修复后才请求用户。
- 多方向并行时路径和 Effect 正交；方向可在自有目录直接 Git，worktree 不是
  默认要求。
- 用户始终拥有全部权限；危险操作警告并记录，但不得形成权限死锁。
- 项目同时对人和 LLM 可读，使用分层文档、稳定目录和明确接口。
- 共享 C++ backend、神经网络基座等核心修改需要用户确认；方向实验代码自主
  修改。
- MARL 实验遵循真实科学与资源约束，不因 toy case 追求无意义精度或逐路径
  穷举。
- 从开源项目吸收简单、程序优先、单一事实源的设计哲学，不复制组件，也不
  叠加第二控制面。
- skill 只是可选组件；项目 spec、角色拓扑和机械协议不得拆散塞进多个 skill。

## 当前验收标准

1. 一条真实无人链完整通过：用户/Root → Clerk → EM → 必要时 CM → Operator
   → Clerk → 用户；Root 不做例行调度。
2. 四个方向可同时运行，任务列表可见，路径/Effect 无交叉，没有重复 task、
   重复发送或重复 Operator。
3. 中断、容量不足和局部失败能以同一工作身份恢复；修复次数有界，且不会传播
   裸 `BLOCKED`。
4. Participant 只看到目标、输入 refs、owned paths、允许 Effects、完成条件和
   返回接口；看不到全局协调复杂度。
5. 用户可随时直接覆盖或介入；危险行为有警告和完整记录，但不会被控制面阻挡。
6. Root 工作目录保持干净 `main`；方向内 Git 自主，worktree 可选且能够回收。
7. scripts 是唯一机械事实源；不存在并行 registry、重复状态机、重复恢复层或
   由 skill 重述的协议。
8. 删除或修改控制面前必须先做调用依赖和同一端到端基线核查。
9. 全部协议测试、命令运行测试和真实 native 测试通过；不能用“局部
   CM→Operator 成功”冒充完整无人链成功。
10. skill 只有在无 skill 基线确实失败、且内容是可重复单一能力时才创建；否则
    保持不存在。

## 已确认的执行与测试 seam

Decision owner: User  
确认日期：2026-08-26

- `scripts/hmasd_codex_tasks.py execute-plan` 是保留的原子内核 seam。一次调用只
  执行一个明确 `work_id` 的闭合 plan，负责确定性的 task create/reuse、投递、
  等待、fresh observation 和 typed return 验证。它不得替 planner 补字段或决定
  后续工作。
- `scripts/hmasd_codex_tasks.py run-chain` 是完整无人工作流的唯一外部验收 seam。
  它从一个明确的起始 `work_id` 出发，只依据 machine-validated return、draft 和
  `next_action` refs，有界组合现有 build、publish、`reconcile --once` 和
  `execute-plan` 操作。
- `run-chain` 不得引入 durable queue、第二 registry、daemon、数据库、新 workflow
  schema 或第二状态机。所有 durable facts 仍来自既有 authority、Work Packet、
  return witness、Effect observer 和 native task history。
- `run-chain` 遇到 terminal completion、用户/领域决定、typed conflict、UNKNOWN
  commitment 或转换上限时停止并返回精确事实。模型或 session 不得在每个 hop
  之间解释状态并自行选择下一次调用。
- 原子 transport/identity 测试使用 `execute-plan`；无人多 hop、bounded recovery、
  四方向并发和 real-native 验收使用 `run-chain`。单独通过前者不得宣称工作流
  完成。

## 当前完成状态

真实全链验收仍未通过，因此不得声称工作流已经完成。局部协议测试、fake
transport、单个 native adapter probe 或 scoped CM→Operator 成功都不能替代
上述完整验收。
