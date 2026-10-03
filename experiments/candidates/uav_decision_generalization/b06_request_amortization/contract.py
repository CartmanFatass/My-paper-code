"""The selected B06 purchase; constants and addresses perform no science."""
from experiments.candidates.uav_decision_generalization.b05_request_schedule.contract import (
    COMMAND_BYTES, CONTROL_PERIOD, FEATURE_COUNT, G_HORIZON, HORIZON,
    LAST_ARRIVAL_TICK, MASTER_SEED, NATIVE_EVENT_NAMES, REPORT_BYTES,
    RESET_BYTES, RESULT_NODE, RUNTIME_VERSIONS, SERVICE_TICKS,
    TERMINAL_WEIGHT, rng_domain as inherited_rng_domain,
)

OBJECT = 'B06_request_amortization'
MAIN_WORLDS = tuple(range(109255000, 109255032))
ARMS = ('G', 'R4', 'R1', 'B', 'S0', 'S1', 'S2')
TEACHER_WORLDS = tuple(range(109253000, 109253032)) + (109253900, 109253901, 109253902)
TORCH_INIT_SEEDS = (109255101, 109255102, 109255103)
EPOCHS, BATCH_SIZE, BANK_CONTEXTS = 64, 64, 2100
FIT_UPDATES, TOTAL_UPDATES = 2112, 6336
WORKER_TAG = 'b06_amortization_a01'
READER_TAG = 'b06_amortization_read_a01'
CPU_STOP_SECONDS, CPU_LIMIT_SECONDS = 9.5 * 3600, 10 * 3600
WALL_STOP_SECONDS, WALL_LIMIT_SECONDS = 23 * 3600, 24 * 3600
DISK_STOP_BYTES, DISK_LIMIT_BYTES = 7 * 1024**3, 8 * 1024**3
ENGINEERING_CPU_LIMIT_SECONDS = .5 * 3600
TEACHER_IDENTITIES = {
    'manifest': '3c3c7c84af0c0b55a4669e71bbad361d5b4e391e26bd237ee59a3f2aea639026',
    'config': 'e675836d1775dcbb414395109ca062b8a3bb8341d196a39eab80f87db643e668',
    'summary': 'd06794e1287e7fca7fd815ec77a4a1e17f6a133f87c42f023ccf50ca42605edd',
    'reader_summary': '8a0a24d9ec71fcfbd892e46729b61e98585a2fbba57ca0a5a4456610f9776612',
}


def rng_domain(name, *coordinates):
    if name == 'shuffle':
        if len(coordinates) != 1 or type(coordinates[0]) is not int or coordinates[0] not in range(3):
            raise ValueError('one literal B06 optimization replicate required')
        return (MASTER_SEED, 51, coordinates[0])
    if name not in ('rates', 'actual_arrivals', 'R'):
        raise ValueError('no other stochastic stream in the selected B06 purchase')
    return inherited_rng_domain(name, *coordinates)


def expected_roster():
    return [(world, 'main/' + arm)
            for index, world in enumerate(MAIN_WORLDS)
            for arm in ARMS[index % len(ARMS):] + ARMS[:index % len(ARMS)]]


def frozen_contract():
    return {
        'object': OBJECT, 'schema': 1, 'node': RESULT_NODE,
        'runtime_versions': list(RUNTIME_VERSIONS), 'master': MASTER_SEED,
        'horizon': HORIZON, 'period': CONTROL_PERIOD,
        'last_arrival_tick': LAST_ARRIVAL_TICK, 'service_ticks': SERVICE_TICKS,
        'terminal_weight': TERMINAL_WEIGHT, 'g_horizon': G_HORIZON,
        'r_horizon': 160, 'r_tapes': {'R4': [0, 1, 2, 3], 'R1': [0]},
        'deadline_seconds': 20, 'activation_delay_ticks': 20,
        'arms': list(ARMS), 'main_worlds': list(MAIN_WORLDS),
        'teacher_worlds': list(TEACHER_WORLDS), 'teacher_identities': dict(TEACHER_IDENTITIES),
        'teacher_contexts': BANK_CONTEXTS, 'teacher_action_labels': 8400,
        'teacher_collection_missions': 0, 'extra_audit_missions': 0,
        'teacher_order': 'world ascending;decision 0..59;action 0..3',
        'teacher_mean': 'ordered 4 float64 cohorts including alias multiplicity',
        'torch_seeds': list(TORCH_INIT_SEEDS), 'shuffle_domain': [MASTER_SEED, 51],
        'epochs': EPOCHS, 'batch': BATCH_SIZE, 'last_batch': 52,
        'fit_updates': FIT_UPDATES, 'worker_updates': TOTAL_UPDATES,
        'context_presentations': 403200, 'features': FEATURE_COUNT,
        'parameters': 55553, 'architecture': [303, 128, 128, 1],
        'executor_dtype': 'float64', 'residual_dtype': 'float32', 'g_dtype': 'float64',
        'loss_dtype': 'float64', 'learned_anchor_detached': False,
        'loss': 'mean(((G/1200+float64(f))_a-(G/1200+float64(f))_g-(Rbar_a-Rbar_g)/1200)^2)',
        'adam': {'lr': .0003, 'betas': [.9, .999], 'eps': 1e-8,
                 'weight_decay': 0., 'amsgrad': False, 'foreach': False,
                 'fused': False, 'maximize': False},
        'gradient_l2_cap': 10., 'torch_threads': 4, 'torch_interop_threads': 1,
        'constant_fit': 'fixed-order float64 G-anchor bordered5x5 LS;sum(b)=0',
        'constant_solve_calls': {'worker': 1, 'reader': 1},
        'scorer_deployment': 'cold persistent process per arm;reload only on deadline restart',
        'initial_deployment': 'canonical G;zero-head and full-bank offline certificate only',
        'worker_missions': 224, 'worker_native_steps': 268800,
        'worker_decisions': 13440, 'logical_task_bytes': 2507680,
        'worker_r_model_initials_max': 3840, 'worker_r_model_steps_max': 5201920,
        'worker_r_physical_cohorts_max': 8352, 'worker_r_logical_cohorts_max': 9600,
        'worker_r_clones_max': 33408, 'worker_r_uniforms_max': 222720,
        'worker_actual_uniforms': 43008, 'worker_g_queries_max': 271488,
        'worker_g_candidate_ticks_max': 246912000,
        'worker_neural_rows_max': 1686240, 'reader_neural_rows_max': 73440,
        'total_neural_rows_max': 1759680, 'reader_optimizer_updates': 0,
        'reader_native_physical_states': 269024, 'reader_total_physical_states_max': 5474784,
        'cpu_stop_seconds': CPU_STOP_SECONDS, 'cpu_limit_seconds': CPU_LIMIT_SECONDS,
        'wall_stop_seconds': WALL_STOP_SECONDS, 'wall_limit_seconds': WALL_LIMIT_SECONDS,
        'disk_stop_bytes': DISK_STOP_BYTES, 'disk_limit_bytes': DISK_LIMIT_BYTES,
        'engineering_cpu_limit_seconds': ENGINEERING_CPU_LIMIT_SECONDS,
        'memory_floor_bytes': 8 * 1024**3, 'disk_free_floor_bytes': 12 * 1024**3,
        'gpu_seconds': 0, 'worker_tag': WORKER_TAG, 'reader_tag': READER_TAG,
        'technical_failure': 'first formal/admission/worker/reader failure stops;no retry',
    }
