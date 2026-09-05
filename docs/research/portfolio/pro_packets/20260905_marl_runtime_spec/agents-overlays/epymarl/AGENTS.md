# EPyMARL local reference overlay

This is a local navigation overlay for the upstream `uoe-agents/epymarl` checkout. It is not an
upstream instruction file. The checkout is read as source evidence at the pinned commit
`cbc38c09588064eab978501d0f12c2cf58fa7fc2`; do not edit, install, train, benchmark, commit, or
push from this reference checkout. Preserve all upstream files, including `LICENSE` and `NOTICE`.

Navigation:

- `src/runners/` covers the episode and subprocess runners, `Pipe` IPC, and rollout assembly.
- `src/envs/` covers the `MultiAgentEnv` contract and Gymnasium, PettingZoo, VMAS, SMAC, SMACv2,
  and SMAClite adapters.
- `src/controllers/` covers MAC action selection, parameter sharing, no-sharing, and tensor batch
  shapes; `src/modules/agents/` contains the RNN implementations used by those MACs.
- `src/components/` covers `EpisodeBatch`, `ReplayBuffer`, transforms, and action selectors.
- `src/learners/` covers representative Q-learning and actor/policy-critic training loops,
  target updates, optimizer steps, and learner logging.

The report under `C:/Projects/ref-lib/reports/epymarl/` is the evidence index. Verify every claim
with `git show <sha>:<path>`, `rg -n`, and the fixed-SHA GitHub blob permalink recorded in the
report. The line numbers are source line numbers at the pinned checkout, not inferred from current
upstream `main`. No runtime result is implied by source inspection. `toy45min` and `UAV12h` are
engineering-investigation thresholds only; they do not make different tasks speed-comparable and
do not authorize reducing scientific requirements to obtain speed.

License identity recorded for this checkout: Apache License 2.0 (`LICENSE`), with the upstream
attribution list in `NOTICE` retained alongside the source.
