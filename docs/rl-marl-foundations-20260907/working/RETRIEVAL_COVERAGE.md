# 本次资料检索与阅读范围

1. 本地正式论文索引 C:/Projects/Inst-sci/papers/MyLib/llm-index/catalog.v2.jsonl；元数据 metadata/v2/papers.v2.jsonl；正文 `json/<id>.json`；PDF `pdf/<id>.pdf`。索引字段json_path/pdf_path相对于 C:/Projects/Inst-sci/papers/，避免重复拼接MyLib。父代理最初检索Sutton、Barto及两本教材完整书名未命中，子代理对MAPPO与几篇基础评价论文亦未命中；这仅是该快照覆盖缺口。
2. C:/Projects/My-lib/README.md说明默认tracked registry含synthetic fixtures，本次未把它们作为科学证据。父代理读取该README并对书目/collection/catalog文件做有界路径检索，仅见部分历史计划文件和.local-phase0-20260727中的source-catalog路径，未据此声称已建立真实教材全文索引。一次递归路径检索在.pytest_cache遇到Access denied；这不影响已读正式论文索引，也不支持‘本地没有书’的全盘判断。
3. 实际使用的本地专题正文包括 MARL-0004（Consensus Learning for Cooperative Multi-Agent Reinforcement Learning）、MARL-0005（Contrastive Identity-Aware Learning for Multi-Agent Value Decomposition）、MARL-0449（Agent-Centric Actor-Critic for Asynchronous Multi-Agent Reinforcement Learning）、MARL-0553（Hierarchical Multi-Agent Skill Discovery）；0449读JSON相关p1–5，0553读相关p1–6及p17–18。其他命中0530/0543/0596只作相关资料定位，未代替核心教材/方法学来源。未把索引摘要当原文定理。
4. 公开来源补查了Sutton/Barto教材、Albrecht/Christianos/Schäfer教材、options/MacDec-POMDP/Option-Critic、MAPPO、reward transformation、policy gradient、RL reproducibility/statistics/implementation原始论文。正文核查按相关章节进行，未声称通读全部书籍。
5. 原对话另直接核对Amato等2019 JAIR PDF https://lis.csail.mit.edu/pubs/amato-konidaris-jair19.pdf 的§2.1/§2.3：Dec-POMDP信息结构、options定义及SMDP reward/discount。此PDF物理第7页是options框架，引用优先章/节，避免页码偏移。
6. 网页工具直接请求 https://incompleteideas.net/book/RLbook2020.pdf 超时；https://www.marl-book.com/download/marl-book.pdf 直接请求返回403，但作者书页/目录与公开索引的相关章节文本可读。此处记录访问方式与限制，不把‘书目存在’当作本轮完整正文已读。
