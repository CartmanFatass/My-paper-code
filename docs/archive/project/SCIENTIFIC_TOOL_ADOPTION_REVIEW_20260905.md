# Scientific tool adoption review

2026-09-05，Root 按所有者请求查阅 C:/Projects/HMASD-scientific-skills 并检索 MARL 官方工具。
这是采用建议与查证记录，不是新规范、安装批准流程或实验启动条件。本次未安装依赖、执行外部 skill 脚本或改变科学对象。

## 结论

应把可计算、可检索、可测量的工作交给实际工具，模型负责选择问题、解释证据及识别工具适用边界。增加提示词型 skill 本身不能替代测量。优先使用现有 Python 科学栈、官方论文元数据、成熟 MARL 实现和局部性能工具；不新增统一平台或每个对象必跑的诊断链。

本次检查全部11个 SKILL.md 的元数据、章节和附属 Python 文件清单，进一步检查实验布局、统计假设检查和引用验证脚本的相关实现。没有宣称完成所有附属脚本的代码审计或运行认证。review-required/research-lookup 保持原状态。

## 本地 skills 筛选

| Skill | 可以采用的部分 | 在 HMASD 中的边界 |
| --- | --- | --- |
| paper-lookup | arXiv/OpenAlex/Crossref/Semantic Scholar 定向检索，附属 Atom/JATS/摘要解析脚本 | 优先采用；用公开查询取得论文与代码出处，元数据命中不证明论文支持某个结论。 |
| statistical-analysis | SciPy 等现成统计计算、效应量与不确定性说明 | 改编使用；其唯一附属 Python 主脚本是 assumption_checks.py，并非 RL 多seed分析器。不能默认先做正态性/功效/p值筛选才允许探索。 |
| scientific-visualization | Matplotlib 曲线、逐run点、导出与缺失数据显示 | 优先采用相关绘图部分；先忠实显示原始结果，出版级样式检查留到需要交付图表时。 |
| experimental-design | randomization.py 与 doe_designs.py 生成布局、区组与因子设计 | 按具体问题采用；MARL 配对外生随机性和独立训练实例需明确，不照搬病人分组。full_factorial 仍可指数膨胀，不能因工具支持就默认全矩阵。 |
| networkx | 连通性、路径、图结构的实际算法计算 | 图问题时采用；不默认调用全简单路径/全部团等组合枚举。不能用图指标替代原生任务回报。 |
| torch-geometric | 图模型、图批处理、消息传递的成熟实现 | 仅图模型方向使用；当前本地解释器未安装，skill针对2.7.x而项目依赖快照2.6.1，不能自动升级。 |
| stable-baselines3 | PPO实现参考、Gymnasium契约、合适单体或明确共享策略基线 | 不能直接当作通用CTDE/MAPPO等价替代。skill针对2.8+，本地是2.6.0。 |
| pufferlib | 环境适配、向量化、吞吐比较脚本 | 独立性能迁移候选；3/4接口和原生工具链不同，不把新框架塞进已冻结实验。 |
| literature-review | 定向文献综合、引用元数据检查 | 不默认全系统综述。主流程还引用parallel-cli及其他skill；不能把再次调用模型当作独立科学验证。verify_citations.py检查DOI/URL及元数据，不检查论证支持关系。 |
| scientific-critical-thinking | 混杂、替代解释、伪重复的提醒 | 主要是分析指导，没有附属Python；GRADE/Cochrane背景不应直接转成MARL探索门槛。 |
| scientific-writing | 成文与局部一致性、参考文献检查脚本 | 报告/论文阶段按需用；不继承全部投稿清单到B科学卡。 |

目录位于HMASD之外；不能仅凭该目录的 README 写“已启用”就声称当前 HMASD 会话自动加载了11项。

## 当前可用依赖

对 C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe 用 importlib.metadata 检查：
numpy1.26.3、scipy1.15.2、pandas2.2.3、matplotlib3.10.0、torch2.7.0、networkx3.2.1、pettingzoo1.24.3、stable-baselines3 2.6.0 已登记安装。
该解释器未登记 torchrl、torch-geometric、benchmarl、rliable、pyDOE3。依赖快照写有某包不证明此解释器已安装。
这是本地包元数据核对，不是import/native能力测试，更不代表远程执行节点。

