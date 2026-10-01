"""Frozen B09 exposure, identities, assignments and random addresses."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.contract import SOURCE_PINS, array_digest
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import CANONICAL_ASSETS

OBJECT = "UAV-MIXED-CONTROLLER-FOCAL-RESPONSE-B09"
MASTER_SEED = 29994000
ENDPOINTS = ("F0", "H0", "F1", "H1")
CONTROLS = ("C", "Q10", "G", "V", "R", "P0", "Bstar0", "Hdirect")
EGOS = ENDPOINTS + CONTROLS
PANELS = ("T", "X")
ROSTERS = {"T": ("C", "P0"), "X": ("G", "P1")}
SLOT_PAIRS = ((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))
ASSET_BINDINGS = dict(zip(("P0", "P1"), CANONICAL_ASSETS))
CONTRASTS = tuple((f"H{block}", f"F{block}", panel) for block in range(2) for panel in PANELS) + tuple(
    (ego, control, panel) for ego in ENDPOINTS for control in CONTROLS for panel in PANELS)
assert len(CONTRASTS) == 68 and len(set(CONTRASTS)) == 68


def assignment(root, world, tape, panel):
    """One uniform six-way draw; assignment never enters the actor context."""
    if panel not in PANELS or tape not in (0, 1):
        raise ValueError("undeclared assignment panel/tape")
    values = (root, world, tape)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("assignment requires nonnegative integer addresses")
    index = int(np.random.default_rng(np.random.SeedSequence(
        [root, world, tape, PANELS.index(panel)])).integers(0, 6))
    first, second = ROSTERS[panel]
    return index, tuple(first if i in SLOT_PAIRS[index] else second for i in range(1, 5))


@dataclass(frozen=True)
class Protocol:
    training_worlds: tuple[tuple[int, ...], ...] = (tuple(range(29991000, 29991256)), tuple(range(29992000, 29992256)))
    worlds: tuple[int, ...] = tuple(range(29993000, 29993032))
    actor_constructor_seed: int = 29994001
    critic_seeds: tuple[int, int] = (29994011, 29994012)
    training_roots: tuple[int, int] = (29994021, 29994022)
    evaluation_roots: tuple[int, ...] = (29994031, 29994032)
    training_assignment_roots: tuple[int, int] = (29994041, 29994042)
    evaluation_assignment_root: int = 29994051
    bootstrap_seed: int = 29994061
    constructor_seed: int = 29994071
    bootstrap_resamples: int = 20000
    horizon: int = 256
    period: int = 4
    n_agents: int = 5

    def validate(self):
        if self.n_agents != 5 or self.period != 4 or not 0 < self.horizon <= 256 or self.horizon % 4:
            raise ValueError("N5, original clock/256 and complete four-tick blocks required")
        if len(self.training_worlds) != 2 or any(not w or len(w) % 2 for w in self.training_worlds) or not self.worlds:
            raise ValueError("two independent blocks with two-episode groups required")
        worlds = [w for panel in (*self.training_worlds, self.worlds) for w in panel]
        if len(worlds) != len(set(worlds)) or any(type(w) is not int or w < 0 for w in worlds):
            raise ValueError("training/final worlds must be disjoint")
        domains = (self.critic_seeds, self.training_roots, self.training_assignment_roots)
        if any(len(domain) != 2 for domain in domains) or len(self.evaluation_roots) not in (1, 2):
            raise ValueError("fixed block domains and one/two fixture/final tapes required")
        seeds = [self.actor_constructor_seed, self.evaluation_assignment_root, self.bootstrap_seed, self.constructor_seed,
                 *self.critic_seeds, *self.training_roots, *self.evaluation_roots, *self.training_assignment_roots]
        if len(seeds) != len(set(seeds)) or any(type(s) is not int or s < 0 for s in seeds) or self.bootstrap_resamples <= 0:
            raise ValueError("separate random domains and positive resamples required")
        return self

    def fit_order(self):
        return ((0, "F"), (0, "H"), (1, "H"), (1, "F"))

    def episode_order(self, index):
        cells = tuple((ego, panel, tape) for ego in EGOS for panel in PANELS
                      for tape in range(len(self.evaluation_roots)))
        start = index % len(cells)
        cells = cells[start:] + cells[:start]
        return cells if index % 2 == 0 else cells[::-1]

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, values):
        values = dict(values)
        values["training_worlds"] = tuple(tuple(w) for w in values["training_worlds"])
        for key in ("worlds", "critic_seeds", "training_roots", "evaluation_roots", "training_assignment_roots"):
            values[key] = tuple(values[key])
        return cls(**values).validate()

    def expected(self):
        self.validate()
        clocks = self.horizon // 4
        train = 2 * sum(map(len, self.training_worlds))
        per_ego = len(self.worlds) * len(self.evaluation_roots) * 2
        final = per_ego * 12
        total = train + final
        # Each T episode has two C/two P0 peers; X two G/two P1 peers.
        neural = 3 * train * clocks + (2 * final + 7 * per_ego) * clocks
        helper = 3 * train * clocks + (2 * final + 6 * per_ego) * clocks
        ranking = 2 * train * clocks + (2 * final + 6 * per_ego) * clocks
        head = (train + 4 * per_ego) * clocks
        tracker_episodes = train // 2 + 4 * per_ego
        return dict(fits=4, training_episodes=train, evaluation_episodes=final, complete_episodes=total,
                    explicit_resets=total, native_steps=total * self.horizon,
                    training_native_steps=train * self.horizon, evaluation_native_steps=final * self.horizon,
                    native_uav_ticks=5 * total * self.horizon, motion_requests=5 * total * clocks,
                    motion_draws=(3 * train + 3 * final + 9 * per_ego) * clocks,
                    roster_draws=total, roster_unique_addresses=sum(map(len, self.training_worlds)) + per_ego,
                    collected_head_rows=head, collected_critic_rows=train * clocks,
                    head_optimizer_steps=train // 2 * 4, critic_optimizer_steps=train // 2 * 4,
                    head_replay_rows=train * clocks * 4, critic_replay_rows=train * clocks * 4,
                    density_identity_rows=train * clocks, group_states=train // 2,
                    frozen_forward_ceiling=neural, helper_request_ceiling=helper, C_ranking_ceiling=ranking,
                    C_path_ceiling=ranking * 27, C_modeled_tick_ceiling=ranking * 108,
                    C_link_ceiling=ranking * 2260, helper_link_ceiling=helper * 140,
                    motion_tracker_ingests=tracker_episodes * self.horizon,
                    motion_pair_gate_ceiling=tracker_episodes * (self.horizon - 1) * 16,
                    V_R_moving_link_ceiling=2 * per_ego * clocks * 4 * 4 * 20,
                    Hdirect_target_vectors=2 * per_ego * clocks,
                    G_score_tail_calls=(final + per_ego) * clocks,
                    reader_head_rows=head + 2 * per_ego * clocks, reader_critic_rows=train * clocks,
                    reader_scalar_states=total * (self.horizon + 1),
                    reader_local_rows=total * (self.horizon + 1) * 5,
                    reader_scalar_links=total * (self.horizon + 1) * 270,
                    native_dense_power_slots=total * (self.horizon + 1) * 275)


FROZEN = Protocol().validate()


def source_identities(repo):
    """Record all execution/reconstruction dependencies before scientific calls."""
    repo = Path(repo)
    records = {}
    for relative, expected in SOURCE_PINS.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("bound host/helper changed: " + relative)
        records[relative] = actual
    for folder in ("uav_fleet_adaptation/b02", "uav_fleet_adaptation/b04_native_development",
                   "uav_fleet_adaptation/b08_local_gate", "uav_fleet_adaptation/b09_focal_response",
                   "uav_local_peer_forecast"):
        for path in sorted((repo / "experiments/candidates" / folder).glob("*.py")):
            records[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in ("envs/pettingzoo/uav_radio.py", "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py",
                     "experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/targets.py",
                     "experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py"):
        records[relative] = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
    return records
