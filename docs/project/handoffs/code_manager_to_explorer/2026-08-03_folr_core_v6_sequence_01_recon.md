# FOLR Core v6 Sequence 01：只读工程侦察结论与 External Pro 审计草案

## 结论

现有 variable-roster event runtime 足以重建 FOLR 六核判别器所需的大部分事件顺序、owner/epoch 身份约束、动作概率计算和 RNG 所有权，因此可以进入一次单候选 External Pro 科学审计；但它还不能直接执行或解释该判别器。

障碍不是“没有任何动作概率接口”。代码能够从已经写入 `high_ledger` 的 `EventTokenRow` 无采样地重放精确 softmax 概率向量。真正缺少的是更严格的对象：仓库没有名为 S03 的状态或其 payload 写入协议，没有正式的 registered-cell 注册表，没有把 complete reset 定义为一个原子入口，也没有在第一次事件后计算发生时截取 fresh kernel 的公共接口。现有 replay 读取的是落账后的不可变 token，而不是证明该 token 当初来自无缓存、无 pending action 的首次重算。

此外，branch label 目前有明确的非 S03 可见路径：`is_genuine_join/is_rejoin` 被编码为 `event_flags` 并直接输入 policy；环境 observation 又包含 owner、此前 action、wave 和 roster 等事件相关字段。若未来只替换一个假定的 payload 而不固定这些字段，任何 kernel 差异都不能归因于 S03。

因此，本次侦察没有形成 FOLR 的科学支持或反驳。它形成的是一个可审计的工程边界：先由 External Pro 决定 S03 在当前 runtime 中应绑定到哪个明确对象、怎样定义 information-matched transplant 与 complete reset、以及六核设计是否足以识别最窄的“payload 介导首次事件后动作”主张；随后才可能设计代码 fixture，并在另行获得明确计算授权后执行。

Explorer 消息中的 source locator `3c0059c705...` 是转录错误。Git 中实际存在、且当前 `HEAD == origin/aggressive` 的完整提交是 `3c0059cbd9cccbb43fd7c8672209febef12fb648`，提交主题为 `handoff: publish FOLR core v6 sequence 01 brief`。这不影响 brief 内容或候选身份。

## 当前实现的数据流

```text
DynamicRosterEventEnv
  reset/step -> MembershipTransaction(pre snapshot, deltas, post snapshot)
        |
        v
VariableRosterEventCore.bind_due_frontier
  校验 key+epoch -> clone records -> 模拟 delta -> 重建 due frontier
        |
        v
VariableRosterEventCore.apply_transaction
  pre-event critic/trace closure
  -> self.records = trial                 [核心 linearization 点]
  -> _process_frontier(post snapshot)
       frontier_rng 决定 owner token 顺序
       -> encode_members(observation, skill, age, event_flags)
       -> set_summary
       -> logits(owner embedding, summary, pre high_hidden)
       -> legal mask / softmax
       -> teacher | argmax | action_rng sample
       -> 更新 skill/high_hidden
       -> opportunity_rng 生成下一机会间隔
       -> EventTokenRow 追加到 high_ledger
        |
        v
runner: batched_low_step -> environment step -> complete_primitive_transition

只读审计路径：
EventTokenRow -> replay_token_distribution -> 精确 softmax 概率向量
```

## 九个工程问题的回答

### 1. owner identity、epoch 与 slot reuse

- `BoundaryMember` 携带 `lifecycle_key` 和 `membership_epoch`；注释明确两者用于 routing，不直接作为模型输入。
- `LifecycleRecord` 是 core 的权威 owner 状态，保存 key、status、epoch、low/high hidden、skill、age、机会时钟、open trace 和 join/rejoin flags。
- `VariableRosterEventCore._new_record()` 只为新 key 创建 epoch 0。
- `_validate_snapshot()` 要求 active key 集合与 records 精确一致，并逐项比较 epoch；旧 epoch 在任何 mutation 之前失败。
- `_simulate_deltas()` 禁止 `JOIN` 复用已出现的 lifecycle key；temporary leave 保留同一记录和 epoch；`REJOIN` 要求临时离开状态并将 epoch 加一；terminal leave 保留 terminal 记录、清空 hidden/skill，从而继续阻止同 key 重新 JOIN。
- 现有测试环境可以复用物理 presentation/整数槽位，但 core 的 authority 是 key+epoch。静态代码未发现绕过 epoch 检查的正常 transaction 路径。

静态事实足以证明正常入口 fail closed；未来 runtime 仍需记录六个分支使用同一 key、同一 epoch、同一 pre snapshot，不能仅凭槽位编号推断 owner 连续。

