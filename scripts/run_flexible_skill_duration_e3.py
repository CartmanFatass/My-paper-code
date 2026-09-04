"""FSD E3 heterogeneous-hazard runner, one row/arm/seed per invocation.

This is a thin instrumentation layer over the E2 corridor learner/evaluator route.  It changes
only the frozen E3 host row and arm parameters, consumes the caller's memory-admission receipt,
and adds the paired-return and regional event-to-renewal quantities named by the E3 card.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
for _path in (REPO_ROOT, REPO_ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from envs.relay_corridor.config import PROPOSAL_GRID, proposal_config  # noqa: E402
import run_flexible_skill_duration_e2 as e2  # noqa: E402


CARD = (
    "docs/research/candidates/flexible_skill_duration/"
    "FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md"
)
ROWS = tuple(PROPOSAL_GRID)
ARMS = ("d0", "d2")
EVAL_MASTER_SEED = 770003
MAX_WALL_SECONDS = 8 * 60 * 60
_PREFLIGHT_RECEIPT: Path | None = None
_ACTIVE_RECORDER = None
_RUN_STARTED = 0.0


class WallCapExceeded(RuntimeError):
    """The frozen stop reached after a completed rollout."""


def row_config(row: str, **overrides):
    """The existing registered proposal row, without a copied host definition."""
    return proposal_config(row, **overrides)


def arm_parameters(row: str, arm: str, horizon: int | None = None) -> dict:
    """Exact E3 treatment/comparator parameters."""
    horizon = int(row_config(row).horizon if horizon is None else horizon)
    k = int(PROPOSAL_GRID[row]["best_k"]) if arm == "d0" else min(40, horizon)
    c = float("inf") if arm == "d0" else 0.25
    return {
        "policy_interruption_mode": "d2",
        "interruption_delta": 1,
        "interruption_cost_c": c,
        "interruption_cost_c_Z": c,
        "skill_cap_k_max": k,
        "team_cap_k_Z": k if arm == "d0" else horizon,
        "age_feature": "off",
    }


def load_preflight(run_dir: Path) -> dict:
    """Consume the receipt produced immediately before this invocation."""
    expected = (run_dir / "preflight.json").resolve()
    if _PREFLIGHT_RECEIPT is None or _PREFLIGHT_RECEIPT.resolve() != expected:
        raise ValueError("--preflight-receipt must name this run's preflight.json")
    payload = json.loads(expected.read_text(encoding="utf-8"))
    if not (payload.get("passed") is True
            and payload.get("physical_floor_pass") is True
            and payload.get("effective_floor_pass") is True):
        raise ValueError("the supplied 4 GiB memory admission did not pass")
    return payload


def peak_rss_bytes() -> int:
    """Read this Windows process's peak working set."""
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong),
            ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t),
            ("quota_peak_paged", ctypes.c_size_t), ("quota_paged", ctypes.c_size_t),
            ("quota_peak_nonpaged", ctypes.c_size_t), ("quota_nonpaged", ctypes.c_size_t),
            ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t),
        ]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb):
        raise OSError("could not read process peak RSS")
    return int(counters.peak_working_set)


class E3Recorder(e2.DriverRecorder):
    """Add host consequence fields to E2's instance-local recorder."""
    def __init__(self, driver):
        global _ACTIVE_RECORDER
        self.lease_fresh = []
        self.role_correct = []
        self.service = []
        self.per_agent_reward = []
        super().__init__(driver)
        _ACTIVE_RECORDER = self

    def reset_rollout(self) -> None:
        super().reset_rollout()
        self.lease_fresh = []
        self.role_correct = []
        self.service = []
        self.per_agent_reward = []

    def _wrapped_adapter_step(self, actions, renew_mask=None, **kwargs):
        out = super()._wrapped_adapter_step(actions, renew_mask=renew_mask, **kwargs)
        info = out[4]
        self.lease_fresh.append(np.asarray(info["lease_fresh"], dtype=bool).copy())
        self.role_correct.append(np.asarray(info["role_correct"], dtype=bool).copy())
        self.service.append(np.asarray(info["service_indicators"], dtype=bool).copy())
        self.per_agent_reward.append(
            np.asarray(info["per_agent_service_reward"], dtype=np.float64).copy())
        return out

    def stacked(self) -> dict:
        out = super().stacked()
        out.update(
            lease_fresh=np.asarray(self.lease_fresh, dtype=bool),
            role_correct=np.asarray(self.role_correct, dtype=bool),
            service=np.asarray(self.service, dtype=bool),
            per_agent_reward=np.asarray(self.per_agent_reward, dtype=np.float64),
        )
        return out


