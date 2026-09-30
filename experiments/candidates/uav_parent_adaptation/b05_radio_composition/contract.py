"""The selected B05 panel, immutable dependencies and complete-work accounting."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time

from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.contract import ASSET, ASSET_PATH as ASSET_ORIGIN_PATH

OBJECT = "UAV-PARENT-RADIO-COMPOSITION-B05"
TAG = "b05_radio_composition_a01"
ASSET_PATH = Path("/home/fires/hmasd-wsl/temp/directions/uav_parent_adaptation/b05-original-S.pt")
ARMS = ("C_all", "Q_I_all", "S_I_all", "C_E", "Q_I_E", "S_I_E",
        "C_S2", "Q_I_S2", "S_I_S2", "C_T2")
WORKER_CPU_SECONDS = 7200.
READER_CPU_SECONDS = 3600.
PINS = {'envs/pettingzoo/env_adapter.py': '8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40',
 'envs/pettingzoo/uav_env.py': 'fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e',
 'envs/pettingzoo/uav_radio.py': 'db3464803b1a5aa9c9504096810dc971266a6bd7eba1c31dfe79e7d8d903f3cc',
 'experiments/candidates/uav_fleet_adaptation/b02/__init__.py': 'acb5ecf84dabf7c006af3c2658d6ee8ef587cf3338d15898df75011c4c0a0970',
 'experiments/candidates/uav_fleet_adaptation/b02/collect.py': '62a691a3d2b3e0579b84aca73b64fe61cdc11aee64ac2bd2d298db6ba59b44ef',
 'experiments/candidates/uav_fleet_adaptation/b02/contract.py': '4f312ecbbe653c1d00632be4cd2f1ea6d48f7f98ce50eb28cf405f06e9fbe1a3',
 'experiments/candidates/uav_fleet_adaptation/b02/controllers.py': 'a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522',
 'experiments/candidates/uav_fleet_adaptation/b02/model.py': 'c9b95b6718262c65591ed106ca81da0abb15b48ef6a8439438618365efc39934',
 'experiments/candidates/uav_fleet_adaptation/b02/policies.py': 'fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd',
 'experiments/candidates/uav_fleet_adaptation/b02/read.py': '6d07435ebeac57ace0a8696d69b1ff5f97cd4e3a15dc5f7486793ce6ba9ab336',
 'experiments/candidates/uav_fleet_adaptation/b02/reading.py': 'e70428557b90fb58fbe45ecdb832c1678328799b4382add92d47389a06e518a0',
 'experiments/candidates/uav_fleet_adaptation/b02/run.py': '7e84a11c2c7e15ada65f0f050917864b40adc1cbb5c62ded943d1d6109a0e7aa',
 'experiments/candidates/uav_fleet_adaptation/b02/study.py': 'ed564b337e3d3f80cc96e50ec7b72c92f910014a31678143d6fc85bb905bef4d',
 'experiments/candidates/uav_local_history/b01/controller.py': 'b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2',
 'experiments/candidates/uav_local_history/b01/study.py': '5fb3a1538a29bc5dd613a49fdd469d351876e8b070794171956a290651cdb8ec',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/__init__.py': 'a6f60a48a41ebee03a205e7a91c78621fdcf06ce40b72477eaf2c75f0e4dfaa5',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/collection.py': 'c7ad316dfbf7de90adc330c0befdcd8b11b313beb74b786cfa1a814b7d4b2bda',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/contract.py': '7e6884a4bac28cf9e91cabdccbef844c093ca72b2d7b99c7dcb69df7a5913fc0',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/read.py': 'a33b66013b85ce7e3bf757566c5e9304458e15e540ee8c54e336e46364aa3560',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/reading.py': 'fdcce95642c0fdb9d77d3e3a928adc2038fdadab1f450c16cfc8ffe2cb519308',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/run.py': 'c69727cb94e585dcdee2d13edddde95a9dd0037af87eec22c7fb5cb3138afbca',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/sampling.py': '0c4319269711627670a76ca0f020dafd5672b411b0c015df68f45116eb78f9a5',
 'experiments/candidates/uav_parent_adaptation/b04_joint_sampling/study.py': '7a5c11b8e8897a8991cba62c2bb96fb8727aadafa3319eb3d1d293a3d5f9e89a',
 'experiments/candidates/uav_radio_activation/b01/protocol.py': '4976e6739d1e5c919bd298b86091dcf6cf5d62d5c3cc3a7b977fa5b5f0956431',
 'experiments/candidates/uav_radio_activation/b01/read.py': '8d9f8d469335d2ac2c7551dd81217b9194c81c6a92d44725b202078c4a7b1347',
 'experiments/candidates/uav_radio_activation/b01/scheduler.py': '2b75232b9b57464b31a113458e9bab6b5c47b00272cf4d255dd670914b05e792',
 'experiments/candidates/uav_radio_activation/b01/study.py': '7af060ca82f357722e76588669e7319b10da7254f317bc312f71d25eca14aa24',
 'experiments/candidates/uav_radio_activation/b02/protocol.py': 'a1dbec8e5aecead2c702fab54376c95c8b9d1fd134cb0894a3c0eb705ebab69b',
 'experiments/candidates/uav_radio_activation/b02/scheduler.py': '5c748f097a7597806f0adb3e5b49a242f000391c7da9ab7eedb2f7efce7535e7',
 'experiments/candidates/uav_radio_activation/b03/protocol.py': '3561dd0c2ea274a7e24e5a8bc6da3d6ee03b21fcec8768d18adb45b4f524b2c1',
 'experiments/candidates/uav_radio_activation/b03/scheduler.py': '41cdda90f1bb677c16f1ca12ee57cef2ac656b9b597a146cf8b4e6be9039d54f',
 'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py': 'fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6'}


def arm_parts(arm):
    if arm not in ARMS:
        raise ValueError("unknown selected B05 program")
    return arm.rsplit("_", 1)


@dataclass(frozen=True)
class Protocol:
    worlds: tuple[int, ...] = tuple(range(29347000, 29347032))
    tapes: tuple[int, ...] = (0, 1)
    public_root: int = 29347091
    departure_root: int = 29347092
    tail_root: int = 29347093
    horizon: int = 256
    n_agents: int = 5
    period: int = 4
    grid_bits: int = 53

    def validate(self):
        if (not self.worlds or len(set(self.worlds)) != len(self.worlds)
                or any(type(w) is not int or w < 0 for w in self.worlds)):
            raise ValueError("unique nonnegative integer worlds required")
        if (self.tapes != (0, 1) or self.n_agents != 5 or self.period != 4 or self.grid_bits != 53
                or type(self.horizon) is not int or not 8 <= self.horizon <= 256 or self.horizon % 4):
            raise ValueError("fixed local/tape law and complete four-tick horizon required")
        roots = (self.public_root, self.departure_root, self.tail_root)
        if any(type(r) is not int or r < 0 for r in roots) or len(set(roots)) != 3:
            raise ValueError("three distinct nonnegative integer stream roots required")
        return self

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        value["worlds"], value["tapes"] = tuple(value["worlds"]), tuple(value["tapes"])
        return cls(**value).validate()

    def schedule(self):
        order = tuple((arm, tape) for arm in ARMS
                      for tape in ((-1,) if arm_parts(arm)[0] == "C" else self.tapes))
        for index, world in enumerate(self.worlds):
            shift = index % len(order)
            rotated = order[shift:] + order[:shift]
            for arm, tape in (rotated[::-1] if index % 2 else rotated):
                yield arm, world, tape

    def expected(self):
        self.validate()
        worlds, h = len(self.worlds), self.horizon
        d = h // 4
        episodes, e_episodes, s2_episodes, t2_episodes = worlds * 16, worlds * 5, worlds * 5, worlds
        c_requests, s_requests = worlds * 10 * d * 5, worlds * 6 * d * 5
        e_states, joint_states = 4 * d - 1, 4 * d - 2
        managed_rounds = worlds * 11 * d
        native_observation_checks = episodes * (h + d + 1)
        return dict(fits=0, expert_labels=0, optimizer_steps=0,
                    complete_episodes=episodes, native_steps=episodes * h,
                    constructor_resets=1, explicit_resets=episodes,
                    policy_blocks=episodes * d, controller_requests=episodes * d * 5,
                    c_requests=c_requests, s_requests=s_requests,
                    c_candidate_paths_ceiling=c_requests * 27,
                    c_model_ticks_ceiling=c_requests * 108,
                    c_candidate_power_ceiling=c_requests * 108 * 20,
                    c_setup_power_ceiling=c_requests * 100,
                    s_forward_rows_ceiling=s_requests, s_helper_calls_ceiling=s_requests,
                    s_helper_setup_power_ceiling=s_requests * 100,
                    s_helper_extreme_power_ceiling=s_requests * 40,
                    sampling_decisions=worlds * 12 * d * 5,
                    private_integer_reads=worlds * 12 * d * 5 * 2,
                    unique_tape_bundles=worlds * 2, unique_tape_integers=worlds * 2 * d * 11,
                    unique_tape_bytes=worlds * 2 * d * 11 * 8,
                    coordinator_rounds=managed_rounds,
                    e_candidate_requests_ceiling=e_episodes * d * 31,
                    e_state_reductions_ceiling=e_episodes * e_states * 31,
                    e_geometry_ceiling=e_episodes * e_states,
                    s2_candidate_requests_ceiling=s2_episodes * d * 116,
                    s2_candidate_plans_ceiling=s2_episodes * d * 112,
                    s2_state_reductions_ceiling=s2_episodes * joint_states * 112,
                    s2_geometry_ceiling=s2_episodes * joint_states * 27,
                    t2_candidate_requests_ceiling=t2_episodes * d * 837,
                    t2_state_reductions_ceiling=t2_episodes * joint_states * 837,
                    t2_geometry_ceiling=t2_episodes * joint_states * 27,
                    joint_prefix_ticks_ceiling=(s2_episodes + t2_episodes) * d * 2,
                    recurring_bytes_ceiling=managed_rounds * 136,
                    map_bytes_provisioned=worlds * 11 * 400,
                    map_bytes_unique=worlds * 400,
                    reader_s_forward_rows=s_requests, reader_s_helper_calls=s_requests,
                    reader_c_ranking_queries=0,
                    reader_candidate_state_reductions_ceiling=(e_episodes * e_states * 31
                                                               + (s2_episodes + t2_episodes) * joint_states * 5),
                    reader_native_observation_formula_checks=native_observation_checks,
                    reader_native_steps=0)


FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    result = {}
    for relative, expected in PINS.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("immutable B04/radio source drift: " + relative)
        result[relative] = actual
    for path in sorted(Path(__file__).parent.glob("*.py")):
        result[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def new_counts():
    return dict(fits=0, expert_labels=0, optimizer_steps=0, constructor_calls=0,
                constructors=0, constructor_resets=0, explicit_reset_calls=0, explicit_resets=0,
                native_step_calls=0, native_steps=0, complete_episodes=0,
                policy_block_calls=0, policy_blocks=0, sampling_decisions=0,
                private_integer_reads=0, coordinator_round_calls=0, coordinator_round_returns=0,
                mask_setter_calls=0, mask_setter_returns=0)


def validate_counts(batch):
    a, e = batch["actual"], batch["expected"]
    for key in ("fits", "expert_labels", "optimizer_steps", "complete_episodes", "native_steps",
                "constructor_resets", "explicit_resets", "sampling_decisions", "private_integer_reads"):
        if a[key] != e[key]:
            raise AssertionError("complete B05 exposure mismatch: " + key)
    checks = {"constructor_calls": 1, "constructors": 1,
              "explicit_reset_calls": e["explicit_resets"], "native_step_calls": e["native_steps"],
              "policy_block_calls": e["policy_blocks"], "policy_blocks": e["policy_blocks"],
              "coordinator_round_calls": e["coordinator_rounds"],
              "coordinator_round_returns": e["coordinator_rounds"],
              "mask_setter_calls": e["coordinator_rounds"], "mask_setter_returns": e["coordinator_rounds"]}
    if any(a[k] != v for k, v in checks.items()):
        raise AssertionError("attempt/completion/reset/refresh count mismatch")
    costs = batch["costs"]
    if costs["C"]["requests"] != e["c_requests"] or costs["S"]["requests"] != e["s_requests"]:
        raise AssertionError("local request exposure mismatch")
    if (costs["S"].get("sampled_draws", 0) != 0
            or costs["S"]["neural_rows"] > e["s_forward_rows_ceiling"]
            or costs["S"]["helper_calls"] > e["s_helper_calls_ceiling"]
            or costs["C"]["model_ticks"] > e["c_model_ticks_ceiling"]):
        raise AssertionError("undeclared local sampling/model work")
    for coordinator in ("E", "S2", "T2"):
        for counter, bound in (("candidate_requests", "candidate_requests"),
                               ("candidate_request_upper", "candidate_requests"),
                               ("state_reductions", "state_reductions"),
                               ("geometry_snapshots", "geometry")):
            if costs[coordinator][counter] > e[coordinator.lower() + "_" + bound + "_ceiling"]:
                raise AssertionError("coordinator work exceeds selected ceiling")


class CpuBudget:
    """Check between bounded calls; preserve partial evidence on expiry."""
    def __init__(self, seconds, *, started=None, clock=time.process_time):
        self.clock, self.started = clock, clock() if started is None else started
        self.seconds = float(seconds)

    def check(self):
        if self.clock() - self.started >= self.seconds:
            raise RuntimeError("selected CPU envelope exhausted; retain incomplete work, no retry")