### 2. S03 私有状态与写入顺序

仓库中没有 `S03` 标识、S03 类型、payload 字段、写入函数或注册表。最接近“owner-private recurrent state”的现有对象是 `LifecycleRecord.high_hidden`，另有 `low_actor_hidden`、`low_critic_hidden`、`active_skill` 和 `open_event_trace`，但把其中任何一个直接宣布为 S03 都会越过当前科学合同。

高层事件的真实写入顺序是：读取 owner 的 `high_hidden` -> 计算 logits/new hidden -> 决定 action -> 写回 `active_skill` 与 `high_hidden` -> 写 opportunity gap/open trace -> 追加 `EventTokenRow`。低层 primitive transition 则另行写 low hidden 与 `low_ledger`。因此 External Pro 必须先冻结“S03 是哪个字段、payload transplant 改写什么、在上述顺序中的哪一点完成”。

### 3. 事件 linearization 与 rebuild

- 环境 `_prepare()` 先创建 pre snapshot，再应用 membership change，最后创建 post snapshot 和 pending `MembershipTransaction`。
- `bind_due_frontier()` 对 pre/post/epoch 做二次验证，并从 core 私有的机会时钟重建最终 frontier。
- `apply_transaction()` 先计算离开者的 pre-event critic/trace closure，再执行 `self.records = trial`；这是 core 内权威身份状态的明确 linearization 点。随后 `_process_frontier(post)` 计算高层事件动作。
- runner 的顺序是 `bind -> apply -> 保存 post snapshot -> low_step -> env.step -> complete_primitive_transition -> 下一 transaction`。

observation 与 critic features 由环境在 post snapshot 构造时重建；legal mask 在当前 `_process_frontier()` 中不是 typed rebuild，而是对所有 `n_skills` 固定为全 True。若 FOLR 主张要求 typed mask，当前 runtime 还没有对应实现对象。

### 4. 第一次事件后 kernel、缓存、RNG 与 pending state

高层 action kernel 由 post snapshot 中的 observations、skills、ages、`event_flags`、owner 的 pre-token `high_hidden`、前序 token 造成的 working summary、全 True legal mask 和当前模型参数计算。frontier 顺序由 `frontier_rng` 控制；随机 action 使用独立 `action_rng`；机会间隔使用 `opportunity_rng`。

代码未发现一个持久化的“kernel cache”或“logit cache”。但以下对象会跨边界保存并可能携带 branch 信息：

- `high_ledger` 中的完整 `EventTokenRow`；
- `low_ledger` 中未完成的 low transition；
- per-owner high/low hidden、skill、age 与 open trace；
- core 的 `pending_membership_transaction` 和 `current_observation_state_boundary`；
- 环境的 `_pending_event_transaction`、预采样环境 ledger 与 observation state；
- 三个 PCG64 RNG 的完整状态。

因此“未发现显式 kernel cache”不等于完成了 no-cache/no-pending closure。

### 5. fresh recomputation 的可证明性

`_process_frontier()` 静态上每次都会重新调用 `encode_members -> set_summary -> logits`，而不是读取一个 logits cache。可是当前接口只在计算结束后留下 `EventTokenRow`。`replay_token_distribution()` 再次对该 row 做 teacher-forced 重算；它可以验证给定 row 对应的概率函数，却不能独立证明原始 row 是“共同 pre snapshot 之后、事件完成之后、没有 pending action/RNG 偏移的第一次 readout”。

最小未来 witness 应在 `_process_frontier()` 内首次 owner token 计算点记录：候选 cell id、key+epoch、pre/post transaction identity、token position、完整输入字段、模型参数版本、legal mask、pre hidden、frontier/action/opportunity RNG 的进入状态或等价冻结见证、logits 与完整概率向量。fixture 还应断言该分支之前没有候选 owner 的 token、low action 或旧 row 被复用。

### 6. branch label `B` 的非 S03 路径

当前至少有以下具体旁路：

- `event_flags=[is_genuine_join,is_rejoin]` 直接拼接进 policy member encoder，也进入 event critic；
- observation 包含当前时间、active count、是否存在 persistent owner、当前 member 是否 owner、wave、previous action、active steps 等事件相关字段；
- active key 集合、frontier 集合及 frontier token 顺序；
- pre-token skills/ages、owner/non-owner hidden 与 working summary；
- legal mask（当前虽恒为全 True，未来 typed mask 可能泄漏）；
- 环境预采样 ledger、pending transaction、三套 core RNG 的消费次序；
- open trace、ledgers 和 slot-local low state。

