### 1. Evidence validity
*   **Registered Result**: The outcome `RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS` is fully supported. The C3 direct active-set recurrent controller failed the short-duty floor and gain lower-bound gate, achieving a final stochastic utility of 0.7245 and deterministic utility of 0.7634.
*   **Strongest supported conclusions**: 
    1. The spatial carrier environment, under the frozen optimization budget and neural capacity, is inaccessible even to ordinary unstructured recurrent MARL. 
    2. The C1 semantic-on arm failed its material audit (forced process-effect CI95 `[0.0026, 0.0146, 0.0335]`, bounded strictly below the `1/12` floor), meaning the specific Iteration-5 posterior pressure completely failed to produce executable, naturally used skills.
*   **What cannot be inferred**: Because the baseline direct carrier access condition failed, we *cannot* infer whether a hierarchical architecture (F0/F1) or an intrinsic semantic reward is algorithmically useful or detrimental. The failure is hopelessly confounded by the substrate's opacity to basic optimization.

### 2. Two-to-four-candidate causal portfolio
**Candidate 1: Optimization/Capacity Mismatch (Evidence-Substrate Adjustment)**
*   *Mechanism*: The neural capacity (hidden dimensions) and optimization budget (320k transitions) are insufficient for a *spatial* SMDP dynamic-roster task, causing standard PPO to underfit before useful recurrent state representations form.
*   *Causal estimand*: Direct active-set utility gain as a monotonic function of model width and sample exposure.
*   *Predicted observation*: Scaling capacity and transitions allows the C3 baseline to cross the access threshold, restoring the spatial task as a valid carrier.
*   *Strongest contradiction*: If massive capacity scaling yields no gain, the spatial task dynamics themselves (not the network) are mathematically opaque to independent recurrence.
*   *Confidence*: High; spatial tasks empirically require orders of magnitude more samples than discrete matrix toys.

**Candidate 2: Environment-Agnostic Segment Information Reward (H2-B)**
*   *Mechanism*: The low policy lacks a task-neutral learning pressure. We introduce an anonymous adaptation of the original HMASD $q_d/q_D$ discriminator, restricted entirely to focal-agent trajectory segments bounded by dynamic membership events.
*   *Causal estimand*: The predictability of a focal agent's skill $z_i$ strictly from its anonymous local primitive-action trajectory.
*   *Predicted observation*: The low-level policy learns distinct, executable sub-trajectories, passing the material semantic audit independent of terminal task success.
*   *Strongest contradiction*: The learned intrinsic behaviors may be completely orthogonal to the specific spatial task requirements, resulting in high intrinsic scores but zero external utility gain.
*   *Confidence*: Medium; it restores the original HMASD pressure but its interaction with dynamic variable lifetimes remains unpredictable.

**Candidate 3: Anonymous Continuous Differentiable Skills (H2-C)**
*   *Mechanism*: Replace the fixed categorical skill bottleneck $z_i$ and the categorical `KEEP/SET` logic with a continuous, end-to-end differentiable skill embedding $z_i \in \mathbb{R}^d$.
*   *Causal estimand*: Direct gradient flow from the terminal external reward through the continuous skill embedding to the high-level policy.
*   *Predicted observation*: Executable extended macro-commitments emerge implicitly via backpropagation without needing an artificial explicit intrinsic reward.
*   *Strongest contradiction*: The architecture mathematically merges into a single deep recurrent network, risking the complete erasure of explicit event ownership and temporal abstraction.
*   *Confidence*: Medium.

### 3. Replacement and simplification ledger
*   **Candidate 1 (Capacity Adjustment)**
    *   *Retained*: Schema-3 runtime, spatial carrier task, C3 direct architecture.
    *   *Deleted*: The arbitrary 320k transition limit and frozen network width.
    *   *Replaced*: `hidden_dim` and `environment_transitions` parameters are scaled up.
    *   *Added*: None (no new modules).
*   **Candidate 2 (Segment Information Reward)**
    *   *Retained*: Schema-3 runtime, high/low architecture, categorical skill bottleneck.
    *   *Deleted*: The assumption that terminal reward alone can shape low-level skills.
    *   *Replaced*: The failed Iteration-5 posterior pressure is replaced by a forward predictive discriminator.
    *   *Added*: A variable-length anonymous segment discriminator and a dense intrinsic reward term in the low-level GAE.
*   **Candidate 3 (Continuous Skills)**
    *   *Retained*: Active-set F0/F1 selector, macro-event clock, variable roster.
    *   *Deleted*: Categorical `KEEP/SET` tokens and semantic-on/off branching.
    *   *Replaced*: Discrete $z_i$ replaced with a continuous representation.
    *   *Added*: End-to-end differentiable backpropagation path through the skill bottleneck.

### 4. Intrinsic-reward and ordinary-MARL boundary
*   **Intrinsic-reward boundary (Candidate 2)**: The semantic signal remains environment-agnostic because the discriminator is fed *only* the focal member's local anonymous primitive observations and actions spanning a single realized segment. Global team state, task identifiers, contact sensors, success predicates, and external rewards are strictly withheld.
*   **Ordinary-MARL reduction**: For both Candidate 2 and 3, the strongest standard-MARL reduction is **Candidate 1** (a well-tuned, adequately-sized ordinary recurrent active-set policy like C3). If an adequately scaled C3 solves the task, it proves explicit hierarchical temporal abstraction is unnecessary, rendering the hierarchical additions superfluous.

