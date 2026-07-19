### 1. Evidence validity and delta
*   **Audit and Validity**: The registered result `PASS_CLEAN_CARRIER_DIRECT_ACCESS` is valid and scientifically interpretable. The M0 checks passed exactly, proving zero replay error and strict schema-3 snapshot continuity.
*   **Delta relative to Iteration 5**: Iteration 5 failed because the spatial carrier itself was mathematically opaque to direct MARL optimization at the given budget. This clean-process run reverts to the accessible Generic-SHORT Stage-B task/learner but strictly isolates a task-neutral, continuous physical process channel (`actuator_position`, `actuator_velocity`).
*   **Process Channel Independence**: The result establishes that the physical process channel completely bypasses the learner (never entering observation, critic, reward, GAE, or PPO) yet flawlessly owns dynamic physical state, cleanly freezing on temporary absence, zeroing on genuine join, and resuming on rejoin. It confirms we possess an access-valid, dynamic-membership evidence substrate, while explicitly avoiding any unearned claims about hierarchy, semantic skills, or variable-lifetime efficacy.

### 2. Two-to-four-candidate causal portfolio
**Candidate B: Factorized Discrete Process Executor (H2-B)**
*   *Mechanism*: Replaces shared unstructured categorical FiLM conditioning with a discrete hierarchical factorized executor, allocating specific process dimensions (e.g., discrete actuator profiles) to explicit macro-commitments.
*   *Causal estimand*: Marginal utility gain of explicit structural factorization over flat recurrence on temporally delayed tasks.
*   *Predicted observation*: The explicit discrete hierarchy discovers executable, temporally extended specialized roles that an ordinary un-factored policy fails to coordinate.
*   *Strongest contradiction*: If factorization provides zero significant task reward gain over a flat direct policy, the structural overhead is mathematically redundant.
*   *Confidence*: Medium.

**Candidate C: Simplex Process Command (H2-C)**
*   *Mechanism*: Instead of rigid discrete skills, the high-level policy emits a continuous simplex vector (barycentric coordinates) blending base process-level macro commands.
*   *Causal estimand*: Gradient flow stability from external return through the continuous simplex boundary.
*   *Predicted observation*: Continuous composition resolves the discrete bottleneck, improving fine-grained temporal coordination and producing smooth macroscopic commitments.
*   *Strongest contradiction*: The simplex command structure mathematically collapses into standard continuous deep recurrent actions, completely erasing explicit event ownership and macro-temporal boundaries.
*   *Confidence*: Low/Medium.

**Candidate D: Hierarchy-Null Direct Recurrence (H2-D)**
*   *Mechanism*: Ordinary direct recurrent MARL with zero high-level semantic, skill, or hierarchical bottlenecks, mapping active-set observations directly to primitive actions.
*   *Causal estimand*: Direct active-set utility gain.
*   *Predicted observation*: Matches or exceeds all hierarchical candidates because implicit recurrent memory over the physical clock is sufficient for the task dynamics.
*   *Strongest contradiction*: Fails catastrophically when a task requires explicitly asynchronous, interdependent event-level coordination that exceeds the backpropagation horizon of primitive recurrent cells.
*   *Confidence*: High (mandatory null hypothesis).

### 3. Replacement and simplification ledger
*   **Candidate B**: *Retains* schema-3 runtime, active-set tensor, and Generic-SHORT baseline. *Deletes* categorical FiLM conditioning. *Replaces* unstructured categorical bottleneck with a factorized categorical tensor. *Adds* no module stacks.
*   **Candidate C**: *Retains* active-set tensor, macro-event clock. *Deletes* discrete $z_i$ and `KEEP/SET` logic. *Replaces* categorical skills with a continuous simplex vector. *Adds* an end-to-end differentiable command interface.
*   **Candidate D**: *Retains* schema-3 runtime, Generic-SHORT. *Deletes* high controller, hierarchical skills, intrinsic rewards, macro GAE. *Replaces* two-level architecture with a single direct ordinary-MARL policy. *Adds* nothing.

### 4. Ordinary-MARL and intrinsic boundary
*   **Strongest Ordinary-MARL reduction**: Candidate D acts as the absolute standard-MARL reduction. If Candidate D perfectly solves a given temporal task, any explicit hierarchical mechanism (Candidate B or C) is scientifically superfluous.
*   **Intrinsic boundary**: If any intrinsic signal is reintroduced, it must be rigorously constrained to the focal member's local, anonymous trajectory bounded between explicit membership events. Global team state, external reward, task progress, and global success labels must never leak into the intrinsic semantic signal, ensuring it remains strictly environment-agnostic.

