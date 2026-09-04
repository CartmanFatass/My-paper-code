# 文献到五方向的精选映射

这是一张 recall map，不是 novelty verdict。`docs/new-libs` 条目可通过 committed overview/claims/chunks
继续取证；InstSci 条目先从 Metadata v2 召回，再回到结构化 JSON/PDF。

## FRRIE

### `docs/new-libs`

| ID | 作用 | 必须保留的边界 |
| --- | --- | --- |
| B01 | parameter sharing、CTDE、implementation/evaluation 基础 | 教材不给 HMASD held-out-`N` 或 churn 结果 |
| P08 | mean-action fixed-width interface，可启发 variable roster representation | 多个固定 `N` 实验不等于一个 frozen policy 的 cross-`N` generalization |
| P12 | graphon/heterogeneous dense interaction与 finite-`N` approximation | `O(N^-1/2)` 在特定假设下；不是 learned-policy universal guarantee |
| P14 | interchangeability 下的 cooperative mean-field Q-learning 与 `N`-independent interface | 不证明 FRRIE tight package 的有限预算优势 |
| P16 | shared-parameter restriction与 sequential trust-region update 的反例/机制 | fixed cooperative game；不覆盖 roster churn，不能直接支持某一 arm |
| P22 | graphon particle approximation，提供“动力学近似≠policy return”的反例边界 | `O(1/N)` object 不是 MARL learned-policy guarantee |

### InstSci

| ID | Title | 作用 | 边界 |
| --- | --- | --- | --- |
| MARL-0078 | Investigating Relational State Abstraction in Collaborative MARL | relational abstraction/GNN 与 sample-efficiency 的近邻 | 不自动证明 held-out roster 或 tight-vs-containing package effect |
| MARL-0104 | ADAPT: ... Structural Generalization in Multi-Agent RL | variable-length set/object-centric structural generalization | 需核对正文 train/test roster protocol；摘要不能替代 HMASD matched work |
| MARL-0009 | Effective and Stable Role-Based Multi-Agent Collaboration... | structural role information与 stable collaboration | role encoding与 FRRIE relation treatment不是同一对象 |
| MARL-0036 | FoX: Formation-Aware Exploration... | formation-aware exploration与 structured state | exploration gain不等于 projection/optimizer effect |

## VNFC

### `docs/new-libs`

| ID | 作用 | 必须保留的边界 |
| --- | --- | --- |
| B01 | parameter-sharing implementation与 cooperative evaluation checklist | homogeneity assumption 不能替代 physical identity/membership law |
| B03 | Dec-POMDP local histories、macro-actions、communication/information semantics | 没有 within-episode fleet loss 或 finite-precision action conformance result |
| P08 | population aggregation作为 fixed-width variable-roster interface | mean effect 可隐藏 multimodal neighbor configurations |
| P12 | graphon labels/blocks可启发 heterogeneous roster serialization | 需要 stable estimable labels、churn与 sparse graph tests |
| P16 | shared-parameter counterexample提醒强共享可能损失表达能力 | 不判断 MAPR/DIRECT/BCRH 在 VNFC host 的 return |

### InstSci

| ID | Title | 作用 | 边界 |
| --- | --- | --- | --- |
| MARL-0104 | ADAPT... Structural Generalization | variable-length set 与 zero-shot structural generalization 最接近 | 不等于 episode内 executor loss；需核对 identity/ordering semantics |
| MARL-0036 | FoX: Formation-Aware Exploration | formation changes和 exploration representation | formation-awareness不保证 presentation-safe physical command |
| MARL-0114 | Autonomous Partner Selection for Cooperative MARL | membership/partner selection 的近邻机制 | partner selection与被动 unannounced executor loss 不同 |
| MARL-0005 | Contrastive Identity-Aware Learning... | identity-aware value decomposition提醒 identity channel 可能有用 | VNFC 的 opaque rank 仅应是 serializer；不能暗中成为 learner feature |

文献 gap：精选 corpus 中没有直接证明同一 finite checkpoint 在任意 row presentation 下产生相同
physical command，更没有覆盖该性质与 in-episode churn recovery return 的组合。这只是当前 snapshot gap，
不是全球 novelty 结论。

## CBSC

### `docs/new-libs`

| ID | 作用 | 必须保留的边界 |
| --- | --- | --- |
| B03 | delayed/costly/local communication与 decentralized information structure | communication delay 不等于 OWNER/epoch currentness state |
| P15 | information bottleneck、learned link scheduler与 task-coupled communication | marginal entropy/compression不证明 conditional semantic sufficiency |
| B01 | recurrent MARL、communication、parameter sharing与 evaluation方法 | 教材没有 CBSC protocol value 或 online currentness learner结果 |
| P01 | 要求明确研究问题是 descriptive/computational/normative | 只提供问题分类，不提供 algorithm evidence |

### InstSci

