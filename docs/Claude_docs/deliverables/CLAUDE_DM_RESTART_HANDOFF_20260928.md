# Claude DM 交接（WSL 重启前）— 2026-09-28 02:06Z（2026-09-27 19:06 PDT）

面向：重启后的 Claude 会话与 owner。两个方向的全部工作已发表在 origin/main（本会话最后一次提交 46aaff40d；此刻 origin/main = c0796c48b，是 Root 的后续提交，工作树与之一致）。没有任何结果性操作在跑；重启会杀掉的只有一个用于登录的有窗口 Chrome、一个 xclock 测试窗口和一个只读观察脚本，都无需恢复。工作树里唯一的未跟踪文件 `experiments/candidates/energy_relay_diagnostics/b02/__init__.py` 属于其他 writer：不加、不清、不动。

## 1. 重启后第一步（顺序）

1. `git -C /home/fires/hmasd-wsl fetch origin main`，`git status --short`；读 `docs/research/RESEARCH.md#session-routing` 拿当前 Root 地址（此刻 `01a0e560-4333-7b03-8ff3-759a4add1d9a`），并重新武装 inbox 监视（`docs/Claude_docs/inbox/` 在本地 HEAD 与 origin/main 上的新提交，30 分钟续期）。
2. 读根 `AGENTS.md` 第 46–53 行的 owner 试行（2026-09-28 UTC）：新选 Codex 研究改为 Root 带原生 DM 子代理；Claude 仍是平级。这不改变本会话两个方向的归属与记录方式。
3. 显示判定（决定登录走哪条路）：`xclock -geometry 300x300+400+300 -title WSLg-test &`。桌面上能看到时钟 → WSLg 已恢复，走 §2 的 A 路线；仍然只在任务栏、点不开 → WSLg 呈现仍坏，走 §2 的 B 路线（不依赖 WSLg），或请 owner 在 Windows 任务管理器结束 `msrdc.exe`（WSLg 的远程桌面客户端，会自动重连）后再试 A。杀测试窗口用 `pgrep -f "WSLg-tes[t]"` 取 pid 再 kill——`pkill -f` / `pgrep -f` 的字面模式会匹配 Bash 工具自己的 shell 并把它杀掉（本会话出现四次，退出码 144），务必用字符类写法。

## 2. 待办：Pro 评审问题已备好，只差账号登录后一次 `send`

- 问题已发表在 b4479693a：`docs/research/candidates/energy_relay_benchmark/NOTES.md` 的 `## Pro question 2026-09-27 reasoning-phase-candidate-selection`（含 critic 规范与 MATERIAL_DISSENT 要求）。
- 已组稿，不要重组：文档 `temp/pro_transport/hmasd-pro-question-reasoning-phase-candidate-selection.md`（sha256 `4ea361fed3d21fa5ec2a8cee356d030ffd24e9c926a054f061ffe040228448bb`），短消息 `temp/pro_transport/reasoning-phase-candidate-selection.short.txt`；key `hmasd:84c1b66eb2fc64d9e8fac22906c764211993ef40f1a3abc8111578c2c71ec065`（也在 `temp/directions/energy_relay_benchmark/scratch/reasoning-phase-20260927/pro_key.txt`）；本地操作文件 `~/.local/state/hmasd-pro-transport/operations/hmasd_84c1b66e….json` 处于 `send_attempted: false`，两次失败都是 pre-send，什么都没提交。
- 为什么卡住：重启后 keyring 重新上锁，Chrome 自动选 keyring 并在（看不见的）解锁窗口上无限等待，一页打不开；驱动已改为显式传代理并固定 `--password-store=basic`（提交 96b976d44、f409554d4、46aaff40d，变更说明 `docs/Claude_docs/changes/2026-09-27-jev-chrome-proxy.md` 含更正）。页面能打开后 chatgpt.com 显示未登录：旧 cookie 很可能是 keyring 密钥加密的（basic 下出现 "Failed to decrypt token for service AccountId-…"），在 basic 下读不出来。登录是人的动作，我不碰凭据。
- 登录路线（owner 二选一）：
  - **A（推荐）在 basic 下重新登录一次。** `JEV=~/test/Jev/jev-ultrafast/.venv/bin/python; D=tools/pro_transport/jev_send.py`；`$JEV $D chrome stop`；`$JEV $D chrome start --mode headed`，在窗口里登录 GPT 账号（Jev 用的那个，有 6 Pro / 5.6 Pro 与 GitHub connector）。若驱动开的窗口不显示，改用与已验证映射一致的手工命令（同一配置目录、同一端口）：
    `~/.omp/puppeteer/chrome/linux-150.0.7871.24/chrome-linux64/chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.config/google-chrome-for-testing --no-first-run --no-default-browser-check --window-size=1280,900 --window-position=100,100 --password-store=basic --proxy-server="$https_proxy" --proxy-bypass-list="$(echo "$no_proxy" | tr ',' ';')" --ozone-platform=x11 --disable-gpu https://chatgpt.com/ &`
    只读观察脚本 `temp/directions/energy_relay_benchmark/scratch/reasoning-phase-20260927/login_observer.py`（用 Jev 的解释器跑，检测到已登录页即退出）。
  - **B（不依赖 WSLg）DevTools 实时画面登录。** 任一 Chrome（headless 也可）开着 9222 端口时，owner 在 Windows 的 Chrome 打开 `chrome://inspect/#devices` → Configure 加 `localhost:9222` → 对 "ChatGPT…" 目标点 inspect，在实时画面里登录。
  - **C（恢复旧会话）** 需先把 `chrome_start` 里的 basic 固定改成可配置，再让 owner 回答 keyring 解锁提示；提示也是 WSLg 窗口。不要单方面回退固定。