def _segments(sampled: np.ndarray) -> list[int]:
    """Lengths under the learner's close-at-renewal and flush-at-H convention."""
    horizon, lanes, agents = sampled.shape
    lengths = []
    for lane in range(lanes):
        for agent in range(agents):
            renewals = np.flatnonzero(sampled[:, lane, agent])
            starts = renewals.tolist() if renewals.size else [0]
            lengths.extend(int(b - a) for a, b in zip(starts, starts[1:]))
            lengths.append(int(horizon - starts[-1]))
    return lengths


def regional_path_record(sampled, agent_cause, team_cause, change_flag,
                         region_of_agent, consequence) -> dict:
    """Compute the frozen regional event-to-renewal path on one rollout."""
    sampled = np.asarray(sampled, dtype=bool)
    causes = np.asarray(agent_cause, dtype=np.int64)
    team = np.asarray(team_cause, dtype=np.int64)
    flags = np.asarray(change_flag, dtype=bool)
    regions = np.asarray(region_of_agent, dtype=np.int64)
    previous = np.zeros_like(flags)
    previous[1:] = flags[:-1]
    event_window = flags | previous
    rows = {}
    for region in range(flags.shape[2]):
        agents = np.flatnonzero(regions == region)
        renew = sampled[:, :, agents]
        region_causes = causes[:, :, agents]
        gap = renew & ((region_causes == e2.CAUSE_GAP)
                       | (region_causes == e2.CAUSE_TEAM_GAP))
        precision_hits = gap & event_window[:, :, region, None]
        gap_any = gap.any(axis=2)
        event_followed = gap_any.copy()
        event_followed[:-1] |= gap_any[1:]
        event = flags[:, :, region]
        denominator = int(np.prod(renew.shape))
        env_steps = int(team.size)
        gap_count = int(gap.sum())
        event_count = int(event.sum())
        lengths = _segments(renew)
        fresh = consequence["lease_fresh"][:, :, agents]
        correct = consequence["role_correct"][:, :, agents]
        service = consequence["service"][:, :, agents]
        stale_service = service & (~fresh)
        stale_opportunity = (~fresh) & correct & (~renew)
        rows[str(region)] = {
            "hazard": "low" if region == 0 else "high",
            "lambda": None,  # filled from the selected proposal row before archival
            "segment_lengths": lengths,
            "segment_length": e2.decile_summary(lengths),
            "agent_steps": denominator,
            "gap_renewal_count": gap_count,
            "gap_renewal_rate_per_agent_step": gap_count / denominator,
            "team_gap_decision_count": int((team == e2.CAUSE_TEAM_GAP).sum()),
            "team_gap_decision_rate_per_env_step": (
                float((team == e2.CAUSE_TEAM_GAP).sum()) / env_steps),
            "event_count": event_count,
            "gap_renewal_event_window_count": int(precision_hits.sum()),
            "event_precision": (float(precision_hits.sum()) / gap_count
                                if gap_count else None),
            "events_followed_by_gap_count": int((event & event_followed).sum()),
            "event_recall": (float((event & event_followed).sum()) / event_count
                             if event_count else None),
            "cap_count": int((renew & ((region_causes == e2.CAUSE_CAP)
                                      | (region_causes == e2.CAUSE_TEAM_CAP))).sum()),
            "reset_count": int((renew & (region_causes == e2.CAUSE_RESET)).sum()),
            "renewal_outage_count": int(renew.sum()),
            "renewal_outage_rate_per_agent_step": float(renew.sum()) / denominator,
            "fresh_correct_role_service_count": int(service.sum()),
            "fresh_correct_role_service_rate": float(service.sum()) / denominator,
            "stale_service_count": int(stale_service.sum()),
            "stale_service_rate_per_agent_step": float(stale_service.sum()) / denominator,
            "stale_correct_role_opportunity_count": int(stale_opportunity.sum()),
            "stale_correct_role_opportunity_rate": (
                float(stale_opportunity.sum()) / denominator),
            "shared_return_contribution": float(
                consequence["per_agent_reward"][:, :, agents].sum() / env_steps),
        }
    return rows


