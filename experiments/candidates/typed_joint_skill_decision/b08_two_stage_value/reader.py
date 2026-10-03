"""Full new uncompressed reconstruction and the fixed complete B08 reading."""
from __future__ import annotations

from copy import deepcopy
import gzip
import json
from pathlib import Path
import time

import numpy as np
import torch

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_transmission.control import predict_next
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.reader import _native_view, _public_state
from experiments.candidates.uav_fleet_transmission.study import metrics
from experiments.candidates.uav_fleet_transmission.b02.controller import KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS
from experiments.candidates.uav_fleet_transmission.b03.option import branch_id
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.inputs import SegmentReference
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.reader import verify_certificate

from . import contract as c, evidence as e, features, functional, learning, model
from .planner import BudgetedProgram


def _compare_payload(actual, expected, label):
    if set(actual["arrays"]) != set(expected["arrays"]):
        raise ValueError(f"model array names differ: {label}")
    for key in actual["arrays"]:
        e.exact(actual["arrays"][key], expected["arrays"][key], f"{label}/{key}")
    e.same_record(actual["summary"], expected["summary"], f"{label}/summary")
    e.same_record(actual["decisions"], expected["decisions"], f"{label}/decisions")


def _query_scores(record):
    scores = np.frombuffer(bytes.fromhex(record["score_bits"]), dtype=np.float32).copy()
    e.same_record(e.array_binding(scores), record["scores"], "query score bits/hash")
    return scores


def _verify_native_snapshot(raw, t, view):
    """Recompute actual saved-state physics and observations, with no env.step."""
    positions, users = raw["positions"][t], raw["users"]
    mask = mask_bits(255 if t == 0 else int(raw["mask"][t - 1]), 8)
    loss = uav_radio.free_space_user_path_loss(positions, users)
    sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask)
    connections = uav_radio.greedy_connection_assignment(sinr, 0., 10)
    e.exact(raw["sinr"][t], sinr, f"native radio/{t}")
    e.exact(raw["connections"][t], connections, f"native assignment/{t}")
    view.uav_positions, view.sinr_matrix, view.connections = positions, sinr, connections
    view._transmitter_mask = mask
    view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
    view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
    view.current_step = t
    e.exact(raw["peer_sinr"][t], view.uav_sinr_matrix, f"native peer radio/{t}")
    e.exact(raw["states"][t], _public_state(positions, users, t, 500), f"public FP32 report/{t}")
    for member in range(8):
        obs = MultiUAVEnv._get_observation_vectorized(view, f"uav_{member}")["obs"]
        e.exact(raw["observations"][t, member], obs, f"native local view/{t}/{member}")
    e.exact(raw["visible_users"][t], np.asarray([len(view._local_user_entries(i)[0][:20]) for i in range(8)]),
            f"visible user slots/{t}")
    e.exact(raw["visible_peers"][t], np.asarray([len(view._local_uav_entries(i)[0][:10]) for i in range(8)]),
            f"visible peer slots/{t}")
    if t:
        native_reward = UAVBaseStationEnv._compute_reward(view)
        components = np.asarray([view.reward_info[name] for name in COMPONENTS], dtype=np.float64)
        e.exact(raw["components"][t - 1], components, f"native reward components/{t}")
        # Native step divides J among eight agents; the adapter sums those
        # eight values in Python order, divides again, then calls float().
        # Preserve that arithmetic, including rounding and signed-zero bits.
        scalar = float(sum(native_reward / 8 for _ in range(8)) / 8)
        e.exact(raw["scalar_reward"][t - 1], np.asarray(scalar, dtype=np.float64),
                f"native adapter scalar bits/{t}")


def _shapes(raw, steps):
    shapes = {"positions": (steps + 1, 8, 3), "observations": (steps + 1, 8, 104),
              "states": (steps + 1, 133), "sinr": (steps + 1, 8, 50),
              "connections": (steps + 1, 8, 50), "peer_sinr": (steps + 1, 8, 8),
              "visible_users": (steps + 1, 8), "visible_peers": (steps + 1, 8),
              "actions": (steps, 8, 3), "mask": (steps,), "components": (steps, 4),
              "scalar_reward": (steps,), "terminal": (steps,), "users": (50, 2)}
    if set(raw) != set(shapes):
        raise ValueError("native saved-array keys differ")
    for key, shape in shapes.items():
        if raw[key].shape != shape or np.isnan(raw[key]).any():
            raise ValueError(f"native saved-array shape/NaN differs: {key}")
        if key not in ("sinr", "peer_sinr") and not np.isfinite(raw[key]).all():
            raise ValueError(f"nonfinite saved native value: {key}")
    if raw["actions"].dtype != np.float32 or not np.isin(raw["actions"], [-1., 0., 1.]).all():
        raise ValueError("issued command dtype/alphabet differs")
    e.exact(raw["terminal"], np.arange(steps) == 499, "actual H500 terminal or prefix nonterminal")


