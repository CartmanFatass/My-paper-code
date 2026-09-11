# Runner navigation overlay

Read `parallel_runner.py` first for process creation, one `Pipe` pair per environment, action and
transition message flow, termination handling, and `env_worker`; read `episode_runner.py` for the
single-environment serial baseline. Then follow `src/run.py` for runner setup, replay insertion,
learner calls, periodic evaluation, checkpointing, and close. Use the fixed commit SHA and report
permalinks; source lines are observations, not benchmark measurements. Preserve upstream files.
