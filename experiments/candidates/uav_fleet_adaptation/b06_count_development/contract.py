"""B06 fixed population, acquisition, random-address and accounting contract."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b02.contract import (
    SOURCE_PINS, array_digest,
)
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import CANONICAL_ASSETS


OBJECT = "UAV-STATIC-COUNT-DEVELOPMENT-B06"
MASTER_SEED = 29514000
COUNTS = (3, 4, 5, 6, 7)
FINAL_COUNTS = (4, 5, 6)
FITS = ("F", "M")
DECODER = "one-row-fp32-numpy-fp64-private-inverse-cdf-v1"
INITIAL_ASSETS = tuple({
    **record,
    "canonical_path": record["path"], "canonical_node": "wsl_4070",
} for record in CANONICAL_ASSETS)
CALIBRATION_SOURCE = {
    "launch_sha": "98307b0c5cb6e42763458d780568d105d3f631af",
    "evidence_commit": "978c622c37207067dd673247cf6729d786383304",
    "reading_path": "runs/uav_fleet_adaptation/b04_native_development_a01/reading.json",
    "reading_sha256": "93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50",
    "winners": ["S_T2", "S_T1"], "new_calibrations": 0,
}


@dataclass(frozen=True)
class Protocol:
    acquisition_worlds: tuple = (tuple(range(29510000, 29510256)), tuple(range(29512000, 29512256)))
    evaluation_worlds: tuple = tuple(range(29515000, 29515032))
    phase_episodes: tuple = (128, 64, 64)
    layout_root: int = 29514001
    evaluation_roots: tuple = (29514011, 29514012)
    shuffle_roots: tuple = (29514101, 29514102)
    actor_constructor_seeds: tuple = (29514201, 29514202)
    environment_constructor_seeds: tuple = tuple(range(29514303, 29514308))
    fixture_world: int = 29519000
    fixture_horizon: int = 8
    horizon: int = 256
    period: int = 4
    epochs: tuple = (30, 20, 20)
    batch_size: int = 512
    learning_rate: float = 3e-4
    grad_norm: float = 1.0

    def validate(self):
        if (self.horizon != 256 or self.period != 4 or self.fixture_horizon != 8
                or self.phase_episodes != (128, 64, 64) or self.epochs != (30, 20, 20)
                or self.batch_size != 512 or self.learning_rate != 3e-4 or self.grad_norm != 1.):
            raise ValueError("B06 exposure/optimizer contract changed")
        if (len(self.acquisition_worlds) != 2 or any(len(p) != 256 for p in self.acquisition_worlds)
                or len(self.evaluation_worlds) != 32):
            raise ValueError("two fixed acquisition lineages and 32 shared final worlds required")
        worlds = [*self.acquisition_worlds[0], *self.acquisition_worlds[1],
                  *self.evaluation_worlds, self.fixture_world]
        roots = [self.layout_root, *self.evaluation_roots, *self.shuffle_roots,
                 *self.actor_constructor_seeds, *self.environment_constructor_seeds]
        if (len(set(worlds + roots)) != len(worlds + roots)
                or any(type(v) is not int or v < 0 for v in worlds + roots)
                or any(len(v) != 2 for v in (self.evaluation_roots, self.shuffle_roots,
                                            self.actor_constructor_seeds))
                or len(self.environment_constructor_seeds) != 5):
            raise ValueError("invalid or overlapping B06 randomness domains")
        return self

    def phase_worlds(self, lineage, phase):
        if lineage not in (0, 1) or phase not in (0, 1, 2):
            raise ValueError("invalid lineage/phase")
        first = sum(self.phase_episodes[:phase])
        return self.acquisition_worlds[lineage][first:first + self.phase_episodes[phase]]

    def acquisition_count(self, arm, index):
        if arm not in FITS or type(index) is not int or index < 0:
            raise ValueError("invalid acquisition arm/index")
        return 5 if arm == "F" else (3 if index % 2 == 0 else 7)

    def expected(self):
        self.validate()
        return dict(
            fits=4, acquisition_episodes=1024, evaluation_episodes=1632, complete_episodes=2656,
            acquisition_native_steps=262144, evaluation_native_steps=417792,
            study_native_steps=679936, fixture_trajectories=5, fixture_native_steps=40,
            native_steps=679976, native_uav_ticks=3399880, expert_labels=327680,
            phase_labels=[40960, 20480, 20480], datasets=[40960, 61440, 81920],
            phase_updates=[2400, 2400, 3200], optimizer_steps=32000,
            sample_presentations=16384000, student_requests=593920,
            full_C_requests=419890, helper_request_ceiling=757810,
            C_path_ceiling=11337030, C_model_tick_ceiling=45348120,
            reader_student_rows=430080, reader_C_requests=80, reader_helper_requests=80,
            reader_C_paths=2160, reader_C_model_ticks=8640,
            constructor_resets=5, explicit_resets=2661, layout_refreshes=2661,
            native_dense_slots=189267523, worker_power_slot_ceiling=1250948643,
            reader_power_slot_ceiling=192000, new_calibrations=0,
        )

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        value["acquisition_worlds"] = tuple(tuple(v) for v in value["acquisition_worlds"])
        for key in ("evaluation_worlds", "phase_episodes", "evaluation_roots", "shuffle_roots",
                    "actor_constructor_seeds", "environment_constructor_seeds", "epochs"):
            value[key] = tuple(value[key])
        return cls(**value).validate()


FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    identities = {}
    for relative, expected in SOURCE_PINS.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"bound teacher/host source changed: {relative}")
        identities[relative] = actual
    directories = ("b02", "b06_count_development")
    paths = [p for directory in directories for p in sorted(
        (repo / "experiments/candidates/uav_fleet_adaptation" / directory).glob("*.py"))]
    paths += [repo / "experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py"]
    for path in paths:
        identities[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return identities


def new_counts():
    return {name: 0 for name in (
        "fits_started", "fits_completed", "optimizer_steps", "sample_presentations",
        "constructor_calls", "constructors", "constructor_resets", "explicit_reset_calls",
        "explicit_resets", "layout_refresh_calls", "layout_refreshes", "native_step_calls",
        "native_steps", "native_uav_ticks", "native_dense_slots", "acquisition_native_steps",
        "evaluation_native_steps", "fixture_native_steps", "acquisition_episodes",
        "evaluation_episodes", "complete_episodes", "fixture_trajectories", "expert_labels",
        "new_calibrations",
    )}
