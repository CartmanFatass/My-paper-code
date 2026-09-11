# Root return: JaxMARL fixed-SHA core evidence

已完成只读检查：`C:/Projects/ref-lib/JaxMARL` 的 `HEAD` 是
`b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9`，远端是 `https://github.com/FLAIROx/JaxMARL.git`，官方 GitHub 页面将其重定向到 `bold-lab-ai/JaxMARL`。仓库声明 Apache-2.0。上游固定树没有 `AGENTS.md` 或 `CLAUDE.md`；新增导航文件全部是本地 overlay，备份在 `agents-overlays/`，未改动源码。

最重要的调用链是：`IPPO ippo_rnn_smax.main` 创建 PRNG key，拆成 `NUM_SEEDS`，对 `make_train` 做 `jax.jit` 和 seed `vmap`；`make_train` 设置 `NUM_ACTORS = num_agents × NUM_ENVS`；外层 `lax.scan(NUM_UPDATES)` 内收集 `lax.scan(NUM_STEPS)`，每一步先 vmapped action mask/network，再 `vmap(env.step)`。SMAX 的单步内部再扫描 `world_steps_per_env_step`（默认 8）个 world step，并 vmapped 处理 unit。随后 GAE reverse scan、epoch/minibatch scan、WandB `io_callback`。VDN 的 `vdn_ff` 也将时间扫描、agent-vmap、replay add/sample/update 扫描包在 `jax.jit(jax.vmap(make_train))` 中，并在入口 `block_until_ready` 后保存参数。

环境 API 是纯函数风格：`reset(key,state)`/`step(key,state,actions)` 返回新 Flax state；公共 `MultiAgentEnv.step` 自动 reset，按 `done["__all__"]` 用 `lax.select` 选择 reset 或 stepped tree。`CTRolloutManager` 才引入并行环境轴：拆 key 后 `vmap` reset/step，同时把 agent dict 按固定 agent 顺序 stack；对 heterogeneous observation 做 flatten、padding、agent one-hot，并增加 global state/reward。MPE state 有 `p_pos/p_vel/c`，碰撞力 nested vmap 形成实体对矩阵；SMAX state 按 allies→enemies 保存位置、alive、health、types、cooldown、previous actions，unit-pair push 和 observation/mask 计算有显式 N×N 或 per-agent 数组。

计时边界要特别小心：`jaxmarl/environments/smax/speed.py` 先 `.lower(...).compile()`，再在 `block_until_ready` 内计时 steady-state；打印的 steps 只等于 `NUM_ENVS × NUM_STEPS`，没有乘 agent 或 SMAX world substeps。`ippo_rnn_smax.py` 入口没有显式 block，不能直接作为 wall-clock benchmark。核心路径没有 pmap/pjit/sharding；GPU 只由 device 选择和 launcher 的进程 slot 控制。没有 `device_put/device_get` 证据。

明确的 host 风险包括：STORM import 时 `itertools.combinations` 生成 spawn 组合、Overcooked V2 构造时组合 recipe、Hanabi 构造/格式化 action/belief 枚举，以及训练 loop 中 `jax.debug.callback`/`io_callback` 的 WandB 主机回调。这些是候选启动、同步或内存开销，未做实测。没有安装依赖、训练、benchmark、GPU/传输/回调/扩展性测试，因此不能承诺 GPU 或 VNFC 加速；toy 超过 45 分钟、UAV 超过 12 小时仅作为工程核查触发。

交付物：

- [`CORE_EVIDENCE.md`](CORE_EVIDENCE.md)：准确路径、行号、短片段、固定 SHA 链接、调用链、观察/推断/未实测界线。
- [`AGENTS_INDEX.json`](AGENTS_INDEX.json)：新增真实目录 overlay 与备份映射。
- `C:/Projects/ref-lib/JaxMARL/**/AGENTS.md`：根、`jaxmarl`/环境、wrapper、IPPO/MAPPO/QLearning 导航；报告目录保存逐文件备份。

建议 Root 将“vmap + scan + jit 是代码事实，速度与 VNFC 是未实测”作为规范中的硬边界，并以 agent/env/time/seed 四轴和 callback/compile 状态共同定义任何后续 benchmark。
