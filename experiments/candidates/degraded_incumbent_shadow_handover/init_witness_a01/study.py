"""Zero-update controller witness; reconstruct B03 seed-73 init and evaluate two views."""

from io import BytesIO
import hashlib
import json
import math
from pathlib import Path

import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    HOST, HARD_EVENTS, evaluate_episode, new_progress, check_time,
    backend, EvaluationCoordinate, load_host, _reset_row,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState, build_master_addressed_initial_state,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    WelfordState,
)

OBJECT = "DISH-INIT-WITNESS-A01"
B03_OBJECT = "DISH-FORECAST-PACKAGE-B03"
SEED = 73
VIEWS = ("CONTROL", "FORECAST_PACKAGE")
EXPECTED_INITIAL_NORM = 38.24996300787587
HORIZON = 1200
SCALE_TICKS = 24
RENEWAL_BOUNDARY = (
    "corrected: observation['renew'] = countdown == 0 (3f4d447f6); raw flag renew_completed"
)
ZERO_TRAINING = {
    "ordinary_training_transitions": 0, "optimizer_steps": 0, "backward_passes": 0,
    "next_label_steps": 0, "passive_label_calls": 0,
}
B03_ARM_FOLDERS = {"CONTROL": "control", "FORECAST_PACKAGE": "forecast_package"}
B03_ROOT = Path(__file__).resolve().parents[4] / (
    "docs/research/candidates/degraded_incumbent_shadow_handover/b03_forecast_package_20260906"
)
REUSED_PAIR_PROVENANCE = (
    "B03 Delta = -272.0 from b03_forecast_package_20260906/forecast_package/summary.json paired_primary"
)


def master():
    return hashlib.sha256(f"{B03_OBJECT}/seed/{SEED}".encode("ascii")).digest()


def coordinate_keys():
    return tuple(
        EvaluationCoordinate(0, regime, schedule, "SPEED_4", 0).canonical_key()
        for regime in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK")
        for schedule in ("K8", "K4_TO_K12")
    )


def model_norm(state_dict):
    return math.sqrt(sum(float(value.double().square().sum()) for value in state_dict.values()))


def configuration():
    return {
        "host": HOST, "master_hex": master().hex(), "seed": SEED, "block": 0,
        "underlying_arm": "STRUCTURED", "views": list(VIEWS), "horizon": HORIZON,
        "renewal_boundary": RENEWAL_BOUNDARY, "torch_threads": torch.get_num_threads(),
        "training_dtype": "float32", "native_dtype": "float64",
    }


def reconstruct_initial():
    payload = build_master_addressed_initial_state(master=master(), block=0, arm="STRUCTURED")
    loaded = torch.load(BytesIO(payload), map_location="cpu", weights_only=False)
    welford = loaded["welford"]
    for name in ("actor", "snapshot", "critic"):
        if not isinstance(welford[name], WelfordState):
            raise TypeError(f"welford {name} is not WelfordState")
    initial_norm = model_norm(loaded["model"])
    facts = {
        "initialization_source": "reconstructed_from_master",
        "initializer_calls": 1,
        "initial_model_norm": initial_norm,
        "expected_initial_norm": EXPECTED_INITIAL_NORM,
        "norm_matches": abs(initial_norm - EXPECTED_INITIAL_NORM) <= 1e-9,
        "welford_counts": {name: int(welford[name].count) for name in ("actor", "snapshot", "critic")},
        "helper_constructed_objects": ["model", "optimizer"],
        "update": int(loaded["update"]),
        "policy_constructions": 0,
        "checkpoint_loads": 0,
    }
    return payload, facts


def load_b03_rows(root):
    root = Path(root)
    expected = coordinate_keys()
    loaded = {}
    for arm, folder in B03_ARM_FOLDERS.items():
        rows = json.loads((root / folder / "summary.json").read_text(encoding="utf8"))["evaluation_rows"]
        order = tuple(row["coordinate"] for row in rows)
        if order != expected:
            raise ValueError(f"{arm} evaluation coordinates differ from B03 order")
        loaded[arm] = {row["coordinate"]: row for row in rows}
    for key in expected:
        if loaded["CONTROL"][key]["reset"] != loaded["FORECAST_PACKAGE"][key]["reset"]:
            raise ValueError(f"B03 reset dictionaries differ at {key}")
    return loaded


