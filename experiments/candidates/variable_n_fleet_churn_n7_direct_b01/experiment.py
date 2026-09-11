"""B01 paired learning, fixed evaluations and readable native-return publication."""

import json
import math
from time import perf_counter

import torch

from . import learning
from .native import Batch, build

METRICS = ("R_fail_60", "U_total", "U_intact", "J_ext")


def checkpoint(out, arm, label, model, optimizer, round_index):
    started = perf_counter()
    path = out / f"{arm}_{label}.pt"
    state = dict(arm=arm, checkpoint=label, round=round_index,
                 model_state=model.state_dict(), optimizer_state=optimizer.state_dict(),
                 dtype="float64", device="cpu", presentation="R02 canonical opaque rank")
    torch.save(state, path)
    restored = torch.load(path, map_location="cpu", weights_only=True)
    count = sum(value.numel() for value in restored["model_state"].values())
    if count != sum(p.numel() for p in model.parameters()) or restored["round"] != round_index:
        raise AssertionError("checkpoint readback count/round differs")
    return dict(path=path.name, parameters=count, round=round_index,
                bytes=path.stat().st_size, seconds=perf_counter() - started)


def bcrh(library, fixtures):
    started = perf_counter()
    checks = 0
    with Batch(library, fixtures) as batch:
        rows = batch.initial
        contexts = [[] for _ in fixtures]
        for epoch in range(6):
            for index, (row, fixture) in enumerate(zip(rows, fixtures)):
                trace, zone = row["next_observation"], fixture.failed_zone - 1
                contexts[index].append(dict(time=20 * epoch,
                    failed_zone_delivery_observed=2 * trace["zone_rows"][zone * 15 + 11],
                    failed_executor_state=trace["token_state"][zone * 2]))
            choices = batch.bcrh(include_candidate_records=False)
            for choice in choices:
                if not (choice["scorer_checker_equal"] and choice["independent_enumerator_equal"]):
                    raise AssertionError("fixed BCRH controller/checker disagreement")
                checks += 1
            rows = batch.step([row["scorer_command"] for row in choices])
        episodes = [dict(learning.terminal_metrics(row), zone=fixture.failed_zone, world=index,
                         recovery_observations_20s=contexts[index], arm="BCRH", checkpoint="fixed")
                    for index, (row, fixture) in enumerate(zip(rows, fixtures))]
    return episodes, dict(seconds=perf_counter() - started, episodes=len(fixtures),
                          complete_bcrh_calls=checks, joint_decisions=6 * len(fixtures))


def describe(values):
    n = len(values)
    mean = sum(values) / n
    return dict(n=n, mean=mean, standard_error=math.sqrt(
        sum((value - mean) ** 2 for value in values) / (n - 1) / n) if n > 1 else None,
        minimum=min(values), maximum=max(values))


def readout(evaluations):
    indexed = {(row["arm"], row["checkpoint"], row["world"]): row for row in evaluations}
    identities = sorted({row["world"] for row in evaluations})
    pairs = [(f"{arm}_final_minus_initial", (arm, "final"), (arm, "initial")) for arm in ("MAPR", "DIRECT")]
    pairs += [("MAPR_minus_DIRECT", ("MAPR", "final"), ("DIRECT", "final"))]
    pairs += [(f"{arm}_minus_BCRH", (arm, "final"), ("BCRH", "fixed")) for arm in ("MAPR", "DIRECT")]
    contrasts = []
    for name, left, right in pairs:
        differences = [dict(world=world, zone=indexed[(*left, world)]["zone"],
                            **{metric: indexed[(*left, world)][metric] - indexed[(*right, world)][metric]
                               for metric in METRICS}) for world in identities]
        contrasts.append(dict(name=name, paired_episodes=differences,
            strata={str(zone): {metric: describe([row[metric] for row in differences
                    if zone == "all" or row["zone"] == zone]) for metric in METRICS}
                    for zone in ("all", 1, 2)}))
    means = []
    for arm, label in sorted({(row["arm"], row["checkpoint"]) for row in evaluations}):
        rows = [row for row in evaluations if (row["arm"], row["checkpoint"]) == (arm, label)]
        means.append(dict(arm=arm, checkpoint=label, strata={str(zone): {
            metric: describe([row[metric] for row in rows if zone == "all" or row["zone"] == zone])
            for metric in METRICS} for zone in ("all", 1, 2)}))
    return dict(means=means, contrasts=contrasts, primary_checkpoint="final", primary_metric="R_fail_60",
                uncertainty="episode-level conditional descriptive SE; one training seed cannot estimate training-seed population uncertainty",
                exact_recovery_latencies="unavailable: observations have20s resolution; not inferred",
                mei_absolute=0.10)


def publish_json(path, data):
    started = perf_counter()
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    restored = json.loads(path.read_text(encoding="utf-8"))
    return restored, perf_counter() - started