共同 pre snapshot 加 payload transplant 只能封闭这些路径的一部分。fixture 必须逐字段证明四个 factorial 分支除 S03 payload 外完全相同，或对不可相同字段提供一个经 External Pro 接受的 information-matched null。

### 7. complete reset 的当前含义

当前没有 complete-reset API。

- `DynamicRosterEventEnv.reset_event_runtime()` 只创建新环境，不重建或清空已有 core。
- `VariableRosterEventCore.clear_rollout_ledgers()` 只清空四类 ledger，并在有 open trace 时拒绝执行；它不清 records、hidden、skill、pending transaction、observation boundary 或 RNG。
- `close_terminal()` 关闭 trace/边界，但不是状态归零。
- checkpoint/restore 会精确保存并恢复 lifecycle records、三套 RNG、ledgers、pending transaction 与 observation boundary；它是 persistence，不是 reset。

所以 `K_reset_0` 与 `K_reset_1` 目前没有可调用的共同语义。External Pro 必须先判断 reset 应只擦除候选私有 payload，还是擦除所有事件后可见状态并从共同模型/环境快照重建。工程上更安全的实现形状可能是从同一个冻结 pretreatment fixture 分别构造全新 core/environment clone，而不是在已经运行的 core 上调用不完整清理函数。

### 8. registered cell

正式 registered-cell 对象不存在。测试中有可复用的敏感性原型：variable-roster event tests 构造 `n_skills >= 2` 的 core，并把 `skill_head.weight[0,0]` 与 `[1,0]` 设为相反符号，从而建立至少两个合法动作和非零 readout sensitivity。实现中的 legal mask 全 True。

这还不满足 brief 的 registered-cell 条件，因为它没有稳定 cell id、正式权重见证、S03 payload 绑定、统一 pretreatment snapshot、owner-epoch continuity 证明和 complete reset。它只能作为未来 fixture 的候选原型，不能当作当前已注册实例。

### 9. 精确动作概率核接口

`replay_token_distribution(row, summary_source=...)` 返回完整 `float64` softmax 概率向量，无采样且不修改 runtime；就“给定一个已经落账的 row”而言，这是精确概率核读出，而不是 logits 或 sample 代理。

限制是它依赖已存在的 `EventTokenRow`，并 teacher-force row 中保存的 observation、skills、ages、flags、pre hidden 和 legal mask。它不是 prospective first-readout hook，无法单独证明 row 的 freshness 或排除构造 row 之前的 branch leakage。未来 fixture 应直接截取首次 `_process_frontier()` 的概率向量，并用 replay 接口作一致性复核。

## 关键代码证据

| 事实 | 路径与符号 |
|---|---|
| typed boundary 与 key+epoch | `ha_ctse_process/variable_roster_event_types.py`: `BoundaryMember`, `BoundarySnapshot`, `MembershipTransaction`, `LifecycleRecord`, `EventTokenRow` |
| owner/epoch 创建与检查 | `ha_ctse_process/variable_roster_event.py`: `_new_record` 276，`_validate_snapshot` 298，`_simulate_deltas` 319 |
| linearization 和高层动作 | 同文件：`bind_due_frontier` 548，`apply_transaction` 590，`_process_frontier` 666 |
| 概率核重放 | 同文件：`replay_token_distribution` 855，`replay_event_token` 910 |
| ledger-only 清理 | 同文件：`clear_rollout_ledgers` 1351 |
| persistence 与 pending/RNG | 同文件：`checkpoint_payload` 1391，`restore_checkpoint_payload` 1489 |
| branch-visible policy inputs | `ha_ctse_process/variable_roster_event_models.py`: `encode_members` 55，`set_summary` 93，`logits` 105 |
| 环境 pre/post transaction | `ha_ctse_process/dynamic_roster_testbed.py`: `_event_snapshot` 377，`_prepare` 397，`event_transaction` 443 |
| branch-correlated observations | 同文件：`_observation_for` 449 |
| environment reset/snapshot | 同文件：`reset_event_runtime` 719，`snapshot_event_runtime` 754 |
| 生产调用顺序 | `ha_ctse_process/event_process_runner.py`: evaluation loop 220-269 |
| readout-sensitive test原型 | `tests/process/variable_roster/ha_ctse_process_dynamic_roster_event_test.py`: `_make_core` 与 `joined_prefix_read`；`tests/process/variable_roster/ha_ctse_process_variable_roster_event_test.py`: opposite `skill_head` weights 509-510 |

