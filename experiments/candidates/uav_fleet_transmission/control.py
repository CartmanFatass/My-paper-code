"""Finite one-step ordinary motion and mask decisions from public coordinates."""

from itertools import product
import hashlib

import numpy as np

from envs.pettingzoo import uav_radio
from .host import mask_bits

COMMANDS = np.asarray(tuple(product((-1, 0, 1), repeat=3)), dtype=np.float32)


def decode_public_state(encoded, n_uavs):
    """Decode CountAdapter's float32 snapshot, preserving its quantization."""
    state = np.asarray(encoded, dtype=np.float32)
    if state.shape != (133,) or n_uavs not in (4, 8) or not np.isfinite(state).all():
        raise ValueError("requires a finite CountAdapter state and N4/N8")
    if not np.array_equal(state[24:32], np.arange(8) < n_uavs):
        raise ValueError("public validity bits disagree with fleet size")
    positions = state[:24].reshape(8, 3)[:n_uavs].astype(np.float64)
    positions[:, :2] *= 1000.0
    positions[:, 2] = positions[:, 2] * 100.0 + 50.0
    users = state[32:132].reshape(50, 2).astype(np.float64) * 1000.0
    return positions, users


def predict_next(positions, commands):
    """Native componentwise motion; multiplication retains action dtype."""
    positions = np.asarray(positions, dtype=np.float64)
    commands = np.asarray(commands)
    if positions.shape != commands.shape or positions.shape[-1] != 3:
        raise ValueError("matching [..., n_uavs, 3] positions and commands required")
    # Do not cast action to double before multiplying: native float32 actors
    # round action*30, then action*30*1, before adding double positions.
    next_positions = positions + (commands * 30) * 1.0
    return np.clip(next_positions, [0.0, 0.0, 50.0], [1000.0, 1000.0, 150.0])


class _Scores:
    """One decision's exact candidate and per-UAV geometry reuse."""

    def __init__(self, users):
        self.users = np.asarray(users, dtype=np.float64)
        if self.users.shape != (50, 2) or not np.isfinite(self.users).all():
            raise ValueError("requires 50 finite public user coordinates")
        self.geometry = {}
        self.cache = {}
        self.counts = dict(requested_candidates=0, scored_candidates=0,
                           cached_candidates=0, geometry_rows_computed=0,
                           geometry_rows_reused=0)

    def score(self, positions, masks):
        positions = np.asarray(positions, dtype=np.float64)
        if positions.ndim == 2:
            positions = np.repeat(positions[None], len(masks), axis=0)
        if positions.ndim != 3 or positions.shape[0] != len(masks) or positions.shape[2] != 3:
            raise ValueError("positions must contain one team per candidate")
        n = positions.shape[1]
        if n not in (4, 8) or not np.isfinite(positions).all():
            raise ValueError("requires finite N4/N8 team positions")
        active = np.asarray([mask_bits(mask, n) for mask in masks])
        masks = [int(mask) for mask in masks]
        self.counts["requested_candidates"] += len(masks)
        keys = [(team.tobytes(), mask) for team, mask in zip(positions, masks)]
        unique = {}
        for index, key in enumerate(keys):
            if key not in self.cache and key not in unique:
                unique[key] = index
        self.counts["cached_candidates"] += len(masks) - len(unique)
        if unique:
            indices = list(unique.values())
            path_loss = np.empty((len(indices), n, 50), dtype=np.float64)
            for candidate, index in enumerate(indices):
                for member, row in enumerate(positions[index]):
                    row_key = row.tobytes()
                    if row_key not in self.geometry:
                        self.geometry[row_key] = uav_radio.free_space_user_path_loss(
                            row[None], self.users)[0]
                        self.counts["geometry_rows_computed"] += 1
                    else:
                        self.counts["geometry_rows_reused"] += 1
                    path_loss[candidate, member] = self.geometry[row_key]
            scores = _score_batch(path_loss, positions[indices], active[indices])
            self.cache.update(zip(unique, scores))
            self.counts["scored_candidates"] += len(unique)
        return [dict(self.cache[key]) for key in keys]