def cost_projection(config, setup, generations, training, evaluation_times, bcrh_time,
                    publication, evaluation_worlds, other_overhead):
    scale = max(64 / config["rounds"], 64 / config["eval_episodes"])
    terms = dict(shared_setup=setup, shared_training_worlds=64 * max(generations),
                 evaluation_world_generation=64 * evaluation_worlds / config["eval_episodes"],
                 other_measured_overhead=scale * other_overhead)
    per_arm = {}
    for arm in ("MAPR", "DIRECT"):
        rows = [row for row in training if row["arm"] == arm]
        evals = [row for row in evaluation_times if row["arm"] == arm]
        units = dict(collect_episode=max(row["collection_seconds"] / row["episodes"] for row in rows),
                     update_round=max(row["update"]["seconds"] for row in rows),
                     eval_episode=max(row["seconds"] / row["episodes"] for row in evals))
        amount = 2048 * units["collect_episode"] + 64 * units["update_round"] + 192 * units["eval_episode"]
        per_arm[arm] = dict(unit_seconds=units, projected_seconds=amount)
        terms[arm] = amount
    terms["fixed_BCRH"] = 64 * bcrh_time["seconds"] / bcrh_time["episodes"]
    actual_rows = 2 * config["rounds"] * 32 + 7 * config["eval_episodes"]
    terms["publication"] = publication * max(1, (4096 + 448) / actual_rows)
    return dict(terms_seconds=terms, per_arm=per_arm, projected_complete_seconds=sum(terms.values()),
                cap_seconds=2700, source="maximum observed unit wall; full/check publication row-ratio scaling includes all six checkpoints",
                formula="shared + sum(2048*collect_episode+64*update_round+192*eval_episode) +64*BCRH_episode+publication",
                limitation="planning estimate from selected N7 sizes; no performance guarantee or additional benchmark")


