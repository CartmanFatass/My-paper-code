# 原设计交付与核验（历史记录）

本节记录实现前的设计状态。后续用户将执行规模收敛为每轮随机经典一题与非范例一题，
并要求独立打开的 session 直接充当 CM、一句话自动完成。当前实现与核验见
[IMPLEMENTATION.md](IMPLEMENTATION.md)；下文“尚未实施”和 21 次批次仅描述旧阶段。

2026-09-09 PDT，源码输入基线 `0fae6912f20a8322376b6289fca3ead4ef2a56ac`。
Owner 要求的两项 CM 场景独立于 root_delegation；后续澄清把 spec 颗粒度与复用作为主线，
并要求同一 CM 承受连续问题和杂务形成的真实上下文压力。

已交付：两个场景入口；spec 主设计与按模型固定的 8 格 spec 策略矩阵；连续任务/独立
验收/成本方案；五类可复用 spec 候选；三个局部可执行范例；Luna 对近期 27 个 CM 会话
的初筛和 9 个代码候选、3 条连续任务来源；完整保留历史成本提取的成功原输出和错误清单。

核验：

- census 的 27 个 ID、CM 角色、agent_path、完整 observed_session_git_sha 与只读 SQLite
  匹配；CSV/JSON 行 ID 一致、类别计数一致。候选的主要代码入口已核对存在。
- 相对 Markdown 链接可达；8 个 spec 策略均为 not_run；主研究 9+12=21 次计划流程，
  另选模型探索最多 10 次。计划次数不表示已发生调用或费用。
- `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B .../_host/check_examples.py`：
  4 项检查通过，覆盖完整 row 分母与梯度、全 held 零项、terminal/truncation 区别及
  evaluation 不推进 training Generator。运行环境 Python 3.10.20、NumPy 1.26.3、
  Torch 2.7.0+cpu。无科研训练、无远程调用、无文件型测试 scratch。

这些检查只验证文档组织、元数据映射和微例子承诺的局部行为。
完整代码题包、起点/依赖冻结、隐藏验收、CM 专用 runner 和候选模型试跑尚未实施。
现有 root_delegation runner 未改动。生产角色、科研授权、方向状态与预算未变更。

下一实现单元：先把一个真实连续流程及其 L0–L3 按档材料制作成可运行题包，验证参考
实现/典型错误，再按共用 DESIGN 的轻量接口完成投递与留档；无需用户逐条复制。
独立运行和评分之后才填写 spec 推荐档位与模型成本结论。