def _score_batch(path_loss, positions, active):
    """Native radio arithmetic, batched over independent candidate teams."""
    rx_power = 23.0 - path_loss
    linear = 10 ** (rx_power / 10)
    linear[~active] = 0.0
    interference = np.zeros_like(path_loss)
    n = path_loss.shape[1]
    for source in range(n):
        for other in range(n):
            if other != source:
                interference[:, source] += linear[:, other]
    positive = interference > 0
    total_dbm = 10 * np.log10(np.where(positive, interference, 1.0))
    denominator = np.where(positive, 10 * np.log10(10 ** (-80.0 / 10)
                           + 10 ** (total_dbm / 10)), -80.0)
    sinr = rx_power - denominator
    sinr[~active] = -np.inf
    eligible = sinr >= 0.0
    # At native 0dB with positive noise, no user can be eligible for two
    # transmitters. Thus per-row top10 equals the global stable greedy rule.
    order = np.argsort(-sinr, axis=2, kind="stable")[:, :, :10]
    connections = np.zeros_like(eligible)
    np.put_along_axis(connections, order, np.take_along_axis(eligible, order, axis=2), axis=2)
    # Preserve generic greedy behavior even if floating rounding at an extreme
    # synthetic geometry defeats the mathematical exclusivity property.
    overlap = np.any(eligible.sum(axis=1) > 1, axis=1)
    for index in np.flatnonzero(overlap):
        connections[index] = uav_radio.greedy_connection_assignment(sinr[index], 0.0, 10)
    served = connections.sum(axis=(1, 2))
    normalized = np.clip(sinr / 30, 0, 1)
    quality_sum = np.cumsum(np.where(connections, normalized, 0.0)
                            .reshape(len(sinr), -1), axis=1)[:, -1]
    quality = quality_sum / np.maximum(served, 1)
    height = (np.mean(positions[:, :, 2], axis=1) - 50.0) / 100.0 * 0.1
    objective = 0.7 * (served / 50) + 0.3 * quality - height
    return [dict(J=float(j), served=int(s), quality=float(q), energy_penalty=float(h))
            for j, s, q, h in zip(objective, served, quality, height)]


def public_scores(users, positions, masks):
    """Score candidate masks (or matching team batches) without hidden truth."""
    return _Scores(users).score(positions, masks)


def choose_mask(users, positions, old_mask):
    n = len(positions)
    mask_bits(old_mask, n)
    masks = list(range(1, 1 << n))
    scorer = _Scores(users)
    scores = scorer.score(positions, masks)
    index = max(range(len(masks)), key=lambda k: (
        scores[k]["J"], scores[k]["served"], masks[k] == old_mask, -masks[k]))
    trace = dict(scorer.counts, masks=masks, scores=scores,
                 old_mask=int(old_mask), selected_mask=masks[index],
                 selected_score=scores[index], old_score=scores[int(old_mask)-1])
    return masks[index], trace


class OrdinaryController:
    """One rotating coordinate pass each tick, followed externally by E."""

    def __init__(self, n_uavs):
        if n_uavs not in (4, 8):
            raise ValueError("requires N4/N8")
        self.n_uavs = n_uavs
        self.commands = np.zeros((n_uavs, 3), dtype=np.float32)
        self.positions = self.users = None
        self.next_t = 0

    def select(self, t, public_state, old_mask):
        if t != self.next_t:
            raise ValueError("controller ticks must be sequential from reset")
        anchored = t % 10 == 0
        if anchored:
            if public_state is None:
                raise ValueError("boundary tick requires its public snapshot")
            self.positions, self.users = decode_public_state(public_state, self.n_uavs)
        elif public_state is not None:
            raise ValueError("fresh global state is forbidden between boundaries")
        mask_bits(old_mask, self.n_uavs)
        base = self.positions.copy()
        chosen = self.commands.copy()
        scorer = _Scores(self.users)
        order = [(t + j) % self.n_uavs for j in range(self.n_uavs)]
        choices = []
        for member in order:
            entering = chosen[member].copy()
            candidates = np.repeat(chosen[None], len(COMMANDS), axis=0)
            candidates[:, member] = COMMANDS
            predictions = predict_next(np.broadcast_to(base, candidates.shape), candidates)
            scores = scorer.score(predictions, [old_mask] * len(COMMANDS))
            movement = np.linalg.norm(predictions - base, axis=2).sum(axis=1)
            index = max(range(len(COMMANDS)), key=lambda k: (
                scores[k]["J"], scores[k]["served"], -float(movement[k]),
                np.array_equal(COMMANDS[k], entering), -k))
            entering_index = int(np.flatnonzero(np.all(COMMANDS == entering, axis=1))[0])
            # Compact reconstruction evidence for all candidates, in fixed command
            # order. Explicit little-endian doubles also fix the digest layout.
            readings = np.asarray([[score["J"], score["served"], score["quality"],
                                    score["energy_penalty"], move]
                                   for score, move in zip(scores, movement)], dtype="<f8")
            score_digest = hashlib.sha256(readings.tobytes()).hexdigest()
            chosen[member] = COMMANDS[index]
            choices.append(dict(member=member, entering=entering.tolist(),
                                selected=chosen[member].tolist(), score=scores[index],
                                entering_score=scores[entering_index],
                                score_digest=score_digest, movement=float(movement[index])))
        self.commands = chosen.copy()  # Issued commands survive position clipping.
        self.positions = predict_next(base, chosen)
        self.next_t += 1
        return chosen, self.positions.copy(), dict(scorer.counts, anchored=anchored,
                member_order=order, choices=choices, motion_mask=int(old_mask))
