### 1. Design verdict
`MODIFY_TESTBED_DRAFT`.
*Rationale:* The anonymous dual-duty process correctly exposes episode-internal roster dynamics and heterogeneous commitments, but its terminal reward must be modified to a continuous/graded completion fraction to prevent the zero-access collapse observed in the R51 full-conjunction failure.

### 2. Causal graph and hypothesis audit
* **H0 (shared-context sufficiency):** Supported if F0 learns the task to an equivalent level as F1; evidence requires both to succeed with no statistically significant performance or collision-rate delta.
* **H1 (irreducible applied-prefix coordination):** Supported if F1 statistically dominates F0 in final task score and exhibits measurable conditional prefix dependence (e.g., probability of selecting `SERVE_PERSISTENT` drops when the applied working-set prefix already contains a `SERVE_PERSISTENT` commitment).
* **H2 (skill-semantic/low-control bottleneck):** Supported if the direct unstructured ordinary-policy baseline solves the task but both F0 and F1 fail, shifting blame from the task/environment to the latent skill bottleneck.
* **H3 (exogenous-opportunity timing bottleneck):** Excluded from direct support in this testbed; a failure of F1 does not strictly prove timing is the bottleneck without testing a learned-timing variant, which is unauthorized.

### 3. Launch-exact environment contract
* **Roster process:** Exogenous deterministic template tracking $N$: $4 \to 2 \to 6 \to 4$. Transitions occur at fixed micro-steps: 20 (two temporary leaves), 40 (two rejoins, two genuine joins), and 60 (two terminal leaves). Indices and lifecycle labels are randomly permuted.
* **Task dynamics:** One persistent duty requiring accumulated progress; short jobs arriving at stochastic intervals that expire in 5 primitive steps.
* **Observations:** Public duty state (persistent progress fraction, short job timers), local task state (member's own progress contribution). No global identity, roster index, or hard masks.
* **Primitive actions:** Discrete set: `0=IDLE`, `1=SERVE_PERSISTENT`, `2=SERVE_SHORT`.
* **Horizon:** $H=80$.
* **Reset:** Randomized duty initial states and short job arrival seeds.
* **Terminal reward:** Shared graded reward: `0.5 * (persistent_progress / max_progress) + 0.5 * (completed_short_jobs / total_short_jobs)`. No per-step shaping, potential differences, or auxiliary losses.

### 4. Learnability and access attribution
* **Access instrument:** A single, shared, direct ordinary recurrent MAPPO policy (no KEEP/SET, no skill bottleneck, outputting primitive actions directly at each step) run on the identical variable-$N$ roster schedule.
* **Separation logic:**
  1. If the direct ordinary policy fails: Environment no-access (stop and fix toy).
  2. If the direct policy succeeds but F0/F1 fail: Latent-skill bottleneck (H2).
  3. If direct policy succeeds, F0 succeeds, and F1 $\approx$ F0: H0 (F1 prefix adds no value).
  4. If direct policy succeeds and F1 $>$ F0 by a specified margin: H1 (F1 prefix value).
This requires no chain of fixed-$N$ specialist gates, resolving the R51-R54 sequential blocking failures.

### 5. F0/F1 causal isolation
F0 and F1 rely on the exact same schema-3 event runtime, `variable_roster_event` parameters, and `StrictHMASDMAPPOLowLevelPolicy`. The sole difference is the configuration string switching the decoder from evaluating the initial active-set summary (F0) to the applied working-set summary (F1). Because the environment provides no identity tokens, static assignment masks, or artificial symmetries, any F1 advantage is causally isolated to common-support autoregressive conditioning on the dynamically changing working roster.

### 6. Metrics and outcome branches
* **Metrics:** 1) Graded terminal task score. 2) Redundancy rate (fraction of steps $>1$ member serves the same short job). 3) Prefix-response KL divergence (shift in skill distributions under simulated prefixes).
* **Outcome branches:**
  * *Stop/Retain F0:* If F0 achieves target score and F1 LCB is indistinguishable, accept H0 and permanently retain F0.
  * *Identify skill bottleneck:* If direct policy succeeds but F0/F1 fail, halt and redesign the skill embedding space.
  * *Support F1:* If F1 achieves a $>0.15$ final-minus-zero LCB score advantage over F0 with a significantly reduced redundancy rate, accept H1 and authorize F1 integration for UAV task domains.

### 7. Minimum evidence budget
* **Parallel configuration:** 16 environments for fast local execution.
* **Exposure:** 500,000 environment steps (sufficient for a toy discrete task).
* **Optimizer updates:** Standard PPO configuration (10 epochs, 5 minibatches per rollout).
* **Evaluation:** 128 episodes over 4 evaluation blocks using exact deterministic execution.
* **Seed logic:** 3 independent seeds to establish a Lower Confidence Bound (LCB) on final-minus-zero learning gain, ensuring statistical significance as mandated by the R53 failure.

### 8. Final-capability map and replacement ledger
* **Retain:** Schema-3 event runtime, F0 reduction, F1 prefix selector, strict terminal-only reward, discrete un-identified active set representations, exact evaluation scripts.
* **Delete:** R51-R54 specialist gates and threshold-only prerequisite contracts, strict full-task conjunctions, identity masks, fixed-$N$ assumptions.
* **Add:** Anonymous Dual-Duty local adapter environment, task-access ordinary-MARL baseline instrument, result metric parser.
* **Prohibited:** Module stacking, slot/graph/attention stacks, learned event time, reward shaping, and retired R53/R54 contract rescue.

### 9. Strongest ordinary-MARL objection
A direct active-set policy or F0 should easily solve the task without F1 because the exogenous opportunity gap (mean 10 steps) allows the system to observe the public duty state frequently. A reactive F0 agent, observing that a short job is unhandled and recognizing its own local features are suited for it, can independently commit to `SERVE_SHORT`. It can avoid collisions through learned implicit marginal probabilities and environmental stochasticity, without ever needing an explicit autoregressive prefix to coordinate perfectly.
