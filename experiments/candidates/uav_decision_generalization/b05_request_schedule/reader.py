"""Complete saved-trace B05 audit, with no native host or optimizer replay.

FIFO, geometry, action mapping, features and G are reconstructed here. Physical
algebra/motion reuse the separately written B03 reader; frozen inference uses
the bound scorer factory. Only committed payloads are replayed. All effects
belong to the admitted reader entry, never module import or implementation tests.
"""
from __future__ import annotations

from collections import deque
import hashlib
import itertools
import json
import ast
from pathlib import Path

import numpy as np

from . import contract as c
from .storage import G_DTYPE, STATE_DTYPE, R_SHAPES, R_STATS


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def same(actual, expected, message):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.array_equal(actual, expected), message)


def packed(value):
    return np.packbits(np.asarray(value, dtype=bool).ravel(), bitorder="little")


def unpack(value, shape):
    size = int(np.prod(shape))
    bits = np.unpackbits(np.asarray(value, dtype=np.uint8), bitorder="little")
    require(not bits[size:].any(), "nonzero packed mask padding")
    return bits[:size].reshape(shape).astype(bool)


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            result.update(block)
    return result.hexdigest()


def contained(root, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and ".." not in relative.parts,
            "manifest path must be relative and contained")
    path = (Path(root) / relative).resolve()
    require(path.is_relative_to(Path(root).resolve()), "manifest path escapes worker root")
    return path


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, sort_keys=True, allow_nan=False,
                                    separators=(",", ":")) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def finite_array(value):
    require(not value.dtype.hasobject, "object trace array forbidden")
    if value.dtype.names:
        for name in value.dtype.names:
            finite_array(value[name])
    elif value.dtype.kind in "fc":
        require(np.isfinite(value).all(), "nonfinite trace array")


def load_arrays(path, specification):
    with np.load(path, allow_pickle=False) as source:
        require(set(source.files) == set(specification), "trace array roster differs")
        result = {}
        for name, (shape, dtype) in specification.items():
            value = source[name]
            require(value.shape == shape and value.dtype == np.dtype(dtype),
                    f"trace shape/dtype differs: {name}")
            finite_array(value)
            result[name] = value
    return result


MISSION_SHAPES = {
    "users": ((50, 2), "int32"), "rates": ((4,), "uint8"), "pairs": ((3, 2), "uint8"),
    "initial_slots": ((6,), "uint8"), "arrival_draws": ((48, 4), "float64"),
    "arrival_tape": ((48, 4), "bool"), "states": ((1201,), STATE_DTYPE),
    "raw_actions": ((1200, 6, 3), "float64"),
    "executed_actions": ((1200, 6, 3), "float64"), "arrivals": ((1200, 4), "bool"),
    "tick_cost": ((1200,), "uint16"), "reports": ((60,), G_DTYPE),
    "features": ((60, 4, 303), "float32"), "commands": ((60, 6), "uint8"),
    "action": ((60,), "uint8"), "g_action": ((60,), "int8"),
    "greedy_action": ((60,), "int8"), "total_q": ((60, 4), "float64"),
    "residual": ((60, 4), "float32"), "nn_complete": ((60,), "bool"),
    "exploration_draw": ((60,), "float64"), "exploratory_action": ((60,), "int8"),
    "macro_cost": ((60,), "uint32"), "update_number": ((60,), "int32"),
    "update_samples": ((60, 128), "int32"), "update_values": ((60, 6), "float64"),
    "offline_wall": ((60,), "float64"), "offline_cpu": ((60,), "float64"),
    "initial_audit_residual": ((60, 4), "float32"),
    "initial_audit_complete": ((60,), "bool"),
}


def expected_roster():
    """Literal ordered launch roster, including rotations without new worlds."""
    result = [(f"train/fit{fit}", int(world)) for fit, worlds in enumerate(c.TRAIN_WORLDS)
              for world in worlds]
    labels = ("G", "R", "L0", "L1", "L2")
    for index, world in enumerate(c.MAIN_WORLDS):
        result.extend((f"main/{label}", int(world))
                      for label in labels[index % 5:] + labels[:index % 5])
    names = ("G", "R", "initial", "final")
    for fit, world in enumerate(c.AUDIT_WORLDS):
        result.extend((f"audit{fit}/{name}", int(world))
                      for name in names[fit % 4:] + names[:fit % 4])
    return result


def validate_manifest(worker_root, manifest, summary, source_identity, meter):
    require(manifest["schema"] == summary["schema"] == 1, "worker schema")
    require(summary["status"] == "COMPLETE" and summary["object"] == "B05_request_schedule",
            "full reader requires complete B05 worker")
    require(summary["missions"] == 1708 and summary["source_identity"] == source_identity,
            "worker count/source identity")
    require([(r["label"], r["world"]) for r in manifest["records"]] == expected_roster(),
            "literal complete ordered mission roster")
    require(summary["fits"] == manifest["fits"] and
            summary["endpoint_counts"] == manifest["endpoint_counts"], "worker count mirrors")
    require(summary["cost"]["counts"]["actual_native_steps"] == 2049600,
            "complete actual native transition count")
    required = {name for record in manifest["records"] for name in (record["npz"], record["metadata"])}
    required |= {"endpoint-counts.json"} | {f"fit{fit}.json" for fit in range(3)}
    for fit in manifest["fits"]:
        for endpoint in ("initial", "final", "training"):
            required.add(f"checkpoints/fit{fit['fit']}_{endpoint}.pt")
    require(required <= set(manifest["files"]), "required evidence absent from manifest")
    for name, identity in manifest["files"].items():
        meter.check()
        path = contained(worker_root, name)
        require(path.is_file() and path.stat().st_size == identity["bytes"],
                f"manifest missing file/size: {name}")
        require(file_hash(path) == identity["sha256"], f"manifest byte hash: {name}")
        meter.add("reader_file_hashes")
    same_fit = read_json(contained(worker_root, "endpoint-counts.json"))
    require(same_fit == manifest["endpoint_counts"], "endpoint count file differs")
    for record in manifest["records"]:
        require(record["status"] == "COMPLETE" and record["completed_native_steps"] == 1200,
                "incomplete actual mission")
    return manifest["records"]


def geometry(world):
    """Reconstruct only selected native/jitter/user domains, not old B03 schedule."""
    native = np.random.RandomState(world)
    positions = np.asarray([[native.uniform(0, 5000), native.uniform(0, 5000),
                             native.uniform(50, 150)] for _ in range(6)], dtype=np.float64)
    far = np.asarray(((500, 500), (4500, 500), (4500, 4500), (500, 4500)), dtype=float)
    jitter = np.random.Generator(np.random.PCG64(np.random.SeedSequence([world, 1])))
    far += jitter.uniform(-50, 50, size=(4, 2))
    users = []
    disks = np.random.Generator(np.random.PCG64(np.random.SeedSequence([world, 2])))
    for center in np.concatenate(([[2500., 2500.]], far)):
        for _ in range(10):
            u, v = disks.uniform(0, 1, 2)
            users.append(np.rint(center + 100 * np.sqrt(u) *
                                 np.asarray((np.cos(2 * np.pi * v), np.sin(2 * np.pi * v)))))
    return positions, np.asarray(users, dtype=np.int32)


def slots_for(users):
    mean = users[10:].reshape(4, 10, 2).astype(np.float64).mean(axis=1)
    xy = 2500. + (mean[:, None, :] - 2500.) * np.asarray([1/3, 2/3])[None, :, None]
    return np.concatenate((xy, np.full((4, 2, 1), 100.)), axis=2).reshape(8, 3)


def assignment(users, rates, positions):
    clusters = sorted(sorted(range(4), key=lambda k: (-int(rates[k]), k))[:3])
    selected = np.asarray([2*k + side for k in clusters for side in range(2)], dtype=np.uint8)
    distances = np.linalg.norm(positions[:, None] - slots_for(users)[selected][None], axis=-1)
    def objective(order):
        distance = distances[np.asarray(order), np.arange(6)]
        return int(np.ceil(distance / 30).sum()), float(distance.sum()), order
    order = min(itertools.permutations(range(6)), key=objective)
    current = np.empty(6, dtype=np.uint8)
    current[list(order)] = selected
    return current, np.asarray([order[0:2], order[2:4], order[4:6]], dtype=np.uint8)


