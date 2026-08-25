# Paper Selection

Selected on 2026-07-17 from the broader 2023-2025 code-bearing conference
corpus plus a targeted ICLR 2026 supplement.

| ID | Paper | Mechanism line | Why retained | PDF filename | Code decision |
|---|---|---|---|---|---|
| P01 | ACE / Asynchronous MAPPO (AAMAS 2023) | joint N + asynchronous execution | Only selected work with both asynchronous action making and an explicit within-episode robot-loss stress | `P01_ACE_AAMAS2023.pdf` | download |
| P02 | Agent-Centric Actor-Critic (ICML 2025) | k / asynchronous credit | Padding-free per-agent trajectories, attention critic, modified asynchronous GAE | `P02_ACAC_ICML2025.pdf` | download |
| P03 | InforMARL (ICML 2023) | N / local aggregation | Local-neighborhood GNN and held-out tests with arbitrary numbers of agents and obstacles | `P03_InforMARL_ICML2023.pdf` | download |
| P04 | Sable (ICML 2025) | many-agent sequence scaling | More than 1,000 agents with linear memory growth; useful as a coordinator scaling reference | `P04_Sable_ICML2025.pdf` | targeted Mava checkout |
| P05 | ExpoComm (ICLR 2025) | sparse large-team topology | Small-size/small-diameter communication topology maps to a bounded critical-member residual | `P05_ExpoComm_ICLR2025.pdf` | download |
| P06 | Safe-M3-UCRL (AAMAS 2024) | cooperative mean field | Population distribution, global capacity/coverage constraints, and a swarm-motion evaluation | `P06_SafeM3UCRL_AAMAS2024.pdf` | inspect paper first; no initial checkout |
| P07 | Continuous-Time Value Iteration for MARL (ICLR 2026) | continuous-time value semantics | HJB-consistent value learning is a useful contrast for irregular time intervals | `P07_CTMARL_ICLR2026.pdf` | download |
| P08 | IARO (ICLR 2026) | multi-agent option discovery | Temporally extended skills and relative-state abstraction expose both useful features and a synchronization failure mode | `P08_IARO_ICLR2026.pdf` | inspect paper first; no initial checkout |

## Hard exclusions from the focused set

- Dynamic grouping alone does not establish variable `N`; HYGMA, GoMARL, and
  GACG remain comparison references in the broader report.
- Observation delay and recurrence do not establish variable `k`; RDC and
  AERIAL remain robustness references.
- Agent-specific masks do not establish roster independence; Kaleidoscope
  remains a heterogeneity diagnostic.
- AlphaZero model-size scaling is not many-agent scaling.

## Source URLs

| ID | Paper | Official code |
|---|---|---|
| P01 | https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p1108.pdf | https://github.com/yang-xy20/async_mappo |
| P02 | https://raw.githubusercontent.com/mlresearch/v267/main/assets/jung25a/jung25a.pdf | https://github.com/LGAI-Research/acac |
| P03 | https://proceedings.mlr.press/v202/nayak23a/nayak23a.pdf | https://github.com/nsidn98/InforMARL |
| P04 | https://raw.githubusercontent.com/mlresearch/v267/main/assets/mahjoub25a/mahjoub25a.pdf | https://github.com/instadeepai/Mava |
| P05 | https://proceedings.iclr.cc/paper_files/paper/2025/file/3514dbacaebf0f38b25adfe59ed81a8a-Paper-Conference.pdf | https://github.com/LXXXXR/ExpoComm |
| P06 | https://www.ifaamas.org/Proceedings/aamas2024/pdfs/p973.pdf | https://github.com/mjusup1501/safe-m3-ucrl |
| P07 | https://arxiv.org/pdf/2509.09135 | https://github.com/Wangxuefeng1024/Continuous-Time-Value-Iteration-for-Multi-Agent-Reinforcement-Learning |
| P08 | https://homepages.inf.ed.ac.uk/msridhar/Papers/iclr26_multiagentOptionsDiscovery.pdf | https://github.com/raulsteleac/IARO |

All eight PDFs were parsed successfully and visually checked on the title and
representative method pages. P01–P05 and P07 code were selected for local
inspection; P06 and P08 remain paper-only after mechanism-level screening.
