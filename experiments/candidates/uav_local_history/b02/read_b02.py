"""Offline B02 artifact, trajectory, lawful-input and frozen-policy verification."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_local_history.b01.read_b01 import reconstruct_native
from experiments.candidates.uav_local_history.b02.inputs import ObservationHistory, current_only
from experiments.candidates.uav_local_history.b02.model import SetActor, categorical_terms


def verify(identity):
    path = Path(identity["path"])
    content = path.read_bytes()
    assert len(content) == identity["bytes"]
    assert hashlib.sha256(content).hexdigest() == identity["sha256"]
    return content


@torch.no_grad()
def read(run):
    run = Path(run).resolve()
    summary_content = (run / "summary.json").read_bytes()
    summary = json.loads(summary_content)
    assert summary["status"] == "COMPLETE" and not summary["limits"]
    counts = summary["counts"]
    assert counts["fit_started"] == counts["fit_completed"] == 3
    assert counts["train_team_steps"] == 393216 and counts["eval_team_steps"] == 65536
    assert counts["team_steps"] == counts["native_step_calls"] == 458752
    assert counts["complete_episodes"] == counts["explicit_resets"] == 1792
    assert counts["actor_optimizer_steps"] == counts["critic_optimizer_steps"] == 3072
    assert counts["optimizer_steps"] == 6144 and counts["ppo_rollouts"] == 768
    assert len(summary["rows"]) == 256 and len(summary["fits"]) == 3
    masters = (291021, 291022, 291023)
    models, fit_readings = {}, []
    for block, fit in enumerate(summary["fits"]):
        master = masters[block]
        assert fit["master"] == master and fit["status"] == "COMPLETE"
        for phase, arm in (("initial", "L0"), ("final", "L1")):
            verify(fit[phase])
            checkpoint = torch.load(fit[phase]["path"], map_location="cpu", weights_only=True)
            assert checkpoint["master"] == master and checkpoint["phase"] == phase
            actor = SetActor()
            actor.load_state_dict(checkpoint["actor"], strict=True)
            actor.eval()
            models[(arm, master)] = actor
        episodes = [json.loads(line) for line in verify(fit["training_episodes"]).splitlines()]
        updates = [json.loads(line) for line in verify(fit["training_updates"]).splitlines()]
        assert len(episodes) == 512 and len(updates) == 1024
        assert [r["seed"] for r in episodes] == list(range(29110000 + 1000 * block, 29110512 + 1000 * block))
        assert all(r["master"] == master and r["phase"] == "train" and r["steps"] == 256 for r in episodes)
        assert [(r["rollout"], r["epoch"]) for r in updates] == [(i, j) for i in range(256) for j in range(4)]
        assert all(np.isfinite([r[k] for k in ("loss", "entropy", "approx_kl", "clip_fraction", "actor_grad_norm", "critic_grad_norm")]).all() for r in updates)
        fit_readings.append(dict(master=master, training_worlds=512, update_epochs=1024,
                                 epoch0_max_abs_kl=max(abs(r["approx_kl"]) for r in updates if r["epoch"] == 0),
                                 epoch0_max_clip_fraction=max(r["clip_fraction"] for r in updates if r["epoch"] == 0),
                                 final_epoch_entropy_per_agent=updates[-1]["entropy"] / 5,
                                 maximum_abs_kl=max(abs(r["approx_kl"]) for r in updates),
                                 mean_clip_fraction=float(np.mean([r["clip_fraction"] for r in updates]))))
    expected_keys = {(a, None, s) for a in ("C", "H") for s in range(29102000, 29102032)}
    expected_keys |= {(a, m, s) for a in ("L0", "L1") for m in masters for s in range(29102000, 29102032)}
    assert {(r["arm"], r.get("master"), r["seed"]) for r in summary["rows"]} == expected_keys
    worlds, raw_bytes = {}, 0
    maximum_reward_error = maximum_logit_error = maximum_logp_error = 0.0
    exact_argmax_rows = lawful_input_rows = shadow_motion_count = 0
    for row in summary["rows"]:
        raw_bytes += len(verify(row["raw"]))
        with np.load(row["raw"]["path"], allow_pickle=False) as raw:
            data = {key: raw[key] for key in raw.files}
        assert data["observations"].shape == (256, 5, 104)
        assert data["post_positions"].shape == data["commands"].shape == (256, 5, 3)
        assert np.array_equal(data["commands"], np.repeat(data["commands"][::4], 4, axis=0))
        before = np.concatenate((data["initial_positions"][None], data["post_positions"][:-1]))
        expected_post = np.clip(before + 30 * data["commands"], [0, 0, 50], [1000, 1000, 150])
        assert np.array_equal(expected_post, data["post_positions"])
        terminal = data["terminal_observation"][:, :3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
        assert np.abs(terminal - data["post_positions"][-1]).max() < 1e-4
        reward, served, quality = reconstruct_native(data["post_positions"], data["true_users"])
        error = float(np.abs(reward - data["reward"]).max())
        maximum_reward_error = max(maximum_reward_error, error)
        assert error < 1e-12 and np.array_equal(served, data["served"])
        assert np.abs(quality - data["sinr_quality"]).max() < 1e-12
        assert abs(reward.mean() - row["J"]) < 1e-12 and served.mean() == row["mean_served"]
        world_hash = hashlib.sha256(data["true_users"].tobytes() + data["initial_positions"].tobytes()).hexdigest()
        if row["seed"] in worlds:
            assert worlds[row["seed"]] == world_hash
        worlds[row["seed"]] = world_hash
        if row["arm"] in ("C", "H"):
            continue
        assert row["initial_world_sha256"] == world_hash
        model = models[(row["arm"], row["master"])]
        histories = [ObservationHistory() for _ in range(5)]
        last = np.zeros((5, 3), dtype=np.float32)
        action_counts = np.zeros(27, dtype=np.int64)
        episode_shadow_changes = 0
        for clock in range(256):
            for agent, history in enumerate(histories):
                history.ingest(data["observations"][clock, agent], clock)
            if clock % 4 == 0:
                index = clock // 4
                packed = [h.features(last[i]) for i, h in enumerate(histories)]
                context, points, valid = (np.stack([p[j] for p in packed]) for j in range(3))
                for key, value in (("context", context), ("points", points), ("valid", valid)):
                    assert np.array_equal(value, data[key][index])
                lawful_input_rows += 5
                logits = model(torch.from_numpy(context), torch.from_numpy(points), torch.from_numpy(valid))
                error = float(np.abs(logits.numpy() - data["logits"][index]).max())
                maximum_logit_error = max(maximum_logit_error, error)
                assert error < 2e-6
                action = logits.argmax(dim=-1)
                assert np.array_equal(action.numpy(), data["action"][index])
                assert np.array_equal(COMMANDS[action.numpy()], data["commands"][clock])
                logp, _ = categorical_terms(logits, action)
                logp_error = float(np.abs(logp.numpy() - data["logp"][index]).max())
                maximum_logp_error = max(maximum_logp_error, logp_error)
                assert logp_error < 2e-6
                exact_argmax_rows += 5
                action_counts += np.bincount(action.numpy(), minlength=27)
                shadow_points, shadow_valid = current_only(points, valid)
                shadow_logits = model(torch.from_numpy(context), torch.from_numpy(shadow_points), torch.from_numpy(shadow_valid))
                assert np.abs(shadow_logits.numpy() - data["shadow_logits"][index]).max() < 2e-6
                shadow_action = shadow_logits.argmax(dim=-1).numpy()
                assert np.array_equal(shadow_action, data["shadow_action"][index])
                changes = []
                for agent, history in enumerate(histories):
                    trajectories = LocalController._trajectories(history.own)
                    changes.append(not np.array_equal(trajectories[int(action[agent])], trajectories[int(shadow_action[agent])]))
                assert np.array_equal(changes, data["shadow_executed_disagreement"][index])
                episode_shadow_changes += sum(changes)
            last[:] = data["commands"][clock]
        assert action_counts.tolist() == row["action_counts"]
        assert episode_shadow_changes == row["shadow_executed_disagreements"]
        shadow_motion_count += episode_shadow_changes
    assert len(worlds) == len(set(worlds.values())) == 32
    assert raw_bytes == summary["artifacts"]["raw_bytes"]
    assert lawful_input_rows == exact_argmax_rows == 61440
    groups = {}
    fields = ("J", "mean_served", "mean_sinr_quality", "min_served", "service_p10", "zero_service_steps", "mean_path_length_m", "xy_boundary_uav_steps")
    for arm, master, _seed in sorted(expected_keys, key=lambda key: (key[0], key[1] or 0, key[2])):
        name = arm if master is None else f"{arm}_{master}"
        if name in groups:
            continue
        selected = [r for r in summary["rows"] if r["arm"] == arm and r.get("master") == master]
        reading = {key: float(np.mean([r[key] for r in selected])) for key in fields}
        reading["minimum_world_mean_service"] = min(r["mean_served"] for r in selected)
        reading["zero_service_ticks_total"] = sum(r["zero_service_steps"] for r in selected)
        reading["absent_point_decisions"] = sum(r["absent_point_decisions"] for r in selected)
        if master is not None:
            reading["action_counts"] = np.sum([r["action_counts"] for r in selected], axis=0).tolist()
            reading["mean_categorical_entropy"] = float(np.mean([r["mean_categorical_entropy"] for r in selected]))
            reading["shadow_executed_disagreements"] = sum(r["shadow_executed_disagreements"] for r in selected)
        groups[name] = reading
    return dict(source_summary_sha256=hashlib.sha256(summary_content).hexdigest(),
                checks=dict(raw_files=256, raw_bytes=raw_bytes, checkpoints=6, independent_training_worlds=1536,
                            update_epochs=3072, distinct_common_eval_worlds=32, reconstructed_native_eval_steps=65536,
                            lawful_input_rows=lawful_input_rows, exact_checkpoint_argmax_rows=exact_argmax_rows,
                            max_reward_error=maximum_reward_error, max_logit_error=maximum_logit_error,
                            max_logp_error=maximum_logp_error, shadow_executed_disagreements=shadow_motion_count),
                fits=fit_readings, groups=groups,
                scope="Offline frozen-artifact verification only; no environment interaction, optimizer or added policy evaluation.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = read(args.run)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result["checks"], sort_keys=True))
