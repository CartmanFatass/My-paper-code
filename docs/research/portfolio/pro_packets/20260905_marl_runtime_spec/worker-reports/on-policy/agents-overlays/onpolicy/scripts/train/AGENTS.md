# Local HMASD navigation overlay

`train_smac.py` is the shared/separated SMAC entry point; `train_mpe.py` covers MPE, and the
Football/Hanabi scripts adapt their environment-specific arguments. `config.py` holds defaults
for rollout threads, episode length, PPO epochs/minibatches, save/log/eval intervals, policy
sharing, and recurrent mode. This additive overlay is for the fixed SHA; no source edits are in
scope.
