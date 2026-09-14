"""Offline B02 intake arithmetic from the archived, completed fixed pair only."""
import csv
import json
import math
from pathlib import Path
import statistics


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    folder = Path(__file__).resolve().parent
    summary = read(folder / "raw/summary.json")
    episodes = [json.loads(x) for x in (folder / "raw/episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    rollouts = [json.loads(x) for x in (folder / "raw/rollouts.jsonl").read_text(encoding="utf-8").splitlines()]
    assert summary["complete"] and summary["object"] == "LCAC_B02_1024" and summary["seed"] == 9412
    assert summary["launch_sha"] == "25ea4d61c0e1f2484da77f4bc1851e17cdc8eb4a"
    assert summary["seed_offsets"] == dict(actor_init=11, critic_init=12, train_reset=1000,
                                           eval_reset=3000, train_action=10000, eval_action=20000)
    result = dict(unit="one independent1024-endpoint matched training pair; master9412", arms={})
    panels = {}
    for arm in ("V", "Q"):
        measured = summary["arms"][arm]
        assert measured["complete"]
        for phase, n, reset, action in (("train", 1024, 1000, 10000), ("eval", 32, 3000, 20000)):
            rows = sorted((r for r in episodes if r["arm"] == arm and r["phase"] == phase), key=lambda r: r["episode"])
            assert [r["episode"] for r in rows] == list(range(n))
            assert all(r["steps"] == 256 and math.isfinite(r["J"]) and math.isfinite(r["reward_sum"])
                       and abs(r["J"] * 256 - r["reward_sum"]) < 1e-9
                       and r["reset_seed"] == 941200000 + reset + r["episode"]
                       and r["action_seed"] == 941200000 + action + r["episode"] for r in rows)
            if phase == "eval":
                panels[arm] = rows
        expected = dict(constructors=1, constructor_resets=1, explicit_resets=1056,
                        step_calls=270336, native_transitions=270336, train_steps=262144,
                        eval_steps=8192, train_episodes=1024, eval_episodes=32,
                        action_draws=1351680, rollouts=512, optimizer_steps=2048,
                        q_baseline_rows=9175040 if arm == "Q" else 0,
                        v_baseline_rows=262144 if arm == "V" else 0, critic_fit_rows=1048576)
        assert measured["counts"] == expected
        records = [r for r in rollouts if r["arm"] == arm]
        assert [r["rollout"] for r in records] == list(range(512))
        assert all(r["optimizer_steps"] == 4 and r["team_training_rows"] == 512 and len(r["epochs"]) == 4 for r in records)
        epochs = [e for r in records for e in r["epochs"]]
        train = [r["J"] for r in episodes if r["arm"] == arm and r["phase"] == "train"]
        result["arms"][arm] = dict(
            counts=measured["counts"], movement=measured["training_exposure"],
            arm_body_wall_seconds=measured["arm_body_wall_seconds"],
            training_scores=dict(first32_mean=statistics.mean(train[:32]), last32_mean=statistics.mean(train[-32:]),
                                 limit="changing training worlds and policies; not evaluation learning gain"),
            residuals={key: dict(first16_mean=statistics.mean(r[key] for r in records[:16]),
                                 last16_mean=statistics.mean(r[key] for r in records[-16:]), last=records[-1][key])
                       for key in ("prefit_residual_mean", "prefit_residual_mse")},
            epoch_extrema={key: dict(min=min(e[key] for e in epochs), max=max(e[key] for e in epochs), last=epochs[-1][key])
                           for key in ("actor_preclip_norm", "critic_preclip_norm", "value_loss", "entropy")},
            rollouts_with_movement={block: sum(r["movement"][block]["displacement"] > 0 for r in records) for block in ("actor", "critic")})
    differences = [q["J"] - v["J"] for v, q in zip(panels["V"], panels["Q"])]
    assert differences == summary["primary"]["differences"]
    assert statistics.mean(differences) == summary["primary"]["delta"]
    assert len(episodes) == 2112 and len(rollouts) == 1024
    result["checks"] = dict(all2112_episodes_units_and_seeds=True, all1024_rollouts=True,
                             exact_per_arm_counts=True, all32_primary_recomputed=True)
    result["primary"] = summary["primary"]
    result["final_worlds"] = [dict(episode=i, V=v["J"], Q=q["J"], difference=d)
                              for i, (v, q, d) in enumerate(zip(panels["V"], panels["Q"], differences))]
    result["cost"] = read(folder / "raw/runner_time.json")
    result["cost"].update(peak_rss_mib=result["cost"]["peak_rss_kib"] / 1024,
                          shared_setup_wall_seconds=summary["shared_setup_wall_seconds"],
                          unassigned_startup_publication_exit_seconds=result["cost"]["wall_seconds"] - summary["elapsed_to_summary_start_seconds"],
                          cpu_seconds=None, total_support_provider_lifetime="UNKNOWN")
    (folder / "ANALYSIS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with (folder / "RUN_SCORES.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["task", "seed", "arm", "score"])
        for arm in ("V", "Q"):
            writer.writerow(["LCAC_B02_1024", 9412, arm, statistics.mean(r["J"] for r in panels[arm])])
    print(json.dumps({k: v for k, v in result.items() if k != "final_worlds"}, indent=2))


if __name__ == "__main__":
    main()