_E2_INTERRUPTION_RECORD = e2.interruption_record


def interruption_record(*args, **kwargs) -> dict:
    base = _E2_INTERRUPTION_RECORD(*args, **kwargs)
    captured = _ACTIVE_RECORDER.stacked()
    consequence = {name: captured[name] for name in (
        "lease_fresh", "role_correct", "service", "per_agent_reward")}
    base["regional_path"] = regional_path_record(
        args[3], args[4], args[5], args[6], args[7], consequence)
    return base


class E3Evaluator(e2.CorridorEvaluator):
    """E2 evaluator with the ordered return inputs retained for pairing."""
    def run(self, learner, episodes, tape_events, references, rollout_index):
        self._sync(learner)
        episodes = int(episodes)
        started = time.perf_counter()
        returns = np.zeros(episodes, dtype=np.float64)
        renew_fraction = np.zeros(episodes, dtype=np.float64)
        service = np.zeros(episodes, dtype=np.float64)
        for start in range(0, episodes, self.chunk):
            ids = list(range(start, min(start + self.chunk, episodes)))
            lanes = len(ids)
            self.adapter._episode_ids = ids + list(
                range(episodes, episodes + self.chunk - lanes))
            observations, info = self.adapter.reset()
            self._reset_lanes()
            observations = np.asarray(observations, dtype=np.float32)
            states = np.asarray(info["state"], dtype=np.float64)
            env_steps = np.zeros(self.chunk, dtype=int)
            dones = np.zeros(self.chunk, dtype=bool)
            reward_sum = np.zeros(self.chunk, dtype=np.float64)
            renew_sum = np.zeros(self.chunk, dtype=np.float64)
            service_sum = np.zeros(self.chunk, dtype=np.float64)
            for _ in range(self.horizon):
                actions, _infos, step = self.agent.step(
                    states, observations, env_steps, dones, deterministic=True,
                    return_step_data=True, build_infos=False)
                renew = np.asarray(step["d2_sampled_mask"], dtype=bool)
                next_obs, _reward, _term, _trunc, step_info = self.adapter.step(
                    np.asarray(actions), renew_mask=renew)
                reward_sum += np.asarray(step_info["shared_reward"], dtype=np.float64)
                renew_sum += renew.mean(axis=1)
                service_sum += np.asarray(
                    step_info["service_indicators"], dtype=np.float64).mean(axis=1)
                observations = np.asarray(next_obs, dtype=np.float32)
                states = np.asarray(step_info["state"], dtype=np.float64)
                env_steps += 1
            returns[start:start + lanes] = reward_sum[:lanes] / self.horizon
            renew_fraction[start:start + lanes] = renew_sum[:lanes] / self.horizon
            service[start:start + lanes] = service_sum[:lanes] / self.horizon
        self.count += 1
        mean = float(returns.mean())
        std = float(returns.std(ddof=1)) if episodes > 1 else 0.0
        return {
            "evaluation_index": self.count, "rollout": int(rollout_index),
            "episodes": episodes, "eval_master_seed": self.master_seed,
            "episode_ids": list(range(episodes)),
            "episode_returns": returns.tolist(),
            "return_definition": (
                "mean per-step shared reward on the ordered keyed episode tape"),
            "return_mean": mean, "return_std": std,
            "return_stderr": std / math.sqrt(episodes) if episodes > 1 else 0.0,
            "return_min": float(returns.min()), "return_max": float(returns.max()),
            "J_switch": float(references["J_switch"]),
            "J_best_fixed_k": float(references["J_best_fixed_k"]),
            "best_fixed_k": int(references["best_fixed_k"]),
            "gap_to_J_switch": float(references["J_switch"]) - mean,
            "gap_to_J_best_fixed_k": float(references["J_best_fixed_k"]) - mean,
            "mean_renew_fraction": float(renew_fraction.mean()),
            "mean_service_fraction": float(service.mean()),
            "wall_seconds": float(time.perf_counter() - started),
        }


