# `mava/configs/` navigation overlay

Hydra configuration is part of the runnable entry-point contract. Keep YAML source unchanged.

## Navigation and boundary

- `arch/anakin.yaml`, `arch/sebulba.yaml`: environment counts, evaluation counts, device ids,
  actor threads, and rollout queue size.
- `system/`: algorithm seeds, rollout/replay lengths, minibatches, epochs, learning rates,
  target updates, and replay ratios.
- `env/`: environment and scenario parameters.
- `logger/logger.yaml`: output sinks and checkpoint options.
- `default/`: Hydra composition for each runner.

Changing counts, seed, rollout length, minibatches, replay size, queue size, or device ids changes
the object or its throughput denominator. Any normalization spec must record those values rather
than assuming the defaults are portable to toy45min or UAV12h.


