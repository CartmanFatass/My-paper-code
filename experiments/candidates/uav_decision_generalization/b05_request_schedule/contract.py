"""Source-fixed B05 constants and stateless RNG addresses (no generators)."""
import numpy as np

HORIZON = 1200
CONTROL_PERIOD = 20
LAST_ARRIVAL_TICK = 940
SERVICE_TICKS = 20
TERMINAL_WEIGHT = 240
G_HORIZON = 240
MASTER_SEED = 109259999
TRAIN_WORLDS = tuple(tuple(range(109250000 + 1000 * fit,
                                 109250512 + 1000 * fit)) for fit in range(3))
MAIN_WORLDS = tuple(range(109253000, 109253032))
AUDIT_WORLDS = (109253900, 109253901, 109253902)
TORCH_INIT_SEEDS = (109254101, 109254102, 109254103)
RESULT_NODE = 'local_linux'
RUNTIME_VERSIONS = ('3.10.20', '1.26.3', '2.7.0+cpu')
RESET_BYTES = 404
REPORT_BYTES = 171
COMMAND_BYTES = 6
FEATURE_COUNT = 303
NATIVE_EVENT_NAMES = ('constructor_calls', 'reset_calls', 'native_step_calls',
                      'native_steps', 'dense_reward_entries', 'parent_reward_entries',
                      'registry_calls', 'physical_state_update_attempts',
                      'channel_state_update_attempts', 'link_update_attempts',
                      'routing_update_attempts', 'constructor_topology_restorations',
                      'public_clone_calls')


def frozen_contract():
    return {'object': 'B05_request_schedule', 'schema': 1,
            'node': RESULT_NODE, 'runtime_versions': list(RUNTIME_VERSIONS),
            'master': MASTER_SEED, 'horizon': HORIZON, 'period': CONTROL_PERIOD,
            'last_arrival_tick': LAST_ARRIVAL_TICK, 'service_ticks': SERVICE_TICKS,
            'terminal_weight': TERMINAL_WEIGHT, 'g_horizon': G_HORIZON,
            'r_horizon': 160, 'r_tapes': 4, 'deadline_seconds': 20,
            'training_worlds': [list(x) for x in TRAIN_WORLDS],
            'main_worlds': list(MAIN_WORLDS), 'audit_worlds': list(AUDIT_WORLDS),
            'torch_seeds': list(TORCH_INIT_SEEDS), 'rate_codes': [6, 3, 2, 1],
            'executor_dtype': 'float64', 'residual_dtype': 'float32',
            'g_dtype': 'float64', 'features': FEATURE_COUNT, 'parameters': 55553,
            'batch': 128, 'warmup': 256, 'target_period': 256, 'epsilon': .1,
            'discount': 1., 'learning_rate': .0003, 'gradient_cap': 10.,
            'cpu_limit_seconds': 180000, 'wall_limit_seconds': 259200,
            'gpu_seconds': 0, 'memory_floor_bytes': 8 * 1024**3,
            'disk_free_floor_bytes': 12 * 1024**3,
            'training_order': 'timed-current-command;offline-previous-update;native-macro',
            'initial_deployment': 'canonical G endpoint;separate offline neural audit',
            'worker_native_steps': 2049600, 'worker_missions': 1708,
            'worker_updates': 91392, 'worker_replay_rows': 11698176,
            'worker_r_model_steps_max': 4424000,
            'worker_g_candidate_ticks_max': 292844160,
            'worker_neural_rows_max': 70582176,
            'reader_native_physical_states': 2051308,
            'reader_neural_rows_max': 24480}


def rng_domain(name, *coordinates):
    """Return SeedSequence entropy, without consuming any stream.

    rates/actual_arrivals take world; R takes world, decision, tape;
    exploration/replay take fit. Geometry/native seeds remain the host's law.
    """
    domains = {"rates": (20, 1), "actual_arrivals": (21, 1),
               "R": (30, 3), "exploration": (10, 1), "replay": (11, 1)}
    if name not in domains:
        raise ValueError("unknown B05 RNG domain")
    domain, arity = domains[name]
    if len(coordinates) != arity or any(
            isinstance(x, (bool, np.bool_)) or not isinstance(x, (int, np.integer))
            or x < 0 for x in coordinates):
        raise ValueError("nonnegative integer domain coordinates required")
    if name in ("exploration", "replay") and coordinates[0] not in range(3):
        raise ValueError("fit must be 0, 1 or 2")
    if name == "R" and (coordinates[1] not in range(60)
                        or coordinates[2] not in range(4)):
        raise ValueError("R decision/tape outside fixed contract")
    return (MASTER_SEED, domain, *(int(x) for x in coordinates))
