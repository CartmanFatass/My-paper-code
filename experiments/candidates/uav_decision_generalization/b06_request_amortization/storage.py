"""New frozen-deployment records, reusing B05's unchanged physical schemas."""
import numpy as np

from experiments.candidates.uav_decision_generalization.b05_request_schedule.storage import (
    STATE_DTYPE, G_DTYPE, R_SHAPES, R_STATS, RolloutTrace, put_state, put_g, write_npz,
)

MISSION_SHAPES = {
    'users': ((50, 2), 'int32'), 'rates': ((4,), 'uint8'), 'pairs': ((3, 2), 'uint8'),
    'initial_slots': ((6,), 'uint8'), 'arrival_draws': ((48, 4), 'float64'),
    'arrival_tape': ((48, 4), 'bool'), 'states': ((1201,), STATE_DTYPE),
    'raw_actions': ((1200, 6, 3), 'float64'),
    'executed_actions': ((1200, 6, 3), 'float64'), 'arrivals': ((1200, 4), 'bool'),
    'tick_cost': ((1200,), 'uint16'), 'reports': ((60,), G_DTYPE),
    'features': ((60, 4, 303), 'float32'), 'commands': ((60, 6), 'uint8'),
    'action': ((60,), 'uint8'), 'g_action': ((60,), 'int8'),
    'greedy_action': ((60,), 'int8'), 'total_q': ((60, 4), 'float64'),
    'residual': ((60, 4), 'float32'), 'nn_complete': ((60,), 'bool'),
    'score_complete': ((60,), 'bool'), 'macro_cost': ((60,), 'uint32'),
}


def new_mission_arrays():
    result = {name: np.zeros(shape, dtype=dtype) for name, (shape, dtype) in MISSION_SHAPES.items()}
    result['g_action'][:] = -1
    result['greedy_action'][:] = -1
    return result
