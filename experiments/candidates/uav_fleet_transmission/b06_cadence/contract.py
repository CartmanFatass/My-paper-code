"""Prospectively fixed B06 panel, addresses, exposure and source bindings."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_transmission.b05_score_sampling.contract import (
    CALIBRATION, CANONICAL_ASSETS, LOW, HIGH, actor_for, array_digest, write_json,
    source_identities as inherited_sources,
)
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.policies import (
    ARMS, ORDINARY_ARMS, STUDENT_ARMS,
)

OBJECT = "UAV-CADENCE-USE-B06"
MASTER_SEED = 29670100
MODES = ("H4", "E", "H1")
CELLS = tuple((arm, mode) for arm in ARMS[:6] for mode in MODES) + (("Bstar_L0", "H4"),)
LOCAL_ASSET_ROOT = Path("/home/fires/hmasd-wsl/temp/directions/uav_fleet_transmission/b06/assets")
LOCAL_ASSETS = tuple(dict(record, canonical_path=record["path"],
                         path=str(LOCAL_ASSET_ROOT / f"S_L{lineage}.pt"))
                     for lineage, record in enumerate(CANONICAL_ASSETS))


def cell_name(arm, mode):
    return arm + "/" + mode


@dataclass(frozen=True)
class Protocol:
    worlds: tuple = tuple(range(29670000, 29670032))
    sampling_roots: tuple = (29670101, 29670102)
    actor_constructor_seeds: tuple = (29670111, 29670112)
    bootstrap_seed: int = 29670191
    bootstrap_resamples: int = 10000
    horizon: int = 256

    def validate(self):
        addresses = (*self.worlds, *self.sampling_roots, *self.actor_constructor_seeds, self.bootstrap_seed)
        if (not self.worlds or len(self.sampling_roots) != 2 or len(self.actor_constructor_seeds) != 2
                or any(type(x) is not int or x < 0 for x in addresses)
                or len(set(addresses)) != len(addresses) or type(self.horizon) is not int
                or self.horizon <= 0 or self.horizon % 4 or type(self.bootstrap_resamples) is not int
                or self.bootstrap_resamples <= 0):
            raise ValueError("invalid or overlapping B06 protocol")
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
        cells = [(arm, mode, tape) for arm, mode in CELLS
                 for tape in ((-1,) if arm == "C" else (0, 1))]
        offset = world_index % len(cells)
        return cells[offset:] + cells[:offset]

    def expected(self):
        w, h = len(self.worlds), self.horizon
        return dict(complete_episodes=w * 35, explicit_resets=w * 35, constructor_resets=1,
                    native_step_calls=w * 35 * h, native_steps=w * 35 * h,
                    event_gate_checks=w * 11 * (h - h // 4) * 5,
                    count_decodes=w * 11 * h * 5, fits=0, optimizer_updates=0, labels=0,
                    calibrations=0, training_native_steps=0)

    def query_bounds(self):
        bounds = dict(ordinary_queries=[0, 0], student_queries=[0, 0],
                      sampled_draws=[0, 0], score_tail_evaluations=[0, 0])
        for arm, mode, _ in self.episode_order(0):
            lo = self.horizon * 5 // (1 if mode == "H1" else 4)
            hi = lo * (2 if mode == "E" else 1)
            for key in ("ordinary_queries" if arm in ORDINARY_ARMS else "student_queries",
                        *(('sampled_draws',) if arm != "C" else ()),
                        *(('score_tail_evaluations',) if arm == "G" else ())):
                bounds[key][0] += lo * len(self.worlds)
                bounds[key][1] += hi * len(self.worlds)
        return bounds

    def check_counts(self, counts):
        exact, bounds = self.expected(), self.query_bounds()
        if set(counts) != set(exact) | set(bounds):
            raise AssertionError("B06 count schema differs")
        if any(type(v) is not int or v < 0 for v in counts.values()):
            raise AssertionError("B06 counts must be nonnegative integers")
        if any(counts[k] != v for k, v in exact.items()):
            raise AssertionError("B06 exact exposure differs")
        if any(not lo <= counts[k] <= hi for k, (lo, hi) in bounds.items()):
            raise AssertionError("B06 query exposure exceeds fixed bounds")


FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    found = inherited_sources(repo)
    own = repo / "experiments/candidates/uav_fleet_transmission/b06_cadence"
    for path in sorted(own.glob("*.py")):
        found[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found
