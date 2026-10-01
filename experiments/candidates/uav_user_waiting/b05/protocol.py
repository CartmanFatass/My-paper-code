"""Frozen identities, serialization names and nonnumerical input utilities."""

import hashlib
import json
from pathlib import Path

OBJECT = 'UAV-USER-WAITING-B05'
SEED = 29426000
SEEDS = tuple(range(SEED, SEED + 64))
PROGRAMS = ('M', 'S', 'U')
LAWS = ('ORIGINAL', 'RR', 'LRS')
PACKAGES = tuple(f'{program}:{law}' for program in PROGRAMS for law in LAWS)
HORIZON, N, U, CAPACITY, MIN_SINR = 256, 5, 50, 10, 3.
T_CRITICAL = 1.998340542520741
ATOL = 1e-12
SOURCE_SHA = 'dd3b2577d407b57a3b76ea4ba95b6ead4349d0d4'
SUMMARY_SHA256 = '49754e61f38009681d5a842d320a1878bdd260518300a5391cc3c8678db47c47'
READING_SHA256 = '69787803a4de84555c534d9b7f21a23c290c7d4446bc874a2da6e49237289513'
B04_CANONICAL_RUN = Path('/home/wu/projects/HMASD/runs/uav_user_waiting/b04_service_floor_a01')
RADIO_PATH = 'envs/pettingzoo/uav_radio.py'
SOURCE_PATHS = (
    RADIO_PATH, 'envs/pettingzoo/uav_env.py', 'envs/pettingzoo/env_adapter.py',
    'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py',
    'experiments/candidates/uav_local_history/b01/controller.py',
    'experiments/candidates/uav_radio_activation/b01/study.py',
    'experiments/candidates/uav_registered_service/b01/history.py',
    'experiments/candidates/uav_user_waiting/b01/history.py',
    'experiments/candidates/uav_user_waiting/b02/protocol.py',
    'experiments/candidates/uav_user_waiting/b02/predictor.py',
    'experiments/candidates/uav_user_waiting/b02/scheduler.py',
    'experiments/candidates/uav_user_waiting/b02/study.py',
    'experiments/candidates/uav_user_waiting/b04/scheduler.py',
    'experiments/candidates/uav_user_waiting/b04/study.py',
)
GAP_COLUMNS = ('start', 'end', 'left_censored', 'right_censored',
               'capacity_denied_ticks', 'no_link_ticks')
NO_LINK_COLUMNS = ('start', 'end', 'left_censored', 'right_censored')
VECTOR_FIELDS = ('service_count', 'mean_age', 'max_gap', 'terminal_age',
                 'changed_grant_ticks', 'capacity_denied_ticks', 'no_link_ticks')
OUTCOME_METRICS = (
    'F_user', 'max_user_mean_age', 'A', 'age_sum', 'mean_age_square', 'age_square_sum',
    'F', 'J', 'return_sum', 'mean_served', 'mean_quality',
    'ever_served', 'never_served', 'max_unserved_gap', 'mean_user_max_unserved_gap', 'G',
    'max_closed_gap', 'max_left_censored_gap', 'max_right_censored_gap',
    'left_censored_gaps', 'right_censored_gaps', 'age_p95',
    'terminal_mean_age', 'terminal_max_age', 'service_p10', 'min_served',
    'zero_service_steps', 'longest_zero_service', 'changed_grant_user_ticks',
    'changed_grant_fleet_ticks', 'changed_grant_uav_ticks', 'capacity_denied_user_ticks',
    'no_link_user_ticks', 'capacity_choice_uav_ticks', 'exact_capacity_uav_ticks',
)
INHERITED_METRICS = ('mean_path_length_m', 'transmitter_on_ticks', 'mean_active_transmitters',
                     'mask_flips', 'deadline_misses', 'candidate_requests', 'candidate_plans',
                     'state_reductions', 'geometry_snapshots', 'scheduler_cpu_seconds',
                     'scheduler_wall_seconds', 'c_cpu_seconds', 'c_wall_seconds')
INHERITED_FIELDS = INHERITED_METRICS + (
    'xy_boundary_uav_steps', 'lower_altitude_uav_steps', 'fallback_decisions', 'fallback_uav_steps',
    'mean_visible_users', 'mean_visible_peers', 'empty_discovery_uav_steps', 'all_on_steps',
    'report_rounds', 'recurring_bytes', 'preinstalled_map_bytes', 'max_scheduler_wall_seconds',
    'prefix_ticks', 'proposal_command_edits', 'executed_block_edits', 'clipped_alias_edits',
    'selected_silent_to_active', 'virtual_c_calls', 'current_candidate_requests', 'current_state_reductions',
    'future_candidate_requests', 'future_state_reductions', 'complete_calculations', 'timely_decisions',
    'executed_command_changes', 'executed_mask_changes', 'executed_forecast_changes',
    'decision_counts', 'controller_counts', 'wall_seconds', 'cpu_seconds',
    'storage_wall_seconds', 'storage_cpu_seconds',
)
METRICS = OUTCOME_METRICS + INHERITED_METRICS
ZERO_COUNTS = ('native_steps', 'native_resets', 'environment_constructions', 'fits',
               'optimizer_updates', 'parameter_updates', 'model_calls', 'c_calls',
               'radio_sinr_queries', 'geometry_predictions', 'candidate_requests')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, allow_nan=False, separators=(',', ':'))
        stream.write('\n')
    temporary.replace(path)


def file_identity(path, counts=None):
    path = Path(path).resolve(strict=True)
    digest, size = hashlib.sha256(), 0
    if counts is not None:
        counts['hash_files'] += 1
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
            if counts is not None:
                counts['hash_bytes'] += len(block)
    return dict(path=str(path), bytes=size, sha256=digest.hexdigest())


def expected_counts():
    ticks = len(SEEDS) * len(PROGRAMS) * HORIZON
    return dict(source_traces=192, original_outcomes=192, fair_outcomes=384,
                source_ticks=ticks, fleet_allocations=3*ticks, uav_allocation_decisions=3*N*ticks,
                original_kernel_calls=ticks, rr_row_selections=N*ticks, lrs_row_selections=N*ticks,
                transition_reductions=3*ticks, user_age_updates=3*U*ticks,
                threshold_scans=2*ticks, threshold_entries=2*N*U*ticks,
                contact_values_retained=2*U*ticks, fair_contact_valid_user_ticks=2*U*ticks,
                **{key: 0 for key in ZERO_COUNTS})
