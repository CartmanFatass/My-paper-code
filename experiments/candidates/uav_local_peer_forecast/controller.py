"""Local two-frame motion; no evaluator state or other actor inputs."""
import numpy as np

from experiments.candidates.uav_local_history.b01.controller import (
    LocalController, COMMANDS, BOUNDS_LOW, BOUNDS_HIGH, NOISE, _parse, _power,
)


def associate(current, previous):
    """Mutually unique component gates; current row -> previous row, or -1."""
    gate = np.all(np.abs(current[:, None] - previous[None]) <= 30.001, axis=-1)
    matches = np.full(len(current), -1, dtype=np.int64)
    for i in range(len(current)):
        indices = np.flatnonzero(gate[i])
        if len(indices) == 1 and gate[:, indices[0]].sum() == 1:
            matches[i] = indices[0]
    delta = np.zeros_like(current)
    valid = matches >= 0
    delta[valid] = current[valid] - previous[matches[valid]]
    delta[np.abs(delta) < .001] = 0.
    return matches, np.clip(delta, -30., 30.), gate.sum(axis=1)


class MotionController(LocalController):
    """C's decision with only qualifying moving-peer future powers replaced."""
    def __init__(self, arm):
        if arm not in ('V', 'R'):
            raise ValueError('motion arm must be V or R')
        self.arm = arm
        super().__init__(history=False)

    def reset(self):
        super().reset()
        self._previous_peers = np.empty((0, 3))
        self._clock = -1
        self.matches = np.empty(0, dtype=np.int64)
        self.delta = np.empty((0, 3))
        self.gate_counts = np.empty(0, dtype=np.int64)
        self.counters.update(adjacent_updates=0, pair_gates=0, matched_rows=0,
                             moving_rows=0, moving_peer_ticks=0, moving_link_evaluations=0)

    def act(self, obs_row, t):
        row = np.asarray(obs_row)
        if (isinstance(t, bool) or not isinstance(t, (int, np.integer))
                or t != self._clock + 1 or t not in range(256)
                or row.shape != (104,) or not np.isfinite(row).all()
                or float(row[103]) != t / 256):
            raise ValueError('expected consecutive integer clock and finite local row')
        _, _, _, peers = _parse(row)
        self.matches, self.delta, self.gate_counts = associate(peers, self._previous_peers)
        if t:
            self.counters['adjacent_updates'] += 1
            self.counters['pair_gates'] += len(peers) * len(self._previous_peers)
        self.counters['matched_rows'] += int((self.matches >= 0).sum())
        self.counters['moving_rows'] += int(np.any(self.delta != 0, axis=1).sum())
        self._clock = int(t)
        self._previous_peers = peers.copy()
        command, diagnostic = super().act(row.copy(), t)
        diagnostic.update(matches=self.matches.copy(), delta=self.delta.copy(),
                          gate_counts=self.gate_counts.copy())
        return command, diagnostic

    def _decide(self, own, sinr_observed, peers, observed_indices):
        moving = np.any(self.delta != 0, axis=1)
        n, p, m = len(self._points), len(peers), int(moving.sum())
        # Calling C itself preserves exact inactive arithmetic and sweep mutation.
        if not n or not m:
            result = super()._decide(own, sinr_observed, peers, observed_indices)
            self.counters['link_evaluations'] += self.counters['moving_link_evaluations']
            return result
        points = self._points
        trajectory = self._trajectories(own)
        self.counters['decisions'] += 1
        self.counters['trajectories'] += 27
        self.counters['model_ticks'] += 108
        self.counters['objective_reductions'] += 108
        self.counters['candidate_link_evaluations'] += 108 * n
        self.counters['setup_link_evaluations'] += (1 + p) * n
        self.counters['moving_peer_ticks'] += 4 * m
        self.counters['moving_link_evaluations'] += 4 * m * n
        present = _power(np.concatenate((own[None], peers)), points)
        peer_total = np.sum(present[1:], axis=0)
        unknown = np.zeros(n)
        if p < 4:
            unknown = np.maximum(present[0] / (10. ** (sinr_observed / 10.))
                                 - peer_total - NOISE, 0.)
        modeled = 10. * np.log10(present[0] / (peer_total + unknown + NOISE))
        self.counters['calibration_discrepancy_rows'] += int(
            np.count_nonzero(np.abs(modeled - sinr_observed) > 1e-4))
        # Stationary columns retain present powers, including decoded boundary roundoff.
        future = np.broadcast_to(present[None, 1:], (4, p, n)).copy()
        locations = peers[moving].copy()
        displacement = self.delta[moving] * (1 if self.arm == 'V' else -1)
        for lead in range(4):
            locations = np.clip(locations + displacement, BOUNDS_LOW, BOUNDS_HIGH)
            future[lead, moving] = _power(locations, points)
        powers = np.concatenate((_power(trajectory, points)[:, :, None],
                                 np.broadcast_to(future, (27, 4, p, n))), axis=2)
        denominator = np.sum(powers, axis=2, keepdims=True) - powers + unknown + NOISE
        sinr = 10. * np.log10(powers / denominator)
        scores, served = self._score(sinr, np.ones(n, dtype=bool))
        fallback = bool(np.all(served == 0.))
        choice = (self._sweep_choice(own, trajectory[:, -1], mutate=True)
                  if fallback else int(np.argmax(scores)))
        self.counters['fallback_decisions'] += int(fallback)
        self.counters['link_evaluations'] = (self.counters['candidate_link_evaluations']
                                            + self.counters['setup_link_evaluations']
                                            + self.counters['moving_link_evaluations'])
        self._command = COMMANDS[choice].copy()
        self._plan.update(fallback=fallback, selected_index=choice,
                          predicted_J=float(scores[choice]), predicted_service=float(served[choice]))
        return scores, served, None, None