def evaluation_tape_inputs(corridor, master_seed: int, episodes: int, chunk: int) -> dict:
    """Record the ordered keyed inputs without E2's out-of-scope content digest."""
    return {
        "episodes": int(episodes),
        "master_seed": int(master_seed),
        "episode_ids": f"0..{int(episodes) - 1}",
        "chunk": int(chunk),
        "keying": "(master_seed, episode_id, entity_or_region_id)",
        "event_counts": np.zeros(int(episodes), dtype=np.int64),
        "event_counts_per_region": np.zeros(
            (int(episodes), int(corridor.n_regions)), dtype=np.int64),
    }


class TimedDriver(e2.RelayCorridorHMASDDriver):
    """Stop after, without altering, the first completed rollout beyond the cap."""
    def run_rollout(self, *args, **kwargs):
        out = super().run_rollout(*args, **kwargs)
        if time.perf_counter() - _RUN_STARTED > MAX_WALL_SECONDS:
            raise WallCapExceeded("first completed rollout exceeded the eight-hour wall cap")
        return out


def event_path(regional: dict) -> bool:
    low, high = regional["0"], regional["1"]
    return bool(
        high["segment_length"]["mean"] < low["segment_length"]["mean"]
        and high["gap_renewal_rate_per_agent_step"]
        > low["gap_renewal_rate_per_agent_step"]
        and high["event_precision"] is not None
        and high["event_precision"] > 0.5
    )


def apply_result_rule(pairs: list[dict]) -> str:
    """Apply the frozen large-row branches in order."""
    competent = [p for p in pairs if p["d0_competence_ratio"] >= 0.85]
    if len(competent) < 2:
        return "E3-COMPETENCE-BLOCKED"
    positive = [p for p in competent if p["G"] > 0]
    same_path = [p for p in positive if p["event_path"]]
    if len(positive) >= 2 and len(same_path) >= 2:
        return "E3-H1-ACTIONABLE"
    if len(positive) >= 2:
        return "E3-RETURN-WITHOUT-PATH"
    if sum(p["G"] <= 0 for p in competent) >= 2:
        return "E3-H0-NO-ADVANTAGE"
    return "E3-UNSTABLE"


def paired_return(d0: list[float], d2: list[float], m_dur: float) -> dict:
    """Primary paired estimand from ordered evaluation inputs."""
    diff = np.asarray(d2, dtype=np.float64) - np.asarray(d0, dtype=np.float64)
    stderr = float(diff.std(ddof=1) / math.sqrt(diff.size)) if diff.size > 1 else 0.0
    gain = float(diff.mean())
    return {"G": gain, "paired_stderr": stderr, "Q": gain / float(m_dur),
            "episode_count": int(diff.size)}


