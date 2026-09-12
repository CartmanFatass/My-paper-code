"""Fixed C/H/G native-renewal observation; see the A01 card and CM spec."""
import time

PROCESS_START = time.perf_counter()  # Before numerical/host/checkpoint imports.

import argparse
import copy
import json
import random
import sys
from contextlib import nullcontext
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from envs.relay_corridor.adapter import RelayCorridorAdapter
from envs.relay_corridor.config import RelayCorridorConfig
from envs.relay_corridor.references import GreedyOnPublicState

OBJECT_ID = "FSD_NATIVE_RENEWAL_CONTROL_A01"
CAP_SECONDS = 180.0
MODULES = (
    "skill_coordinator", "ha_ctse_editor", "low_level_compact_extractor",
    "process_encoder", "process_outcome_predictor", "process_contrastive_head",
    "skill_discoverer", "team_discriminator", "individual_discriminator",
)
COUNT_KEYS = (
    "completed_episodes", "scoring_steps", "agent_observations", "agent_step_batches",
    "greedy_act_batches", "model_constructions", "checkpoint_loads", "training_starts",
    "training_transitions", "optimizer_steps",
)
CHECKPOINT_SHA256 = "2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89"


def check_deadline(start):
    if time.perf_counter() - start > CAP_SECONDS:
        raise TimeoutError("complete-policy 180 s deadline exceeded")


def apply_renew_mask(policy, internal_mask, public_flag, t):
    if policy not in ("C", "H"):
        raise ValueError("applied controller mask requires C or H")
    return np.array(public_flag if policy == "H" and t > 0 else internal_mask,
                    dtype=bool, copy=True)


def load_controller(checkpoint_path, out, lanes, start, counts):
    """Restore only the active fixed-policy state, never the training/resume path."""
    check_deadline(start)
    import torch
    from run_flexible_skill_duration_e2 import E2CorridorConfig
    from hmasd.agent import HMASDAgent

    # E2 executed as a script can have pickled this real class under __main__.
    sys.modules["__main__"].E2CorridorConfig = E2CorridorConfig
    torch.set_num_threads(4)
    check_deadline(start)
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    counts["checkpoint_loads"] += 1
    check_deadline(start)
    config = copy.deepcopy(payload["config"])
    config.num_envs = lanes
    if config.use_obsnorm or config.use_statenorm:
        raise ValueError("selected policy requires disabled observation/state normalization")
    random.seed(2)
    np.random.seed(2)
    torch.manual_seed(2)
    counts["model_constructions"] += 1
    agent = HMASDAgent(config, device=torch.device("cpu"), log_dir=str(out / "agent"))
    check_deadline(start)
    restored = []
    for name in MODULES:
        module = getattr(agent, name)
        if module is not None:
            module.load_state_dict(payload[name], strict=True)
            restored.append(name)
            check_deadline(start)
    statistics = {}
    if config.use_valuenorm:
        for name in ("coordinator", "discoverer"):
            norm = getattr(agent, "value_norm_" + name)
            if norm is None:
                raise ValueError(f"enabled ValueNorm {name} is missing")
            saved = payload["valuenorm_state"][name]
            statistics[name] = {}
            for field in ("mean", "var", "count"):
                value = saved[field]
                if np.shape(value) != np.shape(getattr(norm, field)):
                    raise ValueError(f"ValueNorm {name}.{field} shape mismatch")
                if not np.all(np.isfinite(value)):
                    raise ValueError(f"ValueNorm {name}.{field} is nonfinite")
                setattr(norm, field, copy.deepcopy(value))
                statistics[name][field] = {
                    "value": np.asarray(value).tolist(), "dtype": str(np.asarray(value).dtype),
                }
    agent.train(False)
    check_deadline(start)
    return agent, {
        "use_obsnorm": config.use_obsnorm, "use_statenorm": config.use_statenorm,
        "use_valuenorm": config.use_valuenorm, "valuenorm_state": statistics,
        "restored_modules": restored,
    }


class FixtureController:
    """The specified stateful engineering fake; no learned model or checkpoint."""
    def __init__(self, adapter):
        self.calls = np.zeros(adapter.num_envs, dtype=int)
        self.age_slice = adapter.host.obs_slices["segment_age"]

    def train(self, mode):
        assert mode is False

    def clear_buffers(self):
        pass

    def reset_env_state(self, lane):
        self.calls[lane] = 0

    def step(self, states, observations, env_steps, dones, **kwargs):
        roles = (observations[:, :, self.age_slice].squeeze(-1) >= .5).astype(int)
        renew = np.broadcast_to(np.isin(self.calls, (0, 2))[:, None], roles.shape).copy()
        self.calls += 1
        return np.eye(2, dtype=np.float32)[roles], None, {"d2_sampled_mask": renew}