def _pattern(d_control, d_package, complete):
    if not complete:
        return "incomplete"
    if d_control <= -SCALE_TICKS:
        return "D_C<=-24"
    if d_control > -SCALE_TICKS and d_package <= -SCALE_TICKS:
        return "D_C>-24 and D_P<=-24"
    if d_control >= SCALE_TICKS and d_package >= SCALE_TICKS:
        return "both>=+24"
    return "inside_or_heterogeneous"


def witness_result(new_rows, b03_rows):
    order = tuple(b03_rows["CONTROL"])
    new_by_view = {
        view: {row["coordinate"]: row for row in new_rows if row.get("view") == view}
        for view in VIEWS
    }
    complete = True
    result = {"scale_ticks": SCALE_TICKS, "reused_pair_provenance": REUSED_PAIR_PROVENANCE}
    d_values = {}
    for view in VIEWS:
        mapped = new_by_view[view]
        reused = b03_rows[view]
        view_complete = len(order) == 4 and all(key in mapped and key in reused for key in order)
        complete = complete and view_complete
        entries = []
        for key in order:
            if key not in mapped or key not in reused:
                continue
            j0 = mapped[key]["service_ticks"]
            j16 = reused[key]["service_ticks"]
            entries.append({
                "coordinate": key, "J_0": j0, "J_16": j16, "difference": j16 - j0,
                "source_new": mapped[key].get("source", f"new:zero_update:{view}"),
                "source_reused": f"reused:b03/{view}/summary.json",
            })
        differences = [row["difference"] for row in entries]
        j0s = [row["J_0"] for row in entries]
        j16s = [row["J_16"] for row in entries]
        d = (sum(differences) / 4) if view_complete else None
        d_values[view] = d
        result[view] = {
            "initial_view_mean": (sum(j0s) / len(j0s)) if j0s else None,
            "final_mean": (sum(j16s) / len(j16s)) if j16s else None,
            "rows": entries,
            "D": d,
        }
    result["pattern"] = _pattern(d_values["CONTROL"], d_values["FORECAST_PACKAGE"], complete)
    return result


def run_witness(output, deadline, progress, b03_root):
    torch.set_num_threads(1)
    progress["object"] = OBJECT
    progress["configuration"] = configuration()
    progress["zero_training"] = dict(ZERO_TRAINING)
    progress.setdefault("evaluation_rows", [])
    initial, facts = reconstruct_initial()
    progress["initialization"] = facts
    check_time(deadline)
    if not facts["norm_matches"]:
        progress["status"] = "INPUT_GAP"
        return
    try:
        b03 = load_b03_rows(b03_root)
    except ValueError as error:
        progress["status"] = "INPUT_GAP"
        progress["input_gap"] = str(error)
        return
    progress["reused_rows"] = []
    for view in VIEWS:
        for key in coordinate_keys():
            row = dict(b03[view][key])
            row["source"] = f"reused:b03/{view}/summary.json"
            progress["reused_rows"].append(row)
    try:
        library = load_host(HOST)
        check_time(deadline)
        for view in VIEWS:
            package = view == "FORECAST_PACKAGE"
            for key in coordinate_keys():
                check_time(deadline)
                reset = b03["CONTROL"][key]["reset"]
                native = backend.native_batch_from_rows((reset,), library=library)
                state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
                policy = BatchedRecurrentPolicy(
                    arm="STRUCTURED", checkpoint_bytes=initial, state=state,
                    forecast_package=package,
                )
                facts["policy_constructions"] += 1
                facts["checkpoint_loads"] += 1
                b03_row = b03[view][key]
                record = {
                    "coordinate": key, "view": view, "source": f"new:zero_update:{view}",
                    "reset": reset, "regime": b03_row["regime"], "schedule": b03_row["schedule"],
                    "speed": b03_row["speed"], "slot": b03_row["slot"], "block": b03_row["block"],
                    "parameter_norm_before": facts["initial_model_norm"],
                }
                progress["evaluation_rows"].append(record)
                evaluate_episode(native, policy, deadline, progress, record, horizon=HORIZON)
                after = model_norm(policy.model.state_dict())
                record["parameter_norm_after"] = after
                if abs(after - facts["initial_model_norm"]) > 1e-9:
                    raise ValueError("parameter norm moved during zero-update evaluation")
        progress["status"] = "COMPLETE"
    except TimeoutError:
        progress["status"] = "INCOMPLETE"
        raise
    finally:
        progress["completed_episodes"] = sum(
            1 for row in progress["evaluation_rows"] if row.get("complete")
        )
        progress["witness"] = witness_result(progress["evaluation_rows"], b03)
        if progress.get("status") == "COMPLETE" and progress["completed_episodes"] != 8:
            progress["status"] = "INCOMPLETE"
