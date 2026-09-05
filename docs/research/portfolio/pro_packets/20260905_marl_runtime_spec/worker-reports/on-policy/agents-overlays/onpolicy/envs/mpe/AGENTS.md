# Local HMASD navigation overlay

`MPE_env.py` creates the scenario world and `environment.py` defines the multi-agent Gym contract,
per-agent observations/actions, shared observation space, rewards, dones, and reset behavior.
`runner/shared/mpe_runner.py` and `runner/separated/mpe_runner.py` consume these contracts. This
file is local additive navigation for the fixed SHA; do not change source for the survey.
