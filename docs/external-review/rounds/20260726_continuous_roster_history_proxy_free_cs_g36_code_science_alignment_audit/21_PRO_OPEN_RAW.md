AUDIT_DISPOSITION=MISMATCH

Frozen assertion: active actor coordinates 6:10 must be replaced without the actual lifecycle-age, previous-action, or actor-time values being validated or copied before overwrite; all registered read counters must truthfully remain zero. This is necessary for the positive branch to support bounded actor-sensor substitution rather than merely numerical insensitivity after the real sensors have already been acquired.

Conflicting code path: evaluate_g36_history_proxy first executes:

Python
Run
observations = np.stack([view.observations for view in views])

which materializes and copies all ten actor coordinates. In the inherited source, active coordinates 6:10 already contain the actual lifecycle age, two previous actions, and normalized physical time. Only after that full-width copy does apply_g36_actor_history_proxy_transform overwrite them. The evaluator nevertheless returns actual_age_read_count=0, actual_previous_action_read_count=0, and actual_actor_time_read_count=0.

The focused poisoned-coordinate test exercises the transform in isolation, after a full observation tensor has already been supplied; it does not exercise or exclude the preceding full-width np.stack in the conclusion-bearing evaluator.

Smallest in-contract correction: construct the actor input buffer without ever materializing active source coordinates 6:10: allocate a fresh zeroed ten-coordinate tensor, copy only view.observations[:, :6], and write the donor bundles directly into active rows 6:10. Keep the critic stack separate and unchanged. The zero-read counters must be bound to that no-read construction path rather than returned unconditionally. Add one focused end-to-end evaluator check that fails if any full-width source observation is copied or inspected before substitution. This changes no donor law, proxy tape, checkpoint, source, cell inventory, action stream, estimand, threshold, confidence procedure, evidence volume, or first-match branch.
