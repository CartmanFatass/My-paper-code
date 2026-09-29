"""Observation-only local radio motion rule for S1 B01."""

from itertools import product

import numpy as np


COMMANDS = np.array(sorted(product((-1, 0, 1), repeat=3),
                           key=lambda a: (sum(x * x for x in a), a)), dtype=np.float32)
WAYPOINTS = np.array(((100, 100), (900, 100), (900, 300), (100, 300),
                      (100, 500), (900, 500), (900, 700), (100, 700),
                      (100, 900), (900, 900)), dtype=np.float64)
GRID = np.array(list(product((np.arange(8) + 0.5) * 125.0, repeat=2)), dtype=np.float64)
NOISE = 10.0 ** (-80.0 / 10.0)
THRESHOLD = 3.0
SINR_LINEAR = 10.0 ** (THRESHOLD / 10.0)
BOUNDS_LOW = np.array((0.0, 0.0, 50.0))
BOUNDS_HIGH = np.array((1000.0, 1000.0, 150.0))


def _power(stations, users):
    """Free-space received power in mW, with broadcast station/user axes."""
    delta = stations[..., None, :2] - users[..., :2]
    squared = np.sum(delta * delta, axis=-1) + stations[..., None, 2] ** 2
    distance = np.sqrt(np.maximum(squared, 1e-12))
    loss = 20.0 * np.log10(distance) + 20.0 * np.log10(4.0 * np.pi / 0.15)
    return 10.0 ** ((23.0 - loss) / 10.0)


def _parse(row):
    obs = np.asarray(row, dtype=np.float32)
    if obs.shape != (104,):
        raise ValueError("local observation must have shape (104,)")
    own = np.array((float(obs[0]) * 1000.0, float(obs[1]) * 1000.0,
                    50.0 + float(obs[2]) * 100.0))
    users = obs[3:63].reshape(20, 3)
    valid_users = users[:, 2] > 0.0
    xy = own[:2] + users[valid_users, :2].astype(np.float64) * 1000.0
    sinr = users[valid_users, 2].astype(np.float64) * 50.0 - 10.0
    peers = obs[63:103].reshape(10, 4)
    valid_peers = peers[:, 3] > 0.0
    peer_xyz = own + peers[valid_peers, :3].astype(np.float64) * (1000.0, 1000.0, 100.0)
    return own, xy, sinr, peer_xyz


