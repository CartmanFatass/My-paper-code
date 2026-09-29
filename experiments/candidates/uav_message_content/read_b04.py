"""Read B04 arrays without importing a learner, environment or predictor."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np


MASTERS = (19501, 19502, 19503)
ARMS = ("G", "O", "F")
HORIZON, N = 256, 5
BOUND_SHA = "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"
BOUND_CANONICAL = "/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt"
METRICS = ("J_net", "J_physical", "served_users_per_tick", "Q",
           "boundary_fraction", "height_floor_fraction", "height_ceiling_fraction",
           "mean_height_m", "worst_tick_service")
SPEED = np.array((.03, .03, .30), dtype=np.float64)
METRES = np.array((1000., 1000., 100.))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(actual, expected, atol=1e-10):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)


def ordinary_by_steps(position, action, central, horizon):
    """Independent iterative clipping checks the runner's closed-form forecast."""
    result = np.clip(np.asarray(position, dtype=np.float64) + SPEED * action, 0, 1)
    for _ in range(int(horizon) - 1):
        result = np.clip(result + SPEED * central, 0, 1)
    return result


def geometry(raw):
    users = np.asarray(raw)[3:63].reshape(20, 3)
    visible = users[users[:, 2] > 0]
    centroid = np.zeros(2) if not len(visible) else visible[:, :2].mean(0) + raw[:2]
    return np.r_[raw[:3], centroid, 0., len(visible) / 20]


def behavior(position):
    xyz = np.asarray(position[:-1], dtype=np.float64)
    tolerance = float(np.float32(1e-7))
    boundary = (np.abs(xyz) <= tolerance) | (np.abs(xyz - 1) <= tolerance)
    return dict(boundary_fraction=float(boundary[..., :2].any(-1).mean()),
                height_floor_fraction=float((np.abs(xyz[..., 2]) <= tolerance).mean()),
                height_ceiling_fraction=float((np.abs(xyz[..., 2] - 1) <= tolerance).mean()),
                mean_height_m=float((50 + 100 * xyz[..., 2]).mean()))


def conditional_contrast(first, second, metric):
    """The three continuations, not their nested worlds, are the inference units."""
    vectors = []
    for master in MASTERS:
        a, b = first[master], second[master]
        assert len(a) == len(b) == 32
        assert [row["episode"] for row in a] == list(range(32))
        assert [row["episode"] for row in b] == list(range(32))
        vectors.append([float(x[metric] - y[metric]) for x, y in zip(a, b)])
    means = [statistics.mean(row) for row in vectors]
    mean, sd = statistics.mean(means), statistics.stdev(means)
    half_width = 4.302652729911275 * sd / np.sqrt(3)
    return dict(mean=mean, per_continuation_mean=means, sample_sd=sd,
                descriptive_t95_df2=[mean - half_width, mean + half_width],
                per_world_differences={str(master): values for master, values in zip(MASTERS, vectors)},
                adverse_worlds={str(master): [i for i, x in enumerate(values) if x < 0]
                                for master, values in zip(MASTERS, vectors)},
                minimum=min(map(min, vectors)), maximum=max(map(max, vectors)))


def error_summary(prediction, target, weights):
    error = (np.asarray(prediction, dtype=np.float64) - target) * METRES
    weights = np.asarray(weights, dtype=np.float64)
    assert error.shape == (len(weights), 3)
    assert np.isfinite(error).all() and np.isfinite(weights).all() and np.all(weights >= 0)
    count = int(weights.sum())
    if not count:
        return dict(count=0, horizontal_mean_m=None, horizontal_rms_m=None,
                    height_mae_m=None, height_rms_m=None)
    horizontal_squared = np.square(error[:, :2]).sum(1)
    return dict(count=count,
                horizontal_mean_m=float(np.dot(np.sqrt(horizontal_squared), weights) / count),
                horizontal_rms_m=float(np.sqrt(np.dot(horizontal_squared, weights) / count)),
                height_mae_m=float(np.dot(np.abs(error[:, 2]), weights) / count),
                height_rms_m=float(np.sqrt(np.dot(np.square(error[:, 2]), weights) / count)))


