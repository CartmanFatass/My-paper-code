"""Example only: continuing task with external truncation and episode reset.

Inputs are bool tensors. Bootstrap must use the true final observation, not
an auto-reset observation. A task-defined finite horizon is termination here.
This example neither builds targets nor implements a recurrent/GAE buffer.
"""


def continuing_task_masks(terminated, truncated):
    bootstrap = ~terminated
    connect_trace = ~(terminated | truncated)
    return bootstrap, connect_trace
