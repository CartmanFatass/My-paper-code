# Hanabi environment navigation

`hanabi.py` is a turn-based environment behind the parallel dictionary API. `step_env` selects the
current player from `cur_player_idx` and `seat_order`, executes one action, and returns the same
terminal/reward to all agents; non-acting agents receive legal no-op handling. `get_legal_moves`
vmaps the legality calculation over agents and returns a fixed `num_moves` mask.

Performance reading: the action encoding is built in Python at construction time. Human-readable
belief formatting uses `itertools.product` and NumPy/Python conversions and is a host/rendering
path, not evidence of a compiled rollout kernel. Baselines can still `vmap` independent Hanabi
states, but each state advances one current player at a time.

RNG and dtype follow the concrete state and JAX key arguments; the API's agent dicts do not imply
simultaneous game turns. Preserve the declared agent/seat order and no-op convention when stacking
actions or interpreting throughput.
