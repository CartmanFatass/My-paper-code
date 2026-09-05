# Local HMASD navigation overlay

Start with `base_runner.py` for policy/trainer/buffer construction, return computation, and train
handoff. `smac_runner.py` is the clearest MAPPO rollout path; `mpe_runner.py`,
`football_runner.py`, and `hanabi_runner_forward.py` adapt the same loop to their environment
contracts. Shared collection concatenates `[rollout_threads, agents, ...]` into one policy batch
per environment step, then converts outputs back to NumPy. Source is read-only; this local file
only indexes the fixed upstream snapshot.
