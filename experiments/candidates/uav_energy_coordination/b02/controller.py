"""Read-only telemetry around the two frozen ordinary control programs."""

from __future__ import annotations

import hashlib
from pathlib import Path
import time

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldController
from experiments.candidates.energy_relay_availability.b05.runner import _decision_arrays as _transit_arrays
from experiments.candidates.uav_energy_coordination.b01.controller import AnalyticalController
from experiments.candidates.uav_energy_coordination.b01.runner import _costs, _decisions


ROOT = Path(__file__).resolve().parents[4]
FROZEN_SHA256 = {
    'experiments/candidates/uav_energy_coordination/b01/controller.py':
        '49a7cb8c21115eabfd8bbdc62cf2eb141f72b9ceb7a5fafb34b9cd5761b8a70c',
    'experiments/candidates/uav_energy_coordination/b01/itinerary.py':
        '0afd87c74ceeff2b4558b6a96e79636090a7b27e0f71898aedd044e2523f774b',
    'experiments/candidates/energy_relay_availability/b04/transit_hold.py':
        '1e56e68759f7992d2da39e5f27cc1d71a516f580f0616cc2c0240e15ce776791',
    'experiments/candidates/energy_relay_benchmark/b01/evaluation.py':
        '15391e2eafff0876dd0bfa94a0d8f9f96558c76254e8d73cb8e55426735eccd7',
    'experiments/candidates/energy_relay_benchmark/b01/heuristic.py':
        'f82bbcc1d6586ae41acbb720b225b294c3dff812246e88f15f699b2d9146351e',
    'experiments/candidates/energy_relay_benchmark/b01/feedback.py':
        '0cb8cc14d7d63ea6dd6bbc84c830e01c06837507acd70b8fd29ae6411a6c13d2',
    'experiments/candidates/energy_relay_benchmark/b01/observation.py':
        'baa416c9067504fdeb2656b376768ed06c3febe440c358c92c7281922791536f',
}
COST_KEYS = (
    'score_requests', 'model_evaluations', 'service_snapshots', 'event_count',
    'phase_count', 'analytic_planner_wall_seconds', 'controller_wall_seconds',
    'decision_tick_wall_seconds', 'p_shared_baseline_snapshots',
    'p_projected_positions', 'decision_clocks', 'central_input_calls',
    'primitive_forecast_steps', 'controller_ticks',
)


def source_records():
    """Bind direct program dependencies without requiring Git on the worker path."""
    actual = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in FROZEN_SHA256}
    if actual != FROZEN_SHA256:
        changed = [name for name in actual if actual[name] != FROZEN_SHA256[name]]
        raise ValueError(f'frozen I/P source differs: {changed}')
    return {
        'I_source': 'e663b53c7ea3f52983365ed9c3ce044bc4ccf699',
        'P_source': '025350669bc5e8ab99fc71954f749ae47a6853e9',
        'P_B05_reuse_source': '754d5d34d905a81b58b78e69ae85b8a07cb19aad',
        'sha256': actual,
    }


class FrozenController:
    """Forward the original policy exactly; measurements never enter a proposal."""

    def __init__(self, arm, env, config):
        if arm not in ('I', 'P'):
            raise ValueError('B02 permits only frozen I and P')
        self.arm = arm
        self.base = (AnalyticalController('I', env, config) if arm == 'I'
                     else TransitHoldController(env))
        self._reset_telemetry()

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, 'base'), name)

    def _reset_telemetry(self):
        self._controller_ticks = 0
        self._controller_wall = 0.0
        self._decision_steps = []
        self._decision_wall = []

    def _records(self):
        return (self.base.decision_records if self.arm == 'I'
                else self.base.heuristic.decision_records)

    def reset(self):
        self.base.reset()
        self._reset_telemetry()

    def propose(self, observations, state, step, previous_done, modes):
        count = len(self._records())
        self._controller_ticks += 1
        started = time.monotonic()
        try:
            return self.base.propose(observations, state, step, previous_done, modes)
        finally:
            elapsed = time.monotonic() - started
            self._controller_wall += elapsed
            if len(self._records()) > count:
                self._decision_steps.append(int(step))
                self._decision_wall.append(elapsed)

    def decision_arrays(self):
        if self.arm == 'I':
            arrays = self.base.decision_arrays()
        else:
            original = _transit_arrays(self.base)
            if any(not name.startswith('planner_') for name in original):
                raise ValueError('unexpected frozen P decision field')
            arrays = {'transit_' + name.removeprefix('planner_'): value
                      for name, value in original.items()}
        return {
            **arrays,
            'telemetry_step': np.asarray(self._decision_steps, dtype=np.int64),
            'telemetry_decision_tick_wall_seconds': np.asarray(self._decision_wall, dtype=np.float64),
        }

    @property
    def costs(self):
        result = {key: 0 for key in COST_KEYS}
        records = self._records()
        if self.arm == 'I':
            known = self.base.costs
            for key in ('score_requests', 'model_evaluations', 'service_snapshots',
                        'event_count', 'phase_count'):
                result[key] = known[key]
            result['analytic_planner_wall_seconds'] = known['planner_wall_seconds']
        else:
            active = [record for record in records if record['fallback'] is None]
            candidates = sum(record['candidate_count'] for record in active)
            result.update(score_requests=candidates, model_evaluations=candidates,
                          service_snapshots=self.base.heuristic.service_snapshot_calls,
                          p_shared_baseline_snapshots=len(active),
                          p_projected_positions=2 * candidates)
        result.update(controller_wall_seconds=self._controller_wall,
                      decision_tick_wall_seconds=sum(self._decision_wall),
                      decision_clocks=len(records),
                      central_input_calls=len(self.base.plan_input_steps),
                      controller_ticks=self._controller_ticks)
        return result

    def validate_trace(self, length):
        arrays = self.decision_arrays()
        if self.arm == 'I':
            original = _decisions(self.base, 'I', length)
            _costs(self.base, 'I', original)
            clocks = original['planner_step']
        else:
            records = self._records()
            clocks = arrays['transit_step']
            expected = np.arange(0, length, 10)
            if len(clocks) > 300 or not np.array_equal(clocks, expected):
                raise ValueError('frozen P replanning clock differs')
            if not np.array_equal(self.base.plan_input_steps, clocks):
                raise ValueError('frozen P central input clock differs')
            for record in records:
                n = record['candidate_count']
                if not 1 <= n <= 9:
                    raise ValueError('frozen P candidate bound differs')
                expected_calls = 0 if record['fallback'] is not None else 1 + 2 * n
                if record['snapshot_calls'] != expected_calls:
                    raise ValueError('frozen P q0-inclusive snapshot count differs')
            if sum(record['snapshot_calls'] for record in records) != self.base.heuristic.service_snapshot_calls:
                raise ValueError('frozen P live and per-clock snapshot counters differ')
        if not np.array_equal(arrays['telemetry_step'], clocks):
            raise ValueError('decision timing records differ from original policy clocks')
        if self._controller_ticks != length:
            raise ValueError('controller calls differ from completed native steps')
        costs = self.costs
        if set(costs) != set(COST_KEYS) or any(not np.isfinite(value) or value < 0
                                             for value in costs.values()):
            raise ValueError('invalid B02 cost counters')
        if any(np.asarray(value).dtype.kind == 'O' for value in arrays.values()):
            raise ValueError('object-valued B02 decision arrays')
        return arrays

    def close(self):
        close = getattr(self.base, 'close', None)
        if close is not None:
            close()