def run(config, out, launch_sha, started):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    library = build(out)
    models, optimizers = learning.initialize(config["seed"], config["namespace"])
    initial = {arm: {name: p.detach().clone() for name, p in model.named_parameters()}
               for arm, model in models.items()}
    initial_stats = {arm: learning.parameter_state(model) for arm, model in models.items()}
    world_start = perf_counter()
    panel = learning.worlds(config["eval_seed"], config["namespace"], "evaluation", config["eval_episodes"])
    evaluation_world_seconds = perf_counter() - world_start
    setup_seconds = perf_counter() - started - evaluation_world_seconds
    evaluations, bcrh_time = bcrh(library, panel)
    curves, episode_rows, eval_times, checkpoints, generations = [], [], [], [], []
    publication_seconds = 0.0
    midpoint = config["rounds"] // 2
    for completed in range(config["rounds"] + 1):
        if completed in (0, midpoint, config["rounds"]):
            label = "initial" if completed == 0 else ("final" if completed == config["rounds"] else "midpoint")
            for arm, model in models.items():
                item = checkpoint(out, arm, label, model, optimizers[arm], completed)
                checkpoints.append(dict(arm=arm, checkpoint=label, **item))
                publication_seconds += item["seconds"]
                result = learning.rollout(library, panel, model, arm, config["namespace"], None, completed, False,
                    check_presentation=config["profile"] == "engineering-check" and completed == 0)
                evaluations.extend(dict(row, arm=arm, checkpoint=label) for row in result["episodes"])
                eval_times.append(dict(arm=arm, checkpoint=label, episodes=len(panel), seconds=result["seconds"],
                                       model_forward_calls=result["model_forward_calls"],
                                       checks=result["checks"], residual=result["residual"]))
        if completed == config["rounds"]:
            break
        generation_start = perf_counter()
        fixtures = learning.worlds(config["seed"], config["namespace"], "training", 32, completed)
        generations.append(perf_counter() - generation_start)
        for arm, model in models.items():
            action_source = learning.rng(config["seed"], config["namespace"], f"actions/{arm}")
            result = learning.rollout(library, fixtures, model, arm, config["namespace"], action_source, completed, True)
            update = learning.update(model, optimizers[arm], result, config["seed"], config["namespace"], arm, completed)
            motion = learning.parameter_state(model, initial[arm])
            curves.append(dict(arm=arm, round=completed + 1, episodes=len(fixtures), joint_transitions=len(result["records"]),
                collection_seconds=result["seconds"], update=update, parameters=motion,
                model_forward_calls=result["model_forward_calls"],
                residual=result["residual"], checks=result["checks"],
                training_means={metric: sum(row[metric] for row in result["episodes"]) / len(fixtures) for metric in METRICS}))
            episode_rows.extend(dict(row, arm=arm, round=completed + 1) for row in result["episodes"])
            print(json.dumps(dict(arm=arm, round=completed + 1, actual_transitions=len(result["records"]),
                                  optimizer_steps=update["optimizer_steps"], parameters=motion)), flush=True)
    exposure = {arm: dict(training_instances=1, rounds=sum(row["arm"] == arm for row in curves),
        training_episodes=sum(row["episodes"] for row in curves if row["arm"] == arm),
        joint_transitions=sum(row["joint_transitions"] for row in curves if row["arm"] == arm),
        optimizer_steps=sum(row["update"]["optimizer_steps"] for row in curves if row["arm"] == arm),
        backward_calls=sum(row["update"]["backward_calls"] for row in curves if row["arm"] == arm),
        collection_forward_calls=sum(row["model_forward_calls"] for row in curves if row["arm"] == arm),
        optimizer_forward_calls=sum(row["update"]["optimizer_forward_calls"] for row in curves if row["arm"] == arm),
        optimizer_forward_decisions=sum(row["update"]["optimizer_forward_decisions"] for row in curves if row["arm"] == arm),
        evaluation_forward_calls=sum(row["model_forward_calls"] for row in eval_times if row["arm"] == arm),
        evaluation_episodes=sum(row["episodes"] for row in eval_times if row["arm"] == arm),
        initial_parameters=initial_stats[arm], final_parameters=learning.parameter_state(models[arm], initial[arm]))
        for arm in models}
    for arm in exposure:
        if exposure[arm]["optimizer_steps"] != config["rounds"] * 32:
            raise AssertionError("actual matched PPO exposure differs")
    publication_started = perf_counter()
    checkpoint_seconds = publication_seconds
    for filename, content in (("training_episodes.json", episode_rows), ("evaluation_episodes.json", evaluations),
                              ("training_curves.json", curves)):
        restored, seconds = publish_json(out / filename, content)
        if len(restored) != len(content):
            raise AssertionError("episode/curve publication readback count differs")
        publication_seconds += seconds
    summary = dict(object="VNFC-N7-DIRECT-RETURN-B01", launch_sha=launch_sha, config=config,
        training_seed_count=1, dtype="float64", device="cpu", torch_threads=1, native_threads=1,
        rng_domains="fresh addressed HMAC; paired exogenous-worlds; shared homologous initialization; arm-specific actions/minibatches; separate evaluation master",
        initial_parameters=initial_stats, exposure=exposure, checkpoints=checkpoints,
        initialization_scales=dict(hidden_stiefel_gain=math.sqrt(2), output_gain=0.01,
                                   token_embedding_gain=1.0, initial_direct_residual_output=0.0),
        readout=readout(evaluations), timings=dict(shared_setup=setup_seconds, world_generation=generations,
            evaluation=eval_times, evaluation_world_generation=evaluation_world_seconds,
            bcrh=bcrh_time, publication=publication_seconds),
        total_native_ticks=240 * (len(episode_rows) + len(evaluations)))
    summary["cost_projection"] = None  # Filled after the first complete publication/readback is timed.
    try:
        import resource
        summary["peak_rss_main_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except (ImportError, OSError):
        summary["peak_rss_main_bytes"] = None
        summary["resources_unmeasured"] = True
    summary["wall_before_summary_seconds"] = perf_counter() - started
    restored, summary_seconds = publish_json(out / "summary.json", summary)
    if restored["exposure"] != exposure:
        raise AssertionError("summary exposure readback differs")
    publication_seconds = checkpoint_seconds + perf_counter() - publication_started
    summary["timings"]["publication"] = publication_seconds
    accounted = setup_seconds + evaluation_world_seconds + sum(generations) + bcrh_time["seconds"]
    accounted += sum(row["collection_seconds"] + row["update"]["seconds"] for row in curves)
    accounted += sum(row["seconds"] for row in eval_times) + publication_seconds
    other_overhead = perf_counter() - started - accounted
    summary["timings"]["other_measured_overhead"] = other_overhead
    summary["timings"]["other_overhead_scope"] = "parameter/curve/exposure bookkeeping, progress output and untimed wrappers; scaled by max round/evaluation ratio"
    summary["cost_projection"] = cost_projection(config, setup_seconds, generations, curves,
        eval_times, bcrh_time, publication_seconds, evaluation_world_seconds, other_overhead)
    summary["cost_projection"]["final_summary_write_scope"] = "final stdout adds this replacement write/readback cost"
    # Publish the measured cost of the complete artifact construction/readback.
    # The final stdout wall additionally includes this small summary replacement.
    _, final_summary_seconds = publish_json(out / "summary.json", summary)
    final_projection = cost_projection(config, setup_seconds, generations, curves,
        eval_times, bcrh_time, publication_seconds + final_summary_seconds,
        evaluation_world_seconds, other_overhead)
    complete_wall = perf_counter() - started
    final = dict(summary=str(out / "summary.json"), complete_wall_seconds=complete_wall,
                 summary_publication_seconds=summary_seconds + final_summary_seconds, wall_cap_seconds=config["wall_cap"],
                 within_wall_cap=complete_wall <= config["wall_cap"], exposure=exposure,
                 projected_complete_seconds=final_projection["projected_complete_seconds"],
                 complete_projection=final_projection)
    print(json.dumps(final), flush=True)
    return final
