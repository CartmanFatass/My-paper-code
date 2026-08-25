### 1. PDF inspection ledger

| Paper | Exact Local Path | Sections Inspected | Most Relevant Claim to this Round |
| :--- | :--- | :--- | :--- |
| **P01 ACE** | `docs/research/literature/n_k_many_agent_deep_dive/papers/P01_ACE_AAMAS2023.pdf` | Sec 3.2 (Problem Formulation), Sec 4.1 (Async-MAPPO) | ACE explicitly models asynchronous macro-actions where different robots execute actions with varying time delays, but structurally ties its buffers to a fixed number of agents $N$. |
| **P02 ACAC** | `docs/research/literature/n_k_many_agent_deep_dive/papers/P02_ACAC_ICML2025.pdf` | Sec 3.1 (Review of CTDE), Sec 3.4 (GAE for Async MARL) | ACAC formally shifts $\lambda$-discounting from the micro-timestep to the macro-timestep level, handling variable $T_i$ by separating physical time ($\gamma$) and decision depth ($\lambda$). |
| **P03 InforMARL**| `docs/research/literature/n_k_many_agent_deep_dive/papers/P03_InforMARL_ICML2023.pdf`| Sec 3.2 (Information Aggregation), Sec 3.3 (Graph Info Aggregation) | InforMARL demonstrates that global mean pooling over a graph neural network provides a permutation-invariant active-set reference that operates independently of $N$. |
| **P04 Sable** | `docs/research/literature/n_k_many_agent_deep_dive/papers/P04_Sable_ICML2025.pdf` | Sec 3 (Method), Appendix E.2.2 (Adapting the Decay Matrix) | Sable's retention mechanism flattens the agent-timestep sequence and structurally hardcodes $N$ into the decay matrix $D$, explicitly coupling its autoregression to a fixed roster size. |
| **P05 ExpoComm** | `docs/research/literature/n_k_many_agent_deep_dive/papers/P05_ExpoComm_ICLR2025.pdf` | Sec 3.1.3 (Exponential Graphs) | The exponential topology fundamentally relies on a static, sequential ordering of agents ($0, 1, \dots, N-1$) arranged in a ring, making it incompatible with a dynamic active roster. |
| **P06 SafeM3UCRL**| `docs/research/literature/n_k_many_agent_deep_dive/papers/P06_SafeM3UCRL_AAMAS2024.pdf`| Sec 3 (Problem Statement), Sec 3.1 (Safe Mean-Field RL) | The MFC formulation relies on an infinite population of identical, indistinguishable agents represented as a smooth distribution, which inherently erases exact finite identities and rare-but-critical states. |
| **P07 CTMARL** | `docs/research/literature/n_k_many_agent_deep_dive/papers/P07_CTMARL_ICLR2026.pdf` | Sec 3.1 (Problem Formulation), Sec 3.2 (HJB and Policy Learning) | Elapsed time $\Delta t$ must explicitly enter the value gradient semantics for continuous-time learning, validating the necessity of duration-aware ($\gamma^{T_i}$) discounting. |
| **P08 IARO** | `docs/research/literature/n_k_many_agent_deep_dive/papers/P08_IARO_ICLR2026.pdf` | Sec 3.3 (Adding Joint Options to Dec-POMDPs) | Joint options require full-team consensus ($N$ votes) and synchronize execution, proving that barrier coordination nullifies the benefits of heterogeneous skill lifetimes. |

### 2. Corrections to the divergent review

The original PDFs **strengthen** the claims made in the divergent review (`11_GEMINI_DIVERGENT_RAW.md`). There are no statements in the previous output that the PDFs contradict or weaken. 

*   **Strengthened:** The claim that Sable (P04) cannot support an anonymous, dynamically churning roster without massive architectural changes is explicitly confirmed in Sable's Appendix E.2.2 (Equation 9 and 10), which shows the sequence decay matrix heavily relies on fixed $N \times N$ blocks. 
*   **Strengthened:** The claim that ACAC (P02) is the definitive solution for SMDP credit assignment is confirmed by Section 3.4 (Equation 16), which precisely formulates the macro-level $\lambda$-discounting over agent-centric histories.
*   **Strengthened:** The claim that ExpoComm (P05) relies on static IDs is directly corroborated by Section 3.1.3, which assumes a randomly sequential ordering to compute the $2^k$ hops. 
*   **Strengthened:** The claim that pure mean-field distributions alias critical agents is supported by Safe-M3-UCRL (P06) Section 3, which explicitly assumes the limiting regime of infinitely many identical and indistinguishable agents, confirming it cannot track the exact residuals required by HMASD.

### 3. Revised architecture impact

Because the original PDFs uniformly corroborate the physical and architectural constraints inferred in the divergent review, **no changes are required to the portfolio, capability matrix, discriminating evidence, or R55 disposition**. 

The fundamental contradiction remains exactly as stated: Strict autoregressive sequence generation mathematically conflicts with anonymous, dynamic active-set representations unless a learned probabilistic pointer mechanism is introduced. Therefore, the recommended portfolio remains focused on evaluating the **Decentralized Event-Driven Option Critic (H_Decentralized_Field)** against the null baseline (**H0**) and the learned pointer sequence (**H_Pointer**). 

The R55 disposition remains **PAUSE**, as the toy task does not possess the variable-N and variable-lifetime properties required to discriminate between these hypotheses.

### 4. Coverage declaration

I explicitly confirm that **all eight original PDFs** allowlisted in the local source manifest were successfully accessed, read, and inspected during this bounded source-completeness repair.
