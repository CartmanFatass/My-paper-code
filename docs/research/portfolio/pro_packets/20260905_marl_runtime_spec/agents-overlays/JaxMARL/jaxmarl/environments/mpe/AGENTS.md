# MPE environment navigation

`simple.py` defines the Flax `State` (`p_pos[num_entities,2]`, `p_vel[num_entities,2]`,
`c[num_agents,dim_c]`, plus base `done`/`step`) and the JIT `reset`/`step_env` path. Scenario
specializations such as `simple_spread.py` define observation and reward functions with inner
`vmap` over agent indices.

Performance reading: actions are stacked in declared `self.agents` order and decoded by a vmapped
function. The physical interaction kernel uses nested `vmap` over entity pairs; collision-force
work and intermediate matrices grow quadratically in `num_entities`. `SimpleSpreadMPE.get_obs`
also computes landmark and other-agent features for every agent. The outer batch axis comes from a
baseline `vmap`, not from the environment state itself.

RNG is split for world noise and communication noise, then split per agent. Defaults are JAX arrays
with explicit shapes; discrete actions use the local `Discrete` space and are cast to its dtype.
Auto-reset is inherited from `MultiAgentEnv.step`, so terminal transitions still execute the
selection path. There is no timing result in this overlay.
