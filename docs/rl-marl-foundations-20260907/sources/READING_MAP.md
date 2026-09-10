# 来源索引与阅读路线

本索引记录本轮使用的教材、原始论文和本地资料。正文阅读、章节索引和书目核对不是同一种覆盖程度；以下按实际取得的内容说明。未通读整本教材，未把搜索摘要、代码库名或本地索引命中当作定理证据，也未在本目录复制整本书或论文。

## 两本教材作为主线

<a id="b1"></a>
### B1 · Reinforcement Learning: An Introduction

Richard S. Sutton、Andrew G. Barto，第二版，MIT Press，2018；ISBN 9780262039246。用于建立任务、return、价值、策略与学习的概念层次。

- 正式版书目：[MIT Press](https://mitpress.mit.edu/9780262039246/reinforcement-learning/)。本轮核对的是正式版书目信息，不能表述为已核对正式版完整正文。
- 实际读取的教材正文：[Stanford 托管 PDF](https://web.stanford.edu/class/psych209/Readings/SuttonBartoRL.pdf)。封面标为 Second edition, in progress / Draft，copyright 2014、2015、2016，共 455 个 PDF 页面；它不是 2018 最终版。
- 本轮针对性阅读/核对范围：草稿第 3 章任务与 return，第 9 章函数逼近，第 13 章策略梯度等相关段落。草稿第 9 章从印刷 p.191、第 13 章从 p.265 开始。正文尽量使用章节定位，不把草稿页码归给正式版。
- 建议用途：作为 RL 术语和推导的持续参考；需要引用正式版精确原文或页码时，再核实相应版本。

<a id="b2"></a>
### B2 · Multi-Agent Reinforcement Learning: Foundations and Modern Approaches

Stefano V. Albrecht、Filippos Christianos、Lukas Schäfer，MIT Press，2024。[作者书页](https://www.marl-book.com/)；[作者提供的 PDF 入口](https://www.marl-book.com/download/marl-book.pdf)。

- 作者页说明公开 PDF 包含更新内容；不要假设其分页与每一版纸书完全相同。
- 实际覆盖：作者书目信息、目录，以及公开检索索引可读取的相关正文。涉及第 2 章 return/learning curves，第 5 章 §5.4.1 非平稳性、§5.4.3 信用分配，第 9 章 §9.1 训练/执行安排及 §9.7.1 参数共享。实证专题还检查第 10 章相关目录定位；目录定位不等同于完整正文阅读。
- 访问限制：本轮直接请求 PDF 返回 403；通过公开索引取得了相关章节文本，不声称已下载或通读整本书。
- 建议用途：连接单智能体基础与合作、信息结构、MARL 学习及实验实践。当前最相关的是第 5、9 章，而不是先罗列尽可能多的方法。

## 原始论文：按所回答的问题组织

| ID | 来源与正式身份 | 本轮阅读或核查范围、用途 |
|---|---|---|
| P1 | Watkins & Dayan，*Q-learning*，Machine Learning 8，1992。[作者论文副本](https://www.ece.uvic.ca/~bctill/papers/learning/Watkins_Dayan_1992.pdf) | 经典 Q-learning 与其收敛假设；用于限定 tabular 结论，不能替代任意深度 MARL 的保证。 |
| P2 | Sutton、McAllester、Singh、Mansour，*Policy Gradient Methods for Reinforcement Learning with Function Approximation*，NIPS 12，1999。[官方论文页](https://proceedings.neurips.cc/paper_files/paper/1999/hash/464d828b85b0bed98e80ade0a5c43b0f-Abstract.html) | 相关策略梯度与兼容函数逼近定理；用于区别 baseline 恒等式、近似估计与任意 actor–critic。 |
| P3 | Ng、Harada、Russell，*Policy Invariance under Reward Transformations: Theory and Application to Reward Shaping*，ICML，1999。[作者 PDF](https://ai.stanford.edu/~ang/papers/shaping-icml99.pdf) | reward 变换与 potential-based shaping 的条件。专题中的固定/可变时域常数平移是依 return 定义作的直接说明。 |
| P4 | Sutton、Precup、Singh，*Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning*，Artificial Intelligence 112(1–2):181–211，1999。[作者书目页](https://www.cs.utexas.edu/~shivaram/readings/b2hd-SuttonPS1999.html) | 核对经典论文身份与 options 来源。原始 PDF 访问受限，本轮对 option 定义及 SMDP 公式另用 P5 的可读正文核对；不虚称已完整读过 P4。 |
| P5 | Amato、Konidaris、Kaelbling、How，*Modeling and Planning with Macro-Actions in Decentralized POMDPs*，JAIR，2019。[作者 PDF](https://lis.csail.mit.edu/pubs/amato-konidaris-jair19.pdf) | §2.1 Dec-POMDP、§2.3 options/SMDP 以及宏动作信息与异步边界相关段落。原对话另核对 §2.1/§2.3。优先按节引用，物理 PDF 页与印刷页有偏移。 |
| P6 | Bacon、Harb、Precup，*The Option-Critic Architecture*，AAAI，2017。[官方论文页](https://ojs.aaai.org/index.php/AAAI/article/view/10916)；[arXiv](https://arxiv.org/abs/1609.05140) | 方法概述及 option 内部策略/终止的学习机制；作为一种可学习 options 方案，不把它当成 option 的唯一实现。 |
| P7 | Xiao、Hoffman、Amato，*Macro-Action-Based Deep Multi-Agent Reinforcement Learning*，CoRL，PMLR 100:1146–1161，2020。[官方论文页](https://proceedings.mlr.press/v100/xiao20a.html) | 宏动作设定与异步轨迹组织相关方法部分；用于连接模型与具体深度学习方案，不泛化为必须采用某一种 replay。 |
| P8 | Yu 等，*The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games*，NeurIPS Datasets and Benchmarks，2022。[arXiv v4 入口](https://arxiv.org/abs/2103.01955)；[官方实现](https://github.com/marlbenchmark/on-policy) | §§3–5 的 MAPPO/IPPO、信息输入、基准与实现因素，及论文结论；另核对仓库 README/有关接口。论文任务为 MPE、SMAC、GRF、Hanabi，不能把结果写成当前 UAV 上的已知优势。 |
| P9 | Henderson 等，*Deep Reinforcement Learning That Matters*，AAAI，2018。[官方页面](https://ojs.aaai.org/index.php/AAAI/article/view/11694)；[PDF](https://ojs.aaai.org/index.php/AAAI/article/download/11694/11553) | PDF 相关 pp.1–3：复现、随机性、实现和 reward scale。支持讨论实证敏感性，不能推出固定实验门槛。 |
| P10 | Agarwal 等，*Deep Reinforcement Learning at the Edge of the Statistical Precipice*，NeurIPS，2021。[官方论文页](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html)；[arXiv](https://arxiv.org/abs/2108.13264) | §§1、3、4 中少量运行评价、协议差异、区间和聚合统计等内容。工具选择需匹配任务集合及统计层级。 |
| P11 | Engstrom 等，*Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO*，ICLR，2020。[官方会议页](https://iclr.cc/virtual/2020/poster/1752)；[arXiv](https://arxiv.org/abs/2005.12729) | §§1、3–6 和 Appendix A 相关实验：code-level choices、归一化、裁剪、初始化、学习率等。阅读由最初摘要补充到相关正文；经验范围为 PPO/TRPO 的 MuJoCo 案例。 |

## 本地正式论文库

使用入口：[catalog.v2.jsonl](C:/Projects/Inst-sci/papers/MyLib/llm-index/catalog.v2.jsonl)。索引用于定位；以下引用依对应正文 JSON 的相关页面。索引的相对路径从 C:/Projects/Inst-sci/papers/ 解析。

| ID | 本地资料与原始来源 | 实际阅读范围和作用 |
|---|---|---|
| L1 · MARL-0004 | Xu 等，*Consensus Learning for Cooperative Multi-Agent Reinforcement Learning*，AAAI，2023。[DOI](https://doi.org/10.1609/aaai.v37i10.26385)；[正文 JSON](C:/Projects/Inst-sci/papers/MyLib/json/MARL-0004.json)；[PDF](C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0004.pdf) | 相关 pp.1–7，尤其第 2 页 Dec-POMDP/CTDE 背景及后续方法。用作具体协调方法案例，通用定义优先采用教材/基础建模论文。 |
| L2 · MARL-0005 | Liu 等，*Contrastive Identity-Aware Learning for Multi-Agent Value Decomposition*，AAAI，2023。[DOI](https://doi.org/10.1609/aaai.v37i10.26370)；[正文 JSON](C:/Projects/Inst-sci/papers/MyLib/json/MARL-0005.json)；[PDF](C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0005.pdf) | 相关 pp.1–5、7：身份、值分解和行为差异的方法与结果。用于说明一种表示/学习选择，不是通用协调保证。 |
| L3 · MARL-0553 | Yang 等，*Hierarchical Multi-Agent Skill Discovery*，NeurIPS，2023。[官方论文页](https://papers.neurips.cc/paper_files/paper/2023/hash/c276c3303c0723c83a43b95a44a1fcbf-Abstract-Conference.html)；[正文 JSON](C:/Projects/Inst-sci/papers/MyLib/json/MARL-0553.json)；[PDF](C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0553.pdf) | 相关 pp.1–6、17–18：team/individual latent、coordinator、条件策略及局限。未凭论文术语替当前实现作严格 option 分类。 |
| L4 · MARL-0449 | Jung 等，*Agent-Centric Actor-Critic for Asynchronous Multi-Agent Reinforcement Learning*，ICML，2025。[官方论文页](https://proceedings.mlr.press/v267/jung25a.html)；[正文 JSON](C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json)；[PDF](C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0449.pdf) | 相关 pp.1–5：异步观测、agent-centric history、actor–critic 与其 advantage 方法。是一种具体方案，非全部异步任务的必要步骤。 |

本地另定位过 MARL-0530、0543、0596 等相关候选，本稿没有用它们替代基础来源。当前正式索引未命中两本教材以及部分经典方法论文，不代表整台机器或其他库没有这些资料。C:/Projects/My-lib/README.md 说明默认 tracked registry 含 synthetic fixtures；本轮没有把这些记录当科学证据。详细查询范围和访问失败见 [RETRIEVAL_COVERAGE](../working/RETRIEVAL_COVERAGE.md)。

## 怎样使用这份资料

先读 [综合稿](../FOUNDATIONS.md)，把任务、信息、策略、学习和证据几个层次接起来。查 RL 定义时回到 B1 和 RL 专题；查合作学习的信息、信用与训练结构时回到 B2 和 MARL 专题。进入技能设计再读 P5/P4、P6/P7 及本地 L3/L4；设计具体比较或解释结果时查 P8–P11。

这个顺序按当前问题组织，不要求通读全部资料后才允许思考或实验。下一次讨论若产生确切定义或公式争议，应核对相应原始段落，而不是以本摘要代替原文。
