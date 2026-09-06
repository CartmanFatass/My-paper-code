# 方案：把一部分 CM 工作交给 Grok Build 执行

日期 2026-09-05。作者：Claude Code 研究枢纽（Fable 5.1）。性质：给所有者的对齐草案，
不是科学卡、合同或决策记录。所有者的问题："将一部分 CM 的工作交给 Grok Build 来运行"。

## 0. 结论（一段话）

可以做，而且现在就能开始，但应分层。本机已装 Grok Build CLI 1.0.5，已用 grok.com 账号登录，
无头模式经一次探针验证可用（模型解析为 `grok-4.6-build`，返回 JSON 收据）。Grok 会自动读取
本仓库的 `AGENTS.md`、`CLAUDE.md`、`.claude/agents/` 和 `.claude/skills/`，所以现有的角色定义
可以原样复用。建议把 CM 链里**不含科学判断、可由独立评审兜底**的工作交给它：先是只读侦察和
第二评审（零风险），再是行为保持的机械修改（工作树内、路径白名单），最后在试点合格后才让它做
低风险的语义实现（文档、测试、运行入口胶水），且每个语义 diff 仍由 Opus 评审。启动实验、Pro
传输、任何科学判断永远不交给它。治理上只需在 `AGENTS.md` 加一段附录 C（约十行）。

## 1. 查到的事实

### 1.1 本机状态（直接观察，2026-09-05 22:10 PDT）

| 项 | 观察 |
| --- | --- |
| 可执行文件 | `C:/Users/fires/.grok/bin/grok`，版本 `grok 1.0.5 (5115b46bc9)`，自动更新开启 |
| 登录 | OIDC 登录 `auth.x.ai`，账号为所有者邮箱，有 team_id；令牌 2026-09-06 09:40Z 到期，CLI 自动刷新 |
| 可用模型 | `grok models` 只列 `grok-4.6`（默认，推理档 high）和 `grok-4.5`；`-m grok-build` 被拒绝（`unknown model id`）；默认模型在用量记录里显示为 `grok-4.6-build` |
| 探针 | `grok -p "Reply READY" --output-format json --max-turns 1 --tools read_file --disallowed-tools Agent --disable-web-search` 返回 `{"text":"READY","stopReason":"end_turn","sessionId":…,"usage":{…},"total_cost_usd":0.0018}`，一轮，约 6.9k token |
| 仓库发现 | `grok inspect` 显示它读取了 `Agents.md`（约 8.4k token）和 `Claude.md`（约 1.1k token）、8 个项目技能（含两个 Claude 技能）、`.claude/agents/` 里的全部 hmasd-* 角色 |
| 配置 | `~/.grok/config.toml`：默认模型 grok-4.6 / high；TUI `permission_mode = "always-approve"`；一个无关的 MCP 服务器（OpenAI 文档） |

### 1.2 无头模式的可用控制（来自随装 README 与 `grok --help`）

- 单轮：`-p <prompt>` 或 `--prompt-file <path>`；`--output-format json|streaming-json|streaming-messages-json`；`--json-schema` 强制结构化返回；`--max-turns N`。
- 工具面：`--tools` 白名单（`read_file,grep,list_dir,run_terminal_cmd,search_replace,web_search,web_fetch,todo_write,task`）、`--disallowed-tools`；`--disallowed-tools Agent` 禁止它再生子代理。
- 权限规则：`--allow/--deny "Edit(glob)" "Bash(prefix*)" "Write(glob)"`，与 Claude Code 的规则语法兼容，deny 优先；`--permission-mode default|acceptEdits|auto|dontAsk|bypassPermissions|plan`。
- 上下文注入：`--rules <text>` 追加系统提示；`--agent <名称或 .md 路径>` 指定代理定义（可直接指向 `.claude/agents/hmasd-cm-scout.md` 这类文件）；`--system-prompt-override` 替换整段系统提示。
- 会话：`-s <id>` 命名会话可跨调用续接；JSON 收据带 `sessionId`、`requestId`、`usage`、`total_cost_usd`。
- 位置：`--cwd`；**无头模式不会用 `--worktree` 建工作树**，工作树要我们自己建再用 `--cwd` 指进去。
- 沙箱：`--sandbox` 只在 Linux（Landlock）和 macOS 生效；Windows 上无沙箱，只能靠权限规则、工作树隔离和评审。
- 其它：`--disable-web-search`；`GROK_MEMORY=0` 关跨会话记忆；`GROK_SUBAGENTS=0` 全局关子代理。

### 1.3 订阅与配额（网络检索，未在本机核实）

Grok Build 需要 SuperGrok 或 X Premium+ 订阅；各档位共享一个按周结算的用量池（Chat、Imagine、
Voice、Build 合并），xAI 不公布固定的请求数。API 侧的 `grok-build-0.1` 按 token 计费，与订阅
分开。本机账号属于哪一档、每周池子多大，从 CLI 看不出来（[ASK-1]）。