- 登录后：`$JEV $D chrome stop`（有窗口实例），然后 `$JEV $D send --key <key> --prompt-file temp/pro_transport/reasoning-phase-candidate-selection.short.txt --attach temp/pro_transport/hmasd-pro-question-reasoning-phase-candidate-selection.md --conversation new --dry-run`，成功后去掉 `--dry-run` 同命令发送一次（6 Pro；只有 6 Pro 不可用的具体信号才 `--effort "5.6 Pro"`，且先 dry-run）。发送被接受后用后台 `wait --key <key> --answer-file <path> --timeout <s>` 观察，再 `deliver --key <key> --branch main --source-sha b4479693a0bfde5dbb2b9548321f63d6db05a0c1 --target-path docs/research/candidates/energy_relay_benchmark/NOTES.md --question-heading "## Pro question 2026-09-27 reasoning-phase-candidate-selection" --answer-out <path>`。读完整答复，在 NOTES 新条目记录采纳/异议；在此之前不声明、不买 fit。
- 发送前健康检查：`chrome status`；用 `curl -X PUT 'http://127.0.0.1:9222/json/new?https://example.com/'` 开一页，10 秒内 `/json/list` 里标题应为 "Example Domain"。

## 3. 两个方向的科学状态（只读指针）

- `energy_relay_benchmark`（Claude DM）：owner 决定 A（e2cad37ae）关闭 T′ 信用线；推理阶段条目 1（b4479693a）给出零 fit 读数（读器 `experiments/candidates/energy_relay_benchmark/b04/deployment_readers.py`，记录 `runs/energy_relay_benchmark/b04_deployment_reading_a01/`）：学习器前 100 步航向按编号固定于地图坐标系（R_map .60，早期 .76–1.00；R_spawnrel .20），规划器相反；64% UAV-步贴墙；奖励势能对无回程 UAV 恒为 0。选定候选 = HMASD 协调器的关系型目标解码（两个实体指针 + 分数 → 线段上的目标点；低层用已实现的 GAS 目标条件化 discoverer），消融臂 A（绝对坐标目标），预测 P1–P4，首个实验 2 fits ≈ 26 h GPU + 6 h CPU，**仅在 Pro 评审后声明**。边界：DM3 `uav_cooperative_planning`（reserve）、Root 的 `uav_transit_handoff`（自有 DM `01a0e577-d190-70a1-9526-9d1765eab830`）均不重合；SCOPE 消息已发给 Root，无需回复。
- `sequential_coordinator_credit`（Claude DM）：owner 决定 A 关闭到 reserve；首格读数（D 输给 SeqAU，C1 未满足）不变；Root 独立审查的收窄已接受并记入 NOTES/RESEARCH（+.007 不是协调价值上界；不外推为宿主范围的信用排除；成本 35.39 min / ≈ 4.71 h 累计 worker 墙钟，CPU 未测）；scratch 已删并记录。

## 4. 会话级事实

- 解释器：科学 `/home/fires/.venvs/hmasd-linux-cpu/bin/python`（跑测试时把它的 `bin` 放到 PATH 前面）；控制面 `/home/fires/.venvs/hmasd-linux-science-tools/bin/python`（`tests/skills/test_jev_transport.py` 91 项，约 4 s）。永不安装、永不用 `/mnt/c` 的 python.exe。
- 分类器拒绝（原文类别，不再以任何方式追求同一结果）："[Safety Bypass Flag]"——带 `--no-sandbox` / `--disable-features=NetworkServiceSandbox` 的诊断 Chrome 实例；"[Credential Exploration]"——读取配置的活 cookie 库 `Default/Network/Cookies`。此前已知：治理文件与部分 Claude_docs 提交曾被拒（本会话 `docs/Claude_docs/changes/` 与 `deliverables/` 的提交通过）。
- Peer 通道：出站 `CODEX_HOME=/mnt/c/Users/fires/.codex CODEX_SQLITE_HOME=/home/fires/.codex/sqlite codex queue --thread <当前 Root> --message "<text>"`；首次可能返回 "no rollout found for thread id"，同命令重试一次即可；一事一信、无 ACK 循环。入站 = `docs/Claude_docs/inbox/` 的日期文件。
- 网络：`ip route` 里 198.18.0.2 的 TUN 默认路由吞掉直连流量，只有本机代理 `127.0.0.1:7890` 通；驱动已把 shell 的 `https_proxy` / `no_proxy` 显式传给 Chrome。
- 草稿位置：`temp/directions/energy_relay_benchmark/scratch/reasoning-phase-20260927/`（gitignored，含 Pro 消息原文、key、读数脚本、窗口截图 `headed_window.png`、观察脚本）。`/tmp` 下的会话草稿重启后可能被清。
- 记忆目录 `~/.claude/projects/-home-fires-hmasd-wsl/memory/`：两个方向状态、Jev keyring 事故（`jev-chrome-keyring-stall-20260927.md`）、pkill 自匹配教训均已更新。