### 5. Variable membership and lifetime semantics
*   **Masks & Survivor State**: The active-set schema guarantees survivor recurrent hidden states persist entirely unaltered across an event boundary, while newly joined or rejoined members initialize strictly from cold or previously saved offline states.
*   **Physical vs. Event Time**: Physical time governs primitive transitions. Event time dictates when the high-level policy evaluates the active roster to issue new macro-commitments.
*   **Segment Ownership**: A segment is strictly owned by one continuous lifecycle. Temporary leaves terminate the current segment, forcing a truncation of the low-level credit window and preventing cross-lifecycle gradient contamination.
*   **Credit**: High-level macro-credit is correctly discounted over the variable elapsed physical time ($\gamma^\Delta$). Low-level credit is densely assigned across physical steps within the segment.
*   **Decentralized Execution**: The architecture requires only the individual's anonymous observation and assigned skill $z_i$, completely avoiding reliance on global identity tags or total roster counts.

### 6. Literature-derived principles, not modules
*   **InforMARL (P03) / ACAC (P02)**: We extract the architectural principle of explicit temporal credit decoupling. Event-driven boundaries must correctly discount gradients according to *realized elapsed time* ($\gamma^\Delta$) rather than raw step counts. We reject importing ACAC's specific multi-agent critic modules.
*   **ExpoComm (P05) / Sable (P04)**: We derive the principle that continuous representations (like Candidate 3) risk collapsing into flat uninterpretable vectors if unconstrained. Gradient paths must be explicitly bounded to preserve macroscopic temporal structure, rejecting any blind stacking of their specific attention/communication mechanisms.

### 7. Retired-line exclusion
No live candidate is a renamed **R29** (direct action-information), **R31-CFEI** (observational effect), **R32-IFEPG** (individual-effect gradient), or **R33-IRSC** (intervention-scored complementarity). Candidate 2 ports the *original* HMASD intrinsic mutual-information pressure, explicitly adapting it to anonymous variable-length segments, differing fundamentally from R32's global intervention effects. Candidate 1 is simply a capacity fix for the direct baseline. No candidate introduces global identity labels, task-shaped reward heuristics, or scheduler-only overrides.

### 8. Next-evidence candidates
**Source A (Capacity/Budget Isolation for C3)**
*   *Comparator*: C3 (direct policy) at frozen Iteration-5 budget vs. C3 with 3x capacity/budget.
*   *Estimand*: Marginal utility gain of ordinary MARL as a function of capacity on the spatial carrier.
*   *Outcome branches*: If scaled C3 succeeds, the spatial carrier is restored. If it fails, the spatial task is fatally opaque to MARL.
*   *Portfolio update*: Restores or permanently retires the spatial testbed for all hierarchical candidates.
*   *Prohibited rescues*: Do not shape the reward or add intrinsic terms to C3.
*   *Implementation boundary*: Adjust `hidden_dim` and `environment_transitions` parameters only.

**Source B (Segment Information Reward on Generic-SHORT)**
*   *Comparator*: F0 (no intrinsic reward) vs. Candidate 2 (Segment Intrinsic Reward) evaluated on the *already-solved* Generic-SHORT carrier from Stage B.
*   *Estimand*: Material skill separation (forced process-effect score).
*   *Outcome branches*: If Candidate 2 produces distinct executable skills (high forced effect) on an accessible carrier, it validates the explicit semantic hypothesis. If it fails, the semantic mechanism is flawed.
*   *Portfolio update*: Updates the viability of explicit intrinsic reward hierarchies.
*   *Prohibited rescues*: Do not alter the Stage B environment rules.
*   *Implementation boundary*: Integrate the segment discriminator and intrinsic GAE term into the Generic-SHORT runtime.

### 9. Portfolio stop and integration conditions
*   **Retire Candidate 1 (Capacity Adjust)**: Retire if aggressive capacity/budget scaling yields no significant improvement in C3's task access on the spatial carrier.
*   **Retire Candidate 2 (Segment Intrinsic)**: Retire if the intrinsic discriminator successfully produces separated behaviors that the high policy fundamentally fails to align or compose into task-winning strategies on an accessible carrier.
*   **Retire Candidate 3 (Continuous Skills)**: Retire if the continuous hierarchy collapses, offering no distinct macroscopic temporal boundaries or measurable performance gain over flat ordinary MARL.
*   **Integration**: A hierarchical candidate is justified for integration into the broader target domain only if it demonstrates a statistically significant superiority over the adequately scaled C3 baseline on a testbed strictly requiring asynchronous, interdependent long-horizon commitments.
*   **Whole Portfolio Stop**: The entire hierarchical algorithm line should stop permanently if C3 (ordinary active-set recurrence) consistently matches or beats all hierarchical variants across accessible testbeds, definitively proving that standard PPO implicitly learns sufficient temporal coordination without explicit skill bottlenecks.