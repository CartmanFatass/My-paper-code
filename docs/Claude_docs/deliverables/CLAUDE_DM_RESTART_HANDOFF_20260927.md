# Claude DM 交接（机器重启前）— 2026-09-27 15:40Z

面向：重启后的 Claude 会话与 owner。两个方向（`energy_relay_benchmark`、`sequential_coordinator_credit`）的全部工作已发表在 origin/main = `973d4e37fb18f20354e05b98c798951717c4b447`；本会话没有未提交的改动。唯一在跑的操作是 `b01_first_cell_a01`（supervisor pid 2823708，runner pid 2823709，`local_linux`），重启会杀掉它。

## 1. 重启前的选择

- 进度：15:39:51Z 完成 42/100 种子，约 18 s/种子 → 训练约 15:58Z 结束，读数约 4 分钟 → 预计 16:02Z 前后写出 `runs/sequential_coordinator_credit/b01_first_cell_a01/process-exit.json`（声明上界 17:27Z）。
- 选项 A（若能等约 25 分钟）：等 `process-exit.json` 出现再重启。`first-cell/summary.json`（status COMPLETE）与 `first-cell/regret.npz` 落盘即持久，重启后直接读。
- 选项 B：现在重启。运行被杀，a01 保留为失败根（`first-cell/summary.json` 停在 INCOMPLETE、无 `regret.npz`、`progress.jsonl` 停在中途），不复用、不覆盖；重启后用同一声明、同一命令换新根 `b01_first_cell_a02`（§3），成本约 34 分钟，0 UAV fit。

## 2. 重启后第一步

1. `git -C /home/fires/hmasd-wsl fetch origin main` 与 `git status --short`。工作树里的 `docs/research/candidates/energy_relay_availability/NOTES.md`、`docs/research/candidates/energy_relay_imitation/NOTES.md`（已修改）和 `docs/research/candidates/uav_cooperative_planning/`、`experiments/candidates/energy_relay_availability/b04/`、`experiments/candidates/energy_relay_availability/run_b04.py`、`experiments/candidates/energy_relay_diagnostics/b02/__init__.py`、`tests/experiments/candidates/energy_relay_availability/b04/`（未跟踪）是其他 writer 的：不加、不清、不动。
2. 重新武装 inbox 监视（Root→Claude 通道）：观察 `docs/Claude_docs/inbox/` 在本地 HEAD 与 origin/main 上的新提交，每 30 分钟续期一次。
3. 看 `runs/sequential_coordinator_credit/b01_first_cell_a01/process-exit.json`：
   - 存在、`exit_code` 0、`first-cell/summary.json` 的 status 为 COMPLETE → 按 SCC NOTES 2026-09-27 条目 "First cell implemented … cost bound and reading rules fixed before launch" 的规则 1–3 读。先读 `summary.json` 的聚合：`E4_minus_E3_binding_corner`（每个熵设置的 mean / se / n）、`regret[role].entropy[label].arms` 与 `paired_differences`、`readings[role][label].update_{0,40,200}.arms[arm][calibration]`；npz 轴：训练 `[configuration, arm, entropy, seed]`，读数 `[configuration, entropy, snapshot, arm, seed]`，不要转置。规则 3 两个快照（40、200）都报，说明哪一个达标。
   - 不存在或 `exit_code` 非 0 → §3 重启 a02。
4. 发表：`git add` 显式路径 —— `runs/sequential_coordinator_credit/b01_first_cell_a01/{launch-manifest,launch-status,admission-preflight,process-exit}.json` 与 `first-cell/{config,summary}.json`（`regret.npz`、`progress.jsonl`、`*.log` 被 .gitignore 忽略，留本地）；SCC NOTES 读数条目；RESEARCH 行（单元格内不能出现 `|`）。提交信息以 `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` 结尾；`git push origin main`。
5. 用中文向 owner 汇报。RESEARCH 发表即为对 Root 的通知；只有具体需要时才发 peer 消息。

## 3. 重启 a02 的精确命令（仅当 a01 被杀）

在 `/home/fires/hmasd-wsl` 以裸命令运行（不要 `cd`/`PATH=`/`&&` 链，否则 allow 规则不匹配；launcher 自己应用节点的 `path_prefix`）。sha 必须已在 origin 上（此刻 `973d4e37fb18f20354e05b98c798951717c4b447`；若先提交了新改动，用新的 HEAD）：

```
/home/fires/.venvs/hmasd-linux-cpu/bin/python scripts/hmasd_launch.py launch --direction sequential_coordinator_credit --lead "Claude DM (WSL session)" --sha <full sha on origin> --output /home/fires/hmasd-wsl/runs/sequential_coordinator_credit/b01_first_cell_a02 --snapshot --node local_linux scripts/run_sequential_coordinator_credit_b01.py first-cell --out /home/fires/hmasd-wsl/runs/sequential_coordinator_credit/b01_first_cell_a02 --launch-sha <same full sha> --seeds 100 --updates 300 --workers 8 --host-matched 0.9,2,0.2
```

