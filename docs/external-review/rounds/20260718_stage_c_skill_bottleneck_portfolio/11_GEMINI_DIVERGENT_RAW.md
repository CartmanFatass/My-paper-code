### 1. Evidence audit
* **Stage B** established that an ordinary unstructured recurrent active-set policy can fully solve the dynamic-roster testbed. It proves the environment task, observation space, and state representations are mathematically accessible to standard PPO without a hierarchical skill bottleneck.
* **Stage C forced effects and natural execution failure** established that the F0/F1 hierarchical architecture structurally fails to produce executable, task-aligned skills. Although F1 shifts its label distribution conditionally based on the applied prefix (proven by the positive `rho` and TV metrics), the low-level policy ignores these labels because it receives no gradient or reward pressure to differentiate its primitive actions based on the skill token.
* **Original HMASD** established that the `q_d/q_D` mutual-information discriminator successfully forces the low-level policy to execute distinct behaviors for distinct skill tokens in a static, fixed-$N$ setting. It does *not* establish whether this intrinsic pressure remains stable when membership changes mid-episode and skill lifetimes become heterogeneous.

### 2. Causal portfolio
**Candidate 1: Anonymous Intrinsic Skill Mutual Information (H2-A/B)**
*   *Mechanism:* Reintroduce a dynamic-roster adaptation of the original HMASD `q_d/q_D` discriminator. It scores the predictability of the focal agent's skill token from its anonymous, variable-length primitive trajectory segment, scaling the intrinsic reward by the event duration to align with $\gamma^\Delta$.
*   *Predicted observable:* Forced-effect audits will show distinct, executable sub-trajectories for different skills.
*   *Strongest contradiction:* The discovered intrinsic skills might not align with the specific long/short roles required by the terminal team task, resulting in execution without task success.
*   *Confidence:* High; it directly ports the proven original mechanism to the dynamic-roster runtime.

**Candidate 2: Continuous Skill Composition (H2-C)**
*   *Mechanism:* Replace the discrete skill indices and categorical `KEEP/SET` sampling with a continuous skill embedding vector. The high-level controller outputs this vector, and the low-level policy conditions on it via continuous differentiable paths.
*   *Predicted observable:* End-to-end gradients will align the skill representations directly with the terminal task return, bypassing the need for explicit intrinsic reward matching.
*   *Strongest contradiction:* The architecture mathematically merges into a single deep continuous network, potentially erasing the intended temporal commitment abstraction.
*   *Confidence:* Medium; it solves the bottleneck but risks collapsing the hierarchy.

**Candidate 3: Ordinary Direct Active-Set Recurrence (H2-D)**
*   *Mechanism:* Remove the hierarchical skill bottleneck entirely. Run a single recurrent policy over the active roster, mapping the schema-3 event observations directly to primitive actions.
*   *Predicted observable:* High terminal task performance matching Stage B, proving the hierarchy itself is an artificial impediment for this specific task.
*   *Strongest contradiction:* Fails to facilitate multi-step coordinated macro-commitments if the task horizon is extended beyond what primitive recurrence can bridge.
*   *Confidence:* High for solving this testbed, low for fulfilling the broader HMASD capability goals.

### 3. Replacement ledger per candidate
*   **Candidate 1 (Anonymous Intrinsic):** Retains schema-3 runtime, F0/F1 prefix selector, high/low architecture. Deletes the assumption that terminal reward shapes the low-level policy. Replaces nothing. Adds a variable-length trajectory discriminator and an intrinsic reward term added to the low-level GAE.
*   **Candidate 2 (Continuous Composition):** Retains active-set F0/F1 selector and macro-event clock. Deletes categorical `KEEP/SET` tokens and original `q_d/q_D` components. Replaces discrete $z_i$ with a continuous embedding vector. Adds an end-to-end differentiable gradient path connecting high and low actors.
*   **Candidate 3 (Ordinary Direct):** Retains schema-3 runtime and active-set tensor representations. Deletes high controller, skill bottleneck, F1 prefix, and macro GAE. Replaces the hierarchical actor with a single direct primitive-action recurrent policy. Adds nothing.

