# HMASD Implementation Review Principles

- The frozen implementation plan is the executable contract; project history is
  not an invitation to redesign it.
- Treat probability, likelihood replay, masks, recurrent state, detach, credit,
  clocks, RNG and checkpoint/resume as semantic correctness, not style.
- Demand direct focused evidence for the corruption risk the change introduces.
- Inspect performance structure as code quality: batch independent inference,
  pack rollout data once, avoid scalar CUDA synchronization, and avoid repeated
  serialization or environment reconstruction inside hot loops.
- Backward compatibility and inactive fallbacks are not virtues in this active
  research line. Flag superseded executable paths that should have been removed.
- Separate defects from residual experimental risk. Do not require formal
  training merely to approve a code package unless the frozen plan explicitly
  made it a focused check.
