# `mava/wrappers/` navigation overlay

Wrappers define the environment and metric contracts consumed by every runner.

## Navigation and boundary

- `jumanji.py`: per-agent observation/global-state conversion and reward aggregation.
- `jaxmarl.py`: dictionary-to-agent-axis batching, key-carrying state, masks, discounts.
- `gym.py`: Gymnasium `AsyncVectorEnv` adapter, CPU batch layout, and `real_next_obs`.
- `auto_reset_wrapper.py`: terminal observation retention and key-derived reset.
- `episode_metrics.py`: running return/length and terminal-step extraction.

The canonical observation starts with agent axis `N`; vector adapters add environment axis `B`.
Masks, rewards, discounts, done/terminal distinction, auto-reset behavior, and metric extras are
semantic boundaries. Do not infer interchangeable JAX/CPU environment behavior from matching
array shapes alone.
