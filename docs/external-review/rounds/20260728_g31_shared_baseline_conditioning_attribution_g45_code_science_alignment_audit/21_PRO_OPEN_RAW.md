AUDIT_DISPOSITION=MISMATCH

Frozen assertion: every PPO pass must independently prove that the immediate baseline output is live, the successor baseline output is live, and the shared baseline trunk is live under the union of the two baseline losses.

Conflicting code path: G45 _gradient_probe computes gradients over the complete credit_baselines.parameters() tuple and delegates their evidence to g43.registered_gradient_evidence. That inherited validator reduces each baseline loss to one global norm across the entire baseline module and records only baseline_outputs.immediate and baseline_outputs.successor; it has no parameter-group evidence for either output row or the shared trunk.

The accepted baseline is a shared Linear → Tanh → Linear(2) module. Consequently, a pass with exact-zero gradients on the shared first-layer trunk but a live final-layer output row or bias still has a live whole-module norm and passes the current gate. The focused test zeros the entire baseline-gradient tuple; it does not exercise a dead-trunk/live-output counterexample. A conclusion-bearing checkpoint can therefore pass without proving the frozen shared-trunk learning path.

Smallest in-contract correction: add named baseline-gradient evidence per arm and PPO pass that separately binds:

immediate_output_row_gradient_norm > 1e-12
successor_output_row_gradient_norm > 1e-12
shared_trunk_union_gradient_norm > 1e-12
all_group_gradients_finite=true

The shared-trunk union must be reconstructed from the immediate- and successor-loss gradients of credit_baselines.0.{weight,bias}; output evidence must use the corresponding rows of credit_baselines.2.{weight,bias}. Serialize and revalidate these groups in update, conclusion, checkpoint, and artifact-reload evidence. Add focused guards for dead-trunk/live-output and live-trunk/dead-required-output cases. No source, residual law, optimizer, seed, threshold, evidence volume, confidence procedure, or first-match branch requires modification.
