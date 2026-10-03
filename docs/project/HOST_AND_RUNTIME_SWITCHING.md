# 主机与运行时切换

仅在实际切换／接任时使用。本页解释主机特有差异；暂停、责任移交与冻结合同遵循
[宪法](OPERATING_CONSTITUTION.md)，通用发表／准入／恢复步骤遵循
[engineering](../../.agents/skills/hmasd-research-engineering/SKILL.md)。切换不恢复研究。

## 切换会带走什么

| 对象 | 处理 |
| --- | --- |
| 已发表源与控制 | 按 `.codex/hmasd-compute.toml` 的 control_source 和实际原生源身份读取；main 的控制现状不替代旧实验输入 |
| 进程／claim／观察句柄 | 记录于现有 NOTES/run 元数据；claim 按原 Git common directory 保存，另一 clone 不自动继承 |
| bulk／ignored 输出 | Git 不运输它们；保留已验证的持久位置和哈希，单纯留在将删除的 checkout 不构成保全 |
| 会话私有记忆 | 不作为研究状态；接任依靠 RESEARCH、NOTES、CLAIM 和原始输出 |
| 用户级 MCP／原生设置 | 需在目标环境实际可用；仓库配置或生成检查不证明已生效 |

每台主机使用自己的 checkout/index/解释器。Windows 路径和 WSL 路径不能互换执行；
不要从 WSL 调 `/mnt/c/.../python.exe`。通过 `tools.research_support.interpreters` 查询
scientific/control-plane Python，解释器覆盖和 native-build PATH 见 `tests/AGENTS.md`。
Linux torch 扩展需要 scientific venv 的 bin 在 PATH，才能找到 ninja；不安装进现有环境。

## 接回已有工作

离开前在原记录写清责任、未决判断、已接受和接受不确定的工作、节点及 operation ref、
未读结果／建议和唯一输出位置。发表已完成的自有改动，保留其他写者；遵循 engineering 的
显式路径／串行 Git 方法。共享 main 有他人的未提交文件不是清空工作区或另建发布树的理由。
本机进程若不能由接任环境观察，应先到可恢复边界或保留原观察路径；远端进程可以继续，
但接任者必须实际验证同一原生句柄和可用观察路径。不要用重启获得新句柄。

切入后先核对 owner pause、当前 lead/地址与完整已发表记录。没有真实移交不接管方向。
按原 operation ref 查询 accepted worker／Send 的实际状态；不确定时对账同一请求。
控制 checkout 与运行 snapshot 不是同一对象；不能通过修改旧 snapshot 的 lead 绕过准入。
联系地址变化写 routing；实际责任变化才按合同协调 lead，保留未移交的接受操作。

Codex 原生子 DM 要保持 turn 至完整收集判读，Root 用 native follow-up 恢复同一 child。
独立 POSIX Codex 在返回路径支持时用 `tools/hmasd_wait.py`；Claude／Pi／OMP 采用自身
已验证的确定性观察与 native/manual return。Codex queue 不自动唤醒其他运行时。
Jev 与 Agentify 各按实际 provider 的 transport skill；不要假定两个账号共享 conversation URL。

## 只验证受切换影响的能力

用已有检查回答具体的不确定项，复用仍适用的结果，不把全部测试变成每批启动清单：

- 共享正文／副本变化：control-plane Python 执行 `tools/publish_claude_control.py --check`；
  生成行为变化时使用 `tests/skills/test_control_publication.py` 和 `test_control_alignment.py`。
- 节点、源身份或启动行为变化：核对 compute 配置与实际节点；需要时运行已有
  `tests/test_hmasd_launch.py`，不以一次测试代替 fresh node admission。
- native backend／数值变化：用相关 backend 或方向测试，依 `tests/AGENTS.md` 管理 scratch。
  Windows/Linux 即使版本相同也可能有 ULP 差异；一台机器通过不证明另一台逐位相同。
- Pro 路径变化：按所选 transport 的 preflight 与 same-key reconciliation 检查；不以
  测试链路为由发新问题或重发已有问题。WSL 给 Windows Agentify 的文件路径必须可被 Windows 打开。

源码发布不热加载运行会话。在相关工作的安全边界读取变更；确需重启原生工具注册时，先保全
可恢复上下文和观察责任，重启本身不转移／重做研究。报告实际检查范围及仍未知的运行行为。

## 历史验证

2026-09-18 双主机测试、旧 cherry-pick/tag/bundle 清理和当时残留是历史快照，见
[原始变更记录](../Claude_docs/changes/2026-09-18-wsl-second-host-enablement.md)与
[本页固定原版](https://github.com/CartmanFatass/My-paper-code/blob/94704c0c0a7d711d3708736d3462506e92b48951/docs/project/HOST_AND_RUNTIME_SWITCHING.md)。
其中主机名、测试数量和故障现状不作为当前实测；唯一保留材料仍按其原记录保护。
