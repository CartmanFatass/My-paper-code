"""Immutable B04 evidence and bit comparisons; no controller or model queries."""
from copy import deepcopy
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path
import re

import numpy as np

REPO = Path(__file__).resolve().parents[4]
DIRECTION = "uav_parent_adaptation"
OBJECT_ID = "parent_exact_planning_reuse_b08"
TAG = "b08_exact_planning_reuse_a01"
B04_SHA = "239360b03f5d7acf788bd9ae5d4dccbde4f9237e"
WORLD_IDS = tuple(range(29497000, 29497016))
VARIANTS = ("G2_original", "G2_reuse", "A2_original", "A2_reuse")
SEED = 29368991  # Identity only: the fixed deterministic order draws no RNG.
COUNT_KEYS = ("requested_candidates", "scored_candidates", "cached_candidates",
              "geometry_rows_computed", "geometry_rows_reused")
KINDS = ("motion", "mask", "joint", "option", "arrival")
LOGICAL_COSTS = {"worker_state_mask_requests": 134353178,
                 "model_physical_transitions": 498120,
                 "stationary_banks": 282, "stationary_candidate_rows": 96400,
                 "candidate_transit_ticks": 1904820, "model_branches": 1246}
ORIGINAL_FILES = {
    "config.json": {"bytes": 7959, "sha256": "3651cf713225bcd148297b7434b70270d35c592ecdfb9ca2240d1eb667a29c54"},
    "summary.json": {"bytes": 245904, "sha256": "8bdf64a6bafd75864c10df6a2c5992fb668c393ce271b02adccd472fe4226aa2"},
    "reading.json": {"bytes": 3989184, "sha256": "c9eaac15e69d1195e73710e4b071b5c196402bc6811b3a0bac333c771fd39363"},
}
OWN_SOURCE_NAMES = ("__init__.py", "segment.py", "controller.py", "inputs.py", "study.py", "reader.py", "run.py")
OWN_SOURCE_PATHS = tuple(f"experiments/candidates/{DIRECTION}/b08_exact_planning_reuse/{name}"
                         for name in OWN_SOURCE_NAMES)
EXTRA_SOURCE_PATHS = ("experiments/candidates/uav_parent_adaptation/b06_continuation_amortization/cycle.py",
                      "scripts/hmasd_admission.py")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_bytes(value):
    # Dict insertion order is immaterial; array/list order, numeric types and
    # signed floating zero remain significant in canonical JSON.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def json_record(value):
    return json.loads(record_bytes(value))


def same_record(actual, expected, label):
    if record_bytes(actual) != record_bytes(expected):
        raise ValueError(f"scientific record mismatch: {label}")


def same_array(actual, expected, label):
    a, b = np.asarray(actual), np.asarray(expected)
    if a.dtype.str != b.dtype.str or a.shape != b.shape or a.tobytes(order="C") != b.tobytes(order="C"):
        raise ValueError(f"scientific array bit/dtype/shape mismatch: {label}")


def array_binding(value):
    a = np.asarray(value)
    return {"dtype": a.dtype.str, "shape": list(a.shape),
            "sha256": hashlib.sha256(a.tobytes(order="C")).hexdigest()}


def payload_binding(payload):
    return {"arrays": {name: array_binding(value) for name, value in sorted(payload["arrays"].items())},
            "summary_sha256": hashlib.sha256(record_bytes(payload["summary"])).hexdigest(),
            "decisions_sha256": hashlib.sha256(record_bytes(payload["decisions"])).hexdigest()}


def same_payload(payload, expected, label):
    if set(payload["arrays"]) != set(expected["arrays"]):
        raise ValueError(f"scientific array key mismatch: {label}")
    for name in expected["arrays"]:
        same_array(payload["arrays"][name], expected["arrays"][name], f"{label}/{name}")
    same_record(payload["summary"], expected["summary"], f"{label}/summary")
    same_record(payload["decisions"], expected["decisions"], f"{label}/decisions")


def artifact(path, base):
    path, base = Path(path), Path(base)
    return {"path": str(path.relative_to(base)), "bytes": path.stat().st_size, "sha256": sha256(path)}


