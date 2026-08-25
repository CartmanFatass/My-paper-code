### 1. Evidence validity and exact delta
*   **M0 Audit**: Valid. Replay errors and checkpoint round-trip errors are exactly zero. Anonymous relabeling is correct (max error `1.78e-7`), confirming the active-set survivor continuity and simulation/schema integrity.
*   **H (Oracle High/Skill)**: Valid and identified. Passes tracking/completion/utility against strict floors. This establishes that the benchmark's underlying spatial/temporal mechanics are structurally reachable when perfect macroscopic assignment is provided.
*   **C (Calendar/Static Null)**: Valid and identified. Fails strictly below ceilings. This proves that naive periodic/static schedules are insufficient, isolating a genuine environmental requirement for dynamic assignment.
*   **S (Static Oracle Pressure)**: Valid and identified. The H-minus-S margins are strictly positive and beyond required lower bounds, proving that heterogeneous skill lifetimes are materially superior to uniform/static lifetimes for this task.
*   **D (Direct Ordinary Recurrence)**: Validly evaluated but **unidentified/no-access**. Held-out utility (0.616) and D-minus-C LCBs fail their required margins. 
*   **Exact Delta**: We have identified that the noncalendar benchmark structurally supports dynamic, heterogeneous temporal commitments (H > S > C), but we have *not* identified whether an end-to-end learned hierarchy is necessary or possible, because the ordinary unstructured baseline (D) failed basic task access. H/S oracle separation alone does *not* prove hierarchy is required; it only proves an oracle can solve the math.

### 2. Two-to-four-candidate causal portfolio
*   **Candidate A: Optimization/Credit Mismatch (Model/Data-Flow Limit)**
    *   *Mechanism*: D's failure is caused by sparse terminal reward and insufficient optimization budget (320k transitions, 1k steps) over a long temporal horizon, leading to flat gradients before recurrent memory can form.
    *   *Implication*: The benchmark is valid but severely under-budgeted. D needs capacity/sample scaling before hierarchy can be legitimately tested.
*   **Candidate B: Direct Action Factorization Missing (Spatial vs. Temporal)**
    *   *Mechanism*: D maps complex active-set observations flatly into monolithic primitive actions. The bottleneck is not explicitly temporal, but rather an entanglement of physical process (actuation) and semantic commitment.
    *   *Implication*: D requires a factored action head (separating physical movement from commitment intent) to solve the task, without needing explicit hierarchical temporal limits.
*   **Candidate C: Genuine Temporal Abstraction Required**
    *   *Mechanism*: The benchmark's noncalendar, heterogeneous lifetimes inherently exceed the capacity of primitive unstructured recurrence to properly credit early macro-decisions, causing flat D to fail.
    *   *Implication*: A hierarchical event-driven architecture (with discrete $z_i$ or continuous skills and macro-discounting) is fundamentally required.

### 3. Benchmark versus learner diagnosis
To distinguish these failures without confounding them:
*   *Sparse terminal credit* vs. *Genuine temporal abstraction*: If an artificial dense reward instantly solves D, the failure was mere sparsity. If dense reward still fails D but a hierarchical learner succeeds, the failure is genuine temporal abstraction.
*   *Model/data-flow limits* vs. *Task construction*: If heavily scaling D's capacity solves the task, it was a data-flow limit. If H/S remains solvable but scaled D cannot learn anything, the benchmark contains artificial unlearnable bottlenecks (e.g., mathematically opaque state transitions) that the oracle bypasses.
*   *Action factorization*: If splitting D's output heads solves the task, the bottleneck was spatial action dimensionality, invalidating the claim that explicit temporal abstraction is required.

### 4. Replacement and simplification ledger
*   **Candidate A (Credit/Budget Fix)**: *Retains* schema-3 D architecture, environment. *Deletes* the frozen 320k budget constraint. *Replaces* with scaled transitions/optimizer steps. *Adds* nothing structural.
*   **Candidate B (Factored D)**: *Retains* schema-3 D baseline. *Deletes* monolithic action layer. *Replaces* with a split physical/commitment action space. *Adds* zero new networks.
*   **Candidate C (Hierarchical Event-Driven)**: *Retains* event clock, active-set tensor. *Deletes* D's direct mapping. *Replaces* with high/low separation. *Adds* an environment-agnostic intrinsic segment reward or differentiable simplex command boundary.