def base_summary(policy, config, lanes, seed, launch_sha, fixture):
    return {
        "object_id": OBJECT_ID, "mode": "engineering_fixture" if fixture else "checkpoint_observation",
        "policy": policy, "launch_sha": launch_sha, "master_seed": seed,
        "episode_ids": list(range(lanes)),
        "host": json.loads(json.dumps(config.parameter_record())),
        "counts": dict.fromkeys(COUNT_KEYS, 0), "checkpoint": None, "normalization": None,
        "controller_seed": None, "device": None, "torch_threads": None,
        "status": "incomplete", "failure": None, "wall_seconds_before_publication": None,
    }


def evaluate(policy, adapter, controller, summary, start, fixture=False):
    """One fresh batch, with each next input supplied by this policy's adapter."""
    lanes, n, horizon = adapter.num_envs, adapter.n_agents, adapter.config.horizon
    sums = {key: np.zeros((2, lanes), dtype=np.float64 if key == "return" else np.int64)
            for key in ("return", "eligible", "wrong", "internal_renew", "applied_renew")}
    steps_done = 0
    context = nullcontext()
    if policy != "G" and not fixture:
        import torch
        context = torch.no_grad()
    try:
        check_deadline(start)
        observations, info = adapter.reset()
        observations = np.asarray(observations, dtype=np.float32)
        states = np.asarray(info["state"], dtype=np.float64)
        env_steps = np.zeros(lanes, dtype=int)
        dones = np.zeros(lanes, dtype=bool)
        if policy == "G":
            controller.reset(adapter.host)
        else:
            controller.train(False)
            controller.clear_buffers()
            for lane in range(lanes):
                controller.reset_env_state(lane)
        with context:
            for t in range(horizon):
                check_deadline(start)
                if policy == "G":
                    roles, applied = controller.act(adapter.host, t)
                    summary["counts"]["greedy_act_batches"] += 1
                    actions = np.eye(adapter.config.n_roles, dtype=np.float32)[roles]
                    internal = None
                else:
                    actions, _, step_data = controller.step(
                        states, observations, env_steps, dones, deterministic=True,
                        return_step_data=True, build_infos=False)
                    summary["counts"]["agent_step_batches"] += 1
                    internal = np.array(step_data["d2_sampled_mask"], dtype=bool, copy=True)
                    flag = adapter.host.change_flag[:, adapter.host.region_of_agent].astype(bool)
                    applied = apply_renew_mask(policy, internal, flag, t)
                next_obs, _, term, trunc, step_info = adapter.step(actions, renew_mask=applied)
                steps_done += 1
                summary["counts"]["scoring_steps"] += lanes
                summary["counts"]["agent_observations"] += lanes * n
                if steps_done == horizon:
                    summary["counts"]["completed_episodes"] = lanes
                renew = np.asarray(step_info["renew_mask"], dtype=bool)
                eligible = (~renew) & np.asarray(step_info["lease_fresh"], dtype=bool)
                wrong = eligible & ~np.asarray(step_info["role_correct"], dtype=bool)
                values = {"return": np.asarray(step_info["shared_reward"], dtype=np.float64),
                          "eligible": eligible.sum(1), "wrong": wrong.sum(1),
                          "applied_renew": renew.sum(1)}
                if internal is not None:
                    values["internal_renew"] = internal.sum(1)
                for key, value in values.items():
                    sums[key][0] += value
                    if t > 0:
                        sums[key][1] += value
                observations = np.asarray(next_obs, dtype=np.float32)
                states = np.asarray(step_info["state"], dtype=np.float64)
                env_steps += 1
                dones = np.broadcast_to(np.asarray(term) | np.asarray(trunc), (lanes,)).copy()
                check_deadline(start)
        summary["status"] = "complete"
    finally:
        # Partial sums remain visible with actual counts, never relabelled complete.
        for index, (suffix, denominator) in enumerate((("full", horizon), ("post", horizon - 1))):
            for key, value in sums.items():
                array = value[index]
                summary[key + "_" + suffix] = (
                    None if policy == "G" and key == "internal_renew" else
                    (array / denominator).tolist() if key == "return" else array.tolist())
            wrong, eligible = sums["wrong"][index], sums["eligible"][index]
            summary["role_loss_" + suffix] = (adapter.config.delta * wrong / (denominator * n)).tolist()
            summary["wrong_rate_" + suffix] = [float(w / e) if e else None
                                                 for w, e in zip(wrong, eligible)]