准入检查：direction、runner 路径（runner 里 `require_admission(__file__, direction="sequential_coordinator_credit")` 必须是字面量）、解释器、源 sha 已发表、`--lead` 与 RESEARCH 负责人栏逐字相等、重复 claim、启动前的实际内存预检。a01 的 claim（`.git/hmasd-admission/285d3e49d7a3c14b6b503e81cccc48b8dcf62c969c2eff17321b0c993c59b544.json`）绑定 boot_id，重启后进程身份自然失效；若准入仍以重复 claim 拒绝，原文报告，不绕过。启动后在 SCC NOTES 追加一条："a01 因机器重启被杀；a02 同一声明、同一命令、同一规则"，并挂一个分离等待器观察 `process-exit.json`。

## 4. 两个方向的状态

### sequential_coordinator_credit（Claude DM）

- 已发表链：声明与修订 1 → Root 反例接受（"AND 下 D 无梯度"撤回）→ 宿主坐标（b03_credit_a01）→ L0（`temp/directions/sequential_coordinator_credit/L0_first_cell.md`）→ 实现 63da2bfff → 校准读数、成本上界、规则 1–3（da8824a78）→ runner 字面量修复 6741de83f → 启动记录 341c898ad → 3.28 更正 973d4e37f。
- 关键读数：12 个 K = 4 配置无一达到宿主 Σ D / R ≈ .40（均匀策略 S1 ∈ [.69, 1.16]）；结构原因是微宿主回程对中继二值（任一 RELAY → B），而宿主是分布式多跳中继（每步 3.28 架 UAV 充当中间节点，中继路径约 2 个中间节点，最长 5 跳）并在移除后重路由，服务者冗余来自几何覆盖。宿主匹配槽 = index 11 (β .9, s 2, σ .2)，"最近、未匹配"；绑定角 = index 9 (β .9, s 1, σ .2)。成对残差符号：负 = 互补（AND），正 = 可替代（OR）。
- 规则：规则 1 绑定角 E4 − E3 配对遗憾差，两个熵设置都 < 0 且 |Δ| ≥ 2 SE 才算 D 赢 → (a) D 仍是候选，但 T′ 不用 D，需 K = 6 多中继格；否则 (b) T′ 的信用臂默认 SeqAU，不买第二个 D 格。规则 2 天花板（各臂都在 E3* 的 2 SE 内 → 本格不判别，仍取 (b)）。规则 3 = benchmark 的 C1：被选信用臂对 E1 在两个熵设置都 ≥ 2 SE 更低遗憾，且快照 40 或 200 的原生校准余弦不低于 E1 超过 2 SE、逐样本方差低于 E1 ≥ 2 SE。
- 之后：读数条目 + RESEARCH 行。C1 成立 → 回到 benchmark 声明 Fit A（T′ shared，seed 26092731，≤ 13 h + 3 h，wsl_4070），先写 Fit A 的 L0 工程要求（评估器 trace 记逐决策标签与锚点坐标）；C1 不成立 → 不声明 Fit A/B，T′ 回到推理。

### energy_relay_benchmark（Claude DM）

- 无操作在跑。Stage 2-0 结束（S = hungarian − identity = +.007 ± .007，全部在进入前）；信用诊断已读（b03_credit_a01：不退役、C2 阈值满足、宿主在高可替代区 rho −.615）；Fit A / Fit B 均以 C1（来自上面的第一格）∧ C2 ∧ 规则 S 为条件。
- 本机专有大文件：`runs/energy_relay_benchmark/b03_credit_a01/credit-diagnostics/traces/{hungarian,credit_hungarian}.npz`（gitignored，仅此机器有），不要删。
- 远端节点 wsl_4070：`/home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01/checkpoints/` 是 DM1 的活输入；节点上永不运行 `git sparse-checkout set/add`；957001–957032 与 `b02_holdout_refs_a01` 已用过。

## 5. 会话级事实

- 解释器：科学 `/home/fires/.venvs/hmasd-linux-cpu/bin/python`（跑测试时把它的 `bin` 放到 PATH 前面）；控制面按 `.codex/hmasd-compute.toml`。永不安装、永不用 `/mnt/c` 的 python.exe。测试：`python -m pytest tests/experiments/candidates/sequential_coordinator_credit -q`（36 项，约 20 s）。
- 权限：owner 已应用 option B 的 allow 规则；此后 `git add/commit/push` 与 launcher 的裸命令都通过。分类器拒绝 → 原文报告，不拆分、不重试、不绕过；不读不改自己的 settings 文件。
- Peer 通道（Root 为平级）：出站 `CODEX_HOME=/mnt/c/Users/fires/.codex CODEX_SQLITE_HOME=/home/fires/.codex/sqlite codex queue --thread 01a0e091-9f32-7872-b582-b37a14f8d981 --message "<text>"`；入站 `docs/Claude_docs/inbox/` 的日期文件。一事一信，无 ACK 循环。
- Pro（Jev）传输状态在 `~/.local/state/hmasd-pro-transport/operations/`（会话 URL 只留本地）；headless Chrome 重启后由下一次 `send` 自动拉起。
- 本会话 `/tmp` 草稿已复制到 `temp/directions/sequential_coordinator_credit/scratch/session-scratch-20260927/`（gitignored，PDF 除外）；实现者草稿在 `temp/directions/sequential_coordinator_credit/scratch/first-cell-l0/`，方向收尾时一起清。
- 记忆目录 `~/.claude/projects/-home-fires-hmasd-wsl/memory/`：两个方向的状态文件已更新到本次交接。
