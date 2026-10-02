"""Independent transport/physical/service reconstruction and complete neural replay."""

import hashlib
import math
import struct

import numpy as np
import torch

from envs.pettingzoo.uav_radio import free_space_user_path_loss, user_sinr_from_path_loss, greedy_connection_assignment, service_metrics
from experiments.candidates.uav_message_content.read_b04 import behavior
from experiments.candidates.uav_message_content.read_b05 import interval, longest_zero_interval
from .contract import FIELDS, PROGRAMS, increment, require, verify_artifact


def independent_neural_step(actor, x, hidden, kind):
    """Reconstruct from frozen tensors/modules without using the B07 adapter forward."""
    from torch.nn.functional import linear
    base = actor if kind == "B" else actor.base
    observations = x[None, :, :171]
    encoder = base.encoder
    encoded = linear(observations, encoder.raw.weight, encoder.raw.bias) + linear(
        torch.tanh(linear(observations, encoder.hidden.weight, encoder.hidden.bias)),
        encoder.context.weight, encoder.context.bias)
    recurrent, next_hidden = base.gru(torch.tanh(encoded), hidden)
    mean = linear(recurrent, base.mean.weight, base.mean.bias)
    if kind == "D":
        residual_input = torch.cat((x[None], recurrent), -1)
        correction = .1 * torch.tanh(linear(torch.tanh(linear(
            residual_input, actor.residual_hidden.weight, actor.residual_hidden.bias)),
            actor.residual_output.weight, actor.residual_output.bias))
        mean = mean + correction
    return mean, next_hidden


def close(actual, expected, atol=0):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)


def independent_source(raw):
    """Retain sender's FP32 sum, int64-array division and FP64 addition before cast."""
    users = raw[3:63].reshape(20, 3)
    visible = users[:, 2] > 0
    summed = (users[:, :2] * visible[:, None]).sum(0)
    count = int(visible.sum())
    centroid = summed.astype(np.float64) / max(count, 1) + raw[:2].astype(np.float64) if count else np.zeros(2)
    return np.r_[raw[:3], centroid, count / 20].astype(np.float32)


def delivered_geometry(packet, book):
    values = np.frombuffer(packet[2:], dtype="<f4").copy() if book is None else book[packet[2]].numpy().copy()
    payload = np.zeros(7, dtype=np.float32)
    payload[list(FIELDS)] = values
    return payload


def individual_service(bits):
    require(bits.ndim == 2 and np.isin(bits, (0, 1)).all(), "individual bits")
    horizon, users = bits.shape
    age, run, longest = np.zeros(users, dtype=int), np.zeros(users, dtype=int), np.zeros(users, dtype=int)
    age_sum = np.zeros(users, dtype=int)
    for connected in bits:
        age = np.where(connected, 0, age + 1)
        run = np.where(connected, 0, run + 1)
        longest = np.maximum(longest, run)
        age_sum += age
    ticks = bits.sum(0).astype(int)
    cases = []
    for user in range(users):
        false = np.r_[False, bits[:, user] == 0, False]
        edges = np.flatnonzero(false[1:] != false[:-1])
        gaps = [(int(a), int(b), int(b - a)) for a, b in zip(edges[::2], edges[1::2])]
        maximum = int(longest[user])
        cases.extend(dict(user=user, start=a, end_exclusive=b, gap=length,
                          prefix_censored=a == 0, suffix_censored=b == horizon)
                     for a, b, length in gaps if length == maximum)
    return dict(served_ticks=ticks.tolist(), mean_waiting_age=(age_sum / horizon).tolist(),
                longest_gap=longest.tolist(), prefix_censored=(bits[0] == 0).tolist(),
                suffix_censored=(bits[-1] == 0).tolist(), never_served=int((ticks == 0).sum()),
                minimum_user_served_ticks=int(ticks.min()), worst_user_longest_gap=int(longest.max()),
                world_mean_waiting_age=float(age_sum.mean() / horizon),
                longest_gap_cases=[c for c in cases if c["gap"] == int(longest.max())])


