# HMASD 工作流效率与迁移经验（2026-08-11）

## 文档定位与证据边界

本文是面向人的、可独立阅读的经验记录，记录三轮控制面迁移/收敛后的一次效率跟进。它解释为什么当前 Root-first 工作流要这样分工、检查和恢复，也记录已观察到的故障模式。这里的 `b0a4bb3b`、`5f45c189` 和 `2919b950` 是定位相应阶段的 Git 修订；本文依据本次已确认计划中的里程碑和收敛事件整理，并不把短哈希、文件摘要或本文件本身当作独立的准入、验收或历史证明。

本 follow-on 的写入限于 Root 冻结的 exact union；本文档 writer 仅写本文件。效率建议不改变角色权限、调度权、验收权或 Git 权限。任何需要改变这些边界的意见都必须重新进入 WDM 设计与 Root 集成流程。

## 三轮迁移、问题和已完成的工作

### 第一轮：从隐含协作迁移到可读的控制面（`b0a4bb3b`）

最早的问题不是“少一个测试”，而是任务意义、身份和动作能力混在一起：子任务容易从上下文猜测自己是谁，路径字段容易被误当作任务含义，管理者、实现者和审核者的停止条件不清楚。第一轮把 Root-first 路由、注册角色、作用域键、拥有路径、L1/L2 深度和返回契约写成可读的控制面，完成了以 `b0a4bb3b` 为定位点的迁移阶段。

这一轮的完成项是：让 Root 独占用户交互、跨 owner relay、顶层路径冻结与最终 Git 整合；让 WDM/CPM/EM 各自保留语义所有权；让 L2 只实现一个已确认的冻结切片；把 assignment 的身份字段当作范围锚点，而不是工作流意义或完成证明；并把“不能猜测缺失授权”变成显式失败闭合原则。

### 第二轮：把分散修补合并成可审阅的 union（`5f45c189`）

第二轮暴露了跨 lane 的一致性问题：各自局部看似合理的 profile、Role、测试和路由，组合后仍可能说不同的话。于是把 disjoint slice 先形成候选，再由 Root 集成；集成后再开一个新的 convergence WDM 做 union 级审阅。`5f45c189` 是这次 integrated union 的定位点，而不是某个子代理的单独验收章。

这一步完成了跨 owner 边界的显式化：同一 Root 树可有多个实例，但 `(role, scope_key)` 必须唯一；同一写路径或尚未冻结的共享契约必须串行；并行完成顺序不产生语义优先级。局部 slice packet 只能表示 candidate-ready，不能声称已完成 union review 或 union acceptance。

### 第三轮：接受 convergence，并把运行时风险留到正确的闸门（`2919b950`）

第三轮对集成后的控制面作一致性收敛，最终接受的 convergence/main 定位为 `2919b950`。这轮没有把所有风险都伪装成“通过”：需要真实运行时、fresh smoke 或 canonical reload 才能知道的事项继续留在 Root 闸门；只靠文本或静态证据能证明的事项由对应层完成。当前效率跟进以这个 accepted main 为基准，只增加经验记录和验证分层，不借机重写主线。

### 本次效率 follow-on

本次 follow-on 的主题是减少错误上下文、重复等待和脆弱断言：让 brief 自包含，让 L2 写入精确不相交路径，让脚本负责机械事实，让 Auditor 按风险选择强度，让审核过程可安全中断并报告事实。它不引入队列、调度器、ledger、重试状态或新的 admission token。

## 事件分类：先分因，再定修复

同一个红灯不能自动推出同一种修复。记录事件时使用四类：