### 5. Variable membership and lifetime semantics
*   **Masks, Survivor, and Rejoin State**: The clean-process result proves the architecture handles dynamic membership flawlessly: survivor RNN hidden states persist unaltered during external roster shocks. Temporary absence freezes process/actuator states, which resume exactly upon rejoin. Genuine joins initialize clean zero states.
*   **Clocks**: Physical clocks govern continuous primitive actions; the macro-event clock triggers high-level policy evaluation; the segment clock restricts the continuous realized lifetime of a specific skill.
*   **Credit**: High-level credit spans the realized segment duration discounted exclusively by event elapsed time ($\gamma^\Delta$). Low-level physical credit is dense across physical step cycles.
*   **Decentralized execution**: Execution scales anonymously using only local observations and assigned skill tokens, fully decoupled from global identity masks or absolute roster indices.

### 6. Literature principles, not imports
*   **ACAC (P02) / InforMARL (P03)**: Principle of explicit, decoupled temporal credit assignment. We adopt the requirement of discounting macro-returns by exactly realized elapsed time ($\gamma^\Delta$) without blindly importing their specific centralized critic networks or joint attention structures.
*   **ExpoComm (P05) / Sable (P04)**: Principle of bounded continuous representations. Continuous latent spaces risk uninterpretable flat collapse. Simplex commands (Candidate C) apply this principle by strictly bounding gradient flow and command space, explicitly rejecting unbounded module stacks or generic latent graph aggregations.

### 7. Retired-line exclusion
No live candidate is a renamed **R29** (direct action-information), **R31-CFEI** (observational effects), **R32-IFEPG** (individual-effect policy gradient), or **R33-IRSC** (intervention-scored complementarity). No candidate reuses Iteration 5's C1 semantic posterior. No proposal introduces global identity labels, external-task reward shaping (e.g., distance to goal), scheduler-only rigid overrides, or fixed duration-catalogue routes.

### 8. Two or three next-evidence candidates
**Evidence A: Candidate D Temporal Extension (Direct Null Baseline)**
*   *Comparator*: Candidate D evaluated on a Generic-SHORT variant with substantially increased temporal delays.
*   *Estimand*: Utility gain of direct recurrence when the task horizon heavily outstrips primitive memory.
*   *Branches*: Pass (proves hierarchy is unnecessary for delayed coordination); Fail (proves the mandatory task prerequisite for testing hierarchical variants).
*   *Portfolio update*: A failure forces the requirement to evaluate hierarchical alternatives B/C.
*   *Prohibited rescues*: Do not tune the network capacity repeatedly to brute-force a pass.
*   *Implementation boundary*: Increase temporal spacing/delay parameters within the Generic-SHORT testbed script.

**Evidence B: Candidate B (Factorized Discrete Executor)**
*   *Comparator*: Candidate B vs. Candidate D on the temporally extended testbed.
*   *Estimand*: Marginal utility gain of explicit hierarchical factorized execution over unstructured direct recurrence.
*   *Branches*: B significantly outperforms D (validates explicit discrete hierarchy); B equals or underperforms D (retires Candidate B).
*   *Portfolio update*: A win structurally isolates and validates explicit discrete hierarchy.
*   *Prohibited rescues*: Do not inject task-specific heuristic masks or hand-authored assignments into the high-level policy.
*   *Implementation boundary*: Replace the current `z_i` FiLM embedding with discrete factorized actor inputs.

### 9. Stop and integration conditions
*   **Retire Candidate B**: Retire if it fails to statistically dominate Candidate D on an explicitly temporally demanding task, or if its discovered categorical factors collapse to uniform behavior.
*   **Retire Candidate C**: Retire if continuous simplex composition merges into flat standard continuous MARL, offering zero measurable event-boundary macroscopic performance gain.
*   **Integration**: A hierarchical candidate (B or C) is justified for full codebase/UAV integration *only* if it demonstrates statistically significant, load-bearing superiority over Candidate D on a testbed strictly requiring asynchronous, heterogeneous lifetimes.
*   **Stop the line**: The entire hierarchical research line must definitively stop if Candidate D (direct recurrence) successfully solves every proposed temporally heterogeneous testbed at scale, conclusively proving that explicit skill/hierarchy bottlenecks are unnecessary overhead.