def read_trace(row, arm):
    path = Path(row["raw"])
    assert digest(path) == row["raw_sha256"]
    augmented = arm != "B0"
    with np.load(path, allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
        shapes = dict(actor_input=(256, 5, 186 if augmented else 171),
                      critic_input=(256, 526 if augmented else 451),
                      pre_tanh_motion=(256, 5, 3), central_motion=(256, 5, 3),
                      action=(256, 5, 3), position=(257, 5, 3),
                      initial_state=(116,),
                      user_positions=(50, 2), connected_users=(256, 50),
                      packet=(256, 10 if augmented else 7),
                      ordinary_endpoint=(256, 3), sampled_cv_endpoint=(256, 3),
                      forecast_endpoint=(256, 3),
                      records=(256, 5, 5, 13 if augmented else 10),
                      cache_age=(256, 5, 5), cache_remaining_lead=(256, 5, 5))
        shapes.update({key: (256,) for key in (
            "sender", "due", "good", "deliveries", "reward_physical", "reward_net",
            "served_users", "Q")})
        if arm in ("O", "F"):
            shapes["shadow_central_motion"] = (256, 5, 3)
        for key, shape in shapes.items():
            assert data[key].shape == shape, (key, data[key].shape, shape)
            assert np.isfinite(data[key]).all(), key
        obs, positions, commands = data["actor_input"], data["position"], data["action"]
        close(obs[:, :, :3], positions[:-1], 0)
        close(obs[:, :, 107], 0, 0)
        close(obs[0, :, 104:107], 0, 0)
        close(obs[1:, :, 104:107], commands[:-1], 0)
        close(commands, np.tanh(data["pre_tanh_motion"]), 1e-6)
        close(positions[1:], np.clip(positions[:-1] + commands * SPEED, 0, 1), 3e-7)
        close(obs[:, :, 110:115], np.broadcast_to(np.eye(5), (256, 5, 5)), 0)
        close(data["critic_input"][:, 136:451].reshape(256, 5, 63), obs[:, :, 108:171], 0)
        close(data["critic_input"][:, :15].reshape(256, 5, 3), positions[:-1], 3e-7)
        close(data["critic_input"][:, 15:115].reshape(256, 50, 2),
              np.broadcast_to(data["user_positions"] / 1000, (256, 50, 2)), 1e-7)
        close(data["critic_input"][:, 115], np.arange(256) / 256, 0)
        close(data["critic_input"][:, 116:136].reshape(256, 5, 4), obs[:, :, 104:108], 0)
        close(data["initial_state"][15:115].reshape(50, 2), data["user_positions"], 0)
        if augmented:
            close(data["critic_input"][:, 451:].reshape(256, 5, 15), obs[:, :, 171:], 0)

        pending = np.zeros(5, dtype=bool)
        records = np.zeros((5, 5, 10), dtype=np.float32)
        forecasts = np.zeros((5, 5, 3), dtype=np.float32)
        sent_at = np.full((5, 5), -1, dtype=np.int64)
        rng = np.random.default_rng(row["channel_seed"])
        good = bool(rng.integers(2))
        use_weights = np.zeros(256, dtype=np.int64)
        early_weights = np.zeros(256, dtype=np.int64)
        late_weights = np.zeros(256, dtype=np.int64)
        age_counts = np.zeros(10, dtype=np.int64)
        lead_counts = np.zeros(11, dtype=np.int64)
        delivered = 0
        for t in range(256):
            assert int(data["good"][t]) == int(good)
            arrivals = np.flatnonzero(data["due"][:t] == t)
            for sent in arrivals:
                sender = int(data["sender"][sent])
                peers = np.arange(5) != sender
                records[peers, sender, :7] = data["packet"][sent, :7]
                records[peers, sender, 7] = 1
                records[peers, sender, 8] = sent / 256
                if augmented:
                    forecasts[peers, sender] = data["packet"][sent, 7:]
                sent_at[peers, sender] = sent
                pending[sender] = False
            valid = sent_at >= 0
            age = np.where(valid, t - sent_at, -1)
            lead = np.where(valid, np.minimum(sent_at + 10, 256) - t, 0)
            records[..., 9] = np.where(valid, t / 256 - records[..., 8], 0)
            forecasts[(lead <= 0) | ~valid] = 0
            close(obs[t, :, 121:171].reshape(5, 5, 10), records, 0)
            close(data["records"][t, :, :, :10], records, 0)
            if augmented:
                close(obs[t, :, 171:].reshape(5, 5, 3), forecasts, 0)
                close(data["records"][t, :, :, 10:], forecasts, 0)
            close(data["cache_age"][t], age, 0)
            close(data["cache_remaining_lead"][t], np.maximum(lead, 0), 0)
            assert np.all((age[valid] >= 1) & (age[valid] <= 9))
            assert np.all(lead[valid] > 0)
            for received, received_age, remaining in zip(sent_at[valid], age[valid], lead[valid]):
                use_weights[received] += 1
                (early_weights if received_age <= 4 else late_weights)[received] += 1
                age_counts[received_age] += 1
                lead_counts[remaining] += 1
            close(obs[t, :, 120], pending, 0)
            close(obs[t, :, 108:110], np.tile(np.eye(2)[int(good)], (5, 1)), 0)
            close(obs[t, :, 115:120], np.tile(np.eye(5)[t % 5], (5, 1)), 0)
            assert int(data["deliveries"][t]) == len(arrivals)
            sender = t % 5
            assert int(data["sender"][t]) == sender and not pending[sender]
            assert int(data["due"][t]) == t + (1 if good else 5)
            close(data["packet"][t, :7], geometry(obs[t, sender, :104]), 3e-7)
            k = min(10, 256 - t)
            if arm in ("O", "F"):
                ordinary = ordinary_by_steps(positions[t, sender], commands[t, sender],
                                             data["central_motion"][t, sender], k)
                sampled = ordinary_by_steps(positions[t, sender], commands[t, sender],
                                            commands[t, sender], k)
                close(data["ordinary_endpoint"][t], ordinary, 5e-7)
                close(data["sampled_cv_endpoint"][t], sampled, 5e-7)
                close(data["packet"][t, 7:], data["forecast_endpoint"][t], 0)
                if arm == "O":
                    close(data["forecast_endpoint"][t], ordinary, 5e-7)
                p1 = ordinary_by_steps(positions[t, sender], commands[t, sender],
                                      commands[t, sender], 1)
                lower, upper = np.maximum(0, p1 - (k - 1) * SPEED), np.minimum(1, p1 + (k - 1) * SPEED)
                assert np.all(data["forecast_endpoint"][t] >= lower - 5e-7)
                assert np.all(data["forecast_endpoint"][t] <= upper + 5e-7)
            else:
                for key in ("ordinary_endpoint", "sampled_cv_endpoint", "forecast_endpoint"):
                    close(data[key][t], 0, 0)
                if augmented:
                    close(data["packet"][t, 7:], 0, 0)
            pending[sender] = True
            if "pending_after_send" in data:
                close(data["pending_after_send"][t], pending, 0)
            delivered += len(arrivals)
            if rng.random() >= .95:
                good = not good

        assert np.all((data["connected_users"] == 0) | (data["connected_users"] == 1))
        close(data["connected_users"].sum(1), data["served_users"], 0)
        assert np.all((data["Q"] >= 0) & (data["Q"] <= 1))
        close(data["reward_physical"], .014 * data["served_users"] + .3 * data["Q"])
        close(data["reward_net"], data["reward_physical"] - .001)
        levels = {key: float(data[name].mean()) for key, name in (
            ("J_net", "reward_net"), ("J_physical", "reward_physical"),
            ("served_users_per_tick", "served_users"), ("Q", "Q"))}
        levels.update(behavior(positions))
        levels["worst_tick_service"] = float(data["served_users"].min())
        for key, value in levels.items():
            if key in row:
                close(row[key], value, 2e-5 if key == "mean_height_m" else 1e-7)
        assert delivered == row["delivered_packets"]
        censored = int((data["due"] >= 256).sum())
        assert int(pending.sum()) == censored == row["pending_at_end"]
        assert delivered + censored == 256
        action_hash = hashlib.sha256(commands.tobytes()).hexdigest()
        channel_hash = hashlib.sha256(bytes(data["good"].tolist())).hexdigest()
        if "action_sequence_sha256" in row:
            assert row["action_sequence_sha256"] == action_hash
        assert row["channel_sequence_sha256"] == channel_hash
        scene_hash = hashlib.sha256(obs[0, :, :104].tobytes() + data["initial_state"].tobytes()).hexdigest()
        assert row["initial_scene_sha256"] == scene_hash
        reading = dict(levels=levels, delivered=delivered, censored=censored,
                       cache_uses=int(use_weights.sum()), cache_age_counts=age_counts.tolist(),
                       remaining_lead_counts=lead_counts.tolist(), action_sha256=action_hash,
                       channel_sha256=channel_hash, initial_scene_sha256=scene_hash,
                       user_positions_sha256=hashlib.sha256(data["user_positions"].tobytes()).hexdigest(),
                       connected_bits_bytes=data["connected_users"].nbytes)
        if arm in ("O", "F"):
            targets = positions[np.minimum(np.arange(256) + 10, 256), np.arange(256) % 5]
            eligible = (data["due"] < 256).astype(np.int64)
            weights = dict(delivered_sends=eligible, all_sends=np.ones(256, dtype=np.int64),
                           cache_uses=use_weights, cache_age_1_4=early_weights,
                           cache_age_5_9=late_weights,
                           terminal_short_sends=eligible * (np.arange(256) > 246),
                           terminal_short_uses=use_weights * (np.arange(256) > 246))
            reading["forecast_error"] = {
                name: {group: error_summary(data[key], targets, weight) for group, weight in weights.items()}
                for name, key in (("actual", "forecast_endpoint"), ("ordinary", "ordinary_endpoint"),
                                  ("sampled_cv", "sampled_cv_endpoint"))}
            change = data["central_motion"].astype(np.float64) - data["shadow_central_motion"]
            reading["response_rms"] = float(np.sqrt(np.square(change).mean()))
            reading["response_max"] = float(np.abs(change).max())
            if "shadow_response_rms" in row:
                close(row["shadow_response_rms"], reading["response_rms"], 1e-7)
                close(row["shadow_response_max"], reading["response_max"], 1e-7)
            reading["forecast_minus_ordinary_rms_normalized"] = float(np.sqrt(np.square(
                data["forecast_endpoint"].astype(np.float64) - data["ordinary_endpoint"]).mean()))
        return reading


def merge_error_summaries(items):
    total = sum(item["count"] for item in items)
    if not total:
        return dict(count=0, horizontal_mean_m=None, horizontal_rms_m=None,
                    height_mae_m=None, height_rms_m=None)
    result = {"count": total}
    for key in ("horizontal_mean_m", "horizontal_rms_m", "height_mae_m", "height_rms_m"):
        power = 2 if "rms" in key else 1
        mean_power = sum(item["count"] * item[key] ** power for item in items if item["count"]) / total
        result[key] = float(mean_power ** (1 / power))
    return result


def validate_exposure(cells, b0, actual):
    assert [(cell["master"], cell["arm"]) for cell in cells] == [
        (master, arm) for master in MASTERS for arm in ARMS]
    assert b0["arm"] == "B0" and b0["master"] == 19451
    for cell in [*cells, b0]:
        baseline, forecast = cell["arm"] == "B0", cell["arm"] == "F"
        expected = dict(constructors=1, explicit_resets=32 if baseline else 544,
                        fit_started=0 if baseline else 1,
                        train_episodes=0 if baseline else 512, final_eval_episodes=32,
                        train_team_steps=0 if baseline else 131072,
                        final_eval_team_steps=8192, team_steps=8192 if baseline else 139264,
                        native_step_calls=8192 if baseline else 139264,
                        motion_samples=40960 if baseline else 696320,
                        broadcasts=8192 if baseline else 139264,
                        attempts=8192 if baseline else 139264, rollouts=0 if baseline else 256,
                        optimizer_steps=0 if baseline else 1024,
                        replayed_actor_rows=0 if baseline else 2621440,
                        predictor_forwards=139264 if forecast else 0,
                        predictor_updates=1024 if forecast else 0,
                        evaluation_optimizer_steps=0,
                        diagnostic_forward_calls=8192 if cell["arm"] in ("O", "F") else 0,
                        behavior_actor_forward_calls=8192 if baseline else 139264,
                        behavior_actor_forward_rows=40960 if baseline else 696320,
                        behavior_critic_forward_calls=8192 if baseline else 139264,
                        behavior_critic_forward_rows=8192 if baseline else 139264,
                        ppo_actor_forward_calls=0 if baseline else 1024,
                        ppo_actor_forward_rows=0 if baseline else 2621440,
                        ppo_critic_forward_calls=0 if baseline else 1024,
                        ppo_critic_forward_rows=0 if baseline else 524288)
        assert cell["status"] == "COMPLETE"
        for key, value in expected.items():
            assert cell["counts"][key] == value, (cell["master"], cell["arm"], key, cell["counts"][key], value)
        counts = cell["counts"]
        assert counts["delivered_packets"] + counts["censored_packets"] == counts["team_steps"]
        if forecast:
            assert 128512 <= counts["eligible_labels"] <= 130560
            assert counts["predictor_rows"] == 4 * counts["eligible_labels"]
        else:
            assert counts["eligible_labels"] == counts["predictor_rows"] == 0
    for key in actual:
        assert actual[key] == sum(cell["counts"][key] for cell in [*cells, b0]), key
    for key, expected in dict(fit_started=9, train_episodes=4608, final_eval_episodes=320,
                              train_team_steps=1179648, final_eval_team_steps=81920,
                              team_steps=1261568, motion_samples=6307840,
                              optimizer_steps=9216, replayed_actor_rows=23592960,
                              predictor_forwards=417792, predictor_updates=3072,
                              evaluation_optimizer_steps=0,
                              diagnostic_forward_calls=49152).items():
        assert actual[key] == expected, (key, actual[key], expected)


def read_update_stream(cell, episodes):
    arm = cell["arm"]
    path = Path(cell["directory"]) / "updates.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    kinds = ("ppo", "predictor") if arm == "F" else ("ppo",)
    expected = [(rollout, kind, epoch) for rollout in range(256)
                for kind in kinds for epoch in range(4)]
    assert [(r["rollout"], r["kind"], r["epoch"]) for r in records] == expected
    train = [row for row in episodes if row["phase"] == "train"]
    predictor_rows = 0
    for record in records:
        assert np.isfinite(record["loss"]) and np.isfinite(record["grad_norm"])
        assert record["grad_norm"] >= 0
        if record["kind"] == "predictor":
            rollout = record["rollout"]
            labels = sum(row["delivered_packets"] for row in train[2 * rollout:2 * rollout + 2])
            assert record["eligible_rows"] == labels
            predictor_rows += labels
    assert predictor_rows == cell["counts"]["predictor_rows"]
    result = dict(updates=len(records), sha256=digest(path), predictor_rows=predictor_rows)
    if arm == "F":
        first = [r["loss"] for r in records if r["kind"] == "predictor" and r["rollout"] < 16]
        last = [r["loss"] for r in records if r["kind"] == "predictor" and r["rollout"] >= 240]
        result.update(first16_rollouts_mean_loss=statistics.mean(first),
                      last16_rollouts_mean_loss=statistics.mean(last))
    return result


def read_run(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    manifest = json.loads((root / "launch-manifest.json").read_text())
    witness = json.loads((root / "process-exit.json").read_text())
    assert summary["status"] == "COMPLETE" and witness["exit_code"] == 0
    assert summary["source_sha"] == manifest["sha"]
    assert manifest["node"] == "wsl_4070" and manifest["direction"] == "uav_message_content"
    assert manifest["lead"] == "Codex DM (native child)"
    assert summary["warm_start"]["sha256"] == BOUND_SHA
    assert digest(BOUND_CANONICAL) == BOUND_SHA
    staged_input = Path(summary["warm_start"]["path"])
    if staged_input.exists():
        assert digest(staged_input) == BOUND_SHA
    assert summary["warm_start"]["bytes"] == 463357
    cells, b0, actual = summary["cells"], summary["b0"], summary["actual"]
    validate_exposure(cells, b0, actual)
    reading = dict(source_sha=summary["source_sha"], summary_sha256=digest(root / "summary.json"),
                   reader_sha256=digest(__file__), all_checks_passed=False,
                   native_steps_added=0, optimizer_calls_added=0, model_or_policy_calls_added=0,
                   actual=actual, policy_fits=9, trained_predictor_instances=3,
                   batch_wall_seconds=summary["finished_wall"] - summary["started_wall"],
                   resources=summary["resources"], levels={}, contrasts={}, versus_B0={},
                   raw_checks={}, update_checks={}, exposure={}, forecast={},
                   limitations=[
                       "Three continuation instances are conditional on one selected B19451 parent.",
                       "The df2 intervals assume independent continuation contrasts; 32 worlds are nested deployment variation.",
                       "All primary arms use40-byte packets with the fixed abstract28-byte channel's fee and delay; B0 is cross-contract.",
                       "Forecasts are fallible dated endpoint estimates, not commitments or guaranteed future positions.",
                       "Shadow actor responses do not identify causal mediation or the value of a historical replacement policy.",
                       "Connected-user telemetry is evaluation-only archival evidence, not a B04 objective or metric gate.",
                       "Boundary and altitude measurements are behavior, not battery or physical-safety outcomes."])
    paired = None
    initial_hashes = None
    panels = {}
    raw_bytes = 0
    connected_bytes = 0
    for cell in [*cells, b0]:
        master, arm = cell["master"], cell["arm"]
        label = "B0" if arm == "B0" else f"{master}/{arm}"
        folder = Path(cell["directory"])
        episodes = [json.loads(line) for line in (folder / "episodes.jsonl").read_text().splitlines()]
        train = [row for row in episodes if row["phase"] == "train"]
        final = [row for row in episodes if row["phase"] == "final_eval"]
        assert len(episodes) == (32 if arm == "B0" else 544)
        assert len(train) == (0 if arm == "B0" else 512)
        assert final == cell["rows"] and [row["episode"] for row in final] == list(range(32))
        assert cell["counts"]["delivered_packets"] == sum(row["delivered_packets"] for row in episodes)
        assert cell["counts"]["censored_packets"] == sum(row["pending_at_end"] for row in episodes)
        for e, row in enumerate(train):
            assert row["arm"] == arm and row["master"] == master and row["episode"] == e
            assert row["steps"] == row["attempts"] == row["accepted_packets"] == 256
            assert row["collided_attempts"] == 0
            assert row["reset_seed"] == 100000 * master + 1000 + e
            assert row["channel_seed"] == 100000 * master + 6000 + e
            assert row["motion_seed"] == 100000 * master + 21
        if arm != "B0":
            for checkpoint_key in ("initial_checkpoint", "final_checkpoint"):
                checkpoint = cell[checkpoint_key]
                assert digest(checkpoint["path"]) == checkpoint["sha256"]
            hashes = cell["initial_tensor_sha256"]
            common = {key: hashes[key] for key in ("actor_old", "actor_forecast", "critic_old", "critic_forecast")}
            if initial_hashes is None:
                initial_hashes = common
            else:
                assert common == initial_hashes
            for name in ("actor_forecast", "critic_forecast"):
                assert cell["exposure"][name]["initial_norm"] == 0
                if arm == "G":
                    assert cell["exposure"][name]["displacement"] == 0
            reading["exposure"][label] = cell["exposure"]
            reading["update_checks"][label] = read_update_stream(cell, episodes)
            if arm == "F":
                assert cell["counts"]["eligible_labels"] == sum(row["delivered_packets"] for row in train)
        checks = []
        for e, row in enumerate(final):
            assert row["arm"] == arm and row["master"] == master and row["steps"] == 256
            assert row["reset_seed"] == 1950002000 + e
            assert row["channel_seed"] == 1950007000 + e
            assert row["motion_seed"] == 1950003000 + e
            assert row["attempts"] == row["accepted_packets"] == 256 and row["collided_attempts"] == 0
            close(row["charge_per_tick"], .001)
            checks.append(read_trace(row, arm))
            raw_bytes += Path(row["raw"]).stat().st_size
            connected_bytes += checks[-1]["connected_bits_bytes"]
        witnesses = [(check["initial_scene_sha256"], check["channel_sha256"], check["user_positions_sha256"])
                     for check in checks]
        if paired is None:
            paired = witnesses
        else:
            assert witnesses == paired
        panels[(master, arm)] = [dict(row, **check["levels"]) for row, check in zip(final, checks)]
        reading["raw_checks"][label] = checks
        reading["levels"][label] = {metric: statistics.mean(check["levels"][metric] for check in checks)
                                      for metric in METRICS}
        if arm in ("O", "F"):
            first_error = checks[0]["forecast_error"]
            errors = {name: {group: merge_error_summaries([c["forecast_error"][name][group] for c in checks])
                             for group in groups} for name, groups in first_error.items()}
            reading["forecast"][label] = dict(
                errors=errors, response_rms=float(np.sqrt(np.mean([c["response_rms"] ** 2 for c in checks]))),
                response_max=max(c["response_max"] for c in checks),
                cache_uses=sum(c["cache_uses"] for c in checks),
                cache_age_counts=np.asarray([c["cache_age_counts"] for c in checks]).sum(0).tolist(),
                remaining_lead_counts=np.asarray([c["remaining_lead_counts"] for c in checks]).sum(0).tolist())
    for first, second in (("F", "O"), ("F", "G"), ("O", "G")):
        reading["contrasts"][f"{first}-{second}"] = {
            metric: conditional_contrast({m: panels[(m, first)] for m in MASTERS},
                                         {m: panels[(m, second)] for m in MASTERS}, metric)
            for metric in METRICS}
    for arm in ARMS:
        reading["versus_B0"][arm] = {
            metric: conditional_contrast({m: panels[(m, arm)] for m in MASTERS},
                                         {m: panels[(19451, "B0")] for m in MASTERS}, metric)
            for metric in METRICS}
    assert connected_bytes == 4096000
    reading.update(all_checks_passed=True, raw_trace_bytes=raw_bytes,
                   connected_bits_uncompressed_bytes=connected_bytes, trajectories_read=320,
                   warm_start=summary["warm_start"], canonical_warm_start=BOUND_CANONICAL,
                   initial_common_tensor_hashes=initial_hashes)
    return reading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = read_run(args.run)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