来源：
- https://www.ciodive.com/news/xAI-coding-agents-Grok-Build/820422/
- https://www.buildfastwithai.com/blogs/grok-build-xai-cli-ai-agents-2026
- https://felloai.com/grok-pricing/
- https://www.layer3labs.io/guides/grok-build-pricing
- https://github.com/basissetventures/grok-cli-mcp （社区 MCP 包装，说明无头模式的常见用法）

## 2. 哪些 CM 工作可以交出去

现在的 CM 链（`hmasd-cm`，Opus）一次做五件事：读地图、写语义代码、写测试、算成本线、冻结启动
命令。按"错了能不能被现有评审兜住"分层：

| 层 | 工作 | 现在由谁做 | 交给 Grok 的方式 | 风险 | 何时开始 |
| --- | --- | --- | --- | --- | --- |
| A | 只读代码地图（`hmasd-cm-scout`）、一个静态代码事实 | Sonnet | `--tools read_file,grep,list_dir`，`--json-schema` 返回结构化地图 | 零：只读，输出只是搜索覆盖 | 立刻 |
| A | 高风险 diff 的**第二**独立评审（与 `hmasd-reviewer` 并列，不替代） | Opus | 只读工具，输入固定的验收合同和 diff 范围 | 零：多一双不同模型家族的眼睛 | 立刻 |
| B | 行为保持的机械修改（`hmasd-routine-implementer`）：改名、文档、配置、测试夹具、无语义的接线 | Sonnet | 在枢纽建的工作树里，`--deny "Edit(**)"` 加 `--allow "Edit(<owned>/**)"`，`--disallowed-tools Agent,web_search,web_fetch`，不让它提交 | 低：枢纽按路径审阅后再提交 | 试点第一周 |
| B | 有界的运行时/等价性探针（`hmasd-verifier`）在 proof root 下 | Sonnet | 需要 `run_terminal_cmd`，用 `--allow "Bash(<解释器路径>*)"` 收窄 | 中：可执行任意命令；Windows 无沙箱 | 试点第二周 |
| C | 低风险语义实现：运行入口胶水、读出（readout）、测试、CM 记录草稿；**不含**概率、梯度、回放、递归态、RNG、检查点、原生执行 | Opus | 同 B 层的围栏，外加 Opus `hmasd-reviewer` 必审 | 中：由评审兜底 | 三次 A/B 层试点合格后 |
| 不交 | 触及受保护语义的实现、`hmasd-experiment-operator` 启动、Pro 传输、任何科学判断（卡、目标、intake、决策、所有者条目） | Opus / Sonnet / 枢纽 | 不适用 | 违反 AGENTS.md §8 或 附录 B 的分工 | 永不 |

判断依据：`AGENTS.md` §1 明确"本文件约束所有者使用的每一种代理运行时"，所以 Grok 作为第三
个运行时不需要新的权限体系；它得到的是"工作方法"，不是权限。`hmasd-cm` 定义里"触及概率、
梯度、回放、递归、RNG、检查点、结果同一性、原生执行、运行器或完整执行/评估路径"的改动才叫
CM 工作，这些仍归 Opus。

## 3. 接入机制（推荐：枢纽直接调用，不加子代理层）

与所有者对传输的偏好一致（用 shell 和文件监视，不再套一个 Sonnet 子代理），推荐枢纽自己在
Bash 里起一个 `grok -p` 进程（长任务用后台运行，等待用 Monitor 看输出文件），收据落盘。

每次调用的固定形状（A 层示例，只读侦察）：

```text
grok --cwd <worktree 或仓库根> \
     --prompt-file <任务文件.md> \
     --agent C:/Projects/HMASD/.claude/agents/hmasd-cm-scout.md \
     --rules "Return only facts with file:line; never edit; never run tests." \
     --tools read_file,grep,list_dir --disallowed-tools Agent \
     --disable-web-search --max-turns 40 \
     --output-format json --json-schema <地图的 JSON Schema> \
     > temp/directions/<direction>/exp/grok/<task-id>/response.json
```

B/C 层（可写）追加：

```text
     --tools read_file,grep,list_dir,search_replace,run_terminal_cmd \
     --deny "Edit(**)" --deny "Write(**)" \
     --allow "Edit(experiments/candidates/<dir>/**)" --allow "Edit(tests/experiments/candidates/<dir>/**)" \
     --allow "Bash(C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest*)" \
     --deny "Bash(git *)" --permission-mode dontAsk
```

要点：
- **工作树由枢纽建**（`git worktree add .claude/worktrees/grok-<task> -b grok/<task>`），Grok 只在
  `--cwd` 里工作；`--deny "Bash(git *)"` 让它不提交、不推送，枢纽或 clerk 审阅后按路径提交，
  提交信息注明 `Implemented-By: grok-build 1.0.5 (grok-4.6-build)`。这保住 §6 的 git 纪律。