def lawful(slots, pairs):
    require(np.asarray(slots).shape == (6,) and np.all(np.asarray(slots) < 8), "slot range")
    require(sorted(np.asarray(pairs).ravel().tolist()) == list(range(6)), "pair partition")
    occupied = []
    for pair in pairs:
        left, right = map(int, np.asarray(slots)[pair])
        require(left // 2 == right // 2 and {left % 2, right % 2} == {0, 1}, "pair slots")
        occupied.append(left // 2)
    require(len(set(occupied)) == 3, "distinct pair targets")


def candidates(state):
    current, pairs = state["slots"], state["pairs"]
    lawful(current, pairs)
    occupied = {int(current[int(pair[0])]) // 2 for pair in pairs}
    missing, = set(range(4)) - occupied
    destination = slots_for(state["users"])[[2*missing, 2*missing + 1]]
    choices = np.tile(current, (4, 1))
    for action, pair in enumerate(pairs, 1):
        def objective(order):
            distance = np.linalg.norm(state["positions"][list(order)] - destination, axis=1)
            return int(np.ceil(distance / 30).max()), float(distance.sum()), order
        order = min(itertools.permutations(map(int, pair)), key=objective)
        choices[action, list(order)] = [2*missing, 2*missing + 1]
    return choices


def public(row, users, rates, pairs, world):
    return {"world": int(world), "tick": int(row["tick"]), "users": users, "rates": rates,
            "positions": row["positions"].copy(), "ack": unpack(row["ack"], (50,)),
            "counts": row["counts"].astype(np.int64), "progress": row["progress"].astype(np.int64),
            "slots": row["slots"].copy(), "pairs": pairs}


def report_identity(row, state, costs=False):
    for key in ("positions", "counts", "progress", "slots", "tick"):
        same(row[key], state[key], "public report " + key)
    same(unpack(row["ack"], (50,)), state["ack"], "public report ACK")
    lawful(row["slots"], state["pairs"])
    if costs:
        require(row["complete"] == 1, "uncommitted G query")


def predict_g(state):
    """Independent vectorized recurrence, preserving the source's FP64 order."""
    time0 = state["tick"]
    require(time0 < 1200, "no terminal G query")
    horizon = min(240, 1200 - time0)
    choices = candidates(state)
    xyz = np.tile(state["positions"], (4, 1, 1))
    integer_heads = np.tile(state["counts"], (4, 1))
    head_run = np.tile(state["progress"], (4, 1))
    unknown = np.zeros((4, 4), dtype=np.float64)
    accumulated = np.zeros(4, dtype=np.float64)
    destinations = slots_for(state["users"])
    previous = np.tile(state["slots"], (4, 1))
    pairs = np.asarray(state["pairs"], dtype=np.int64)
    boundaries = 0
    for offset in range(horizon):
        tick = time0 + offset
        active = previous if offset < 20 else choices
        target = destinations[active]
        if tick > time0 and tick <= 940 and tick % 20 == 0:
            unknown += state["rates"].astype(np.float64) / 10.
            boundaries += 1
        accumulated += (integer_heads + unknown).sum(axis=1)
        direction = target - xyz
        length = np.linalg.norm(direction, axis=-1)
        xyz += direction * (30. / np.maximum(30., length))[:, :, None]
        near = np.linalg.norm(xyz - target, axis=-1) <= 1.
        served = np.zeros((4, 4), dtype=bool)
        served[np.arange(4)[:, None], active[:, pairs[:, 0]] // 2] = near[:, pairs].all(axis=2)
        known_service = served & (integer_heads > 0)
        unknown_service = served & (integer_heads == 0)
        head_run = np.where(known_service, head_run + 1, 0)
        finished = known_service & (head_run == 20)
        integer_heads -= finished
        head_run[finished] = 0
        unknown = np.where(unknown_service, np.maximum(0., unknown - 1. / 20), unknown)
    accumulated += 240 * (integer_heads + unknown).sum(axis=1)
    return accumulated, horizon, boundaries


def features(state, raw_g):
    xyz = state["positions"].copy()
    xyz[:, :2] /= 5000.
    xyz[:, 2] = (xyz[:, 2] - 50.) / 100.
    members = np.zeros((6, 3), dtype=np.float64)
    for k, pair in enumerate(state["pairs"]):
        members[pair, k] = 1.
    common = np.concatenate((state["users"].ravel() / 5000., state["rates"].astype(float) / 10.,
                             xyz.ravel(), state["ack"], state["counts"] / 48.,
                             state["progress"] / 20., members.ravel(),
                             np.eye(8)[state["slots"]].ravel()))
    return np.concatenate((np.tile(common, (4, 1)),
                           np.eye(8)[candidates(state)].reshape(4, 48), np.eye(4),
                           np.full((4, 1), state["tick"] / 1200.),
                           np.tile(raw_g / 1200., (4, 1))), axis=1).astype(np.float32)


def compose(raw_g, residual):
    require(np.asarray(raw_g).dtype == np.float64 and np.asarray(residual).dtype == np.float32,
            "canonical Q dtypes")
    return raw_g / 1200. + residual.astype(np.float64)


def greedy(total, raw_g):
    return int(np.lexsort((np.arange(4), raw_g, total))[0])


class FIFO:
    """Scalar head accounting; public reconstruction gives unknown old ages."""

    def __init__(self, counts=None, progress=None):
        counts = [0] * 4 if counts is None else counts
        self.queues = [deque({"request_id": None, "cluster": k, "arrival_tick": None}
                             for _ in range(int(n))) for k, n in enumerate(counts)]
        self.progress = [0] * 4 if progress is None else list(map(int, progress))
        self.requests, self.completions = [], []
        self.area, self.next_id = 0, 0
        self.interruptions = [0] * 4

    @property
    def counts(self):
        return np.asarray([len(queue) for queue in self.queues], dtype=np.int64)

    def arrive(self, tick, arrivals):
        for k, bit in enumerate(arrivals):
            if bit:
                require(tick % 20 == 0 and tick <= 940, "arrival grid")
                request = {"request_id": self.next_id, "cluster": k, "arrival_tick": tick}
                self.next_id += 1
                self.requests.append(request)
                self.queues[k].append(request)
        return int(self.counts.sum())

    def charge(self):
        charged = int(self.counts.sum())
        self.area += charged
        return charged

    def service(self, tick, ack):
        qualified = np.asarray(ack)[10:].reshape(4, 10).sum(axis=1) >= 8
        for k, queue in enumerate(self.queues):
            if queue and qualified[k]:
                self.progress[k] += 1
                if self.progress[k] == 20:
                    self.completions.append({"request": queue.popleft(), "completion_tick": tick + 1})
                    self.progress[k] = 0
            else:
                if queue and self.progress[k]:
                    self.interruptions[k] += 1
                self.progress[k] = 0


def longest_false(mask):
    run = best = 0
    for value in mask:
        run = 0 if value else run + 1
        best = max(best, run)
    return best


def distribution(values):
    if not values:
        return {"n": 0, "p50": None, "p90": None, "max": None}
    value = np.asarray(values, dtype=np.float64)
    return {"n": len(values), "p50": float(np.percentile(value, 50)),
            "p90": float(np.percentile(value, 90)), "max": float(value.max())}


def marker_gap(committed, counter, interrupted, label):
    gap = int(committed) - int(counter)
    require(gap in ((0, 1) if interrupted else (0,)), label + " commit/counter gap")
    return gap


def physical_state(positions, users):
    from experiments.candidates.uav_decision_generalization.b03_joint_window.independent import physical_state as reconstruct
    return reconstruct(positions, users)


def motion(positions, raw):
    from experiments.candidates.uav_decision_generalization.b03_joint_window.independent import motion as reconstruct
    return reconstruct(positions, raw)


class Audit:
    def __init__(self, meter, source_identity):
        self.meter, self.source_identity = meter, source_identity
        self.counts = {}

    def add(self, name, amount=1):
        require(isinstance(amount, int) and amount >= 0, "reader count must be nonnegative integer")
        self.counts[name] = self.counts.get(name, 0) + amount
        self.meter.add("reader_" + name, amount)

    def reserve(self, name, limit, amount=1):
        require(self.counts.get(name, 0) + amount <= limit, "reader exposure bound: " + name)
        self.add(name, amount)

    def physics(self, row, users, role):
        self.meter.check()
        require(role in ("native", "R_initial", "R_prefix"), "physical reconstruction role")
        limit = {"native": 2051308, "R_initial": 2100, "R_prefix": 4424000}[role]
        self.reserve(role + "_physical_attempts", limit)
        result = physical_state(row["positions"], users)
        self.add(role + "_physical_states")
        self.add(role + "_physical_relations", 321)
        for name in ("connections", "uav_connections", "bs_connections"):
            same(unpack(row[name], result[name].shape), result[name], "native physical " + name)
        for name in ("routes", "route_lengths"):
            same(row[name], result[name], "native physical " + name)
        ack = np.any(result["connections"] & (result["route_lengths"] > 0)[:, None], axis=0)
        same(unpack(row["ack"], (50,)), ack, "native physical ACK")
        return ack

    def g(self, row, state, role):
        report_identity(row, state, costs=True)
        self.meter.check()
        self.add("G_attempts")
        horizon = min(240, 1200 - state["tick"])
        self.reserve("G_reserved_candidate_ticks", 292844160, 4 * horizon)
        self.add("G_" + role + "_queries")
        costs, horizon, boundaries = predict_g(state)
        self.add("G_queries")
        self.add("G_candidate_values", 4)
        self.add("G_candidate_ticks", 4 * horizon)
        self.add("G_cluster_recurrences", 16 * horizon)
        self.add("G_kinematic_uav_steps", 24 * horizon)
        self.add("G_future_arrival_cluster_additions", 16 * boundaries)
        same(row["costs"], costs, "exact canonical G recurrence")
        return costs


class FrozenModels:
    """One CPU scorer per saved endpoint; constructors and all rows are charged."""

    def __init__(self, worker_root, manifest, audit):
        import torch
        from .learner import ResidualScorer, _digest
        self.torch, self.audit, self.models, self.payloads = torch, audit, {}, {}
        for fit in range(3):
            record = manifest["fits"][fit]
            require(record["fit"] == fit and record == read_json(worker_root / f"fit{fit}.json"),
                    "fit metadata lineage")
            for endpoint in ("initial", "final"):
                relative = f"checkpoints/fit{fit}_{endpoint}.pt"
                identity = manifest["files"][relative]
                require(record[endpoint]["bytes"] == identity["bytes"] and
                        record[endpoint]["sha256"] == identity["sha256"], "checkpoint identity mirrors")
                # Bytes were bound before any unpickling. Deployment snapshots
                # contain only tensors and primitive metadata.
                payload = torch.load(contained(worker_root, relative), map_location="cpu", weights_only=True)
                require(payload["schema"] == 1 and payload["fit_index"] == fit and
                        payload["init_seed"] == c.TORCH_INIT_SEEDS[fit], "endpoint schema/fit/seed")
                audit.meter.check()
                audit.reserve("scorer_constructor_attempts", 6)
                model = ResidualScorer(c.TORCH_INIT_SEEDS[fit])
                audit.add("scorer_constructors")
                require(_digest(model.state_dict()) == payload["certificate"]["initial_parameter_sha256"],
                        "source-seeded initial parameters")
                current = model.state_dict()
                require(payload["online"].keys() == current.keys(), "scorer weight keys")
                for name, value in payload["online"].items():
                    require(value.device.type == "cpu" and value.dtype == torch.float32 and
                            value.shape == current[name].shape and bool(torch.isfinite(value).all()),
                            "scorer weight finite/shape/dtype")
                model.load_state_dict(payload["online"], strict=True)
                model.eval().requires_grad_(False)
                require(_digest(model.state_dict()) == payload["certificate"]["parameter_sha256"],
                        "saved endpoint parameter certificate")
                require(payload["certificate"]["parameter_count"] == 55553 and
                        payload["certificate"]["dtype"] == "float32" and
                        payload["certificate"]["device"] == "cpu", "fixed scorer architecture")
                zero = bool(torch.count_nonzero(model.layers[-1].weight) == 0 and
                            torch.count_nonzero(model.layers[-1].bias) == 0)
                require(zero == payload["certificate"]["exact_zero_head"], "head certificate truth")
                if endpoint == "initial":
                    require(zero and _digest(payload["online"]) ==
                            payload["certificate"]["initial_parameter_sha256"], "initial endpoint identity")
                self.models[fit, endpoint], self.payloads[fit, endpoint] = model, payload

    def infer(self, fit, endpoint, rows):
        self.audit.meter.check()
        self.audit.reserve("neural_attempted_rows", 24480, len(rows))
        self.audit.add("neural_" + endpoint + "_attempted_rows", len(rows))
        with self.torch.no_grad():
            result = self.models[fit, endpoint](self.torch.from_numpy(rows)).numpy().copy()
        self.audit.add("neural_rows", len(rows))
        self.audit.add("neural_" + endpoint + "_rows", len(rows))
        require(result.shape == (len(rows),) and result.dtype == np.float32 and
                np.isfinite(result).all(), "finite frozen residual rows")
        return result


def hash_replay_row(digest, row):
    """Stream the learner's typed digest format without retaining a second replay."""
    def feed(item):
        if hasattr(item, "detach"):
            feed(item.detach().cpu().numpy())
        elif isinstance(item, np.ndarray):
            digest.update(b"array" + item.dtype.str.encode() + repr(item.shape).encode())
            digest.update(np.ascontiguousarray(item).tobytes())
        elif isinstance(item, dict):
            digest.update(b"dict")
            for key in sorted(item, key=lambda x: (type(x).__name__, repr(x))):
                feed(key)
                feed(item[key])
        elif isinstance(item, (tuple, list)):
            digest.update(type(item).__name__.encode() + str(len(item)).encode())
            for child in item:
                feed(child)
        else:
            digest.update(type(item).__name__.encode() + repr(item).encode() + b";")
    feed(row)


class TrainingRead:
    def __init__(self, fit, compact_state):
        self.fit, self.transitions, self.updates, self.nonterminal_rows = fit, 0, 0, 0
        self.nonterminal_batches = 0
        self.state = compact_state
        self.exploration = np.random.Generator(np.random.PCG64(np.random.SeedSequence([109259999, 10, fit])))
        self.sampler = np.random.Generator(np.random.PCG64(np.random.SeedSequence([109259999, 11, fit])))
        self.replay_hash = hashlib.sha256()
        self.replay_hash.update(b"list30720")
        self.full_hash = hashlib.sha256()
        self.full_hash.update(b"dict")
        added = {"replay_size", "replay_sha256", "full_state_sha256", "replay_storage"}
        self.state_keys = sorted(set(compact_state) - added)
        for key in self.state_keys:
            if key < "replay":
                hash_replay_row(self.full_hash, key)
                hash_replay_row(self.full_hash, compact_state[key])
        hash_replay_row(self.full_hash, "replay")
        self.full_hash.update(b"list30720")
        self.curves, self.offline_wall, self.offline_cpu = [], 0., 0.

    def decisions(self, arrays):
        for index in range(60):
            require(arrays["reports"][index]["complete"] == 1 and arrays["nn_complete"][index],
                    "training decision missing canonical caches")
            draw = float(self.exploration.random())
            selected = int(self.exploration.integers(4)) if draw < .1 else -1
            same(arrays["exploration_draw"][index], draw, "exploration stream draw")
            same(arrays["exploratory_action"][index], selected, "exploration stream action")
            expected = selected if selected >= 0 else int(arrays["greedy_action"][index])
            same(arrays["action"][index], expected, "training exploration-to-execution")

    def transitions_from(self, world, arrays):
        values, terminal_samples = [], 0
        start_updates = self.updates
        for index in range(60):
            self.transitions += 1
            terminal = index == 59
            row = (arrays["features"][index], arrays["reports"][index]["costs"],
                   int(arrays["action"][index]), int(arrays["macro_cost"][index]),
                   None if terminal else arrays["features"][index + 1],
                   None if terminal else arrays["reports"][index + 1]["costs"], terminal)
            hash_replay_row(self.replay_hash, row)
            hash_replay_row(self.full_hash, row)
            if self.transitions <= 256:
                same(arrays["update_number"][index], 0, "warmup has no update")
                same(arrays["update_samples"][index], np.full(128, -1), "warmup has no sample")
                same(arrays["update_values"][index], np.zeros(6), "warmup has no update values")
                continue
            self.updates += 1
            same(arrays["update_number"][index], self.updates, "one update per later transition")
            indices = self.sampler.choice(self.transitions, size=128, replace=False)
            same(arrays["update_samples"][index], indices, "private replay PCG64 distinct indices")
            require(len(np.unique(indices)) == 128 and np.all(indices < self.transitions),
                    "128 distinct current replay indices")
            nonterminal = int(np.count_nonzero(indices % 60 != 59))
            self.nonterminal_rows += nonterminal
            self.nonterminal_batches += int(nonterminal > 0)
            terminal_samples += 128 - nonterminal
            update = arrays["update_values"][index]
            require(update[0] >= 0 and update[1] >= 0 and update[2] >= 0, "loss/gradient norm signs")
            same(update[5], nonterminal, "terminal samples have no next network evaluation")
            values.append(update)
        self.offline_wall += float(arrays["offline_wall"].sum())
        self.offline_cpu += float(arrays["offline_cpu"].sum())
        require(np.all(arrays["offline_wall"] >= 0) and np.all(arrays["offline_cpu"] >= 0),
                "offline measured time signs")
        value = np.asarray(values).reshape(-1, 6)
        self.curves.append({"world": int(world), "C": int(arrays["macro_cost"].sum()),
                            "updates": self.updates - start_updates,
                            "terminal_sample_rows": terminal_samples,
                            "loss_mean": float(value[:, 0].mean()) if len(value) else None,
                            "loss_max": float(value[:, 0].max()) if len(value) else None,
                            "gradient_norm_before_max": float(value[:, 1].max()) if len(value) else None,
                            "gradient_norm_after_max": float(value[:, 2].max()) if len(value) else None,
                            "reported_cap_excess_max": float(np.maximum(value[:, 2] - 10., 0).max()) if len(value) else None})

    def finish(self, root, worker_root, manifest, models):
        import torch
        from .learner import _digest
        require(self.transitions == 30720 and self.updates == 30464, "complete fixed fit counts")
        record = manifest["fits"][self.fit]
        relative = f"checkpoints/fit{self.fit}_training.pt"
        require(relative in manifest["files"], "compact training state absent from manifest")
        identity = manifest["files"][relative]
        require(record["training"]["sha256"] == identity["sha256"] and
                record["training"]["bytes"] == identity["bytes"], "training snapshot hash mirror")
        state = self.state
        require(state["schema"] == 1 and state["fit_index"] == self.fit and
                state["init_seed"] == c.TORCH_INIT_SEEDS[self.fit] and not state["failed"],
                "compact training lineage/status")
        require("replay" not in state and state["replay_storage"] == "canonical mission transitions",
                "single canonical replay evidence")
        require(state["replay_size"] == 30720 and state["replay_sha256"] == self.replay_hash.hexdigest(),
                "all cached transition replay byte identity")
        require(state["sampler"] == self.sampler.bit_generator.state, "terminal private sampler state")
        require(state["full_state_sha256"] == record["full_state_identity"], "full training identity mirror")
        for key in self.state_keys:
            if key > "replay":
                hash_replay_row(self.full_hash, key)
                hash_replay_row(self.full_hash, state[key])
        require(self.full_hash.hexdigest() == state["full_state_sha256"],
                "streamed complete training state identity")
        counters = state["counters"]
        expected = {"transition_attempts": 30720, "transitions": 30720, "updates": 30464,
                    "update_attempts": 30464, "backward_attempts": 30464, "backwards": 30464,
                    "optimizer_attempts": 30464, "optimizer_steps": 30464,
                    "initial_target_copy_attempts": 1, "initial_target_copies": 1,
                    "target_copy_attempts": 119, "target_copies": 119, "update_failures": 0}
        require(counters == expected,
                "fit update/copy attempt and completion counts")
        for name, amount in expected.items():
            same(record["metrics"][name], amount, "worker final metric " + name)
        expected_forward = {"collection": (30720, 122880), "update_current": (30464, 30464 * 128),
                            "update_next_online": (self.nonterminal_batches, 4 * self.nonterminal_rows),
                            "update_next_target": (self.nonterminal_batches, self.nonterminal_rows)}
        for role, (calls, rows) in expected_forward.items():
            require(state["forward_counts"][role] == {"attempts": calls, "calls": calls,
                    "attempted_rows": rows, "rows": rows}, "actual fit forward exposure " + role)
        require(state["forward_counts"] == record["metrics"]["forward"], "fit forward count mirrors")
        for endpoint, key in (("final", "online"), ("final", "target"), ("initial", "initial")):
            expected_weights = models.payloads[self.fit, endpoint]["online"]
            require(state[key].keys() == expected_weights.keys(), "training tensor keys")
            for name, value in state[key].items():
                require(value.dtype == torch.float32 and value.device.type == "cpu" and
                        bool(torch.isfinite(value).all()), "finite training tensor dtype")
                same(value.numpy(), expected_weights[name].numpy(), "terminal target/online/initial weights")
        optimizer = state["optimizer"]
        require(len(optimizer["param_groups"]) == 1, "one Adam parameter group")
        group = optimizer["param_groups"][0]
        require(group["lr"] == 3e-4 and tuple(group["betas"]) == (.9, .999) and
                group["eps"] == 1e-8 and group["weight_decay"] == 0 and
                not group["amsgrad"] and not group["maximize"] and not group["capturable"] and
                not group["differentiable"] and group["foreach"] is None and group["fused"] is None,
                "fixed Adam contract")
        parameters = list(state["online"].values())
        require(len(group["params"]) == len(parameters) and
                set(optimizer["state"]) == set(group["params"]), "all optimizer parameter states")
        for identifier, parameter in zip(group["params"], parameters):
            values = optimizer["state"][identifier]
            require(set(values) == {"step", "exp_avg", "exp_avg_sq"}, "Adam state keys")
            for name, value in values.items():
                require(value.dtype == torch.float32 and value.device.type == "cpu" and
                        bool(torch.isfinite(value).all()) and
                        value.shape == (() if name == "step" else parameter.shape), "Adam tensor shape/finite")
            same(values["step"].numpy(), 30464., "Adam actual step count")
        module = ast.parse((root / "experiments/candidates/uav_decision_generalization/b05_request_schedule/learner.py").read_text())
        clipping = [node for node in ast.walk(module) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr == "clip_grad_norm_"]
        require(len(clipping) == 1 and ast.literal_eval(clipping[0].args[1]) == 10.,
                "bound source global gradient clipping call")
        initial, final = models.payloads[self.fit, "initial"]["online"], state["online"]
        differences = torch.cat([(value - initial[name]).reshape(-1).double()
                                 for name, value in final.items()])
        movement = {"parameter_motion_l2": float(torch.linalg.vector_norm(differences)),
                    "parameter_motion_max": float(differences.abs().max()),
                    "parameter_changed_coordinates": int(torch.count_nonzero(differences))}
        for name, value in movement.items():
            same(record["metrics"][name], value, "parameter movement " + name)
        return {"fit": self.fit, "transitions": self.transitions, "updates": self.updates,
                "nonterminal_sample_rows": self.nonterminal_rows, "target_copies": 119,
                "replay_sha256": self.replay_hash.hexdigest(), "movement": movement,
                "offline_wall_s": self.offline_wall, "offline_cpu_s": self.offline_cpu,
                "optimizer_replayed": False, "full_state_sha256": state["full_state_sha256"]}


def wire_key(state, times, tape, source_identity):
    """Exact framed reuse identity, rebuilt without worker pack/cohort helpers."""
    reset = state["users"].astype("<i4").tobytes() + state["rates"].tobytes()
    report = (state["positions"].astype("<f8").tobytes() + packed(state["ack"]).tobytes()
              + state["counts"].astype("<u2").tobytes()
              + state["progress"].astype("u1").tobytes() + state["slots"].tobytes()
              + int(state["tick"]).to_bytes(2, "little"))
    require(len(reset) == 404 and len(report) == 171, "exact public wire identity")
    result = hashlib.sha256()
    for block in (source_identity.encode(), int(state["world"]).to_bytes(8, "little"), reset, report,
                  np.asarray(state["pairs"], dtype=np.uint8).tobytes(),
                  np.asarray(times, dtype="<u2").tobytes(), np.asarray(tape, dtype=bool).tobytes()):
        result.update(len(block).to_bytes(8, "little"))
        result.update(block)
    return result.hexdigest()


def future_arrivals(state, tape_index):
    horizon = min(160, 1200 - state["tick"])
    times = np.arange(state["tick"] + 20, min(state["tick"] + horizon, 940) + 1, 20,
                      dtype=np.int64)
    random = np.random.Generator(np.random.PCG64(np.random.SeedSequence(
        [109259999, 30, state["world"], state["tick"] // 20, tape_index])))
    return times, random.random((len(times), 4)) < state["rates"].astype(float) / 10.


def commanded_motion(positions, active, users):
    direction = slots_for(users)[active] - positions
    raw = direction / np.maximum(30., np.linalg.norm(direction, axis=-1))[:, None]
    executed, following, events = motion(positions, raw)
    return raw, executed, following, events


def check_timing(timing):
    start, deadline, fixed, reaped = (int(timing[name]) for name in
                                    ("start_ns", "deadline_ns", "command_fixed_ns", "reaped_ns"))
    require(deadline - start == 20_000_000_000 and start <= fixed <= reaped,
            "actual decision clock/deadline/reap order")
    eligible = []
    previous = start
    for message in timing["messages"]:
        ready, received = int(message["ready_ns"]), int(message["received_ns"])
        require(previous <= received <= fixed and start <= ready <= received, "message clock order")
        previous = received
        expected = received <= deadline and ready <= deadline
        require(bool(message["eligible"]) == expected, "actual ready AND receipt deadline eligibility")
        if expected and message["type"] in ("fallback", "cohort", "result"):
            eligible.append(message)
    if not timing["deadline_expired"]:
        require(bool(timing["completed_request"]), "nonexpired request must finish")
    return eligible


def rollout_read(arrays, state, collected, selected, audit):
    """Read committed prefixes/queries, including unused work; never finish one."""
    statistics = {name: int(arrays["stats"][i]) for i, name in enumerate(R_STATS)}
    require(all(value >= 0 for value in statistics.values()), "negative R exposure")
    interrupted = bool(selected["timing"]["deadline_expired"])
    horizon = min(160, 1200 - state["tick"])
    require(np.all((arrays["rows"] >= 0) & (arrays["rows"] <= horizon + 1)), "committed R prefix bound")
    for name in ("tape_complete", "cohort_complete", "branch_complete"):
        require(np.all((arrays[name] == 0) | (arrays[name] == 1)), "binary R commit markers")
    require(statistics["initial_attempts"] <= 1 and statistics["initial_complete"] <=
            statistics["initial_attempts"], "single public reconstruction")
    rows = arrays["rows"]
    if np.any(rows):
        require(statistics["initial_complete"] == 1, "clones require committed shared reconstruction")
    if statistics["initial_complete"]:
        report_identity(arrays["initial"][0], state)
        audit.physics(arrays["initial"][0], state["users"], "R_initial")
    tape_indices = np.flatnonzero(arrays["tape_complete"])
    same(tape_indices, np.arange(len(tape_indices)), "contiguous committed R tapes")
    tapes, keys = {}, {}
    for index in tape_indices:
        index = int(index)
        audit.meter.check()
        audit.add("R_tape_reconstructions")
        times, tape = future_arrivals(state, index)
        audit.add("R_tape_uniforms", int(tape.size))
        size = int(arrays["tape_lengths"][index])
        require(size == len(times), "R tape endpoint length")
        same(arrays["tape_times"][index, :size], times, "fixed R tape times")
        same(arrays["tape_times"][index, size:], np.full(8 - size, -1), "R tape padding")
        same(arrays["tapes"][index, :size], tape, "separate public-rate R tape")
        same(arrays["tapes"][index, size:], np.zeros((8 - size, 4)), "R tape unused bits")
        tapes[index] = {int(tick): bit for tick, bit in zip(times, tape)}
        keys[index] = wire_key(state, times, tape, audit.source_identity)
    committed_branches = np.flatnonzero(rows)
    same(committed_branches, np.arange(len(committed_branches)), "contiguous committed branch starts")
    if len(committed_branches) > 1:
        require(np.all(arrays["branch_complete"][committed_branches[:-1]] == 1),
                "only the last started candidate may be incomplete")
        require(np.all(np.diff(arrays["branch_tape"][committed_branches]) >= 0),
                "physical candidates follow tape publication order")
    for tape_index in tape_indices:
        ids = np.flatnonzero((rows > 0) & (arrays["branch_tape"] == tape_index))
        rotation = (state["world"] + state["tick"] // 20 + int(tape_index)) % 4
        same(arrays["branch_action"][ids], np.roll(np.arange(4), -rotation)[:len(ids)],
             "fixed rotated candidate prefix order")
        require(len(ids) <= 4, "four physical candidates per unique tape")
        if any(keys[int(previous)] == keys[int(tape_index)] for previous in tape_indices
               if previous < tape_index and arrays["cohort_complete"][previous]):
            require(len(ids) == 0, "duplicate full input must reuse prior physical cohort")
    gaps = {"tapes": marker_gap(len(tape_indices), statistics["tape_draws"], interrupted, "R tape")}
    require(len(tape_indices) <= statistics["tape_attempts"] <= len(tape_indices) + int(interrupted),
            "R tape attempts/commits")
    # Uniforms are a second publication after tape_draws, so at most the final
    # committed tape's exact draw count can be missing on cancellation.
    tape_uniforms = sum(len(tape) * 4 for tape in tapes.values())
    last_tape_uniforms = len(tapes[int(tape_indices[-1])]) * 4 if len(tape_indices) else 0
    missing_uniforms = tape_uniforms - statistics["tape_uniforms"]
    require(missing_uniforms in ((0, last_tape_uniforms) if interrupted else (0,)),
            "R tape uniform counter")
    if gaps["tapes"] or missing_uniforms:
        last = int(tape_indices[-1])
        require(not np.any((rows > 0) & (arrays["branch_tape"] == last)) and
                arrays["cohort_complete"][last] == 0, "tape counter gap must be final publication")
        if gaps["tapes"]:
            require(missing_uniforms == last_tape_uniforms, "draw publication precedes uniform counter")
    complete_g = np.flatnonzero(arrays["g"]["complete"])
    same(complete_g, np.arange(len(complete_g)), "contiguous committed R G queries")
    require(np.all((arrays["g"]["complete"] == 0) | (arrays["g"]["complete"] == 1)), "binary G commits")
    gaps["G"] = marker_gap(len(complete_g), statistics["g_complete"], interrupted, "R G")
    require(len(complete_g) <= statistics["g_attempts"] <= len(complete_g) + int(interrupted), "R G attempts")
    predictions, matched = {}, set()
    for index in complete_g:
        index = int(index)
        query = arrays["g"][index]
        if index == 0:
            report_identity(query, state, costs=True)
            if collected["complete"]:
                same(query["costs"], collected["costs"], "R base-G duplicate cost identity")
                predictions[index] = query["costs"].copy()
                audit.add("G_duplicate_R_base_records")
            else:
                predictions[index] = audit.g(query, state, "R_base_only")
            matched.add(index)
        else:
            query_state = public(query, state["users"], state["rates"], state["pairs"], state["world"])
            predictions[index] = audit.g(query, query_state, "R_internal")
    predicted_ticks = sum(4 * min(240, 1200 - int(arrays["g"][i]["tick"])) for i in complete_g)
    completed_ticks = statistics["g_complete_candidate_ticks"]
    allowed_tick_gap = (4 * min(240, 1200 - int(arrays["g"][complete_g[-1]]["tick"]))) if len(complete_g) else 0
    require(predicted_ticks - completed_ticks in ((0, allowed_tick_gap) if interrupted else (0,)),
            "R committed G candidate-tick counter")
    require(predicted_ticks == completed_ticks or gaps["G"] == 1,
            "G tick publication precedes complete counter")
    require(statistics["g_reserved_candidate_ticks"] >= predicted_ticks, "R reserved G ticks")
    require(np.all(arrays["g_links"][:, 7] == -1), "unused internal G link slot")
    candidates0 = candidates(state)
    frontier_inputs = {}
    branch_readouts = []
    for branch in np.flatnonzero(rows):
        branch = int(branch)
        action, tape_index = int(arrays["branch_action"][branch]), int(arrays["branch_tape"][branch])
        require(action in range(4) and tape_index in tapes, "committed branch action/tape")
        same(arrays["states"][branch, 0], arrays["initial"][0], "clone initial exact copied identity")
        ledger = FIFO(state["counts"], state["progress"])
        require(all(request["arrival_tick"] is None for queue in ledger.queues for request in queue),
                "model reconstruction must not invent ages")
        active, pending = state["slots"].copy(), candidates0[action].copy()
        paid = int(rows[branch]) - 1
        for offset in range(paid):
            tick = state["tick"] + offset
            previous = arrays["states"][branch, offset]
            same(previous["counts"], ledger.counts, "R pre-arrival integer counts")
            same(previous["progress"], ledger.progress, "R pre-arrival head progress")
            if offset and offset % 20 == 0:
                active = pending.copy()
            arrivals = tapes[tape_index].get(tick, np.zeros(4, dtype=bool))
            same(arrays["arrivals"][branch, offset], arrivals, "R branch public future arrivals")
            ledger.arrive(tick, arrivals)
            same(arrays["tick_cost"][branch, offset], ledger.charge(), "R pre-service residence charge")
            if offset and offset % 20 == 0:
                index = int(arrays["g_links"][branch, offset // 20 - 1])
                require(index in predictions, "paid native prefix needs completed continuation G")
                expected = public(previous, state["users"], state["rates"], state["pairs"], state["world"])
                expected.update(tick=tick, counts=ledger.counts,
                                progress=np.asarray(ledger.progress), slots=active)
                report_identity(arrays["g"][index], expected)
                matched.add(index)
                pending = candidates(expected)[int(np.argmin(predictions[index]))].copy()
            successor = arrays["states"][branch, offset + 1]
            _, _, following, _ = commanded_motion(previous["positions"], active, state["users"])
            same(successor["positions"], following, "R faithful copied-vector native motion")
            same(successor["slots"], active, "R delayed active slots")
            same(successor["tick"], tick + 1, "R successor clock")
            ack = audit.physics(successor, state["users"], "R_prefix")
            ledger.service(tick, ack)
            same(successor["counts"], ledger.counts, "R native FIFO counts")
            same(successor["progress"], ledger.progress, "R native FIFO progress")
        complete = bool(arrays["branch_complete"][branch])
        require(not complete or paid == horizon, "complete branch must contain full paid horizon")
        endpoint = state["tick"] + paid
        query_at_frontier = (paid > 0 and paid % 20 == 0 and endpoint < 1200)
        score = None
        if query_at_frontier:
            previous = arrays["states"][branch, paid]
            active = pending.copy()
            arrivals = tapes[tape_index].get(endpoint, np.zeros(4, dtype=bool))
            ledger.arrive(endpoint, arrivals)  # no endpoint residence charge
            expected = public(previous, state["users"], state["rates"], state["pairs"], state["world"])
            expected.update(counts=ledger.counts, progress=np.asarray(ledger.progress), slots=active)
            slot = 8 if paid == horizon else paid // 20 - 1
            index = int(arrays["g_links"][branch, slot])
            if index >= 0:
                require(index in predictions, "frontier G link must be committed")
                report_identity(arrays["g"][index], expected)
                same(arrays["arrivals"][branch, paid], arrivals, "R endpoint arrivals")
                matched.add(index)
                if paid == horizon:
                    score = ledger.area + float(np.min(predictions[index]))
            frontier_inputs[branch] = expected
        elif paid == horizon and endpoint == 1200:
            score = ledger.area + 240 * int(ledger.counts.sum())
        if complete:
            require(score is not None, "complete nonterminal branch needs completed tail")
            same(arrays["branch_cost"][branch], score, "R score excludes endpoint double charge")
        branch_readouts.append({"branch": branch, "action": action, "tape": tape_index,
                                "committed_native_steps": paid, "complete": complete,
                                "cost": float(score) if complete else None})
    # A last G payload can be committed before its branch link is published.
    unmatched = set(predictions) - matched
    require(len(unmatched) <= int(interrupted), "unjoined completed R G queries")
    for index in unmatched:
        require(index == int(complete_g[-1]) and len(committed_branches) > 0 and
                arrays["branch_complete"][committed_branches[-1]] == 0,
                "only final candidate may have an unlinked final G payload")
        query = arrays["g"][index]
        expected = frontier_inputs.get(int(committed_branches[-1]))
        require(expected is not None and
                all(np.array_equal(query[name], expected[name]) for name in
                    ("positions", "counts", "progress", "slots", "tick")) and
                np.array_equal(unpack(query["ack"], (50,)), expected["ack"]),
                "unlinked G must match the final candidate prefix frontier")
    if gaps["G"]:
        if int(complete_g[-1]) == 0:
            require(statistics["initial_attempts"] == 0 and statistics["tape_attempts"] == 0 and
                    not len(committed_branches), "base G counter gap precedes all R model work")
        else:
            require(unmatched == {int(complete_g[-1])}, "G counter gap must precede final link publication")
    native_commits = sum(int(value) - 1 for value in rows if value)
    gaps["native"] = marker_gap(native_commits, statistics["native_complete"], interrupted, "R native")
    require(native_commits <= statistics["native_attempts"] <= native_commits + int(interrupted),
            "R native attempt exposure")
    if gaps["native"]:
        final_branch = int(committed_branches[-1]) if len(committed_branches) else -1
        paid = int(rows[final_branch]) - 1 if final_branch >= 0 else 0
        frontier_slot = 8 if paid == horizon else paid // 20 - 1
        has_later_G = paid > 0 and paid % 20 == 0 and state["tick"] + paid < 1200 and \
            arrays["g_links"][final_branch, frontier_slot] >= 0
        require(len(committed_branches) > 0 and
                arrays["branch_complete"][final_branch] == 0 and not unmatched and not has_later_G,
                "native counter gap must precede final candidate completion or new G work")
    clone_rows = int(np.count_nonzero(rows))
    require(clone_rows <= statistics["clones"] <= clone_rows + int(interrupted) and
            statistics["clones"] <= statistics["clone_attempts"] <= statistics["clones"] + int(interrupted),
            "R clone call/row publication")
    require(np.all(arrays["branch_complete"][rows == 0] == 0), "no complete empty branch")
    cohort_indices = np.flatnonzero(arrays["cohort_complete"])
    same(cohort_indices, np.arange(len(cohort_indices)), "contiguous committed cohorts")
    gaps["cohorts"] = marker_gap(len(cohort_indices), statistics["cohorts_complete"], interrupted, "R cohort")
    require(len(tape_indices) in (len(cohort_indices), len(cohort_indices) + 1) and
            statistics["tape_attempts"] <= len(cohort_indices) + 1,
            "next tape starts only after preceding cohort publication")
    if not interrupted:
        require(len(cohort_indices) == 4 and statistics["initial_complete"] == 1,
                "completed R decision contains all four cohorts")
    if gaps["cohorts"]:
        require(len(tape_indices) == len(cohort_indices) == statistics["tape_attempts"] and
                len(selected["cohorts"]) < len(cohort_indices),
                "cohort counter gap must precede next tape and selected message")
    cohorts, cache, used_branches = [], {}, set()
    for index in cohort_indices:
        index = int(index)
        require(index in tapes, "completed cohort has its committed tape")
        previous = cache.get(keys[index])
        reused = int(arrays["cohort_reuse"][index])
        require(reused == (-1 if previous is None else previous), "exact full-input cohort reuse")
        ids = arrays["cohort_branches"][index]
        if previous is None:
            require(len(set(map(int, ids))) == 4, "four distinct first-action branches")
            for action, branch in enumerate(ids):
                branch = int(branch)
                require(branch in range(16) and arrays["branch_complete"][branch] == 1 and
                        int(arrays["branch_action"][branch]) == action and
                        int(arrays["branch_tape"][branch]) == index, "complete cohort action correspondence")
                same(arrays["cohort_costs"][index, action], arrays["branch_cost"][branch], "cohort costs")
                used_branches.add(branch)
            cache[keys[index]] = index
        else:
            same(ids, arrays["cohort_branches"][previous], "reused exact branch identities")
            same(arrays["cohort_costs"][index], arrays["cohort_costs"][previous], "reused score multiplicity")
        same(arrays["cohort_input_sha256"][index], np.frombuffer(bytes.fromhex(keys[index]), dtype=np.uint8),
             "full source/public/tape reuse hash")
        require(int(arrays["cohort_ready_ns"][index]) >= int(selected["timing"]["start_ns"]), "cohort ready time")
        size = int(arrays["tape_lengths"][index])
        cohorts.append({"tape": index, "times": arrays["tape_times"][index, :size].astype(int).tolist(),
                        "bits": arrays["tapes"][index, :size].astype(int).tolist(),
                        "input_sha256": keys[index], "reused_cohort": None if reused < 0 else reused,
                        "branches": ids.astype(int).tolist(), "costs": arrays["cohort_costs"][index].tolist()})
    committed_reuse = sum(cohort["reused_cohort"] is not None for cohort in cohorts)
    require(committed_reuse <= statistics["cohorts_reused"] <= committed_reuse + int(interrupted),
            "R reuse-hit versus committed publication")
    if state["tick"] >= 940:
        require(len(cache) <= 1, "no-arrival tail has one exact physical cohort")
    chosen = selected["cohorts"]
    require(chosen == cohorts[:len(chosen)], "selected complete cohort prefix")
    messages = check_timing(selected["timing"])
    selected_messages = [message for message in messages if message["type"] == "cohort"]
    require(len(chosen) == len(selected_messages), "eligible cohort messages define selected multiplicity")
    for cohort, message in zip(chosen, selected_messages):
        require(int(arrays["cohort_ready_ns"][cohort["tape"]]) <= int(message["ready_ns"]),
                "committed cohort precedes its actual ready message")
    selected_branches = {branch for cohort in chosen for branch in cohort["branches"]}
    audit.add("R_committed_native_steps", native_commits)
    audit.add("R_complete_cohorts", len(cohorts))
    audit.add("R_selected_cohorts", len(chosen))
    audit.add("R_reused_cohorts", committed_reuse)
    audit.add("R_incomplete_native_attempts", statistics["native_attempts"] - native_commits)
    native_events = {name: int(arrays["native_events"][i]) for i, name in enumerate(c.NATIVE_EVENT_NAMES)}
    require(all(value >= 0 for value in native_events.values()), "negative paid native event exposure")
    require(0 <= statistics["native_attempts"] - native_events["native_step_calls"] <= int(interrupted),
            "R registered step attempt precedes native entry sink")
    require(native_events["native_steps"] >= native_commits and
            native_events["native_steps"] <= native_commits + int(interrupted), "R returned native step exposure")
    return {"statistics": statistics, "native_events": native_events,
            "commit_counter_gaps": gaps, "branches": branch_readouts,
            "committed_cohorts": len(cohorts), "selected_cohorts": len(chosen),
            "reused_cohorts": committed_reuse,
            "completed_unused_branches": [int(i) for i in np.flatnonzero(arrays["branch_complete"])
                                           if int(i) not in selected_branches],
            "deadline_expired": interrupted}


def policy_kind(label):
    if label.startswith("train/"):
        return "train", int(label[-1])
    phase, name = label.split("/")
    if name in ("G", "R"):
        return name, None
    if phase == "main":
        return "L", int(name[-1])
    return ("initial" if name == "initial" else "L"), int(phase[-1])


def request_metrics(ledger, ack, positions, route_lengths, counts, active):
    completed = [item["completion_tick"] - item["request"]["arrival_tick"]
                 for item in ledger.completions]
    unfinished = [1200 - item["arrival_tick"] for queue in ledger.queues for item in queue]
    require(sum(completed) + sum(unfinished) == ledger.area, "request residence conserves area")
    per_cluster = []
    for cluster in range(4):
        done = [item["completion_tick"] - item["request"]["arrival_tick"] for item in ledger.completions
                if item["request"]["cluster"] == cluster]
        ages = [1200 - item["arrival_tick"] for item in ledger.queues[cluster]]
        qualified = ack[:, 10 + 10*cluster:20 + 10*cluster].sum(axis=1) >= 8
        per_cluster.append({"cluster": cluster,
                            "requests": sum(item["cluster"] == cluster for item in ledger.requests),
                            "completed": len(done), "backlog": len(ages),
                            "residence_completed": distribution(done), "unfinished_ages": distribution(ages),
                            "qualified_ticks": int(qualified.sum()),
                            "longest_unqualified_run": longest_false(qualified),
                            "head_interruptions": ledger.interruptions[cluster],
                            "max_backlog": int(np.max(counts[:, cluster]))})
    travel = np.linalg.norm(np.diff(positions, axis=0), axis=-1).sum(axis=0)
    signed_lengths = route_lengths.astype(np.int64)
    hops = np.where(signed_lengths > 0, signed_lengths - 1, 0)
    return {"requests": len(ledger.requests), "completed": len(ledger.completions),
            "unfinished": len(unfinished), "area_cost": ledger.area,
            "terminal_charge": 240 * len(unfinished), "C": ledger.area + 240 * len(unfinished),
            "residence_completed": distribution(completed), "unfinished_ages": distribution(unfinished),
            "per_cluster": per_cluster, "user_routed_ticks": ack.sum(axis=0).astype(int).tolist(),
            "user_longest_service_gap": [longest_false(ack[:, user]) for user in range(50)],
            "team_zero_service_ticks": int(np.count_nonzero(~ack.any(axis=1))),
            "longest_team_zero_service_run": longest_false(ack.any(axis=1)),
            "travel_metres_per_uav": travel.tolist(), "travel_metres_total": float(travel.sum()),
            "route_hops_histogram": np.bincount(hops.astype(int).ravel(), minlength=7).tolist(),
            "unrouted_uav_ticks": int(np.count_nonzero(route_lengths == 0)),
            "active_uav_target_changes": int(np.count_nonzero(np.diff(active.astype(int), axis=0)))}


def intervention_joins(arrays, public_states, completions, kind):
    joins = []
    if kind != "L":
        return joins
    qualified = np.asarray([unpack(row["ack"], (50,))[10:].reshape(4, 10).sum(axis=1) >= 8
                            for row in arrays["states"][1:]])
    for index, state in enumerate(public_states):
        if not arrays["reports"][index]["complete"]:
            continue
        g_action = int(np.argmin(arrays["reports"][index]["costs"]))
        chosen = int(arrays["action"][index])
        greedy_action = int(arrays["greedy_action"][index])
        activation = state["tick"] + 20
        unused = activation == 1200
        choices = candidates(state)
        different_command = not np.array_equal(arrays["commands"][index], choices[g_action])
        changed_motion = False
        if not unused:
            position = arrays["states"][activation]["positions"]
            target_g = slots_for(state["users"])[choices[g_action]]
            direction = target_g - position
            alternative = direction / np.maximum(30., np.linalg.norm(direction, axis=-1))[:, None]
            changed_motion = not np.array_equal(arrays["raw_actions"][activation], alternative)
        stop = min(activation + 20, 1200)
        joins.append({"decision": index, "tick": state["tick"],
                      "neural_argmin_differs_G": bool(greedy_action >= 0 and greedy_action != g_action),
                      "executed_action_differs_G": chosen != g_action,
                      "command_differs_G": different_command, "activation_tick": activation,
                      "terminal_unused": unused, "motion_differs_at_observed_activation_position": changed_motion,
                      "post_activation_window": [activation, stop],
                      "qualified_ticks": qualified[activation:stop].sum(axis=0).astype(int).tolist(),
                      "completion_request_ids": [item["request"]["request_id"] for item in completions
                                                 if activation < item["completion_tick"] <= stop],
                      "residence_charge": int(arrays["tick_cost"][activation:stop].sum()),
                      "counterfactual_causality_established": False})
    return joins


def check_actual_native_events(native_events):
    require(set(native_events) == set(c.NATIVE_EVENT_NAMES) and
            all(type(value) is int and value >= 0 for value in native_events.values()), "native actual event roster")
    # Both MultiUAVEnv.step and Scenario2.step dispatch _compute_reward;
    # RegisteredHost increments both reward-entry counters on each dispatch.
    for name, amount in (("constructor_calls", 1), ("reset_calls", 1), ("registry_calls", 1),
                         ("native_step_calls", 1200), ("native_steps", 1200),
                         ("dense_reward_entries", 2400), ("parent_reward_entries", 2400),
                         ("constructor_topology_restorations", 1), ("public_clone_calls", 0)):
        same(native_events[name], amount, "actual native event " + name)


def read_mission(record, worker_root, manifest, audit, models, training):
    label, world = record["label"], int(record["world"])
    kind, fit = policy_kind(label)
    arrays = load_arrays(contained(worker_root, record["npz"]), MISSION_SHAPES)
    metadata = read_json(contained(worker_root, record["metadata"]))
    require(metadata["schema"] == 1 and metadata["status"] == "COMPLETE" and
            metadata["world"] == world and metadata["label"] == label and
            bool(metadata["training"]) == (kind == "train") and
            bool(metadata["initial_audit"]) == (kind == "initial"), "mission metadata identity")
    require(metadata["completed_native_steps"] == 1200 and metadata["completed_decisions"] == 60 and
            len(metadata["decisions"]) == 60 and metadata["last_command_unused"], "complete mission bounds")
    same(arrays["initial_audit_complete"], np.full(60, kind == "initial"), "complete offline initial audit roster")
    if kind not in ("L", "train"):
        require(not arrays["nn_complete"].any(), "ordinary residual placeholders are not neural calls")
    native_events = metadata["actual_native_events"]
    check_actual_native_events(native_events)
    cost = metadata["cost"]
    same(cost["inclusive_cpu_seconds"], cost["after"]["phase_cpu_seconds"] -
         cost["before"]["phase_cpu_seconds"], "mission inclusive CPU snapshots")
    require(np.isfinite(cost["inclusive_cpu_seconds"]) and np.isfinite(cost["inclusive_wall_seconds"]) and
            cost["inclusive_wall_seconds"] >= 0, "measured mission time")
    audit.meter.check()
    audit.add("geometry_reconstructions")
    initial_positions, users = geometry(world)
    same(arrays["users"], users, "source-fixed map law")
    same(arrays["states"][0]["positions"], initial_positions, "native source-fixed initial positions")
    rate_rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([109259999, 20, world])))
    rates = rate_rng.permutation(np.asarray([6, 3, 2, 1], dtype=np.uint8))
    arrival_rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([109259999, 21, world])))
    draws = arrival_rng.random((48, 4))
    tape = draws < rates.astype(float) / 10.
    same(arrays["rates"], rates, "public rate permutation domain")
    same(arrays["arrival_draws"], draws, "private actual-arrival draw domain")
    same(arrays["arrival_tape"], tape, "actual future tape stays outcome-only")
    audit.add("actual_arrival_tape_reconstructions")
    audit.add("actual_arrival_uniforms", 192)
    active, pairs = assignment(users, rates, initial_positions)
    same(arrays["initial_slots"], active, "initial 720-permutation assignment")
    same(arrays["pairs"], pairs, "fixed ordered pair membership")
    audit.add("assignment_permutations", 720)
    audit.add("assignment_distances", 36)
    same(arrays["states"]["tick"], np.arange(1201), "complete native clocks")
    require(np.all((arrays["reports"]["complete"] == 0) | (arrays["reports"]["complete"] == 1)),
            "binary collected G commits")
    ack = np.stack([audit.physics(row, users, "native") for row in arrays["states"]])
    executed, following, _ = motion(arrays["states"]["positions"][:-1], arrays["raw_actions"])
    same(arrays["executed_actions"], executed, "strict copied-three-vector >1 normalization")
    same(arrays["states"]["positions"][1:], following, "float64 native following positions")
    audit.add("native_motion_steps", 1200)
    ledger, pending = FIFO(), active.copy()
    public_states, rollout_checks, policy_missing = [], [], []
    expected_macro = np.zeros(60, dtype=np.uint32)
    actual_active = np.empty((1200, 6), dtype=np.uint8)
    pre_counts = np.empty((1200, 4), dtype=np.int64)
    if kind == "train":
        training.decisions(arrays)
    traces = {int(item["decision"]): item for item in metadata["rollout_traces"]}
    require(len(traces) == (60 if kind == "R" else 0), "complete R trace roster")
    if kind == "R":
        require(set(traces) == set(range(60)), "all R decision traces retained")
    for tick in range(1200):
        if tick % 20 == 0:
            audit.meter.check()
        index = tick // 20
        row = arrays["states"][tick]
        same(row["counts"], ledger.counts, "native before-arrival FIFO count")
        same(row["progress"], ledger.progress, "native before-arrival head progress")
        same(row["slots"], active, "native state records preceding active targets")
        if tick and tick % 20 == 0:
            active = pending.copy()
        arrivals = tape[index] if tick % 20 == 0 and tick <= 940 else np.zeros(4, dtype=bool)
        same(arrays["arrivals"][tick], arrivals, "actual append-before-report arrival order")
        ledger.arrive(tick, arrivals)
        charged = ledger.charge()
        pre_counts[tick] = ledger.counts
        same(arrays["tick_cost"][tick], charged, "native pre-service residence charge")
        expected_macro[index] += charged
        actual_active[tick] = active
        if tick % 20 == 0:
            state = public(row, users, rates, pairs, world)
            state.update(counts=ledger.counts, progress=np.asarray(ledger.progress), slots=active.copy())
            public_states.append(state)
            report = arrays["reports"][index]
            report_identity(report, state)
            complete = bool(report["complete"])
            raw_g = None
            if complete:
                raw_g = audit.g(report, state, "collected")
                expected_features = features(state, raw_g)
                same(arrays["features"][index], expected_features, "independent fixed 303 feature layout")
                same(arrays["g_action"][index], int(np.argmin(raw_g)), "raw G action ordering")
            else:
                require(kind not in ("train", "initial"), "mandatory decision cache missing")
                require(not arrays["nn_complete"][index], "NN cannot commit without G cache")
                policy_missing.append({"decision": index, "G_cache_missing": True, "neural_cache_missing": kind == "L"})
            decision = metadata["decisions"][index]
            eligible = check_timing(decision["timing"])
            selected_action = 0
            if eligible:
                require(complete, "eligible program result requires committed G cache")
                selected_action = int(np.argmin(raw_g))
            if kind == "R":
                trace = traces[index]
                require(trace["path"] in manifest["files"], "R prefix file must be byte-bound")
                trace_arrays = load_arrays(contained(worker_root, trace["path"]), R_SHAPES)
                same(trace_arrays["stats"], [trace["stats"][name] for name in R_STATS], "R lower counter mirrors")
                check = rollout_read(trace_arrays, state, report, decision, audit)
                check["decision"] = index
                rollout_checks.append(check)
                if decision["cohorts"]:
                    scores = np.mean(np.stack([cohort["costs"] for cohort in decision["cohorts"]]),
                                     axis=0, dtype=np.float64)
                    selected_action = greedy(scores, raw_g)
            elif kind in ("L", "train"):
                if arrays["nn_complete"][index]:
                    require(complete, "committed residual needs complete G")
                    residual = arrays["residual"][index]
                    if kind == "L":
                        predicted = models.infer(fit, "final", expected_features)
                        same(residual, predicted, "frozen final scorer output")
                    total = compose(raw_g, residual)
                    same(arrays["total_q"][index], total, "float64 canonical G plus float32 residual")
                    same(arrays["greedy_action"][index], greedy(total, raw_g), "float64/raw-G/action lex minimum")
                    if eligible:
                        selected_action = int(arrays["action"][index]) if kind == "train" else greedy(total, raw_g)
                else:
                    require(kind != "train", "training neural cache incomplete")
                    require(not eligible, "eligible learned result cannot omit NN output")
                    if complete:
                        policy_missing.append({"decision": index, "G_cache_missing": False, "neural_cache_missing": True})
            if kind == "initial":
                residual = models.infer(fit, "initial", expected_features)
                same(residual, np.zeros(4, dtype=np.float32), "exact zero neural initialization output")
                same(arrays["initial_audit_residual"][index], residual, "saved offline initial output")
                require(greedy(compose(raw_g, residual), raw_g) == int(np.argmin(raw_g)),
                        "zero neural mathematical raw-G tie identity")
            same(arrays["action"][index], selected_action, "actual eligible/fallback executed action")
            choices = candidates(state)
            require(selected_action in range(4), "four-action schedule")
            same(arrays["commands"][index], choices[selected_action], "reported-position action-to-pending command")
            pending = arrays["commands"][index].copy()
            lawful(pending, pairs)
        direction = slots_for(users)[active] - row["positions"]
        expected_raw = direction / np.maximum(30., np.linalg.norm(direction, axis=-1))[:, None]
        same(arrays["raw_actions"][tick], expected_raw, "lawful active-slot steering")
        ledger.service(tick, ack[tick + 1])
        successor = arrays["states"][tick + 1]
        same(successor["counts"], ledger.counts, "post-native integer FIFO counts")
        same(successor["progress"], ledger.progress, "post-native twentieth-tick completion")
        same(successor["slots"], active, "pending target activates only after 20 ticks")
    terminal = 240 * int(ledger.counts.sum())
    expected_macro[-1] += terminal
    same(arrays["macro_cost"], expected_macro, "60 nonnegative macro costs including terminal charge")
    require(int(expected_macro.sum()) == metadata["total_cost"] == record["total_cost"] and
            ledger.area == metadata["area_cost"] and terminal == metadata["terminal_charge"], "whole C conservation")
    require(metadata["requests"] == ledger.requests and metadata["completions"] == ledger.completions and
            metadata["unfinished"] == [list(queue) for queue in ledger.queues], "complete actual request identity/timestamps")
    require(metadata["logical_reset_bytes"] == 404 and metadata["logical_report_bytes"] == 61 * 171 and
            metadata["logical_command_bytes"] == 60 * 6 and
            metadata["logical_training_feedback_bytes"] == (240 if kind == "train" else 0), "logical payload bill")
    metrics = request_metrics(ledger, ack[1:], arrays["states"]["positions"],
                              arrays["states"]["route_lengths"][1:], pre_counts, actual_active)
    timings = [item["timing"] for item in metadata["decisions"]]
    metrics.update({"schema": 1, "status": "CHECKED", "label": label, "world": world,
                    "native_physical_states": 1201, "G_collected_complete": int(arrays["reports"]["complete"].sum()),
                    "policy_cache_missingness": policy_missing,
                    "deadline_misses": sum(bool(item["deadline_expired"]) for item in timings),
                    "decision_wall_seconds": distribution([(item["command_fixed_ns"] - item["start_ns"]) / 1e9
                                                            for item in timings]),
                    "reap_seconds": distribution([(item["reaped_ns"] - item["command_fixed_ns"]) / 1e9
                                                   for item in timings]),
                    "rollout_checks": rollout_checks,
                    "intervention_joins": intervention_joins(arrays, public_states, ledger.completions, kind),
                    "cost": metadata.get("cost"), "initial_audit_cpu_seconds": metadata.get("offline_initial_audit_cpu_seconds", 0),
                    "initial_audit_wall_seconds": metadata.get("offline_initial_audit_wall_seconds", 0)})
    if kind == "train":
        training.transitions_from(world, arrays)
    else:
        same(arrays["update_number"], np.zeros(60), "fixed policy has zero updates")
        same(arrays["update_samples"], np.full((60, 128), -1), "fixed policy has no replay samples")
        same(arrays["update_values"], np.zeros((60, 6)), "fixed policy has no optimization values")
    audit.add("missions")
    audit.add("training_missions" if kind == "train" else "frozen_missions")
    return metrics


def paired_t(values, conditioning):
    from scipy.stats import t
    value = np.asarray(values, dtype=np.float64)
    require(value.ndim == 1 and len(value) > 1 and np.isfinite(value).all(), "paired finite vector")
    average = float(value.mean())
    standard_error = float(value.std(ddof=1) / np.sqrt(len(value)))
    half = float(t.ppf(.975, len(value) - 1) * standard_error)
    return {"n": len(value), "df": len(value) - 1, "mean": average,
            "standard_error": standard_error, "confidence": .95,
            "interval": [average - half, average + half],
            "conditioning": conditioning, "values": value.tolist(),
            "descriptive_exploration": True}


def compare_panel(readouts, fits, worker_summary, meter):
    indexed = {(item["label"], item["world"]): item for item in readouts}
    costs = {name: np.asarray([indexed[f"main/{name}", world]["C"] for world in c.MAIN_WORLDS],
                             dtype=np.float64) for name in ("G", "R", "L0", "L1", "L2")}
    cpu = {name: float(np.mean([indexed[f"main/{name}", world]["cost"]["inclusive_cpu_seconds"]
                               for world in c.MAIN_WORLDS])) for name in costs}
    contrasts, curves = {}, []
    world_condition = "32 common worlds; conditional on these frozen trained endpoints and shared G/R realization"
    for fit in range(3):
        contrasts[f"L{fit}-G"] = paired_t(costs[f"L{fit}"] - costs["G"], world_condition)
        contrasts[f"L{fit}-R"] = paired_t(costs[f"L{fit}"] - costs["R"], world_condition)
        acquisition = float(fits[fit]["acquisition_cost"]["cpu_seconds"])
        for baseline in ("G", "R"):
            denominator = cpu[baseline] - cpu[f"L{fit}"]
            curves.append({"fit": fit, "baseline": baseline,
                           "training_inclusive_cpu_intercept": acquisition,
                           "learner_deployment_cpu_per_mission": cpu[f"L{fit}"],
                           "baseline_deployment_cpu_per_mission": cpu[baseline],
                           "baseline_minus_learner_cpu": denominator,
                           "break_even_missions": acquisition / denominator if denominator > 0 else None,
                           "break_even_scope": "per-fit acquisition-only intercept; excludes shared whole-study research cost",
                           "timing_scope": "inclusive main mission CPU; includes constructor/process/deadline/cancel/trace recording",
                           "no_request_cost_CPU_exchange_rate": True})
    contrasts["R-G"] = paired_t(costs["R"] - costs["G"], world_condition)
    for baseline in ("G", "R"):
        means = np.asarray([contrasts[f"L{fit}-{baseline}"]["mean"] for fit in range(3)])
        contrasts[f"three-fit-means-{baseline}"] = paired_t(means,
            "3 independent fits, conditional on the same 32-world panel; df2, not96 independent observations")
        average = np.mean(np.stack([costs[f"L{fit}"] for fit in range(3)]), axis=0)
        contrasts[f"shared-world-policy-average-{baseline}"] = paired_t(average - costs[baseline],
            "32 worlds, conditional on these three fixed policies; shared-world covariance retained")
    audit = []
    for fit, world in enumerate(c.AUDIT_WORLDS):
        audit.append({"fit": fit, "world": int(world),
                      "costs": {name: indexed[f"audit{fit}/{name}", world]["C"]
                                for name in ("G", "R", "initial", "final")},
                      "initial_program": "canonical G execution; zero neural identity checked offline",
                      "extra_comparison_worlds": 0})
    training_cpu = sum(float(record["acquisition_cost"]["cpu_seconds"]) for record in fits)
    frozen_cpu = sum(item["cost"]["inclusive_cpu_seconds"] for item in readouts
                     if not item["label"].startswith("train/"))
    return {"main_worlds": list(c.MAIN_WORLDS), "contrasts": contrasts, "audit": audit,
            "training_inclusive_CPU_curves": curves, "measured_main_deployment_cpu_per_mission": cpu,
            "training_acquisition_cpu_seconds": training_cpu,
            "frozen_inclusive_cpu_seconds": frozen_cpu,
            "worker_unattributed_CPU_residual": worker_summary["cost"]["phase_cpu_seconds"] - training_cpu - frozen_cpu,
            "unattributed_scope": "operation setup, final metadata/hash/publication and measurement-boundary residual; not zero",
            "total_research_CPU_measured_at_summary": meter.report()["cumulative_cpu_seconds"],
            "whole_study_research_CPU_intercept": meter.report()["cumulative_cpu_seconds"],
            "whole_study_research_CPU_intercept_scope":
                "one shared purchased study, counted once rather than once per fit; measured at comparison construction; excludes incompletely metered support",
            "CPU_request_cost_scalar_exchange_rate": None}


def run(root, out, args, context):
    """Called only by the admitted same-source reader; no independent admission."""
    root, out, worker_root = Path(root), Path(out), Path(context["worker_root"])
    meter, manifest = context["meter"], context["manifest"]
    worker_summary, worker_config = context["worker_summary"], context["worker_config"]
    audit = Audit(meter, context["source_identity"])
    readouts, training_results = [], []
    try:
        require(worker_config["mode"] == "worker" and worker_config["seed"] == 109259999 and
                worker_summary["launch_sha"] == worker_config["launch_sha"] and
                worker_config["source_identity"] == context["source_identity"] and
                worker_config["contract"] == c.frozen_contract(), "fixed worker configuration/source")
        records = validate_manifest(worker_root, manifest, worker_summary, context["source_identity"], meter)
        require("config.json" in manifest["files"] and read_json(worker_root / "config.json") == worker_config,
                "bound exact worker config bytes")
        models = FrozenModels(worker_root, manifest, audit)
        training = {}
        for fit in range(3):
            relative = f"checkpoints/fit{fit}_training.pt"
            state = models.torch.load(contained(worker_root, relative), map_location="cpu", weights_only=False)
            training[fit] = TrainingRead(fit, state)
        for record in records:
            meter.check()
            kind, fit = policy_kind(record["label"])
            result = read_mission(record, worker_root, manifest, audit, models,
                                  training[fit] if kind == "train" else None)
            relative = Path("checks") / record["label"] / f"{record['world']}.json"
            write_json(out / relative, result)
            readouts.append(result)
            write_json(out / "progress.json", {"checked_missions": len(readouts), "last_record": record,
                                               "counts": audit.counts, "cost": meter.report()})
        for fit in range(3):
            meter.check()
            result = training[fit].finish(root, worker_root, manifest, models)
            result["acquisition_cost"] = manifest["fits"][fit]["acquisition_cost"]
            training_results.append(result)
        endpoints = {item["name"]: item for item in manifest["endpoint_counts"]}
        require(len(endpoints) == len(manifest["endpoint_counts"]), "unique endpoint count names")
        for fit in range(3):
            counters = endpoints[f"train{fit}"]["counts"]
            for name, value in training[fit].state["counters"].items():
                same(counters[name], value, "endpoint learner event count " + name)
            for role, readings in training[fit].state["forward_counts"].items():
                for name, value in readings.items():
                    same(counters[role + "_" + name], value, "endpoint durable forward event count")
            same(endpoints[f"initial{fit}"]["counts"]["offline_audit_rows"], 240, "initial endpoint offline row count")
        frozen_rows = sum(item["counts"]["frozen_nn_rows"] for item in endpoints.values())
        # Completion can precede cache publication by one decision on expiry;
        # reader never invents the lost network payload merely to equal a counter.
        require(audit.counts.get("neural_final_rows", 0) <= frozen_rows <= 23760,
                "frozen reader rows bounded by committed worker inference")
        require(audit.counts.get("neural_initial_rows", 0) == 720 and
                audit.counts["neural_rows"] <= 24480, "initial/final reader row purchase")
        require(audit.counts["native_physical_states"] == 2051308 and
                audit.counts["native_motion_steps"] == 2049600 and audit.counts["missions"] == 1708 and
                audit.counts["training_missions"] == 1536 and audit.counts["frozen_missions"] == 172,
                "complete reader native/mission exposure")
        require(sum(len(item["rollout_checks"]) for item in readouts) == 2100, "all35x60 R decision traces")
        comparison = compare_panel(readouts, manifest["fits"], worker_summary, meter)
        write_json(out / "training-curves.json", {"schema": 1,
                   "fits": [{"fit": fit, "episodes": training[fit].curves} for fit in range(3)],
                   "raw_action_Q_update_ledger": "byte-bound worker mission NPZ files; retained without copying",
                   "optimizer_replayed": False})
        reading = {"schema": 1, "object": "B05_request_schedule", "status": "COMPLETE",
                   "mode": "reader", "launch_sha": args.launch_sha,
                   "worker_launch_sha": worker_summary["launch_sha"],
                   "source_identity": context["source_identity"], "missions": 1708,
                   "counts": audit.counts, "training_checks": training_results,
                   "comparison": comparison,
                   "numerical_comparison": {"native_masks_routes_FIFO_commands_motion": "exact",
                                             "G_costs_features_total_Q_frozen_residual": "exact",
                                             "gradient_norm_summary": "finite sign diagnostics; source cap10 verified; no norm-error outcome cutoff"},
                   "input_identities": {name: context[name] for name in
                                        ("config_identity", "summary_identity", "manifest_identity") if name in context},
                   "per_record_checks": "checks/<label>/<world>.json", "training_curves": "training-curves.json",
                   "missing_policy_cache_decisions": sum(len(item["policy_cache_missingness"]) for item in readouts),
                   "missing_neural_cache_decisions": sum(int(entry["neural_cache_missing"])
                        for item in readouts for entry in item["policy_cache_missingness"]),
                   "new_native_worlds": 0, "new_fits": 0, "optimizer_updates": 0,
                   "cost": meter.report()}
        write_json(out / "reading.json", reading)
        write_json(out / "summary.json", reading)
    except BaseException as error:
        reading = {"schema": 1, "object": "B05_request_schedule", "status": "FAILED",
                   "mode": "reader", "launch_sha": args.launch_sha,
                   "checked_missions": len(readouts), "counts": audit.counts,
                   "error": {"type": type(error).__name__, "message": str(error)}, "cost": meter.report()}
        write_json(out / "reading.json", reading)
        write_json(out / "summary.json", reading)
        raise
