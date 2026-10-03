"""Fixed B06 acquisition from the bound B05 bank, without task/model queries.

The admitted runner owns runtime setup and resource admission. Public functions
bind the bank, solve B, generate the fixed shuffle, fit one seed, load a bound
checkpoint and evaluate one endpoint. Torch is imported only on neural paths.
The optional numerical backend/solver injection supports pure engineering tests;
the scientific defaults are the frozen B05 scorer and the prescribed NumPy solve.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
from pathlib import Path
import time

import numpy as np

SEEDS = (109255101, 109255102, 109255103)
WORLDS = tuple(range(109253000, 109253032)) + tuple(range(109253900, 109253903))
OLD_HASHES = {
    "manifest.json": "3c3c7c84af0c0b55a4669e71bbad361d5b4e391e26bd237ee59a3f2aea639026",
    "config.json": "e675836d1775dcbb414395109ca062b8a3bb8341d196a39eab80f87db643e668",
    "summary.json": "d06794e1287e7fca7fd815ec77a4a1e17f6a133f87c42f023ccf50ca42605edd",
    "reader_summary": "8a0a24d9ec71fcfbd892e46729b61e98585a2fbba57ca0a5a4456610f9776612",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def array(value, shape, dtype, name):
    require(isinstance(value, np.ndarray) and value.shape == shape and
            value.dtype == np.dtype(dtype) and np.isfinite(value).all(), name + " shape/dtype/finite")
    return value


def digest(value):
    """B05 typed state hash, with lazy tensor conversion and no Torch import."""
    result = hashlib.sha256()
    def feed(item):
        if hasattr(item, "detach"):
            feed(item.detach().cpu().numpy())
        elif isinstance(item, np.ndarray):
            result.update(b"array" + item.dtype.str.encode() + repr(item.shape).encode())
            result.update(np.ascontiguousarray(item).tobytes())
        elif isinstance(item, dict):
            result.update(b"dict")
            for key in sorted(item, key=lambda x: (type(x).__name__, repr(x))):
                feed(key)
                feed(item[key])
        elif isinstance(item, (list, tuple)):
            result.update(type(item).__name__.encode() + str(len(item)).encode())
            for child in item:
                feed(child)
        else:
            result.update(type(item).__name__.encode() + repr(item).encode() + b";")
    feed(value)
    return result.hexdigest()


def file_identity(path):
    path = Path(path)
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            result.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": result.hexdigest()}


def contained(root, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and ".." not in relative.parts, "relative bank path")
    path = (Path(root) / relative).resolve()
    require(path.is_relative_to(Path(root).resolve()), "bank path escapes root")
    return path


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


class Counts:
    """Numeric sink boundaries; a failed sink is quarantined, never retried.

    Meter names are b06_<phase>_<counter>. Phases: bank_worker/bank_reader,
    constant_acquisition/constant_verification, fit0/1/2, and caller-specified
    endpoint load/evaluation phases. reserve runs before every scientific call.
    """
    def __init__(self, phase, meter=None, callback=None):
        self.phase, self.meter, self.callback = phase, meter, callback
        self.counts, self.sink_failed = {}, False

    def check(self):
        if self.meter is not None:
            self.meter.check()

    def event(self, event, name, amount=1, *, attempt=False):
        if attempt:
            self.check()
        require(type(amount) is int and amount >= 0, "numeric counter increment")
        if self.meter is not None:
            method = self.meter.reserve if attempt else self.meter.add
            method("b06_" + self.phase + "_" + name, amount)
        self.counts[name] = self.counts.get(name, 0) + amount
        if self.callback is not None and not self.sink_failed:
            try:
                self.callback(event, dict(self.counts))
            except BaseException:
                self.sink_failed = True
                raise


@dataclass(frozen=True)
class Bank:
    features: np.ndarray
    raw_g: np.ndarray
    teacher: np.ndarray
    keys: tuple
    provenance: dict

    def validate(self):
        array(self.features, (2100, 4, 303), "float32", "bank features")
        array(self.raw_g, (2100, 4), "float64", "bank G")
        array(self.teacher, (2100, 4), "float64", "bank teacher")
        require(self.keys == tuple((world, decision) for world in WORLDS for decision in range(60)),
                "fixed bank context roster/order")
        return self

    @property
    def identity(self):
        return digest((self.features, self.raw_g, self.teacher, self.keys, self.provenance))


def cohort_mean(trace, selected):
    """Reconstruct four ordered samples, retaining exact reuse multiplicity."""
    require(len(selected) == 4, "four selected teacher cohorts required")
    for name in ("cohort_complete", "tape_complete"):
        require(np.array_equal(trace[name], np.ones(4, dtype=np.uint8)), "complete teacher " + name)
    costs = array(trace["cohort_costs"], (4, 4), "float64", "cohort costs")
    cache = {}
    for index, cohort in enumerate(selected):
        require(cohort["tape"] == index and len(cohort["costs"]) == 4, "teacher cohort order")
        require(np.array_equal(costs[index], np.asarray(cohort["costs"], dtype=np.float64)), "selected teacher cost identity")
        key = bytes(trace["cohort_input_sha256"][index]).hex()
        require(key == cohort["input_sha256"], "teacher input identity")
        previous = cache.get(key)
        reused = int(trace["cohort_reuse"][index])
        require(reused == (-1 if previous is None else previous) and
                cohort["reused_cohort"] == (None if reused < 0 else reused), "teacher exact reuse alias")
        ids = trace["cohort_branches"][index]
        require(np.array_equal(ids, cohort["branches"]), "teacher branch identities")
        size = int(trace["tape_lengths"][index])
        require(0 <= size <= 8 and
                np.array_equal(trace["tape_times"][index, :size], cohort["times"]) and
                np.array_equal(trace["tapes"][index, :size], np.asarray(cohort["bits"]).reshape(size, 4)),
                "teacher sampled-tape identity")
        if previous is None:
            require(len(set(map(int, ids))) == 4, "four distinct teacher actions")
            for action, branch in enumerate(ids):
                branch = int(branch)
                require(branch in range(16) and trace["branch_complete"][branch] == 1 and
                        trace["branch_action"][branch] == action and trace["branch_tape"][branch] == index and
                        trace["branch_cost"][branch] == costs[index, action], "teacher action/score correspondence")
            cache[key] = index
        else:
            require(np.array_equal(ids, trace["cohort_branches"][previous]) and
                    np.array_equal(costs[index], costs[previous]), "teacher reused exact scores")
    return np.mean(np.stack([costs[index] for index in range(4)]), axis=0, dtype=np.float64)


def binding_bank(old_root, reader_summary_path, *, meter=None, event_callback=None, phase="bank_worker"):
    """Bind four fixed SHA anchors and70 mission/2100 rollout files in place.

    Returns only public cached features/G, ordered teacher means and provenance;
    no old realized future, outcome, age or DDQN output becomes a fit input.
    """
    require(phase in ("bank_worker", "bank_reader"), "bank accounting phase")
    count, root = Counts(phase, meter, event_callback), Path(old_root)
    originals = {}
    for name, expected in OLD_HASHES.items():
        path = Path(reader_summary_path) if name == "reader_summary" else root / name
        count.event("file_hash.attempt", "file_hash_attempts", attempt=True)
        identity = file_identity(path)
        count.event("file_hash.complete", "file_hashes")
        require(identity["sha256"] == expected, "fixed old SHA anchor " + name)
        originals[name] = identity
    manifest, config, summary = (json.loads((root / name).read_text()) for name in
                                 ("manifest.json", "config.json", "summary.json"))
    reader = json.loads(Path(reader_summary_path).read_text())
    require(manifest["schema"] == 1 and summary["status"] == reader["status"] == "COMPLETE" and
            summary["missions"] == reader["missions"] == 1708 and
            summary["source_identity"] == config["source_identity"] == reader["source_identity"],
            "original complete source certification")
    for name in ("config", "manifest", "summary"):
        require(reader["input_identities"][name + "_identity"]["sha256"] == originals[name + ".json"]["sha256"],
                "original reader input binding")
    records = [record for record in manifest["records"] if record["label"] == "main/R" or
               record["label"] in ("audit0/R", "audit1/R", "audit2/R")]
    records.sort(key=lambda record: record["world"])
    require(tuple(record["world"] for record in records) == WORLDS, "old35 teacher mission roster")
    bound, feature_rows, raw_rows, labels, keys = {}, [], [], [], []
    def bind(relative):
        require(relative not in bound and relative in manifest["files"], "unique manifested teacher file")
        path = contained(root, relative)
        count.event("file_hash.attempt", "file_hash_attempts", attempt=True)
        identity = file_identity(path)
        count.event("file_hash.complete", "file_hashes")
        expected = manifest["files"][relative]
        require(identity["sha256"] == expected["sha256"] and identity["bytes"] == expected["bytes"],
                "manifested teacher file identity")
        bound[relative] = identity
        return path
    for record in records:
        count.check()
        world = int(record["world"])
        label = "main/R" if world < 109253900 else f"audit{world - 109253900}/R"
        require(record["status"] == "COMPLETE" and record["completed_native_steps"] == 1200 and
                record["label"] == label, "selected old mission complete identity")
        metadata = json.loads(bind(record["metadata"]).read_text())
        require(metadata["status"] == "COMPLETE" and metadata["label"] == label and
                metadata["world"] == world and metadata["completed_decisions"] == 60 and
                metadata["completed_native_steps"] == 1200, "teacher mission metadata")
        with np.load(bind(record["npz"]), allow_pickle=False) as archive:
            features = array(archive["features"], (60, 4, 303), "float32", "mission features")
            reports = archive["reports"]
            require(reports.shape == (60,) and reports["costs"].dtype == np.float64 and
                    np.array_equal(reports["complete"], np.ones(60)) and
                    np.array_equal(reports["tick"], np.arange(60) * 20), "complete ordered canonical G reports")
            raw_g = array(reports["costs"], (60, 4), "float64", "mission raw G").copy()
        traces = metadata["rollout_traces"]
        require(len(traces) == len(metadata["decisions"]) == 60 and
                [item["decision"] for item in traces] == list(range(60)), "ordered teacher decision traces")
        for decision, item in enumerate(traces):
            count.check()
            saved = metadata["decisions"][decision]
            timing = saved["timing"]
            messages = [message for message in timing["messages"] if message["type"] == "cohort" and message["eligible"]]
            require(len(messages) == 4 and all(message["ready_ns"] <= message["received_ns"] <= timing["deadline_ns"]
                                              for message in messages), "four selected complete teacher publications")
            from ..b05_request_schedule.storage import R_SHAPES, R_STATS
            needed = ("cohort_complete", "cohort_reuse", "cohort_costs", "cohort_branches", "cohort_input_sha256",
                      "tape_complete", "tape_lengths", "tape_times", "tapes", "branch_complete", "branch_action",
                      "branch_tape", "branch_cost", "cohort_ready_ns", "stats")
            with np.load(bind(item["path"]), allow_pickle=False) as archive:
                trace = {name: archive[name] for name in needed}
            for name, value in trace.items():
                shape, dtype = R_SHAPES[name]
                array(value, shape, dtype, "teacher trace " + name)
            require(np.array_equal(trace["stats"], [item["stats"][name] for name in R_STATS]) and
                    item["stats"]["cohorts_complete"] == 4, "old complete rollout counter mirrors")
            require(all(int(trace["cohort_ready_ns"][index]) <= message["ready_ns"]
                        for index, message in enumerate(messages)), "teacher commit precedes selected publication")
            count.event("label.attempt", "label_attempts", attempt=True)
            labels.append(cohort_mean(trace, saved["cohorts"]))
            count.event("label.complete", "label_contexts")
            keys.append((world, decision))
        feature_rows.append(features.copy())
        raw_rows.append(raw_g)
    require(len(bound) == 2170, "70 mission plus2100 rollout identity purchase")
    provenance = {"anchors": originals, "files": bound, "old_source_identity": config["source_identity"],
                  "old_reader_physics_reused": True, "new_teacher_queries": 0}
    bank = Bank(np.concatenate(feature_rows), np.concatenate(raw_rows), np.stack(labels), tuple(keys), provenance).validate()
    for value in (bank.features, bank.raw_g, bank.teacher):
        value.flags.writeable = False
    return bank


def compose_q(raw_g, residual):
    """B05 FP64 composition: divide G before adding cast FP32 residual."""
    require(raw_g.shape == residual.shape and raw_g.shape[-1] == 4 and raw_g.dtype == np.float64 and
            residual.dtype == np.float32 and np.isfinite(raw_g).all() and np.isfinite(residual).all(), "Q inputs")
    result = raw_g / 1200. + residual.astype(np.float64)
    require(np.isfinite(result).all(), "finite composed Q")
    return result


def greedy(total, raw_g):
    require(total.shape == raw_g.shape and total.dtype == raw_g.dtype == np.float64 and
            total.shape[-1] == 4 and np.isfinite(total).all() and np.isfinite(raw_g).all(), "greedy inputs")
    return np.lexsort((np.broadcast_to(np.arange(4), total.shape), raw_g, total), axis=-1)[..., 0]


def relative_errors(q, raw_g, teacher):
    anchor = np.argmin(raw_g, axis=1)
    rows = np.arange(len(q))
    return (q - q[rows, anchor, None]) - (teacher - teacher[rows, anchor, None]) / 1200.


def solve_constant(bank, *, meter=None, event_callback=None, solver=None, phase="constant_acquisition"):
    """One ordered G-anchored LS solve; verification uses distinct accounting."""
    require(phase in ("constant_acquisition", "constant_verification"), "constant phase")
    bank.validate()
    count = Counts(phase, meter, event_callback)
    H, z, basis = np.zeros((4, 4), dtype=np.float64), np.zeros(4, dtype=np.float64), np.eye(4, dtype=np.float64)
    count.event("system.attempt", "system_attempts", attempt=True)
    count.event("system.rows.reserve", "system_attempted_action_rows", 8400, attempt=True)
    for raw, teacher in zip(bank.raw_g, bank.teacher):
        count.check()
        anchor = int(np.argmin(raw))
        for action in range(4):
            A = basis[action] - basis[anchor]
            y = (teacher[action] - teacher[anchor]) - (raw[action] - raw[anchor])
            H += np.outer(A, A)
            z += A * y
            count.event("system.row.complete", "system_action_rows")
    count.event("system.complete", "systems")
    bordered = np.zeros((5, 5), dtype=np.float64)
    bordered[:4, :4], bordered[:4, 4], bordered[4, :4] = H, 1., 1.
    rhs = np.concatenate((z, [0.]))
    count.event("solve.attempt", "solve_attempts", attempt=True)
    solution = (np.linalg.solve if solver is None else solver)(bordered, rhs)
    array(solution, (5,), "float64", "bordered solution")
    count.event("solve.complete", "solves")
    return {"H": H, "z": z, "b": solution[:4].copy(), "lambda": float(solution[4]),
            "normal_residual": H @ solution[:4] + solution[4] - z,
            "constraint_residual": float(solution[:4].sum()), "counts": count.counts,
            "bank_identity": bank.identity}


def shuffle_batches(fit_index, *, rng=None):
    """Yield(epoch,batch,indices),64x(32 batches64 + final52),zero-based."""
    require(type(fit_index) is int and fit_index in range(3), "fit index")
    if rng is None:
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((109259999, 51, fit_index))))
    for epoch in range(64):
        permutation = np.asarray(rng.permutation(2100))
        require(permutation.dtype.kind in "iu" and np.array_equal(np.sort(permutation), np.arange(2100)), "full shuffle permutation")
        for batch, start in enumerate(range(0, 2100, 64)):
            yield epoch, batch, permutation[start:start + 64].astype(np.int64, copy=True)


def anchored_loss(raw_g, teacher, residual, torch):
    """Keep learned anchor in gradient; FP64 q is composed before subtraction."""
    G = torch.as_tensor(raw_g, dtype=torch.float64, device="cpu")
    target = torch.as_tensor(teacher, dtype=torch.float64, device="cpu")
    anchor = torch.as_tensor(np.argmin(raw_g, axis=1), dtype=torch.int64, device="cpu")
    q = G / 1200. + residual.to(torch.float64)
    q_anchor = q.gather(1, anchor[:, None])
    target_anchor = target.gather(1, anchor[:, None])
    errors = (q - q_anchor) - (target - target_anchor) / 1200.
    return errors.square().mean()


class TorchBackend:
    """One concrete lazy CPU backend, replaceable by a fake in engineering tests."""
    def __init__(self, seed, *, training):
        import torch
        from ..b05_request_schedule.learner import ResidualScorer
        self.torch, self.model = torch, ResidualScorer(seed)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=3e-4, betas=(.9, .999), eps=1e-8,
                                          weight_decay=0, amsgrad=False, foreach=False, fused=False,
                                          maximize=False) if training else None

    def parameters(self):
        return {name: value.detach().clone() for name, value in self.model.state_dict().items()}

    def optimizer_state(self):
        return copy.deepcopy(self.optimizer.state_dict()) if self.optimizer is not None else None

    def zero_head(self):
        return bool(self.torch.count_nonzero(self.model.layers[-1].weight) == 0 and
                    self.torch.count_nonzero(self.model.layers[-1].bias) == 0)

    def forward(self, features, *, training):
        tensor = self.torch.from_numpy(np.array(features, dtype=np.float32, copy=True))
        if training:
            self.model.train()
            return self.model(tensor).reshape(-1, 4)
        self.model.eval()
        with self.torch.no_grad():
            return self.model(tensor).reshape(-1, 4).numpy().copy()

    def loss(self, raw_g, teacher, residual):
        return anchored_loss(raw_g, teacher, residual, self.torch)

    def zero_grad(self):
        self.optimizer.zero_grad(set_to_none=True)

    def backward(self, loss):
        loss.backward()

    def clip(self):
        parameters = list(self.model.parameters())
        require(all(parameter.grad is not None and bool(self.torch.isfinite(parameter.grad).all())
                    for parameter in parameters), "all finite gradients")
        before = float(self.torch.nn.utils.clip_grad_norm_(parameters, 10., error_if_nonfinite=True))
        after = float(self.torch.sqrt(sum(parameter.grad.double().square().sum() for parameter in parameters)))
        require(np.isfinite(before) and np.isfinite(after), "finite gradient norms")
        return before, after

    def step(self):
        self.optimizer.step()
        for value in list(self.model.parameters()) + [value for state in self.optimizer.state.values()
                                                     for value in state.values() if self.torch.is_tensor(value)]:
            require(bool(self.torch.isfinite(value).all()), "finite parameters/optimizer state")

    def validate_optimizer_steps(self, expected):
        require(len(self.optimizer.state) == len(list(self.model.parameters())) and
                all(float(state["step"]) == expected for state in self.optimizer.state.values()),
                "all Adam parameter step counts")

    def save(self, path, payload):
        temporary = Path(str(path) + ".partial")
        self.torch.save(payload, temporary)
        temporary.replace(path)

    def load(self, payload):
        self.model.load_state_dict(payload["parameters"], strict=True)
        self.model.eval().requires_grad_(False)


def checkpoint_payload(backend, fit_index, stage, source_identity, launch_sha, bank_identity, initial_hash):
    weights = backend.parameters()
    for value in weights.values():
        converted = value.detach().cpu().numpy() if hasattr(value, "detach") else value
        require(converted.dtype == np.float32 and np.isfinite(converted).all(), "finite CPU FP32 weights")
    return {"schema": 1, "fit": fit_index, "stage": stage, "init_seed": SEEDS[fit_index],
            "source_identity": source_identity, "launch_sha": launch_sha, "bank_identity": bank_identity,
            "parameters": weights, "certificate": {"parameter_count": 55553, "dtype": "float32", "device": "cpu",
            "parameter_sha256": digest(weights), "initial_parameter_sha256": initial_hash,
            "exact_zero_head": backend.zero_head()}}


def evaluate_endpoint(bank, scorer, *, phase, meter=None, event_callback=None):
    """Exactly ascending64/52 full-bank forwards, with no additional calls."""
    bank.validate()
    count, chunks = Counts(phase, meter, event_callback), []
    try:
        for start in range(0, 2100, 64):
            rows = bank.features[start:start + 64].reshape(-1, 303)
            count.event("forward.attempt", "forward_attempts", attempt=True)
            count.event("forward.rows.reserve", "forward_attempted_rows", len(rows), attempt=True)
            result = scorer.forward(rows, training=False)
            count.event("forward.complete", "forward_calls")
            count.event("forward.rows.complete", "forward_rows", len(rows))
            array(result, (len(rows) // 4, 4), "float32", "endpoint residual")
            chunks.append(result)
    except BaseException as error:
        error.b06_partial_counts = {phase: dict(count.counts)}
        raise
    residual = np.concatenate(chunks)
    q = compose_q(bank.raw_g, residual)
    errors = relative_errors(q, bank.raw_g, bank.teacher)
    action = greedy(q, bank.raw_g)
    teacher_min = bank.teacher.min(axis=1)
    ordered = np.sort(q, axis=1)
    teacher_ordered = np.sort(bank.teacher, axis=1)
    return {"residual": residual, "q": q, "relative_errors": errors, "relative_loss": np.mean(errors ** 2, axis=1),
            "action": action, "teacher_action": np.argmin(bank.teacher, axis=1),
            "regret": bank.teacher[np.arange(2100), action] - teacher_min,
            "ties": q == q.min(axis=1)[:, None], "teacher_ties": bank.teacher == teacher_min[:, None],
            "margin": ordered[:, 1] - ordered[:, 0], "teacher_margin": teacher_ordered[:, 1] - teacher_ordered[:, 0],
            "counts": count.counts}


def fit_endpoint(bank, fit_index, out, *, source_identity, launch_sha, meter=None, event_callback=None, backend=None):
    """Fit one fixed seed; persist every pre-attempt and completion, never retry.

    Outputs fit<index>_{initial,final,training}.pt, initial/final-bank.npz,
    updates.jsonl, epochs.json and fit.json under the caller's dedicated out.
    A failure preserves the append-only journal and FAILED fit.json; no resume.
    """
    bank.validate()
    require(type(fit_index) is int and fit_index in range(3), "fit index")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    require(not (out / "updates.jsonl").exists(), "fit cannot replay existing attempt")
    count, bank_hash = Counts(f"fit{fit_index}", meter, event_callback), bank.identity
    wall, cpu = time.perf_counter(), time.process_time()
    result = {"schema": 1, "fit": fit_index, "source_identity": source_identity, "launch_sha": launch_sha,
              "bank_identity": bank_hash, "init_seed": SEEDS[fit_index], "status": "STARTED"}
    journal = (out / "updates.jsonl").open("x", buffering=1)
    current, rng = None, None
    try:
        count.event("constructor.attempt", "scorer_constructor_attempts", attempt=True)
        backend = TorchBackend(SEEDS[fit_index], training=True) if backend is None else backend
        count.event("constructor.complete", "scorer_constructors")
        initial_weights = backend.parameters()
        initial_hash = digest(initial_weights)
        require(backend.zero_head(), "exact zero output head")
        initial_payload = checkpoint_payload(backend, fit_index, "initial", source_identity, launch_sha, bank_hash, initial_hash)
        count.check()
        path = out / f"fit{fit_index}_initial.pt"
        backend.save(path, initial_payload)
        result["initial"] = file_identity(path)
        evaluation = evaluate_endpoint(bank, backend, phase=f"fit{fit_index}_initial_bank", meter=meter, event_callback=event_callback)
        require(not evaluation["residual"].any() and np.array_equal(evaluation["action"], np.argmin(bank.raw_g, axis=1)),
                "offline initial G identity")
        count.check()
        np.savez_compressed(out / "initial-bank.npz", **{key: value for key, value in evaluation.items() if key != "counts"})
        result["initial_bank"] = file_identity(out / "initial-bank.npz")
        result["initial_forward_counts"] = evaluation["counts"]
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((109259999, 51, fit_index))))
        epochs = []
        weighted_loss = 0.
        for epoch, batch, indices in shuffle_batches(fit_index, rng=rng):
            start_wall, start_cpu = time.perf_counter(), time.process_time()
            current = {"fit": fit_index, "epoch": epoch, "batch": batch, "indices": indices.tolist(),
                       "batch_size": len(indices), "number": epoch * 33 + batch + 1,
                       "parameters_before": digest(backend.parameters()), "optimizer_before": digest(backend.optimizer_state()),
                       "status": "ATTEMPTED", "completed": False}
            journal.write(json.dumps(current, sort_keys=True, allow_nan=False) + "\n")
            count.event("update.attempt", "update_attempts", attempt=True)
            backend.zero_grad()
            count.event("forward.attempt", "forward_attempts", attempt=True)
            count.event("forward.rows.reserve", "forward_attempted_rows", 4 * len(indices), attempt=True)
            residual = backend.forward(bank.features[indices].reshape(-1, 303), training=True)
            count.event("forward.complete", "forward_calls")
            count.event("forward.rows.complete", "forward_rows", 4 * len(indices))
            loss = backend.loss(bank.raw_g[indices], bank.teacher[indices], residual)
            value = float(loss.detach()) if hasattr(loss, "detach") else float(loss)
            require(np.isfinite(value) and value >= 0, "finite nonnegative loss")
            current["loss"] = value
            count.event("backward.attempt", "backward_attempts", attempt=True)
            backend.backward(loss)
            count.event("backward.complete", "backwards")
            count.event("clip.attempt", "clip_attempts", attempt=True)
            before, after = backend.clip()
            require(np.isfinite(before) and np.isfinite(after) and before >= 0 and after >= 0, "gradient diagnostic signs")
            count.event("clip.complete", "clips")
            current.update(gradient_norm_before=before, gradient_norm_after=after)
            count.event("optimizer.attempt", "optimizer_attempts", attempt=True)
            backend.step()
            count.event("optimizer.complete", "optimizer_steps")
            current.update(parameters_after=digest(backend.parameters()), optimizer_after=digest(backend.optimizer_state()))
            count.event("update.complete", "updates")
            current.update(completed=True, status="COMPLETE", cpu_seconds=time.process_time() - start_cpu,
                           wall_seconds=time.perf_counter() - start_wall, counts=dict(count.counts))
            journal.write(json.dumps(current, sort_keys=True, allow_nan=False) + "\n")
            current = None  # Finalization failure cannot relabel a completed update.
            weighted_loss += value * len(indices)
            if batch == 32:
                epochs.append({"epoch": epoch, "context_weighted_online_loss": weighted_loss / 2100.,
                               "contexts": 2100, "updates": 33, "fixed_endpoint_evaluation": False})
                weighted_loss = 0.
        require(count.counts["updates"] == 2112 and count.counts["forward_rows"] == 537600, "fixed complete fit purchase")
        backend.validate_optimizer_steps(2112)
        final_payload = checkpoint_payload(backend, fit_index, "final", source_identity, launch_sha, bank_hash, initial_hash)
        path = out / f"fit{fit_index}_final.pt"
        count.check()
        backend.save(path, final_payload)
        result["final"] = file_identity(path)
        evaluation = evaluate_endpoint(bank, backend, phase=f"fit{fit_index}_final_bank", meter=meter, event_callback=event_callback)
        count.check()
        np.savez_compressed(out / "final-bank.npz", **{key: value for key, value in evaluation.items() if key != "counts"})
        result["final_bank"] = file_identity(out / "final-bank.npz")
        result["final_forward_counts"] = evaluation["counts"]
        final_weights = backend.parameters()
        def numpy(value):
            return value.detach().cpu().numpy() if hasattr(value, "detach") else value
        delta = np.concatenate([(numpy(final_weights[name]) - numpy(value)).reshape(-1).astype(np.float64)
                                for name, value in initial_weights.items()])
        result["parameter_motion"] = {"l2": float(np.linalg.norm(delta)), "max": float(np.abs(delta).max()),
                                      "changed_coordinates": int(np.count_nonzero(delta))}
        path = out / f"fit{fit_index}_training.pt"
        count.check()
        backend.save(path, {"schema": 1, "fit": fit_index, "init_seed": SEEDS[fit_index],
                           "bank_identity": bank_hash, "source_identity": source_identity, "launch_sha": launch_sha,
                           "optimizer": backend.optimizer_state(), "rng": rng.bit_generator.state,
                           "counts": dict(count.counts), "initial_parameter_sha256": initial_hash,
                           "final_parameter_sha256": digest(final_weights)})
        result["training"] = file_identity(path)
        write_json(out / "epochs.json", epochs)
        result["epochs"] = file_identity(out / "epochs.json")
        result["status"] = "COMPLETE"
    except BaseException as error:
        result.update(status="FAILED", error={"type": type(error).__name__, "message": str(error)})
        if hasattr(error, "b06_partial_counts"):
            result["partial_phase_counts"] = error.b06_partial_counts
        if current is not None:
            current.update(status="FAILED", completed=count.counts.get("updates", 0) >= current["number"],
                           counts=dict(count.counts), cpu_seconds=time.process_time() - start_cpu,
                           wall_seconds=time.perf_counter() - start_wall)
            journal.write(json.dumps(current, sort_keys=True, allow_nan=False) + "\n")
        if backend is not None:
            try:
                path = out / f"fit{fit_index}_partial.pt"
                partial = {"schema": 1, "fit": fit_index, "init_seed": SEEDS[fit_index],
                           "stage": "partial", "bank_identity": bank_hash,
                           "source_identity": source_identity, "launch_sha": launch_sha,
                           "parameters": backend.parameters(), "optimizer": backend.optimizer_state(),
                           "rng": None if rng is None else rng.bit_generator.state, "counts": dict(count.counts)}
                backend.save(path, partial)
                result["partial"] = file_identity(path)
                result["partial_parameter_sha256"] = digest(partial["parameters"])
                result["partial_optimizer_sha256"] = digest(partial["optimizer"])
            except BaseException as finalization_error:
                result["partial_save_error"] = {"type": type(finalization_error).__name__, "message": str(finalization_error)}
        raise
    finally:
        journal.close()
        result.update(counts=dict(count.counts), cpu_seconds=time.process_time() - cpu,
                      wall_seconds=time.perf_counter() - wall, update_evidence=file_identity(out / "updates.jsonl"))
        write_json(out / "fit.json", result)
    return result


def load_scorer(path, identity, *, fit_index, stage, source_identity, bank_identity,
                meter=None, event_callback=None, phase="checkpoint_load"):
    """Bind bytes BEFORE Torch load; enforce initial/final source/bank/seed."""
    require(type(fit_index) is int and fit_index in range(3) and stage in ("initial", "final"), "checkpoint fit/stage")
    count = Counts(phase, meter, event_callback)
    count.check()
    actual = file_identity(path)
    require(actual["sha256"] == identity["sha256"] and actual["bytes"] == identity["bytes"], "checkpoint byte identity")
    count.event("load.attempt", "checkpoint_load_attempts", attempt=True)
    import torch
    payload = torch.load(path, map_location="cpu", weights_only=True)
    require(payload["schema"] == 1 and payload["fit"] == fit_index and payload["stage"] == stage and
            payload["init_seed"] == SEEDS[fit_index] and payload["source_identity"] == source_identity and
            payload["bank_identity"] == bank_identity, "checkpoint source/bank/fit/stage lineage")
    count.event("load.complete", "checkpoint_loads")
    count.event("constructor.attempt", "scorer_constructor_attempts", attempt=True)
    backend = TorchBackend(SEEDS[fit_index], training=False)
    count.event("constructor.complete", "scorer_constructors")
    certificate = payload["certificate"]
    require(digest(backend.parameters()) == certificate["initial_parameter_sha256"] and
            digest(payload["parameters"]) == certificate["parameter_sha256"] and
            certificate["parameter_count"] == 55553 and certificate["device"] == "cpu" and
            certificate["dtype"] == "float32", "checkpoint architecture and typed weight identities")
    expected = backend.parameters()
    require(payload["parameters"].keys() == expected.keys(), "checkpoint weight keys")
    for name, value in payload["parameters"].items():
        actual = value.detach().cpu().numpy() if hasattr(value, "detach") else value
        require(actual.dtype == np.float32 and actual.shape == expected[name].shape and
                np.isfinite(actual).all() and
                (not hasattr(value, "device") or value.device.type == "cpu"),
                "checkpoint weight CPU/FP32/shape/finite")
    backend.load(payload)
    require(backend.zero_head() == certificate["exact_zero_head"] and
            (stage != "initial" or (backend.zero_head() and certificate["parameter_sha256"] ==
                                     certificate["initial_parameter_sha256"])), "checkpoint initial/head certificate")
    # Validate loaded weights without another forward.
    checkpoint_payload(backend, fit_index, stage, source_identity, payload["launch_sha"], bank_identity,
                       certificate["initial_parameter_sha256"])
    backend.payload, backend.load_counts = payload, dict(count.counts)
    return backend
