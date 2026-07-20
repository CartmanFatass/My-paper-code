### 1. Evidence and branch validity
*   **Audit of M0 and branch validity**: The `INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT` branch was correctly and deterministically triggered. The M0 evidence confirms the implementation is perfectly valid: zero replay errors, zero low-level rows/gradients (proving the fixed executors were perfectly frozen), finite high updates, and exact survivor continuity. 
*   **Implementation vs. Scientific Comparator**: The implementation of the dual-path event architecture is mathematically sound and bug-free. However, the scientific comparator—the constructive routing oracle—is invalid. The oracle failed to reach the `0.95` floor for SHORT (scoring `0.660`) and UTILITY (`0.819`), whereas the learned policy achieved `0.938` and `0.940` respectively. An upper-bound oracle cannot logically perform worse than a naive learned agent; thus, the comparator contract itself is scientifically defective.

### 2. Oracle opportunity diagnosis
The constructive routing oracle can have lower SHORT/utility than the learned actor due to several non-exclusive mechanisms:
*   **Heuristic Brittleness vs. Continuous State**: The oracle relies on a strict, hand-authored constructive rule (e.g., proximity thresholds for assigning SHORT). In a continuous spatial environment, rigid thresholds cause catastrophic oscillation or miss dynamic interception opportunities that a learned neural policy smoothly approximates. (Invalidates: The assumption that the task's optimal policy can be hand-coded simply).
*   **Macro-Event Clock / Temporal Discount Exploitation**: The oracle might assign a skill correctly for the instantaneous state, but because skills commit over an event duration, the world state changes before the next event clock tick. The learned actor might learn to preemptively switch skills or exploit the $\gamma^\Delta$ discount boundary to maximize return. (Invalidates: The assumption that instantaneous state heuristics translate to optimal macro-temporal commitments).
*   **Supplied-Executor Edge Cases**: The hardcoded `SHORT` executor might fail or behave suboptimally under the exact boundary conditions where the oracle triggers it. The learned actor avoids these failure modes by triggering `SHORT` only in safe state-pockets. (Invalidates: The assumed optimality of the supplied primitives).

### 3. Two-to-four-candidate causal portfolio
**Candidate 1: Oracle Heuristic Defect (State-Dependent Opportunity)**
*   *Mechanism*: The hand-authored oracle rule fails to capture the true joint-state opportunity surface, while standard PPO discovers a more optimal stochastic routing policy.
*   *Evidence*: The learned high policy heavily outperforms the oracle on the SHORT task (`0.938` vs `0.660`).
*   *Strongest contradiction*: If the oracle mathematically implements the exact theoretical solution to the MDP, it cannot be beaten.
*   *Confidence*: High.
*   *Separating observation*: A relaxed, smoothed, or epsilon-greedy oracle outperforming the strict deterministic oracle.

**Candidate 2: Event-Time / Discounting Exploit**
*   *Mechanism*: The learned actor maximizes the episodic return by manipulating the event boundaries—switching commitments early to reset the supplied-executor state machine or to game the $\gamma^\Delta$ credit assignment.
*   *Evidence*: The high relative drift (`2.067`) indicates the high policy aggressively updated away from initialization to find a non-obvious optimal behavior.
*   *Strongest contradiction*: If utility is strictly a terminal sum of episodic rewards with no step penalties, discount-gaming is mathematically impossible.
*   *Confidence*: Medium.
*   *Separating observation*: The learned policy exhibits a significantly higher macro-action switching frequency (shorter segments) than the oracle.

**Candidate 3: Ordinary Direct-MARL Sufficiency (The Null)**
*   *Mechanism*: The supplied executors simply act as a hardcoded options-framework. The task does not actually require temporal abstraction and is easily solved by an ordinary recurrent policy.
*   *Evidence*: The learned high path successfully masters the routing in only 320k transitions, suggesting the underlying task state-space is simple.
*   *Strongest contradiction*: Direct unstructured MARL failing to solve the exact same task due to horizon/delay limits.
*   *Confidence*: High.
*   *Separating observation*: Direct unstructured MARL matching the utility of the supplied-executor high path.

### 4. Ordinary-MARL and replacement audit
*   **Strongest simpler reduction**: A single direct active-set recurrent policy (ordinary MARL) that maps observations directly to primitive actions, deleting the supplied executors, the oracle, and the high/low split entirely.
*   **Candidate 1 (Oracle Defect)**: *Retains* supplied executors, event clock, high policy. *Replaces* the strict constructive oracle with a relaxed or empirical expert comparator. *Deletes* the invalid 0.95 threshold. *Adds* an empirically tuned heuristic bound.
*   **Candidate 2 (Discount Exploit)**: *Retains* event architecture. *Replaces* the physical step reward structure to eliminate early-termination loopholes. *Deletes* the current evaluation metric. *Adds* strict penalty for premature macro-action termination.
*   **Candidate 3 (Direct Null)**: *Retains* the active-set testbed. *Deletes* all hierarchical routing, oracles, and fixed primitives. *Replaces* dual-policy with single flat policy.

### 5. Variable membership, lifetime and intrinsic boundary
*   **Anonymous membership and survivor continuity**: The M0 audit strictly confirms `rejoin_survivor_high_continuity` and `temporary_leave_freeze`. The event architecture preserves survivor recurrent state unaltered across dynamic membership shocks.
*   **Distinct clocks and credit**: The architecture cleanly decouples the physical clock (primitive actions) from the event clock (high-level routing decisions) and the segment clock (credit window), correctly applying `owner_local_physical_time_credit`.
*   **Environment-agnostic intrinsic boundary**: No intrinsic reward is active in this supplied-executor test. If a semantic objective is integrated later, it must strictly consume only anonymous, local segment trajectories and completely exclude task fields, identity, and global terminal rewards.

### 6. Literature principles, not modules
*   **Decoupled Temporal Credit (ACAC/P02, InforMARL/P03)**: The literature establishes the principle of separating credit across heterogeneous timescales ($\gamma^\Delta$). We use this principle to explain Candidate 2 (event-time exploitation) without blindly importing their specific joint-attention or centralized critic networks. 
*   **Comparator Validity in Options (ACE/P01)**: Constructive upper bounds for hierarchical options are notoriously brittle. We extract the principle that a learned high-level policy often discovers macro-action synergies that hand-authored heuristics miss, emphasizing the need for empirical baselines over constructive strict rules.

### 7. Two or three next-evidence candidates
**Evidence A: Direct Recurrence Baseline (Ordinary-MARL Control)**
*   *Comparator*: Learned High Path (with supplied executors) vs. Direct Recurrent MARL (no executors, flat policy).
*   *Estimand*: Marginal utility gain of the fixed macro-action space over unstructured recurrence.
*   *Mutually exclusive branches*: If Direct MARL matches/beats the High Path, hierarchy is unnecessary for this task. If Direct MARL fails, the fixed options are load-bearing.
*   *Portfolio update*: Validates or retires the necessity of temporal abstraction on this specific spatial carrier.
*   *Prohibited rescue*: Do not inject task heuristics into the Direct MARL baseline.
*   *Minimal implementation boundary*: Run the standard C3 direct active-set baseline on this specific environment contract.

**Evidence B: Empirical Oracle Relaxation**
*   *Comparator*: Strict Oracle vs. Tuned/Relaxed Heuristic Oracle.
*   *Estimand*: The true opportunity ceiling of constructive routing.
*   *Mutually exclusive branches*: If the relaxed oracle scores $>0.95$, Candidate 1 is validated and the contract can be repaired. If it remains $<0.95$, the supplied primitives themselves are defective.
*   *Portfolio update*: Isolates whether the failure is in the routing rule or the physical primitives.
*   *Prohibited rescue*: Do not train a neural network to act as the oracle.
*   *Minimal implementation boundary*: Modify the hardcoded conditional thresholds in the oracle's Python routing function.

### 8. Valuable unselected ideas
*   **Continuous Simplex Commands**: The idea to replace discrete skills with continuous barycentric commands is parked because the immediate priority is establishing a valid discrete comparator contract. If discrete fixed options cannot be reliably orchestrated, continuous execution adds premature complexity.
*   **Skill-Conditioned Mutual Information**: Parked because this run uses fixed (supplied) executors. It becomes relevant only when we return to *discovering* executable skills, rather than routing pre-programmed ones.

### 9. Stop and integration conditions
*   **Retire the supplied-executor line** if standard unstructured Direct MARL matches or exceeds the learned high path's utility, proving the supplied primitives offer no structural temporal advantage.
*   **Merge into a simpler controller** if the relaxed oracle (Evidence B) cannot be fixed, implying the task dynamics do not cleanly factorize into discrete human-authored primitives.
*   **Eligible for learned-skill integration** *only* when (1) the oracle is repaired (validating the opportunity contract), AND (2) a flat Direct MARL baseline is proven to fail, establishing that hierarchical routing over extended temporal commitments is scientifically load-bearing.