class LocalController:
    def __init__(self, history: bool):
        self.history = bool(history)
        self.reset()

    def reset(self):
        self._points = np.empty((0, 2), dtype=np.float64)
        self._last_seen = np.empty(0, dtype=np.int64)
        self._insert_order = np.empty(0, dtype=np.int64)
        self._current_mask = np.empty(0, dtype=bool)
        self._next_insert = 0
        self._nav_index = None
        self._command = np.zeros(3, dtype=np.float32)
        self._plan = dict(fallback=False, selected_index=-1, shadow_current_index=-1,
                          shadow_current_fallback=False, predicted_J=0.0,
                          predicted_service=0.0, shadow_current_action=np.zeros(3, dtype=np.float32),
                          shadow_command_disagreement=False,
                          shadow_executed_disagreement=False,
                          max_absent_current_sinr_db=float('nan'))
        self.counters = dict(ingests=0, decisions=0, trajectories=0, model_ticks=0,
                             candidate_link_evaluations=0, setup_link_evaluations=0,
                             link_evaluations=0, objective_reductions=0,
                             shadow_objective_reductions=0, shadow_decisions=0,
                             cache_matches=0, cache_inserts=0, cache_evicts=0,
                             fallback_decisions=0, grid_power_evaluations=0,
                             calibration_discrepancy_rows=0,
                             censor_discrepancy_rows=0,
                             censor_prior_conflicts=0)

    @property
    def points(self):
        return self._points.copy()

    @property
    def current_points(self):
        return self._points[self._current_mask].copy()

    @property
    def cache_points(self):
        return self._points.copy() if self.history else np.empty((0, 2))

    @property
    def last_seen(self):
        return self._last_seen.copy()

    @property
    def current_mask(self):
        return self._current_mask.copy()

    def _ingest(self, xy, t):
        matches = inserts = evicts = 0
        if not self.history:
            self._points = xy.copy()
            self._last_seen = np.full(len(xy), t, dtype=np.int64)
            self._current_mask = np.ones(len(xy), dtype=bool)
            return matches, inserts, evicts, np.arange(len(xy))
        self._current_mask[:] = False
        observed_indices = []
        for point in xy:
            distance = np.linalg.norm(self._points - point, axis=1)
            nearest = int(np.argmin(distance)) if len(distance) else -1
            if nearest >= 0 and distance[nearest] <= 0.01:
                self._points[nearest] = point
                self._last_seen[nearest] = t
                self._current_mask[nearest] = True
                matches += 1
                observed_indices.append(nearest)
                continue
            if len(self._points) == 64:
                victim = min(range(64), key=lambda i: (self._last_seen[i], self._insert_order[i]))
                self._points[victim] = point
                self._last_seen[victim] = t
                self._insert_order[victim] = self._next_insert
                self._current_mask[victim] = True
                evicts += 1
                observed_indices.append(victim)
            else:
                self._points = np.vstack((self._points, point[None, :]))
                self._last_seen = np.append(self._last_seen, t)
                self._insert_order = np.append(self._insert_order, self._next_insert)
                self._current_mask = np.append(self._current_mask, True)
                inserts += 1
                observed_indices.append(len(self._points) - 1)
            self._next_insert += 1
        self.counters['cache_matches'] += matches
        self.counters['cache_inserts'] += inserts
        self.counters['cache_evicts'] += evicts
        return matches, inserts, evicts, np.asarray(observed_indices, dtype=np.int64)

    @staticmethod
    def _trajectories(own):
        positions = np.broadcast_to(own, (27, 3)).copy()
        trajectory = np.empty((27, 4, 3), dtype=np.float64)
        for step in range(4):
            positions = np.clip(positions + COMMANDS * 30.0, BOUNDS_LOW, BOUNDS_HIGH)
            trajectory[:, step, :] = positions
        return trajectory

    def _sweep_choice(self, own, endpoints, *, mutate):
        index = self._nav_index
        if index is None:
            index = int(np.argmin(np.sum((WAYPOINTS - own[:2]) ** 2, axis=1)))
        if np.linalg.norm(WAYPOINTS[index] - own[:2]) <= 60.0:
            index = (index + 1) % len(WAYPOINTS)
        target = np.r_[WAYPOINTS[index], 50.0]
        choice = int(np.argmin(np.sum((endpoints - target) ** 2, axis=1)))
        if mutate:
            self._nav_index = index
        return choice

    def _score(self, sinr, subset):
        eligible = (sinr[:, :, :, subset] >= THRESHOLD)
        selected = np.zeros_like(eligible)
        values = sinr[:, :, :, subset]
        for tx in range(values.shape[2]):
            order = np.argsort(-values[:, :, tx, :], axis=-1, kind='stable')
            top = order[:, :, :10]
            np.put_along_axis(selected[:, :, tx, :], top,
                              np.take_along_axis(eligible[:, :, tx, :], top, axis=-1), axis=-1)
        served = np.sum(selected, axis=(-1, -2))
        quality = np.sum(np.where(selected, np.clip((values - 3.0) / 30.0, 0.0, 1.0), 0.0),
                         axis=(-1, -2)) / np.maximum(served, 1)
        j = 0.7 * served / 50.0 + 0.3 * quality
        return np.mean(j, axis=1), np.mean(served, axis=1)

    def _decide(self, own, sinr_observed, peers, observed_indices):
        points = self._points
        current = self._current_mask
        n = len(points)
        p = len(peers)
        trajectory = self._trajectories(own)
        self.counters['decisions'] += 1
        self.counters['trajectories'] += 27
        self.counters['model_ticks'] += 108
        self.counters['objective_reductions'] += 108
        self.counters['candidate_link_evaluations'] += 108 * n
        self.counters['setup_link_evaluations'] += (1 + p) * n
        max_absent_current_sinr_db = float('nan')
        if n:
            stations = np.concatenate((own[None, :], peers), axis=0)
            present_power = _power(stations, points)
            own_power = present_power[0]
            peer_power = np.sum(present_power[1:], axis=0)
            unknown = np.zeros(n)
            if np.any(current) and p < 4:
                gamma = 10.0 ** (sinr_observed / 10.0)
                unknown[observed_indices] = np.maximum(
                    own_power[observed_indices] / gamma - peer_power[observed_indices] - NOISE, 0.0)
            if np.any(current):
                modeled_db = 10.0 * np.log10(
                    own_power[observed_indices] /
                    (peer_power[observed_indices] + unknown[observed_indices] + NOISE))
                self.counters['calibration_discrepancy_rows'] += int(
                    np.count_nonzero(np.abs(modeled_db - sinr_observed) > 1e-4))
            if self.history and np.any(~current):
                absent = ~current
                gamma_upper = 3.0 if len(sinr_observed) < 20 else float(sinr_observed[-1])
                gamma_upper -= 1e-4
                required = own_power[absent] / (10.0 ** (gamma_upper / 10.0)) - peer_power[absent] - NOISE
                if p < 4:
                    grid_stations = np.column_stack((GRID, np.full(64, 100.0)))
                    prior = (4 - p) * np.mean(_power(grid_stations, points[absent]), axis=0)
                    grid_links = 64 * int(np.sum(absent))
                    self.counters['grid_power_evaluations'] += grid_links
                    self.counters['setup_link_evaluations'] += grid_links
                    self.counters['censor_prior_conflicts'] += int(np.count_nonzero(prior < required))
                    unknown[absent] = np.maximum(np.maximum(prior, required), 0.0)
                modeled_db = 10.0 * np.log10(own_power[absent] /
                                             (peer_power[absent] + unknown[absent] + NOISE))
                max_absent_current_sinr_db = float(np.max(modeled_db))
                self.counters['censor_discrepancy_rows'] += int(
                    np.count_nonzero(modeled_db >= gamma_upper + 1e-4))
            moving_power = _power(trajectory, points)
            all_power = np.concatenate((moving_power[:, :, None, :],
                                        np.broadcast_to(present_power[None, None, 1:, :],
                                                        (27, 4, p, n))), axis=2)
            denominator = np.sum(all_power, axis=2, keepdims=True) - all_power + unknown + NOISE
            sinr = 10.0 * np.log10(all_power / denominator)
        else:
            sinr = np.empty((27, 4, 1 + p, 0))
        self.counters['link_evaluations'] = (self.counters['candidate_link_evaluations']
                                              + self.counters['setup_link_evaluations'])
        scores, served = self._score(sinr, np.ones(n, dtype=bool))
        fallback = bool(np.all(served == 0.0))
        shadow_choice = -1
        shadow_fallback = False
        shadow_scores = shadow_served = None
        if self.history:
            self.counters['shadow_decisions'] += 1
            self.counters['shadow_objective_reductions'] += 108
            shadow_scores, shadow_served = self._score(sinr, current)
            shadow_fallback = bool(np.all(shadow_served == 0.0))
            shadow_choice = (self._sweep_choice(own, trajectory[:, -1, :], mutate=False)
                             if shadow_fallback else int(np.argmax(shadow_scores)))
        choice = self._sweep_choice(own, trajectory[:, -1, :], mutate=True) if fallback else int(np.argmax(scores))
        if fallback:
            self.counters['fallback_decisions'] += 1
        self._command = COMMANDS[choice].copy()
        self._plan = dict(fallback=fallback, selected_index=choice,
                          shadow_current_index=shadow_choice,
                          shadow_current_fallback=shadow_fallback,
                          predicted_J=float(scores[choice]),
                          predicted_service=float(served[choice]),
                          shadow_current_action=(COMMANDS[shadow_choice].copy()
                                                 if self.history else np.zeros(3, dtype=np.float32)),
                          shadow_command_disagreement=(self.history and choice != shadow_choice),
                          shadow_executed_disagreement=(self.history and not np.array_equal(
                              trajectory[choice], trajectory[shadow_choice])),
                          max_absent_current_sinr_db=max_absent_current_sinr_db)
        return scores, served, shadow_scores, shadow_served

    def act(self, obs_row, t: int):
        if t < 0:
            raise ValueError('t must be nonnegative')
        own, xy, sinr, peers = _parse(obs_row)
        if self._nav_index is None:
            self._nav_index = int(np.argmin(np.sum((WAYPOINTS - own[:2]) ** 2, axis=1)))
        self.counters['ingests'] += 1
        matches, inserts, evicts, observed_indices = self._ingest(xy, t)
        decision = t % 4 == 0
        scores = served = shadow_scores = shadow_served = None
        if decision:
            scores, served, shadow_scores, shadow_served = self._decide(
                own, sinr, peers, observed_indices)
        ages = t - self._last_seen[~self._current_mask]
        diag = dict(self._plan, decision=decision, n_current=len(xy),
                    n_current_points=int(np.sum(self._current_mask)),
                    n_cached=len(self._points) if self.history else 0,
                    n_absent=int(len(ages)), mean_absent_age=float(np.mean(ages)) if len(ages) else 0.0,
                    max_absent_age=int(np.max(ages)) if len(ages) else 0,
                    n_visible_peers=len(peers), n_unknown_peers=4-len(peers),
                    cache_matches=matches,
                    cache_inserts=inserts, cache_evicts=evicts)
        if decision:
            diag['scores'] = scores.copy()
            diag['served_candidates'] = served.copy()
            if self.history:
                diag['shadow_scores'] = shadow_scores.copy()
                diag['shadow_served_candidates'] = shadow_served.copy()
        return self._command.copy(), diag
