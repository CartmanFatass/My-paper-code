# Local HMASD navigation overlay

`runner/shared/` implements one parameter-shared policy and `SharedReplayBuffer`; its environment
runner batches all agents with each rollout thread. `runner/separated/` builds one policy, trainer,
and buffer per agent and loops over agents. Environment-specific `run`, `collect`, `insert`, and
`eval` methods are the concrete call sites. See `onpolicy/runner/shared/base_runner.py` and
`onpolicy/runner/separated/base_runner.py`. This is local additive navigation for the fixed SHA;
the source files are read-only and no upstream navigation was present here.