def summarize_panel(policies):
    if set(policies) != {"G", "C", "H"}:
        raise ValueError("panel requires G, C, H")
    reference = policies["G"]
    for policy, summary in policies.items():
        for key in ("object_id", "mode", "launch_sha", "master_seed", "episode_ids", "host"):
            if summary[key] != reference[key]:
                raise ValueError(f"panel mismatch: {key}")
        lanes, horizon, n = len(summary["episode_ids"]), summary["host"]["H"], summary["host"]["N"]
        if summary["policy"] != policy or summary["status"] != "complete":
            raise ValueError("panel needs correctly labelled completed policies")
        for key, expected in (("completed_episodes", lanes), ("scoring_steps", lanes * horizon),
                              ("agent_observations", lanes * horizon * n)):
            if summary["counts"][key] != expected:
                raise ValueError(f"panel incomplete count: {key}")
        for suffix in ("full", "post"):
            values = np.asarray(summary["return_" + suffix], dtype=np.float64)
            if values.shape != (lanes,) or not np.isfinite(values).all():
                raise ValueError("panel return rows are missing or nonfinite")
    paired = {}
    for a, b, name in (("H", "C", "h_minus_c"), ("G", "H", "g_minus_h")):
        for suffix in ("full", "post"):
            differences = np.asarray(policies[a]["return_" + suffix]) - np.asarray(policies[b]["return_" + suffix])
            paired[name + "_" + suffix] = {
                "differences": differences.tolist(), "mean": float(differences.mean()),
                "stderr": float(differences.std(ddof=1) / np.sqrt(len(differences))),
            }
    return {"policies": policies, "paired": paired,
            "counts": {key: sum(s["counts"][key] for s in policies.values()) for key in COUNT_KEYS}}


def write_summary(out, summary):
    with (out / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main(argv=None):
    start = PROCESS_START
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=("G", "C", "H"))
    parser.add_argument("--seed", type=int, required=True, choices=(770103,))
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--panel-inputs", type=Path, nargs=2)
    parser.add_argument("--engineering-fixture", action="store_true")
    args = parser.parse_args(argv)
    if args.engineering_fixture:
        if args.checkpoint or args.policy or args.panel_inputs or args.launch_sha != "ENGINEERING_FIXTURE":
            parser.error("fixture uses ENGINEERING_FIXTURE and no policy/checkpoint/panel inputs")
    elif not args.policy or (args.policy in ("C", "H") and not args.checkpoint):
        parser.error("production requires a policy and C/H require a checkpoint")
    elif bool(args.panel_inputs) != (args.policy == "H") or (args.policy == "G" and args.checkpoint):
        parser.error("only H requires panel inputs; G must not load a checkpoint")
    out = args.out.resolve()
    allowed = ROOT / "temp/directions/flexible_skill_duration/exp"
    if not out.is_relative_to(allowed):
        parser.error("output must be below temp/directions/flexible_skill_duration/exp/")
    out.mkdir(parents=True, exist_ok=True)
    fixture = args.engineering_fixture
    config = RelayCorridorConfig(delta=1., horizon=4 if fixture else 400,
                                 lambda_regions=(0., 1.) if fixture else (.02, .20))
    lanes = 2 if fixture else 32
    policies = {}
    result = {"object_id": OBJECT_ID, "mode": "engineering_fixture" if fixture else "checkpoint_observation",
              "launch_sha": args.launch_sha, "status": "incomplete", "failure": None}
    failure = None
    try:
        check_deadline(start)
        if args.panel_inputs:
            for name, path in zip(("G", "C"), args.panel_inputs):
                with path.open(encoding="utf-8") as stream:
                    policies[name] = json.load(stream)
                check_deadline(start)
        for policy in (("G", "C", "H") if fixture else (args.policy,)):
            summary = base_summary(policy, config, lanes, args.seed, args.launch_sha, fixture)
            policies[policy] = summary
            result = {"object_id": OBJECT_ID, "mode": "engineering_fixture", "launch_sha": args.launch_sha,
                      "policies": policies, "status": "incomplete", "failure": None} if fixture else summary
            adapter = RelayCorridorAdapter(config, num_envs=lanes, master_seed=args.seed,
                                          episode_ids=list(range(lanes)), squeeze_batch=False)
            if policy == "G":
                controller = GreedyOnPublicState()
            elif fixture:
                controller = FixtureController(adapter)
            else:
                summary["checkpoint"] = {"path": str(args.checkpoint), "expected_sha256": CHECKPOINT_SHA256,
                                         "expected_bytes": 64782527}
                summary["controller_seed"], summary["device"], summary["torch_threads"] = 2, "cpu", 4
                controller, summary["normalization"] = load_controller(
                    args.checkpoint, out, lanes, start, summary["counts"])
            evaluate(policy, adapter, controller, summary, start, fixture)
            summary["wall_seconds_before_publication"] = time.perf_counter() - start
        if fixture:
            result.update(summarize_panel(policies))
            result["status"] = "complete"
        elif args.policy == "H":
            result["panel"] = summarize_panel({**policies, "H": copy.deepcopy(result)})
        check_deadline(start)
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        result["status"], result["failure"] = "incomplete", failure
        if fixture:
            result["counts"] = {key: sum(s["counts"][key] for s in policies.values()) for key in COUNT_KEYS}
    result["wall_seconds_before_publication"] = time.perf_counter() - start
    try:
        write_summary(out, result)
        check_deadline(start)
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    wall = time.perf_counter() - start
    breached = wall > CAP_SECONDS
    success = failure is None and not breached and result["status"] == "complete"
    print(json.dumps({"status": "complete" if success else "incomplete", "failure": failure,
                      "complete_wall_seconds": wall, "cap_breached": breached}, allow_nan=False))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
