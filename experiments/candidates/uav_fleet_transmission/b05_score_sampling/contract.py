"""Published B05 population, random addresses, sources and exposure contract."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import (
    BOUND_SOURCES, CANONICAL_ASSETS,
)
from .policies import ARMS, ORDINARY_ARMS, STUDENT_ARMS

OBJECT = "UAV-SCORE-SAMPLING-B05"
MASTER_SEED = 29630100
CALIBRATION = {
    "launch_sha": "98307b0c5cb6e42763458d780568d105d3f631af",
    "evidence_commit": "978c622c37207067dd673247cf6729d786383304",
    "reading_path": "runs/uav_fleet_adaptation/b04_native_development_a01/reading.json",
    "reading_sha256": "93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50",
    "winners": ["S_T2", "S_T1"], "new_calibrations": 0,
}
LOW, HIGH = (0., 0., 50.), (1000., 1000., 150.)


@dataclass(frozen=True)
class Protocol:
    worlds: tuple = tuple(range(29630000, 29630032))
    sampling_roots: tuple = (29630101, 29630102)
    actor_constructor_seeds: tuple = (29630111, 29630112)
    bootstrap_seed: int = 29630191
    bootstrap_resamples: int = 10000
    horizon: int = 256

    def validate(self):
        addresses = (*self.worlds, *self.sampling_roots, *self.actor_constructor_seeds, self.bootstrap_seed)
        if (not self.worlds or len(self.sampling_roots) != 2 or len(self.actor_constructor_seeds) != 2
                or any(type(x) is not int or x < 0 for x in addresses)
                or len(set(addresses)) != len(addresses) or self.horizon <= 0 or self.horizon % 4
                or self.bootstrap_resamples <= 0):
            raise ValueError("invalid or overlapping B05 protocol")
        return self

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        for name in ("worlds", "sampling_roots", "actor_constructor_seeds"):
            value[name] = tuple(value[name])
        return cls(**value).validate()

    def episode_order(self, world_index):
        cells = [(arm, tape) for arm in ARMS for tape in ((-1,) if arm == "C" else (0, 1))]
        offset = world_index % len(cells)
        return cells[offset:] + cells[:offset]

    def expected(self):
        worlds, decisions = len(self.worlds), self.horizon // 4 * 5
        return dict(complete_episodes=worlds * 13, explicit_resets=worlds * 13,
                    constructor_resets=1, native_step_calls=worlds * 13 * self.horizon,
                    native_steps=worlds * 13 * self.horizon,
                    ordinary_queries=worlds * 7 * decisions, student_queries=worlds * 6 * decisions,
                    sampled_draws=worlds * 12 * decisions, score_tail_evaluations=worlds * 2 * decisions,
                    fits=0, optimizer_updates=0, labels=0, calibrations=0, training_native_steps=0)


FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    found = {}
    for relative, expected in BOUND_SOURCES.items():
        digest = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("bound source changed: " + relative)
        found[relative] = digest
    extra = repo / "experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py"
    own = repo / "experiments/candidates/uav_fleet_transmission/b05_score_sampling"
    for path in [extra, *sorted(own.glob("*.py"))]:
        found[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def actor_for(arm, models):
    return models[1 if arm == "S_L1" else 0] if arm in STUDENT_ARMS else None


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)
