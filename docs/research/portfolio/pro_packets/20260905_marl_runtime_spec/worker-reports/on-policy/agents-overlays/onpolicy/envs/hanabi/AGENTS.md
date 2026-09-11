# Local HMASD navigation overlay

`Hanabi_Env.py` is the turn-based adapter; `ChooseSubprocVecEnv` and `ChooseDummyVecEnv` pass a
per-environment reset choice and return local/shared observations plus available actions. The
forward runner and choose insert path are specialized for this contract. This is additive local
navigation for the fixed SHA; no upstream file was overwritten.