### 4. Intrinsic-reward boundary
For Candidate 1, the original `q_d/q_D` semantics survive variable membership by enforcing strict segment ownership: the discriminator scores a trajectory segment belonging *only* to one continuous lifecycle between two membership shocks. By feeding the discriminator solely the focal member's local anonymous primitive observation trajectory and its assigned skill token—stripping all global state, task fields, role labels, and external rewards—the intrinsic reward remains completely environment-agnostic.

### 5. Probability, credit and lifetime audit
*   **Candidate 1:** High policy requires macro-step likelihoods; low policy requires primitive-step likelihoods. Gradients are detached between them. High policy receives terminal external return via macro GAE; low policy receives the same terminal return plus dense intrinsic reward. Segments cleanly terminate at lifecycle leaves.
*   **Candidate 2:** Requires continuous likelihoods for the skill embedding and primitive likelihoods for the low policy. The detach boundary is removed; gradients flow continuously. Credit is exclusively the terminal external reward.
*   **Candidate 3:** Requires only primitive action likelihoods. Uses standard PPO physical-time return and masks. Segment ownership simply restricts RNN hidden-state continuity.

### 6. Ordinary-MARL objections
*   **Against Candidate 1:** The intrinsic reward injects non-stationary bias that distracts from the true external objective. A well-tuned standard network finds useful internal representations implicitly without needing to explicitly classify them.
*   **Against Candidate 2:** A continuous hierarchical embedding is mathematically isomorphic to adding another recurrent MLP layer; it provides no structural coordination advantage over a sufficiently deep, flat MARL policy.
*   **Against Candidate 3:** While standard MARL solves this specific short-horizon toy, it abandons explicit heterogeneous skill lifetimes and interpretable event boundaries, failing the core motivation of the HMASD project.

### 7. Retired-line exclusion
*   Candidate 1 ports the *original* HMASD mutual-information logic directly to variable-length anonymous segments. It is not R29 (direct action-information), R31-CFEI (observational forced effects), R32-IFEPG (individual-effect gradient), or R33-IRSC (intervention-scored complementarity).
*   Candidate 2 introduces fully continuous embeddings, a structure never tested in this repository's retired lines.
*   Candidate 3 is an unstructured control baseline, not a renamed hierarchical scheduler or shaped identity route.

### 8. Serialized evidence graph
1.  **Source 1 (Skill Execution Isolation):** Evaluate Candidate 1 using *only* the intrinsic reward (zero external reward) on the Stage C testbed. **Update:** If it fails to produce distinct executable skills (via forced audit), H2-A is falsified, and Candidate 1 is retired. If it succeeds, it proves the dynamic-roster discriminator works.
2.  **Source 2 (Task Alignment):** Evaluate Candidate 1 with both intrinsic and terminal external reward. **Update:** If it executes skills but fails the task, H2-B (alignment mismatch) is confirmed, heavily penalizing Candidate 1. If it solves the task, it validates the discrete hierarchy.
3.  **Source 3 (Continuous Benchmark):** Evaluate Candidate 2 end-to-end. **Update:** If it matches Candidate 1's performance but is structurally simpler, it shifts preference to H2-C. If it collapses to the performance of a flat policy (Candidate 3), it falsifies the continuous hierarchy.

### 9. Portfolio stop and integration conditions
*   **Retire Candidate 1:** Retire if the intrinsic reward produces distinct executable behaviors but the high-level controller fundamentally fails to align these behaviors with the terminal external task return.
*   **Retire Candidate 2:** Retire if the continuous hierarchy collapses into a single undifferentiated mode or provides zero performance/stability gain over Candidate 3.
*   **Retire Candidate 3:** Retire as a primary architecture if it succeeds here but fails completely on tasks requiring explicit long-horizon macro-commitments, serving only as a baseline.
*   **Justify Integration:** Integration into the main UAV target is justified if a hierarchical candidate (1 or 2) significantly outperforms the flat Candidate 3 baseline on a testbed requiring asynchronous, interdependent long-horizon commitments, proving the hierarchy's distinct algorithmic value.
*   **Stop Portfolio:** The entire portfolio must stop if Candidate 3 perfectly solves all dynamic-roster and long-horizon tasks while the hierarchical candidates consistently fail or provide no measurable advantage, indicating the HMASD hierarchy is fundamentally unnecessary for the target domain.
