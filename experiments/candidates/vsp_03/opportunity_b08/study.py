"""Fixed G512 versus a fitted public finite-horizon opportunity rule."""

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.vsp_03.vsp03_b01.b01 import (
    objective, peak_rss, scales, vectors, write_json,
)
from experiments.candidates.vsp_03.vsp03_b02.b02 import (
    Model, action_tapes, difference, metrics, rollout, worlds,
)
from .opportunity import EndpointCounts, Planner, fit_model


SEEDS = (21801, 21802, 21803)
UPDATES = 512
TRAIN_BATCH = 128
EVAL_EPISODES = 4096
ARMS = ("G", "G_stochastic", "O", "R0", "R", "O_self", "O_known")
CONTRASTS = (("G", "O"), ("O", "R0"), ("G", "R0"), ("G", "R"),
             ("O", "O_self"), ("O_known", "O"), ("G_stochastic", "G"))


def activity_counter():
    return dict.fromkeys(("episodes_started", "episodes_completed", "team_ticks",
                          "target_transitions", "decision_rows",
                          "rollout_policy_forwards"), 0)


def annotate_rows(batch, phase):
    """Add observed events; none are labeled a counterfactual loss."""
    rows = batch["rows"]
    n = len(rows)
    extra = {name: np.zeros(n, dtype=np.int64) for name in (
        "expired_at_own_clock", "blocked_final_ready",
        "submit_blocks_partner_next_clock", "submit_blocks_partner_last_clock",
        "wait_when_ready", "submit_when_not_ready")}
    for event in batch["trace"]:
        t = event["t"]
        own = phase if t % 4 == 0 else 1 - phase
        ids = np.arange(n)
        extra["expired_at_own_clock"] += event["e_before"][ids, own]
        if t in (30, 32):
            extra["blocked_final_ready"] += event["blocked"] & event["b_before"][ids, own]
    x, action = batch["x"], batch["actions"].astype(bool)
    ids, ts = batch["episode_ids"], batch["times"]
    ready = x[:, 5] == 1
    partner_pending = x[:, 11] == 1
    last_partner_clock = np.where(x[:, 12] == 1, 32, 30)
    blocked_next = action & partner_pending & (ts < 32)
    blocked_last = blocked_next & (last_partner_clock >= ts + 2) & (last_partner_clock < ts + 8)
    for name, values in (
        ("submit_blocks_partner_next_clock", blocked_next),
        ("submit_blocks_partner_last_clock", blocked_last),
        ("wait_when_ready", ~action & ready),
        ("submit_when_not_ready", action & ~ready),
    ):
        np.add.at(extra[name], ids, values.astype(np.int64))
    for i, row in enumerate(rows):
        row.update({name: int(values[i]) for name, values in extra.items()})
        units = sum(j["units"] for j in row["jobs"])
        expected = sum(200 * j["success"] - 10 * j["attempt"] - j["waiting_ticks"]
                       for j in row["jobs"])
        if units != expected or units != int(batch["interval_units"][i].sum()):
            raise AssertionError("native accounting mismatch")
        if row["return"] != units / 400:
            raise AssertionError("team return mismatch")
    return rows, tuple(extra)


def save_panel(out, name, batch, phase):
    rows, extra_names = annotate_rows(batch, phase)
    write_json(out / f"{name}.json", rows)
    arrays = {key: batch[key] for key in
              ("x", "actions", "episode_ids", "times", "units", "interval_units")}
    np.savez_compressed(out / f"{name}_decisions.npz", **arrays)
    result = metrics(rows)
    result.update({name + "_per_team": float(np.mean([r[name] for r in rows]))
                   for name in extra_names})
    return rows, result


def artifact_hashes(out):
    return {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                     "bytes": p.stat().st_size}
            for p in sorted(out.iterdir()) if p.is_file() and p.name != "summary.json"}


