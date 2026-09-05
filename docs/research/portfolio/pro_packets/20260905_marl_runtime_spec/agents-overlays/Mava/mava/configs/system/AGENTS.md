# `mava/configs/system/` navigation overlay

System YAML files define algorithm semantics and throughput arithmetic. PPO uses rollout length,
update batch, epochs, and minibatches; IQL/SAC add replay sequence or item buffer sizes and
sampling; Sable adds its policy configuration. The seed and all terminal/target-update settings
must be carried into any normalized run. YAML edits are semantic changes and require a new
evidence record.
