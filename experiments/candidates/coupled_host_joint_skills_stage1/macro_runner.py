"""Macro-step fits and zero-fit floors (coupled_host_joint_skills_stage1, T-W).

Entered through ``runner.py`` (``--contract target|slot|offset`` for a fit, ``--floor NAME`` for a
zero-fit floor); admission stays in ``runner.main``.  The per-step b01 fit (``runner.run_fit``) is
not touched.

Fit (arms H and SET, the b01 seeds and pairing): 16 lanes x 50 macro steps x 45 rollouts
(= 360k host steps, 36k lane-decisions); one macro step = one action per UAV held for 10 host
steps by the go-to executor (``adapter.MacroContractAdapter``); ``k = 1`` in macro units for both
arms (H: a d2 team decision every macro step, 800 per rollout); shared training worlds
``300000 + lane + episode * 10000`` (no fit-seed term).  Panels as b01 (dev deterministic after
rollouts 0/15/30/45, hold-out deterministic + sampled after 45) with ``runner.WorldTracker`` fed
every host step.  ``probe=True``: 3 rollouts + one timed panel-sized run, ``timing_probe.json``
with ms per host step and per macro step.

Floors (no learner): ``random-target`` (uniform destination in the arena box every macro step),
``random-slot`` (uniform slot per UAV every macro step), ``sticky-random-slot`` (uniform at the
first macro step, then held), ``nearest-unclaimed-slot`` (UAVs in index order each take the
nearest unclaimed slot, 3-D distance from the current position, ties by slot index; cadence
``every_macro_step`` (default) or ``first_macro_step``), ``planner-slots`` (M: the min-makespan
assignment = ``P_relay^on``, held), ``identity-permutation-slots`` (UAV ``i`` takes menu slot ``i``
in the stored menu order, held), ``held-random-permutation-slots`` (one uniform permutation of the
six slots per world, held; conflict-free by construction, no travel optimisation).  Floor
randomness: ``numpy.random.default_rng([world, 1])`` per world (the gate's random-floor derivation)
for the random floors; the held random permutation draws once from a separate
``numpy.random.default_rng([world, 2])`` so the ``[world, 1]`` stream is untouched.

H label readers (panels and training rows, zero cost): see ``LABEL_READER_DEFINITIONS``.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

import numpy as np
import torch

from experiments.candidates.coupled_host_joint_skills_stage1 import runner as R
from experiments.candidates.coupled_host_joint_skills_stage1.adapter import (
    CONTRACTS, MacroCounters, PANEL_WORLD_SET, macro_training_world_seed, make_macro_envs,
    merge_counters,
)
from experiments.candidates.coupled_host_joint_skills_stage1.configuration import (
    DIRECTION, PAIRS, SEEDS, MacroFitSpec, action_squash, is_declared_macro_spec, macro_config_dict,
    make_macro_config,
)
from experiments.candidates.coupled_host_joint_skills_stage1.menus import MENU_WIDTH, MenuProvider

DEFAULT_MENU_DIR = R.ROOT / "runs" / DIRECTION / "menus"
FLOORS = ("random-target", "random-slot", "sticky-random-slot", "nearest-unclaimed-slot",
          "planner-slots", "identity-permutation-slots", "held-random-permutation-slots")
FLOOR_CONTRACT = {"random-target": "target", "random-slot": "slot", "sticky-random-slot": "slot",
                  "nearest-unclaimed-slot": "slot", "planner-slots": "slot",
                  "identity-permutation-slots": "slot", "held-random-permutation-slots": "slot"}
#: permutation floors: the episode-long assignment is recorded per world as ``held_slots``
PERMUTATION_FLOORS = ("identity-permutation-slots", "held-random-permutation-slots")
NEAREST_CADENCES = ("every_macro_step", "first_macro_step")
MACRO_READER_COUNTERS = ("far_target_fraction", "target_change_rate", "slot_conflicts_per_team_decision",
                         "slot_switches_per_episode")


LABEL_READER_DEFINITIONS = {
    "label_team_decisions": "H team decisions read (lanes x macro steps; one team label Z and six agent labels "
                            "z_i per team decision)",
    "agent_distinct_labels_per_team_decision_mean": "mean over team decisions of the number of distinct agent "
                                                    "labels z_i among the six UAVs",
    "agent_distinct_labels_histogram": "team decisions with 1, 2, ..., 6 distinct agent labels (index 0 = 1)",
    "agent_label_entropy_bits_per_team_decision_mean": "mean over team decisions of the entropy (bits, log2) of "
                                                       "the empirical distribution of the six agent labels "
                                                       "within that decision (0 = all six equal)",
    "team_label_episodes": "lane-episodes read for the within-episode team-label analogue",
    "team_distinct_labels_per_episode_mean": "one Z per team decision makes 'distinct team labels per team "
                                             "decision' 1 and its entropy 0 by construction; recorded instead: "
                                             "mean over lane-episodes of the number of distinct Z over the "
                                             "episode's team decisions",
    "team_label_entropy_bits_per_episode_mean": "mean over lane-episodes of the entropy (bits) of Z over the "
                                                "episode's team decisions",
    "agent_label_counts": "pooled agent-label counts (training rows; panels already record them)",
    "team_label_counts": "pooled team-label counts (training rows; panels already record them)",
    "agent_label_entropy_bits": "entropy (bits) of the pooled agent-label counts (training rows)",
    "team_label_entropy_bits": "entropy (bits) of the pooled team-label counts (training rows)",
}


class LabelReader:
    """Zero-cost H label reader over ``(lanes, 6)`` agent labels and ``(lanes,)`` team labels per
    team decision (definitions in ``LABEL_READER_DEFINITIONS``); reads copies, never the step data."""

    def __init__(self, n_z, n_Z, lanes, n_agents=6):
        self.n_z, self.n_Z, self.lanes, self.n_agents = int(n_z), int(n_Z), int(lanes), int(n_agents)
        self.decisions = 0
        self.distinct_sum = 0
        self.distinct_hist = np.zeros(self.n_agents, dtype=np.int64)
        self.entropy_sum = 0.0
        self.agent_counts = np.zeros(self.n_z, dtype=np.int64)
        self.team_counts = np.zeros(self.n_Z, dtype=np.int64)
        self.episode_team_counts = np.zeros((self.lanes, self.n_Z), dtype=np.int64)
        self.episodes = 0
        self.episode_distinct_sum = 0
        self.episode_entropy_sum = 0.0

    def update(self, agent_skills, team_skills):
        agent = np.array(agent_skills, dtype=np.int64, copy=True)
        team = np.array(team_skills, dtype=np.int64, copy=True).reshape(-1)
        if agent.shape != (self.lanes, self.n_agents) or team.shape != (self.lanes,):
            raise ValueError(f"label roster mismatch: agent {agent.shape}, team {team.shape}")
        if agent.min() < 0 or agent.max() >= self.n_z or team.min() < 0 or team.max() >= self.n_Z:
            raise ValueError("label outside the declared label range")
        per_decision = (agent[:, :, None] == np.arange(self.n_z)).sum(axis=1)  # (lanes, n_z)
        distinct = (per_decision > 0).sum(axis=1)
        p = per_decision / float(self.n_agents)
        with np.errstate(divide="ignore", invalid="ignore"):
            entropy = -np.where(p > 0, p * np.log2(p), 0.0).sum(axis=1)
        self.decisions += self.lanes
        self.distinct_sum += int(distinct.sum())
        self.distinct_hist += np.bincount(distinct - 1, minlength=self.n_agents)[:self.n_agents]
        self.entropy_sum += float(entropy.sum())
        self.agent_counts += per_decision.sum(axis=0)
        np.add.at(self.team_counts, team, 1)
        np.add.at(self.episode_team_counts, (np.arange(self.lanes), team), 1)

    def end_episodes(self):
        """Close one episode on every lane (all lanes end together on this host)."""
        for counts in self.episode_team_counts:
            if counts.sum() == 0:
                raise ValueError("closing an empty label episode")
            self.episodes += 1
            self.episode_distinct_sum += int((counts > 0).sum())
            self.episode_entropy_sum += float(R.entropy_bits(counts))
        self.episode_team_counts[:] = 0

    def summary(self, pooled=False):
        if self.episode_team_counts.sum():
            raise ValueError("label reader has an unclosed episode")
        n, e = self.decisions, self.episodes
        out = {"label_team_decisions": n,
               "agent_distinct_labels_per_team_decision_mean": self.distinct_sum / n if n else None,
               "agent_distinct_labels_histogram": self.distinct_hist.tolist(),
               "agent_label_entropy_bits_per_team_decision_mean": self.entropy_sum / n if n else None,
               "team_label_episodes": e,
               "team_distinct_labels_per_episode_mean": self.episode_distinct_sum / e if e else None,
               "team_label_entropy_bits_per_episode_mean": self.episode_entropy_sum / e if e else None}
        if pooled:
            out.update(agent_label_counts=self.agent_counts.tolist(),
                       agent_label_entropy_bits=R.entropy_bits(self.agent_counts),
                       team_label_counts=self.team_counts.tolist(),
                       team_label_entropy_bits=R.entropy_bits(self.team_counts))
        return out


def motion_modules(agent):
    result = {"coordinator": agent.skill_coordinator,
              "discoverer_actor": agent.skill_discoverer.actor,
              "discoverer_critic": agent.skill_discoverer.critic}
    for name in ("team_discriminator", "individual_discriminator"):
        module = getattr(agent, name, None)
        if module is not None:
            result[name] = module
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import ENCODER_CLASS_NAMES

    for root_name, module in list(result.items()):
        for name, child in module.named_modules():
            if name and type(child).__name__ in ENCODER_CLASS_NAMES:
                result[f"{root_name}.{name}"] = child
    return result


def capture_parameters(agent):
    return {name: {k: p.detach().cpu().clone() for k, p in module.named_parameters()}
            for name, module in motion_modules(agent).items()}


def parameter_motion(agent, initial):
    result = {}
    for name, module in motion_modules(agent).items():
        numerator, denominator = 0.0, 0.0
        for key, p in module.named_parameters():
            p0 = initial[name][key].double()
            numerator += float((p.detach().cpu().double() - p0).square().sum())
            denominator += float(p0.square().sum())
        result[name] = {"delta_l2": numerator ** .5,
                        "relative_l2": (numerator / denominator) ** .5 if denominator else None}
    return result


def check_macro_spec_worlds(spec):
    if not isinstance(spec, MacroFitSpec) or spec.contract not in CONTRACTS:
        raise ValueError("a macro fit needs a MacroFitSpec with a known contract")
    if int(spec.horizon) % int(spec.macro_k):
        raise ValueError("macro_k must divide the horizon")
    used = set(spec.dev_worlds) | set(spec.holdout_worlds) | set(spec.probe_panel_worlds)
    if not is_declared_macro_spec(spec) and used & PANEL_WORLD_SET:
        raise ValueError("a non-declared (technical) macro spec must not touch the dev/hold-out panel worlds")
    for name in ("dev_worlds", "holdout_worlds", "probe_panel_worlds"):
        worlds = tuple(getattr(spec, name))
        if not worlds or len(set(worlds)) != len(worlds):
            raise ValueError(f"{name} must be a non-empty list of distinct worlds")
        if len(worlds) % spec.eval_lanes:
            raise ValueError(f"{name} must fill whole evaluation chunks of {spec.eval_lanes} lanes")
    for lane in range(spec.train_lanes):
        for episode in range(max(spec.rollouts, spec.probe_rollouts) + 1):
            macro_training_world_seed(lane, episode)


def _action_shape(spec, lanes):
    return (lanes, 6) if spec.contract == "slot" else (lanes, 6, 3)


def _make_envs(spec, worlds, menus):
    return make_macro_envs(len(worlds), worlds, spec.contract, menus, spec.resolved_menu_in_inputs,
                           spec.area_size, spec.macro_k, action_squash(spec))


def save_checkpoint(agent, out, rollout, config, sha):
    path = out / f"checkpoint_{rollout:02d}.pt"
    payload = {
        "schema": 1, "direction": DIRECTION, "launch_sha": sha, "rollout": rollout,
        "macro_contract": getattr(config, "macro_contract", None),
        "config": R.jsonable(macro_config_dict(config)),
        "modules": {name: module.state_dict() for name, module in R.model_modules(agent).items()},
        "normalizers": {name: R.jsonable(vars(norm)) if (norm := getattr(agent, name, None)) is not None
                        else None for name in R.NORMALIZERS},
        "usage": "Evaluation weights; load through macro_models.build_macro_agent + models.strict_sync; "
                 "no training resume contract or optimizer restoration.",
    }
    partial = path.with_suffix(".pt.partial")
    torch.save(payload, partial)
    partial.replace(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.name, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


# ------------------------------------------------------------------------------ panels


def run_macro_panel(learner, arm, seed, worlds, deterministic, spec, counters, menus, record_memory=None,
                    log_name="evaluation"):
    """Frozen evaluation over ``worlds`` in macro steps; trackers fed every host step."""
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import build_macro_agent
    from experiments.candidates.coupled_host_joint_skills_stage1.models import strict_sync

    worlds = [int(w) for w in worlds]
    lanes = int(spec.eval_lanes)
    chunks = [worlds[i:i + lanes] for i in range(0, len(worlds), lanes)]
    rng_seed = worlds[0] + 51
    learner_before = R.digest_agent(learner)
    row = {"worlds": worlds, "deterministic": bool(deterministic), "rng_seed": rng_seed,
           "steps": 0, "macro_steps": 0, "episodes": 0, "per_world": []}
    target, envs, hooks = None, [], []
    started = time.perf_counter()
    try:
        with R.preserve_rng():
            R.seed_rng(rng_seed)
            envs = _make_envs(spec, chunks[0], menus)
            config = make_macro_config(arm, envs, seed, spec)
            memory_before = R.proc_memory()
            target = build_macro_agent(config, str(counters["log_root"] / "evaluation_logs" / log_name))
            strict_sync(target, learner)
            target.train(False)
            if record_memory is not None:
                record_memory({"before_target_build": memory_before, "after_target_build": R.proc_memory()})
            calls, hooks = R.optimizer_counts(target)
            before = R.digest_agent(target)
            label_counts = np.zeros(int(config.n_z), dtype=np.int64)
            team_counts = np.zeros(int(config.n_Z), dtype=np.int64)
            per_agent_counts = np.zeros((6, int(config.n_z)), dtype=np.int64)
            d2_causes = {"reset": 0, "team_cap": 0, "other": 0}
            label_reader = LabelReader(config.n_z, config.n_Z, lanes) if arm == "H" else None
            for chunk_index, chunk in enumerate(chunks):
                if chunk_index:
                    for env in envs:
                        env.close()
                    envs = _make_envs(spec, chunk, menus)
                for lane in range(lanes):
                    target.reset_env_state(lane)
                states, observations = R.reset_all(envs, chunk)
                trackers = [R.WorldTracker(env, world) for env, world in zip(envs, chunk)]
                world_counters = [None] * lanes
                steps = np.zeros(lanes, dtype=int)
                dones = np.zeros(lanes, dtype=bool)
                with torch.no_grad():
                    for t in range(spec.macro_horizon):
                        actions, _, data = target.step(states, observations, steps, dones,
                            deterministic=bool(deterministic), return_step_data=True, build_infos=False)
                        R.finite(actions, "evaluation actions")
                        if actions.shape != _action_shape(spec, lanes):
                            raise ValueError("evaluation action roster mismatch")
                        if arm == "H":
                            agent_skills = np.asarray(data["agent_skills"], dtype=np.int64)
                            team_skills = np.asarray(data["team_skills"], dtype=np.int64).reshape(-1)
                            for lane in range(lanes):
                                np.add.at(label_counts, agent_skills[lane], 1)
                                np.add.at(per_agent_counts, (np.arange(6), agent_skills[lane]), 1)
                                team_counts[team_skills[lane]] += 1
                            label_reader.update(agent_skills, team_skills)
                            team_cause = np.asarray(data["d2_team_cause"], dtype=np.int64).reshape(-1)
                            if t == 0 and not np.all(team_cause == R.D2_CAUSE_RESET):
                                raise AssertionError("evaluation episode did not start with a d2 reset")
                            d2_causes["reset"] += int(np.sum(team_cause == R.D2_CAUSE_RESET))
                            d2_causes["team_cap"] += int(np.sum(team_cause == 3))
                            d2_causes["other"] += int(np.sum((team_cause != 0) & (team_cause != 1)
                                                             & (team_cause != 3)))
                            agent_cause = np.asarray(data["d2_agent_cause"], dtype=np.int64)
                            if np.any((agent_cause == 4) | (agent_cause == 5) | (team_cause == 2)[:, None]):
                                raise AssertionError("d2 evaluation produced a gap/cap interruption")
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(
                                actions[lane], on_host_step=trackers[lane].update)
                            states[lane] = info["next_state"]
                            observations[lane] = obs
                            dones[lane] = bool(term or trunc)
                            if trunc:
                                raise ValueError("the host contract never truncates")
                            if dones[lane]:
                                world_counters[lane] = info["episode_counters"]
                            row["steps"] += int(info["host_steps"])
                            row["macro_steps"] += 1
                            counters["evaluation_team_steps"] += int(info["host_steps"])
                            counters["evaluation_macro_steps"] += 1
                            row["episodes"] += int(dones[lane])
                        steps += 1
                        if dones.any() and (t != spec.macro_horizon - 1 or not dones.all()):
                            raise ValueError("unexpected evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("evaluation missing terminal boundary")
                if label_reader is not None:
                    label_reader.end_episodes()
                for tracker, macro_counts in zip(trackers, world_counters):
                    summary = tracker.summary()
                    summary["macro_counters"] = macro_counts
                    row["per_world"].append(summary)
            if any(calls.values()) or R.digest_agent(target) != before:
                raise ValueError("evaluation modified parameters or normalizers")
            counters["evaluation_episodes"] += row["episodes"]
            row["means"] = {key: float(np.mean([w[key] for w in row["per_world"]])) for key in R.READER_KEYS}
            row["macro_counters"] = merge_counters(w["macro_counters"] for w in row["per_world"])
            row["relay_position_share_by_agent_mean"] = np.mean(
                [w["relay_position_share_by_agent"] for w in row["per_world"]], axis=0).tolist()
            if arm == "H":
                row["labels"] = {
                    "agent_label_counts": label_counts.tolist(),
                    "agent_label_entropy_bits": R.entropy_bits(label_counts),
                    "team_label_counts": team_counts.tolist(),
                    "team_label_entropy_bits": R.entropy_bits(team_counts),
                    "per_agent_label_entropy_bits": [R.entropy_bits(c) for c in per_agent_counts],
                    "d2_team_causes": d2_causes,
                    **label_reader.summary(),
                }
            row.update(optimizer_calls=calls.copy(), frozen_weights_and_normalizers=True,
                       config=macro_config_dict(config))
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        del target
    if R.digest_agent(learner) != learner_before:
        raise ValueError("evaluator modified learner weights or normalizers")
    row["wall_seconds"] = time.perf_counter() - started
    return row


def evaluate_macro_panels(learner, arm, seed, rollout, out, summary, spec, publish, final, menus):
    runs = [("dev", spec.dev_worlds, True)]
    if final:
        runs += [("holdout", spec.holdout_worlds, True), ("holdout", spec.holdout_worlds, False)]
    for kind, worlds, deterministic in runs:
        mode = "deterministic" if deterministic else "sampled"
        name = f"panel_{rollout:02d}_{kind}_{mode}.json"
        header = {"after_rollout": rollout,
                  "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                  "training_macro_steps": rollout * spec.train_lanes * spec.macro_horizon,
                  "kind": kind, "mode": mode, "status": "running", "file": name}
        summary["panels"].append(header)
        publish(f"evaluation {rollout} {kind} {mode} starting")
        try:
            row = run_macro_panel(learner, arm, seed, worlds, deterministic, spec, summary["counts_ref"], menus,
                                  record_memory=lambda m: summary["memory"]["evaluation_overlap"].append(
                                      {"after_rollout": rollout, "kind": kind, "mode": mode, **m}),
                                  log_name=f"r{rollout:02d}_{kind}_{mode}")
        except Exception as exc:
            header.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            R.write_json(out / name, header)
            raise
        header.update(status="complete", means=row["means"], macro_counters=row["macro_counters"])
        R.write_json(out / name, {**header, **row})
        publish(f"evaluation {rollout} {kind} {mode} complete")


# ------------------------------------------------------------------------------ fit


def _parameter_counts(agent):
    counts = {}
    for name, module in R.model_modules(agent).items():
        counts[name] = int(sum(p.numel() for p in module.parameters()))
    for name, module in motion_modules(agent).items():
        if "." in name:
            counts[name] = int(sum(p.numel() for p in module.parameters()))
    counts["discoverer_actor"] = int(sum(p.numel() for p in agent.skill_discoverer.actor.parameters()))
    counts["discoverer_critic"] = int(sum(p.numel() for p in agent.skill_discoverer.critic.parameters()))
    return counts


def macro_matching_table(arm, seed, envs, spec, learner, config, log_dir):
    """Both arms' macro configs, parameter counts and routes (other arm built under preserved RNG)."""
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import (
        assert_macro_route, build_macro_agent,
    )

    other_arm = "SET" if arm == "H" else "H"
    pair = next(p for p in PAIRS if seed in p)
    other_seed = pair[1] if arm == "H" else pair[0]
    with R.preserve_rng():
        other_config = make_macro_config(other_arm, envs, other_seed, spec)
        count_config = make_macro_config(other_arm, envs[:1], other_seed, spec)
        other_agent = build_macro_agent(count_config, str(log_dir))
    configs = {arm: config, other_arm: other_config}
    agents = {arm: learner, other_arm: other_agent}
    per_arm = {a: macro_config_dict(c) for a, c in configs.items()}
    differing = {name: {"H": per_arm["H"][name], "SET": per_arm["SET"][name]}
                 for name in sorted(per_arm["H"]) if per_arm["H"][name] != per_arm["SET"][name]}
    env0 = envs[0]
    table = {
        "schema": 1, "direction": DIRECTION, "mode": "macro", "contract": spec.contract,
        "pairs_by_position": [list(p) for p in PAIRS],
        "lanes": spec.train_lanes, "horizon_host_steps": spec.horizon, "macro_k": spec.macro_k,
        "macro_horizon": spec.macro_horizon, "rollouts": spec.rollouts,
        "exposure_host_steps_per_fit": spec.train_lanes * spec.horizon * spec.rollouts,
        "exposure_macro_rows_per_fit": spec.train_lanes * spec.macro_horizon * spec.rollouts,
        "team_decisions_per_rollout_H": spec.train_lanes * spec.macro_horizon,
        "action_contract": {
            "contract": spec.contract, "action_space_type": env0.action_space_type,
            "action_dim": env0.action_dim,
            "action_head": {key: getattr(spec, key) for key in ("continuous_action_distribution",
                            "continuous_logstd_init", "continuous_logstd_min", "continuous_logstd_max")},
            "squash": env0.squash,
            "decode": {"target": "low + (high - low) * (u + 1) / 2 per axis, box [0, A]^2 x [50, 150]; "
                                 "u = tanh(a) (Gaussian head) or a (bounded head)",
                       "slot": "index into the world's six P_relay menu rows",
                       "offset": "anchor (P_relay^on assigned target) + disk offset (Gaussian head: "
                                 "300 tanh|a_xy| a_xy/|a_xy|, 50 tanh a_z; bounded head: 300 a_xy/max(1,|a_xy|), "
                                 "50 a_z), clipped to the box"}[spec.contract],
            "executor": "planner.closed_loop_execute action rule for macro_k host steps (unit-ball clip)",
            "menu_in_inputs": bool(spec.resolved_menu_in_inputs),
            "menu_width": int(env0.menu_width),
            "obs_dim": int(env0.obs_dim), "state_dim": int(env0.state_dim),
        },
        "reward_units": "macro reward = mean of the macro_k per-step adapter scalars (team r / 6)",
        "clock": "k = 1 macro step for both arms (H: d2 caps 1, costs +inf; SET: off route)",
        "training_worlds": "300000 + lane + episode * 10000 (shared by every macro fit; no seed term)",
        "counters": MacroCounters.DEFINITIONS,
        "parameter_counts": {a: _parameter_counts(agent) for a, agent in agents.items()},
        "routes": {a: assert_macro_route(agent, a) for a, agent in agents.items()},
        "parameter_count_note": f"{other_arm} counts from a one-lane build of the same recipe",
        "differing_config_fields": differing,
        "config": per_arm,
    }
    del other_agent
    return table


