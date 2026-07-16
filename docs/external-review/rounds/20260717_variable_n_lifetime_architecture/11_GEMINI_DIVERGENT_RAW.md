### 1. Independent thesis

The joint variable-N and variable-lifetime problem requires breaking the synchronous, fixed-tensor structure that pervades standard MARL. Current architectures (including HMASD and most baselines) confound three separate concepts: the physical environment clock, the logical agent decision clock, and the active roster index. 

To unify dynamic N and heterogeneous $T_i$, we must shift from a "tensor-per-timestep" paradigm to an **"Event Ledger"** paradigm. The active policy must operate strictly as a stateless, event-driven function on an anonymous, permutation-invariant active-set representation (e.g., a hybrid field-slot graph). Autoregressive coordination (which inherently relies on a fixed sequence like $1 \dots N$) fundamentally conflicts with an anonymous, dynamically churning roster unless the sequence order itself is a differentiable output of the policy. Therefore, explicit autoregression should be deliberately replaced by **decentralized, independent option execution conditioned on a shared active-skill context**. The execution environment (runner), not the policy, acts as the out-of-core router that maps physical UAV lifecycles to recurrent states and exact physical elapsed time ($\Delta t$) for accurate SMDP credit.

### 2. Evidence audit

*   **Repository Facts:** `transformer_policy.py` structurally enforces a fixed `num_agents` across its inputs, outputs, and attention masks. R49 passed purely interface checks for anonymous encoding but provided no learning evidence. 
*   **Paper Claims vs. Utility:** 
    *   *ACAC (P02)* provides the correct SMDP ledger logic by separating physical time ($\gamma$) from macro-step depth ($\lambda$), but its codebase assumes a fixed `n_agent` structure. 
    *   *InforMARL (P03)* proves global representation scalability via GNNs, but *Safe-M3-UCRL (P06)* acts as a warning that pure mean-field/global pooling aliases away rare, critical agents (requiring the Field-Slot exact residual correction).
    *   *IARO (P08)* proves that forced synchronization (barrier coordination) destroys the utility of variable lifetimes.
*   **False Synthesis in the Brief:** The brief implies that preserving HMASD's autoregressive coordination (H1) is equally viable alongside H3. However, under the constraint that ordering must be anonymous, deterministic, and free of environment keys, generating a strict autoregressive sequence is mathematically brittle (feature-sorting ties break exact replayability). Autoregression and anonymous dynamic sets are fundamentally at odds without introducing stochastic sequence generation. 

### 3. Portfolio reconstruction

*   **RETIRE H1 (Autoregressive event-token coordinator):** Retired because deterministic autoregressive ordering on an anonymous set without environment keys is unstable, and sorting by internal continuous features risks ties that destroy policy replayability.
*   **MERGE H2 & H3 $\rightarrow$ H_Decentralized_Field (Decentralized Event-Driven Option Critic):**
    *   *Replaces:* Fixed-N global MAT attention and synchronous macro-timesteps.
    *   *Retains:* HMASD skill semantics and exact probability/credit correctness (via an ACAC-style per-agent ledger).
    *   *Adds:* Agents trigger independently based on their own $T_i$. Coordination is achieved not by sequential assignment, but by conditioning each independent option-policy on a permutation-invariant active-pool summary (Hybrid Field-Slot).
*   **RETAIN H0 (Ordinary Masked/Padded MARL):** Retained as the critical complexity-reduction null hypothesis.
*   **ADD H_Pointer (Learned Autoregressive Sequence):**
    *   *Replaces:* Fixed-index MAT.
    *   *Retains:* Strict autoregressive joint assignment pressure.
    *   *Adds:* A learned sequence-to-sequence pointer mechanism that emits the anonymous sequence order. The log-probability of the sequence order becomes part of the behavior policy, resolving the anonymous ordering contradiction probabilistically.

### 4. Capability matrix

| Architecture | Dynamic N | Het. Lifetime ($T_i$) | HMASD Skills | Coordination | SMDP Credit | Comp. Scaling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **H0 (Masked MARL)** | Padded Masking | Padded/Repeated Steps | Retained | Retained (Fixed Order) | Distorted | $O(N_{max}^2)$ |
| **H_Decentralized_Field** | Ragged Tensor + Graph | Agent-Centric Ledger | Retained | Replaced (Active Context) | Exact ($\gamma^{T_i}$) | $O(N_{active} \log N_{active})$ |
| **H_Pointer** | Ragged Tensor + Graph | Agent-Centric Ledger | Retained | Retained (Learned Order) | Exact | $O(N_{active}^2)$ |

### 5. Unifying insight versus module stack

**Module Stack to Avoid:** Blindly combining ACAC's centralized critic, ACE's asynchronous execution shell, InforMARL's message passing, and Sable's retention. This will collapse because their underlying data tensors implicitly assume global time alignment or static array bounds.

**Unifying Principle (The Agent-Centric Event Ledger):** Separate the physical simulation loop from the learning buffer. The neural architecture becomes a stateless function mapping an anonymous active-set observation to a skill choice. The *runner* manages state routing using lifecycle metadata. When a UAV triggers, the runner retrieves its historical RNN state (ignoring it if it's a new cold-start), queries the policy, logs the exact physical time elapsed since its last event, and stores it in a ragged ledger. All discounting and GAE occur strictly on these asynchronous agent-specific boundaries.

### 6. Discriminating evidence

*   **Evidence Source:** A shared, existing testbed (e.g., a continuous particle environment) modified *only* to enforce high-variance asynchronous action delays (variable $T_i$), keeping $N$ fixed initially.
*   **Measurement:** Compare the sample efficiency and coordination breakdown of decentralized concurrent decisions (H_Decentralized_Field proxy) against a forced autoregressive chain (H_Pointer proxy) under asynchronous conditions.
*   **Portfolio Updates:**
    *   If H_Decentralized_Field matches or exceeds the performance of the autoregressive chain, it proves that explicit autoregression is unnecessary when macro-actions naturally stagger in continuous time. We retire H_Pointer.
    *   If H_Decentralized_Field suffers severe anti-coordination (thrashing), the active-skill context is insufficient, validating the necessity of H_Pointer's complex sequence generation.
    *   If H0 (masked MARL) matches the performance of both, we retire the entire complex portfolio.

### 7. R55 disposition

**PAUSE.** 
R55-ABRP-G0 tests a fixed-membership, fixed-horizon direct-edge topology. Because it deliberately isolates itself from episode-internal join/leave and heterogeneous $T_i$, it operates in a regime where the contradictions of anonymous autoregressive ordering do not manifest. Passing R55 provides zero information gain toward resolving the tension between H_Decentralized_Field and H_Pointer. 

### 8. Strongest self-critique

The preferred account (H_Decentralized_Field) deliberately abandons explicit autoregressive coordination, relying entirely on agents observing the "active skill pool" to avoid redundant actions. If the environment contains severe anti-coordination bottlenecks (e.g., exactly one UAV must enter a narrow corridor, and multiple trigger simultaneously), concurrent independent policies might persistently collide. 

In such bottleneck scenarios, the entire variable-N/variable-lifetime architecture could prove inferior to H0 (masked MARL). H0 preserves a fixed global ordering that flawlessly breaks symmetry and prevents anti-coordination, arguably making the wasted compute on masked agents a worthwhile price to pay compared to the sample inefficiency of learning to avoid collisions in a decentralized system.