只读搜索在上述候选局部源文件与测试中没有找到 `S03` 定义。所有定位均来自静态源码；未执行测试、fixture、runtime、training 或科学计算。

## 建议冻结的单候选 External Pro 审计问题

下面是建议的问题边界，不是预设答案，也尚未提交：

> 我们只审计 `CAND-VAP-FOLR-CORE@constructive-revision-v6` 的一个窄设计，不审计回报、完整 lifecycle ledger、跨 epoch carry、delayed credit 或 coordination。现有 runtime 用 `lifecycle_key+membership_epoch` 管理 owner；membership transaction 在 `self.records=trial` 后调用 `_process_frontier`，policy 输入包括 post-event observations、skills/ages、显式 join/rejoin flags、pre high hidden、working summary 和全 True legal mask。frontier/action/opportunity 使用三条独立 PCG64 stream。`replay_token_distribution` 能从已落账 token 精确重放 softmax 概率，但没有 prospective first-kernel hook。代码中没有命名 S03、registered-cell registry 或 complete-reset API；join/rejoin flags 与环境 observation 是明确的 branch-label 旁路。
>
> 计划中的确定性设计从一个共同 pretreatment snapshot 克隆六个分支：四个 `payload P ∈ {0,1} × branch B ∈ {0,1}` transplant 分支和两个 complete-reset 分支。要求固定 payload 时改变 B 不改变 kernel，至少一个固定 B 下改变 P 会改变 kernel，两个 reset kernel 相等，且 owner epoch、支持、legal set、模型参数、token position、frontier order、RNG 条件和所有非 S03 输入都闭合。
>
> 请判断：
>
> 1. 在上述 event/cache/RNG closure 真正成立时，这六个精确概率核是否足以识别最窄的“安装后的私有 payload 介导第一次事件后动作核”主张？它识别的是 controlled direct effect、mediated access，还是更弱的功能依赖？
> 2. 固定-payload 2×2 transplant 与 complete-reset equality 是否已经是最强的简单 null？考虑当前显式 event flags、observation/rebuild、working-summary 与 RNG/order 路径，是否还必须加入 information-matched null；若需要，请给出最小、不可继续删减的第七/第八分支定义。
> 3. 在写代码或运行计算之前，S03 必须绑定到哪个层级的对象：一个明确 `LifecycleRecord` 字段、完整 private-state tuple，还是事件更新函数的输出？complete reset 应擦除哪些字段，哪些字段必须共同冻结？
> 4. “第一次 fresh kernel”必须用什么实现见证：在 `_process_frontier` 内直接截取概率、从不可变 token replay、二者一致性，还是还需要证明此前没有 owner token/pending low action/RNG consumption？
> 5. 请把未来结果划分为最小类别：支持窄主张、反驳 payload access、固定-payload null 失败导致识别无效、reset null 失败、接口/实例不足。每类最多允许推出什么，明确禁止推出什么。
> 6. 测试中的相反 `skill_head` 权重原型能否作为 readout-sensitive registered cell 的工程实现，还是它会人为保证 payload effect，从而需要一个预先存在且与判别器无关的 registration rule？

提交给 External Pro 时应只附与上述实现事实直接相关的公开 GitHub 固定提交链接，不附 `local_research`、任务历史或其他候选材料。推荐的固定源码定位为：

- `https://github.com/CartmanFatass/My-paper-code/blob/3c0059cbd9cccbb43fd7c8672209febef12fb648/ha_ctse_process/variable_roster_event.py`
- `https://github.com/CartmanFatass/My-paper-code/blob/3c0059cbd9cccbb43fd7c8672209febef12fb648/ha_ctse_process/variable_roster_event_models.py`
- `https://github.com/CartmanFatass/My-paper-code/blob/3c0059cbd9cccbb43fd7c8672209febef12fb648/ha_ctse_process/variable_roster_event_types.py`
- `https://github.com/CartmanFatass/My-paper-code/blob/3c0059cbd9cccbb43fd7c8672209febef12fb648/ha_ctse_process/dynamic_roster_testbed.py`
- `https://github.com/CartmanFatass/My-paper-code/blob/3c0059cbd9cccbb43fd7c8672209febef12fb648/ha_ctse_process/event_process_runner.py`

## 推荐的下一步

Explorer 先对这份结论做科学 intake，并确认这确实是其希望送交 External Pro 的单候选问题边界。Code Manager 在收到对应语义回传前不提交 Pro、不实现 fixture、不启动 Sequence 02。即使 External Pro 冻结设计，代码和运行仍分别需要 Code Manager 的技术接受流程与用户明确的计算授权。
