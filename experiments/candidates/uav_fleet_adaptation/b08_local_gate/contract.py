"""Prospectively fixed B08 population, private randomness and complete exposure."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.contract import SOURCE_PINS, array_digest
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import CANONICAL_ASSETS


OBJECT = "UAV-LOCAL-TRANSMITTER-GATE-B08"
MASTER_SEED = 29832000
PARENTS = ("P0", "Bstar0", "Hdirect", "G", "Q10", "C")
NEURAL = ("P0", "Bstar0", "Hdirect")
HELPER_PARENTS = ("P0", "Bstar0")
FITTED = ("RAW", "HIDDEN")
GATES = ("A", "O", "R", "ZERO", *FITTED)
PROGRAMS = tuple("P0_" + gate for gate in GATES) + tuple(
    parent + "_" + gate for parent in PARENTS[1:] for gate in ("A", "ZERO"))
UNFITTED = tuple(program for program in PROGRAMS if program not in ("P0_RAW", "P0_HIDDEN"))
CONTRASTS = (("P0_HIDDEN", "P0_RAW"),) + tuple(
    ("P0_" + gate, other) for gate in FITTED for other in UNFITTED) + tuple(
    (parent + "_ZERO", parent + "_A") for parent in PARENTS) + (
    ("P0_O", "P0_A"), ("P0_R", "P0_A"))
assert len(PROGRAMS) == 16 and len(set(CONTRASTS)) == 37
P0_BINDING = dict(CANONICAL_ASSETS[0])


@dataclass(frozen=True)
class Protocol:
    training_worlds: tuple[int, ...] = tuple(range(29830000, 29830512))
    worlds: tuple[int, ...] = tuple(range(29831000, 29831032))
    training_motion_root: int = 29832011
    evaluation_motion_roots: tuple[int, int] = (29832021, 29832022)
    training_gate_root: int = 29832031
    evaluation_gate_roots: tuple[int, int] = (29832041, 29832042)
    bootstrap_seed: int = 29832051
    constructor_seed: int = 29832061
    bootstrap_resamples: int = 20000
    horizon: int = 256
    period: int = 4
    n_agents: int = 5

    def validate(self):
        if self.n_agents != 5 or self.period != 4 or self.horizon <= 0 or self.horizon % 4:
            raise ValueError("N5 and complete four-tick blocks are required")
        worlds = (*self.training_worlds, *self.worlds)
        if (not self.training_worlds or not self.worlds or len(worlds) != len(set(worlds))
                or any(type(w) is not int or w < 0 for w in worlds)
                or len(self.training_worlds) % (self.horizon // 4)):
            raise ValueError("disjoint nonempty worlds and balanced force clocks required")
        roots = (self.training_motion_root, *self.evaluation_motion_roots, self.training_gate_root,
                 *self.evaluation_gate_roots, self.bootstrap_seed, self.constructor_seed)
        if (len(self.evaluation_motion_roots) != 2 or len(self.evaluation_gate_roots) != 2
                or len(roots) != len(set(roots)) or any(type(r) is not int or r < 0 for r in roots)
                or self.bootstrap_resamples <= 0):
            raise ValueError("distinct declared private domains and descriptive resamples required")
        return self

    def force_tick(self, index):
        if not 0 <= index < len(self.training_worlds):
            raise ValueError("training index outside frozen panel")
        return 4 * (index % (self.horizon // 4))

    def branches(self, index):
        return ("OFF", "ON") if index % 2 == 0 else ("ON", "OFF")

    def episode_order(self, world_index):
        cells = tuple((program, tape) for program in PROGRAMS
                      for tape in ((None,) if program.startswith("C_") else (0, 1)))
        start = world_index % len(cells)
        cells = cells[start:] + cells[:start]
        return cells if world_index % 2 == 0 else cells[::-1]

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, values):
        values = dict(values)
        for name in ("training_worlds", "worlds", "evaluation_motion_roots", "evaluation_gate_roots"):
            values[name] = tuple(values[name])
        return cls(**values).validate()

    def expected(self):
        self.validate()
        clocks = self.horizon // self.period
        acquisition = 2 * len(self.training_worlds)
        final = len(self.worlds) * 30
        episodes = acquisition + final
        neural_episodes = acquisition + len(self.worlds) * 20
        helper_episodes = acquisition + len(self.worlds) * 16
        c_episodes = len(self.worlds) * 14
        return dict(fits=2, optimizer_steps=0, motion_updates=0, paired_targets=len(self.training_worlds),
                    acquisition_episodes=acquisition, evaluation_episodes=final, complete_episodes=episodes,
                    acquisition_native_steps=acquisition * self.horizon,
                    evaluation_native_steps=final * self.horizon, native_steps=episodes * self.horizon,
                    native_uav_ticks=episodes * self.horizon * 5, explicit_resets=episodes,
                    constructor_resets=1, native_dense_power_slots=275 * (episodes * (self.horizon + 1) + 1),
                    mask_installs=episodes * clocks, mask_refresh_dense_sinr_slots=275 * episodes * clocks,
                    motion_requests=episodes * clocks * 5, gate_opportunities=episodes * clocks,
                    neural_forward_ceiling=neural_episodes * clocks * 5,
                    standalone_helper_requests=helper_episodes * clocks * 5,
                    C_family_requests=c_episodes * clocks * 5,
                    C_path_ceiling=c_episodes * clocks * 5 * 27,
                    C_model_tick_ceiling=c_episodes * clocks * 5 * 27 * 4,
                    helper_link_ceiling=helper_episodes * clocks * 5 * 140,
                    C_link_ceiling=c_episodes * clocks * 5 * 2260,
                    motion_draws=(episodes - len(self.worlds) * 2) * clocks * 5,
                    gate_draws=(acquisition + len(self.worlds) * 2) * clocks,
                    Hdirect_law_calls=len(self.worlds) * 4 * clocks * 5,
                    Hdirect_target_vectors=len(self.worlds) * 4 * clocks * 5 * 2,
                    G_score_tail_calls=len(self.worlds) * 4 * clocks * 5)


FROZEN = Protocol().validate()


def gate_uniform(root, world, tick, agent):
    if type(tick) is not int or tick < 0 or tick % 4 or type(agent) is not int or agent != (tick // 4) % 5:
        raise ValueError("gate address must name the rotating eligible member")
    return float(np.random.default_rng(np.random.SeedSequence(
        [int(root), int(world), int(tick), int(agent)])).random())


def source_identities(repo):
    """Bind reused dependencies as well as all new executable inputs."""
    repo = Path(repo)
    records = {}
    for relative, expected in SOURCE_PINS.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("frozen host/helper changed: " + relative)
        records[relative] = actual
    extra = (
        "envs/pettingzoo/uav_radio.py",
        "experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py",
        "experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/targets.py",
        "experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py",
    )
    paths = [repo / relative for relative in extra]
    for folder in ("b02", "b08_local_gate"):
        paths.extend(sorted((repo / "experiments/candidates/uav_fleet_adaptation" / folder).glob("*.py")))
    for path in paths:
        records[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return records