def run_macro_fit(out, arm, seed, launch_sha, admission, spec, menu_dir=DEFAULT_MENU_DIR, probe=False):
    from experiments.candidates.coupled_host_joint_skills_stage1.macro_models import build_macro_agent

    out = Path(out)
    if (out / "summary.json").exists():
        raise ValueError("existing scientific summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_start = R.cpu_seconds()
    rollouts = int(spec.probe_rollouts if probe else spec.rollouts)
    counts = {"training_team_steps": 0, "training_macro_steps": 0, "stored_team_steps": 0,
              "training_episodes": 0, "updates": 0, "evaluation_team_steps": 0,
              "evaluation_macro_steps": 0, "evaluation_episodes": 0, "log_root": out}
    menus = MenuProvider(menu_dir, spec.area_size)
    summary = {"schema": 1, "direction": DIRECTION, "mode": "macro", "contract": getattr(spec, "contract", None),
               "arm": arm, "seed": seed, "launch_sha": launch_sha, "admission": admission,
               "probe": bool(probe), "status": "initializing", "fit_started": False, "failure": None,
               "spec": asdict(spec) if isinstance(spec, MacroFitSpec) else None,
               "rollouts_run": rollouts, "panels": [], "checkpoints": [],
               "counts": counts, "counts_ref": counts,
               "memory": {"evaluation_overlap": [], "start": R.proc_memory()},
               "reward_units": {"training": "macro scalar = mean over the 10 host steps of the adapter scalar "
                                            "(contract team r / 6)",
                                "readings": "team per-step r = 0.5 * (C_bh + S/D), every host step"},
               "counter_definitions": MacroCounters.DEFINITIONS,
               "label_reader_definitions": LABEL_READER_DEFINITIONS if arm == "H" else None,
               "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                           "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
                           "thread_environment": {name: os.environ.get(name) for name in
                              ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}}}

    def publish(boundary):
        summary["last_boundary"] = boundary
        summary["wall_seconds"] = time.perf_counter() - R.PROCESS_START
        summary["menus"] = menus.summary()
        public = {k: v for k, v in summary.items() if k != "counts_ref"}
        public["counts"] = {k: v for k, v in counts.items() if k != "log_root"}
        R.write_json(out / "summary.json", public)
        print(json.dumps({"boundary": boundary, "wall_seconds": round(summary["wall_seconds"], 2)}), flush=True)

    publish("admitted")
    envs, agent, hooks = [], None, []
    timing_rows = []
    try:
        if arm not in SEEDS:
            raise ValueError(f"unknown arm {arm}")
        check_macro_spec_worlds(spec)
        torch.set_num_threads(spec.torch_threads)
        R.seed_rng(seed)
        horizon = spec.macro_horizon
        episodes = np.zeros(spec.train_lanes, dtype=int)
        lane_worlds = [macro_training_world_seed(lane, 0) for lane in range(spec.train_lanes)]
        envs = _make_envs(spec, lane_worlds, menus)
        config = make_macro_config(arm, envs, seed, spec)
        summary["config"] = macro_config_dict(config)
        R.write_json(out / "config.json", {"launch_sha": launch_sha, "spec": asdict(spec),
                                           "config": summary["config"]})
        agent = build_macro_agent(config, str(out / "learner_logs"))
        from experiments.candidates.coupled_host_joint_skills_stage1.models import route_facts

        summary["route"] = route_facts(agent)
        calls, hooks = R.optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["parameter_counts"] = {name: sum(p.numel() for p in module.parameters())
                                       for name, module in R.model_modules(agent).items()}
        initial = capture_parameters(agent)
        summary["initial_parameter_digest"] = R.digest_agent(agent)
        memory_before_table = R.proc_memory()
        table = macro_matching_table(arm, seed, envs, spec, agent, config, out / "matching_table_logs")
        summary["memory"]["matching_table_build"] = {"before": memory_before_table, "after": R.proc_memory()}
        R.write_json(out / "matching_table.json", table)
        if R.digest_agent(agent) != summary["initial_parameter_digest"]:
            raise AssertionError("building the matching table changed the learner")
        agent.train(True)
        if not probe and 0 in spec.panels:
            summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
            evaluate_macro_panels(agent, arm, seed, 0, out, summary, spec, publish, rollouts == 0, menus)
        states, observations = R.reset_all(envs, lane_worlds)
        steps = np.zeros(spec.train_lanes, dtype=int)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"] = "training"
        summary["fit_started"] = True
        summary["training_started_wall"] = time.perf_counter() - R.PROCESS_START
        publish("training starts")
        for rollout in range(1, rollouts + 1):
            rollout_start = time.perf_counter()
            rollout_cpu = R.cpu_seconds()
            menu_seconds_before = menus.seconds
            before = calls.copy()
            if arm == "H":
                agent.reset_d2_metrics()
            world_seeds = [macro_training_world_seed(lane, int(episodes[lane])) for lane in range(spec.train_lanes)]
            returns = np.zeros(spec.train_lanes)
            c_bh_sum = np.zeros(spec.train_lanes)
            clip_events = 0
            episode_counters = []
            label_reader = LabelReader(config.n_z, config.n_Z, spec.train_lanes) if arm == "H" else None
            policy_s = env_s = store_s = 0.0
            for t in range(horizon):
                tick = time.perf_counter()
                actions, _, data = agent.step(states, observations, steps, dones,
                    deterministic=False, return_step_data=True, build_infos=False)
                policy_s += time.perf_counter() - tick
                R.finite(actions, "training actions")
                R.finite(data, "training step data")
                if actions.shape != _action_shape(spec, spec.train_lanes):
                    raise ValueError("training action roster mismatch")
                if label_reader is not None:
                    label_reader.update(data["agent_skills"], data["team_skills"])
                actions_before = actions.copy()
                next_states, next_observations = [], []
                rewards = np.zeros(spec.train_lanes)
                next_dones = np.zeros(spec.train_lanes, dtype=bool)
                tick = time.perf_counter()
                for lane, env in enumerate(envs):
                    obs, reward, term, trunc, info = env.step(actions[lane])
                    if trunc:
                        raise ValueError("the host contract never truncates")
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                    rewards[lane] = reward
                    next_dones[lane] = bool(term or trunc)
                    returns[lane] += reward
                    c_bh_sum[lane] += info["contract_mean"]["coverage_backhauled"] * info["host_steps"]
                    clip_events += info["action_clip_events"]
                    counts["training_team_steps"] += int(info["host_steps"])
                    counts["training_macro_steps"] += 1
                    counts["training_episodes"] += int(next_dones[lane])
                    if next_dones[lane]:
                        episode_counters.append(info["episode_counters"])
                env_s += time.perf_counter() - tick
                if not np.array_equal(actions, actions_before):
                    raise AssertionError("the adapter mutated the stored actions")
                next_states, next_observations = np.stack(next_states), np.stack(next_observations)
                R.finite((next_states, next_observations, rewards), "training transition")
                tick = time.perf_counter()
                agent.store_transition_batch(states=states, next_states=next_states.copy(),
                    observations=observations, next_observations=next_observations.copy(),
                    actions=actions, rewards=rewards, dones=next_dones, infos_batch=None,
                    rollout_step_idx=t, step_data=data)
                store_s += time.perf_counter() - tick
                counts["stored_team_steps"] += spec.train_lanes
                tick = time.perf_counter()
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        episodes[lane] += 1
                        obs, info = env.reset(seed=macro_training_world_seed(lane, int(episodes[lane])))
                        next_states[lane], next_observations[lane] = info["state"], obs
                        agent.reset_env_state(lane)
                        steps[lane] = 0
                    else:
                        steps[lane] += 1
                env_s += time.perf_counter() - tick
                states, observations, dones = next_states, next_observations, next_dones
                if dones.any() and (t != horizon - 1 or not dones.all()):
                    raise ValueError("unexpected training terminal boundary")
            if not dones.all():
                raise ValueError("training rollout missing full episodes")
            if label_reader is not None:
                label_reader.end_episodes()
            menu_s = menus.seconds - menu_seconds_before
            collection_s = time.perf_counter() - rollout_start
            facts = R.terminal_facts(agent, arm, horizon)
            summary["terminal_facts"] = facts
            publish(f"rollout {rollout} collected")
            tick = time.perf_counter()
            losses = agent.update(last_values=np.zeros((spec.train_lanes, 6), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=horizon, last_state=states.copy(),
                last_observations=observations.copy())
            update_s = time.perf_counter() - tick
            R.finite(losses, "training losses")
            counts["updates"] += 1
            d2 = None
            if arm == "H":
                d2 = agent.get_d2_metrics()
                bad = {name: d2["cause_counts"][name] for name in R.D2_FORBIDDEN_CAUSES if d2["cause_counts"][name]}
                if bad:
                    raise AssertionError(f"d2 produced interruption causes {bad}")
                expected_decisions = spec.train_lanes * horizon
                if (d2["team_decisions"] != d2["decision_steps"] or d2["decision_steps"] != d2["steps"]
                        or d2["steps"] != expected_decisions or d2["sampled_total"] != 6 * d2["decision_steps"]):
                    raise AssertionError(f"d2 is not a six-agent team decision every macro step: {d2}")
            motion = parameter_motion(agent, initial)
            timing = {"collection_seconds": collection_s, "update_seconds": update_s,
                      "policy_seconds": policy_s, "env_seconds": env_s - menu_s, "menu_seconds": menu_s,
                      "store_seconds": store_s, "cpu_seconds": R.cpu_seconds() - rollout_cpu,
                      "wall_seconds": time.perf_counter() - rollout_start}
            timing_rows.append(timing)
            rollout_counters = merge_counters(episode_counters)
            row = {"rollout": rollout, "team_steps": counts["training_team_steps"],
                   "macro_steps": counts["training_macro_steps"], "world_seeds": world_seeds,
                   "training_scalar_returns": returns.tolist(),
                   "training_team_r_mean": (6.0 * returns / horizon).tolist(),
                   "training_c_bh_mean": (c_bh_sum / spec.horizon).tolist(),
                   "action_clip_events": int(clip_events), "macro_counters": rollout_counters,
                   "losses": R.jsonable(losses), "d2_metrics": R.jsonable(d2),
                   "terminal_facts": facts,
                   "optimizer_delta": {name: calls[name] - before[name] for name in calls},
                   "optimizer_total": calls.copy(), "parameter_motion": motion,
                   "timing": timing, "memory": R.proc_memory(),
                   "rollout_wall_seconds": timing["wall_seconds"]}
            if label_reader is not None:
                row["labels"] = label_reader.summary(pooled=True)
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(R.jsonable(row), allow_nan=False) + "\n")
            summary["parameter_motion"] = motion
            summary["last_training_row"] = {k: row[k] for k in ("rollout", "team_steps", "macro_steps", "timing",
                                                                "optimizer_total", "action_clip_events",
                                                                "macro_counters")}
            agent.clear_buffers()
            publish(f"rollout {rollout} updated")
            if not probe and rollout in spec.panels:
                summary["checkpoints"].append(save_checkpoint(agent, out, rollout, config, launch_sha))
                evaluate_macro_panels(agent, arm, seed, rollout, out, summary, spec, publish,
                                      rollout == rollouts, menus)
        expected_host = rollouts * spec.train_lanes * spec.horizon
        expected_macro = rollouts * spec.train_lanes * horizon
        if (counts["training_team_steps"] != expected_host or counts["training_macro_steps"] != expected_macro
                or counts["stored_team_steps"] != expected_macro):
            raise ValueError("training exposure incomplete")
        required = ("discoverer_actor", "discoverer_critic") + (
            ("coordinator", "team_discriminator", "individual_discriminator") if arm == "H" else ())
        for name in required:
            if calls[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required learner module did not update: {name}")
        for name, moved in summary["parameter_motion"].items():
            if "." in name and not (arm == "SET" and name.startswith("coordinator.")) and moved["delta_l2"] <= 0:
                raise ValueError(f"new encoder did not update: {name}")
        if arm == "SET" and any(calls[name] for name in ("coordinator", "team_discriminator", "individual_discriminator")):
            raise ValueError("SET unexpectedly updated skill modules")
        if probe:
            summary["probe_result"] = write_macro_probe(out, arm, seed, agent, spec, timing_rows, summary,
                                                        publish, menus)
        summary["status"] = "complete"
        summary["final_parameter_digest"] = R.digest_agent(agent)
        return_code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {"wall_seconds_in_run_fit": time.perf_counter() - started,
                                "command_wall_seconds": time.perf_counter() - R.PROCESS_START,
                                "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
                                "cpu_seconds_in_run_fit": R.cpu_seconds() - cpu_start,
                                "peak_rss_kib": usage.ru_maxrss, "proc_memory_end": R.proc_memory(),
                                "rss_scope": "scientific process Linux RUSAGE_SELF",
                                "resources_unmeasured": ["peak_scratch_bytes"]}
        publish(summary["status"])
    return return_code


def write_macro_probe(out, arm, seed, agent, spec, timing_rows, summary, publish, menus):
    """Time one panel-sized frozen macro evaluation; write ``timing_probe.json`` (no scores)."""
    publish("probe panel timing starts")
    scratch_counts = {"evaluation_team_steps": 0, "evaluation_macro_steps": 0, "evaluation_episodes": 0,
                      "log_root": out}
    overlap = []
    menu0 = menus.seconds
    cpu0, wall0 = R.cpu_seconds(), time.perf_counter()
    row = run_macro_panel(agent, arm, seed, spec.probe_panel_worlds, True, spec, scratch_counts, menus,
                          record_memory=overlap.append, log_name="probe_timing")
    panel_menu = menus.seconds - menu0
    panel_wall = time.perf_counter() - wall0 - panel_menu
    panel_cpu = R.cpu_seconds() - cpu0 - panel_menu
    del row  # timing only
    n = len(timing_rows)
    host_steps = spec.train_lanes * spec.horizon * n
    macro_steps = spec.train_lanes * spec.macro_horizon * n
    total = {key: sum(r[key] for r in timing_rows) for key in
             ("collection_seconds", "update_seconds", "policy_seconds", "env_seconds", "menu_seconds",
              "store_seconds", "cpu_seconds", "wall_seconds")}
    wall_ex_menu = [r["wall_seconds"] - r["menu_seconds"] for r in timing_rows]
    cpu_ex_menu = [r["cpu_seconds"] - r["menu_seconds"] for r in timing_rows]
    per_world = panel_wall / len(spec.probe_panel_worlds)
    per_world_cpu = panel_cpu / len(spec.probe_panel_worlds)
    panel_world_runs = len(spec.panels) * len(spec.dev_worlds) + 2 * len(spec.holdout_worlds)
    probe = {
        "schema": 1, "direction": DIRECTION, "mode": "macro", "contract": spec.contract, "arm": arm,
        "seed": seed, "probe_rollouts": n, "host_steps": host_steps, "macro_steps": macro_steps,
        "seconds_per_rollout": {k.replace("_seconds", ""): v / n for k, v in total.items()},
        "per_rollout": timing_rows,
        "ms_per_host_step": {"env": 1000.0 * total["env_seconds"] / host_steps,
                             "all_excluding_menus": 1000.0 * sum(wall_ex_menu) / host_steps},
        "ms_per_macro_step": {name: 1000.0 * total[f"{name}_seconds"] / macro_steps
                              for name in ("env", "policy", "store", "update")},
        "menu_seconds_excluded": {"training": total["menu_seconds"], "panel": panel_menu,
                                  "note": "menu cache fills (planner searches) are one-off; a warm cache "
                                          "costs ~0"},
        "panel_run": {"worlds": list(spec.probe_panel_worlds), "deterministic": True,
                      "wall_seconds": panel_wall, "cpu_seconds": panel_cpu,
                      "scores": "not recorded (timing only)"},
        "wall_cpu_ratio_training": float(sum(cpu_ex_menu) / sum(wall_ex_menu)) if sum(wall_ex_menu) else None,
        "projection": {
            "rollouts": spec.rollouts,
            "training_wall_seconds": spec.rollouts * float(np.mean(wall_ex_menu)),
            "training_cpu_seconds": spec.rollouts * float(np.mean(cpu_ex_menu)),
            "panel_world_episodes": panel_world_runs,
            "panel_wall_seconds": panel_world_runs * per_world,
            "panel_cpu_seconds": panel_world_runs * per_world_cpu,
        },
        "memory": {"peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   "evaluation_overlap": overlap, "now": R.proc_memory()},
        "note": "projection = declared rollouts x mean probe rollout (menu fills excluded) + declared panel "
                "episodes x probe per-world panel time; checkpoints and menu cache fills not included",
    }
    probe["projection"]["fit_wall_seconds"] = (probe["projection"]["training_wall_seconds"]
                                               + probe["projection"]["panel_wall_seconds"])
    probe["projection"]["fit_cpu_seconds"] = (probe["projection"]["training_cpu_seconds"]
                                              + probe["projection"]["panel_cpu_seconds"])
    R.write_json(out / "timing_probe.json", probe)
    publish("probe panel timing complete")
    return {"timing_probe": "timing_probe.json",
            "projected_fit_wall_seconds": probe["projection"]["fit_wall_seconds"],
            "projected_fit_cpu_seconds": probe["projection"]["fit_cpu_seconds"]}


# ------------------------------------------------------------------------------ zero-fit floors


def nearest_unclaimed(positions, menu_positions):
    """UAVs in index order take the nearest unclaimed slot (3-D distance; ties -> lower slot)."""
    claimed = np.zeros(menu_positions.shape[0], dtype=bool)
    slots = np.zeros(positions.shape[0], dtype=np.int64)
    for i in range(positions.shape[0]):
        distance = np.linalg.norm(menu_positions - positions[i], axis=1)
        distance[claimed] = np.inf
        slots[i] = int(np.argmin(distance))
        claimed[slots[i]] = True
    return slots


class FloorPolicy:
    """Zero-fit floor decisions for one episode of one world."""

    def __init__(self, floor, env, world, nearest_cadence="every_macro_step"):
        if floor not in FLOORS:
            raise ValueError(f"unknown floor {floor!r}")
        if nearest_cadence not in NEAREST_CADENCES:
            raise ValueError(f"unknown nearest cadence {nearest_cadence!r}")
        self.floor = floor
        self.env = env
        self.rng = np.random.default_rng([int(world), 1])
        self.world = int(world)
        self.cadence = nearest_cadence
        self.held = None

    def step(self, on_host_step=None):
        env = self.env
        if self.floor == "random-target":
            low = np.array([0.0, 0.0, env.height_range[0]])
            high = np.array([env.area_size, env.area_size, env.height_range[1]])
            targets = self.rng.uniform(low, high, (env.n_uavs, 3))
            return env.step_targets(targets, on_host_step=on_host_step)
        if self.floor == "random-slot":
            slots = self.rng.integers(0, env.n_slots, env.n_uavs)
        elif self.floor == "sticky-random-slot":
            if self.held is None:
                self.held = self.rng.integers(0, env.n_slots, env.n_uavs)
            slots = self.held
        elif self.floor == "nearest-unclaimed-slot":
            if self.held is None or self.cadence == "every_macro_step":
                self.held = nearest_unclaimed(np.asarray(env.host.uav_positions, dtype=float),
                                              np.asarray(env.menu["positions_xyz"], dtype=float))
            slots = self.held
        elif self.floor == "identity-permutation-slots":
            if self.held is None:
                self.held = np.arange(env.n_slots, dtype=np.int64)
            slots = self.held
        elif self.floor == "held-random-permutation-slots":
            if self.held is None:  # separate stream: the [world, 1] draws of the other floors are unchanged
                self.held = np.random.default_rng([self.world, 2]).permutation(env.n_slots).astype(np.int64)
            slots = self.held
        else:  # planner-slots (M)
            slots = np.asarray(env.menu["m_permutation"], dtype=np.int64)
        return env.step(np.asarray(slots, dtype=np.int64), on_host_step=on_host_step)


def run_floor_world(floor, world, area_size, menus, nearest_cadence="every_macro_step"):
    """One 500-step episode of a floor on ``world``; returns the tracker summary + counters."""
    contract = FLOOR_CONTRACT[floor]
    env = make_macro_envs(1, [world], contract, menus, None, area_size)[0]
    try:
        env.reset(seed=int(world))
        tracker = R.WorldTracker(env, world)
        policy = FloorPolicy(floor, env, world, nearest_cadence)
        done = False
        info = None
        while not done:
            _obs, _reward, done, _trunc, info = policy.step(on_host_step=tracker.update)
        row = tracker.summary()
        row["macro_counters"] = info["episode_counters"]
        if floor in PERMUTATION_FLOORS:
            row["held_slots"] = [int(s) for s in policy.held]
        return row
    finally:
        env.close()


def run_floor(out, floor, worlds, area_size, menu_dir, launch_sha, admission,
              nearest_cadence="every_macro_step"):
    out = Path(out)
    if (out / "summary.json").exists():
        raise ValueError("existing scientific summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started, cpu0 = time.perf_counter(), R.cpu_seconds()
    menus = MenuProvider(menu_dir, area_size)
    summary = {"schema": 1, "direction": DIRECTION, "mode": "macro_floor", "floor": floor,
               "contract": FLOOR_CONTRACT[floor], "launch_sha": launch_sha, "admission": admission,
               "worlds": [int(w) for w in worlds], "area_size": int(area_size),
               "nearest_cadence": nearest_cadence if floor == "nearest-unclaimed-slot" else None,
               "rng": {"held-random-permutation-slots": "numpy.random.default_rng([world, 2]).permutation(6) "
                                                        "once per world",
                       "identity-permutation-slots": "none (UAV i -> menu slot i)"}.get(
                           floor, "numpy.random.default_rng([world, 1]) per world (random floors)"),
               "training_fits_performed": 0, "status": "running", "per_world": [],
               "counter_definitions": MacroCounters.DEFINITIONS}
    try:
        for world in worlds:
            w0 = time.perf_counter()
            menu0 = menus.seconds
            row = run_floor_world(floor, int(world), area_size, menus, nearest_cadence)
            row["wall_seconds_excluding_menu"] = time.perf_counter() - w0 - (menus.seconds - menu0)
            summary["per_world"].append(row)
        rows = summary["per_world"]
        summary["means"] = {key: float(np.mean([w[key] for w in rows])) for key in R.READER_KEYS}
        summary["macro_counters"] = merge_counters(w["macro_counters"] for w in rows)
        summary["status"] = "complete"
        code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        code = 1
    summary["menus"] = menus.summary()
    summary["resources"] = {"wall_seconds": time.perf_counter() - started, "cpu_seconds": R.cpu_seconds() - cpu0,
                            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    R.write_json(out / "summary.json", summary)
    return code


def smoke_refusal(worlds, out, menu_dir):
    """``--smoke-no-admission`` guard: non-panel worlds only; ``--out`` and ``--menu-dir`` under this
    checkout's temp/ (a smoke never writes under runs/)."""
    panel = [w for w in worlds if int(w) in PANEL_WORLD_SET]
    if panel:
        return f"--smoke-no-admission refuses declared panel worlds {panel}"
    temp_root = (R.ROOT / "temp").resolve()
    for flag, path in (("--out", out), ("--menu-dir", menu_dir)):
        resolved = Path(path).resolve()
        if resolved != temp_root and temp_root not in resolved.parents:
            return f"--smoke-no-admission needs {flag} under {temp_root}"
    return None
