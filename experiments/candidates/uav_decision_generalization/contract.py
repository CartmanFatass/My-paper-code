"""Outcome-free B01 contract, layout selection and lossless canonical records.

No native imports or RNG draws occur here. Construction slots are immutable identities;
list/display order never supplies a requested fixed policy's fallback.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

DIRECTION = "uav_decision_generalization"
SCHEMA = 1
BASES = (106100000, 106200000, 106300000)
HORIZON = 500
MAX_MENU = 8
AREA = 5000
TEMPERATURE = 0.02
MAX_NATIVE_STEPS = 1_736_000
MAX_STATIC_CALLS = 2_307_840
MAX_CORRECTNESS_EPISODES = 16
MAX_CPU_SECONDS = 18_000
MAX_DISK_BYTES = None
KINDS = ("kmeans_plain", "subset_relay", "subset_flat")
SOURCE_SHA256 = {
    "experiments/candidates/coupled_host_joint_skills_stage1/host.py":
        "92b75c0317009380108bd45429892e49ca857b901ae1adbcd5bfe483d89ef469",
    "experiments/candidates/coupled_host_joint_skills_stage1/planner.py":
        "5c23f4c8a25df55052fa6eb4bb0da65fcf0f079560789b8abd7db416222a0aa6",
    "experiments/candidates/coupled_host_joint_skills_stage1/menus.py":
        "15b818e0250141b45a47480d5acaa6b0f217c8ce8fe8c35ef6a7abb765102886",
    "envs/pettingzoo/uav_env.py":
        "fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e",
    "envs/pettingzoo/scenario2.py":
        "277374f365e8eeda882de53d53cc051c1534fe210622fee74d7b5a8f9d2cf2f2",
}


def encode_json(value: Any) -> bytes:
    """Python's shortest round-trip decimal JSON, finite numbers only, one LF."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False, ensure_ascii=True) + "\n").encode("ascii")


def digest(value: Any) -> str:
    return hashlib.sha256(encode_json(value)).hexdigest()


def worlds(split="fresh"):
    if split not in ("train", "fresh"):
        raise ValueError("old test is excluded")
    for block, base in enumerate(BASES, 1):
        offsets = range(256) if split == "train" else range(30000,30128)
        for offset in offsets:
            yield {"block": block, "split": split, "offset": offset, "world": base+offset}


def rows(value: Any, n: int, width: int) -> list[list[float]]:
    if len(value) != n or any(len(row) != width for row in value):
        raise ValueError(f"expected {n} x {width} coordinates")
    result = []
    for row in value:
        if any(isinstance(x, bool) for x in row):
            raise ValueError("boolean coordinate")
        converted = [float(x) for x in row]
        if not all(math.isfinite(x) for x in converted):
            raise ValueError("non-finite coordinate")
        result.append([0.0 if x == 0 else x for x in converted])
    return result


def canonical_layout(value: Any) -> list[list[float]]:
    return sorted(rows(value, 6, 3))


def layout_bytes(value: Any) -> bytes:
    """The frozen tie/dedup key: numerically sorted XYZ rows, .17g decimal triples."""
    return ("\n".join(",".join(format(x, ".17g") for x in row)
                      for row in canonical_layout(value)) + "\n").encode("ascii")