- **每次调用一个任务文件**，内容就是现在发给 `hmasd-cm` 的那种"意义完整的目标"（类、受保护
  语义、拥有路径、停止规则、非目标），加一句"你没有科学判断权，遇到矛盾就返回矛盾"。
- **记录**：任务文件、`response.json`（含 sessionId、usage、cost）、`git diff` 一起放在
  `temp/directions/<direction>/exp/grok/<task-id>/`；CM 记录里写明哪一段由 Grok 产出。
- 关闭它自己的记忆和网络（`GROK_MEMORY=0`，`--disable-web-search`），避免跨任务串味和把网页
  文本当指令。
- 备选：做一个类似 `codex-rescue` 的薄转发子代理 `hmasd-grok-forward`（Sonnet，只有 Bash）。
  它只是把上面这条命令包起来，好处是枢纽上下文更干净，坏处是多一层、少一份可见性。先不做，
  等 A/B 层跑顺再看是否需要。
- 不需要新的脚本或工具链：全部是命令行参数。若以后调用形状稳定，可以加一个 ≤100 行的
  `scripts/hmasd_grok_task.py` 把参数拼起来（属于工作流层，`scope: none`）。

## 4. 治理与记录

- `AGENTS.md` 加附录 C（Grok Build 具体规定），十行以内：Grok 是第三运行时；只承担 §2 表格
  里的工作方法；无头调用的固定围栏（只读或路径白名单、禁子代理、禁 git、禁网络）；产物是待
  评审的 diff，不是任何层级的权威；语义 diff 必经 Opus 评审；启动、传输、科学判断不交给它；
  记录位置。这是治理文件改动，按 §4.7 需要所有者点头（[DECIDE-1]）。
- `.claude/skills/hmasd-research-hub/SKILL.md` 的委派表加一列"可交 Grok"，并写清调用形状。
- 审计账本不变：Grok 产出经评审接受时和现在一样是 `technical` 行；不新增标签体系。
- `.claude/agents/hmasd-cm.md` 不改；Grok 直接读同一份定义文件（`--agent`），保证两边的合同一致。

## 5. 试点（三次，边推进研究边做）

1. **A 层，今天**：给 DISH 新 A/RECON 对象做只读地图（`forecast_package_b02/study.py` 的
   `evaluate_episode` 调用顺序、`observe()` 的 Python 包装、`renew` 标志的来源），JSON 返回。
   对照标准：Opus/Sonnet 侦察的同题地图，看遗漏与错误。
2. **A 层，今天**：对 VNFC 部署模式评估 diff（`main` 上 6fc574561）做第二评审，输入是 CM
   目标里的受保护语义清单。对照标准：与枢纽自己的审阅结论比对。
3. **B 层，本周**：一次机械修改（例如 CM 记录格式、测试夹具或文档修订）在工作树里完成，
   枢纽审后提交。对照标准：diff 只落在白名单路径、测试通过、无多余改动。

通过标准：三次里没有越界（改了白名单外文件、跑了不该跑的命令、编造事实）；用量在每周池子里
可承受；返回结构可解析。通过后开放 C 层，每个语义任务仍配 Opus 评审。

## 6. 风险与限制

- **Windows 无沙箱**：围栏只有权限规则和工作树。`--deny` 是进程内策略，不是操作系统隔离；
  因此 B/C 层永远在独立工作树里跑，且不给 git 权限。
- **模型可选范围窄**：只有 grok-4.6 / grok-4.5；`grok-build` 这个模型名在本账号不可用，实际
  用的是 `grok-4.6-build`。能力是否够 C 层，要靠试点而不是宣传数字（SWE-bench 那类分数不迁移
  到本仓库的原生/PyTorch 路径）。
- **配额不透明**：周池子共享且不公布；建议前几次记录 `usage.total_tokens`，一周后再定期望。
- **指令文件体积**：每次调用注入约 9.5k token 的项目指令，是固定开销。
- **并发**：Grok 不占 Claude 的两方向名额（它是实现者，不是方向链），但一个方向同时只让一个
  实现者写同一路径，避免工作树冲突。
- **不替代传输**：Grok 没有 ChatGPT Pro 的决策节点角色，也不接触 Agentify。

## 7. 需要所有者决定的事

- [DECIDE-1] 是否批准附录 C 与枢纽技能的委派表改动（治理文件，§4.7）。
- [DECIDE-2] 试点顺序是否按 §5（A、A、B），以及是否允许通过后开放 C 层。
- [DECIDE-3] B/C 层是否允许 Grok 运行本机 pytest（需要 `run_terminal_cmd`），还是只改文件、
  测试由枢纽跑。推荐允许但用 `--allow "Bash(<解释器> -m pytest*)"` 收窄。
- [ASK-1] 账号是哪一档订阅（SuperGrok / Heavy / X Premium+），以便估每周可承受的调用数。
- [ASK-2] 是否希望做薄转发子代理（§3 备选），还是维持枢纽直接调用。
