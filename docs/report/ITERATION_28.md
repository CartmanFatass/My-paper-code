# 迭代 28:复合条件里那一半从未被变化过

日期:2026-07-27 · 分支 `untied-k` · 支撑性工作,不消耗结论性迭代额度
(授权余量维持 17)。

## 发生了什么

继续按"把测试名字当规格读"扫,进入 §2 认证谓词。两条发现,形状与前几例不同:
**一个 `if` 里合了两个条件,而所有夹具只违反其中同一个。**

### 7. `certify_stable` 从未见过 `active=False`(真实缺口)

```python
if not (active and has_valid_incumbent):
    reasons.append("no_valid_incumbent")
```

五个入参、四个条件——`active` 被折进第一个合取项,**并共用它的 reason 字符串**。
五条兄弟测试覆盖了 `has_valid_incumbent`、位移界、`scheduled_to_leave_within_delta`
和空合法集,**没有一条传 `active=False`**。

变异(把 `active` 从合取里删掉):**181/181 全绿**。非活跃无人机随即可认证为
stable,把冻结 §2 谓词排除的事件放进来,**扩大估计量的条件集**——这正是本项目
implementer 规则里"永远不算普通设计缺口"的那一类。

### 8. `certify_flex` 的链式比较(真实缺口,但只是纵深防御)

```python
if not (prior_check_step < leave_step <= t_e):
```

所有夹具的 `leave_step` ∈ {479, 480, 485} 而 `t_e = 490`,**上界由构造满足**,
只有下界被违反过。删掉 `<= t_e`:**182/182 全绿**。

**严重性按实测说,不拔高。** 唯一的生产调用点(`:2152`)传的是
`leave_step=t+1, t_e=t+1`,所以该界在今天的路径上不可达,这条守卫的价值是纵深
防御而非活风险。把它说成第八个警报,就是把"过度采纳一个看似成立的发现"重演一遍。

**查可达性时掉出来一个更有意思的事实**:同一调用点传 `prior_check_step=t`、
`leave_step=t+1`,所以下界也恒真——`leave_not_after_preceding_check` 在生产路径上
**根本不可能触发**,整条谓词在唯一调用点退化。这源于"事件即离开、故
`t_e == leave_step`",本身自洽;记录它,是因为一条生产路径无法触发的冻结谓词在
合约里读起来像覆盖,而它不是。

两条修复均观察过 RED→GREEN。242 项测试绿,生产代码未改动。

### 扫过且干净的

`focal_eligible_to_act`(四条件逐一翻转)、`compute_conformance_ok`(三合取逐一
翻转)、`certify_flex` 的五个 reason 字符串(全部被断言)、`support_ok` 第二合取项
(测试第 245 行取 `False`)。

**报告干净项和报告命中同样重要**:一份只报命中的扫查,不提供任何关于覆盖面的信息。

## 新增推论

八例中六例可由"名字即规格 + 检查量词"捕获。本轮两条补上一条推论:
**复合条件需要每个操作数各一个负例**——共用一个 reason 字符串会让两个条件看起来
像一个。

## 下一边界

`USER_COMPUTE_AUTHORIZATION`。剩余量词候选:
`test_state_hash_is_sensitive_to_every_digested_key`、
`test_user_world_seed_is_disjoint_from_every_other_registered_seed`、
`test_legal_set_never_excludes_for_unreachability_within_delta` 等。

## 时间分布(迭代 28)

墙钟只对可测项给数;本会话经过时间未测,不编造。

| 桶 | 内容 | 约计 | 占比 |
|---|---|---|---|
| 科研推进 | 谓词逐条对照、两次变异、可达性追踪、两条修复及 RED 观察 | 大头 | ~70% |
| 核定/仪式 | 证据笔记、迭代报告 | 中 | ~25% |
| 损耗 | 无 | — | ~5% |

可测锚点:聚焦测试 0.3–0.6s;全相关套件 242 项约 24s。

**无事故**。

**下轮削减**:干净项的确认这轮花了不少读代码时间;下轮先用"生产端 reason/条件
清单 vs 测试端断言清单"对拉一次差集,再只读差集里的项。