def select_menu(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Choose preferred slots, canonical dedupe, then fill holes relay/flat/plain.

    The source build_candidates has already applied its own rounded, row-sensitive
    dedupe. This layer adds the reviewed exact, row-insensitive dedupe; it does not
    modify that imported generator or insert any scored planner layout.
    """
    pool = []
    for index, candidate in enumerate(raw):
        kind, k = candidate["kind"], int(candidate["k"])
        if kind not in KINDS or k not in (4, 5, 6):
            raise ValueError("unexpected raw candidate metadata")
        xyz = canonical_layout(candidate["positions_xyz"])
        if any(not (0 <= x <= AREA and 0 <= y <= AREA and 50 <= z <= 150)
               for x, y, z in xyz):
            raise ValueError("illegal raw layout")
        key = layout_bytes(xyz)
        pool.append({"kind": kind, "k": k, "positions_xyz": xyz,
                     "source_index": int(candidate.get("index", index)),
                     "served": list(candidate.get("served", [])),
                     "layout_sha256": hashlib.sha256(key).hexdigest(), "_key": key})
    def rank(c):
        return (-len(c["served"]), c["layout_sha256"], c["source_index"])
    def first(kind, k=None, excluded=()):
        return next(iter(sorted((c for c in pool if c["kind"] == kind
                                 and (k is None or c["k"] == k)
                                 and c["_key"] not in excluded), key=rank)), None)
    preferred = [first("kmeans_plain", k) for k in (4, 5, 6)]
    preferred += [first("subset_relay", k) for k in (4, 5, 6)]
    relay_keys = {c["_key"] for c in preferred[3:] if c is not None}
    preferred += [first("subset_relay", excluded=relay_keys), first("subset_flat")]
    selected, seen, dropped = {}, set(), []
    for slot, c in enumerate(preferred):
        if c is None:
            continue
        if c["_key"] in seen:
            dropped.append({"construction_slot": slot, "layout_sha256": c["layout_sha256"]})
        else:
            selected[slot] = (c, "preferred")
            seen.add(c["_key"])
    fill = [c for kind in ("subset_relay", "subset_flat", "kmeans_plain")
            for c in sorted((c for c in pool if c["kind"] == kind), key=rank)]
    for slot in range(MAX_MENU):
        if slot in selected:
            continue
        c = next((c for c in fill if c["_key"] not in seen), None)
        if c is not None:
            selected[slot] = (c, "fill")
            seen.add(c["_key"])
    if not selected:
        raise ValueError("empty legal menu")
    menu = [{**{key: value for key, value in c.items() if key != "_key"},
             "construction_slot": slot, "slot_origin": origin}
            for slot, (c, origin) in sorted(selected.items())]
    return menu, {"source_candidates": len(raw), "canonical_distinct":
                  len({c["_key"] for c in pool}), "preferred_duplicates": dropped,
                  "legal_candidates": len(menu)}


def make_features(initial, users, bs, assigned: list[dict[str, Any]]) -> dict[str, Any]:
    """Only permitted learner inputs; provenance and scores belong to other files."""
    plans = [{"construction_slot": int(c["construction_slot"]), "kind": c["kind"],
              "k": int(c["k"]), "assigned_targets_xyz": rows(c["assigned_targets_xyz"], 6, 3)}
             for c in sorted(assigned, key=lambda c: c["construction_slot"])]
    canonical = {"initial_uav_xyz": rows(initial, 6, 3), "user_xy": rows(users, 50, 2),
                 "bs_xyz": rows([bs], 1, 3)[0], "plans": plans,
                 "legal_mask": [any(c["construction_slot"] == s for c in plans)
                                for s in range(MAX_MENU)]}
    validate_features(canonical)
    canonical_hash = digest(canonical)
    # Hash permutation: no RNG stream, labels, world IDs or source paths.
    order = sorted((c["construction_slot"] for c in plans),
                   key=lambda slot: hashlib.sha256(
                       f"{canonical_hash}:{slot}".encode("ascii")).hexdigest())
    canonical["display_order"] = order
    return canonical


def validate_features(features: dict[str, Any]) -> None:
    permitted = {"initial_uav_xyz", "user_xy", "bs_xyz", "plans", "legal_mask", "display_order"}
    if set(features) - permitted or not (permitted - {"display_order"}) <= set(features):
        raise ValueError("outcome/provenance field or missing feature")
    rows(features["initial_uav_xyz"], 6, 3)
    rows(features["user_xy"], 50, 2)
    rows([features["bs_xyz"]], 1, 3)
    plans = features["plans"]
    if not 1 <= len(plans) <= MAX_MENU:
        raise ValueError("bad legal plan count")
    slots = []
    for c in plans:
        if set(c) != {"construction_slot", "kind", "k", "assigned_targets_xyz"}:
            raise ValueError("unexpected plan feature")
        slot = c["construction_slot"]
        if type(slot) is not int or slot not in range(MAX_MENU):
            raise ValueError("bad construction slot")
        if c["kind"] not in KINDS or type(c["k"]) is not int or c["k"] not in (4, 5, 6):
            raise ValueError("bad plan metadata")
        xyz = rows(c["assigned_targets_xyz"], 6, 3)
        if any(not (0 <= x <= AREA and 0 <= y <= AREA and 50 <= z <= 150) for x, y, z in xyz):
            raise ValueError("illegal target")
        slots.append(slot)
    if len(set(slots)) != len(slots):
        raise ValueError("repeated construction slot")
    if (len(features["legal_mask"]) != MAX_MENU
            or any(type(v) is not bool for v in features["legal_mask"])
            or features["legal_mask"] != [s in slots for s in range(MAX_MENU)]):
        raise ValueError("mask disagrees with construction slots")
    if "display_order" in features and (any(type(v) is not int for v in features["display_order"])
                                         or sorted(features["display_order"]) != sorted(slots)):
        raise ValueError("display order is not an inversion of legal slots")


def fallback_slot(requested: int, legal: list[int]) -> int:
    if type(requested) is not int or requested not in range(MAX_MENU) or not legal:
        raise ValueError("invalid fixed policy")
    return requested if requested in legal else min(legal)


def soft_targets(q: list[float]) -> list[float]:
    if not q or not all(math.isfinite(x) for x in q):
        raise ValueError("invalid native Q")
    shifted = [math.exp((x - max(q)) / TEMPERATURE) for x in q]
    total = sum(shifted)
    return [x / total for x in shifted]


def ordinary_choices(plans, static_c, initial_c) -> dict[str, int]:
    """Static and fixed travel surrogate; both ties use max/total distance, then slot."""
    def best(travel):
        def key(c):
            slot = c["construction_slot"]
            alpha = min(c["max_travel_distance_m"] / (30 * HORIZON), 1.0)
            score = ((1 - alpha) * static_c[slot] + alpha * initial_c
                     if travel else static_c[slot])
            return (-score, c["max_travel_distance_m"], c["total_travel_distance_m"], slot)
        return min(plans, key=key)["construction_slot"]
    return {"static": best(False), "travel": best(True)}


REFERENCE_SHA = "61a2dfa9cde0178d482d0a079c5629c3bcb7789e"
ORIGINAL_CONTRACT_SHA256 = "ce85822ca29c139d98cdcb44f57d698175b70ac1d474b716c0663008cf347402"
N_FINAL_DIGESTS = {
    1: "c61e2846205748d7168e93fc48d0d3c2b0b4b3695ab3cb5223c1fd7a123a786d",
    2: "8e4e76de7a3e300e8a504b2fe04a76128f7799ca7126d616c105e6e57ff4c115",
    3: "be386396f4f3311cd0ad7d5941499883fcd126544b8c0f32236fd0f54d8bdb2e",
}
PARAMETERS = {"A":348417,"R":208449,"N":105473}
TENSOR_SHAPES = {"U":(6,12),"Y":(50,52),"B":(3,),"M":(14,),
                 "E_UY":(6,50,8),"E_UU":(6,5,8),"E_UB":(6,8)}


def frozen_contract():
    return {"schema":1,"direction":DIRECTION,"reference_sha":REFERENCE_SHA,
            "original_contract_sha256":ORIGINAL_CONTRACT_SHA256,"sources":SOURCE_SHA256,
            "bases":BASES,"training_offsets":[0,255],"fresh_offsets":[30000,30127],
            "tensor_shapes":TENSOR_SHAPES,"parameters":PARAMETERS,
            "architecture_A":"5377-64-64-1; GELU between linears",
            "architecture_R":"U/Y/B 2-layer GELU encoders; three typed mean-message residual layers; 206-64-1",
            "model_seed_offsets":{"A":41001,"R":42001},"order_seed_offset":20002,
            "optimizer":{"name":"AdamW","lr":.001,"weight_decay":.0001,"betas":[.9,.999],"eps":1e-8},
            "epochs":64,"batch_size":32,"endpoint":"final","dtype":"float32","tf32":False,
            "old_N_final_digests":N_FINAL_DIGESTS,"temperature":TEMPERATURE,
            "horizon":HORIZON,"fixed_requested_slot":3,"exact_tie":"first display",
            "ceilings":{"native_steps":MAX_NATIVE_STEPS,"static_calls":MAX_STATIC_CALLS,
                        "cpu_seconds":MAX_CPU_SECONDS,"gpu_seconds":3600,
                        "fits":6,"updates":3072,"endpoint_contexts":4992,"reader_contexts":4992}}
