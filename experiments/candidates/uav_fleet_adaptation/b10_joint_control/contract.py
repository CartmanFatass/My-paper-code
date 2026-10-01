"""Fixed B10 scientific population, private addresses, comparisons and cost."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b02.contract import SOURCE_PINS, array_digest
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import CANONICAL_ASSETS


OBJECT = "UAV-JOINT-LOCAL-MOTION-TRANSMISSION-B10"
MASTER_SEED = 30013000
ENDPOINTS = ("J0", "J1")
JOINT = (*ENDPOINTS, "INIT90")
PROGRAMS = (*JOINT, "P0_A", "P0_ZERO", "P0_HIDDEN", "Bstar0_A", "Bstar0_ZERO",
            "Hdirect_A", "Hdirect_ZERO", "G_A", "G_ZERO", "C_A", "C_ZERO", "CJ")
DETERMINISTIC = ("C_A", "C_ZERO", "CJ")
CONTROLS = tuple(program for program in PROGRAMS if program not in ENDPOINTS)
CONTRASTS = tuple((endpoint, control) for endpoint in ENDPOINTS for control in CONTROLS) + tuple(
    (parent + "_ZERO", parent + "_A") for parent in ("P0", "Bstar0", "Hdirect", "G", "C")) + (
    ("INIT90", "P0_HIDDEN"),)
assert len(PROGRAMS) == 15 and len(CONTROLS) == 13 and len(set(CONTRASTS)) == 32

ASSET_BINDINGS = {
    "P0": dict(CANONICAL_ASSETS[0]),
    "HIDDEN": dict(path="/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b08_local_gate_a01/assets/HIDDEN.npz",
                   bytes=5119, sha256="e8f6ecea525d7892edc1e82c407070d14ea234dae3c90c6c054ce16804eaa026",
                   launch_sha="21de06cd2cd465d3962bbe95183bbfc7c3eddeb1"),
}


@dataclass(frozen=True)
class Protocol:
    training_worlds: tuple[tuple[int, ...], tuple[int, ...]] = (
        tuple(range(30010000, 30010256)), tuple(range(30011000, 30011256)))
    worlds: tuple[int, ...] = tuple(range(30012000, 30012032))
    training_motion_roots: tuple[int, int] = (30013011, 30013012)
    critic_seeds: tuple[int, int] = (30013021, 30013022)
    evaluation_motion_roots: tuple[int, int] = (30013031, 30013032)
    bootstrap_seed: int = 30013041
    constructor_seed: int = 30013051
    actor_constructor_seed: int = 30013061
    bootstrap_resamples: int = 20000
    horizon: int = 256
    period: int = 4
    n_agents: int = 5

    def validate(self):
        if self.n_agents != 5 or self.period != 4 or type(self.horizon) is not int or self.horizon <= 0 or self.horizon % 4:
            raise ValueError("N5 and complete four-tick episodes required")
        if len(self.training_worlds) != 2 or any(not w or len(w) % 2 for w in self.training_worlds) or not self.worlds:
            raise ValueError("two nonempty training blocks of complete episode pairs required")
        worlds = (*self.training_worlds[0], *self.training_worlds[1], *self.worlds)
        if any(type(w) is not int or w < 0 for w in worlds) or len(set(worlds)) != len(worlds):
            raise ValueError("training/final worlds must be distinct nonnegative integers")
        if any(len(values) != 2 for values in (self.training_motion_roots, self.critic_seeds, self.evaluation_motion_roots)):
            raise ValueError("two independent training/critic and two final motion domains required")
        roots = (*self.training_motion_roots, *self.critic_seeds, *self.evaluation_motion_roots,
                 self.bootstrap_seed, self.constructor_seed, self.actor_constructor_seed)
        if any(type(r) is not int or r < 0 for r in roots) or len(set(roots)) != len(roots) or set(roots) & set(worlds):
            raise ValueError("declared private randomness domains must be disjoint")
        if type(self.bootstrap_resamples) is not int or self.bootstrap_resamples <= 0:
            raise ValueError("positive fixed bootstrap count required")
        return self

    def episode_order(self, world_index):
        cells = tuple((program, tape) for program in PROGRAMS
                      for tape in ((None,) if program in DETERMINISTIC else (0, 1)))
        start = int(world_index) % len(cells)
        cells = cells[start:] + cells[:start]
        return cells if int(world_index) % 2 == 0 else cells[::-1]

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, values):
        values = dict(values)
        values["training_worlds"] = tuple(tuple(w) for w in values["training_worlds"])
        for key in ("worlds", "training_motion_roots", "critic_seeds", "evaluation_motion_roots"):
            values[key] = tuple(values[key])
        return cls(**values).validate()

    def expected(self):
        self.validate()
        d, w = self.horizon // 4, len(self.worlds)
        training = sum(map(len, self.training_worlds))
        final = w * 27
        total, groups = training + final, training // 2
        joint = (training + w * 6) * d * 5
        ordinary_neural = w * 14 * d * 5
        prior_rows = (training + w * 6) * d
        helpers = joint + w * 10 * d * 5
        full_c = w * 11 * d * 5
        scalar = total * (self.horizon + 1 + d)
        return dict(fits=2, training_episodes=training, evaluation_episodes=final, complete_episodes=total,
                    training_native_steps=training * self.horizon, evaluation_native_steps=final * self.horizon,
                    native_steps=total * self.horizon, native_uav_ticks=total * self.horizon * 5,
                    explicit_resets=total, constructor_resets=1,
                    native_dense_power_slots=275 * (total * (self.horizon + 1) + 1),
                    native_unique_distance_pairs=260 * (total * (self.horizon + 1) + 1),
                    mask_installs=total * d, mask_refresh_dense_sinr_slots=total * d * 275,
                    motion_requests=total * d * 5, gate_opportunities=total * d,
                    motion_draws=(training + w * 24) * d * 5, gate_draws=0,
                    collected_actor_rows=training * d * 5, collected_critic_rows=training * d,
                    actor_optimizer_steps=groups * 4, critic_optimizer_steps=groups * 4,
                    actor_replay_rows=training * d * 5 * 4, critic_replay_rows=training * d * 4,
                    density_identity_rows=training * d * 5, group_states=groups,
                    joint_collection_rows=joint, joint_forward_ceiling=joint,
                    frozen_forward_ceiling=ordinary_neural + prior_rows, helper_requests=helpers,
                    helper_link_ceiling=helpers * 140, C_family_requests=full_c,
                    C_path_ceiling=full_c * 27, C_model_tick_ceiling=full_c * 108,
                    C_link_ceiling=full_c * 2260, CJ_off_scores=w * d,
                    CJ_off_logical_ticks=w * d * 4, CJ_setup_link_ceiling=w * d * 100,
                    controller_link_ceiling=helpers * 140 + full_c * 2260 + w * d * 100,
                    Hdirect_target_vectors=w * 4 * d * 5 * 2, G_score_tail_calls=w * 4 * d * 5,
                    gate_prediction_rows=prior_rows + w * 2 * d,
                    reader_scalar_states=scalar, reader_local_rows=scalar * 5,
                    reader_scalar_power_links=scalar * 270, reader_distance_pairs=scalar * 260,
                    reader_dense_sinr_slots=scalar * 275, reader_critic_rows=training * d)


FROZEN = Protocol().validate()


def source_identities(repo):
    """Freeze every executed experiment dependency and original native source."""
    repo = Path(repo)
    records = {}
    for relative, expected in SOURCE_PINS.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("frozen host/helper source changed: " + relative)
        records[relative] = actual
    directories = ("uav_fleet_adaptation/b02", "uav_fleet_adaptation/b08_local_gate",
                   "uav_fleet_adaptation/b10_joint_control")
    paths = [path for directory in directories
             for path in (repo / "experiments/candidates" / directory).glob("*.py")]
    paths.extend(repo / path for path in (
        "envs/pettingzoo/uav_radio.py",
        "experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py",
        "experiments/candidates/uav_fleet_adaptation/b04_native_development/learning.py",
        "experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/targets.py",
        "experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py",
        "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py",
    ))
    for path in paths:
        records[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(records.items()))
