"""Prospective worlds, independent addresses, balanced order and exact B07 bill."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import numpy as np

from experiments.candidates.uav_fleet_transmission.b06_cadence.contract import (
    LOW, HIGH, array_digest, write_json, source_identities as inherited_sources,
)

OBJECT = "UAV-JOINT-RENEWAL-B07"
MASTER_SEED = 29750100
ARMS = ("C", "Q10")
SCHEDULES = ("SYNC", "DISPERSED")
STRATA = (("C", -1), ("Q10", 0), ("Q10", 1))
CELLS = tuple((arm, schedule) for arm in ARMS for schedule in SCHEDULES)


def cell_name(arm, schedule):
    return arm + "/" + schedule


@dataclass(frozen=True)
class Protocol:
    worlds: tuple = tuple(range(29750000, 29750032))
    sampling_roots: tuple = (29750101, 29750102)
    phase_root: int = 29750110
    bootstrap_seed: int = 29750191
    bootstrap_resamples: int = 10000
    horizon: int = 256

    def validate(self):
        addresses = (*self.worlds, *self.sampling_roots, self.phase_root, self.bootstrap_seed)
        if (not self.worlds or len(self.sampling_roots) != 2
                or any(type(x) is not int or x < 0 for x in addresses)
                or len(set(addresses)) != len(addresses)
                or type(self.horizon) is not int or self.horizon < 8 or self.horizon % 4
                or type(self.bootstrap_resamples) is not int or self.bootstrap_resamples <= 0):
            raise ValueError("invalid or overlapping B07 protocol")
        return self

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        for name in ("worlds", "sampling_roots"):
            value[name] = tuple(value[name])
        return cls(**value).validate()

    def phase_offsets(self, world):
        if type(world) is not int or world not in self.worlds:
            raise ValueError("undeclared world")
        return np.random.default_rng(np.random.SeedSequence([self.phase_root, world])).permutation(
            np.array([0, 0, 1, 2, 3], dtype=np.int64))

    def phases(self, world, q, schedule):
        if type(q) is not int or q not in range(4) or schedule not in SCHEDULES:
            raise ValueError("undeclared offset or schedule")
        offsets = self.phase_offsets(world)
        return np.full(5, q, dtype=np.int64) if schedule == "SYNC" else (q + offsets) % 4

    def episode_order(self, world_index):
        if type(world_index) is not int or not 0 <= world_index < len(self.worlds):
            raise ValueError("invalid world index")
        block = world_index // 2
        result = []
        for j in range(4):
            q = (block + j) % 4
            for k in range(3):
                arm, tape = STRATA[(block + j + k) % 3]
                schedules = SCHEDULES if (world_index + j + k) % 2 == 0 else SCHEDULES[::-1]
                result.extend((arm, schedule, q, tape) for schedule in schedules)
        return result

    def expected(self):
        episodes = len(self.worlds) * 24
        queries = episodes * self.horizon // 4 * 5
        return dict(complete_episodes=episodes, explicit_resets=episodes, constructor_resets=1,
                    native_step_calls=episodes * self.horizon, native_steps=episodes * self.horizon,
                    schedule_checks=episodes * self.horizon * 5, ordinary_queries=queries,
                    sampled_draws=queries * 2 // 3, student_queries=0, actor_rows=0,
                    analytic_helper_queries=0, score_tail_evaluations=0,
                    fits=0, optimizer_updates=0, labels=0, calibrations=0, training_native_steps=0)

    def check_counts(self, counts):
        if (set(counts) != set(self.expected())
                or any(type(value) is not int or value < 0 for value in counts.values())
                or counts != self.expected()):
            raise AssertionError("B07 exact exposure differs")

    def model_ceiling(self):
        queries = self.expected()["ordinary_queries"]
        return dict(trajectories=27 * queries, model_ticks=108 * queries,
                    objective_reductions=108 * queries, candidate_link_evaluations=2160 * queries,
                    setup_link_evaluations=100 * queries)


FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    found = inherited_sources(repo)
    own = repo / "experiments/candidates/uav_fleet_transmission/b07_joint_renewal"
    for path in sorted(own.glob("*.py")):
        found[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found
