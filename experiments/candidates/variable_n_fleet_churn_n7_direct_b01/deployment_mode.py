"""Fixed-policy deployment-mode evaluation of the four saved B01 final policies.

Zero training: no optimizer, no parameter update, no new learner.  The four checkpoints are
frozen inputs; the two treatments are the two decoding branches that already exist in the shared
R09 forward (`uniforms is None` greedy maximum, inverse-CDF masked-categorical sample).
"""

import hashlib
import json
from pathlib import Path
from time import perf_counter

import torch

from . import experiment, learning
from .native import build
from ..variable_n_fleet_churn_bpcr_r09.torch_models import direct_parameter_shapes, mapr_parameter_shapes

RECORDS = ("b01_formal_20260905_02", "b01_seed02_20260905_01")
ARMS = ("MAPR", "DIRECT")
MODES = ("GREEDY", "SAMPLE")

# The R09 coordinate registry (`empirical_contract.DOMAIN_LABELS`) is a read-only reuse input and
# carries no evaluation-action label, so this registered conclusion-family label - unused anywhere
# in the B01 path - is the domain separation tag for the evaluation action draws.  Stream
# independence itself comes from the dedicated action master and the `eval-actions/...` stream:
# no coordinate, master or purpose is shared with the training `training/action` draws.
EVALUATION_ACTION_DOMAIN = "conclusion/cut-derangement"

CHECKPOINT_DIGESTS = {
    ("b01_formal_20260905_02", "MAPR"): "1b36ccb40cdfd9e91433ed3c73b656492130ce00bfd0ee1bd7ddfd320c312971",
    ("b01_formal_20260905_02", "DIRECT"): "326cb831b924ddc456931fdafa0cc1381eb956bb63a52d1b8c56a3054cd461d2",
    ("b01_seed02_20260905_01", "MAPR"): "e8dd2494436b1c6831fc0c541e745747024c67755524e0b54a4ddc9cad15d098",
    ("b01_seed02_20260905_01", "DIRECT"): "6da2ae47ec8a33f5608844b9b3d496b65236d0dc165747858808c0136245e019",
}
REFERENCE_FIELDS = ("R_fail_60", "U_total", "U_intact", "J_ext", "fail_endpoint", "total_endpoint",
                    "intact_endpoint", "safety_violation", "exclusivity_violation", "event_count",
                    "integrated_ticks", "zone")


def checkpoint_path(root, record, arm):
    return Path(root) / record / "checkpoints" / f"{arm}_final.pt"


def placeholder_parameters(arm):
    """Exact-shape finite float64 CPU tensors, the explicit-parameter constructor's contract."""
    shapes = mapr_parameter_shapes() if arm == "MAPR" else direct_parameter_shapes()
    return {name: torch.zeros(shape, dtype=torch.float64) for name, shape in shapes.items()}


def load_checkpoint(path, arm, expected_sha256=None, expected_round=64):
    path = Path(path)
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise AssertionError(f"frozen checkpoint digest differs: {path}")
    state = torch.load(path, map_location="cpu", weights_only=True)
    if state["arm"] != arm or state["checkpoint"] != "final" or state["round"] != expected_round:
        raise AssertionError(f"checkpoint arm/label/round differs: {path}")
    if state["dtype"] != "float64" or state["device"] != "cpu":
        raise AssertionError(f"checkpoint dtype/device differs: {path}")
    model = (learning.MAPR if arm == "MAPR" else learning.Direct)(placeholder_parameters(arm))
    model.load_state_dict(state["model_state"], strict=True)
    if arm == "DIRECT":
        model.residual_observation = None
    parameters = sum(p.numel() for p in model.parameters())
    if parameters != sum(value.numel() for value in state["model_state"].values()):
        raise AssertionError(f"loaded parameter count differs: {path}")
    if any(p.dtype != torch.float64 or p.device.type != "cpu" for p in model.parameters()):
        raise AssertionError(f"loaded parameters are not CPU binary64: {path}")
    meta = dict(arm=arm, checkpoint=state["checkpoint"], round=state["round"], path=str(path),
                sha256=digest, bytes=len(payload), parameters=parameters,
                presentation=state["presentation"], optimizer_state_loaded=False)
    return model, meta


def evaluation_uniform_supplier(seed, namespace, record, arm, fixtures, counter):
    """One masked-categorical uniform per token per episode, from a dedicated evaluation stream."""
    source = learning.rng(seed, namespace, f"eval-actions/{record}/{arm}")
    purpose = f"eval-action/{record}/{arm}"
    scale = float(1 << 64)

    def supplier(epoch):
        block = []
        for index, fixture in enumerate(fixtures):
            row = []
            for token in range(4):
                address = learning.coordinate(namespace, EVALUATION_ACTION_DOMAIN, purpose, 0, index,
                                              fixture.failed_zone, 20 * epoch, token)
                row.append((source.word(address, now=None) + .5) / scale)
                counter["draws"] += 1
            block.append(row)
        return torch.tensor(block, dtype=torch.float64)

    return supplier