1. **执行错误（execution mistake）**：动作违反了已经清楚的边界，例如把不属于自己的路径当成写入目标、把 L2 当成可路由的 manager、或在未获授权时继续扩展任务。修复是撤回/纠正该动作、保留证据并重跑受限检查，不改变合同。
2. **合同或设计缺陷（contract/design defect）**：两个规范面本身给出冲突含义，或没有表达完成所必需的身份、作用域、动作能力。例如 Explorer WDM 命名混淆、Explorer profile 缺失 L1 identity、Explorer singleton 与 scope-key 规则冲突、WDM native-default capability regression。这类问题必须回到拥有该合同的 WDM/Root 设计层，不能让某个测试补丁偷偷决定语义。
3. **脆弱测试（brittle test）**：实现契约是正确的，断言却依赖偶然的精确 prose、大小写、陈旧字段或不稳定临时路径。例如 case-sensitive/精确措辞 PowerShell assertions、stale-field 断言，以及把旧 runtime-pool Map 与新测试解释硬绑在一起。修复是稳定断言、明确来源或更新测试夹具，不降低语义要求。
4. **环境失败（environment failure）**：代码和合同未必有错，但运行环境阻止了证据取得。例如 Windows 长 basetemp 导致 `WinError 206`，或 integrated Reviewer 过慢。修复是短 basetemp、合理超时和 Root 授权的一次安全 interrupt；不能把环境红灯改写成业务通过。

收敛时实际遇到的事件覆盖了四类：`Explorer WDM` 的可见命名使用户误解 owner；旧 runtime-pool Map 与测试互相矛盾；把 `#fragment` 当作 filesystem locator；Explorer profile 没有完整 L1 identity；WDM native-default capability 发生回归；Explorer singleton 规则与 scope-key multiplicity 冲突；PowerShell 对精确 prose、case 和 stale field 过于敏感；Windows 长 basetemp 触发 `WinError 206`；integrated Reviewer 运行缓慢，最后需要一次 Root-authorized safe interrupt，并用同一个 Reviewer 返回 reporting-only 结果。最后一项也说明不能让 manager-only lane 饱和：应把可机械、可局部、精确不相交的工作下沉到注册 L2，而不是让 WDM 亲自承接所有操作。

## 已落实的优化

- **上下文最小但含义完整**：每个 brief 明确 owner、父级、scope key、精确路径、允许动作、完成证据和不允许的外扩；不依赖子代理自行重建历史。
- **作用域与名称分开**：内部 `(role, scope_key)` 用来隔离并发实例；对人可见的任务名只说明工作性质。`WM_<purpose>` 表示 workflow/control-plane，`CM_<purpose_or_direction>` 表示 code，`EM_<direction>` 表示实际 Explorer manager；WM 可以指出研究路由目标，但不冒充研究执行者。
- **并行先行、依赖串行**：不同 scope 且不同冻结路径的 L1 可并行；同一文件、同一未冻结共享契约或需要先集成的 union 必须按依赖顺序执行。完成先后不是语义优先级。
- **动作能力显式化**：L1 由 Root 以 `fork_turns=1` 获得一次背景上下文；注册 L2 由 WDM 以 `fork_turns=none` 接收自包含 brief。前者不是 L1 的持久身份，后者不是缩小版 manager。
- **检查分层**：把测试、静态检查、语义审阅拆开，避免“某个脚本通过”被误报为“设计接受”。
- **稳定执行环境**：PowerShell/pytest 等临时目录使用短 basetemp 约定，避免 Windows 路径长度吞掉真正的证据；审核慢时只允许 Root 按流程安全中断并报告，不以静默取消冒充成功。
- **机械事实脚本化**：确定性映射、字段存在性、路径集合、格式和哈希由脚本执行；LLM 只解释语义和残余风险。哈希/摘要用于完整性或定位，不能作为 workflow admission evidence；Git revision 只是可复查定位器。
- **五个可见进度事件**：统一使用 `DISPATCHED`、`WRITES_COMPLETE`、`TESTS_COMPLETE`、`REVIEW_READY`、`TERMINAL`。它们只是状态可见性事件，不是 scheduler、queue、ledger、retry state、admission token 或 acceptance 记录。事件必须附事实和限制，不能靠终端词替代结论。

## 当前 Root → WM/CM/EM → 注册 L2 拓扑与控制流

从用户请求开始，Root 先判定 owner lane，冻结顶层路径和当前确认计划，然后按作用域派发：

最终控制面可压缩记为：**Root → scope-keyed WM/CM/EM → registered L2**。这里的 scope key 隔离同一角色的并发实例，registered L2 则只承接其父 L1 明确冻结的一片动作能力。