def first_coupling_disagreements(joint, isolated, joint_rows, isolated_rows):
    """Read the first policy divergence, while paired histories are identical."""
    result = []
    for world in range(len(joint_rows)):
        left = np.flatnonzero(joint["episode_ids"] == world)
        right = np.flatnonzero(isolated["episode_ids"] == world)
        found = None
        for li, ri in zip(left, right):
            if joint["times"][li] != isolated["times"][ri] or not np.array_equal(
                    joint["x"][li], isolated["x"][ri]):
                raise AssertionError("histories differ before first policy action disagreement")
            la, ra = bool(joint["actions"][li]), bool(isolated["actions"][ri])
            if la != ra:
                if joint["x"][li, 11] != 1:
                    raise AssertionError("coupled and isolated decisions differ with one pending job")
                found = {"t": int(joint["times"][li]), "public_x": joint["x"][li].tolist(),
                         "direction": "joint_SUBMIT_self_WAIT" if la else "joint_WAIT_self_SUBMIT"}
                break
        if found is None and len(left) != len(right):
            raise AssertionError("observation stream lengths differ without policy divergence")
        result.append({"world": world, "first_disagreement": found,
                       "complete_world_J_difference": joint_rows[world]["return"] - isolated_rows[world]["return"]})
    return result


def train_and_evaluate(seed, out, launch_sha):
    """One independent block, with O estimated only from G's training observations."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    train_activity, eval_activity = activity_counter(), activity_counter()
    summary = {
        "seed": seed, "launch_sha": launch_sha, "status": "incomplete",
        "fits_started": {"G": 0, "O": 0}, "fits_completed": {"G": 0, "O": 0},
        "training": train_activity, "evaluation": eval_activity, "optimizer_steps": 0,
        "training_gradient_rows": 0, "evaluation_optimizer_steps": 0,
        "primary_name": "final512:G-O", "arms": {},
    }
    try:
        summary["fits_started"]["G"] = 1
        model = Model(seed, "G")
        initial = vectors(model)
        summary["initial"] = scales(model, initial)
        counts = EndpointCounts()
        optimizer = torch.optim.Adam(model.parameters(), lr=.001, betas=(.9, .999),
                                     eps=1e-8, weight_decay=0)
        fit_start = time.perf_counter()
        with (out / "G_curve.jsonl").open("w", encoding="utf-8") as curve:
            for update in range(1, UPDATES + 1):
                first = (update - 1) * TRAIN_BATCH
                draws, phase = worlds(seed, 100, first, TRAIN_BATCH)
                batch = rollout(draws, phase, model,
                                action_tapes(seed, 100, 0, 1, first, TRAIN_BATCH),
                                activity=train_activity)
                # The fitted rule receives exactly the public packed observation stream.
                counts.add_batch({k: batch[k] for k in ("x", "episode_ids", "times")})
                loss, info = objective(model, batch, update)
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
                summary["optimizer_steps"] += 1
                summary["training_gradient_rows"] += batch["decision_rows"]
                curve.write(json.dumps({"update": update, **info, **metrics(batch["rows"]),
                                        "gradient_rows": batch["decision_rows"]}, allow_nan=False) + "\n")
                if update in (1, 128, 512):
                    curve.flush()
                    summary[f"scale_{update}"] = scales(model, initial)
                    print(json.dumps({"seed": seed, "stage": "G", "update": update,
                                      "wall_s": time.perf_counter() - wall_start}), flush=True)
        summary["G_fit_wall_s_including_observation_collection"] = time.perf_counter() - fit_start
        summary["fits_completed"]["G"] = 1
        state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        torch.save(state, out / "G_512.pt")
        saved = torch.load(out / "G_512.pt", map_location="cpu", weights_only=True)
        if not all(torch.equal(state[k], saved[k]) for k in state):
            raise AssertionError("G weight readback mismatch")

        summary["fits_started"]["O"] = 1
        fit_start = time.perf_counter()
        fitted = fit_model(counts)
        summary["O_fit_wall_s"] = time.perf_counter() - fit_start
        summary["fitted_model"] = fitted
        write_json(out / "fitted_model.json", fitted)
        np.savez_compressed(out / "public_endpoint_counts.npz", counts=counts.counts)
        if not fitted["metadata"]["success"]:
            raise RuntimeError("O likelihood fit did not converge: " + fitted["metadata"]["message"])
        summary["fits_completed"]["O"] = 1
        plan_start = time.perf_counter()
        planner = Planner(fitted["c"], fitted["p"])
        known = Planner(4., .5)
        summary["planning_wall_s_both_models"] = time.perf_counter() - plan_start
        summary["initial_expected_J"] = {
            "O_under_fitted_law": float(planner.joint[0, 1, 1] / 400),
            "O_known_under_true_law": float(known.joint[0, 1, 1] / 400),
        }
        np.savez_compressed(out / "planner_tables.npz", even_clocks=np.arange(0, 33, 2),
                            fitted_solo=planner.solo[::2], fitted_joint=planner.joint[::2],
                            known_solo=known.solo[::2], known_joint=known.joint[::2])
        summary["model_rights"] = {
            "O": "estimated c,p; public G training endpoints only; declared age-Markov family",
            "O_self": "same fitted model; isolated-job recursion ignoring reciprocal slot interaction",
            "O_known": "EXTRA_MODEL_KNOWLEDGE: true c=4,p=.5; diagnostic only",
        }

        # Evaluation worlds are first constructed after fitting and final weight freezing.
        draws, phase = worlds(seed, 200, 0, EVAL_EPISODES)
        uniforms = action_tapes(seed, 200, 1, 1, 0, EVAL_EPISODES)
        np.savez_compressed(out / "evaluation_worlds.npz", draws=draws, phase=phase,
                            stochastic_uniforms=uniforms)
        panels, coupling_batches = {}, {}
        for name in ARMS:
            panel_start = time.perf_counter()
            kwargs = dict(activity=eval_activity, trace=True)
            if name in ("G", "G_stochastic"):
                kwargs.update(model=model, uniforms=uniforms if name == "G_stochastic" else None)
            elif name in ("R0", "R"):
                kwargs["rule"] = name
            else:
                selected = known if name == "O_known" else planner
                mode = "self" if name == "O_self" else "joint"
                kwargs["scripted"] = lambda ids, t, own, x, p=selected, m=mode: p.actions(x, mode=m)
            batch = rollout(draws, phase, **kwargs)
            rows, absolute = save_panel(out, name, batch, phase)
            panels[name] = rows
            if name in ("O", "O_self"):
                coupling_batches[name] = {k: batch[k] for k in ("x", "actions", "episode_ids", "times")}
            summary["arms"][name] = {**absolute, "panel_wall_s": time.perf_counter() - panel_start}
        disagreements = first_coupling_disagreements(coupling_batches["O"], coupling_batches["O_self"],
                                                     panels["O"], panels["O_self"])
        write_json(out / "first_coupling_disagreements.json", disagreements)
        summary["coupling_activation"] = {
            "first_disagreement_worlds": sum(r["first_disagreement"] is not None for r in disagreements),
            **{direction: sum(r["first_disagreement"] is not None and
                             r["first_disagreement"]["direction"] == direction for r in disagreements)
               for direction in ("joint_SUBMIT_self_WAIT", "joint_WAIT_self_SUBMIT")},
        }
        if not all(torch.equal(state[k], model.state_dict()[k]) for k in state):
            raise AssertionError("evaluation changed G weights")
        summary["comparisons"] = {a + "-" + b: difference(panels[a], panels[b]) for a, b in CONTRASTS}
        summary["primary"] = summary["comparisons"]["G-O"]
        write_json(out / "paired_differences.json", [
            {"world": i, "phase": int(phase[i]), **{
                a + "-" + b: panels[a][i]["return"] - panels[b][i]["return"] for a, b in CONTRASTS}}
            for i in range(EVAL_EPISODES)])
        assert train_activity["episodes_completed"] == UPDATES * TRAIN_BATCH
        assert summary["optimizer_steps"] == UPDATES
        assert eval_activity["episodes_completed"] == len(ARMS) * EVAL_EPISODES
        summary["status"] = "complete"
    except Exception as exc:
        summary["error"] = repr(exc)
        raise
    finally:
        summary["block_wall_s_through_publication_start"] = time.perf_counter() - wall_start
        summary["block_cpu_s"] = time.process_time() - cpu_start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "research process lifetime maximum, not block increment"
        summary["artifacts"] = artifact_hashes(out)
        if write_json(out / "summary.json", summary) != summary:
            raise AssertionError("summary readback mismatch")
    return summary


def across_blocks(blocks):
    result = {}
    for a, b in CONTRASTS:
        key = a + "-" + b
        values = np.array([block["comparisons"][key]["mean"] for block in blocks])
        sd = float(values.std(ddof=1))
        se = sd / math.sqrt(len(values))
        # Three independent paired training/data blocks; episodes are nested observations.
        half = 4.302652729911275 * se
        result[key] = {"per_block": values.tolist(), "mean": float(values.mean()),
                       "between_block_sd": sd, "independent_blocks": len(values),
                       "descriptive_t95": [float(values.mean() - half), float(values.mean() + half)],
                       "interval_assumption": "independent approximately normal block contrasts; n=3"}
    return result


def run(out, launch_sha, seeds=SEEDS):
    if tuple(seeds) != SEEDS:
        raise ValueError("B08 has exactly the three prospectively fixed independent blocks")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    config = {"object": "VSP03_OPPORTUNITY_B08", "seeds": list(seeds), "launch_sha": launch_sha,
              "training_updates": UPDATES, "episodes_per_update": TRAIN_BATCH,
              "evaluation_episodes_per_arm_per_block": EVAL_EPISODES, "arms": list(ARMS),
              "planned_fits": 6, "G_fits": 3, "O_transition_model_fits": 3,
              "planned_unique_training_episodes": 3 * UPDATES * TRAIN_BATCH,
              "planned_evaluation_episodes": 3 * len(ARMS) * EVAL_EPISODES,
              "planned_team_ticks": 3 * (UPDATES * TRAIN_BATCH + len(ARMS) * EVAL_EPISODES) * 40,
              "threads": 1, "device": "cpu", "G_dtype": "float32", "O_dtype": "float64",
              "selection": "none; G final512; one fixed model family and optimizer; no score selection"}
    write_json(out / "config.json", config)
    summary = {**config, "status": "incomplete", "blocks": [], "technical_failures": []}
    start = time.perf_counter()
    try:
        for seed in seeds:
            try:
                block = train_and_evaluate(seed, out / str(seed), launch_sha)
                summary["blocks"].append(block)
                print(json.dumps({"seed": seed, "status": "complete", "primary": block["primary"]}), flush=True)
            except Exception as exc:
                summary["technical_failures"].append({"seed": seed, "error": repr(exc)})
                raise
        summary["comparisons"] = across_blocks(summary["blocks"])
        summary["status"] = "complete"
    finally:
        summary["study_wall_s_through_publication_start"] = time.perf_counter() - start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "single research process lifetime maximum"
        retained_blocks = [json.loads((out / str(seed) / "summary.json").read_text())
                           for seed in seeds if (out / str(seed) / "summary.json").exists()]
        summary["fits_started"] = {arm: sum(b["fits_started"][arm] for b in retained_blocks)
                                   for arm in ("G", "O")}
        summary["fits_completed"] = {arm: sum(b["fits_completed"][arm] for b in retained_blocks)
                                     for arm in ("G", "O")}
        write_json(out / "summary.json", summary)
    return summary
