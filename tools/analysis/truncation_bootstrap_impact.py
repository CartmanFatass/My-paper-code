"""Measure what the truncation-bootstrap fix changes on a real legacy rollout.

Before 2026-09-17 the low-level GAE collapsed `terminated or truncated` into one flag and
zeroed the bootstrap for both.  The legacy relay environments end **only** by truncation
(`is_terminated = False` in `belief_map.py`, `forced_relay.py`, `routed_core.py`), so that
branch fired at every episode boundary they ever produced.  Correct semantics are now the
default and the old arithmetic is available behind
`config.legacy_truncation_as_termination`.

This tool quantifies the difference on a genuine rollout rather than a synthetic one.  It
collects one rollout through the real runner, with the real environment, the real policy
and the real critic, then recomputes the value targets twice from that single rollout - once
with the corrected semantics and once with the legacy flag - and reports the difference.

**It takes no optimizer step.**  `process_update` and `update_low` are intercepted so the
collection pass runs and the update does not, which is what makes this a measurement of
the arithmetic rather than a training run.  The manifest export is suppressed too, so
nothing is written to `runs/`, `logs/` or `metadata/`, and no archived direction is
re-executed.

Usage::

    python tools/analysis/truncation_bootstrap_impact.py --scenario belief_map \
        --rollout-length 64 --max-steps 16 --seed 12345
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _capture_one_rollout(config: Any, args: argparse.Namespace) -> tuple[Any, Any]:
    """Run exactly one collection pass and return (agent, rollout), updating nothing."""

    from ha_ctse_process import standalone_train_runner
    from ha_ctse_process.standalone_agent import StandaloneProcessAgent

    captured: dict[str, Any] = {}

    class _StopAfterCollection(Exception):
        """Raised to end the pass the moment the rollout is complete."""

    real_process_update = StandaloneProcessAgent.process_update
    real_export = standalone_train_runner.standalone_manifest.export_run_manifest

    def intercepted_process_update(self, rollout, *called_args, **called_kwargs):
        # `process_update` is the first update the runner calls, so stopping here means
        # the collection pass ran in full and not one optimizer step was taken. The
        # rollout is kept exactly as the collector produced it.
        captured["rollout"] = rollout
        captured["agent"] = self
        raise _StopAfterCollection

    StandaloneProcessAgent.process_update = intercepted_process_update
    # A measurement is not a run: suppress the manifest export so this never leaves a
    # `metadata/run_manifest.json` behind that could be mistaken for a training record.
    standalone_train_runner.standalone_manifest.export_run_manifest = (
        lambda *called_args, **called_kwargs: None
    )
    try:
        standalone_train_runner.train_loop(config, args, writer=None)
    except _StopAfterCollection:
        pass
    finally:
        StandaloneProcessAgent.process_update = real_process_update
        standalone_train_runner.standalone_manifest.export_run_manifest = real_export

    if "rollout" not in captured:
        raise RuntimeError(
            "no rollout was collected; raise --rollout-length or --total-timesteps"
        )
    return captured["agent"], captured["rollout"]


def _summarise(name: str, values: np.ndarray) -> dict[str, float]:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    return {
        f"{name}_mean": float(np.mean(flat)) if flat.size else 0.0,
        f"{name}_abs_mean": float(np.mean(np.abs(flat))) if flat.size else 0.0,
        f"{name}_abs_max": float(np.max(np.abs(flat))) if flat.size else 0.0,
    }


def _pre_reset_evidence(
    rollout: Any, env_ids: np.ndarray, boundary_rows: np.ndarray, stored: dict
) -> dict[str, Any]:
    """Show that the captured V(s') is not the post-reset value.

    ``bootstrap_values[env_id]`` is read after the collection loop, when a truncated
    environment has already been reset, so it is the value of the *next* episode's first
    observation.  For a truncation on an environment's last row the two are directly
    comparable: if the capture happened after the reset they would be identical.  They
    must not be, and the gap is the size of the error a naive fallback would make.
    """

    end_of_pass = getattr(rollout, "bootstrap_values", {}) or {}
    rows = [
        int(row)
        for row in boundary_rows
        if int(row) in stored and int(env_ids[int(row)]) in end_of_pass
    ]
    # Only an environment's final row is comparable; earlier truncations were followed by
    # more steps, so the end-of-pass value belongs to a later episode still.
    final_rows = [
        row
        for row in rows
        if not np.any(env_ids[row + 1 :] == env_ids[row])
    ]
    if not final_rows:
        return {"comparable_rows": 0, "note": "no truncation on an environment's last row"}
    captured = np.asarray([np.mean(stored[row]) for row in final_rows], dtype=np.float64)
    post_reset = np.asarray(
        [np.mean(end_of_pass[int(env_ids[row])]) for row in final_rows], dtype=np.float64
    )
    return {
        "comparable_rows": len(final_rows),
        "captured_mean": float(np.mean(captured)),
        "post_reset_mean": float(np.mean(post_reset)),
        "identical": bool(np.allclose(captured, post_reset)),
        "abs_gap_mean": float(np.mean(np.abs(captured - post_reset))),
        "note": (
            "identical=false is the required outcome: it shows the capture happened "
            "before the reset. abs_gap_mean is the error a fallback to the end-of-pass "
            "bootstrap would have introduced."
        ),
    }


def measure(config: Any, args: argparse.Namespace) -> dict[str, Any]:
    agent, rollout = _capture_one_rollout(config, args)

    terminated = np.asarray(getattr(rollout, "terminated", []), dtype=np.bool_)
    truncated = np.asarray(getattr(rollout, "truncated", []), dtype=np.bool_)
    dones = np.asarray(rollout.dones, dtype=np.bool_)
    stored = getattr(rollout, "truncation_bootstrap_values", {}) or {}

    # Same rollout, two arithmetics. The legacy flag is read per call, so flipping it on
    # the agent is enough; nothing about the collected data changes.
    agent.legacy_truncation_as_termination = False
    corrected_returns, corrected_adv, values, env_ids = agent._low_returns(rollout)
    agent.legacy_truncation_as_termination = True
    legacy_returns, legacy_adv, _values, _env_ids = agent._low_returns(rollout)
    agent.legacy_truncation_as_termination = False

    return_delta = corrected_returns - legacy_returns
    advantage_delta = corrected_adv - legacy_adv
    changed_rows = np.flatnonzero(np.any(np.abs(return_delta) > 0.0, axis=1))
    boundary_rows = np.flatnonzero(truncated) if truncated.size else np.zeros(0, int)

    report: dict[str, Any] = {
        "tool": "truncation_bootstrap_impact",
        "optimizer_updates": 0,
        "training_fits_performed": 0,
        "scenario": getattr(args, "scenario", None),
        "seed": int(args.seed),
        "gamma": float(agent.gamma),
        "low_gae_lambda": float(agent.low_gae_lambda),
        "rollout": {
            "rows": int(dones.size),
            "n_envs": int(np.unique(env_ids).size),
            "n_boundaries": int(dones.sum()),
            "n_terminated": int(terminated.sum()) if terminated.size else None,
            "n_truncated": int(truncated.sum()) if truncated.size else None,
            "n_truncation_bootstraps_captured": len(stored),
            "truncated_row_indices": [int(row) for row in boundary_rows],
        },
        "value_target_change": {
            "n_rows_changed": int(changed_rows.size),
            "fraction_of_rows_changed": (
                float(changed_rows.size / dones.size) if dones.size else 0.0
            ),
            **_summarise("return_delta", return_delta),
            **_summarise("advantage_delta", advantage_delta),
            "legacy_return_abs_mean": float(np.mean(np.abs(legacy_returns))),
            "corrected_return_abs_mean": float(np.mean(np.abs(corrected_returns))),
        },
        "at_truncation_rows": {
            "legacy_return_mean": (
                float(np.mean(legacy_returns[boundary_rows])) if boundary_rows.size else None
            ),
            "corrected_return_mean": (
                float(np.mean(corrected_returns[boundary_rows])) if boundary_rows.size else None
            ),
            "captured_bootstrap_mean": (
                float(np.mean([np.mean(stored[int(row)]) for row in boundary_rows]))
                if boundary_rows.size and all(int(r) in stored for r in boundary_rows)
                else None
            ),
        },
        "capture_is_pre_reset": _pre_reset_evidence(rollout, env_ids, boundary_rows, stored),
        "interpretation": (
            "A non-zero change is expected and is the point: the legacy arithmetic zeroed "
            "the bootstrap at every time limit. The corrected targets are the ones a "
            "continuing or time-limited task should be fit on. This is a single short "
            "rollout from an untrained policy, so the magnitudes characterise the "
            "arithmetic, not the eventual effect on a trained result."
        ),
    }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truncation_bootstrap_impact.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", default="configs.config_test", help="config module")
    parser.add_argument("--scenario", default="belief_map", help="legacy scenario name")
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--num-envs", type=int, default=2)
    parser.add_argument("--rollout-length", type=int, default=64)
    parser.add_argument(
        "--max-steps",
        type=int,
        default=16,
        help="episode length; must be shorter than --rollout-length to force truncations",
    )
    parser.add_argument("--skill-interval", type=int, default=4)
    parser.add_argument(
        "--log-dir",
        default="",
        help="run directory; empty keeps this measurement out of logs/",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "write the report here. Prefer this over piping stdout: the trainer emits its "
            "own start banner to stdout, so only this file is pure JSON."
        ),
    )
    return parser


def build_run_inputs(argv=None):
    """The setup half of `run`: the config and args needed to collect one rollout.

    Separated so a test can reach the collected `(agent, rollout)` pair through exactly
    the setup a reported measurement uses, rather than a second hand-made copy of it.
    Returns `(config, args, args_ns)`.
    """

    args_ns = build_parser().parse_args(argv)

    from ha_ctse_process import standalone_cli

    # Build a *complete* args namespace through the real parser rather than a hand-made
    # stand-in, so this measurement sees the same defaults a training run would.
    cli_argv = [
        "--config", str(args_ns.config),
        "--scenario", str(args_ns.scenario),
        "--seed", str(int(args_ns.seed)),
        "--num_envs", str(int(args_ns.num_envs)),
        "--rollout_length", str(int(args_ns.rollout_length)),
        "--total_timesteps", str(int(args_ns.rollout_length) * int(args_ns.num_envs)),
        "--skill_interval", str(int(args_ns.skill_interval)),
        "--save_interval", "0",
        "--eval_interval", "0",
        "--log_dir", str(args_ns.log_dir),
    ]
    saved_argv = sys.argv
    sys.argv = ["standalone_cli", *cli_argv]
    try:
        args = standalone_cli.parse_args()
    finally:
        sys.argv = saved_argv

    # `train.py` seeds the global RNGs before building anything; this tool calls
    # `train_loop` directly, so it must do the same or the critic is initialised
    # differently on every invocation and the measured magnitudes are not reproducible.
    import random

    import torch

    random.seed(int(args.seed))
    np.random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))

    config = standalone_cli.load_config(args.config, args.preset or None)
    standalone_cli.apply_standalone_overrides(config, args)
    # `create_collector` reads `config.scenario`, not `args.scenario`.
    from ha_ctse_process.env_factory import normalize_scenario

    config.scenario = normalize_scenario(str(args_ns.scenario))
    # Short episodes are the point: the rollout must contain truncations to measure.
    config.max_steps = int(args_ns.max_steps)
    return config, args, args_ns


def run(argv: list[str] | None = None) -> dict[str, Any]:
    """Collect one rollout and return the impact report, printing nothing."""

    config, args, args_ns = build_run_inputs(argv)
    report = measure(config, args)
    report["episode_max_steps"] = int(args_ns.max_steps)
    return report


def main(argv: list[str] | None = None) -> int:
    args_ns = build_parser().parse_args(argv)
    report = run(argv)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args_ns.output:
        Path(args_ns.output).write_text(text + chr(10), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