```text
用户请求
   ↓（用户交互、跨 owner relay、路径/Git 生命周期均由 Root 保留）
Root
   ├─ WM_<purpose>  WDM：workflow 设计、修改编排、union 语义验收
   │    └─ 注册 Workflow L2：一个自包含、精确、非重叠的冻结切片
   ├─ CM_<purpose_or_direction>  CPM：代码/技术/运行时所有权
   │    └─ 其注册 code/mechanical/transport L2
   └─ EM_<direction>  Explorer：研究执行与 advisory 研究所有权
        └─ 其注册 research/mechanical/transport L2
```

WM/CM/EM 是可见方向，不是额外的队列层。L1 只在自身 owner lane 内路由；跨 owner 信息返回 Root 再 relay；L2 不联系 Root、用户、兄弟或其他分支，不 spawn，不改 canonical state，不做 Git 或最终 acceptance。

控制流是：Root 派发一个带唯一 scope key 的 L1 → L1 读取自己的 assignment/profile/Role/必要 immediate references → L1 按已确认计划派发 disjoint L2 → L2 只写精确 owned paths 并返回结论与证据 → L1 汇总为 slice candidate → Root 检查路径、revision 和一致性并集成 → Root 对集成 union 派发新的 convergence WDM → convergence WDM 安排一致的 integrated review 并作 union 语义接受 → Root 按接受的路径执行 canonical/Git 生命周期。任何缺失身份、权限、路径或决定都应失败闭合并返回最小缺口。

## 正确派发示例与反模式

以下示例刻意代表不同的语义，而不只是换一个文件名：

**例一：WM 控制面文档切片。** `WM_workflow_efficiency` 在路径冻结后，把“只写一份 H_read 经验文档”的完整 brief 派给 Workflow Implementer：给出中文主题、必须覆盖的事件、仅一个 owned path、允许的直接检查和 force-add 提醒，使用 `fork_turns=none`。L2 不需要也不能自行寻找新的历史或改 Role。

**例二：CM 的机械接口检查。** Root 把一个 code lane 的精确测试夹具修复交给注册 CPM mechanical L2，路径只包含该测试文件；同一 L1 worktree 中另一个 L2 只改互不相交的静态映射文件。两者可并行，L1 在两者返回后才形成一个 candidate。该示例的语义所有权仍在 CM，不能由 WM 代收。

**例三：EM 的单 scope 研究切片。** Root 以 `EM_forward` 和 `scope_key=direction:forward` 派发 Explorer L1，再由其注册 research L2 只整理一个指定证据包到 assignment-specific temporary path。另一个 `EM_reverse` 只有在 scope key、路径和任务意义均独立时才并行；它们不能靠 singleton 名称互相覆盖。

**反模式**包括：把 `fork_turns=1` 的 L1 背景上下文误当作持久身份或 L2 权限；用 `fork_turns=1` 派一个需要自包含 brief 的注册 L2；让 L2 通过路径字段猜测业务目标；让 WDM 直接执行所有 code/research 子任务以“避免派发”；让两个 L2 同写一文件或共享未冻结契约；让 slice packet 宣称 union accepted；把 `WM_Explorer` 当作 Explorer research manager；用短哈希作为准入凭证；把五个 progress events 当队列/重试/验收状态；或在 Reviewer 变慢时未经 Root 授权静默终止并报告通过。

## Worktree、receipt、恢复与释放

一个可写的 L1 assignment 由 Root 发放一个 Root-managed worktree 和 lifecycle receipt。该 worktree 有一个冻结 base；其下多个 L2 共享同一 worktree/base，但必须拥有精确不相交的路径。L2 不创建自己的 worktree，不调用 helper，不运行 Git，不 stage/commit/push。它们的结果合成一个 L1 slice candidate，待 Root 受理后才记录或整合。