def checked_file(base, binding):
    base = Path(base).resolve()
    relative = Path(binding["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("absolute/traversing artifact path")
    path = (base / relative).resolve()
    if (not path.is_relative_to(base) or not path.is_file()
            or path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]):
        raise ValueError(f"bound artifact differs or is absent: {binding['path']}")
    return path


def load_arrays(path):
    with np.load(path, allow_pickle=False) as source:
        return {name: source[name] for name in source.files}


def load_trace(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def load_catalog(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def public_users(report):
    a = np.asarray(report)
    if a.shape != (133,) or a.dtype != np.dtype(np.float32):
        raise ValueError("original public report shape/dtype differs")
    return a[32:132].reshape(50, 2).astype(np.float64) * 1000.0


def source_bindings(frozen):
    result = {}
    for name in (*frozen, *OWN_SOURCE_PATHS, *EXTRA_SOURCE_PATHS):
        path = REPO / name
        result[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    for name, expected in frozen.items():
        same_record(result[name], expected, f"frozen B04 source/{name}")
    return result


class OriginalInputs:
    """Read/hash bound originals; never invoke their worker, policy or reader."""
    def __init__(self, records_root, bulk_root):
        self.records_root, self.bulk_root = Path(records_root).resolve(), Path(bulk_root).resolve()
        objects = {}
        for name, binding in ORIGINAL_FILES.items():
            base = self.bulk_root if name == "reading.json" else self.records_root
            path = checked_file(base, dict(binding, path=name))
            objects[name] = json.loads(path.read_text())
        self.config, self.summary, self.reading = (objects[name] for name in ORIGINAL_FILES)
        if (self.config["launch_sha"] != B04_SHA or self.summary["launch_sha"] != B04_SHA
                or self.reading["source_sha"] != B04_SHA or self.summary["status"] != "complete"
                or self.summary["worker_status"] != "complete" or self.reading["status"] != "complete"
                or self.reading["episodes_verified"] != 48 or self.reading["native_steps_verified"] != 24000
                or self.reading["new_fits"] != 0 or self.reading["updates"] != 0
                or self.reading["cycle_reuse"] is not False
                or any(self.reading[name] is not True for name in (
                    "all_native_physics_observations_actions_checked",
                    "all_nested_branches_and_stationary_candidates_reconstructed",
                    "all_native_decisions_reconstructed"))):
            raise ValueError("original complete frozen reader/source contract differs")
        same_record(self.summary["config"], self.config, "B04 config/summary binding")
        same_record(self.summary["config_artifact"], dict(ORIGINAL_FILES["config.json"], path="config.json"),
                    "B04 config artifact")
        same_record(self.summary["reading"], dict(ORIGINAL_FILES["reading.json"], path="reading.json"),
                    "B04 full-reader artifact")
        expected_order = [( ("T", "G2", "A2")[(i + offset) % 3], world)
                          for i, world in enumerate(WORLD_IDS) for offset in range(3)]
        if [(r["arm"], r["world_id"]) for r in self.summary["episodes"]] != expected_order:
            raise ValueError("original panel identity/order differs")
        self.rows, self.catalogs, bindings = {}, {}, []
        for row in self.summary["episodes"]:
            if row["arm"] not in ("G2", "A2"):
                continue
            if row["n"] != 8 or row["steps"] != 500 or row["complete"] is not True:
                raise ValueError("original selected complete cell differs")
            key = (row["arm"], row["world_id"])
            catalog = load_catalog(self.path(row["evidence_catalog"]))
            if set(catalog) != {"plans", "selections", "banks", "model_branches", "candidate_banks"}:
                raise ValueError("original catalog fields differ")
            if set(catalog["selections"]) != {"40", "120"} or set(catalog["plans"]) != {"40", "120"}:
                raise ValueError("original actual selection clocks differ")
            for kind in ("model_branches", "candidate_banks"):
                ids = [item["id"] for item in catalog[kind]]
                if len(ids) != len(set(ids)):
                    raise ValueError("original branch/bank ID duplicated")
            self.rows[key], self.catalogs[key] = row, catalog
            bindings.extend(row[name] for name in ("raw", "decisions", "evidence_catalog"))
            bindings.extend(branch[name] for branch in catalog["model_branches"] for name in ("raw", "decisions"))
            bindings.extend(bank["raw"] for bank in catalog["candidate_banks"])
        if len(bindings) != 1483 or len({b["path"] for b in bindings}) != len(bindings):
            raise ValueError("complete selected original artifact set differs")
        for binding in bindings:
            self.path(binding)
        self.bindings = sorted(bindings, key=lambda item: item["path"])
        self.sources = source_bindings(self.config["source_bindings"])

    def path(self, binding):
        if Path(binding["path"]).parts[:1] != ("raw",):
            raise ValueError("expected original raw artifact")
        return checked_file(self.bulk_root, binding)

    def binding(self):
        return {"source_sha": B04_SHA, "records_root": str(self.records_root), "bulk_root": str(self.bulk_root),
                "files": deepcopy(ORIGINAL_FILES), "selected_artifacts": deepcopy(self.bindings),
                "selected_artifact_bytes": sum(b["bytes"] for b in self.bindings),
                "full_original_reader_reused": True, "new_reader_model_queries": 0}

    def episode(self, arm, world_id):
        return ReferenceEpisode(self, self.rows[arm, world_id], self.catalogs[arm, world_id])


@dataclass
class SegmentReference:
    payload: dict
    start: int
    end: int
    entry_commands: np.ndarray
    entry_mask: int
    entry_users: np.ndarray
    kind: str
    branch_binding: dict
    plan_bound: bool = False
    expected_plan: object = None


class ReferenceEpisode:
    """One replay's private reference reads, with only a last-branch I/O cache."""
    def __init__(self, inputs, row, catalog):
        self.inputs, self.row, self.catalog = inputs, row, deepcopy(catalog)
        self.native = load_arrays(inputs.path(row["raw"]))
        self.decisions = load_trace(inputs.path(row["decisions"]))
        self.branches = {b["id"]: b for b in catalog["model_branches"]}
        self.banks = {b["id"]: b for b in catalog["candidate_banks"]}
        self._last_branch = None
        self._last_outer = None
        if len(self.decisions) != 500 or self.native["states"].shape != (501, 133):
            raise ValueError("bound controller history is incomplete")

    def branch(self, identifier):
        for cached in (self._last_branch, self._last_outer):
            if cached is not None and cached[0] == identifier:
                return cached[1]
        record = self.branches[identifier]
        payload = {"arrays": load_arrays(self.inputs.path(record["raw"])),
                   "decisions": load_trace(self.inputs.path(record["decisions"])),
                   "summary": deepcopy(record["summary"])}
        if identifier.endswith("/outer"):
            self._last_outer = (identifier, payload)
        else:
            self._last_branch = (identifier, payload)
        return payload

    def bank(self, identifier):
        return np.load(self.inputs.path(self.banks[identifier]["raw"]), allow_pickle=False)

    def segment(self, identifier):
        match = re.fullmatch(r"a2/first/([^/]+)/(prefix|suffix)", identifier)
        if match:
            first, kind = match.groups()
            branch_id = f"a2/first/{first}/outer"
            whole = self.branch(branch_id)
            start, end, segment_index = (40, 120, 0) if kind == "prefix" else (120, 500, 1)
            lo, hi = start - 40, end - 40
            arrays = {}
            for name, value in whole["arrays"].items():
                if name in ("positions", "controller_estimates"):
                    arrays[name] = value[lo:hi + 1]
                elif name in ("reports", "report_times"):
                    take = (whole["arrays"]["report_times"] >= start) & (whole["arrays"]["report_times"] < end)
                    arrays[name] = value[take]
                else:
                    arrays[name] = value[lo:hi]
            decisions = deepcopy(whole["decisions"][lo:hi])
            if kind == "suffix":
                if decisions[0].pop("predicted_temporal_selection", None) != whole["summary"]["inner_selection"]:
                    raise ValueError("original outer boundary annotation differs")
            payload = {"arrays": arrays, "decisions": decisions,
                       "summary": deepcopy(whole["summary"]["segments"][segment_index])}
        else:
            if identifier not in self.branches:
                raise ValueError(f"unexpected model segment ID: {identifier}")
            branch_id = identifier
            whole = self.branch(branch_id)
            summary = deepcopy(whole["summary"])
            summary.pop("identity")
            start, end = summary["start_t"], summary.get("end_t", summary["horizon"])
            payload = dict(arrays=whole["arrays"], decisions=whole["decisions"], summary=summary)
            kind = "inner" if identifier.startswith("a2/") else "actual"
        if identifier.startswith("actual/") or kind == "prefix":
            command = self.native["actions"][start - 1]
            mask = int(self.native["mask"][start - 1])
            users = public_users(self.native["states"][start - 10])
        else:
            first = identifier.split("/")[2]
            outer = self.branch(f"a2/first/{first}/outer")
            command, mask = outer["arrays"]["actions"][79], int(outer["arrays"]["masks"][79])
            users = public_users(outer["arrays"]["reports"][7])
            same_array(payload["arrays"]["controller_estimates"][0],
                       outer["arrays"]["controller_estimates"][80], "nested entering controller estimate")
        # The original compact inner selection retains only the winning full
        # plan. All actual and first-stage alternatives retain their full plans.
        plan_bound, expected_plan = False, None
        if kind in ("actual", "prefix"):
            local = identifier.split("/")[2] if kind == "prefix" else identifier.rsplit("/", 1)[-1]
            choices = self.catalog["selections"][str(start)]["branches"]
            expected_plan = next(item["plan"] for item in choices if item["id"] == local)
            plan_bound = True
        elif kind == "suffix":
            expected_plan = outer["summary"]["inner_selection"]["selected_plan"]
            plan_bound = True
        else:
            local = identifier.rsplit("/", 1)[-1]
            selection = outer["summary"]["inner_selection"]
            if local == "stay":
                plan_bound = True
            elif local == selection["selected_branch"]:
                plan_bound, expected_plan = True, selection["selected_plan"]
        return SegmentReference(payload, start, end, command, mask, users, kind,
                                deepcopy(self.branches[branch_id]), plan_bound, deepcopy(expected_plan))