def grid_readout(rows, bcrh_rows):
    """Paired contrasts over the policy x mode grid; `readout` stays the B01 six-cell readout."""
    metrics = experiment.METRICS
    indexed = {(row["record"], row["arm"], row["mode"], row["world"]): row for row in rows}
    reference = {row["world"]: row for row in bcrh_rows}
    identities = sorted({row["world"] for row in rows})
    pairs = [(f"{record}/{arm}_SAMPLE_minus_GREEDY", (record, arm, "SAMPLE"), (record, arm, "GREEDY"))
             for record in RECORDS for arm in ARMS]
    pairs += [(f"{record}/MAPR_minus_DIRECT_{mode}", (record, "MAPR", mode), (record, "DIRECT", mode))
              for record in RECORDS for mode in MODES]
    pairs += [(f"{record}/{arm}_{mode}_minus_BCRH", (record, arm, mode), None)
              for record in RECORDS for arm in ARMS for mode in MODES]
    contrasts = []
    for name, left, right in pairs:
        differences = []
        for world in identities:
            first = indexed[(*left, world)]
            second = reference[world] if right is None else indexed[(*right, world)]
            differences.append(dict(world=world, zone=first["zone"],
                                    **{metric: first[metric] - second[metric] for metric in metrics}))
        contrasts.append(dict(name=name, paired_episodes=differences,
            strata={str(zone): {metric: experiment.describe([row[metric] for row in differences
                    if zone == "all" or row["zone"] == zone]) for metric in metrics}
                    for zone in ("all", 1, 2)}))
    means = []
    for cell in sorted({(row["record"], row["arm"], row["mode"]) for row in rows}) + [("BCRH", "BCRH", "fixed")]:
        selected = bcrh_rows if cell[0] == "BCRH" else [row for row in rows
                   if (row["record"], row["arm"], row["mode"]) == cell]
        means.append(dict(record=cell[0], arm=cell[1], mode=cell[2], strata={str(zone): {
            metric: experiment.describe([row[metric] for row in selected if zone == "all" or row["zone"] == zone])
            for metric in metrics} for zone in ("all", 1, 2)}))
    primary = {name: contrast["strata"]["all"]["R_fail_60"]["mean"] for name, contrast in
               zip([pair[0] for pair in pairs], contrasts) if name.endswith("SAMPLE_minus_GREEDY")}
    return dict(means=means, contrasts=contrasts, primary_metric="R_fail_60",
                primary_contrast_means=primary, mei_absolute=0.10,
                uncertainty="episode-level conditional descriptive SE over one shared panel; modes and "
                            "episodes are not independent training seeds",
                exact_recovery_latencies="unavailable: observations have 20s resolution; not inferred")


def b01_greedy_replay(library, config, checkpoint_root, reference_path):
    """Greedy-path equality against the recorded B01 formal02 evaluation rows on its own panel."""
    started = perf_counter()
    payload = Path(reference_path).read_bytes()
    reference = json.loads(payload.decode("utf-8"))
    record, arm = config["reference_record"], config["reference_arm"]
    panel = learning.worlds(config["reference_eval_seed"], config["reference_namespace"], "evaluation",
                            config["reference_episodes"])
    model, meta = load_checkpoint(checkpoint_path(checkpoint_root, record, arm), arm,
                                  CHECKPOINT_DIGESTS[(record, arm)])
    result = learning.rollout(library, panel, model, arm, config["reference_namespace"], None,
                             config["reference_round"], False)
    expected = {row["world"]: row for row in reference if row["arm"] == arm and row["checkpoint"] == "final"}
    compared = 0
    for row in result["episodes"]:
        want = expected[row["world"]]
        if [row[name] for name in REFERENCE_FIELDS] != [want[name] for name in REFERENCE_FIELDS]:
            raise AssertionError(f"greedy replay differs from the recorded B01 row: world {row['world']}")
        compared += 1
    if compared != config["reference_episodes"]:
        raise AssertionError("greedy replay compared fewer rows than the recorded panel")
    return dict(record=record, arm=arm, checkpoint="final", episodes=len(panel), compared_rows=compared,
                compared_fields=list(REFERENCE_FIELDS), reference_path=str(reference_path),
                reference_sha256=hashlib.sha256(payload).hexdigest(), checkpoint_sha256=meta["sha256"],
                seconds=perf_counter() - started)