Root 负责 receipt 的 provision、record、integrate、release 或 retain，并确保每个 assignment 至多一个 nonterminal receipt。局部失败应记录为 receipt-local failure，由 Root 诊断、重试或 park，不拖累无关 lane，也不让 L2 把临时失败改称终止。完成后 Root 可在接受的精确路径上整合并释放；独立 candidate 或新的 release lifecycle 必须是新的 L1 assignment。当前本文件是 ignored-only 例外，但若要进入版本控制，WDM 接受后 Root 必须显式执行：

```powershell
git add -f -- docs/H_read/2026-08-11_subagent_worktree_workflow_lessons.md
```

## Tests、Static checks 与 Semantic review 必须严格分离

**Tests** 验证实现行为或契约例子，例如注册路由、字段组合、失败分支和受限单元场景；`TESTS_COMPLETE` 表示所需测试层已完成并有证据，不表示设计已接受。

**Static checks** 验证可机械判断的事实，例如 UTF-8 可读性、尾随空白、精确路径集合、固定字段、格式、映射、大小写或摘要。它们应由确定性脚本执行。遇到旧 Map、stale field 或 `#fragment` 这类输入时，脚本应明确失败原因或更新稳定 fixture，而不是让 LLM 猜。

**Semantic review** 判断名称是否让人理解、owner/作用域是否一致、控制流是否保留正确权威、断言是否表达真正契约，以及是否有过度声明。Reviewer 可 advisory；WDM 才能接受其 workflow union。Reviewer 过慢时可以在 Root 授权的一次安全 interrupt 后，以同一个 Reviewer 做 reporting-only 返回；这不是 acceptance。

`Auditor` 应按风险层级选强度：低风险的局部文字/格式变更做静态和最小语义检查；涉及 owner、scope、路径、停止条件或跨 lane 的变更增加合同交叉检查和 integrated review；涉及运行时、canonical reload、外部审阅或用户可见行为的变更必须保留相应 owner/Root 闸门。风险分层不是新的 admission 机制。

断言应稳定地检查契约结构、规范化字段和明确 token；不要把完整自然语言句子、偶然大小写、陈旧字段名或深层临时目录当作唯一真相。Windows 临时目录应采用短 basetemp；路径长度失败属于环境失败，需修环境再取证。

## 一般原则

1. 先冻结意义，再并行动作；并行只减少等待，不改变所有权。
2. 作用域 key 解决并发隔离，不能替代 ticket、queue、ledger、admission 或 continuity identity。
3. 路径是边界，不是任务解释；assignment 是完整语义，字段只是事实锚点。
4. 可机械证明的事实交给脚本，可解释的关系交给 owner，可接受的决定留给对应 L1/Root。
5. 每个结果都要把完成内容、直接后果、限制和残余不确定性分开写。
6. 取消、超时、环境失败和执行错误不能互相伪装；安全恢复要可记录、可重跑、可 park。
7. 可见命名服务于人，内部标识服务于隔离；二者都不能越权。

## 非主张与当前限制

本文不主张已经完成新的 canonical 写入、Git 提交、跨 lane acceptance、研究结论、运行时健康证明或 fresh smoke。本文也不主张 `b0a4bb3b`、`5f45c189`、`2919b950` 的短哈希本身提供完整历史或准入证据；它们只是本次记录使用的修订定位。本文没有重跑 whole suite，没有替 Root 做 reviewer acceptance，没有替 CPM/EM 证明其 owner 领域正确性。

尤其要明确：**Root live runtime/fresh smoke 必须在 Root 完成集成和 canonical reload 后再运行；本次没有运行它。** 因此本文件完成的是经验文档切片和直接文件检查，不是最终发布或运行时收敛。

## 本切片结论与直接检查

本文件已按确认的效率 follow-on 切片写入指定位置，覆盖里程碑、事件分类、优化、拓扑、派发、worktree receipt、检查分层、进度事件、命名、非主张和 Root 待办。直接检查仅限：目标文件存在且可用 UTF-8 读取、内容无尾随空白、Markdown 标题基本可识别；未运行 whole suite、runtime 或 fresh smoke。WDM 接受后，Root 仍需按上文使用 `git add -f --` 显式纳入该 `*.md` 文件。