## MARL工具与实际接入点

1. **DM/Root算数与结果分析：NumPy/Pandas/SciPy。** 从配置计算真实episodes、updates、评估量和嵌套调用数；从结果表计算差值及适合数据结构的不确定性。SciPy支持配对bootstrap，需保持真实配对单位和分层；一个训练seed的64个评估episode不能提供训练seed总体不确定性。有限计算不能自动解决估计量选择问题。[SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)

2. **多任务、多训练seed报告：rliable。** 提供分层bootstrap、IQM、performance profiles与improvement probability。适合积累足够结构化结果后的benchmark报告，单seed首轮信号不必安装它或制造汇总指标。官方仓库已于2025-10-15归档，只读；采用时固定版本并检查依赖，不称为活跃维护项目。[rliable](https://github.com/google-research/rliable)

3. **CM性能定位：torch.profiler、torch.utils.benchmark。** 对具体慢路径记录少量operator事件，或对一个候选kernel测量；与完整调用wall分开。Profiler有额外开销，也无法自动拆解一个不透明C++扩展内部的所有热点。C++热点仍需原生工具或有针对性的阶段计时。现行spec禁止常驻profiler/framework，不等于每项工作都要新建profile任务；如需给当前对象增加探针，应在该CM工程范围说明目的、边界、次数及成本。[PyTorch2.7 profiler](https://docs.pytorch.org/docs/2.7/profiler.html)、[benchmark](https://docs.pytorch.org/docs/2.7/benchmark_utils.html)

4. **实现与基线：BenchMARL/TorchRL、EPyMARL、官方on-policy MAPPO。** 复用已有算法、collector、buffer和评价接口，减少重新编写与模型猜测；先使用 C:/Projects/ref-lib/reports/ 已有六库调查和固定源，不再重复下载阅读整库。BenchMARL适合PyTorch体系的新benchmark；EPyMARL提供合作MARL算法/环境实现。加入自定义host仍需明确观测、mask、终止与奖励接口。[BenchMARL](https://github.com/facebookresearch/BenchMARL)、[EPyMARL](https://github.com/uoe-agents/epymarl)

5. **环境接口验证：PettingZoo tests。** 仅在已有/新建PettingZoo适配器上使用API/parallel契约检查；它们验证接口行为，不证明奖励含义和信息无泄漏。不要为调用测试而强迫当前VNFC原生接口重写。[官方环境测试](https://pettingzoo.farama.org/content/environment_tests/)

6. **公开任务与加速候选：VMAS、SMACv2、JaxMARL/Mava。** VMAS是PyTorch向量化多机器人环境；SMACv2提供合作任务基准；JaxMARL提供JAX算法和环境。适合独立benchmark或明确迁移问题，不是当前host的无损替代，也不能把上游吞吐当HMASD加速实测。[VMAS](https://github.com/proroklab/VectorizedMultiAgentSimulator)、[SMACv2](https://github.com/oxwhirl/smacv2)、[JaxMARL](https://github.com/bold-lab-ai/JaxMARL)

## 最小采用顺序建议

第一批：paper-lookup定向来源、现有NumPy/SciPy/Pandas计算、Matplotlib逐run曲线、具体性能疑问的局部计时。以任务实际使用的短脚本/结果表回传模型，避免重复输入全部源码或原始日志。

第二批：在新增benchmark方向接入一个成熟MARL基线框架；有图问题才用NetworkX/PyG，有PettingZoo适配才用其tests。rliable用于后续多任务多seed汇总。

第三批：仅在需要独立性能/平台迁移时评估PufferLib、JaxMARL/Mava、VMAS，不以框架替换延迟当前就绪实验。

模型负责提出可证伪的问题、选择独立单位、检查工具适用性和解释结果；工具负责检索、算数、统计、执行和测量。下一步接入应保持这一分工，而非要求所有角色每轮加载全部skills。