def run(config, out, launch_sha, started, checkpoint_root, reference_path=None):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    build_started = perf_counter()
    library = build(out)
    build_seconds = perf_counter() - build_started
    world_started = perf_counter()
    panel = learning.worlds(config["world_seed"], config["namespace"], "evaluation", config["episodes"])
    world_seconds = perf_counter() - world_started
    setup_seconds = perf_counter() - started - build_seconds - world_seconds
    counter = {"draws": 0}
    rows, cells, loaded = [], [], []
    for record in RECORDS:
        for arm in ARMS:
            load_started = perf_counter()
            model, meta = load_checkpoint(checkpoint_path(checkpoint_root, record, arm), arm,
                                          CHECKPOINT_DIGESTS[(record, arm)])
            initial = {name: p.detach().clone() for name, p in model.named_parameters()}
            meta.update(record=record, load_seconds=perf_counter() - load_started)
            for mode in MODES:
                before = counter["draws"]
                supplier = None if mode == "GREEDY" else evaluation_uniform_supplier(
                    config["action_seed"], config["namespace"], record, arm, panel, counter)
                result = learning.rollout(library, panel, model, arm, config["namespace"], None, 0, False,
                                          evaluation_uniforms=supplier)
                rows.extend(dict(row, record=record, arm=arm, mode=mode) for row in result["episodes"])
                cells.append(dict(record=record, arm=arm, mode=mode, episodes=len(panel),
                                  seconds=result["seconds"], checks=result["checks"], residual=result["residual"],
                                  model_forward_calls=result["model_forward_calls"],
                                  model_forward_decisions=result["model_forward_decisions"],
                                  action_draws=counter["draws"] - before))
            meta["parameter_state"] = learning.parameter_state(model, initial)
            if meta["parameter_state"]["displacement_norm"] != 0.0:
                raise AssertionError("loaded parameters moved during a zero-training evaluation")
            loaded.append(meta)
    bcrh_rows, bcrh_time = experiment.bcrh(library, panel)
    replay = None
    if config["profile"] == "engineering-check":
        replay = b01_greedy_replay(library, config, checkpoint_root, reference_path)
    exposure = dict(training_instances=0, rounds=0, optimizer_steps=0, backward_calls=0,
                    parameter_updates=0, parameter_displacement_norms=[meta["parameter_state"]["displacement_norm"]
                                                                       for meta in loaded],
                    loaded_parameters={f"{meta['record']}/{meta['arm']}": meta["parameters"] for meta in loaded},
                    policy_cells=len(cells), evaluation_episodes=len(rows),
                    policy_joint_decisions=sum(cell["model_forward_decisions"] for cell in cells),
                    evaluation_action_draws=counter["draws"],
                    bcrh_episodes=len(bcrh_rows), bcrh_complete_calls=bcrh_time["complete_bcrh_calls"],
                    native_ticks=240 * (len(rows) + len(bcrh_rows)))
    publication_started = perf_counter()
    for filename, content in (("evaluation_episodes.json", rows), ("bcrh_episodes.json", bcrh_rows)):
        restored, _ = experiment.publish_json(out / filename, content)
        if len(restored) != len(content):
            raise AssertionError("episode publication readback count differs")
    summary = dict(object="VNFC-N7-B01-DEPLOYMENT-MODE-EVAL", launch_sha=launch_sha, config=config,
        dtype="float64", device="cpu", torch_threads=1, native_threads=1, training_seed_count=2,
        rng_domains="dedicated world/action masters and namespace; GREEDY consumes no action draw; "
                    "SAMPLE draws one uniform per token from eval-actions/<record>/<arm>",
        checkpoints=loaded, cells=cells, exposure=exposure, readout=grid_readout(rows, bcrh_rows),
        b01_greedy_replay=replay,
        timings=dict(shared_setup=setup_seconds, native_build=build_seconds, world_generation=world_seconds,
                     cells=[dict(record=cell["record"], arm=cell["arm"], mode=cell["mode"],
                                 seconds=cell["seconds"]) for cell in cells],
                     checkpoint_loading=[meta["load_seconds"] for meta in loaded], bcrh=bcrh_time,
                     b01_greedy_replay=None if replay is None else replay["seconds"]),
        total_native_ticks=exposure["native_ticks"])
    try:
        import resource
        summary["peak_rss_main_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except (ImportError, OSError):
        summary["peak_rss_main_bytes"] = None
        summary["resources_unmeasured"] = True
    summary["timings"]["publication"] = perf_counter() - publication_started
    summary["wall_before_summary_seconds"] = perf_counter() - started
    restored, summary_seconds = experiment.publish_json(out / "summary.json", summary)
    if restored["exposure"] != exposure:
        raise AssertionError("summary exposure readback differs")
    complete_wall = perf_counter() - started
    final = dict(summary=str(out / "summary.json"), complete_wall_seconds=complete_wall,
                 summary_publication_seconds=summary_seconds, wall_cap_seconds=config["wall_cap"],
                 within_wall_cap=complete_wall <= config["wall_cap"], exposure=exposure,
                 peak_rss_main_bytes=summary["peak_rss_main_bytes"],
                 primary_contrast_means=summary["readout"]["primary_contrast_means"])
    print(json.dumps(final), flush=True)
    return final
