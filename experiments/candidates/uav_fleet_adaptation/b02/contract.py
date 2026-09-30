"""Frozen scientific identities and counts; no production tuning interface."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path


ARMS = ("S0", "BC", "S_greedy", "S_sampled", "C_memo", "C7_memo")
PHASES = ("expert", "aggregate1", "aggregate2")
SOURCE_PINS = {
    "experiments/candidates/uav_local_history/b01/controller.py":
        "b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2",
    "experiments/candidates/ucope/uav_motion_prefix_b01/environment.py":
        "fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6",
    "envs/pettingzoo/uav_env.py":
        "fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e",
    "envs/pettingzoo/env_adapter.py":
        "8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40",
    "experiments/candidates/uav_local_history/b01/study.py":
        "5fb3a1538a29bc5dd613a49fdd469d351876e8b070794171956a290651cdb8ec",
}


@dataclass(frozen=True)
class Protocol:
    training_worlds: tuple[tuple[int, ...], ...] = (
        tuple(range(29340000, 29340128)),
        tuple(range(29340128, 29340192)),
        tuple(range(29340192, 29340256)),
    )
    evaluation_worlds: tuple[int, ...] = tuple(range(29341000, 29341032))
    init_seed: int = 29342001
    shuffle_root: int = 29342002
    sampling_root: int = 29342003
    horizon: int = 256
    n_agents: int = 5
    period: int = 4
    epochs: tuple[int, ...] = (30, 20, 20)
    batch_size: int = 512
    learning_rate: float = 3e-4
    grad_norm: float = 1.0

    def validate(self):
        if self.n_agents != 5 or self.period != 4 or self.horizon <= 0 or self.horizon % self.period:
            raise ValueError("fixed five-agent/four-tick contract violated")
        if len(self.training_worlds) != 3 or len(self.epochs) != 3:
            raise ValueError("exactly three optimization phases required")
        training = [s for phase in self.training_worlds for s in phase]
        all_worlds = training + list(self.evaluation_worlds)
        if len(set(all_worlds)) != len(all_worlds) or not all_worlds:
            raise ValueError("training/evaluation worlds overlap or are empty")
        if any(not phase for phase in self.training_worlds) or not self.evaluation_worlds:
            raise ValueError("empty phase/panel")
        if len({self.init_seed, self.shuffle_root, self.sampling_root}) != 3:
            raise ValueError("randomness domains require distinct roots")
        if any(x <= 0 for x in self.epochs) or self.batch_size <= 0:
            raise ValueError("invalid optimizer exposure")
        cumulative = 0
        for worlds in self.training_worlds:
            cumulative += len(worlds) * self.horizon // self.period * self.n_agents
            if cumulative % self.batch_size:
                raise ValueError("each accumulated dataset must divide into full batches")
        return self

    def expected(self):
        self.validate()
        decisions = self.horizon // self.period * self.n_agents
        phase_labels = [len(s) * decisions for s in self.training_worlds]
        datasets = [sum(phase_labels[:i + 1]) for i in range(3)]
        phase_updates = [n // self.batch_size * e for n, e in zip(datasets, self.epochs)]
        training_episodes = sum(map(len, self.training_worlds))
        evaluation_episodes = len(ARMS) * len(self.evaluation_worlds)
        return {
            "training_episodes": training_episodes,
            "evaluation_episodes": evaluation_episodes,
            "complete_episodes": training_episodes + evaluation_episodes,
            "training_native_steps": training_episodes * self.horizon,
            "evaluation_native_steps": evaluation_episodes * self.horizon,
            "native_steps": (training_episodes + evaluation_episodes) * self.horizon,
            "phase_labels": phase_labels, "datasets": datasets,
            "expert_label_requests": sum(phase_labels),
            "full_C_requests": sum(phase_labels) + len(self.evaluation_worlds) * decisions,
            "C7_requests": len(self.evaluation_worlds) * decisions,
            "phase_updates": phase_updates, "optimizer_updates": sum(phase_updates),
            "sample_presentations": sum(n * e for n, e in zip(datasets, self.epochs)),
            "helper_request_ceiling": sum(phase_labels) + 5 * len(self.evaluation_worlds) * decisions,
            "neural_rollout_row_ceiling": sum(phase_labels[1:]) + 4 * len(self.evaluation_worlds) * decisions,
            "sampled_draws": len(self.evaluation_worlds) * decisions,
            "fits": 1,
        }

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))


FROZEN = Protocol().validate()


def array_digest(*arrays):
    """Bind shape/dtype/bytes, including the precise training order."""
    digest = hashlib.sha256()
    for array in arrays:
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(json.dumps(list(array.shape)).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def source_identities(repo: Path):
    identities = {}
    for relative, expected in SOURCE_PINS.items():
        value = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if value != expected:
            raise ValueError(f"bound teacher/host source changed: {relative}")
        identities[relative] = value
    for path in sorted((repo / "experiments/candidates/uav_fleet_adaptation/b02").glob("*.py")):
        identities[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return identities