### 5. Strongest ordinary-MARL reduction
The strongest information-matched reduction before any hierarchical claim is a **High-Capacity, Factored Direct Recurrent Policy (Scaled/Factored D)**. It receives the exact same active-set observation stream and asynchronous macro-event triggers as a hierarchical model but maps them directly to primitive continuous actions using a deep LSTM, bypassing any discrete $z_i$ skill assignments or intrinsic segment rewards. If an intrinsic reward is later added to a hierarchical candidate, it must remain strictly restricted to the focal member's local, anonymous trajectory bounded between membership events, remaining entirely environment-agnostic.

### 6. Variable membership and lifetime semantics
*   **Masks and Anonymous Lifecycle**: Validated. The benchmark correctly forces anonymous join/leave/rejoin events that trigger active-set masks without relying on global identity.
*   **Survivor/Rejoin State**: Validated by M0 checks. Recurrent hidden states cleanly persist across event shocks; rejoins restore state accurately.
*   **Clocks**: 
    *   *Physical clock*: Primitive transitions. 
    *   *Event clock*: Asynchronous roster shocks evaluating macro-decisions. 
    *   *Segment clock*: The realized heterogeneous lifetime of a skill (proven materially relevant by H > S). 
    *   *Credit clock*: Terminal reward window evaluated at episode end.

### 7. Literature principles, not imports
*   **InforMARL (P03) / ACAC (P02)**: Principle of decoupled temporal credit assignment. We apply $\gamma^\Delta$ macro-discounting and segment-owned credit horizons. We explicitly *reject* blindly importing their centralized joint-critics or global attention structures.
*   **ExpoComm (P05) / Sable (P04)**: Principle of bounded continuous representations. We recognize that unstructured continuous representations (like D) risk temporal collapse. Any continuous command interface must explicitly restrict gradient flow to preserve discrete temporal event ownership.

### 8. Two or three separating evidence candidates
**Evidence 1: Scaled-Budget D (Diagnostic Limit Check)**
*   *Comparator*: Frozen D vs. Scaled D (3x transitions, 3x optimizer steps).
*   *Estimand*: Marginal utility gain of unconstrained standard recurrence.
*   *Branches*: Scaled D solves it (proves hierarchy unnecessary; temporal abstraction was a capacity illusion); Scaled D fails (proves optimization/budget is not the sole blocker).
*   *Portfolio update*: A failure forces the requirement to test Factored D or Candidate C.
*   *Prohibited rescues*: Do not shape the reward or inject intrinsic signals into D.
*   *Minimal implementation*: Modify `environment_transitions` and `optimizer_steps` in the benchmark runner.

**Evidence 2: Factored D (Spatial vs. Temporal Action Split)**
*   *Comparator*: Monolithic D vs. Factored D (separate continuous heads for physical movement vs. semantic tracking).
*   *Estimand*: Utility gain from spatial action decomposition vs. temporal decomposition.
*   *Branches*: Factored D solves it (bottleneck was spatial/dimensionality, retire temporal hierarchy); Factored D fails (strongly isolates Candidate C temporal abstraction as necessary).
*   *Portfolio update*: Validates or refutes the necessity of explicit temporal boundaries.
*   *Minimal implementation*: Split the final linear output layer of the ordinary D policy.

### 9. Unselected ideas and stop conditions
*   **Unselected/Parked Ideas**: 
    *   *Simplex continuous commands*: Parked until a discrete temporal hierarchy is proven necessary. 
    *   *Anonymous segment intrinsic discriminator*: Parked because introducing it now confounds the failure of D; it should only be introduced once D is proven to fail a learnable benchmark due to temporal abstraction.
*   **Stop and Promotion Conditions**:
    *   *Retire Benchmark*: If heavy scaling (Evidence 1) and factorization (Evidence 2) of D still leave the benchmark completely unlearnable, the benchmark is mathematically opaque and must be redesigned or abandoned.
    *   *Retire Hierarchy*: If any ordinary-MARL variant (Scaled/Factored D) perfectly matches H oracle performance, explicit temporal abstraction is proven superfluous. Stop the hierarchical line.
    *   *Promote Hierarchy*: If D definitively fails all reasonable scaling and factorization, but a self-discovered hierarchical model (Candidate C) succeeds and approaches H, promote the explicit hierarchy to the target UAV integration.