def read_episode(row, actor, kind, book, scales, counts, progress=lambda: None):
    path = verify_artifact(row["raw"])
    with np.load(path, allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
    horizon = row["steps"]
    require(horizon == 256, "reader full H256")
    require((row["physical_seed"], row["channel_seed"], row["motion_seed"]) ==
            (1981002000 + row["world"], 1981007000 + row["world"], 1981003000 + row["world"]),
            "reader fixed world tuple")
    shapes = dict(raw_observation=(horizon, 5, 104), actor_input=(horizon, 5, 186),
                  composed_mean=(horizon, 5, 3), pre_tanh_motion=(horizon, 5, 3),
                  action=(horizon, 5, 3), sample_logp=(horizon, 5),
                  packet_bytes=(horizon, 26 if book is None else 3), beacon_bytes=(horizon, 2),
                  physical_position=(horizon + 1, 5, 3), user_positions=(50, 2), log_std=(3,), initial_state=(116,),
                  records=(horizon, 5, 5, 10), pending_after_send=(horizon, 5), connected_users=(horizon, 50))
    shapes.update({k: (horizon,) for k in ("due", "served_users", "Q", "reward_physical", "reward_net", "deliveries")})
    for key, shape in shapes.items():
        require(data[key].shape == shape and np.isfinite(data[key]).all(), f"reader {key} shape/finite")
    require(data["packet_bytes"].dtype == data["beacon_bytes"].dtype == np.uint8, "trace byte dtype")
    require(hashlib.sha256(data["raw_observation"][0].tobytes() + data["initial_state"].tobytes()).hexdigest() == row["initial_scene_sha256"], "reader scene hash")
    close(data["initial_state"][:15], data["physical_position"][0].ravel().astype(np.float32))
    close(data["initial_state"][15:115], data["user_positions"].ravel().astype(np.float32))
    close(data["log_std"], actor.log_std.detach().numpy())
    close(data["raw_observation"][..., :2], data["physical_position"][:-1, :, :2] / 1000, 6e-8)
    close(data["raw_observation"][..., 2], (data["physical_position"][:-1, :, 2] - 50) / 100, 6e-8)
    close(data["raw_observation"][..., -1], np.broadcast_to(np.arange(horizon)[:, None] / 256, (horizon, 5)))
    expected_xyz = data["physical_position"][:-1] + data["action"] * np.float32(30)
    expected_xyz[..., :2] = np.clip(expected_xyz[..., :2], 0, 1000)
    expected_xyz[..., 2] = np.clip(expected_xyz[..., 2], 50, 150)
    close(data["physical_position"][1:], expected_xyz, 1e-12)
    channel_rng = np.random.default_rng(row["channel_seed"])
    good = bool(channel_rng.integers(2))
    motion_rng = torch.Generator().manual_seed(row["motion_seed"])
    require(hashlib.sha256(motion_rng.get_state().numpy().tobytes()).hexdigest() == row["motion_rng_start_sha256"], "reader motion start")
    innovations = hashlib.sha256()
    records = np.zeros((5, 5, 10), dtype=np.float32)
    deadline = np.full(5, -1, dtype=int)
    queue, hidden, last = [], torch.zeros(1, 5, 64), np.zeros((5, 3), dtype=np.float32)
    means, densities, delivered = [], [], 0
    for t in range(horizon):
        arriving = [(due, packet) for due, packet in queue if due == t]
        queue = [item for item in queue if item[0] > t]
        for due, packet in arriving:
            delivered_word = struct.unpack("<H", packet[:2])[0]
            sender, sent = delivered_word & 7, (delivered_word >> 3) & 255
            value = delivered_geometry(packet, book)
            peers = np.arange(5) != sender
            records[peers, sender, :7] = value
            records[peers, sender, 7] = 1
            records[peers, sender, 8] = sent / 256
        records[..., 9] = np.where(records[..., 7] > 0, t / 256 - records[..., 8], 0)
        pending = deadline > t
        close(data["beacon_bytes"][t], [t, int(good)])
        close(data["records"][t], records)
        close(data["deliveries"][t], len(arriving))
        public = np.concatenate((np.tile(np.eye(2, dtype=np.float32)[int(good)], (5, 1)),
                                 np.eye(5, dtype=np.float32), np.tile(np.eye(5, dtype=np.float32)[t % 5], (5, 1)),
                                 pending[:, None], records.reshape(5, 50)), 1)
        x = np.concatenate((data["raw_observation"][t], last, np.zeros((5, 1), dtype=np.float32),
                            public, np.zeros((5, 15), dtype=np.float32)), 1).astype(np.float32)
        close(data["actor_input"][t], x)
        with torch.no_grad():
            mean, hidden = independent_neural_step(actor, torch.from_numpy(x), hidden, kind)
            mean = mean[0]
        increment(counts, "reader_actor_rows", 5)
        increment(counts, "reader_actor_calls")
        require(torch.equal(mean, torch.from_numpy(data["composed_mean"][t])), "native neural mean replay")
        epsilon = torch.stack([torch.randn(3, generator=motion_rng) for _ in range(5)])
        innovations.update(epsilon.numpy().tobytes())
        expected_u = mean + actor.log_std.clamp(-5, 2).exp() * epsilon
        require(torch.equal(expected_u, torch.from_numpy(data["pre_tanh_motion"][t])), "reader motion sample")
        close(data["action"][t], expected_u.tanh().numpy())
        # Independent Gaussian/Jacobian density arithmetic in float64.
        u, mu = expected_u.numpy().astype(np.float64), mean.numpy().astype(np.float64)
        log_sd = np.clip(data["log_std"].astype(np.float64), -5, 2)
        density = (-.5 * ((u - mu) / np.exp(log_sd)) ** 2 - log_sd - .5 * math.log(2 * math.pi)
                   - 2 * (math.log(2) - u - np.logaddexp(0, -2 * u))).sum(-1)
        close(data["sample_logp"][t], density, 2e-5)
        means.append(mean.numpy())
        densities.append(float(np.max(np.abs(density - data["sample_logp"][t]))))
        packet = bytes(data["packet_bytes"][t])
        word = struct.unpack("<H", packet[:2])[0]
        sender, sent = word & 7, (word >> 3) & 255
        require(sender == t % 5 and sent == t and word >> 11 == 1 and not pending[sender], "reader wire header")
        source = independent_source(data["raw_observation"][t, sender])
        if book is None:
            value = np.frombuffer(packet[2:], dtype="<f4").copy()
            close(value, source)
        else:
            distance = (((torch.from_numpy(source)[None] - book) * scales) ** 2).sum(1)
            index = int(torch.argmin(distance))
            increment(counts, "nearest_center_comparisons", 256)
            require(packet[2] == index, "reader hard index")
        due = t + (1 if good else 5)
        close(data["due"][t], due)
        queue.append((due, packet))
        deadline[sender] = due
        pending[sender] = True
        close(data["pending_after_send"][t], pending)
        xyz = data["physical_position"][t + 1]
        loss = free_space_user_path_loss(xyz, data["user_positions"])
        sinr = user_sinr_from_path_loss(loss)
        connections = greedy_connection_assignment(sinr)
        outcome = service_metrics(sinr, connections)
        close(data["connected_users"][t], connections.any(0))
        close(data["served_users"][t], outcome["served"])
        close(data["Q"][t], outcome["quality"], 1e-12)
        close(data["reward_physical"][t], outcome["J"], 1e-12)
        close(data["reward_net"][t], outcome["J"] - .001, 1e-12)
        increment(counts, "reader_physical_states")
        increment(counts, "reader_steps")
        delivered += len(arriving)
        last = data["action"][t]
        if channel_rng.random() >= .95:
            good = not good
        if t % 32 == 31:
            progress()
    require(innovations.hexdigest() == row["innovation_sha256"] and row["innovation_vectors"] == 5 * horizon,
            "reader innovation identity")
    require(hashlib.sha256(motion_rng.get_state().numpy().tobytes()).hexdigest() == row["motion_rng_end_sha256"], "reader motion end")
    require(delivered == row["delivered"] and len(queue) == row["censored"] and delivered + len(queue) == horizon,
            "reader arrival/censor totals")
    require(hashlib.sha256(data["action"].tobytes()).hexdigest() == row["action_sequence_sha256"], "reader action hash")
    require(hashlib.sha256(data["beacon_bytes"][:, 1].tobytes()).hexdigest() == row["channel_sequence_sha256"], "reader channel hash")
    require(hashlib.sha256(data["user_positions"].tobytes()).hexdigest() == row["user_positions_sha256"], "reader users hash")
    levels = {key: float(data[name].mean()) for key, name in (
        ("J_net", "reward_net"), ("J_physical", "reward_physical"), ("served_users_per_tick", "served_users"), ("Q", "Q"))}
    for key, value in levels.items():
        close(row[key], value, 1e-12)
    normalized = data["physical_position"].copy()
    normalized[..., :2] /= 1000
    normalized[..., 2] = (normalized[..., 2] - 50) / 100
    levels.update(behavior(normalized), worst_tick_service=int(data["served_users"].min()),
                  p10_team_service=float(np.percentile(data["served_users"], 10)),
                  zero_service_steps=int((data["served_users"] == 0).sum()),
                  longest_zero_service=longest_zero_interval(data["served_users"]),
                  motion_path_m_per_uav=float(np.linalg.norm(np.diff(data["physical_position"], axis=0), axis=-1).sum(0).mean()))
    service = individual_service(data["connected_users"])
    levels.update({k: service[k] for k in ("never_served", "minimum_user_served_ticks", "worst_user_longest_gap", "world_mean_waiting_age")})
    return dict(world=row["world"], levels=levels, individual_service=service,
                density_max_abs_error=max(densities), neural_replay_rows=5 * horizon,
                packet_bytes=data["packet_bytes"].nbytes, beacon_bytes=data["beacon_bytes"].nbytes)


def compare(first, second):
    result = {}
    for metric in first[0]["levels"]:
        differences = [a["levels"][metric] - b["levels"][metric] for a, b in zip(first, second)]
        lower = metric in ("never_served", "worst_user_longest_gap", "world_mean_waiting_age", "zero_service_steps", "longest_zero_service")
        higher = metric in ("J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service", "p10_team_service", "minimum_user_served_ticks")
        direction = "lower" if lower else ("higher" if higher else "descriptive")
        result[metric] = dict(interval(differences, 31), per_world=differences,
                              signed_negative_worlds=[i for i, v in enumerate(differences) if v < 0],
                              signed_positive_worlds=[i for i, v in enumerate(differences) if v > 0],
                              utility_direction=direction,
                              adverse_worlds=[i for i, v in enumerate(differences) if (v > 0 if lower else v < 0)] if lower or higher else None)
    individual = {}
    for metric in ("served_ticks", "mean_waiting_age", "longest_gap"):
        differences = np.asarray([a["individual_service"][metric] for a in first]) - np.asarray([b["individual_service"][metric] for b in second])
        individual[metric] = dict(same_user_differences=differences.tolist(), minimum=float(differences.min()),
                                  maximum=float(differences.max()), mean=float(differences.mean()))
    return dict(metrics=result, individual=individual)


def full_read(rows, actors, selected, counts, progress=lambda: None):
    require(tuple(rows) == PROGRAMS, "reader program coverage/order")
    panels = {}
    for program in PROGRAMS:
        require([r["world"] for r in rows[program]] == list(range(32)), "reader world coverage")
        kind = "B" if program == "fullB" else "D"
        book, scales = selected[program] if program in selected else (None, None)
        panels[program] = []
        for row in rows[program]:
            panels[program].append(read_episode(row, actors[kind], kind, book, scales, counts, progress))
            progress()
    for e in range(32):
        for witness in ("initial_scene_sha256", "user_positions_sha256", "channel_sequence_sha256", "innovation_sha256",
                        "motion_rng_start_sha256", "motion_rng_end_sha256"):
            require(len({rows[p][e][witness] for p in PROGRAMS}) == 1, f"common world witness {witness}")
    comparisons = {}
    for r in range(1, 4):
        for a, b in ((f"L{r}", f"O{r}"), (f"O{r}", "fullD"), (f"L{r}", "fullD"),
                     (f"O{r}", "fullB"), (f"L{r}", "fullB")):
            comparisons[f"{a}-{b}"] = compare(panels[a], panels[b])
    comparisons["fullD-fullB"] = compare(panels["fullD"], panels["fullB"])
    conditional = {}
    for family, reference in (("L", "O"), ("O", "fullD"), ("L", "fullD"), ("O", "fullB"), ("L", "fullB")):
        conditional[f"{family}-{reference}"] = {
            metric: dict(interval([comparisons[f"{family}{r}-{reference + str(r) if reference == 'O' else reference}"]["metrics"][metric]["mean"]
                                   for r in range(1, 4)], 2), scope="codec initializations conditional on selected D, old bank and common fresh panel")
            for metric in panels["fullD"][0]["levels"]}
    return dict(panels=panels, comparisons=comparisons, conditional_codec_seed=conditional,
                retention="descriptive paired distributions; no adoption/equivalence threshold",
                actor_rows=327680, native_rollouts_added=0)
