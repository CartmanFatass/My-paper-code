"""Offline checks of retained B01 artifacts; no environment or actor execution."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def reconstruct_native(positions, users):
    delta = positions[..., None, :2] - users[None, None, :, :]
    distance2 = np.sum(delta * delta, axis=-1) + positions[..., None, 2] ** 2
    power = 10 ** (23 / 10) * (.15 / (4 * np.pi)) ** 2 / distance2
    sinr = 10 * np.log10(power / (power.sum(axis=1, keepdims=True) - power + 1e-8))
    eligible = sinr >= 3
    if (eligible.sum(axis=1) > 1).any():
        raise AssertionError("3dB cochannel eligibility must be unique per user")
    top = np.argsort(-sinr, axis=-1, kind="stable")[..., :10]
    selected = np.take_along_axis(eligible, top, axis=-1)
    values = np.take_along_axis(sinr, top, axis=-1)
    served = selected.sum(axis=(1, 2))
    quality = (np.where(selected, np.clip((values - 3) / 30, 0, 1), 0).sum(axis=(1, 2))
               / np.maximum(served, 1))
    return .7 * served / 50 + .3 * quality, served, quality


def read(run):
    run = Path(run).resolve()
    summary_bytes = (run / "summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    assert summary["status"] == "COMPLETE" and not summary["limits"]
    assert summary["counts"]["team_steps"] == 16384
    assert summary["counts"]["fit_started"] == summary["counts"]["optimizer_steps"] == 0
    assert len(summary["rows"]) == 64
    expected = {(a, s) for a in ("C", "H") for s in range(29091000, 29091032)}
    assert {(r["arm"], r["seed"]) for r in summary["rows"]} == expected
    arrays, rows, worlds = {}, {}, set()
    max_reward_error = max_quality_error = max_endpoint_error = 0.0
    raw_bytes = 0
    exposure = {a: dict(absent_uav_steps=0, full_user_rows=0, no_user_rows=0,
                       visible_peer_histogram=[0] * 5) for a in ("C", "H")}
    for row in summary["rows"]:
        arm, seed = row["arm"], row["seed"]
        path = run / "raw" / f"{arm}_{seed}.npz"
        content = path.read_bytes()
        assert hashlib.sha256(content).hexdigest() == row["raw"]["sha256"]
        assert len(content) == row["raw"]["bytes"]
        raw_bytes += len(content)
        with np.load(path, allow_pickle=False) as raw:
            data = {key: raw[key] for key in raw.files}
        assert data["observations"].shape == (256, 5, 104)
        assert data["commands"].shape == data["post_positions"].shape == (256, 5, 3)
        assert np.array_equal(data["decision_time"], np.arange(0, 256, 4))
        assert np.array_equal(data["decision"], np.repeat((np.arange(256) % 4 == 0)[:, None], 5, 1))
        assert np.array_equal(data["commands"], np.repeat(data["commands"][::4], 4, axis=0))
        before = np.concatenate((data["initial_positions"][None], data["post_positions"][:-1]))
        expected_post = np.clip(before + data["commands"] * 30, [0, 0, 50], [1000, 1000, 150])
        assert np.array_equal(expected_post, data["post_positions"])
        assert np.array_equal(data["displacements"], data["post_positions"] - before)
        terminal = data["terminal_observation"][:, :3].astype(np.float64)
        terminal = terminal * [1000, 1000, 100] + [0, 0, 50]
        endpoint_error = float(np.abs(terminal - data["post_positions"][-1]).max())
        assert endpoint_error < 1e-4
        reward, served, quality = reconstruct_native(data["post_positions"], data["true_users"])
        reward_error = float(np.abs(reward - data["reward"]).max())
        quality_error = float(np.abs(quality - data["sinr_quality"]).max())
        assert reward_error < 1e-12 and quality_error < 1e-12
        assert np.array_equal(served, data["served"])
        assert abs(float(reward.mean()) - row["J"]) < 1e-12
        assert float(served.mean()) == row["mean_served"]
        max_reward_error = max(max_reward_error, reward_error)
        max_quality_error = max(max_quality_error, quality_error)
        max_endpoint_error = max(max_endpoint_error, endpoint_error)
        exposure[arm]["absent_uav_steps"] += int((data["n_absent"] > 0).sum())
        exposure[arm]["full_user_rows"] += int((data["n_current"] == 20).sum())
        exposure[arm]["no_user_rows"] += int((data["n_current"] == 0).sum())
        hist = np.bincount(data["n_visible_peers"].ravel().astype(int), minlength=5)
        exposure[arm]["visible_peer_histogram"] = (
            np.asarray(exposure[arm]["visible_peer_histogram"]) + hist).tolist()
        arrays[(arm, seed)], rows[(arm, seed)] = data, row
    assert raw_bytes == summary["artifacts"]["raw_bytes"]
    paired = []
    for seed in range(29091000, 29091032):
        c, h = arrays[("C", seed)], arrays[("H", seed)]
        assert np.array_equal(c["true_users"], h["true_users"])
        assert np.array_equal(c["initial_positions"], h["initial_positions"])
        worlds.add(hashlib.sha256(c["true_users"].tobytes() + c["initial_positions"].tobytes()).hexdigest())
        command_diff = np.any(c["commands"] != h["commands"], axis=(1, 2))
        position_diff = np.any(c["post_positions"] != h["post_positions"], axis=(1, 2))
        cr, hr = rows[("C", seed)], rows[("H", seed)]
        paired.append(dict(seed=seed, J_H_minus_C=hr["J"] - cr["J"],
                           served_H_minus_C=hr["mean_served"] - cr["mean_served"],
                           path_H_minus_C_m=hr["mean_path_length_m"] - cr["mean_path_length_m"],
                           first_command_difference=int(np.flatnonzero(command_diff)[0]) if command_diff.any() else None,
                           first_position_difference=int(np.flatnonzero(position_diff)[0]) if position_diff.any() else None,
                           absent_point_decisions=hr["absent_point_decisions"],
                           shadow_executed_disagreements=hr["same_input_shadow_executed_disagreements"]))
    assert len(worlds) == 32
    arm_readings = {}
    mean_fields = ("J", "mean_served", "mean_sinr_quality", "coverage_reward", "quality_reward",
                   "mean_path_length_m", "min_served", "service_p10", "mean_cached_points", "mean_absent_points")
    sum_fields = ("zero_service_steps", "xy_boundary_uav_steps", "lower_altitude_uav_steps",
                  "fallback_decisions", "fallback_uav_steps", "never_observed_uavs", "absent_point_decisions",
                  "unmatched_cache_point_observations", "duplicate_cache_match_observations", "ambiguous_cache_match_observations")
    for arm in ("C", "H"):
        selected = [r for r in summary["rows"] if r["arm"] == arm]
        reading = {k: float(np.mean([r[k] for r in selected])) for k in mean_fields}
        reading.update({k: sum(r[k] for r in selected) for k in sum_fields})
        reading.update({k: max(r[k] for r in selected) for k in
                        ("max_cached_points", "max_absent_age", "max_cache_position_error_m")})
        reading["controller_counts"] = {k: sum(r["controller_counts"][k] for r in selected)
                                         for k in selected[0]["controller_counts"]}
        reading["episode_wall_seconds"] = sum(r["wall_seconds"] for r in selected)
        reading["exposure"] = exposure[arm]
        if arm == "H":
            for key in ("same_input_shadow_action_disagreements", "same_input_shadow_executed_disagreements", "shadow_fallback_decisions"):
                reading[key] = sum(r[key] for r in selected)
        arm_readings[arm] = reading
    return dict(source_summary_sha256=hashlib.sha256(summary_bytes).hexdigest(),
                artifact_checks=dict(raw_files=64, raw_bytes=raw_bytes, distinct_paired_worlds=32,
                                     reconstructed_native_steps=16384,
                                     max_reward_error=max_reward_error, max_quality_error=max_quality_error,
                                     max_terminal_position_roundoff_m=max_endpoint_error),
                arms=arm_readings, paired_worlds=paired,
                scope="Offline artifact verification and descriptive reading only; no new environment, policy, fit or evaluation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = read(args.run)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result["artifact_checks"], sort_keys=True))
