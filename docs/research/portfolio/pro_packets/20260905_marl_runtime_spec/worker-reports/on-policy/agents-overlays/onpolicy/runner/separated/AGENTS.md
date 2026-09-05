# Local HMASD navigation overlay

Start with `base_runner.py` for one policy/trainer/`SeparatedReplayBuffer` per agent. The SMAC and
MPE runners collect by iterating over `agent_id`; `base_runner.train` also iterates agents and
re-evaluates old/new action log probabilities around each update. This file is additive local
navigation for the fixed SHA; source remains read-only and no upstream file was present here.