| ID | Title | 作用 | 边界 |
| --- | --- | --- | --- |
| MARL-0006 | DACOM: Learning Delay-Aware Communication... | stale/delayed messages影响协作决策的直接近邻 | delay-aware communication不是 receiver-content correctness/capability semantics |
| MARL-0066 | CoDe: Communication Delay-Tolerant... | intent/timeliness alignment与 outdated information | 摘要级结果不证明 CBSC typed recurrent adapter价值 |
| MARL-0203 | VIL2C: Value-of-Information Aware Low-Latency Communication... | message timeliness与 VoI/resource allocation | 更接近 UCOPE active acquisition；不能混成 CBSC passive currentness证据 |
| MARL-0078 | Investigating Relational State Abstraction... | relation-aligned state abstraction近邻 | 需真实正文核对 control/baseline；不证明 OWNER/epoch机制 |
| MARL-0034 | Expressive Multi-Agent Communication via Identity-Aware Learning | receiver/identity-specific communication启发 | identity-aware message与 CBSC public OWNER register不是同一处理 |

## SCDMP

### `docs/new-libs`

| ID | 作用 | 必须保留的边界 |
| --- | --- | --- |
| B03 | macro-actions/temporal abstraction、termination与 information timing | macro-action不自动使 duration adaptive，也不证明 H/R order value |
| P17 | episode-persistent latent与 committed exploration | latent固定整 episode；不是 variable `k` 或 event-order treatment |
| P01 | 要求先说明学习/控制问题与评价目标 | 没有 SCDMP physics/result |
| B01 | Markov game/RL/empirical workflow基础 | 不提供 event noncommutation→native action value 的推论 |

### InstSci

| ID | Title | 作用 | 边界 |
| --- | --- | --- | --- |
| MARL-0449 | Agent-Centric Actor-Critic for Asynchronous MARL | asynchronous macro-actions与 agent-centric actor-critic 最接近 | asynchronous duration不等于固定 H/R graph causal order |
| VS-0002 | Continuous-Time Value Iteration for MARL | continuous-time value与 timing formalism | grade B；需全文核对，不能直接支持 finite UAV simulator object |
| VS-0005 | Learning Uncertainty-Aware Temporally-Extended Actions | uncertainty-aware action extension | single-agent/HRL近邻；不证明 MARL event-order value |
| MARL-0032 | Decomposing Temporal Equilibrium Strategy... | non-Markovian temporal/reward-machine decomposition | temporal logic/order strategy与 SCDMP physical H/R treatment不同 |
| MARL-0134 | Emergent Fast-Slow Dynamics in Multi-Agent Q-Learning... | multi-timescale dynamics与 networked games | fast/slow learning dynamics不等于 external `k` 或 event map |

另见 `literature/README.md` 中四篇 legacy physics references。它们只支持 broad physical ingredients。

## UCOPE

### `docs/new-libs`

| ID | 作用 | 必须保留的边界 |
| --- | --- | --- |
| B01 | Bayesian learning/value-of-information 与 MARL foundations | 概念性 VoI 不建立 UCOPE paid-probe efficacy |
| B03 | costly/delayed communication与 Dec-POMDP information structure | communication action与 diagnostic state probe必须显式区分 |
| P15 | information bottleneck与 communication resource allocation | compression/scheduling不是主动获取 hidden diagnostic的同一 intervention |
| P17 | committed exploration、latent MI与 coordinated modes | episode-level exploration不等于 context-specific paid probe |

### InstSci

| ID | Title | 作用 | 边界 |
| --- | --- | --- | --- |
| MARL-0203 | VIL2C... Value-of-Information Aware Low-Latency Communication | VoI、latency、resource cost 与 progressive reception的最直接近邻 | message prioritization不是 UCOPE diagnostic probe；不能转移 acquisition polarity |
| MARL-0006 | DACOM: Learning Delay-Aware Communication... | communication delay与 overhead下的 policy learning | passive delayed message不等于主动 probe决策 |
| MARL-0062 | AIR: Unifying Individual and Collective Exploration... | individual/collective exploration机制 | exploration bonus/coordination可能不含真实 service/time/energy probe cost |
| MARL-0071 | Efficient Communication... Implicit Consensus Generation | communication efficiency与 learned shared information | consensus communication不证明 COUNT/RAW representation residual |

文献 gap：当前精选库没有直接覆盖“competence-first、真实付费 diagnostic intervention、然后在同一
数据上比较 protected COUNT 与 containing RAW”的完整两阶段设计。该 gap 只描述已索引 snapshot。

## Cross-cutting sources

- `docs/new-libs/B01` 与 InstSci 的多个 recent MARL papers用于方法/工程背景，不替代 HMASD 结果。
- `MARL_EMPIRICAL_EVIDENCE_SPEC.md` 中 MADDPG/QMIX/MAPPO 与 deep-RL evaluation sources用于校准
  证据 burden：早期 3–5 seeds可支持 preliminary B signal，但不能支持 stable/general superiority。
- 五方向都应把 literature mechanism、HMASD construction和direct empirical observation分栏报告。
