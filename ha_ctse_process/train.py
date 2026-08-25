"""Standalone CLI and evaluation entrypoint for HA-CTSE process-core."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
import traceback

import numpy as np
import torch

try:
    from torch.utils.tensorboard import SummaryWriter
except ModuleNotFoundError:
    SummaryWriter = None

from ha_ctse_process.env_factory import normalize_scenario
from ha_ctse_process import standalone_eval_runner
from ha_ctse_process import standalone_train_runner
from ha_ctse_process.standalone_metrics import emit
from ha_ctse_process.checkpoint_io import (
    apply_checkpoint_structure,
    load_checkpoint_metadata,
)
from ha_ctse_process.standalone_cli import (
    apply_standalone_overrides,
    create_env,
    load_config,
    parse_args,
)
from ha_ctse_process.standalone_contracts import (
    enforce_iteration5_process_semantics_contract,
    enforce_r30_contract,
    enforce_r30_pair_gate,
    enforce_variable_roster_event_contract,
    is_variable_roster_event,
)
from ha_ctse_process.standalone_event_support import (
    _write_event_arm_status,
    enforce_variable_roster_event_resume_boundary,
)





def run_env_dry_check(config, args: argparse.Namespace) -> None:
    """Check the standalone env path without touching HMASD training code."""

    env = create_env(config, config.scenario, args.seed, rank=0, scale_mode="train")
    try:
        obs, info = env.reset(seed=args.seed)
        state = np.asarray(info["state"], dtype=np.float32)
        emit(
            args,
            "standalone_env_reset "
            f"scenario={normalize_scenario(args.scenario)} "
            f"state_shape={tuple(state.shape)} obs_shape={tuple(obs.shape)} "
            f"action_space={env.action_space}"
        )

        for step in range(int(args.dry_run_env_steps)):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)
            emit(
                args,
                "standalone_env_step "
                f"step={step + 1} reward={float(reward):.6f} done={done}"
            )
            if done:
                obs, info = env.reset()
    finally:
        env.close()


















def main() -> None:
    args = parse_args()
    random.seed(int(args.seed))
    np.random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(args.seed))
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(args.log_dir) if SummaryWriter is not None else None
    config = load_config(args.config, args.preset or None)
    config.scenario = normalize_scenario(args.scenario)
    apply_standalone_overrides(config, args)
    enforce_variable_roster_event_resume_boundary(config, args)
    metadata = None
    if args.resume_from:
        metadata = load_checkpoint_metadata(args.resume_from)
        apply_checkpoint_structure(config, args, metadata)
    enforce_iteration5_process_semantics_contract(config, args, metadata)
    if is_variable_roster_event(config):
        enforce_variable_roster_event_contract(config, args, metadata)
        try:
            if args.dry_run_env_steps > 0:
                raise ValueError("event mode has no environment dry-run path")
            if args.mode != "train":
                raise ValueError("event evaluation remains runner/analyzer-owned")
            standalone_train_runner.train_loop(config, args, writer)
        except Exception as exc:
            Path(args.log_dir).mkdir(parents=True, exist_ok=True)
            (Path(args.log_dir) / "runner_stderr.log").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            _write_event_arm_status(
                args,
                state="failed",
                phase="runner",
                mode=str(getattr(config, "event_architecture_mode", "unknown")),
                error=f"{type(exc).__name__}: {exc}",
                error_path=str(Path(args.log_dir) / "runner_stderr.log"),
            )
            raise
        finally:
            if writer is not None:
                writer.close()
        return
    enforce_r30_pair_gate(config, args, metadata)
    enforce_r30_contract(config, args)

    try:
        if args.dry_run_env_steps > 0:
            run_env_dry_check(config, args)
            return
        if args.mode == "eval":
            standalone_eval_runner.eval_loop(config, args, writer)
        else:
            standalone_train_runner.train_loop(config, args, writer)
    finally:
        if writer is not None:
            writer.close()


if __name__ == "__main__":
    main()