def verify_case(out, row, world, budget, *, state=None):
    """Exactly one full reader pass over each new case and all paid branches."""
    out = Path(out)
    wall, cpu = time.monotonic(), time.process_time()
    steps = 40 if row["kind"] == "train" else 500
    if not row["complete"] or row["steps"] != steps or row["runtime_seed"] != world["runtime_seed"]:
        raise ValueError("incomplete or mismatched native case")
    raw = e.load_arrays(e.checked_path(out, row["raw"]))
    decisions = e.read_gzip(e.checked_path(out, row["decisions"]))
    catalog = e.read_gzip(e.checked_path(out, row["evidence_catalog"]))
    _shapes(raw, steps)
    if len(decisions) != steps or row.get("decisions_attempted") != steps:
        raise ValueError("native decision exposure differs")
    e.exact(raw["users"], np.asarray(world["user_positions"], dtype=np.float64), "bound native users")
    e.exact(raw["positions"][0], np.asarray(world["uav_positions"], dtype=np.float64), "bound initial UAVs")
    segments = catalog["segments"]
    segment_reads, branch_reads, bank_reads, menu_reads, query_reads = [], [], [], [], []
    full_segments = []
    for name in ("segments", "model_branches", "candidate_banks"):
        ids = [r["id"] for r in catalog[name]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate scientific identity in {name}")

    def segment_sink(identifier, result):
        index = len(segment_reads)
        if index >= len(segments) or segments[index]["id"] != identifier:
            raise ValueError("complete model segment order/identity differs")
        saved = segments[index]
        actual = e.load_segment(out, saved)
        reference = {key: result[key] for key in ("arrays", "summary", "decisions")}
        _compare_payload(actual, reference, identifier)
        cert = result["certificate"]
        kind = "prefix" if identifier.endswith("/prefix") else "suffix" if identifier.endswith("/suffix") else "actual"
        ref = SegmentReference(reference, cert["start_t"], cert["end_t"],
            e.decode_array(cert["entry"]["commands"]), cert["entry"]["mask"],
            e.decode_array(cert["entry"]["users"]), kind, {}, True, deepcopy(cert["plan"]))
        # The inherited independent certificate checker dispatches its B06
        # C-only key by this historical prefix. Alias only that dispatch input;
        # the stored paid segment retains its explicit K2-C identity.
        proof_id = "actual/t40/branch/" + identifier.rsplit("/", 1)[-1] if identifier.startswith("k2-c/rank/") else identifier
        proof = {"id": proof_id, "certificate": saved["certificate"], "scientific": saved["scientific"]}
        checked = verify_certificate(proof_id, proof, ref, True)
        segment_reads.append({"id": identifier, **checked})
        full_segments.append({"id": identifier, "certificate": json.loads(c.encoded(cert))})
        budget.check(progress={"reader_case_segments": len(segment_reads)})

    def branch_sink(identifier, result):
        index = len(branch_reads)
        if index >= len(catalog["model_branches"]) or catalog["model_branches"][index]["id"] != identifier:
            raise ValueError("complete branch exposure/order differs")
        record = catalog["model_branches"][index]
        _compare_payload(e.load_branch(out, catalog, record), result, identifier)
        branch_reads.append(identifier)

    def candidate_sink(identifier, values):
        index = len(bank_reads)
        if index >= len(catalog["candidate_banks"]) or catalog["candidate_banks"][index]["id"] != identifier:
            raise ValueError("stationary bank exposure/order differs")
        record = catalog["candidate_banks"][index]
        saved = np.load(e.checked_path(out, record["raw"]), allow_pickle=False)
        e.exact(saved, values, f"all stationary rows/{identifier}")
        bank_reads.append(identifier)

    def menu_sink(**values):
        index = len(menu_reads)
        if index >= len(catalog["menus"]):
            raise ValueError("missing lawful first menu")
        record = e.menu_record(**values)
        e.same_record(record, catalog["menus"][index], "lawful first-menu replay")
        menu_reads.append(record["start_t"])

    def scorer(report, history, mask, bank, plans):
        if state is None or query_reads or len(catalog["queries"]) != 1:
            raise ValueError("learner query/state identity differs")
        query = catalog["queries"][0]
        if query["state_sha256"] != model.state_digest(state) or query["valid_count"] != len(plans):
            raise ValueError("query checkpoint/cardinality differs")
        feature_menu = features.build_features(report, history.commands, mask, plans, bank)
        e.same_record(query["features"], {key: e.array_binding(value) for key, value in feature_menu.items()},
                      "all reconstructed feature bits")
        scores = _query_scores(query)
        checked = functional.verify(state, feature_menu, scores)
        query_reads.append(checked)
        # These bits were independently reconstructed above; using them avoids
        # an undeclared third reader forward call.
        return scores[:len(plans)].copy()

    learner = row["arm"].startswith("L2")
    if learner != (state is not None) or (not learner and catalog["queries"]):
        raise ValueError("unexpected learned query or missing final state")
    policy = BudgetedProgram("L2" if learner else row["arm"], branch_sink=branch_sink,
        candidate_sink=candidate_sink, reuse=False, segment_sink=segment_sink, menu_sink=menu_sink,
        scorer=scorer if learner else None)
    counts, calls, old_mask = empty_counts(), {kind: 0 for kind in KINDS}, 255
    view = _native_view(8, raw["users"], 500)
    for t in range(steps + 1):
        _verify_native_snapshot(raw, t, view)
        if t == steps:
            break
        e.exact(raw["positions"][t + 1], predict_next(raw["positions"][t], raw["actions"][t]), f"native motion/{t}")
        command, mask, decision = policy.select(t, raw["states"][t] if t % 10 == 0 else None, old_mask)
        e.same_record(decision, decisions[t], f"actual native decision/{t}")
        e.exact(raw["actions"][t], command, f"issued primitive command/{t}")
        if int(raw["mask"][t]) != mask or (t % 10 and old_mask != mask):
            raise ValueError("issued mask/hold differs")
        trace_counts(decision, counts)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        old_mask = mask
        if t % 10 == 0:
            budget.check(progress={"reader_case_native_snapshots": t + 1})
    if row["kind"] == "train":
        policy.prepare_first(raw["states"][-1], old_mask)
    if (len(segment_reads) != len(segments) or len(branch_reads) != len(catalog["model_branches"])
            or len(bank_reads) != len(catalog["candidate_banks"]) or len(menu_reads) != len(catalog["menus"])
            or len(query_reads) != len(catalog["queries"])):
        raise ValueError("incomplete paid model/menu/functional reconstruction")
    e.same_record(policy.plans, {int(key): value for key, value in catalog["plans"].items()}, "actual requested plans")
    e.same_record(policy.selections, {int(key): value for key, value in catalog["selections"].items()}, "complete selections")
    e.same_record(policy.banks, catalog["banks"], "all bank accounting")
    e.same_record(counts, row["native_candidate_counts"], "native query accounting")
    e.same_record(calls, row["calls"], "native controller calls")
    e.same_record(metrics(raw, 8), row["metrics"], "native scalar/vector reductions")
    worker_costs = e.case_costs(catalog, counts)
    e.same_record(worker_costs, row["costs"], "complete worker cost ledger")
    full_catalog = dict(catalog, segments=full_segments)
    reader_costs = e.case_costs(full_catalog, counts)
    if reader_costs["actual_worker_requests"] != worker_costs["logical_worker_requests"]:
        raise ValueError("uncompressed full reader did not pay the complete logical request scope")
    reading = {"kind": row["kind"], "arm": row["arm"], "world_id": row["world_id"],
               "status": "complete", "native_snapshots": steps + 1, "new_native_transitions": 0,
               "worker_costs": worker_costs, "reader_costs": reader_costs,
               "segments": segment_reads, "branch_ids": branch_reads, "bank_ids": bank_reads,
               "functional_queries": query_reads, "all_scientific_payloads_bitwise_equal": True,
               "cpu_seconds": time.process_time() - cpu, "wall_seconds": time.monotonic() - wall}
    path = e.checked_path(out, row["evidence_catalog"]).parent / "reader.json.gz"
    e.write_gzip(path, reading)
    return {"kind": row["kind"], "arm": row["arm"], "world_id": row["world_id"],
            "artifact": c.binding(path, out), "cpu_seconds": reading["cpu_seconds"],
            "wall_seconds": reading["wall_seconds"], "native_snapshots": steps + 1,
            "functional_menu_queries": len(query_reads), "reader_costs": reader_costs}


def verify_fit(out, fit, bank, labels, budget, *, source_sha, bank_binding):
    """Trace exposure plus both functional paths at every saved checkpoint.

    This is not an optimizer replay and adds no fit/update. It tests the fixed
    recorded function and observed optimization/exposure at the promised scope.
    """
    out = Path(out)
    wall, cpu = time.monotonic(), time.process_time()
    if [cp["update"] for cp in fit["checkpoints"]] != list(c.CHECKPOINTS):
        raise ValueError("fixed checkpoint schedule incomplete")
    if (fit["fit_id"] not in (0, 1, 2) or fit["label"] != c.FIT_LABELS[fit["fit_id"]]
            or fit["init_seed"] != c.addressed_seed(fit["label"], 10)
            or fit["permutation_seed"] != c.addressed_seed(fit["label"], 11)):
        raise ValueError("fit RNG identity differs")
    for cp in fit["checkpoints"]:
        if (cp["fit_index"] != fit["fit_id"] or cp["init_seed"] != fit["init_seed"]
                or cp["permutation_seed"] != fit["permutation_seed"]
                or cp["fit_id"] != {"init_seed": fit["init_seed"], "permutation_seed": fit["permutation_seed"]}
                or cp["source_sha"] != source_sha or cp["bank"] != bank_binding
                or cp["world_ids"] != list(c.TRAIN_IDS) or cp["epochs"] != 256
                or cp["batch_size"] != 16 or cp["scheduled_updates"] != 2048):
            raise ValueError("checkpoint source/bank/world/RNG contract differs")
    e.same_record(fit["final"], fit["checkpoints"][-1], "fixed final checkpoint identity")
    counts = bank["valid"].sum(axis=1).astype(np.int64)
    pair_counts = counts * (counts - 1) // 2
    exposure = np.zeros(128, dtype=np.int64)
    candidates = pairs = updates = 0
    checkpoints_by_step = {cp["update"]: cp for cp in fit["checkpoints"]}
    with gzip.open(e.checked_path(out, fit["updates"]), "rt", encoding="utf-8") as stream:
        expected = iter(learning.epoch_batches(fit["permutation_seed"]))
        for line in stream:
            record = json.loads(line)
            updates += 1
            epoch, indices = next(expected)
            exposure[indices] += 1
            candidates += int(counts[indices].sum())
            pairs += int(pair_counts[indices].sum())
            if (record["update"] != updates or record["optimizer_counter"] != updates
                    or record["epoch"] != epoch or record["batch_indices"] != indices.tolist()
                    or record["batch_world_ids"] != [c.TRAIN_IDS[i] for i in indices]
                    or record["world_ids"] != list(c.TRAIN_IDS)
                    or record["world_exposure"] != exposure.tolist()
                    or record["menu_presentations"] != int(exposure.sum())
                    or record["candidate_presentations"] != candidates or record["pair_presentations"] != pairs
                    or record["valid_candidates"] != counts[indices].tolist()
                    or record["valid_pairs"] != pair_counts[indices].tolist()
                    or record["init_seed"] != fit["init_seed"] or record["permutation_seed"] != fit["permutation_seed"]
                    or record["finite_loss"] is not True or record["finite_gradient"] is not True
                    or not np.isfinite([record["loss"], record["gradient_norm_before_clip"]]).all()
                    or len(record["actual_optimizer_steps"]) != len(model.STATE_SHAPES)
                    or any(step != updates for step in record["actual_optimizer_steps"])):
                raise ValueError("observed optimization/exposure trace differs")
            if updates in checkpoints_by_step:
                cp = checkpoints_by_step[updates]
                for key in ("world_exposure", "menu_presentations", "candidate_presentations", "pair_presentations", "optimizer_counter"):
                    e.same_record(cp[key], record[key], f"checkpoint/update exposure/{key}")
    if updates != 2048 or np.any(exposure != 256):
        raise ValueError("incomplete fixed optimizer exposure")
    checkpoints, initial = [], None
    for cp in fit["checkpoints"]:
        state = torch.load(e.checked_path(out, cp["weights"]), map_location="cpu", weights_only=True)["state"]
        if model.state_digest(state) != cp["state_sha256"]:
            raise ValueError("checkpoint tensor identity differs")
        if initial is None:
            initial = deepcopy(state)
            if (cp["update"] != 0 or cp["world_exposure"] != [0] * 128 or cp["optimizer_counter"] != 0
                    or any(cp[key] for key in ("menu_presentations", "candidate_presentations", "pair_presentations"))):
                raise ValueError("initial checkpoint is not pre-update")
        e.same_record(model.parameter_movement(initial, state), cp["parameter_movement"], "checkpoint parameter movement")
        e.same_record(cp["valid"], bank["valid"].tolist(), "checkpoint validity")
        predictions = np.load(e.checked_path(out, cp["predictions"]), allow_pickle=False)
        if predictions.dtype != np.float32 or predictions.shape != (128, 8):
            raise ValueError("recorded whole-bank prediction shape differs")
        queries, per_world = [], []
        for i, world_id in enumerate(c.TRAIN_IDS):
            menu = {key: value[i] for key, value in bank.items()}
            queries.append(functional.verify(state, menu, predictions[i]))
            per_world.append(ranking_reading(predictions[i], labels[i], bank["valid"][i]))
            if i % 16 == 0:
                budget.check(progress={"functional_fit": fit["fit_id"], "checkpoint": cp["update"], "menus_checked": i + 1})
        checkpoints.append({"update": cp["update"], "state_sha256": cp["state_sha256"],
                            "functional_queries": queries, "training_worlds": per_world,
                            "parameter_movement": cp["parameter_movement"]})
    e.same_record(fit["metadata"]["parameter_movement"], checkpoints[-1]["parameter_movement"], "final movement")
    for key in ("world_ids", "world_exposure", "menu_presentations", "candidate_presentations", "pair_presentations",
                "optimizer_counter", "update", "init_seed", "permutation_seed", "epochs", "batch_size", "scheduled_updates"):
        e.same_record(fit["metadata"][key], fit["final"][key], f"final fit metadata/{key}")
    result = {"fit_id": fit["fit_id"], "status": "complete", "updates_observed": updates,
              "new_fits": 0, "new_optimizer_updates": 0, "optimizer_replay_performed": False,
              "menu_presentations": int(exposure.sum()), "candidate_presentations": candidates,
              "pair_presentations": pairs, "checkpoints": checkpoints,
              "recorded_menus_verified": 9 * 128, "reader_forward_menus": 2 * 9 * 128,
              "cpu_seconds": time.process_time() - cpu, "wall_seconds": time.monotonic() - wall}
    path = out / "raw" / "fits" / f"s{fit['fit_id']}" / "reader.json.gz"
    e.write_gzip(path, result)
    return {"fit_id": fit["fit_id"], "artifact": c.binding(path, out), "cpu_seconds": result["cpu_seconds"],
            "wall_seconds": result["wall_seconds"], "recorded_menus_verified": 1152,
            "reader_forward_menus": 2304, "updates_observed": updates}


def ranking_reading(scores, values, valid):
    scores = np.asarray(scores, dtype=np.float64)[valid]
    values = np.asarray(values, dtype=np.float64)[valid]
    target = 100.0 * values / 460.0
    error = scores - target
    centered = error - error.mean()
    i, j = np.triu_indices(len(scores), 1)
    pair = (scores[i] - scores[j]) - 100.0 * (values[i] - values[j]) / 460.0
    return {"valid_candidates": len(scores), "pair_mse": float(np.mean(pair**2)) if len(pair) else 0.0,
            "centered_mse": float(np.mean(centered**2)), "world_mean_error": float(error.mean()),
            "exact_value_pairs": int(np.sum(values[i] == values[j]))}


def verify_cold_identity(out, audit, main):
    a = e.load_arrays(e.checked_path(out, audit["raw"]))
    b = e.load_arrays(e.checked_path(out, main["raw"]))
    if set(a) != set(b):
        raise ValueError("cold/native array keys differ")
    for key in a:
        e.exact(a[key], b[key], f"cold complete native/{key}")
    ca = e.read_gzip(e.checked_path(out, audit["evidence_catalog"]))
    cb = e.read_gzip(e.checked_path(out, main["evidence_catalog"]))
    for key in ("plans", "selections", "banks", "menus"):
        e.same_record(ca[key], cb[key], f"cold complete control/{key}")
    e.same_record(audit["metrics"], main["metrics"], "cold native metrics")
    for left, right in zip(ca["queries"], cb["queries"]):
        for key in ("t", "scores", "score_bits", "features", "valid_count", "state_sha256"):
            e.same_record(left[key], right[key], f"cold learned query/{key}")
    if len(ca["queries"]) != len(cb["queries"]):
        raise ValueError("cold query count differs")


def _longest(values):
    best = current = 0
    for value in values:
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def individual_reading(served):
    result = []
    horizon = len(served)
    for user in range(50):
        signal = served[:, user]
        seen = np.flatnonzero(signal)
        starts = np.flatnonzero(np.r_[True, signal[:-1]] & ~signal)
        gaps = []
        for start in starts:
            future = np.flatnonzero(signal[start:])
            end = int(start + future[0]) if len(future) else horizon
            gaps.append({"start": int(start), "end_exclusive": end, "length": end - int(start),
                         "left_censored": bool(start == 0), "right_censored": bool(end == horizon)})
        maximum = max((gap["length"] for gap in gaps), default=0)
        result.append({"user": user, "served_ticks": int(signal.sum()), "first_service_tick": int(seen[0]) if len(seen) else None,
                       "never_served": not bool(len(seen)), "longest_observed_gap": maximum,
                       "longest_gap_records": [gap for gap in gaps if gap["length"] == maximum]})
    return result


def native_reading(raw):
    served_user = raw["connections"][1:].any(axis=1)
    total = served_user.sum(axis=1)
    parts = {}
    for name, begin in (("whole", 0), ("post_t40", 40), ("post_t120", 120)):
        q = raw["components"][begin:]
        s = total[begin:]
        path = np.linalg.norm(np.diff(raw["positions"][begin:], axis=0), axis=2).sum(axis=0)
        parts[name] = {"J": float(q[:, 3].mean()), "served": float(s.mean()), "quality": float(q[:, 1].mean()),
                       "height_penalty": float(q[:, 2].mean()), "mean_path_per_uav": float(path.mean()),
                       "served_min": int(s.min()), "served_p05": float(np.quantile(s, .05)),
                       "zero_team_ticks": int(np.sum(s == 0)), "longest_zero_team_run": _longest(s == 0)}
    users = individual_reading(served_user)
    return {**parts, "users": users, "maximum_observed_user_gap": max(r["longest_observed_gap"] for r in users),
            "never_served_users": sum(r["never_served"] for r in users),
            "minimum_user_served_ticks": min(r["served_ticks"] for r in users)}


def plan_reading(plan, raw, start):
    if plan is None or not plan["initiated"]:
        return {"initiated": False, "physical_identity": "stay"}
    member, arrival = plan["member"], plan["arrival_t"]
    active = (raw["mask"][arrival:] & (1 << member)) != 0
    off = np.flatnonzero(~active)
    return {"initiated": True, "member": member, "site": plan["site"], "duration": plan["duration"],
            "arrival_t": arrival, "requested_command_bits": e.array_binding(np.asarray(plan["commands"], dtype=np.float32)),
            "stationary_candidate": plan["selected"], "actual_arrival_mask": int(raw["mask"][arrival]),
            "actual_arrival_position": raw["positions"][arrival, member].tolist(),
            "arrival_model_position": plan["predicted_destination"][member],
            "transit_J": float(sum(float(v) for v in raw["components"][start:arrival, 3])),
            "transit_served": int(raw["connections"][start + 1:arrival + 1].sum()),
            "activated_ticks_after_arrival": int(active.sum()),
            "first_remute_t": int(arrival + off[0]) if len(off) else None}


def forecast_reading(out, catalog, raw, arm, start):
    selection = catalog["selections"][str(start)]
    record = next(r for r in catalog["model_branches"] if r["id"] == selection["selected_model_branch"])
    modeled = e.load_branch(out, catalog, record)["arrays"]
    end = 120 if arm == "G2" and start == 40 else 500
    count = end - start
    reward = modeled["reward_components"][:count]
    native_served = raw["connections"][start + 1:end + 1].sum(axis=(1, 2))
    return {"start": start, "end": end, "selected_branch": record["id"],
            "model_minus_native_total_J": float(sum(float(v) for v in reward[:, 0]))
                - float(sum(float(v) for v in raw["components"][start:end, 3])),
            "model_minus_native_total_served": int(reward[:, 1].sum()) - int(native_served.sum()),
            "equal_commands": bool(np.array_equal(modeled["actions"][:count], raw["actions"][start:end])),
            "equal_masks": bool(np.array_equal(modeled["masks"][:count], raw["mask"][start:end])),
            "equal_per_tick_service": bool(np.array_equal(reward[:, 1], native_served)),
            "max_coordinate_error_m": float(np.max(np.abs(modeled["positions"][:count + 1] - raw["positions"][start:end + 1]))),
            "scope": "model versus native including actual replanning; valid disagreement retained"}


def _paired(a, b, indices):
    diff = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    bootstrap = diff[indices].mean(axis=1)
    return {"paired_differences": diff.tolist(), "mean": float(diff.mean()),
            "descriptive_95_interval": np.quantile(bootstrap, [.025, .975]).tolist(),
            "positive": int(np.sum(diff > 0)), "zero": int(np.sum(diff == 0)), "negative": int(np.sum(diff < 0))}


def complete_reading(out, summary, budget):
    out = Path(out)
    expected_order = [(world, c.ARMS[(i + offset) % 7]) for i, world in enumerate(c.FINAL_IDS) for offset in range(7)]
    if ([(r["world_id"], r["arm"]) for r in summary["final"]] != expected_order
            or [(r["world_id"], r["arm"]) for r in summary["audits"]] != [(c.FINAL_IDS[0], a) for a in c.ARMS]
            or [r["world_id"] for r in summary["acquisition"]] != list(c.TRAIN_IDS)
            or len(summary["fits"]) != 3 or len(summary["functional_readings"]) != 3):
        raise ValueError("complete fixed acquisition/fit/panel/audit inventory differs")
    cases = summary["acquisition"] + summary["final"] + summary["audits"]
    case_id = lambda row: (row["kind"], row["world_id"], row["arm"])
    if ([case_id(row) for row in summary["case_readings"]] != [case_id(row) for row in cases]
            or [row["fit_id"] for row in summary["functional_readings"]] != [0, 1, 2]
            or [row["fit_id"] for row in summary["fits"]] != [0, 1, 2]):
        raise ValueError("not every paid case received the full reader")
    for row, case in zip(summary["case_readings"], cases):
        bound = e.read_gzip(e.checked_path(out, row["artifact"]))
        if bound["status"] != "complete" or case_id(bound) != case_id(case):
            raise ValueError("full reader artifact identity/status differs")
        e.same_record(bound["worker_costs"], case["costs"], "full reader worker accounting")
        e.same_record(bound["reader_costs"], row["reader_costs"], "full reader independent accounting")
    for row in summary["functional_readings"]:
        bound = e.read_gzip(e.checked_path(out, row["artifact"]))
        if bound["status"] != "complete" or bound["fit_id"] != row["fit_id"]:
            raise ValueError("functional reader artifact identity/status differs")
    counts = {"native_transitions": sum(row["steps"] for row in cases),
              "native_snapshots": sum(row["native_snapshots"] for row in summary["case_readings"]),
              "new_fits": len(summary["fits"]), "optimizer_updates": sum(row["metadata"]["update"] for row in summary["fits"]),
              "worker_model_ticks": sum(row["costs"]["logical_model_ticks"] for row in cases),
              "worker_logical_requests": sum(row["costs"]["logical_worker_requests"] for row in cases),
              "stationary_banks": sum(row["costs"]["stationary_banks"] for row in cases),
              "stationary_candidate_rows": sum(row["costs"]["stationary_candidate_rows"] for row in cases),
              "candidate_transit_ticks": sum(row["costs"]["candidate_transit_ticks"] for row in cases),
              "training_menu_presentations": sum(row["metadata"]["menu_presentations"] for row in summary["fits"]),
              "training_candidate_presentations": sum(row["metadata"]["candidate_presentations"] for row in summary["fits"]),
              "training_pair_presentations": sum(row["metadata"]["pair_presentations"] for row in summary["fits"]),
              "recorded_forward_menus": sum(row["recorded_menus_verified"] for row in summary["functional_readings"])
                  + sum(row["functional_menu_queries"] for row in summary["case_readings"]),
              "functional_reader_forward_menus": sum(row["reader_forward_menus"] for row in summary["functional_readings"])
                  + 2 * sum(row["functional_menu_queries"] for row in summary["case_readings"])}
    exact_counts = ("native_transitions", "native_snapshots", "new_fits", "optimizer_updates",
                    "training_menu_presentations", "recorded_forward_menus", "functional_reader_forward_menus")
    for key, limit in c.CEILINGS.items():
        if counts[key] > limit or (key in exact_counts and counts[key] != limit):
            raise ValueError(f"fixed exposure or conservative ceiling differs: {key}")
    indexed = {(r["world_id"], r["arm"]): r for r in summary["final"]}
    worlds = []
    for world_id in c.FINAL_IDS:
        readings, first_menu = {}, None
        root_values = None
        for arm in c.ARMS:
            row = indexed[world_id, arm]
            raw = e.load_arrays(e.checked_path(out, row["raw"]))
            catalog = e.read_gzip(e.checked_path(out, row["evidence_catalog"]))
            menu = catalog["menus"][0]
            if first_menu is None:
                first_menu = menu
                prefix = {key: value[:41] if key in ("positions", "observations", "states", "sinr", "connections", "peer_sinr", "visible_users", "visible_peers")
                          else value if key == "users" else value[:40] for key, value in raw.items()}
            else:
                e.same_record(menu, first_menu, "paired common t40 lawful menu")
                for key, expected in prefix.items():
                    e.exact(raw[key] if key == "users" else raw[key][:len(expected)], expected, f"common native prefix/{key}")
            reading = native_reading(raw)
            reading["plans"] = {key: plan_reading(plan, raw, int(key)) for key, plan in catalog["plans"].items()}
            reading["forecasts"] = [forecast_reading(out, catalog, raw, arm, start) for start in (40, 120)]
            reading["allocation"] = catalog["selections"]["40"]["allocation"]
            reading["choices"] = {key: {field: selection.get(field) for field in
                ("selected_branch", "selected_physical_identity", "strict_model_improvement_over_stay")}
                for key, selection in catalog["selections"].items()}
            reading["online_worker_cpu_seconds"] = row["timing"]["cpu_seconds"]
            reading["controller_model_cpu_seconds"] = row["timing"]["controller_model_cpu_excluding_owned_callback_IO"]
            reading["model_costs"] = row["costs"]
            if arm == "A2":
                root_values = catalog["selections"]["40"]["Q2"]
            if arm.startswith("L2"):
                reading["scores"] = _query_scores(catalog["queries"][0]).tolist()
            readings[arm] = reading
        ids = [branch_id(plan) for plan in first_menu["plans"]]
        if root_values is None or set(root_values) != set(ids):
            raise ValueError("fresh A2 reference lacks complete root labels")
        best = max(root_values.values())
        for arm in ("K2-C", "K2-S", "L2-s0", "L2-s1", "L2-s2"):
            allocation = readings[arm]["allocation"]
            retained = allocation["retained_first_ids"]
            retained_best = max(root_values[identifier] for identifier in retained)
            readings[arm]["allocation_regret_J_per_500"] = (best - retained_best) / 500.0
            readings[arm]["retains_a_complete_value_winner"] = any(root_values[i] == best for i in retained)
            if arm.startswith("L2"):
                values = np.zeros(8, dtype=np.float64)
                values[:len(ids)] = [root_values[i] for i in ids]
                readings[arm]["fresh_ranking"] = ranking_reading(readings[arm]["scores"], values, np.arange(8) < len(ids))
        worlds.append({"world_id": world_id, "A2_root_values": root_values, "arms": readings})
        budget.check(progress={"read_worlds": len(worlds)})
    indices = np.random.RandomState(c.BOOTSTRAP_SEED).randint(0, 32, size=(c.BOOTSTRAP_REPLICATES, 32))
    pairs = [(learner, ordinary) for learner in c.ARMS[4:] for ordinary in c.ARMS[:4]]
    pairs += [(a, b) for i, a in enumerate(c.ARMS[:4]) for b in c.ARMS[:i]]
    comparisons = []
    fields = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "served_min", "served_p05",
              "zero_team_ticks", "longest_zero_team_run")
    for a, b in pairs:
        contrast = {"a": a, "b": b, "metrics": {}}
        for scope in ("whole", "post_t40", "post_t120"):
            for field in fields:
                contrast["metrics"][f"{scope}/{field}"] = _paired(
                    [w["arms"][a][scope][field] for w in worlds], [w["arms"][b][scope][field] for w in worlds], indices)
        for field in ("maximum_observed_user_gap", "never_served_users", "minimum_user_served_ticks",
                      "online_worker_cpu_seconds", "controller_model_cpu_seconds"):
            contrast["metrics"][field] = _paired([w["arms"][a][field] for w in worlds],
                                                   [w["arms"][b][field] for w in worlds], indices)
        contrast["changed_first_physical_choices"] = sum(w["arms"][a]["choices"]["40"]["selected_physical_identity"]
            != w["arms"][b]["choices"]["40"]["selected_physical_identity"] for w in worlds)
        comparisons.append(contrast)
    acquisition_cpu = sum(r["timing"]["cpu_seconds"] for r in summary["acquisition"])
    fit_cpu = [r["intrinsic_cpu_seconds"] for r in summary["fits"]]
    fit_observation_cpu = sum(r["research_observation_cpu_seconds"] for r in summary["fits"])
    verification_cpu = sum(r["cpu_seconds"] for r in summary["case_readings"] + summary["functional_readings"])
    audit_cpu = sum(r["timing"]["cpu_seconds"] for r in summary["audits"])
    cost_accounts = {"intrinsic_acquisition_cpu_seconds": acquisition_cpu, "intrinsic_fit_cpu_seconds": fit_cpu,
                     "intrinsic_bank_packing_cpu_seconds": summary["preparation_cpu"]["bank_packing"],
                     "research_fit_observation_cpu_seconds": fit_observation_cpu,
                     "main_panel_model_restoration_cpu_seconds": summary["preparation_cpu"]["panel_model_restoration"],
                     "main_panel_online_worker_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in summary["final"]),
                     "research_cold_audit_worker_cpu_seconds": audit_cpu,
                     "research_cold_audit_complete_process_cpu_seconds": sum(r["cold_process_resources"]["self_cpu_seconds"]
                         + r["cold_process_resources"]["finished_children_cpu_seconds"] for r in summary["audits"]),
                     "research_cold_model_restoration_cpu_seconds": sum(r["model_restore_cpu_seconds"] for r in summary["audits"]),
                     "research_reconstruction_cpu_seconds": verification_cpu,
                     "result_process_resources": e.resources(),
                     "accounting_note": "cold worker and cold model restoration are subsets of complete cold-process CPU; process totals include additional import/persistence/orchestration costs and finalization tails",
                     "support": "engineering, source preparation, interpretation/publication and unmetered tails are separate",
                     "break_even": "not automatically established; requires supported matched value and positive measured savings",
                     "assumed_deployment_volume": None}
    fit_effects = {}
    for ordinary in c.ARMS[:4]:
        effects = [next(r for r in comparisons if r["a"] == learner and r["b"] == ordinary)["metrics"]["whole/J"]["mean"]
                   for learner in c.ARMS[4:]]
        fit_effects[ordinary] = {"per_fit": effects, "mean": float(np.mean(effects)), "range": [min(effects), max(effects)],
                                 "scope": "three optimizer streams conditional on one128-world bank"}
    reading = {"status": "complete", "counts": counts, "cost_accounts": cost_accounts,
               "worker_actual_requests": sum(r["costs"]["actual_worker_requests"] for r in cases),
               "reader_actual_requests": sum(r["reader_costs"]["actual_worker_requests"] for r in summary["case_readings"]),
               "worlds": worlds, "comparisons": comparisons, "fit_effects": fit_effects,
               "bootstrap": {"seed": c.BOOTSTRAP_SEED, "replicates": c.BOOTSTRAP_REPLICATES,
                             "common_world_indices_sha256": e.array_binding(indices)},
               "scope": "exploratory fixed finales; no best fit, native label, mechanism repair or confirmation claim"}
    return reading
