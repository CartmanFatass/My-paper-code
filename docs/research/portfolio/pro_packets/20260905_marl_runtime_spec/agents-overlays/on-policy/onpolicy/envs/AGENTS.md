# Local HMASD navigation overlay

`env_wrappers.py` provides in-process dummy vectors and Pipe-backed subprocess vectors. MPE and
Football use `SubprocVecEnv`/`DummyVecEnv`; SMAC uses `ShareSubprocVecEnv`/`ShareDummyVecEnv` to
carry local observations, centralized observations, rewards, dones, infos, and available actions;
Hanabi uses the choose-reset variants. Environment adapters below this directory define the
per-agent spaces and step/reset contracts. Source is read-only; this is local additive navigation.