def _aggregate_path(records: list[dict]) -> dict:
    out = {}
    for region in ("0", "1"):
        rows = [r["regional_path"][region] for r in records]
        lengths = [v for row in rows for v in row["segment_lengths"]]
        agent_steps = sum(r["agent_steps"] for r in rows)
        gap = sum(r["gap_renewal_count"] for r in rows)
        precision_hits = sum(r["gap_renewal_event_window_count"] for r in rows)
        events = sum(r["event_count"] for r in rows)
        recalled = sum(r["events_followed_by_gap_count"] for r in rows)
        env_steps = sum(r["agent_steps"] // 3 for r in rows)
        team_gap = sum(r["team_gap_decision_count"] for r in rows)
        outage = sum(r["renewal_outage_count"] for r in rows)
        fresh_service = sum(r["fresh_correct_role_service_count"] for r in rows)
        stale_service = sum(r["stale_service_count"] for r in rows)
        stale_opportunity = sum(r["stale_correct_role_opportunity_count"] for r in rows)
        out[region] = {
            "hazard": rows[0]["hazard"], "lambda": rows[0]["lambda"],
            "segment_length": e2.decile_summary(lengths),
            "agent_steps": agent_steps,
            "env_steps": env_steps,
            "gap_renewal_count": gap,
            "gap_renewal_rate_per_agent_step": gap / agent_steps,
            "team_gap_decision_count": team_gap,
            "team_gap_decision_rate_per_env_step": team_gap / env_steps,
            "event_count": events,
            "gap_renewal_event_window_count": precision_hits,
            "event_precision": precision_hits / gap if gap else None,
            "events_followed_by_gap_count": recalled,
            "event_recall": recalled / events if events else None,
            "cap_count": sum(r["cap_count"] for r in rows),
            "reset_count": sum(r["reset_count"] for r in rows),
            "renewal_outage_count": outage,
            "renewal_outage_rate_per_agent_step": outage / agent_steps,
            "fresh_correct_role_service_count": fresh_service,
            "fresh_correct_role_service_rate": fresh_service / agent_steps,
            "stale_service_count": stale_service,
            "stale_service_rate_per_agent_step": stale_service / agent_steps,
            "stale_correct_role_opportunity_count": stale_opportunity,
            "stale_correct_role_opportunity_rate": stale_opportunity / agent_steps,
            "shared_return_contribution": sum(
                r["shared_return_contribution"] for r in rows) / len(rows),
        }
    return out


def strip_inherited_versions(run_dir: Path) -> None:
    """Remove E2 compatibility fields from success and terminal partial artifacts."""
    for name in ("manifest.json", "summary.json"):
        path = run_dir / name
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload.pop("schema_version", None)
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _postprocess(run_dir: Path, row: str, arm: str) -> None:
    interruptions = [json.loads(line) for line in
                     (run_dir / "interruptions.jsonl").read_text(
                         encoding="utf-8").splitlines() if line.strip()]
    hazards = row_config(row).lambda_regions
    for record in interruptions:
        for region in ("0", "1"):
            record["regional_path"][region]["lambda"] = float(hazards[int(region)])
    (run_dir / "path.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in interruptions),
        encoding="utf-8")
    summary_path = run_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.pop("schema_version", None)
    refs = summary["references"]
    k = int(PROPOSAL_GRID[row]["best_k"])
    j_k = (float(refs["J_fixed_k"][str(k)])
           if str(k) in refs["J_fixed_k"] else None)
    final_return = summary["final_evaluation_return_mean"]
    cumulative = _aggregate_path(interruptions) if interruptions else None
    try:
        rss = peak_rss_bytes()
        resource_status = "measured"
    except OSError:
        rss = None
        resource_status = "resources_unmeasured"
    summary.update({
        "card": CARD, "runner": "scripts/run_flexible_skill_duration_e3.py",
        "row": row, "arm": arm,
        "reference_m_dur": float(refs["m_dur"]),
        "reference_m_dur_frozen_table": float(PROPOSAL_GRID[row]["m_dur"]),
        "reference_J_k": j_k,
        "d0_competence_ratio_input": (
            float(final_return) / j_k
            if arm == "d0" and final_return is not None and j_k is not None else None),
        "evaluation_episodes_total": sum(
            int(record["episodes"]) for record in summary["evaluations"]),
        "evaluation_episode_return_inputs": [
            r["episode_returns"] for r in summary["evaluations"]],
        "final_regional_path": interruptions[-1]["regional_path"] if interruptions else None,
        "cumulative_regional_path": cumulative,
        "large_row_event_path": event_path(cumulative) if row == "large" and cumulative else None,
        "preflight_receipt_path": str(_PREFLIGHT_RECEIPT.resolve()),
        "peak_rss_bytes": rss,
        "resource_telemetry_status": resource_status,
        "artifact_names": {
            "summary": "summary.json", "preflight": "preflight.json",
            "evaluations": "eval.jsonl", "learner_path": "path.jsonl",
            "checkpoint": "checkpoint_final.pt",
        },
        "cost_law": {
            "training_seconds": "rollouts * (64.6 + 0.769 * coordinator_steps_per_rollout)",
            "evaluation_seconds": "evaluated_episodes * 0.46",
            "margin": 0.15,
            "projected_wall_hours": (1.16 if arm == "d0" and k == 20
                                     else 1.68 if arm == "d0" else 4.63),
            "cap_hours": 8.0,
            "measured_wall_seconds": summary["wall_seconds_total"],
            "measured_seconds_per_rollout": summary["seconds_per_rollout_mean"],
        },
    })
    summary_path.write_text(json.dumps(e2._jsonable(summary), indent=2), encoding="utf-8")
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("schema_version", None)
    manifest.update({"contract": CARD, "runner": "scripts/run_flexible_skill_duration_e3.py",
                     "row": row, "e3_arm": arm})
    expected_eval = {
        "checkpoints": [5, 10, 15, 20], "intermediate_episodes": 512,
        "final_episodes": 2048, "full_run_records": 4,
    }
    manifest["evaluation"]["e3_expected_counts"] = expected_eval
    observed_eval_episodes = [int(record["episodes"]) for record in summary["evaluations"]]
    manifest["evaluation"]["reduced_from_contract"] = not (
        [int(record["rollout"]) for record in summary["evaluations"]]
        == expected_eval["checkpoints"]
        and observed_eval_episodes == [512, 512, 512, 2048]
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FSD E3 heterogeneous-hazard runner")
    parser.add_argument("--row", choices=ROWS, required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--preflight-receipt", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--launch-commit", required=True)
    parser.add_argument("--rollouts", type=int, default=20)
    parser.add_argument("--num-envs", type=int, default=16)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--eval-interval", type=int, default=5)
    parser.add_argument("--eval-episodes", type=int, default=2048)
    parser.add_argument("--eval-intermediate-episodes", type=int, default=512)
    parser.add_argument("--eval-chunk", type=int, default=512)
    return parser


def main(argv=None) -> int:
    global _PREFLIGHT_RECEIPT, _RUN_STARTED
    args = build_parser().parse_args(argv)
    _PREFLIGHT_RECEIPT = Path(args.preflight_receipt)
    run_name = f"{args.row}_{args.arm}_seed{args.seed}"
    config_kwargs = {"horizon": int(args.horizon)}
    if int(args.horizon) != 400:
        config_kwargs["d0_k_set"] = (1,)
    config = row_config(args.row, **config_kwargs)
    overrides = arm_parameters(args.row, args.arm, horizon=int(args.horizon))
    e2.CONTRACT = CARD
    e2.HOST_POINT = config.__dict__
    e2.ARMS = {args.arm: {"family": args.arm, "k": overrides["skill_cap_k_max"],
                         "c": overrides["interruption_cost_c"]}}
    e2.ARM_ORDER = (args.arm,)
    e2.corridor_config = lambda **_kw: config
    e2.arm_parameters = lambda _arm: dict(overrides)
    e2.run_preflight = load_preflight
    e2.DriverRecorder = E3Recorder
    e2.interruption_record = interruption_record
    e2.CorridorEvaluator = E3Evaluator
    e2.tape_digest_and_events = evaluation_tape_inputs
    e2.RelayCorridorHMASDDriver = TimedDriver
    _RUN_STARTED = time.perf_counter()
    code = e2.main([
        "--arm", args.arm, "--seed", str(args.seed), "--rollouts", str(args.rollouts),
        "--num-envs", str(args.num_envs), "--threads", str(args.threads),
        "--output-root", args.output_root, "--launch-commit", args.launch_commit,
        "--eval-interval", str(args.eval_interval),
        "--eval-tape-set", str(args.eval_episodes),
        "--eval-episodes", str(args.eval_episodes),
        "--eval-intermediate-episodes", str(args.eval_intermediate_episodes),
        "--eval-chunk", str(args.eval_chunk),
        "--eval-master-seed", str(EVAL_MASTER_SEED), "--run-name", run_name,
    ])
    run_dir = Path(args.output_root).resolve() / run_name
    strip_inherited_versions(run_dir)
    if (run_dir / "summary.json").exists():
        _postprocess(run_dir, args.row, args.arm)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
